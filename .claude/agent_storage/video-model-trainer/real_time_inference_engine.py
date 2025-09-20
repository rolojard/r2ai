#!/usr/bin/env python3
"""
R2D2 Real-Time Computer Vision Inference Engine
Orchestrates all computer vision components for real-time R2D2 interactions
"""

import cv2
import numpy as np
import time
import threading
import queue
import json
import asyncio
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass, asdict
from concurrent.futures import ThreadPoolExecutor
import logging
from pathlib import Path

# Import our custom CV system components
from cv_system_architecture import (
    CVSystemConfig, GuestDetector, CostumeRecognizer, FaceRecognizer,
    GuestMemoryManager, R2D2BehaviorEngine, DetectionResult, GuestProfile, R2D2Response
)

logger = logging.getLogger(__name__)

@dataclass
class FrameProcessingResult:
    """Complete frame processing result"""
    frame_id: int
    timestamp: float
    guest_detections: List[DetectionResult]
    costume_recognitions: List[Tuple[str, float]]  # (costume, confidence)
    face_recognitions: List[str]  # guest_ids
    r2d2_responses: List[R2D2Response]
    processing_time: float

class CameraManager:
    """Manage camera input and frame buffering"""

    def __init__(self, config: CVSystemConfig):
        self.config = config
        self.cap = None
        self.frame_queue = queue.Queue(maxsize=10)
        self.running = False
        self.capture_thread = None

    def start_camera(self) -> bool:
        """Initialize and start camera capture"""
        try:
            device_id = self.config.get('camera.device_id')
            self.cap = cv2.VideoCapture(device_id)

            if not self.cap.isOpened():
                logger.error(f"Failed to open camera {device_id}")
                return False

            # Configure camera
            width, height = self.config.get('camera.resolution')
            fps = self.config.get('camera.fps')

            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
            self.cap.set(cv2.CAP_PROP_FPS, fps)
            self.cap.set(cv2.CAP_PROP_BUFFERSIZE, self.config.get('camera.buffer_size'))

            # Start capture thread
            self.running = True
            self.capture_thread = threading.Thread(target=self._capture_loop, daemon=True)
            self.capture_thread.start()

            logger.info(f"Camera started: {width}x{height} @ {fps}fps")
            return True

        except Exception as e:
            logger.error(f"Error starting camera: {e}")
            return False

    def _capture_loop(self):
        """Continuous frame capture loop"""
        frame_id = 0
        while self.running:
            try:
                ret, frame = self.cap.read()
                if ret:
                    # Add frame to queue (non-blocking)
                    try:
                        self.frame_queue.put_nowait((frame_id, time.time(), frame))
                        frame_id += 1
                    except queue.Full:
                        # Drop oldest frame if queue is full
                        try:
                            self.frame_queue.get_nowait()
                            self.frame_queue.put_nowait((frame_id, time.time(), frame))
                            frame_id += 1
                        except queue.Empty:
                            pass
                else:
                    logger.warning("Failed to read frame from camera")
                    time.sleep(0.1)

            except Exception as e:
                logger.error(f"Error in capture loop: {e}")
                time.sleep(0.1)

    def get_frame(self) -> Optional[Tuple[int, float, np.ndarray]]:
        """Get latest frame from queue"""
        try:
            return self.frame_queue.get_nowait()
        except queue.Empty:
            return None

    def stop_camera(self):
        """Stop camera capture"""
        self.running = False
        if self.capture_thread:
            self.capture_thread.join(timeout=2.0)
        if self.cap:
            self.cap.release()

