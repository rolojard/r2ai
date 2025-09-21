#!/usr/bin/env python3
"""
Pololu Maestro Mini 12-Channel USB Servo Controller Integration
Professional R2-D2 Servo Control System with Safety Features

This module provides comprehensive control for the Pololu Maestro Mini 12-Channel
USB servo controller, specifically designed for R2-D2 animatronics with:
- USB serial communication interface
- 12 servo channels with quarter-microsecond resolution
- Position, speed, and acceleration control
- Safety systems with emergency stop
- Real-time position feedback and monitoring
- Hardware-specific safety limits and validation

HARDWARE SPECIFICATIONS:
- Pololu Maestro Mini 12-Channel USB Servo Controller
- Communication: USB serial interface (/dev/ttyACM0 typical)
- Position control: 0.25µs resolution (quarter-microseconds)
- Range: 64-8000 quarter-microseconds (16-2000µs)
- Speed control: 0-255 (0=unlimited, 1=slowest)
- Acceleration: 0-255 (0=unlimited, 1=slowest)
"""

import serial
import time
import logging
import threading
from typing import Dict, List, Tuple, Optional, Union
from dataclasses import dataclass, field
from enum import Enum
import json

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MaestroCommand(Enum):
    """Pololu Maestro Protocol Commands"""
    SET_TARGET = 0x84           # Set target position
    SET_SPEED = 0x87            # Set speed limit
    SET_ACCELERATION = 0x89     # Set acceleration limit
    GET_POSITION = 0x90         # Get current position
    GET_MOVING_STATE = 0x93     # Check if servos are moving
    GET_ERRORS = 0xA1           # Get error status
    GO_HOME = 0xA2              # Move all servos to home

class ServoChannel(Enum):
    """R2-D2 Servo Channel Assignments for 12-Channel Maestro"""
    # Primary Movement Servos (Channels 0-5)
    DOME_ROTATION = 0           # Main dome rotation
    HEAD_TILT = 1              # Head tilt mechanism
    PERISCOPE = 2              # Periscope raise/lower
    RADAR_EYE = 3              # Radar eye rotation
    UTILITY_ARM_LEFT = 4        # Left utility arm
    UTILITY_ARM_RIGHT = 5       # Right utility arm

    # Panel Servos (Channels 6-11)
    DOME_PANEL_FRONT = 6        # Front dome panel
    DOME_PANEL_LEFT = 7         # Left dome panel
    DOME_PANEL_RIGHT = 8        # Right dome panel
    DOME_PANEL_BACK = 9         # Back dome panel
    BODY_DOOR_LEFT = 10         # Left body access door
    BODY_DOOR_RIGHT = 11        # Right body access door

@dataclass
class ServoConfig:
    """Configuration for individual servo with safety limits"""
    channel: int
    name: str
    min_position: int = 1000    # Minimum position in quarter-microseconds (250µs)
    max_position: int = 8000    # Maximum position in quarter-microseconds (2000µs)
    home_position: int = 6000   # Home position in quarter-microseconds (1500µs)
    max_speed: int = 50         # Speed limit (0-255, 0=unlimited)
    acceleration: int = 20      # Acceleration limit (0-255, 0=unlimited)
    reverse: bool = False       # Reverse servo direction
    enabled: bool = True        # Enable/disable servo

    def validate_position(self, position: int) -> int:
        """Validate and clamp position to safe range"""
        if not self.enabled:
            return self.home_position
        return max(self.min_position, min(self.max_position, position))

    def microseconds_to_quarters(self, microseconds: float) -> int:
        """Convert microseconds to quarter-microseconds"""
        return int(microseconds * 4)

    def quarters_to_microseconds(self, quarters: int) -> float:
        """Convert quarter-microseconds to microseconds"""
        return quarters / 4.0

@dataclass
class ServoStatus:
    """Current status of a servo"""
    channel: int
    position: int = 0           # Current position in quarter-microseconds
    target: int = 0             # Target position in quarter-microseconds
    moving: bool = False        # Whether servo is currently moving
    enabled: bool = True        # Whether servo is enabled
    last_update: float = 0      # Timestamp of last update

