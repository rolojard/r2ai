#!/usr/bin/env python3
"""
Stable Vision System for R2D2
Integrates camera resource management, memory optimization, and error recovery
Designed to prevent crashes and ensure consistent operation
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

# Import our optimization modules
try:
    from orin_nano_camera_resource_manager import acquire_camera, get_system_status
    from orin_nano_memory_optimizer import optimize_memory, start_monitoring, get_memory_status, emergency_cleanup
    OPTIMIZATIONS_AVAILABLE = True
except ImportError as e:
    logging.warning(f"Optimization modules not available: {e}")
    OPTIMIZATIONS_AVAILABLE = False

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class StableVisionSystem:
    """Ultra-stable vision system with integrated resource management"""

    def __init__(self, websocket_port=8767, camera_index=0):
        self.websocket_port = websocket_port
        self.camera_index = camera_index
        self.running = False

        # System components
        self.camera = None
        self.model = None

        # Thread-safe queues
        self.frame_queue = queue.Queue(maxsize=2)
        self.detection_queue = queue.Queue(maxsize=5)

        # Client management
        self.connected_clients = set()
        self.max_clients = 3  # Allow multiple dashboard connections

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

        # Initialize optimizations if available
        if OPTIMIZATIONS_AVAILABLE:
            try:
                optimize_memory()
                start_monitoring(interval=10.0)  # Monitor every 10 seconds
                logger.info("Memory optimizations and monitoring enabled")
            except Exception as e:
                logger.warning(f"Failed to initialize optimizations: {e}")

        # Load YOLO model
        self._load_yolo_model()

    def _load_yolo_model(self):
        """Load YOLO model with error handling"""
        try:
            from ultralytics import YOLO
            logger.info("Loading YOLOv8 model...")

            self.model = YOLO('yolov8n.pt')

            # GPU optimization if available
            import torch
            if torch.cuda.is_available():
                self.model.to('cuda')
                logger.info("YOLO model loaded on GPU")
            else:
                logger.info("YOLO model loaded on CPU")

            # Optimal settings for stability
            self.model.overrides['verbose'] = False
            self.model.overrides['conf'] = 0.5
            self.model.overrides['iou'] = 0.45
            self.model.overrides['max_det'] = 20  # Limit detections for performance

        except Exception as e:
            logger.error(f"Failed to load YOLO model: {e}")
            self.model = None

    def _check_system_health(self) -> Dict[str, Any]:
        """Check system health and resource status"""
        try:
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
            if uptime > 60:  # Only check after 1 minute of operation
                error_rate = self.error_count / uptime
                health_status['error_rate_ok'] = error_rate < 0.1  # Less than 0.1 errors/second

            # Check uptime
            health_status['uptime_ok'] = uptime < 3600  # Restart every hour for stability
            health_status['uptime_seconds'] = uptime

            # Overall health
            health_status['system_ready'] = all([
                health_status['memory_ok'],
                health_status['error_rate_ok'],
                health_status['camera_accessible']
            ])

            return health_status

        except Exception as e:
            logger.error(f"Error checking system health: {e}")
            return {'system_ready': False, 'error': str(e)}

    def _safe_camera_operation(self, operation_func, *args, **kwargs):
        """Safely execute camera operations with error recovery"""
        max_retries = 3
        retry_count = 0

        while retry_count < max_retries:
            try:
                return operation_func(*args, **kwargs)

            except Exception as e:
                retry_count += 1
                self.error_count += 1
                self.performance_stats['error_count'] = self.error_count

                logger.warning(f"Camera operation failed (attempt {retry_count}): {e}")

                if retry_count < max_retries:
                    time.sleep(self.recovery_delay * retry_count)

                    # Try emergency cleanup if memory related
                    if 'memory' in str(e).lower() or 'allocation' in str(e).lower():
                        if OPTIMIZATIONS_AVAILABLE:
                            emergency_cleanup()
                else:
                    logger.error(f"Camera operation failed after {max_retries} attempts")
                    raise

        return None

    @contextmanager
    def _managed_camera_access(self):
        """Context manager for safe camera access using resource manager"""
        camera = None

        try:
            if OPTIMIZATIONS_AVAILABLE:
                # Use optimized camera resource manager
                with acquire_camera(self.camera_index) as managed_camera:
                    camera = managed_camera
                    yield camera
            else:
                # Fallback to basic camera access
                camera = cv2.VideoCapture(self.camera_index, cv2.CAP_V4L2)
                if not camera.isOpened():
                    raise RuntimeError(f"Failed to open camera {self.camera_index}")

                # Basic optimizations
                camera.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
                camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
                camera.set(cv2.CAP_PROP_FPS, 30)
                camera.set(cv2.CAP_PROP_BUFFERSIZE, 1)

                yield camera

        except Exception as e:
            logger.error(f"Camera access error: {e}")
            raise

        finally:
            if camera and not OPTIMIZATIONS_AVAILABLE:
                try:
                    camera.release()
                except:
                    pass

    def _capture_frames_stable(self):
        """Stable frame capture with error recovery"""
        logger.info("Starting stable frame capture thread")

        consecutive_failures = 0
        max_consecutive_failures = 10

        while self.running:
            try:
                # Check system health before camera operations
                health = self._check_system_health()
                if not health['system_ready']:
                    logger.warning(f"System health check failed: {health}")
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
                                    # Add to queue (non-blocking)
                                    try:
                                        self.frame_queue.put_nowait(frame.copy())
                                        consecutive_failures = 0
                                        frame_count += 1

                                        # Update FPS stats
                                        if frame_count % 30 == 0:
                                            elapsed = time.time() - capture_start_time
                                            self.performance_stats['fps'] = frame_count / elapsed

                                    except queue.Full:
                                        # Replace oldest frame
                                        try:
                                            self.frame_queue.get_nowait()
                                            self.frame_queue.put_nowait(frame.copy())
                                        except queue.Empty:
                                            pass
                                else:
                                    consecutive_failures += 1
                                    logger.warning(f"Invalid frame quality (failure #{consecutive_failures})")
                            else:
                                consecutive_failures += 1
                                logger.warning(f"Failed to read frame (failure #{consecutive_failures})")

                            # Adaptive frame rate based on system load
                            if OPTIMIZATIONS_AVAILABLE:
                                memory_status = get_memory_status()
                                if 'error' not in memory_status:
                                    memory_percent = memory_status['system']['used_percent']
                                    if memory_percent > 80:
                                        time.sleep(0.05)  # Slower capture if memory constrained
                                    else:
                                        time.sleep(0.033)  # ~30 FPS
                                else:
                                    time.sleep(0.033)
                            else:
                                time.sleep(0.033)

                        except Exception as e:
                            consecutive_failures += 1
                            logger.error(f"Frame capture error: {e}")
                            time.sleep(0.1)

                        # Break if too many consecutive failures
                        if consecutive_failures >= max_consecutive_failures:
                            logger.error("Too many consecutive capture failures, reinitializing camera")
                            break

            except Exception as e:
                logger.error(f"Camera session error: {e}")
                consecutive_failures += 1
                time.sleep(self.recovery_delay)

                # Emergency recovery
                if consecutive_failures > 5:
                    if OPTIMIZATIONS_AVAILABLE:
                        emergency_cleanup()
                    self.performance_stats['recovery_count'] += 1
                    time.sleep(5.0)  # Longer recovery delay

        logger.info("Frame capture thread stopped")

    def _is_frame_valid(self, frame) -> bool:
        """Validate frame quality"""
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
        """Stable detection processing with error recovery"""
        logger.info("Starting stable detection processing thread")

        while self.running:
            try:
                # Get frame from queue
                frame = self.frame_queue.get(timeout=1.0)

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
                    # Run YOLO detection with error handling
                    try:
                        start_time = time.time()
                        results = self.model(frame, verbose=False)
                        detection_time = time.time() - start_time

                        self.performance_stats['detection_time'] = detection_time

                        # Process results
                        detections = self._extract_detections(results)
                        annotated_frame = self._draw_detections(frame, detections)

                        detection_data = {
                            'frame': annotated_frame,
                            'detections': detections,
                            'timestamp': datetime.now().isoformat(),
                            'stats': self.performance_stats.copy()
                        }

                    except Exception as e:
                        logger.error(f"Detection processing error: {e}")
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
                logger.error(f"Detection processing error: {e}")
                time.sleep(0.1)

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
        cv2.putText(annotated_frame, "R2D2 STABLE VISION", (10, 30),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)

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

        return annotated_frame

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

    async def _handle_websocket_client(self, websocket):
        """Handle WebSocket client connections with stability focus"""
        client_addr = websocket.remote_address

        # Enforce connection limit
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
                'message': 'R2D2 Stable Vision Connected',
                'optimizations_enabled': OPTIMIZATIONS_AVAILABLE
            }))

            # Main streaming loop
            while self.running:
                try:
                    # Get latest detection data
                    detection_data = self.detection_queue.get(timeout=0.1)

                    # Encode frame
                    encode_params = [cv2.IMWRITE_JPEG_QUALITY, 85]
                    _, buffer = cv2.imencode('.jpg', detection_data['frame'], encode_params)
                    frame_base64 = base64.b64encode(buffer).decode('utf-8')

                    # Prepare message (dashboard expects 'character_vision_data' for detections)
                    message = {
                        'type': 'character_vision_data',
                        'frame': frame_base64,
                        'detections': detection_data['detections'],
                        'timestamp': detection_data['timestamp'],
                        'stats': detection_data['stats']
                    }

                    # Send to client
                    await websocket.send(json.dumps(message))

                    # Control frame rate
                    await asyncio.sleep(1.0 / 12)  # 12 FPS

                except queue.Empty:
                    # Send heartbeat
                    await websocket.send(json.dumps({
                        'type': 'heartbeat',
                        'timestamp': datetime.now().isoformat(),
                        'system_status': self.performance_stats.copy()
                    }))
                    await asyncio.sleep(0.5)

                except websockets.exceptions.ConnectionClosed:
                    break
                except Exception as e:
                    logger.error(f"WebSocket send error: {e}")
                    break

        except websockets.exceptions.ConnectionClosed:
            logger.info(f"Client disconnected: {client_addr}")
        except Exception as e:
            logger.error(f"WebSocket client error: {e}")
        finally:
            self.connected_clients.discard(websocket)

    async def _run_websocket_server(self):
        """Run the WebSocket server"""
        async with websockets.serve(
            self._handle_websocket_client,
            "0.0.0.0",
            self.websocket_port
        ):
            logger.info(f"Stable Vision WebSocket server running on port {self.websocket_port}")
            await asyncio.Future()  # Run forever

    def start(self):
        """Start the stable vision system"""
        logger.info("Starting R2D2 Stable Vision System")

        # System health check
        health = self._check_system_health()
        if not health['system_ready']:
            logger.warning(f"System health issues detected: {health}")

        self.running = True

        # Start frame capture thread
        capture_thread = threading.Thread(target=self._capture_frames_stable, daemon=True)
        capture_thread.start()

        # Start detection processing thread
        detection_thread = threading.Thread(target=self._process_detections_stable, daemon=True)
        detection_thread.start()

        logger.info(f"WebSocket server starting on port {self.websocket_port}")

        try:
            asyncio.run(self._run_websocket_server())
        except KeyboardInterrupt:
            logger.info("Shutting down Stable Vision System")
        finally:
            self.stop()

        return True

    def stop(self):
        """Stop the stable vision system"""
        logger.info("Stopping R2D2 Stable Vision System")
        self.running = False

        # Stop memory monitoring if enabled
        if OPTIMIZATIONS_AVAILABLE:
            try:
                from orin_nano_memory_optimizer import stop_monitoring
                stop_monitoring()
            except:
                pass

        # Close WebSocket connections
        for client in self.connected_clients.copy():
            try:
                loop = asyncio.get_running_loop()
                loop.create_task(client.close())
            except RuntimeError:
                pass

        logger.info("Stable Vision System stopped")

def main():
    """Main function"""
    print("🎯 R2D2 Stable Vision System")
    print("=" * 40)
    print("Integrated resource management and crash prevention")
    print("Press Ctrl+C to stop")
    print("=" * 40)

    # Parse arguments
    port = 8767
    camera_index = 0

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
    vision_system = StableVisionSystem(websocket_port=port, camera_index=camera_index)

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