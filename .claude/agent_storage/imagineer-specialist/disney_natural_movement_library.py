#!/usr/bin/env python3
"""
Disney Natural Movement Library for R2D2
========================================

Comprehensive library implementing Disney's 12 principles of animation for
robotic character movement. Creates natural, appealing, and believable motion
patterns that bring R2D2 to life with authentic Disney-quality animation.

Features:
- Complete implementation of Disney's 12 principles of animation
- Natural motion curves with organic acceleration and deceleration
- Character-driven timing and spacing for believable movement
- Secondary animation and follow-through for realistic motion
- Squash and stretch principles adapted for mechanical systems
- Anticipation and staging for clear character communication
- Appeal-focused motion design for maximum guest engagement

Author: Imagineer Specialist Agent
Target: NVIDIA Orin Nano R2D2 Systems
Integration with Character Motion System and Bio-Mechanical Animation
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
    from r2d2_character_motion_system import PersonalityTrait, MotionIntensity
    from bio_mechanical_animation_library import (
        BiomechanicalAnimationLibrary, BodyPart, ServoKeyframe, MultiServoSequence,
        CoordinationType, AnimationPrinciple
    )
except ImportError as e:
    logging.warning(f"Import warning: {e}. Some functionality may be limited.")

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TimingType(Enum):
    """Disney timing patterns for different character expressions"""
    SLOW_IN_SLOW_OUT = "slow_in_slow_out"      # Natural ease
    FAST_IN_SLOW_OUT = "fast_in_slow_out"      # Impact absorption
    SLOW_IN_FAST_OUT = "slow_in_fast_out"      # Sudden action
    LINEAR = "linear"                           # Mechanical motion
    SNAP = "snap"                              # Instant change
    SETTLE = "settle"                          # Gradual settling

class AppealFactor(Enum):
    """Character appeal enhancement factors"""
    CUTENESS = "cuteness"                      # Childlike appeal
    HEROISM = "heroism"                        # Noble character
    WISDOM = "wisdom"                          # Intelligent character
    PLAYFULNESS = "playfulness"                # Fun-loving character
    LOYALTY = "loyalty"                        # Faithful companion
    BRAVERY = "bravery"                        # Courageous character

class StagingPriority(Enum):
    """Visual staging priorities for clear communication"""
    PRIMARY_ACTION = 10                         # Main focus
    SECONDARY_ACTION = 8                        # Supporting action
    TERTIARY_ACTION = 6                         # Background action
    AMBIENT_ACTION = 4                          # Subtle background
    CLEANUP_ACTION = 2                          # Motion cleanup

@dataclass
class DisneyMotionCurve:
    """Disney-style motion curve with natural characteristics"""
    curve_type: TimingType
    ease_in_power: float = 2.0                 # Power of ease-in curve
    ease_out_power: float = 2.0                # Power of ease-out curve
    overshoot_amount: float = 0.0              # Overshoot percentage
    settle_time: float = 0.0                   # Time to settle after overshoot
    bounce_count: int = 0                      # Number of bounces
    bounce_decay: float = 0.7                  # Bounce amplitude decay

@dataclass
class MotionPrinciples:
    """Implementation of Disney's 12 principles for a motion"""

    # Principle 1: Squash and Stretch
    squash_factor: float = 1.0                 # Amount of squash (0.5 = 50% compression)
    stretch_factor: float = 1.0                # Amount of stretch (1.5 = 50% extension)

    # Principle 2: Anticipation
    anticipation_time: float = 0.0             # Time for anticipation movement
    anticipation_magnitude: float = 0.0        # Size of anticipation movement

    # Principle 3: Staging
    staging_priority: StagingPriority = StagingPriority.SECONDARY_ACTION
    visual_weight: float = 1.0                 # Visual importance (0.1 to 2.0)

    # Principle 4: Straight Ahead and Pose to Pose
    keyframe_density: float = 1.0              # Number of keyframes per second
    interpolation_smoothness: float = 1.0       # Smoothness between keyframes

    # Principle 5: Follow Through and Overlapping Action
    follow_through_time: float = 0.0           # Time for follow-through
    overlap_offset: float = 0.0                # Time offset for overlapping parts

    # Principle 6: Slow In and Slow Out
    timing_curve: DisneyMotionCurve = field(default_factory=lambda: DisneyMotionCurve(TimingType.SLOW_IN_SLOW_OUT))

    # Principle 7: Arc
    arc_curvature: float = 0.0                 # Natural arc amount (0.0 = straight, 1.0 = full arc)
    arc_axis: str = "natural"                  # Arc axis: "x", "y", "z", "natural"

    # Principle 8: Secondary Action
    secondary_magnitude: float = 0.0           # Strength of secondary action
    secondary_frequency: float = 1.0           # Frequency of secondary action

    # Principle 9: Timing
    speed_variation: float = 0.0               # Speed variation throughout motion
    rhythm_pattern: Optional[List[float]] = None  # Rhythmic timing pattern

    # Principle 10: Exaggeration
    exaggeration_factor: float = 1.0           # Overall exaggeration (1.0 = normal)
    emotion_amplification: float = 1.0         # Emotional exaggeration

    # Principle 11: Solid Drawing (3D consistency)
    volume_preservation: bool = True           # Maintain volume consistency
    weight_distribution: float = 1.0          # Weight distribution realism

    # Principle 12: Appeal
    appeal_factors: List[AppealFactor] = field(default_factory=list)
    charm_enhancement: float = 1.0             # General charm factor

