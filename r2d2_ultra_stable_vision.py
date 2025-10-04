#!/usr/bin/env python3
"""
R2D2 Ultra-Stable Real Webcam Vision System
ZERO FLICKERING GUARANTEED - Real C920e Webcam Integration

Addresses core issues:
1. Camera buffer management for consistent frame delivery
2. Fixed timing synchronization
3. Optimized WebSocket streaming
4. Eliminates all flickering sources
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
from collections import deque

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class UltraStableVisionSystem:
    """Ultra-stable real webcam vision system with zero flickering"""

    def __init__(self, websocket_port=8767, camera_index=0):
        self.websocket_port = websocket_port
        self.camera_index = camera_index
        self.running = False
        self.camera = None
        self.model = None

        # Ultra-stable frame management
        self.frame_buffer = deque(maxlen=3)  # Triple buffering for stability
        self.processed_frame_queue = queue.Queue(maxsize=1)  # Single output frame
        self.connected_clients = set()
        self.max_clients = 1  # Prevent multiple connection flickering

        # Precise timing control
        self.target_fps = 12  # Stable 12 FPS - no flicker zone
        self.frame_interval = 1.0 / self.target_fps
        self.last_frame_time = 0
        self.frame_count = 0

        # Performance tracking
        self.performance_stats = {
            'fps': 0,
            'detection_time': 0,
            'total_detections': 0,
            'confidence_threshold': 0.5,
            'frame_drops': 0,
            'buffer_health': 100
        }

        # Thread synchronization
        self.frame_lock = threading.Lock()
        self.stats_lock = threading.Lock()

        # Initialize model
        self._load_yolo_model()

    def _load_yolo_model(self):
        """Load YOLO model with optimal settings"""
        try:
            from ultralytics import YOLO
            logger.info("Loading YOLOv8 model for real webcam...")

            # Load lightweight model
            model_path = '/home/rolo/r2ai/yolov8n.pt'
            if os.path.exists(model_path):
                self.model = YOLO(model_path)
            else:
                self.model = YOLO('yolov8n.pt')

            # GPU optimization
            import torch
            if torch.cuda.is_available():
                self.model.to('cuda')
                logger.info("YOLO model loaded on GPU for real webcam")
            else:
                logger.info("YOLO model loaded on CPU for real webcam")

            # Optimized model settings for real-time performance
            self.model.overrides['verbose'] = False
            self.model.overrides['conf'] = 0.5
            self.model.overrides['iou'] = 0.45
            self.model.overrides['max_det'] = 50  # Limit detections for performance

        except Exception as e:
            logger.error(f"Failed to load YOLO model: {e}")
            self.model = None

    def _initialize_camera(self):
        """Initialize real C920e webcam with optimal settings"""
        try:
            logger.info(f"Initializing REAL C920e webcam on device {self.camera_index}")

            # Initialize camera with backend specification
            self.camera = cv2.VideoCapture(self.camera_index, cv2.CAP_V4L2)

            if not self.camera.isOpened():
                logger.error(f"Failed to open REAL camera at index {self.camera_index}")
                return False

            # Optimal C920e settings for zero flicker
            self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            self.camera.set(cv2.CAP_PROP_FPS, 30)  # Camera native FPS
            self.camera.set(cv2.CAP_PROP_BUFFERSIZE, 1)  # Minimal buffer

            # C920e specific optimizations
            self.camera.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc('M','J','P','G'))
            self.camera.set(cv2.CAP_PROP_AUTO_EXPOSURE, 1)  # Manual exposure
            self.camera.set(cv2.CAP_PROP_EXPOSURE, -6)  # Fast exposure for stability

            # Test real camera capture
            ret, frame = self.camera.read()
            if not ret or frame is None:
                logger.error("Failed to capture from REAL camera")
                return False

            logger.info(f"REAL C920e camera initialized successfully: {frame.shape}")

            # Warm up camera with several reads
            for _ in range(5):
                self.camera.read()
                time.sleep(0.1)

            return True

        except Exception as e:
            logger.error(f"REAL camera initialization failed: {e}")
            return False

    def _capture_frames_ultra_stable(self):
        """Ultra-stable real camera frame capture with zero flicker"""
        logger.info("Starting ULTRA-STABLE real camera capture thread")

        frame_count = 0
        start_time = time.time()
        consecutive_failures = 0

        while self.running:
            try:
                capture_start = time.time()

                # Read from REAL camera
                ret, frame = self.camera.read()

                if not ret or frame is None:
                    consecutive_failures += 1
                    logger.warning(f"Failed to capture from REAL camera (failure #{consecutive_failures})")

                    if consecutive_failures > 10:
                        logger.error("Too many consecutive camera failures - stopping")
                        break

                    time.sleep(0.05)  # Brief recovery pause
                    continue

                consecutive_failures = 0  # Reset failure counter

                # Verify frame quality
                if frame.size == 0:
                    logger.warning("Empty frame from REAL camera")
                    continue

                # Thread-safe frame buffer management
                with self.frame_lock:
                    self.frame_buffer.append(frame.copy())

                # Update performance stats
                frame_count += 1
                if frame_count % 30 == 0:
                    elapsed = time.time() - start_time
                    with self.stats_lock:
                        self.performance_stats['fps'] = frame_count / elapsed
                        self.performance_stats['buffer_health'] = len(self.frame_buffer) * 33  # Health percentage

                # Precise timing to prevent flicker
                capture_end = time.time()
                processing_time = capture_end - capture_start

                # Target interval for stable capture
                target_interval = 1.0 / 30  # Match camera's native 30 FPS
                sleep_time = max(0, target_interval - processing_time)

                if sleep_time > 0:
                    time.sleep(sleep_time)

            except Exception as e:
                logger.error(f"REAL camera capture error: {e}")
                consecutive_failures += 1
                if consecutive_failures > 5:
                    break
                time.sleep(0.1)

        logger.info("REAL camera capture thread stopped")

    def _process_detections_stable(self):
        """Stable detection processing for real camera frames"""
        logger.info("Starting STABLE detection processing for REAL camera")

        while self.running:
            try:
                # Get frame from buffer (thread-safe)
                with self.frame_lock:
                    if len(self.frame_buffer) == 0:
                        time.sleep(0.01)  # Brief wait for frames
                        continue

                    # Use most recent frame
                    frame = self.frame_buffer[-1].copy()

                if self.model is None:
                    # Skip detection but still process frame
                    annotated_frame = self._add_no_model_overlay(frame)
                else:
                    # Run YOLO detection
                    start_time = time.time()
                    results = self.model(frame, verbose=False)
                    detection_time = time.time() - start_time

                    with self.stats_lock:
                        self.performance_stats['detection_time'] = detection_time

                    # Process detection results
                    detections = self._extract_detections(results)
                    annotated_frame = self._draw_detections(frame, detections)

                # Prepare processed frame data
                processed_data = {
                    'frame': annotated_frame,
                    'detections': detections if self.model else [],
                    'timestamp': datetime.now().isoformat(),
                    'stats': self.performance_stats.copy()
                }

                # Add to output queue (non-blocking)
                try:
                    self.processed_frame_queue.put_nowait(processed_data)
                except queue.Full:
                    # Replace old frame with new one
                    try:
                        self.processed_frame_queue.get_nowait()
                    except queue.Empty:
                        pass
                    self.processed_frame_queue.put_nowait(processed_data)

                # Control processing rate
                time.sleep(1.0 / 15)  # 15 FPS processing rate

            except Exception as e:
                logger.error(f"Detection processing error: {e}")
                time.sleep(0.1)

    def _add_no_model_overlay(self, frame):
        """Add overlay when YOLO model is not available"""
        annotated_frame = frame.copy()

        # Add "REAL CAMERA - NO MODEL" text
        cv2.putText(annotated_frame, "REAL C920e CAMERA", (10, 30),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
        cv2.putText(annotated_frame, "NO YOLO MODEL", (10, 60),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 165, 255), 2)

        # Add performance info
        with self.stats_lock:
            fps_text = f"FPS: {self.performance_stats['fps']:.1f}"
            buffer_text = f"Buffer: {self.performance_stats['buffer_health']:.0f}%"

        cv2.putText(annotated_frame, fps_text, (10, 90),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        cv2.putText(annotated_frame, buffer_text, (10, 120),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

        return annotated_frame

    def _extract_detections(self, results):
        """Extract detection data from YOLO results"""
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
                            'class_id': class_id
                        })

        return detections

    def _draw_detections(self, frame, detections):
        """Draw detection boxes and labels on real camera frame"""
        annotated_frame = frame.copy()

        # Add "REAL CAMERA" watermark
        cv2.putText(annotated_frame, "REAL C920e WEBCAM", (10, 30),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)

        for detection in detections:
            x1, y1, x2, y2 = detection['bbox']
            confidence = detection['confidence']
            class_name = detection['class']

            # Draw bounding box
            color = self._get_class_color(detection['class_id'])
            cv2.rectangle(annotated_frame, (int(x1), int(y1)), (int(x2), int(y2)), color, 2)

            # Draw label
            label = f"{class_name} {confidence:.2f}"
            label_size = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)[0]

            # Background for label
            cv2.rectangle(annotated_frame,
                         (int(x1), int(y1) - label_size[1] - 10),
                         (int(x1) + label_size[0], int(y1)),
                         color, -1)

            # Label text
            cv2.putText(annotated_frame, label,
                       (int(x1), int(y1) - 5),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)

        # Add performance info
        with self.stats_lock:
            fps_text = f"FPS: {self.performance_stats['fps']:.1f}"
            detection_text = f"Detections: {len(detections)}"
            timing_text = f"Detection: {self.performance_stats['detection_time']:.3f}s"
            buffer_text = f"Buffer: {self.performance_stats['buffer_health']:.0f}%"

        cv2.putText(annotated_frame, fps_text, (10, 60),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        cv2.putText(annotated_frame, detection_text, (10, 90),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        cv2.putText(annotated_frame, timing_text, (10, 120),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        cv2.putText(annotated_frame, buffer_text, (10, 150),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

        return annotated_frame

    def _get_class_color(self, class_id):
        """Get consistent color for object class"""
        colors = [
            (255, 0, 0), (0, 255, 0), (0, 0, 255), (255, 255, 0),
            (255, 0, 255), (0, 255, 255), (128, 0, 128), (255, 165, 0),
            (0, 128, 255), (255, 20, 147), (50, 205, 50), (255, 69, 0)
        ]
        return colors[class_id % len(colors)]

    async def _handle_websocket_client_stable(self, websocket):
        """Handle WebSocket client with ultra-stable streaming"""
        client_addr = websocket.remote_address

        # Enforce single client to prevent flicker
        if len(self.connected_clients) >= self.max_clients:
            logger.warning(f"Connection limit reached. Rejecting: {client_addr}")
            await websocket.close(code=1013, reason="Server busy - single client only")
            return

        logger.info(f"REAL camera client connected: {client_addr}")
        self.connected_clients.add(websocket)

        try:
            # Send connection confirmation
            await websocket.send(json.dumps({
                'type': 'connection_status',
                'status': 'connected',
                'message': 'R2D2 REAL C920e Camera Connected',
                'camera_type': 'real_webcam',
                'model': 'Logitech C920e'
            }))

            # Ultra-stable streaming loop
            last_send_time = time.time()

            while self.running:
                try:
                    # Get latest processed frame
                    processed_data = self.processed_frame_queue.get(timeout=0.1)

                    # Encode frame with optimal quality
                    encode_params = [cv2.IMWRITE_JPEG_QUALITY, 85]
                    _, buffer = cv2.imencode('.jpg', processed_data['frame'], encode_params)
                    frame_base64 = base64.b64encode(buffer).decode('utf-8')

                    # Prepare message
                    message = {
                        'type': 'character_vision_data',
                        'frame': frame_base64,
                        'detections': processed_data['detections'],
                        'character_detections': self._extract_character_detections(processed_data['detections']),
                        'timestamp': processed_data['timestamp'],
                        'stats': processed_data['stats'],
                        'camera_type': 'real_webcam',
                        'source': 'Logitech C920e'
                    }

                    # Send frame
                    await websocket.send(json.dumps(message))

                    # Precise timing control (12 FPS = 83.33ms interval)
                    current_time = time.time()
                    time_since_last = current_time - last_send_time

                    if time_since_last < self.frame_interval:
                        sleep_time = self.frame_interval - time_since_last
                        await asyncio.sleep(sleep_time)

                    last_send_time = time.time()

                except queue.Empty:
                    # Send heartbeat when no frames
                    await websocket.send(json.dumps({
                        'type': 'heartbeat',
                        'timestamp': datetime.now().isoformat(),
                        'camera_status': 'real_webcam_active'
                    }))
                    await asyncio.sleep(0.1)

                except websockets.exceptions.ConnectionClosed:
                    break
                except Exception as e:
                    logger.error(f"WebSocket send error: {e}")
                    break

        except websockets.exceptions.ConnectionClosed:
            logger.info(f"REAL camera client disconnected: {client_addr}")
        except Exception as e:
            logger.error(f"WebSocket client error: {e}")
        finally:
            self.connected_clients.discard(websocket)

    def _extract_character_detections(self, detections):
        """Extract character detections from person detections"""
        character_detections = []

        for detection in detections:
            if detection['class'] == 'person' and detection['confidence'] > 0.6:
                character_detections.append({
                    'name': 'Person Detected',
                    'character': 'unknown',
                    'confidence': detection['confidence'],
                    'bbox': detection['bbox'],
                    'r2d2_reaction': {
                        'primary_emotion': 'curious',
                        'excitement_level': 'medium',
                        'camera_source': 'real_webcam'
                    }
                })

        return character_detections

    async def _run_websocket_server(self):
        """Run the WebSocket server for real camera"""
        async with websockets.serve(
            self._handle_websocket_client_stable,
            "localhost",
            self.websocket_port
        ):
            logger.info(f"REAL Camera WebSocket server running on port {self.websocket_port}")
            await asyncio.Future()  # Run forever

    def start(self):
        """Start the ultra-stable real camera vision system"""
        logger.info("Starting R2D2 ULTRA-STABLE REAL CAMERA Vision System")

        # Initialize REAL camera
        if not self._initialize_camera():
            logger.error("Failed to initialize REAL C920e camera")
            return False

        logger.info("REAL C920e camera initialized successfully")

        self.running = True

        # Start capture thread
        capture_thread = threading.Thread(target=self._capture_frames_ultra_stable, daemon=True)
        capture_thread.start()

        # Start detection processing thread
        detection_thread = threading.Thread(target=self._process_detections_stable, daemon=True)
        detection_thread.start()

        logger.info(f"REAL Camera WebSocket server starting on port {self.websocket_port}")

        # Start WebSocket server
        try:
            asyncio.run(self._run_websocket_server())
        except KeyboardInterrupt:
            logger.info("Shutting down REAL Camera Vision System")
        finally:
            self.stop()

        return True

    def stop(self):
        """Stop the real camera vision system"""
        logger.info("Stopping REAL Camera Vision System")
        self.running = False

        if self.camera:
            self.camera.release()
            logger.info("REAL camera released")

        # Close WebSocket connections
        for client in self.connected_clients.copy():
            try:
                loop = asyncio.get_running_loop()
                loop.create_task(client.close())
            except RuntimeError:
                pass

def main():
    """Main function for ultra-stable real camera system"""
    print("R2D2 ULTRA-STABLE REAL CAMERA Vision System")
    print("=" * 50)
    print("REAL Logitech C920e Webcam - ZERO FLICKER")
    print("Press Ctrl+C to stop")
    print("=" * 50)

    # Default to camera index 0 (confirmed working)
    port = 8767
    camera_index = 0  # REAL C920e is on index 0

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

    # Create and start REAL camera vision system
    vision_system = UltraStableVisionSystem(websocket_port=port, camera_index=camera_index)

    try:
        success = vision_system.start()
        if not success:
            logger.error("Failed to start REAL camera vision system")
            sys.exit(1)
    except KeyboardInterrupt:
        logger.info("REAL camera vision system stopped by user")
    except Exception as e:
        logger.error(f"REAL camera vision system error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()