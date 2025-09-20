#!/usr/bin/env python3
"""
R2-D2 Simple Servo Control System
Simplified Disney-Level Animatronic Control for Testing

This is a simplified version without complex threading for initial testing
"""

import time
import math
import logging
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from enum import Enum

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

@dataclass
class ServoConfig:
    """Configuration for individual servo"""
    min_pulse: int = 500     # Minimum pulse width in microseconds
    max_pulse: int = 2500    # Maximum pulse width in microseconds
    min_angle: float = 0     # Minimum angle
    max_angle: float = 180   # Maximum angle
    default_angle: float = 90 # Default position
    max_speed: float = 360   # Maximum degrees per second

class R2D2ServoControllerSimple:
    """Simplified servo controller for R2-D2 animatronics"""

    def __init__(self, simulation_mode: bool = True):
        """Initialize simplified R2-D2 servo controller"""
        self.simulation_mode = simulation_mode
        self.servo_configs: Dict[R2D2Component, ServoConfig] = {}
        self.current_positions: Dict[R2D2Component, float] = {}
        self.emergency_stopped = False

        # Initialize servo configurations
        self._initialize_servo_configs()

        logger.info(f"R2-D2 Simple Servo Controller initialized - Simulation Mode: {self.simulation_mode}")

    def _initialize_servo_configs(self):
        """Initialize default servo configurations for all R2-D2 components"""
        # Standard configuration for most servos
        standard_config = ServoConfig()

        # Specialized configurations
        dome_rotation_config = ServoConfig(
            min_angle=0, max_angle=360, max_speed=90, default_angle=0
        )

        panel_config = ServoConfig(
            min_angle=0, max_angle=120, max_speed=180, default_angle=0
        )

        # Apply configurations
        for component in R2D2Component:
            if "DOME_PANEL" in component.name:
                self.servo_configs[component] = panel_config
            elif component == R2D2Component.DOME_ROTATION:
                self.servo_configs[component] = dome_rotation_config
            else:
                self.servo_configs[component] = standard_config

            # Set initial positions
            self.current_positions[component] = self.servo_configs[component].default_angle

    def _set_servo_position(self, component: R2D2Component, angle: float):
        """Set physical servo position (simulation mode logs only)"""
        if self.simulation_mode:
            logger.info(f"[SERVO] {component.name}: {angle:.1f}°")
        else:
            # This is where real hardware control would go
            logger.info(f"[HARDWARE] Setting {component.name} to {angle:.1f}°")

        # Update current position
        self.current_positions[component] = angle

    def move_to(self, component: R2D2Component, angle: float, smooth: bool = True):
        """
        Move servo to specified angle

        Args:
            component: R2D2 component to move
            angle: Target angle in degrees
            smooth: Enable smooth movement (simulated delay)
        """
        if self.emergency_stopped:
            logger.warning("Cannot move - emergency stop active")
            return

        config = self.servo_configs[component]

        # Clamp angle to valid range
        angle = max(config.min_angle, min(config.max_angle, angle))

        if smooth:
            # Simulate smooth movement
            current = self.current_positions[component]
            distance = abs(angle - current)
            move_time = distance / config.max_speed  # Simple timing calculation

            if move_time > 0.1:  # Only show progress for longer moves
                steps = max(3, int(move_time * 10))  # 10Hz update
                for i in range(steps + 1):
                    if self.emergency_stopped:
                        break
                    intermediate = current + (angle - current) * (i / steps)
                    self._set_servo_position(component, intermediate)
                    if i < steps:  # Don't sleep on last iteration
                        time.sleep(move_time / steps)
            else:
                self._set_servo_position(component, angle)
        else:
            self._set_servo_position(component, angle)

        logger.info(f"✅ {component.name} moved to {angle:.1f}°")

    def move_multiple(self, movements: Dict[R2D2Component, float], smooth: bool = True):
        """Move multiple servos simultaneously"""
        if self.emergency_stopped:
            logger.warning("Cannot move - emergency stop active")
            return

        logger.info(f"Moving {len(movements)} servos simultaneously...")

        if smooth:
            # Calculate maximum movement time
            max_time = 0
            for component, angle in movements.items():
                config = self.servo_configs[component]
                current = self.current_positions[component]
                distance = abs(angle - current)
                move_time = distance / config.max_speed
                max_time = max(max_time, move_time)

            if max_time > 0.1:
                steps = max(3, int(max_time * 10))
                start_positions = {comp: self.current_positions[comp] for comp in movements}

                for i in range(steps + 1):
                    if self.emergency_stopped:
                        break

                    for component, target_angle in movements.items():
                        start_angle = start_positions[component]
                        intermediate = start_angle + (target_angle - start_angle) * (i / steps)
                        self._set_servo_position(component, intermediate)

                    if i < steps:
                        time.sleep(max_time / steps)
            else:
                for component, angle in movements.items():
                    self._set_servo_position(component, angle)
        else:
            for component, angle in movements.items():
                self._set_servo_position(component, angle)

        logger.info("✅ Multi-servo movement completed")

    def get_position(self, component: R2D2Component) -> float:
        """Get current position of servo"""
        return self.current_positions[component]

    def emergency_stop(self):
        """Emergency stop all servo movement"""
        self.emergency_stopped = True
        logger.warning("🚨 EMERGENCY STOP ACTIVATED")

    def resume_operation(self):
        """Resume normal operation"""
        self.emergency_stopped = False
        logger.info("✅ Emergency stop cleared")

    def home_all_servos(self):
        """Move all servos to home position"""
        logger.info("Homing all servos...")

        movements = {}
        for component in R2D2Component:
            default_angle = self.servo_configs[component].default_angle
            movements[component] = default_angle

        self.move_multiple(movements, smooth=True)
        logger.info("✅ All servos homed")

    def status_report(self):
        """Generate status report of all servos"""
        logger.info("\n" + "="*50)
        logger.info("R2-D2 SERVO STATUS REPORT")
        logger.info("="*50)

        # Group by controller
        controller1_servos = []
        controller2_servos = []

        for component in R2D2Component:
            if component.value < 16:
                controller1_servos.append(component)
            else:
                controller2_servos.append(component)

        logger.info("Controller 1 (0x40) - Head/Dome:")
        for component in controller1_servos:
            pos = self.current_positions[component]
            config = self.servo_configs[component]
            logger.info(f"  Ch{component.value:2d}: {component.name:<15} {pos:6.1f}° (Range: {config.min_angle:.0f}-{config.max_angle:.0f}°)")

        logger.info("\nController 2 (0x41) - Body:")
        for component in controller2_servos:
            pos = self.current_positions[component]
            config = self.servo_configs[component]
            ch_num = component.value - 16
            logger.info(f"  Ch{ch_num:2d}: {component.name:<15} {pos:6.1f}° (Range: {config.min_angle:.0f}-{config.max_angle:.0f}°)")

        logger.info("="*50)

