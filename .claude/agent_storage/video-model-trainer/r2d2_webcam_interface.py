#!/usr/bin/env python3
"""
R2D2 Real-time Webcam Interface
Comprehensive webcam interface for real-time guest detection and interaction triggers
Optimized for Nvidia Orin Nano with visual overlays and agent monitoring
"""

import cv2
import numpy as np
import asyncio
import threading
import time
import json
import logging
from typing import Dict, List, Tuple, Optional, Any, Callable
from dataclasses import dataclass, asdict
from pathlib import Path
import base64
from concurrent.futures import ThreadPoolExecutor
import queue
from datetime import datetime, timedelta
import socketio
import psutil
import GPUtil

# Import existing R2D2 computer vision components
from real_time_inference_engine import R2D2VisionSystem
from cv_system_architecture import R2D2Response, GuestProfile
from face_recognition_system import R2D2GuestMemorySystem

logger = logging.getLogger(__name__)

@dataclass
class DetectionResult:
    """Structure for detection results with visual overlay information"""
    guest_id: str
    bbox: Tuple[int, int, int, int]  # x, y, w, h
    confidence: float
    costume: str
    costume_confidence: float
    face_recognition: Optional[str]
    face_confidence: float
    distance_zone: str  # "immediate", "close", "medium", "far"
    timestamp: float
    interaction_count: int
    relationship_level: int

@dataclass
class TriggerZone:
    """Interaction trigger zone configuration"""
    name: str
    bbox: Tuple[int, int, int, int]  # x, y, w, h
    color: Tuple[int, int, int]  # BGR color
    interaction_type: str
    priority: int
    cooldown_seconds: float

@dataclass
class SystemStatus:
    """Real-time system status for monitoring"""
    fps: float
    inference_time_ms: float
    queue_size: int
    active_detections: int
    cpu_usage: float
    gpu_usage: float
    memory_usage: float
    temperature: float
    timestamp: float

