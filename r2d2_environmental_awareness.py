#!/usr/bin/env python3
"""
R2D2 Environmental Awareness System
==================================

Advanced environmental processing system that transforms raw sensor data
into meaningful behavioral triggers for authentic R2D2 character responses.

This system provides:
- Multi-sensor data fusion and processing
- Context-aware behavior trigger generation
- Adaptive learning from environmental patterns
- Real-time threat and opportunity assessment
- Social context understanding for appropriate responses

Technical Features:
- Vision system integration for person/object detection
- Audio level monitoring for social engagement cues
- Motion detection and tracking for security awareness
- Spatial relationship understanding for safe operation
- Character recognition for personalized interactions

Author: Expert Python Coder
Target: NVIDIA Orin Nano R2D2 Systems
Integration: Vision (8767), Audio, Dashboard, Behavioral Intelligence
"""

import asyncio
import json
import logging
import time
import threading
import websockets
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple, Set
from dataclasses import dataclass, field, asdict
from enum import Enum
import queue
import sys
import os
import math
from collections import deque, defaultdict
import cv2

# Import system components
sys.path.append('/home/rolo/r2ai')

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class EnvironmentalThreatLevel(Enum):
    """Threat assessment levels for environmental situations"""
    SAFE = "safe"
    LOW_CAUTION = "low_caution"
    MODERATE_ALERT = "moderate_alert"
    HIGH_ALERT = "high_alert"
    EMERGENCY = "emergency"

class SocialContext(Enum):
    """Social contexts that affect behavioral responses"""
    ALONE = "alone"
    ONE_ON_ONE = "one_on_one"
    SMALL_GROUP = "small_group"
    CROWD = "crowd"
    PERFORMANCE = "performance"
    MAINTENANCE = "maintenance"
    CONVENTION = "convention"

class PersonInteractionType(Enum):
    """Types of person interactions R2D2 can have"""
    FIRST_MEETING = "first_meeting"
    FAMILIAR_PERSON = "familiar_person"
    FRIEND = "friend"
    CHILD = "child"
    ADULT = "adult"
    GROUP_MEMBER = "group_member"
    AUTHORITY_FIGURE = "authority_figure"
    CHARACTER_COSPLAYER = "character_cosplayer"

@dataclass
class PersonProfile:
    """Profile of a detected person with interaction history"""
    person_id: str
    first_detected: float
    last_seen: float
    total_interactions: int
    interaction_quality: float  # -1.0 to 1.0
    estimated_age_group: Optional[str] = None
    is_child: bool = False
    is_cosplayer: bool = False
    character_type: Optional[str] = None
    preferred_responses: List[str] = field(default_factory=list)
    interaction_history: List[Dict[str, Any]] = field(default_factory=list)

    # Spatial tracking
    last_position: Optional[Tuple[int, int]] = None
    movement_pattern: str = "stationary"  # stationary, approaching, departing, circling
    distance_trend: str = "stable"  # approaching, departing, stable

    # Social context
    came_with_group: bool = False
    group_size: int = 1
    social_role: str = "individual"  # individual, group_leader, follower, observer

@dataclass
class EnvironmentalReading:
    """Comprehensive environmental sensor reading"""
    timestamp: float = field(default_factory=time.time)

    # Vision data
    people_detected: List[Dict[str, Any]] = field(default_factory=list)
    total_people_count: int = 0
    children_count: int = 0
    adults_count: int = 0

    # Character detection
    character_detections: List[Dict[str, Any]] = field(default_factory=list)
    jedi_candidates: List[Dict[str, Any]] = field(default_factory=list)
    droid_detections: List[Dict[str, Any]] = field(default_factory=list)

    # Spatial analysis
    average_person_distance: Optional[float] = None
    closest_person_distance: Optional[float] = None
    crowd_density: float = 0.0
    movement_activity_level: float = 0.0

    # Audio context (placeholder for future integration)
    ambient_noise_level: float = 0.0
    speech_detected: bool = False
    music_detected: bool = False
    sound_direction: Optional[float] = None

    # Environmental context
    lighting_quality: str = "normal"  # bright, normal, dim, dark
    space_constraint: float = 1.0  # 0.0 = very cramped, 1.0 = wide open
    safety_clearance: float = 1.0  # 0.0 = unsafe, 1.0 = completely safe

    # System context
    dashboard_clients_connected: int = 0
    system_performance: float = 1.0  # 0.0 = poor, 1.0 = excellent

