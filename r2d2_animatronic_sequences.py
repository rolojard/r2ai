#!/usr/bin/env python3
"""
R2D2 Disney-Level Animatronic Movement Patterns and Sequences
Professional Character Animation System for Servo Controllers

This module provides comprehensive animatronic sequence creation and playback
for R2D2 character performance with Disney-level quality and authenticity.

Features:
- Authentic R2D2 character movement patterns
- Smooth motion interpolation and easing
- Emotion-driven behavior sequences
- Interactive response patterns
- Professional timing and coordination
- Layered animation system with priorities
"""

import time
import math
import logging
import threading
from typing import Dict, List, Optional, Tuple, Callable, Any, Union
from dataclasses import dataclass, field
from enum import Enum
import json
import random

from pololu_maestro_controller import PololuMaestroController, R2D2MaestroInterface, ServoChannel
from r2d2_servo_config_manager import R2D2ServoConfigManager, ServoConfiguration

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class R2D2Emotion(Enum):
    """R2D2 emotional states for character-driven animation"""
    NEUTRAL = "neutral"           # Calm, idle state
    EXCITED = "excited"           # Happy, energetic
    CURIOUS = "curious"           # Inquisitive, alert
    WORRIED = "worried"           # Concerned, nervous
    FRUSTRATED = "frustrated"     # Annoyed, agitated
    SCARED = "scared"            # Fearful, defensive
    CONFIDENT = "confident"       # Bold, assertive
    PLAYFUL = "playful"          # Fun, mischievous
    FOCUSED = "focused"          # Concentrated, working

class SequencePriority(Enum):
    """Animation sequence priority levels"""
    EMERGENCY = 0     # Emergency stop, safety sequences
    CRITICAL = 1      # Important character responses
    HIGH = 2          # Primary character animations
    NORMAL = 3        # Standard movements and behaviors
    LOW = 4           # Idle animations, background movements
    AMBIENT = 5       # Subtle environmental responses

class EasingType(Enum):
    """Motion easing types for natural movement"""
    LINEAR = "linear"
    EASE_IN = "ease_in"
    EASE_OUT = "ease_out"
    EASE_IN_OUT = "ease_in_out"
    BOUNCE = "bounce"
    ELASTIC = "elastic"

@dataclass
class Keyframe:
    """Single keyframe in an animation sequence"""
    timestamp: float                    # Time from sequence start (seconds)
    servo_positions: Dict[int, float]   # Servo positions in microseconds
    speed_override: Optional[int] = None  # Speed override for this keyframe
    easing: EasingType = EasingType.EASE_IN_OUT
    hold_duration: float = 0.0         # Time to hold this position
    description: str = ""              # Human-readable description

@dataclass
class AnimationSequence:
    """Complete animation sequence definition"""
    name: str
    description: str
    emotion: R2D2Emotion
    priority: SequencePriority
    duration: float                    # Total sequence duration
    keyframes: List[Keyframe]
    loop: bool = False                # Whether to loop the sequence
    randomize: bool = False           # Add slight randomization
    blend_in_time: float = 0.5        # Time to blend in from current position
    blend_out_time: float = 0.5       # Time to blend out to next sequence

    def __post_init__(self):
        """Validate and sort keyframes"""
        self.keyframes.sort(key=lambda k: k.timestamp)
        if self.keyframes and self.keyframes[-1].timestamp > self.duration:
            self.duration = self.keyframes[-1].timestamp

