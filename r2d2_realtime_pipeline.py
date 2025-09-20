#!/usr/bin/env python3
"""
R2D2 Real-time Recognition Pipeline
Optimized for NVIDIA Orin Nano with CUDA acceleration
High-performance person detection and recognition with edge optimization
"""

import cv2
import numpy as np
import torch
import threading
import time
import logging
import queue
import asyncio
import websockets
import json
import base64
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
import multiprocessing as mp
from concurrent.futures import ThreadPoolExecutor

from r2d2_person_recognition_system import R2D2PersonRecognitionSystem
from r2d2_recognition_integration import R2D2BehaviorCoordinator
from r2d2_memory_manager import R2D2MemoryManager

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class PerformanceMetrics:
    """Performance tracking metrics"""
    fps: float = 0.0
    detection_fps: float = 0.0
    recognition_fps: float = 0.0
    avg_detection_time: float = 0.0
    avg_recognition_time: float = 0.0
    gpu_utilization: float = 0.0
    gpu_memory_used: float = 0.0
    cpu_utilization: float = 0.0
    frame_drops: int = 0
    queue_depth: int = 0
    total_persons_detected: int = 0
    successful_recognitions: int = 0

class OrionNanoOptimizer:
    """Optimization utilities for NVIDIA Orin Nano"""

    def __init__(self):
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        self.gpu_available = torch.cuda.is_available()

        if self.gpu_available:
            # Get GPU properties
            self.gpu_properties = torch.cuda.get_device_properties(0)
            logger.info(f"GPU: {self.gpu_properties.name}")
            logger.info(f"GPU Memory: {self.gpu_properties.total_memory / 1024**3:.1f} GB")

    def optimize_torch_settings(self):
        """Optimize PyTorch settings for Orin Nano"""
        try:
            if self.gpu_available:
                # Enable TensorFloat-32 for better performance
                torch.backends.cuda.matmul.allow_tf32 = True
                torch.backends.cudnn.allow_tf32 = True

                # Enable cudnn benchmarking for consistent input sizes
                torch.backends.cudnn.benchmark = True

                # Set memory allocation strategy
                torch.cuda.empty_cache()

                logger.info("PyTorch CUDA optimizations enabled")

        except Exception as e:
            logger.error(f"Error applying PyTorch optimizations: {e}")

    def get_optimal_batch_size(self, model_type: str = "yolo") -> int:
        """Get optimal batch size for the model"""
        if not self.gpu_available:
            return 1

        # Conservative batch sizes for Orin Nano's limited memory
        batch_sizes = {
            "yolo": 2,
            "face_recognition": 4,
            "general": 1
        }

        return batch_sizes.get(model_type, 1)

    def get_gpu_memory_info(self) -> Dict[str, float]:
        """Get current GPU memory utilization"""
        if not self.gpu_available:
            return {"total": 0, "used": 0, "free": 0, "utilization": 0}

        try:
            memory_stats = torch.cuda.memory_stats()
            allocated = memory_stats.get("allocated_bytes.all.current", 0)
            reserved = memory_stats.get("reserved_bytes.all.current", 0)
            total = self.gpu_properties.total_memory

            return {
                "total": total / 1024**3,  # GB
                "allocated": allocated / 1024**3,  # GB
                "reserved": reserved / 1024**3,  # GB
                "utilization": (allocated / total) * 100
            }

        except Exception as e:
            logger.error(f"Error getting GPU memory info: {e}")
            return {"total": 0, "used": 0, "free": 0, "utilization": 0}

