#!/usr/bin/env python3
"""
R2D2 Enhanced Real-time Vision System with Person Recognition
Integrates YOLO object detection with advanced person recognition, face detection,
Star Wars character identification, and memory management for personalized interactions
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
import queue
import sys
import os
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
import sqlite3
from pathlib import Path

# Import existing vision system
from r2d2_realtime_vision import R2D2RealtimeVision
from r2d2_person_recognition_system import R2D2PersonRecognitionSystem, PersonIdentity

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class EnhancedDetectionResult:
    """Enhanced detection result combining object detection and person recognition"""
    timestamp: str
    frame_shape: Tuple[int, int, int]
    processing_time: float

    # Original YOLO detections
    object_detections: List[Dict]

    # Person-specific detections
    person_detections: List[Dict]
    face_detections: List[Dict]
    person_identities: List[Dict]

    # R2D2 response generation
    r2d2_responses: List[Dict]

    # Character detection results
    character_detections: List[Dict]

    # Performance metrics
    performance_stats: Dict[str, Any]

class R2D2EnhancedVisionSystem(R2D2RealtimeVision):
    """Enhanced R2D2 vision system with integrated person recognition"""

    def __init__(self, websocket_port=8767, camera_index=1, config: Dict = None):
        # Initialize base vision system
        super().__init__(websocket_port, camera_index)

        # Initialize person recognition system
        self.person_recognition = R2D2PersonRecognitionSystem(config)

        # Enhanced configuration
        self.config = self._get_enhanced_config(config)

        # Enhanced performance tracking
        self.enhanced_stats = {
            'recognition_fps': 0,
            'total_faces_detected': 0,
            'unique_persons_recognized': 0,
            'star_wars_characters_detected': 0,
            'response_generation_time': 0,
            'avg_recognition_confidence': 0.0,
            'memory_cleanup_cycles': 0
        }

        # Processing control
        self.recognition_enabled = True
        self.frame_skip_counter = 0
        self.recognition_frame_interval = self.config.get('recognition_frame_interval', 3)

        # Response generation
        self.response_queue = queue.Queue(maxsize=20)
        self.last_cleanup_time = datetime.now()

        logger.info("R2D2 Enhanced Vision System initialized with person recognition")

    def _get_enhanced_config(self, user_config: Dict = None) -> Dict:
        """Get enhanced configuration with person recognition settings"""
        base_config = {
            'recognition_frame_interval': 3,  # Process every 3rd frame for recognition
            'response_cooldown_seconds': 2.0,  # Minimum time between responses to same person
            'max_concurrent_recognitions': 3,
            'performance_monitoring_interval': 30,  # seconds
            'memory_cleanup_interval': 3600,  # 1 hour
            'enable_character_detection': True,
            'enable_response_generation': True,
            'debug_visualization': True
        }

        if user_config:
            base_config.update(user_config)

        return base_config

    def _process_detections(self):
        """Enhanced detection processing with person recognition"""
        logger.info("Starting enhanced detection processing with person recognition")

        recognition_frame_count = 0
        recognition_start_time = time.time()

        while self.running:
            try:
                # Get frame from queue
                frame = self.frame_queue.get(timeout=1.0)

                if self.model is None:
                    continue

                # Run standard YOLO detection
                start_time = time.time()
                yolo_results = self.model(frame, verbose=False)
                yolo_detection_time = time.time() - start_time

                # Process YOLO results for objects
                object_detections = self._process_yolo_results(yolo_results)

                # Enhanced person recognition processing
                recognition_results = []
                character_detections = []
                r2d2_responses = []

                # Process person recognition every Nth frame
                self.frame_skip_counter += 1
                if (self.recognition_enabled and
                    self.frame_skip_counter >= self.recognition_frame_interval):

                    self.frame_skip_counter = 0
                    recognition_start = time.time()

                    # Run person recognition pipeline
                    recognition_result = self.person_recognition.process_frame(frame)

                    if 'results' in recognition_result:
                        for result in recognition_result['results']:
                            recognition_results.append(result)

                            # Extract character detection
                            if result.get('character_detected'):
                                character_detections.append({
                                    'character': result['character_detected'],
                                    'bbox': result['person_detection']['bbox'],
                                    'confidence': 0.8  # Placeholder confidence
                                })

                            # Generate R2D2 response
                            if self.config['enable_response_generation']:
                                response = self._generate_enhanced_r2d2_response(result)
                                if response:
                                    r2d2_responses.append(response)

                    recognition_time = time.time() - recognition_start

                    # Update recognition performance stats
                    recognition_frame_count += 1
                    if recognition_frame_count % 10 == 0:
                        elapsed = time.time() - recognition_start_time
                        self.enhanced_stats['recognition_fps'] = recognition_frame_count / elapsed

                    self.enhanced_stats['response_generation_time'] = recognition_time

                # Create enhanced detection result
                enhanced_result = EnhancedDetectionResult(
                    timestamp=datetime.now().isoformat(),
                    frame_shape=frame.shape,
                    processing_time=yolo_detection_time + self.enhanced_stats.get('response_generation_time', 0),
                    object_detections=object_detections,
                    person_detections=[r.get('person_detection', {}) for r in recognition_results],
                    face_detections=[r.get('face_detection', {}) for r in recognition_results],
                    person_identities=[r.get('person_identity', {}) for r in recognition_results],
                    r2d2_responses=r2d2_responses,
                    character_detections=character_detections,
                    performance_stats=self._get_combined_performance_stats()
                )

                # Draw enhanced visualizations
                annotated_frame = self._draw_enhanced_detections(frame, enhanced_result)

                # Add to detection queue
                detection_data = {
                    'frame': annotated_frame,
                    'enhanced_result': asdict(enhanced_result),
                    'timestamp': enhanced_result.timestamp,
                    'stats': enhanced_result.performance_stats
                }

                try:
                    self.detection_queue.put_nowait(detection_data)
                except queue.Full:
                    # Remove old detection and add new one
                    try:
                        self.detection_queue.get_nowait()
                        self.detection_queue.put_nowait(detection_data)
                    except queue.Empty:
                        pass

                # Update statistics
                self.performance_stats['total_detections'] += len(object_detections)
                self.enhanced_stats['total_faces_detected'] += len(recognition_results)

                # Periodic maintenance
                self._perform_periodic_maintenance()

            except queue.Empty:
                continue
            except Exception as e:
                logger.error(f"Enhanced detection processing error: {e}")

    def _process_yolo_results(self, results) -> List[Dict]:
        """Process YOLO results into standardized format"""
        detections = []

        if results and len(results) > 0:
            result = results[0]

            if result.boxes is not None:
                boxes = result.boxes.cpu().numpy()

                for box in boxes:
                    x1, y1, x2, y2 = box.xyxy[0]
                    confidence = box.conf[0]
                    class_id = int(box.cls[0])
                    class_name = self.model.names[class_id]

                    if confidence >= self.performance_stats['confidence_threshold']:
                        detections.append({
                            'class': class_name,
                            'confidence': float(confidence),
                            'bbox': [float(x1), float(y1), float(x2), float(y2)],
                            'class_id': class_id,
                            'detection_type': 'object'
                        })

        return detections

    def _generate_enhanced_r2d2_response(self, recognition_result: Dict) -> Optional[Dict]:
        """Generate enhanced R2D2 response with context awareness"""
        try:
            person_identity = recognition_result.get('person_identity')
            if not person_identity:
                return None

            # Check response cooldown to avoid spam
            person_id = person_identity.get('person_id')
            current_time = datetime.now()

            # Generate base response using person recognition system
            base_response = recognition_result.get('r2d2_response', {})

            # Enhance with additional context
            enhanced_response = {
                'person_id': person_id,
                'response_type': base_response.get('response_type', 'friendly_greeting'),
                'excitement_level': base_response.get('excitement_level', 'medium'),
                'timestamp': current_time.isoformat(),
                'context': {
                    'familiarity_level': person_identity.get('familiarity_level', 1),
                    'visit_count': person_identity.get('visit_count', 1),
                    'character_detected': recognition_result.get('character_detected'),
                    'recognition_confidence': person_identity.get('recognition_confidence', 0.0)
                },
                'recommended_actions': base_response.get('recommended_actions', {}),
                'priority': self._calculate_response_priority(person_identity, base_response),
                'duration_estimate': self._estimate_response_duration(base_response)
            }

            return enhanced_response

        except Exception as e:
            logger.error(f"Error generating enhanced R2D2 response: {e}")
            return None

    def _calculate_response_priority(self, person_identity: Dict, response: Dict) -> str:
        """Calculate response priority based on context"""
        familiarity = person_identity.get('familiarity_level', 1)
        character = person_identity.get('character_name')

        if character and familiarity >= 4:
            return 'very_high'
        elif character or familiarity >= 3:
            return 'high'
        elif familiarity == 2:
            return 'medium'
        else:
            return 'low'

    def _estimate_response_duration(self, response: Dict) -> float:
        """Estimate response duration in seconds"""
        response_type = response.get('response_type', 'default')
        excitement = response.get('excitement_level', 'medium')

        base_duration = {
            'curious_cautious': 2.0,
            'friendly_recognition': 3.0,
            'warm_greeting': 4.0,
            'enthusiastic_welcome': 6.0,
            'excited_celebration': 8.0
        }.get(response_type, 3.0)

        excitement_multiplier = {
            'low': 0.8,
            'medium': 1.0,
            'medium_high': 1.2,
            'high': 1.5,
            'very_high': 2.0
        }.get(excitement, 1.0)

        return base_duration * excitement_multiplier

    def _draw_enhanced_detections(self, frame: np.ndarray, result: EnhancedDetectionResult) -> np.ndarray:
        """Draw enhanced detection visualizations"""
        annotated_frame = frame.copy()

        if not self.config['debug_visualization']:
            return annotated_frame

        # Draw object detections (existing functionality)
        for detection in result.object_detections:
            x1, y1, x2, y2 = detection['bbox']
            confidence = detection['confidence']
            class_name = detection['class']

            # Standard object detection visualization
            color = self._get_class_color(detection['class_id'])
            cv2.rectangle(annotated_frame, (int(x1), int(y1)), (int(x2), int(y2)), color, 2)

            label = f"{class_name} {confidence:.2f}"
            cv2.putText(annotated_frame, label, (int(x1), int(y1) - 5),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)

        # Draw person detections with enhanced information
        for i, person_det in enumerate(result.person_detections):
            if not person_det:
                continue

            x, y, w, h = person_det['bbox']

            # Person bounding box in green
            cv2.rectangle(annotated_frame, (x, y), (x+w, y+h), (0, 255, 0), 3)

            # Get corresponding identity and face detection
            identity = result.person_identities[i] if i < len(result.person_identities) else {}
            face_det = result.face_detections[i] if i < len(result.face_detections) else {}

            # Draw face detection
            if face_det and 'bbox' in face_det:
                fx, fy, fw, fh = face_det['bbox']
                cv2.rectangle(annotated_frame, (fx, fy), (fx+fw, fy+fh), (255, 0, 0), 2)

                # Face quality indicator
                quality = face_det.get('quality_score', 0.0)
                quality_color = (0, 255, 0) if quality > 0.6 else (0, 255, 255) if quality > 0.4 else (0, 0, 255)
                cv2.circle(annotated_frame, (fx + fw//2, fy + fh//2), 5, quality_color, -1)

            # Person identity information
            if identity:
                familiarity = identity.get('familiarity_level', 1)
                visit_count = identity.get('visit_count', 1)
                character = identity.get('character_name', '')
                confidence = identity.get('recognition_confidence', 0.0)

                # Create comprehensive label
                labels = [
                    f"Visits: {visit_count}",
                    f"Level: {familiarity}",
                    f"Conf: {confidence:.2f}"
                ]

                if character:
                    labels.append(f"Char: {character}")

                # Draw labels
                for j, label in enumerate(labels):
                    y_offset = y - 10 - (j * 20)
                    cv2.putText(annotated_frame, label, (x, y_offset),
                               cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)

        # Draw character detections with special highlighting
        for char_det in result.character_detections:
            x, y, w, h = char_det['bbox']
            character = char_det['character']

            # Special character highlighting
            char_colors = {
                'jedi': (0, 255, 0),      # Green
                'sith': (0, 0, 255),      # Red
                'stormtrooper': (255, 255, 255),  # White
                'rebel_pilot': (0, 165, 255),     # Orange
                'princess_leia': (255, 0, 255)    # Magenta
            }

            color = char_colors.get(character, (255, 255, 0))
            cv2.rectangle(annotated_frame, (x, y), (x+w, y+h), color, 4)

            # Character label with special styling
            cv2.putText(annotated_frame, f"STAR WARS: {character.upper()}",
                       (x, y - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)

        # Draw R2D2 response indicators
        response_y = 30
        for response in result.r2d2_responses:
            response_type = response.get('response_type', 'unknown')
            excitement = response.get('excitement_level', 'medium')
            priority = response.get('priority', 'low')

            # Color code by priority
            priority_colors = {
                'very_high': (0, 0, 255),    # Red
                'high': (0, 165, 255),       # Orange
                'medium': (0, 255, 255),     # Yellow
                'low': (255, 255, 255)       # White
            }

            color = priority_colors.get(priority, (255, 255, 255))
            response_text = f"R2D2: {response_type} ({excitement})"

            cv2.putText(annotated_frame, response_text, (10, response_y),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
            response_y += 25

        # Enhanced performance display
        stats = result.performance_stats
        perf_texts = [
            f"FPS: {stats.get('fps', 0):.1f}",
            f"Recognition FPS: {stats.get('recognition_fps', 0):.1f}",
            f"Faces: {stats.get('total_faces_detected', 0)}",
            f"Characters: {stats.get('star_wars_characters_detected', 0)}",
            f"Unique Persons: {stats.get('unique_persons_recognized', 0)}"
        ]

        for i, text in enumerate(perf_texts):
            y_pos = frame.shape[0] - 120 + (i * 20)
            cv2.putText(annotated_frame, text, (10, y_pos),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)

        return annotated_frame

    def _get_combined_performance_stats(self) -> Dict[str, Any]:
        """Get combined performance statistics"""
        combined_stats = self.performance_stats.copy()
        combined_stats.update(self.enhanced_stats)
        combined_stats.update(self.person_recognition.performance_stats)
        return combined_stats

    def _perform_periodic_maintenance(self):
        """Perform periodic system maintenance"""
        current_time = datetime.now()

        # Memory cleanup every hour
        if (current_time - self.last_cleanup_time).total_seconds() > self.config['memory_cleanup_interval']:
            self.person_recognition.cleanup_old_identities()
            self.enhanced_stats['memory_cleanup_cycles'] += 1
            self.last_cleanup_time = current_time
            logger.info("Performed periodic memory cleanup")

    async def _handle_websocket_client(self, websocket):
        """Enhanced WebSocket client handler with person recognition data"""
        logger.info(f"Enhanced client connected: {websocket.remote_address}")
        self.connected_clients.add(websocket)

        try:
            await websocket.send(json.dumps({
                'type': 'enhanced_connection_status',
                'status': 'connected',
                'message': 'R2D2 Enhanced Vision System Connected',
                'features': {
                    'person_recognition': True,
                    'character_detection': self.config['enable_character_detection'],
                    'response_generation': self.config['enable_response_generation']
                }
            }))

            # Handle incoming configuration changes
            async def handle_incoming_messages():
                async for message in websocket:
                    try:
                        data = json.loads(message)
                        if data.get('type') == 'update_recognition_config':
                            self._update_recognition_config(data.get('config', {}))
                        elif data.get('type') == 'toggle_recognition':
                            self.recognition_enabled = data.get('enabled', True)
                            logger.info(f"Recognition {'enabled' if self.recognition_enabled else 'disabled'}")
                        elif data.get('type') == 'manual_cleanup':
                            self.person_recognition.cleanup_old_identities()
                            logger.info("Manual memory cleanup performed")
                    except json.JSONDecodeError:
                        logger.warning("Received invalid JSON message")
                    except Exception as e:
                        logger.error(f"Error handling message: {e}")

            # Start message handler
            asyncio.create_task(handle_incoming_messages())

            # Send enhanced detection data
            while self.running:
                try:
                    detection_data = self.detection_queue.get(timeout=0.1)

                    # Encode frame as base64
                    _, buffer = cv2.imencode('.jpg', detection_data['frame'],
                                           [cv2.IMWRITE_JPEG_QUALITY, 80])
                    frame_base64 = base64.b64encode(buffer).decode('utf-8')

                    # Prepare enhanced WebSocket message
                    message = {
                        'type': 'enhanced_vision_data',
                        'frame': frame_base64,
                        'enhanced_result': detection_data['enhanced_result'],
                        'timestamp': detection_data['timestamp'],
                        'stats': detection_data['stats']
                    }

                    await websocket.send(json.dumps(message))

                except queue.Empty:
                    # Send heartbeat with system status
                    status = self.person_recognition.get_system_status()
                    await websocket.send(json.dumps({
                        'type': 'enhanced_heartbeat',
                        'timestamp': datetime.now().isoformat(),
                        'system_status': status
                    }))
                    await asyncio.sleep(0.1)

                except websockets.exceptions.ConnectionClosed:
                    break
                except Exception as e:
                    logger.error(f"Enhanced WebSocket send error: {e}")
                    break

        except websockets.exceptions.ConnectionClosed:
            logger.info("Enhanced client disconnected")
        except Exception as e:
            logger.error(f"Enhanced WebSocket client error: {e}")
        finally:
            self.connected_clients.discard(websocket)

    def _update_recognition_config(self, config_updates: Dict):
        """Update recognition configuration dynamically"""
        try:
            for key, value in config_updates.items():
                if key in self.config:
                    self.config[key] = value
                    logger.info(f"Updated config: {key} = {value}")
        except Exception as e:
            logger.error(f"Error updating recognition config: {e}")

    def get_enhanced_status(self) -> Dict[str, Any]:
        """Get comprehensive system status including person recognition"""
        base_status = {
            'vision_system': 'active' if self.running else 'inactive',
            'recognition_enabled': self.recognition_enabled,
            'connected_clients': len(self.connected_clients)
        }

        recognition_status = self.person_recognition.get_system_status()
        performance_stats = self._get_combined_performance_stats()

        return {
            **base_status,
            'person_recognition': recognition_status,
            'performance': performance_stats,
            'configuration': self.config
        }

def main():
    """Main function to run the enhanced R2D2 vision system"""
    print("R2D2 Enhanced Real-time Vision System with Person Recognition")
    print("=" * 60)
    print("Features:")
    print("- YOLO Object Detection")
    print("- Face Detection & Recognition")
    print("- Star Wars Character Detection")
    print("- Memory Management (7-day + Persistent)")
    print("- Real-time R2D2 Response Generation")
    print("=" * 60)
    print("Press Ctrl+C to stop")
    print("=" * 60)

    # Configuration
    config = {
        'recognition_frame_interval': 2,  # Process every 2nd frame
        'enable_character_detection': True,
        'enable_response_generation': True,
        'debug_visualization': True
    }

    # Check for optional arguments
    port = 8767
    camera_index = 1

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

    # Create and start enhanced vision system
    enhanced_vision = R2D2EnhancedVisionSystem(
        websocket_port=port,
        camera_index=camera_index,
        config=config
    )

    try:
        success = enhanced_vision.start()
        if not success:
            logger.error("Failed to start enhanced vision system")
            sys.exit(1)
    except KeyboardInterrupt:
        logger.info("Enhanced vision system stopped by user")
    except Exception as e:
        logger.error(f"Enhanced vision system error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()