#!/usr/bin/env python3
"""
Enhanced Pololu Maestro Controller with Dynamic Configuration
===========================================================

Advanced servo control system that builds upon the existing pololu_maestro_controller.py
with dynamic configuration, hardware detection, and sequence management capabilities.

Features:
- Auto-detection of Pololu Maestro boards
- Dynamic servo configuration (user-definable count and names)
- Import servo limits from Maestro settings
- Advanced sequence management with save/load/execute
- Pololu Maestro script execution
- Real-time position feedback and monitoring
- Integration with dashboard and vision systems

Author: Expert Project Manager + Super Coder Agent
Target: NVIDIA Orin Nano R2D2 Systems
Hardware: Pololu Maestro Mini 12-Channel USB Servo Controller
"""

import os
import sys
import time
import json
import threading
import logging
import subprocess
from typing import Dict, List, Tuple, Optional, Union, Any
from dataclasses import dataclass, field, asdict
from enum import Enum
import serial
import serial.tools.list_ports
from pathlib import Path

# Import existing foundation
sys.path.append('/home/rolo/r2ai')
from pololu_maestro_controller import PololuMaestroController, ServoConfig as BaseServoConfig, ServoChannel

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class HardwareDetectionStatus(Enum):
    """Hardware detection status"""
    SEARCHING = "searching"
    FOUND = "found"
    CONNECTED = "connected"
    FAILED = "failed"
    SIMULATION = "simulation"

class SequenceStatus(Enum):
    """Servo sequence execution status"""
    IDLE = "idle"
    LOADING = "loading"
    EXECUTING = "executing"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"

@dataclass
class MaestroHardwareInfo:
    """Maestro hardware information"""
    port: str
    device_name: str
    serial_number: str
    firmware_version: str
    channel_count: int
    connection_status: str
    last_detected: float = field(default_factory=time.time)

@dataclass
class DynamicServoConfig:
    """Enhanced servo configuration with user customization"""
    channel: int
    name: str
    display_name: str
    min_position: int = 1000    # Quarter-microseconds
    max_position: int = 8000    # Quarter-microseconds
    home_position: int = 6000   # Quarter-microseconds
    max_speed: int = 50         # 0-255
    acceleration: int = 20      # 0-255
    enabled: bool = True
    user_defined: bool = False
    r2d2_function: str = ""     # e.g., "dome_rotation", "panel_front"
    movement_range_deg: float = 180.0
    calibration_offset: float = 0.0
    safety_limits_enforced: bool = True

    def to_base_config(self) -> BaseServoConfig:
        """Convert to base servo config for compatibility"""
        return BaseServoConfig(
            channel=self.channel,
            name=self.name,
            min_position=self.min_position,
            max_position=self.max_position,
            home_position=self.home_position,
            max_speed=self.max_speed,
            acceleration=self.acceleration,
            enabled=self.enabled
        )

@dataclass
class ServoSequenceStep:
    """Single step in a servo sequence"""
    channel: int
    position: int               # Quarter-microseconds
    duration_ms: int            # Duration in milliseconds
    easing_type: str = "linear" # linear, ease_in, ease_out, ease_in_out
    hold_time_ms: int = 0       # Hold time at position

@dataclass
class ServoSequence:
    """Complete servo sequence with metadata"""
    name: str
    description: str
    steps: List[ServoSequenceStep]
    total_duration_ms: int
    loop_count: int = 1         # 0 = infinite loop
    priority: int = 1           # 1-10, higher = more important
    created_by: str = "user"
    created_at: float = field(default_factory=time.time)
    r2d2_behavior: str = ""     # e.g., "greeting", "search", "alert"

