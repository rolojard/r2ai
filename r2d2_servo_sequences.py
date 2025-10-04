#!/usr/bin/env python3
"""
R2D2 Servo Sequences - Authentic Star Wars Character Movements
============================================================

This module contains professionally crafted servo sequences that bring R2D2 to life
with authentic character movements based on the original films. Each sequence is
designed to convey R2D2's personality and emotional states through precise mechanical
movements that reflect the beloved droid's characteristics.

Features:
- Film-accurate movement patterns
- Emotional expression through servo positioning
- Contextual behaviors for different situations
- Smooth easing functions for natural movement
- Safety-conscious sequence design

Author: Expert Project Manager + Star Wars Specialist Agent
Hardware: Pololu Maestro Mini 12-Channel USB Servo Controller
"""

import time
import math
from typing import List, Dict, Tuple
from dataclasses import dataclass
from enum import Enum

# Import our enhanced controller
import sys
sys.path.append('/home/rolo/r2ai')
from maestro_enhanced_controller import ServoSequence, ServoSequenceStep

class R2D2EmotionalState(Enum):
    """R2D2's emotional and behavioral states"""
    CURIOUS = "curious"
    EXCITED = "excited"
    ALERT = "alert"
    WORRIED = "worried"
    HAPPY = "happy"
    SEARCHING = "searching"
    SLEEPING = "sleeping"
    STARTLED = "startled"
    CONFIDENT = "confident"
    CAUTIOUS = "cautious"

class R2D2ServoChannels:
    """Standard R2D2 servo channel assignments"""
    DOME_ROTATION = 0       # Main dome rotation (360°)
    HEAD_TILT = 1          # Head tilt mechanism
    PERISCOPE = 2          # Periscope raise/lower
    RADAR_EYE = 3          # Radar eye rotation
    UTILITY_ARM_LEFT = 4    # Left utility arm
    UTILITY_ARM_RIGHT = 5   # Right utility arm
    DOME_PANEL_FRONT = 6    # Front dome panel
    DOME_PANEL_LEFT = 7     # Left dome panel
    DOME_PANEL_RIGHT = 8    # Right dome panel
    DOME_PANEL_BACK = 9     # Back dome panel
    BODY_DOOR_LEFT = 10     # Left body access door
    BODY_DOOR_RIGHT = 11    # Right body access door

