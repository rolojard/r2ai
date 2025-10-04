#!/usr/bin/env python3
"""
Simulated Camera Vision System for Dashboard Testing
Creates synthetic video frames for testing the dashboard video functionality
"""

import cv2
import numpy as np
import json
import time
import threading
import base64
import asyncio
import websockets
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SimulatedCameraVision:
    """Simulated camera vision system for dashboard testing"""

    def __init__(self, websocket_port=8767):
        self.websocket_port = websocket_port
        self.running = False
        self.connected_clients = set()
        self.max_clients = 10

        # Simulation parameters
        self.frame_width = 640
        self.frame_height = 480
        self.frame_rate = 15
        self.frame_count = 0

        # Performance tracking
        self.stats = {
            'fps': 0,
            'total_frames': 0,
            'detection_time': 0.05,  # Simulated detection time
            'total_detections': 0
        }

        # Simulated detections
        self.detection_classes = ['person', 'car', 'dog', 'cat', 'bicycle', 'bottle', 'chair', 'cup']
        self.last_detection_time = time.time()

    def _generate_synthetic_frame(self):
        """Generate a synthetic video frame with overlays"""
        # Create base frame with gradient background
        frame = np.zeros((self.frame_height, self.frame_width, 3), dtype=np.uint8)

        # Create animated gradient background
        t = time.time() * 0.5
        for y in range(self.frame_height):
            for x in range(self.frame_width):
                r = int(128 + 64 * np.sin(t + x * 0.01))
                g = int(128 + 64 * np.sin(t + y * 0.01 + 2))
                b = int(128 + 64 * np.sin(t + (x + y) * 0.005 + 4))
                frame[y, x] = [max(0, min(255, b)), max(0, min(255, g)), max(0, min(255, r))]

        # Add R2D2 logo/text
        cv2.putText(frame, "R2D2 VISION SYSTEM", (50, 50), cv2.FONT_HERSHEY_SIMPLEX,
                   1.2, (255, 255, 255), 2)

        # Add timestamp
        timestamp = datetime.now().strftime("%H:%M:%S")
        cv2.putText(frame, f"TIME: {timestamp}", (50, 100), cv2.FONT_HERSHEY_SIMPLEX,
                   0.8, (200, 200, 200), 2)

        # Add frame counter
        cv2.putText(frame, f"FRAME: {self.frame_count}", (50, 130), cv2.FONT_HERSHEY_SIMPLEX,
                   0.8, (200, 200, 200), 2)

        # Add simulated moving objects
        self._add_moving_objects(frame)

        # Add system status overlay
        cv2.putText(frame, "STATUS: SIMULATED", (450, 50), cv2.FONT_HERSHEY_SIMPLEX,
                   0.6, (0, 255, 0), 2)

        return frame

    def _add_moving_objects(self, frame):
        """Add simulated moving objects to the frame"""
        t = time.time()

        # Moving circle (simulated object)
        center_x = int(320 + 200 * np.sin(t * 0.5))
        center_y = int(240 + 100 * np.cos(t * 0.3))
        cv2.circle(frame, (center_x, center_y), 30, (0, 255, 255), -1)
        cv2.putText(frame, "OBJECT", (center_x - 30, center_y - 40),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)

        # Moving rectangle (another simulated object)
        rect_x = int(100 + 150 * np.sin(t * 0.8 + 1))
        rect_y = int(200 + 80 * np.cos(t * 0.6))
        cv2.rectangle(frame, (rect_x, rect_y), (rect_x + 60, rect_y + 40), (255, 0, 255), -1)

    def _generate_simulated_detections(self):
        """Generate simulated object detections"""
        detections = []

        # Generate 1-3 random detections
        num_detections = np.random.randint(0, 4)

        for i in range(num_detections):
            # Random bounding box
            x1 = np.random.randint(0, self.frame_width // 2)
            y1 = np.random.randint(0, self.frame_height // 2)
            x2 = x1 + np.random.randint(50, 150)
            y2 = y1 + np.random.randint(30, 100)

            # Ensure within frame bounds
            x2 = min(x2, self.frame_width)
            y2 = min(y2, self.frame_height)

            detection = {
                'class': np.random.choice(self.detection_classes),
                'confidence': np.random.uniform(0.6, 0.95),
                'bbox': [x1, y1, x2, y2]
            }

            detections.append(detection)

        return detections

    def _frame_to_base64(self, frame):
        """Convert frame to base64 string"""
        try:
            # Encode frame as JPEG
            ret, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
            if ret:
                jpg_as_text = base64.b64encode(buffer).decode('utf-8')
                return jpg_as_text
            return None
        except Exception as e:
            logger.error(f"Frame encoding error: {e}")
            return None

    async def _handle_websocket_client(self, websocket):
        """Handle WebSocket client connections"""
        client_addr = websocket.remote_address

        # Enforce connection limit
        if len(self.connected_clients) >= self.max_clients:
            logger.warning(f"Connection limit reached. Rejecting: {client_addr}")
            await websocket.close(code=1013, reason="Server busy")
            return

        logger.info(f"Client connected: {client_addr}")
        self.connected_clients.add(websocket)

        try:
            # Send connection confirmation
            await websocket.send(json.dumps({
                'type': 'connection_status',
                'status': 'connected',
                'message': 'R2D2 Simulated Vision Connected',
                'simulation': True
            }))

            # Main streaming loop
            frame_start_time = time.time()

            while self.running:
                try:
                    # Generate synthetic frame
                    frame = self._generate_synthetic_frame()

                    # Convert to base64
                    frame_b64 = self._frame_to_base64(frame)

                    if frame_b64:
                        # Generate simulated detections
                        detections = self._generate_simulated_detections()

                        # Update stats
                        current_time = time.time()
                        frame_time = current_time - frame_start_time
                        self.stats['fps'] = 1.0 / frame_time if frame_time > 0 else 0
                        self.stats['total_frames'] += 1
                        self.stats['total_detections'] += len(detections)

                        # Create message
                        message = {
                            'type': 'vision_data',
                            'frame': frame_b64,
                            'detections': detections,
                            'timestamp': datetime.now().isoformat(),
                            'stats': self.stats.copy(),
                            'simulation': True
                        }

                        # Send to client
                        await websocket.send(json.dumps(message))

                        self.frame_count += 1
                        frame_start_time = current_time

                    # Control frame rate
                    await asyncio.sleep(1.0 / self.frame_rate)

                except websockets.exceptions.ConnectionClosed:
                    break
                except Exception as e:
                    logger.error(f"WebSocket send error: {e}")
                    break

        except websockets.exceptions.ConnectionClosed:
            logger.info(f"Client disconnected: {client_addr}")
        except Exception as e:
            logger.error(f"WebSocket client error: {e}")
        finally:
            self.connected_clients.discard(websocket)

    async def _run_websocket_server(self):
        """Run the WebSocket server"""
        async with websockets.serve(
            self._handle_websocket_client,
            "localhost",
            self.websocket_port
        ):
            logger.info(f"Simulated Vision WebSocket server running on port {self.websocket_port}")
            await asyncio.Future()  # Run forever

    def start(self):
        """Start the simulated vision system"""
        logger.info("Starting R2D2 Simulated Vision System")
        logger.info("This system generates synthetic video frames for dashboard testing")

        self.running = True

        try:
            asyncio.run(self._run_websocket_server())
        except KeyboardInterrupt:
            logger.info("Shutting down Simulated Vision System")
        finally:
            self.stop()

        return True

    def stop(self):
        """Stop the simulated vision system"""
        logger.info("Stopping R2D2 Simulated Vision System")
        self.running = False

def main():
    """Main function"""
    print("🎯 R2D2 Simulated Vision System")
    print("=" * 40)
    print("Synthetic video frames for dashboard testing")
    print("Press Ctrl+C to stop")
    print("=" * 40)

    # Create and start simulated vision system
    vision_system = SimulatedCameraVision(websocket_port=8767)

    try:
        success = vision_system.start()
        if not success:
            logger.error("Failed to start simulated vision system")
            return False
    except KeyboardInterrupt:
        logger.info("Simulated vision system stopped by user")
    except Exception as e:
        logger.error(f"Simulated vision system error: {e}")
        return False

    return True

if __name__ == "__main__":
    main()