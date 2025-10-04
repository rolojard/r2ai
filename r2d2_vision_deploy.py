#!/usr/bin/env python3
"""
R2D2 Enhanced Vision System - Stable Deployment Version
Real-time webcam with YOLOv8 character detection for R2D2 dashboard
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
from typing import Dict, List, Any
import queue

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class R2D2EnhancedVision:
    """Enhanced R2D2 Vision System with YOLO character detection"""

    def __init__(self, websocket_port=8767, camera_index=0):
        self.websocket_port = websocket_port
        self.camera_index = camera_index
        self.running = False
        self.camera = None
        self.yolo_model = None
        self.frame_queue = queue.Queue(maxsize=2)
        self.detection_queue = queue.Queue(maxsize=5)
        self.connected_clients = set()

        # Performance tracking
        self.stats = {
            'fps': 0,
            'detection_time': 0,
            'total_detections': 0,
            'confidence_threshold': 0.5
        }

        # Initialize YOLO
        self._load_yolo_model()

    def _load_yolo_model(self):
        """Load YOLOv8 model"""
        try:
            from ultralytics import YOLO
            logger.info("Loading YOLOv8n model...")
            self.yolo_model = YOLO('yolov8n.pt')

            # Configure for optimal performance
            self.yolo_model.overrides['verbose'] = False
            self.yolo_model.overrides['conf'] = 0.5
            self.yolo_model.overrides['iou'] = 0.45

            logger.info("YOLO model loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load YOLO model: {e}")
            self.yolo_model = None

    def _initialize_camera(self):
        """Initialize camera"""
        try:
            self.camera = cv2.VideoCapture(self.camera_index)

            if not self.camera.isOpened():
                logger.error("Failed to open camera")
                return False

            # Configure camera
            self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            self.camera.set(cv2.CAP_PROP_FPS, 30)
            self.camera.set(cv2.CAP_PROP_BUFFERSIZE, 1)

            # Test capture
            ret, frame = self.camera.read()
            if not ret:
                logger.error("Failed to read from camera")
                return False

            logger.info(f"Camera initialized successfully: {frame.shape}")
            return True

        except Exception as e:
            logger.error(f"Camera initialization failed: {e}")
            return False

    def _capture_frames(self):
        """Frame capture thread"""
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
                    self.stats['fps'] = frame_count / elapsed

                # Add to queue
                try:
                    self.frame_queue.put_nowait(frame.copy())
                except queue.Full:
                    try:
                        self.frame_queue.get_nowait()
                        self.frame_queue.put_nowait(frame.copy())
                    except queue.Empty:
                        pass

                # Target 15 FPS for stable streaming
                time.sleep(1.0 / 15)

            except Exception as e:
                logger.error(f"Frame capture error: {e}")
                time.sleep(0.1)

    def _process_detections(self):
        """YOLO detection processing thread"""
        logger.info("Starting detection processing thread")

        while self.running:
            try:
                frame = self.frame_queue.get(timeout=1.0)

                if self.yolo_model is None:
                    continue

                # Run YOLO detection
                start_time = time.time()
                results = self.yolo_model(frame, verbose=False)
                detection_time = time.time() - start_time
                self.stats['detection_time'] = detection_time

                # Process results
                detections = []
                if results and len(results) > 0:
                    result = results[0]
                    if result.boxes is not None:
                        boxes = result.boxes.cpu().numpy()
                        for box in boxes:
                            x1, y1, x2, y2 = box.xyxy[0]
                            confidence = float(box.conf[0])
                            class_id = int(box.cls[0])
                            class_name = self.yolo_model.names[class_id]

                            if confidence >= self.stats['confidence_threshold']:
                                detections.append({
                                    'class': class_name,
                                    'confidence': confidence,
                                    'bbox': [float(x1), float(y1), float(x2), float(y2)],
                                    'class_id': class_id
                                })

                # Draw detections
                annotated_frame = self._draw_detections(frame, detections)

                # Add to detection queue
                detection_data = {
                    'frame': annotated_frame,
                    'detections': detections,
                    'character_detections': self._analyze_characters(detections),
                    'timestamp': datetime.now().isoformat(),
                    'stats': self.stats.copy()
                }

                try:
                    self.detection_queue.put_nowait(detection_data)
                except queue.Full:
                    try:
                        self.detection_queue.get_nowait()
                        self.detection_queue.put_nowait(detection_data)
                    except queue.Empty:
                        pass

                self.stats['total_detections'] += len(detections)

            except queue.Empty:
                continue
            except Exception as e:
                logger.error(f"Detection processing error: {e}")

    def _analyze_characters(self, detections):
        """Analyze detections for Star Wars characters"""
        characters = []

        for detection in detections:
            if detection['class'] == 'person' and detection['confidence'] > 0.6:
                # Basic character analysis
                x1, y1, x2, y2 = detection['bbox']
                width = x2 - x1
                height = y2 - y1
                aspect_ratio = height / width if width > 0 else 1

                # Determine character type
                if aspect_ratio > 2.5:
                    character_type = 'Tall Figure (Jedi/Sith?)'
                    emotion = 'respectful'
                elif aspect_ratio < 1.5:
                    character_type = 'Short Figure (Droid?)'
                    emotion = 'excited'
                else:
                    character_type = 'Human Figure'
                    emotion = 'friendly'

                characters.append({
                    'name': character_type,
                    'character': detection['class'],
                    'confidence': detection['confidence'],
                    'bbox': detection['bbox'],
                    'costume_match': 'detected',
                    'r2d2_reaction': {
                        'primary_emotion': emotion,
                        'excitement_level': 'medium',
                        'sound_suggestion': 'greeting'
                    }
                })

        return characters

    def _draw_detections(self, frame, detections):
        """Draw detection boxes and info"""
        annotated_frame = frame.copy()

        # Draw R2D2 header
        cv2.putText(annotated_frame, "R2D2 VISION SYSTEM", (10, 25),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)

        # Draw stats
        cv2.putText(annotated_frame, f"FPS: {self.stats['fps']:.1f}", (10, 50),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
        cv2.putText(annotated_frame, f"Detections: {len(detections)}", (10, 70),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
        cv2.putText(annotated_frame, f"Inference: {self.stats['detection_time']*1000:.1f}ms", (10, 90),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

        # Draw detections
        for detection in detections:
            x1, y1, x2, y2 = detection['bbox']
            confidence = detection['confidence']
            class_name = detection['class']

            # Color based on class
            if class_name == 'person':
                color = (0, 255, 100)  # Green for people
            else:
                color = (255, 100, 0)  # Orange for objects

            # Draw box
            cv2.rectangle(annotated_frame, (int(x1), int(y1)), (int(x2), int(y2)), color, 2)

            # Draw label
            label = f"{class_name} {confidence:.2f}"
            cv2.putText(annotated_frame, label, (int(x1), int(y1) - 10),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)

        return annotated_frame

    async def _handle_websocket_client(self, websocket):
        """Handle WebSocket client connections"""
        client_addr = websocket.remote_address
        logger.info(f"New client connected: {client_addr}")
        self.connected_clients.add(websocket)

        try:
            # Send connection confirmation
            await websocket.send(json.dumps({
                'type': 'connection_status',
                'status': 'connected',
                'message': 'R2D2 Vision System Connected'
            }))

            # Stream data
            while self.running:
                try:
                    detection_data = self.detection_queue.get(timeout=0.5)

                    # Encode frame
                    _, buffer = cv2.imencode('.jpg', detection_data['frame'],
                                           [cv2.IMWRITE_JPEG_QUALITY, 85])
                    frame_base64 = base64.b64encode(buffer).decode('utf-8')

                    # Send message
                    message = {
                        'type': 'character_vision_data',
                        'frame': frame_base64,
                        'detections': detection_data['detections'],
                        'character_detections': detection_data['character_detections'],
                        'timestamp': detection_data['timestamp'],
                        'stats': detection_data['stats']
                    }

                    await websocket.send(json.dumps(message))

                    # Limit to 12 FPS for stable streaming
                    await asyncio.sleep(1.0 / 12)

                except queue.Empty:
                    # Send heartbeat
                    await websocket.send(json.dumps({
                        'type': 'heartbeat',
                        'timestamp': datetime.now().isoformat()
                    }))

                except websockets.exceptions.ConnectionClosed:
                    break

        except Exception as e:
            logger.error(f"WebSocket client error: {e}")
        finally:
            self.connected_clients.discard(websocket)
            logger.info(f"Client disconnected: {client_addr}")

    async def _run_websocket_server(self):
        """Run WebSocket server"""
        async with websockets.serve(
            self._handle_websocket_client,
            "localhost",
            self.websocket_port
        ):
            logger.info(f"WebSocket server running on port {self.websocket_port}")
            await asyncio.Future()  # Run forever

    def start(self):
        """Start the vision system"""
        logger.info("Starting R2D2 Enhanced Vision System")

        # Initialize camera
        if not self._initialize_camera():
            logger.error("Failed to initialize camera")
            return False

        if self.yolo_model is None:
            logger.error("YOLO model not available")
            return False

        self.running = True

        # Start threads
        capture_thread = threading.Thread(target=self._capture_frames, daemon=True)
        detection_thread = threading.Thread(target=self._process_detections, daemon=True)

        capture_thread.start()
        detection_thread.start()

        # Start WebSocket server
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

def main():
    """Main function"""
    print("R2D2 Enhanced Vision System")
    print("=" * 40)
    print("Press Ctrl+C to stop")
    print("=" * 40)

    # Create and start vision system
    vision_system = R2D2EnhancedVision(websocket_port=8767, camera_index=0)

    try:
        success = vision_system.start()
        if not success:
            logger.error("Failed to start vision system")
            return 1
    except KeyboardInterrupt:
        logger.info("Vision system stopped by user")
    except Exception as e:
        logger.error(f"Vision system error: {e}")
        return 1

    return 0

if __name__ == "__main__":
    exit(main())