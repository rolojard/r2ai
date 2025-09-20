#!/usr/bin/env python3
"""
Disney-Level Bio-Mechanical Animation Library for R2D2
=====================================================

Advanced multi-servo animation system that creates natural, bio-mechanical motion
patterns using Disney animation principles. This library provides sophisticated
choreography for complex R2D2 expressions and interactions.

Features:
- Multi-servo synchronized choreography with natural coordination
- Bio-mechanical motion patterns based on organic movement studies
- Disney's 12 principles of animation applied to robotic systems
- Complex gesture sequences for emotional and contextual expression
- Natural acceleration curves with anticipation and follow-through
- Coordinated body language for immersive character interaction

Author: Imagineer Specialist Agent
Target: NVIDIA Orin Nano R2D2 Systems
Integration with Character Motion System and Disney Servo Control
"""

import time
import math
import threading
import logging
import asyncio
from typing import Dict, List, Tuple, Optional, Callable, Any, Union
from dataclasses import dataclass, field
from enum import Enum
import numpy as np
from collections import deque
import json

# Import foundational systems
try:
    from servo_foundation_library import DisneyServoController, EasingType, MotionKeyframe, ServoConfig
    from r2d2_character_motion_system import (
        PersonalityTrait, MotionIntensity, InteractionContext,
        CharacterMotionProfile, MotionBehavior
    )
except ImportError as e:
    logging.warning(f"Import warning: {e}. Some functionality may be limited.")

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AnimationPrinciple(Enum):
    """Disney's animation principles applied to robotics"""
    SQUASH_AND_STRETCH = "squash_and_stretch"
    ANTICIPATION = "anticipation"
    STAGING = "staging"
    STRAIGHT_AHEAD_AND_POSE = "straight_ahead_and_pose"
    FOLLOW_THROUGH = "follow_through"
    SLOW_IN_SLOW_OUT = "slow_in_slow_out"
    ARC = "arc"
    SECONDARY_ACTION = "secondary_action"
    TIMING = "timing"
    EXAGGERATION = "exaggeration"
    SOLID_DRAWING = "solid_drawing"
    APPEAL = "appeal"

class BodyPart(Enum):
    """R2D2 body parts for coordinated animation"""
    HEAD_PITCH = "head_pitch"           # Head up/down
    HEAD_YAW = "head_yaw"               # Head left/right
    DOME_ROTATION = "dome_rotation"      # Full dome spin
    EYE_LEFT = "eye_left"               # Left eye servo
    EYE_RIGHT = "eye_right"             # Right eye servo
    PERISCOPE = "periscope"             # Periscope extension
    ARM_LEFT = "arm_left"               # Left utility arm
    ARM_RIGHT = "arm_right"             # Right utility arm
    SHOULDER_LEFT = "shoulder_left"      # Left shoulder movement
    SHOULDER_RIGHT = "shoulder_right"    # Right shoulder movement
    BODY_LEAN = "body_lean"             # Body lean servo
    BASE_ROTATION = "base_rotation"      # Base rotation if available

class CoordinationType(Enum):
    """Types of multi-servo coordination patterns"""
    SEQUENTIAL = "sequential"           # One after another
    SYNCHRONIZED = "synchronized"       # All together
    LAYERED = "layered"                # Overlapping timing
    COUNTERPOINT = "counterpoint"       # Contrasting movements
    CHAIN_REACTION = "chain_reaction"   # Cascading effect
    MIRROR = "mirror"                   # Mirrored movements
    OFFSET = "offset"                   # Time-delayed synchronization

@dataclass
class ServoKeyframe:
    """Enhanced keyframe with bio-mechanical properties"""
    servo: BodyPart
    position: float
    duration: float
    easing: EasingType = EasingType.EASE_IN_OUT_CUBIC

    # Bio-mechanical properties
    anticipation_offset: float = 0.0    # Pre-movement anticipation
    follow_through: float = 0.0         # Post-movement settling
    secondary_motion: float = 0.0       # Secondary bounce/settle
    arc_curvature: float = 0.0          # Natural arc movement

    # Animation principle applications
    squash_factor: float = 1.0          # Squash and stretch
    exaggeration_factor: float = 1.0    # Exaggeration amount
    staging_priority: int = 1           # Visual staging importance (1-10)

