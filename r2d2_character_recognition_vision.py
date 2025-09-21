#!/usr/bin/env python3
"""
R2D2 Star Wars Character Recognition System
==========================================

Enhanced real-time vision system with Star Wars character recognition,
costume detection, and authentic R2D2 reactions based on canon relationships.

Features:
- 17 Star Wars character database integration
- HSV color-based costume detection
- Character-specific R2D2 reactions
- Real-time person + character detection
- Dashboard integration with character display
- Optimized for 15+ FPS performance
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
import colorsys

# Import our Star Wars character database
from star_wars_character_database import create_star_wars_character_database, create_reaction_sound_library
from star_wars_character_database_schema import *

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class StarWarsCharacterRecognizer:
    """Advanced Star Wars character recognition using visual features and costume analysis"""

    def __init__(self):
        self.character_db = create_star_wars_character_database()
        self.sound_library = create_reaction_sound_library()
        self.costume_detectors = self._create_costume_detectors()
        self.character_history = {}  # Track character recognition over time

    def _create_costume_detectors(self) -> Dict[str, Dict]:
        """Create HSV color-based costume detectors for major characters"""
        return {
            # Jedi Robes - Brown/Tan colors
            "jedi_robes": {
                "hsv_ranges": [
                    # Brown range
                    {"lower": np.array([10, 50, 20]), "upper": np.array([20, 255, 200])},
                    # Tan range
                    {"lower": np.array([15, 30, 100]), "upper": np.array([25, 150, 255])}
                ],
                "min_area": 5000,
                "characters": ["Luke Skywalker", "Obi-Wan Kenobi", "Qui-Gon Jinn", "Mace Windu", "Rey"],
                "confidence_boost": 0.3
            },

            # Stormtrooper Armor - White
            "stormtrooper_armor": {
                "hsv_ranges": [
                    {"lower": np.array([0, 0, 200]), "upper": np.array([180, 30, 255])}
                ],
                "min_area": 8000,
                "characters": ["Stormtrooper", "Finn"],  # Finn as former stormtrooper
                "confidence_boost": 0.4
            },

            # Darth Vader - Black armor/cape
            "vader_black": {
                "hsv_ranges": [
                    {"lower": np.array([0, 0, 0]), "upper": np.array([180, 255, 50])}
                ],
                "min_area": 6000,
                "characters": ["Darth Vader", "Kylo Ren"],
                "confidence_boost": 0.4
            },

            # Princess Leia - White dress
            "leia_white_dress": {
                "hsv_ranges": [
                    {"lower": np.array([0, 0, 200]), "upper": np.array([180, 30, 255])}
                ],
                "min_area": 4000,
                "characters": ["Leia Organa"],
                "confidence_boost": 0.3
            },

            # Han Solo - White shirt/dark vest
            "han_smuggler": {
                "hsv_ranges": [
                    # White shirt
                    {"lower": np.array([0, 0, 180]), "upper": np.array([180, 40, 255])},
                    # Dark vest/jacket
                    {"lower": np.array([0, 0, 0]), "upper": np.array([180, 255, 80])}
                ],
                "min_area": 3000,
                "characters": ["Han Solo"],
                "confidence_boost": 0.25
            },

            # Resistance Orange (Pilot suits)
            "resistance_orange": {
                "hsv_ranges": [
                    {"lower": np.array([10, 100, 100]), "upper": np.array([25, 255, 255])}
                ],
                "min_area": 3000,
                "characters": ["Poe Dameron", "Luke Skywalker"],  # Luke as pilot
                "confidence_boost": 0.3
            },

            # C-3PO Gold
            "golden_droid": {
                "hsv_ranges": [
                    {"lower": np.array([20, 100, 100]), "upper": np.array([30, 255, 255])}
                ],
                "min_area": 4000,
                "characters": ["C-3PO"],
                "confidence_boost": 0.5
            },

            # BB-8 Orange and White
            "bb8_orange_white": {
                "hsv_ranges": [
                    {"lower": np.array([10, 120, 120]), "upper": np.array([25, 255, 255])},  # Orange
                    {"lower": np.array([0, 0, 200]), "upper": np.array([180, 30, 255])}     # White
                ],
                "min_area": 1000,
                "characters": ["BB-8"],
                "confidence_boost": 0.4
            }
        }

    def detect_costume_features(self, image: np.ndarray, person_bbox: Tuple[int, int, int, int]) -> Dict[str, float]:
        """Detect costume features within person bounding box"""
        x1, y1, x2, y2 = person_bbox
        person_roi = image[y1:y2, x1:x2]

        if person_roi.size == 0:
            return {}

        # Convert to HSV for better color detection
        hsv_roi = cv2.cvtColor(person_roi, cv2.COLOR_BGR2HSV)

        costume_scores = {}

        for costume_name, detector in self.costume_detectors.items():
            total_mask_area = 0

            for hsv_range in detector["hsv_ranges"]:
                # Create mask for this color range
                mask = cv2.inRange(hsv_roi, hsv_range["lower"], hsv_range["upper"])

                # Apply morphological operations to clean up mask
                kernel = np.ones((3,3), np.uint8)
                mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
                mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)

                total_mask_area += cv2.countNonZero(mask)

            # Calculate confidence based on area coverage
            roi_area = person_roi.shape[0] * person_roi.shape[1]
            coverage_ratio = total_mask_area / roi_area if roi_area > 0 else 0

            # Apply minimum area threshold
            if total_mask_area >= detector["min_area"]:
                costume_scores[costume_name] = min(coverage_ratio * 2.0, 1.0)  # Scale and cap at 1.0

        return costume_scores

    def recognize_character(self, image: np.ndarray, person_bbox: Tuple[int, int, int, int],
                          person_confidence: float) -> Optional[Dict[str, Any]]:
        """Attempt to recognize Star Wars character from person detection"""

        # Detect costume features
        costume_scores = self.detect_costume_features(image, person_bbox)

        if not costume_scores:
            return None

        # Find best character matches based on costume detection
        character_candidates = {}

        for costume_name, costume_confidence in costume_scores.items():
            if costume_confidence > 0.1:  # Minimum threshold
                detector = self.costume_detectors[costume_name]
                confidence_boost = detector["confidence_boost"]

                for character_name in detector["characters"]:
                    character = self.character_db.get_character(character_name)
                    if character:
                        # Calculate combined confidence
                        base_confidence = person_confidence * costume_confidence
                        boosted_confidence = base_confidence + confidence_boost
                        final_confidence = min(boosted_confidence, 1.0)

                        # Apply character-specific confidence modifier
                        final_confidence *= character.r2d2_reaction.confidence_modifier

                        # Only consider if above character's threshold
                        if final_confidence >= character.confidence_threshold:
                            if character_name not in character_candidates:
                                character_candidates[character_name] = {
                                    'confidence': final_confidence,
                                    'costume_match': costume_name,
                                    'character': character
                                }
                            else:
                                # Take higher confidence
                                if final_confidence > character_candidates[character_name]['confidence']:
                                    character_candidates[character_name]['confidence'] = final_confidence
                                    character_candidates[character_name]['costume_match'] = costume_name

        if not character_candidates:
            return None

        # Select best candidate
        best_character_name = max(character_candidates.keys(),
                                key=lambda x: character_candidates[x]['confidence'])
        best_match = character_candidates[best_character_name]

        # Update character history for temporal consistency
        self._update_character_history(best_character_name, best_match['confidence'])

        return {
            'name': best_character_name,
            'confidence': best_match['confidence'],
            'costume_match': best_match['costume_match'],
            'character_data': best_match['character'],
            'r2d2_reaction': self._generate_r2d2_reaction(best_match['character'])
        }

    def _update_character_history(self, character_name: str, confidence: float):
        """Update character recognition history for temporal consistency"""
        current_time = time.time()

        if character_name not in self.character_history:
            self.character_history[character_name] = []

        # Add current detection
        self.character_history[character_name].append({
            'timestamp': current_time,
            'confidence': confidence
        })

        # Clean old entries (keep last 30 seconds)
        self.character_history[character_name] = [
            entry for entry in self.character_history[character_name]
            if current_time - entry['timestamp'] < 30.0
        ]

    def _generate_r2d2_reaction(self, character: StarWarsCharacter) -> Dict[str, Any]:
        """Generate appropriate R2D2 reaction for recognized character"""
        reaction = character.r2d2_reaction
        sound_info = self.sound_library.get(reaction.primary_emotion, {})

        return {
            'primary_emotion': reaction.primary_emotion.value,
            'secondary_emotions': [e.value for e in reaction.secondary_emotions],
            'sound_pattern': reaction.sound_pattern,
            'behavioral_notes': reaction.behavioral_notes,
            'sound_details': sound_info,
            'relationship': character.relationship_to_r2d2.value,
            'trust_level': character.trust_level,
            'priority': character.recognition_priority
        }


class R2D2CharacterVisionSystem:
    """Enhanced R2D2 vision system with Star Wars character recognition"""

    def __init__(self, websocket_port=8767, camera_index=0):
        self.websocket_port = websocket_port
        self.camera_index = camera_index
        self.running = False
        self.camera = None
        self.yolo_model = None
        self.character_recognizer = StarWarsCharacterRecognizer()

        # Queues for processing pipeline
        self.frame_queue = queue.Queue(maxsize=2)
        self.detection_queue = queue.Queue(maxsize=10)
        self.connected_clients = set()

        # Performance tracking
        self.performance_stats = {
            'fps': 0,
            'detection_time': 0,
            'character_time': 0,
            'total_detections': 0,
            'character_detections': 0,
            'confidence_threshold': 0.5
        }

        # Character recognition state
        self.last_character_detections = {}
        self.character_reaction_cooldown = {}  # Prevent spam reactions

        # Initialize models
        self._load_yolo_model()

    def _load_yolo_model(self):
        """Load YOLO model for person detection"""
        try:
            from ultralytics import YOLO
            logger.info("Loading YOLOv8 model for person detection...")

            self.yolo_model = YOLO('yolov8n.pt')

            # Move to GPU if available
            import torch
            if torch.cuda.is_available():
                self.yolo_model.to('cuda')
                logger.info("YOLO model loaded on GPU")
            else:
                logger.info("YOLO model loaded on CPU")

            # Optimize for real-time performance
            self.yolo_model.overrides['verbose'] = False
            self.yolo_model.overrides['conf'] = 0.5
            self.yolo_model.overrides['iou'] = 0.45
            self.yolo_model.overrides['classes'] = [0]  # Only detect persons (class 0)

        except Exception as e:
            logger.error(f"Failed to load YOLO model: {e}")
            self.yolo_model = None

    def _initialize_camera(self):
        """Initialize camera capture"""
        try:
            self.camera = cv2.VideoCapture(self.camera_index)

            if not self.camera.isOpened():
                logger.error("Failed to open camera")
                return False

            # Optimize camera settings for performance
            self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            self.camera.set(cv2.CAP_PROP_FPS, 30)
            self.camera.set(cv2.CAP_PROP_BUFFERSIZE, 1)

            # Test capture
            ret, frame = self.camera.read()
            if not ret:
                logger.error("Failed to read from camera")
                return False

            logger.info(f"Camera initialized: {frame.shape}")
            return True

        except Exception as e:
            logger.error(f"Camera initialization failed: {e}")
            return False

    def _capture_frames(self):
        """Continuous frame capture thread"""
        logger.info("Starting frame capture thread")
        frame_count = 0
        start_time = time.time()

        while self.running:
            try:
                ret, frame = self.camera.read()
                if not ret:
                    logger.warning("Failed to capture frame")
                    continue

                # Calculate FPS
                frame_count += 1
                if frame_count % 30 == 0:
                    elapsed = time.time() - start_time
                    self.performance_stats['fps'] = frame_count / elapsed

                # Add to queue (non-blocking)
                try:
                    self.frame_queue.put_nowait(frame.copy())
                except queue.Full:
                    # Remove old frame and add new one
                    try:
                        self.frame_queue.get_nowait()
                        self.frame_queue.put_nowait(frame.copy())
                    except queue.Empty:
                        pass

                time.sleep(0.01)  # Prevent overwhelming

            except Exception as e:
                logger.error(f"Frame capture error: {e}")
                break

    def _process_detections(self):
        """Process YOLO detections and character recognition"""
        logger.info("Starting detection processing thread")

        while self.running:
            try:
                # Get frame from queue
                frame = self.frame_queue.get(timeout=1.0)

                if self.yolo_model is None:
                    continue

                # Run YOLO person detection
                start_time = time.time()
                results = self.yolo_model(frame, verbose=False)
                detection_time = time.time() - start_time

                # Process YOLO results
                detections = []
                character_detections = []

                if results and len(results) > 0:
                    result = results[0]

                    if result.boxes is not None:
                        boxes = result.boxes.cpu().numpy()

                        for box in boxes:
                            x1, y1, x2, y2 = box.xyxy[0]
                            confidence = box.conf[0]
                            class_id = int(box.cls[0])
                            class_name = self.yolo_model.names[class_id]

                            if confidence >= self.performance_stats['confidence_threshold']:
                                person_detection = {
                                    'class': class_name,
                                    'confidence': float(confidence),
                                    'bbox': [float(x1), float(y1), float(x2), float(y2)],
                                    'class_id': class_id
                                }
                                detections.append(person_detection)

                                # Attempt character recognition for person detections
                                if class_name == 'person':
                                    char_start_time = time.time()
                                    character_result = self.character_recognizer.recognize_character(
                                        frame, (int(x1), int(y1), int(x2), int(y2)), confidence
                                    )
                                    char_time = time.time() - char_start_time

                                    if character_result:
                                        character_result['person_bbox'] = person_detection['bbox']
                                        character_detections.append(character_result)
                                        self.performance_stats['character_detections'] += 1

                                        # Log significant character detections
                                        char_name = character_result['name']
                                        char_conf = character_result['confidence']
                                        if char_conf > 0.7:
                                            logger.info(f"Character detected: {char_name} (confidence: {char_conf:.2f})")

                # Draw annotations on frame
                annotated_frame = self._draw_detections(frame, detections, character_detections)

                # Update performance stats
                self.performance_stats['detection_time'] = detection_time
                if character_detections:
                    self.performance_stats['character_time'] = char_time

                # Prepare data for WebSocket
                detection_data = {
                    'frame': annotated_frame,
                    'detections': detections,
                    'character_detections': character_detections,
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

                self.performance_stats['total_detections'] += len(detections)

            except queue.Empty:
                continue
            except Exception as e:
                logger.error(f"Detection processing error: {e}")

    def _draw_detections(self, frame, detections, character_detections):
        """Draw detection boxes and character information on frame"""
        annotated_frame = frame.copy()

        # Draw person detections
        for detection in detections:
            x1, y1, x2, y2 = detection['bbox']
            confidence = detection['confidence']
            class_name = detection['class']

            # Default person detection color
            color = (0, 255, 0)
            cv2.rectangle(annotated_frame, (int(x1), int(y1)), (int(x2), int(y2)), color, 2)

            label = f"{class_name} {confidence:.2f}"
            cv2.putText(annotated_frame, label, (int(x1), int(y1) - 10),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)

        # Draw character detections (overlay on person detections)
        for char_detection in character_detections:
            x1, y1, x2, y2 = char_detection['person_bbox']
            char_name = char_detection['name']
            char_conf = char_detection['confidence']
            costume = char_detection['costume_match']

            # Character detection gets special color based on faction
            character_data = char_detection['character_data']
            faction_colors = {
                'jedi': (255, 255, 0),      # Yellow for Jedi
                'sith': (0, 0, 255),        # Red for Sith
                'rebel_alliance': (0, 255, 0),  # Green for Rebels
                'resistance': (0, 255, 0),      # Green for Resistance
                'droid': (255, 0, 255),         # Magenta for Droids
                'galactic_empire': (128, 0, 128)  # Purple for Empire
            }

            faction = character_data.faction.value
            char_color = faction_colors.get(faction, (255, 255, 255))

            # Draw enhanced character box
            cv2.rectangle(annotated_frame, (int(x1), int(y1)), (int(x2), int(y2)), char_color, 3)

            # Character name and confidence
            char_label = f"{char_name} {char_conf:.2f}"
            label_size = cv2.getTextSize(char_label, cv2.FONT_HERSHEY_SIMPLEX, 0.7, 2)[0]

            # Background for character label
            cv2.rectangle(annotated_frame,
                         (int(x1), int(y1) - label_size[1] - 20),
                         (int(x1) + label_size[0], int(y1)),
                         char_color, -1)

            # Character name
            cv2.putText(annotated_frame, char_label,
                       (int(x1), int(y1) - 25),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 2)

            # Costume info
            costume_label = f"Costume: {costume}"
            cv2.putText(annotated_frame, costume_label,
                       (int(x1), int(y1) - 5),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 1)

            # R2D2 reaction indicator
            reaction = char_detection['r2d2_reaction']
            reaction_text = f"R2D2: {reaction['primary_emotion']}"
            cv2.putText(annotated_frame, reaction_text,
                       (int(x1), int(y2) + 15),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, char_color, 2)

        # Add performance info
        fps_text = f"FPS: {self.performance_stats['fps']:.1f}"
        detection_text = f"Persons: {len(detections)}"
        character_text = f"Characters: {len(character_detections)}"

        cv2.putText(annotated_frame, fps_text, (10, 30),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        cv2.putText(annotated_frame, detection_text, (10, 60),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        cv2.putText(annotated_frame, character_text, (10, 90),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 0), 2)

        return annotated_frame

    async def _handle_websocket_client(self, websocket):
        """Handle WebSocket client connections"""
        logger.info(f"New client connected: {websocket.remote_address}")
        self.connected_clients.add(websocket)

        try:
            await websocket.send(json.dumps({
                'type': 'connection_status',
                'status': 'connected',
                'message': 'R2D2 Character Recognition System Connected',
                'character_count': len(self.character_recognizer.character_db.characters)
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
            logger.info(f"R2D2 Character Recognition WebSocket server running on port {self.websocket_port}")
            await asyncio.Future()  # Run forever

    def start(self):
        """Start the R2D2 character recognition system"""
        logger.info("Starting R2D2 Character Recognition System")

        # Initialize camera
        if not self._initialize_camera():
            logger.error("Failed to initialize camera")
            return False

        if self.yolo_model is None:
            logger.error("YOLO model not available")
            return False

        # Log character database stats
        stats = self.character_recognizer.character_db.get_database_stats()
        logger.info(f"Loaded {stats['total_characters']} Star Wars characters")
        logger.info(f"High priority characters: {stats['high_priority_count']}")

        self.running = True

        # Start processing threads
        capture_thread = threading.Thread(target=self._capture_frames, daemon=True)
        capture_thread.start()

        detection_thread = threading.Thread(target=self._process_detections, daemon=True)
        detection_thread.start()

        logger.info(f"R2D2 Character Recognition WebSocket server starting on port {self.websocket_port}")

        # Start WebSocket server
        try:
            asyncio.run(self._run_websocket_server())
        except KeyboardInterrupt:
            logger.info("Shutting down R2D2 Character Recognition System")
        finally:
            self.stop()

        return True

    def stop(self):
        """Stop the character recognition system"""
        logger.info("Stopping R2D2 Character Recognition System")
        self.running = False

        if self.camera:
            self.camera.release()

        # Close WebSocket connections
        for client in self.connected_clients.copy():
            try:
                loop = asyncio.get_running_loop()
                loop.create_task(client.close())
            except RuntimeError:
                asyncio.run(client.close())


def main():
    """Main function to run the R2D2 character recognition system"""
    print("R2D2 Star Wars Character Recognition System")
    print("=" * 50)
    print("Features:")
    print("- Real-time person detection with YOLO")
    print("- Star Wars character recognition via costume analysis")
    print("- 17 character database with canonical relationships")
    print("- Authentic R2D2 reactions based on character bonds")
    print("- WebSocket streaming for dashboard integration")
    print("=" * 50)
    print("Press Ctrl+C to stop")
    print("=" * 50)

    # Parse command line arguments
    port = 8767
    camera_index = 1  # Default to camera index 1

    if len(sys.argv) > 1:
        try:
            port = int(sys.argv[1])
        except ValueError:
            logger.error("Invalid port number")
            sys.exit(1)

    if len(sys.argv) > 2:
        try:
            camera_index = int(sys.argv[2])
        except ValueError:
            logger.error("Invalid camera index")
            sys.exit(1)

    # Create and start the character recognition system
    vision_system = R2D2CharacterVisionSystem(websocket_port=port, camera_index=camera_index)

    try:
        success = vision_system.start()
        if not success:
            logger.error("Failed to start character recognition system")
            sys.exit(1)
    except KeyboardInterrupt:
        logger.info("Character recognition system stopped by user")
    except Exception as e:
        logger.error(f"Character recognition system error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()