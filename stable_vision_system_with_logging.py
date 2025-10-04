#!/usr/bin/env python3
"""
Stable Vision System with Integrated Logging
============================================

Enhanced version of the stable vision system with comprehensive logging.
This is a drop-in replacement that maintains all functionality while
adding structured logging capabilities.

Features:
- All original stable vision system functionality
- Comprehensive structured logging
- Performance monitoring
- WebSocket event tracking
- Memory-safe operation
- Agent-analyzable log output

Author: Expert Python Coder Agent
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
from datetime import datetime
from typing import Dict, List, Any, Optional
from contextlib import contextmanager

# Import optimization modules
try:
    from orin_nano_camera_resource_manager import acquire_camera, get_system_status
    from orin_nano_memory_optimizer import optimize_memory, start_monitoring, get_memory_status, emergency_cleanup
    OPTIMIZATIONS_AVAILABLE = True
except ImportError as e:
    OPTIMIZATIONS_AVAILABLE = False

# Import our logging framework
sys.path.append('/home/rolo/r2ai')
from r2d2_logging_framework import R2D2LoggerFactory

class StableVisionSystemWithLogging:
    """Ultra-stable vision system with integrated comprehensive logging"""

    def __init__(self, websocket_port=8767, camera_index=0, enable_logging=True):
        self.websocket_port = websocket_port
        self.camera_index = camera_index
        self.running = False

        # Initialize logging first
        self.enable_logging = enable_logging
        if enable_logging:
            self._initialize_logging()
        else:
            # Basic fallback logging
            logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
            self.logger = logging.getLogger(__name__)

        # System components
        self.camera = None
        self.model = None

        # Thread-safe queues
        self.frame_queue = queue.Queue(maxsize=2)
        self.detection_queue = queue.Queue(maxsize=5)

        # Client management
        self.connected_clients = set()
        self.max_clients = 3

        # Performance monitoring
        self.performance_stats = {
            'fps': 0,
            'detection_time': 0,
            'total_detections': 0,
            'confidence_threshold': 0.5,
            'memory_usage_mb': 0,
            'system_health': 'unknown',
            'uptime_seconds': 0,
            'error_count': 0,
            'recovery_count': 0
        }

        # Error recovery
        self.error_count = 0
        self.max_errors = 10
        self.recovery_delay = 1.0
        self.last_error_time = 0

        # Resource monitoring
        self.resource_monitor_active = False
        self.start_time = time.time()

        # Frame processing tracking
        self.frame_counter = 0
        self.last_performance_log = time.time()

        # Initialize optimizations if available
        if OPTIMIZATIONS_AVAILABLE:
            try:
                optimize_memory()
                start_monitoring(interval=10.0)
                if self.enable_logging:
                    self.logger.info("Memory optimizations enabled", extra={
                        "event_type": "optimization_enabled",
                        "optimization_type": "memory"
                    })
            except Exception as e:
                if self.enable_logging:
                    self.logger.warning("Failed to initialize optimizations", extra={
                        "event_type": "optimization_failed",
                        "error_message": str(e)
                    })

        # Load YOLO model
        self._load_yolo_model()

    def _initialize_logging(self):
        """Initialize comprehensive logging system"""
        try:
            self.logging_components = R2D2LoggerFactory.create_service_logger(
                "stable_vision_system",
                enable_performance_monitoring=True,
                enable_websocket_logging=True,
                enable_vision_logging=True
            )

            self.logger = self.logging_components["logger"]
            self.perf_logger = self.logging_components["performance_logger"]
            self.ws_logger = self.logging_components["websocket_logger"]
            self.vision_logger = self.logging_components["vision_logger"]

            self.logger.info("Comprehensive logging initialized", extra={
                "event_type": "logging_initialized",
                "websocket_port": self.websocket_port,
                "camera_index": self.camera_index
            })

        except Exception as e:
            # Fallback to basic logging
            logging.basicConfig(level=logging.INFO)
            self.logger = logging.getLogger(__name__)
            self.logger.error(f"Failed to initialize advanced logging: {e}")
            self.enable_logging = False

    def _load_yolo_model(self):
        """Load YOLO model with comprehensive logging"""
        try:
            if self.enable_logging:
                with self.perf_logger.measure_operation("yolo_model_loading"):
                    self._do_load_yolo_model()
            else:
                self._do_load_yolo_model()

        except Exception as e:
            if self.enable_logging:
                self.logger.error("Failed to load YOLO model", exc_info=True, extra={
                    "event_type": "model_load_error",
                    "error_message": str(e)
                })
            else:
                self.logger.error(f"Failed to load YOLO model: {e}")
            self.model = None

    def _do_load_yolo_model(self):
        """Actual YOLO model loading implementation"""
        from ultralytics import YOLO

        if self.enable_logging:
            self.logger.info("Loading YOLOv8 model", extra={
                "event_type": "model_load_start",
                "model_type": "yolov8n"
            })

        self.model = YOLO('yolov8n.pt')

        # GPU optimization if available
        import torch
        if torch.cuda.is_available():
            self.model.to('cuda')
            if self.enable_logging:
                self.logger.info("YOLO model loaded on GPU", extra={
                    "event_type": "model_load_complete",
                    "device": "cuda"
                })
        else:
            if self.enable_logging:
                self.logger.info("YOLO model loaded on CPU", extra={
                    "event_type": "model_load_complete",
                    "device": "cpu"
                })

        # Optimal settings for stability
        self.model.overrides['verbose'] = False
        self.model.overrides['conf'] = 0.5
        self.model.overrides['iou'] = 0.45
        self.model.overrides['max_det'] = 20

    def _check_system_health(self) -> Dict[str, Any]:
        """Check system health with logging"""
        try:
            if self.enable_logging:
                with self.perf_logger.measure_operation("health_check"):
                    health_status = self._do_health_check()
            else:
                health_status = self._do_health_check()

            # Log health warnings
            if self.enable_logging and not health_status.get('system_ready', False):
                self.logger.warning("System health warning detected", extra={
                    "event_type": "health_warning",
                    "health_status": health_status
                })

            return health_status

        except Exception as e:
            if self.enable_logging:
                self.logger.error("Health check failed", exc_info=True, extra={
                    "event_type": "health_check_error",
                    "error_message": str(e)
                })
            return {'system_ready': False, 'error': str(e)}

    def _do_health_check(self) -> Dict[str, Any]:
        """Actual health check implementation"""
        health_status = {
            'memory_ok': True,
            'system_ready': True,
            'camera_accessible': True,
            'error_rate_ok': True,
            'uptime_ok': True
        }

        # Check memory status
        if OPTIMIZATIONS_AVAILABLE:
            memory_status = get_memory_status()
            if 'error' not in memory_status:
                memory_percent = memory_status['system']['used_percent']
                health_status['memory_ok'] = memory_percent < 85
                health_status['memory_percent'] = memory_percent

        # Check error rate
        uptime = time.time() - self.start_time
        if uptime > 60:
            error_rate = self.error_count / uptime
            health_status['error_rate_ok'] = error_rate < 0.1

        # Check uptime
        health_status['uptime_ok'] = uptime < 3600
        health_status['uptime_seconds'] = uptime

        # Overall health
        health_status['system_ready'] = all([
            health_status['memory_ok'],
            health_status['error_rate_ok'],
            health_status['camera_accessible']
        ])

        return health_status

    def _safe_camera_operation(self, operation_func, *args, **kwargs):
        """Safely execute camera operations with comprehensive logging"""
        max_retries = 3
        retry_count = 0

        while retry_count < max_retries:
            try:
                return operation_func(*args, **kwargs)

            except Exception as e:
                retry_count += 1
                self.error_count += 1
                self.performance_stats['error_count'] = self.error_count

                if self.enable_logging:
                    self.logger.warning("Camera operation failed", extra={
                        "event_type": "camera_operation_retry",
                        "attempt": retry_count,
                        "max_retries": max_retries,
                        "error_message": str(e)
                    })

                if retry_count < max_retries:
                    time.sleep(self.recovery_delay * retry_count)

                    # Try emergency cleanup if memory related
                    if 'memory' in str(e).lower() or 'allocation' in str(e).lower():
                        if OPTIMIZATIONS_AVAILABLE:
                            emergency_cleanup()
                            if self.enable_logging:
                                self.logger.info("Emergency memory cleanup executed", extra={
                                    "event_type": "emergency_cleanup",
                                    "trigger": "memory_error"
                                })
                else:
                    if self.enable_logging:
                        self.logger.error("Camera operation failed after all retries", extra={
                            "event_type": "camera_operation_failed",
                            "retries": max_retries,
                            "error_message": str(e)
                        })
                    raise

        return None

    @contextmanager
    def _managed_camera_access(self):
        """Context manager for safe camera access with logging"""
        camera = None

        try:
            if OPTIMIZATIONS_AVAILABLE:
                with acquire_camera(self.camera_index) as managed_camera:
                    camera = managed_camera
                    if self.enable_logging:
                        self.logger.debug("Camera acquired via resource manager", extra={
                            "event_type": "camera_acquired",
                            "camera_index": self.camera_index,
                            "method": "resource_manager"
                        })
                    yield camera
            else:
                camera = cv2.VideoCapture(self.camera_index, cv2.CAP_V4L2)
                if not camera.isOpened():
                    raise RuntimeError(f"Failed to open camera {self.camera_index}")

                # Basic optimizations
                camera.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
                camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
                camera.set(cv2.CAP_PROP_FPS, 30)
                camera.set(cv2.CAP_PROP_BUFFERSIZE, 1)

                if self.enable_logging:
                    self.logger.debug("Camera acquired via direct access", extra={
                        "event_type": "camera_acquired",
                        "camera_index": self.camera_index,
                        "method": "direct_access"
                    })

                yield camera

        except Exception as e:
            if self.enable_logging:
                self.logger.error("Camera access error", exc_info=True, extra={
                    "event_type": "camera_access_error",
                    "camera_index": self.camera_index,
                    "error_message": str(e)
                })
            raise

        finally:
            if camera and not OPTIMIZATIONS_AVAILABLE:
                try:
                    camera.release()
                    if self.enable_logging:
                        self.logger.debug("Camera released", extra={
                            "event_type": "camera_released",
                            "method": "direct_access"
                        })
                except Exception as e:
                    if self.enable_logging:
                        self.logger.warning("Error releasing camera", extra={
                            "event_type": "camera_release_error",
                            "error_message": str(e)
                        })

    def _capture_frames_stable(self):
        """Stable frame capture with comprehensive logging"""
        if self.enable_logging:
            self.logger.info("Frame capture thread started", extra={
                "event_type": "frame_capture_start",
                "thread_id": threading.current_thread().ident
            })

        consecutive_failures = 0
        max_consecutive_failures = 10

        try:
            while self.running:
                try:
                    # Check system health before camera operations
                    health = self._check_system_health()
                    if not health['system_ready']:
                        if self.enable_logging:
                            self.logger.warning("System health check failed", extra={
                                "event_type": "health_check_failed",
                                "health_status": health
                            })
                        if OPTIMIZATIONS_AVAILABLE and not health.get('memory_ok', True):
                            emergency_cleanup()
                        time.sleep(2.0)
                        continue

                    # Safe camera operation
                    with self._managed_camera_access() as camera:
                        frame_count = 0
                        capture_start_time = time.time()

                        # Capture frames with this camera session
                        while self.running and consecutive_failures < max_consecutive_failures:
                            try:
                                ret, frame = self._safe_camera_operation(camera.read)

                                if ret and frame is not None:
                                    # Validate frame quality
                                    if self._is_frame_valid(frame):
                                        self.frame_counter += 1
                                        frame_id = f"frame_{self.frame_counter:06d}"

                                        # Add to queue (non-blocking)
                                        try:
                                            self.frame_queue.put_nowait(frame.copy())
                                            consecutive_failures = 0
                                            frame_count += 1

                                            # Log frame processing if enabled
                                            if self.enable_logging and self.frame_counter % 100 == 0:
                                                self.vision_logger.log_frame_processing(
                                                    frame_id, 0.033, frame.shape[:2], []
                                                )

                                            # Update FPS stats
                                            if frame_count % 30 == 0:
                                                elapsed = time.time() - capture_start_time
                                                self.performance_stats['fps'] = frame_count / elapsed

                                                # Periodic performance logging
                                                if self.enable_logging and time.time() - self.last_performance_log > 30:
                                                    self.logger.info("Frame capture performance update", extra={
                                                        "event_type": "performance_update",
                                                        "fps": self.performance_stats['fps'],
                                                        "frames_processed": self.frame_counter,
                                                        "uptime_seconds": time.time() - self.start_time
                                                    })
                                                    self.last_performance_log = time.time()

                                        except queue.Full:
                                            # Replace oldest frame
                                            try:
                                                self.frame_queue.get_nowait()
                                                self.frame_queue.put_nowait(frame.copy())
                                            except queue.Empty:
                                                pass
                                    else:
                                        consecutive_failures += 1
                                        if self.enable_logging:
                                            self.vision_logger.log_frame_error(
                                                f"frame_{self.frame_counter:06d}",
                                                "frame_validation_failed",
                                                f"Invalid frame quality (failure #{consecutive_failures})"
                                            )
                                else:
                                    consecutive_failures += 1
                                    if self.enable_logging:
                                        self.vision_logger.log_frame_error(
                                            f"frame_{self.frame_counter:06d}",
                                            "frame_read_failed",
                                            f"Failed to read frame (failure #{consecutive_failures})"
                                        )

                                # Adaptive frame rate based on system load
                                if OPTIMIZATIONS_AVAILABLE:
                                    memory_status = get_memory_status()
                                    if 'error' not in memory_status:
                                        memory_percent = memory_status['system']['used_percent']
                                        if memory_percent > 80:
                                            time.sleep(0.05)
                                        else:
                                            time.sleep(0.033)
                                    else:
                                        time.sleep(0.033)
                                else:
                                    time.sleep(0.033)

                            except Exception as e:
                                consecutive_failures += 1
                                if self.enable_logging:
                                    self.logger.error("Frame capture error", exc_info=True, extra={
                                        "event_type": "frame_capture_error",
                                        "consecutive_failures": consecutive_failures,
                                        "error_message": str(e)
                                    })
                                time.sleep(0.1)

                            # Break if too many consecutive failures
                            if consecutive_failures >= max_consecutive_failures:
                                if self.enable_logging:
                                    self.logger.error("Too many consecutive capture failures", extra={
                                        "event_type": "capture_failure_limit",
                                        "consecutive_failures": consecutive_failures,
                                        "max_failures": max_consecutive_failures
                                    })
                                break

                except Exception as e:
                    if self.enable_logging:
                        self.logger.error("Camera session error", exc_info=True, extra={
                            "event_type": "camera_session_error",
                            "error_message": str(e)
                        })
                    consecutive_failures += 1
                    time.sleep(self.recovery_delay)

                    # Emergency recovery
                    if consecutive_failures > 5:
                        if OPTIMIZATIONS_AVAILABLE:
                            emergency_cleanup()
                        self.performance_stats['recovery_count'] += 1
                        if self.enable_logging:
                            self.logger.warning("Emergency recovery executed", extra={
                                "event_type": "emergency_recovery",
                                "recovery_count": self.performance_stats['recovery_count']
                            })
                        time.sleep(5.0)

        finally:
            if self.enable_logging:
                self.logger.info("Frame capture thread stopped", extra={
                    "event_type": "frame_capture_stop",
                    "total_frames": self.frame_counter
                })

    def _is_frame_valid(self, frame) -> bool:
        """Validate frame quality with logging"""
        if frame is None or frame.size == 0:
            return False

        # Check for reasonable dimensions
        h, w = frame.shape[:2]
        if h < 100 or w < 100 or h > 2000 or w > 2000:
            return False

        # Check for completely black or white frames
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        mean_brightness = cv2.mean(gray)[0]

        if mean_brightness < 5 or mean_brightness > 250:
            return False

        return True

    def _process_detections_stable(self):
        """Stable detection processing with comprehensive logging"""
        if self.enable_logging:
            self.logger.info("Detection processing thread started", extra={
                "event_type": "detection_processing_start",
                "thread_id": threading.current_thread().ident
            })

        try:
            while self.running:
                try:
                    # Get frame from queue
                    frame = self.frame_queue.get(timeout=1.0)
                    frame_id = f"frame_{self.frame_counter:06d}"

                    if self.model is None:
                        # No model available, just process frame for display
                        processed_frame = self._add_system_info_overlay(frame)
                        detection_data = {
                            'frame': processed_frame,
                            'detections': [],
                            'timestamp': datetime.now().isoformat(),
                            'stats': self.performance_stats.copy()
                        }
                    else:
                        # Run YOLO detection with comprehensive logging
                        try:
                            if self.enable_logging:
                                with self.perf_logger.measure_operation("yolo_detection", frame_id=frame_id):
                                    detection_data = self._do_yolo_detection(frame, frame_id)
                            else:
                                detection_data = self._do_yolo_detection(frame, frame_id)

                        except Exception as e:
                            if self.enable_logging:
                                self.logger.error("Detection processing error", exc_info=True, extra={
                                    "event_type": "detection_error",
                                    "frame_id": frame_id,
                                    "error_message": str(e)
                                })
                            # Fallback to frame without detection
                            detection_data = {
                                'frame': self._add_system_info_overlay(frame),
                                'detections': [],
                                'timestamp': datetime.now().isoformat(),
                                'stats': self.performance_stats.copy()
                            }

                    # Add to detection queue
                    try:
                        self.detection_queue.put_nowait(detection_data)
                    except queue.Full:
                        # Replace oldest detection
                        try:
                            self.detection_queue.get_nowait()
                            self.detection_queue.put_nowait(detection_data)
                        except queue.Empty:
                            pass

                except queue.Empty:
                    continue
                except Exception as e:
                    if self.enable_logging:
                        self.logger.error("Detection processing error", exc_info=True, extra={
                            "event_type": "detection_processing_error",
                            "error_message": str(e)
                        })
                    time.sleep(0.1)

        finally:
            if self.enable_logging:
                self.logger.info("Detection processing thread stopped", extra={
                    "event_type": "detection_processing_stop"
                })

    def _do_yolo_detection(self, frame, frame_id):
        """Perform YOLO detection with logging"""
        start_time = time.time()
        results = self.model(frame, verbose=False)
        detection_time = time.time() - start_time

        self.performance_stats['detection_time'] = detection_time

        # Process results
        detections = self._extract_detections(results)
        annotated_frame = self._draw_detections(frame, detections)

        # Log detection results
        if self.enable_logging:
            self.vision_logger.log_detection_results(
                frame_id, detections, self.performance_stats['confidence_threshold']
            )

        return {
            'frame': annotated_frame,
            'detections': detections,
            'timestamp': datetime.now().isoformat(),
            'stats': self.performance_stats.copy()
        }

    def _extract_detections(self, results):
        """Extract detections from YOLO results"""
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
        """Draw detections with system overlay"""
        annotated_frame = self._add_system_info_overlay(frame)

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

            cv2.rectangle(annotated_frame,
                         (int(x1), int(y1) - label_size[1] - 10),
                         (int(x1) + label_size[0], int(y1)),
                         color, -1)

            cv2.putText(annotated_frame, label,
                       (int(x1), int(y1) - 5),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)

        return annotated_frame

    def _get_class_color(self, class_id):
        """Get consistent color for object class"""
        colors = [
            (255, 0, 0), (0, 255, 0), (0, 0, 255), (255, 255, 0),
            (255, 0, 255), (0, 255, 255), (128, 0, 128), (255, 165, 0)
        ]
        return colors[class_id % len(colors)]

    def _add_system_info_overlay(self, frame):
        """Add system information overlay to frame"""
        annotated_frame = frame.copy()

        # Update system stats
        self.performance_stats['uptime_seconds'] = time.time() - self.start_time

        if OPTIMIZATIONS_AVAILABLE:
            try:
                memory_status = get_memory_status()
                if 'error' not in memory_status:
                    self.performance_stats['memory_usage_mb'] = memory_status['process']['rss_mb']

                health = self._check_system_health()
                self.performance_stats['system_health'] = 'good' if health['system_ready'] else 'warning'
            except:
                pass

        # Draw system info
        cv2.putText(annotated_frame, "R2D2 STABLE VISION + LOGGING", (10, 30),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

        fps_text = f"FPS: {self.performance_stats['fps']:.1f}"
        cv2.putText(annotated_frame, fps_text, (10, 60),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

        uptime_text = f"Uptime: {int(self.performance_stats['uptime_seconds'])}s"
        cv2.putText(annotated_frame, uptime_text, (10, 90),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

        if self.performance_stats['memory_usage_mb'] > 0:
            memory_text = f"Memory: {self.performance_stats['memory_usage_mb']:.0f}MB"
            cv2.putText(annotated_frame, memory_text, (10, 120),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

        health_color = (0, 255, 0) if self.performance_stats['system_health'] == 'good' else (0, 255, 255)
        health_text = f"Health: {self.performance_stats['system_health']}"
        cv2.putText(annotated_frame, health_text, (10, 150),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, health_color, 2)

        # Show logging status
        log_status = "LOGGING: ON" if self.enable_logging else "LOGGING: OFF"
        log_color = (0, 255, 0) if self.enable_logging else (0, 0, 255)
        cv2.putText(annotated_frame, log_status, (10, 180),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, log_color, 2)

        return annotated_frame

    async def _handle_websocket_client(self, websocket):
        """Handle WebSocket client connections with comprehensive logging"""
        client_addr = websocket.remote_address
        client_id = f"client_{id(websocket)}"

        # Enforce connection limit
        if len(self.connected_clients) >= self.max_clients:
            if self.enable_logging:
                self.logger.warning("Connection limit reached", extra={
                    "event_type": "connection_rejected",
                    "client_address": str(client_addr),
                    "reason": "max_clients_reached",
                    "max_clients": self.max_clients
                })
            await websocket.close(code=1013, reason="Server busy")
            return

        # Log connection
        if self.enable_logging:
            self.ws_logger.log_connection(client_id, str(client_addr), "connected")

        self.connected_clients.add(websocket)

        try:
            # Send connection confirmation
            confirmation_message = {
                'type': 'connection_status',
                'status': 'connected',
                'message': 'R2D2 Stable Vision Connected (with Logging)',
                'optimizations_enabled': OPTIMIZATIONS_AVAILABLE,
                'logging_enabled': self.enable_logging
            }
            await websocket.send(json.dumps(confirmation_message))

            if self.enable_logging:
                self.ws_logger.log_message(
                    client_id, "sent", "connection_status",
                    len(json.dumps(confirmation_message).encode()), 0.001
                )

            # Main streaming loop
            while self.running:
                try:
                    # Get latest detection data
                    detection_data = self.detection_queue.get(timeout=0.1)

                    # Encode frame
                    encode_params = [cv2.IMWRITE_JPEG_QUALITY, 85]
                    _, buffer = cv2.imencode('.jpg', detection_data['frame'], encode_params)
                    frame_base64 = base64.b64encode(buffer).decode('utf-8')

                    # Prepare message
                    message = {
                        'type': 'vision_data',
                        'frame': frame_base64,
                        'detections': detection_data['detections'],
                        'timestamp': detection_data['timestamp'],
                        'stats': detection_data['stats']
                    }

                    # Send to client
                    send_start = time.time()
                    await websocket.send(json.dumps(message))
                    send_time = time.time() - send_start

                    # Log message
                    if self.enable_logging:
                        self.ws_logger.log_message(
                            client_id, "sent", "vision_data",
                            len(json.dumps(message).encode()), send_time
                        )

                    # Control frame rate
                    await asyncio.sleep(1.0 / 12)  # 12 FPS

                except queue.Empty:
                    # Send heartbeat
                    heartbeat = {
                        'type': 'heartbeat',
                        'timestamp': datetime.now().isoformat(),
                        'system_status': self.performance_stats.copy()
                    }
                    await websocket.send(json.dumps(heartbeat))

                    if self.enable_logging:
                        self.ws_logger.log_message(
                            client_id, "sent", "heartbeat",
                            len(json.dumps(heartbeat).encode()), 0.001
                        )

                    await asyncio.sleep(0.5)

                except websockets.exceptions.ConnectionClosed:
                    break
                except Exception as e:
                    if self.enable_logging:
                        self.ws_logger.log_error(client_id, "send_error", str(e))
                    break

        except websockets.exceptions.ConnectionClosed:
            if self.enable_logging:
                self.logger.info("Client disconnected normally", extra={
                    "event_type": "client_disconnected",
                    "client_id": client_id,
                    "client_address": str(client_addr)
                })
        except Exception as e:
            if self.enable_logging:
                self.logger.error("WebSocket client error", exc_info=True, extra={
                    "event_type": "websocket_client_error",
                    "client_id": client_id,
                    "error_message": str(e)
                })
        finally:
            self.connected_clients.discard(websocket)
            if self.enable_logging:
                self.ws_logger.log_connection(client_id, str(client_addr), "disconnected")

    async def _run_websocket_server(self):
        """Run the WebSocket server with logging"""
        if self.enable_logging:
            self.logger.info("Starting WebSocket server", extra={
                "event_type": "websocket_server_start",
                "port": self.websocket_port,
                "max_clients": self.max_clients
            })

        async with websockets.serve(
            self._handle_websocket_client,
            "localhost",
            self.websocket_port
        ):
            if self.enable_logging:
                self.logger.info("WebSocket server running", extra={
                    "event_type": "websocket_server_running",
                    "port": self.websocket_port
                })
            await asyncio.Future()  # Run forever

    def start(self):
        """Start the stable vision system with logging"""
        if self.enable_logging:
            self.logger.info("Starting R2D2 Stable Vision System with Logging", extra={
                "event_type": "system_start",
                "websocket_port": self.websocket_port,
                "camera_index": self.camera_index,
                "logging_enabled": self.enable_logging
            })

        # System health check
        health = self._check_system_health()
        if not health['system_ready']:
            if self.enable_logging:
                self.logger.warning("System health issues detected at startup", extra={
                    "event_type": "startup_health_warning",
                    "health_status": health
                })

        self.running = True

        # Start frame capture thread
        capture_thread = threading.Thread(target=self._capture_frames_stable, daemon=True)
        capture_thread.start()

        # Start detection processing thread
        detection_thread = threading.Thread(target=self._process_detections_stable, daemon=True)
        detection_thread.start()

        if self.enable_logging:
            self.logger.info("All threads started, launching WebSocket server", extra={
                "event_type": "threads_started",
                "websocket_port": self.websocket_port
            })

        try:
            asyncio.run(self._run_websocket_server())
        except KeyboardInterrupt:
            if self.enable_logging:
                self.logger.info("Shutting down due to keyboard interrupt", extra={
                    "event_type": "shutdown_interrupt"
                })
        finally:
            self.stop()

        return True

    def stop(self):
        """Stop the stable vision system with logging"""
        if self.enable_logging:
            self.logger.info("Stopping R2D2 Stable Vision System", extra={
                "event_type": "system_stop",
                "uptime_seconds": time.time() - self.start_time,
                "frames_processed": self.frame_counter
            })

        self.running = False

        # Stop memory monitoring if enabled
        if OPTIMIZATIONS_AVAILABLE:
            try:
                from orin_nano_memory_optimizer import stop_monitoring
                stop_monitoring()
                if self.enable_logging:
                    self.logger.info("Memory monitoring stopped", extra={
                        "event_type": "memory_monitoring_stopped"
                    })
            except Exception as e:
                if self.enable_logging:
                    self.logger.warning("Error stopping memory monitoring", extra={
                        "event_type": "memory_monitoring_stop_error",
                        "error_message": str(e)
                    })

        # Close WebSocket connections
        for client in self.connected_clients.copy():
            try:
                loop = asyncio.get_running_loop()
                loop.create_task(client.close())
            except RuntimeError:
                pass

        if self.enable_logging:
            # Final performance summary
            summary = {
                "total_frames_processed": self.frame_counter,
                "total_uptime_seconds": time.time() - self.start_time,
                "average_fps": self.frame_counter / (time.time() - self.start_time) if (time.time() - self.start_time) > 0 else 0,
                "error_count": self.error_count,
                "recovery_count": self.performance_stats['recovery_count']
            }
            self.logger.info("System shutdown complete", extra={
                "event_type": "system_shutdown_complete",
                "performance_summary": summary
            })

def main():
    """Main function with logging support"""
    print("🎯 R2D2 Stable Vision System with Comprehensive Logging")
    print("=" * 60)
    print("Enhanced with structured logging and performance monitoring")
    print("Press Ctrl+C to stop")
    print("=" * 60)

    # Parse arguments
    port = 8767
    camera_index = 0
    enable_logging = True

    if len(sys.argv) > 1:
        try:
            port = int(sys.argv[1])
        except ValueError:
            print("Error: Invalid port number")
            sys.exit(1)

    if len(sys.argv) > 2:
        try:
            camera_index = int(sys.argv[2])
        except ValueError:
            print("Error: Invalid camera index")
            sys.exit(1)

    if len(sys.argv) > 3:
        enable_logging = sys.argv[3].lower() in ['true', '1', 'yes', 'on']

    # Create and start vision system
    vision_system = StableVisionSystemWithLogging(
        websocket_port=port,
        camera_index=camera_index,
        enable_logging=enable_logging
    )

    try:
        success = vision_system.start()
        if not success:
            print("Error: Failed to start vision system")
            sys.exit(1)
    except KeyboardInterrupt:
        print("Vision system stopped by user")
    except Exception as e:
        print(f"Vision system error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()