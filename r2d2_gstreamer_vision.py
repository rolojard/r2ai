#!/usr/bin/env python3
"""
R2D2 GStreamer Vision System for Orin Nano
High-performance video capture using GStreamer backend
Optimized for Nvidia Orin Nano with hardware acceleration
"""

import cv2
import asyncio
import websockets
import json
import base64
import numpy as np
import threading
import time
import queue
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class R2D2GStreamerVision:
    def __init__(self, width=640, height=480, fps=30):
        self.width = width
        self.height = height
        self.fps = fps
        self.cap = None

        # Performance monitoring
        self.frame_count = 0
        self.start_time = time.time()
        self.last_fps_report = time.time()
        self.performance_stats = {
            'fps': 0,
            'frame_time': 0,
            'processing_time': 0,
            'dropped_frames': 0,
            'total_frames': 0
        }

        # Threading
        self.frame_queue = queue.Queue(maxsize=2)
        self.capture_thread = None
        self.is_running = False

        # WebSocket connections
        self.connected_clients = set()

    def create_gstreamer_pipeline(self):
        """Create optimized GStreamer pipeline for Orin Nano"""
        # GStreamer pipeline optimized for Orin Nano
        pipeline = (
            f"v4l2src device=/dev/video0 ! "
            f"video/x-raw,width={self.width},height={self.height},framerate={self.fps}/1,format=YUY2 ! "
            f"videoconvert ! "
            f"video/x-raw,format=BGR ! "
            f"appsink emit-signals=true sync=false max-buffers=1 drop=true"
        )

        logger.info(f"GStreamer pipeline: {pipeline}")
        return pipeline

    def initialize_camera(self):
        """Initialize camera with GStreamer backend"""
        logger.info("Initializing camera with GStreamer...")

        pipeline = self.create_gstreamer_pipeline()

        # Use GStreamer backend
        self.cap = cv2.VideoCapture(pipeline, cv2.CAP_GSTREAMER)

        if not self.cap.isOpened():
            logger.error("Failed to open GStreamer pipeline")
            return False

        # Verify configuration
        actual_width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        actual_height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        actual_fps = self.cap.get(cv2.CAP_PROP_FPS)

        logger.info(f"Camera configured: {actual_width}x{actual_height} @ {actual_fps} FPS")

        # Test capture
        ret, frame = self.cap.read()
        if ret:
            logger.info(f"Test frame captured: {frame.shape}")
        else:
            logger.error("Failed to capture test frame")
            return False

        logger.info("Camera initialization successful!")
        return True

    def capture_thread_worker(self):
        """Dedicated thread for frame capture"""
        logger.info("Starting GStreamer capture thread...")

        frame_interval = 1.0 / self.fps
        last_capture = 0

        while self.is_running:
            try:
                current_time = time.time()

                # Control capture rate
                if current_time - last_capture < frame_interval:
                    time.sleep(0.001)
                    continue

                ret, frame = self.cap.read()

                if ret and frame is not None:
                    last_capture = current_time

                    # Put frame in queue (non-blocking)
                    try:
                        self.frame_queue.put_nowait(frame)
                        self.performance_stats['total_frames'] += 1
                    except queue.Full:
                        # Queue full, drop oldest frame
                        try:
                            self.frame_queue.get_nowait()
                            self.frame_queue.put_nowait(frame)
                            self.performance_stats['dropped_frames'] += 1
                        except queue.Empty:
                            pass
                else:
                    logger.warning("Failed to capture frame")
                    time.sleep(0.01)

            except Exception as e:
                logger.error(f"Capture thread error: {e}")
                time.sleep(0.01)

        logger.info("Capture thread stopped")

    def process_frame_with_r2d2_overlay(self, frame):
        """Process frame with R2D2 character overlay"""
        process_start = time.time()

        # Ensure correct size
        if frame.shape[1] != self.width or frame.shape[0] != self.height:
            frame = cv2.resize(frame, (self.width, self.height))

        # R2D2 themed overlay
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]

        # Main title
        cv2.putText(frame, "R2-D2 VISION SYSTEM", (10, 25),
                   cv2.FONT_HERSHEY_DUPLEX, 0.6, (0, 255, 255), 2)

        # Status line
        status_text = f"ORIN NANO | {timestamp}"
        cv2.putText(frame, status_text, (10, 50),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)

        # Performance stats
        fps_text = f"FPS: {self.performance_stats['fps']:.1f}"
        cv2.putText(frame, fps_text, (10, self.height - 40),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 0), 1)

        frames_text = f"FRAMES: {self.performance_stats['total_frames']}"
        cv2.putText(frame, frames_text, (10, self.height - 20),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 0), 1)

        # Connection indicator
        if self.connected_clients:
            cv2.circle(frame, (self.width - 30, 30), 8, (0, 255, 0), -1)
            cv2.putText(frame, f"CLIENTS: {len(self.connected_clients)}", (self.width - 120, 50),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 255, 0), 1)
        else:
            cv2.circle(frame, (self.width - 30, 30), 8, (0, 0, 255), -1)
            cv2.putText(frame, "NO CLIENTS", (self.width - 90, 50),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 0, 255), 1)

        process_time = time.time() - process_start
        self.performance_stats['processing_time'] = process_time

        return frame

    def encode_frame_for_web(self, frame):
        """Encode frame for web transmission"""
        # High quality JPEG encoding
        encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), 90]
        ret, buffer = cv2.imencode('.jpg', frame, encode_param)

        if ret:
            frame_data = base64.b64encode(buffer).decode('utf-8')
            return frame_data
        return None

    def update_performance_stats(self):
        """Update performance statistics"""
        current_time = time.time()
        self.frame_count += 1

        # Calculate FPS every second
        if current_time - self.last_fps_report >= 1.0:
            elapsed = current_time - self.start_time
            self.performance_stats['fps'] = self.frame_count / elapsed if elapsed > 0 else 0
            self.last_fps_report = current_time

    async def websocket_handler(self, websocket, path):
        """Handle WebSocket connections"""
        logger.info(f"New WebSocket connection from {websocket.remote_address}")
        self.connected_clients.add(websocket)

        try:
            # Send initial status
            status_message = json.dumps({
                'type': 'status',
                'message': 'R2D2 Vision System Connected',
                'camera_config': {
                    'width': self.width,
                    'height': self.height,
                    'fps': self.fps
                }
            })
            await websocket.send(status_message)

            await websocket.wait_closed()
        except Exception as e:
            logger.error(f"WebSocket error: {e}")
        finally:
            self.connected_clients.remove(websocket)
            logger.info(f"WebSocket connection closed: {websocket.remote_address}")

    async def broadcast_frame(self, frame_data):
        """Broadcast frame to all connected clients"""
        if not self.connected_clients:
            return

        message = json.dumps({
            'type': 'frame',
            'data': frame_data,
            'timestamp': time.time(),
            'stats': self.performance_stats
        })

        # Send to all connected clients
        disconnected = set()
        for client in self.connected_clients:
            try:
                await client.send(message)
            except websockets.exceptions.ConnectionClosed:
                disconnected.add(client)
            except Exception as e:
                logger.error(f"Error sending frame: {e}")
                disconnected.add(client)

        # Remove disconnected clients
        self.connected_clients -= disconnected

    async def video_processing_loop(self):
        """Main video processing loop"""
        logger.info("Starting video processing loop...")

        frame_interval = 1.0 / self.fps
        last_broadcast = 0

        while self.is_running:
            try:
                # Get frame from queue
                frame = self.frame_queue.get(timeout=0.1)

                # Process frame
                processed_frame = self.process_frame_with_r2d2_overlay(frame)

                # Update performance stats
                self.update_performance_stats()

                # Control broadcast rate
                current_time = time.time()
                if current_time - last_broadcast >= frame_interval:
                    # Encode for web
                    frame_data = self.encode_frame_for_web(processed_frame)

                    if frame_data:
                        # Broadcast to connected clients
                        await self.broadcast_frame(frame_data)
                        last_broadcast = current_time

                # Small delay to prevent overwhelming
                await asyncio.sleep(0.001)

            except queue.Empty:
                await asyncio.sleep(0.01)
            except Exception as e:
                logger.error(f"Processing loop error: {e}")
                await asyncio.sleep(0.01)

    async def start_vision_system(self, host='0.0.0.0', port=8765):
        """Start the complete vision system"""
        logger.info("Starting R2D2 GStreamer Vision System...")

        # Initialize camera
        if not self.initialize_camera():
            logger.error("Failed to initialize camera")
            return False

        self.is_running = True
        self.start_time = time.time()

        # Start capture thread
        self.capture_thread = threading.Thread(target=self.capture_thread_worker)
        self.capture_thread.daemon = True
        self.capture_thread.start()

        # Start WebSocket server
        logger.info(f"Starting WebSocket server on {host}:{port}")
        server = await websockets.serve(self.websocket_handler, host, port)

        # Start video processing loop
        processing_task = asyncio.create_task(self.video_processing_loop())

        logger.info("R2D2 Vision System is running!")
        logger.info(f"Connect to ws://{host}:{port} for video feed")

        try:
            # Run until interrupted
            await processing_task
        except KeyboardInterrupt:
            logger.info("Shutting down vision system...")
        finally:
            await self.stop_vision_system()
            server.close()
            await server.wait_closed()

    async def stop_vision_system(self):
        """Stop the vision system"""
        logger.info("Stopping vision system...")
        self.is_running = False

        # Wait for capture thread to finish
        if self.capture_thread and self.capture_thread.is_alive():
            self.capture_thread.join(timeout=2)

        # Release camera
        if self.cap:
            self.cap.release()

        logger.info("Vision system stopped")

def main():
    """Main entry point"""
    print("=== R2D2 GStreamer Vision System for Orin Nano ===")
    print("Optimized for hardware-accelerated video capture")

    # Create vision system
    vision = R2D2GStreamerVision(
        width=640,
        height=480,
        fps=30
    )

    try:
        # Run the vision system
        asyncio.run(vision.start_vision_system())
    except KeyboardInterrupt:
        print("\nShutdown requested by user")
    except Exception as e:
        print(f"Error: {e}")
        logger.error(f"Main error: {e}")

if __name__ == "__main__":
    main()