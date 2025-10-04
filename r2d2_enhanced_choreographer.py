#!/usr/bin/env python3
"""
R2D2 Enhanced Choreographer - Advanced Movement Patterns
=======================================================

Extension to the Enhanced Maestro Controller that adds sophisticated
movement choreography specifically designed for authentic R2D2 behaviors.

This module provides:
- Advanced easing functions for natural servo movement
- Complex multi-servo choreography coordination
- Character-specific movement patterns based on Star Wars canon
- Real-time movement interpolation and smoothing
- Performance optimization for 60fps behavioral integration

Author: Expert Python Coder
Target: NVIDIA Orin Nano R2D2 Systems with Pololu Maestro
Integration: Enhanced Maestro Controller + Behavioral Intelligence
"""

import asyncio
import time
import math
import threading
from typing import Dict, List, Tuple, Optional, Callable, Any
from dataclasses import dataclass, field, asdict
from enum import Enum
import logging
import json
import numpy as np
from collections import deque
import sys

# Import base servo controller
sys.path.append('/home/rolo/r2ai')
from maestro_enhanced_controller import EnhancedMaestroController, ServoSequenceStep, ServoSequence

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EasingFunction(Enum):
    """Advanced easing functions for natural movement"""
    LINEAR = "linear"
    EASE_IN = "ease_in"
    EASE_OUT = "ease_out"
    EASE_IN_OUT = "ease_in_out"
    BOUNCE = "bounce"
    ELASTIC = "elastic"
    BACK = "back"
    CIRC = "circ"
    CUBIC = "cubic"
    QUART = "quart"
    QUINT = "quint"
    SINE = "sine"
    EXPO = "expo"
    R2D2_ORGANIC = "r2d2_organic"  # Custom R2D2 natural movement
    R2D2_MECHANICAL = "r2d2_mechanical"  # Precise mechanical movement
    R2D2_EMOTIONAL = "r2d2_emotional"  # Movement that conveys emotion

class MovementPersonality(Enum):
    """Movement personality traits for different behavioral states"""
    CURIOUS_INVESTIGATIVE = "curious_investigative"
    HAPPY_ENTHUSIASTIC = "happy_enthusiastic"
    PLAYFUL_ENERGETIC = "playful_energetic"
    ALERT_FOCUSED = "alert_focused"
    STUBBORN_RESISTANT = "stubborn_resistant"
    GENTLE_CAREFUL = "gentle_careful"
    EXCITED_BOUNCY = "excited_bouncy"
    SARCASTIC_DISMISSIVE = "sarcastic_dismissive"
    PROTECTIVE_DEFENSIVE = "protective_defensive"
    MAINTENANCE_SYSTEMATIC = "maintenance_systematic"

@dataclass
class AdvancedServoStep:
    """Enhanced servo step with advanced movement control"""
    channel: int
    start_position: int
    end_position: int
    duration_ms: int
    easing_function: EasingFunction = EasingFunction.LINEAR
    delay_before_ms: int = 0
    hold_at_end_ms: int = 0

    # Advanced parameters
    overshoot_factor: float = 0.0  # Amount of overshoot (for bounce effects)
    oscillation_damping: float = 0.8  # Damping for oscillations
    velocity_curve: Optional[List[float]] = None  # Custom velocity profile

    # Synchronization
    sync_group: Optional[str] = None  # Group servos for synchronized movement
    sync_offset_ms: int = 0  # Offset within sync group

    # Character behavior
    personality_modifier: float = 1.0  # Personality-based speed/intensity modifier
    emotional_emphasis: float = 1.0  # Emotional emphasis scaling

@dataclass
class ChoreographySequence:
    """Complete choreographed movement sequence"""
    name: str
    description: str
    steps: List[AdvancedServoStep]
    total_duration_ms: int
    personality: MovementPersonality
    emotional_intensity: float = 1.0  # 0.0-2.0

    # Performance parameters
    requires_precise_timing: bool = False
    allows_interruption: bool = True
    priority: int = 1  # 1-10, higher = more important

    # Integration parameters
    audio_sync_points: List[Tuple[int, str]] = field(default_factory=list)  # (time_ms, audio_cue)
    visual_focus_points: List[Tuple[int, str]] = field(default_factory=list)  # (time_ms, focus_target)

    # Canon authenticity
    star_wars_reference: str = ""
    canon_accuracy: float = 9.0  # Out of 10

    # Safety and limits
    max_acceleration: Optional[int] = None
    emergency_stop_time_ms: int = 500