class PololuMaestroController:
    """Pololu Maestro Mini 12-Channel USB Servo Controller"""

    def __init__(self, port: str = "/dev/ttyACM0", baudrate: int = 9600, simulation_mode: bool = False):
        """
        Initialize Pololu Maestro controller

        Args:
            port: Serial port path (typically /dev/ttyACM0)
            baudrate: Serial communication baudrate (9600 default)
            simulation_mode: Run in simulation mode without hardware
        """
        self.port = port
        self.baudrate = baudrate
        self.simulation_mode = simulation_mode
        self.serial_connection: Optional[serial.Serial] = None
        self.servo_configs: Dict[int, ServoConfig] = {}
        self.servo_status: Dict[int, ServoStatus] = {}
        self.emergency_stop_active = False
        self.monitoring_thread: Optional[threading.Thread] = None
        self.is_running = True
        self._lock = threading.Lock()

        # Initialize servo configurations
        self._initialize_servo_configs()

        # Initialize hardware connection
        self._initialize_connection()

        # Start monitoring thread
        self._start_monitoring()

        logger.info(f"Pololu Maestro Controller initialized - Port: {port}, Simulation: {simulation_mode}")

    def _initialize_servo_configs(self):
        """Initialize default servo configurations for R2-D2"""
        servo_configs = [
            # Primary Movement Servos
            ServoConfig(0, "Dome Rotation", 2000, 8000, 6000, 30, 15),
            ServoConfig(1, "Head Tilt", 4000, 8000, 6000, 40, 20),
            ServoConfig(2, "Periscope", 4000, 7500, 4000, 50, 25),
            ServoConfig(3, "Radar Eye", 4000, 8000, 6000, 60, 30),
            ServoConfig(4, "Utility Arm Left", 2000, 8000, 4000, 40, 20),
            ServoConfig(5, "Utility Arm Right", 2000, 8000, 4000, 40, 20),

            # Panel Servos (faster movement for panels)
            ServoConfig(6, "Dome Panel Front", 4000, 7000, 4000, 80, 40),
            ServoConfig(7, "Dome Panel Left", 4000, 7000, 4000, 80, 40),
            ServoConfig(8, "Dome Panel Right", 4000, 7000, 4000, 80, 40),
            ServoConfig(9, "Dome Panel Back", 4000, 7000, 4000, 80, 40),
            ServoConfig(10, "Body Door Left", 4000, 7000, 4000, 60, 30),
            ServoConfig(11, "Body Door Right", 4000, 7000, 4000, 60, 30),
        ]

        for config in servo_configs:
            self.servo_configs[config.channel] = config
            self.servo_status[config.channel] = ServoStatus(
                channel=config.channel,
                position=config.home_position,
                target=config.home_position
            )

    def _initialize_connection(self):
        """Initialize serial connection to Maestro controller"""
        if self.simulation_mode:
            logger.info("Running in simulation mode - no hardware connection")
            return

        try:
            self.serial_connection = serial.Serial(
                port=self.port,
                baudrate=self.baudrate,
                timeout=1.0,
                write_timeout=1.0
            )
            # Wait for connection to stabilize
            time.sleep(0.1)

            # Test connection by getting error status
            self._send_command(MaestroCommand.GET_ERRORS.value)

            logger.info(f"✅ Connected to Pololu Maestro on {self.port}")

        except Exception as e:
            logger.error(f"Failed to connect to Maestro controller: {e}")
            logger.info("Falling back to simulation mode")
            self.simulation_mode = True
            self.serial_connection = None

    def _send_command(self, *args) -> bytes:
        """Send command to Maestro controller"""
        if self.simulation_mode or self.serial_connection is None:
            return b''

        try:
            with self._lock:
                command = bytes(args)
                self.serial_connection.write(command)
                self.serial_connection.flush()

                # Read response if expected
                if args[0] in [MaestroCommand.GET_POSITION.value,
                               MaestroCommand.GET_MOVING_STATE.value,
                               MaestroCommand.GET_ERRORS.value]:
                    response = self.serial_connection.read(2)
                    return response

        except Exception as e:
            logger.error(f"Command send failed: {e}")
            return b''

        return b''

    def _start_monitoring(self):
        """Start servo monitoring thread"""
        if self.monitoring_thread is None:
            self.monitoring_thread = threading.Thread(
                target=self._monitoring_loop,
                daemon=True,
                name="MaestroMonitor"
            )
            self.monitoring_thread.start()

    def _monitoring_loop(self):
        """Main monitoring loop for servo status"""
        while self.is_running:
            try:
                if not self.simulation_mode and not self.emergency_stop_active:
                    # Update servo positions
                    for channel in range(12):
                        position = self._get_servo_position(channel)
                        if position is not None:
                            with self._lock:
                                self.servo_status[channel].position = position
                                self.servo_status[channel].last_update = time.time()

                time.sleep(0.1)  # 10Hz monitoring rate

            except Exception as e:
                logger.error(f"Monitoring loop error: {e}")
                time.sleep(1.0)

    def _get_servo_position(self, channel: int) -> Optional[int]:
        """Get current servo position"""
        if channel < 0 or channel > 11:
            return None

        response = self._send_command(MaestroCommand.GET_POSITION.value, channel)
        if len(response) == 2:
            return response[0] + 256 * response[1]
        return None

    def set_servo_position(self, channel: int, position: int, validate: bool = True) -> bool:
        """
        Set servo position with safety validation

        Args:
            channel: Servo channel (0-11)
            position: Target position in quarter-microseconds
            validate: Apply safety validation

        Returns:
            True if command was sent successfully
        """
        if self.emergency_stop_active:
            logger.warning("Cannot move servos - emergency stop active")
            return False

        if channel not in self.servo_configs:
            logger.error(f"Invalid servo channel: {channel}")
            return False

        config = self.servo_configs[channel]

        if not config.enabled:
            logger.warning(f"Servo {channel} ({config.name}) is disabled")
            return False

        # Apply safety validation
        if validate:
            position = config.validate_position(position)

        # Reverse servo direction if configured
        if config.reverse:
            center = (config.min_position + config.max_position) // 2
            position = center + (center - position)

        # Send position command
        success = self._send_position_command(channel, position)

        if success:
            with self._lock:
                self.servo_status[channel].target = position

            if self.simulation_mode:
                logger.info(f"[SIM] Servo {channel} ({config.name}): {position/4:.1f}µs")
            else:
                logger.debug(f"Servo {channel} ({config.name}): {position/4:.1f}µs")

        return success

    def _send_position_command(self, channel: int, position: int) -> bool:
        """Send position command to specific servo"""
        try:
            # Position is sent as 14-bit value (0-16383)
            # Split into two 7-bit values
            low_byte = position & 0x7F
            high_byte = (position >> 7) & 0x7F

            self._send_command(
                MaestroCommand.SET_TARGET.value,
                channel,
                low_byte,
                high_byte
            )
            return True

        except Exception as e:
            logger.error(f"Failed to send position command: {e}")
            return False

    def set_servo_speed(self, channel: int, speed: int) -> bool:
        """Set servo speed limit (0-255, 0=unlimited)"""
        if channel not in self.servo_configs:
            return False

        try:
            self._send_command(
                MaestroCommand.SET_SPEED.value,
                channel,
                speed & 0x7F,
                (speed >> 7) & 0x7F
            )
            self.servo_configs[channel].max_speed = speed
            return True

        except Exception as e:
            logger.error(f"Failed to set servo speed: {e}")
            return False

    def set_servo_acceleration(self, channel: int, acceleration: int) -> bool:
        """Set servo acceleration limit (0-255, 0=unlimited)"""
        if channel not in self.servo_configs:
            return False

        try:
            self._send_command(
                MaestroCommand.SET_ACCELERATION.value,
                channel,
                acceleration & 0x7F,
                (acceleration >> 7) & 0x7F
            )
            self.servo_configs[channel].acceleration = acceleration
            return True

        except Exception as e:
            logger.error(f"Failed to set servo acceleration: {e}")
            return False

    def move_servo_microseconds(self, channel: int, microseconds: float) -> bool:
        """Move servo to position specified in microseconds"""
        if channel not in self.servo_configs:
            return False

        config = self.servo_configs[channel]
        quarters = config.microseconds_to_quarters(microseconds)
        return self.set_servo_position(channel, quarters)

    def move_servo_angle(self, channel: int, angle: float, angle_range: Tuple[float, float] = (0, 180)) -> bool:
        """
        Move servo to angle position

        Args:
            channel: Servo channel
            angle: Target angle in degrees
            angle_range: Min/max angle range (default 0-180 degrees)
        """
        if channel not in self.servo_configs:
            return False

        config = self.servo_configs[channel]
        min_angle, max_angle = angle_range

        # Clamp angle to range
        angle = max(min_angle, min(max_angle, angle))

        # Convert angle to position
        angle_fraction = (angle - min_angle) / (max_angle - min_angle)
        position_range = config.max_position - config.min_position
        position = config.min_position + int(angle_fraction * position_range)

        return self.set_servo_position(channel, position)

    def get_servo_position_microseconds(self, channel: int) -> Optional[float]:
        """Get servo position in microseconds"""
        if channel not in self.servo_status:
            return None

        with self._lock:
            quarters = self.servo_status[channel].position

        return quarters / 4.0

    def is_servo_moving(self, channel: int) -> bool:
        """Check if servo is currently moving"""
        if self.simulation_mode:
            return False

        response = self._send_command(MaestroCommand.GET_MOVING_STATE.value)
        if len(response) == 2:
            moving_state = response[0] + 256 * response[1]
            return bool(moving_state & (1 << channel))

        return False

    def are_any_servos_moving(self) -> bool:
        """Check if any servos are currently moving"""
        if self.simulation_mode:
            return False

        response = self._send_command(MaestroCommand.GET_MOVING_STATE.value)
        if len(response) == 2:
            moving_state = response[0] + 256 * response[1]
            return moving_state != 0

        return False

    def home_all_servos(self):
        """Move all servos to home position"""
        logger.info("Moving all servos to home position...")

        for channel, config in self.servo_configs.items():
            if config.enabled:
                self.set_servo_position(channel, config.home_position)

        logger.info("✅ All servos moved to home position")

    def emergency_stop(self):
        """Emergency stop all servo movement"""
        self.emergency_stop_active = True

        # Send stop command to all servos
        if not self.simulation_mode:
            try:
                # Set all targets to current positions to stop movement
                for channel in range(12):
                    current_pos = self._get_servo_position(channel)
                    if current_pos is not None:
                        self._send_position_command(channel, current_pos)
            except Exception as e:
                logger.error(f"Emergency stop command failed: {e}")

        logger.warning("🚨 EMERGENCY STOP ACTIVATED - All servo movement halted")

    def resume_operation(self):
        """Resume normal operation after emergency stop"""
        self.emergency_stop_active = False
        logger.info("✅ Emergency stop cleared - Resuming normal operation")

    def get_error_status(self) -> int:
        """Get error status from Maestro controller"""
        if self.simulation_mode:
            return 0

        response = self._send_command(MaestroCommand.GET_ERRORS.value)
        if len(response) == 2:
            return response[0] + 256 * response[1]

        return 0

    def get_status_report(self) -> Dict:
        """Generate comprehensive status report"""
        report = {
            "controller": {
                "port": self.port,
                "simulation_mode": self.simulation_mode,
                "emergency_stop": self.emergency_stop_active,
                "connected": self.serial_connection is not None
            },
            "servos": {}
        }

        with self._lock:
            for channel, config in self.servo_configs.items():
                status = self.servo_status[channel]
                report["servos"][channel] = {
                    "name": config.name,
                    "enabled": config.enabled,
                    "position_us": status.position / 4.0,
                    "target_us": status.target / 4.0,
                    "home_us": config.home_position / 4.0,
                    "range_us": [config.min_position / 4.0, config.max_position / 4.0],
                    "moving": self.is_servo_moving(channel) if not self.simulation_mode else False,
                    "last_update": status.last_update
                }

        return report

    def save_configuration(self, filename: str):
        """Save servo configuration to JSON file"""
        config_data = {
            "port": self.port,
            "baudrate": self.baudrate,
            "servos": {}
        }

        for channel, config in self.servo_configs.items():
            config_data["servos"][channel] = {
                "name": config.name,
                "min_position": config.min_position,
                "max_position": config.max_position,
                "home_position": config.home_position,
                "max_speed": config.max_speed,
                "acceleration": config.acceleration,
                "reverse": config.reverse,
                "enabled": config.enabled
            }

        with open(filename, 'w') as f:
            json.dump(config_data, f, indent=2)

        logger.info(f"Configuration saved to {filename}")

    def load_configuration(self, filename: str):
        """Load servo configuration from JSON file"""
        try:
            with open(filename, 'r') as f:
                config_data = json.load(f)

            # Update servo configurations
            for channel_str, servo_data in config_data.get("servos", {}).items():
                channel = int(channel_str)
                if channel in self.servo_configs:
                    config = self.servo_configs[channel]
                    config.name = servo_data.get("name", config.name)
                    config.min_position = servo_data.get("min_position", config.min_position)
                    config.max_position = servo_data.get("max_position", config.max_position)
                    config.home_position = servo_data.get("home_position", config.home_position)
                    config.max_speed = servo_data.get("max_speed", config.max_speed)
                    config.acceleration = servo_data.get("acceleration", config.acceleration)
                    config.reverse = servo_data.get("reverse", config.reverse)
                    config.enabled = servo_data.get("enabled", config.enabled)

            logger.info(f"Configuration loaded from {filename}")

        except Exception as e:
            logger.error(f"Failed to load configuration: {e}")

    def shutdown(self):
        """Safely shutdown the controller"""
        logger.info("Shutting down Pololu Maestro controller...")

        self.is_running = False

        # Wait for monitoring thread to stop
        if self.monitoring_thread and self.monitoring_thread.is_alive():
            self.monitoring_thread.join(timeout=2.0)

        # Close serial connection
        if self.serial_connection:
            try:
                self.serial_connection.close()
            except:
                pass

        logger.info("✅ Pololu Maestro controller shutdown complete")

