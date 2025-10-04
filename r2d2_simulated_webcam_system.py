#!/usr/bin/env python3
"""
R2D2 Simulated Webcam System - Acts like real webcam without hardware
AUTONOMOUS IMPLEMENTATION - Simulates real camera behavior with zero flickering
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
import math

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class R2D2SimulatedWebcamSystem:
    def __init__(self):
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

        # Simulated camera configuration
        self.camera_width = 640
        self.camera_height = 480
        self.camera_fps = 30

        logger.info("R2D2 Simulated Webcam System initialized")

    def create_simulated_frame(self):
        """Create a realistic simulated camera frame"""
        try:
            # Create a gradient background
            frame = np.zeros((self.camera_height, self.camera_width, 3), dtype=np.uint8)

            # Create animated gradient based on frame count
            time_factor = self.frame_count * 0.1

            for y in range(self.camera_height):
                for x in range(self.camera_width):
                    # Create animated color patterns
                    r = int(128 + 127 * math.sin(time_factor + x * 0.01))
                    g = int(128 + 127 * math.sin(time_factor + y * 0.01 + math.pi/3))
                    b = int(128 + 127 * math.sin(time_factor + (x+y) * 0.005 + 2*math.pi/3))

                    frame[y, x] = [b, g, r]  # OpenCV uses BGR

            # Add moving R2D2 logo
            center_x = int(self.camera_width/2 + 100 * math.sin(time_factor * 0.5))
            center_y = int(self.camera_height/2 + 50 * math.cos(time_factor * 0.3))

            # Draw R2D2-like elements
            cv2.circle(frame, (center_x, center_y), 80, (255, 255, 255), -1)  # Head
            cv2.circle(frame, (center_x, center_y), 75, (200, 200, 255), -1)  # Head inner
            cv2.circle(frame, (center_x-25, center_y-20), 15, (0, 0, 255), -1)  # Left eye
            cv2.circle(frame, (center_x+25, center_y-20), 15, (0, 255, 0), -1)  # Right eye
            cv2.rectangle(frame, (center_x-40, center_y+10), (center_x+40, center_y+30), (100, 100, 100), -1)  # Mouth

            # Add noise for realism
            noise = np.random.randint(0, 20, frame.shape, dtype=np.uint8)
            frame = cv2.add(frame, noise)

            return frame

        except Exception as e:
            logger.error(f"Error creating simulated frame: {e}")
            # Return a simple black frame if generation fails
            return np.zeros((self.camera_height, self.camera_width, 3), dtype=np.uint8)

    def capture_frames(self):
        """Continuous frame generation with anti-flickering timing"""
        logger.info("Starting simulated frame generation thread")

        while self.is_running:
            try:
                frame_start = time.time()

                # Generate simulated frame
                frame = self.create_simulated_frame()

                # Apply image enhancement
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
                logger.error(f"Error in frame generation: {e}")
                time.sleep(0.1)

        logger.info("Frame generation thread stopped")

    def enhance_frame(self, frame):
        """Apply image enhancement for better quality and stability"""
        try:
            # Apply slight Gaussian blur to reduce noise
            frame = cv2.GaussianBlur(frame, (3, 3), 0.5)

            # Enhance contrast slightly
            frame = cv2.convertScaleAbs(frame, alpha=1.05, beta=5)

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
            cv2.putText(frame, f"R2D2 Simulated Vision System", (10, 30),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)
            cv2.putText(frame, f"Time: {timestamp}", (10, 60),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 255), 1)
            cv2.putText(frame, f"FPS: {fps:.1f}", (10, 80),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 255), 1)
            cv2.putText(frame, f"Frames: {self.frame_count}", (10, 100),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 255), 1)
            cv2.putText(frame, f"Status: REAL SIMULATION", (10, 120),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 255, 0), 1)

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
                "message": "Connected to R2D2 Simulated Webcam System",
                "timestamp": datetime.now().isoformat()
            }))

            # Keep connection alive and send periodic status
            while websocket.open:
                await asyncio.sleep(5)
                await websocket.send(json.dumps({
                    "type": "status",
                    "frame_count": self.frame_count,
                    "uptime": time.time() - self.start_time,
                    "camera_active": True,
                    "simulation_mode": True
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
                            "frame_number": self.frame_count,
                            "simulation_mode": True
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
        """Start the simulated webcam system"""
        logger.info("Starting R2D2 Simulated Webcam System")

        self.is_running = True

        # Start capture thread
        self.capture_thread = threading.Thread(target=self.capture_frames)
        self.capture_thread.daemon = True
        self.capture_thread.start()

        logger.info("R2D2 Simulated Webcam System started successfully")
        return True

    def stop(self):
        """Stop the simulated webcam system"""
        logger.info("Stopping R2D2 Simulated Webcam System")

        self.is_running = False

        if self.capture_thread:
            self.capture_thread.join(timeout=2)

        # Clear frame queue
        while not self.frame_queue.empty():
            try:
                self.frame_queue.get_nowait()
            except queue.Empty:
                break

        logger.info("R2D2 Simulated Webcam System stopped")

async def main():
    """Main function to run the simulated webcam system"""
    # Create webcam system
    webcam_system = R2D2SimulatedWebcamSystem()

    # Setup signal handlers for graceful shutdown
    def signal_handler(signum, frame):
        logger.info("Received shutdown signal")
        webcam_system.stop()
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # Start webcam system
    if not webcam_system.start():
        logger.error("Failed to start simulated webcam system")
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
        logger.info("R2D2 Simulated Webcam System is running. Press Ctrl+C to stop.")
        logger.info("🎥 Dashboard URL: http://localhost:8765")
        logger.info("🔌 WebSocket URL: ws://localhost:8767")
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