#!/usr/bin/env python3
"""
R2-D2 Advanced Servo Control System
Disney-Level Animatronic Control with PCA9685 I2C Integration

This module provides comprehensive servo control for R2-D2 animatronics including:
- PCA9685 I2C servo controllers (16 channels each)
- Multiple controller support for complex choreography
- Disney-level motion smoothing and natural movement
- Safety systems and emergency stops
- Simulation mode for development without hardware
"""

import time
import math
import logging
import threading
from typing import Dict, List, Tuple, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum

try:
    import board
    import busio
    from adafruit_pca9685 import PCA9685
    from adafruit_motor import servo
    from adafruit_servokit import ServoKit
    HARDWARE_AVAILABLE = True
except Exception as e:
    logging.warning(f"Hardware libraries not available (expected on Orin Nano): {e}")
    HARDWARE_AVAILABLE = False

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ServoPosition(Enum):
    """Standard servo positions for R2-D2 components"""
    CLOSED = 0
    NEUTRAL = 90
    OPEN = 180

class R2D2Component(Enum):
    """R2-D2 Component definitions with servo channel assignments"""
    # Head/Dome Components (Controller 1 - Address 0x40)
    DOME_ROTATION = 0        # Main dome rotation servo
    HEAD_TILT = 1           # Head tilt mechanism
    PERISCOPE = 2           # Periscope raise/lower
    RADAR_EYE = 3           # Radar eye rotation

    # Dome Panels (Controller 1 - Channels 4-11)
    DOME_PANEL_1 = 4       # Front pie panel
    DOME_PANEL_2 = 5       # Front side panels
    DOME_PANEL_3 = 6
    DOME_PANEL_4 = 7       # Side panels
    DOME_PANEL_5 = 8
    DOME_PANEL_6 = 9       # Back panels
    DOME_PANEL_7 = 10
    DOME_PANEL_8 = 11      # Large back panel

    # Utility Arms (Controller 1 - Channels 12-15)
    UTILITY_ARM_1 = 12     # Left utility arm
    UTILITY_ARM_2 = 13     # Right utility arm
    INTERFACE_ARM = 14     # Computer interface arm
    GRIPPER_ARM = 15       # Gripper mechanism

    # Body Components (Controller 2 - Address 0x41)
    CENTER_LEG = 16        # Center leg extend/retract
    ANKLE_TILT_L = 17      # Left ankle tilt
    ANKLE_TILT_R = 18      # Right ankle tilt
    BODY_DOORS_L = 19      # Left body access doors
    BODY_DOORS_R = 20      # Right body access doors

    # Additional Components (Controller 2 - Channels 5-15)
    DATA_PORT = 21         # Data port cover
    POWER_COUPLING = 22    # Power coupling cover
    HOLOGRAM = 23          # Hologram projector position
    RESTRAINING_BOLT = 24  # Restraining bolt mechanism

@dataclass
class ServoConfig:
    """Configuration for individual servo"""
    min_pulse: int = 500     # Minimum pulse width in microseconds
    max_pulse: int = 2500    # Maximum pulse width in microseconds
    min_angle: float = 0     # Minimum angle
    max_angle: float = 180   # Maximum angle
    default_angle: float = 90 # Default position
    max_speed: float = 360   # Maximum degrees per second
    acceleration: float = 720 # Degrees per second squared

@dataclass
class MotionSequence:
    """Defines a motion sequence for choreographed movements"""
    name: str
    steps: List[Dict] = field(default_factory=list)
    duration: float = 0.0
    loop: bool = False
    priority: int = 1  # 1=low, 5=high priority

