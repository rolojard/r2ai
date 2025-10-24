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
from collections import deque
import sys
import os
import signal
import subprocess
import re

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class OrinNanoOptimizedVision:
    """Orin Nano optimized vision system with hardware-level anti-flickering"""

    def __init__(self, websocket_port=8767, camera_device=0):
        # Input validation - whitelist valid port range
        if not isinstance(websocket_port, int) or websocket_port < 1024 or websocket_port > 65535:
            raise ValueError(f"Invalid websocket_port: {websocket_port}. Must be integer between 1024-65535")

        # Input validation - whitelist valid camera device indices
        if not isinstance(camera_device, int) or camera_device < 0 or camera_device > 10:
            raise ValueError(f"Invalid camera_device: {camera_device}. Must be integer between 0-10")

        self.websocket_port = websocket_port
        self.camera_device = camera_device
        self.running = False
        self.camera = None
        self.model = None

        # Thread tracking for proper cleanup
        self.capture_thread = None
        self.detection_thread = None

        # Optimized queue sizes for Orin Nano memory management
        # Using deque with maxlen=1 for automatic old-frame eviction (prevents memory leak)
        self.frame_queue = deque(maxlen=1)  # Single frame buffer, auto-discards old frames
        self.frame_queue_lock = threading.Lock()  # Protect frame queue access
        self.detection_queue = deque(maxlen=3)  # Small detection buffer, auto-discards old
        self.detection_queue_lock = threading.Lock()  # Protect detection queue access
        self.connected_clients = set()
        self.max_clients = 3  # Allow dashboard + backup connections

        # Hardware-optimized parameters
        self.camera_params = {
            'width': 640,
            'height': 480,
            'fps': 15,  # Stable 15 FPS for consistent streaming
            'format': cv2.CAP_PROP_FOURCC,
            'codec': cv2.VideoWriter_fourcc('M', 'J', 'P', 'G'),  # Hardware MJPEG
            'buffer_size': 1,  # Minimal buffer to prevent flickering
            'auto_exposure': 3,  # V4L2 auto exposure mode 3 (aperture priority)
            'auto_white_balance': 1,  # Enable auto white balance
            'brightness': 128,  # Balanced brightness (0-255, default 128)
            'contrast': 42,  # Improved contrast for better separation
            'saturation': 100,  # OPTIMIZED: Increased saturation for vibrant, non-washed colors
            'gain': 50,  # Reduced gain to minimize noise/grain
            'sharpness': 140  # Enhanced sharpness for clearer, less grainy image
        }

        self.performance_stats = {
            'fps': 0,
            'detection_time': 0,
            'inference_fps': 0,
            'total_detections': 0,
            'confidence_threshold': 0.5,
            'gpu_memory_usage': 0,
            'capture_latency': 0,
            'gpu_utilization': 0,
            'gpu_memory_mb': 0,
            'temperature_c': 0,  # FIXED: Changed from temperature_celsius to match dashboard
            'cpu_utilization': 0,
            'system_memory_mb': 0
        }

        # GPU metrics collection thread
        self.metrics_thread = None
        self.last_metrics_update = 0
        self.metrics_update_interval = 0.5  # Update metrics every 500ms

        # Frame timing for flicker elimination
        self.target_fps = 15
        self.frame_interval = 1.0 / self.target_fps
        self.last_frame_time = 0

        # Initialize model
        self._load_optimized_model()

    def _load_optimized_model(self):
        """Load YOLO model optimized for Orin Nano with TensorRT support"""
        try:
            from ultralytics import YOLO
            import torch
            logger.info("Loading YOLOv8n model optimized for Orin Nano...")

            # CRITICAL FIX: Use TensorRT engine if available for 2-3x speedup
            tensorrt_engine = '/home/rolo/r2ai/yolov8n_fp16.engine'
            if os.path.exists(tensorrt_engine):
                logger.info(f"Loading TensorRT engine: {tensorrt_engine}")
                self.model = YOLO(tensorrt_engine, task='detect')
                self.using_tensorrt = True
                logger.info("TensorRT engine loaded successfully - 2-3x faster inference!")
            else:
                logger.info("TensorRT engine not found, using PyTorch model")
                # Use YOLOv8n for optimal performance on edge hardware
                self.model = YOLO('yolov8n.pt')
                self.using_tensorrt = False

                # Configure for Orin Nano GPU acceleration
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
                self.model.overrides['device'] = 'cuda:0' if torch.cuda.is_available() else 'cpu'

        except (RuntimeError, ValueError, OSError, ImportError) as e:
            logger.error(f"Failed to load YOLO model: {e}")
            self.model = None
            self.using_tensorrt = False

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

            # Image quality parameters - CRITICAL FIX for washed out and grainy video
            try:
                self.camera.set(cv2.CAP_PROP_BRIGHTNESS, self.camera_params['brightness'])
                self.camera.set(cv2.CAP_PROP_CONTRAST, self.camera_params['contrast'])
                self.camera.set(cv2.CAP_PROP_SATURATION, self.camera_params['saturation'])
                self.camera.set(cv2.CAP_PROP_GAIN, self.camera_params['gain'])

                # Try to set sharpness if supported by camera
                try:
                    self.camera.set(cv2.CAP_PROP_SHARPNESS, self.camera_params['sharpness'])
                except (RuntimeError, cv2.error):
                    pass  # Sharpness not supported by all cameras

                logger.info(f"Applied image quality settings: brightness={self.camera_params['brightness']}, "
                          f"contrast={self.camera_params['contrast']}, "
                          f"saturation={self.camera_params['saturation']}, "
                          f"gain={self.camera_params['gain']}")
            except (RuntimeError, cv2.error) as e:
                logger.warning(f"Could not set all image quality parameters: {e}")

            # Disable auto focus for stability (if supported)
            try:
                self.camera.set(cv2.CAP_PROP_AUTOFOCUS, 0)
            except (RuntimeError, cv2.error):
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

            # Warm-up period: Discard first 30 frames to allow auto-exposure to adjust
            logger.info("Warming up camera for auto-exposure adjustment...")
            for i in range(30):
                ret, _ = self.camera.read()
                if not ret:
                    logger.warning(f"Warning: Failed to capture warm-up frame {i+1}/30")

            # Capture a frame after warm-up to check brightness
            ret, warmed_frame = self.camera.read()
            if ret:
                logger.info(f"Post-warmup frame stats: min={warmed_frame.min()}, max={warmed_frame.max()}, mean={warmed_frame.mean():.1f}")

            logger.info("Camera warm-up complete")
            return True

        except Exception as e:
            logger.error(f"Camera initialization failed: {e}")
            return False

    def _capture_frames_hardware_optimized(self):
        """Hardware-optimized frame capture with precise timing"""
        logger.info("Starting hardware-optimized frame capture")
        frame_count = 0
        fps_start_time = time.time()
        total_frames_queued = 0

        while self.running:
            try:
                frame_start_time = time.perf_counter()

                # Read frame from camera
                ret, frame = self.camera.read()
                if not ret:
                    logger.warning("Failed to capture frame")
                    time.sleep(0.01)  # Brief pause before retry
                    continue

                # DEBUG: Check captured frame pixel data
                if frame_count % 30 == 0:  # Log every 30th frame
                    logger.info(f"[CAPTURE DEBUG] Raw frame - shape: {frame.shape}, dtype: {frame.dtype}, "
                              f"min: {frame.min()}, max: {frame.max()}, mean: {frame.mean():.1f}")
                    if frame.max() == 0:
                        logger.error(f"[CAPTURE DEBUG] ❌ CAPTURED FRAME IS ALL BLACK!")

                # Calculate actual capture latency
                capture_end_time = time.perf_counter()
                self.performance_stats['capture_latency'] = (capture_end_time - frame_start_time) * 1000

                # FPS calculation
                frame_count += 1
                if frame_count % 30 == 0:
                    elapsed = time.time() - fps_start_time
                    self.performance_stats['fps'] = frame_count / elapsed
                    with self.frame_queue_lock:
                        queue_size = len(self.frame_queue)
                    logger.info(f"[CAPTURE] FPS: {self.performance_stats['fps']:.1f}, Total frames queued: {total_frames_queued}, frame_queue size: {queue_size}")
                    frame_count = 0
                    fps_start_time = time.time()

                # Thread-safe atomic queue update with deque (auto-discards old frames)
                with self.frame_queue_lock:
                    self.frame_queue.append(frame.copy())  # deque with maxlen=1 auto-discards old
                    total_frames_queued += 1

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
        logger.info(f"Starting GPU-optimized detection processing (model available: {self.model is not None})")
        frames_processed = 0
        detections_sent = 0

        while self.running:
            try:
                # Get frame with timeout - thread-safe deque access
                frame = None
                with self.frame_queue_lock:
                    if len(self.frame_queue) > 0:
                        frame = self.frame_queue.popleft()

                if frame is None:
                    time.sleep(0.01)  # Brief wait if no frame available
                    continue

                frames_processed += 1

                if self.model is None:
                    logger.warning(f"[DETECTION] Model is None, skipping detection but still sending frame (frames processed: {frames_processed})")
                    # Even without model, send the frame to WebSocket
                    annotated_frame = self._draw_detections_optimized(frame, [])
                    detection_data = {
                        'frame': annotated_frame,
                        'detections': [],
                        'timestamp': datetime.now().isoformat(),
                        'stats': self.performance_stats.copy()
                    }

                    # Thread-safe atomic queue update with deque
                    with self.detection_queue_lock:
                        self.detection_queue.append(detection_data)  # deque auto-discards old
                        detections_sent += 1
                        queue_size = len(self.detection_queue)
                    if detections_sent % 10 == 0:
                        logger.info(f"[DETECTION] No model - sent {detections_sent} frames to detection_queue, queue size: {queue_size}")
                    continue

                # GPU detection timing
                detection_start = time.perf_counter()

                # CRITICAL FIX: Force GPU inference with explicit device parameter
                # Without this, model may fall back to CPU inference!
                if self.using_tensorrt:
                    # TensorRT engine already optimized for GPU
                    results = self.model(frame, verbose=False, stream=False)
                else:
                    # PyTorch model - MUST specify device='cuda:0' to force GPU usage
                    results = self.model(frame, verbose=False, stream=False, device='cuda:0')

                detection_end = time.perf_counter()
                self.performance_stats['detection_time'] = (detection_end - detection_start) * 1000

                # Calculate actual inference FPS (not capture FPS!)
                inference_fps = 1000.0 / self.performance_stats['detection_time'] if self.performance_stats['detection_time'] > 0 else 0
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

                # Draw detections
                annotated_frame = self._draw_detections_optimized(frame, detections)

                # Update detection queue
                detection_data = {
                    'frame': annotated_frame,
                    'detections': detections,
                    'timestamp': datetime.now().isoformat(),
                    'stats': self.performance_stats.copy()
                }

                # Thread-safe atomic queue update with deque
                with self.detection_queue_lock:
                    self.detection_queue.append(detection_data)  # deque auto-discards old
                    detections_sent += 1
                    queue_size = len(self.detection_queue)

                if detections_sent % 10 == 0:
                    logger.info(f"[DETECTION] Sent {detections_sent} frames | Inference: {inference_fps:.1f} FPS | "
                              f"Det time: {self.performance_stats['detection_time']:.1f}ms | "
                              f"Detections: {len(detections)} | Queue: {queue_size}")

                # Log GPU stats every 30 frames
                if detections_sent % 30 == 0:
                    try:
                        import torch
                        if torch.cuda.is_available():
                            gpu_mem_allocated = torch.cuda.memory_allocated(0) / 1024**2
                            gpu_mem_reserved = torch.cuda.memory_reserved(0) / 1024**2
                            logger.info(f"[GPU] Memory: {gpu_mem_allocated:.1f}MB allocated, {gpu_mem_reserved:.1f}MB reserved")
                    except (RuntimeError, ImportError):
                        pass

                self.performance_stats['total_detections'] += len(detections)

            except Exception as e:
                logger.error(f"Detection processing error: {e}")
                time.sleep(0.1)

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

        # Performance overlay with inference FPS
        perf_text = f"Capture: {self.performance_stats['fps']:.1f} FPS | " \
                   f"Inference: {self.performance_stats['inference_fps']:.1f} FPS | " \
                   f"Det: {self.performance_stats['detection_time']:.1f}ms"

        cv2.putText(annotated_frame, perf_text, (10, 30),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

        return annotated_frame

    def _get_class_color(self, class_id):
        """Get consistent color for object class"""
        colors = [(255, 0, 0), (0, 255, 0), (0, 0, 255), (255, 255, 0), (255, 0, 255)]
        return colors[class_id % len(colors)]

    def _collect_gpu_metrics(self):
        """Collect GPU utilization, memory, and temperature metrics for Orin Nano"""
        try:
            # Method 1: Try tegrastats (Orin Nano specific)
            try:
                result = subprocess.run(['tegrastats', '--interval', '100'],
                                      capture_output=True, text=True, timeout=0.3)
                if result.stdout:
                    # Parse tegrastats output
                    # Example: RAM 2047/7766MB (lfb 1x4MB) CPU [5%@1190,2%@1190,2%@1190,2%@1190,3%@1190,2%@1190]
                    # EMC_FREQ 0% GR3D_FREQ 0% VIC_FREQ 153 APE 150 MTS fg 0% bg 0% AO@34.5C GPU@33C
                    output = result.stdout

                    # GPU utilization from GR3D_FREQ
                    gpu_match = re.search(r'GR3D_FREQ\s+(\d+)%', output)
                    if gpu_match:
                        self.performance_stats['gpu_utilization'] = int(gpu_match.group(1))

                    # GPU temperature
                    temp_match = re.search(r'GPU@(\d+(?:\.\d+)?)C', output)
                    if temp_match:
                        self.performance_stats['temperature_c'] = float(temp_match.group(1))

                    # System memory
                    mem_match = re.search(r'RAM\s+(\d+)/(\d+)MB', output)
                    if mem_match:
                        self.performance_stats['system_memory_mb'] = int(mem_match.group(1))

                    # CPU utilization (average)
                    cpu_matches = re.findall(r'CPU\s+\[([\d%@,]+)\]', output)
                    if cpu_matches:
                        cpu_vals = re.findall(r'(\d+)%', cpu_matches[0])
                        if cpu_vals:
                            avg_cpu = sum(int(v) for v in cpu_vals) / len(cpu_vals)
                            self.performance_stats['cpu_utilization'] = round(avg_cpu, 1)

                    return
            except (subprocess.TimeoutExpired, FileNotFoundError, subprocess.CalledProcessError):
                pass

            # Method 2: Try nvidia-smi (general NVIDIA GPU)
            try:
                result = subprocess.run(['nvidia-smi', '--query-gpu=utilization.gpu,memory.used,temperature.gpu',
                                       '--format=csv,noheader,nounits'],
                                      capture_output=True, text=True, timeout=0.5)
                if result.returncode == 0 and result.stdout and '[N/A]' not in result.stdout:
                    parts = result.stdout.strip().split(',')
                    if len(parts) >= 3:
                        self.performance_stats['gpu_utilization'] = int(parts[0].strip())
                        self.performance_stats['gpu_memory_mb'] = float(parts[1].strip())
                        self.performance_stats['temperature_c'] = float(parts[2].strip())
                    return
            except (subprocess.TimeoutExpired, FileNotFoundError, subprocess.CalledProcessError, ValueError):
                pass

            # Method 3: Try PyTorch CUDA metrics (GPU memory only)
            try:
                import torch
                if torch.cuda.is_available():
                    self.performance_stats['gpu_memory_mb'] = torch.cuda.memory_allocated(0) / 1024**2
            except (RuntimeError, ImportError):
                pass

            # Method 4: Try reading /sys/class/thermal for temperature
            try:
                thermal_zones = ['/sys/class/thermal/thermal_zone0/temp',
                               '/sys/class/thermal/thermal_zone1/temp']
                for zone in thermal_zones:
                    if os.path.exists(zone):
                        with open(zone, 'r') as f:
                            temp = int(f.read().strip()) / 1000.0
                            if temp > 20 and temp < 100:  # Sanity check
                                self.performance_stats['temperature_c'] = temp
                                break
            except (IOError, ValueError):
                pass

            # Method 5: Try psutil for CPU and system memory
            try:
                import psutil
                self.performance_stats['cpu_utilization'] = psutil.cpu_percent(interval=0.1)
                mem = psutil.virtual_memory()
                self.performance_stats['system_memory_mb'] = mem.used / 1024**2
            except ImportError:
                pass

        except Exception as e:
            logger.error(f"Error collecting GPU metrics: {e}")

    def _gpu_metrics_collector_thread(self):
        """Background thread to continuously collect GPU metrics"""
        logger.info("Starting GPU metrics collector thread")
        metrics_count = 0

        while self.running:
            try:
                self._collect_gpu_metrics()
                metrics_count += 1

                if metrics_count % 10 == 0:
                    logger.info(f"[METRICS] GPU: {self.performance_stats['gpu_utilization']}%, "
                              f"Mem: {self.performance_stats['gpu_memory_mb']:.1f}MB, "
                              f"Temp: {self.performance_stats['temperature_c']}°C, "
                              f"CPU: {self.performance_stats['cpu_utilization']}%")

                time.sleep(self.metrics_update_interval)

            except Exception as e:
                logger.error(f"GPU metrics collection error: {e}")
                time.sleep(1.0)

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
            frames_sent = 0
            heartbeats_sent = 0

            while self.running:
                try:
                    # Get detection data - thread-safe deque access with timeout behavior
                    detection_data = None
                    with self.detection_queue_lock:
                        if len(self.detection_queue) > 0:
                            detection_data = self.detection_queue.popleft()

                    if detection_data is None:
                        # No data available, send heartbeat instead
                        raise queue.Empty

                    # DEBUG: Check frame pixel data
                    frame = detection_data['frame']
                    if frames_sent % 30 == 0:  # Log every 30th frame
                        logger.info(f"[FRAME DEBUG] shape: {frame.shape}, dtype: {frame.dtype}, "
                                  f"min: {frame.min()}, max: {frame.max()}, mean: {frame.mean():.1f}")
                        if frame.max() == 0:
                            logger.error(f"[FRAME DEBUG] ❌ FRAME IS ALL BLACK (all zeros)!")

                    # Encode frame with MAXIMUM quality (98) to eliminate compression artifacts
                    # This fixes grainy appearance from over-compression
                    encode_start = time.perf_counter()
                    _, buffer = cv2.imencode('.jpg', frame,
                                           [cv2.IMWRITE_JPEG_QUALITY, 98])
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
                    frames_sent += 1

                    if frames_sent % 10 == 0:
                        with self.detection_queue_lock:
                            queue_size = len(self.detection_queue)
                        logger.info(f"[WEBSOCKET] Sent {frames_sent} frames to client {client_addr}, detection_queue size: {queue_size}")

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
                    heartbeats_sent += 1
                    if heartbeats_sent % 50 == 0:
                        with self.detection_queue_lock:
                            queue_size = len(self.detection_queue)
                        logger.warning(f"[WEBSOCKET] Sent {heartbeats_sent} heartbeats (NO FRAMES), detection_queue size: {queue_size}")
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
        """Run WebSocket server with graceful shutdown"""
        loop = asyncio.get_running_loop()
        stop_future = loop.create_future()

        # Handle signals for graceful shutdown
        def signal_handler():
            if not stop_future.done():
                stop_future.set_result(None)

        for sig in (signal.SIGTERM, signal.SIGINT):
            loop.add_signal_handler(sig, signal_handler)

        async with websockets.serve(
            self._handle_websocket_stable,
            "0.0.0.0",  # Listen on all interfaces
            self.websocket_port
        ):
            logger.info(f"Orin Nano Vision WebSocket server running on port {self.websocket_port}")
            await stop_future  # Wait for signal

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

        # Start hardware-optimized threads (NOT daemon threads for proper cleanup)
        self.capture_thread = threading.Thread(target=self._capture_frames_hardware_optimized, daemon=False, name="CaptureThread")
        self.capture_thread.start()

        self.detection_thread = threading.Thread(target=self._process_detections_gpu_optimized, daemon=False, name="DetectionThread")
        self.detection_thread.start()

        # Start GPU metrics collector thread
        self.metrics_thread = threading.Thread(target=self._gpu_metrics_collector_thread, daemon=False, name="MetricsThread")
        self.metrics_thread.start()

        logger.info("All threads started successfully (capture, detection, metrics)")

        # Start WebSocket server
        try:
            asyncio.run(self._run_websocket_server())
        except KeyboardInterrupt:
            logger.info("Shutting down system")
        finally:
            self.stop()

        return True

    def stop(self):
        """Stop the vision system with proper thread cleanup"""
        logger.info("Stopping Orin Nano Vision System")
        self.running = False

        # Wait for threads to finish (with timeout)
        if self.capture_thread and self.capture_thread.is_alive():
            logger.info("Waiting for capture thread to finish...")
            self.capture_thread.join(timeout=5.0)
            if self.capture_thread.is_alive():
                logger.warning("Capture thread did not finish in time")

        if self.detection_thread and self.detection_thread.is_alive():
            logger.info("Waiting for detection thread to finish...")
            self.detection_thread.join(timeout=5.0)
            if self.detection_thread.is_alive():
                logger.warning("Detection thread did not finish in time")

        if self.metrics_thread and self.metrics_thread.is_alive():
            logger.info("Waiting for metrics thread to finish...")
            self.metrics_thread.join(timeout=5.0)
            if self.metrics_thread.is_alive():
                logger.warning("Metrics thread did not finish in time")

        # Release camera
        if self.camera:
            self.camera.release()
            logger.info("Camera released")

        # Clean up GPU memory
        try:
            import torch
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
                logger.info("GPU memory cleared")
        except (RuntimeError, ImportError):
            pass

        logger.info("Vision system stopped successfully")

def main():
    """Main function"""
    print("Orin Nano Optimized Vision System")
    print("=" * 50)
    print("Hardware-optimized real webcam with zero flickering")
    print("Press Ctrl+C to stop")
    print("=" * 50)

    # Parse arguments with input validation
    port = 8767
    camera_device = 0  # Integer device index (0 = /dev/video0)

    if len(sys.argv) > 1:
        try:
            port = int(sys.argv[1])
            if port < 1024 or port > 65535:
                logger.error(f"Port {port} out of valid range (1024-65535)")
                sys.exit(1)
        except ValueError:
            logger.error("Invalid port number, must be integer")
            sys.exit(1)

    if len(sys.argv) > 2:
        try:
            camera_device = int(sys.argv[2])
            if camera_device < 0 or camera_device > 10:
                logger.error(f"Camera device {camera_device} out of valid range (0-10)")
                sys.exit(1)
        except ValueError:
            logger.error("Invalid camera device, must be integer (0, 1, 2, etc.)")
            sys.exit(1)

    # Create and start system with validated inputs
    try:
        vision_system = OrinNanoOptimizedVision(websocket_port=port, camera_device=camera_device)
    except ValueError as e:
        logger.error(f"Invalid configuration: {e}")
        sys.exit(1)

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