class PerformanceMonitor:
    """Monitor system performance metrics"""

    def __init__(self):
        self.metrics = {
            'fps': 0.0,
            'avg_processing_time': 0.0,
            'detection_accuracy': 0.0,
            'memory_usage': 0.0,
            'gpu_utilization': 0.0
        }
        self.frame_times = []
        self.processing_times = []
        self.max_history = 100

    def update_frame_time(self, frame_time: float):
        """Update frame timing metrics"""
        self.frame_times.append(frame_time)
        if len(self.frame_times) > self.max_history:
            self.frame_times.pop(0)

        if len(self.frame_times) > 1:
            time_diffs = [self.frame_times[i] - self.frame_times[i-1]
                         for i in range(1, len(self.frame_times))]
            avg_frame_time = sum(time_diffs) / len(time_diffs)
            self.metrics['fps'] = 1.0 / avg_frame_time if avg_frame_time > 0 else 0.0

    def update_processing_time(self, processing_time: float):
        """Update processing time metrics"""
        self.processing_times.append(processing_time)
        if len(self.processing_times) > self.max_history:
            self.processing_times.pop(0)

        self.metrics['avg_processing_time'] = sum(self.processing_times) / len(self.processing_times)

    def get_metrics(self) -> Dict[str, float]:
        """Get current performance metrics"""
        return self.metrics.copy()

    def is_performance_acceptable(self, target_fps: float = 30.0, max_latency: float = 0.1) -> bool:
        """Check if performance meets requirements"""
        return (self.metrics['fps'] >= target_fps * 0.8 and
                self.metrics['avg_processing_time'] <= max_latency)

