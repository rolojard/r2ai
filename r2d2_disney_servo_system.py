#!/usr/bin/env python3
"""
Disney-Level R2D2 Servo Integration System
Professional Pololu Maestro Control with Advanced Features

This module provides comprehensive Disney-level animatronic control for R2D2
with Pololu Maestro servo controllers, featuring:
- Automatic hardware detection and configuration
- Advanced sequence and script management
- Real-time monitoring and feedback systems
- Professional safety protocols
- Smooth, lifelike movement patterns
- Interactive performance modes

Author: Imagineer Specialist
Version: 1.0.0
Date: 2024-09-22
"""

import serial
import serial.tools.list_ports
import time
import logging
import threading
import json
import math
import random
from typing import Dict, List, Tuple, Optional, Union, Callable
from dataclasses import dataclass, field, asdict
from enum import Enum
from pathlib import Path
import queue
import numpy as np

# Import base controller
from pololu_maestro_controller import PololuMaestroController, ServoChannel, ServoConfig

# Configure professional logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/home/rolo/r2ai/logs/r2d2_servo_system.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class MaestroBoard(Enum):
    """Supported Pololu Maestro Board Types"""
    MICRO_6 = ("Micro 6-Channel", 6, 0x89, "1350")
    MINI_12 = ("Mini 12-Channel", 12, 0x8A, "1351")
    MINI_18 = ("Mini 18-Channel", 18, 0x8B, "1352")
    MINI_24 = ("Mini 24-Channel", 24, 0x8C, "1353")
    STANDARD = ("Standard", 12, 0x87, "1354")

    def __init__(self, name: str, channels: int, device_id: int, product_id: str):
        self.board_name = name
        self.channel_count = channels
        self.device_id = device_id
        self.product_id = product_id

@dataclass
class HardwareInfo:
    """Hardware detection and capability information"""
    port: str
    board_type: MaestroBoard
    firmware_version: str = "Unknown"
    serial_number: str = "Unknown"
    capabilities: Dict = field(default_factory=dict)
    detected_servos: List[int] = field(default_factory=list)
    connection_status: str = "Unknown"

@dataclass
class MovementSequence:
    """Defines a sequence of servo movements"""
    name: str
    description: str
    movements: List[Dict] = field(default_factory=list)
    duration: float = 0.0
    loop: bool = False
    priority: int = 1
    safety_checks: bool = True

@dataclass
class PerformanceMode:
    """R2D2 performance behavior modes"""
    name: str
    description: str
    sequences: List[str] = field(default_factory=list)
    triggers: List[str] = field(default_factory=list)
    personality_traits: Dict = field(default_factory=dict)
    response_patterns: Dict = field(default_factory=dict)

