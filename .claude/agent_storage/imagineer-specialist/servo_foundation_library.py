#!/usr/bin/env python3
"""
Servo Foundation Library for R2D2 Motion Systems
================================================

Foundational servo control library that provides Disney-quality motion control
using the AdaFruit ServoKit hardware. This library implements the core motion
primitives needed for character animation and serves as the base for all
higher-level motion systems.

Features:
- ServoKit integration for reliable hardware control
- Disney-quality easing functions and motion curves
- Multi-servo coordination with precise timing
- Emergency stop and safety systems
- Motion keyframes and sequence management
- Character-appropriate motion parameters

Author: Imagineer Specialist Agent
Target: NVIDIA Orin Nano R2D2 Systems
Hardware: AdaFruit ServoKit (PCA9685-based)
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

try:
    from adafruit_servokit import ServoKit
    SERVOKIT_AVAILABLE = True
except (ImportError, Exception) as e:
    SERVOKIT_AVAILABLE = False
    logging.warning(f"ServoKit not available ({e}). Using simulation mode.")

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EasingType(Enum):
    """Disney-quality easing functions for natural motion"""
    LINEAR = "linear"
    EASE_IN = "ease_in"
    EASE_OUT = "ease_out"
    EASE_IN_OUT = "ease_in_out"
    EASE_IN_CUBIC = "ease_in_cubic"
    EASE_OUT_CUBIC = "ease_out_cubic"
    EASE_IN_OUT_CUBIC = "ease_in_out_cubic"
    EASE_IN_QUART = "ease_in_quart"
    EASE_OUT_QUART = "ease_out_quart"
    EASE_IN_OUT_QUART = "ease_in_out_quart"
    EASE_IN_BACK = "ease_in_back"
    EASE_OUT_BACK = "ease_out_back"
    EASE_IN_OUT_BACK = "ease_in_out_back"
    BOUNCE_OUT = "bounce_out"
    ELASTIC_OUT = "elastic_out"

class MotionState(Enum):
    """Motion execution states"""
    IDLE = "idle"
    MOVING = "moving"
    PAUSED = "paused"
    EMERGENCY_STOP = "emergency_stop"
    ERROR = "error"

@dataclass
class ServoConfig:
    """Configuration for individual servo channels"""
    channel: int
    min_angle: float = 0.0
    max_angle: float = 180.0
    center_angle: float = 90.0
    speed_limit: float = 180.0  # degrees per second
    acceleration_limit: float = 360.0  # degrees per second squared
    name: str = ""
    enabled: bool = True

@dataclass
class MotionKeyframe:
    """Single keyframe for servo motion"""
    channel: int
    angle: float
    timestamp: float
    easing: EasingType = EasingType.EASE_IN_OUT_CUBIC
    duration: float = 1.0
    hold_time: float = 0.0

@dataclass
class ServoSequence:
    """Complete motion sequence for multiple servos"""
    name: str
    keyframes: List[MotionKeyframe]
    total_duration: float
    loop: bool = False
    priority: int = 1

class DisneyEasingFunctions:
    """Implementation of Disney-quality easing functions"""

    @staticmethod
    def linear(t: float) -> float:
        """Linear interpolation"""
        return t

    @staticmethod
    def ease_in(t: float) -> float:
        """Quadratic ease in"""
        return t * t

    @staticmethod
    def ease_out(t: float) -> float:
        """Quadratic ease out"""
        return 1 - (1 - t) * (1 - t)

    @staticmethod
    def ease_in_out(t: float) -> float:
        """Quadratic ease in-out"""
        if t < 0.5:
            return 2 * t * t
        return 1 - pow(-2 * t + 2, 2) / 2

    @staticmethod
    def ease_in_cubic(t: float) -> float:
        """Cubic ease in"""
        return t * t * t

    @staticmethod
    def ease_out_cubic(t: float) -> float:
        """Cubic ease out"""
        return 1 - pow(1 - t, 3)

    @staticmethod
    def ease_in_out_cubic(t: float) -> float:
        """Cubic ease in-out"""
        if t < 0.5:
            return 4 * t * t * t
        return 1 - pow(-2 * t + 2, 3) / 2

    @staticmethod
    def ease_in_quart(t: float) -> float:
        """Quartic ease in"""
        return t * t * t * t

    @staticmethod
    def ease_out_quart(t: float) -> float:
        """Quartic ease out"""
        return 1 - pow(1 - t, 4)

    @staticmethod
    def ease_in_out_quart(t: float) -> float:
        """Quartic ease in-out"""
        if t < 0.5:
            return 8 * t * t * t * t
        return 1 - pow(-2 * t + 2, 4) / 2

    @staticmethod
    def ease_in_back(t: float) -> float:
        """Back ease in"""
        c1 = 1.70158
        c3 = c1 + 1
        return c3 * t * t * t - c1 * t * t

    @staticmethod
    def ease_out_back(t: float) -> float:
        """Back ease out"""
        c1 = 1.70158
        c3 = c1 + 1
        return 1 + c3 * pow(t - 1, 3) + c1 * pow(t - 1, 2)

    @staticmethod
    def ease_in_out_back(t: float) -> float:
        """Back ease in-out"""
        c1 = 1.70158
        c2 = c1 * 1.525
        if t < 0.5:
            return (pow(2 * t, 2) * ((c2 + 1) * 2 * t - c2)) / 2
        return (pow(2 * t - 2, 2) * ((c2 + 1) * (t * 2 - 2) + c2) + 2) / 2

    @staticmethod
    def bounce_out(t: float) -> float:
        """Bounce ease out"""
        n1 = 7.5625
        d1 = 2.75
        if t < 1 / d1:
            return n1 * t * t
        elif t < 2 / d1:
            t -= 1.5 / d1
            return n1 * t * t + 0.75
        elif t < 2.5 / d1:
            t -= 2.25 / d1
            return n1 * t * t + 0.9375
        else:
            t -= 2.625 / d1
            return n1 * t * t + 0.984375

    @staticmethod
    def elastic_out(t: float) -> float:
        """Elastic ease out"""
        c4 = (2 * math.pi) / 3
        if t == 0:
            return 0
        elif t == 1:
            return 1
        else:
            return pow(2, -10 * t) * math.sin((t * 10 - 0.75) * c4) + 1

    @staticmethod
    def get_easing_function(easing_type: EasingType) -> Callable[[float], float]:
        """Get easing function by type"""
        easing_map = {
            EasingType.LINEAR: DisneyEasingFunctions.linear,
            EasingType.EASE_IN: DisneyEasingFunctions.ease_in,
            EasingType.EASE_OUT: DisneyEasingFunctions.ease_out,
            EasingType.EASE_IN_OUT: DisneyEasingFunctions.ease_in_out,
            EasingType.EASE_IN_CUBIC: DisneyEasingFunctions.ease_in_cubic,
            EasingType.EASE_OUT_CUBIC: DisneyEasingFunctions.ease_out_cubic,
            EasingType.EASE_IN_OUT_CUBIC: DisneyEasingFunctions.ease_in_out_cubic,
            EasingType.EASE_IN_QUART: DisneyEasingFunctions.ease_in_quart,
            EasingType.EASE_OUT_QUART: DisneyEasingFunctions.ease_out_quart,
            EasingType.EASE_IN_OUT_QUART: DisneyEasingFunctions.ease_in_out_quart,
            EasingType.EASE_IN_BACK: DisneyEasingFunctions.ease_in_back,
            EasingType.EASE_OUT_BACK: DisneyEasingFunctions.ease_out_back,
            EasingType.EASE_IN_OUT_BACK: DisneyEasingFunctions.ease_in_out_back,
            EasingType.BOUNCE_OUT: DisneyEasingFunctions.bounce_out,
            EasingType.ELASTIC_OUT: DisneyEasingFunctions.elastic_out
        }
        return easing_map.get(easing_type, DisneyEasingFunctions.ease_in_out_cubic)

class DisneyServoController:
    """Disney-quality servo controller with advanced motion capabilities"""

    def __init__(self, servo_configs: List[ServoConfig], kit_address: int = 0x40):
        self.servo_configs = {config.channel: config for config in servo_configs}
        self.motion_state = MotionState.IDLE
        self.current_angles = {}
        self.target_angles = {}
        self.motion_thread = None
        self.emergency_stop = False
        self.running = False

        # Hardware initialization
        if SERVOKIT_AVAILABLE:
            try:
                self.kit = ServoKit(channels=16, address=kit_address)
                logger.info(f"ServoKit initialized at address 0x{kit_address:02x}")
            except Exception as e:
                logger.error(f"Failed to initialize ServoKit: {e}")
                self.kit = None
        else:
            self.kit = None
            logger.warning("ServoKit not available. Running in simulation mode.")

        # Initialize servo positions
        for channel, config in self.servo_configs.items():
            self.current_angles[channel] = config.center_angle
            self.target_angles[channel] = config.center_angle

            if self.kit and config.enabled:
                try:
                    self.kit.servo[channel].angle = config.center_angle
                except Exception as e:
                    logger.error(f"Failed to initialize servo {channel}: {e}")

        # Motion control thread
        self.motion_lock = threading.Lock()
        self.active_sequences = []
        self.motion_update_rate = 50  # Hz - Disney-quality smoothness

    def start_motion_control(self):
        """Start the motion control thread"""
        if not self.running:
            self.running = True
            self.motion_thread = threading.Thread(target=self._motion_control_loop, daemon=True)
            self.motion_thread.start()
            logger.info("Motion control thread started")

    def stop_motion_control(self):
        """Stop the motion control thread"""
        self.running = False
        if self.motion_thread:
            self.motion_thread.join(timeout=2.0)
        logger.info("Motion control thread stopped")

    def emergency_stop_all(self):
        """Emergency stop all servo motion"""
        self.emergency_stop = True
        self.motion_state = MotionState.EMERGENCY_STOP
        with self.motion_lock:
            self.active_sequences.clear()
        logger.warning("EMERGENCY STOP ACTIVATED")

    def reset_emergency_stop(self):
        """Reset emergency stop state"""
        self.emergency_stop = False
        self.motion_state = MotionState.IDLE
        logger.info("Emergency stop reset")

    def move_servo_to_angle(self, channel: int, angle: float, duration: float = 1.0,
                           easing: EasingType = EasingType.EASE_IN_OUT_CUBIC):
        """Move single servo to target angle with Disney-quality easing"""
        if channel not in self.servo_configs:
            logger.error(f"Servo channel {channel} not configured")
            return False

        config = self.servo_configs[channel]
        if not config.enabled:
            logger.warning(f"Servo channel {channel} is disabled")
            return False

        # Clamp angle to servo limits
        angle = max(config.min_angle, min(config.max_angle, angle))

        # Create single keyframe motion
        keyframe = MotionKeyframe(
            channel=channel,
            angle=angle,
            timestamp=time.time(),
            duration=duration,
            easing=easing
        )

        sequence = ServoSequence(
            name=f"single_servo_{channel}",
            keyframes=[keyframe],
            total_duration=duration
        )

        return self.execute_sequence(sequence)

    def execute_sequence(self, sequence: ServoSequence) -> bool:
        """Execute a complete motion sequence"""
        if self.emergency_stop:
            logger.warning("Cannot execute sequence: Emergency stop active")
            return False

        with self.motion_lock:
            self.active_sequences.append(sequence)

        self.motion_state = MotionState.MOVING
        logger.info(f"Executing sequence: {sequence.name}")
        return True

    def _motion_control_loop(self):
        """Main motion control loop - runs at high frequency for smooth motion"""
        dt = 1.0 / self.motion_update_rate

        while self.running:
            if self.emergency_stop:
                time.sleep(dt)
                continue

            current_time = time.time()

            with self.motion_lock:
                # Process all active sequences
                completed_sequences = []

                for sequence in self.active_sequences:
                    sequence_complete = True

                    for keyframe in sequence.keyframes:
                        elapsed = current_time - keyframe.timestamp

                        if elapsed < 0:
                            # Keyframe hasn't started yet
                            sequence_complete = False
                            continue
                        elif elapsed > keyframe.duration:
                            # Keyframe is complete
                            continue
                        else:
                            # Keyframe is in progress
                            sequence_complete = False
                            progress = elapsed / keyframe.duration

                            # Apply easing function
                            easing_func = DisneyEasingFunctions.get_easing_function(keyframe.easing)
                            eased_progress = easing_func(progress)

                            # Calculate current angle
                            start_angle = self.current_angles.get(keyframe.channel, 90.0)
                            angle_delta = keyframe.angle - start_angle
                            current_angle = start_angle + (angle_delta * eased_progress)

                            # Update servo position
                            self._set_servo_angle(keyframe.channel, current_angle)

                    if sequence_complete:
                        completed_sequences.append(sequence)

                # Remove completed sequences
                for completed in completed_sequences:
                    self.active_sequences.remove(completed)
                    logger.info(f"Sequence completed: {completed.name}")

            # Update motion state
            if not self.active_sequences and self.motion_state == MotionState.MOVING:
                self.motion_state = MotionState.IDLE

            time.sleep(dt)

    def _set_servo_angle(self, channel: int, angle: float):
        """Set servo angle with safety checks"""
        if channel not in self.servo_configs:
            return

        config = self.servo_configs[channel]
        if not config.enabled:
            return

        # Clamp to limits
        angle = max(config.min_angle, min(config.max_angle, angle))

        # Update current position
        self.current_angles[channel] = angle

        # Send to hardware
        if self.kit:
            try:
                self.kit.servo[channel].angle = angle
            except Exception as e:
                logger.error(f"Failed to set servo {channel} angle: {e}")

    def get_servo_angle(self, channel: int) -> Optional[float]:
        """Get current servo angle"""
        return self.current_angles.get(channel)

    def is_moving(self) -> bool:
        """Check if any servos are currently moving"""
        return self.motion_state == MotionState.MOVING

    def get_motion_state(self) -> MotionState:
        """Get current motion state"""
        return self.motion_state

    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get motion controller performance metrics"""
        return {
            'motion_state': self.motion_state.value,
            'active_sequences': len(self.active_sequences),
            'configured_servos': len(self.servo_configs),
            'enabled_servos': sum(1 for config in self.servo_configs.values() if config.enabled),
            'hardware_available': self.kit is not None,
            'update_rate_hz': self.motion_update_rate,
            'emergency_stop_active': self.emergency_stop
        }

