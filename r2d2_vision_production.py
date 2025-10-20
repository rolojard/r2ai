#!/usr/bin/env python3
"""
R2D2 Orin Nano Production Vision System
PRODUCTION-READY with ALL critical fixes applied:
- ✅ Fix #1: Camera initialization uses index 0
- ✅ Fix #2: Asyncio event loop non-blocking
- ✅ Fix #3: Memory leak eliminated
- ✅ Fix #4: Queue race conditions fixed (deque + locks)
- ✅ Fix #5: WebSocket timeout handling
- ✅ Fix #6: Thread cleanup and joining
- ✅ Fix #7: Proper exception handling (no bare except)
- ✅ Fix #8: Input validation with argparse
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
import argparse
from datetime import datetime
from typing import Dict, List, Any, Optional
from collections import deque
import sys
import os

# Import authentication module
from r2d2_auth_module import auth_manager, validate_websocket_token

# Import torch at module level for performance
try:
    import torch
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False
    torch = None

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class VisionSystemConfig:
    """Configuration class for vision system parameters"""
    # Camera settings
    CAMERA_WIDTH = 640
    CAMERA_HEIGHT = 480
    CAMERA_FPS = 15
    CAMERA_BUFFER_SIZE = 1

    # Queue settings (using deque with maxlen for automatic old-frame eviction)
    FRAME_QUEUE_MAXLEN = 1
    DETECTION_QUEUE_MAXLEN = 3

    # WebSocket settings
    DEFAULT_WS_PORT = 8767
    WS_SEND_TIMEOUT = 5.0  # seconds
    WS_STREAM_FPS = 12
    MAX_CLIENTS = 3

    # Performance settings
    JPEG_QUALITY = 85  # Optimized (not 98 which wastes bandwidth)
    TARGET_CAPTURE_FPS = 15

    # Threading settings
    THREAD_JOIN_TIMEOUT = 5.0  # seconds


class OrinNanoProductionVision:
    """Production-ready Orin Nano vision system with all critical fixes"""

    def __init__(self, websocket_port: int = VisionSystemConfig.DEFAULT_WS_PORT,
                 camera_device: int = 0) -> None:
        """Initialize vision system

        Args:
            websocket_port: WebSocket server port (1024-65535)
            camera_device: Camera device index (0, 1, 2, etc.)
        """
        self.websocket_port = websocket_port
        self.camera_device = camera_device
        self.running = False
        self.camera = None
        self.model = None
        self.loop = None  # Event loop reference

        # Thread tracking for proper cleanup (FIX #6)
        self.capture_thread: Optional[threading.Thread] = None
        self.detection_thread: Optional[threading.Thread] = None

        # Shared frame with lock (FIX #3: prevents memory leak from multiple copies)
        self.current_frame: Optional[np.ndarray] = None
        self.frame_lock = threading.Lock()

        # Detection queue with lock (FIX #4: thread-safe)
        self.detection_queue = deque(maxlen=VisionSystemConfig.DETECTION_QUEUE_MAXLEN)
        self.detection_queue_lock = threading.Lock()

        # WebSocket client tracking
        self.connected_clients = set()
        self.client_lock = threading.Lock()
        self.max_clients = VisionSystemConfig.MAX_CLIENTS

        # Hardware-optimized camera parameters
        self.camera_params = {
            'width': VisionSystemConfig.CAMERA_WIDTH,
            'height': VisionSystemConfig.CAMERA_HEIGHT,
            'fps': VisionSystemConfig.CAMERA_FPS,
            'format': cv2.CAP_PROP_FOURCC,
            'codec': cv2.VideoWriter_fourcc('M', 'J', 'P', 'G'),
            'buffer_size': VisionSystemConfig.CAMERA_BUFFER_SIZE,
            'auto_exposure': 3,
            'auto_white_balance': 1,
            'brightness': 128,
            'contrast': 42,
            'saturation': 100,
            'gain': 50,
            'sharpness': 140
        }

        # Performance statistics
        self.performance_stats = {
            'fps': 0.0,
            'detection_time': 0.0,
            'inference_fps': 0.0,
            'total_detections': 0,
            'confidence_threshold': 0.5,
            'gpu_memory_usage': 0.0,
            'capture_latency': 0.0
        }

        # Frame timing
        self.target_fps = VisionSystemConfig.TARGET_CAPTURE_FPS
        self.frame_interval = 1.0 / self.target_fps

        # FPS smoothing (exponential moving average)
        self.fps_smoothed = 0.0
        self.fps_alpha = 0.1  # Smoothing factor

        # Initialize model
        self._load_optimized_model()

    def _load_optimized_model(self) -> None:
        """Load YOLO model optimized for Orin Nano with TensorRT support"""
        try:
            if not TORCH_AVAILABLE:
                logger.error("PyTorch not available, cannot load model")
                self.model = None
                self.using_tensorrt = False
                return

            from ultralytics import YOLO
            logger.info("Loading YOLOv8n model optimized for Orin Nano...")

            # Try TensorRT engine first (2-3x speedup)
            tensorrt_engine = '/home/rolo/r2ai/yolov8n_fp16.engine'
            if os.path.exists(tensorrt_engine):
                logger.info(f"Loading TensorRT engine: {tensorrt_engine}")
                self.model = YOLO(tensorrt_engine, task='detect')
                self.using_tensorrt = True
                logger.info("TensorRT engine loaded successfully!")
            else:
                logger.info("TensorRT engine not found, using PyTorch model")
                self.model = YOLO('yolov8n.pt')
                self.using_tensorrt = False

                # Configure for GPU acceleration
                if torch.cuda.is_available():
                    device = torch.device('cuda:0')
                    self.model.to(device)
                    logger.info(f"YOLO model loaded on GPU: {torch.cuda.get_device_name(0)}")

                    # Optimize GPU memory
                    torch.cuda.empty_cache()
                    torch.backends.cudnn.benchmark = True
                else:
                    logger.warning("CUDA not available, using CPU")

                # Orin Nano optimized parameters
                self.model.overrides['verbose'] = False
                self.model.overrides['conf'] = 0.5
                self.model.overrides['iou'] = 0.45
                self.model.overrides['max_det'] = 100
                self.model.overrides['device'] = 'cuda:0' if torch.cuda.is_available() else 'cpu'

        except (RuntimeError, ValueError, OSError, ImportError) as e:
            logger.error(f"Failed to load YOLO model: {e}")
            self.model = None
            self.using_tensorrt = False

    def _initialize_camera_v4l2(self) -> bool:
        """Initialize camera with optimized V4L2 parameters"""
        try:
            logger.info(f"Initializing camera device index: {self.camera_device}")

            # Use V4L2 backend for hardware optimization
            self.camera = cv2.VideoCapture(self.camera_device, cv2.CAP_V4L2)

            if not self.camera.isOpened():
                logger.error(f"Failed to open camera device: {self.camera_device}")
                return False

            # Set hardware-optimized parameters
            param_success = []
            param_success.append(self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, self.camera_params['width']))
            param_success.append(self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, self.camera_params['height']))
            param_success.append(self.camera.set(cv2.CAP_PROP_FPS, self.camera_params['fps']))
            param_success.append(self.camera.set(cv2.CAP_PROP_BUFFERSIZE, self.camera_params['buffer_size']))
            param_success.append(self.camera.set(cv2.CAP_PROP_FOURCC, self.camera_params['codec']))
            param_success.append(self.camera.set(cv2.CAP_PROP_AUTO_EXPOSURE, self.camera_params['auto_exposure']))
            param_success.append(self.camera.set(cv2.CAP_PROP_AUTO_WB, self.camera_params['auto_white_balance']))

            # Image quality parameters
            try:
                self.camera.set(cv2.CAP_PROP_BRIGHTNESS, self.camera_params['brightness'])
                self.camera.set(cv2.CAP_PROP_CONTRAST, self.camera_params['contrast'])
                self.camera.set(cv2.CAP_PROP_SATURATION, self.camera_params['saturation'])
                self.camera.set(cv2.CAP_PROP_GAIN, self.camera_params['gain'])

                try:
                    self.camera.set(cv2.CAP_PROP_SHARPNESS, self.camera_params['sharpness'])
                except (RuntimeError, cv2.error):
                    pass  # Not all cameras support sharpness

                logger.info(f"Applied image quality settings: brightness={self.camera_params['brightness']}, "
                          f"contrast={self.camera_params['contrast']}, saturation={self.camera_params['saturation']}")
            except (RuntimeError, cv2.error) as e:
                logger.warning(f"Could not set all image quality parameters: {e}")

            # Disable auto focus for stability
            try:
                self.camera.set(cv2.CAP_PROP_AUTOFOCUS, 0)
            except (RuntimeError, cv2.error):
                pass

            logger.info(f"Camera parameter setup success rate: {sum(param_success)}/{len(param_success)}")

            # Verify settings
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

            # Warm-up period
            logger.info("Warming up camera (30 frames)...")
            for i in range(30):
                ret, _ = self.camera.read()
                if not ret:
                    logger.warning(f"Failed to capture warm-up frame {i+1}/30")

            # Capture test frame after warm-up
            ret, warmed_frame = self.camera.read()
            if ret:
                logger.info(f"Post-warmup frame: min={warmed_frame.min()}, max={warmed_frame.max()}, mean={warmed_frame.mean():.1f}")

            logger.info("Camera warm-up complete")
            return True

        except (RuntimeError, cv2.error, OSError) as e:
            logger.error(f"Camera initialization failed: {e}")
            return False

    def _capture_frames_hardware_optimized(self) -> None:
        """Hardware-optimized frame capture thread"""
        logger.info("Starting frame capture thread")
        frame_count = 0
        fps_start_time = time.time()

        while self.running:
            try:
                frame_start_time = time.perf_counter()

                # Read frame
                ret, frame = self.camera.read()
                if not ret:
                    logger.warning("Failed to capture frame")
                    time.sleep(0.01)
                    continue

                # Calculate capture latency
                capture_end_time = time.perf_counter()
                self.performance_stats['capture_latency'] = (capture_end_time - frame_start_time) * 1000

                # FPS calculation with smoothing
                frame_count += 1
                if frame_count % 30 == 0:
                    elapsed = time.time() - fps_start_time
                    instantaneous_fps = frame_count / elapsed

                    # Exponential moving average for smooth FPS
                    if self.fps_smoothed == 0:
                        self.fps_smoothed = instantaneous_fps
                    else:
                        self.fps_smoothed = (self.fps_alpha * instantaneous_fps +
                                           (1 - self.fps_alpha) * self.fps_smoothed)

                    self.performance_stats['fps'] = self.fps_smoothed
                    logger.info(f"[CAPTURE] FPS: {self.fps_smoothed:.1f} (instantaneous: {instantaneous_fps:.1f})")

                    frame_count = 0
                    fps_start_time = time.time()

                # FIX #3: Update shared frame with lock (NO extra copy, prevents memory leak)
                with self.frame_lock:
                    self.current_frame = frame

                # Precise frame timing
                current_time = time.perf_counter()
                elapsed_frame_time = current_time - frame_start_time
                sleep_time = max(0, self.frame_interval - elapsed_frame_time)

                if sleep_time > 0:
                    time.sleep(sleep_time)

            except (RuntimeError, cv2.error) as e:
                logger.error(f"Frame capture error: {e}")
                time.sleep(0.1)
            except Exception as e:
                logger.error(f"Unexpected frame capture error: {e}")
                time.sleep(0.1)

    def _process_detections_gpu_optimized(self) -> None:
        """GPU-optimized detection processing thread"""
        logger.info(f"Starting detection processing thread (model available: {self.model is not None})")
        frames_processed = 0
        detections_sent = 0

        while self.running:
            try:
                # FIX #3: Get reference to current frame (NO copy)
                frame = None
                with self.frame_lock:
                    if self.current_frame is not None:
                        frame = self.current_frame

                if frame is None:
                    time.sleep(0.01)
                    continue

                frames_processed += 1

                # If no model, just send frame
                if self.model is None:
                    annotated_frame = self._draw_detections_optimized(frame, [])
                    detection_data = {
                        'frame': annotated_frame,
                        'detections': [],
                        'timestamp': datetime.now().isoformat(),
                        'stats': self.performance_stats.copy()
                    }

                    with self.detection_queue_lock:
                        self.detection_queue.append(detection_data)
                        detections_sent += 1

                    time.sleep(0.05)  # Rate limit when no model
                    continue

                # GPU detection timing
                detection_start = time.perf_counter()

                # Force GPU inference
                if self.using_tensorrt:
                    results = self.model(frame, verbose=False, stream=False)
                else:
                    results = self.model(frame, verbose=False, stream=False, device='cuda:0')

                detection_end = time.perf_counter()
                self.performance_stats['detection_time'] = (detection_end - detection_start) * 1000

                # Calculate inference FPS
                inference_fps = (1000.0 / self.performance_stats['detection_time']
                               if self.performance_stats['detection_time'] > 0 else 0)
                self.performance_stats['inference_fps'] = inference_fps

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

                # Draw detections (makes a copy here, only place we need it)
                annotated_frame = self._draw_detections_optimized(frame, detections)

                # Update detection queue
                detection_data = {
                    'frame': annotated_frame,
                    'detections': detections,
                    'timestamp': datetime.now().isoformat(),
                    'stats': self.performance_stats.copy()
                }

                with self.detection_queue_lock:
                    self.detection_queue.append(detection_data)
                    detections_sent += 1

                if detections_sent % 10 == 0:
                    logger.info(f"[DETECTION] Processed: {detections_sent} | "
                              f"Inference: {inference_fps:.1f} FPS | "
                              f"Time: {self.performance_stats['detection_time']:.1f}ms | "
                              f"Detections: {len(detections)}")

                # Log GPU stats periodically
                if detections_sent % 30 == 0 and TORCH_AVAILABLE and torch.cuda.is_available():
                    try:
                        gpu_mem_allocated = torch.cuda.memory_allocated(0) / 1024**2
                        gpu_mem_reserved = torch.cuda.memory_reserved(0) / 1024**2
                        logger.info(f"[GPU] Memory: {gpu_mem_allocated:.1f}MB allocated, {gpu_mem_reserved:.1f}MB reserved")
                    except (RuntimeError, AttributeError):
                        pass

                self.performance_stats['total_detections'] += len(detections)

            except (RuntimeError, cv2.error) as e:
                logger.error(f"Detection processing error: {e}")
                time.sleep(0.1)
            except Exception as e:
                logger.error(f"Unexpected detection error: {e}")
                time.sleep(0.1)

    def _draw_detections_optimized(self, frame: np.ndarray, detections: List[Dict]) -> np.ndarray:
        """Draw detections on frame (makes copy here)"""
        annotated_frame = frame.copy()

        for detection in detections:
            x1, y1, x2, y2 = detection['bbox']
            confidence = detection['confidence']
            class_name = detection['class']

            color = self._get_class_color(detection['class_id'])
            cv2.rectangle(annotated_frame, (int(x1), int(y1)), (int(x2), int(y2)), color, 2)

            label = f"{class_name} {confidence:.2f}"
            cv2.putText(annotated_frame, label, (int(x1), int(y1) - 5),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)

        # Performance overlay
        perf_text = (f"Capture: {self.performance_stats['fps']:.1f} FPS | "
                    f"Inference: {self.performance_stats['inference_fps']:.1f} FPS | "
                    f"Det: {self.performance_stats['detection_time']:.1f}ms")

        cv2.putText(annotated_frame, perf_text, (10, 30),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

        return annotated_frame

    def _get_class_color(self, class_id: int) -> tuple:
        """Get consistent color for object class"""
        colors = [(255, 0, 0), (0, 255, 0), (0, 0, 255), (255, 255, 0), (255, 0, 255)]
        return colors[class_id % len(colors)]

    async def _handle_websocket_stable(self, websocket) -> None:
        """WebSocket handler with timeout and proper cleanup (FIX #5)"""
        client_addr = websocket.remote_address

        # AUTHENTICATION CHECK - Validate token from headers
        auth_valid = validate_websocket_token(websocket.request_headers)
        if not auth_valid:
            logger.warning(f"Unauthorized WebSocket connection attempt from {client_addr}")
            await websocket.close(code=1008, reason="Unauthorized - Invalid or missing token")
            return

        logger.info(f"Client authenticated successfully: {client_addr}")

        # Check client limit
        with self.client_lock:
            if len(self.connected_clients) >= self.max_clients:
                logger.warning(f"Connection limit reached. Rejecting: {client_addr}")
                await websocket.close(code=1013, reason="Server busy")
                return

            self.connected_clients.add(websocket)
            client_count = len(self.connected_clients)

        logger.info(f"Client connected: {client_addr} (total clients: {client_count})")

        try:
            # Send connection confirmation with timeout (FIX #5)
            await asyncio.wait_for(
                websocket.send(json.dumps({
                    'type': 'connection_status',
                    'status': 'connected',
                    'message': 'Orin Nano Vision System Connected'
                })),
                timeout=VisionSystemConfig.WS_SEND_TIMEOUT
            )

            # Streaming loop
            last_send_time = time.perf_counter()
            send_interval = 1.0 / VisionSystemConfig.WS_STREAM_FPS
            frames_sent = 0

            while self.running:
                try:
                    # Get detection data
                    detection_data = None
                    with self.detection_queue_lock:
                        if len(self.detection_queue) > 0:
                            detection_data = self.detection_queue.popleft()

                    if detection_data is None:
                        # Send heartbeat
                        await asyncio.wait_for(
                            websocket.send(json.dumps({
                                'type': 'heartbeat',
                                'timestamp': datetime.now().isoformat()
                            })),
                            timeout=VisionSystemConfig.WS_SEND_TIMEOUT
                        )
                        await asyncio.sleep(0.1)
                        continue

                    # Encode frame
                    encode_start = time.perf_counter()
                    frame = detection_data['frame']
                    _, buffer = cv2.imencode('.jpg', frame,
                                           [cv2.IMWRITE_JPEG_QUALITY, VisionSystemConfig.JPEG_QUALITY])
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

                    # Send with timeout (FIX #5)
                    await asyncio.wait_for(
                        websocket.send(json.dumps(message)),
                        timeout=VisionSystemConfig.WS_SEND_TIMEOUT
                    )
                    frames_sent += 1

                    if frames_sent % 30 == 0:
                        logger.info(f"[WEBSOCKET] Sent {frames_sent} frames to {client_addr}")

                    # Precise timing
                    current_time = time.perf_counter()
                    time_since_last = current_time - last_send_time
                    if time_since_last < send_interval:
                        await asyncio.sleep(send_interval - time_since_last)
                    last_send_time = time.perf_counter()

                except asyncio.TimeoutError:
                    logger.error(f"WebSocket send timeout for {client_addr}")
                    break
                except websockets.exceptions.ConnectionClosed:
                    break
                except Exception as e:
                    logger.error(f"WebSocket send error for {client_addr}: {e}")
                    break

        except Exception as e:
            logger.error(f"WebSocket error for {client_addr}: {e}")
        finally:
            with self.client_lock:
                self.connected_clients.discard(websocket)
                client_count = len(self.connected_clients)
            logger.info(f"Client disconnected: {client_addr} (remaining clients: {client_count})")

    def _extract_character_detections(self, detections: List[Dict]) -> List[Dict]:
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

    async def _run_websocket_server_async(self) -> None:
        """Run WebSocket server asynchronously"""
        async with websockets.serve(
            self._handle_websocket_stable,
            "0.0.0.0",
            self.websocket_port
        ):
            logger.info(f"WebSocket server running on port {self.websocket_port}")
            await asyncio.Future()  # Run forever

    def _run_websocket_server(self) -> None:
        """Run WebSocket server in separate event loop (FIX #2: non-blocking)"""
        logger.info("Starting WebSocket server in separate thread")

        # FIX #2: Create new event loop instead of using asyncio.run()
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)

        try:
            self.loop.run_until_complete(self._run_websocket_server_async())
        except Exception as e:
            logger.error(f"WebSocket server error: {e}")
        finally:
            # Proper cleanup
            logger.info("Closing WebSocket event loop")
            self.loop.run_until_complete(self.loop.shutdown_asyncgens())
            self.loop.close()

    def start(self) -> bool:
        """Start the vision system"""
        logger.info("=" * 70)
        logger.info("Starting Orin Nano Production Vision System")
        logger.info("=" * 70)

        # Initialize camera
        if not self._initialize_camera_v4l2():
            logger.error("Failed to initialize camera")
            return False

        if self.model is None:
            logger.warning("YOLO model not available, running camera only")

        self.running = True

        # Start threads (FIX #6: save references, not daemon for proper cleanup)
        self.capture_thread = threading.Thread(
            target=self._capture_frames_hardware_optimized,
            daemon=False,
            name="CaptureThread"
        )
        self.capture_thread.start()
        logger.info("✅ Capture thread started")

        # Verify thread started (FIX #6)
        time.sleep(0.1)
        if not self.capture_thread.is_alive():
            logger.error("❌ Capture thread failed to start!")
            self.running = False
            return False

        self.detection_thread = threading.Thread(
            target=self._process_detections_gpu_optimized,
            daemon=False,
            name="DetectionThread"
        )
        self.detection_thread.start()
        logger.info("✅ Detection thread started")

        # Verify thread started (FIX #6)
        time.sleep(0.1)
        if not self.detection_thread.is_alive():
            logger.error("❌ Detection thread failed to start!")
            self.running = False
            self.capture_thread.join(timeout=VisionSystemConfig.THREAD_JOIN_TIMEOUT)
            return False

        logger.info("✅ All threads verified and running")

        # Start WebSocket server (runs in main thread)
        try:
            self._run_websocket_server()
        except KeyboardInterrupt:
            logger.info("System stopped by user (Ctrl+C)")
        finally:
            self.stop()

        return True

    def stop(self) -> None:
        """Stop the vision system with proper cleanup (FIX #6)"""
        logger.info("=" * 70)
        logger.info("Stopping Vision System")
        logger.info("=" * 70)

        # Signal threads to stop
        self.running = False
        logger.info("Sent stop signal to threads")

        # Close all WebSocket connections first
        with self.client_lock:
            clients_to_close = list(self.connected_clients)

        logger.info(f"Closing {len(clients_to_close)} WebSocket connections...")
        for client in clients_to_close:
            try:
                asyncio.run_coroutine_threadsafe(
                    client.close(code=1001, reason="Server shutdown"),
                    self.loop
                ) if self.loop else None
            except Exception as e:
                logger.warning(f"Error closing client connection: {e}")

        with self.client_lock:
            self.connected_clients.clear()
        logger.info("✅ All WebSocket connections closed")

        # Wait for capture thread (FIX #6: proper join with timeout)
        if self.capture_thread and self.capture_thread.is_alive():
            logger.info("Waiting for capture thread to finish...")
            self.capture_thread.join(timeout=VisionSystemConfig.THREAD_JOIN_TIMEOUT)
            if self.capture_thread.is_alive():
                logger.warning("⚠️  Capture thread did not finish in time")
            else:
                logger.info("✅ Capture thread stopped")

        # Wait for detection thread (FIX #6)
        if self.detection_thread and self.detection_thread.is_alive():
            logger.info("Waiting for detection thread to finish...")
            self.detection_thread.join(timeout=VisionSystemConfig.THREAD_JOIN_TIMEOUT)
            if self.detection_thread.is_alive():
                logger.warning("⚠️  Detection thread did not finish in time")
            else:
                logger.info("✅ Detection thread stopped")

        # Release camera
        if self.camera:
            self.camera.release()
            logger.info("✅ Camera released")

        # Clean up GPU memory
        if TORCH_AVAILABLE and torch and torch.cuda.is_available():
            try:
                torch.cuda.empty_cache()
                logger.info("✅ GPU memory cleared")
            except (RuntimeError, AttributeError):
                pass

        logger.info("=" * 70)
        logger.info("Vision system stopped successfully")
        logger.info("=" * 70)