# Convenience functions for R2-D2 specific movements
class R2D2MaestroInterface:
    """High-level R2-D2 interface for Pololu Maestro controller"""

    def __init__(self, controller: PololuMaestroController):
        self.controller = controller

    def dome_rotation(self, angle: float):
        """Rotate dome to specific angle (-180 to 180 degrees)"""
        return self.controller.move_servo_angle(
            ServoChannel.DOME_ROTATION.value,
            angle + 180,  # Convert to 0-360 range
            (0, 360)
        )

    def head_tilt(self, angle: float):
        """Tilt head (-30 to 30 degrees)"""
        return self.controller.move_servo_angle(
            ServoChannel.HEAD_TILT.value,
            angle + 30,  # Convert to 0-60 range
            (0, 60)
        )

    def periscope_extend(self, extend: bool):
        """Extend or retract periscope"""
        position = 1800 if extend else 1200  # microseconds
        return self.controller.move_servo_microseconds(
            ServoChannel.PERISCOPE.value,
            position
        )

    def utility_arms(self, left_angle: float, right_angle: float):
        """Control both utility arms (0-180 degrees)"""
        left_success = self.controller.move_servo_angle(
            ServoChannel.UTILITY_ARM_LEFT.value,
            left_angle
        )
        right_success = self.controller.move_servo_angle(
            ServoChannel.UTILITY_ARM_RIGHT.value,
            right_angle
        )
        return left_success and right_success

    def dome_panels(self, front: bool = False, left: bool = False,
                   right: bool = False, back: bool = False):
        """Control dome panels (True = open, False = closed)"""
        panels = [
            (ServoChannel.DOME_PANEL_FRONT.value, front),
            (ServoChannel.DOME_PANEL_LEFT.value, left),
            (ServoChannel.DOME_PANEL_RIGHT.value, right),
            (ServoChannel.DOME_PANEL_BACK.value, back)
        ]

        success = True
        for channel, open_panel in panels:
            position = 1800 if open_panel else 1200  # microseconds
            success &= self.controller.move_servo_microseconds(channel, position)

        return success

    def body_doors(self, left: bool = False, right: bool = False):
        """Control body access doors"""
        left_success = self.controller.move_servo_microseconds(
            ServoChannel.BODY_DOOR_LEFT.value,
            1800 if left else 1200
        )
        right_success = self.controller.move_servo_microseconds(
            ServoChannel.BODY_DOOR_RIGHT.value,
            1800 if right else 1200
        )
        return left_success and right_success