class R2D2EnhancedChoreographer:
    """
    Advanced choreographer for R2D2 movements with sophisticated easing
    and character-based movement patterns
    """

    def __init__(self, servo_controller: EnhancedMaestroController):
        """Initialize the enhanced choreographer"""
        self.servo_controller = servo_controller
        self.active_choreography: Optional[ChoreographySequence] = None
        self.choreography_start_time: Optional[float] = None

        # Movement state tracking
        self.current_positions: Dict[int, int] = {}
        self.target_positions: Dict[int, int] = {}
        self.movement_velocities: Dict[int, float] = {}

        # Performance tracking
        self.choreography_library: Dict[str, ChoreographySequence] = {}
        self.execution_history: deque = deque(maxlen=100)

        # Real-time interpolation
        self.interpolation_thread: Optional[threading.Thread] = None
        self.running = False
        self.interpolation_rate_hz = 60  # 60fps for smooth movement

        # Performance metrics
        self.performance_metrics = {
            'sequences_executed': 0,
            'total_execution_time': 0.0,
            'average_precision': 0.0,
            'timing_accuracy': 0.0,
            'movement_smoothness': 0.0
        }

        # Initialize servo positions from controller
        self._initialize_servo_positions()

        # Create choreography library
        self._create_choreography_library()

        logger.info("R2D2 Enhanced Choreographer initialized")

    def _initialize_servo_positions(self):
        """Initialize current servo positions from controller"""
        try:
            for channel in range(self.servo_controller.get_servo_count()):
                # Get current position (assume center as default)
                current_pos = 6000  # Default center position
                self.current_positions[channel] = current_pos
                self.target_positions[channel] = current_pos
                self.movement_velocities[channel] = 0.0

        except Exception as e:
            logger.error(f"Error initializing servo positions: {e}")

    def _create_choreography_library(self):
        """Create comprehensive library of R2D2 choreographed movements"""
        logger.info("Creating enhanced R2D2 choreography library...")

        # =============================================
        # GREETING CHOREOGRAPHIES
        # =============================================

        # Enthusiastic Friend Greeting
        friend_greeting_steps = [
            # Initial attention-getting dome spin
            AdvancedServoStep(
                channel=0, start_position=6000, end_position=7800, duration_ms=400,
                easing_function=EasingFunction.R2D2_ORGANIC, delay_before_ms=0,
                personality_modifier=1.2, emotional_emphasis=1.3
            ),
            # Head tilt with character
            AdvancedServoStep(
                channel=1, start_position=6000, end_position=7200, duration_ms=600,
                easing_function=EasingFunction.EASE_OUT, delay_before_ms=200,
                hold_at_end_ms=300, personality_modifier=1.0
            ),
            # Dome swing to other side with slight overshoot
            AdvancedServoStep(
                channel=0, start_position=7800, end_position=4200, duration_ms=1000,
                easing_function=EasingFunction.R2D2_EMOTIONAL, delay_before_ms=300,
                overshoot_factor=0.1, personality_modifier=1.1
            ),
            # Synchronized return to center
            AdvancedServoStep(
                channel=0, start_position=4200, end_position=6000, duration_ms=800,
                easing_function=EasingFunction.EASE_IN_OUT, delay_before_ms=0,
                sync_group="return_center", personality_modifier=0.9
            ),
            AdvancedServoStep(
                channel=1, start_position=7200, end_position=6000, duration_ms=700,
                easing_function=EasingFunction.EASE_IN_OUT, delay_before_ms=100,
                sync_group="return_center", sync_offset_ms=100
            )
        ]

        self.choreography_library["enthusiastic_friend_greeting"] = ChoreographySequence(
            name="Enthusiastic Friend Greeting",
            description="Warm, energetic greeting for recognized friends",
            steps=friend_greeting_steps,
            total_duration_ms=3200,
            personality=MovementPersonality.HAPPY_ENTHUSIASTIC,
            emotional_intensity=1.3,
            allows_interruption=False,
            priority=8,
            audio_sync_points=[(0, "greeting_friends"), (1500, "happy_excited")],
            star_wars_reference="R2D2 greeting Luke - Empire Strikes Back",
            canon_accuracy=9.2
        )

        # Curious Investigation Greeting
        curious_greeting_steps = [
            # Slow, deliberate dome turn
            AdvancedServoStep(
                channel=0, start_position=6000, end_position=7000, duration_ms=1000,
                easing_function=EasingFunction.R2D2_ORGANIC, delay_before_ms=0,
                personality_modifier=0.8
            ),
            # Head tilt with questioning motion
            AdvancedServoStep(
                channel=1, start_position=6000, end_position=6800, duration_ms=800,
                easing_function=EasingFunction.EASE_IN_OUT, delay_before_ms=500,
                hold_at_end_ms=600
            ),
            # Slight head movement (like listening)
            AdvancedServoStep(
                channel=1, start_position=6800, end_position=5200, duration_ms=600,
                easing_function=EasingFunction.SINE, delay_before_ms=800,
                personality_modifier=0.7
            ),
            # Return to attentive position
            AdvancedServoStep(
                channel=1, start_position=5200, end_position=6400, duration_ms=700,
                easing_function=EasingFunction.EASE_OUT, delay_before_ms=400
            ),
            # Dome return with slight hesitation
            AdvancedServoStep(
                channel=0, start_position=7000, end_position=6000, duration_ms=900,
                easing_function=EasingFunction.R2D2_ORGANIC, delay_before_ms=200,
                personality_modifier=0.9
            )
        ]

        self.choreography_library["curious_investigation_greeting"] = ChoreographySequence(
            name="Curious Investigation Greeting",
            description="Cautious, inquisitive greeting for unknown individuals",
            steps=curious_greeting_steps,
            total_duration_ms=4800,
            personality=MovementPersonality.CURIOUS_INVESTIGATIVE,
            emotional_intensity=0.8,
            priority=6,
            audio_sync_points=[(800, "curious_inquisitive"), (3200, "responding_questions")],
            star_wars_reference="R2D2 meeting Yoda - Empire Strikes Back",
            canon_accuracy=9.4
        )

        # =============================================
        # CHARACTER RECOGNITION CHOREOGRAPHIES
        # =============================================

        # Jedi Respect Sequence
        jedi_respect_steps = [
            # Alert posture - head up
            AdvancedServoStep(
                channel=1, start_position=6000, end_position=7500, duration_ms=600,
                easing_function=EasingFunction.R2D2_MECHANICAL, delay_before_ms=0,
                personality_modifier=1.0
            ),
            # Dome slight turn (acknowledgment)
            AdvancedServoStep(
                channel=0, start_position=6000, end_position=6800, duration_ms=800,
                easing_function=EasingFunction.EASE_IN_OUT, delay_before_ms=300
            ),
            # Respectful bow - head down slowly
            AdvancedServoStep(
                channel=1, start_position=7500, end_position=4500, duration_ms=1500,
                easing_function=EasingFunction.R2D2_ORGANIC, delay_before_ms=600,
                hold_at_end_ms=1000, personality_modifier=0.7
            ),
            # Slow return to center (reverent)
            AdvancedServoStep(
                channel=1, start_position=4500, end_position=6000, duration_ms=1200,
                easing_function=EasingFunction.EASE_OUT, delay_before_ms=1000,
                personality_modifier=0.8
            ),
            # Dome return to center
            AdvancedServoStep(
                channel=0, start_position=6800, end_position=6000, duration_ms=800,
                easing_function=EasingFunction.EASE_IN_OUT, delay_before_ms=800
            )
        ]

        self.choreography_library["jedi_recognition_respect"] = ChoreographySequence(
            name="Jedi Recognition Respect",
            description="Respectful acknowledgment sequence for Jedi-like figures",
            steps=jedi_respect_steps,
            total_duration_ms=6700,
            personality=MovementPersonality.GENTLE_CAREFUL,
            emotional_intensity=1.1,
            requires_precise_timing=True,
            allows_interruption=False,
            priority=9,
            audio_sync_points=[(0, "alert_warning"), (2000, "jedi_recognition")],
            star_wars_reference="R2D2 with Obi-Wan Kenobi - A New Hope",
            canon_accuracy=9.8
        )

        # =============================================
        # PERSONALITY-DRIVEN CHOREOGRAPHIES
        # =============================================

        # Stubborn Resistance Sequence
        stubborn_steps = [
            # Initial resistance - turn head away
            AdvancedServoStep(
                channel=1, start_position=6000, end_position=5000, duration_ms=800,
                easing_function=EasingFunction.R2D2_EMOTIONAL, delay_before_ms=0,
                personality_modifier=1.2, emotional_emphasis=1.4
            ),
            # Dome turn away (defiant)
            AdvancedServoStep(
                channel=0, start_position=6000, end_position=4800, duration_ms=1000,
                easing_function=EasingFunction.BACK, delay_before_ms=400,
                overshoot_factor=0.15
            ),
            # Hold stubborn position
            AdvancedServoStep(
                channel=1, start_position=5000, end_position=4700, duration_ms=400,
                easing_function=EasingFunction.LINEAR, delay_before_ms=1200,
                hold_at_end_ms=1500, personality_modifier=0.8
            ),
            # Reluctant partial return (still stubborn)
            AdvancedServoStep(
                channel=1, start_position=4700, end_position=5500, duration_ms=1200,
                easing_function=EasingFunction.R2D2_ORGANIC, delay_before_ms=1500,
                personality_modifier=0.6
            ),
            # Final grudging return to center
            AdvancedServoStep(
                channel=0, start_position=4800, end_position=6000, duration_ms=1500,
                easing_function=EasingFunction.EASE_IN, delay_before_ms=800,
                personality_modifier=0.7
            ),
            AdvancedServoStep(
                channel=1, start_position=5500, end_position=6000, duration_ms=1000,
                easing_function=EasingFunction.EASE_IN, delay_before_ms=1000
            )
        ]

        self.choreography_library["stubborn_resistance"] = ChoreographySequence(
            name="Stubborn Resistance",
            description="R2D2's characteristic stubborn defiance",
            steps=stubborn_steps,
            total_duration_ms=8200,
            personality=MovementPersonality.STUBBORN_RESISTANT,
            emotional_intensity=1.5,
            priority=7,
            audio_sync_points=[(500, "frustrated_stubborn"), (4000, "expressing_sarcasm")],
            star_wars_reference="R2D2 refusing orders - Original Trilogy",
            canon_accuracy=9.6
        )

        # Playful Dance Sequence
        playful_dance_steps = [
            # Energetic dome spins
            AdvancedServoStep(
                channel=0, start_position=6000, end_position=8000, duration_ms=300,
                easing_function=EasingFunction.EASE_OUT, personality_modifier=1.5
            ),
            AdvancedServoStep(
                channel=0, start_position=8000, end_position=4000, duration_ms=350,
                easing_function=EasingFunction.LINEAR, delay_before_ms=0,
                personality_modifier=1.4
            ),
            AdvancedServoStep(
                channel=0, start_position=4000, end_position=7500, duration_ms=400,
                easing_function=EasingFunction.BOUNCE, delay_before_ms=50,
                overshoot_factor=0.2
            ),
            # Head bobbing with dome movement
            AdvancedServoStep(
                channel=1, start_position=6000, end_position=7000, duration_ms=250,
                easing_function=EasingFunction.SINE, delay_before_ms=150,
                sync_group="dance_bob"
            ),
            AdvancedServoStep(
                channel=1, start_position=7000, end_position=5000, duration_ms=300,
                easing_function=EasingFunction.SINE, delay_before_ms=250,
                sync_group="dance_bob"
            ),
            AdvancedServoStep(
                channel=1, start_position=5000, end_position=6800, duration_ms=350,
                easing_function=EasingFunction.BOUNCE, delay_before_ms=300,
                overshoot_factor=0.1
            ),
            # Final flourish
            AdvancedServoStep(
                channel=0, start_position=7500, end_position=6000, duration_ms=600,
                easing_function=EasingFunction.ELASTIC, delay_before_ms=400,
                oscillation_damping=0.6
            ),
            AdvancedServoStep(
                channel=1, start_position=6800, end_position=6000, duration_ms=500,
                easing_function=EasingFunction.EASE_OUT, delay_before_ms=500
            )
        ]

        self.choreography_library["playful_entertainment_dance"] = ChoreographySequence(
            name="Playful Entertainment Dance",
            description="Energetic dance sequence for entertainment",
            steps=playful_dance_steps,
            total_duration_ms=4000,
            personality=MovementPersonality.PLAYFUL_ENERGETIC,
            emotional_intensity=1.8,
            priority=5,
            audio_sync_points=[(0, "musical_entertainment"), (2000, "playful_mischievous")],
            star_wars_reference="R2D2 entertaining at Jabba's Palace - Return of the Jedi",
            canon_accuracy=8.9
        )

        # =============================================
        # ENVIRONMENTAL RESPONSE CHOREOGRAPHIES
        # =============================================

        # Alert Scanning Sequence
        alert_scan_steps = [
            # Rapid dome movement to threat direction
            AdvancedServoStep(
                channel=0, start_position=6000, end_position=7800, duration_ms=400,
                easing_function=EasingFunction.R2D2_MECHANICAL, delay_before_ms=0,
                personality_modifier=1.3
            ),
            # Head up for better scanning
            AdvancedServoStep(
                channel=1, start_position=6000, end_position=7500, duration_ms=300,
                easing_function=EasingFunction.LINEAR, delay_before_ms=100
            ),
            # Systematic scanning sweep
            AdvancedServoStep(
                channel=0, start_position=7800, end_position=4200, duration_ms=2000,
                easing_function=EasingFunction.LINEAR, delay_before_ms=400,
                personality_modifier=0.8
            ),
            # Head movement during scan
            AdvancedServoStep(
                channel=1, start_position=7500, end_position=4500, duration_ms=1200,
                easing_function=EasingFunction.SINE, delay_before_ms=800,
                sync_group="scan_coordination"
            ),
            # Return to alert center position
            AdvancedServoStep(
                channel=0, start_position=4200, end_position=6000, duration_ms=800,
                easing_function=EasingFunction.EASE_OUT, delay_before_ms=2000
            ),
            AdvancedServoStep(
                channel=1, start_position=4500, end_position=6000, duration_ms=700,
                easing_function=EasingFunction.EASE_OUT, delay_before_ms=2100
            )
        ]

        self.choreography_library["environmental_alert_scan"] = ChoreographySequence(
            name="Environmental Alert Scan",
            description="Systematic environmental scanning for threats or changes",
            steps=alert_scan_steps,
            total_duration_ms=6300,
            personality=MovementPersonality.ALERT_FOCUSED,
            emotional_intensity=1.2,
            requires_precise_timing=True,
            priority=8,
            audio_sync_points=[(0, "alert_warning"), (3000, "curious_inquisitive")],
            visual_focus_points=[(400, "scan_left"), (1600, "scan_center"), (2400, "scan_right")],
            star_wars_reference="R2D2 detecting Imperial troops - A New Hope",
            canon_accuracy=9.1
        )

        # =============================================
        # DEMONSTRATION CHOREOGRAPHIES
        # =============================================

        # Full Capability Demonstration
        demo_steps = [
            # Opening fanfare movement
            AdvancedServoStep(
                channel=0, start_position=6000, end_position=8000, duration_ms=500,
                easing_function=EasingFunction.R2D2_ORGANIC, emotional_emphasis=1.5
            ),
            AdvancedServoStep(
                channel=1, start_position=6000, end_position=7500, duration_ms=400,
                easing_function=EasingFunction.EASE_OUT, delay_before_ms=200
            ),

            # Character showcase - multiple movement types
            AdvancedServoStep(
                channel=0, start_position=8000, end_position=4000, duration_ms=800,
                easing_function=EasingFunction.BOUNCE, delay_before_ms=500,
                overshoot_factor=0.15
            ),
            AdvancedServoStep(
                channel=1, start_position=7500, end_position=4500, duration_ms=600,
                easing_function=EasingFunction.ELASTIC, delay_before_ms=700,
                oscillation_damping=0.7
            ),

            # Personality showcase - stubborn moment
            AdvancedServoStep(
                channel=0, start_position=4000, end_position=5200, duration_ms=1000,
                easing_function=EasingFunction.BACK, delay_before_ms=1000,
                personality_modifier=0.7
            ),
            AdvancedServoStep(
                channel=1, start_position=4500, end_position=5800, duration_ms=800,
                easing_function=EasingFunction.R2D2_EMOTIONAL, delay_before_ms=1200,
                emotional_emphasis=1.3
            ),

            # Technical precision showcase
            AdvancedServoStep(
                channel=0, start_position=5200, end_position=7200, duration_ms=600,
                easing_function=EasingFunction.R2D2_MECHANICAL, delay_before_ms=1800,
                sync_group="precision_demo"
            ),
            AdvancedServoStep(
                channel=1, start_position=5800, end_position=6800, duration_ms=500,
                easing_function=EasingFunction.R2D2_MECHANICAL, delay_before_ms=1900,
                sync_group="precision_demo", sync_offset_ms=100
            ),

            # Playful finale
            AdvancedServoStep(
                channel=0, start_position=7200, end_position=6000, duration_ms=800,
                easing_function=EasingFunction.ELASTIC, delay_before_ms=2400,
                oscillation_damping=0.5, emotional_emphasis=1.4
            ),
            AdvancedServoStep(
                channel=1, start_position=6800, end_position=6000, duration_ms=700,
                easing_function=EasingFunction.EASE_OUT, delay_before_ms=2500
            )
        ]

        self.choreography_library["full_capability_demonstration"] = ChoreographySequence(
            name="Full Capability Demonstration",
            description="Complete showcase of R2D2's movement and personality",
            steps=demo_steps,
            total_duration_ms=8000,
            personality=MovementPersonality.HAPPY_ENTHUSIASTIC,
            emotional_intensity=1.6,
            requires_precise_timing=True,
            allows_interruption=False,
            priority=9,
            audio_sync_points=[
                (0, "happy_excited"), (2000, "astromech_duties"),
                (4000, "frustrated_stubborn"), (6000, "musical_entertainment")
            ],
            star_wars_reference="R2D2 showcase compilation - Original Trilogy",
            canon_accuracy=9.3,
            emergency_stop_time_ms=300
        )

        logger.info(f"Created {len(self.choreography_library)} advanced choreography sequences")

    def _calculate_easing(self, t: float, easing_function: EasingFunction) -> float:
        """Calculate easing value for time t (0.0 to 1.0)"""
        # Clamp t to valid range
        t = max(0.0, min(1.0, t))

        if easing_function == EasingFunction.LINEAR:
            return t
        elif easing_function == EasingFunction.EASE_IN:
            return t * t
        elif easing_function == EasingFunction.EASE_OUT:
            return 1 - (1 - t) * (1 - t)
        elif easing_function == EasingFunction.EASE_IN_OUT:
            if t < 0.5:
                return 2 * t * t
            else:
                return 1 - 2 * (1 - t) * (1 - t)
        elif easing_function == EasingFunction.BOUNCE:
            if t < 0.36:
                return 7.5625 * t * t
            elif t < 0.73:
                t -= 0.545
                return 7.5625 * t * t + 0.75
            elif t < 0.9:
                t -= 0.82
                return 7.5625 * t * t + 0.9375
            else:
                t -= 0.955
                return 7.5625 * t * t + 0.984375
        elif easing_function == EasingFunction.ELASTIC:
            if t == 0 or t == 1:
                return t
            p = 0.3
            s = p / 4
            return -(2 ** (10 * (t - 1))) * math.sin((t - 1 - s) * (2 * math.pi) / p)
        elif easing_function == EasingFunction.BACK:
            s = 1.70158
            return t * t * ((s + 1) * t - s)
        elif easing_function == EasingFunction.CIRC:
            return 1 - math.sqrt(1 - t * t)
        elif easing_function == EasingFunction.SINE:
            return 1 - math.cos(t * math.pi / 2)
        elif easing_function == EasingFunction.R2D2_ORGANIC:
            # Custom organic movement that feels natural for R2D2
            return t + 0.1 * math.sin(t * math.pi * 4) * (1 - t)
        elif easing_function == EasingFunction.R2D2_MECHANICAL:
            # Precise mechanical movement with slight easing
            return t * t * (3 - 2 * t)  # Smoothstep
        elif easing_function == EasingFunction.R2D2_EMOTIONAL:
            # Emotional movement with character
            return t + 0.15 * math.sin(t * math.pi * 2) * (1 - t) * t
        else:
            return t  # Default to linear

    def _interpolate_position(self, start: int, end: int, progress: float,
                            easing_function: EasingFunction,
                            overshoot_factor: float = 0.0) -> int:
        """Interpolate servo position with easing and overshoot"""
        try:
            # Apply easing function
            eased_progress = self._calculate_easing(progress, easing_function)

            # Calculate base interpolated position
            base_position = start + (end - start) * eased_progress

            # Apply overshoot effect
            if overshoot_factor > 0.0 and 0.3 < progress < 0.8:
                overshoot_amount = (end - start) * overshoot_factor
                overshoot_curve = math.sin((progress - 0.3) * math.pi / 0.5)
                base_position += overshoot_amount * overshoot_curve

            # Clamp to servo limits (typically 1000-8000)
            return int(max(1000, min(8000, base_position)))

        except Exception as e:
            logger.error(f"Error interpolating position: {e}")
            return start

    async def execute_choreography(self, choreography_name: str,
                                 personality_modifier: float = 1.0,
                                 emotional_intensity_override: Optional[float] = None) -> bool:
        """Execute a choreographed sequence with real-time interpolation"""
        try:
            if choreography_name not in self.choreography_library:
                logger.error(f"Choreography '{choreography_name}' not found")
                return False

            choreography = self.choreography_library[choreography_name]

            # Check if we can interrupt current choreography
            if (self.active_choreography and
                not self.active_choreography.allows_interruption and
                choreography.priority <= self.active_choreography.priority):
                logger.warning(f"Cannot interrupt current choreography with {choreography_name}")
                return False

            # Set active choreography
            self.active_choreography = choreography
            self.choreography_start_time = time.time()

            # Apply modifiers
            emotional_intensity = emotional_intensity_override or choreography.emotional_intensity
            effective_personality_modifier = personality_modifier

            logger.info(f"🎭 Executing choreography: {choreography_name}")
            logger.info(f"   Duration: {choreography.total_duration_ms}ms")
            logger.info(f"   Personality: {choreography.personality.value}")
            logger.info(f"   Emotional Intensity: {emotional_intensity}")

            # Start real-time interpolation
            await self._execute_choreography_with_interpolation(
                choreography, effective_personality_modifier, emotional_intensity
            )

            # Update performance metrics
            self.performance_metrics['sequences_executed'] += 1
            execution_time = time.time() - self.choreography_start_time
            self.performance_metrics['total_execution_time'] += execution_time

            # Record in history
            self.execution_history.append({
                'choreography': choreography_name,
                'timestamp': time.time(),
                'duration': execution_time,
                'personality_modifier': effective_personality_modifier,
                'emotional_intensity': emotional_intensity
            })

            logger.info(f"✅ Choreography completed: {choreography_name} ({execution_time:.2f}s)")
            return True

        except Exception as e:
            logger.error(f"Error executing choreography {choreography_name}: {e}")
            return False
        finally:
            self.active_choreography = None
            self.choreography_start_time = None

    async def _execute_choreography_with_interpolation(self, choreography: ChoreographySequence,
                                                     personality_modifier: float,
                                                     emotional_intensity: float):
        """Execute choreography with real-time servo interpolation"""
        try:
            start_time = time.time()
            last_update_time = start_time

            # Track active steps for each servo channel
            active_steps: Dict[int, AdvancedServoStep] = {}
            step_start_times: Dict[int, float] = {}

            # Create timeline of all steps
            timeline = []
            for step in choreography.steps:
                step_start_time = step.delay_before_ms / 1000.0
                timeline.append((step_start_time, 'start', step))

                step_end_time = step_start_time + step.duration_ms / 1000.0
                timeline.append((step_end_time, 'end', step))

                if step.hold_at_end_ms > 0:
                    hold_end_time = step_end_time + step.hold_at_end_ms / 1000.0
                    timeline.append((hold_end_time, 'hold_end', step))

            # Sort timeline by time
            timeline.sort(key=lambda x: x[0])
            timeline_index = 0

            # Real-time interpolation loop
            while True:
                current_time = time.time()
                elapsed_time = current_time - start_time

                # Check if choreography is complete
                if elapsed_time >= choreography.total_duration_ms / 1000.0:
                    break

                # Process timeline events
                while (timeline_index < len(timeline) and
                       timeline[timeline_index][0] <= elapsed_time):

                    event_time, event_type, step = timeline[timeline_index]

                    if event_type == 'start':
                        # Start new step for this channel
                        channel = step.channel
                        active_steps[channel] = step
                        step_start_times[channel] = current_time

                        # Update start position to current position
                        if channel in self.current_positions:
                            step.start_position = self.current_positions[channel]

                    elif event_type == 'end':
                        # End step for this channel
                        channel = step.channel
                        if channel in active_steps:
                            self.current_positions[channel] = step.end_position
                            if channel not in [s.channel for _, _, s in timeline[timeline_index:]
                                             if s.channel == channel]:
                                # No more steps for this channel, remove from active
                                active_steps.pop(channel, None)
                                step_start_times.pop(channel, None)

                    timeline_index += 1

                # Update servo positions for all active steps
                positions_to_update = {}

                for channel, step in active_steps.items():
                    if channel in step_start_times:
                        step_elapsed = current_time - step_start_times[channel]
                        step_duration = step.duration_ms / 1000.0

                        if step_elapsed <= step_duration:
                            # Calculate progress with personality and emotional modifiers
                            base_progress = step_elapsed / step_duration

                            # Apply personality modifier to timing
                            modified_progress = base_progress * step.personality_modifier * personality_modifier
                            modified_progress = max(0.0, min(1.0, modified_progress))

                            # Calculate interpolated position
                            interpolated_position = self._interpolate_position(
                                step.start_position,
                                step.end_position,
                                modified_progress,
                                step.easing_function,
                                step.overshoot_factor * emotional_intensity
                            )

                            positions_to_update[channel] = interpolated_position
                            self.current_positions[channel] = interpolated_position

                # Send position updates to servo controller
                if positions_to_update:
                    for channel, position in positions_to_update.items():
                        success = self.servo_controller.set_servo_position(channel, position)
                        if not success:
                            logger.warning(f"Failed to update servo {channel} to {position}")

                # Maintain interpolation rate (60fps)
                frame_time = 1.0 / self.interpolation_rate_hz
                sleep_time = max(0, frame_time - (time.time() - current_time))
                if sleep_time > 0:
                    await asyncio.sleep(sleep_time)

                last_update_time = current_time

        except Exception as e:
            logger.error(f"Error in choreography interpolation: {e}")

    def stop_current_choreography(self) -> bool:
        """Stop currently executing choreography"""
        try:
            if self.active_choreography:
                logger.info(f"Stopping choreography: {self.active_choreography.name}")

                # Use emergency stop time if defined
                if hasattr(self.active_choreography, 'emergency_stop_time_ms'):
                    stop_time_ms = self.active_choreography.emergency_stop_time_ms
                else:
                    stop_time_ms = 500  # Default 500ms stop time

                # Gradually stop all servos
                current_time = time.time()
                for channel, current_pos in self.current_positions.items():
                    # Create emergency stop to center position
                    center_position = 6000

                    # Use servo controller to smoothly stop
                    self.servo_controller.set_servo_position(channel, center_position)

                self.active_choreography = None
                self.choreography_start_time = None
                return True
            else:
                logger.info("No active choreography to stop")
                return False

        except Exception as e:
            logger.error(f"Error stopping choreography: {e}")
            return False

    def get_choreography_status(self) -> Dict[str, Any]:
        """Get current choreography status"""
        status = {
            'active_choreography': {
                'name': self.active_choreography.name if self.active_choreography else None,
                'personality': self.active_choreography.personality.value if self.active_choreography else None,
                'elapsed_time': (time.time() - self.choreography_start_time) if self.choreography_start_time else 0,
                'total_duration': self.active_choreography.total_duration_ms / 1000.0 if self.active_choreography else 0,
                'progress': 0.0
            },
            'available_choreographies': list(self.choreography_library.keys()),
            'current_servo_positions': dict(self.current_positions),
            'performance_metrics': dict(self.performance_metrics),
            'interpolation_rate_hz': self.interpolation_rate_hz
        }

        # Calculate progress
        if self.active_choreography and self.choreography_start_time:
            elapsed = time.time() - self.choreography_start_time
            total = self.active_choreography.total_duration_ms / 1000.0
            status['active_choreography']['progress'] = min(elapsed / total, 1.0) * 100

        return status

    def list_choreographies_by_personality(self, personality: MovementPersonality) -> List[str]:
        """Get list of choreographies matching a specific personality"""
        return [name for name, choreo in self.choreography_library.items()
                if choreo.personality == personality]

    def get_choreography_info(self, choreography_name: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about a choreography"""
        if choreography_name not in self.choreography_library:
            return None

        choreo = self.choreography_library[choreography_name]
        return {
            'name': choreo.name,
            'description': choreo.description,
            'personality': choreo.personality.value,
            'emotional_intensity': choreo.emotional_intensity,
            'duration_seconds': choreo.total_duration_ms / 1000.0,
            'priority': choreo.priority,
            'allows_interruption': choreo.allows_interruption,
            'requires_precise_timing': choreo.requires_precise_timing,
            'star_wars_reference': choreo.star_wars_reference,
            'canon_accuracy': choreo.canon_accuracy,
            'step_count': len(choreo.steps),
            'audio_sync_points': choreo.audio_sync_points,
            'visual_focus_points': choreo.visual_focus_points
        }


def main():
    """Demonstrate the Enhanced Choreographer"""
    print("🎭 R2D2 Enhanced Choreographer System")
    print("=" * 50)

    try:
        # Initialize servo controller
        from maestro_enhanced_controller import EnhancedMaestroController
        servo_controller = EnhancedMaestroController(auto_detect=True)

        # Initialize choreographer
        choreographer = R2D2EnhancedChoreographer(servo_controller)

        # Show available choreographies
        status = choreographer.get_choreography_status()
        print(f"\n📋 Available Choreographies ({len(status['available_choreographies'])}):")
        for choreo_name in status['available_choreographies']:
            info = choreographer.get_choreography_info(choreo_name)
            if info:
                print(f"   • {info['name']}")
                print(f"     {info['description']}")
                print(f"     Duration: {info['duration_seconds']:.1f}s, Personality: {info['personality']}")
                print(f"     Canon: {info['star_wars_reference']}")
                print()

        print("🎪 Enhanced choreographer ready for R2D2 authentic movement!")

    except Exception as e:
        logger.error(f"Demo error: {e}")


if __name__ == "__main__":
    main()