def validate_port(port: int) -> bool:
    """Validate port number (FIX #8)"""
    return 1024 <= port <= 65535


def validate_camera_device(device: int) -> bool:
    """Validate camera device index (FIX #8)"""
    return device >= 0 and os.path.exists(f'/dev/video{device}')


def main() -> int:
    """Main function with input validation (FIX #8)"""
    # FIX #8: Use argparse for proper input validation
    parser = argparse.ArgumentParser(
        description='R2D2 Orin Nano Production Vision System',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                          # Use defaults (port 8767, camera 0)
  %(prog)s --port 8080              # Custom port
  %(prog)s --camera 1               # Use /dev/video1
  %(prog)s --port 9000 --camera 0   # Custom port and camera
        """
    )

    parser.add_argument(
        '--port', '-p',
        type=int,
        default=VisionSystemConfig.DEFAULT_WS_PORT,
        help=f'WebSocket server port (1024-65535, default: {VisionSystemConfig.DEFAULT_WS_PORT})'
    )

    parser.add_argument(
        '--camera', '-c',
        type=int,
        default=0,
        help='Camera device index (0=/dev/video0, 1=/dev/video1, etc., default: 0)'
    )

    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose logging (DEBUG level)'
    )

    args = parser.parse_args()

    # Set logging level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
        logger.debug("Verbose logging enabled")

    # FIX #8: Validate port
    if not validate_port(args.port):
        logger.error(f"Invalid port {args.port}. Must be in range 1024-65535")
        return 1

    # FIX #8: Validate camera device
    if args.camera < 0:
        logger.error(f"Invalid camera device {args.camera}. Must be >= 0")
        return 1

    if not validate_camera_device(args.camera):
        logger.warning(f"Camera device /dev/video{args.camera} may not exist, will try anyway...")

    # Print banner
    print("\n" + "=" * 70)
    print("R2D2 ORIN NANO PRODUCTION VISION SYSTEM")
    print("=" * 70)
    print(f"WebSocket Port: {args.port}")
    print(f"Camera Device: {args.camera} (/dev/video{args.camera})")
    print(f"Target FPS: {VisionSystemConfig.TARGET_CAPTURE_FPS}")
    print(f"Stream FPS: {VisionSystemConfig.WS_STREAM_FPS}")
    print(f"JPEG Quality: {VisionSystemConfig.JPEG_QUALITY}")
    print("=" * 70)
    print("Press Ctrl+C to stop")
    print("=" * 70 + "\n")

    # Create and start system
    vision_system = OrinNanoProductionVision(
        websocket_port=args.port,
        camera_device=args.camera
    )

    try:
        success = vision_system.start()
        if not success:
            logger.error("Failed to start vision system")
            return 1
        return 0
    except KeyboardInterrupt:
        logger.info("System stopped by user")
        return 0
    except Exception as e:
        logger.error(f"System error: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
