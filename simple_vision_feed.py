#!/usr/bin/env python3
"""
Simple Vision Feed for Dashboard Testing
Sends real webcam frames via WebSocket on port 8767
"""
import asyncio
import websockets
import cv2
import base64
import json
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SimpleVisionFeed:
    def __init__(self):
        self.camera = None
        self.running = False

    def initialize_camera(self):
        """Initialize webcam"""
        try:
            self.camera = cv2.VideoCapture(0)
            self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            self.camera.set(cv2.CAP_PROP_FPS, 15)

            # Test read
            ret, frame = self.camera.read()
            if ret:
                logger.info(f"✅ Camera initialized: {frame.shape}")
                return True
            else:
                logger.error("❌ Failed to read from camera")
                return False
        except Exception as e:
            logger.error(f"❌ Camera initialization failed: {e}")
            return False

    async def handle_client(self, websocket):
        """Handle WebSocket client connection"""
        client_addr = websocket.remote_address
        logger.info(f"🔌 Client connected: {client_addr}")

        try:
            # Send connection confirmation
            await websocket.send(json.dumps({
                'type': 'connection_status',
                'status': 'connected',
                'message': 'Vision feed connected'
            }))

            # Send frames
            frame_count = 0
            while True:
                if self.camera is None or not self.camera.isOpened():
                    if not self.initialize_camera():
                        await asyncio.sleep(1)
                        continue

                # Capture frame
                ret, frame = self.camera.read()
                if not ret:
                    logger.warning("Failed to capture frame")
                    await asyncio.sleep(0.1)
                    continue

                # Encode frame to JPEG
                _, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
                frame_b64 = base64.b64encode(buffer).decode('utf-8')

                # Create message
                message = {
                    'type': 'vision_data',
                    'frame': frame_b64,
                    'stats': {
                        'fps': 15.0,
                        'detection_time': 0.05,
                        'total_detections': frame_count
                    },
                    'detections': []
                }

                # Send frame
                await websocket.send(json.dumps(message))
                frame_count += 1

                if frame_count % 30 == 0:
                    logger.info(f"📹 Sent {frame_count} frames")

                # Control frame rate
                await asyncio.sleep(1/15)  # 15 FPS

        except websockets.exceptions.ConnectionClosed:
            logger.info(f"🔌 Client disconnected: {client_addr}")
        except Exception as e:
            logger.error(f"❌ Error handling client: {e}")
        finally:
            if self.camera:
                self.camera.release()

    async def start_server(self):
        """Start WebSocket server"""
        logger.info("🚀 Starting Simple Vision Feed Server")
        logger.info("📡 WebSocket: ws://localhost:8767")

        # Initialize camera once
        if not self.initialize_camera():
            logger.error("Failed to initialize camera, exiting")
            return

        async with websockets.serve(self.handle_client, "0.0.0.0", 8767):
            logger.info("✅ Server running on port 8767")
            await asyncio.Future()  # Run forever

if __name__ == "__main__":
    feed = SimpleVisionFeed()
    try:
        asyncio.run(feed.start_server())
    except KeyboardInterrupt:
        logger.info("🛑 Server stopped by user")
    finally:
        if feed.camera:
            feed.camera.release()