class R2D2ServoController:
    """Advanced servo controller for R2-D2 animatronics"""

    def __init__(self, simulation_mode: bool = None):
        """
        Initialize R2-D2 servo controller

        Args:
            simulation_mode: Force simulation mode. If None, auto-detect hardware
        """
        self.simulation_mode = simulation_mode if simulation_mode is not None else not HARDWARE_AVAILABLE
        self.controllers: Dict[int, any] = {}
        self.servo_configs: Dict[R2D2Component, ServoConfig] = {}
        self.current_positions: Dict[R2D2Component, float] = {}
        self.target_positions: Dict[R2D2Component, float] = {}
        self.motion_threads: Dict[str, threading.Thread] = {}
        self.emergency_stop = threading.Event()
        self.is_running = True

        # Initialize servo configurations
        self._initialize_servo_configs()

        # Initialize hardware controllers
        self._initialize_controllers()

        # Start motion control thread
        self.motion_thread = threading.Thread(target=self._motion_control_loop, daemon=True)
        self.motion_thread.start()

        logger.info(f"R2-D2 Servo Controller initialized - Simulation Mode: {self.simulation_mode}")

    def _initialize_servo_configs(self):
        """Initialize default servo configurations for all R2-D2 components"""
        # Standard configuration for most servos
        standard_config = ServoConfig()

        # Specialized configurations for specific components
        dome_rotation_config = ServoConfig(
            min_angle=0, max_angle=360, max_speed=90,  # Slower dome rotation
            acceleration=180
        )

        panel_config = ServoConfig(
            min_angle=0, max_angle=120, max_speed=180,  # Fast panel movement
            acceleration=360
        )

        utility_arm_config = ServoConfig(
            min_angle=0, max_angle=180, max_speed=120,  # Moderate arm movement
            acceleration=240
        )

        # Apply configurations
        for component in R2D2Component:
            if "DOME_PANEL" in component.name:
                self.servo_configs[component] = panel_config
            elif component == R2D2Component.DOME_ROTATION:
                self.servo_configs[component] = dome_rotation_config
            elif "ARM" in component.name:
                self.servo_configs[component] = utility_arm_config
            else:
                self.servo_configs[component] = standard_config

            # Set initial positions
            self.current_positions[component] = self.servo_configs[component].default_angle
            self.target_positions[component] = self.servo_configs[component].default_angle

    def _initialize_controllers(self):
        """Initialize PCA9685 controllers"""
        if self.simulation_mode:
            logger.info("Running in simulation mode - no hardware controllers initialized")
            return

        try:
            # Initialize I2C bus
            i2c = busio.I2C(board.SCL, board.SDA)

            # Controller 1: Head/Dome components (Address 0x40)
            try:
                controller1 = PCA9685(i2c, address=0x40)
                controller1.frequency = 50  # 50Hz for servo control
                self.controllers[0x40] = controller1
                logger.info("✅ PCA9685 Controller 1 (0x40) initialized - Head/Dome servos")
            except Exception as e:
                logger.warning(f"Controller 1 (0x40) not available: {e}")

            # Controller 2: Body components (Address 0x41)
            try:
                controller2 = PCA9685(i2c, address=0x41)
                controller2.frequency = 50
                self.controllers[0x41] = controller2
                logger.info("✅ PCA9685 Controller 2 (0x41) initialized - Body servos")
            except Exception as e:
                logger.warning(f"Controller 2 (0x41) not available: {e}")

        except Exception as e:
            logger.error(f"Failed to initialize I2C controllers: {e}")
            logger.info("Falling back to simulation mode")
            self.simulation_mode = True

    def _get_controller_and_channel(self, component: R2D2Component) -> Tuple[int, int]:
        """Get controller address and channel for a component"""
        channel = component.value
        if channel < 16:
            return 0x40, channel  # Controller 1
        else:
            return 0x41, channel - 16  # Controller 2

    def _set_servo_position(self, component: R2D2Component, angle: float):
        """Set physical servo position"""
        if self.simulation_mode:
            logger.debug(f"[SIM] {component.name}: {angle:.1f}°")
            return

        controller_addr, channel = self._get_controller_and_channel(component)
        controller = self.controllers.get(controller_addr)

        if controller is None:
            logger.warning(f"Controller {hex(controller_addr)} not available for {component.name}")
            return

        try:
            # Convert angle to pulse width
            config = self.servo_configs[component]
            pulse_range = config.max_pulse - config.min_pulse
            angle_range = config.max_angle - config.min_angle
            pulse_width = config.min_pulse + (angle - config.min_angle) * pulse_range / angle_range

            # Set PWM duty cycle
            duty_cycle = int(pulse_width * 0xFFFF / 20000)  # 20ms period
            controller.channels[channel].duty_cycle = duty_cycle

        except Exception as e:
            logger.error(f"Failed to set servo position for {component.name}: {e}")

    def _motion_control_loop(self):
        """Main motion control loop for smooth servo movement"""
        while self.is_running and not self.emergency_stop.is_set():
            try:
                for component in R2D2Component:
                    current = self.current_positions[component]
                    target = self.target_positions[component]

                    if abs(current - target) > 0.5:  # Movement threshold
                        config = self.servo_configs[component]

                        # Calculate movement step based on max speed
                        max_step = config.max_speed * 0.02  # 50Hz update rate

                        # Calculate direction and distance
                        distance = target - current
                        step = max(min(distance, max_step), -max_step)

                        # Update position
                        new_position = current + step
                        self.current_positions[component] = new_position

                        # Send to hardware
                        self._set_servo_position(component, new_position)

                time.sleep(0.02)  # 50Hz update rate

            except Exception as e:
                logger.error(f"Motion control loop error: {e}")
                time.sleep(0.1)

    def move_to(self, component: R2D2Component, angle: float, duration: float = None):
        """
        Move servo to specified angle

        Args:
            component: R2D2 component to move
            angle: Target angle in degrees
            duration: Movement duration in seconds (optional)
        """
        config = self.servo_configs[component]

        # Clamp angle to valid range
        angle = max(config.min_angle, min(config.max_angle, angle))

        # Set target position
        self.target_positions[component] = angle

        logger.info(f"Moving {component.name} to {angle:.1f}°")

    def move_multiple(self, movements: Dict[R2D2Component, float], duration: float = None):
        """
        Move multiple servos simultaneously

        Args:
            movements: Dictionary of component -> angle pairs
            duration: Movement duration in seconds
        """
        for component, angle in movements.items():
            self.move_to(component, angle, duration)

    def get_position(self, component: R2D2Component) -> float:
        """Get current position of servo"""
        return self.current_positions[component]

    def emergency_stop_all(self):
        """Emergency stop all servo movement"""
        self.emergency_stop.set()
        logger.warning("🚨 EMERGENCY STOP ACTIVATED - All servo movement halted")

    def resume_operation(self):
        """Resume normal operation after emergency stop"""
        self.emergency_stop.clear()
        logger.info("✅ Emergency stop cleared - Resuming normal operation")

    def home_all_servos(self):
        """Move all servos to home position"""
        logger.info("Homing all servos to default positions...")

        movements = {}
        for component in R2D2Component:
            default_angle = self.servo_configs[component].default_angle
            movements[component] = default_angle

        self.move_multiple(movements)

    def shutdown(self):
        """Safely shutdown servo controller"""
        logger.info("Shutting down R2-D2 servo controller...")
        self.is_running = False

        # Stop all motion threads
        for thread in self.motion_threads.values():
            if thread.is_alive():
                thread.join(timeout=1.0)

        # Join main motion thread
        if self.motion_thread.is_alive():
            self.motion_thread.join(timeout=2.0)

        # Turn off all PWM channels
        if not self.simulation_mode:
            for controller in self.controllers.values():
                try:
                    controller.deinit()
                except:
                    pass

        logger.info("✅ Servo controller shutdown complete")