class R2D2RealtimePipeline:
    """High-performance real-time recognition pipeline for R2D2"""

    def __init__(self, config: Dict = None):
        self.config = config or self._get_default_config()

        # Initialize optimizer
        self.optimizer = OrionNanoOptimizer()
        self.optimizer.optimize_torch_settings()

        # Core systems
        self.recognition_system = R2D2PersonRecognitionSystem(self.config.get('recognition', {}))
        self.behavior_coordinator = R2D2BehaviorCoordinator(self.config.get('behavior', {}))

        # Camera setup
        self.camera = None
        self.camera_index = self.config.get('camera_index', 0)
        self.frame_width = self.config.get('frame_width', 640)
        self.frame_height = self.config.get('frame_height', 480)
        self.target_fps = self.config.get('target_fps', 30)

        # Processing queues with size limits for memory management
        self.frame_queue = queue.Queue(maxsize=3)
        self.detection_queue = queue.Queue(maxsize=5)
        self.recognition_queue = queue.Queue(maxsize=3)
        self.result_queue = queue.Queue(maxsize=10)

        # Thread management
        self.running = False
        self.threads = {}
        self.thread_pool = ThreadPoolExecutor(max_workers=4)

        # Performance tracking
        self.metrics = PerformanceMetrics()
        self.frame_times = []
        self.detection_times = []
        self.recognition_times = []

        # WebSocket server for dashboard integration
        self.websocket_port = self.config.get('websocket_port', 8768)
        self.connected_clients = set()

        # Frame processing control
        self.detection_interval = self.config.get('detection_interval', 2)  # Process every Nth frame
        self.frame_counter = 0

        logger.info("R2D2 Real-time Pipeline initialized")

    def _get_default_config(self) -> Dict:
        """Get default configuration optimized for Orin Nano"""
        return {
            "camera_index": 0,
            "frame_width": 640,
            "frame_height": 480,
            "target_fps": 30,
            "detection_interval": 2,  # Process every 2nd frame for performance
            "websocket_port": 8768,
            "optimization": {
                "use_gpu_acceleration": True,
                "enable_tensorrt": False,  # Would require TensorRT setup
                "max_detection_fps": 15,
                "max_recognition_fps": 10,
                "memory_optimization": True
            },
            "quality": {
                "jpeg_quality": 80,
                "detection_confidence": 0.7,
                "face_quality_threshold": 0.4
            },
            "performance": {
                "max_queue_size": 5,
                "thread_timeout": 5.0,
                "memory_cleanup_interval": 60
            }
        }

    def _initialize_camera(self) -> bool:
        """Initialize camera with optimal settings"""
        try:
            self.camera = cv2.VideoCapture(self.camera_index)

            if not self.camera.isOpened():
                logger.error("Failed to open camera")
                return False

            # Set camera properties for optimal performance
            self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, self.frame_width)
            self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, self.frame_height)
            self.camera.set(cv2.CAP_PROP_FPS, self.target_fps)
            self.camera.set(cv2.CAP_PROP_BUFFERSIZE, 1)  # Minimize buffer lag

            # Additional optimizations for USB cameras
            self.camera.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc('M', 'J', 'P', 'G'))
            self.camera.set(cv2.CAP_PROP_AUTO_EXPOSURE, 0.25)  # Reduce auto-exposure for speed

            # Test frame capture
            ret, frame = self.camera.read()
            if not ret:
                logger.error("Failed to read test frame")
                return False

            logger.info(f"Camera initialized: {frame.shape} @ {self.target_fps}fps")
            return True

        except Exception as e:
            logger.error(f"Camera initialization error: {e}")
            return False

    def _frame_capture_thread(self):
        """High-speed frame capture thread"""
        logger.info("Frame capture thread started")

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
                    self.metrics.fps = frame_count / elapsed
                    if elapsed > 5:  # Reset counter every 5 seconds
                        frame_count = 0
                        start_time = time.time()

                # Add frame to processing queue (non-blocking)
                try:
                    self.frame_queue.put_nowait(frame.copy())
                except queue.Full:
                    # Drop oldest frame and add new one
                    try:
                        self.frame_queue.get_nowait()
                        self.frame_queue.put_nowait(frame.copy())
                        self.metrics.frame_drops += 1
                    except queue.Empty:
                        pass

                # Small delay to prevent overwhelming
                time.sleep(1 / (self.target_fps * 1.1))

            except Exception as e:
                logger.error(f"Frame capture error: {e}")
                time.sleep(0.1)

    def _detection_processing_thread(self):
        """Person detection processing thread"""
        logger.info("Detection processing thread started")

        detection_count = 0
        start_time = time.time()

        while self.running:
            try:
                # Get frame from queue
                frame = self.frame_queue.get(timeout=1.0)

                # Skip frames based on detection interval for performance
                self.frame_counter += 1
                if self.frame_counter % self.detection_interval != 0:
                    continue

                # Process detection
                detection_start = time.time()
                persons = self.recognition_system.detect_persons(frame)
                detection_time = time.time() - detection_start

                # Update metrics
                self.detection_times.append(detection_time)
                if len(self.detection_times) > 100:
                    self.detection_times = self.detection_times[-50:]
                self.metrics.avg_detection_time = np.mean(self.detection_times)

                detection_count += 1
                elapsed = time.time() - start_time
                if elapsed > 0:
                    self.metrics.detection_fps = detection_count / elapsed

                self.metrics.total_persons_detected += len(persons)

                # Add to recognition queue if persons detected
                if persons:
                    detection_data = {
                        'frame': frame,
                        'persons': persons,
                        'timestamp': datetime.now(),
                        'detection_time': detection_time
                    }

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

    def _recognition_processing_thread(self):
        """Face recognition processing thread"""
        logger.info("Recognition processing thread started")

        recognition_count = 0
        start_time = time.time()

        while self.running:
            try:
                # Get detection data
                detection_data = self.detection_queue.get(timeout=1.0)

                frame = detection_data['frame']
                persons = detection_data['persons']

                recognition_start = time.time()

                # Process each detected person
                recognition_results = []
                for person in persons:
                    # Detect faces in person
                    faces = self.recognition_system.detect_faces_in_person(frame, person.bbox)

                    for face in faces:
                        # Recognize person
                        identity = self.recognition_system.recognize_person(face)

                        if identity:
                            # Detect character if applicable
                            character = self.recognition_system.detect_star_wars_character(frame, person.bbox)
                            if character:
                                identity.character_name = character

                            recognition_results.append({
                                'person_detection': person,
                                'face_detection': face,
                                'identity': identity,
                                'character': character
                            })

                            self.metrics.successful_recognitions += 1

                recognition_time = time.time() - recognition_start

                # Update metrics
                self.recognition_times.append(recognition_time)
                if len(self.recognition_times) > 50:
                    self.recognition_times = self.recognition_times[-25:]
                self.metrics.avg_recognition_time = np.mean(self.recognition_times)

                recognition_count += 1
                elapsed = time.time() - start_time
                if elapsed > 0:
                    self.metrics.recognition_fps = recognition_count / elapsed

                # Process through behavior coordinator
                if recognition_results:
                    for result in recognition_results:
                        self.behavior_coordinator.process_frame_for_recognition(
                            frame, {"recognition_result": result}
                        )

                # Add to result queue for dashboard
                result_data = {
                    'frame': frame,
                    'recognition_results': recognition_results,
                    'timestamp': detection_data['timestamp'],
                    'processing_times': {
                        'detection': detection_data['detection_time'],
                        'recognition': recognition_time
                    },
                    'metrics': self._get_current_metrics()
                }

                try:
                    self.result_queue.put_nowait(result_data)
                except queue.Full:
                    try:
                        self.result_queue.get_nowait()
                        self.result_queue.put_nowait(result_data)
                    except queue.Empty:
                        pass

            except queue.Empty:
                continue
            except Exception as e:
                logger.error(f"Recognition processing error: {e}")

    def _performance_monitoring_thread(self):
        """Performance monitoring and optimization thread"""
        logger.info("Performance monitoring thread started")

        while self.running:
            try:
                # Update GPU metrics
                gpu_info = self.optimizer.get_gpu_memory_info()
                self.metrics.gpu_memory_used = gpu_info['utilization']

                # Update queue depths
                self.metrics.queue_depth = (
                    self.frame_queue.qsize() +
                    self.detection_queue.qsize() +
                    self.recognition_queue.qsize()
                )

                # Memory cleanup if needed
                if self.metrics.gpu_memory_used > 80:
                    logger.warning("High GPU memory usage, performing cleanup")
                    torch.cuda.empty_cache()

                # Log performance stats
                if hasattr(self, '_last_perf_log'):
                    if time.time() - self._last_perf_log > 30:  # Log every 30 seconds
                        self._log_performance_stats()
                        self._last_perf_log = time.time()
                else:
                    self._last_perf_log = time.time()

                time.sleep(5)  # Check every 5 seconds

            except Exception as e:
                logger.error(f"Performance monitoring error: {e}")
                time.sleep(10)

    def _log_performance_stats(self):
        """Log current performance statistics"""
        logger.info(f"Performance Stats - FPS: {self.metrics.fps:.1f}, "
                   f"Detection FPS: {self.metrics.detection_fps:.1f}, "
                   f"Recognition FPS: {self.metrics.recognition_fps:.1f}, "
                   f"GPU Memory: {self.metrics.gpu_memory_used:.1f}%, "
                   f"Queue Depth: {self.metrics.queue_depth}, "
                   f"Frame Drops: {self.metrics.frame_drops}")

    async def _websocket_handler(self, websocket, path):
        """Handle WebSocket connections for dashboard integration"""
        logger.info(f"WebSocket client connected: {websocket.remote_address}")
        self.connected_clients.add(websocket)

        try:
            await websocket.send(json.dumps({
                'type': 'connection_status',
                'status': 'connected',
                'message': 'R2D2 Real-time Pipeline Connected'
            }))

            # Send data to client
            while self.running:
                try:
                    # Get latest result
                    result_data = self.result_queue.get(timeout=0.1)

                    # Encode frame as base64
                    _, buffer = cv2.imencode('.jpg', result_data['frame'],
                                           [cv2.IMWRITE_JPEG_QUALITY, self.config['quality']['jpeg_quality']])
                    frame_base64 = base64.b64encode(buffer).decode('utf-8')

                    # Prepare recognition data
                    recognition_data = []
                    for result in result_data['recognition_results']:
                        recognition_data.append({
                            'person_bbox': result['person_detection'].bbox,
                            'face_bbox': result['face_detection'].bbox,
                            'identity': {
                                'person_id': result['identity'].person_id,
                                'familiarity_level': result['identity'].familiarity_level,
                                'visit_count': result['identity'].visit_count,
                                'character_name': result['identity'].character_name
                            },
                            'character_detected': result['character']
                        })

                    # Send WebSocket message
                    message = {
                        'type': 'recognition_data',
                        'frame': frame_base64,
                        'recognition_results': recognition_data,
                        'timestamp': result_data['timestamp'].isoformat(),
                        'performance': result_data['metrics'],
                        'processing_times': result_data['processing_times']
                    }

                    await websocket.send(json.dumps(message))

                except queue.Empty:
                    # Send heartbeat
                    await websocket.send(json.dumps({
                        'type': 'heartbeat',
                        'timestamp': datetime.now().isoformat(),
                        'metrics': self._get_current_metrics()
                    }))
                    await asyncio.sleep(0.1)

                except websockets.exceptions.ConnectionClosed:
                    break

        except Exception as e:
            logger.error(f"WebSocket handler error: {e}")
        finally:
            self.connected_clients.discard(websocket)
            logger.info("WebSocket client disconnected")

    def _get_current_metrics(self) -> Dict[str, Any]:
        """Get current performance metrics"""
        return {
            'fps': round(self.metrics.fps, 1),
            'detection_fps': round(self.metrics.detection_fps, 1),
            'recognition_fps': round(self.metrics.recognition_fps, 1),
            'avg_detection_time': round(self.metrics.avg_detection_time * 1000, 1),  # ms
            'avg_recognition_time': round(self.metrics.avg_recognition_time * 1000, 1),  # ms
            'gpu_memory_used': round(self.metrics.gpu_memory_used, 1),
            'queue_depth': self.metrics.queue_depth,
            'frame_drops': self.metrics.frame_drops,
            'total_persons_detected': self.metrics.total_persons_detected,
            'successful_recognitions': self.metrics.successful_recognitions
        }

    def start_pipeline(self):
        """Start the real-time recognition pipeline"""
        try:
            logger.info("Starting R2D2 Real-time Recognition Pipeline")

            # Initialize camera
            if not self._initialize_camera():
                raise RuntimeError("Failed to initialize camera")

            # Start behavior coordinator
            self.behavior_coordinator.start_integration_system()

            self.running = True

            # Start processing threads
            self.threads['frame_capture'] = threading.Thread(
                target=self._frame_capture_thread, daemon=True
            )
            self.threads['detection'] = threading.Thread(
                target=self._detection_processing_thread, daemon=True
            )
            self.threads['recognition'] = threading.Thread(
                target=self._recognition_processing_thread, daemon=True
            )
            self.threads['performance'] = threading.Thread(
                target=self._performance_monitoring_thread, daemon=True
            )

            # Start all threads
            for thread_name, thread in self.threads.items():
                thread.start()
                logger.info(f"Started {thread_name} thread")

            # Start WebSocket server
            start_server = websockets.serve(
                self._websocket_handler,
                "localhost",
                self.websocket_port
            )

            logger.info(f"WebSocket server starting on port {self.websocket_port}")

            # Run WebSocket server
            loop = asyncio.get_event_loop()
            loop.run_until_complete(start_server)

            logger.info("R2D2 Real-time Pipeline fully started")

            try:
                loop.run_forever()
            except KeyboardInterrupt:
                logger.info("Shutting down pipeline...")
            finally:
                self.stop_pipeline()

        except Exception as e:
            logger.error(f"Error starting pipeline: {e}")
            raise

    def stop_pipeline(self):
        """Stop the real-time recognition pipeline"""
        try:
            logger.info("Stopping R2D2 Real-time Pipeline")

            self.running = False

            # Stop behavior coordinator
            self.behavior_coordinator.stop_integration_system()

            # Wait for threads to complete
            for thread_name, thread in self.threads.items():
                if thread.is_alive():
                    thread.join(timeout=5)
                    if thread.is_alive():
                        logger.warning(f"{thread_name} thread did not stop gracefully")

            # Close camera
            if self.camera:
                self.camera.release()

            # Close WebSocket connections
            for client in self.connected_clients.copy():
                asyncio.create_task(client.close())

            # Cleanup GPU memory
            if torch.cuda.is_available():
                torch.cuda.empty_cache()

            logger.info("R2D2 Real-time Pipeline stopped")

        except Exception as e:
            logger.error(f"Error stopping pipeline: {e}")

    def get_pipeline_status(self) -> Dict[str, Any]:
        """Get comprehensive pipeline status"""
        try:
            behavior_status = self.behavior_coordinator.get_integration_status()

            status = {
                "pipeline_running": self.running,
                "camera_active": self.camera is not None and self.camera.isOpened(),
                "threads_active": {
                    name: thread.is_alive()
                    for name, thread in self.threads.items()
                },
                "connected_clients": len(self.connected_clients),
                "performance_metrics": self._get_current_metrics(),
                "gpu_info": self.optimizer.get_gpu_memory_info(),
                "behavior_system": behavior_status,
                "configuration": {
                    "frame_size": f"{self.frame_width}x{self.frame_height}",
                    "target_fps": self.target_fps,
                    "detection_interval": self.detection_interval,
                    "websocket_port": self.websocket_port
                }
            }

            return status

        except Exception as e:
            logger.error(f"Error getting pipeline status: {e}")
            return {"error": str(e)}

def main():
    """Main function for running the real-time pipeline"""
    print("R2D2 Real-time Recognition Pipeline")
    print("=" * 50)
    print("Optimized for NVIDIA Orin Nano")
    print("Press Ctrl+C to stop")
    print("=" * 50)

    try:
        # Create and start pipeline
        pipeline = R2D2RealtimePipeline()

        # Register some dummy callbacks for testing
        def dummy_audio_callback(sequence, duration):
            print(f"🎵 Audio: {sequence} ({duration}s)")
            return {"executed": True}

        def dummy_servo_callback(pattern, duration):
            print(f"🤖 Movement: {pattern} ({duration}s)")
            return {"executed": True}

        pipeline.behavior_coordinator.register_reaction_callback("audio_system", dummy_audio_callback)
        pipeline.behavior_coordinator.register_reaction_callback("servo_system", dummy_servo_callback)

        # Start the pipeline
        pipeline.start_pipeline()

    except KeyboardInterrupt:
        logger.info("Pipeline stopped by user")
    except Exception as e:
        logger.error(f"Pipeline error: {e}")
    finally:
        print("Pipeline shutdown complete")

if __name__ == "__main__":
    main()