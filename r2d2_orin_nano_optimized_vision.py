#!/usr/bin/env python3
"""
R2D2 Orin Nano Optimized Vision System
Hardware-optimized real webcam integration with zero flickering
Specifically designed for Nvidia Orin Nano with V4L2 and CUDA acceleration
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

class OrinNanoOptimizedVision:
    """Orin Nano optimized vision system with hardware-level anti-flickering"""

    def __init__(self, websocket_port=8767, camera_device='/dev/video0'):
        self.websocket_port = websocket_port
        self.camera_device = camera_device
        self.running = False
        self.camera = None
        self.model = None

        # Optimized queue sizes for Orin Nano memory management
        self.frame_queue = queue.Queue(maxsize=1)  # Single frame buffer to prevent lag
        self.detection_queue = queue.Queue(maxsize=3)  # Small detection buffer
        self.connected_clients = set()
        self.max_clients = 1  # Single client connection for stability

        # Hardware-optimized parameters
        self.camera_params = {
            'width': 640,
            'height': 480,
            'fps': 15,  # Stable 15 FPS for consistent streaming
            'format': cv2.CAP_PROP_FOURCC,
            'codec': cv2.VideoWriter_fourcc('M', 'J', 'P', 'G'),  # Hardware MJPEG
            'buffer_size': 1,  # Minimal buffer to prevent flickering
            'auto_exposure': 1,  # Enable auto exposure for lighting stability
            'auto_white_balance': 1  # Enable auto white balance
        }

        self.performance_stats = {
            'fps': 0,
            'detection_time': 0,
            'total_detections': 0,
            'confidence_threshold': 0.5,
            'gpu_memory_usage': 0,
            'capture_latency': 0
        }

        # Frame timing for flicker elimination
        self.target_fps = 15
        self.frame_interval = 1.0 / self.target_fps
        self.last_frame_time = 0

        # Initialize model
        self._load_optimized_model()

    def _load_optimized_model(self):
        """Load YOLO model optimized for Orin Nano"""
        try:
            from ultralytics import YOLO
            logger.info("Loading YOLOv8n model optimized for Orin Nano...")

            # Use YOLOv8n for optimal performance on edge hardware
            self.model = YOLO('yolov8n.pt')

            # Configure for Orin Nano GPU acceleration
            import torch
            if torch.cuda.is_available():
                device = torch.device('cuda:0')
                self.model.to(device)
                logger.info(f"YOLO model loaded on GPU: {torch.cuda.get_device_name(0)}")

                # Optimize GPU memory usage
                torch.cuda.empty_cache()
                torch.backends.cudnn.benchmark = True  # Optimize for consistent input sizes

            else:
                logger.warning("CUDA not available, using CPU")

            # Orin Nano optimized parameters
            self.model.overrides['verbose'] = False
            self.model.overrides['conf'] = 0.5  # Confidence threshold
            self.model.overrides['iou'] = 0.45   # IoU threshold
            self.model.overrides['max_det'] = 100  # Limit detections for performance
            self.model.overrides['device'] = 'cuda' if torch.cuda.is_available() else 'cpu'

        except Exception as e:
            logger.error(f"Failed to load YOLO model: {e}")
            self.model = None

    def _initialize_camera_v4l2(self):
        """Initialize camera with optimized V4L2 parameters for Orin Nano"""
        try:
            logger.info(f"Initializing camera: {self.camera_device}")

            # Use V4L2 backend explicitly for hardware optimization
            self.camera = cv2.VideoCapture(self.camera_device, cv2.CAP_V4L2)

            if not self.camera.isOpened():
                logger.error(f"Failed to open camera device: {self.camera_device}")
                return False

            # Set hardware-optimized camera parameters
            param_success = []

            # Set frame dimensions
            param_success.append(self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, self.camera_params['width']))
            param_success.append(self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, self.camera_params['height']))

            # Set FPS for consistent timing
            param_success.append(self.camera.set(cv2.CAP_PROP_FPS, self.camera_params['fps']))

            # Critical: Set buffer size to 1 to eliminate flickering
            param_success.append(self.camera.set(cv2.CAP_PROP_BUFFERSIZE, self.camera_params['buffer_size']))

            # Set hardware codec for better performance
            param_success.append(self.camera.set(cv2.CAP_PROP_FOURCC, self.camera_params['codec']))

            # Auto exposure and white balance for stability
            param_success.append(self.camera.set(cv2.CAP_PROP_AUTO_EXPOSURE, self.camera_params['auto_exposure']))
            param_success.append(self.camera.set(cv2.CAP_PROP_AUTO_WB, self.camera_params['auto_white_balance']))

            # Disable auto focus for stability (if supported)
            try:
                self.camera.set(cv2.CAP_PROP_AUTOFOCUS, 0)
            except:
                pass  # Not all cameras support this

            logger.info(f"Camera parameter setup success rate: {sum(param_success)}/{len(param_success)}")

            # Verify actual settings
            actual_width = int(self.camera.get(cv2.CAP_PROP_FRAME_WIDTH))
            actual_height = int(self.camera.get(cv2.CAP_PROP_FRAME_HEIGHT))
            actual_fps = self.camera.get(cv2.CAP_PROP_FPS)
            actual_buffer = int(self.camera.get(cv2.CAP_PROP_BUFFERSIZE))

            logger.info(f"Camera configured: {actual_width}x{actual_height} @ {actual_fps}fps, buffer: {actual_buffer}")

            # Test frame capture
            ret, frame = self.camera.read()
            if not ret:
                logger.error("Failed to capture test frame")
                return False

            logger.info(f"Camera successfully initialized: {frame.shape}")
            return True

        except Exception as e:
            logger.error(f"Camera initialization failed: {e}")
            return False

    def _capture_frames_hardware_optimized(self):
        """Hardware-optimized frame capture with precise timing"""
        logger.info("Starting hardware-optimized frame capture")
        frame_count = 0
        fps_start_time = time.time()

        while self.running:
            try:
                frame_start_time = time.perf_counter()

                # Read frame from camera
                ret, frame = self.camera.read()
                if not ret:
                    logger.warning("Failed to capture frame")
                    time.sleep(0.01)  # Brief pause before retry
                    continue

                # Calculate actual capture latency
                capture_end_time = time.perf_counter()
                self.performance_stats['capture_latency'] = (capture_end_time - frame_start_time) * 1000

                # FPS calculation
                frame_count += 1
                if frame_count % 30 == 0:
                    elapsed = time.time() - fps_start_time
                    self.performance_stats['fps'] = frame_count / elapsed
                    frame_count = 0
                    fps_start_time = time.time()

                # Non-blocking queue update to prevent frame stacking
                if not self.frame_queue.full():
                    self.frame_queue.put_nowait(frame.copy())
                else:
                    # Replace old frame with new one
                    try:
                        self.frame_queue.get_nowait()
                        self.frame_queue.put_nowait(frame.copy())
                    except queue.Empty:
                        self.frame_queue.put_nowait(frame.copy())

                # Precise frame timing to eliminate flicker
                current_time = time.perf_counter()
                elapsed_frame_time = current_time - frame_start_time
                sleep_time = max(0, self.frame_interval - elapsed_frame_time)

                if sleep_time > 0:
                    time.sleep(sleep_time)

            except Exception as e:
                logger.error(f"Frame capture error: {e}")
                time.sleep(0.1)

    def _process_detections_gpu_optimized(self):
        """GPU-optimized detection processing"""
        logger.info("Starting GPU-optimized detection processing")

        while self.running:
            try:
                # Get frame with timeout
                frame = self.frame_queue.get(timeout=1.0)

                if self.model is None:
                    continue

                # GPU detection timing
                detection_start = time.perf_counter()

                # Run inference with GPU optimization
                results = self.model(frame, verbose=False, stream=False)

                detection_end = time.perf_counter()
                self.performance_stats['detection_time'] = (detection_end - detection_start) * 1000

                # Process results
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

                # Draw detections
                annotated_frame = self._draw_detections_optimized(frame, detections)

                # Update detection queue
                detection_data = {
                    'frame': annotated_frame,
                    'detections': detections,
                    'timestamp': datetime.now().isoformat(),
                    'stats': self.performance_stats.copy()
                }

                # Non-blocking queue update
                if not self.detection_queue.full():
                    self.detection_queue.put_nowait(detection_data)
                else:
                    try:
                        self.detection_queue.get_nowait()
                        self.detection_queue.put_nowait(detection_data)
                    except queue.Empty:
                        self.detection_queue.put_nowait(detection_data)

                self.performance_stats['total_detections'] += len(detections)

            except queue.Empty:
                continue
            except Exception as e:
                logger.error(f"Detection processing error: {e}")

    def _draw_detections_optimized(self, frame, detections):
        """Optimized detection drawing for Orin Nano"""
        annotated_frame = frame.copy()

        for detection in detections:
            x1, y1, x2, y2 = detection['bbox']
            confidence = detection['confidence']
            class_name = detection['class']

            # Optimized drawing with reduced complexity
            color = self._get_class_color(detection['class_id'])
            cv2.rectangle(annotated_frame, (int(x1), int(y1)), (int(x2), int(y2)), color, 2)

            # Simplified label drawing
            label = f"{class_name} {confidence:.2f}"
            cv2.putText(annotated_frame, label, (int(x1), int(y1) - 5),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)

        # Performance overlay
        perf_text = f"FPS: {self.performance_stats['fps']:.1f} | " \
                   f"Det: {self.performance_stats['detection_time']:.1f}ms | " \
                   f"Cap: {self.performance_stats['capture_latency']:.1f}ms"

        cv2.putText(annotated_frame, perf_text, (10, 30),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

        return annotated_frame

    def _get_class_color(self, class_id):
        """Get consistent color for object class"""
        colors = [(255, 0, 0), (0, 255, 0), (0, 0, 255), (255, 255, 0), (255, 0, 255)]
        return colors[class_id % len(colors)]

    async def _handle_websocket_stable(self, websocket):
        """Stable WebSocket handler with connection limiting"""
        client_addr = websocket.remote_address

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
                'message': 'Orin Nano Vision System Connected'
            }))

            # Stable streaming with precise timing
            last_send_time = time.perf_counter()
            send_interval = 1.0 / 12  # Fixed 12 FPS for web streaming stability

            while self.running:
                try:
                    # Get detection data
                    detection_data = self.detection_queue.get(timeout=0.1)

                    # Encode frame with optimized quality
                    encode_start = time.perf_counter()
                    _, buffer = cv2.imencode('.jpg', detection_data['frame'],
                                           [cv2.IMWRITE_JPEG_QUALITY, 85])
                    frame_base64 = base64.b64encode(buffer).decode('utf-8')
                    encode_time = (time.perf_counter() - encode_start) * 1000

                    # Prepare message
                    message = {
                        'type': 'character_vision_data',
                        'frame': frame_base64,
                        'detections': detection_data['detections'],
                        'character_detections': self._extract_character_detections(detection_data['detections']),
                        'timestamp': detection_data['timestamp'],
                        'stats': {
                            **detection_data['stats'],
                            'encode_time': encode_time
                        }
                    }

                    # Send with timing control
                    await websocket.send(json.dumps(message))

                    # Precise timing for flicker-free streaming
                    current_time = time.perf_counter()
                    time_since_last = current_time - last_send_time
                    if time_since_last < send_interval:
                        await asyncio.sleep(send_interval - time_since_last)
                    last_send_time = time.perf_counter()

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

        except Exception as e:
            logger.error(f"WebSocket error: {e}")
        finally:
            self.connected_clients.discard(websocket)
            logger.info(f"Client disconnected: {client_addr}")

    def _extract_character_detections(self, detections):
        """Extract character detections from YOLO results"""
        character_detections = []

        for detection in detections:
            if detection['class'] == 'person' and detection['confidence'] > 0.6:
                character_detections.append({
                    'name': 'Detected Person',
                    'character': 'person',
                    'confidence': detection['confidence'],
                    'bbox': detection['bbox'],
                    'r2d2_reaction': {
                        'primary_emotion': 'curious',
                        'excitement_level': 'medium'
                    }
                })

        return character_detections

    async def _run_websocket_server(self):
        """Run WebSocket server"""
        async with websockets.serve(
            self._handle_websocket_stable,
            "0.0.0.0",  # Listen on all interfaces
            self.websocket_port
        ):
            logger.info(f"Orin Nano Vision WebSocket server running on port {self.websocket_port}")
            await asyncio.Future()  # Run forever

    def start(self):
        """Start the optimized vision system"""
        logger.info("Starting Orin Nano Optimized Vision System")

        # Initialize camera with V4L2 optimization
        if not self._initialize_camera_v4l2():
            logger.error("Failed to initialize camera")
            return False

        if self.model is None:
            logger.warning("YOLO model not available, running camera only")

        self.running = True

        # Start hardware-optimized threads
        capture_thread = threading.Thread(target=self._capture_frames_hardware_optimized, daemon=True)
        capture_thread.start()

        detection_thread = threading.Thread(target=self._process_detections_gpu_optimized, daemon=True)
        detection_thread.start()

        logger.info("All threads started successfully")

        # Start WebSocket server
        try:
            asyncio.run(self._run_websocket_server())
        except KeyboardInterrupt:
            logger.info("Shutting down system")
        finally:
            self.stop()

        return True

    def stop(self):
        """Stop the vision system"""
        logger.info("Stopping Orin Nano Vision System")
        self.running = False

        if self.camera:
            self.camera.release()

        # Clean up GPU memory
        try:
            import torch
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
        except:
            pass

def main():
    """Main function"""
    print("Orin Nano Optimized Vision System")
    print("=" * 50)
    print("Hardware-optimized real webcam with zero flickering")
    print("Press Ctrl+C to stop")
    print("=" * 50)

    # Parse arguments
    port = 8767
    camera_device = '/dev/video0'  # Direct device access

    if len(sys.argv) > 1:
        try:
            port = int(sys.argv[1])
        except ValueError:
            logger.error("Invalid port number")
            sys.exit(1)

    if len(sys.argv) > 2:
        camera_device = sys.argv[2]

    # Create and start system
    vision_system = OrinNanoOptimizedVision(websocket_port=port, camera_device=camera_device)

    try:
        success = vision_system.start()
        if not success:
            logger.error("Failed to start vision system")
            sys.exit(1)
    except KeyboardInterrupt:
        logger.info("System stopped by user")
    except Exception as e:
        logger.error(f"System error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()