class R2D2VisionSystem:
    """Main computer vision system for R2D2 interactions"""

    def __init__(self, config_path: str = None):
        self.config = CVSystemConfig(config_path)

        # Initialize components
        self.camera_manager = CameraManager(self.config)
        self.guest_detector = GuestDetector(self.config)
        self.costume_recognizer = CostumeRecognizer(self.config)
        self.face_recognizer = FaceRecognizer(self.config)
        self.memory_manager = GuestMemoryManager(self.config)
        self.behavior_engine = R2D2BehaviorEngine(self.config)
        self.performance_monitor = PerformanceMonitor()

        # Processing control
        self.running = False
        self.processing_executor = ThreadPoolExecutor(max_workers=4)
        self.response_queue = queue.Queue()

        # API for external coordination
        self.motion_api_callback = None
        self.audio_api_callback = None

    async def start_system(self) -> bool:
        """Start the complete vision system"""
        try:
            logger.info("Starting R2D2 Vision System...")

            # Start camera
            if not self.camera_manager.start_camera():
                logger.error("Failed to start camera")
                return False

            # Start processing loop
            self.running = True
            asyncio.create_task(self._main_processing_loop())
            asyncio.create_task(self._response_execution_loop())

            logger.info("R2D2 Vision System started successfully")
            return True

        except Exception as e:
            logger.error(f"Error starting vision system: {e}")
            return False

    async def _main_processing_loop(self):
        """Main processing loop for real-time inference"""
        frame_count = 0

        while self.running:
            try:
                start_time = time.time()

                # Get latest frame
                frame_data = self.camera_manager.get_frame()
                if frame_data is None:
                    await asyncio.sleep(0.01)  # 10ms
                    continue

                frame_id, frame_timestamp, frame = frame_data
                self.performance_monitor.update_frame_time(frame_timestamp)

                # Process frame
                result = await self._process_frame(frame_id, frame_timestamp, frame)

                # Execute R2D2 responses
                for response in result.r2d2_responses:
                    self.response_queue.put(response)

                # Update performance metrics
                processing_time = time.time() - start_time
                self.performance_monitor.update_processing_time(processing_time)

                # Log performance every 100 frames
                frame_count += 1
                if frame_count % 100 == 0:
                    metrics = self.performance_monitor.get_metrics()
                    logger.info(f"Performance: {metrics['fps']:.1f} FPS, "
                              f"Processing: {metrics['avg_processing_time']*1000:.1f}ms")

                    if not self.performance_monitor.is_performance_acceptable():
                        logger.warning("Performance below target - consider optimization")

            except Exception as e:
                logger.error(f"Error in main processing loop: {e}")
                await asyncio.sleep(0.1)

    async def _process_frame(self, frame_id: int, timestamp: float, frame: np.ndarray) -> FrameProcessingResult:
        """Process single frame through complete pipeline"""
        try:
            # 1. Detect guests (persons)
            guest_detections = self.guest_detector.detect_guests(frame)

            # 2. Process each detected person
            costume_recognitions = []
            face_recognitions = []
            r2d2_responses = []

            for detection in guest_detections:
                # Extract person crop
                x, y, w, h = detection.bbox
                person_crop = frame[y:y+h, x:x+w]

                # Recognize costume
                costume, costume_confidence = self.costume_recognizer.recognize_costume(person_crop)
                if costume_confidence > self.config.get('recognition.costume_confidence_threshold'):
                    costume_recognitions.append((costume, costume_confidence))
                else:
                    costume = "civilian"  # Default
                    costume_recognitions.append((costume, 0.5))

                # Detect and recognize faces
                faces = self.face_recognizer.detect_faces(person_crop)
                guest_id = None

                for face_bbox in faces:
                    fx, fy, fw, fh = face_bbox
                    face_crop = person_crop[fy:fy+fh, fx:fx+fw]

                    # Generate face embedding
                    face_embedding = self.face_recognizer.generate_face_embedding(face_crop)

                    # Find or create guest
                    guest_id = self.memory_manager.find_or_create_guest(face_embedding, costume)
                    face_recognitions.append(guest_id)

                    # Get guest profile
                    guest_profile = self.memory_manager.get_guest_profile(guest_id)

                    if guest_profile:
                        # Generate R2D2 response
                        response = self.behavior_engine.generate_response(
                            guest_profile, costume, {"detection_confidence": detection.confidence}
                        )
                        r2d2_responses.append(response)

                        # Log interaction
                        self._log_interaction(guest_id, costume, response)

            return FrameProcessingResult(
                frame_id=frame_id,
                timestamp=timestamp,
                guest_detections=guest_detections,
                costume_recognitions=costume_recognitions,
                face_recognitions=face_recognitions,
                r2d2_responses=r2d2_responses,
                processing_time=time.time() - timestamp
            )

        except Exception as e:
            logger.error(f"Error processing frame {frame_id}: {e}")
            return FrameProcessingResult(
                frame_id=frame_id,
                timestamp=timestamp,
                guest_detections=[],
                costume_recognitions=[],
                face_recognitions=[],
                r2d2_responses=[],
                processing_time=time.time() - timestamp
            )

    async def _response_execution_loop(self):
        """Execute R2D2 responses through API callbacks"""
        while self.running:
            try:
                # Get response from queue (blocking with timeout)
                try:
                    response = self.response_queue.get(timeout=0.1)
                except queue.Empty:
                    continue

                # Execute response through APIs
                await self._execute_r2d2_response(response)

            except Exception as e:
                logger.error(f"Error in response execution loop: {e}")
                await asyncio.sleep(0.1)

    async def _execute_r2d2_response(self, response: R2D2Response):
        """Execute R2D2 response through motion and audio APIs"""
        try:
            # Coordinate with motion system
            if self.motion_api_callback:
                await self.motion_api_callback({
                    "movement_pattern": response.movement_pattern,
                    "light_pattern": response.light_pattern,
                    "priority": response.priority,
                    "duration": response.duration,
                    "context": response.context
                })

            # Coordinate with audio system
            if self.audio_api_callback:
                await self.audio_api_callback({
                    "audio_sequence": response.audio_sequence,
                    "priority": response.priority,
                    "context": response.context
                })

            logger.debug(f"Executed R2D2 response: {response.audio_sequence}")

        except Exception as e:
            logger.error(f"Error executing R2D2 response: {e}")

    def _log_interaction(self, guest_id: str, costume: str, response: R2D2Response):
        """Log interaction for learning and analytics"""
        try:
            # This would be expanded to include effectiveness scoring
            interaction_data = {
                "guest_id": guest_id,
                "timestamp": time.time(),
                "costume_detected": costume,
                "response": asdict(response),
                "effectiveness_score": 0.8  # Placeholder
            }

            # Log to database or file for analysis
            log_path = "/home/rolo/r2ai/.claude/agent_storage/video-model-trainer/interaction_log.json"
            with open(log_path, "a") as f:
                f.write(json.dumps(interaction_data) + "\n")

        except Exception as e:
            logger.error(f"Error logging interaction: {e}")

    def set_motion_api_callback(self, callback):
        """Set callback for motion system coordination"""
        self.motion_api_callback = callback

    def set_audio_api_callback(self, callback):
        """Set callback for audio system coordination"""
        self.audio_api_callback = callback

    def get_system_status(self) -> Dict[str, Any]:
        """Get current system status and metrics"""
        return {
            "running": self.running,
            "performance": self.performance_monitor.get_metrics(),
            "camera_active": self.camera_manager.running,
            "queue_size": self.response_queue.qsize(),
            "config": {
                "detection_threshold": self.config.get('detection.confidence_threshold'),
                "recognition_threshold": self.config.get('recognition.face_similarity_threshold'),
                "max_inference_time": self.config.get('performance.max_inference_time')
            }
        }

    async def stop_system(self):
        """Stop the vision system gracefully"""
        logger.info("Stopping R2D2 Vision System...")

        self.running = False
        self.camera_manager.stop_camera()
        self.processing_executor.shutdown(wait=True)

        logger.info("R2D2 Vision System stopped")

