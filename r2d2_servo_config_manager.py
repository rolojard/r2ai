#!/usr/bin/env python3
"""
R2D2 Dynamic Servo Configuration Management System
Disney-Level Animatronics Configuration and Safety System

This module provides comprehensive servo configuration management with
dynamic adaptation, safety enforcement, and professional animatronics
integration for R2D2 servo control systems.

Features:
- Dynamic servo configuration with hardware adaptation
- Professional safety limit enforcement
- Real-time servo monitoring and feedback
- Configuration import/export with validation
- Hardware-specific optimization profiles
- Emergency safety systems with instant response
"""

import json
import time
import logging
import threading
from typing import Dict, List, Optional, Tuple, Union, Any
from dataclasses import dataclass, field
from enum import Enum
import math
from pathlib import Path

from maestro_hardware_detector import MaestroHardwareDetector, MaestroHardwareInfo, MaestroVariant

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ServoType(Enum):
    """Servo function types for R2D2 animatronics"""
    PRIMARY = "primary"        # Main character movement (dome, head)
    UTILITY = "utility"        # Utility arms, periscope, radar
    PANEL = "panel"           # Access panels and doors
    DISPLAY = "display"       # Logic displays and visual elements
    SPECIAL = "special"       # Holoprojectors and unique features
    LIGHTING = "lighting"     # LED controllers and lighting
    AUDIO = "audio"          # Sound triggers and audio control
    DRIVE = "drive"          # Motor control and locomotion
    EXPANSION = "expansion"   # Future expansion and custom features

class ServoRange(Enum):
    """Servo movement range classifications"""
    BINARY = "binary"         # Simple open/close (panels, doors)
    LIMITED = "limited"       # Restricted range (head tilt, displays)
    WIDE = "wide"            # Full range movement (arms, utilities)
    CONTINUOUS = "continuous" # 360-degree rotation (dome, radar)

class SafetyLevel(Enum):
    """Safety enforcement levels"""
    STRICT = "strict"         # Maximum safety, limited movement
    NORMAL = "normal"         # Standard safety limits
    RELAXED = "relaxed"       # Expanded limits for advanced users
    DISABLED = "disabled"     # Safety checks disabled (expert only)

@dataclass
class ServoLimits:
    """Comprehensive servo safety and operational limits"""
    min_pulse_us: float = 500.0      # Minimum pulse width (microseconds)
    max_pulse_us: float = 2500.0     # Maximum pulse width (microseconds)
    home_pulse_us: float = 1500.0    # Home position (microseconds)
    max_speed: int = 100             # Maximum speed setting (0-255)
    max_acceleration: int = 50       # Maximum acceleration (0-255)
    position_deadband_us: float = 2.0 # Position accuracy tolerance
    timeout_ms: int = 5000           # Communication timeout
    emergency_position_us: float = 1500.0 # Emergency safe position

    def to_quarters(self, microseconds: float) -> int:
        """Convert microseconds to quarter-microseconds"""
        return int(microseconds * 4)

    def from_quarters(self, quarters: int) -> float:
        """Convert quarter-microseconds to microseconds"""
        return quarters / 4.0

    def validate_position(self, pulse_us: float) -> float:
        """Validate and clamp position to safe range"""
        return max(self.min_pulse_us, min(self.max_pulse_us, pulse_us))

@dataclass
class ServoConfiguration:
    """Complete servo configuration with metadata"""
    channel: int
    name: str
    servo_type: ServoType
    servo_range: ServoRange
    limits: ServoLimits
    enabled: bool = True
    reverse: bool = False
    description: str = ""
    calibration_offset: float = 0.0  # Calibration adjustment in microseconds

    # Motion characteristics
    default_speed: int = 50
    default_acceleration: int = 25
    smooth_motion: bool = True

    # Monitoring settings
    monitor_position: bool = True
    monitor_load: bool = False
    alert_on_stall: bool = True

    def get_effective_position(self, target_us: float) -> float:
        """Calculate effective position with calibration and limits"""
        # Apply calibration offset
        adjusted = target_us + self.calibration_offset

        # Apply reversal if configured
        if self.reverse:
            center = (self.limits.min_pulse_us + self.limits.max_pulse_us) / 2
            adjusted = center + (center - adjusted)

        # Apply safety limits
        return self.limits.validate_position(adjusted)