# Demo function for testing
def demo_pololu_maestro():
    """Demonstration of Pololu Maestro functionality"""
    logger.info("🤖 Starting Pololu Maestro Demo...")

    # Initialize controller
    controller = PololuMaestroController(simulation_mode=True)
    r2d2 = R2D2MaestroInterface(controller)

    try:
        # Home all servos
        controller.home_all_servos()
        time.sleep(2)

        # Test dome rotation
        logger.info("Testing dome rotation...")
        r2d2.dome_rotation(45)
        time.sleep(1)
        r2d2.dome_rotation(-45)
        time.sleep(1)
        r2d2.dome_rotation(0)
        time.sleep(1)

        # Test panel movements
        logger.info("Testing dome panels...")
        r2d2.dome_panels(front=True, left=True)
        time.sleep(1)
        r2d2.dome_panels(right=True, back=True)
        time.sleep(1)
        r2d2.dome_panels()  # Close all
        time.sleep(1)

        # Test utility arms
        logger.info("Testing utility arms...")
        r2d2.utility_arms(90, 90)
        time.sleep(1)
        r2d2.utility_arms(0, 0)
        time.sleep(1)

        # Test periscope
        logger.info("Testing periscope...")
        r2d2.periscope_extend(True)
        time.sleep(1)
        r2d2.periscope_extend(False)
        time.sleep(1)

        # Print status report
        logger.info("\n--- Status Report ---")
        status = controller.get_status_report()
        for channel, servo_info in status["servos"].items():
            logger.info(f"Servo {channel}: {servo_info['name']} - {servo_info['position_us']:.1f}µs")

        logger.info("✅ Demo completed successfully!")

    except KeyboardInterrupt:
        logger.info("Demo interrupted by user")
    except Exception as e:
        logger.error(f"Demo failed: {e}")
    finally:
        controller.shutdown()

if __name__ == "__main__":
    demo_pololu_maestro()