class R2D2AnimatronicSequencer:
    """Disney-Level R2D2 Animatronic Sequence Engine"""

    def __init__(self, controller: PololuMaestroController, config_manager: R2D2ServoConfigManager):
        self.controller = controller
        self.config_manager = config_manager
        self.r2d2_interface = R2D2MaestroInterface(controller)

        # Sequence management
        self.sequences: Dict[str, AnimationSequence] = {}
        self.current_sequence: Optional[AnimationSequence] = None
        self.sequence_thread: Optional[threading.Thread] = None
        self.is_playing = False
        self.stop_requested = False

        # Animation state
        self.current_emotion = R2D2Emotion.NEUTRAL
        self.current_positions: Dict[int, float] = {}  # Current servo positions
        self.target_positions: Dict[int, float] = {}   # Target servo positions
        self.animation_lock = threading.Lock()

        # Performance tracking
        self.sequence_start_time = 0.0
        self.frame_count = 0
        self.target_fps = 50.0  # 50 FPS for smooth animation

        # Initialize standard R2D2 sequences
        self._initialize_standard_sequences()

        logger.info("🎭 R2D2 Animatronic Sequencer initialized")

    def _initialize_standard_sequences(self):
        """Initialize standard R2D2 animation sequences"""

        # === IDLE SEQUENCES ===
        self.add_sequence(self._create_idle_scan_sequence())
        self.add_sequence(self._create_idle_panels_sequence())
        self.add_sequence(self._create_idle_dome_sequence())

        # === EMOTIONAL SEQUENCES ===
        self.add_sequence(self._create_excited_sequence())
        self.add_sequence(self._create_curious_sequence())
        self.add_sequence(self._create_worried_sequence())
        self.add_sequence(self._create_frustrated_sequence())

        # === FUNCTIONAL SEQUENCES ===
        self.add_sequence(self._create_startup_sequence())
        self.add_sequence(self._create_shutdown_sequence())
        self.add_sequence(self._create_attention_sequence())
        self.add_sequence(self._create_acknowledgment_sequence())

        # === INTERACTIVE SEQUENCES ===
        self.add_sequence(self._create_greeting_sequence())
        self.add_sequence(self._create_farewell_sequence())
        self.add_sequence(self._create_celebration_sequence())

        logger.info(f"✅ Initialized {len(self.sequences)} standard R2D2 sequences")

    def _create_idle_scan_sequence(self) -> AnimationSequence:
        """Create subtle scanning behavior for idle state"""
        return AnimationSequence(
            name="idle_scan",
            description="Subtle dome rotation and radar eye scanning",
            emotion=R2D2Emotion.NEUTRAL,
            priority=SequencePriority.AMBIENT,
            duration=8.0,
            loop=True,
            randomize=True,
            keyframes=[
                Keyframe(0.0, {ServoChannel.DOME_ROTATION.value: 1500}, description="Center position"),
                Keyframe(2.0, {
                    ServoChannel.DOME_ROTATION.value: 1700,
                    ServoChannel.RADAR_EYE.value: 1600
                }, easing=EasingType.EASE_IN_OUT, description="Look right, radar up"),
                Keyframe(4.0, {
                    ServoChannel.DOME_ROTATION.value: 1500,
                    ServoChannel.RADAR_EYE.value: 1500
                }, easing=EasingType.EASE_IN_OUT, description="Return center"),
                Keyframe(6.0, {
                    ServoChannel.DOME_ROTATION.value: 1300,
                    ServoChannel.RADAR_EYE.value: 1400
                }, easing=EasingType.EASE_IN_OUT, description="Look left, radar down"),
                Keyframe(8.0, {
                    ServoChannel.DOME_ROTATION.value: 1500,
                    ServoChannel.RADAR_EYE.value: 1500
                }, easing=EasingType.EASE_OUT, description="Return to center")
            ]
        )

    def _create_idle_panels_sequence(self) -> AnimationSequence:
        """Create subtle panel movements for ambient life"""
        return AnimationSequence(
            name="idle_panels",
            description="Subtle panel movements to show life",
            emotion=R2D2Emotion.NEUTRAL,
            priority=SequencePriority.AMBIENT,
            duration=12.0,
            loop=True,
            randomize=True,
            keyframes=[
                Keyframe(0.0, {}, description="All panels closed"),
                Keyframe(3.0, {ServoChannel.DOME_PANEL_FRONT.value: 1300},
                        easing=EasingType.EASE_OUT, description="Front panel slight open"),
                Keyframe(4.5, {ServoChannel.DOME_PANEL_FRONT.value: 1200},
                        easing=EasingType.EASE_IN, description="Front panel close"),
                Keyframe(7.0, {ServoChannel.DOME_PANEL_LEFT.value: 1350},
                        easing=EasingType.EASE_OUT, description="Left panel slight open"),
                Keyframe(8.5, {ServoChannel.DOME_PANEL_LEFT.value: 1200},
                        easing=EasingType.EASE_IN, description="Left panel close"),
                Keyframe(10.0, {ServoChannel.DOME_PANEL_RIGHT.value: 1300},
                         easing=EasingType.EASE_OUT, description="Right panel slight open"),
                Keyframe(12.0, {ServoChannel.DOME_PANEL_RIGHT.value: 1200},
                         easing=EasingType.EASE_IN, description="Right panel close")
            ]
        )

    def _create_excited_sequence(self) -> AnimationSequence:
        """Create excited/happy behavior sequence"""
        return AnimationSequence(
            name="excited",
            description="Excited R2D2 behavior with dome spins and panel activity",
            emotion=R2D2Emotion.EXCITED,
            priority=SequencePriority.HIGH,
            duration=6.0,
            keyframes=[
                Keyframe(0.0, {ServoChannel.DOME_ROTATION.value: 1500}, description="Start center"),
                Keyframe(1.0, {
                    ServoChannel.DOME_ROTATION.value: 2000,
                    ServoChannel.DOME_PANEL_FRONT.value: 1600,
                    ServoChannel.DOME_PANEL_BACK.value: 1600
                }, speed_override=120, easing=EasingType.EASE_OUT, description="Quick spin right, panels open"),
                Keyframe(2.0, {
                    ServoChannel.DOME_ROTATION.value: 1000,
                    ServoChannel.DOME_PANEL_LEFT.value: 1600,
                    ServoChannel.DOME_PANEL_RIGHT.value: 1600
                }, speed_override=120, easing=EasingType.LINEAR, description="Quick spin left, side panels"),
                Keyframe(3.5, {
                    ServoChannel.DOME_ROTATION.value: 1800,
                    ServoChannel.UTILITY_ARM_LEFT.value: 1600,
                    ServoChannel.UTILITY_ARM_RIGHT.value: 1600
                }, speed_override=100, easing=EasingType.BOUNCE, description="Spin right, arms out"),
                Keyframe(5.0, {
                    ServoChannel.DOME_ROTATION.value: 1500,
                    ServoChannel.PERISCOPE.value: 1600
                }, easing=EasingType.EASE_IN_OUT, description="Center, periscope up"),
                Keyframe(6.0, {
                    ServoChannel.DOME_PANEL_FRONT.value: 1200,
                    ServoChannel.DOME_PANEL_BACK.value: 1200,
                    ServoChannel.DOME_PANEL_LEFT.value: 1200,
                    ServoChannel.DOME_PANEL_RIGHT.value: 1200,
                    ServoChannel.UTILITY_ARM_LEFT.value: 1200,
                    ServoChannel.UTILITY_ARM_RIGHT.value: 1200,
                    ServoChannel.PERISCOPE.value: 1200
                }, easing=EasingType.EASE_IN, description="Close all, return to neutral")
            ]
        )

    def _create_curious_sequence(self) -> AnimationSequence:
        """Create curious investigation behavior"""
        return AnimationSequence(
            name="curious",
            description="Curious investigation with head tilt and scanning",
            emotion=R2D2Emotion.CURIOUS,
            priority=SequencePriority.NORMAL,
            duration=5.0,
            keyframes=[
                Keyframe(0.0, {ServoChannel.HEAD_TILT.value: 1500}, description="Head level"),
                Keyframe(1.0, {
                    ServoChannel.HEAD_TILT.value: 1700,
                    ServoChannel.DOME_ROTATION.value: 1300
                }, easing=EasingType.EASE_OUT, description="Tilt head, look left"),
                Keyframe(2.0, {
                    ServoChannel.RADAR_EYE.value: 1700,
                    ServoChannel.PERISCOPE.value: 1400
                }, easing=EasingType.EASE_IN_OUT, description="Radar up, periscope slight"),
                Keyframe(3.0, {
                    ServoChannel.DOME_ROTATION.value: 1700,
                    ServoChannel.HEAD_TILT.value: 1300
                }, easing=EasingType.EASE_IN_OUT, description="Look right, tilt other way"),
                Keyframe(4.0, {
                    ServoChannel.DOME_PANEL_FRONT.value: 1400
                }, easing=EasingType.EASE_OUT, description="Front panel peek"),
                Keyframe(5.0, {
                    ServoChannel.HEAD_TILT.value: 1500,
                    ServoChannel.DOME_ROTATION.value: 1500,
                    ServoChannel.RADAR_EYE.value: 1500,
                    ServoChannel.PERISCOPE.value: 1200,
                    ServoChannel.DOME_PANEL_FRONT.value: 1200
                }, easing=EasingType.EASE_IN, description="Return to neutral")
            ]
        )

    def _create_worried_sequence(self) -> AnimationSequence:
        """Create worried/nervous behavior"""
        return AnimationSequence(
            name="worried",
            description="Worried behavior with nervous movements",
            emotion=R2D2Emotion.WORRIED,
            priority=SequencePriority.NORMAL,
            duration=4.0,
            keyframes=[
                Keyframe(0.0, {}, description="Start neutral"),
                Keyframe(0.5, {
                    ServoChannel.HEAD_TILT.value: 1600,
                    ServoChannel.DOME_ROTATION.value: 1400
                }, easing=EasingType.EASE_OUT, description="Nervous head movement"),
                Keyframe(1.0, {
                    ServoChannel.HEAD_TILT.value: 1400,
                    ServoChannel.DOME_ROTATION.value: 1600
                }, easing=EasingType.LINEAR, description="Quick nervous look"),
                Keyframe(1.5, {
                    ServoChannel.HEAD_TILT.value: 1600,
                    ServoChannel.DOME_ROTATION.value: 1400
                }, easing=EasingType.LINEAR, description="More nervous movement"),
                Keyframe(2.5, {
                    ServoChannel.UTILITY_ARM_LEFT.value: 1400,
                    ServoChannel.UTILITY_ARM_RIGHT.value: 1400
                }, easing=EasingType.EASE_IN_OUT, description="Arms retract defensively"),
                Keyframe(4.0, {
                    ServoChannel.HEAD_TILT.value: 1500,
                    ServoChannel.DOME_ROTATION.value: 1500,
                    ServoChannel.UTILITY_ARM_LEFT.value: 1200,
                    ServoChannel.UTILITY_ARM_RIGHT.value: 1200
                }, easing=EasingType.EASE_OUT, description="Slowly return to neutral")
            ]
        )

    def _create_frustrated_sequence(self) -> AnimationSequence:
        """Create frustrated/agitated behavior"""
        return AnimationSequence(
            name="frustrated",
            description="Frustrated behavior with agitated movements",
            emotion=R2D2Emotion.FRUSTRATED,
            priority=SequencePriority.HIGH,
            duration=5.0,
            keyframes=[
                Keyframe(0.0, {}, description="Start position"),
                Keyframe(0.5, {
                    ServoChannel.DOME_ROTATION.value: 1800,
                    ServoChannel.HEAD_TILT.value: 1700
                }, speed_override=150, easing=EasingType.LINEAR, description="Sharp turn right"),
                Keyframe(1.0, {
                    ServoChannel.DOME_ROTATION.value: 1200,
                    ServoChannel.HEAD_TILT.value: 1300
                }, speed_override=150, easing=EasingType.LINEAR, description="Sharp turn left"),
                Keyframe(1.5, {
                    ServoChannel.DOME_ROTATION.value: 1500,
                    ServoChannel.DOME_PANEL_FRONT.value: 1700,
                    ServoChannel.DOME_PANEL_BACK.value: 1700
                }, speed_override=120, easing=EasingType.BOUNCE, description="Center with panel flaps"),
                Keyframe(2.5, {
                    ServoChannel.DOME_PANEL_FRONT.value: 1200,
                    ServoChannel.DOME_PANEL_BACK.value: 1200,
                    ServoChannel.UTILITY_ARM_LEFT.value: 1800,
                    ServoChannel.UTILITY_ARM_RIGHT.value: 1800
                }, speed_override=100, description="Close panels, extend arms"),
                Keyframe(3.5, {
                    ServoChannel.UTILITY_ARM_LEFT.value: 1000,
                    ServoChannel.UTILITY_ARM_RIGHT.value: 1000
                }, speed_override=80, description="Retract arms"),
                Keyframe(5.0, {
                    ServoChannel.HEAD_TILT.value: 1500,
                    ServoChannel.DOME_ROTATION.value: 1500,
                    ServoChannel.UTILITY_ARM_LEFT.value: 1200,
                    ServoChannel.UTILITY_ARM_RIGHT.value: 1200
                }, easing=EasingType.EASE_IN, description="Return to neutral, calming down")
            ]
        )

    def _create_startup_sequence(self) -> AnimationSequence:
        """Create startup initialization sequence"""
        return AnimationSequence(
            name="startup",
            description="R2D2 startup and system check sequence",
            emotion=R2D2Emotion.FOCUSED,
            priority=SequencePriority.CRITICAL,
            duration=8.0,
            keyframes=[
                Keyframe(0.0, {}, description="All servos at home"),
                Keyframe(1.0, {ServoChannel.PERISCOPE.value: 1600},
                        easing=EasingType.EASE_OUT, description="Periscope up - systems check"),
                Keyframe(2.0, {ServoChannel.RADAR_EYE.value: 1800},
                        easing=EasingType.EASE_IN_OUT, description="Radar eye scan"),
                Keyframe(3.0, {
                    ServoChannel.DOME_PANEL_FRONT.value: 1500,
                    ServoChannel.DOME_PANEL_BACK.value: 1500
                }, easing=EasingType.EASE_OUT, description="Front/back panels test"),
                Keyframe(4.0, {
                    ServoChannel.DOME_PANEL_LEFT.value: 1500,
                    ServoChannel.DOME_PANEL_RIGHT.value: 1500
                }, easing=EasingType.EASE_OUT, description="Side panels test"),
                Keyframe(5.0, {
                    ServoChannel.UTILITY_ARM_LEFT.value: 1600,
                    ServoChannel.UTILITY_ARM_RIGHT.value: 1600
                }, easing=EasingType.EASE_IN_OUT, description="Utility arms extend"),
                Keyframe(6.0, {ServoChannel.DOME_ROTATION.value: 1800},
                        easing=EasingType.EASE_IN_OUT, description="Dome rotation test"),
                Keyframe(7.0, {
                    ServoChannel.DOME_ROTATION.value: 1500,
                    ServoChannel.HEAD_TILT.value: 1600
                }, easing=EasingType.EASE_IN_OUT, description="Return to center, head tilt test"),
                Keyframe(8.0, {
                    ServoChannel.PERISCOPE.value: 1200,
                    ServoChannel.RADAR_EYE.value: 1500,
                    ServoChannel.DOME_PANEL_FRONT.value: 1200,
                    ServoChannel.DOME_PANEL_BACK.value: 1200,
                    ServoChannel.DOME_PANEL_LEFT.value: 1200,
                    ServoChannel.DOME_PANEL_RIGHT.value: 1200,
                    ServoChannel.UTILITY_ARM_LEFT.value: 1200,
                    ServoChannel.UTILITY_ARM_RIGHT.value: 1200,
                    ServoChannel.HEAD_TILT.value: 1500
                }, easing=EasingType.EASE_IN, description="All systems return to ready state")
            ]
        )

    def _create_greeting_sequence(self) -> AnimationSequence:
        """Create friendly greeting sequence"""
        return AnimationSequence(
            name="greeting",
            description="Friendly R2D2 greeting with dome nod and panel wave",
            emotion=R2D2Emotion.PLAYFUL,
            priority=SequencePriority.HIGH,
            duration=4.0,
            keyframes=[
                Keyframe(0.0, {}, description="Start neutral"),
                Keyframe(0.5, {ServoChannel.HEAD_TILT.value: 1700},
                        easing=EasingType.EASE_OUT, description="Head tilt down (nod)"),
                Keyframe(1.0, {ServoChannel.HEAD_TILT.value: 1500},
                        easing=EasingType.BOUNCE, description="Head return (friendly nod)"),
                Keyframe(1.5, {
                    ServoChannel.DOME_PANEL_LEFT.value: 1600,
                    ServoChannel.DOME_PANEL_RIGHT.value: 1600
                }, easing=EasingType.EASE_OUT, description="Side panels open (wave)"),
                Keyframe(2.0, {
                    ServoChannel.DOME_PANEL_LEFT.value: 1200,
                    ServoChannel.DOME_PANEL_RIGHT.value: 1200
                }, easing=EasingType.EASE_IN, description="Panels close"),
                Keyframe(2.5, {
                    ServoChannel.DOME_PANEL_LEFT.value: 1600,
                    ServoChannel.DOME_PANEL_RIGHT.value: 1600
                }, easing=EasingType.EASE_OUT, description="Panels open again"),
                Keyframe(3.0, {
                    ServoChannel.DOME_PANEL_LEFT.value: 1200,
                    ServoChannel.DOME_PANEL_RIGHT.value: 1200,
                    ServoChannel.PERISCOPE.value: 1500
                }, easing=EasingType.EASE_IN, description="Panels close, periscope up"),
                Keyframe(4.0, {ServoChannel.PERISCOPE.value: 1200},
                        easing=EasingType.EASE_IN, description="Periscope down - greeting complete")
            ]
        )

    def _create_celebration_sequence(self) -> AnimationSequence:
        """Create celebration/victory sequence"""
        return AnimationSequence(
            name="celebration",
            description="Celebration sequence with spins and all panels active",
            emotion=R2D2Emotion.EXCITED,
            priority=SequencePriority.HIGH,
            duration=6.0,
            keyframes=[
                Keyframe(0.0, {}, description="Ready to celebrate"),
                Keyframe(0.5, {
                    ServoChannel.DOME_ROTATION.value: 2000,
                    ServoChannel.PERISCOPE.value: 1700
                }, speed_override=150, easing=EasingType.EASE_OUT, description="Quick spin, periscope up"),
                Keyframe(1.5, {
                    ServoChannel.DOME_ROTATION.value: 1000,
                    ServoChannel.DOME_PANEL_FRONT.value: 1700,
                    ServoChannel.DOME_PANEL_BACK.value: 1700
                }, speed_override=120, easing=EasingType.LINEAR, description="Spin other way, panels pop"),
                Keyframe(2.5, {
                    ServoChannel.DOME_ROTATION.value: 1800,
                    ServoChannel.DOME_PANEL_LEFT.value: 1700,
                    ServoChannel.DOME_PANEL_RIGHT.value: 1700,
                    ServoChannel.UTILITY_ARM_LEFT.value: 1700,
                    ServoChannel.UTILITY_ARM_RIGHT.value: 1700
                }, speed_override=120, description="Another spin, all panels and arms"),
                Keyframe(3.5, {
                    ServoChannel.DOME_ROTATION.value: 1200,
                    ServoChannel.HEAD_TILT.value: 1300
                }, speed_override=100, easing=EasingType.BOUNCE, description="Happy head movements"),
                Keyframe(4.5, {
                    ServoChannel.DOME_ROTATION.value: 1500,
                    ServoChannel.HEAD_TILT.value: 1700
                }, easing=EasingType.BOUNCE, description="More celebration moves"),
                Keyframe(6.0, {
                    ServoChannel.HEAD_TILT.value: 1500,
                    ServoChannel.DOME_PANEL_FRONT.value: 1200,
                    ServoChannel.DOME_PANEL_BACK.value: 1200,
                    ServoChannel.DOME_PANEL_LEFT.value: 1200,
                    ServoChannel.DOME_PANEL_RIGHT.value: 1200,
                    ServoChannel.UTILITY_ARM_LEFT.value: 1200,
                    ServoChannel.UTILITY_ARM_RIGHT.value: 1200,
                    ServoChannel.PERISCOPE.value: 1200
                }, easing=EasingType.EASE_IN, description="Return to neutral, celebration complete")
            ]
        )

    def _create_shutdown_sequence(self) -> AnimationSequence:
        """Create shutdown sequence"""
        return AnimationSequence(
            name="shutdown",
            description="Graceful shutdown sequence",
            emotion=R2D2Emotion.NEUTRAL,
            priority=SequencePriority.CRITICAL,
            duration=5.0,
            keyframes=[
                Keyframe(0.0, {}, description="Begin shutdown"),
                Keyframe(1.0, {ServoChannel.HEAD_TILT.value: 1700},
                        easing=EasingType.EASE_OUT, description="Head down (powering down)"),
                Keyframe(2.0, {ServoChannel.PERISCOPE.value: 1200},
                        easing=EasingType.EASE_IN, description="Periscope retract"),
                Keyframe(3.0, {
                    ServoChannel.UTILITY_ARM_LEFT.value: 1200,
                    ServoChannel.UTILITY_ARM_RIGHT.value: 1200
                }, easing=EasingType.EASE_IN, description="Arms retract"),
                Keyframe(4.0, {ServoChannel.RADAR_EYE.value: 1200},
                        easing=EasingType.EASE_IN, description="Radar eye down"),
                Keyframe(5.0, {
                    ServoChannel.HEAD_TILT.value: 1500,
                    ServoChannel.DOME_ROTATION.value: 1500
                }, easing=EasingType.EASE_IN, description="Return to neutral - shutdown complete")
            ]
        )

    def _create_attention_sequence(self) -> AnimationSequence:
        """Create attention-getting sequence"""
        return AnimationSequence(
            name="attention",
            description="Attention-getting behavior",
            emotion=R2D2Emotion.CONFIDENT,
            priority=SequencePriority.HIGH,
            duration=3.0,
            keyframes=[
                Keyframe(0.0, {}, description="Start"),
                Keyframe(0.3, {ServoChannel.HEAD_TILT.value: 1300},
                        speed_override=100, easing=EasingType.EASE_OUT, description="Quick head up"),
                Keyframe(0.6, {ServoChannel.HEAD_TILT.value: 1500},
                        easing=EasingType.BOUNCE, description="Head return"),
                Keyframe(1.0, {ServoChannel.PERISCOPE.value: 1600},
                        speed_override=120, easing=EasingType.EASE_OUT, description="Periscope up quickly"),
                Keyframe(1.5, {ServoChannel.PERISCOPE.value: 1200},
                        easing=EasingType.EASE_IN, description="Periscope down"),
                Keyframe(2.0, {ServoChannel.DOME_PANEL_FRONT.value: 1500},
                        speed_override=150, easing=EasingType.EASE_OUT, description="Front panel pop"),
                Keyframe(3.0, {ServoChannel.DOME_PANEL_FRONT.value: 1200},
                        easing=EasingType.EASE_IN, description="Panel close")
            ]
        )

    def _create_acknowledgment_sequence(self) -> AnimationSequence:
        """Create acknowledgment/yes sequence"""
        return AnimationSequence(
            name="acknowledgment",
            description="Acknowledgment nod sequence",
            emotion=R2D2Emotion.CONFIDENT,
            priority=SequencePriority.NORMAL,
            duration=2.0,
            keyframes=[
                Keyframe(0.0, {}, description="Start neutral"),
                Keyframe(0.5, {ServoChannel.HEAD_TILT.value: 1700},
                        easing=EasingType.EASE_OUT, description="Nod down"),
                Keyframe(1.0, {ServoChannel.HEAD_TILT.value: 1500},
                        easing=EasingType.EASE_IN, description="Return up"),
                Keyframe(1.5, {ServoChannel.HEAD_TILT.value: 1700},
                        easing=EasingType.EASE_OUT, description="Second nod"),
                Keyframe(2.0, {ServoChannel.HEAD_TILT.value: 1500},
                        easing=EasingType.EASE_IN, description="Final return")
            ]
        )

    def _create_farewell_sequence(self) -> AnimationSequence:
        """Create farewell sequence"""
        return AnimationSequence(
            name="farewell",
            description="Friendly farewell with dome turn and panel wave",
            emotion=R2D2Emotion.PLAYFUL,
            priority=SequencePriority.HIGH,
            duration=4.0,
            keyframes=[
                Keyframe(0.0, {}, description="Start farewell"),
                Keyframe(1.0, {ServoChannel.DOME_ROTATION.value: 1700},
                        easing=EasingType.EASE_IN_OUT, description="Turn to look"),
                Keyframe(2.0, {
                    ServoChannel.DOME_PANEL_LEFT.value: 1600,
                    ServoChannel.UTILITY_ARM_LEFT.value: 1600
                }, easing=EasingType.EASE_OUT, description="Left panel and arm wave"),
                Keyframe(3.0, {
                    ServoChannel.DOME_PANEL_LEFT.value: 1200,
                    ServoChannel.UTILITY_ARM_LEFT.value: 1200,
                    ServoChannel.HEAD_TILT.value: 1700
                }, easing=EasingType.EASE_IN, description="Close panel/arm, head nod"),
                Keyframe(4.0, {
                    ServoChannel.DOME_ROTATION.value: 1500,
                    ServoChannel.HEAD_TILT.value: 1500
                }, easing=EasingType.EASE_IN, description="Return to neutral")
            ]
        )

    def add_sequence(self, sequence: AnimationSequence):
        """Add animation sequence to library"""
        self.sequences[sequence.name] = sequence
        logger.debug(f"Added sequence: {sequence.name} ({sequence.duration}s)")

    def play_sequence(self, sequence_name: str, loop: bool = False, callback: Optional[Callable] = None) -> bool:
        """
        Play animation sequence

        Args:
            sequence_name: Name of sequence to play
            loop: Whether to loop the sequence
            callback: Optional callback when sequence completes

        Returns:
            True if sequence started successfully
        """
        if sequence_name not in self.sequences:
            logger.error(f"Sequence not found: {sequence_name}")
            return False

        if self.is_playing:
            logger.warning("Stopping current sequence to play new one")
            self.stop_sequence()

        sequence = self.sequences[sequence_name]
        sequence.loop = loop

        with self.animation_lock:
            self.current_sequence = sequence
            self.is_playing = True
            self.stop_requested = False
            self.sequence_start_time = time.time()
            self.frame_count = 0

        # Start playback thread
        self.sequence_thread = threading.Thread(
            target=self._sequence_playback_loop,
            args=(sequence, callback),
            daemon=True,
            name=f"Sequence-{sequence_name}"
        )
        self.sequence_thread.start()

        logger.info(f"🎭 Started sequence: {sequence_name} ({sequence.emotion.value})")
        return True

    def stop_sequence(self):
        """Stop current sequence playback"""
        if not self.is_playing:
            return

        self.stop_requested = True

        if self.sequence_thread and self.sequence_thread.is_alive():
            self.sequence_thread.join(timeout=1.0)

        with self.animation_lock:
            self.is_playing = False
            self.current_sequence = None

        logger.info("⏹️ Sequence playback stopped")

    def _sequence_playback_loop(self, sequence: AnimationSequence, callback: Optional[Callable]):
        """Main sequence playback loop"""
        try:
            frame_time = 1.0 / self.target_fps

            while not self.stop_requested:
                start_time = time.time()
                current_time = start_time - self.sequence_start_time

                # Check if sequence is complete
                if current_time >= sequence.duration:
                    if sequence.loop:
                        # Restart sequence
                        self.sequence_start_time = start_time
                        current_time = 0.0
                        logger.debug(f"Looping sequence: {sequence.name}")
                    else:
                        # Sequence complete
                        break

                # Calculate current servo positions
                target_positions = self._interpolate_keyframes(sequence, current_time)

                # Apply positions to servos
                if target_positions:
                    self._apply_servo_positions(target_positions)

                self.frame_count += 1

                # Maintain frame rate
                elapsed = time.time() - start_time
                sleep_time = max(0, frame_time - elapsed)
                if sleep_time > 0:
                    time.sleep(sleep_time)

            # Sequence completed
            with self.animation_lock:
                self.is_playing = False
                self.current_sequence = None

            logger.info(f"✅ Sequence completed: {sequence.name} ({self.frame_count} frames)")

            # Call completion callback
            if callback:
                try:
                    callback(sequence.name, True)
                except Exception as e:
                    logger.error(f"Sequence callback error: {e}")

        except Exception as e:
            logger.error(f"Sequence playback error: {e}")
            with self.animation_lock:
                self.is_playing = False
                self.current_sequence = None

            if callback:
                try:
                    callback(sequence.name, False)
                except:
                    pass

    def _interpolate_keyframes(self, sequence: AnimationSequence, current_time: float) -> Dict[int, float]:
        """Interpolate servo positions between keyframes"""
        if not sequence.keyframes:
            return {}

        # Find surrounding keyframes
        prev_keyframe = None
        next_keyframe = None

        for i, keyframe in enumerate(sequence.keyframes):
            if keyframe.timestamp <= current_time:
                prev_keyframe = keyframe
            else:
                next_keyframe = keyframe
                break

        # Handle edge cases
        if prev_keyframe is None:
            # Before first keyframe
            return sequence.keyframes[0].servo_positions.copy()

        if next_keyframe is None:
            # After last keyframe
            return prev_keyframe.servo_positions.copy()

        # Interpolate between keyframes
        time_delta = next_keyframe.timestamp - prev_keyframe.timestamp
        if time_delta == 0:
            return prev_keyframe.servo_positions.copy()

        progress = (current_time - prev_keyframe.timestamp) / time_delta
        progress = max(0.0, min(1.0, progress))

        # Apply easing
        eased_progress = self._apply_easing(progress, next_keyframe.easing)

        # Interpolate positions
        interpolated_positions = {}

        # Start with previous positions
        for channel, position in prev_keyframe.servo_positions.items():
            interpolated_positions[channel] = position

        # Interpolate to next positions
        for channel, target_position in next_keyframe.servo_positions.items():
            if channel in prev_keyframe.servo_positions:
                start_position = prev_keyframe.servo_positions[channel]
                interpolated_positions[channel] = start_position + (target_position - start_position) * eased_progress
            else:
                interpolated_positions[channel] = target_position

        # Add randomization if enabled
        if sequence.randomize:
            for channel in interpolated_positions:
                # Add ±2μs randomization for natural movement
                randomization = random.uniform(-2.0, 2.0)
                interpolated_positions[channel] += randomization

        return interpolated_positions

    def _apply_easing(self, progress: float, easing_type: EasingType) -> float:
        """Apply easing function to progress value"""
        if easing_type == EasingType.LINEAR:
            return progress

        elif easing_type == EasingType.EASE_IN:
            return progress * progress

        elif easing_type == EasingType.EASE_OUT:
            return 1 - (1 - progress) * (1 - progress)

        elif easing_type == EasingType.EASE_IN_OUT:
            if progress < 0.5:
                return 2 * progress * progress
            else:
                return 1 - 2 * (1 - progress) * (1 - progress)

        elif easing_type == EasingType.BOUNCE:
            if progress < 0.5:
                return 2 * progress * progress
            else:
                return 1 - 0.5 * (2 - 2 * progress) * (2 - 2 * progress)

        elif easing_type == EasingType.ELASTIC:
            if progress == 0 or progress == 1:
                return progress
            return math.pow(2, -10 * progress) * math.sin((progress - 0.1) * 2 * math.pi / 0.4) + 1

        return progress

    def _apply_servo_positions(self, positions: Dict[int, float]):
        """Apply servo positions with safety validation"""
        for channel, position_us in positions.items():
            # Get servo configuration
            config = self.config_manager.get_servo_config(channel)
            if not config or not config.enabled:
                continue

            # Apply configuration and safety limits
            effective_position = config.get_effective_position(position_us)

            # Convert to quarter-microseconds and send command
            quarters = config.limits.to_quarters(effective_position)
            success = self.controller.set_servo_position(channel, quarters, validate=True)

            if success:
                self.current_positions[channel] = effective_position
            else:
                logger.warning(f"Failed to set servo {channel} to {effective_position:.1f}μs")

    def set_emotion(self, emotion: R2D2Emotion):
        """Set current emotional state (affects sequence selection)"""
        self.current_emotion = emotion
        logger.info(f"🎭 R2D2 emotion set to: {emotion.value}")

    def play_emotion_sequence(self, emotion: R2D2Emotion) -> bool:
        """Play a sequence appropriate for the given emotion"""
        # Map emotions to sequences
        emotion_sequences = {
            R2D2Emotion.EXCITED: "excited",
            R2D2Emotion.CURIOUS: "curious",
            R2D2Emotion.WORRIED: "worried",
            R2D2Emotion.FRUSTRATED: "frustrated",
            R2D2Emotion.CONFIDENT: "attention",
            R2D2Emotion.PLAYFUL: "greeting",
            R2D2Emotion.NEUTRAL: "idle_scan"
        }

        sequence_name = emotion_sequences.get(emotion, "idle_scan")
        return self.play_sequence(sequence_name)

    def get_available_sequences(self) -> List[str]:
        """Get list of available sequence names"""
        return list(self.sequences.keys())

    def get_sequence_info(self, sequence_name: str) -> Optional[Dict]:
        """Get information about a specific sequence"""
        if sequence_name not in self.sequences:
            return None

        sequence = self.sequences[sequence_name]
        return {
            "name": sequence.name,
            "description": sequence.description,
            "emotion": sequence.emotion.value,
            "priority": sequence.priority.value,
            "duration": sequence.duration,
            "keyframe_count": len(sequence.keyframes),
            "loop": sequence.loop,
            "randomize": sequence.randomize
        }

    def get_status_report(self) -> Dict:
        """Generate comprehensive sequencer status report"""
        with self.animation_lock:
            current_sequence_info = None
            if self.current_sequence:
                current_time = time.time() - self.sequence_start_time
                progress = min(1.0, current_time / self.current_sequence.duration) if self.current_sequence.duration > 0 else 0.0

                current_sequence_info = {
                    "name": self.current_sequence.name,
                    "emotion": self.current_sequence.emotion.value,
                    "duration": self.current_sequence.duration,
                    "current_time": current_time,
                    "progress": progress,
                    "loop": self.current_sequence.loop
                }

        return {
            "sequencer_active": self.is_playing,
            "current_emotion": self.current_emotion.value,
            "current_sequence": current_sequence_info,
            "available_sequences": len(self.sequences),
            "frame_count": self.frame_count,
            "target_fps": self.target_fps,
            "current_positions": self.current_positions.copy(),
            "timestamp": time.time()
        }

