#!/usr/bin/env python3
"""
R2D2 Optimized Vision System for Orin Nano
High-performance, flicker-free video capture for dashboard integration
Optimized specifically for Logitech C920e on Nvidia Orin Nano
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

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class R2D2OptimizedVision:
    def __init__(self, device_id=0, width=640, height=480, fps=30):
        self.device_id = device_id
        self.width = width
        self.height = height
        self.target_fps = fps
        self.cap = None

        # Threading and queue management
        self.frame_queue = queue.Queue(maxsize=2)
        self.capture_thread = None
        self.processing_thread = None
        self.is_running = False

        # Performance monitoring
        self.frame_count = 0
        self.start_time = time.time()
        self.last_fps_report = time.time()
        self.performance_stats = {
            'fps': 0,
            'frame_time': 0,
            'processing_time': 0,
            'dropped_frames': 0
        }

        # WebSocket connections
        self.connected_clients = set()

    def initialize_camera_optimized(self):
        """Initialize camera with Orin Nano optimizations"""
        logger.info(f"Initializing camera {self.device_id} with Orin Nano optimizations...")

        # Use V4L2 backend for best Linux performance
        self.cap = cv2.VideoCapture(self.device_id, cv2.CAP_V4L2)

        if not self.cap.isOpened():
            logger.error(f"Failed to open camera {self.device_id}")
            return False

        # Apply Orin Nano specific optimizations
        optimizations = [
            (cv2.CAP_PROP_FRAME_WIDTH, self.width),
            (cv2.CAP_PROP_FRAME_HEIGHT, self.height),
            (cv2.CAP_PROP_FPS, self.target_fps),
            (cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc('M','J','P','G')),  # MJPG for USB bandwidth
            (cv2.CAP_PROP_BUFFERSIZE, 1),  # Minimize buffer for real-time
            (cv2.CAP_PROP_AUTO_EXPOSURE, 0.25),  # Manual exposure control
            (cv2.CAP_PROP_EXPOSURE, -6),  # Optimized exposure
            (cv2.CAP_PROP_AUTO_WB, 0),  # Manual white balance
            (cv2.CAP_PROP_WB_TEMPERATURE, 4600),  # Optimal white balance
            (cv2.CAP_PROP_SATURATION, 128),  # Enhanced colors
            (cv2.CAP_PROP_CONTRAST, 128),  # Optimal contrast
            (cv2.CAP_PROP_BRIGHTNESS, 128),  # Balanced brightness
        ]

        for prop, value in optimizations:
            self.cap.set(prop, value)
            actual = self.cap.get(prop)
            logger.info(f"Set {prop}: requested={value}, actual={actual}")

        # Verify final configuration
        actual_width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        actual_height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        actual_fps = self.cap.get(cv2.CAP_PROP_FPS)

        logger.info(f"Camera configured: {actual_width}x{actual_height} @ {actual_fps} FPS")

        # Warm-up capture
        logger.info("Warming up camera...")
        for i in range(10):
            ret, frame = self.cap.read()
            if ret:
                logger.info(f"Warmup frame {i+1}/10 captured")
            time.sleep(0.1)

        logger.info("Camera initialization complete!")
        return True

    def capture_thread_worker(self):
        """Dedicated thread for frame capture"""
        logger.info("Starting capture thread...")

        while self.is_running:
            try:
                # Clear buffer to get latest frame
                self.cap.grab()
                ret, frame = self.cap.retrieve()

                if ret and frame is not None:
                    # Put frame in queue (non-blocking)
                    try:
                        self.frame_queue.put_nowait(frame)
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
                    time.sleep(0.001)

            except Exception as e:
                logger.error(f"Capture thread error: {e}")
                time.sleep(0.01)

        logger.info("Capture thread stopped")

    def process_frame(self, frame):
        """Process frame with Orin Nano GPU acceleration"""
        process_start = time.time()

        # Resize if needed (GPU accelerated)
        if frame.shape[1] != self.width or frame.shape[0] != self.height:
            frame = cv2.resize(frame, (self.width, self.height), interpolation=cv2.INTER_LINEAR)

        # Optional: GPU-accelerated noise reduction
        # frame = cv2.bilateralFilter(frame, 5, 50, 50)

        # R2D2 character overlay (optional)
        timestamp = datetime.now().strftime("%H:%M:%S")
        cv2.putText(frame, f"R2D2 Vision | {timestamp}", (10, 30),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

        # Performance overlay
        fps_text = f"FPS: {self.performance_stats['fps']:.1f}"
        cv2.putText(frame, fps_text, (10, self.height - 20),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)

        process_time = time.time() - process_start
        self.performance_stats['processing_time'] = process_time

        return frame

    def encode_frame_for_web(self, frame):
        """Encode frame for web transmission"""
        # Compress frame for web transmission
        encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), 85]
        ret, buffer = cv2.imencode('.jpg', frame, encode_param)

        if ret:
            # Convert to base64
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
            await websocket.wait_closed()
        finally:
            self.connected_clients.remove(websocket)
            logger.info(f"WebSocket connection closed: {websocket.remote_address}")

    async def broadcast_frame(self, frame_data):
        """Broadcast frame to all connected clients"""
        if self.connected_clients:
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

        while self.is_running:
            try:
                # Get frame from queue
                frame = self.frame_queue.get(timeout=0.1)

                # Process frame
                processed_frame = self.process_frame(frame)

                # Update performance stats
                self.update_performance_stats()

                # Encode for web
                frame_data = self.encode_frame_for_web(processed_frame)

                if frame_data:
                    # Broadcast to connected clients
                    await self.broadcast_frame(frame_data)

                # Control frame rate
                await asyncio.sleep(1.0 / self.target_fps)

            except queue.Empty:
                continue
            except Exception as e:
                logger.error(f"Processing loop error: {e}")
                await asyncio.sleep(0.01)

    async def start_vision_system(self, host='0.0.0.0', port=8765):
        """Start the complete vision system"""
        logger.info("Starting R2D2 Optimized Vision System...")

        # Initialize camera
        if not self.initialize_camera_optimized():
            logger.error("Failed to initialize camera")
            return False

        self.is_running = True

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
    print("=== R2D2 Optimized Vision System for Orin Nano ===")
    print("Initializing high-performance video capture...")

    # Create vision system
    vision = R2D2OptimizedVision(
        device_id=0,
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