# API Interface for external integration
class R2D2VisionAPI:
    """API interface for R2D2 vision system integration"""

    def __init__(self, vision_system: R2D2VisionSystem):
        self.vision_system = vision_system

    async def start(self) -> Dict[str, Any]:
        """Start vision system API"""
        success = await self.vision_system.start_system()
        return {"success": success, "message": "Vision system started" if success else "Failed to start"}

    async def stop(self) -> Dict[str, Any]:
        """Stop vision system API"""
        await self.vision_system.stop_system()
        return {"success": True, "message": "Vision system stopped"}

    async def get_status(self) -> Dict[str, Any]:
        """Get system status API"""
        return self.vision_system.get_system_status()

    async def configure(self, config_updates: Dict[str, Any]) -> Dict[str, Any]:
        """Update system configuration API"""
        try:
            # Update configuration
            for key, value in config_updates.items():
                # Validate and update config
                pass  # Implementation would validate and apply updates

            return {"success": True, "message": "Configuration updated"}
        except Exception as e:
            return {"success": False, "message": f"Configuration error: {e}"}

    async def register_motion_callback(self, callback) -> Dict[str, Any]:
        """Register motion system callback API"""
        try:
            self.vision_system.set_motion_api_callback(callback)
            return {"success": True, "message": "Motion callback registered"}
        except Exception as e:
            return {"success": False, "message": f"Callback registration error: {e}"}

    async def register_audio_callback(self, callback) -> Dict[str, Any]:
        """Register audio system callback API"""
        try:
            self.vision_system.set_audio_api_callback(callback)
            return {"success": True, "message": "Audio callback registered"}
        except Exception as e:
            return {"success": False, "message": f"Callback registration error: {e}"}

# Example usage and testing
async def main():
    """Example usage of the R2D2 Vision System"""
    try:
        # Initialize system
        config_path = "/home/rolo/r2ai/.claude/agent_storage/video-model-trainer/config.json"
        vision_system = R2D2VisionSystem(config_path)

        # Example motion callback
        async def motion_callback(motion_data):
            logger.info(f"Motion command: {motion_data['movement_pattern']}")

        # Example audio callback
        async def audio_callback(audio_data):
            logger.info(f"Audio command: {audio_data['audio_sequence']}")

        # Register callbacks
        vision_system.set_motion_api_callback(motion_callback)
        vision_system.set_audio_api_callback(audio_callback)

        # Start system
        if await vision_system.start_system():
            logger.info("Vision system running...")

            # Run for demonstration
            await asyncio.sleep(30)  # Run for 30 seconds

        # Stop system
        await vision_system.stop_system()

    except Exception as e:
        logger.error(f"Error in main: {e}")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())