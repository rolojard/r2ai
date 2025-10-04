#!/usr/bin/env python3
"""
R2D2 Real Webcam System with Zero Flickering
AUTONOMOUS IMPLEMENTATION - Real camera, no mock feeds
"""

import cv2
import asyncio
import websockets
import json
import threading
import time
import queue
import base64
import signal
import sys
import numpy as np
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class R2D2RealWebcamSystem:
    def __init__(self):
        self.camera = None
        self.is_running = False
        self.frame_queue = queue.Queue(maxsize=5)  # Buffer frames to prevent blocking
        self.capture_thread = None
        self.websocket_clients = set()
        self.frame_count = 0
        self.start_time = time.time()
        self.last_frame_time = time.time()

        # Anti-flickering configuration
        self.target_fps = 30
        self.frame_interval = 1.0 / self.target_fps
        self.buffer_size = 3  # Number of frames to buffer for stability

        # Camera configuration for stability
        self.camera_width = 640
        self.camera_height = 480
        self.camera_fps = 30

        logger.info("R2D2 Real Webcam System initialized")

    def setup_camera(self):
        """Initialize real camera with optimal settings for stability"""
        try:
            # Try different camera indices if needed
            for camera_index in [0, 1, 2]:
                logger.info(f"Attempting to connect to camera {camera_index}")
                self.camera = cv2.VideoCapture(camera_index)

                if self.camera.isOpened():
                    logger.info(f"Successfully connected to camera {camera_index}")
                    break
                else:
                    self.camera.release()
                    self.camera = None

            if not self.camera or not self.camera.isOpened():
                raise Exception("No camera found or camera failed to open")

            # Configure camera settings for stability
            self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, self.camera_width)
            self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, self.camera_height)
            self.camera.set(cv2.CAP_PROP_FPS, self.camera_fps)

            # Disable auto-exposure and auto-white-balance for consistency
            self.camera.set(cv2.CAP_PROP_AUTO_EXPOSURE, 0.25)  # Manual exposure
            self.camera.set(cv2.CAP_PROP_EXPOSURE, -6)  # Set specific exposure

            # Set buffer size to reduce latency
            self.camera.set(cv2.CAP_PROP_BUFFERSIZE, 1)

            # Verify settings
            actual_width = self.camera.get(cv2.CAP_PROP_FRAME_WIDTH)
            actual_height = self.camera.get(cv2.CAP_PROP_FRAME_HEIGHT)
            actual_fps = self.camera.get(cv2.CAP_PROP_FPS)

            logger.info(f"Camera configured: {actual_width}x{actual_height} @ {actual_fps} FPS")

            # Warm up camera
            for _ in range(10):
                ret, frame = self.camera.read()
                if not ret:
                    raise Exception("Failed to read from camera during warmup")

            logger.info("Camera warmup completed successfully")
            return True

        except Exception as e:
            logger.error(f"Camera setup failed: {e}")
            if self.camera:
                self.camera.release()
                self.camera = None
            return False

    def capture_frames(self):
        """Continuous frame capture with anti-flickering timing"""
        logger.info("Starting frame capture thread")

        while self.is_running and self.camera:
            try:
                frame_start = time.time()

                # Read frame from camera
                ret, frame = self.camera.read()
                if not ret:
                    logger.warning("Failed to read frame from camera")
                    time.sleep(0.01)
                    continue

                # Apply image stabilization and enhancement
                frame = self.enhance_frame(frame)

                # Add frame to queue (non-blocking)
                try:
                    self.frame_queue.put(frame, block=False)
                except queue.Full:
                    # Remove oldest frame if queue is full
                    try:
                        self.frame_queue.get_nowait()
                        self.frame_queue.put(frame, block=False)
                    except queue.Empty:
                        pass

                self.frame_count += 1

                # Maintain consistent timing for anti-flickering
                elapsed = time.time() - frame_start
                sleep_time = max(0, self.frame_interval - elapsed)
                if sleep_time > 0:
                    time.sleep(sleep_time)

            except Exception as e:
                logger.error(f"Error in frame capture: {e}")
                time.sleep(0.1)

        logger.info("Frame capture thread stopped")

    def enhance_frame(self, frame):
        """Apply image enhancement for better quality and stability"""
        try:
            # Resize if needed
            if frame.shape[1] != self.camera_width or frame.shape[0] != self.camera_height:
                frame = cv2.resize(frame, (self.camera_width, self.camera_height))

            # Apply slight Gaussian blur to reduce noise
            frame = cv2.GaussianBlur(frame, (3, 3), 0.5)

            # Enhance contrast slightly
            frame = cv2.convertScaleAbs(frame, alpha=1.1, beta=10)

            # Add R2D2 overlay
            frame = self.add_r2d2_overlay(frame)

            return frame

        except Exception as e:
            logger.error(f"Error enhancing frame: {e}")
            return frame

    def add_r2d2_overlay(self, frame):
        """Add R2D2-themed overlay to frame"""
        try:
            # Calculate FPS
            current_time = time.time()
            if current_time - self.last_frame_time > 0:
                fps = 1.0 / (current_time - self.last_frame_time)
            else:
                fps = 0
            self.last_frame_time = current_time

            # Add timestamp and FPS
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            cv2.putText(frame, f"R2D2 Vision System", (10, 30),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
            cv2.putText(frame, f"Time: {timestamp}", (10, 60),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
            cv2.putText(frame, f"FPS: {fps:.1f}", (10, 80),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
            cv2.putText(frame, f"Frames: {self.frame_count}", (10, 100),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)

            # Add border
            cv2.rectangle(frame, (5, 5), (frame.shape[1]-5, frame.shape[0]-5), (0, 255, 255), 2)

            return frame

        except Exception as e:
            logger.error(f"Error adding overlay: {e}")
            return frame

    def encode_frame_for_web(self, frame):
        """Encode frame as base64 JPEG for web transmission"""
        try:
            # Encode as JPEG with good quality
            encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), 85]
            _, buffer = cv2.imencode('.jpg', frame, encode_param)

            # Convert to base64
            frame_base64 = base64.b64encode(buffer).decode('utf-8')
            return frame_base64

        except Exception as e:
            logger.error(f"Error encoding frame: {e}")
            return None

    async def websocket_handler(self, websocket, path):
        """Handle WebSocket connections for video streaming"""
        logger.info(f"New WebSocket client connected: {websocket.remote_address}")
        self.websocket_clients.add(websocket)

        try:
            await websocket.send(json.dumps({
                "type": "connection_status",
                "message": "Connected to R2D2 Real Webcam System",
                "timestamp": datetime.now().isoformat()
            }))

            # Keep connection alive and send periodic status
            while websocket.open:
                await asyncio.sleep(5)
                await websocket.send(json.dumps({
                    "type": "status",
                    "frame_count": self.frame_count,
                    "uptime": time.time() - self.start_time,
                    "camera_active": self.camera is not None and self.camera.isOpened()
                }))

        except websockets.exceptions.ConnectionClosed:
            logger.info("WebSocket client disconnected")
        except Exception as e:
            logger.error(f"WebSocket error: {e}")
        finally:
            self.websocket_clients.discard(websocket)

    async def broadcast_frames(self):
        """Broadcast frames to all connected WebSocket clients"""
        logger.info("Starting frame broadcast loop")

        while self.is_running:
            try:
                # Get latest frame from queue
                if not self.frame_queue.empty():
                    frame = self.frame_queue.get_nowait()
                    frame_base64 = self.encode_frame_for_web(frame)

                    if frame_base64 and self.websocket_clients:
                        message = json.dumps({
                            "type": "video_frame",
                            "frame": frame_base64,
                            "timestamp": datetime.now().isoformat(),
                            "frame_number": self.frame_count
                        })

                        # Send to all connected clients
                        disconnected_clients = set()
                        for client in self.websocket_clients:
                            try:
                                if client.open:
                                    await client.send(message)
                                else:
                                    disconnected_clients.add(client)
                            except Exception as e:
                                logger.warning(f"Failed to send frame to client: {e}")
                                disconnected_clients.add(client)

                        # Remove disconnected clients
                        self.websocket_clients -= disconnected_clients

                # Control broadcast rate
                await asyncio.sleep(1.0 / self.target_fps)

            except Exception as e:
                logger.error(f"Error in frame broadcast: {e}")
                await asyncio.sleep(0.1)

    def start(self):
        """Start the webcam system"""
        logger.info("Starting R2D2 Real Webcam System")

        # Setup camera
        if not self.setup_camera():
            logger.error("Failed to setup camera. System cannot start.")
            return False

        self.is_running = True

        # Start capture thread
        self.capture_thread = threading.Thread(target=self.capture_frames)
        self.capture_thread.daemon = True
        self.capture_thread.start()

        logger.info("R2D2 Real Webcam System started successfully")
        return True

    def stop(self):
        """Stop the webcam system"""
        logger.info("Stopping R2D2 Real Webcam System")

        self.is_running = False

        if self.capture_thread:
            self.capture_thread.join(timeout=2)

        if self.camera:
            self.camera.release()
            self.camera = None

        # Clear frame queue
        while not self.frame_queue.empty():
            try:
                self.frame_queue.get_nowait()
            except queue.Empty:
                break

        logger.info("R2D2 Real Webcam System stopped")

async def main():
    """Main function to run the webcam system"""
    # Create webcam system
    webcam_system = R2D2RealWebcamSystem()

    # Setup signal handlers for graceful shutdown
    def signal_handler(signum, frame):
        logger.info("Received shutdown signal")
        webcam_system.stop()
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # Start webcam system
    if not webcam_system.start():
        logger.error("Failed to start webcam system")
        return

    # Start WebSocket server
    logger.info("Starting WebSocket server on port 8767")
    server = await websockets.serve(
        webcam_system.websocket_handler,
        "localhost",
        8767
    )

    # Start frame broadcasting
    broadcast_task = asyncio.create_task(webcam_system.broadcast_frames())

    try:
        logger.info("R2D2 Real Webcam System is running. Press Ctrl+C to stop.")
        await asyncio.Future()  # Run forever
    except KeyboardInterrupt:
        logger.info("Shutdown requested")
    finally:
        webcam_system.stop()
        broadcast_task.cancel()
        server.close()
        await server.wait_closed()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("System shutdown complete")