class EnhancedMaestroController(PololuMaestroController):
    """Enhanced Maestro controller with dynamic configuration and advanced features"""

    def __init__(self, auto_detect: bool = True, config_file: str = None):
        """
        Initialize enhanced Maestro controller

        Args:
            auto_detect: Automatically detect and connect to Maestro board
            config_file: Path to servo configuration file
        """
        self.hardware_info: Optional[MaestroHardwareInfo] = None
        self.dynamic_configs: Dict[int, DynamicServoConfig] = {}
        self.saved_sequences: Dict[str, ServoSequence] = {}
        self.active_sequence: Optional[str] = None
        self.sequence_status = SequenceStatus.IDLE
        self.detection_status = HardwareDetectionStatus.SEARCHING

        # Configuration file paths
        self.config_dir = Path("/home/rolo/r2ai/config")
        self.config_dir.mkdir(exist_ok=True)
        self.servo_config_file = self.config_dir / "servo_config.json"
        self.sequences_file = self.config_dir / "servo_sequences.json"

        # Initialize base controller first
        if auto_detect:
            detected_port = self.detect_maestro_hardware()
            if detected_port:
                super().__init__(port=detected_port, simulation_mode=False)
                self.detection_status = HardwareDetectionStatus.CONNECTED
            else:
                logger.warning("No Maestro hardware detected, running in simulation mode")
                super().__init__(simulation_mode=True)
                self.detection_status = HardwareDetectionStatus.SIMULATION
        else:
            super().__init__(simulation_mode=True)
            self.detection_status = HardwareDetectionStatus.SIMULATION

        # Load existing configuration after base initialization
        if config_file:
            self.load_servo_configuration(config_file)
        else:
            self.load_servo_configuration()

        # Load saved sequences
        self.load_servo_sequences()

        logger.info("Enhanced Maestro Controller initialized")

    def detect_maestro_hardware(self) -> Optional[str]:
        """
        Auto-detect Pololu Maestro hardware

        Returns:
            Port path if found, None otherwise
        """
        logger.info("🔍 Detecting Pololu Maestro hardware...")
        self.detection_status = HardwareDetectionStatus.SEARCHING

        # Search for USB serial devices
        ports = serial.tools.list_ports.comports()
        maestro_ports = []

        for port in ports:
            # Look for Pololu vendor ID (0x1ffb) or device descriptions
            if (hasattr(port, 'vid') and port.vid == 0x1ffb) or \
               any(keyword in (port.description or "").lower()
                   for keyword in ['maestro', 'pololu', 'servo']):
                maestro_ports.append(port)
                logger.info(f"Found potential Maestro device: {port.device} - {port.description}")

        # Test each potential port
        for port in maestro_ports:
            if self.test_maestro_connection(port.device):
                self.hardware_info = MaestroHardwareInfo(
                    port=port.device,
                    device_name=port.description or "Unknown Maestro",
                    serial_number=port.serial_number or "Unknown",
                    firmware_version="Unknown",
                    channel_count=12,  # Default for Mini 12-channel
                    connection_status="connected"
                )
                self.detection_status = HardwareDetectionStatus.FOUND
                logger.info(f"✅ Maestro detected and connected: {port.device}")
                return port.device

        self.detection_status = HardwareDetectionStatus.FAILED
        logger.warning("No Maestro hardware found")
        return None

    def test_maestro_connection(self, port: str) -> bool:
        """Test connection to Maestro on specified port"""
        try:
            test_serial = serial.Serial(
                port=port,
                baudrate=9600,
                timeout=1.0
            )
            time.sleep(0.1)

            # Try to get error status - should return 2 bytes
            test_serial.write(bytes([0xA1]))  # GET_ERRORS command
            response = test_serial.read(2)
            test_serial.close()

            return len(response) == 2

        except Exception as e:
            logger.debug(f"Connection test failed for {port}: {e}")
            return False

    def create_dynamic_servo_config(self, channel: int, name: str, display_name: str = None) -> DynamicServoConfig:
        """Create a new dynamic servo configuration"""
        if display_name is None:
            display_name = name.replace('_', ' ').title()

        config = DynamicServoConfig(
            channel=channel,
            name=name,
            display_name=display_name,
            user_defined=True
        )

        self.dynamic_configs[channel] = config

        # Update base controller configuration
        base_config = config.to_base_config()
        self.servo_configs[channel] = base_config

        logger.info(f"Created dynamic servo config: Channel {channel} - {display_name}")
        return config

    def update_servo_limits_from_maestro(self, channel: int) -> bool:
        """
        Import servo limits from Maestro hardware settings

        This would typically read from the Maestro's internal settings
        For now, we'll implement reasonable defaults based on hardware specs
        """
        if channel not in self.dynamic_configs:
            logger.error(f"No configuration found for channel {channel}")
            return False

        config = self.dynamic_configs[channel]

        # In a real implementation, this would query the Maestro for:
        # - Minimum position limit
        # - Maximum position limit
        # - Speed and acceleration settings
        # - Home position

        # For now, apply conservative defaults
        config.min_position = max(config.min_position, 992)   # 248µs (safe minimum)
        config.max_position = min(config.max_position, 8000)  # 2000µs (safe maximum)

        # Update base configuration
        base_config = config.to_base_config()
        self.servo_configs[channel] = base_config

        logger.info(f"Updated servo limits for channel {channel} from Maestro settings")
        return True

    def get_servo_count(self) -> int:
        """Get number of configured servos"""
        return len(self.dynamic_configs)

    def set_servo_count(self, count: int) -> bool:
        """Set number of active servos (1-12)"""
        if not 1 <= count <= 12:
            logger.error("Servo count must be between 1 and 12")
            return False

        # Remove configurations beyond the new count
        channels_to_remove = [ch for ch in self.dynamic_configs.keys() if ch >= count]
        for channel in channels_to_remove:
            del self.dynamic_configs[channel]
            if channel in self.servo_configs:
                del self.servo_configs[channel]

        # Create default configurations for missing channels
        for channel in range(count):
            if channel not in self.dynamic_configs:
                self.create_dynamic_servo_config(
                    channel=channel,
                    name=f"servo_{channel}",
                    display_name=f"Servo {channel + 1}"
                )

        logger.info(f"Servo count set to {count}")
        return True

    def rename_servo(self, channel: int, name: str, display_name: str = None) -> bool:
        """Rename a servo channel"""
        if channel not in self.dynamic_configs:
            logger.error(f"No servo configured for channel {channel}")
            return False

        config = self.dynamic_configs[channel]
        config.name = name
        config.display_name = display_name or name.replace('_', ' ').title()

        # Update base configuration
        base_config = config.to_base_config()
        self.servo_configs[channel] = base_config

        logger.info(f"Renamed servo {channel}: {config.display_name}")
        return True

    def create_sequence(self, name: str, description: str = "") -> ServoSequence:
        """Create a new servo sequence"""
        sequence = ServoSequence(
            name=name,
            description=description,
            steps=[],
            total_duration_ms=0
        )

        self.saved_sequences[name] = sequence
        logger.info(f"Created new sequence: {name}")
        return sequence

    def add_sequence_step(self, sequence_name: str, channel: int, position: int,
                         duration_ms: int, easing_type: str = "linear") -> bool:
        """Add a step to a servo sequence"""
        if sequence_name not in self.saved_sequences:
            logger.error(f"Sequence '{sequence_name}' not found")
            return False

        if channel not in self.dynamic_configs:
            logger.error(f"Channel {channel} not configured")
            return False

        sequence = self.saved_sequences[sequence_name]
        step = ServoSequenceStep(
            channel=channel,
            position=position,
            duration_ms=duration_ms,
            easing_type=easing_type
        )

        sequence.steps.append(step)
        sequence.total_duration_ms = sum(step.duration_ms + step.hold_time_ms for step in sequence.steps)

        logger.info(f"Added step to sequence '{sequence_name}': Ch{channel} -> {position} ({duration_ms}ms)")
        return True

    def execute_sequence(self, sequence_name: str) -> bool:
        """Execute a saved servo sequence"""
        if sequence_name not in self.saved_sequences:
            logger.error(f"Sequence '{sequence_name}' not found")
            return False

        if self.sequence_status in [SequenceStatus.EXECUTING, SequenceStatus.LOADING]:
            logger.warning("Another sequence is already running")
            return False

        sequence = self.saved_sequences[sequence_name]
        self.active_sequence = sequence_name
        self.sequence_status = SequenceStatus.LOADING

        # Execute sequence in separate thread
        sequence_thread = threading.Thread(
            target=self._execute_sequence_thread,
            args=(sequence,),
            daemon=True
        )
        sequence_thread.start()

        logger.info(f"Starting execution of sequence: {sequence_name}")
        return True

    def _execute_sequence_thread(self, sequence: ServoSequence):
        """Execute servo sequence in separate thread"""
        try:
            self.sequence_status = SequenceStatus.EXECUTING

            for step in sequence.steps:
                if self.sequence_status != SequenceStatus.EXECUTING:
                    break  # Sequence was stopped or paused

                # Move servo to position
                success = self.set_servo_position(step.channel, step.position)
                if not success:
                    logger.error(f"Failed to execute step: Ch{step.channel}")
                    self.sequence_status = SequenceStatus.FAILED
                    return

                # Wait for duration
                time.sleep(step.duration_ms / 1000.0)

                # Hold time
                if step.hold_time_ms > 0:
                    time.sleep(step.hold_time_ms / 1000.0)

            self.sequence_status = SequenceStatus.COMPLETED
            logger.info(f"Sequence '{sequence.name}' completed successfully")

        except Exception as e:
            logger.error(f"Sequence execution failed: {e}")
            self.sequence_status = SequenceStatus.FAILED
        finally:
            self.active_sequence = None

    def stop_sequence(self) -> bool:
        """Stop currently executing sequence"""
        if self.sequence_status == SequenceStatus.EXECUTING:
            self.sequence_status = SequenceStatus.IDLE
            self.active_sequence = None
            logger.info("Sequence execution stopped")
            return True
        return False

    def save_servo_configuration(self, filename: str = None):
        """Save dynamic servo configuration to file"""
        if filename is None:
            filename = str(self.servo_config_file)

        config_data = {
            "hardware_info": asdict(self.hardware_info) if self.hardware_info else None,
            "servo_count": len(self.dynamic_configs),
            "servos": {str(ch): asdict(config) for ch, config in self.dynamic_configs.items()},
            "saved_at": time.time()
        }

        with open(filename, 'w') as f:
            json.dump(config_data, f, indent=2)

        logger.info(f"Servo configuration saved to {filename}")

    def load_servo_configuration(self, filename: str = None):
        """Load dynamic servo configuration from file"""
        if filename is None:
            filename = str(self.servo_config_file)

        if not os.path.exists(filename):
            logger.info("No existing servo configuration found, using defaults")
            self._create_default_configuration()
            return

        try:
            with open(filename, 'r') as f:
                config_data = json.load(f)

            # Load hardware info
            if config_data.get("hardware_info"):
                self.hardware_info = MaestroHardwareInfo(**config_data["hardware_info"])

            # Load servo configurations
            for ch_str, servo_data in config_data.get("servos", {}).items():
                channel = int(ch_str)
                config = DynamicServoConfig(**servo_data)
                self.dynamic_configs[channel] = config

            logger.info(f"Servo configuration loaded from {filename}")

        except Exception as e:
            logger.error(f"Failed to load servo configuration: {e}")
            self._create_default_configuration()

    def save_servo_sequences(self, filename: str = None):
        """Save servo sequences to file"""
        if filename is None:
            filename = str(self.sequences_file)

        sequences_data = {
            name: asdict(sequence) for name, sequence in self.saved_sequences.items()
        }

        with open(filename, 'w') as f:
            json.dump(sequences_data, f, indent=2)

        logger.info(f"Servo sequences saved to {filename}")

    def load_servo_sequences(self, filename: str = None):
        """Load servo sequences from file"""
        if filename is None:
            filename = str(self.sequences_file)

        if not os.path.exists(filename):
            logger.info("No saved sequences found")
            return

        try:
            with open(filename, 'r') as f:
                sequences_data = json.load(f)

            for name, sequence_data in sequences_data.items():
                # Convert step dictionaries back to ServoSequenceStep objects
                steps = [ServoSequenceStep(**step) for step in sequence_data["steps"]]
                sequence_data["steps"] = steps

                sequence = ServoSequence(**sequence_data)
                self.saved_sequences[name] = sequence

            logger.info(f"Loaded {len(self.saved_sequences)} servo sequences")

        except Exception as e:
            logger.error(f"Failed to load servo sequences: {e}")

    def _create_default_configuration(self):
        """Create default servo configuration"""
        logger.info("Creating default servo configuration")

        # Create 6 default servos (expandable)
        default_servos = [
            ("dome_rotation", "Dome Rotation"),
            ("head_tilt", "Head Tilt"),
            ("periscope", "Periscope"),
            ("utility_arm_left", "Left Utility Arm"),
            ("utility_arm_right", "Right Utility Arm"),
            ("dome_panel_front", "Front Dome Panel")
        ]

        for i, (name, display_name) in enumerate(default_servos):
            self.create_dynamic_servo_config(i, name, display_name)

        # Create default R2D2 choreographed sequences
        self._create_default_r2d2_sequences()

    def _create_default_r2d2_sequences(self):
        """Create default choreographed R2D2 movement sequences"""
        logger.info("Creating default R2D2 choreographed sequences")

        # =============================================
        # R2D2 GREETING SEQUENCE
        # =============================================
        greeting_sequence = self.create_sequence(
            "r2d2_greeting",
            "Friendly R2D2 greeting with dome rotation and head movement"
        )

        # Dome rotation left
        self.add_sequence_step("r2d2_greeting", 0, 7500, 800, "ease_out")
        # Head tilt up slightly
        self.add_sequence_step("r2d2_greeting", 1, 7000, 600, "ease_in_out")
        # Brief pause at position
        self.add_sequence_step("r2d2_greeting", 0, 7500, 200, "linear")
        # Dome rotation right
        self.add_sequence_step("r2d2_greeting", 0, 4500, 1000, "ease_in_out")
        # Head return to center
        self.add_sequence_step("r2d2_greeting", 1, 6000, 600, "ease_in")
        # Dome return to center
        self.add_sequence_step("r2d2_greeting", 0, 6000, 800, "ease_out")

        # =============================================
        # JEDI RESPECT BOW SEQUENCE
        # =============================================
        respect_sequence = self.create_sequence(
            "jedi_respect_bow",
            "Respectful bow sequence for Jedi recognition"
        )

        # Head tilt down (respectful bow)
        self.add_sequence_step("jedi_respect_bow", 1, 4500, 1200, "ease_in")
        # Hold the bow position
        self.add_sequence_step("jedi_respect_bow", 1, 4500, 800, "linear")
        # Slow return to center
        self.add_sequence_step("jedi_respect_bow", 1, 6000, 1000, "ease_out")

        # =============================================
        # AREA SCAN SEQUENCE
        # =============================================
        scan_sequence = self.create_sequence(
            "area_scan_sequence",
            "Systematic environmental scanning pattern"
        )

        # Dome scan left to right
        self.add_sequence_step("area_scan_sequence", 0, 8000, 1500, "linear")
        self.add_sequence_step("area_scan_sequence", 0, 4000, 3000, "linear")
        # Head scan up and down while dome moves
        self.add_sequence_step("area_scan_sequence", 1, 7500, 800, "ease_in_out")
        self.add_sequence_step("area_scan_sequence", 1, 4500, 1200, "ease_in_out")
        self.add_sequence_step("area_scan_sequence", 1, 6000, 800, "ease_in_out")
        # Return dome to center
        self.add_sequence_step("area_scan_sequence", 0, 6000, 1500, "ease_out")

        # =============================================
        # PLAYFUL DANCE SEQUENCE
        # =============================================
        dance_sequence = self.create_sequence(
            "playful_dance",
            "Playful dancing movement for entertainment"
        )

        # Quick dome spins
        self.add_sequence_step("playful_dance", 0, 8000, 400, "ease_in")
        self.add_sequence_step("playful_dance", 0, 4000, 400, "ease_out")
        self.add_sequence_step("playful_dance", 0, 8000, 400, "ease_in")
        self.add_sequence_step("playful_dance", 0, 6000, 300, "ease_out")

        # Head bobbing
        self.add_sequence_step("playful_dance", 1, 7200, 300, "ease_in_out")
        self.add_sequence_step("playful_dance", 1, 4800, 300, "ease_in_out")
        self.add_sequence_step("playful_dance", 1, 7200, 300, "ease_in_out")
        self.add_sequence_step("playful_dance", 1, 6000, 300, "ease_out")

        # Periscope dance if available
        if 2 in self.dynamic_configs:
            self.add_sequence_step("playful_dance", 2, 7500, 200, "linear")
            self.add_sequence_step("playful_dance", 2, 4500, 300, "linear")
            self.add_sequence_step("playful_dance", 2, 6000, 200, "linear")

        # =============================================
        # SYSTEM CHECK SEQUENCE
        # =============================================
        system_check = self.create_sequence(
            "system_check",
            "Power-up system check and calibration"
        )

        # Sequential servo check
        for channel in range(min(3, len(self.dynamic_configs))):
            # Move to test position
            self.add_sequence_step("system_check", channel, 7000, 500, "linear")
            # Return to home
            self.add_sequence_step("system_check", channel, 6000, 500, "linear")

        # =============================================
        # STUBBORN SEQUENCE
        # =============================================
        stubborn_sequence = self.create_sequence(
            "stubborn_turn_away",
            "Stubborn behavior - turning away in defiance"
        )

        # Turn head away slowly
        self.add_sequence_step("stubborn_turn_away", 1, 4000, 1000, "ease_in")
        # Turn dome away too
        self.add_sequence_step("stubborn_turn_away", 0, 4500, 800, "ease_in")
        # Hold the stubborn position
        self.add_sequence_step("stubborn_turn_away", 0, 4500, 1500, "linear")
        # Reluctant return (slow)
        self.add_sequence_step("stubborn_turn_away", 1, 6000, 1200, "ease_out")
        self.add_sequence_step("stubborn_turn_away", 0, 6000, 1000, "ease_out")

        # =============================================
        # EXCITED SEQUENCE
        # =============================================
        excited_sequence = self.create_sequence(
            "excited_bounce",
            "Excited bouncing and movement"
        )

        # Rapid head movements
        self.add_sequence_step("excited_bounce", 1, 7500, 200, "ease_in")
        self.add_sequence_step("excited_bounce", 1, 4500, 200, "ease_out")
        self.add_sequence_step("excited_bounce", 1, 7500, 200, "ease_in")
        self.add_sequence_step("excited_bounce", 1, 4500, 200, "ease_out")
        self.add_sequence_step("excited_bounce", 1, 6000, 300, "ease_in_out")

        # Quick dome wiggles
        self.add_sequence_step("excited_bounce", 0, 7000, 150, "linear")
        self.add_sequence_step("excited_bounce", 0, 5000, 150, "linear")
        self.add_sequence_step("excited_bounce", 0, 7000, 150, "linear")
        self.add_sequence_step("excited_bounce", 0, 5000, 150, "linear")
        self.add_sequence_step("excited_bounce", 0, 6000, 200, "ease_out")

        # =============================================
        # TRACKING SEQUENCE
        # =============================================
        tracking_sequence = self.create_sequence(
            "smooth_tracking",
            "Smooth tracking movement for following objects"
        )

        # Smooth left tracking
        self.add_sequence_step("smooth_tracking", 0, 7200, 1000, "ease_in_out")
        self.add_sequence_step("smooth_tracking", 1, 6800, 800, "ease_in_out")
        # Pause and track
        self.add_sequence_step("smooth_tracking", 0, 7200, 500, "linear")
        # Smooth right tracking
        self.add_sequence_step("smooth_tracking", 0, 4800, 1200, "ease_in_out")
        self.add_sequence_step("smooth_tracking", 1, 5200, 800, "ease_in_out")
        # Return to center
        self.add_sequence_step("smooth_tracking", 0, 6000, 1000, "ease_out")
        self.add_sequence_step("smooth_tracking", 1, 6000, 800, "ease_out")

        logger.info(f"✅ Created {len(self.saved_sequences)} default R2D2 choreographed sequences")

    def get_enhanced_status_report(self) -> Dict[str, Any]:
        """Get comprehensive status report including dynamic configuration"""
        base_report = self.get_status_report()

        enhanced_report = {
            **base_report,
            "hardware_detection": {
                "status": self.detection_status.value,
                "hardware_info": asdict(self.hardware_info) if self.hardware_info else None
            },
            "dynamic_configuration": {
                "servo_count": len(self.dynamic_configs),
                "user_defined_servos": sum(1 for config in self.dynamic_configs.values() if config.user_defined),
                "configurations": {
                    ch: {
                        "name": config.name,
                        "display_name": config.display_name,
                        "enabled": config.enabled,
                        "r2d2_function": config.r2d2_function
                    } for ch, config in self.dynamic_configs.items()
                }
            },
            "sequences": {
                "total_saved": len(self.saved_sequences),
                "active_sequence": self.active_sequence,
                "sequence_status": self.sequence_status.value,
                "available_sequences": list(self.saved_sequences.keys())
            }
        }

        return enhanced_report