class R2D2Choreographer:
    """Disney-level motion choreography for R2-D2"""

    def __init__(self, servo_controller: R2D2ServoControllerSimple):
        self.servo_controller = servo_controller

    def excited_sequence(self):
        """Excited/Happy R2-D2 behavior"""
        logger.info("🎭 Playing EXCITED sequence...")

        try:
            # Dome rotation with panel flutter
            self.servo_controller.move_to(R2D2Component.DOME_ROTATION, 45)
            time.sleep(0.5)

            # Open panels sequentially
            panels = [R2D2Component.DOME_PANEL_1, R2D2Component.DOME_PANEL_2,
                     R2D2Component.DOME_PANEL_3, R2D2Component.DOME_PANEL_4]

            for panel in panels:
                self.servo_controller.move_to(panel, 90, smooth=False)
                time.sleep(0.2)

            # Dome wiggle
            self.servo_controller.move_to(R2D2Component.DOME_ROTATION, -45)
            time.sleep(0.5)
            self.servo_controller.move_to(R2D2Component.DOME_ROTATION, 0)

            # Extend utility arms
            arms = {
                R2D2Component.UTILITY_ARM_1: 120,
                R2D2Component.UTILITY_ARM_2: 120
            }
            self.servo_controller.move_multiple(arms)
            time.sleep(1)

            # Close everything
            close_movements = {}
            for panel in panels:
                close_movements[panel] = 0
            close_movements[R2D2Component.UTILITY_ARM_1] = 0
            close_movements[R2D2Component.UTILITY_ARM_2] = 0

            self.servo_controller.move_multiple(close_movements)

            logger.info("✅ Excited sequence completed!")

        except Exception as e:
            logger.error(f"Excited sequence failed: {e}")

    def scanning_sequence(self):
        """Scanning/Alert behavior"""
        logger.info("🎭 Playing SCANNING sequence...")

        try:
            # Raise periscope
            self.servo_controller.move_to(R2D2Component.PERISCOPE, 180)
            time.sleep(0.5)

            # 360-degree dome scan
            scan_angles = [0, 90, 180, 270, 360]
            for angle in scan_angles:
                self.servo_controller.move_to(R2D2Component.DOME_ROTATION, angle)
                time.sleep(0.8)

            # Activate radar eye during scan
            self.servo_controller.move_to(R2D2Component.RADAR_EYE, 180)
            time.sleep(0.5)
            self.servo_controller.move_to(R2D2Component.RADAR_EYE, 0)

            # Lower periscope and return dome to center
            self.servo_controller.move_to(R2D2Component.PERISCOPE, 0)
            self.servo_controller.move_to(R2D2Component.DOME_ROTATION, 0)

            logger.info("✅ Scanning sequence completed!")

        except Exception as e:
            logger.error(f"Scanning sequence failed: {e}")

    def maintenance_mode(self):
        """Full maintenance access mode"""
        logger.info("🎭 Entering MAINTENANCE mode...")

        try:
            # Open all access panels
            maintenance_movements = {
                # All dome panels
                R2D2Component.DOME_PANEL_1: 90,
                R2D2Component.DOME_PANEL_2: 90,
                R2D2Component.DOME_PANEL_3: 90,
                R2D2Component.DOME_PANEL_4: 90,
                R2D2Component.DOME_PANEL_5: 90,
                R2D2Component.DOME_PANEL_6: 90,
                R2D2Component.DOME_PANEL_7: 90,
                R2D2Component.DOME_PANEL_8: 90,

                # All utility arms
                R2D2Component.UTILITY_ARM_1: 90,
                R2D2Component.UTILITY_ARM_2: 90,
                R2D2Component.INTERFACE_ARM: 90,

                # Body panels
                R2D2Component.BODY_DOORS_L: 90,
                R2D2Component.BODY_DOORS_R: 90,

                # Extend center leg
                R2D2Component.CENTER_LEG: 180
            }

            self.servo_controller.move_multiple(maintenance_movements)
            time.sleep(2)

            logger.info("✅ Maintenance mode activated - All panels open")
            logger.info("   Run servo_controller.home_all_servos() to exit maintenance mode")

        except Exception as e:
            logger.error(f"Maintenance mode failed: {e}")

