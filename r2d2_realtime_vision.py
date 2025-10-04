#!/usr/bin/env python3
"""
R2D2 Real-time Vision System with WebSocket Streaming
Provides live webcam feed with YOLO object detection for dashboard integration
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
import queue
import sys
import os

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class R2D2RealtimeVision:
    """Real-time vision system for R2D2 with WebSocket streaming"""

    def __init__(self, websocket_port=8767, camera_index=0):
        self.websocket_port = websocket_port
        self.camera_index = camera_index
        self.running = False
        self.camera = None
        self.model = None
        self.frame_queue = queue.Queue(maxsize=2)
        self.detection_queue = queue.Queue(maxsize=10)
        self.connected_clients = set()
        self.max_clients = 1  # Limit to 1 client to prevent flickering from multiple connections
        self.performance_stats = {
            'fps': 0,
            'detection_time': 0,
            'total_detections': 0,
            'confidence_threshold': 0.5
        }

        # Initialize model
        self._load_yolo_model()

    def _load_yolo_model(self):
        """Load YOLO model for object detection"""
        try:
            from ultralytics import YOLO
            logger.info("Loading YOLOv8 model...")

            # Try to load YOLOv8n model (lightweight for real-time performance)
            self.model = YOLO('yolov8n.pt')

            # Move to GPU if available
            import torch
            if torch.cuda.is_available():
                self.model.to('cuda')
                logger.info("YOLO model loaded on GPU")
            else:
                logger.info("YOLO model loaded on CPU")

            # Set model parameters for optimal performance
            self.model.overrides['verbose'] = False
            self.model.overrides['conf'] = 0.5  # Confidence threshold
            self.model.overrides['iou'] = 0.45   # IoU threshold

        except Exception as e:
            logger.error(f"Failed to load YOLO model: {e}")
            self.model = None

    def _initialize_camera(self):
        """Initialize camera capture with Orin Nano optimized backend"""
        try:
            # Use V4L2 backend specifically for Orin Nano compatibility
            self.camera = cv2.VideoCapture(self.camera_index, cv2.CAP_V4L2)

            if not self.camera.isOpened():
                logger.error("Failed to open camera with V4L2 backend")
                # Fallback to default backend
                logger.info("Trying fallback to default backend...")
                self.camera = cv2.VideoCapture(self.camera_index)

                if not self.camera.isOpened():
                    logger.error("Failed to open camera with any backend")
                    return False

            # Set camera properties for optimal performance
            self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            self.camera.set(cv2.CAP_PROP_FPS, 30)
            self.camera.set(cv2.CAP_PROP_BUFFERSIZE, 1)

            # Test frame capture
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
        """Continuous frame capture thread with advanced anti-flickering"""
        logger.info("Starting enhanced frame capture thread")
        frame_count = 0
        start_time = time.time()
        last_successful_frame = None
        stable_frame_buffer = []
        buffer_size = 3

        while self.running:
            try:
                frame_start_time = time.time()  # Start timing for FPS lock
                ret, frame = self.camera.read()

                if not ret:
                    logger.warning("Failed to capture frame")
                    # Use last successful frame if available to prevent blank frames
                    if last_successful_frame is not None:
                        frame = last_successful_frame.copy()
                    else:
                        continue

                # Frame stabilization buffer
                stable_frame_buffer.append(frame.copy())
                if len(stable_frame_buffer) > buffer_size:
                    stable_frame_buffer.pop(0)

                # Use most stable frame (middle of buffer)
                if len(stable_frame_buffer) >= buffer_size:
                    stable_frame = stable_frame_buffer[buffer_size // 2]
                else:
                    stable_frame = frame

                last_successful_frame = stable_frame.copy()

                # Calculate FPS with smoothing
                frame_count += 1
                if frame_count % 30 == 0:
                    elapsed = time.time() - start_time
                    new_fps = frame_count / elapsed
                    # Smooth FPS calculation to prevent jumpy readings
                    if hasattr(self, 'smooth_fps'):
                        self.performance_stats['fps'] = (self.smooth_fps * 0.8) + (new_fps * 0.2)
                    else:
                        self.performance_stats['fps'] = new_fps
                    self.smooth_fps = self.performance_stats['fps']

                # Enhanced frame quality check before queuing
                if self._is_frame_quality_good(stable_frame):
                    # Add frame to queue (non-blocking) with smart replacement
                    try:
                        self.frame_queue.put_nowait(stable_frame.copy())
                    except queue.Full:
                        # Replace oldest frame with newest to maintain flow
                        try:
                            self.frame_queue.get_nowait()
                            self.frame_queue.put_nowait(stable_frame.copy())
                        except queue.Empty:
                            pass

                # Adaptive FPS control based on processing load
                target_fps = self._get_adaptive_fps()
                frame_time = 1.0 / target_fps

                # Calculate actual processing time and sleep accordingly
                frame_end_time = time.time()
                processing_time = frame_end_time - frame_start_time
                sleep_time = max(0, frame_time - processing_time)

                # Micro-sleep for precise timing
                if sleep_time > 0:
                    time.sleep(sleep_time)

            except Exception as e:
                logger.error(f"Frame capture error: {e}")
                # Don't break immediately, try to recover
                time.sleep(0.1)
                continue

    def _is_frame_quality_good(self, frame):
        """Check if frame quality is good enough for processing"""
        if frame is None:
            return False

        # Check for completely black or white frames
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        mean_brightness = cv2.mean(gray)[0]

        # Reject frames that are too dark or too bright
        if mean_brightness < 10 or mean_brightness > 245:
            return False

        # Check for motion blur using Laplacian variance
        laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()

        # Reject blurry frames (adjust threshold as needed)
        if laplacian_var < 50:
            return False

        return True

    def _get_adaptive_fps(self):
        """Get adaptive FPS based on current system load"""
        detection_time = self.performance_stats['detection_time']
        connected_clients = len(self.connected_clients)

        # Base FPS
        base_fps = 15

        # Reduce FPS if detection is taking too long
        if detection_time > 0.1:  # 100ms
            base_fps = 12
        elif detection_time > 0.15:  # 150ms
            base_fps = 10

        # Reduce FPS if no clients connected to save resources
        if connected_clients == 0:
            base_fps = min(base_fps, 8)

        # Increase FPS for better responsiveness if system is performing well
        if detection_time < 0.05 and connected_clients > 0:  # 50ms
            base_fps = min(18, base_fps + 3)

        return base_fps

    def _extract_character_detections(self, detections: List[Dict]) -> List[Dict]:
        """Extract and analyze character detections with Star Wars character recognition"""
        character_detections = []

        # Star Wars character detection patterns based on YOLO classes
        character_mapping = {
            'person': self._analyze_person_for_character,
            'backpack': lambda d: self._check_if_r2d2_or_droid(d),
            'handbag': lambda d: self._check_costume_accessories(d),
            'sports ball': lambda d: self._check_if_bb8(d),
            'bottle': lambda d: self._check_lightsaber_prop(d),
            'cup': lambda d: self._check_droid_parts(d),
            'remote': lambda d: self._check_if_remote_droid(d)
        }

        for detection in detections:
            class_name = detection['class']
            confidence = detection['confidence']

            if class_name in character_mapping and confidence > 0.5:
                character_result = character_mapping[class_name](detection)
                if character_result:
                    character_detections.append(character_result)

        return character_detections

    def _analyze_person_for_character(self, detection: Dict) -> Dict:
        """Analyze person detection for Star Wars character traits"""
        x1, y1, x2, y2 = detection['bbox']
        width = x2 - x1
        height = y2 - y1
        aspect_ratio = height / width if width > 0 else 1

        # Character recognition based on size, position, and context
        character_data = {
            'name': 'Unknown Person',
            'character': 'unknown',
            'confidence': detection['confidence'],
            'bbox': detection['bbox'],
            'costume_match': 'civilian',
            'character_traits': [],
            'r2d2_reaction': {
                'primary_emotion': 'curious',
                'excitement_level': 'medium',
                'sound_suggestion': 'greeting'
            }
        }

        # Analyze aspect ratio and size for character type hints
        if aspect_ratio > 2.5:
            # Tall, thin - possibly Jedi/Sith
            character_data.update({
                'name': 'Tall Figure',
                'character': 'jedi_sith_candidate',
                'costume_match': 'robed_figure',
                'character_traits': ['tall', 'robed'],
                'r2d2_reaction': {
                    'primary_emotion': 'respectful',
                    'excitement_level': 'high',
                    'sound_suggestion': 'jedi_recognition'
                }
            })
        elif aspect_ratio < 1.5 and width > 100:
            # Short, wide - possibly droid or child
            character_data.update({
                'name': 'Short Figure',
                'character': 'droid_candidate',
                'costume_match': 'mechanical',
                'character_traits': ['short', 'wide'],
                'r2d2_reaction': {
                    'primary_emotion': 'excited',
                    'excitement_level': 'high',
                    'sound_suggestion': 'astromech_duties'
                }
            })
        elif 1.7 <= aspect_ratio <= 2.2:
            # Human proportions
            character_data.update({
                'name': 'Human Figure',
                'character': 'human_candidate',
                'costume_match': 'standard_human',
                'character_traits': ['human_proportions'],
                'r2d2_reaction': {
                    'primary_emotion': 'friendly',
                    'excitement_level': 'medium',
                    'sound_suggestion': 'chatting'
                }
            })

        # Add position-based context
        frame_center_x = 320  # Assuming 640px width
        obj_center_x = (x1 + x2) / 2

        if abs(obj_center_x - frame_center_x) < 50:
            character_data['character_traits'].append('center_stage')
            character_data['r2d2_reaction']['excitement_level'] = 'high'

        return character_data

    def _check_if_r2d2_or_droid(self, detection: Dict) -> Dict:
        """Check if backpack detection might be R2D2 or another droid"""
        x1, y1, x2, y2 = detection['bbox']
        width = x2 - x1
        height = y2 - y1
        aspect_ratio = height / width if width > 0 else 1

        if 1.2 <= aspect_ratio <= 2.0 and width > 60:
            return {
                'name': 'Possible Droid',
                'character': 'droid_detected',
                'confidence': detection['confidence'],
                'bbox': detection['bbox'],
                'costume_match': 'droid_silhouette',
                'character_traits': ['cylindrical', 'mechanical'],
                'r2d2_reaction': {
                    'primary_emotion': 'excited',
                    'excitement_level': 'very_high',
                    'sound_suggestion': 'astromech_duties'
                }
            }
        return None

    def _check_costume_accessories(self, detection: Dict) -> Dict:
        """Check for costume accessories that might indicate Star Wars characters"""
        return {
            'name': 'Costume Accessory',
            'character': 'costume_piece',
            'confidence': detection['confidence'],
            'bbox': detection['bbox'],
            'costume_match': 'accessory',
            'character_traits': ['prop', 'costume_element'],
            'r2d2_reaction': {
                'primary_emotion': 'curious',
                'excitement_level': 'medium',
                'sound_suggestion': 'curious'
            }
        }

    def _check_if_bb8(self, detection: Dict) -> Dict:
        """Check if spherical object might be BB-8"""
        x1, y1, x2, y2 = detection['bbox']
        width = x2 - x1
        height = y2 - y1
        aspect_ratio = height / width if width > 0 else 1

        if 0.8 <= aspect_ratio <= 1.3:  # Nearly circular
            return {
                'name': 'Spherical Droid Candidate',
                'character': 'bb8_candidate',
                'confidence': detection['confidence'],
                'bbox': detection['bbox'],
                'costume_match': 'spherical_droid',
                'character_traits': ['spherical', 'rolling'],
                'r2d2_reaction': {
                    'primary_emotion': 'playful',
                    'excitement_level': 'high',
                    'sound_suggestion': 'playful'
                }
            }
        return None

    def _check_lightsaber_prop(self, detection: Dict) -> Dict:
        """Check if elongated object might be a lightsaber prop"""
        x1, y1, x2, y2 = detection['bbox']
        width = x2 - x1
        height = y2 - y1
        aspect_ratio = height / width if width > 0 else 1

        if aspect_ratio > 3.0:  # Very elongated
            return {
                'name': 'Lightsaber Prop',
                'character': 'lightsaber_detected',
                'confidence': detection['confidence'],
                'bbox': detection['bbox'],
                'costume_match': 'jedi_weapon',
                'character_traits': ['weapon', 'jedi_tool'],
                'r2d2_reaction': {
                    'primary_emotion': 'alert',
                    'excitement_level': 'high',
                    'sound_suggestion': 'jedi_recognition'
                }
            }
        return None

    def _check_droid_parts(self, detection: Dict) -> Dict:
        """Check for potential droid parts or mechanical elements"""
        return {
            'name': 'Mechanical Component',
            'character': 'droid_component',
            'confidence': detection['confidence'],
            'bbox': detection['bbox'],
            'costume_match': 'mechanical_part',
            'character_traits': ['mechanical', 'technical'],
            'r2d2_reaction': {
                'primary_emotion': 'interested',
                'excitement_level': 'medium',
                'sound_suggestion': 'maintenance'
            }
        }

    def _check_if_remote_droid(self, detection: Dict) -> Dict:
        """Check if remote-like object might be a droid control device"""
        return {
            'name': 'Control Device',
            'character': 'droid_controller',
            'confidence': detection['confidence'],
            'bbox': detection['bbox'],
            'costume_match': 'control_device',
            'character_traits': ['electronic', 'control'],
            'r2d2_reaction': {
                'primary_emotion': 'attentive',
                'excitement_level': 'medium',
                'sound_suggestion': 'alert'
            }
        }

    def _process_detections(self):
        """Process YOLO detections on captured frames"""
        logger.info("Starting detection processing thread")

        while self.running:
            try:
                # Get frame from queue
                frame = self.frame_queue.get(timeout=1.0)

                if self.model is None:
                    continue

                # Run YOLO detection
                start_time = time.time()
                results = self.model(frame, verbose=False)
                detection_time = time.time() - start_time

                self.performance_stats['detection_time'] = detection_time

                # Process detection results
                detections = []
                if results and len(results) > 0:
                    result = results[0]

                    if result.boxes is not None:
                        boxes = result.boxes.cpu().numpy()

                        for box in boxes:
                            # Extract box information
                            x1, y1, x2, y2 = box.xyxy[0]
                            confidence = box.conf[0]
                            class_id = int(box.cls[0])
                            class_name = self.model.names[class_id]

                            if confidence >= self.performance_stats['confidence_threshold']:
                                detections.append({
                                    'class': class_name,
                                    'confidence': float(confidence),
                                    'bbox': [float(x1), float(y1), float(x2), float(y2)],
                                    'class_id': class_id
                                })

                # Draw detections on frame
                annotated_frame = self._draw_detections(frame, detections)

                # Add to detection queue
                detection_data = {
                    'frame': annotated_frame,
                    'detections': detections,
                    'timestamp': datetime.now().isoformat(),
                    'stats': self.performance_stats.copy()
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

                self.performance_stats['total_detections'] += len(detections)

            except queue.Empty:
                continue
            except Exception as e:
                logger.error(f"Detection processing error: {e}")

    def _draw_detections(self, frame, detections):
        """Draw detection boxes and labels on frame with Star Wars character enhancements"""
        annotated_frame = frame.copy()

        for detection in detections:
            x1, y1, x2, y2 = detection['bbox']
            confidence = detection['confidence']
            class_name = detection['class']

            # Get enhanced color based on Star Wars context
            color = self._get_enhanced_class_color(detection['class_id'], class_name)

            # Draw enhanced bounding box with thicker lines for important detections
            thickness = 3 if class_name == 'person' else 2
            cv2.rectangle(annotated_frame, (int(x1), int(y1)), (int(x2), int(y2)), color, thickness)

            # Enhanced label with confidence and class
            label = f"{class_name} {confidence:.2f}"
            label_size = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)[0]

            # Enhanced background for label with better visibility
            cv2.rectangle(annotated_frame,
                         (int(x1), int(y1) - label_size[1] - 15),
                         (int(x1) + label_size[0] + 10, int(y1)),
                         color, -1)

            # White border for better text visibility
            cv2.rectangle(annotated_frame,
                         (int(x1), int(y1) - label_size[1] - 15),
                         (int(x1) + label_size[0] + 10, int(y1)),
                         (255, 255, 255), 1)

            # Enhanced label text with shadow effect
            cv2.putText(annotated_frame, label,
                       (int(x1) + 6, int(y1) - 7),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 3)  # Shadow
            cv2.putText(annotated_frame, label,
                       (int(x1) + 5, int(y1) - 8),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)  # Text

            # Add special indicators for specific classes
            if class_name == 'person':
                # Add person indicator
                cv2.circle(annotated_frame, (int(x1) + 10, int(y1) + 10), 5, (0, 255, 0), -1)
            elif class_name in ['backpack', 'sports ball']:
                # Add potential droid indicator
                cv2.circle(annotated_frame, (int(x1) + 10, int(y1) + 10), 5, (255, 0, 255), -1)

        # Enhanced performance info display
        self._draw_performance_overlay(annotated_frame, detections)

        return annotated_frame

    def _draw_performance_overlay(self, frame, detections):
        """Draw enhanced performance overlay with R2D2 style"""
        h, w = frame.shape[:2]

        # Create semi-transparent overlay area
        overlay = frame.copy()

        # Performance stats background
        cv2.rectangle(overlay, (5, 5), (350, 130), (0, 0, 0), -1)
        cv2.addWeighted(overlay, 0.7, frame, 0.3, 0, frame)

        # R2D2 Vision System title
        cv2.putText(frame, "R2D2 VISION SYSTEM", (10, 25),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (100, 255, 255), 2)

        # Performance metrics with color coding
        fps_color = (0, 255, 0) if self.performance_stats['fps'] > 10 else (0, 255, 255)
        fps_text = f"FPS: {self.performance_stats['fps']:.1f}"
        cv2.putText(frame, fps_text, (10, 50),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, fps_color, 2)

        detection_color = (0, 255, 0) if len(detections) > 0 else (128, 128, 128)
        detection_text = f"Detections: {len(detections)}"
        cv2.putText(frame, detection_text, (10, 70),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, detection_color, 2)

        timing_color = (0, 255, 0) if self.performance_stats['detection_time'] < 0.1 else (255, 255, 0)
        timing_text = f"Inference: {self.performance_stats['detection_time']*1000:.1f}ms"
        cv2.putText(frame, timing_text, (10, 90),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, timing_color, 2)

        confidence_text = f"Threshold: {self.performance_stats['confidence_threshold']:.2f}"
        cv2.putText(frame, confidence_text, (10, 110),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)

        # Connection status indicator
        status_color = (0, 255, 0) if len(self.connected_clients) > 0 else (0, 0, 255)
        cv2.circle(frame, (w - 20, 20), 8, status_color, -1)
        cv2.putText(frame, "CONNECTED" if len(self.connected_clients) > 0 else "NO CLIENT",
                   (w - 100, 45), cv2.FONT_HERSHEY_SIMPLEX, 0.4, status_color, 1)

    def _get_enhanced_class_color(self, class_id, class_name):
        """Get enhanced colors for Star Wars themed detection"""
        # Star Wars themed colors
        star_wars_colors = {
            'person': (0, 255, 100),      # Green - for humans/characters
            'backpack': (255, 100, 255),   # Magenta - potential droids
            'handbag': (100, 100, 255),    # Blue - accessories
            'sports ball': (255, 255, 0),  # Yellow - BB-8 candidates
            'bottle': (0, 255, 255),       # Cyan - lightsaber props
            'cup': (255, 150, 0),          # Orange - droid parts
            'remote': (150, 255, 150),     # Light green - controllers
        }

        # Return Star Wars color if available, otherwise default YOLO colors
        if class_name in star_wars_colors:
            return star_wars_colors[class_name]

        # Default YOLO colors for other classes
        colors = [
            (255, 0, 0), (0, 255, 0), (0, 0, 255), (255, 255, 0),
            (255, 0, 255), (0, 255, 255), (128, 0, 128), (255, 165, 0),
            (0, 128, 255), (255, 20, 147), (50, 205, 50), (255, 69, 0)
        ]
        return colors[class_id % len(colors)]

    def _get_class_color(self, class_id):
        """Get consistent color for object class"""
        colors = [
            (255, 0, 0), (0, 255, 0), (0, 0, 255), (255, 255, 0),
            (255, 0, 255), (0, 255, 255), (128, 0, 128), (255, 165, 0),
            (0, 128, 255), (255, 20, 147), (50, 205, 50), (255, 69, 0)
        ]
        return colors[class_id % len(colors)]

    async def _handle_websocket_client(self, websocket):
        """Handle WebSocket client connections with connection limiting"""
        client_addr = websocket.remote_address

        # Check connection limit to prevent flickering from multiple clients
        if len(self.connected_clients) >= self.max_clients:
            logger.warning(f"Connection limit reached. Rejecting client: {client_addr}")
            await websocket.close(code=1013, reason="Server busy - too many connections")
            return

        logger.info(f"New client connected: {client_addr}")
        self.connected_clients.add(websocket)

        try:
            await websocket.send(json.dumps({
                'type': 'connection_status',
                'status': 'connected',
                'message': 'R2D2 Vision System Connected'
            }))

            # Listen for incoming messages with better error handling
            async def handle_incoming_messages():
                try:
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
                except websockets.exceptions.ConnectionClosed:
                    logger.info("Client disconnected gracefully")
                except Exception as e:
                    logger.error(f"WebSocket error in message handler: {e}")

            # Start message handler task
            import asyncio
            asyncio.create_task(handle_incoming_messages())

            # Enhanced frame and detection data streaming with adaptive quality
            last_send_time = time.time()
            frame_skip_counter = 0
            quality_adaptation = {
                'jpeg_quality': 85,
                'target_fps': 12,
                'adaptive_quality': True
            }

            while self.running:
                try:
                    # Get latest detection data with timeout
                    detection_data = self.detection_queue.get(timeout=0.1)

                    # Adaptive frame skipping for performance
                    if len(self.connected_clients) > 1:
                        frame_skip_counter += 1
                        if frame_skip_counter % 2 == 0:  # Skip every other frame for multiple clients
                            continue
                        frame_skip_counter = 0

                    # Adaptive JPEG quality based on detection complexity
                    num_detections = len(detection_data['detections'])
                    if quality_adaptation['adaptive_quality']:
                        if num_detections > 5:
                            quality_adaptation['jpeg_quality'] = 75  # Lower quality for complex scenes
                        elif num_detections < 2:
                            quality_adaptation['jpeg_quality'] = 90  # Higher quality for simple scenes
                        else:
                            quality_adaptation['jpeg_quality'] = 85  # Standard quality

                    # Encode frame with adaptive quality
                    encode_params = [cv2.IMWRITE_JPEG_QUALITY, quality_adaptation['jpeg_quality']]
                    _, buffer = cv2.imencode('.jpg', detection_data['frame'], encode_params)
                    frame_base64 = base64.b64encode(buffer).decode('utf-8')

                    # Extract character detections with caching for performance
                    character_detections = self._extract_character_detections(detection_data['detections'])

                    # Enhanced WebSocket message with performance stats
                    message = {
                        'type': 'character_vision_data',
                        'frame': frame_base64,
                        'detections': detection_data['detections'],
                        'character_detections': character_detections,
                        'timestamp': detection_data['timestamp'],
                        'stats': {
                            **detection_data['stats'],
                            'character_count': len(character_detections),
                            'character_time': detection_data['stats'].get('detection_time', 0),
                            'stream_quality': quality_adaptation['jpeg_quality'],
                            'adaptive_fps': quality_adaptation['target_fps']
                        }
                    }

                    # Send to client with error handling
                    try:
                        await websocket.send(json.dumps(message))
                    except websockets.exceptions.ConnectionClosed:
                        logger.info("Client disconnected during send")
                        break

                    # Adaptive frame timing based on system performance
                    current_time = time.time()
                    detection_time = detection_data['stats']['detection_time']

                    # Adjust target FPS based on detection performance
                    if detection_time > 0.1:
                        quality_adaptation['target_fps'] = 10
                    elif detection_time < 0.05:
                        quality_adaptation['target_fps'] = 15
                    else:
                        quality_adaptation['target_fps'] = 12

                    send_interval = 1.0 / quality_adaptation['target_fps']
                    time_since_last_send = current_time - last_send_time

                    if time_since_last_send < send_interval:
                        sleep_time = send_interval - time_since_last_send
                        await asyncio.sleep(sleep_time)

                    last_send_time = time.time()

                except queue.Empty:
                    # Send enhanced heartbeat with system status
                    heartbeat_data = {
                        'type': 'heartbeat',
                        'timestamp': datetime.now().isoformat(),
                        'system_status': {
                            'fps': self.performance_stats['fps'],
                            'detection_time': self.performance_stats['detection_time'],
                            'total_detections': self.performance_stats['total_detections'],
                            'connected_clients': len(self.connected_clients),
                            'queue_size': self.detection_queue.qsize()
                        }
                    }
                    try:
                        await websocket.send(json.dumps(heartbeat_data))
                    except websockets.exceptions.ConnectionClosed:
                        break
                    await asyncio.sleep(0.5)  # Longer heartbeat interval

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
            logger.info(f"WebSocket server running on port {self.websocket_port}")
            # Keep the server running
            await asyncio.Future()  # Run forever

    def start(self):
        """Start the real-time vision system"""
        logger.info("Starting R2D2 Real-time Vision System")

        # Initialize camera
        if not self._initialize_camera():
            logger.error("Failed to initialize camera")
            return False

        if self.model is None:
            logger.error("YOLO model not available")
            return False

        self.running = True

        # Start capture thread
        capture_thread = threading.Thread(target=self._capture_frames, daemon=True)
        capture_thread.start()

        # Start detection processing thread
        detection_thread = threading.Thread(target=self._process_detections, daemon=True)
        detection_thread.start()

        logger.info(f"R2D2 Vision WebSocket server starting on port {self.websocket_port}")

        # Start WebSocket server using asyncio.run for modern Python
        try:
            asyncio.run(self._run_websocket_server())
        except KeyboardInterrupt:
            logger.info("Shutting down R2D2 Vision System")
        finally:
            self.stop()

        return True

    def stop(self):
        """Stop the vision system"""
        logger.info("Stopping R2D2 Vision System")
        self.running = False

        if self.camera:
            self.camera.release()

        # Close all WebSocket connections
        for client in self.connected_clients.copy():
            try:
                loop = asyncio.get_running_loop()
                loop.create_task(client.close())
            except RuntimeError:
                # No running loop, close synchronously
                asyncio.run(client.close())

def main():
    """Main function to run the R2D2 vision system"""
    print("R2D2 Real-time Vision System")
    print("=" * 40)
    print("Press Ctrl+C to stop")
    print("=" * 40)

    # Check for optional port and camera arguments
    port = 8767
    camera_index = 0  # Default to camera index 0 (primary camera)

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

    # Create and start vision system
    vision_system = R2D2RealtimeVision(websocket_port=port, camera_index=camera_index)

    try:
        success = vision_system.start()
        if not success:
            logger.error("Failed to start vision system")
            sys.exit(1)
    except KeyboardInterrupt:
        logger.info("Vision system stopped by user")
    except Exception as e:
        logger.error(f"Vision system error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()