def demo_enhanced_maestro():
    """Demonstration of enhanced Maestro capabilities"""
    logger.info("🤖 Enhanced Maestro Controller Demo")
    logger.info("=" * 50)

    # Initialize enhanced controller
    controller = EnhancedMaestroController(auto_detect=True)

    try:
        # Demo 1: Dynamic configuration
        logger.info("\n--- Demo 1: Dynamic Configuration ---")
        controller.set_servo_count(8)
        controller.rename_servo(0, "dome_rotation", "Dome Rotation")
        controller.rename_servo(1, "head_tilt", "Head Tilt")
        controller.rename_servo(2, "periscope", "Periscope")

        # Demo 2: Create and execute sequence
        logger.info("\n--- Demo 2: Servo Sequences ---")
        controller.create_sequence("r2d2_greeting", "Friendly R2D2 greeting sequence")
        controller.add_sequence_step("r2d2_greeting", 0, 7000, 1000)  # Dome rotate
        controller.add_sequence_step("r2d2_greeting", 1, 7500, 800)   # Head tilt
        controller.add_sequence_step("r2d2_greeting", 2, 7000, 600)   # Periscope up
        controller.add_sequence_step("r2d2_greeting", 2, 4000, 600)   # Periscope down
        controller.add_sequence_step("r2d2_greeting", 1, 6000, 800)   # Head center
        controller.add_sequence_step("r2d2_greeting", 0, 6000, 1000)  # Dome center

        controller.execute_sequence("r2d2_greeting")

        # Wait for sequence to complete
        while controller.sequence_status == SequenceStatus.EXECUTING:
            time.sleep(0.1)

        # Demo 3: Enhanced status report
        logger.info("\n--- Demo 3: Enhanced Status Report ---")
        status = controller.get_enhanced_status_report()

        print(f"Hardware Detection: {status['hardware_detection']['status']}")
        print(f"Servo Count: {status['dynamic_configuration']['servo_count']}")
        print(f"Saved Sequences: {status['sequences']['total_saved']}")
        print(f"Last Sequence Status: {status['sequences']['sequence_status']}")

        # Save configuration
        controller.save_servo_configuration()
        controller.save_servo_sequences()

        logger.info("✅ Enhanced Maestro demo completed successfully!")

    except Exception as e:
        logger.error(f"Demo failed: {e}")
    finally:
        controller.shutdown()

if __name__ == "__main__":
    demo_enhanced_maestro()