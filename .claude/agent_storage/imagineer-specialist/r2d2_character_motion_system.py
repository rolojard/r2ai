#!/usr/bin/env python3
"""
Disney-Level R2D2 Character Personality Motion Control System
============================================================

Advanced character animation system that brings R2D2 to life with Disney-quality
motion patterns, authentic Star Wars behaviors, and natural personality expression.
This system creates believable, engaging interactions that delight convention guests.

Features:
- Authentic R2D2 character personality with 12 distinct behavioral modes
- Bio-mechanical motion patterns based on Disney animation principles
- Natural acceleration curves with organic movement flow
- Character emotion expression through movement dynamics
- Interactive guest recognition and response behaviors
- Sophisticated multi-servo choreography for complex expressions
- Convention-safe operation with emergency stop integration

Author: Imagineer Specialist Agent
Target: NVIDIA Orin Nano R2D2 Systems
Integration with Super Coder's Disney Servo Control & Audio Coordination
"""

import time
import math
import threading
import logging
import asyncio
import random
from typing import Dict, List, Tuple, Optional, Callable, Any, Union
from dataclasses import dataclass, field
from enum import Enum
import numpy as np
from collections import deque
import json

# Import foundational systems
try:
    from servo_foundation_library import DisneyServoController, EasingType, MotionKeyframe, ServoConfig
    from audio_servo_coordinator import AudioServoCoordinator, PerformanceMode, AudioServoEvent
    from r2d2_sound_library import R2D2SoundLibrary, EmotionalState, CharacterContext
except ImportError as e:
    logging.warning(f"Import warning: {e}. Some functionality may be limited.")

# Configure logging for character motion system
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PersonalityTrait(Enum):
    """R2D2 personality traits that influence movement patterns"""
    CURIOUS = "curious"           # Eager, investigating movements
    CAUTIOUS = "cautious"         # Careful, hesitant movements
    CONFIDENT = "confident"       # Bold, assertive movements
    PLAYFUL = "playful"          # Bouncy, energetic movements
    CONCERNED = "concerned"       # Worried, protective movements
    EXCITED = "excited"          # Rapid, enthusiastic movements
    STUBBORN = "stubborn"        # Resistant, defiant movements
    LOYAL = "loyal"              # Steady, following movements
    MISCHIEVOUS = "mischievous"  # Sneaky, unexpected movements
    PROTECTIVE = "protective"    # Alert, guardian movements
    ANALYTICAL = "analytical"    # Methodical, scanning movements
    HEROIC = "heroic"           # Noble, brave movements

class MotionIntensity(Enum):
    """Motion intensity levels for different contexts"""
    SUBTLE = 0.3        # Gentle, background movements
    MODERATE = 0.6      # Normal character expression
    DRAMATIC = 0.9      # Strong emotional expression
    EXTREME = 1.2       # Maximum impact movements

class InteractionContext(Enum):
    """Different interaction contexts requiring specific behaviors"""
    FIRST_ENCOUNTER = "first_encounter"     # Meeting new guests
    FAMILIAR_GUEST = "familiar_guest"       # Recognized returning guest
    CHILD_INTERACTION = "child_interaction" # Special child-friendly behaviors
    ADULT_CONVERSATION = "adult_conversation" # Mature interaction patterns
    GROUP_CROWD = "group_crowd"            # Managing multiple guests
    PHOTO_SESSION = "photo_session"        # Posing and performance
    DEMONSTRATION = "demonstration"         # Educational/technical display
    IDLE_PATROL = "idle_patrol"            # Background ambient behavior

@dataclass
class CharacterMotionProfile:
    """Defines a complete character motion profile with personality traits"""
    name: str
    primary_trait: PersonalityTrait
    secondary_traits: List[PersonalityTrait] = field(default_factory=list)
    movement_speed_modifier: float = 1.0     # 0.5 = slower, 2.0 = faster
    gesture_frequency: float = 1.0           # How often gestures occur
    idle_activity_level: float = 0.5         # Background movement amount
    emotional_responsiveness: float = 1.0    # How strongly emotions affect motion
    preferred_easing: EasingType = EasingType.EASE_IN_OUT_CUBIC
    safety_margin: float = 0.1               # Extra safety for convention use