# R2D2-specific servo configurations
def create_r2d2_servo_configs() -> List[ServoConfig]:
    """Create standard R2D2 servo configurations"""
    configs = [
        # Head rotation and tilt
        ServoConfig(channel=0, min_angle=0, max_angle=180, center_angle=90,
                   speed_limit=120, name="head_rotation"),
        ServoConfig(channel=1, min_angle=45, max_angle=135, center_angle=90,
                   speed_limit=90, name="head_tilt"),

        # Eye movement (if equipped)
        ServoConfig(channel=2, min_angle=60, max_angle=120, center_angle=90,
                   speed_limit=180, name="eye_horizontal"),
        ServoConfig(channel=3, min_angle=70, max_angle=110, center_angle=90,
                   speed_limit=180, name="eye_vertical"),

        # Utility arm and tools
        ServoConfig(channel=4, min_angle=0, max_angle=180, center_angle=45,
                   speed_limit=90, name="utility_arm_rotation"),
        ServoConfig(channel=5, min_angle=30, max_angle=150, center_angle=90,
                   speed_limit=60, name="utility_arm_extension"),
        ServoConfig(channel=6, min_angle=0, max_angle=90, center_angle=0,
                   speed_limit=120, name="tool_gripper"),
        ServoConfig(channel=7, min_angle=0, max_angle=180, center_angle=90,
                   speed_limit=150, name="scanner_rotation"),

        # Dome panels (8 panels)
        ServoConfig(channel=8, min_angle=0, max_angle=90, center_angle=0,
                   speed_limit=90, name="dome_panel_1"),
        ServoConfig(channel=9, min_angle=0, max_angle=90, center_angle=0,
                   speed_limit=90, name="dome_panel_2"),
        ServoConfig(channel=10, min_angle=0, max_angle=90, center_angle=0,
                   speed_limit=90, name="dome_panel_3"),
        ServoConfig(channel=11, min_angle=0, max_angle=90, center_angle=0,
                   speed_limit=90, name="dome_panel_4"),
        ServoConfig(channel=12, min_angle=0, max_angle=90, center_angle=0,
                   speed_limit=90, name="dome_panel_5"),
        ServoConfig(channel=13, min_angle=0, max_angle=90, center_angle=0,
                   speed_limit=90, name="dome_panel_6"),
        ServoConfig(channel=14, min_angle=0, max_angle=90, center_angle=0,
                   speed_limit=90, name="dome_panel_7"),
        ServoConfig(channel=15, min_angle=0, max_angle=90, center_angle=0,
                   speed_limit=90, name="dome_panel_8")
    ]
    return configs