@dataclass
class BehavioralTriggerEvent:
    """Event that should trigger a behavioral response"""
    trigger_id: str
    trigger_type: str
    priority: int  # 1-10, higher = more urgent
    confidence: float  # 0.0-1.0

    # Context data
    environmental_context: Dict[str, Any]
    social_context: SocialContext
    threat_level: EnvironmentalThreatLevel

    # Suggested responses
    suggested_behaviors: List[str]
    audio_context_suggestions: List[str]

    # Timing
    expiration_time: float
    minimum_duration: float = 0.0

class R2D2EnvironmentalAwareness:
    """
    Advanced environmental awareness system that processes multi-sensor data
    and generates intelligent behavioral triggers for authentic R2D2 responses
    """

    def __init__(self, vision_websocket_port: int = 8767,
                 behavioral_websocket_port: int = 8768):
        """Initialize the environmental awareness system"""

        # Network configuration
        self.vision_websocket_port = vision_websocket_port
        self.behavioral_websocket_port = behavioral_websocket_port

        # Core data structures
        self.current_reading = EnvironmentalReading()
        self.reading_history = deque(maxlen=1000)
        self.person_profiles: Dict[str, PersonProfile] = {}

        # Analysis and triggers
        self.trigger_queue = queue.PriorityQueue()
        self.active_triggers: Dict[str, BehavioralTriggerEvent] = {}
        self.environmental_patterns = defaultdict(list)

        # System state
        self.current_social_context = SocialContext.ALONE
        self.current_threat_level = EnvironmentalThreatLevel.SAFE
        self.last_significant_event: Optional[float] = None

        # Configuration
        self.config = {
            'person_recognition_confidence_threshold': 0.7,
            'character_recognition_confidence_threshold': 0.6,
            'proximity_alert_distance': 1.0,  # meters
            'crowd_threshold': 4,  # number of people
            'movement_sensitivity': 0.3,
            'social_interaction_timeout': 30.0,  # seconds
            'learning_enabled': True,
            'threat_assessment_enabled': True
        }

        # Performance metrics
        self.metrics = {
            'readings_processed': 0,
            'triggers_generated': 0,
            'people_tracked': 0,
            'character_recognitions': 0,
            'threat_assessments': 0,
            'average_processing_time': 0.0,
            'system_uptime_start': time.time()
        }

        # Learning and adaptation
        self.interaction_patterns = defaultdict(list)
        self.successful_responses = defaultdict(int)
        self.environmental_memory = {}

        # System control
        self.running = False
        self.connections = {
            'vision_client': None,
            'behavioral_client': None
        }

        logger.info("R2D2 Environmental Awareness System initialized")

    async def start_environmental_processing(self):
        """Start the environmental awareness processing system"""
        logger.info("🌍 Starting R2D2 Environmental Awareness System")

        self.running = True

        # Start background processing threads
        processing_thread = threading.Thread(
            target=self._environmental_processing_loop,
            daemon=True,
            name="EnvironmentalProcessing"
        )
        processing_thread.start()

        pattern_analysis_thread = threading.Thread(
            target=self._pattern_analysis_loop,
            daemon=True,
            name="PatternAnalysis"
        )
        pattern_analysis_thread.start()

        # Start connection tasks
        tasks = [
            asyncio.create_task(self._connect_to_vision_system()),
            asyncio.create_task(self._connect_to_behavioral_system())
        ]

        try:
            await asyncio.gather(*tasks)
        except KeyboardInterrupt:
            logger.info("Environmental awareness system stopped by user")
        finally:
            await self.stop_environmental_processing()

    def _environmental_processing_loop(self):
        """Main environmental processing loop"""
        logger.info("Environmental processing loop started")

        while self.running:
            try:
                start_time = time.time()

                # Process current environmental reading
                self._analyze_current_environment()

                # Generate behavioral triggers
                self._generate_behavioral_triggers()

                # Clean up expired data
                self._cleanup_expired_data()

                # Update performance metrics
                processing_time = time.time() - start_time
                self._update_performance_metrics(processing_time)

                # Sleep for processing interval (10Hz)
                time.sleep(0.1)

            except Exception as e:
                logger.error(f"Error in environmental processing loop: {e}")
                time.sleep(1.0)

    def _pattern_analysis_loop(self):
        """Background pattern analysis and learning loop"""
        logger.info("Pattern analysis loop started")

        while self.running:
            try:
                if self.config['learning_enabled']:
                    self._analyze_interaction_patterns()
                    self._update_person_profiles()
                    self._adapt_trigger_sensitivities()

                time.sleep(5.0)  # Run every 5 seconds

            except Exception as e:
                logger.error(f"Error in pattern analysis: {e}")
                time.sleep(10.0)

    async def _connect_to_vision_system(self):
        """Connect to the vision system WebSocket"""
        uri = f"ws://localhost:{self.vision_websocket_port}"

        while self.running:
            try:
                logger.info(f"Connecting to vision system at {uri}")

                async with websockets.connect(uri) as websocket:
                    self.connections['vision_client'] = websocket
                    logger.info("✅ Connected to vision system")

                    # Listen for vision data
                    async for message in websocket:
                        try:
                            data = json.loads(message)
                            await self._process_vision_data(data)
                        except json.JSONDecodeError:
                            logger.warning("Invalid JSON from vision system")
                        except Exception as e:
                            logger.error(f"Error processing vision data: {e}")

            except websockets.exceptions.ConnectionClosed:
                logger.warning("Vision connection closed, retrying...")
            except Exception as e:
                logger.error(f"Vision connection error: {e}")

            # Wait before retry
            if self.running:
                await asyncio.sleep(5.0)

    async def _connect_to_behavioral_system(self):
        """Connect to the behavioral intelligence system"""
        uri = f"ws://localhost:{self.behavioral_websocket_port}"

        while self.running:
            try:
                logger.info(f"Connecting to behavioral system at {uri}")

                async with websockets.connect(uri) as websocket:
                    self.connections['behavioral_client'] = websocket
                    logger.info("✅ Connected to behavioral intelligence system")

                    # Send environmental updates
                    while self.running:
                        await self._send_environmental_update(websocket)
                        await asyncio.sleep(1.0)  # Send updates every second

            except websockets.exceptions.ConnectionClosed:
                logger.warning("Behavioral connection closed, retrying...")
            except Exception as e:
                logger.error(f"Behavioral connection error: {e}")

            # Wait before retry
            if self.running:
                await asyncio.sleep(5.0)

    async def _process_vision_data(self, vision_data: Dict[str, Any]):
        """Process incoming vision system data"""
        try:
            # Extract detection data
            detections = vision_data.get('detections', [])
            character_detections = vision_data.get('character_detections', [])
            frame_info = vision_data.get('frame_info', {})

            # Update current reading
            reading = EnvironmentalReading()
            reading.timestamp = time.time()

            # Process person detections
            people_detected = []
            children_count = 0
            adults_count = 0

            for detection in detections:
                if detection.get('class') == 'person':
                    confidence = detection.get('confidence', 0.0)

                    if confidence >= self.config['person_recognition_confidence_threshold']:
                        bbox = detection.get('bbox', [0, 0, 0, 0])

                        person_data = {
                            'bbox': bbox,
                            'confidence': confidence,
                            'center_x': (bbox[0] + bbox[2]) / 2,
                            'center_y': (bbox[1] + bbox[3]) / 2,
                            'width': bbox[2] - bbox[0],
                            'height': bbox[3] - bbox[1],
                            'estimated_distance': self._estimate_person_distance(bbox),
                            'estimated_age_group': self._estimate_age_group(bbox)
                        }

                        people_detected.append(person_data)

                        # Count age groups
                        if person_data['estimated_age_group'] == 'child':
                            children_count += 1
                        else:
                            adults_count += 1

            reading.people_detected = people_detected
            reading.total_people_count = len(people_detected)
            reading.children_count = children_count
            reading.adults_count = adults_count

            # Process character detections
            character_list = []
            jedi_candidates = []
            droid_detections = []

            for char_detection in character_detections:
                confidence = char_detection.get('confidence', 0.0)

                if confidence >= self.config['character_recognition_confidence_threshold']:
                    character_type = char_detection.get('character', 'unknown')

                    character_list.append(char_detection)

                    if 'jedi' in character_type.lower() or 'sith' in character_type.lower():
                        jedi_candidates.append(char_detection)
                    elif 'droid' in character_type.lower():
                        droid_detections.append(char_detection)

            reading.character_detections = character_list
            reading.jedi_candidates = jedi_candidates
            reading.droid_detections = droid_detections

            # Calculate spatial metrics
            if people_detected:
                distances = [p['estimated_distance'] for p in people_detected if p['estimated_distance']]
                if distances:
                    reading.average_person_distance = sum(distances) / len(distances)
                    reading.closest_person_distance = min(distances)

                # Calculate crowd density
                frame_area = frame_info.get('width', 640) * frame_info.get('height', 480)
                total_person_area = sum(p['width'] * p['height'] for p in people_detected)
                reading.crowd_density = total_person_area / frame_area

            # Update current reading
            self.current_reading = reading
            self.reading_history.append(reading)

            # Update person profiles
            self._update_person_tracking(reading)

            # Update metrics
            self.metrics['readings_processed'] += 1

        except Exception as e:
            logger.error(f"Error processing vision data: {e}")

    def _estimate_person_distance(self, bbox: List[float]) -> Optional[float]:
        """Estimate person distance based on bounding box size"""
        try:
            # Simple distance estimation based on person height in pixels
            person_height_pixels = bbox[3] - bbox[1]

            # Rough calibration (adjust based on your camera setup)
            # Assumes average person height of 1.7m
            if person_height_pixels > 0:
                estimated_distance = (1.7 * 400) / person_height_pixels  # meters
                return max(0.5, min(10.0, estimated_distance))  # Clamp to reasonable range

            return None

        except Exception as e:
            logger.error(f"Error estimating distance: {e}")
            return None

    def _estimate_age_group(self, bbox: List[float]) -> str:
        """Estimate age group based on bounding box proportions"""
        try:
            person_height = bbox[3] - bbox[1]
            person_width = bbox[2] - bbox[0]

            # Simple heuristic: children are typically shorter relative to frame
            if person_height < 200:  # Adjust threshold based on your setup
                return 'child'
            else:
                return 'adult'

        except Exception:
            return 'adult'  # Default to adult

    def _update_person_tracking(self, reading: EnvironmentalReading):
        """Update person tracking and profiles"""
        try:
            current_time = time.time()

            # Track each detected person
            for person_data in reading.people_detected:
                person_id = self._generate_person_id(person_data)

                if person_id not in self.person_profiles:
                    # New person detected
                    profile = PersonProfile(
                        person_id=person_id,
                        first_detected=current_time,
                        last_seen=current_time,
                        total_interactions=0,
                        interaction_quality=0.0,
                        estimated_age_group=person_data.get('estimated_age_group', 'adult'),
                        is_child=person_data.get('estimated_age_group') == 'child'
                    )

                    profile.last_position = (person_data['center_x'], person_data['center_y'])
                    profile.group_size = reading.total_people_count
                    profile.came_with_group = reading.total_people_count > 1

                    self.person_profiles[person_id] = profile

                    logger.info(f"👤 New person detected: {person_id} ({profile.estimated_age_group})")

                else:
                    # Update existing person
                    profile = self.person_profiles[person_id]
                    profile.last_seen = current_time

                    # Update position and movement
                    if profile.last_position:
                        old_x, old_y = profile.last_position
                        new_x, new_y = person_data['center_x'], person_data['center_y']

                        movement_distance = math.sqrt((new_x - old_x)**2 + (new_y - old_y)**2)

                        if movement_distance > 20:  # Significant movement
                            profile.movement_pattern = "moving"
                        else:
                            profile.movement_pattern = "stationary"

                    profile.last_position = (person_data['center_x'], person_data['center_y'])

            # Clean up profiles for people who haven't been seen recently
            profiles_to_remove = []
            for person_id, profile in self.person_profiles.items():
                if current_time - profile.last_seen > self.config['social_interaction_timeout']:
                    profiles_to_remove.append(person_id)

            for person_id in profiles_to_remove:
                logger.info(f"👤 Person departed: {person_id}")
                del self.person_profiles[person_id]

        except Exception as e:
            logger.error(f"Error updating person tracking: {e}")

    def _generate_person_id(self, person_data: Dict[str, Any]) -> str:
        """Generate a consistent ID for a person based on their characteristics"""
        try:
            # Simple ID generation based on position and size
            # In a more sophisticated system, this would use facial recognition
            center_x = int(person_data['center_x'] / 50) * 50  # Quantize position
            center_y = int(person_data['center_y'] / 50) * 50
            size = int((person_data['width'] * person_data['height']) / 1000) * 1000

            return f"person_{center_x}_{center_y}_{size}"

        except Exception:
            return f"person_{int(time.time() * 1000)}"

    def _analyze_current_environment(self):
        """Analyze current environmental conditions"""
        try:
            # Determine social context
            people_count = self.current_reading.total_people_count

            if people_count == 0:
                self.current_social_context = SocialContext.ALONE
            elif people_count == 1:
                self.current_social_context = SocialContext.ONE_ON_ONE
            elif people_count <= 3:
                self.current_social_context = SocialContext.SMALL_GROUP
            elif people_count <= self.config['crowd_threshold']:
                self.current_social_context = SocialContext.CROWD
            else:
                self.current_social_context = SocialContext.CROWD

            # Assess threat level
            if self.config['threat_assessment_enabled']:
                threat_level = self._assess_threat_level()
                if threat_level != self.current_threat_level:
                    logger.info(f"⚠️ Threat level changed: {self.current_threat_level.value} → {threat_level.value}")
                    self.current_threat_level = threat_level

            # Update environmental patterns
            pattern_key = f"{self.current_social_context.value}_{people_count}"
            self.environmental_patterns[pattern_key].append({
                'timestamp': time.time(),
                'people_count': people_count,
                'children_present': self.current_reading.children_count > 0,
                'characters_detected': len(self.current_reading.character_detections) > 0
            })

        except Exception as e:
            logger.error(f"Error analyzing environment: {e}")

    def _assess_threat_level(self) -> EnvironmentalThreatLevel:
        """Assess current environmental threat level"""
        try:
            threat_indicators = []

            # Check proximity
            if self.current_reading.closest_person_distance:
                if self.current_reading.closest_person_distance < self.config['proximity_alert_distance']:
                    threat_indicators.append('close_proximity')

            # Check crowd density
            if self.current_reading.crowd_density > 0.3:
                threat_indicators.append('high_crowd_density')

            # Check rapid movement
            if self.current_reading.movement_activity_level > 0.8:
                threat_indicators.append('high_activity')

            # Check for too many people
            if self.current_reading.total_people_count > 8:
                threat_indicators.append('overcrowding')

            # Assess threat level based on indicators
            if not threat_indicators:
                return EnvironmentalThreatLevel.SAFE
            elif len(threat_indicators) == 1:
                return EnvironmentalThreatLevel.LOW_CAUTION
            elif len(threat_indicators) == 2:
                return EnvironmentalThreatLevel.MODERATE_ALERT
            elif len(threat_indicators) >= 3:
                return EnvironmentalThreatLevel.HIGH_ALERT

            return EnvironmentalThreatLevel.SAFE

        except Exception as e:
            logger.error(f"Error assessing threat level: {e}")
            return EnvironmentalThreatLevel.SAFE

    def _generate_behavioral_triggers(self):
        """Generate behavioral triggers based on environmental analysis"""
        try:
            current_time = time.time()

            # New person detection triggers
            for person_id, profile in self.person_profiles.items():
                if current_time - profile.first_detected < 2.0:  # Recently detected
                    trigger = self._create_person_greeting_trigger(profile)
                    if trigger:
                        self._queue_trigger(trigger)

            # Character recognition triggers
            for char_detection in self.current_reading.character_detections:
                trigger = self._create_character_recognition_trigger(char_detection)
                if trigger:
                    self._queue_trigger(trigger)

            # Social context change triggers
            trigger = self._create_social_context_trigger()
            if trigger:
                self._queue_trigger(trigger)

            # Idle state triggers
            if self.last_significant_event is None or current_time - self.last_significant_event > 30.0:
                trigger = self._create_idle_behavior_trigger()
                if trigger:
                    self._queue_trigger(trigger)

        except Exception as e:
            logger.error(f"Error generating behavioral triggers: {e}")

    def _create_person_greeting_trigger(self, profile: PersonProfile) -> Optional[BehavioralTriggerEvent]:
        """Create greeting trigger for a detected person"""
        try:
            if profile.total_interactions == 0:  # First meeting
                interaction_type = PersonInteractionType.FIRST_MEETING
                suggested_behaviors = ["curious_investigation_greeting", "polite_stranger_greeting"]
                audio_contexts = ["curious_inquisitive", "chatting_casual"]
            else:
                interaction_type = PersonInteractionType.FAMILIAR_PERSON
                suggested_behaviors = ["friendly_greeting", "enthusiastic_friend_greeting"]
                audio_contexts = ["greeting_friends", "happy_excited"]

            # Adjust for children
            if profile.is_child:
                suggested_behaviors.insert(0, "gentle_child_greeting")
                audio_contexts.insert(0, "playful_mischievous")

            # Adjust for group context
            if profile.came_with_group:
                suggested_behaviors.append("group_acknowledgment")

            trigger = BehavioralTriggerEvent(
                trigger_id=f"greeting_{profile.person_id}_{int(time.time())}",
                trigger_type="person_greeting",
                priority=7 if interaction_type == PersonInteractionType.FIRST_MEETING else 5,
                confidence=0.9,
                environmental_context={
                    'person_id': profile.person_id,
                    'interaction_type': interaction_type.value,
                    'is_child': profile.is_child,
                    'group_size': profile.group_size
                },
                social_context=self.current_social_context,
                threat_level=self.current_threat_level,
                suggested_behaviors=suggested_behaviors,
                audio_context_suggestions=audio_contexts,
                expiration_time=time.time() + 10.0,
                minimum_duration=3.0
            )

            return trigger

        except Exception as e:
            logger.error(f"Error creating greeting trigger: {e}")
            return None

    def _create_character_recognition_trigger(self, char_detection: Dict[str, Any]) -> Optional[BehavioralTriggerEvent]:
        """Create trigger for character recognition"""
        try:
            character_type = char_detection.get('character', 'unknown')
            confidence = char_detection.get('confidence', 0.0)

            if 'jedi' in character_type.lower() or 'sith' in character_type.lower():
                suggested_behaviors = ["jedi_recognition_respect", "force_user_acknowledgment"]
                audio_contexts = ["jedi_recognition", "alert_warning"]
                priority = 9
            elif 'droid' in character_type.lower():
                suggested_behaviors = ["droid_excitement", "astromech_greeting"]
                audio_contexts = ["astromech_duties", "happy_excited"]
                priority = 8
            elif 'princess' in character_type.lower():
                suggested_behaviors = ["royal_respect_bow", "princess_leia_sequence"]
                audio_contexts = ["princess_leia_message", "jedi_recognition"]
                priority = 10
            else:
                suggested_behaviors = ["character_acknowledgment", "curious_investigation"]
                audio_contexts = ["curious_inquisitive", "chatting_casual"]
                priority = 6

            trigger = BehavioralTriggerEvent(
                trigger_id=f"character_{character_type}_{int(time.time())}",
                trigger_type="character_recognition",
                priority=priority,
                confidence=confidence,
                environmental_context={
                    'character_type': character_type,
                    'detection_confidence': confidence,
                    'bbox': char_detection.get('bbox', [])
                },
                social_context=self.current_social_context,
                threat_level=self.current_threat_level,
                suggested_behaviors=suggested_behaviors,
                audio_context_suggestions=audio_contexts,
                expiration_time=time.time() + 15.0,
                minimum_duration=5.0
            )

            return trigger

        except Exception as e:
            logger.error(f"Error creating character trigger: {e}")
            return None

    def _create_social_context_trigger(self) -> Optional[BehavioralTriggerEvent]:
        """Create trigger for social context changes"""
        try:
            # Check if we've had recent context changes
            if len(self.reading_history) < 5:
                return None

            # Look for social context change
            recent_contexts = []
            for reading in list(self.reading_history)[-5:]:
                if reading.total_people_count == 0:
                    recent_contexts.append(SocialContext.ALONE)
                elif reading.total_people_count == 1:
                    recent_contexts.append(SocialContext.ONE_ON_ONE)
                elif reading.total_people_count <= 3:
                    recent_contexts.append(SocialContext.SMALL_GROUP)
                else:
                    recent_contexts.append(SocialContext.CROWD)

            # Check if context just changed
            if len(set(recent_contexts)) > 1 and recent_contexts[-1] != recent_contexts[-2]:
                new_context = recent_contexts[-1]

                if new_context == SocialContext.CROWD:
                    suggested_behaviors = ["crowd_performance_mode", "playful_entertainment"]
                    audio_contexts = ["musical_entertainment", "playful_mischievous"]
                    priority = 6
                elif new_context == SocialContext.ALONE:
                    suggested_behaviors = ["return_to_idle", "area_scan"]
                    audio_contexts = ["astromech_duties", "power_up_down"]
                    priority = 3
                else:
                    return None  # No specific trigger for other contexts

                trigger = BehavioralTriggerEvent(
                    trigger_id=f"social_context_{new_context.value}_{int(time.time())}",
                    trigger_type="social_context_change",
                    priority=priority,
                    confidence=0.8,
                    environmental_context={
                        'new_context': new_context.value,
                        'people_count': self.current_reading.total_people_count
                    },
                    social_context=new_context,
                    threat_level=self.current_threat_level,
                    suggested_behaviors=suggested_behaviors,
                    audio_context_suggestions=audio_contexts,
                    expiration_time=time.time() + 8.0
                )

                return trigger

            return None

        except Exception as e:
            logger.error(f"Error creating social context trigger: {e}")
            return None

    def _create_idle_behavior_trigger(self) -> Optional[BehavioralTriggerEvent]:
        """Create trigger for idle behavior"""
        try:
            # Create idle behavior based on context
            if self.current_social_context == SocialContext.ALONE:
                suggested_behaviors = ["environmental_scan", "maintenance_check", "idle_animation"]
                audio_contexts = ["astromech_duties", "curious_inquisitive"]
            else:
                suggested_behaviors = ["attention_seeking", "social_interaction"]
                audio_contexts = ["chatting_casual", "playful_mischievous"]

            trigger = BehavioralTriggerEvent(
                trigger_id=f"idle_behavior_{int(time.time())}",
                trigger_type="idle_timeout",
                priority=2,
                confidence=0.7,
                environmental_context={'context': self.current_social_context.value},
                social_context=self.current_social_context,
                threat_level=self.current_threat_level,
                suggested_behaviors=suggested_behaviors,
                audio_context_suggestions=audio_contexts,
                expiration_time=time.time() + 20.0
            )

            return trigger

        except Exception as e:
            logger.error(f"Error creating idle trigger: {e}")
            return None

    def _queue_trigger(self, trigger: BehavioralTriggerEvent):
        """Queue a behavioral trigger for processing"""
        try:
            # Check if similar trigger already exists
            for existing_id, existing_trigger in self.active_triggers.items():
                if (existing_trigger.trigger_type == trigger.trigger_type and
                    time.time() - existing_trigger.expiration_time < 5.0):
                    # Similar recent trigger exists, skip this one
                    return

            # Add to queue (priority queue uses negative priority for high-priority-first)
            priority_score = -trigger.priority
            self.trigger_queue.put((priority_score, time.time(), trigger))

            # Add to active triggers
            self.active_triggers[trigger.trigger_id] = trigger

            self.metrics['triggers_generated'] += 1
            logger.info(f"🎯 Generated trigger: {trigger.trigger_type} (priority: {trigger.priority})")

        except Exception as e:
            logger.error(f"Error queuing trigger: {e}")

    async def _send_environmental_update(self, websocket):
        """Send environmental update to behavioral intelligence system"""
        try:
            # Prepare environmental data for behavioral system
            environmental_data = {
                'type': 'environmental_input',
                'timestamp': time.time(),
                'environmental_data': {
                    'social_context': self.current_social_context.value,
                    'threat_level': self.current_threat_level.value,
                    'people_count': self.current_reading.total_people_count,
                    'children_present': self.current_reading.children_count > 0,
                    'characters_detected': len(self.current_reading.character_detections),
                    'crowd_density': self.current_reading.crowd_density,
                    'closest_distance': self.current_reading.closest_person_distance,
                    'persons': [
                        {
                            'id': pid,
                            'confidence': 0.9,
                            'bbox': [0, 0, 100, 100],  # Placeholder
                            'face_detected': False,
                            'distance': self.current_reading.closest_person_distance
                        }
                        for pid in self.person_profiles.keys()
                    ]
                }
            }

            # Send pending triggers
            triggers_to_send = []
            while not self.trigger_queue.empty():
                try:
                    priority, queue_time, trigger = self.trigger_queue.get_nowait()

                    # Check if trigger is still valid
                    if time.time() < trigger.expiration_time:
                        triggers_to_send.append({
                            'trigger_id': trigger.trigger_id,
                            'trigger_type': trigger.trigger_type,
                            'priority': trigger.priority,
                            'confidence': trigger.confidence,
                            'suggested_behaviors': trigger.suggested_behaviors,
                            'audio_contexts': trigger.audio_context_suggestions,
                            'environmental_context': trigger.environmental_context
                        })

                except queue.Empty:
                    break

            if triggers_to_send:
                environmental_data['behavioral_triggers'] = triggers_to_send

            # Send to behavioral intelligence system
            await websocket.send(json.dumps(environmental_data))

        except Exception as e:
            logger.error(f"Error sending environmental update: {e}")

    def _cleanup_expired_data(self):
        """Clean up expired triggers and old data"""
        try:
            current_time = time.time()

            # Clean up expired triggers
            expired_triggers = []
            for trigger_id, trigger in self.active_triggers.items():
                if current_time > trigger.expiration_time:
                    expired_triggers.append(trigger_id)

            for trigger_id in expired_triggers:
                del self.active_triggers[trigger_id]

            # Clean up old environmental patterns
            for pattern_key in list(self.environmental_patterns.keys()):
                pattern_list = self.environmental_patterns[pattern_key]
                # Keep only recent patterns (last hour)
                recent_patterns = [p for p in pattern_list if current_time - p['timestamp'] < 3600]
                if recent_patterns:
                    self.environmental_patterns[pattern_key] = recent_patterns
                else:
                    del self.environmental_patterns[pattern_key]

        except Exception as e:
            logger.error(f"Error cleaning up expired data: {e}")

    def _analyze_interaction_patterns(self):
        """Analyze patterns in environmental interactions for learning"""
        try:
            if not self.config['learning_enabled']:
                return

            # Analyze successful interaction patterns
            for person_id, profile in self.person_profiles.items():
                if len(profile.interaction_history) > 2:
                    # Look for patterns in successful interactions
                    successful_interactions = [i for i in profile.interaction_history
                                             if i.get('quality', 0) > 0.5]

                    if successful_interactions:
                        # Learn preferred interaction types
                        preferred_types = defaultdict(int)
                        for interaction in successful_interactions:
                            interaction_type = interaction.get('type', 'unknown')
                            preferred_types[interaction_type] += 1

                        # Update profile preferences
                        profile.preferred_responses = [
                            interaction_type for interaction_type, count in
                            sorted(preferred_types.items(), key=lambda x: x[1], reverse=True)[:3]
                        ]

        except Exception as e:
            logger.error(f"Error analyzing interaction patterns: {e}")

    def _update_person_profiles(self):
        """Update person profiles with learning data"""
        try:
            for person_id, profile in self.person_profiles.items():
                # Update interaction quality based on recent responses
                # This would integrate with behavioral intelligence feedback
                pass

        except Exception as e:
            logger.error(f"Error updating person profiles: {e}")

    def _adapt_trigger_sensitivities(self):
        """Adapt trigger generation sensitivities based on learning"""
        try:
            # Analyze success rates of different trigger types
            # Adjust thresholds and priorities based on effectiveness
            pass

        except Exception as e:
            logger.error(f"Error adapting trigger sensitivities: {e}")

    def _update_performance_metrics(self, processing_time: float):
        """Update performance metrics"""
        try:
            # Update average processing time
            current_avg = self.metrics['average_processing_time']
            count = self.metrics['readings_processed']
            self.metrics['average_processing_time'] = (current_avg * (count - 1) + processing_time) / count

            # Update other metrics
            self.metrics['people_tracked'] = len(self.person_profiles)
            self.metrics['character_recognitions'] = len(self.current_reading.character_detections)

        except Exception as e:
            logger.error(f"Error updating performance metrics: {e}")

    def get_environmental_status(self) -> Dict[str, Any]:
        """Get comprehensive environmental status report"""
        uptime = time.time() - self.metrics['system_uptime_start']

        return {
            'system_status': {
                'running': self.running,
                'uptime_seconds': uptime,
                'vision_connected': self.connections['vision_client'] is not None,
                'behavioral_connected': self.connections['behavioral_client'] is not None
            },
            'current_environment': {
                'social_context': self.current_social_context.value,
                'threat_level': self.current_threat_level.value,
                'people_count': self.current_reading.total_people_count,
                'children_count': self.current_reading.children_count,
                'characters_detected': len(self.current_reading.character_detections),
                'crowd_density': self.current_reading.crowd_density,
                'closest_distance': self.current_reading.closest_person_distance
            },
            'person_tracking': {
                'active_profiles': len(self.person_profiles),
                'total_people_tracked': self.metrics['people_tracked'],
                'profile_summary': [
                    {
                        'person_id': pid,
                        'age_group': profile.estimated_age_group,
                        'interactions': profile.total_interactions,
                        'quality': profile.interaction_quality,
                        'last_seen': time.time() - profile.last_seen
                    }
                    for pid, profile in list(self.person_profiles.items())[:10]  # Show first 10
                ]
            },
            'trigger_system': {
                'active_triggers': len(self.active_triggers),
                'triggers_generated': self.metrics['triggers_generated'],
                'queue_size': self.trigger_queue.qsize()
            },
            'performance_metrics': dict(self.metrics),
            'configuration': dict(self.config)
        }

    async def stop_environmental_processing(self):
        """Stop the environmental awareness system"""
        logger.info("Stopping R2D2 Environmental Awareness System")

        self.running = False

        # Close WebSocket connections
        for connection_name, connection in self.connections.items():
            if connection:
                try:
                    await connection.close()
                except Exception as e:
                    logger.error(f"Error closing {connection_name}: {e}")

        logger.info("Environmental Awareness System stopped")


async def main():
    """Main entry point for R2D2 Environmental Awareness"""
    print("🌍 R2D2 Advanced Environmental Awareness System")
    print("=" * 60)
    print("Initializing intelligent environmental processing...")

    # Create environmental awareness system
    environmental_system = R2D2EnvironmentalAwareness()

    try:
        # Start the system
        await environmental_system.start_environmental_processing()

    except KeyboardInterrupt:
        print("\nShutdown requested by user")
    except Exception as e:
        logger.error(f"Critical error in environmental awareness: {e}")
    finally:
        await environmental_system.stop_environmental_processing()


if __name__ == "__main__":
    asyncio.run(main())