class R2D2ServoConfigManager:
    """Advanced R2D2 Servo Configuration Management System"""

    def __init__(self, hardware_detector: Optional[MaestroHardwareDetector] = None):
        self.hardware_detector = hardware_detector or MaestroHardwareDetector()
        self.servo_configs: Dict[int, ServoConfiguration] = {}
        self.safety_level = SafetyLevel.NORMAL
        self.config_lock = threading.Lock()
        self.monitoring_active = False
        self.config_changed_callbacks: List[callable] = []

        # Performance tracking
        self.config_load_time = 0.0
        self.last_validation_time = 0.0
        self.validation_errors: List[str] = []

    def add_config_change_callback(self, callback: callable):
        """Add callback for configuration change events"""
        self.config_changed_callbacks.append(callback)

    def _notify_config_change(self, change_type: str, channel: int, config: ServoConfiguration):
        """Notify callbacks of configuration changes"""
        for callback in self.config_changed_callbacks:
            try:
                callback(change_type, channel, config)
            except Exception as e:
                logger.error(f"Config change callback error: {e}")

    def initialize_from_hardware(self, device: Optional[MaestroHardwareInfo] = None) -> bool:
        """
        Initialize servo configuration from detected hardware

        Args:
            device: Specific device to use, or None for auto-detection

        Returns:
            True if initialization successful
        """
        start_time = time.time()
        logger.info("🔧 Initializing servo configuration from hardware...")

        try:
            # Detect hardware if not provided
            if device is None:
                devices = self.hardware_detector.scan_for_maestro_devices()
                if not devices:
                    logger.error("No Maestro hardware detected")
                    return False
                device = self.hardware_detector.get_optimal_device()

            if not device:
                logger.error("No suitable Maestro device found")
                return False

            # Generate configuration based on hardware
            with self.config_lock:
                self.servo_configs.clear()
                self._generate_r2d2_configuration(device)

            self.config_load_time = time.time() - start_time
            logger.info(f"✅ Configuration initialized for {device.variant.value} "
                       f"({device.channels} channels) in {self.config_load_time:.3f}s")

            # Validate configuration
            self._validate_configuration()

            return True

        except Exception as e:
            logger.error(f"Hardware initialization failed: {e}")
            return False

    def _generate_r2d2_configuration(self, device: MaestroHardwareInfo):
        """Generate R2D2-specific servo configuration for hardware"""

        # R2D2 servo definitions with Disney-level specifications
        r2d2_servos = [
            # Primary Movement Servos (Critical for character performance)
            {
                "channel": 0, "name": "Dome Rotation", "type": ServoType.PRIMARY, "range": ServoRange.CONTINUOUS,
                "limits": ServoLimits(600, 2400, 1500, 80, 30, 1.0, 3000, 1500),
                "description": "Main dome 360-degree rotation mechanism",
                "default_speed": 60, "smooth_motion": True, "monitor_load": True
            },
            {
                "channel": 1, "name": "Head Tilt", "type": ServoType.PRIMARY, "range": ServoRange.LIMITED,
                "limits": ServoLimits(1000, 2000, 1500, 70, 25, 1.5, 4000, 1500),
                "description": "Head tilt mechanism (-30° to +30°)",
                "default_speed": 50, "smooth_motion": True, "alert_on_stall": True
            },
            {
                "channel": 2, "name": "Periscope", "type": ServoType.UTILITY, "range": ServoRange.BINARY,
                "limits": ServoLimits(800, 1800, 800, 120, 60, 2.0, 2000, 800),
                "description": "Periscope extend/retract mechanism",
                "default_speed": 80, "smooth_motion": False
            },
            {
                "channel": 3, "name": "Radar Eye", "type": ServoType.UTILITY, "range": ServoRange.CONTINUOUS,
                "limits": ServoLimits(700, 2300, 1500, 100, 40, 1.0, 2500, 1500),
                "description": "Radar eye rotation and scanning",
                "default_speed": 70, "smooth_motion": True
            },
            {
                "channel": 4, "name": "Utility Arm Left", "type": ServoType.UTILITY, "range": ServoRange.WIDE,
                "limits": ServoLimits(500, 2500, 1000, 90, 35, 2.0, 3500, 1000),
                "description": "Left utility arm positioning",
                "default_speed": 60, "smooth_motion": True, "monitor_load": True
            },
            {
                "channel": 5, "name": "Utility Arm Right", "type": ServoType.UTILITY, "range": ServoRange.WIDE,
                "limits": ServoLimits(500, 2500, 1000, 90, 35, 2.0, 3500, 1000),
                "description": "Right utility arm positioning",
                "default_speed": 60, "smooth_motion": True, "monitor_load": True
            }
        ]

        # Panel servos for 12+ channel controllers
        if device.channels >= 12:
            r2d2_servos.extend([
                {
                    "channel": 6, "name": "Dome Panel Front", "type": ServoType.PANEL, "range": ServoRange.BINARY,
                    "limits": ServoLimits(1000, 2000, 1000, 150, 80, 3.0, 1500, 1000),
                    "description": "Front dome access panel",
                    "default_speed": 100, "smooth_motion": False
                },
                {
                    "channel": 7, "name": "Dome Panel Left", "type": ServoType.PANEL, "range": ServoRange.BINARY,
                    "limits": ServoLimits(1000, 2000, 1000, 150, 80, 3.0, 1500, 1000),
                    "description": "Left dome access panel",
                    "default_speed": 100, "smooth_motion": False
                },
                {
                    "channel": 8, "name": "Dome Panel Right", "type": ServoType.PANEL, "range": ServoRange.BINARY,
                    "limits": ServoLimits(1000, 2000, 1000, 150, 80, 3.0, 1500, 1000),
                    "description": "Right dome access panel",
                    "default_speed": 100, "smooth_motion": False
                },
                {
                    "channel": 9, "name": "Dome Panel Back", "type": ServoType.PANEL, "range": ServoRange.BINARY,
                    "limits": ServoLimits(1000, 2000, 1000, 150, 80, 3.0, 1500, 1000),
                    "description": "Back dome access panel",
                    "default_speed": 100, "smooth_motion": False
                },
                {
                    "channel": 10, "name": "Body Door Left", "type": ServoType.PANEL, "range": ServoRange.BINARY,
                    "limits": ServoLimits(1200, 1800, 1200, 120, 60, 3.0, 1500, 1200),
                    "description": "Left body access door",
                    "default_speed": 80, "smooth_motion": True
                },
                {
                    "channel": 11, "name": "Body Door Right", "type": ServoType.PANEL, "range": ServoRange.BINARY,
                    "limits": ServoLimits(1200, 1800, 1200, 120, 60, 3.0, 1500, 1200),
                    "description": "Right body access door",
                    "default_speed": 80, "smooth_motion": True
                }
            ])

        # Advanced features for 18+ channel controllers
        if device.channels >= 18:
            r2d2_servos.extend([
                {
                    "channel": 12, "name": "Front Logic Display", "type": ServoType.DISPLAY, "range": ServoRange.LIMITED,
                    "limits": ServoLimits(1200, 1800, 1500, 100, 50, 2.0, 2000, 1500),
                    "description": "Front logic display animation",
                    "default_speed": 70, "smooth_motion": True
                },
                {
                    "channel": 13, "name": "Rear Logic Display", "type": ServoType.DISPLAY, "range": ServoRange.LIMITED,
                    "limits": ServoLimits(1200, 1800, 1500, 100, 50, 2.0, 2000, 1500),
                    "description": "Rear logic display animation",
                    "default_speed": 70, "smooth_motion": True
                },
                {
                    "channel": 14, "name": "Holoprojector 1", "type": ServoType.SPECIAL, "range": ServoRange.WIDE,
                    "limits": ServoLimits(800, 2200, 1500, 120, 60, 2.0, 2500, 1500),
                    "description": "Primary holoprojector positioning",
                    "default_speed": 90, "smooth_motion": True, "monitor_load": True
                },
                {
                    "channel": 15, "name": "Holoprojector 2", "type": ServoType.SPECIAL, "range": ServoRange.WIDE,
                    "limits": ServoLimits(800, 2200, 1500, 120, 60, 2.0, 2500, 1500),
                    "description": "Secondary holoprojector positioning",
                    "default_speed": 90, "smooth_motion": True, "monitor_load": True
                },
                {
                    "channel": 16, "name": "Body Rotation", "type": ServoType.DRIVE, "range": ServoRange.CONTINUOUS,
                    "limits": ServoLimits(600, 2400, 1500, 60, 20, 1.0, 5000, 1500),
                    "description": "Body rotation mechanism",
                    "default_speed": 40, "smooth_motion": True, "monitor_load": True, "alert_on_stall": True
                },
                {
                    "channel": 17, "name": "Reserved Expansion", "type": ServoType.EXPANSION, "range": ServoRange.WIDE,
                    "limits": ServoLimits(500, 2500, 1500, 100, 50, 2.0, 3000, 1500),
                    "description": "Reserved for future expansion",
                    "default_speed": 50, "enabled": False
                }
            ])

        # Professional features for 24-channel controllers
        if device.channels >= 24:
            r2d2_servos.extend([
                {
                    "channel": 18, "name": "LED Controller 1", "type": ServoType.LIGHTING, "range": ServoRange.WIDE,
                    "limits": ServoLimits(1000, 2000, 1000, 200, 100, 5.0, 1000, 1000),
                    "description": "Primary LED brightness/color control",
                    "default_speed": 150, "smooth_motion": False
                },
                {
                    "channel": 19, "name": "LED Controller 2", "type": ServoType.LIGHTING, "range": ServoRange.WIDE,
                    "limits": ServoLimits(1000, 2000, 1000, 200, 100, 5.0, 1000, 1000),
                    "description": "Secondary LED brightness/color control",
                    "default_speed": 150, "smooth_motion": False
                },
                {
                    "channel": 20, "name": "Sound Trigger 1", "type": ServoType.AUDIO, "range": ServoRange.BINARY,
                    "limits": ServoLimits(1000, 2000, 1000, 255, 200, 10.0, 500, 1000),
                    "description": "Primary audio system trigger",
                    "default_speed": 255, "smooth_motion": False
                },
                {
                    "channel": 21, "name": "Sound Trigger 2", "type": ServoType.AUDIO, "range": ServoRange.BINARY,
                    "limits": ServoLimits(1000, 2000, 1000, 255, 200, 10.0, 500, 1000),
                    "description": "Secondary audio system trigger",
                    "default_speed": 255, "smooth_motion": False
                },
                {
                    "channel": 22, "name": "Custom Expansion 1", "type": ServoType.EXPANSION, "range": ServoRange.WIDE,
                    "limits": ServoLimits(500, 2500, 1500, 100, 50, 2.0, 3000, 1500),
                    "description": "Custom expansion port 1",
                    "default_speed": 50, "enabled": False
                },
                {
                    "channel": 23, "name": "Custom Expansion 2", "type": ServoType.EXPANSION, "range": ServoRange.WIDE,
                    "limits": ServoLimits(500, 2500, 1500, 100, 50, 2.0, 3000, 1500),
                    "description": "Custom expansion port 2",
                    "default_speed": 50, "enabled": False
                }
            ])

        # Create servo configurations
        for servo_def in r2d2_servos[:device.channels]:  # Limit to available channels
            config = ServoConfiguration(
                channel=servo_def["channel"],
                name=servo_def["name"],
                servo_type=servo_def["type"],
                servo_range=servo_def["range"],
                limits=servo_def["limits"],
                enabled=servo_def.get("enabled", True),
                description=servo_def["description"],
                default_speed=servo_def.get("default_speed", 50),
                default_acceleration=servo_def.get("default_acceleration", 25),
                smooth_motion=servo_def.get("smooth_motion", True),
                monitor_load=servo_def.get("monitor_load", False),
                alert_on_stall=servo_def.get("alert_on_stall", False)
            )

            self.servo_configs[servo_def["channel"]] = config
            logger.debug(f"Configured servo {servo_def['channel']}: {servo_def['name']}")

    def apply_safety_level(self, safety_level: SafetyLevel):
        """Apply safety level to all servo configurations"""
        self.safety_level = safety_level
        logger.info(f"🔒 Applying safety level: {safety_level.value}")

        with self.config_lock:
            for channel, config in self.servo_configs.items():
                original_limits = config.limits

                if safety_level == SafetyLevel.STRICT:
                    # Restrict ranges and speeds significantly
                    config.limits.max_speed = min(original_limits.max_speed, 50)
                    config.limits.max_acceleration = min(original_limits.max_acceleration, 20)

                    # Reduce range by 20%
                    center = (original_limits.min_pulse_us + original_limits.max_pulse_us) / 2
                    range_reduction = (original_limits.max_pulse_us - original_limits.min_pulse_us) * 0.1
                    config.limits.min_pulse_us = center - (center - original_limits.min_pulse_us - range_reduction)
                    config.limits.max_pulse_us = center + (original_limits.max_pulse_us - center - range_reduction)

                elif safety_level == SafetyLevel.NORMAL:
                    # Standard limits (already configured)
                    pass

                elif safety_level == SafetyLevel.RELAXED:
                    # Allow higher speeds and expanded range
                    config.limits.max_speed = min(255, int(original_limits.max_speed * 1.5))
                    config.limits.max_acceleration = min(255, int(original_limits.max_acceleration * 1.3))

                elif safety_level == SafetyLevel.DISABLED:
                    # Remove most restrictions (expert mode)
                    config.limits.max_speed = 255
                    config.limits.max_acceleration = 255
                    logger.warning(f"⚠️ Safety disabled for channel {channel} - Expert mode active")

                self._notify_config_change("safety_update", channel, config)

    def update_servo_config(self, channel: int, **kwargs) -> bool:
        """Update specific servo configuration parameters"""
        if channel not in self.servo_configs:
            logger.error(f"Invalid servo channel: {channel}")
            return False

        with self.config_lock:
            config = self.servo_configs[channel]

            # Update configuration fields
            for key, value in kwargs.items():
                if hasattr(config, key):
                    setattr(config, key, value)
                    logger.debug(f"Updated servo {channel} {key}: {value}")
                elif hasattr(config.limits, key):
                    setattr(config.limits, key, value)
                    logger.debug(f"Updated servo {channel} limits.{key}: {value}")
                else:
                    logger.warning(f"Unknown configuration parameter: {key}")
                    continue

            self._notify_config_change("parameter_update", channel, config)

        return True

    def calibrate_servo(self, channel: int, target_position_us: float, actual_position_us: float) -> bool:
        """Calibrate servo by calculating offset from target vs actual position"""
        if channel not in self.servo_configs:
            return False

        offset = target_position_us - actual_position_us

        with self.config_lock:
            config = self.servo_configs[channel]
            config.calibration_offset = offset

        logger.info(f"🎯 Servo {channel} calibrated: offset = {offset:.2f}μs")
        self._notify_config_change("calibration_update", channel, config)

        return True

    def _validate_configuration(self) -> bool:
        """Validate entire servo configuration for safety and consistency"""
        start_time = time.time()
        self.validation_errors.clear()

        with self.config_lock:
            for channel, config in self.servo_configs.items():
                # Validate pulse width ranges
                if config.limits.min_pulse_us >= config.limits.max_pulse_us:
                    error = f"Channel {channel}: Invalid pulse range"
                    self.validation_errors.append(error)

                # Validate home position is within range
                if not (config.limits.min_pulse_us <= config.limits.home_pulse_us <= config.limits.max_pulse_us):
                    error = f"Channel {channel}: Home position outside range"
                    self.validation_errors.append(error)

                # Validate speed and acceleration values
                if not (0 <= config.limits.max_speed <= 255):
                    error = f"Channel {channel}: Invalid speed limit"
                    self.validation_errors.append(error)

                if not (0 <= config.limits.max_acceleration <= 255):
                    error = f"Channel {channel}: Invalid acceleration limit"
                    self.validation_errors.append(error)

        self.last_validation_time = time.time() - start_time

        if self.validation_errors:
            logger.error(f"Configuration validation failed: {len(self.validation_errors)} errors")
            for error in self.validation_errors:
                logger.error(f"  {error}")
            return False
        else:
            logger.info(f"✅ Configuration validation passed ({self.last_validation_time:.3f}s)")
            return True

    def save_configuration(self, filename: str) -> bool:
        """Save current configuration to JSON file"""
        try:
            config_data = {
                "metadata": {
                    "version": "1.0",
                    "created": time.time(),
                    "safety_level": self.safety_level.value,
                    "description": "R2D2 Servo Configuration - Disney-Level Animatronics"
                },
                "servos": {}
            }

            with self.config_lock:
                for channel, config in self.servo_configs.items():
                    config_data["servos"][str(channel)] = {
                        "name": config.name,
                        "servo_type": config.servo_type.value,
                        "servo_range": config.servo_range.value,
                        "enabled": config.enabled,
                        "reverse": config.reverse,
                        "description": config.description,
                        "calibration_offset": config.calibration_offset,
                        "default_speed": config.default_speed,
                        "default_acceleration": config.default_acceleration,
                        "smooth_motion": config.smooth_motion,
                        "monitor_position": config.monitor_position,
                        "monitor_load": config.monitor_load,
                        "alert_on_stall": config.alert_on_stall,
                        "limits": {
                            "min_pulse_us": config.limits.min_pulse_us,
                            "max_pulse_us": config.limits.max_pulse_us,
                            "home_pulse_us": config.limits.home_pulse_us,
                            "max_speed": config.limits.max_speed,
                            "max_acceleration": config.limits.max_acceleration,
                            "position_deadband_us": config.limits.position_deadband_us,
                            "timeout_ms": config.limits.timeout_ms,
                            "emergency_position_us": config.limits.emergency_position_us
                        }
                    }

            with open(filename, 'w') as f:
                json.dump(config_data, f, indent=2)

            logger.info(f"✅ Configuration saved to {filename}")
            return True

        except Exception as e:
            logger.error(f"Failed to save configuration: {e}")
            return False

    def load_configuration(self, filename: str) -> bool:
        """Load configuration from JSON file"""
        try:
            with open(filename, 'r') as f:
                config_data = json.load(f)

            # Validate file format
            if "servos" not in config_data:
                logger.error("Invalid configuration file format")
                return False

            with self.config_lock:
                self.servo_configs.clear()

                for channel_str, servo_data in config_data["servos"].items():
                    channel = int(channel_str)

                    # Create limits object
                    limits_data = servo_data.get("limits", {})
                    limits = ServoLimits(
                        min_pulse_us=limits_data.get("min_pulse_us", 500),
                        max_pulse_us=limits_data.get("max_pulse_us", 2500),
                        home_pulse_us=limits_data.get("home_pulse_us", 1500),
                        max_speed=limits_data.get("max_speed", 100),
                        max_acceleration=limits_data.get("max_acceleration", 50),
                        position_deadband_us=limits_data.get("position_deadband_us", 2.0),
                        timeout_ms=limits_data.get("timeout_ms", 5000),
                        emergency_position_us=limits_data.get("emergency_position_us", 1500)
                    )

                    # Create servo configuration
                    config = ServoConfiguration(
                        channel=channel,
                        name=servo_data.get("name", f"Servo {channel}"),
                        servo_type=ServoType(servo_data.get("servo_type", "utility")),
                        servo_range=ServoRange(servo_data.get("servo_range", "wide")),
                        limits=limits,
                        enabled=servo_data.get("enabled", True),
                        reverse=servo_data.get("reverse", False),
                        description=servo_data.get("description", ""),
                        calibration_offset=servo_data.get("calibration_offset", 0.0),
                        default_speed=servo_data.get("default_speed", 50),
                        default_acceleration=servo_data.get("default_acceleration", 25),
                        smooth_motion=servo_data.get("smooth_motion", True),
                        monitor_position=servo_data.get("monitor_position", True),
                        monitor_load=servo_data.get("monitor_load", False),
                        alert_on_stall=servo_data.get("alert_on_stall", False)
                    )

                    self.servo_configs[channel] = config

            # Apply safety level if specified
            metadata = config_data.get("metadata", {})
            if "safety_level" in metadata:
                safety_level = SafetyLevel(metadata["safety_level"])
                self.apply_safety_level(safety_level)

            logger.info(f"✅ Configuration loaded from {filename} ({len(self.servo_configs)} servos)")

            # Validate loaded configuration
            self._validate_configuration()

            return True

        except Exception as e:
            logger.error(f"Failed to load configuration: {e}")
            return False

    def get_servo_config(self, channel: int) -> Optional[ServoConfiguration]:
        """Get configuration for specific servo channel"""
        with self.config_lock:
            return self.servo_configs.get(channel)

    def get_all_configs(self) -> Dict[int, ServoConfiguration]:
        """Get all servo configurations"""
        with self.config_lock:
            return self.servo_configs.copy()

    def get_status_report(self) -> Dict:
        """Generate comprehensive configuration status report"""
        with self.config_lock:
            servo_summary = {}
            for channel, config in self.servo_configs.items():
                servo_summary[channel] = {
                    "name": config.name,
                    "type": config.servo_type.value,
                    "range": config.servo_range.value,
                    "enabled": config.enabled,
                    "pulse_range_us": [config.limits.min_pulse_us, config.limits.max_pulse_us],
                    "home_us": config.limits.home_pulse_us,
                    "max_speed": config.limits.max_speed,
                    "calibration_offset": config.calibration_offset
                }

        return {
            "total_servos": len(self.servo_configs),
            "enabled_servos": sum(1 for c in self.servo_configs.values() if c.enabled),
            "safety_level": self.safety_level.value,
            "config_load_time": self.config_load_time,
            "last_validation_time": self.last_validation_time,
            "validation_errors": len(self.validation_errors),
            "servo_summary": servo_summary,
            "timestamp": time.time()
        }

