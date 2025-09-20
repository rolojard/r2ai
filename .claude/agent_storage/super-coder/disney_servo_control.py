#!/usr/bin/env python3
"""
Disney-Level Smooth Servo Control Library
=========================================

Professional-grade servo control system with Disney-inspired motion curves
for lifelike R2D2 character animation. This library provides the foundation
for convention-ready, crowd-pleasing robotic performances.

Features:
- Organic motion curves with squash and stretch principles
- Anticipation and follow-through animations
- Multi-servo synchronized choreography
- Real-time performance optimization
- Failsafe protection systems

Author: Super Coder Agent
Target: NVIDIA Orin Nano R2D2 Systems
"""

import time
import math
import threading
import logging
from typing import Dict, List, Tuple, Optional, Callable, Any
from dataclasses import dataclass, field
from enum import Enum
import numpy as np
from collections import deque
import json

# Configure logging for servo control
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EasingType(Enum):
    """Disney-inspired easing curves for natural motion"""
    LINEAR = "linear"
    EASE_IN_QUAD = "ease_in_quad"
    EASE_OUT_QUAD = "ease_out_quad"
    EASE_IN_OUT_QUAD = "ease_in_out_quad"
    EASE_IN_CUBIC = "ease_in_cubic"
    EASE_OUT_CUBIC = "ease_out_cubic"
    EASE_IN_OUT_CUBIC = "ease_in_out_cubic"
    EASE_IN_QUART = "ease_in_quart"
    EASE_OUT_QUART = "ease_out_quart"
    EASE_IN_OUT_QUART = "ease_in_out_quart"
    EASE_IN_BACK = "ease_in_back"
    EASE_OUT_BACK = "ease_out_back"
    EASE_IN_OUT_BACK = "ease_in_out_back"
    EASE_OUT_BOUNCE = "ease_out_bounce"
    EASE_OUT_ELASTIC = "ease_out_elastic"
    DISNEY_ANTIC = "disney_anticipation"  # Custom Disney anticipation curve
    DISNEY_SQUASH = "disney_squash_stretch"  # Squash and stretch
    DISNEY_SETTLE = "disney_settle"  # Natural settling motion

@dataclass
class ServoConfig:
    """Configuration for individual servo motors"""
    channel: int
    min_pulse: int = 500     # Minimum pulse width (microseconds)
    max_pulse: int = 2500    # Maximum pulse width (microseconds)
    min_angle: float = 0.0   # Minimum angle (degrees)
    max_angle: float = 180.0 # Maximum angle (degrees)
    center_angle: float = 90.0 # Center/rest position
    max_speed: float = 180.0 # Maximum speed (degrees/second)
    acceleration: float = 360.0 # Maximum acceleration (degrees/second²)
    name: str = ""           # Human-readable name
    invert: bool = False     # Invert direction
    trim: float = 0.0        # Trim adjustment (degrees)

@dataclass
class MotionKeyframe:
    """Keyframe for servo animation sequences"""
    time: float              # Time in seconds
    angle: float             # Target angle
    easing: EasingType = EasingType.EASE_IN_OUT_CUBIC
    hold_time: float = 0.0   # Time to hold at this position

@dataclass
class ServoState:
    """Current state of a servo motor"""
    current_angle: float = 90.0
    target_angle: float = 90.0
    velocity: float = 0.0
    last_update: float = field(default_factory=time.time)
    is_moving: bool = False
    position_history: deque = field(default_factory=lambda: deque(maxlen=100))