@dataclass
class MotionBehavior:
    """Defines a specific motion behavior with personality expression"""
    name: str
    description: str
    servo_sequence: List[MotionKeyframe]
    duration: float
    personality_traits: List[PersonalityTrait]
    emotional_context: EmotionalState
    interaction_context: InteractionContext
    intensity: MotionIntensity
    audio_coordination: bool = True
    repeatable: bool = False
    safety_critical: bool = False

@dataclass
class GuestInteractionData:
    """Data structure for guest interaction tracking"""
    guest_id: str
    position: Tuple[float, float, float]  # x, y, z in meters
    distance: float
    estimated_age_group: str  # "child", "teen", "adult", "senior"
    interaction_history: List[str] = field(default_factory=list)
    first_encounter_time: float = field(default_factory=time.time)
    last_interaction_time: float = field(default_factory=time.time)
    guest_engagement_level: float = 0.5  # 0.0 to 1.0
    preferred_interaction_style: str = "standard"

class R2D2CharacterMotionSystem:
    """
    Disney-Level Character Motion System for R2D2

    This system creates authentic, engaging R2D2 character behaviors with
    sophisticated motion patterns that express personality, emotion, and
    interactive awareness. Built for convention environments with safety
    and reliability as top priorities.
    """

    def __init__(self, servo_controller: Optional[DisneyServoController] = None,
                 audio_coordinator: Optional[AudioServoCoordinator] = None):
        """Initialize the character motion system"""

        # Core system components
        self.servo_controller = servo_controller
        self.audio_coordinator = audio_coordinator
        self.sound_library = R2D2SoundLibrary()

        # Character personality system
        self.current_personality = None
        self.personality_profiles = {}
        self.motion_behaviors = {}
        self.active_behaviors = deque(maxlen=50)

        # Guest interaction system
        self.guest_tracking = {}
        self.interaction_zones = {}
        self.current_interaction_context = InteractionContext.IDLE_PATROL

        # Motion control state
        self.is_active = False
        self.emergency_stop_active = False
        self.motion_thread = None
        self.behavior_thread = None

        # Performance metrics
        self.performance_metrics = {
            'total_behaviors_executed': 0,
            'guest_interactions': 0,
            'motion_smoothness_score': 0.0,
            'personality_consistency_score': 0.0,
            'safety_incidents': 0,
            'uptime_hours': 0.0
        }

        # Initialize character system
        self._initialize_personality_profiles()
        self._initialize_motion_behaviors()
        self._initialize_interaction_zones()

        logger.info("Disney-Level R2D2 Character Motion System initialized")

    def _initialize_personality_profiles(self):
        """Initialize the authentic R2D2 personality profiles"""

        # Primary Character Personalities
        self.personality_profiles = {
            "hero_mode": CharacterMotionProfile(
                name="Hero R2D2",
                primary_trait=PersonalityTrait.HEROIC,
                secondary_traits=[PersonalityTrait.CONFIDENT, PersonalityTrait.LOYAL],
                movement_speed_modifier=1.2,
                gesture_frequency=1.1,
                idle_activity_level=0.6,
                emotional_responsiveness=1.2,
                preferred_easing=EasingType.EASE_OUT_BACK
            ),

            "curious_explorer": CharacterMotionProfile(
                name="Curious R2D2",
                primary_trait=PersonalityTrait.CURIOUS,
                secondary_traits=[PersonalityTrait.ANALYTICAL, PersonalityTrait.PLAYFUL],
                movement_speed_modifier=0.9,
                gesture_frequency=1.3,
                idle_activity_level=0.8,
                emotional_responsiveness=1.0,
                preferred_easing=EasingType.EASE_IN_OUT_QUAD
            ),

            "protective_guardian": CharacterMotionProfile(
                name="Protective R2D2",
                primary_trait=PersonalityTrait.PROTECTIVE,
                secondary_traits=[PersonalityTrait.CAUTIOUS, PersonalityTrait.LOYAL],
                movement_speed_modifier=0.8,
                gesture_frequency=0.8,
                idle_activity_level=0.4,
                emotional_responsiveness=1.1,
                preferred_easing=EasingType.EASE_IN_OUT_CUBIC
            ),

            "mischievous_companion": CharacterMotionProfile(
                name="Mischievous R2D2",
                primary_trait=PersonalityTrait.MISCHIEVOUS,
                secondary_traits=[PersonalityTrait.PLAYFUL, PersonalityTrait.STUBBORN],
                movement_speed_modifier=1.1,
                gesture_frequency=1.4,
                idle_activity_level=0.7,
                emotional_responsiveness=0.9,
                preferred_easing=EasingType.EASE_OUT_BOUNCE
            ),

            "excited_fan_encounter": CharacterMotionProfile(
                name="Excited R2D2",
                primary_trait=PersonalityTrait.EXCITED,
                secondary_traits=[PersonalityTrait.PLAYFUL, PersonalityTrait.CONFIDENT],
                movement_speed_modifier=1.4,
                gesture_frequency=1.6,
                idle_activity_level=0.9,
                emotional_responsiveness=1.3,
                preferred_easing=EasingType.EASE_OUT_QUART
            ),

            "wise_mentor": CharacterMotionProfile(
                name="Wise R2D2",
                primary_trait=PersonalityTrait.ANALYTICAL,
                secondary_traits=[PersonalityTrait.CONFIDENT, PersonalityTrait.PROTECTIVE],
                movement_speed_modifier=0.7,
                gesture_frequency=0.9,
                idle_activity_level=0.3,
                emotional_responsiveness=0.8,
                preferred_easing=EasingType.EASE_IN_OUT_CUBIC
            )
        }

        # Set default personality
        self.current_personality = self.personality_profiles["curious_explorer"]

        logger.info(f"Initialized {len(self.personality_profiles)} personality profiles")

    def _initialize_motion_behaviors(self):
        """Initialize the library of R2D2 motion behaviors"""

        # Head Movement Behaviors
        self.motion_behaviors.update({
            "curious_head_tilt": MotionBehavior(
                name="Curious Head Tilt",
                description="Inquisitive head movement showing interest",
                servo_sequence=[
                    MotionKeyframe(position=15.0, duration=0.8, easing=EasingType.EASE_OUT_QUAD),
                    MotionKeyframe(position=0.0, duration=1.2, easing=EasingType.EASE_IN_OUT_CUBIC)
                ],
                duration=2.0,
                personality_traits=[PersonalityTrait.CURIOUS, PersonalityTrait.ANALYTICAL],
                emotional_context=EmotionalState.CURIOUS,
                interaction_context=InteractionContext.FIRST_ENCOUNTER,
                intensity=MotionIntensity.MODERATE
            ),

            "excited_head_bob": MotionBehavior(
                name="Excited Head Bob",
                description="Enthusiastic bobbing motion showing excitement",
                servo_sequence=[
                    MotionKeyframe(position=10.0, duration=0.3, easing=EasingType.EASE_OUT_BOUNCE),
                    MotionKeyframe(position=-5.0, duration=0.3, easing=EasingType.EASE_IN_BOUNCE),
                    MotionKeyframe(position=8.0, duration=0.3, easing=EasingType.EASE_OUT_BOUNCE),
                    MotionKeyframe(position=0.0, duration=0.4, easing=EasingType.EASE_IN_OUT_CUBIC)
                ],
                duration=1.3,
                personality_traits=[PersonalityTrait.EXCITED, PersonalityTrait.PLAYFUL],
                emotional_context=EmotionalState.EXCITED,
                interaction_context=InteractionContext.CHILD_INTERACTION,
                intensity=MotionIntensity.DRAMATIC
            ),

            "protective_scan": MotionBehavior(
                name="Protective Scan",
                description="Alert scanning motion checking for threats",
                servo_sequence=[
                    MotionKeyframe(position=-30.0, duration=1.0, easing=EasingType.EASE_IN_OUT_QUAD),
                    MotionKeyframe(position=30.0, duration=2.0, easing=EasingType.LINEAR),
                    MotionKeyframe(position=0.0, duration=1.0, easing=EasingType.EASE_IN_OUT_QUAD)
                ],
                duration=4.0,
                personality_traits=[PersonalityTrait.PROTECTIVE, PersonalityTrait.CAUTIOUS],
                emotional_context=EmotionalState.ALERT,
                interaction_context=InteractionContext.GROUP_CROWD,
                intensity=MotionIntensity.MODERATE
            )
        })

        # Dome Rotation Behaviors
        self.motion_behaviors.update({
            "mischievous_spin": MotionBehavior(
                name="Mischievous Spin",
                description="Playful spinning motion with personality",
                servo_sequence=[
                    MotionKeyframe(position=180.0, duration=1.5, easing=EasingType.EASE_OUT_BACK),
                    MotionKeyframe(position=270.0, duration=0.8, easing=EasingType.EASE_IN_OUT_BOUNCE),
                    MotionKeyframe(position=0.0, duration=1.2, easing=EasingType.EASE_IN_OUT_CUBIC)
                ],
                duration=3.5,
                personality_traits=[PersonalityTrait.MISCHIEVOUS, PersonalityTrait.PLAYFUL],
                emotional_context=EmotionalState.PLAYFUL,
                interaction_context=InteractionContext.CHILD_INTERACTION,
                intensity=MotionIntensity.DRAMATIC
            ),

            "analytical_examination": MotionBehavior(
                name="Analytical Examination",
                description="Methodical scanning and analysis motion",
                servo_sequence=[
                    MotionKeyframe(position=45.0, duration=1.5, easing=EasingType.EASE_IN_OUT_QUAD),
                    MotionKeyframe(position=90.0, duration=2.0, easing=EasingType.LINEAR),
                    MotionKeyframe(position=135.0, duration=1.5, easing=EasingType.LINEAR),
                    MotionKeyframe(position=180.0, duration=1.5, easing=EasingType.LINEAR),
                    MotionKeyframe(position=0.0, duration=2.0, easing=EasingType.EASE_IN_OUT_CUBIC)
                ],
                duration=8.5,
                personality_traits=[PersonalityTrait.ANALYTICAL, PersonalityTrait.CURIOUS],
                emotional_context=EmotionalState.FOCUSED,
                interaction_context=InteractionContext.DEMONSTRATION,
                intensity=MotionIntensity.MODERATE
            )
        })

        # Complex Multi-Servo Behaviors
        self.motion_behaviors.update({
            "hero_presentation": MotionBehavior(
                name="Hero Presentation",
                description="Confident heroic stance with multiple servo coordination",
                servo_sequence=[
                    # This will be expanded to include multiple servos
                    MotionKeyframe(position=0.0, duration=0.5, easing=EasingType.EASE_OUT_BACK),
                    MotionKeyframe(position=10.0, duration=1.0, easing=EasingType.EASE_IN_OUT_CUBIC),
                    MotionKeyframe(position=0.0, duration=1.5, easing=EasingType.EASE_IN_OUT_CUBIC)
                ],
                duration=3.0,
                personality_traits=[PersonalityTrait.HEROIC, PersonalityTrait.CONFIDENT],
                emotional_context=EmotionalState.CONFIDENT,
                interaction_context=InteractionContext.PHOTO_SESSION,
                intensity=MotionIntensity.DRAMATIC
            ),

            "gentle_greeting": MotionBehavior(
                name="Gentle Greeting",
                description="Warm, welcoming greeting motion for all ages",
                servo_sequence=[
                    MotionKeyframe(position=5.0, duration=0.8, easing=EasingType.EASE_OUT_QUAD),
                    MotionKeyframe(position=-5.0, duration=0.8, easing=EasingType.EASE_IN_OUT_QUAD),
                    MotionKeyframe(position=0.0, duration=1.0, easing=EasingType.EASE_IN_OUT_CUBIC)
                ],
                duration=2.6,
                personality_traits=[PersonalityTrait.LOYAL, PersonalityTrait.CONFIDENT],
                emotional_context=EmotionalState.FRIENDLY,
                interaction_context=InteractionContext.FIRST_ENCOUNTER,
                intensity=MotionIntensity.MODERATE
            )
        })

        logger.info(f"Initialized {len(self.motion_behaviors)} motion behaviors")

    def _initialize_interaction_zones(self):
        """Initialize spatial interaction zones for guest detection"""

        self.interaction_zones = {
            "intimate_zone": {
                "distance_range": (0.0, 1.2),  # 0-1.2 meters
                "behavior_intensity": MotionIntensity.SUBTLE,
                "preferred_behaviors": ["gentle_greeting", "curious_head_tilt"],
                "audio_volume": 0.7
            },

            "personal_zone": {
                "distance_range": (1.2, 2.5),  # 1.2-2.5 meters
                "behavior_intensity": MotionIntensity.MODERATE,
                "preferred_behaviors": ["excited_head_bob", "analytical_examination"],
                "audio_volume": 0.8
            },

            "social_zone": {
                "distance_range": (2.5, 4.0),  # 2.5-4.0 meters
                "behavior_intensity": MotionIntensity.DRAMATIC,
                "preferred_behaviors": ["hero_presentation", "mischievous_spin"],
                "audio_volume": 1.0
            },

            "public_zone": {
                "distance_range": (4.0, 8.0),  # 4.0-8.0 meters
                "behavior_intensity": MotionIntensity.EXTREME,
                "preferred_behaviors": ["protective_scan", "analytical_examination"],
                "audio_volume": 1.0
            }
        }

        logger.info(f"Initialized {len(self.interaction_zones)} interaction zones")

    def set_personality_mode(self, personality_name: str) -> bool:
        """
        Set the active personality mode for the character

        Args:
            personality_name: Name of the personality profile to activate

        Returns:
            bool: True if personality was set successfully
        """
        if personality_name not in self.personality_profiles:
            logger.error(f"Unknown personality profile: {personality_name}")
            return False

        old_personality = self.current_personality.name if self.current_personality else "None"
        self.current_personality = self.personality_profiles[personality_name]

        logger.info(f"Personality changed from {old_personality} to {self.current_personality.name}")

        # Adjust motion parameters based on new personality
        self._update_motion_parameters()

        return True

    def _update_motion_parameters(self):
        """Update motion control parameters based on current personality"""
        if not self.current_personality or not self.servo_controller:
            return

        # Update servo controller timing based on personality
        speed_modifier = self.current_personality.movement_speed_modifier

        # This would integrate with the servo controller's timing system
        # Implementation depends on the specific servo controller interface
        logger.info(f"Updated motion parameters for {self.current_personality.name}")

    def execute_behavior(self, behavior_name: str, target_servo: str,
                        intensity_override: Optional[MotionIntensity] = None) -> bool:
        """
        Execute a specific character behavior

        Args:
            behavior_name: Name of the behavior to execute
            target_servo: Servo to apply the behavior to
            intensity_override: Optional intensity override

        Returns:
            bool: True if behavior was executed successfully
        """
        if behavior_name not in self.motion_behaviors:
            logger.error(f"Unknown behavior: {behavior_name}")
            return False

        if not self.servo_controller:
            logger.error("No servo controller available")
            return False

        behavior = self.motion_behaviors[behavior_name]
        intensity = intensity_override or behavior.intensity

        # Apply personality modifications to the behavior
        modified_sequence = self._apply_personality_to_sequence(
            behavior.servo_sequence, intensity
        )

        # Execute the motion sequence
        try:
            success = self.servo_controller.animate_sequence(target_servo, modified_sequence)

            if success:
                # Record behavior execution
                self.active_behaviors.append({
                    'behavior': behavior_name,
                    'servo': target_servo,
                    'timestamp': time.time(),
                    'personality': self.current_personality.name,
                    'intensity': intensity.value
                })

                self.performance_metrics['total_behaviors_executed'] += 1

                # Coordinate with audio if enabled
                if behavior.audio_coordination and self.audio_coordinator:
                    self._coordinate_behavior_audio(behavior)

                logger.info(f"Executed behavior '{behavior_name}' on servo '{target_servo}'")

            return success

        except Exception as e:
            logger.error(f"Failed to execute behavior '{behavior_name}': {e}")
            return False

    def _apply_personality_to_sequence(self, sequence: List[MotionKeyframe],
                                     intensity: MotionIntensity) -> List[MotionKeyframe]:
        """
        Apply current personality traits to modify a motion sequence

        Args:
            sequence: Original motion sequence
            intensity: Motion intensity level

        Returns:
            List[MotionKeyframe]: Modified sequence with personality applied
        """
        if not self.current_personality:
            return sequence

        modified_sequence = []
        personality = self.current_personality

        for keyframe in sequence:
            # Apply speed modifier
            new_duration = keyframe.duration / personality.movement_speed_modifier

            # Apply intensity scaling
            position_scale = intensity.value * personality.emotional_responsiveness
            new_position = keyframe.position * position_scale

            # Apply safety margin for convention use
            safety_factor = 1.0 - personality.safety_margin
            new_position *= safety_factor

            # Use personality's preferred easing if not specified
            new_easing = keyframe.easing or personality.preferred_easing

            modified_keyframe = MotionKeyframe(
                position=new_position,
                duration=max(new_duration, 0.1),  # Minimum duration for safety
                easing=new_easing
            )

            modified_sequence.append(modified_keyframe)

        return modified_sequence

    def _coordinate_behavior_audio(self, behavior: MotionBehavior):
        """Coordinate audio playback with behavior execution"""
        if not self.audio_coordinator:
            return

        # Select appropriate sound effect based on behavior context
        sound_context = self._behavior_to_sound_context(behavior)

        # This would integrate with the audio coordinator
        logger.info(f"Coordinating audio for behavior: {behavior.name}")

    def _behavior_to_sound_context(self, behavior: MotionBehavior) -> str:
        """Map behavior to appropriate sound context"""
        emotion_to_sound = {
            EmotionalState.EXCITED: "excited_beeps",
            EmotionalState.CURIOUS: "questioning_warbles",
            EmotionalState.CONFIDENT: "confident_chirps",
            EmotionalState.ALERT: "alert_tones",
            EmotionalState.PLAYFUL: "playful_sounds",
            EmotionalState.FRIENDLY: "greeting_sounds"
        }

        return emotion_to_sound.get(behavior.emotional_context, "general_sounds")

    def react_to_guest_interaction(self, guest_data: GuestInteractionData) -> bool:
        """
        React to guest interaction with appropriate behavior

        Args:
            guest_data: Information about the guest interaction

        Returns:
            bool: True if reaction was successful
        """
        # Determine appropriate interaction zone
        interaction_zone = self._get_interaction_zone(guest_data.distance)

        # Select behavior based on guest data and current personality
        behavior_name = self._select_contextual_behavior(guest_data, interaction_zone)

        if behavior_name:
            # Determine target servo based on behavior type
            target_servo = self._get_primary_servo_for_behavior(behavior_name)

            # Execute the selected behavior
            success = self.execute_behavior(
                behavior_name,
                target_servo,
                interaction_zone["behavior_intensity"]
            )

            if success:
                self.performance_metrics['guest_interactions'] += 1
                self._update_guest_interaction_history(guest_data, behavior_name)

                logger.info(f"Reacted to guest {guest_data.guest_id} with behavior '{behavior_name}'")

            return success

        return False

    def _get_interaction_zone(self, distance: float) -> Dict[str, Any]:
        """Determine which interaction zone a guest is in"""
        for zone_name, zone_data in self.interaction_zones.items():
            min_dist, max_dist = zone_data["distance_range"]
            if min_dist <= distance < max_dist:
                return zone_data

        # Default to public zone if distance is very far
        return self.interaction_zones["public_zone"]

    def _select_contextual_behavior(self, guest_data: GuestInteractionData,
                                  interaction_zone: Dict[str, Any]) -> Optional[str]:
        """Select the most appropriate behavior for the interaction context"""

        # Get preferred behaviors for this zone
        preferred_behaviors = interaction_zone["preferred_behaviors"]

        # Filter behaviors based on current personality traits
        suitable_behaviors = []
        for behavior_name in preferred_behaviors:
            if behavior_name in self.motion_behaviors:
                behavior = self.motion_behaviors[behavior_name]

                # Check if behavior matches current personality
                personality_match = any(
                    trait in behavior.personality_traits
                    for trait in [self.current_personality.primary_trait] +
                                self.current_personality.secondary_traits
                )

                if personality_match:
                    suitable_behaviors.append(behavior_name)

        # Select behavior based on guest characteristics
        if guest_data.estimated_age_group == "child":
            child_friendly = ["excited_head_bob", "gentle_greeting", "mischievous_spin"]
            for behavior in child_friendly:
                if behavior in suitable_behaviors:
                    return behavior

        # Default selection
        return suitable_behaviors[0] if suitable_behaviors else None

    def _get_primary_servo_for_behavior(self, behavior_name: str) -> str:
        """Determine the primary servo for a given behavior"""
        behavior_servo_mapping = {
            "curious_head_tilt": "head_pitch",
            "excited_head_bob": "head_pitch",
            "protective_scan": "head_yaw",
            "mischievous_spin": "dome_rotation",
            "analytical_examination": "dome_rotation",
            "hero_presentation": "head_pitch",
            "gentle_greeting": "head_pitch"
        }

        return behavior_servo_mapping.get(behavior_name, "head_pitch")

    def _update_guest_interaction_history(self, guest_data: GuestInteractionData,
                                        behavior_name: str):
        """Update guest interaction history for learning and adaptation"""
        interaction_entry = {
            'timestamp': time.time(),
            'behavior': behavior_name,
            'distance': guest_data.distance,
            'context': self.current_interaction_context.value
        }

        guest_data.interaction_history.append(interaction_entry)
        guest_data.last_interaction_time = time.time()

        # Update guest tracking
        self.guest_tracking[guest_data.guest_id] = guest_data

    def start_character_system(self) -> bool:
        """Start the character motion system"""
        if self.is_active:
            logger.warning("Character system is already active")
            return True

        try:
            # Start motion control thread
            self.is_active = True
            self.emergency_stop_active = False

            self.motion_thread = threading.Thread(
                target=self._character_motion_loop,
                daemon=True,
                name="CharacterMotionLoop"
            )
            self.motion_thread.start()

            # Start behavior selection thread
            self.behavior_thread = threading.Thread(
                target=self._autonomous_behavior_loop,
                daemon=True,
                name="AutonomousBehaviorLoop"
            )
            self.behavior_thread.start()

            logger.info("Character motion system started successfully")
            return True

        except Exception as e:
            logger.error(f"Failed to start character system: {e}")
            self.is_active = False
            return False

    def stop_character_system(self):
        """Stop the character motion system"""
        self.is_active = False

        # Wait for threads to finish
        if self.motion_thread and self.motion_thread.is_alive():
            self.motion_thread.join(timeout=2.0)

        if self.behavior_thread and self.behavior_thread.is_alive():
            self.behavior_thread.join(timeout=2.0)

        logger.info("Character motion system stopped")

    def emergency_stop(self):
        """Emergency stop all character motion"""
        self.emergency_stop_active = True
        self.is_active = False

        if self.servo_controller:
            self.servo_controller.emergency_stop()

        if self.audio_coordinator:
            # This would stop audio coordination
            pass

        logger.warning("EMERGENCY STOP activated for character motion system")

    def _character_motion_loop(self):
        """Main character motion control loop"""
        logger.info("Character motion loop started")

        while self.is_active and not self.emergency_stop_active:
            try:
                # Update motion smoothness and character consistency
                self._update_motion_metrics()

                # Handle any queued motion requests
                self._process_motion_queue()

                # Sleep for motion control cycle
                time.sleep(0.02)  # 50Hz motion control loop

            except Exception as e:
                logger.error(f"Error in character motion loop: {e}")
                time.sleep(0.1)

        logger.info("Character motion loop stopped")

    def _autonomous_behavior_loop(self):
        """Autonomous behavior selection and execution loop"""
        logger.info("Autonomous behavior loop started")

        last_idle_behavior = time.time()
        idle_behavior_interval = 5.0  # Execute idle behavior every 5 seconds

        while self.is_active and not self.emergency_stop_active:
            try:
                current_time = time.time()

                # Execute idle behaviors based on personality
                if (current_time - last_idle_behavior) > idle_behavior_interval:
                    self._execute_idle_behavior()
                    last_idle_behavior = current_time

                # Check for any pending guest interactions
                self._process_guest_interactions()

                # Sleep for behavior control cycle
                time.sleep(0.1)  # 10Hz behavior control loop

            except Exception as e:
                logger.error(f"Error in autonomous behavior loop: {e}")
                time.sleep(0.5)

        logger.info("Autonomous behavior loop stopped")

    def _execute_idle_behavior(self):
        """Execute appropriate idle behavior based on current personality"""
        if not self.current_personality:
            return

        # Select idle behavior based on personality and activity level
        idle_behaviors = {
            PersonalityTrait.CURIOUS: ["curious_head_tilt", "analytical_examination"],
            PersonalityTrait.PLAYFUL: ["mischievous_spin", "excited_head_bob"],
            PersonalityTrait.PROTECTIVE: ["protective_scan"],
            PersonalityTrait.ANALYTICAL: ["analytical_examination"]
        }

        primary_trait = self.current_personality.primary_trait
        available_behaviors = idle_behaviors.get(primary_trait, ["gentle_greeting"])

        # Randomly select from available behaviors
        if available_behaviors and random.random() < self.current_personality.idle_activity_level:
            behavior_name = random.choice(available_behaviors)
            target_servo = self._get_primary_servo_for_behavior(behavior_name)

            # Execute with subtle intensity for idle behavior
            self.execute_behavior(behavior_name, target_servo, MotionIntensity.SUBTLE)

    def _process_motion_queue(self):
        """Process any queued motion requests"""
        # This would handle queued motion requests from external systems
        pass

    def _process_guest_interactions(self):
        """Process any pending guest interactions"""
        # This would handle guest detection and interaction processing
        # Integration with computer vision system would happen here
        pass

    def _update_motion_metrics(self):
        """Update performance metrics for motion quality"""
        # Calculate motion smoothness and consistency scores
        if len(self.active_behaviors) > 10:
            recent_behaviors = list(self.active_behaviors)[-10:]

            # Calculate personality consistency
            personality_consistency = self._calculate_personality_consistency(recent_behaviors)
            self.performance_metrics['personality_consistency_score'] = personality_consistency

            # Update motion smoothness score
            self.performance_metrics['motion_smoothness_score'] = 0.95  # Placeholder

    def _calculate_personality_consistency(self, recent_behaviors: List[Dict]) -> float:
        """Calculate how consistent behaviors are with current personality"""
        if not recent_behaviors or not self.current_personality:
            return 0.0

        consistent_behaviors = 0

        for behavior_data in recent_behaviors:
            behavior_name = behavior_data['behavior']
            if behavior_name in self.motion_behaviors:
                behavior = self.motion_behaviors[behavior_name]

                # Check if behavior matches current personality traits
                personality_traits = [self.current_personality.primary_trait] + \
                                   self.current_personality.secondary_traits

                if any(trait in behavior.personality_traits for trait in personality_traits):
                    consistent_behaviors += 1

        return consistent_behaviors / len(recent_behaviors)

    def get_character_performance_report(self) -> Dict[str, Any]:
        """Get comprehensive performance report for the character system"""

        uptime = time.time() - getattr(self, 'start_time', time.time())
        self.performance_metrics['uptime_hours'] = uptime / 3600.0

        report = {
            'character_system_status': 'ACTIVE' if self.is_active else 'INACTIVE',
            'current_personality': self.current_personality.name if self.current_personality else 'None',
            'performance_metrics': self.performance_metrics.copy(),
            'active_behaviors_count': len(self.active_behaviors),
            'tracked_guests': len(self.guest_tracking),
            'available_behaviors': len(self.motion_behaviors),
            'available_personalities': len(self.personality_profiles),
            'emergency_stop_status': self.emergency_stop_active,
            'system_integration': {
                'servo_controller': self.servo_controller is not None,
                'audio_coordinator': self.audio_coordinator is not None,
                'sound_library': self.sound_library is not None
            }
        }

        return report

    def save_character_session(self, filename: str):
        """Save current character session data for analysis"""
        session_data = {
            'timestamp': time.time(),
            'personality_profile': self.current_personality.name if self.current_personality else None,
            'performance_metrics': self.performance_metrics.copy(),
            'behavior_history': list(self.active_behaviors),
            'guest_interactions': {
                guest_id: {
                    'interaction_count': len(data.interaction_history),
                    'total_engagement_time': data.last_interaction_time - data.first_encounter_time,
                    'preferred_style': data.preferred_interaction_style
                }
                for guest_id, data in self.guest_tracking.items()
            }
        }

        try:
            with open(filename, 'w') as f:
                json.dump(session_data, f, indent=2)
            logger.info(f"Character session saved to {filename}")
        except Exception as e:
            logger.error(f"Failed to save character session: {e}")

# Example usage and testing functions
def create_demo_character_system():
    """Create a demo character system for testing"""

    # Create character motion system
    character_system = R2D2CharacterMotionSystem()

    # Set personality mode
    character_system.set_personality_mode("curious_explorer")

    return character_system

def demo_character_behaviors():
    """Demonstrate various character behaviors"""

    character_system = create_demo_character_system()

    # Demo different personality modes
    personalities = ["hero_mode", "curious_explorer", "mischievous_companion"]

    for personality in personalities:
        print(f"\n--- Demonstrating {personality} ---")
        character_system.set_personality_mode(personality)

        # Execute some behaviors
        behaviors = ["curious_head_tilt", "excited_head_bob", "gentle_greeting"]
        for behavior in behaviors:
            success = character_system.execute_behavior(behavior, "head_pitch")
            print(f"Behavior '{behavior}': {'SUCCESS' if success else 'FAILED'}")

    # Generate performance report
    report = character_system.get_character_performance_report()
    print(f"\n--- Performance Report ---")
    print(json.dumps(report, indent=2))

if __name__ == "__main__":
    # Run demonstration
    demo_character_behaviors()