# Demo and test functions
def demo_r2d2_servos():
    """Comprehensive R2-D2 servo demonstration"""
    logger.info("🤖 Starting R2-D2 Servo Demonstration...")

    controller = R2D2ServoControllerSimple(simulation_mode=True)
    choreographer = R2D2Choreographer(controller)

    try:
        # Initial status
        controller.status_report()

        # Test individual movements
        logger.info("\n--- Testing Individual Movements ---")
        controller.move_to(R2D2Component.DOME_ROTATION, 90)
        time.sleep(1)

        controller.move_to(R2D2Component.DOME_PANEL_1, 120)
        time.sleep(1)

        controller.move_to(R2D2Component.UTILITY_ARM_1, 135)
        time.sleep(1)

        # Test multiple movements
        logger.info("\n--- Testing Simultaneous Movements ---")
        multi_movements = {
            R2D2Component.DOME_ROTATION: 180,
            R2D2Component.DOME_PANEL_2: 90,
            R2D2Component.DOME_PANEL_3: 90,
            R2D2Component.UTILITY_ARM_2: 120
        }
        controller.move_multiple(multi_movements)
        time.sleep(2)

        # Choreographed sequences
        logger.info("\n--- Testing Choreographed Sequences ---")
        choreographer.excited_sequence()
        time.sleep(2)

        choreographer.scanning_sequence()
        time.sleep(2)

        # Test emergency stop
        logger.info("\n--- Testing Emergency Stop ---")
        controller.move_to(R2D2Component.DOME_ROTATION, 270)
        time.sleep(0.2)
        controller.emergency_stop()
        time.sleep(1)
        controller.resume_operation()

        # Return to home
        logger.info("\n--- Returning to Home Position ---")
        controller.home_all_servos()
        time.sleep(2)

        # Final status
        controller.status_report()

        logger.info("🎉 Demo completed successfully!")

    except KeyboardInterrupt:
        logger.info("Demo interrupted by user")
    except Exception as e:
        logger.error(f"Demo failed: {e}")

if __name__ == "__main__":
    demo_r2d2_servos()