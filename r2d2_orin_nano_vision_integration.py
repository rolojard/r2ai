#!/usr/bin/env python3
"""
R2D2 Orin Nano Vision Integration
Direct integration with existing R2D2 dashboard
Works around OpenCV camera issues on Orin Nano
"""

import asyncio
import websockets
import json
import base64
import subprocess
import threading
import time
import queue
import logging
import tempfile
import os
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class R2D2OrinNanoVision:
    def __init__(self, width=640, height=480, fps=30):
        self.width = width
        self.height = height
        self.fps = fps

        # Performance monitoring
        self.frame_count = 0
        self.start_time = time.time()
        self.performance_stats = {
            'fps': 0,
            'total_frames': 0,
            'status': 'initializing'
        }

        # Threading
        self.frame_queue = queue.Queue(maxsize=2)
        self.capture_process = None
        self.is_running = False

        # WebSocket connections
        self.connected_clients = set()

    def create_gstreamer_capture_command(self):
        """Create GStreamer command for frame capture"""
        # Use GStreamer to capture frames to stdout
        cmd = [
            'gst-launch-1.0',
            'v4l2src', f'device=/dev/video0',
            '!', f'video/x-raw,width={self.width},height={self.height},framerate={self.fps}/1',
            '!', 'videoconvert',
            '!', 'video/x-raw,format=RGB',
            '!', 'appsink', 'emit-signals=true', 'sync=false', 'max-buffers=1', 'drop=true'
        ]
        return cmd

    def create_alternative_capture(self):
        """Alternative capture method using ffmpeg"""
        temp_dir = tempfile.mkdtemp()
        fifo_path = os.path.join(temp_dir, 'camera_feed')

        # Create named pipe
        os.mkfifo(fifo_path)

        # FFmpeg command to capture and write to pipe
        cmd = [
            'ffmpeg',
            '-f', 'v4l2',
            '-input_format', 'mjpeg',
            '-video_size', f'{self.width}x{self.height}',
            '-framerate', str(self.fps),
            '-i', '/dev/video0',
            '-f', 'image2pipe',
            '-vcodec', 'mjpeg',
            '-q:v', '5',
            fifo_path
        ]

        return cmd, fifo_path

    def capture_frames_with_ffmpeg(self):
        """Capture frames using ffmpeg as fallback"""
        logger.info("Starting FFmpeg capture process...")

        try:
            # FFmpeg command to capture JPEG frames
            cmd = [
                'ffmpeg',
                '-f', 'v4l2',
                '-input_format', 'mjpeg',
                '-video_size', f'{self.width}x{self.height}',
                '-framerate', str(self.fps),
                '-i', '/dev/video0',
                '-f', 'image2pipe',
                '-vcodec', 'mjpeg',
                '-q:v', '5',
                'pipe:1'
            ]

            self.capture_process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                bufsize=0
            )

            jpeg_buffer = b''
            frame_start_marker = b'\xff\xd8'  # JPEG start marker
            frame_end_marker = b'\xff\xd9'    # JPEG end marker

            while self.is_running:
                try:
                    # Read data from ffmpeg
                    data = self.capture_process.stdout.read(4096)
                    if not data:
                        break

                    jpeg_buffer += data

                    # Look for complete JPEG frames
                    while frame_start_marker in jpeg_buffer:
                        start_idx = jpeg_buffer.find(frame_start_marker)
                        if start_idx > 0:
                            jpeg_buffer = jpeg_buffer[start_idx:]

                        end_idx = jpeg_buffer.find(frame_end_marker)
                        if end_idx > 0:
                            # Complete JPEG frame found
                            frame_data = jpeg_buffer[:end_idx + 2]
                            jpeg_buffer = jpeg_buffer[end_idx + 2:]

                            # Add to queue
                            try:
                                self.frame_queue.put_nowait(frame_data)
                                self.performance_stats['total_frames'] += 1
                            except queue.Full:
                                # Drop old frame
                                try:
                                    self.frame_queue.get_nowait()
                                    self.frame_queue.put_nowait(frame_data)
                                except queue.Empty:
                                    pass
                        else:
                            break

                except Exception as e:
                    logger.error(f"Capture error: {e}")
                    time.sleep(0.1)

        except Exception as e:
            logger.error(f"FFmpeg capture failed: {e}")
        finally:
            if self.capture_process:
                self.capture_process.terminate()

    def create_synthetic_frame(self):
        """Create synthetic frame when camera is not available"""
        # Create a simple status frame
        import cv2
        import numpy as np

        frame = np.zeros((self.height, self.width, 3), dtype=np.uint8)

        # Background color
        frame[:] = (20, 20, 40)  # Dark blue background

        # R2D2 status text
        timestamp = datetime.now().strftime("%H:%M:%S")

        cv2.putText(frame, "R2-D2 VISION SYSTEM", (50, 100),
                   cv2.FONT_HERSHEY_DUPLEX, 1.0, (0, 255, 255), 2)

        cv2.putText(frame, "ORIN NANO PLATFORM", (80, 140),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)

        cv2.putText(frame, f"STATUS: {self.performance_stats['status'].upper()}", (50, 200),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 0), 2)

        cv2.putText(frame, f"TIME: {timestamp}", (50, 240),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)

        cv2.putText(frame, f"FRAMES: {self.performance_stats['total_frames']}", (50, 270),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)

        if self.connected_clients:
            cv2.putText(frame, f"CLIENTS CONNECTED: {len(self.connected_clients)}", (50, 300),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 1)
        else:
            cv2.putText(frame, "WAITING FOR CLIENTS...", (50, 300),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 1)

        # Connection indicator
        if self.connected_clients:
            cv2.circle(frame, (self.width - 50, 50), 20, (0, 255, 0), -1)
            cv2.putText(frame, "ONLINE", (self.width - 120, 60),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
        else:
            cv2.circle(frame, (self.width - 50, 50), 20, (0, 0, 255), -1)
            cv2.putText(frame, "OFFLINE", (self.width - 120, 60),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1)

        # Encode to JPEG
        encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), 85]
        ret, buffer = cv2.imencode('.jpg', frame, encode_param)

        if ret:
            return buffer.tobytes()
        return None

    def initialize_camera_system(self):
        """Initialize camera capture system"""
        logger.info("Initializing Orin Nano camera system...")

        # Try ffmpeg capture
        try:
            # Test if we can access the camera
            test_cmd = ['ffmpeg', '-f', 'v4l2', '-list_formats', 'all', '-i', '/dev/video0']
            result = subprocess.run(test_cmd, capture_output=True, text=True, timeout=5)

            if result.returncode == 0 or 'mjpeg' in result.stderr.lower():
                logger.info("Camera detected, using FFmpeg capture")
                self.performance_stats['status'] = 'camera_ready'
                return True
            else:
                logger.warning("Camera access issues, using synthetic frames")
                self.performance_stats['status'] = 'synthetic_mode'
                return True

        except Exception as e:
            logger.warning(f"Camera initialization failed: {e}")
            self.performance_stats['status'] = 'synthetic_mode'
            return True

    def start_capture_system(self):
        """Start the capture system"""
        if self.performance_stats['status'] == 'camera_ready':
            # Start FFmpeg capture in thread
            capture_thread = threading.Thread(target=self.capture_frames_with_ffmpeg)
            capture_thread.daemon = True
            capture_thread.start()
        else:
            # Use synthetic frames
            logger.info("Using synthetic frame generation")

    def get_next_frame(self):
        """Get next frame (either from camera or synthetic)"""
        if self.performance_stats['status'] == 'camera_ready':
            try:
                # Try to get frame from camera queue
                frame_data = self.frame_queue.get_nowait()
                return base64.b64encode(frame_data).decode('utf-8')
            except queue.Empty:
                # Fall back to synthetic frame
                synthetic_frame = self.create_synthetic_frame()
                if synthetic_frame:
                    return base64.b64encode(synthetic_frame).decode('utf-8')
        else:
            # Generate synthetic frame
            synthetic_frame = self.create_synthetic_frame()
            if synthetic_frame:
                return base64.b64encode(synthetic_frame).decode('utf-8')

        return None

    def update_performance_stats(self):
        """Update performance statistics"""
        self.frame_count += 1
        elapsed = time.time() - self.start_time
        self.performance_stats['fps'] = self.frame_count / elapsed if elapsed > 0 else 0

    async def websocket_handler(self, websocket, path):
        """Handle WebSocket connections"""
        logger.info(f"New WebSocket connection from {websocket.remote_address}")
        self.connected_clients.add(websocket)

        try:
            # Send initial status
            status_message = json.dumps({
                'type': 'status',
                'message': 'R2D2 Orin Nano Vision System Connected',
                'config': {
                    'width': self.width,
                    'height': self.height,
                    'fps': self.fps,
                    'mode': self.performance_stats['status']
                }
            })
            await websocket.send(status_message)

            await websocket.wait_closed()
        except Exception as e:
            logger.error(f"WebSocket error: {e}")
        finally:
            self.connected_clients.remove(websocket)
            logger.info(f"WebSocket connection closed")

    async def broadcast_frames(self):
        """Broadcast frames to connected clients"""
        frame_interval = 1.0 / self.fps
        last_broadcast = 0

        while self.is_running:
            try:
                current_time = time.time()

                if current_time - last_broadcast >= frame_interval:
                    frame_data = self.get_next_frame()

                    if frame_data and self.connected_clients:
                        message = json.dumps({
                            'type': 'frame',
                            'data': frame_data,
                            'timestamp': current_time,
                            'stats': self.performance_stats
                        })

                        # Send to all connected clients
                        disconnected = set()
                        for client in self.connected_clients:
                            try:
                                await client.send(message)
                            except:
                                disconnected.add(client)

                        # Remove disconnected clients
                        self.connected_clients -= disconnected

                        self.update_performance_stats()
                        last_broadcast = current_time

                await asyncio.sleep(0.01)

            except Exception as e:
                logger.error(f"Broadcast error: {e}")
                await asyncio.sleep(0.1)

    async def start_vision_system(self, host='0.0.0.0', port=8765):
        """Start the complete vision system"""
        logger.info("Starting R2D2 Orin Nano Vision System...")

        # Initialize camera
        if not self.initialize_camera_system():
            logger.error("Failed to initialize camera system")
            return False

        self.is_running = True
        self.start_time = time.time()

        # Start capture system
        self.start_capture_system()

        # Start WebSocket server
        logger.info(f"Starting WebSocket server on {host}:{port}")
        server = await websockets.serve(self.websocket_handler, host, port)

        # Start broadcasting
        broadcast_task = asyncio.create_task(self.broadcast_frames())

        logger.info("R2D2 Vision System is running!")
        logger.info(f"Connect to ws://{host}:{port} for video feed")
        logger.info(f"Status: {self.performance_stats['status']}")

        try:
            await broadcast_task
        except KeyboardInterrupt:
            logger.info("Shutting down...")
        finally:
            self.is_running = False
            if self.capture_process:
                self.capture_process.terminate()
            server.close()
            await server.wait_closed()

def main():
    """Main entry point"""
    print("=== R2D2 Orin Nano Vision Integration ===")
    print("Hardware-optimized video system for R2D2 dashboard")

    vision = R2D2OrinNanoVision(
        width=640,
        height=480,
        fps=30
    )

    try:
        asyncio.run(vision.start_vision_system())
    except KeyboardInterrupt:
        print("\nShutdown requested")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()