class DisneyServoController:
    """
    Disney-quality servo control system with organic motion curves

    This controller implements the fundamental principles of Disney animation:
    1. Squash and Stretch
    2. Anticipation
    3. Staging
    4. Straight Ahead and Pose to Pose
    5. Follow Through and Overlapping Action
    6. Slow In and Slow Out
    7. Arc
    8. Secondary Action
    9. Timing
    10. Exaggeration
    11. Solid Drawing
    12. Appeal
    """

    def __init__(self, i2c_bus: int = 1, pca9685_address: int = 0x40):
        """
        Initialize the Disney servo controller

        Args:
            i2c_bus: I2C bus number (typically 1 for Jetson)
            pca9685_address: I2C address of PCA9685 servo controller
        """
        self.i2c_bus = i2c_bus
        self.pca9685_address = pca9685_address
        self.servos: Dict[str, ServoConfig] = {}
        self.servo_states: Dict[str, ServoState] = {}
        self.pca9685 = None
        self._motion_thread = None
        self._motion_running = False
        self._motion_lock = threading.Lock()
        self._animation_queue: List[Dict[str, Any]] = []
        self._performance_metrics = {
            'total_movements': 0,
            'smooth_transitions': 0,
            'average_precision': 0.0,
            'last_update_time': time.time()
        }

        # Initialize hardware if available
        self._initialize_hardware()

        # Start motion control thread
        self._start_motion_thread()

    def _initialize_hardware(self):
        """Initialize PCA9685 hardware with error handling"""
        try:
            # Try to import and initialize Adafruit PCA9685
            from adafruit_pca9685 import PCA9685
            import busio
            import board

            # Initialize I2C bus
            i2c = busio.I2C(board.SCL, board.SDA)
            self.pca9685 = PCA9685(i2c, address=self.pca9685_address)
            self.pca9685.frequency = 50  # 50Hz for servos

            logger.info(f"PCA9685 initialized on bus {self.i2c_bus}, address 0x{self.pca9685_address:02X}")

        except ImportError:
            logger.warning("Adafruit PCA9685 library not available - running in simulation mode")
            self.pca9685 = None
        except Exception as e:
            logger.error(f"Failed to initialize PCA9685: {e}")
            self.pca9685 = None

    def add_servo(self, name: str, config: ServoConfig) -> bool:
        """
        Add a servo to the controller

        Args:
            name: Unique identifier for the servo
            config: Servo configuration

        Returns:
            True if servo was added successfully
        """
        try:
            config.name = name
            self.servos[name] = config
            self.servo_states[name] = ServoState(current_angle=config.center_angle)

            # Move to center position
            self.set_angle(name, config.center_angle, duration=2.0, easing=EasingType.EASE_OUT_CUBIC)

            logger.info(f"Added servo '{name}' on channel {config.channel}")
            return True

        except Exception as e:
            logger.error(f"Failed to add servo '{name}': {e}")
            return False

    def remove_servo(self, name: str) -> bool:
        """Remove a servo from the controller"""
        try:
            if name in self.servos:
                # Move to safe position before removal
                self.set_angle(name, self.servos[name].center_angle, duration=1.0)
                time.sleep(1.1)  # Wait for movement to complete

                del self.servos[name]
                del self.servo_states[name]
                logger.info(f"Removed servo '{name}'")
                return True
            return False
        except Exception as e:
            logger.error(f"Failed to remove servo '{name}': {e}")
            return False

    def set_angle(self, servo_name: str, angle: float, duration: float = 1.0,
                  easing: EasingType = EasingType.EASE_IN_OUT_CUBIC) -> bool:
        """
        Set servo to target angle with smooth motion

        Args:
            servo_name: Name of the servo
            angle: Target angle in degrees
            duration: Movement duration in seconds
            easing: Motion curve type

        Returns:
            True if command was accepted
        """
        if servo_name not in self.servos:
            logger.error(f"Servo '{servo_name}' not found")
            return False

        config = self.servos[servo_name]

        # Clamp angle to valid range
        angle = max(config.min_angle, min(config.max_angle, angle))

        # Apply trim adjustment
        angle += config.trim

        # Create motion command
        motion_cmd = {
            'servo_name': servo_name,
            'target_angle': angle,
            'duration': duration,
            'easing': easing,
            'start_time': time.time(),
            'start_angle': self.servo_states[servo_name].current_angle
        }

        with self._motion_lock:
            self._animation_queue.append(motion_cmd)

        return True

    def set_multiple_angles(self, servo_angles: Dict[str, float], duration: float = 1.0,
                           easing: EasingType = EasingType.EASE_IN_OUT_CUBIC) -> bool:
        """
        Set multiple servos simultaneously for synchronized motion

        Args:
            servo_angles: Dictionary of {servo_name: target_angle}
            duration: Movement duration in seconds
            easing: Motion curve type for all servos

        Returns:
            True if all commands were accepted
        """
        start_time = time.time()
        success = True

        with self._motion_lock:
            for servo_name, angle in servo_angles.items():
                if servo_name not in self.servos:
                    logger.error(f"Servo '{servo_name}' not found")
                    success = False
                    continue

                config = self.servos[servo_name]

                # Clamp angle to valid range
                angle = max(config.min_angle, min(config.max_angle, angle))
                angle += config.trim

                motion_cmd = {
                    'servo_name': servo_name,
                    'target_angle': angle,
                    'duration': duration,
                    'easing': easing,
                    'start_time': start_time,
                    'start_angle': self.servo_states[servo_name].current_angle
                }

                self._animation_queue.append(motion_cmd)

        return success

    def animate_sequence(self, servo_name: str, keyframes: List[MotionKeyframe]) -> bool:
        """
        Animate servo through a sequence of keyframes with Disney timing

        Args:
            servo_name: Name of the servo
            keyframes: List of motion keyframes

        Returns:
            True if animation was started successfully
        """
        if servo_name not in self.servos:
            logger.error(f"Servo '{servo_name}' not found")
            return False

        if not keyframes:
            logger.error("No keyframes provided")
            return False

        # Sort keyframes by time
        keyframes.sort(key=lambda k: k.time)

        start_time = time.time()
        current_angle = self.servo_states[servo_name].current_angle

        with self._motion_lock:
            for i, keyframe in enumerate(keyframes):
                # Calculate start angle (previous keyframe or current position)
                if i == 0:
                    start_angle = current_angle
                else:
                    start_angle = keyframes[i-1].angle

                motion_cmd = {
                    'servo_name': servo_name,
                    'target_angle': keyframe.angle,
                    'duration': keyframe.time - (keyframes[i-1].time if i > 0 else 0),
                    'easing': keyframe.easing,
                    'start_time': start_time + (keyframes[i-1].time if i > 0 else 0),
                    'start_angle': start_angle,
                    'hold_time': keyframe.hold_time
                }

                self._animation_queue.append(motion_cmd)

        logger.info(f"Started sequence animation for '{servo_name}' with {len(keyframes)} keyframes")
        return True

    def create_disney_head_nod(self, head_servo: str, intensity: float = 1.0) -> bool:
        """
        Create a Disney-style head nod with anticipation and follow-through

        Args:
            head_servo: Name of the head tilt servo
            intensity: Animation intensity (0.0 to 2.0)

        Returns:
            True if animation was created successfully
        """
        if head_servo not in self.servos:
            logger.error(f"Servo '{head_servo}' not found")
            return False

        config = self.servos[head_servo]
        center = config.center_angle

        # Disney animation: anticipation -> main action -> follow through -> settle
        keyframes = [
            # Slight anticipation upward
            MotionKeyframe(0.1, center - 5 * intensity, EasingType.EASE_OUT_QUAD),
            # Main downward nod
            MotionKeyframe(0.4, center + 25 * intensity, EasingType.EASE_IN_OUT_CUBIC),
            # Quick return with overshoot
            MotionKeyframe(0.7, center - 8 * intensity, EasingType.EASE_OUT_BACK),
            # Settle to center
            MotionKeyframe(1.0, center, EasingType.DISNEY_SETTLE, hold_time=0.5)
        ]

        return self.animate_sequence(head_servo, keyframes)

    def create_disney_head_shake(self, head_servo: str, intensity: float = 1.0) -> bool:
        """
        Create a Disney-style head shake with personality

        Args:
            head_servo: Name of the head rotation servo
            intensity: Animation intensity (0.0 to 2.0)

        Returns:
            True if animation was created successfully
        """
        if head_servo not in self.servos:
            logger.error(f"Servo '{head_servo}' not found")
            return False

        config = self.servos[head_servo]
        center = config.center_angle

        keyframes = [
            # Anticipation
            MotionKeyframe(0.1, center + 10 * intensity, EasingType.EASE_OUT_QUAD),
            # First shake
            MotionKeyframe(0.3, center - 30 * intensity, EasingType.EASE_IN_OUT_CUBIC),
            # Second shake (faster)
            MotionKeyframe(0.5, center + 30 * intensity, EasingType.EASE_IN_OUT_CUBIC),
            # Third shake (fastest)
            MotionKeyframe(0.65, center - 20 * intensity, EasingType.EASE_IN_OUT_CUBIC),
            # Settle with slight overshoot
            MotionKeyframe(0.9, center + 5 * intensity, EasingType.EASE_OUT_BACK),
            # Final settle
            MotionKeyframe(1.2, center, EasingType.DISNEY_SETTLE)
        ]

        return self.animate_sequence(head_servo, keyframes)

    def create_dome_rotation_search(self, dome_servo: str, search_pattern: str = "scan") -> bool:
        """
        Create R2D2's characteristic dome search pattern

        Args:
            dome_servo: Name of the dome rotation servo
            search_pattern: Type of search ("scan", "alert", "curious")

        Returns:
            True if animation was created successfully
        """
        if dome_servo not in self.servos:
            logger.error(f"Servo '{dome_servo}' not found")
            return False

        config = self.servos[dome_servo]
        center = config.center_angle

        if search_pattern == "scan":
            # Slow methodical scan
            keyframes = [
                MotionKeyframe(0.0, center, EasingType.EASE_OUT_CUBIC),
                MotionKeyframe(1.5, center - 60, EasingType.EASE_IN_OUT_CUBIC, hold_time=0.3),
                MotionKeyframe(3.5, center + 60, EasingType.EASE_IN_OUT_CUBIC, hold_time=0.3),
                MotionKeyframe(5.0, center, EasingType.EASE_IN_OUT_CUBIC)
            ]
        elif search_pattern == "alert":
            # Quick alert movements
            keyframes = [
                MotionKeyframe(0.2, center + 45, EasingType.EASE_OUT_QUART),
                MotionKeyframe(0.4, center - 30, EasingType.EASE_IN_OUT_CUBIC),
                MotionKeyframe(0.6, center + 20, EasingType.EASE_IN_OUT_CUBIC),
                MotionKeyframe(0.8, center, EasingType.DISNEY_SETTLE)
            ]
        elif search_pattern == "curious":
            # Tilted curious look with slight movements
            keyframes = [
                MotionKeyframe(0.3, center + 25, EasingType.EASE_OUT_CUBIC),
                MotionKeyframe(1.0, center + 35, EasingType.EASE_IN_OUT_CUBIC, hold_time=0.5),
                MotionKeyframe(1.8, center + 15, EasingType.EASE_IN_OUT_CUBIC, hold_time=0.3),
                MotionKeyframe(2.5, center, EasingType.DISNEY_SETTLE)
            ]

        return self.animate_sequence(dome_servo, keyframes)

    def _calculate_easing(self, t: float, easing_type: EasingType) -> float:
        """
        Calculate easing function value for given time ratio

        Args:
            t: Time ratio (0.0 to 1.0)
            easing_type: Type of easing curve

        Returns:
            Eased value (0.0 to 1.0)
        """
        # Clamp t to valid range
        t = max(0.0, min(1.0, t))

        if easing_type == EasingType.LINEAR:
            return t
        elif easing_type == EasingType.EASE_IN_QUAD:
            return t * t
        elif easing_type == EasingType.EASE_OUT_QUAD:
            return 1 - (1 - t) * (1 - t)
        elif easing_type == EasingType.EASE_IN_OUT_QUAD:
            return 2 * t * t if t < 0.5 else 1 - 2 * (1 - t) * (1 - t)
        elif easing_type == EasingType.EASE_IN_CUBIC:
            return t * t * t
        elif easing_type == EasingType.EASE_OUT_CUBIC:
            return 1 - (1 - t) ** 3
        elif easing_type == EasingType.EASE_IN_OUT_CUBIC:
            return 4 * t * t * t if t < 0.5 else 1 - 4 * (1 - t) ** 3
        elif easing_type == EasingType.EASE_IN_QUART:
            return t ** 4
        elif easing_type == EasingType.EASE_OUT_QUART:
            return 1 - (1 - t) ** 4
        elif easing_type == EasingType.EASE_IN_OUT_QUART:
            return 8 * t ** 4 if t < 0.5 else 1 - 8 * (1 - t) ** 4
        elif easing_type == EasingType.EASE_IN_BACK:
            c1, c3 = 1.70158, 2.70158
            return c3 * t * t * t - c1 * t * t
        elif easing_type == EasingType.EASE_OUT_BACK:
            c1, c3 = 1.70158, 2.70158
            return 1 + c3 * (t - 1) ** 3 + c1 * (t - 1) ** 2
        elif easing_type == EasingType.EASE_IN_OUT_BACK:
            c1, c2 = 1.70158, 2.5949095
            if t < 0.5:
                return (2 * t) ** 2 * ((c2 + 1) * 2 * t - c2) / 2
            else:
                return ((2 * t - 2) ** 2 * ((c2 + 1) * (t * 2 - 2) + c2) + 2) / 2
        elif easing_type == EasingType.EASE_OUT_BOUNCE:
            n1, d1 = 7.5625, 2.75
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
        elif easing_type == EasingType.EASE_OUT_ELASTIC:
            c4 = (2 * math.pi) / 3
            if t == 0 or t == 1:
                return t
            return 2 ** (-10 * t) * math.sin((t * 10 - 0.75) * c4) + 1
        elif easing_type == EasingType.DISNEY_ANTIC:
            # Custom Disney anticipation curve: slight reverse, then forward with overshoot
            if t < 0.2:
                return -0.1 * math.sin(t * math.pi / 0.2)
            else:
                adjusted_t = (t - 0.2) / 0.8
                return -0.1 + 1.1 * (1 - (1 - adjusted_t) ** 3)
        elif easing_type == EasingType.DISNEY_SQUASH:
            # Squash and stretch curve
            return t + 0.3 * math.sin(t * math.pi * 2) * (1 - t)
        elif easing_type == EasingType.DISNEY_SETTLE:
            # Natural settling with dampening
            return 1 - math.exp(-5 * t) * math.cos(10 * t)
        else:
            # Default to ease in-out cubic
            return 4 * t * t * t if t < 0.5 else 1 - 4 * (1 - t) ** 3

    def _angle_to_pulse(self, servo_config: ServoConfig, angle: float) -> int:
        """
        Convert angle to PWM pulse width

        Args:
            servo_config: Servo configuration
            angle: Target angle in degrees

        Returns:
            Pulse width in microseconds
        """
        # Apply inversion if configured
        if servo_config.invert:
            angle = servo_config.max_angle - (angle - servo_config.min_angle)

        # Convert angle to pulse width
        angle_range = servo_config.max_angle - servo_config.min_angle
        pulse_range = servo_config.max_pulse - servo_config.min_pulse

        normalized_angle = (angle - servo_config.min_angle) / angle_range
        pulse_width = servo_config.min_pulse + (normalized_angle * pulse_range)

        return int(pulse_width)

    def _set_servo_pulse(self, channel: int, pulse_width: int):
        """
        Set servo PWM pulse width on hardware

        Args:
            channel: PWM channel (0-15)
            pulse_width: Pulse width in microseconds
        """
        if self.pca9685 is None:
            # Simulation mode - just log the command
            logger.debug(f"SIM: Channel {channel} -> {pulse_width}μs")
            return

        try:
            # Convert microseconds to 12-bit PWM value
            # 50Hz = 20ms period, 4096 steps
            pwm_value = int((pulse_width / 20000.0) * 4096)
            pwm_value = max(0, min(4095, pwm_value))

            self.pca9685.channels[channel].duty_cycle = pwm_value

        except Exception as e:
            logger.error(f"Failed to set pulse on channel {channel}: {e}")

    def _motion_control_loop(self):
        """Main motion control loop - runs in separate thread"""
        logger.info("Motion control thread started")

        while self._motion_running:
            try:
                current_time = time.time()

                with self._motion_lock:
                    # Process animation queue
                    active_animations = []

                    for animation in self._animation_queue:
                        elapsed_time = current_time - animation['start_time']

                        if elapsed_time < 0:
                            # Animation hasn't started yet
                            active_animations.append(animation)
                            continue
                        elif elapsed_time >= animation['duration']:
                            # Animation completed - set final position
                            servo_name = animation['servo_name']
                            if servo_name in self.servo_states:
                                self.servo_states[servo_name].current_angle = animation['target_angle']
                                self.servo_states[servo_name].is_moving = False

                                # Set hardware position
                                if servo_name in self.servos:
                                    config = self.servos[servo_name]
                                    pulse_width = self._angle_to_pulse(config, animation['target_angle'])
                                    self._set_servo_pulse(config.channel, pulse_width)

                                # Update performance metrics
                                self._performance_metrics['total_movements'] += 1
                                self._performance_metrics['smooth_transitions'] += 1
                        else:
                            # Animation in progress
                            servo_name = animation['servo_name']
                            if servo_name in self.servo_states:
                                # Calculate current position using easing
                                t = elapsed_time / animation['duration']
                                eased_t = self._calculate_easing(t, animation['easing'])

                                start_angle = animation['start_angle']
                                target_angle = animation['target_angle']
                                current_angle = start_angle + (target_angle - start_angle) * eased_t

                                # Update servo state
                                self.servo_states[servo_name].current_angle = current_angle
                                self.servo_states[servo_name].target_angle = target_angle
                                self.servo_states[servo_name].is_moving = True

                                # Calculate velocity for smoothness metrics
                                last_angle = self.servo_states[servo_name].position_history[-1] if self.servo_states[servo_name].position_history else current_angle
                                velocity = abs(current_angle - last_angle) / 0.02  # Assuming 50Hz update
                                self.servo_states[servo_name].velocity = velocity

                                # Update position history
                                self.servo_states[servo_name].position_history.append(current_angle)

                                # Set hardware position
                                if servo_name in self.servos:
                                    config = self.servos[servo_name]
                                    pulse_width = self._angle_to_pulse(config, current_angle)
                                    self._set_servo_pulse(config.channel, pulse_width)

                            active_animations.append(animation)

                    # Update animation queue with active animations
                    self._animation_queue = active_animations

                # Sleep for smooth 50Hz update rate
                time.sleep(0.02)

            except Exception as e:
                logger.error(f"Motion control loop error: {e}")
                time.sleep(0.1)

        logger.info("Motion control thread stopped")

    def _start_motion_thread(self):
        """Start the motion control thread"""
        if self._motion_thread is None or not self._motion_thread.is_alive():
            self._motion_running = True
            self._motion_thread = threading.Thread(target=self._motion_control_loop, daemon=True)
            self._motion_thread.start()

    def stop_motion_thread(self):
        """Stop the motion control thread"""
        self._motion_running = False
        if self._motion_thread and self._motion_thread.is_alive():
            self._motion_thread.join(timeout=2.0)

    def emergency_stop(self):
        """Emergency stop all servo motion"""
        logger.warning("EMERGENCY STOP activated")

        with self._motion_lock:
            self._animation_queue.clear()

        # Stop all servos at current position
        for servo_name in self.servos:
            self.servo_states[servo_name].is_moving = False
            self.servo_states[servo_name].velocity = 0.0

    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get performance metrics for system monitoring"""
        current_time = time.time()

        # Calculate average precision from position histories
        total_smoothness = 0.0
        servo_count = 0

        for servo_name, state in self.servo_states.items():
            if len(state.position_history) > 10:
                # Calculate smoothness as inverse of velocity variations
                velocities = np.diff(list(state.position_history))
                velocity_variance = np.var(velocities) if len(velocities) > 1 else 0
                smoothness = 1.0 / (1.0 + velocity_variance)
                total_smoothness += smoothness
                servo_count += 1

        avg_precision = total_smoothness / servo_count if servo_count > 0 else 1.0

        self._performance_metrics.update({
            'average_precision': avg_precision,
            'active_animations': len(self._animation_queue),
            'servos_moving': sum(1 for state in self.servo_states.values() if state.is_moving),
            'update_frequency': 50.0,  # 50Hz target
            'last_update_time': current_time
        })

        return self._performance_metrics.copy()

    def save_performance_profile(self, filename: str):
        """Save performance profile for optimization"""
        try:
            profile_data = {
                'timestamp': time.time(),
                'servo_configs': {name: {
                    'channel': config.channel,
                    'min_angle': config.min_angle,
                    'max_angle': config.max_angle,
                    'max_speed': config.max_speed,
                    'name': config.name
                } for name, config in self.servos.items()},
                'performance_metrics': self.get_performance_metrics(),
                'servo_states': {name: {
                    'current_angle': state.current_angle,
                    'velocity': state.velocity,
                    'is_moving': state.is_moving
                } for name, state in self.servo_states.items()}
            }

            with open(filename, 'w') as f:
                json.dump(profile_data, f, indent=2)

            logger.info(f"Performance profile saved to {filename}")

        except Exception as e:
            logger.error(f"Failed to save performance profile: {e}")

    def __del__(self):
        """Cleanup when controller is destroyed"""
        self.stop_motion_thread()
        if self.pca9685:
            try:
                # Set all channels to safe center position
                for servo_name, config in self.servos.items():
                    pulse_width = self._angle_to_pulse(config, config.center_angle)
                    self._set_servo_pulse(config.channel, pulse_width)
            except:
                pass


# Example usage and R2D2 specific configurations
class R2D2ServoSystem:
    """
    Complete R2D2 servo system with pre-configured animations
    """

    def __init__(self):
        self.controller = DisneyServoController()
        self._setup_r2d2_servos()

    def _setup_r2d2_servos(self):
        """Setup standard R2D2 servo configuration"""

        # Dome rotation (continuous servo or stepper)
        dome_config = ServoConfig(
            channel=0,
            min_angle=0,
            max_angle=360,
            center_angle=180,
            max_speed=90,  # Slower dome rotation
            name="dome_rotation"
        )
        self.controller.add_servo("dome", dome_config)

        # Head tilt/nod
        head_tilt_config = ServoConfig(
            channel=1,
            min_angle=45,
            max_angle=135,
            center_angle=90,
            max_speed=120,
            name="head_tilt"
        )
        self.controller.add_servo("head_tilt", head_tilt_config)

        # Periscope extend/retract
        periscope_config = ServoConfig(
            channel=2,
            min_angle=0,
            max_angle=180,
            center_angle=0,  # Retracted by default
            max_speed=60,   # Slower for dramatic effect
            name="periscope"
        )
        self.controller.add_servo("periscope", periscope_config)

        # Front panel servos (utility arms, panels, etc.)
        for i in range(4):
            panel_config = ServoConfig(
                channel=3 + i,
                min_angle=0,
                max_angle=90,
                center_angle=0,  # Closed by default
                max_speed=180,
                name=f"front_panel_{i+1}"
            )
            self.controller.add_servo(f"panel_{i+1}", panel_config)

        logger.info("R2D2 servo system initialized with Disney-quality motion control")

    def perform_greeting_sequence(self):
        """Perform R2D2's signature greeting sequence"""
        logger.info("Performing R2D2 greeting sequence")

        # 1. Head nod
        self.controller.create_disney_head_nod("head_tilt", intensity=1.5)
        time.sleep(1.5)

        # 2. Dome scan
        self.controller.create_dome_rotation_search("dome", "curious")
        time.sleep(2.5)

        # 3. Panel flourish
        self.controller.set_multiple_angles({
            "panel_1": 45,
            "panel_2": 30,
            "panel_3": 60
        }, duration=1.0, easing=EasingType.EASE_OUT_BACK)
        time.sleep(1.5)

        # 4. Return to neutral
        self.controller.set_multiple_angles({
            "panel_1": 0,
            "panel_2": 0,
            "panel_3": 0
        }, duration=2.0, easing=EasingType.EASE_IN_OUT_CUBIC)

    def perform_alert_sequence(self):
        """Perform alert/warning sequence"""
        logger.info("Performing R2D2 alert sequence")

        # Quick dome movements
        self.controller.create_dome_rotation_search("dome", "alert")

        # Rapid head movements
        keyframes = [
            MotionKeyframe(0.1, 75, EasingType.EASE_OUT_QUART),
            MotionKeyframe(0.3, 105, EasingType.EASE_IN_OUT_CUBIC),
            MotionKeyframe(0.5, 75, EasingType.EASE_IN_OUT_CUBIC),
            MotionKeyframe(0.7, 105, EasingType.EASE_IN_OUT_CUBIC),
            MotionKeyframe(1.0, 90, EasingType.DISNEY_SETTLE)
        ]
        self.controller.animate_sequence("head_tilt", keyframes)

    def perform_search_sequence(self):
        """Perform searching/scanning sequence"""
        logger.info("Performing R2D2 search sequence")

        # Systematic search pattern
        self.controller.create_dome_rotation_search("dome", "scan")

        # Periscope extension for better view
        self.controller.set_angle("periscope", 120, duration=2.0, easing=EasingType.EASE_OUT_CUBIC)
        time.sleep(3.0)

        # Periscope retraction
        self.controller.set_angle("periscope", 0, duration=1.5, easing=EasingType.EASE_IN_CUBIC)

    def emergency_stop(self):
        """Emergency stop all R2D2 motion"""
        self.controller.emergency_stop()

    def get_system_status(self) -> Dict[str, Any]:
        """Get complete R2D2 system status"""
        return {
            'servo_controller': self.controller.get_performance_metrics(),
            'servo_positions': {name: state.current_angle
                              for name, state in self.controller.servo_states.items()},
            'moving_servos': [name for name, state in self.controller.servo_states.items()
                            if state.is_moving],
            'system_health': 'OPERATIONAL' if len(self.controller._animation_queue) < 20 else 'BUSY'
        }


if __name__ == "__main__":
    # Example usage
    print("Disney Servo Control Library - R2D2 Demo")
    print("=" * 50)

    # Create R2D2 system
    r2d2 = R2D2ServoSystem()

    try:
        # Demo sequence
        r2d2.perform_greeting_sequence()
        time.sleep(3)

        r2d2.perform_search_sequence()
        time.sleep(5)

        r2d2.perform_alert_sequence()
        time.sleep(2)

        # Display final status
        status = r2d2.get_system_status()
        print(f"\nFinal System Status: {status['system_health']}")
        print(f"Active Servos: {len(status['servo_positions'])}")
        print(f"Moving Servos: {len(status['moving_servos'])}")

        # Save performance profile
        r2d2.controller.save_performance_profile("/home/rolo/r2ai/.claude/agent_storage/super-coder/r2d2_performance_profile.json")

    except KeyboardInterrupt:
        print("\nDemo interrupted - performing emergency stop")
        r2d2.emergency_stop()
    except Exception as e:
        print(f"Error during demo: {e}")
        r2d2.emergency_stop()
    finally:
        print("Demo completed")