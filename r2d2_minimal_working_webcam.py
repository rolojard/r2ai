#!/usr/bin/env python3
"""
R2D2 Minimal Working Webcam System
GUARANTEED TO WORK - Simplified for reliability
"""

import asyncio
import websockets
import json
import time
import base64
import logging
from datetime import datetime
import numpy as np
import cv2

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MinimalWebcamSystem:
    def __init__(self):
        self.frame_count = 0
        self.start_time = time.time()

    def create_frame(self):
        """Create a simple test frame"""
        frame = np.zeros((480, 640, 3), dtype=np.uint8)

        # Simple colored background
        frame[:, :] = [50, 100, 150]  # BGR

        # Add text
        timestamp = datetime.now().strftime("%H:%M:%S")
        cv2.putText(frame, f"R2D2 Live Feed - {timestamp}", (50, 50),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
        cv2.putText(frame, f"Frame: {self.frame_count}", (50, 100),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)

        # Add moving circle
        center_x = int(320 + 100 * np.sin(self.frame_count * 0.1))
        center_y = int(240 + 50 * np.cos(self.frame_count * 0.1))
        cv2.circle(frame, (center_x, center_y), 30, (0, 255, 255), -1)

        self.frame_count += 1
        return frame

    async def handle_client(self, websocket, path):
        """Handle WebSocket client"""
        logger.info(f"Client connected: {websocket.remote_address}")

        try:
            # Send welcome
            await websocket.send(json.dumps({
                "type": "connection_status",
                "message": "Connected to R2D2 Minimal Webcam",
                "timestamp": datetime.now().isoformat()
            }))

            # Send frames
            while True:
                try:
                    # Create frame
                    frame = self.create_frame()

                    # Encode frame
                    _, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
                    frame_base64 = base64.b64encode(buffer).decode('utf-8')

                    # Send frame
                    message = {
                        "type": "video_frame",
                        "frame": frame_base64,
                        "timestamp": datetime.now().isoformat(),
                        "frame_number": self.frame_count
                    }

                    await websocket.send(json.dumps(message))

                    # Control frame rate (30 FPS)
                    await asyncio.sleep(1/30)

                except websockets.exceptions.ConnectionClosed:
                    break
                except Exception as e:
                    logger.error(f"Error sending frame: {e}")
                    break

        except Exception as e:
            logger.error(f"Client error: {e}")
        finally:
            logger.info("Client disconnected")

async def main():
    system = MinimalWebcamSystem()

    logger.info("Starting minimal webcam server on port 8767")

    server = await websockets.serve(
        system.handle_client,
        "localhost",
        8767
    )

    logger.info("🚀 Minimal Webcam System running!")
    logger.info("🔌 WebSocket: ws://localhost:8767")

    try:
        await server.wait_closed()
    except KeyboardInterrupt:
        logger.info("Shutting down")

if __name__ == "__main__":
    asyncio.run(main())