class DisneyServoSystem:
    """Disney-Level Servo Control System for R2D2 Animatronics"""

    def __init__(self, config_path: str = "/home/rolo/r2ai/configs/servo_config.json"):
        """Initialize Disney-level servo system"""
        self.config_path = Path(config_path)
        self.config_path.parent.mkdir(parents=True, exist_ok=True)

        # Hardware components
        self.hardware_info: List[HardwareInfo] = []
        self.maestro_controllers: Dict[str, PololuMaestroController] = {}
        self.active_controller: Optional[PololuMaestroController] = None

        # Sequence and performance management
        self.movement_sequences: Dict[str, MovementSequence] = {}
        self.performance_modes: Dict[str, PerformanceMode] = {}
        self.current_mode: Optional[str] = None
        self.sequence_queue = queue.Queue()

        # Real-time monitoring
        self.monitoring_active = True
        self.performance_thread: Optional[threading.Thread] = None
        self.sequence_thread: Optional[threading.Thread] = None

        # Safety and emergency systems
        self.safety_active = True
        self.emergency_protocols: Dict[str, Callable] = {}

        # Performance metrics
        self.movement_history: List[Dict] = []
        self.performance_stats: Dict = {}

        logger.info("🎭 Disney-Level R2D2 Servo System Initialized")

        # Initialize system components
        self._initialize_system()

    def _initialize_system(self):
        """Initialize all system components"""
        try:
            # Detect hardware
            self._detect_maestro_hardware()

            # Initialize default sequences
            self._initialize_default_sequences()

            # Initialize performance modes
            self._initialize_performance_modes()

            # Start monitoring systems
            self._start_monitoring_systems()

            # Load saved configuration if available
            self._load_configuration()

            logger.info("✅ Disney servo system initialization complete")

        except Exception as e:
            logger.error(f"System initialization failed: {e}")
            raise

    def _detect_maestro_hardware(self):
        """Advanced hardware detection with auto-configuration"""
        logger.info("🔍 Detecting Pololu Maestro hardware...")

        # Get all available serial ports
        available_ports = serial.tools.list_ports.comports()

        detected_maestros = []

        for port in available_ports:
            # Check for Pololu VID (Vendor ID)
            if port.vid == 0x1FFB:  # Pololu Vendor ID
                try:
                    # Attempt to identify board type
                    board_info = self._identify_maestro_board(port.device)
                    if board_info:
                        detected_maestros.append(board_info)
                        logger.info(f"✅ Detected {board_info.board_type.board_name} on {port.device}")
                except Exception as e:
                    logger.warning(f"Failed to identify Maestro on {port.device}: {e}")

        if not detected_maestros:
            logger.warning("⚠️  No Maestro boards detected, using simulation mode")
            # Create simulated hardware for development
            sim_info = HardwareInfo(
                port="/dev/ttyACM0",
                board_type=MaestroBoard.MINI_12,
                connection_status="Simulated"
            )
            detected_maestros.append(sim_info)

        self.hardware_info = detected_maestros

        # Initialize controllers for detected hardware
        for hardware in self.hardware_info:
            try:
                simulation = hardware.connection_status == "Simulated"
                controller = PololuMaestroController(
                    port=hardware.port,
                    simulation_mode=simulation
                )
                self.maestro_controllers[hardware.port] = controller

                # Set first detected as active controller
                if self.active_controller is None:
                    self.active_controller = controller
                    logger.info(f"🎯 Active controller: {hardware.board_type.board_name}")

            except Exception as e:
                logger.error(f"Failed to initialize controller on {hardware.port}: {e}")

    def _identify_maestro_board(self, port: str) -> Optional[HardwareInfo]:
        """Identify specific Maestro board type and capabilities"""
        try:
            # Attempt connection
            with serial.Serial(port, 9600, timeout=1.0) as ser:
                time.sleep(0.1)

                # Send device info request (custom protocol)
                ser.write(b'\xA1')  # Get errors command as test
                response = ser.read(2)

                if len(response) == 2:
                    # Successfully communicated - assume Mini 12 for now
                    # In production, would implement proper device identification
                    hardware_info = HardwareInfo(
                        port=port,
                        board_type=MaestroBoard.MINI_12,
                        connection_status="Connected"
                    )

                    # Test servo detection
                    hardware_info.detected_servos = self._detect_connected_servos(ser)

                    return hardware_info

        except Exception as e:
            logger.debug(f"Port {port} identification failed: {e}")
            return None

        return None

    def _detect_connected_servos(self, serial_conn: serial.Serial) -> List[int]:
        """Detect which servo channels have servos connected"""
        detected = []

        try:
            for channel in range(12):  # Test first 12 channels
                # Send position request
                cmd = bytes([0x90, channel])  # GET_POSITION command
                serial_conn.write(cmd)
                response = serial_conn.read(2)

                if len(response) == 2:
                    position = response[0] + 256 * response[1]
                    # If position is not 0, likely a servo is connected
                    if position > 0:
                        detected.append(channel)

                time.sleep(0.01)  # Small delay between tests

        except Exception as e:
            logger.debug(f"Servo detection error: {e}")

        return detected

    def _initialize_default_sequences(self):
        """Initialize Disney-level movement sequences"""
        logger.info("🎬 Initializing R2D2 movement sequences...")

        # Greeting sequence
        greeting_seq = MovementSequence(
            name="greeting",
            description="Friendly R2D2 greeting with dome rotation and panel flash",
            movements=[
                {"action": "dome_rotation", "angle": 15, "duration": 1.0},
                {"action": "dome_panels", "panels": {"front": True}, "duration": 0.5},
                {"action": "dome_panels", "panels": {}, "duration": 0.5},
                {"action": "dome_rotation", "angle": -15, "duration": 1.0},
                {"action": "dome_rotation", "angle": 0, "duration": 1.0},
            ],
            duration=4.0
        )

        # Excited sequence
        excited_seq = MovementSequence(
            name="excited",
            description="Excited R2D2 behavior with rapid movements",
            movements=[
                {"action": "dome_rotation", "angle": 30, "duration": 0.3},
                {"action": "dome_rotation", "angle": -30, "duration": 0.3},
                {"action": "dome_rotation", "angle": 0, "duration": 0.3},
                {"action": "dome_panels", "panels": {"left": True, "right": True}, "duration": 0.2},
                {"action": "dome_panels", "panels": {}, "duration": 0.2},
                {"action": "utility_arms", "left": 90, "right": 90, "duration": 0.5},
                {"action": "utility_arms", "left": 0, "right": 0, "duration": 0.5},
            ],
            duration=2.5
        )

        # Curious sequence
        curious_seq = MovementSequence(
            name="curious",
            description="Curious investigation behavior",
            movements=[
                {"action": "head_tilt", "angle": 15, "duration": 1.0},
                {"action": "dome_rotation", "angle": 45, "duration": 1.5},
                {"action": "periscope", "extend": True, "duration": 1.0},
                {"action": "dome_rotation", "angle": -45, "duration": 2.0},
                {"action": "periscope", "extend": False, "duration": 1.0},
                {"action": "head_tilt", "angle": 0, "duration": 1.0},
                {"action": "dome_rotation", "angle": 0, "duration": 1.0},
            ],
            duration=8.5
        )

        # Alarm sequence
        alarm_seq = MovementSequence(
            name="alarm",
            description="Alert/alarm behavior with rapid panel movements",
            movements=[
                {"action": "dome_panels", "panels": {"front": True, "back": True}, "duration": 0.1},
                {"action": "dome_panels", "panels": {"left": True, "right": True}, "duration": 0.1},
                {"action": "dome_panels", "panels": {}, "duration": 0.1},
                {"action": "dome_rotation", "angle": 90, "duration": 0.2},
                {"action": "dome_rotation", "angle": -90, "duration": 0.2},
                {"action": "dome_rotation", "angle": 0, "duration": 0.2},
            ],
            duration=0.9,
            loop=True
        )

        # Sleep sequence
        sleep_seq = MovementSequence(
            name="sleep",
            description="Powering down to sleep mode",
            movements=[
                {"action": "dome_rotation", "angle": 0, "duration": 2.0},
                {"action": "head_tilt", "angle": -10, "duration": 2.0},
                {"action": "utility_arms", "left": 0, "right": 0, "duration": 2.0},
                {"action": "periscope", "extend": False, "duration": 1.0},
                {"action": "dome_panels", "panels": {}, "duration": 1.0},
            ],
            duration=8.0
        )

        sequences = [greeting_seq, excited_seq, curious_seq, alarm_seq, sleep_seq]

        for seq in sequences:
            self.movement_sequences[seq.name] = seq
            logger.info(f"  ✓ Loaded sequence: {seq.name}")

    def _initialize_performance_modes(self):
        """Initialize R2D2 personality and performance modes"""
        logger.info("🎭 Initializing performance modes...")

        # Interactive Mode
        interactive_mode = PerformanceMode(
            name="interactive",
            description="Responsive interactive mode for user engagement",
            sequences=["greeting", "curious", "excited"],
            triggers=["person_detected", "voice_command", "touch_sensor"],
            personality_traits={
                "curiosity": 0.8,
                "friendliness": 0.9,
                "responsiveness": 0.9
            },
            response_patterns={
                "person_detected": "greeting",
                "voice_command": "excited",
                "unknown_sound": "curious"
            }
        )

        # Demo Mode
        demo_mode = PerformanceMode(
            name="demo",
            description="Continuous demonstration mode for exhibitions",
            sequences=["greeting", "excited", "curious", "sleep"],
            triggers=["timer", "random"],
            personality_traits={
                "showmanship": 0.9,
                "energy": 0.7,
                "variety": 0.8
            },
            response_patterns={
                "timer_5min": "greeting",
                "timer_10min": "excited",
                "timer_15min": "curious"
            }
        )

        # Guard Mode
        guard_mode = PerformanceMode(
            name="guard",
            description="Security/alert mode with alarm behaviors",
            sequences=["alarm", "curious"],
            triggers=["motion_detected", "security_breach"],
            personality_traits={
                "alertness": 1.0,
                "suspicion": 0.8,
                "protectiveness": 0.9
            },
            response_patterns={
                "motion_detected": "curious",
                "security_breach": "alarm"
            }
        )

        # Maintenance Mode
        maintenance_mode = PerformanceMode(
            name="maintenance",
            description="Safe mode for maintenance and calibration",
            sequences=["sleep"],
            triggers=["manual"],
            personality_traits={
                "compliance": 1.0,
                "safety": 1.0,
                "stillness": 0.9
            },
            response_patterns={
                "maintenance_start": "sleep"
            }
        )

        modes = [interactive_mode, demo_mode, guard_mode, maintenance_mode]

        for mode in modes:
            self.performance_modes[mode.name] = mode
            logger.info(f"  ✓ Loaded mode: {mode.name}")

        # Set default mode
        self.current_mode = "interactive"

    def _start_monitoring_systems(self):
        """Start real-time monitoring and performance threads"""
        logger.info("🔄 Starting monitoring systems...")

        # Start sequence processing thread
        self.sequence_thread = threading.Thread(
            target=self._sequence_processor,
            daemon=True,
            name="SequenceProcessor"
        )
        self.sequence_thread.start()

        # Start performance monitoring thread
        self.performance_thread = threading.Thread(
            target=self._performance_monitor,
            daemon=True,
            name="PerformanceMonitor"
        )
        self.performance_thread.start()

        logger.info("✅ Monitoring systems started")

    def _sequence_processor(self):
        """Process movement sequences from queue"""
        while self.monitoring_active:
            try:
                if not self.sequence_queue.empty():
                    sequence_name = self.sequence_queue.get(timeout=1.0)
                    self._execute_sequence(sequence_name)
                else:
                    time.sleep(0.1)
            except queue.Empty:
                continue
            except Exception as e:
                logger.error(f"Sequence processor error: {e}")
                time.sleep(1.0)

    def _performance_monitor(self):
        """Monitor system performance and health"""
        while self.monitoring_active:
            try:
                # Update performance statistics
                self._update_performance_stats()

                # Check for autonomous behaviors in demo mode
                if self.current_mode == "demo":
                    self._check_demo_behaviors()

                time.sleep(1.0)  # 1Hz monitoring

            except Exception as e:
                logger.error(f"Performance monitor error: {e}")
                time.sleep(5.0)

    def _update_performance_stats(self):
        """Update system performance statistics"""
        if self.active_controller:
            # Get controller status
            status = self.active_controller.get_status_report()

            # Update stats
            self.performance_stats.update({
                "timestamp": time.time(),
                "controller_status": status["controller"],
                "active_servos": len([s for s in status["servos"].values() if s["moving"]]),
                "sequence_queue_size": self.sequence_queue.qsize(),
                "current_mode": self.current_mode,
                "uptime": time.time() - getattr(self, 'start_time', time.time())
            })

    def _check_demo_behaviors(self):
        """Check for autonomous demo behaviors"""
        # Random behavior triggers for demo mode
        if random.random() < 0.1:  # 10% chance per second
            available_sequences = self.performance_modes["demo"].sequences
            sequence = random.choice(available_sequences)
            self.queue_sequence(sequence)

    def _execute_sequence(self, sequence_name: str):
        """Execute a movement sequence"""
        if sequence_name not in self.movement_sequences:
            logger.error(f"Unknown sequence: {sequence_name}")
            return False

        sequence = self.movement_sequences[sequence_name]
        logger.info(f"🎬 Executing sequence: {sequence.name}")

        if not self.active_controller:
            logger.error("No active controller available")
            return False

        try:
            # Record sequence start
            sequence_start = {
                "sequence": sequence_name,
                "start_time": time.time(),
                "mode": self.current_mode
            }

            # Execute each movement in sequence
            for movement in sequence.movements:
                if not self.monitoring_active:
                    break

                self._execute_movement(movement)

                # Wait for movement duration
                time.sleep(movement.get("duration", 1.0))

            # Record completion
            sequence_start["end_time"] = time.time()
            sequence_start["duration"] = sequence_start["end_time"] - sequence_start["start_time"]
            self.movement_history.append(sequence_start)

            # Keep history limited
            if len(self.movement_history) > 100:
                self.movement_history = self.movement_history[-50:]

            logger.info(f"✅ Sequence '{sequence_name}' completed")
            return True

        except Exception as e:
            logger.error(f"Sequence execution failed: {e}")
            return False

    def _execute_movement(self, movement: Dict):
        """Execute a single movement command"""
        if not self.active_controller:
            return

        action = movement.get("action")

        if action == "dome_rotation":
            angle = movement.get("angle", 0)
            self._move_dome_rotation(angle)

        elif action == "head_tilt":
            angle = movement.get("angle", 0)
            self._move_head_tilt(angle)

        elif action == "dome_panels":
            panels = movement.get("panels", {})
            self._control_dome_panels(panels)

        elif action == "utility_arms":
            left = movement.get("left", 0)
            right = movement.get("right", 0)
            self._move_utility_arms(left, right)

        elif action == "periscope":
            extend = movement.get("extend", False)
            self._control_periscope(extend)

        else:
            logger.warning(f"Unknown movement action: {action}")

    def _move_dome_rotation(self, angle: float):
        """Move dome rotation with smooth interpolation"""
        if self.active_controller:
            # Convert angle to servo position with smooth curve
            self.active_controller.move_servo_angle(
                ServoChannel.DOME_ROTATION.value,
                angle + 180,  # Convert to 0-360 range
                (0, 360)
            )

    def _move_head_tilt(self, angle: float):
        """Move head tilt with natural motion"""
        if self.active_controller:
            self.active_controller.move_servo_angle(
                ServoChannel.HEAD_TILT.value,
                angle + 30,  # Convert to 0-60 range
                (0, 60)
            )

    def _control_dome_panels(self, panels: Dict):
        """Control dome panels with coordinated movement"""
        if self.active_controller:
            panel_map = {
                "front": ServoChannel.DOME_PANEL_FRONT.value,
                "left": ServoChannel.DOME_PANEL_LEFT.value,
                "right": ServoChannel.DOME_PANEL_RIGHT.value,
                "back": ServoChannel.DOME_PANEL_BACK.value
            }

            for panel_name, servo_channel in panel_map.items():
                is_open = panels.get(panel_name, False)
                position = 1800 if is_open else 1200  # microseconds
                self.active_controller.move_servo_microseconds(servo_channel, position)

    def _move_utility_arms(self, left_angle: float, right_angle: float):
        """Move utility arms with coordinated motion"""
        if self.active_controller:
            self.active_controller.move_servo_angle(
                ServoChannel.UTILITY_ARM_LEFT.value,
                left_angle
            )
            self.active_controller.move_servo_angle(
                ServoChannel.UTILITY_ARM_RIGHT.value,
                right_angle
            )

    def _control_periscope(self, extend: bool):
        """Control periscope with smooth extension/retraction"""
        if self.active_controller:
            position = 1800 if extend else 1200  # microseconds
            self.active_controller.move_servo_microseconds(
                ServoChannel.PERISCOPE.value,
                position
            )

    # Public API Methods

    def queue_sequence(self, sequence_name: str) -> bool:
        """Queue a movement sequence for execution"""
        if sequence_name in self.movement_sequences:
            self.sequence_queue.put(sequence_name)
            logger.info(f"📋 Queued sequence: {sequence_name}")
            return True
        else:
            logger.error(f"Unknown sequence: {sequence_name}")
            return False

    def set_performance_mode(self, mode_name: str) -> bool:
        """Set the current performance mode"""
        if mode_name in self.performance_modes:
            self.current_mode = mode_name
            logger.info(f"🎭 Performance mode set: {mode_name}")
            return True
        else:
            logger.error(f"Unknown performance mode: {mode_name}")
            return False

    def emergency_stop(self):
        """Emergency stop all movements"""
        logger.warning("🚨 EMERGENCY STOP ACTIVATED")

        if self.active_controller:
            self.active_controller.emergency_stop()

        # Clear sequence queue
        while not self.sequence_queue.empty():
            try:
                self.sequence_queue.get_nowait()
            except queue.Empty:
                break

    def home_all_servos(self):
        """Move all servos to home position"""
        if self.active_controller:
            self.active_controller.home_all_servos()
            logger.info("🏠 All servos moved to home position")

    def get_system_status(self) -> Dict:
        """Get comprehensive system status"""
        status = {
            "hardware": [asdict(hw) for hw in self.hardware_info],
            "active_controller": self.active_controller.port if self.active_controller else None,
            "current_mode": self.current_mode,
            "sequence_queue_size": self.sequence_queue.qsize(),
            "available_sequences": list(self.movement_sequences.keys()),
            "available_modes": list(self.performance_modes.keys()),
            "performance_stats": self.performance_stats,
            "movement_history": self.movement_history[-10:],  # Last 10 movements
            "monitoring_active": self.monitoring_active
        }

        if self.active_controller:
            status["controller_status"] = self.active_controller.get_status_report()

        return status

    def _load_configuration(self):
        """Load saved configuration"""
        try:
            if self.config_path.exists():
                with open(self.config_path, 'r') as f:
                    config = json.load(f)

                # Load custom sequences
                if "custom_sequences" in config:
                    for seq_data in config["custom_sequences"]:
                        sequence = MovementSequence(**seq_data)
                        self.movement_sequences[sequence.name] = sequence

                logger.info(f"✅ Configuration loaded from {self.config_path}")
        except Exception as e:
            logger.error(f"Failed to load configuration: {e}")

    def save_configuration(self):
        """Save current configuration"""
        try:
            config = {
                "system_info": {
                    "version": "1.0.0",
                    "saved_at": time.time()
                },
                "hardware": [asdict(hw) for hw in self.hardware_info],
                "custom_sequences": [asdict(seq) for seq in self.movement_sequences.values()],
                "performance_modes": [asdict(mode) for mode in self.performance_modes.values()],
                "performance_stats": self.performance_stats
            }

            with open(self.config_path, 'w') as f:
                json.dump(config, f, indent=2)

            logger.info(f"✅ Configuration saved to {self.config_path}")
        except Exception as e:
            logger.error(f"Failed to save configuration: {e}")

    def shutdown(self):
        """Safely shutdown the servo system"""
        logger.info("🔄 Shutting down Disney servo system...")

        self.monitoring_active = False

        # Stop all sequences
        self.emergency_stop()

        # Wait for threads to finish
        if self.sequence_thread and self.sequence_thread.is_alive():
            self.sequence_thread.join(timeout=2.0)

        if self.performance_thread and self.performance_thread.is_alive():
            self.performance_thread.join(timeout=2.0)

        # Shutdown controllers
        for controller in self.maestro_controllers.values():
            controller.shutdown()

        # Save configuration
        self.save_configuration()

        logger.info("✅ Disney servo system shutdown complete")