def demo_r2d2_sequences():
    """Demonstration of R2D2 animatronic sequences"""
    logger.info("🎭 Starting R2D2 Animatronic Sequences Demo...")

    # Initialize systems
    controller = PololuMaestroController(simulation_mode=True)
    config_manager = R2D2ServoConfigManager()
    config_manager.initialize_from_hardware()

    sequencer = R2D2AnimatronicSequencer(controller, config_manager)

    try:
        # Demo startup sequence
        logger.info("🚀 Playing startup sequence...")
        sequencer.play_sequence("startup")
        time.sleep(8.5)

        # Demo emotional sequences
        emotions = [R2D2Emotion.EXCITED, R2D2Emotion.CURIOUS, R2D2Emotion.WORRIED]
        for emotion in emotions:
            logger.info(f"🎭 Playing {emotion.value} sequence...")
            sequencer.play_emotion_sequence(emotion)
            time.sleep(6.5)

        # Demo interactive sequences
        interactive_sequences = ["greeting", "celebration", "farewell"]
        for seq_name in interactive_sequences:
            logger.info(f"🎪 Playing {seq_name} sequence...")
            sequencer.play_sequence(seq_name)
            time.sleep(5.0)

        # Demo idle behavior (looped)
        logger.info("💤 Playing idle sequence (looped for 15 seconds)...")
        sequencer.play_sequence("idle_scan", loop=True)
        time.sleep(15.0)

        sequencer.stop_sequence()

        # Demo shutdown
        logger.info("🌙 Playing shutdown sequence...")
        sequencer.play_sequence("shutdown")
        time.sleep(5.5)

        # Print status report
        status = sequencer.get_status_report()
        print("\n" + "="*60)
        print("R2D2 ANIMATRONIC SEQUENCES REPORT")
        print("="*60)
        print(json.dumps(status, indent=2))

        logger.info("✅ R2D2 animatronic sequences demo completed!")

    except KeyboardInterrupt:
        logger.info("Demo interrupted by user")
        sequencer.stop_sequence()
    except Exception as e:
        logger.error(f"Demo failed: {e}")
    finally:
        controller.shutdown()

if __name__ == "__main__":
    demo_r2d2_sequences()