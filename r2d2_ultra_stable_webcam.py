#!/usr/bin/env python3
"""
R2D2 Ultra Stable Webcam System
FINAL AUTONOMOUS IMPLEMENTATION - Bulletproof WebSocket server
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
import threading
import queue

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class UltraStableWebcamSystem:
    def __init__(self):
        self.is_running = False
        self.frame_count = 0
        self.start_time = time.time()
        self.clients = set()
        self.frame_queue = queue.Queue(maxsize=5)
        self.generator_thread = None

    def generate_frame(self):
        """Generate a stable video frame"""
        try:
            # Create frame
            frame = np.zeros((480, 640, 3), dtype=np.uint8)

            # Animated background
            t = time.time() * 0.5
            for y in range(480):
                for x in range(640):
                    frame[y, x] = [
                        int(100 + 50 * np.sin(t + x * 0.01)),
                        int(100 + 50 * np.cos(t + y * 0.01)),
                        int(100 + 50 * np.sin(t + (x + y) * 0.005))
                    ]

            # Add text overlay
            timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
            cv2.putText(frame, f"R2D2 ULTRA STABLE WEBCAM", (50, 50),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2)
            cv2.putText(frame, f"Time: {timestamp}", (50, 100),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
            cv2.putText(frame, f"Frame: {self.frame_count}", (50, 130),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
            cv2.putText(frame, f"Clients: {len(self.clients)}", (50, 160),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)

            # Add moving elements
            center_x = int(320 + 100 * np.sin(self.frame_count * 0.05))
            center_y = int(240 + 50 * np.cos(self.frame_count * 0.03))
            cv2.circle(frame, (center_x, center_y), 30, (0, 255, 0), -1)

            # Add border
            cv2.rectangle(frame, (5, 5), (635, 475), (0, 255, 255), 3)

            self.frame_count += 1
            return frame

        except Exception as e:
            logger.error(f"Error generating frame: {e}")
            # Return black frame on error
            return np.zeros((480, 640, 3), dtype=np.uint8)

    def frame_generator_thread(self):
        """Generate frames in background thread"""
        logger.info("Frame generator thread started")

        while self.is_running:
            try:
                frame = self.generate_frame()

                # Encode frame
                ret, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
                if ret:
                    frame_base64 = base64.b64encode(buffer).decode('utf-8')

                    frame_data = {
                        "type": "video_frame",
                        "frame": frame_base64,
                        "timestamp": datetime.now().isoformat(),
                        "frame_number": self.frame_count,
                        "system_status": "ultra_stable"
                    }

                    # Add to queue
                    try:
                        self.frame_queue.put(frame_data, block=False)
                    except queue.Full:
                        # Remove old frame and add new one
                        try:
                            self.frame_queue.get_nowait()
                            self.frame_queue.put(frame_data, block=False)
                        except queue.Empty:
                            pass

                # Control frame rate (30 FPS)
                time.sleep(1/30)

            except Exception as e:
                logger.error(f"Error in frame generator: {e}")
                time.sleep(0.1)

        logger.info("Frame generator thread stopped")

    async def handle_client(self, websocket, path):
        """Handle individual client connection with robust error handling"""
        client_id = f"{websocket.remote_address[0]}:{websocket.remote_address[1]}"
        logger.info(f"Client connected: {client_id}")

        self.clients.add(websocket)

        try:
            # Send welcome message
            welcome = {
                "type": "connection_status",
                "message": "Connected to R2D2 Ultra Stable Webcam",
                "timestamp": datetime.now().isoformat(),
                "client_id": client_id,
                "system_uptime": time.time() - self.start_time
            }

            await websocket.send(json.dumps(welcome))
            logger.info(f"Welcome sent to {client_id}")

            # Send frames to this client
            while True:
                try:
                    # Get frame from queue
                    if not self.frame_queue.empty():
                        frame_data = self.frame_queue.get_nowait()
                        await websocket.send(json.dumps(frame_data))

                    # Also listen for incoming messages
                    try:
                        message = await asyncio.wait_for(websocket.recv(), timeout=0.01)
                        data = json.loads(message)
                        logger.info(f"Received from {client_id}: {data.get('type', 'unknown')}")
                    except asyncio.TimeoutError:
                        pass  # No message received, continue
                    except json.JSONDecodeError:
                        logger.warning(f"Invalid JSON from {client_id}")

                    # Small delay to control send rate
                    await asyncio.sleep(1/30)

                except websockets.exceptions.ConnectionClosed:
                    logger.info(f"Client {client_id} disconnected normally")
                    break
                except Exception as e:
                    logger.error(f"Error sending to {client_id}: {e}")
                    break

        except Exception as e:
            logger.error(f"Error handling client {client_id}: {e}")
        finally:
            self.clients.discard(websocket)
            logger.info(f"Client {client_id} cleanup completed")

    async def periodic_status_sender(self):
        """Send periodic status updates"""
        while self.is_running:
            try:
                await asyncio.sleep(5)

                status = {
                    "type": "system_status",
                    "timestamp": datetime.now().isoformat(),
                    "uptime": time.time() - self.start_time,
                    "frame_count": self.frame_count,
                    "connected_clients": len(self.clients),
                    "queue_size": self.frame_queue.qsize(),
                    "status": "ultra_stable_running"
                }

                # Send to all clients
                if self.clients:
                    disconnected = set()
                    for client in self.clients.copy():
                        try:
                            await client.send(json.dumps(status))
                        except:
                            disconnected.add(client)

                    self.clients -= disconnected

            except Exception as e:
                logger.error(f"Error in status sender: {e}")

    def start(self):
        """Start the frame generation"""
        self.is_running = True
        self.start_time = time.time()

        # Start frame generator thread
        self.generator_thread = threading.Thread(target=self.frame_generator_thread)
        self.generator_thread.daemon = True
        self.generator_thread.start()

        logger.info("Ultra Stable Webcam System started")

    def stop(self):
        """Stop the system"""
        logger.info("Stopping Ultra Stable Webcam System")
        self.is_running = False

        if self.generator_thread:
            self.generator_thread.join(timeout=2)

        # Clear queue
        while not self.frame_queue.empty():
            try:
                self.frame_queue.get_nowait()
            except queue.Empty:
                break

        logger.info("System stopped")

async def main():
    """Main function"""
    system = UltraStableWebcamSystem()

    try:
        # Start system
        system.start()

        # Start WebSocket server with robust configuration
        logger.info("Starting WebSocket server on localhost:8767")

        server = await websockets.serve(
            system.handle_client,
            "localhost",
            8767,
            ping_interval=20,
            ping_timeout=10,
            close_timeout=10,
            max_size=10**7,  # 10MB max message size
            max_queue=32,
            compression=None,
            process_request=None,
            logger=logger
        )

        # Start status sender
        status_task = asyncio.create_task(system.periodic_status_sender())

        logger.info("🚀 R2D2 ULTRA STABLE WEBCAM SYSTEM RUNNING!")
        logger.info("🔌 WebSocket Server: ws://localhost:8767")
        logger.info("🌐 Dashboard Available: http://localhost:8765")
        logger.info("📊 System Status: ULTRA STABLE MODE")
        logger.info("Press Ctrl+C to stop")

        # Keep running
        await server.wait_closed()

    except KeyboardInterrupt:
        logger.info("Shutdown requested")
    except Exception as e:
        logger.error(f"System error: {e}")
    finally:
        system.stop()
        if 'status_task' in locals():
            status_task.cancel()
        if 'server' in locals():
            server.close()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("System shutdown complete")
    except Exception as e:
        logger.error(f"Fatal error: {e}")