def demo_servo_foundation():
    """Demonstration of servo foundation library capabilities"""
    print("🎭 Disney Servo Foundation Library Demo")
    print("=" * 50)

    # Create R2D2 servo configuration
    servo_configs = create_r2d2_servo_configs()

    # Initialize servo controller
    controller = DisneyServoController(servo_configs)
    controller.start_motion_control()

    try:
        # Demo 1: Head movement sequence
        print("Demo 1: Head movement sequence")
        controller.move_servo_to_angle(0, 45, 2.0, EasingType.EASE_IN_OUT_CUBIC)  # Head left
        time.sleep(2.5)
        controller.move_servo_to_angle(0, 135, 2.0, EasingType.EASE_IN_OUT_CUBIC)  # Head right
        time.sleep(2.5)
        controller.move_servo_to_angle(0, 90, 1.5, EasingType.EASE_OUT_BACK)  # Head center
        time.sleep(2.0)

        # Demo 2: Complex multi-servo sequence
        print("Demo 2: Multi-servo dome panel sequence")
        panel_sequence = ServoSequence(
            name="dome_panel_wave",
            keyframes=[
                MotionKeyframe(8, 45, time.time() + 0.0, EasingType.EASE_OUT_CUBIC, 0.5),
                MotionKeyframe(9, 45, time.time() + 0.2, EasingType.EASE_OUT_CUBIC, 0.5),
                MotionKeyframe(10, 45, time.time() + 0.4, EasingType.EASE_OUT_CUBIC, 0.5),
                MotionKeyframe(11, 45, time.time() + 0.6, EasingType.EASE_OUT_CUBIC, 0.5),
                MotionKeyframe(8, 0, time.time() + 2.0, EasingType.EASE_IN_CUBIC, 0.5),
                MotionKeyframe(9, 0, time.time() + 2.2, EasingType.EASE_IN_CUBIC, 0.5),
                MotionKeyframe(10, 0, time.time() + 2.4, EasingType.EASE_IN_CUBIC, 0.5),
                MotionKeyframe(11, 0, time.time() + 2.6, EasingType.EASE_IN_CUBIC, 0.5),
            ],
            total_duration=3.5
        )
        controller.execute_sequence(panel_sequence)
        time.sleep(4.0)

        # Demo 3: Character personality motion
        print("Demo 3: Character personality motion")
        controller.move_servo_to_angle(1, 75, 1.0, EasingType.EASE_OUT_BACK)  # Head tilt curious
        controller.move_servo_to_angle(0, 75, 1.2, EasingType.EASE_IN_OUT_BACK)  # Head turn
        time.sleep(2.0)
        controller.move_servo_to_angle(1, 90, 0.8, EasingType.BOUNCE_OUT)  # Head return
        controller.move_servo_to_angle(0, 90, 1.0, EasingType.ELASTIC_OUT)  # Head center
        time.sleep(2.0)

        # Performance metrics
        metrics = controller.get_performance_metrics()
        print("\n--- Performance Metrics ---")
        print(f"Motion State: {metrics['motion_state']}")
        print(f"Active Sequences: {metrics['active_sequences']}")
        print(f"Configured Servos: {metrics['configured_servos']}")
        print(f"Hardware Available: {metrics['hardware_available']}")
        print(f"Update Rate: {metrics['update_rate_hz']} Hz")

    finally:
        controller.stop_motion_control()
        print("\nDemo completed")

if __name__ == "__main__":
    demo_servo_foundation()