class R2D2WebcamInterface:
    """
    Comprehensive webcam interface for R2D2 guest detection and interaction
    Features:
    - Real-time webcam capture with visual overlays
    - Guest detection with bounding boxes and confidence scores
    - Distance-based trigger zones for interactions
    - Visual interface showing detection results and system status
    - Screen viewing capability for agent monitoring
    - Integration with existing computer vision models
    """

    def __init__(self, config_path: str = None):
        """Initialize the webcam interface system"""
        self.config = self._load_config(config_path)

        # Initialize computer vision system
        self.vision_system = None
        self.memory_system = None

        # Camera and processing
        self.camera = None
        self.camera_active = False
        self.frame_queue = queue.Queue(maxsize=3)
        self.detection_queue = queue.Queue(maxsize=10)

        # Real-time state
        self.current_detections: List[DetectionResult] = []
        self.active_triggers: Dict[str, float] = {}  # trigger_id -> last_activation_time
        self.system_status = SystemStatus(0, 0, 0, 0, 0, 0, 0, 0, time.time())

        # Performance monitoring
        self.fps_counter = 0
        self.fps_start_time = time.time()
        self.avg_inference_time = 0
        self.frame_times = []

        # Visual interface
        self.show_interface = True
        self.show_agent_monitor = True
        self.overlay_opacity = 0.7

        # Threading
        self.executor = ThreadPoolExecutor(max_workers=4)
        self.running = False

        # Callbacks for integration
        self.motion_callback: Optional[Callable] = None
        self.audio_callback: Optional[Callable] = None
        self.status_callback: Optional[Callable] = None

        # Socket.IO for real-time monitoring
        self.sio = socketio.AsyncServer(cors_allowed_origins="*")
        self.monitor_clients = set()

        # Setup trigger zones
        self.trigger_zones = self._setup_trigger_zones()

        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )

    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """Load configuration from file or use defaults"""
        default_config = {
            "camera": {
                "device_id": 0,
                "resolution": [1920, 1080],
                "fps": 30,
                "buffer_size": 1,
                "auto_exposure": False,
                "exposure": -6
            },
            "detection": {
                "confidence_threshold": 0.7,
                "nms_threshold": 0.4,
                "max_detections": 50,
                "min_detection_size": 30
            },
            "visual": {
                "show_bboxes": True,
                "show_confidence": True,
                "show_zones": True,
                "show_status": True,
                "overlay_opacity": 0.7,
                "font_scale": 0.6,
                "line_thickness": 2
            },
            "triggers": {
                "immediate_zone": {"distance": 50, "priority": 10, "cooldown": 2.0},
                "close_zone": {"distance": 100, "priority": 8, "cooldown": 5.0},
                "medium_zone": {"distance": 200, "priority": 6, "cooldown": 10.0},
                "far_zone": {"distance": 300, "priority": 4, "cooldown": 15.0}
            },
            "performance": {
                "target_fps": 30,
                "max_inference_time_ms": 100,
                "max_queue_size": 10,
                "tensorrt_enabled": True,
                "fp16_enabled": True
            },
            "monitoring": {
                "enable_agent_monitor": True,
                "websocket_port": 8765,
                "update_interval_ms": 100,
                "save_screenshots": False
            }
        }

        if config_path and Path(config_path).exists():
            try:
                with open(config_path, 'r') as f:
                    config = json.load(f)
                    # Merge with defaults
                    for key, value in default_config.items():
                        if key not in config:
                            config[key] = value
                        elif isinstance(value, dict):
                            for subkey, subvalue in value.items():
                                if subkey not in config[key]:
                                    config[key][subkey] = subvalue
                    return config
            except Exception as e:
                logger.warning(f"Failed to load config from {config_path}: {e}")

        return default_config

    def _setup_trigger_zones(self) -> List[TriggerZone]:
        """Setup interaction trigger zones"""
        # Get camera resolution
        width = self.config["camera"]["resolution"][0]
        height = self.config["camera"]["resolution"][1]

        # Center point (where R2D2 is positioned)
        center_x, center_y = width // 2, height // 2

        zones = []

        # Immediate interaction zone (very close)
        immediate_size = self.config["triggers"]["immediate_zone"]["distance"]
        zones.append(TriggerZone(
            name="immediate",
            bbox=(center_x - immediate_size//2, center_y - immediate_size//2,
                  immediate_size, immediate_size),
            color=(0, 0, 255),  # Red
            interaction_type="immediate_response",
            priority=self.config["triggers"]["immediate_zone"]["priority"],
            cooldown_seconds=self.config["triggers"]["immediate_zone"]["cooldown"]
        ))

        # Close interaction zone
        close_size = self.config["triggers"]["close_zone"]["distance"]
        zones.append(TriggerZone(
            name="close",
            bbox=(center_x - close_size//2, center_y - close_size//2,
                  close_size, close_size),
            color=(0, 165, 255),  # Orange
            interaction_type="close_greeting",
            priority=self.config["triggers"]["close_zone"]["priority"],
            cooldown_seconds=self.config["triggers"]["close_zone"]["cooldown"]
        ))

        # Medium interaction zone
        medium_size = self.config["triggers"]["medium_zone"]["distance"]
        zones.append(TriggerZone(
            name="medium",
            bbox=(center_x - medium_size//2, center_y - medium_size//2,
                  medium_size, medium_size),
            color=(0, 255, 255),  # Yellow
            interaction_type="attention_getting",
            priority=self.config["triggers"]["medium_zone"]["priority"],
            cooldown_seconds=self.config["triggers"]["medium_zone"]["cooldown"]
        ))

        # Far interaction zone (awareness)
        far_size = self.config["triggers"]["far_zone"]["distance"]
        zones.append(TriggerZone(
            name="far",
            bbox=(center_x - far_size//2, center_y - far_size//2,
                  far_size, far_size),
            color=(0, 255, 0),  # Green
            interaction_type="subtle_acknowledgment",
            priority=self.config["triggers"]["far_zone"]["priority"],
            cooldown_seconds=self.config["triggers"]["far_zone"]["cooldown"]
        ))

        return zones

    async def initialize_system(self) -> bool:
        """Initialize all system components"""
        try:
            logger.info("Initializing R2D2 Webcam Interface System...")

            # Initialize computer vision system
            vision_config_path = "/home/rolo/r2ai/.claude/agent_storage/video-model-trainer/config.json"
            self.vision_system = R2D2VisionSystem(vision_config_path)
            await self.vision_system.initialize()

            # Initialize memory system
            self.memory_system = R2D2GuestMemorySystem()
            await self.memory_system.initialize()

            # Initialize camera
            if not await self._initialize_camera():
                logger.error("Failed to initialize camera")
                return False

            # Setup Socket.IO events
            self._setup_socketio_events()

            logger.info("✅ R2D2 Webcam Interface System initialized successfully")
            return True

        except Exception as e:
            logger.error(f"Failed to initialize system: {e}")
            return False

    async def _initialize_camera(self) -> bool:
        """Initialize camera with optimal settings"""
        try:
            device_id = self.config["camera"]["device_id"]
            self.camera = cv2.VideoCapture(device_id)

            if not self.camera.isOpened():
                logger.error(f"Failed to open camera device {device_id}")
                return False

            # Set camera properties
            width, height = self.config["camera"]["resolution"]
            fps = self.config["camera"]["fps"]

            self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, width)
            self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
            self.camera.set(cv2.CAP_PROP_FPS, fps)
            self.camera.set(cv2.CAP_PROP_BUFFERSIZE, self.config["camera"]["buffer_size"])

            # Disable auto exposure for consistent lighting
            if not self.config["camera"]["auto_exposure"]:
                self.camera.set(cv2.CAP_PROP_AUTO_EXPOSURE, 0.25)
                self.camera.set(cv2.CAP_PROP_EXPOSURE, self.config["camera"]["exposure"])

            # Verify settings
            actual_width = int(self.camera.get(cv2.CAP_PROP_FRAME_WIDTH))
            actual_height = int(self.camera.get(cv2.CAP_PROP_FRAME_HEIGHT))
            actual_fps = self.camera.get(cv2.CAP_PROP_FPS)

            logger.info(f"Camera initialized: {actual_width}x{actual_height} @ {actual_fps}fps")

            self.camera_active = True
            return True

        except Exception as e:
            logger.error(f"Camera initialization error: {e}")
            return False

    def _setup_socketio_events(self):
        """Setup Socket.IO events for agent monitoring"""

        @self.sio.event
        async def connect(sid, environ):
            """Handle client connection"""
            logger.info(f"Monitor client connected: {sid}")
            self.monitor_clients.add(sid)

            # Send initial status
            await self.sio.emit('status_update', asdict(self.system_status), room=sid)

        @self.sio.event
        async def disconnect(sid):
            """Handle client disconnection"""
            logger.info(f"Monitor client disconnected: {sid}")
            self.monitor_clients.discard(sid)

        @self.sio.event
        async def request_screenshot(sid):
            """Handle screenshot request"""
            if hasattr(self, 'current_frame') and self.current_frame is not None:
                # Encode frame as base64
                _, buffer = cv2.imencode('.jpg', self.current_frame)
                img_base64 = base64.b64encode(buffer).decode('utf-8')

                await self.sio.emit('screenshot', {
                    'image': img_base64,
                    'timestamp': time.time()
                }, room=sid)

    async def start_system(self) -> bool:
        """Start the complete webcam interface system"""
        try:
            if self.running:
                logger.warning("System already running")
                return True

            if not await self.initialize_system():
                return False

            self.running = True

            # Start processing threads
            asyncio.create_task(self._camera_capture_loop())
            asyncio.create_task(self._detection_processing_loop())
            asyncio.create_task(self._visual_interface_loop())
            asyncio.create_task(self._system_monitoring_loop())

            logger.info("🚀 R2D2 Webcam Interface System started successfully!")
            return True

        except Exception as e:
            logger.error(f"Failed to start system: {e}")
            self.running = False
            return False

    async def stop_system(self):
        """Stop the webcam interface system"""
        try:
            logger.info("Stopping R2D2 Webcam Interface System...")
            self.running = False

            # Stop camera
            if self.camera and self.camera.isOpened():
                self.camera.release()
                self.camera_active = False

            # Stop vision system
            if self.vision_system:
                await self.vision_system.stop_system()

            # Close windows
            cv2.destroyAllWindows()

            logger.info("✅ R2D2 Webcam Interface System stopped")

        except Exception as e:
            logger.error(f"Error stopping system: {e}")

    async def _camera_capture_loop(self):
        """Main camera capture loop - optimized for real-time performance"""
        logger.info("Starting camera capture loop...")

        while self.running and self.camera_active:
            try:
                start_time = time.time()

                # Capture frame
                ret, frame = self.camera.read()
                if not ret:
                    logger.warning("Failed to capture frame")
                    await asyncio.sleep(0.1)
                    continue

                # Store current frame for monitoring
                self.current_frame = frame.copy()

                # Add to processing queue (non-blocking)
                try:
                    self.frame_queue.put_nowait({
                        'frame': frame,
                        'timestamp': time.time(),
                        'frame_id': self.fps_counter
                    })
                except queue.Full:
                    # Drop oldest frame if queue is full
                    try:
                        self.frame_queue.get_nowait()
                        self.frame_queue.put_nowait({
                            'frame': frame,
                            'timestamp': time.time(),
                            'frame_id': self.fps_counter
                        })
                    except queue.Empty:
                        pass

                # Update FPS counter
                self.fps_counter += 1

                # Maintain target FPS
                frame_time = time.time() - start_time
                self.frame_times.append(frame_time)
                if len(self.frame_times) > 30:
                    self.frame_times.pop(0)

                target_frame_time = 1.0 / self.config["performance"]["target_fps"]
                sleep_time = max(0, target_frame_time - frame_time)
                if sleep_time > 0:
                    await asyncio.sleep(sleep_time)

            except Exception as e:
                logger.error(f"Camera capture error: {e}")
                await asyncio.sleep(0.1)

    async def _detection_processing_loop(self):
        """Process frames for guest detection and analysis"""
        logger.info("Starting detection processing loop...")

        while self.running:
            try:
                # Get frame from queue
                try:
                    frame_data = self.frame_queue.get(timeout=0.1)
                except queue.Empty:
                    continue

                frame = frame_data['frame']
                timestamp = frame_data['timestamp']

                inference_start = time.time()

                # Run detection through vision system
                detection_results = await self._process_frame_detection(frame, timestamp)

                inference_time = (time.time() - inference_start) * 1000
                self.avg_inference_time = (self.avg_inference_time * 0.9) + (inference_time * 0.1)

                # Update current detections
                self.current_detections = detection_results

                # Process triggers for each detection
                await self._process_interaction_triggers(detection_results)

                # Add to detection queue for visual interface
                try:
                    self.detection_queue.put_nowait({
                        'frame': frame,
                        'detections': detection_results,
                        'timestamp': timestamp,
                        'inference_time': inference_time
                    })
                except queue.Full:
                    # Drop oldest detection if queue is full
                    try:
                        self.detection_queue.get_nowait()
                        self.detection_queue.put_nowait({
                            'frame': frame,
                            'detections': detection_results,
                            'timestamp': timestamp,
                            'inference_time': inference_time
                        })
                    except queue.Empty:
                        pass

            except Exception as e:
                logger.error(f"Detection processing error: {e}")
                await asyncio.sleep(0.1)

    async def _process_frame_detection(self, frame: np.ndarray, timestamp: float) -> List[DetectionResult]:
        """Process single frame for guest detection and analysis"""
        try:
            detections = []

            # Run YOLO detection
            detection_results = await self.vision_system.detect_guests(frame)

            for detection in detection_results:
                bbox = detection.get('bbox', [0, 0, 0, 0])
                confidence = detection.get('confidence', 0.0)

                # Skip low confidence detections
                if confidence < self.config["detection"]["confidence_threshold"]:
                    continue

                # Extract person region for costume and face analysis
                x, y, w, h = bbox
                person_region = frame[y:y+h, x:x+w]

                # Costume recognition
                costume_result = await self.vision_system.recognize_costume(person_region)
                costume = costume_result.get('class', 'civilian')
                costume_confidence = costume_result.get('confidence', 0.0)

                # Face recognition
                face_result = await self.vision_system.recognize_face(person_region)
                face_id = face_result.get('guest_id')
                face_confidence = face_result.get('confidence', 0.0)

                # Determine distance zone
                distance_zone = self._calculate_distance_zone(bbox)

                # Get guest profile from memory
                interaction_count = 0
                relationship_level = 1
                if face_id:
                    guest_profile = self.memory_system.get_guest_profile(face_id)
                    if guest_profile:
                        interaction_count = guest_profile.interaction_count
                        relationship_level = guest_profile.relationship_level

                # Create detection result
                guest_id = face_id or f"guest_{int(timestamp)}"

                detections.append(DetectionResult(
                    guest_id=guest_id,
                    bbox=tuple(bbox),
                    confidence=confidence,
                    costume=costume,
                    costume_confidence=costume_confidence,
                    face_recognition=face_id,
                    face_confidence=face_confidence,
                    distance_zone=distance_zone,
                    timestamp=timestamp,
                    interaction_count=interaction_count,
                    relationship_level=relationship_level
                ))

            return detections

        except Exception as e:
            logger.error(f"Frame detection error: {e}")
            return []

    def _calculate_distance_zone(self, bbox: List[int]) -> str:
        """Calculate which distance zone the detection falls into"""
        x, y, w, h = bbox

        # Calculate center point of detection
        center_x = x + w // 2
        center_y = y + h // 2

        # Check which trigger zone this falls into (smallest first)
        for zone in sorted(self.trigger_zones, key=lambda z: z.bbox[2] * z.bbox[3]):
            zx, zy, zw, zh = zone.bbox
            if (zx <= center_x <= zx + zw) and (zy <= center_y <= zy + zh):
                return zone.name

        return "far"

    async def _process_interaction_triggers(self, detections: List[DetectionResult]):
        """Process interaction triggers based on detections"""
        current_time = time.time()

        for detection in detections:
            # Check cooldown
            trigger_key = f"{detection.guest_id}_{detection.distance_zone}"
            last_trigger_time = self.active_triggers.get(trigger_key, 0)

            # Get zone configuration
            zone_config = None
            for zone in self.trigger_zones:
                if zone.name == detection.distance_zone:
                    zone_config = zone
                    break

            if not zone_config:
                continue

            # Check if cooldown period has passed
            if current_time - last_trigger_time < zone_config.cooldown_seconds:
                continue

            # Trigger interaction
            await self._trigger_r2d2_interaction(detection, zone_config)

            # Update trigger time
            self.active_triggers[trigger_key] = current_time

    async def _trigger_r2d2_interaction(self, detection: DetectionResult, zone: TriggerZone):
        """Trigger R2D2 interaction based on detection and zone"""
        try:
            # Generate R2D2 response based on costume and context
            response = await self.vision_system.generate_r2d2_response(
                costume=detection.costume,
                distance_zone=detection.distance_zone,
                is_returning_guest=detection.face_recognition is not None,
                relationship_level=detection.relationship_level
            )

            # Execute motion callback
            if self.motion_callback and response.get('movement_pattern'):
                motion_data = {
                    'movement_pattern': response['movement_pattern'],
                    'light_pattern': response.get('light_pattern', 'default'),
                    'priority': zone.priority,
                    'duration': response.get('duration', 3.0),
                    'context': {
                        'guest_id': detection.guest_id,
                        'costume': detection.costume,
                        'distance_zone': detection.distance_zone,
                        'trigger_zone': zone.name
                    }
                }
                await self.motion_callback(motion_data)

            # Execute audio callback
            if self.audio_callback and response.get('audio_sequence'):
                audio_data = {
                    'audio_sequence': response['audio_sequence'],
                    'priority': zone.priority,
                    'context': {
                        'guest_id': detection.guest_id,
                        'costume': detection.costume,
                        'emotion': response.get('emotion', 'neutral')
                    }
                }
                await self.audio_callback(audio_data)

            # Log interaction
            if detection.face_recognition:
                self.memory_system.log_interaction(
                    detection.guest_id,
                    detection.costume,
                    response.get('emotion', 'neutral'),
                    zone.interaction_type
                )

            logger.info(f"🤖 R2D2 interaction triggered: {detection.costume} in {zone.name} zone")

        except Exception as e:
            logger.error(f"Failed to trigger R2D2 interaction: {e}")

    async def _visual_interface_loop(self):
        """Main visual interface loop with overlays and monitoring"""
        logger.info("Starting visual interface loop...")

        while self.running:
            try:
                # Get detection data from queue
                try:
                    detection_data = self.detection_queue.get(timeout=0.1)
                except queue.Empty:
                    continue

                frame = detection_data['frame']
                detections = detection_data['detections']
                timestamp = detection_data['timestamp']
                inference_time = detection_data['inference_time']

                # Create visual overlay
                display_frame = self._create_visual_overlay(
                    frame, detections, inference_time
                )

                # Show interface if enabled
                if self.show_interface:
                    cv2.imshow('R2D2 Webcam Interface', display_frame)

                    # Handle keyboard input
                    key = cv2.waitKey(1) & 0xFF
                    if key == ord('q'):
                        logger.info("Quit command received")
                        self.running = False
                    elif key == ord('m'):
                        self.show_agent_monitor = not self.show_agent_monitor
                    elif key == ord('z'):
                        self.config["visual"]["show_zones"] = not self.config["visual"]["show_zones"]
                    elif key == ord('b'):
                        self.config["visual"]["show_bboxes"] = not self.config["visual"]["show_bboxes"]
                    elif key == ord('c'):
                        self.config["visual"]["show_confidence"] = not self.config["visual"]["show_confidence"]

                # Broadcast to monitoring clients
                if self.monitor_clients:
                    await self._broadcast_detection_update(display_frame, detections)

            except Exception as e:
                logger.error(f"Visual interface error: {e}")
                await asyncio.sleep(0.1)

    def _create_visual_overlay(self, frame: np.ndarray, detections: List[DetectionResult],
                             inference_time: float) -> np.ndarray:
        """Create visual overlay with detection results and system status"""
        display_frame = frame.copy()

        # Draw trigger zones
        if self.config["visual"]["show_zones"]:
            self._draw_trigger_zones(display_frame)

        # Draw detection bounding boxes
        if self.config["visual"]["show_bboxes"]:
            self._draw_detection_bboxes(display_frame, detections)

        # Draw system status overlay
        if self.config["visual"]["show_status"]:
            self._draw_status_overlay(display_frame, inference_time)

        # Draw agent monitoring panel
        if self.show_agent_monitor:
            self._draw_agent_monitor_panel(display_frame, detections)

        return display_frame

    def _draw_trigger_zones(self, frame: np.ndarray):
        """Draw interaction trigger zones"""
        overlay = frame.copy()

        for zone in self.trigger_zones:
            x, y, w, h = zone.bbox

            # Draw zone rectangle
            cv2.rectangle(overlay, (x, y), (x + w, y + h), zone.color, 2)

            # Draw zone label
            label = f"{zone.name.upper()} ZONE"
            label_size = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)[0]
            cv2.rectangle(overlay, (x, y - 25), (x + label_size[0] + 10, y), zone.color, -1)
            cv2.putText(overlay, label, (x + 5, y - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)

        # Blend overlay with original frame
        cv2.addWeighted(overlay, self.overlay_opacity, frame, 1 - self.overlay_opacity, 0, frame)

    def _draw_detection_bboxes(self, frame: np.ndarray, detections: List[DetectionResult]):
        """Draw detection bounding boxes with information"""
        for detection in detections:
            x, y, w, h = detection.bbox

            # Choose color based on distance zone
            zone_colors = {
                "immediate": (0, 0, 255),    # Red
                "close": (0, 165, 255),      # Orange
                "medium": (0, 255, 255),     # Yellow
                "far": (0, 255, 0)           # Green
            }
            color = zone_colors.get(detection.distance_zone, (255, 255, 255))

            # Draw bounding box
            thickness = 3 if detection.face_recognition else 2
            cv2.rectangle(frame, (x, y), (x + w, y + h), color, thickness)

            # Prepare label text
            labels = []
            if self.config["visual"]["show_confidence"]:
                labels.append(f"Det: {detection.confidence:.2f}")

            labels.append(f"Costume: {detection.costume}")
            if detection.costume_confidence > 0.5:
                labels.append(f"({detection.costume_confidence:.2f})")

            if detection.face_recognition:
                labels.append(f"Guest: {detection.face_recognition}")
                labels.append(f"Visits: {detection.interaction_count}")

            labels.append(f"Zone: {detection.distance_zone}")

            # Draw labels
            y_offset = y - 10
            for i, label in enumerate(labels):
                if y_offset < 20:
                    y_offset = y + h + 20 + (i * 20)
                else:
                    y_offset -= 20

                # Background for text
                label_size = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)[0]
                cv2.rectangle(frame, (x, y_offset - 15), (x + label_size[0] + 5, y_offset + 5), color, -1)
                cv2.putText(frame, label, (x + 2, y_offset), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)

    def _draw_status_overlay(self, frame: np.ndarray, inference_time: float):
        """Draw system status overlay"""
        # Calculate current FPS
        current_time = time.time()
        if current_time - self.fps_start_time >= 1.0:
            self.system_status.fps = self.fps_counter / (current_time - self.fps_start_time)
            self.fps_counter = 0
            self.fps_start_time = current_time

        # Update status
        self.system_status.inference_time_ms = inference_time
        self.system_status.queue_size = self.frame_queue.qsize()
        self.system_status.active_detections = len(self.current_detections)
        self.system_status.timestamp = current_time

        # System resource usage
        self.system_status.cpu_usage = psutil.cpu_percent()
        self.system_status.memory_usage = psutil.virtual_memory().percent

        try:
            gpus = GPUtil.getGPUs()
            if gpus:
                gpu = gpus[0]
                self.system_status.gpu_usage = gpu.load * 100
                self.system_status.temperature = gpu.temperature
        except:
            pass

        # Draw status panel
        panel_height = 150
        panel_width = 300
        overlay = frame.copy()

        cv2.rectangle(overlay, (10, 10), (panel_width, panel_height), (0, 0, 0), -1)
        cv2.addWeighted(overlay, 0.7, frame, 0.3, 0, frame)

        # Status text
        status_texts = [
            f"FPS: {self.system_status.fps:.1f}",
            f"Inference: {self.system_status.inference_time_ms:.1f}ms",
            f"Queue: {self.system_status.queue_size}",
            f"Detections: {self.system_status.active_detections}",
            f"CPU: {self.system_status.cpu_usage:.1f}%",
            f"GPU: {self.system_status.gpu_usage:.1f}%",
            f"Memory: {self.system_status.memory_usage:.1f}%",
            f"Temp: {self.system_status.temperature:.1f}°C"
        ]

        for i, text in enumerate(status_texts):
            y_pos = 30 + (i * 15)
            color = (0, 255, 0)  # Green by default

            # Color coding for warnings
            if "FPS" in text and self.system_status.fps < 20:
                color = (0, 165, 255)  # Orange
            elif "Inference" in text and self.system_status.inference_time_ms > 100:
                color = (0, 165, 255)  # Orange
            elif "CPU" in text and self.system_status.cpu_usage > 80:
                color = (0, 165, 255)  # Orange
            elif "GPU" in text and self.system_status.gpu_usage > 95:
                color = (0, 165, 255)  # Orange
            elif "Temp" in text and self.system_status.temperature > 80:
                color = (0, 0, 255)  # Red

            cv2.putText(frame, text, (15, y_pos), cv2.FONT_HERSHEY_SIMPLEX, 0.4, color, 1)

    def _draw_agent_monitor_panel(self, frame: np.ndarray, detections: List[DetectionResult]):
        """Draw agent monitoring panel"""
        panel_x = frame.shape[1] - 250
        panel_y = 10
        panel_width = 240
        panel_height = min(200 + len(detections) * 60, frame.shape[0] - 20)

        # Draw panel background
        overlay = frame.copy()
        cv2.rectangle(overlay, (panel_x, panel_y), (panel_x + panel_width, panel_y + panel_height), (0, 0, 0), -1)
        cv2.addWeighted(overlay, 0.8, frame, 0.2, 0, frame)

        # Panel title
        cv2.putText(frame, "AGENT MONITOR", (panel_x + 10, panel_y + 20),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)

        # System status
        y_offset = panel_y + 40
        status_items = [
            f"Status: {'ACTIVE' if self.running else 'INACTIVE'}",
            f"Camera: {'ONLINE' if self.camera_active else 'OFFLINE'}",
            f"Triggers: {len([t for t in self.active_triggers.values() if time.time() - t < 30])}",
            f"Memory: {len(self.memory_system.get_all_guests()) if self.memory_system else 0} guests"
        ]

        for item in status_items:
            cv2.putText(frame, item, (panel_x + 10, y_offset),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.3, (200, 200, 200), 1)
            y_offset += 15

        # Current detections
        y_offset += 10
        cv2.putText(frame, "CURRENT DETECTIONS:", (panel_x + 10, y_offset),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 255), 1)
        y_offset += 15

        for i, detection in enumerate(detections[:3]):  # Show max 3 detections
            guest_text = f"#{i+1}: {detection.costume}"
            zone_text = f"Zone: {detection.distance_zone}"
            conf_text = f"Conf: {detection.confidence:.2f}"

            cv2.putText(frame, guest_text, (panel_x + 10, y_offset),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.3, (255, 255, 0), 1)
            y_offset += 12
            cv2.putText(frame, zone_text, (panel_x + 15, y_offset),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.3, (200, 200, 200), 1)
            y_offset += 12
            cv2.putText(frame, conf_text, (panel_x + 15, y_offset),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.3, (200, 200, 200), 1)
            y_offset += 20

        # Controls
        y_offset += 10
        cv2.putText(frame, "CONTROLS:", (panel_x + 10, y_offset),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 255), 1)
        y_offset += 15

        controls = [
            "Q: Quit", "M: Toggle Monitor", "Z: Toggle Zones",
            "B: Toggle Boxes", "C: Toggle Confidence"
        ]

        for control in controls:
            cv2.putText(frame, control, (panel_x + 10, y_offset),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.3, (150, 150, 150), 1)
            y_offset += 12

    async def _broadcast_detection_update(self, frame: np.ndarray, detections: List[DetectionResult]):
        """Broadcast detection updates to monitoring clients"""
        if not self.monitor_clients:
            return

        try:
            # Encode frame for transmission
            _, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
            img_base64 = base64.b64encode(buffer).decode('utf-8')

            # Prepare detection data
            detection_data = []
            for detection in detections:
                detection_data.append({
                    'guest_id': detection.guest_id,
                    'bbox': detection.bbox,
                    'confidence': detection.confidence,
                    'costume': detection.costume,
                    'distance_zone': detection.distance_zone,
                    'face_recognition': detection.face_recognition,
                    'interaction_count': detection.interaction_count
                })

            # Broadcast update
            await self.sio.emit('detection_update', {
                'frame': img_base64,
                'detections': detection_data,
                'system_status': asdict(self.system_status),
                'timestamp': time.time()
            })

        except Exception as e:
            logger.error(f"Failed to broadcast detection update: {e}")

    async def _system_monitoring_loop(self):
        """Background system monitoring and alerts"""
        logger.info("Starting system monitoring loop...")

        while self.running:
            try:
                # Check system health
                await self._check_system_health()

                # Broadcast status to monitoring clients
                if self.monitor_clients:
                    await self.sio.emit('status_update', asdict(self.system_status))

                # Sleep for monitoring interval
                await asyncio.sleep(self.config["monitoring"]["update_interval_ms"] / 1000.0)

            except Exception as e:
                logger.error(f"System monitoring error: {e}")
                await asyncio.sleep(1.0)

    async def _check_system_health(self):
        """Check system health and generate alerts"""
        current_time = time.time()

        # Performance alerts
        if self.system_status.fps < 20:
            logger.warning(f"Low FPS detected: {self.system_status.fps:.1f}")

        if self.system_status.inference_time_ms > 150:
            logger.warning(f"High inference time: {self.system_status.inference_time_ms:.1f}ms")

        if self.system_status.temperature > 85:
            logger.warning(f"High temperature: {self.system_status.temperature:.1f}°C")

        # Resource alerts
        if self.system_status.cpu_usage > 90:
            logger.warning(f"High CPU usage: {self.system_status.cpu_usage:.1f}%")

        if self.system_status.gpu_usage > 98:
            logger.warning(f"High GPU usage: {self.system_status.gpu_usage:.1f}%")

        # Queue size alerts
        if self.system_status.queue_size > 8:
            logger.warning(f"High queue size: {self.system_status.queue_size}")

    # Integration callback setters
    def set_motion_callback(self, callback: Callable):
        """Set motion system callback"""
        self.motion_callback = callback
        logger.info("Motion callback registered")

    def set_audio_callback(self, callback: Callable):
        """Set audio system callback"""
        self.audio_callback = callback
        logger.info("Audio callback registered")

    def set_status_callback(self, callback: Callable):
        """Set status update callback"""
        self.status_callback = callback
        logger.info("Status callback registered")

    # Public interface methods
    def get_system_status(self) -> Dict[str, Any]:
        """Get current system status"""
        return asdict(self.system_status)

    def get_current_detections(self) -> List[Dict[str, Any]]:
        """Get current detection results"""
        return [asdict(detection) for detection in self.current_detections]

    def update_config(self, config_updates: Dict[str, Any]):
        """Update system configuration"""
        for key, value in config_updates.items():
            if key in self.config:
                if isinstance(self.config[key], dict) and isinstance(value, dict):
                    self.config[key].update(value)
                else:
                    self.config[key] = value
                logger.info(f"Updated config: {key}")

    async def capture_screenshot(self) -> Optional[np.ndarray]:
        """Capture current screenshot"""
        if hasattr(self, 'current_frame') and self.current_frame is not None:
            return self.current_frame.copy()
        return None

if __name__ == "__main__":
    # Example usage
    async def main():
        interface = R2D2WebcamInterface()

        # Set up callbacks
        async def motion_callback(motion_data):
            print(f"🤖 Motion: {motion_data['movement_pattern']}")

        async def audio_callback(audio_data):
            print(f"🔊 Audio: {audio_data['audio_sequence']}")

        interface.set_motion_callback(motion_callback)
        interface.set_audio_callback(audio_callback)

        # Start system
        if await interface.start_system():
            try:
                # Keep running until interrupted
                while interface.running:
                    await asyncio.sleep(1)
            except KeyboardInterrupt:
                pass
            finally:
                await interface.stop_system()
        else:
            print("Failed to start webcam interface")

    asyncio.run(main())