def demo_servo_config_manager():
    """Demonstration of servo configuration management"""
    logger.info("🎯 Starting R2D2 Servo Configuration Manager Demo...")

    # Initialize hardware detector and config manager
    detector = MaestroHardwareDetector()
    config_manager = R2D2ServoConfigManager(detector)

    try:
        # Initialize from hardware (or use simulation)
        success = config_manager.initialize_from_hardware()

        if success:
            logger.info("Configuration initialized from hardware")
        else:
            logger.info("Using default simulation configuration")

        # Apply different safety levels
        for safety_level in [SafetyLevel.STRICT, SafetyLevel.NORMAL, SafetyLevel.RELAXED]:
            logger.info(f"\nTesting safety level: {safety_level.value}")
            config_manager.apply_safety_level(safety_level)

        # Update some servo parameters
        config_manager.update_servo_config(0, default_speed=75, smooth_motion=True)
        config_manager.update_servo_config(1, description="Enhanced head tilt with smooth motion")

        # Calibrate a servo
        config_manager.calibrate_servo(0, 1500.0, 1505.0)  # 5μs offset

        # Save configuration
        config_manager.save_configuration("r2d2_servo_config_demo.json")

        # Print status report
        status = config_manager.get_status_report()
        print("\n" + "="*60)
        print("R2D2 SERVO CONFIGURATION REPORT")
        print("="*60)
        print(json.dumps(status, indent=2))

        logger.info("✅ Servo configuration demo completed")

    except Exception as e:
        logger.error(f"Demo failed: {e}")

if __name__ == "__main__":
    demo_servo_config_manager()