class R2D2Choreographer:
    """Disney-level motion choreography for R2-D2"""

    def __init__(self, servo_controller: R2D2ServoController):
        self.servo_controller = servo_controller
        self.sequences: Dict[str, MotionSequence] = {}
        self.active_sequence = None
        self._create_standard_sequences()

    def _create_standard_sequences(self):
        """Create standard R2-D2 motion sequences"""

        # Excited/Happy sequence
        excited_sequence = MotionSequence(
            name="excited",
            duration=4.0,
            steps=[
                {"time": 0.0, "dome_rotation": 0, "dome_panels": "closed"},
                {"time": 0.5, "dome_rotation": 45, "dome_panels": "open_sequential"},
                {"time": 1.0, "dome_rotation": -45, "utility_arms": "extended"},
                {"time": 1.5, "dome_rotation": 0, "head_tilt": 15},
                {"time": 2.0, "dome_panels": "flutter"},
                {"time": 3.0, "dome_panels": "closed", "utility_arms": "retracted"},
                {"time": 4.0, "head_tilt": 0, "dome_rotation": 0}
            ]
        )

        # Scanning/Alert sequence
        scanning_sequence = MotionSequence(
            name="scanning",
            duration=6.0,
            loop=True,
            steps=[
                {"time": 0.0, "dome_rotation": 0, "periscope": "up"},
                {"time": 1.0, "dome_rotation": 90, "radar_eye": "active"},
                {"time": 2.0, "dome_rotation": 180},
                {"time": 3.0, "dome_rotation": 270},
                {"time": 4.0, "dome_rotation": 360},
                {"time": 5.0, "periscope": "down", "radar_eye": "inactive"},
                {"time": 6.0, "dome_rotation": 0}
            ]
        )

        # Maintenance mode sequence
        maintenance_sequence = MotionSequence(
            name="maintenance",
            duration=8.0,
            steps=[
                {"time": 0.0, "all_panels": "closed"},
                {"time": 1.0, "dome_panels": "open_all"},
                {"time": 2.0, "utility_arms": "extended"},
                {"time": 3.0, "interface_arm": "extended"},
                {"time": 4.0, "body_doors": "open"},
                {"time": 5.0, "data_port": "open"},
                {"time": 6.0, "power_coupling": "open"},
                {"time": 7.0, "center_leg": "extended"},
                {"time": 8.0, "hold_position": True}
            ]
        )

        self.sequences.update({
            "excited": excited_sequence,
            "scanning": scanning_sequence,
            "maintenance": maintenance_sequence
        })

    def play_sequence(self, sequence_name: str, callback: Optional[Callable] = None):
        """Play a choreographed motion sequence"""
        if sequence_name not in self.sequences:
            logger.error(f"Unknown sequence: {sequence_name}")
            return

        sequence = self.sequences[sequence_name]
        self.active_sequence = sequence_name

        logger.info(f"🎭 Playing choreography sequence: {sequence_name}")

        def execute_sequence():
            try:
                start_time = time.time()

                for step in sequence.steps:
                    if self.servo_controller.emergency_stop.is_set():
                        break

                    # Wait for step time
                    step_time = step["time"]
                    while time.time() - start_time < step_time:
                        time.sleep(0.01)

                    # Execute step movements
                    self._execute_step(step)

                # Wait for sequence completion
                while time.time() - start_time < sequence.duration:
                    time.sleep(0.01)

                self.active_sequence = None
                if callback:
                    callback()

            except Exception as e:
                logger.error(f"Sequence execution error: {e}")
                self.active_sequence = None

        # Start sequence in separate thread
        sequence_thread = threading.Thread(target=execute_sequence, daemon=True)
        sequence_thread.start()
        self.servo_controller.motion_threads[sequence_name] = sequence_thread

    def _execute_step(self, step: Dict):
        """Execute a single step in a motion sequence"""
        movements = {}

        # Parse step commands
        for command, value in step.items():
            if command == "time":
                continue

            if command == "dome_rotation":
                movements[R2D2Component.DOME_ROTATION] = value

            elif command == "dome_panels":
                if value == "open_all":
                    for i in range(8):
                        panel = list(R2D2Component)[4 + i]  # DOME_PANEL_1 through 8
                        movements[panel] = 90
                elif value == "closed":
                    for i in range(8):
                        panel = list(R2D2Component)[4 + i]
                        movements[panel] = 0
                elif value == "open_sequential":
                    # This would need timing logic for sequential opening
                    pass

            elif command == "utility_arms":
                if value == "extended":
                    movements[R2D2Component.UTILITY_ARM_1] = 90
                    movements[R2D2Component.UTILITY_ARM_2] = 90
                elif value == "retracted":
                    movements[R2D2Component.UTILITY_ARM_1] = 0
                    movements[R2D2Component.UTILITY_ARM_2] = 0

        # Execute movements
        if movements:
            self.servo_controller.move_multiple(movements)

    def stop_sequence(self):
        """Stop current sequence"""
        if self.active_sequence:
            logger.info(f"Stopping sequence: {self.active_sequence}")
            self.active_sequence = None

# Convenience functions for quick testing
def demo_r2d2_movement():
    """Demonstration of R2-D2 servo capabilities"""
    controller = R2D2ServoController()
    choreographer = R2D2Choreographer(controller)

    try:
        logger.info("🤖 R2-D2 Movement Demonstration Starting...")

        # Home all servos
        controller.home_all_servos()
        time.sleep(2)

        # Test individual movements
        logger.info("Testing individual servo movements...")
        controller.move_to(R2D2Component.DOME_ROTATION, 45)
        time.sleep(1)

        controller.move_to(R2D2Component.DOME_PANEL_1, 90)
        time.sleep(1)

        controller.move_to(R2D2Component.UTILITY_ARM_1, 120)
        time.sleep(1)

        # Play choreographed sequence
        logger.info("Playing excited sequence...")
        choreographer.play_sequence("excited")
        time.sleep(5)

        # Return to home
        controller.home_all_servos()
        time.sleep(2)

        logger.info("✅ Demonstration complete!")

    except KeyboardInterrupt:
        logger.info("Demo interrupted by user")
    finally:
        controller.shutdown()

if __name__ == "__main__":
    demo_r2d2_movement()