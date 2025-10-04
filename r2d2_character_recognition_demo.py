#!/usr/bin/env python3
"""
R2D2 Character Recognition Demo System
=====================================

Demo version that generates simulated video and character detections
for testing dashboard integration without requiring camera access.
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
from typing import Dict, List, Any, Optional, Tuple
import queue
import sys
import os
import random

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class R2D2CharacterVisionDemoSystem:
    """Demo R2D2 vision system with simulated character detection"""

    def __init__(self, websocket_port=8767):
        self.websocket_port = websocket_port
        self.running = False

        # Queues for processing pipeline
        self.detection_queue = queue.Queue(maxsize=10)
        self.connected_clients = set()

        # Performance tracking
        self.performance_stats = {
            'fps': 15.0,
            'detection_time': 0.045,
            'character_time': 0.012,
            'total_detections': 0,
            'character_detections': 0,
            'confidence_threshold': 0.5
        }

        # Demo character database
        self.demo_characters = [
            {
                'name': 'Han Solo',
                'confidence': 0.87,
                'costume_match': 'han_smuggler',
                'r2d2_reaction': {
                    'primary_emotion': 'playful',
                    'secondary_emotions': ['curious'],
                    'relationship': 'ally'
                },
                'bbox': [150, 100, 350, 400]
            },
            {
                'name': 'Princess Leia',
                'confidence': 0.92,
                'costume_match': 'leia_white_dress',
                'r2d2_reaction': {
                    'primary_emotion': 'loyal',
                    'secondary_emotions': ['protective'],
                    'relationship': 'beloved_ally'
                },
                'bbox': [200, 80, 400, 380]
            },
            {
                'name': 'Luke Skywalker',
                'confidence': 0.89,
                'costume_match': 'jedi_robes',
                'r2d2_reaction': {
                    'primary_emotion': 'excited',
                    'secondary_emotions': ['loyal', 'protective'],
                    'relationship': 'beloved_ally'
                },
                'bbox': [100, 90, 300, 390]
            },
            {
                'name': 'Darth Vader',
                'confidence': 0.95,
                'costume_match': 'vader_black',
                'r2d2_reaction': {
                    'primary_emotion': 'concerned',
                    'secondary_emotions': ['alert'],
                    'relationship': 'enemy'
                },
                'bbox': [180, 70, 380, 420]
            },
            {
                'name': 'C-3PO',
                'confidence': 0.93,
                'costume_match': 'golden_droid',
                'r2d2_reaction': {
                    'primary_emotion': 'affectionate',
                    'secondary_emotions': ['playful'],
                    'relationship': 'companion'
                },
                'bbox': [220, 120, 320, 380]
            }
        ]

        self.current_character_index = 0
        self.frame_count = 0

    def _generate_demo_frame(self):
        """Generate a demo frame with simulated character"""
        # Create a simple demo frame
        frame = np.zeros((480, 640, 3), dtype=np.uint8)

        # Add background gradient
        for i in range(480):
            for j in range(640):
                frame[i, j] = [
                    int(50 + (i * 100 / 480)),  # Blue gradient
                    int(30 + (j * 80 / 640)),   # Green gradient
                    int(20 + ((i + j) * 60 / (480 + 640)))  # Red gradient
                ]

        # Add some "stars" for space background
        for _ in range(50):
            x = random.randint(0, 639)
            y = random.randint(0, 479)
            cv2.circle(frame, (x, y), 1, (255, 255, 255), -1)

        # Add title
        cv2.putText(frame, "R2D2 Character Recognition Demo", (50, 50),
                   cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)

        # Cycle through characters every 5 seconds (75 frames at 15 FPS)
        if self.frame_count % 75 == 0:
            self.current_character_index = (self.current_character_index + 1) % len(self.demo_characters)

        current_char = self.demo_characters[self.current_character_index]

        # Draw character simulation box
        x1, y1, x2, y2 = current_char['bbox']

        # Add some animation
        offset_x = int(10 * np.sin(self.frame_count * 0.1))
        offset_y = int(5 * np.cos(self.frame_count * 0.1))

        x1 += offset_x
        x2 += offset_x
        y1 += offset_y
        y2 += offset_y

        # Draw character box with faction color
        faction_colors = {
            'han_smuggler': (0, 255, 255),      # Yellow
            'leia_white_dress': (0, 255, 0),    # Green
            'jedi_robes': (255, 255, 0),        # Cyan
            'vader_black': (0, 0, 255),         # Red
            'golden_droid': (255, 0, 255)       # Magenta
        }

        color = faction_colors.get(current_char['costume_match'], (255, 255, 255))
        cv2.rectangle(frame, (x1, y1), (x2, y2), color, 3)

        # Add character name and confidence
        char_label = f"{current_char['name']} {current_char['confidence']:.2f}"
        label_size = cv2.getTextSize(char_label, cv2.FONT_HERSHEY_SIMPLEX, 0.7, 2)[0]

        # Background for label
        cv2.rectangle(frame, (x1, y1 - label_size[1] - 20), (x1 + label_size[0], y1), color, -1)
        cv2.putText(frame, char_label, (x1, y1 - 25), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 2)

        # Add costume info
        costume_label = f"Costume: {current_char['costume_match']}"
        cv2.putText(frame, costume_label, (x1, y1 - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 1)

        # Add R2D2 reaction
        reaction_text = f"R2D2: {current_char['r2d2_reaction']['primary_emotion']}"
        cv2.putText(frame, reaction_text, (x1, y2 + 15), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)

        # Add performance info
        cv2.putText(frame, f"FPS: {self.performance_stats['fps']:.1f}", (10, 100),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        cv2.putText(frame, "Persons: 1", (10, 130),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        cv2.putText(frame, "Characters: 1", (10, 160),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 0), 2)

        # Add demo notice
        cv2.putText(frame, "DEMO MODE - No Camera Required", (10, 400),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)

        # Update bbox for return
        current_char['bbox'] = [x1, y1, x2, y2]

        return frame, current_char

    def _generate_demo_data(self):
        """Generate demo detection data continuously"""
        logger.info("Starting demo data generation")

        while self.running:
            try:
                # Generate demo frame and character data
                frame, character_data = self._generate_demo_frame()

                # Create person detection
                x1, y1, x2, y2 = character_data['bbox']
                person_detection = {
                    'class': 'person',
                    'confidence': 0.85,
                    'bbox': [float(x1), float(y1), float(x2), float(y2)],
                    'class_id': 0
                }

                # Create character detection
                character_detection = {
                    'name': character_data['name'],
                    'confidence': character_data['confidence'],
                    'costume_match': character_data['costume_match'],
                    'character_data': {'faction': {'value': 'rebel_alliance'}},
                    'r2d2_reaction': character_data['r2d2_reaction'],
                    'person_bbox': character_data['bbox']
                }

                # Prepare data for WebSocket
                detection_data = {
                    'frame': frame,
                    'detections': [person_detection],
                    'character_detections': [character_detection],
                    'timestamp': datetime.now().isoformat(),
                    'stats': self.performance_stats.copy()
                }

                # Add to detection queue
                try:
                    self.detection_queue.put_nowait(detection_data)
                except queue.Full:
                    try:
                        self.detection_queue.get_nowait()
                        self.detection_queue.put_nowait(detection_data)
                    except queue.Empty:
                        pass

                self.frame_count += 1
                self.performance_stats['total_detections'] += 1
                self.performance_stats['character_detections'] += 1

                # Maintain 15 FPS
                time.sleep(1.0 / 15.0)

            except Exception as e:
                logger.error(f"Demo data generation error: {e}")
                break

    async def _handle_websocket_client(self, websocket):
        """Handle WebSocket client connections"""
        logger.info(f"New client connected: {websocket.remote_address}")
        self.connected_clients.add(websocket)

        try:
            await websocket.send(json.dumps({
                'type': 'connection_status',
                'status': 'connected',
                'message': 'R2D2 Character Recognition Demo System Connected',
                'character_count': len(self.demo_characters)
            }))

            # Handle incoming messages
            async def handle_incoming_messages():
                async for message in websocket:
                    try:
                        data = json.loads(message)
                        if data.get('type') == 'update_confidence':
                            threshold = data.get('threshold', 0.5)
                            self.performance_stats['confidence_threshold'] = threshold
                            logger.info(f"Updated confidence threshold to {threshold}")
                    except json.JSONDecodeError:
                        logger.warning("Received invalid JSON message")
                    except Exception as e:
                        logger.error(f"Error handling message: {e}")

            # Start message handler
            asyncio.create_task(handle_incoming_messages())

            # Send detection data
            while self.running:
                try:
                    detection_data = self.detection_queue.get(timeout=0.1)

                    # Encode frame
                    _, buffer = cv2.imencode('.jpg', detection_data['frame'],
                                           [cv2.IMWRITE_JPEG_QUALITY, 80])
                    frame_base64 = base64.b64encode(buffer).decode('utf-8')

                    # Prepare message
                    message = {
                        'type': 'character_vision_data',
                        'frame': frame_base64,
                        'detections': detection_data['detections'],
                        'character_detections': detection_data['character_detections'],
                        'timestamp': detection_data['timestamp'],
                        'stats': detection_data['stats']
                    }

                    await websocket.send(json.dumps(message))

                except queue.Empty:
                    # Send heartbeat
                    await websocket.send(json.dumps({
                        'type': 'heartbeat',
                        'timestamp': datetime.now().isoformat()
                    }))
                    await asyncio.sleep(0.1)

                except websockets.exceptions.ConnectionClosed:
                    break
                except Exception as e:
                    logger.error(f"WebSocket send error: {e}")
                    break

        except websockets.exceptions.ConnectionClosed:
            logger.info("Client disconnected")
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
            logger.info(f"R2D2 Character Recognition Demo WebSocket server running on port {self.websocket_port}")
            await asyncio.Future()  # Run forever

    def start(self):
        """Start the demo character recognition system"""
        logger.info("Starting R2D2 Character Recognition Demo System")
        logger.info("🎬 Demo Mode: Simulated video and character detection")
        logger.info("🎭 Characters: Han Solo, Princess Leia, Luke Skywalker, Darth Vader, C-3PO")

        self.running = True

        # Start demo data generation thread
        demo_thread = threading.Thread(target=self._generate_demo_data, daemon=True)
        demo_thread.start()

        logger.info(f"R2D2 Character Recognition Demo WebSocket server starting on port {self.websocket_port}")

        # Start WebSocket server
        try:
            asyncio.run(self._run_websocket_server())
        except KeyboardInterrupt:
            logger.info("Shutting down R2D2 Character Recognition Demo System")
        finally:
            self.stop()

        return True

    def stop(self):
        """Stop the demo character recognition system"""
        logger.info("Stopping R2D2 Character Recognition Demo System")
        self.running = False

        # Close WebSocket connections
        for client in self.connected_clients.copy():
            try:
                loop = asyncio.get_running_loop()
                loop.create_task(client.close())
            except RuntimeError:
                asyncio.run(client.close())


def main():
    """Main function to run the demo system"""
    print("R2D2 Star Wars Character Recognition Demo System")
    print("=" * 50)
    print("Features:")
    print("- Simulated real-time character detection")
    print("- 5 demo Star Wars characters with cycling display")
    print("- Full dashboard integration without camera requirement")
    print("- WebSocket streaming for dashboard testing")
    print("=" * 50)
    print("🎬 Demo Mode: No camera required!")
    print("🎭 Characters: Han Solo, Leia, Luke, Vader, C-3PO")
    print("Press Ctrl+C to stop")
    print("=" * 50)

    # Parse command line arguments
    port = 8767
    if len(sys.argv) > 1:
        try:
            port = int(sys.argv[1])
        except ValueError:
            logger.error("Invalid port number")
            sys.exit(1)

    # Create and start the demo system
    demo_system = R2D2CharacterVisionDemoSystem(websocket_port=port)

    try:
        success = demo_system.start()
        if not success:
            logger.error("Failed to start demo system")
            sys.exit(1)
    except KeyboardInterrupt:
        logger.info("Demo system stopped by user")
    except Exception as e:
        logger.error(f"Demo system error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()