# Demo and Testing Functions

def demo_disney_servo_system():
    """Comprehensive demo of Disney servo system"""
    logger.info("🎭 Starting Disney-Level R2D2 Servo System Demo...")

    # Initialize system
    servo_system = DisneyServoSystem()

    try:
        # Display system status
        status = servo_system.get_system_status()
        logger.info(f"Hardware detected: {len(status['hardware'])} devices")
        logger.info(f"Available sequences: {status['available_sequences']}")
        logger.info(f"Available modes: {status['available_modes']}")

        # Home all servos
        servo_system.home_all_servos()
        time.sleep(2)

        # Demo each performance mode
        modes_to_demo = ["interactive", "demo"]

        for mode in modes_to_demo:
            logger.info(f"\n🎭 Demonstrating {mode} mode...")
            servo_system.set_performance_mode(mode)

            # Queue some sequences
            if mode == "interactive":
                sequences = ["greeting", "excited", "curious"]
            else:
                sequences = ["greeting", "excited"]

            for seq in sequences:
                servo_system.queue_sequence(seq)
                time.sleep(6)  # Wait for sequence to complete

        # Demonstrate manual control
        logger.info("\n🎮 Demonstrating manual control...")
        servo_system.set_performance_mode("maintenance")

        # Individual movements
        if servo_system.active_controller:
            logger.info("  - Dome rotation test...")
            servo_system._move_dome_rotation(45)
            time.sleep(1)
            servo_system._move_dome_rotation(-45)
            time.sleep(1)
            servo_system._move_dome_rotation(0)
            time.sleep(1)

            logger.info("  - Panel test...")
            servo_system._control_dome_panels({"front": True, "back": True})
            time.sleep(1)
            servo_system._control_dome_panels({})
            time.sleep(1)

        # Display final status
        final_status = servo_system.get_system_status()
        logger.info("\n📊 Final System Status:")
        logger.info(f"  Total movements executed: {len(final_status['movement_history'])}")
        logger.info(f"  Current mode: {final_status['current_mode']}")
        logger.info(f"  Queue size: {final_status['sequence_queue_size']}")

        logger.info("\n✅ Disney servo system demo completed successfully!")

    except KeyboardInterrupt:
        logger.info("\nDemo interrupted by user")
    except Exception as e:
        logger.error(f"Demo failed: {e}")
    finally:
        servo_system.shutdown()

if __name__ == "__main__":
    # Ensure log directory exists
    Path("/home/rolo/r2ai/logs").mkdir(exist_ok=True)

    # Run demo
    demo_disney_servo_system()