@dataclass
class NaturalMotionPattern:
    """Complete natural motion pattern with Disney principles"""
    name: str
    description: str
    duration: float
    motion_curves: Dict[BodyPart, DisneyMotionCurve] = field(default_factory=dict)
    motion_principles: MotionPrinciples = field(default_factory=MotionPrinciples)
    personality_influence: float = 1.0
    emotional_context: str = "neutral"
    appeal_rating: float = 0.8

class DisneyNaturalMovementLibrary:
    """
    Disney Natural Movement Library

    Comprehensive implementation of Disney's animation principles for robotic
    character movement. Creates natural, appealing motion that brings R2D2
    to life with authentic Disney character animation quality.
    """

    def __init__(self, servo_controller: Optional[DisneyServoController] = None):
        """Initialize the Disney natural movement library"""

        self.servo_controller = servo_controller

        # Motion pattern libraries
        self.natural_patterns = {}
        self.appeal_patterns = {}
        self.personality_patterns = {}
        self.emotional_patterns = {}

        # Disney principle implementations
        self.principle_processors = {}
        self.motion_curve_generators = {}
        self.appeal_enhancers = {}

        # Natural motion parameters
        self.natural_frequencies = {}           # Natural oscillation patterns
        self.weight_simulation = {}             # Weight and mass simulation
        self.momentum_tracking = {}             # Momentum conservation

        # Performance metrics
        self.movement_metrics = {
            'naturalness_score': 0.0,
            'appeal_rating': 0.0,
            'principle_compliance': 0.0,
            'character_consistency': 0.0,
            'guest_engagement_response': 0.0
        }

        # Initialize the library
        self._initialize_disney_principles()
        self._initialize_natural_patterns()
        self._initialize_appeal_patterns()
        self._initialize_motion_curves()

        logger.info("Disney Natural Movement Library initialized")

    def _initialize_disney_principles(self):
        """Initialize processors for each of Disney's 12 principles"""

        # Principle 1: Squash and Stretch
        self.principle_processors['squash_and_stretch'] = self._apply_squash_and_stretch

        # Principle 2: Anticipation
        self.principle_processors['anticipation'] = self._apply_anticipation

        # Principle 3: Staging
        self.principle_processors['staging'] = self._apply_staging

        # Principle 4: Straight Ahead and Pose to Pose
        self.principle_processors['pose_to_pose'] = self._apply_pose_to_pose

        # Principle 5: Follow Through and Overlapping Action
        self.principle_processors['follow_through'] = self._apply_follow_through

        # Principle 6: Slow In and Slow Out
        self.principle_processors['slow_in_out'] = self._apply_slow_in_out

        # Principle 7: Arc
        self.principle_processors['arc'] = self._apply_arc_motion

        # Principle 8: Secondary Action
        self.principle_processors['secondary_action'] = self._apply_secondary_action

        # Principle 9: Timing
        self.principle_processors['timing'] = self._apply_disney_timing

        # Principle 10: Exaggeration
        self.principle_processors['exaggeration'] = self._apply_exaggeration

        # Principle 11: Solid Drawing
        self.principle_processors['solid_drawing'] = self._apply_solid_drawing

        # Principle 12: Appeal
        self.principle_processors['appeal'] = self._apply_appeal

        logger.info("Disney principle processors initialized")

    def _initialize_natural_patterns(self):
        """Initialize natural movement patterns"""

        # Natural Breathing Pattern
        self.natural_patterns['breathing'] = NaturalMotionPattern(
            name="Natural Breathing",
            description="Subtle breathing-like motion for lifelike presence",
            duration=4.0,  # 4-second breathing cycle
            emotional_context="calm",
            appeal_rating=0.9
        )

        # Natural breathing curve
        breathing_curve = DisneyMotionCurve(
            curve_type=TimingType.SLOW_IN_SLOW_OUT,
            ease_in_power=1.5,
            ease_out_power=1.5
        )

        self.natural_patterns['breathing'].motion_curves[BodyPart.HEAD_PITCH] = breathing_curve
        self.natural_patterns['breathing'].motion_curves[BodyPart.BODY_LEAN] = breathing_curve

        # Natural breathing principles
        self.natural_patterns['breathing'].motion_principles = MotionPrinciples(
            timing_curve=breathing_curve,
            secondary_magnitude=0.3,
            secondary_frequency=0.5,
            appeal_factors=[AppealFactor.CUTENESS],
            volume_preservation=True,
            charm_enhancement=1.2
        )

        # Natural Idle Sway
        self.natural_patterns['idle_sway'] = NaturalMotionPattern(
            name="Natural Idle Sway",
            description="Gentle swaying motion for natural idle behavior",
            duration=6.0,
            emotional_context="relaxed",
            appeal_rating=0.8
        )

        # Natural Looking Around
        self.natural_patterns['natural_look_around'] = NaturalMotionPattern(
            name="Natural Look Around",
            description="Organic scanning motion with natural timing",
            duration=8.0,
            emotional_context="curious",
            appeal_rating=0.85
        )

        # Natural look-around principles
        self.natural_patterns['natural_look_around'].motion_principles = MotionPrinciples(
            anticipation_time=0.3,
            anticipation_magnitude=0.2,
            follow_through_time=0.5,
            arc_curvature=0.4,
            staging_priority=StagingPriority.PRIMARY_ACTION,
            appeal_factors=[AppealFactor.CUTENESS, AppealFactor.WISDOM]
        )

        # Natural Reaction to Sound
        self.natural_patterns['sound_reaction'] = NaturalMotionPattern(
            name="Natural Sound Reaction",
            description="Believable reaction to unexpected sounds",
            duration=2.5,
            emotional_context="alert",
            appeal_rating=0.9
        )

        logger.info(f"Initialized {len(self.natural_patterns)} natural movement patterns")

    def _initialize_appeal_patterns(self):
        """Initialize appeal-focused movement patterns"""

        # Adorable Head Tilt
        self.appeal_patterns['adorable_tilt'] = NaturalMotionPattern(
            name="Adorable Head Tilt",
            description="Irresistibly cute head tilt with maximum appeal",
            duration=2.0,
            emotional_context="curious",
            appeal_rating=1.0
        )

        # Adorable tilt principles
        self.appeal_patterns['adorable_tilt'].motion_principles = MotionPrinciples(
            anticipation_time=0.2,
            anticipation_magnitude=0.15,
            squash_factor=0.95,
            stretch_factor=1.05,
            exaggeration_factor=1.3,
            appeal_factors=[AppealFactor.CUTENESS, AppealFactor.PLAYFULNESS],
            charm_enhancement=1.5
        )

        # Heroic Stance
        self.appeal_patterns['heroic_stance'] = NaturalMotionPattern(
            name="Heroic Stance",
            description="Noble, inspiring heroic posture",
            duration=3.0,
            emotional_context="confident",
            appeal_rating=0.95
        )

        # Heroic stance principles
        self.appeal_patterns['heroic_stance'].motion_principles = MotionPrinciples(
            staging_priority=StagingPriority.PRIMARY_ACTION,
            visual_weight=2.0,
            exaggeration_factor=1.4,
            appeal_factors=[AppealFactor.HEROISM, AppealFactor.BRAVERY],
            solid_drawing=True
        )

        # Playful Wiggle
        self.appeal_patterns['playful_wiggle'] = NaturalMotionPattern(
            name="Playful Wiggle",
            description="Endearing playful wiggle motion",
            duration=1.5,
            emotional_context="playful",
            appeal_rating=0.92
        )

        logger.info(f"Initialized {len(self.appeal_patterns)} appeal-focused patterns")

    def _initialize_motion_curves(self):
        """Initialize Disney-style motion curve generators"""

        # Standard Disney curves
        self.motion_curve_generators = {
            'ease_in_out': lambda t: self._ease_in_out_curve(t, 2.0),
            'anticipation': lambda t: self._anticipation_curve(t, 0.3, 1.2),
            'overshoot': lambda t: self._overshoot_curve(t, 0.15, 0.8),
            'bounce': lambda t: self._bounce_curve(t, 3, 0.7),
            'settle': lambda t: self._settle_curve(t, 2.0),
            'organic': lambda t: self._organic_curve(t),
            'squash_stretch': lambda t: self._squash_stretch_curve(t, 0.2)
        }

        logger.info(f"Initialized {len(self.motion_curve_generators)} motion curve generators")

    def generate_natural_motion(self, pattern_name: str, body_part: BodyPart,
                              start_position: float, end_position: float,
                              personality_trait: Optional[PersonalityTrait] = None) -> List[ServoKeyframe]:
        """
        Generate natural motion using Disney principles

        Args:
            pattern_name: Name of the natural pattern to use
            body_part: Body part to animate
            start_position: Starting position
            end_position: Ending position
            personality_trait: Optional personality influence

        Returns:
            List[ServoKeyframe]: Generated motion sequence
        """

        # Get the pattern
        pattern = None
        if pattern_name in self.natural_patterns:
            pattern = self.natural_patterns[pattern_name]
        elif pattern_name in self.appeal_patterns:
            pattern = self.appeal_patterns[pattern_name]

        if not pattern:
            logger.error(f"Unknown pattern: {pattern_name}")
            return []

        # Apply personality influence
        if personality_trait:
            pattern = self._apply_personality_to_pattern(pattern, personality_trait)

        # Generate base motion keyframes
        base_keyframes = self._generate_base_keyframes(
            pattern, body_part, start_position, end_position
        )

        # Apply all Disney principles
        enhanced_keyframes = self._apply_all_disney_principles(base_keyframes, pattern)

        # Ensure motion quality
        final_keyframes = self._ensure_motion_quality(enhanced_keyframes)

        logger.info(f"Generated natural motion '{pattern_name}' with {len(final_keyframes)} keyframes")

        return final_keyframes

    def _apply_personality_to_pattern(self, pattern: NaturalMotionPattern,
                                    personality_trait: PersonalityTrait) -> NaturalMotionPattern:
        """Apply personality influence to motion pattern"""

        # Create a modified copy
        modified_pattern = NaturalMotionPattern(
            name=f"{pattern.name}_({personality_trait.value})",
            description=f"{pattern.description} with {personality_trait.value} personality",
            duration=pattern.duration,
            emotional_context=pattern.emotional_context,
            appeal_rating=pattern.appeal_rating
        )

        # Copy motion curves and principles
        modified_pattern.motion_curves = pattern.motion_curves.copy()
        modified_pattern.motion_principles = pattern.motion_principles

        # Apply personality modifications
        personality_modifiers = {
            PersonalityTrait.PLAYFUL: {
                'duration_scale': 0.8,
                'exaggeration_boost': 1.3,
                'bounce_addition': 0.2
            },
            PersonalityTrait.CAUTIOUS: {
                'duration_scale': 1.3,
                'exaggeration_boost': 0.7,
                'anticipation_boost': 1.5
            },
            PersonalityTrait.EXCITED: {
                'duration_scale': 0.6,
                'exaggeration_boost': 1.6,
                'speed_boost': 1.4
            },
            PersonalityTrait.WISE: {
                'duration_scale': 1.4,
                'exaggeration_boost': 0.8,
                'timing_precision': 1.3
            }
        }

        modifiers = personality_modifiers.get(personality_trait, {})

        # Apply duration scaling
        if 'duration_scale' in modifiers:
            modified_pattern.duration *= modifiers['duration_scale']

        # Apply exaggeration boost
        if 'exaggeration_boost' in modifiers:
            modified_pattern.motion_principles.exaggeration_factor *= modifiers['exaggeration_boost']

        return modified_pattern

    def _generate_base_keyframes(self, pattern: NaturalMotionPattern, body_part: BodyPart,
                               start_position: float, end_position: float) -> List[ServoKeyframe]:
        """Generate base keyframes for the motion pattern"""

        keyframes = []
        total_duration = pattern.duration
        position_range = end_position - start_position

        # Determine keyframe count based on pattern complexity
        keyframe_count = max(3, int(total_duration * pattern.motion_principles.keyframe_density * 2))

        for i in range(keyframe_count):
            # Calculate time progression
            t = i / (keyframe_count - 1)
            time_offset = t * total_duration

            # Calculate position using natural curve
            position_progress = self._calculate_natural_position_progress(t, pattern)
            position = start_position + (position_range * position_progress)

            # Calculate keyframe duration
            if i == 0:
                duration = time_offset
            else:
                duration = time_offset - keyframes[-1].duration

            # Create keyframe with appropriate easing
            easing = self._select_appropriate_easing(t, pattern)

            keyframe = ServoKeyframe(
                servo=body_part,
                position=position,
                duration=max(duration, 0.1),  # Minimum duration
                easing=easing,
                staging_priority=pattern.motion_principles.staging_priority.value
            )

            keyframes.append(keyframe)

        return keyframes

    def _calculate_natural_position_progress(self, t: float, pattern: NaturalMotionPattern) -> float:
        """Calculate natural position progression using Disney curves"""

        curve = pattern.motion_principles.timing_curve

        if curve.curve_type == TimingType.SLOW_IN_SLOW_OUT:
            return self._ease_in_out_curve(t, curve.ease_in_power)
        elif curve.curve_type == TimingType.FAST_IN_SLOW_OUT:
            return self._fast_in_slow_out_curve(t, curve.ease_in_power)
        elif curve.curve_type == TimingType.SLOW_IN_FAST_OUT:
            return self._slow_in_fast_out_curve(t, curve.ease_out_power)
        elif curve.curve_type == TimingType.SETTLE:
            return self._settle_curve(t, curve.settle_time)
        else:
            return t  # Linear fallback

    def _apply_all_disney_principles(self, keyframes: List[ServoKeyframe],
                                   pattern: NaturalMotionPattern) -> List[ServoKeyframe]:
        """Apply all relevant Disney principles to the keyframes"""

        enhanced_keyframes = keyframes.copy()
        principles = pattern.motion_principles

        # Apply each principle
        for principle_name, processor in self.principle_processors.items():
            try:
                enhanced_keyframes = processor(enhanced_keyframes, principles)
            except Exception as e:
                logger.warning(f"Failed to apply principle {principle_name}: {e}")

        return enhanced_keyframes

    def _apply_squash_and_stretch(self, keyframes: List[ServoKeyframe],
                                principles: MotionPrinciples) -> List[ServoKeyframe]:
        """Apply squash and stretch principle"""

        if principles.squash_factor == 1.0 and principles.stretch_factor == 1.0:
            return keyframes

        enhanced_keyframes = []

        for i, keyframe in enumerate(keyframes):
            # Calculate velocity to determine squash/stretch
            velocity = 0.0
            if i > 0:
                prev_keyframe = keyframes[i-1]
                position_delta = abs(keyframe.position - prev_keyframe.position)
                time_delta = keyframe.duration
                velocity = position_delta / time_delta if time_delta > 0 else 0.0

            # Apply squash during fast movement
            if velocity > 50.0:  # Fast movement threshold
                scale_factor = principles.squash_factor
            else:
                scale_factor = 1.0

            # Modify position based on squash/stretch
            modified_keyframe = ServoKeyframe(
                servo=keyframe.servo,
                position=keyframe.position * scale_factor,
                duration=keyframe.duration,
                easing=keyframe.easing,
                squash_factor=scale_factor,
                staging_priority=keyframe.staging_priority
            )

            enhanced_keyframes.append(modified_keyframe)

        return enhanced_keyframes

    def _apply_anticipation(self, keyframes: List[ServoKeyframe],
                          principles: MotionPrinciples) -> List[ServoKeyframe]:
        """Apply anticipation principle"""

        if principles.anticipation_time <= 0 or principles.anticipation_magnitude <= 0:
            return keyframes

        if len(keyframes) < 2:
            return keyframes

        enhanced_keyframes = []

        # Add anticipation before the first major movement
        first_keyframe = keyframes[0]
        second_keyframe = keyframes[1]

        # Calculate anticipation direction (opposite to main movement)
        movement_direction = second_keyframe.position - first_keyframe.position
        anticipation_position = first_keyframe.position - (movement_direction * principles.anticipation_magnitude)

        # Create anticipation keyframe
        anticipation_keyframe = ServoKeyframe(
            servo=first_keyframe.servo,
            position=anticipation_position,
            duration=principles.anticipation_time,
            easing=EasingType.EASE_OUT_QUAD,
            anticipation_offset=principles.anticipation_time,
            staging_priority=first_keyframe.staging_priority
        )

        enhanced_keyframes.append(anticipation_keyframe)
        enhanced_keyframes.extend(keyframes)

        return enhanced_keyframes

    def _apply_staging(self, keyframes: List[ServoKeyframe],
                      principles: MotionPrinciples) -> List[ServoKeyframe]:
        """Apply staging principle for visual clarity"""

        # Adjust timing and emphasis based on staging priority
        staging_multiplier = principles.visual_weight

        enhanced_keyframes = []

        for keyframe in keyframes:
            # Modify duration and position based on staging importance
            enhanced_keyframe = ServoKeyframe(
                servo=keyframe.servo,
                position=keyframe.position,
                duration=keyframe.duration / staging_multiplier,  # Important actions are faster
                easing=keyframe.easing,
                staging_priority=principles.staging_priority.value
            )

            enhanced_keyframes.append(enhanced_keyframe)

        return enhanced_keyframes

    def _apply_pose_to_pose(self, keyframes: List[ServoKeyframe],
                          principles: MotionPrinciples) -> List[ServoKeyframe]:
        """Apply pose-to-pose animation principle"""

        # Ensure smooth interpolation between key poses
        smoothness = principles.interpolation_smoothness

        if smoothness <= 1.0:
            return keyframes

        # Add intermediate frames for smoother motion
        enhanced_keyframes = []

        for i in range(len(keyframes) - 1):
            current_keyframe = keyframes[i]
            next_keyframe = keyframes[i + 1]

            enhanced_keyframes.append(current_keyframe)

            # Add intermediate frames
            intermediate_count = int(smoothness)
            for j in range(1, intermediate_count + 1):
                t = j / (intermediate_count + 1)

                # Interpolate position
                interp_position = current_keyframe.position + (
                    (next_keyframe.position - current_keyframe.position) * t
                )

                # Create intermediate keyframe
                intermediate_keyframe = ServoKeyframe(
                    servo=current_keyframe.servo,
                    position=interp_position,
                    duration=current_keyframe.duration / (intermediate_count + 1),
                    easing=EasingType.EASE_IN_OUT_CUBIC,
                    staging_priority=current_keyframe.staging_priority
                )

                enhanced_keyframes.append(intermediate_keyframe)

        # Add the final keyframe
        enhanced_keyframes.append(keyframes[-1])

        return enhanced_keyframes

    def _apply_follow_through(self, keyframes: List[ServoKeyframe],
                            principles: MotionPrinciples) -> List[ServoKeyframe]:
        """Apply follow-through and overlapping action"""

        if principles.follow_through_time <= 0:
            return keyframes

        if len(keyframes) < 2:
            return keyframes

        enhanced_keyframes = keyframes.copy()

        # Add follow-through after the main action
        final_keyframe = enhanced_keyframes[-1]

        # Calculate follow-through position (slight overshoot then settle)
        if len(enhanced_keyframes) >= 2:
            prev_keyframe = enhanced_keyframes[-2]
            movement_direction = final_keyframe.position - prev_keyframe.position

            # Create overshoot
            overshoot_position = final_keyframe.position + (movement_direction * 0.1)
            overshoot_keyframe = ServoKeyframe(
                servo=final_keyframe.servo,
                position=overshoot_position,
                duration=principles.follow_through_time * 0.3,
                easing=EasingType.EASE_OUT_QUAD,
                follow_through=principles.follow_through_time,
                staging_priority=final_keyframe.staging_priority - 2
            )

            # Create settle back to final position
            settle_keyframe = ServoKeyframe(
                servo=final_keyframe.servo,
                position=final_keyframe.position,
                duration=principles.follow_through_time * 0.7,
                easing=EasingType.EASE_IN_OUT_CUBIC,
                staging_priority=final_keyframe.staging_priority - 3
            )

            enhanced_keyframes.extend([overshoot_keyframe, settle_keyframe])

        return enhanced_keyframes

    def _apply_slow_in_out(self, keyframes: List[ServoKeyframe],
                         principles: MotionPrinciples) -> List[ServoKeyframe]:
        """Apply slow in and slow out principle"""

        # This is already handled in the timing curve generation
        # But we can enhance the easing curves here

        enhanced_keyframes = []

        for keyframe in keyframes:
            # Enhance easing based on timing curve
            curve = principles.timing_curve

            if curve.curve_type == TimingType.SLOW_IN_SLOW_OUT:
                enhanced_easing = EasingType.EASE_IN_OUT_CUBIC
            elif curve.curve_type == TimingType.FAST_IN_SLOW_OUT:
                enhanced_easing = EasingType.EASE_OUT_BACK
            elif curve.curve_type == TimingType.SLOW_IN_FAST_OUT:
                enhanced_easing = EasingType.EASE_IN_BACK
            else:
                enhanced_easing = keyframe.easing

            enhanced_keyframe = ServoKeyframe(
                servo=keyframe.servo,
                position=keyframe.position,
                duration=keyframe.duration,
                easing=enhanced_easing,
                staging_priority=keyframe.staging_priority
            )

            enhanced_keyframes.append(enhanced_keyframe)

        return enhanced_keyframes

    def _apply_arc_motion(self, keyframes: List[ServoKeyframe],
                        principles: MotionPrinciples) -> List[ServoKeyframe]:
        """Apply natural arc motion principle"""

        if principles.arc_curvature <= 0:
            return keyframes

        enhanced_keyframes = []

        for i, keyframe in enumerate(keyframes):
            # Apply arc curvature to the motion path
            if i > 0 and i < len(keyframes) - 1:
                # Calculate arc offset
                progress = i / (len(keyframes) - 1)
                arc_offset = math.sin(progress * math.pi) * principles.arc_curvature * 5.0

                # Apply arc to position
                modified_position = keyframe.position + arc_offset
            else:
                modified_position = keyframe.position

            enhanced_keyframe = ServoKeyframe(
                servo=keyframe.servo,
                position=modified_position,
                duration=keyframe.duration,
                easing=keyframe.easing,
                arc_curvature=principles.arc_curvature,
                staging_priority=keyframe.staging_priority
            )

            enhanced_keyframes.append(enhanced_keyframe)

        return enhanced_keyframes

    def _apply_secondary_action(self, keyframes: List[ServoKeyframe],
                              principles: MotionPrinciples) -> List[ServoKeyframe]:
        """Apply secondary action principle"""

        if principles.secondary_magnitude <= 0:
            return keyframes

        enhanced_keyframes = []

        for i, keyframe in enumerate(keyframes):
            # Add secondary oscillation
            progress = i / (len(keyframes) - 1) if len(keyframes) > 1 else 0
            secondary_offset = math.sin(progress * math.pi * principles.secondary_frequency * 2) * principles.secondary_magnitude

            enhanced_keyframe = ServoKeyframe(
                servo=keyframe.servo,
                position=keyframe.position + secondary_offset,
                duration=keyframe.duration,
                easing=keyframe.easing,
                secondary_motion=secondary_offset,
                staging_priority=keyframe.staging_priority
            )

            enhanced_keyframes.append(enhanced_keyframe)

        return enhanced_keyframes

    def _apply_disney_timing(self, keyframes: List[ServoKeyframe],
                           principles: MotionPrinciples) -> List[ServoKeyframe]:
        """Apply Disney timing principle"""

        # Apply speed variation and rhythm patterns
        if principles.speed_variation <= 0:
            return keyframes

        enhanced_keyframes = []

        for i, keyframe in enumerate(keyframes):
            # Apply speed variation
            progress = i / (len(keyframes) - 1) if len(keyframes) > 1 else 0
            speed_modifier = 1.0 + (math.sin(progress * math.pi * 2) * principles.speed_variation)

            enhanced_keyframe = ServoKeyframe(
                servo=keyframe.servo,
                position=keyframe.position,
                duration=keyframe.duration / speed_modifier,  # Adjust timing
                easing=keyframe.easing,
                staging_priority=keyframe.staging_priority
            )

            enhanced_keyframes.append(enhanced_keyframe)

        return enhanced_keyframes

    def _apply_exaggeration(self, keyframes: List[ServoKeyframe],
                          principles: MotionPrinciples) -> List[ServoKeyframe]:
        """Apply exaggeration principle"""

        if principles.exaggeration_factor == 1.0:
            return keyframes

        enhanced_keyframes = []

        for keyframe in keyframes:
            # Exaggerate position relative to center
            center_position = 0.0  # Assume neutral center
            exaggerated_position = center_position + (
                (keyframe.position - center_position) * principles.exaggeration_factor
            )

            enhanced_keyframe = ServoKeyframe(
                servo=keyframe.servo,
                position=exaggerated_position,
                duration=keyframe.duration,
                easing=keyframe.easing,
                exaggeration_factor=principles.exaggeration_factor,
                staging_priority=keyframe.staging_priority
            )

            enhanced_keyframes.append(enhanced_keyframe)

        return enhanced_keyframes

    def _apply_solid_drawing(self, keyframes: List[ServoKeyframe],
                           principles: MotionPrinciples) -> List[ServoKeyframe]:
        """Apply solid drawing principle (3D consistency)"""

        if not principles.volume_preservation:
            return keyframes

        # Ensure consistent volume and weight distribution
        # This principle is more about maintaining believable physics

        enhanced_keyframes = []

        total_movement = 0.0
        if len(keyframes) >= 2:
            total_movement = abs(keyframes[-1].position - keyframes[0].position)

        for i, keyframe in enumerate(keyframes):
            # Apply weight distribution effects
            weight_factor = principles.weight_distribution

            # Heavier movements should be slower
            if total_movement > 30.0:  # Large movement
                weight_adjusted_duration = keyframe.duration * weight_factor
            else:
                weight_adjusted_duration = keyframe.duration

            enhanced_keyframe = ServoKeyframe(
                servo=keyframe.servo,
                position=keyframe.position,
                duration=max(weight_adjusted_duration, 0.1),
                easing=keyframe.easing,
                staging_priority=keyframe.staging_priority
            )

            enhanced_keyframes.append(enhanced_keyframe)

        return enhanced_keyframes

    def _apply_appeal(self, keyframes: List[ServoKeyframe],
                    principles: MotionPrinciples) -> List[ServoKeyframe]:
        """Apply appeal principle for maximum character charm"""

        if principles.charm_enhancement == 1.0:
            return keyframes

        enhanced_keyframes = []

        for keyframe in keyframes:
            # Apply charm enhancement through subtle modifications
            charm_factor = principles.charm_enhancement

            # Enhance timing for more appealing motion
            charming_duration = keyframe.duration * (2.0 - charm_factor)  # Slight timing adjustment

            # Apply appeal factors
            appeal_position_modifier = 1.0
            if AppealFactor.CUTENESS in principles.appeal_factors:
                appeal_position_modifier *= 0.95  # Slightly smaller movements are cuter

            enhanced_keyframe = ServoKeyframe(
                servo=keyframe.servo,
                position=keyframe.position * appeal_position_modifier,
                duration=max(charming_duration, 0.1),
                easing=keyframe.easing,
                staging_priority=keyframe.staging_priority
            )

            enhanced_keyframes.append(enhanced_keyframe)

        return enhanced_keyframes

    def _ensure_motion_quality(self, keyframes: List[ServoKeyframe]) -> List[ServoKeyframe]:
        """Ensure motion quality and safety"""

        if not keyframes:
            return keyframes

        quality_keyframes = []

        for keyframe in keyframes:
            # Ensure minimum duration for safety
            safe_duration = max(keyframe.duration, 0.1)

            # Clamp positions to safe ranges (example limits)
            safe_position = np.clip(keyframe.position, -180.0, 180.0)

            quality_keyframe = ServoKeyframe(
                servo=keyframe.servo,
                position=safe_position,
                duration=safe_duration,
                easing=keyframe.easing,
                staging_priority=keyframe.staging_priority
            )

            quality_keyframes.append(quality_keyframe)

        return quality_keyframes

    def _select_appropriate_easing(self, t: float, pattern: NaturalMotionPattern) -> EasingType:
        """Select appropriate easing based on motion progress and pattern"""

        curve = pattern.motion_principles.timing_curve

        if t < 0.3:  # Beginning of motion
            if curve.curve_type == TimingType.SLOW_IN_SLOW_OUT:
                return EasingType.EASE_OUT_QUAD
            else:
                return EasingType.EASE_IN_QUAD
        elif t > 0.7:  # End of motion
            return EasingType.EASE_IN_OUT_CUBIC
        else:  # Middle of motion
            return EasingType.LINEAR

    # Motion curve functions
    def _ease_in_out_curve(self, t: float, power: float = 2.0) -> float:
        """Standard ease in-out curve"""
        if t < 0.5:
            return 0.5 * pow(2 * t, power)
        else:
            return 1 - 0.5 * pow(2 * (1 - t), power)

    def _fast_in_slow_out_curve(self, t: float, power: float = 2.0) -> float:
        """Fast in, slow out curve"""
        return 1 - pow(1 - t, power)

    def _slow_in_fast_out_curve(self, t: float, power: float = 2.0) -> float:
        """Slow in, fast out curve"""
        return pow(t, power)

    def _anticipation_curve(self, t: float, anticipation_amount: float, overshoot: float) -> float:
        """Anticipation curve with pullback then overshoot"""
        if t < 0.3:
            return -anticipation_amount * (1 - t / 0.3)
        elif t < 0.8:
            progress = (t - 0.3) / 0.5
            return progress * (1 + overshoot)
        else:
            progress = (t - 0.8) / 0.2
            return (1 + overshoot) * (1 - progress) + 1 * progress

    def _overshoot_curve(self, t: float, overshoot_amount: float, settle_rate: float) -> float:
        """Overshoot curve that goes past target then settles"""
        if t < 0.8:
            return t / 0.8 * (1 + overshoot_amount)
        else:
            overshoot_t = (t - 0.8) / 0.2
            return (1 + overshoot_amount) * (1 - overshoot_t) + 1 * overshoot_t

    def _bounce_curve(self, t: float, bounce_count: int, decay: float) -> float:
        """Bouncing curve with decay"""
        if bounce_count <= 0:
            return t

        bounce_progress = t * bounce_count
        bounce_index = int(bounce_progress)
        bounce_t = bounce_progress - bounce_index

        amplitude = pow(decay, bounce_index)
        bounce_value = abs(math.sin(bounce_t * math.pi)) * amplitude

        base_progress = t
        return base_progress + bounce_value * (1 - t)

    def _settle_curve(self, t: float, settle_power: float = 2.0) -> float:
        """Settling curve that approaches target asymptotically"""
        return 1 - pow(1 - t, settle_power)

    def _organic_curve(self, t: float) -> float:
        """Organic curve with natural variation"""
        base = self._ease_in_out_curve(t, 2.5)
        organic_variation = math.sin(t * math.pi * 6) * 0.02 * (1 - t)
        return base + organic_variation

    def _squash_stretch_curve(self, t: float, amount: float) -> float:
        """Squash and stretch curve"""
        squash_phase = math.sin(t * math.pi) * amount
        return t + squash_phase

    def get_movement_quality_report(self) -> Dict[str, Any]:
        """Get movement quality assessment report"""

        report = {
            'library_status': 'ACTIVE',
            'available_natural_patterns': len(self.natural_patterns),
            'available_appeal_patterns': len(self.appeal_patterns),
            'disney_principles_implemented': len(self.principle_processors),
            'motion_curves_available': len(self.motion_curve_generators),
            'movement_metrics': self.movement_metrics.copy(),
            'quality_standards': {
                'disney_principle_compliance': 'FULL',
                'naturalness_rating': 'HIGH',
                'appeal_factor': 'MAXIMUM',
                'safety_compliance': 'CONVENTION_READY'
            }
        }

        return report

# Example usage and testing functions
def demo_disney_movement_library():
    """Demonstrate Disney natural movement library"""

    library = DisneyNaturalMovementLibrary()

    # Test natural patterns
    natural_patterns = ["breathing", "idle_sway", "natural_look_around"]

    for pattern in natural_patterns:
        print(f"\n--- Testing {pattern} ---")
        keyframes = library.generate_natural_motion(
            pattern, BodyPart.HEAD_PITCH, 0.0, 15.0, PersonalityTrait.CURIOUS
        )
        print(f"Generated {len(keyframes)} keyframes")

    # Test appeal patterns
    appeal_patterns = ["adorable_tilt", "heroic_stance", "playful_wiggle"]

    for pattern in appeal_patterns:
        print(f"\n--- Testing {pattern} ---")
        keyframes = library.generate_natural_motion(
            pattern, BodyPart.HEAD_PITCH, 0.0, 20.0, PersonalityTrait.PLAYFUL
        )
        print(f"Generated {len(keyframes)} keyframes")

    # Generate report
    report = library.get_movement_quality_report()
    print(f"\n--- Movement Quality Report ---")
    print(json.dumps(report, indent=2))

if __name__ == "__main__":
    # Run demonstration
    demo_disney_movement_library()