class R2D2SequenceLibrary:
    """Library of authentic R2D2 servo sequences"""

    @staticmethod
    def create_greeting_sequence() -> ServoSequence:
        """
        Classic R2D2 greeting sequence - excited and friendly
        Mimics his behavior when meeting friends like Luke or Leia
        """
        steps = [
            # Initial excited dome rotation
            ServoSequenceStep(
                channel=R2D2ServoChannels.DOME_ROTATION,
                position=7200,  # 45° right
                duration_ms=600,
                easing_type="ease_out",
                hold_time_ms=100
            ),

            # Quick head tilt - curious/excited
            ServoSequenceStep(
                channel=R2D2ServoChannels.HEAD_TILT,
                position=7000,  # Slight up tilt
                duration_ms=400,
                easing_type="ease_in_out",
                hold_time_ms=200
            ),

            # Dome back to center with bounce
            ServoSequenceStep(
                channel=R2D2ServoChannels.DOME_ROTATION,
                position=6000,  # Center
                duration_ms=800,
                easing_type="ease_out_back",
                hold_time_ms=150
            ),

            # Periscope up - "Hello there!"
            ServoSequenceStep(
                channel=R2D2ServoChannels.PERISCOPE,
                position=7500,  # Extended
                duration_ms=700,
                easing_type="ease_out_cubic",
                hold_time_ms=300
            ),

            # Left utility arm wave
            ServoSequenceStep(
                channel=R2D2ServoChannels.UTILITY_ARM_LEFT,
                position=7800,  # Extended
                duration_ms=500,
                easing_type="ease_out",
                hold_time_ms=200
            ),

            # Quick dome wiggle - excitement
            ServoSequenceStep(
                channel=R2D2ServoChannels.DOME_ROTATION,
                position=6800,  # Right
                duration_ms=300,
                easing_type="linear",
                hold_time_ms=100
            ),
            ServoSequenceStep(
                channel=R2D2ServoChannels.DOME_ROTATION,
                position=5200,  # Left
                duration_ms=400,
                easing_type="linear",
                hold_time_ms=100
            ),
            ServoSequenceStep(
                channel=R2D2ServoChannels.DOME_ROTATION,
                position=6000,  # Center
                duration_ms=300,
                easing_type="ease_out",
                hold_time_ms=200
            ),

            # Return to rest position
            ServoSequenceStep(
                channel=R2D2ServoChannels.PERISCOPE,
                position=4000,  # Retracted
                duration_ms=600,
                easing_type="ease_in_cubic",
                hold_time_ms=100
            ),
            ServoSequenceStep(
                channel=R2D2ServoChannels.UTILITY_ARM_LEFT,
                position=4000,  # Retracted
                duration_ms=700,
                easing_type="ease_in_out",
                hold_time_ms=100
            ),
            ServoSequenceStep(
                channel=R2D2ServoChannels.HEAD_TILT,
                position=6000,  # Level
                duration_ms=500,
                easing_type="ease_in_out",
                hold_time_ms=0
            )
        ]

        return ServoSequence(
            name="r2d2_greeting",
            description="Authentic R2D2 greeting sequence with excited dome movement and friendly gestures",
            steps=steps,
            total_duration_ms=6400,
            loop_count=1,
            r2d2_behavior="greeting"
        )

    @staticmethod
    def create_search_sequence() -> ServoSequence:
        """
        R2D2 search pattern - systematic and determined
        Based on his behavior when looking for Luke or scanning for threats
        """
        steps = [
            # Periscope up for better view
            ServoSequenceStep(
                channel=R2D2ServoChannels.PERISCOPE,
                position=7800,
                duration_ms=800,
                easing_type="ease_out_cubic",
                hold_time_ms=300
            ),

            # Systematic dome rotation - left sweep
            ServoSequenceStep(
                channel=R2D2ServoChannels.DOME_ROTATION,
                position=4000,  # 90° left
                duration_ms=1500,
                easing_type="linear",
                hold_time_ms=500
            ),

            # Head tilt up - scanning high
            ServoSequenceStep(
                channel=R2D2ServoChannels.HEAD_TILT,
                position=7200,
                duration_ms=600,
                easing_type="ease_in_out",
                hold_time_ms=400
            ),

            # Continue dome rotation - center
            ServoSequenceStep(
                channel=R2D2ServoChannels.DOME_ROTATION,
                position=6000,  # Center
                duration_ms=1200,
                easing_type="linear",
                hold_time_ms=300
            ),

            # Head level for medium scan
            ServoSequenceStep(
                channel=R2D2ServoChannels.HEAD_TILT,
                position=6000,
                duration_ms=500,
                easing_type="ease_in_out",
                hold_time_ms=300
            ),

            # Right sweep
            ServoSequenceStep(
                channel=R2D2ServoChannels.DOME_ROTATION,
                position=8000,  # 90° right
                duration_ms=1200,
                easing_type="linear",
                hold_time_ms=500
            ),

            # Head tilt down - scanning low
            ServoSequenceStep(
                channel=R2D2ServoChannels.HEAD_TILT,
                position=4800,
                duration_ms=600,
                easing_type="ease_in_out",
                hold_time_ms=400
            ),

            # Return to center position
            ServoSequenceStep(
                channel=R2D2ServoChannels.DOME_ROTATION,
                position=6000,
                duration_ms=1000,
                easing_type="ease_in_out",
                hold_time_ms=200
            ),
            ServoSequenceStep(
                channel=R2D2ServoChannels.HEAD_TILT,
                position=6000,
                duration_ms=600,
                easing_type="ease_in_out",
                hold_time_ms=200
            ),

            # Periscope retract
            ServoSequenceStep(
                channel=R2D2ServoChannels.PERISCOPE,
                position=4000,
                duration_ms=700,
                easing_type="ease_in_cubic",
                hold_time_ms=0
            )
        ]

        return ServoSequence(
            name="search_pattern",
            description="Systematic search pattern with periscope and methodical dome rotation",
            steps=steps,
            total_duration_ms=9400,
            loop_count=1,
            r2d2_behavior="searching"
        )

    @staticmethod
    def create_alert_sequence() -> ServoSequence:
        """
        R2D2 alert/warning sequence - urgent and attention-grabbing
        Based on his behavior when detecting danger or trying to warn allies
        """
        steps = [
            # Rapid dome rotation - urgent attention getting
            ServoSequenceStep(
                channel=R2D2ServoChannels.DOME_ROTATION,
                position=7500,
                duration_ms=200,
                easing_type="linear",
                hold_time_ms=50
            ),
            ServoSequenceStep(
                channel=R2D2ServoChannels.DOME_ROTATION,
                position=4500,
                duration_ms=300,
                easing_type="linear",
                hold_time_ms=50
            ),
            ServoSequenceStep(
                channel=R2D2ServoChannels.DOME_ROTATION,
                position=7500,
                duration_ms=250,
                easing_type="linear",
                hold_time_ms=50
            ),

            # Head tilt - emphatic gesture
            ServoSequenceStep(
                channel=R2D2ServoChannels.HEAD_TILT,
                position=7800,  # Strong upward tilt
                duration_ms=400,
                easing_type="ease_out",
                hold_time_ms=200
            ),

            # Both utility arms out - "Pay attention!"
            ServoSequenceStep(
                channel=R2D2ServoChannels.UTILITY_ARM_LEFT,
                position=7800,
                duration_ms=300,
                easing_type="ease_out",
                hold_time_ms=100
            ),
            ServoSequenceStep(
                channel=R2D2ServoChannels.UTILITY_ARM_RIGHT,
                position=7800,
                duration_ms=300,
                easing_type="ease_out",
                hold_time_ms=400
            ),

            # Periscope rapid extension - urgent scanning
            ServoSequenceStep(
                channel=R2D2ServoChannels.PERISCOPE,
                position=8000,
                duration_ms=400,
                easing_type="ease_out",
                hold_time_ms=300
            ),

            # Rapid dome side-to-side - agitated
            ServoSequenceStep(
                channel=R2D2ServoChannels.DOME_ROTATION,
                position=4000,
                duration_ms=200,
                easing_type="linear",
                hold_time_ms=100
            ),
            ServoSequenceStep(
                channel=R2D2ServoChannels.DOME_ROTATION,
                position=8000,
                duration_ms=300,
                easing_type="linear",
                hold_time_ms=100
            ),
            ServoSequenceStep(
                channel=R2D2ServoChannels.DOME_ROTATION,
                position=6000,
                duration_ms=200,
                easing_type="ease_out",
                hold_time_ms=200
            ),

            # Return to neutral but ready position
            ServoSequenceStep(
                channel=R2D2ServoChannels.HEAD_TILT,
                position=6500,  # Slightly up - alert
                duration_ms=500,
                easing_type="ease_in_out",
                hold_time_ms=100
            ),
            ServoSequenceStep(
                channel=R2D2ServoChannels.UTILITY_ARM_LEFT,
                position=4000,
                duration_ms=600,
                easing_type="ease_in",
                hold_time_ms=100
            ),
            ServoSequenceStep(
                channel=R2D2ServoChannels.UTILITY_ARM_RIGHT,
                position=4000,
                duration_ms=600,
                easing_type="ease_in",
                hold_time_ms=100
            ),
            ServoSequenceStep(
                channel=R2D2ServoChannels.PERISCOPE,
                position=6000,  # Partially extended - still alert
                duration_ms=400,
                easing_type="ease_in_out",
                hold_time_ms=0
            )
        ]

        return ServoSequence(
            name="alert_warning",
            description="Urgent alert sequence with rapid movements to grab attention",
            steps=steps,
            total_duration_ms=5300,
            loop_count=1,
            r2d2_behavior="alert"
        )

    @staticmethod
    def create_excited_sequence() -> ServoSequence:
        """
        R2D2 excited/happy sequence - pure joy and enthusiasm
        Based on his behavior when reunited with friends or discovering something amazing
        """
        steps = [
            # Excited dome spin - multiple directions
            ServoSequenceStep(
                channel=R2D2ServoChannels.DOME_ROTATION,
                position=8000,  # Right
                duration_ms=400,
                easing_type="ease_out",
                hold_time_ms=50
            ),
            ServoSequenceStep(
                channel=R2D2ServoChannels.DOME_ROTATION,
                position=4000,  # Left
                duration_ms=500,
                easing_type="ease_in_out",
                hold_time_ms=50
            ),
            ServoSequenceStep(
                channel=R2D2ServoChannels.DOME_ROTATION,
                position=7500,  # Right again
                duration_ms=400,
                easing_type="ease_out",
                hold_time_ms=100
            ),

            # Happy head bob
            ServoSequenceStep(
                channel=R2D2ServoChannels.HEAD_TILT,
                position=5000,  # Down
                duration_ms=250,
                easing_type="ease_in",
                hold_time_ms=100
            ),
            ServoSequenceStep(
                channel=R2D2ServoChannels.HEAD_TILT,
                position=7000,  # Up
                duration_ms=300,
                easing_type="ease_out",
                hold_time_ms=100
            ),
            ServoSequenceStep(
                channel=R2D2ServoChannels.HEAD_TILT,
                position=5500,  # Down
                duration_ms=250,
                easing_type="ease_in",
                hold_time_ms=100
            ),
            ServoSequenceStep(
                channel=R2D2ServoChannels.HEAD_TILT,
                position=6500,  # Up
                duration_ms=300,
                easing_type="ease_out_back",
                hold_time_ms=200
            ),

            # Both arms celebration
            ServoSequenceStep(
                channel=R2D2ServoChannels.UTILITY_ARM_LEFT,
                position=8000,
                duration_ms=400,
                easing_type="ease_out",
                hold_time_ms=200
            ),
            ServoSequenceStep(
                channel=R2D2ServoChannels.UTILITY_ARM_RIGHT,
                position=8000,
                duration_ms=400,
                easing_type="ease_out",
                hold_time_ms=300
            ),

            # Periscope celebration pop
            ServoSequenceStep(
                channel=R2D2ServoChannels.PERISCOPE,
                position=8000,
                duration_ms=300,
                easing_type="ease_out",
                hold_time_ms=200
            ),

            # Final happy dome wiggle
            ServoSequenceStep(
                channel=R2D2ServoChannels.DOME_ROTATION,
                position=6000,  # Center
                duration_ms=600,
                easing_type="ease_out_back",
                hold_time_ms=300
            ),

            # Settle to happy rest position
            ServoSequenceStep(
                channel=R2D2ServoChannels.HEAD_TILT,
                position=6200,  # Slightly up - happy
                duration_ms=500,
                easing_type="ease_in_out",
                hold_time_ms=100
            ),
            ServoSequenceStep(
                channel=R2D2ServoChannels.UTILITY_ARM_LEFT,
                position=4000,
                duration_ms=700,
                easing_type="ease_in_out",
                hold_time_ms=100
            ),
            ServoSequenceStep(
                channel=R2D2ServoChannels.UTILITY_ARM_RIGHT,
                position=4000,
                duration_ms=700,
                easing_type="ease_in_out",
                hold_time_ms=100
            ),
            ServoSequenceStep(
                channel=R2D2ServoChannels.PERISCOPE,
                position=4000,
                duration_ms=600,
                easing_type="ease_in_cubic",
                hold_time_ms=0
            )
        ]

        return ServoSequence(
            name="excited_celebration",
            description="Enthusiastic celebration sequence with multiple servo coordination",
            steps=steps,
            total_duration_ms=6750,
            loop_count=1,
            r2d2_behavior="excited"
        )

    @staticmethod
    def create_cautious_sequence() -> ServoSequence:
        """
        R2D2 cautious/worried sequence - tentative and careful
        Based on his behavior in dangerous situations or when approaching unknowns
        """
        steps = [
            # Slow, careful periscope extension
            ServoSequenceStep(
                channel=R2D2ServoChannels.PERISCOPE,
                position=5500,  # Partially extended
                duration_ms=1200,
                easing_type="ease_in_out",
                hold_time_ms=400
            ),

            # Tentative dome movement - checking left
            ServoSequenceStep(
                channel=R2D2ServoChannels.DOME_ROTATION,
                position=5000,  # Slight left
                duration_ms=800,
                easing_type="ease_in_out",
                hold_time_ms=600
            ),

            # Worried head tilt
            ServoSequenceStep(
                channel=R2D2ServoChannels.HEAD_TILT,
                position=5200,  # Slightly down - worried
                duration_ms=700,
                easing_type="ease_in_out",
                hold_time_ms=400
            ),

            # Check right side cautiously
            ServoSequenceStep(
                channel=R2D2ServoChannels.DOME_ROTATION,
                position=7000,  # Right
                duration_ms=1000,
                easing_type="ease_in_out",
                hold_time_ms=600
            ),

            # Nervous utility arm extension - ready but careful
            ServoSequenceStep(
                channel=R2D2ServoChannels.UTILITY_ARM_LEFT,
                position=5500,  # Partially extended
                duration_ms=800,
                easing_type="ease_in_out",
                hold_time_ms=300
            ),

            # Return to center, still cautious
            ServoSequenceStep(
                channel=R2D2ServoChannels.DOME_ROTATION,
                position=6000,
                duration_ms=900,
                easing_type="ease_in_out",
                hold_time_ms=400
            ),

            # Slight head bob - uncertain
            ServoSequenceStep(
                channel=R2D2ServoChannels.HEAD_TILT,
                position=6200,
                duration_ms=500,
                easing_type="ease_in_out",
                hold_time_ms=200
            ),
            ServoSequenceStep(
                channel=R2D2ServoChannels.HEAD_TILT,
                position=5800,
                duration_ms=500,
                easing_type="ease_in_out",
                hold_time_ms=300
            ),

            # Retract cautiously - still ready to extend again
            ServoSequenceStep(
                channel=R2D2ServoChannels.PERISCOPE,
                position=4500,
                duration_ms=900,
                easing_type="ease_in_out",
                hold_time_ms=200
            ),
            ServoSequenceStep(
                channel=R2D2ServoChannels.UTILITY_ARM_LEFT,
                position=4200,
                duration_ms=700,
                easing_type="ease_in_out",
                hold_time_ms=100
            ),
            ServoSequenceStep(
                channel=R2D2ServoChannels.HEAD_TILT,
                position=6000,
                duration_ms=600,
                easing_type="ease_in_out",
                hold_time_ms=0
            )
        ]

        return ServoSequence(
            name="cautious_investigation",
            description="Careful, worried investigation sequence with tentative movements",
            steps=steps,
            total_duration_ms=9200,
            loop_count=1,
            r2d2_behavior="cautious"
        )

    @staticmethod
    def create_sleep_sequence() -> ServoSequence:
        """
        R2D2 sleep/power down sequence - gradual shutdown
        Based on his behavior when powering down or resting
        """
        steps = [
            # Slow periscope retraction
            ServoSequenceStep(
                channel=R2D2ServoChannels.PERISCOPE,
                position=3500,  # Fully retracted
                duration_ms=2000,
                easing_type="ease_in_cubic",
                hold_time_ms=300
            ),

            # Head slowly droops
            ServoSequenceStep(
                channel=R2D2ServoChannels.HEAD_TILT,
                position=4500,  # Down position
                duration_ms=1800,
                easing_type="ease_in_cubic",
                hold_time_ms=500
            ),

            # Utility arms retract slowly
            ServoSequenceStep(
                channel=R2D2ServoChannels.UTILITY_ARM_LEFT,
                position=3500,
                duration_ms=1500,
                easing_type="ease_in_out",
                hold_time_ms=200
            ),
            ServoSequenceStep(
                channel=R2D2ServoChannels.UTILITY_ARM_RIGHT,
                position=3500,
                duration_ms=1500,
                easing_type="ease_in_out",
                hold_time_ms=400
            ),

            # Dome settles to rest position
            ServoSequenceStep(
                channel=R2D2ServoChannels.DOME_ROTATION,
                position=6000,  # Centered
                duration_ms=1200,
                easing_type="ease_in_out",
                hold_time_ms=1000
            ),

            # Final settling - all systems down
            ServoSequenceStep(
                channel=R2D2ServoChannels.HEAD_TILT,
                position=4000,  # Lower
                duration_ms=1000,
                easing_type="ease_in_cubic",
                hold_time_ms=0
            )
        ]

        return ServoSequence(
            name="sleep_powerdown",
            description="Gradual power down sequence with slow, sleepy movements",
            steps=steps,
            total_duration_ms=8400,
            loop_count=1,
            r2d2_behavior="sleeping"
        )

    @staticmethod
    def create_wakeup_sequence() -> ServoSequence:
        """
        R2D2 wake up sequence - gradual activation
        Based on his behavior when powering up or being activated
        """
        steps = [
            # Slow head lift - coming online
            ServoSequenceStep(
                channel=R2D2ServoChannels.HEAD_TILT,
                position=5500,
                duration_ms=1500,
                easing_type="ease_out_cubic",
                hold_time_ms=400
            ),

            # Dome rotation - systems check
            ServoSequenceStep(
                channel=R2D2ServoChannels.DOME_ROTATION,
                position=5500,  # Slight left
                duration_ms=800,
                easing_type="ease_out",
                hold_time_ms=200
            ),
            ServoSequenceStep(
                channel=R2D2ServoChannels.DOME_ROTATION,
                position=6500,  # Slight right
                duration_ms=800,
                easing_type="ease_in_out",
                hold_time_ms=200
            ),
            ServoSequenceStep(
                channel=R2D2ServoChannels.DOME_ROTATION,
                position=6000,  # Center
                duration_ms=600,
                easing_type="ease_out",
                hold_time_ms=300
            ),

            # Head to normal position
            ServoSequenceStep(
                channel=R2D2ServoChannels.HEAD_TILT,
                position=6000,
                duration_ms=800,
                easing_type="ease_out",
                hold_time_ms=200
            ),

            # Periscope test extension
            ServoSequenceStep(
                channel=R2D2ServoChannels.PERISCOPE,
                position=6000,
                duration_ms=1000,
                easing_type="ease_out_cubic",
                hold_time_ms=300
            ),
            ServoSequenceStep(
                channel=R2D2ServoChannels.PERISCOPE,
                position=4000,
                duration_ms=700,
                easing_type="ease_in_out",
                hold_time_ms=200
            ),

            # Utility arm systems check
            ServoSequenceStep(
                channel=R2D2ServoChannels.UTILITY_ARM_LEFT,
                position=5000,
                duration_ms=600,
                easing_type="ease_out",
                hold_time_ms=200
            ),
            ServoSequenceStep(
                channel=R2D2ServoChannels.UTILITY_ARM_LEFT,
                position=4000,
                duration_ms=500,
                easing_type="ease_in",
                hold_time_ms=100
            ),

            # Final activation head nod - "I'm ready"
            ServoSequenceStep(
                channel=R2D2ServoChannels.HEAD_TILT,
                position=6500,
                duration_ms=400,
                easing_type="ease_out",
                hold_time_ms=200
            ),
            ServoSequenceStep(
                channel=R2D2ServoChannels.HEAD_TILT,
                position=6000,
                duration_ms=400,
                easing_type="ease_in",
                hold_time_ms=0
            )
        ]

        return ServoSequence(
            name="wakeup_activation",
            description="Gradual wake up sequence with system check movements",
            steps=steps,
            total_duration_ms=8500,
            loop_count=1,
            r2d2_behavior="confident"
        )

    @staticmethod
    def get_all_sequences() -> Dict[str, ServoSequence]:
        """Get all available R2D2 servo sequences"""
        return {
            "greeting": R2D2SequenceLibrary.create_greeting_sequence(),
            "search": R2D2SequenceLibrary.create_search_sequence(),
            "alert": R2D2SequenceLibrary.create_alert_sequence(),
            "excited": R2D2SequenceLibrary.create_excited_sequence(),
            "cautious": R2D2SequenceLibrary.create_cautious_sequence(),
            "sleep": R2D2SequenceLibrary.create_sleep_sequence(),
            "wakeup": R2D2SequenceLibrary.create_wakeup_sequence()
        }

    @staticmethod
    def create_quick_demo() -> ServoSequence:
        """Quick demonstration sequence showcasing key movements"""
        steps = [
            # Quick dome rotation
            ServoSequenceStep(R2D2ServoChannels.DOME_ROTATION, 7000, 800, "ease_out", 200),
            # Head tilt
            ServoSequenceStep(R2D2ServoChannels.HEAD_TILT, 6800, 600, "ease_in_out", 200),
            # Periscope up
            ServoSequenceStep(R2D2ServoChannels.PERISCOPE, 7000, 700, "ease_out", 300),
            # Utility arm
            ServoSequenceStep(R2D2ServoChannels.UTILITY_ARM_LEFT, 7000, 500, "ease_out", 200),
            # Return dome
            ServoSequenceStep(R2D2ServoChannels.DOME_ROTATION, 6000, 800, "ease_in_out", 200),
            # Return all to home
            ServoSequenceStep(R2D2ServoChannels.HEAD_TILT, 6000, 600, "ease_in_out", 100),
            ServoSequenceStep(R2D2ServoChannels.PERISCOPE, 4000, 700, "ease_in", 100),
            ServoSequenceStep(R2D2ServoChannels.UTILITY_ARM_LEFT, 4000, 600, "ease_in", 0)
        ]

        return ServoSequence(
            name="quick_demo",
            description="Quick demonstration of R2D2's primary movements",
            steps=steps,
            total_duration_ms=5200,
            loop_count=1,
            r2d2_behavior="confident"
        )

def demo_r2d2_sequences():
    """Demonstration of R2D2 servo sequences"""
    print("🤖 R2D2 Servo Sequences Library Demo")
    print("=" * 50)

    sequences = R2D2SequenceLibrary.get_all_sequences()

    for name, sequence in sequences.items():
        print(f"\n--- {sequence.name.upper()} ---")
        print(f"Description: {sequence.description}")
        print(f"Behavior: {sequence.r2d2_behavior}")
        print(f"Duration: {sequence.total_duration_ms/1000:.1f} seconds")
        print(f"Steps: {len(sequence.steps)}")

        # Show first few steps
        print("First few steps:")
        for i, step in enumerate(sequence.steps[:3]):
            channel_name = [name for name, val in vars(R2D2ServoChannels).items()
                          if not name.startswith('_') and val == step.channel][0]
            print(f"  {i+1}. {channel_name}: {step.position} ({step.duration_ms}ms)")

        if len(sequence.steps) > 3:
            print(f"  ... and {len(sequence.steps) - 3} more steps")

if __name__ == "__main__":
    demo_r2d2_sequences()