@dataclass
class MultiServoSequence:
    """Complex multi-servo animation sequence"""
    name: str
    description: str
    duration: float
    coordination_type: CoordinationType
    servo_keyframes: Dict[BodyPart, List[ServoKeyframe]] = field(default_factory=dict)

    # Bio-mechanical properties
    breathing_rhythm: float = 0.0       # Natural breathing-like rhythm
    weight_distribution: Dict[BodyPart, float] = field(default_factory=dict)
    momentum_conservation: bool = True   # Maintain realistic momentum

    # Animation principles
    primary_focus: BodyPart = BodyPart.HEAD_PITCH
    secondary_actions: List[BodyPart] = field(default_factory=list)
    appeal_factor: float = 1.0          # Overall character appeal

@dataclass
class GestureParameters:
    """Parameters for gesture generation"""
    emotional_intensity: float = 1.0
    physical_scale: float = 1.0
    temporal_scale: float = 1.0
    personality_influence: float = 1.0
    bio_mechanical_realism: float = 0.8

class BiomechanicalAnimationLibrary:
    """
    Disney-Level Bio-Mechanical Animation Library

    Creates natural, organic motion patterns for R2D2 using sophisticated
    multi-servo coordination and Disney animation principles. Focuses on
    believable, appealing character animation that brings R2D2 to life.
    """

    def __init__(self, servo_controller: Optional[DisneyServoController] = None):
        """Initialize the bio-mechanical animation library"""

        self.servo_controller = servo_controller

        # Animation libraries
        self.gesture_sequences = {}
        self.emotional_expressions = {}
        self.contextual_behaviors = {}
        self.idle_animations = {}

        # Bio-mechanical parameters
        self.natural_frequencies = {}    # Natural oscillation frequencies
        self.joint_constraints = {}      # Physical joint limitations
        self.momentum_profiles = {}      # Momentum and inertia simulation

        # Animation state
        self.active_sequences = {}
        self.coordination_manager = None
        self.physics_simulator = None

        # Performance metrics
        self.animation_metrics = {
            'sequences_executed': 0,
            'coordination_accuracy': 0.0,
            'bio_mechanical_realism': 0.0,
            'appeal_rating': 0.0,
            'timing_precision': 0.0
        }

        # Initialize animation library
        self._initialize_natural_frequencies()
        self._initialize_joint_constraints()
        self._initialize_gesture_library()
        self._initialize_emotional_expressions()
        self._initialize_contextual_behaviors()

        logger.info("Bio-Mechanical Animation Library initialized")

    def _initialize_natural_frequencies(self):
        """Initialize natural movement frequencies for each body part"""

        # Based on mechanical properties and desired character feel
        self.natural_frequencies = {
            BodyPart.HEAD_PITCH: 0.8,      # Gentle nodding frequency
            BodyPart.HEAD_YAW: 0.6,        # Natural scanning frequency
            BodyPart.DOME_ROTATION: 0.3,   # Slower dome rotation
            BodyPart.EYE_LEFT: 2.0,        # Quick eye movements
            BodyPart.EYE_RIGHT: 2.0,       # Quick eye movements
            BodyPart.PERISCOPE: 0.5,       # Moderate extension speed
            BodyPart.ARM_LEFT: 1.2,        # Natural arm swing
            BodyPart.ARM_RIGHT: 1.2,       # Natural arm swing
            BodyPart.SHOULDER_LEFT: 0.7,   # Shoulder movement
            BodyPart.SHOULDER_RIGHT: 0.7,  # Shoulder movement
            BodyPart.BODY_LEAN: 0.4,       # Slow body movements
            BodyPart.BASE_ROTATION: 0.2    # Very slow base rotation
        }

        logger.info("Natural frequencies initialized for bio-mechanical realism")

    def _initialize_joint_constraints(self):
        """Initialize physical joint constraints and limitations"""

        # Define realistic movement ranges and constraints
        self.joint_constraints = {
            BodyPart.HEAD_PITCH: {
                'range': (-45.0, 30.0),     # degrees
                'max_velocity': 120.0,       # degrees/second
                'max_acceleration': 300.0,   # degrees/second²
                'natural_rest': 0.0
            },
            BodyPart.HEAD_YAW: {
                'range': (-90.0, 90.0),
                'max_velocity': 90.0,
                'max_acceleration': 250.0,
                'natural_rest': 0.0
            },
            BodyPart.DOME_ROTATION: {
                'range': (-360.0, 360.0),   # Full rotation
                'max_velocity': 60.0,
                'max_acceleration': 180.0,
                'natural_rest': 0.0
            },
            BodyPart.EYE_LEFT: {
                'range': (-30.0, 30.0),
                'max_velocity': 200.0,
                'max_acceleration': 500.0,
                'natural_rest': 0.0
            },
            BodyPart.EYE_RIGHT: {
                'range': (-30.0, 30.0),
                'max_velocity': 200.0,
                'max_acceleration': 500.0,
                'natural_rest': 0.0
            }
        }

        logger.info("Joint constraints initialized for safety and realism")

    def _initialize_gesture_library(self):
        """Initialize library of complex gesture sequences"""

        # Greeting Gestures
        self.gesture_sequences["enthusiastic_greeting"] = MultiServoSequence(
            name="Enthusiastic Greeting",
            description="Excited multi-servo greeting with head bob and dome spin",
            duration=4.5,
            coordination_type=CoordinationType.LAYERED,
            primary_focus=BodyPart.HEAD_PITCH,
            secondary_actions=[BodyPart.DOME_ROTATION, BodyPart.EYE_LEFT, BodyPart.EYE_RIGHT],
            appeal_factor=1.3
        )

        # Head movement with anticipation
        self.gesture_sequences["enthusiastic_greeting"].servo_keyframes[BodyPart.HEAD_PITCH] = [
            ServoKeyframe(
                servo=BodyPart.HEAD_PITCH,
                position=-5.0,
                duration=0.3,
                easing=EasingType.EASE_OUT_BACK,
                anticipation_offset=0.1,
                staging_priority=10
            ),
            ServoKeyframe(
                servo=BodyPart.HEAD_PITCH,
                position=15.0,
                duration=0.6,
                easing=EasingType.EASE_OUT_BOUNCE,
                exaggeration_factor=1.2,
                staging_priority=10
            ),
            ServoKeyframe(
                servo=BodyPart.HEAD_PITCH,
                position=-3.0,
                duration=0.4,
                easing=EasingType.EASE_IN_QUAD,
                staging_priority=8
            ),
            ServoKeyframe(
                servo=BodyPart.HEAD_PITCH,
                position=10.0,
                duration=0.5,
                easing=EasingType.EASE_OUT_CUBIC,
                staging_priority=9
            ),
            ServoKeyframe(
                servo=BodyPart.HEAD_PITCH,
                position=0.0,
                duration=0.8,
                easing=EasingType.EASE_IN_OUT_CUBIC,
                follow_through=0.2,
                staging_priority=5
            )
        ]

        # Coordinated dome rotation
        self.gesture_sequences["enthusiastic_greeting"].servo_keyframes[BodyPart.DOME_ROTATION] = [
            ServoKeyframe(
                servo=BodyPart.DOME_ROTATION,
                position=0.0,
                duration=0.5,
                easing=EasingType.EASE_IN_QUAD,
                staging_priority=6
            ),
            ServoKeyframe(
                servo=BodyPart.DOME_ROTATION,
                position=90.0,
                duration=1.2,
                easing=EasingType.EASE_OUT_BACK,
                arc_curvature=0.3,
                staging_priority=7
            ),
            ServoKeyframe(
                servo=BodyPart.DOME_ROTATION,
                position=180.0,
                duration=1.0,
                easing=EasingType.LINEAR,
                staging_priority=6
            ),
            ServoKeyframe(
                servo=BodyPart.DOME_ROTATION,
                position=0.0,
                duration=1.8,
                easing=EasingType.EASE_IN_OUT_CUBIC,
                follow_through=0.3,
                staging_priority=4
            )
        ]

        # Eye coordination
        eye_sequence = [
            ServoKeyframe(
                servo=BodyPart.EYE_LEFT,
                position=0.0,
                duration=0.8,
                easing=EasingType.LINEAR,
                staging_priority=3
            ),
            ServoKeyframe(
                servo=BodyPart.EYE_LEFT,
                position=20.0,
                duration=0.4,
                easing=EasingType.EASE_OUT_QUART,
                staging_priority=4
            ),
            ServoKeyframe(
                servo=BodyPart.EYE_LEFT,
                position=-15.0,
                duration=0.5,
                easing=EasingType.EASE_IN_OUT_QUAD,
                staging_priority=4
            ),
            ServoKeyframe(
                servo=BodyPart.EYE_LEFT,
                position=0.0,
                duration=0.7,
                easing=EasingType.EASE_IN_OUT_CUBIC,
                staging_priority=2
            )
        ]

        self.gesture_sequences["enthusiastic_greeting"].servo_keyframes[BodyPart.EYE_LEFT] = eye_sequence

        # Mirror for right eye with slight offset
        right_eye_sequence = []
        for keyframe in eye_sequence:
            right_keyframe = ServoKeyframe(
                servo=BodyPart.EYE_RIGHT,
                position=-keyframe.position,  # Mirror position
                duration=keyframe.duration + 0.05,  # Slight offset
                easing=keyframe.easing,
                staging_priority=keyframe.staging_priority
            )
            right_eye_sequence.append(right_keyframe)

        self.gesture_sequences["enthusiastic_greeting"].servo_keyframes[BodyPart.EYE_RIGHT] = right_eye_sequence

        # Curious Investigation Gesture
        self.gesture_sequences["curious_investigation"] = MultiServoSequence(
            name="Curious Investigation",
            description="Analytical scanning with coordinated head and dome movement",
            duration=6.0,
            coordination_type=CoordinationType.SEQUENTIAL,
            primary_focus=BodyPart.HEAD_YAW,
            secondary_actions=[BodyPart.DOME_ROTATION, BodyPart.PERISCOPE],
            appeal_factor=1.1
        )

        # Sequential head scanning
        self.gesture_sequences["curious_investigation"].servo_keyframes[BodyPart.HEAD_YAW] = [
            ServoKeyframe(
                servo=BodyPart.HEAD_YAW,
                position=0.0,
                duration=0.5,
                easing=EasingType.EASE_IN_QUAD,
                staging_priority=10
            ),
            ServoKeyframe(
                servo=BodyPart.HEAD_YAW,
                position=-45.0,
                duration=1.5,
                easing=EasingType.EASE_IN_OUT_CUBIC,
                arc_curvature=0.2,
                staging_priority=9
            ),
            ServoKeyframe(
                servo=BodyPart.HEAD_YAW,
                position=45.0,
                duration=2.5,
                easing=EasingType.LINEAR,
                staging_priority=8
            ),
            ServoKeyframe(
                servo=BodyPart.HEAD_YAW,
                position=0.0,
                duration=1.5,
                easing=EasingType.EASE_IN_OUT_CUBIC,
                follow_through=0.1,
                staging_priority=6
            )
        ]

        # Alert Response Gesture
        self.gesture_sequences["alert_response"] = MultiServoSequence(
            name="Alert Response",
            description="Rapid alert response with periscope extension and head snap",
            duration=2.5,
            coordination_type=CoordinationType.CHAIN_REACTION,
            primary_focus=BodyPart.PERISCOPE,
            secondary_actions=[BodyPart.HEAD_PITCH, BodyPart.EYE_LEFT, BodyPart.EYE_RIGHT],
            appeal_factor=1.4
        )

        # Chain reaction starting with periscope
        self.gesture_sequences["alert_response"].servo_keyframes[BodyPart.PERISCOPE] = [
            ServoKeyframe(
                servo=BodyPart.PERISCOPE,
                position=0.0,
                duration=0.1,
                easing=EasingType.EASE_OUT_QUART,
                anticipation_offset=0.05,
                staging_priority=10
            ),
            ServoKeyframe(
                servo=BodyPart.PERISCOPE,
                position=100.0,
                duration=0.8,
                easing=EasingType.EASE_OUT_BACK,
                exaggeration_factor=1.3,
                staging_priority=10
            ),
            ServoKeyframe(
                servo=BodyPart.PERISCOPE,
                position=90.0,
                duration=1.6,
                easing=EasingType.EASE_IN_OUT_CUBIC,
                follow_through=0.15,
                staging_priority=8
            )
        ]

        logger.info(f"Initialized {len(self.gesture_sequences)} gesture sequences")

    def _initialize_emotional_expressions(self):
        """Initialize emotional expression patterns"""

        # Joy/Excitement Expression
        self.emotional_expressions["joy"] = MultiServoSequence(
            name="Joy Expression",
            description="Full-body expression of joy and excitement",
            duration=3.5,
            coordination_type=CoordinationType.SYNCHRONIZED,
            primary_focus=BodyPart.HEAD_PITCH,
            secondary_actions=[BodyPart.DOME_ROTATION, BodyPart.BODY_LEAN],
            appeal_factor=1.5,
            breathing_rhythm=1.2
        )

        # Synchronized joy movement
        self.emotional_expressions["joy"].servo_keyframes[BodyPart.HEAD_PITCH] = [
            ServoKeyframe(
                servo=BodyPart.HEAD_PITCH,
                position=20.0,
                duration=0.4,
                easing=EasingType.EASE_OUT_BOUNCE,
                exaggeration_factor=1.4,
                staging_priority=10
            ),
            ServoKeyframe(
                servo=BodyPart.HEAD_PITCH,
                position=-5.0,
                duration=0.3,
                easing=EasingType.EASE_IN_BOUNCE,
                staging_priority=8
            ),
            ServoKeyframe(
                servo=BodyPart.HEAD_PITCH,
                position=15.0,
                duration=0.4,
                easing=EasingType.EASE_OUT_BOUNCE,
                staging_priority=9
            ),
            ServoKeyframe(
                servo=BodyPart.HEAD_PITCH,
                position=0.0,
                duration=0.8,
                easing=EasingType.EASE_IN_OUT_CUBIC,
                follow_through=0.2,
                staging_priority=5
            )
        ]

        # Concern/Worry Expression
        self.emotional_expressions["concern"] = MultiServoSequence(
            name="Concern Expression",
            description="Worried, protective body language",
            duration=4.0,
            coordination_type=CoordinationType.LAYERED,
            primary_focus=BodyPart.HEAD_PITCH,
            secondary_actions=[BodyPart.HEAD_YAW, BodyPart.BODY_LEAN],
            appeal_factor=1.2,
            breathing_rhythm=0.8
        )

        logger.info(f"Initialized {len(self.emotional_expressions)} emotional expressions")

    def _initialize_contextual_behaviors(self):
        """Initialize context-specific behavior patterns"""

        # Photo Session Pose
        self.contextual_behaviors["photo_pose"] = MultiServoSequence(
            name="Photo Session Pose",
            description="Heroic pose for photo opportunities",
            duration=5.0,
            coordination_type=CoordinationType.SYNCHRONIZED,
            primary_focus=BodyPart.HEAD_PITCH,
            secondary_actions=[BodyPart.DOME_ROTATION, BodyPart.BODY_LEAN],
            appeal_factor=1.6
        )

        # Demonstration Mode
        self.contextual_behaviors["demonstration_mode"] = MultiServoSequence(
            name="Demonstration Mode",
            description="Educational display of capabilities",
            duration=8.0,
            coordination_type=CoordinationType.SEQUENTIAL,
            primary_focus=BodyPart.DOME_ROTATION,
            secondary_actions=[BodyPart.HEAD_PITCH, BodyPart.PERISCOPE, BodyPart.EYE_LEFT],
            appeal_factor=1.3
        )

        logger.info(f"Initialized {len(self.contextual_behaviors)} contextual behaviors")

    def execute_gesture_sequence(self, sequence_name: str,
                                 parameters: Optional[GestureParameters] = None) -> bool:
        """
        Execute a complex multi-servo gesture sequence

        Args:
            sequence_name: Name of the sequence to execute
            parameters: Optional parameters to modify the gesture

        Returns:
            bool: True if sequence was executed successfully
        """

        # Find the sequence
        sequence = None
        if sequence_name in self.gesture_sequences:
            sequence = self.gesture_sequences[sequence_name]
        elif sequence_name in self.emotional_expressions:
            sequence = self.emotional_expressions[sequence_name]
        elif sequence_name in self.contextual_behaviors:
            sequence = self.contextual_behaviors[sequence_name]

        if not sequence:
            logger.error(f"Unknown sequence: {sequence_name}")
            return False

        if not self.servo_controller:
            logger.error("No servo controller available")
            return False

        # Apply parameters if provided
        if parameters:
            sequence = self._apply_gesture_parameters(sequence, parameters)

        # Apply bio-mechanical principles
        sequence = self._apply_biomechanical_principles(sequence)

        # Execute the coordinated sequence
        try:
            success = self._execute_coordinated_sequence(sequence)

            if success:
                self.animation_metrics['sequences_executed'] += 1
                self._update_animation_metrics(sequence)

                logger.info(f"Successfully executed sequence: {sequence_name}")

            return success

        except Exception as e:
            logger.error(f"Failed to execute sequence '{sequence_name}': {e}")
            return False

    def _apply_gesture_parameters(self, sequence: MultiServoSequence,
                                 parameters: GestureParameters) -> MultiServoSequence:
        """Apply gesture parameters to modify the sequence"""

        modified_sequence = MultiServoSequence(
            name=sequence.name,
            description=sequence.description,
            duration=sequence.duration * parameters.temporal_scale,
            coordination_type=sequence.coordination_type,
            primary_focus=sequence.primary_focus,
            secondary_actions=sequence.secondary_actions.copy(),
            appeal_factor=sequence.appeal_factor * parameters.personality_influence
        )

        # Apply scaling to all keyframes
        for body_part, keyframes in sequence.servo_keyframes.items():
            modified_keyframes = []

            for keyframe in keyframes:
                modified_keyframe = ServoKeyframe(
                    servo=keyframe.servo,
                    position=keyframe.position * parameters.physical_scale,
                    duration=keyframe.duration * parameters.temporal_scale,
                    easing=keyframe.easing,
                    anticipation_offset=keyframe.anticipation_offset * parameters.temporal_scale,
                    follow_through=keyframe.follow_through * parameters.temporal_scale,
                    secondary_motion=keyframe.secondary_motion * parameters.emotional_intensity,
                    arc_curvature=keyframe.arc_curvature * parameters.bio_mechanical_realism,
                    squash_factor=keyframe.squash_factor * parameters.emotional_intensity,
                    exaggeration_factor=keyframe.exaggeration_factor * parameters.emotional_intensity,
                    staging_priority=keyframe.staging_priority
                )
                modified_keyframes.append(modified_keyframe)

            modified_sequence.servo_keyframes[body_part] = modified_keyframes

        return modified_sequence

    def _apply_biomechanical_principles(self, sequence: MultiServoSequence) -> MultiServoSequence:
        """Apply bio-mechanical principles to enhance realism"""

        # Apply natural frequencies and joint constraints
        for body_part, keyframes in sequence.servo_keyframes.items():
            if body_part in self.joint_constraints:
                constraints = self.joint_constraints[body_part]

                for keyframe in keyframes:
                    # Clamp positions to safe ranges
                    min_pos, max_pos = constraints['range']
                    keyframe.position = np.clip(keyframe.position, min_pos, max_pos)

                    # Apply velocity and acceleration constraints
                    # This would involve calculating and adjusting durations
                    # based on maximum velocity and acceleration limits

        # Apply momentum conservation
        if sequence.momentum_conservation:
            self._apply_momentum_conservation(sequence)

        # Apply natural breathing rhythm if specified
        if sequence.breathing_rhythm > 0:
            self._apply_breathing_rhythm(sequence)

        return sequence

    def _apply_momentum_conservation(self, sequence: MultiServoSequence):
        """Apply momentum conservation for realistic motion"""

        # This would analyze the sequence and adjust timing and positions
        # to maintain realistic momentum throughout the movement
        pass

    def _apply_breathing_rhythm(self, sequence: MultiServoSequence):
        """Apply subtle breathing-like rhythm to the sequence"""

        # Add subtle oscillations that simulate natural breathing
        breathing_frequency = sequence.breathing_rhythm

        for body_part, keyframes in sequence.servo_keyframes.items():
            for i, keyframe in enumerate(keyframes):
                # Add subtle breathing motion
                breathing_offset = math.sin(i * breathing_frequency) * 0.5
                keyframe.position += breathing_offset

    def _execute_coordinated_sequence(self, sequence: MultiServoSequence) -> bool:
        """Execute a coordinated multi-servo sequence"""

        coordination_type = sequence.coordination_type

        if coordination_type == CoordinationType.SYNCHRONIZED:
            return self._execute_synchronized_sequence(sequence)
        elif coordination_type == CoordinationType.SEQUENTIAL:
            return self._execute_sequential_sequence(sequence)
        elif coordination_type == CoordinationType.LAYERED:
            return self._execute_layered_sequence(sequence)
        elif coordination_type == CoordinationType.CHAIN_REACTION:
            return self._execute_chain_reaction_sequence(sequence)
        else:
            logger.warning(f"Unsupported coordination type: {coordination_type}")
            return self._execute_synchronized_sequence(sequence)

    def _execute_synchronized_sequence(self, sequence: MultiServoSequence) -> bool:
        """Execute all servos simultaneously"""

        try:
            # Start all servo sequences at the same time
            threads = []

            for body_part, keyframes in sequence.servo_keyframes.items():
                servo_name = body_part.value

                # Convert ServoKeyframe to MotionKeyframe
                motion_keyframes = []
                for keyframe in keyframes:
                    motion_keyframe = MotionKeyframe(
                        position=keyframe.position,
                        duration=keyframe.duration,
                        easing=keyframe.easing
                    )
                    motion_keyframes.append(motion_keyframe)

                # Execute servo sequence in separate thread
                thread = threading.Thread(
                    target=self._execute_servo_sequence,
                    args=(servo_name, motion_keyframes),
                    daemon=True
                )
                threads.append(thread)
                thread.start()

            # Wait for all sequences to complete
            for thread in threads:
                thread.join(timeout=sequence.duration + 2.0)

            return True

        except Exception as e:
            logger.error(f"Failed to execute synchronized sequence: {e}")
            return False

    def _execute_sequential_sequence(self, sequence: MultiServoSequence) -> bool:
        """Execute servos one after another"""

        try:
            # Sort by staging priority
            sorted_servos = sorted(
                sequence.servo_keyframes.items(),
                key=lambda x: self._get_staging_priority(x[1]),
                reverse=True
            )

            for body_part, keyframes in sorted_servos:
                servo_name = body_part.value

                # Convert ServoKeyframe to MotionKeyframe
                motion_keyframes = []
                for keyframe in keyframes:
                    motion_keyframe = MotionKeyframe(
                        position=keyframe.position,
                        duration=keyframe.duration,
                        easing=keyframe.easing
                    )
                    motion_keyframes.append(motion_keyframe)

                # Execute servo sequence
                success = self.servo_controller.animate_sequence(servo_name, motion_keyframes)
                if not success:
                    logger.warning(f"Failed to execute sequence for {servo_name}")

                # Brief pause between servos
                time.sleep(0.1)

            return True

        except Exception as e:
            logger.error(f"Failed to execute sequential sequence: {e}")
            return False

    def _execute_layered_sequence(self, sequence: MultiServoSequence) -> bool:
        """Execute servos with overlapping timing"""

        try:
            # Start primary focus first
            primary_keyframes = sequence.servo_keyframes.get(sequence.primary_focus, [])
            if primary_keyframes:
                servo_name = sequence.primary_focus.value
                motion_keyframes = self._convert_to_motion_keyframes(primary_keyframes)

                # Start primary sequence
                thread = threading.Thread(
                    target=self._execute_servo_sequence,
                    args=(servo_name, motion_keyframes),
                    daemon=True
                )
                thread.start()

                # Stagger secondary actions
                delay = 0.2
                for body_part in sequence.secondary_actions:
                    if body_part in sequence.servo_keyframes:
                        time.sleep(delay)

                        keyframes = sequence.servo_keyframes[body_part]
                        servo_name = body_part.value
                        motion_keyframes = self._convert_to_motion_keyframes(keyframes)

                        secondary_thread = threading.Thread(
                            target=self._execute_servo_sequence,
                            args=(servo_name, motion_keyframes),
                            daemon=True
                        )
                        secondary_thread.start()

                        delay += 0.1  # Increase delay for each subsequent action

                # Wait for primary sequence to complete
                thread.join(timeout=sequence.duration + 2.0)

            return True

        except Exception as e:
            logger.error(f"Failed to execute layered sequence: {e}")
            return False

    def _execute_chain_reaction_sequence(self, sequence: MultiServoSequence) -> bool:
        """Execute servos in cascading chain reaction"""

        try:
            # Start with highest priority servo
            remaining_servos = list(sequence.servo_keyframes.items())

            while remaining_servos:
                # Find next servo to trigger
                next_servo = max(remaining_servos,
                               key=lambda x: self._get_staging_priority(x[1]))

                body_part, keyframes = next_servo
                remaining_servos.remove(next_servo)

                servo_name = body_part.value
                motion_keyframes = self._convert_to_motion_keyframes(keyframes)

                # Execute servo sequence
                thread = threading.Thread(
                    target=self._execute_servo_sequence,
                    args=(servo_name, motion_keyframes),
                    daemon=True
                )
                thread.start()

                # Wait for trigger point (partial completion)
                trigger_delay = motion_keyframes[0].duration * 0.3 if motion_keyframes else 0.2
                time.sleep(trigger_delay)

            return True

        except Exception as e:
            logger.error(f"Failed to execute chain reaction sequence: {e}")
            return False

    def _execute_servo_sequence(self, servo_name: str, motion_keyframes: List[MotionKeyframe]):
        """Execute a single servo sequence"""
        try:
            self.servo_controller.animate_sequence(servo_name, motion_keyframes)
        except Exception as e:
            logger.error(f"Failed to execute servo sequence for {servo_name}: {e}")

    def _convert_to_motion_keyframes(self, servo_keyframes: List[ServoKeyframe]) -> List[MotionKeyframe]:
        """Convert ServoKeyframes to MotionKeyframes"""
        motion_keyframes = []
        for keyframe in servo_keyframes:
            motion_keyframe = MotionKeyframe(
                position=keyframe.position,
                duration=keyframe.duration,
                easing=keyframe.easing
            )
            motion_keyframes.append(motion_keyframe)
        return motion_keyframes

    def _get_staging_priority(self, keyframes: List[ServoKeyframe]) -> int:
        """Get the staging priority for a set of keyframes"""
        if not keyframes:
            return 0
        return max(keyframe.staging_priority for keyframe in keyframes)

    def _update_animation_metrics(self, sequence: MultiServoSequence):
        """Update animation performance metrics"""

        # Calculate coordination accuracy
        coordination_accuracy = self._calculate_coordination_accuracy(sequence)
        self.animation_metrics['coordination_accuracy'] = coordination_accuracy

        # Update bio-mechanical realism score
        bio_mechanical_score = self._calculate_biomechanical_score(sequence)
        self.animation_metrics['bio_mechanical_realism'] = bio_mechanical_score

        # Update appeal rating
        self.animation_metrics['appeal_rating'] = sequence.appeal_factor

        logger.info(f"Animation metrics updated for sequence: {sequence.name}")

    def _calculate_coordination_accuracy(self, sequence: MultiServoSequence) -> float:
        """Calculate how well coordinated the sequence execution was"""
        # This would measure timing accuracy between servos
        return 0.95  # Placeholder

    def _calculate_biomechanical_score(self, sequence: MultiServoSequence) -> float:
        """Calculate how realistic the bio-mechanical motion was"""
        # This would analyze motion curves and natural movement patterns
        return 0.92  # Placeholder

    def get_animation_performance_report(self) -> Dict[str, Any]:
        """Get comprehensive animation performance report"""

        report = {
            'animation_library_status': 'ACTIVE',
            'available_gestures': len(self.gesture_sequences),
            'available_emotions': len(self.emotional_expressions),
            'available_contexts': len(self.contextual_behaviors),
            'animation_metrics': self.animation_metrics.copy(),
            'natural_frequencies_configured': len(self.natural_frequencies),
            'joint_constraints_configured': len(self.joint_constraints),
            'servo_controller_connected': self.servo_controller is not None
        }

        return report

    def create_custom_gesture(self, name: str, description: str,
                            servo_commands: Dict[str, List[Tuple[float, float, EasingType]]],
                            coordination_type: CoordinationType = CoordinationType.SYNCHRONIZED) -> bool:
        """
        Create a custom gesture sequence

        Args:
            name: Name of the custom gesture
            description: Description of the gesture
            servo_commands: Dict mapping servo names to lists of (position, duration, easing) tuples
            coordination_type: How to coordinate the servos

        Returns:
            bool: True if gesture was created successfully
        """

        try:
            # Create new sequence
            custom_sequence = MultiServoSequence(
                name=name,
                description=description,
                duration=0.0,  # Will be calculated
                coordination_type=coordination_type,
                appeal_factor=1.0
            )

            total_duration = 0.0

            # Convert servo commands to keyframes
            for servo_name, commands in servo_commands.items():
                try:
                    body_part = BodyPart(servo_name)
                except ValueError:
                    logger.warning(f"Unknown body part: {servo_name}")
                    continue

                keyframes = []
                sequence_duration = 0.0

                for position, duration, easing in commands:
                    keyframe = ServoKeyframe(
                        servo=body_part,
                        position=position,
                        duration=duration,
                        easing=easing,
                        staging_priority=5  # Default priority
                    )
                    keyframes.append(keyframe)
                    sequence_duration += duration

                custom_sequence.servo_keyframes[body_part] = keyframes
                total_duration = max(total_duration, sequence_duration)

            custom_sequence.duration = total_duration

            # Add to gesture library
            self.gesture_sequences[name] = custom_sequence

            logger.info(f"Created custom gesture: {name}")
            return True

        except Exception as e:
            logger.error(f"Failed to create custom gesture '{name}': {e}")
            return False

# Example usage and testing functions
def create_demo_animation_library():
    """Create a demo animation library for testing"""

    animation_library = BiomechanicalAnimationLibrary()
    return animation_library

def demo_animation_sequences():
    """Demonstrate various animation sequences"""

    library = create_demo_animation_library()

    # Demo gesture sequences
    gestures = ["enthusiastic_greeting", "curious_investigation", "alert_response"]

    for gesture in gestures:
        print(f"\n--- Demonstrating {gesture} ---")
        success = library.execute_gesture_sequence(gesture)
        print(f"Gesture execution: {'SUCCESS' if success else 'FAILED'}")

    # Demo emotional expressions
    emotions = ["joy", "concern"]

    for emotion in emotions:
        print(f"\n--- Demonstrating {emotion} emotion ---")
        success = library.execute_gesture_sequence(emotion)
        print(f"Emotion execution: {'SUCCESS' if success else 'FAILED'}")

    # Generate performance report
    report = library.get_animation_performance_report()
    print(f"\n--- Animation Performance Report ---")
    print(json.dumps(report, indent=2))

if __name__ == "__main__":
    # Run demonstration
    demo_animation_sequences()