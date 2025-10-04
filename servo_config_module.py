#!/usr/bin/env python3
"""
R2D2 Servo Configuration Module
Centralized configuration management for all servo systems

This module consolidates all servo configuration functionality from multiple
files into a single, comprehensive configuration management system.
"""

import json
import time
import logging
from typing import Dict, List, Optional, Any, Callable
from pathlib import Path
from servo_base_classes import (
    ConfigurationManagerBase,
    ServoConfiguration,
    ServoLimits,
    ServoType,
    ServoRange,
    SafetyLevel,
    create_default_servo_config,
    R2D2_SERVO_CHANNELS,
    DEFAULT_SAFETY_LIMITS
)

logger = logging.getLogger(__name__)

class ServoConfigurationManager(ConfigurationManagerBase):
    """Unified servo configuration manager"""

    def __init__(self, config_dir: str = "/home/rolo/r2ai/servo_configs"):
        super().__init__(config_dir)
        self.servo_configs: Dict[int, ServoConfiguration] = {}
        self.config_change_callbacks: List[Callable] = []
        self.hardware_profiles: Dict[str, Dict[str, Any]] = {}
        self.active_profile = "default"
        self._load_hardware_profiles()
        self._initialize_default_configs()

    def _initialize_default_configs(self):
        """Initialize default R2D2 servo configurations"""
        # Create configurations for all standard R2D2 channels
        r2d2_servo_definitions = {
            'DOME_ROTATION': {
                'channel': 0,
                'name': 'Dome Rotation',
                'type': ServoType.PRIMARY,
                'range': ServoRange.FULL,
                'limits': ServoLimits(
                    min_position=600, max_position=2400,
                    safe_min=800, safe_max=2200,
                    max_speed=80, max_acceleration=40
                ),
                'home_position': 1500
            },
            'HEAD_TILT': {
                'channel': 1,
                'name': 'Head Tilt',
                'type': ServoType.PRIMARY,
                'range': ServoRange.LIMITED,
                'limits': ServoLimits(
                    min_position=1200, max_position=1800,
                    safe_min=1300, safe_max=1700,
                    max_speed=60, max_acceleration=30
                ),
                'home_position': 1500
            },
            'PERISCOPE': {
                'channel': 2,
                'name': 'Periscope',
                'type': ServoType.UTILITY,
                'range': ServoRange.BINARY,
                'limits': ServoLimits(
                    min_position=1000, max_position=2000,
                    safe_min=1100, safe_max=1900,
                    max_speed=100, max_acceleration=50
                ),
                'home_position': 1000  # Retracted
            },
            'RADAR_EYE': {
                'channel': 3,
                'name': 'Radar Eye',
                'type': ServoType.DISPLAY,
                'range': ServoRange.FULL,
                'limits': ServoLimits(
                    min_position=600, max_position=2400,
                    safe_min=800, safe_max=2200,
                    max_speed=120, max_acceleration=60
                ),
                'home_position': 1500
            },
            'FRONT_ARM': {
                'channel': 4,
                'name': 'Front Utility Arm',
                'type': ServoType.UTILITY,
                'range': ServoRange.LIMITED,
                'limits': DEFAULT_SAFETY_LIMITS,
                'home_position': 1200  # Retracted
            },
            'REAR_ARM': {
                'channel': 5,
                'name': 'Rear Utility Arm',
                'type': ServoType.UTILITY,
                'range': ServoRange.LIMITED,
                'limits': DEFAULT_SAFETY_LIMITS,
                'home_position': 1200  # Retracted
            },
            'UTILITY_ARM_1': {
                'channel': 6,
                'name': 'Utility Arm 1',
                'type': ServoType.UTILITY,
                'range': ServoRange.LIMITED,
                'limits': DEFAULT_SAFETY_LIMITS,
                'home_position': 1500
            },
            'UTILITY_ARM_2': {
                'channel': 7,
                'name': 'Utility Arm 2',
                'type': ServoType.UTILITY,
                'range': ServoRange.LIMITED,
                'limits': DEFAULT_SAFETY_LIMITS,
                'home_position': 1500
            },
            'DOOR_PANEL_1': {
                'channel': 8,
                'name': 'Door Panel 1',
                'type': ServoType.PANEL,
                'range': ServoRange.BINARY,
                'limits': DEFAULT_SAFETY_LIMITS,
                'home_position': 1000  # Closed
            },
            'DOOR_PANEL_2': {
                'channel': 9,
                'name': 'Door Panel 2',
                'type': ServoType.PANEL,
                'range': ServoRange.BINARY,
                'limits': DEFAULT_SAFETY_LIMITS,
                'home_position': 1000  # Closed
            },
            'DOOR_PANEL_3': {
                'channel': 10,
                'name': 'Door Panel 3',
                'type': ServoType.PANEL,
                'range': ServoRange.BINARY,
                'limits': DEFAULT_SAFETY_LIMITS,
                'home_position': 1000  # Closed
            },
            'HOLOPROJECTOR': {
                'channel': 11,
                'name': 'Holoprojector',
                'type': ServoType.SPECIAL,
                'range': ServoRange.BINARY,
                'limits': DEFAULT_SAFETY_LIMITS,
                'home_position': 1000  # Retracted
            },
            'LOGIC_DISPLAY_1': {
                'channel': 12,
                'name': 'Logic Display 1',
                'type': ServoType.DISPLAY,
                'range': ServoRange.LIMITED,
                'limits': DEFAULT_SAFETY_LIMITS,
                'home_position': 1500
            },
            'LOGIC_DISPLAY_2': {
                'channel': 13,
                'name': 'Logic Display 2',
                'type': ServoType.DISPLAY,
                'range': ServoRange.LIMITED,
                'limits': DEFAULT_SAFETY_LIMITS,
                'home_position': 1500
            },
            'AUX_1': {
                'channel': 14,
                'name': 'Auxiliary 1',
                'type': ServoType.EXPANSION,
                'range': ServoRange.LIMITED,
                'limits': DEFAULT_SAFETY_LIMITS,
                'home_position': 1500
            },
            'AUX_2': {
                'channel': 15,
                'name': 'Auxiliary 2',
                'type': ServoType.EXPANSION,
                'range': ServoRange.LIMITED,
                'limits': DEFAULT_SAFETY_LIMITS,
                'home_position': 1500
            }
        }

        # Create servo configurations
        for servo_name, servo_def in r2d2_servo_definitions.items():
            config = ServoConfiguration(
                channel=servo_def['channel'],
                name=servo_def['name'],
                servo_type=servo_def['type'],
                servo_range=servo_def['range'],
                limits=servo_def['limits'],
                home_position=servo_def['home_position'],
                default_speed=50,
                default_acceleration=20,
                enabled=True,
                inverted=False,
                safety_level=SafetyLevel.PRODUCTION
            )
            self.servo_configs[servo_def['channel']] = config

        logger.info(f"Initialized {len(self.servo_configs)} default servo configurations")

    def _load_hardware_profiles(self):
        """Load hardware-specific configuration profiles"""
        self.hardware_profiles = {
            'maestro_6': {
                'name': 'Pololu Maestro 6-Channel',
                'max_channels': 6,
                'default_limits': DEFAULT_SAFETY_LIMITS,
                'recommended_channels': [0, 1, 2, 3, 4, 5]
            },
            'maestro_12': {
                'name': 'Pololu Maestro 12-Channel',
                'max_channels': 12,
                'default_limits': DEFAULT_SAFETY_LIMITS,
                'recommended_channels': list(range(12))
            },
            'maestro_18': {
                'name': 'Pololu Maestro 18-Channel',
                'max_channels': 18,
                'default_limits': DEFAULT_SAFETY_LIMITS,
                'recommended_channels': list(range(16))  # Use first 16 for R2D2
            },
            'maestro_24': {
                'name': 'Pololu Maestro 24-Channel',
                'max_channels': 24,
                'default_limits': DEFAULT_SAFETY_LIMITS,
                'recommended_channels': list(range(16))  # Use first 16 for R2D2
            },
            'pca9685': {
                'name': 'PCA9685 I2C Controller',
                'max_channels': 16,
                'default_limits': ServoLimits(
                    min_position=150, max_position=600,  # Different scale for PWM
                    safe_min=200, safe_max=550,
                    max_speed=100, max_acceleration=50
                ),
                'recommended_channels': list(range(16))
            }
        }

    def save_configuration(self, name: str, config: Dict[str, Any] = None) -> bool:
        """Save current configuration to file"""
        try:
            config_file = self.config_dir / f"{name}.json"

            if config is None:
                # Save current servo configurations
                config_data = {
                    'metadata': {
                        'name': name,
                        'created': time.time(),
                        'version': '2.0',
                        'profile': self.active_profile,
                        'total_servos': len(self.servo_configs)
                    },
                    'servos': {}
                }

                for channel, servo_config in self.servo_configs.items():
                    config_data['servos'][str(channel)] = {
                        'channel': servo_config.channel,
                        'name': servo_config.name,
                        'servo_type': servo_config.servo_type.value,
                        'servo_range': servo_config.servo_range.value,
                        'limits': {
                            'min_position': servo_config.limits.min_position,
                            'max_position': servo_config.limits.max_position,
                            'max_speed': servo_config.limits.max_speed,
                            'max_acceleration': servo_config.limits.max_acceleration,
                            'safe_min': servo_config.limits.safe_min,
                            'safe_max': servo_config.limits.safe_max,
                            'emergency_stop_speed': servo_config.limits.emergency_stop_speed
                        },
                        'home_position': servo_config.home_position,
                        'default_speed': servo_config.default_speed,
                        'default_acceleration': servo_config.default_acceleration,
                        'enabled': servo_config.enabled,
                        'inverted': servo_config.inverted,
                        'safety_level': servo_config.safety_level.value
                    }
            else:
                config_data = config

            with open(config_file, 'w') as f:
                json.dump(config_data, f, indent=2)

            logger.info(f"Configuration '{name}' saved to {config_file}")
            return True

        except Exception as e:
            logger.error(f"Failed to save configuration '{name}': {e}")
            return False

    def load_configuration(self, name: str) -> Optional[Dict[str, Any]]:
        """Load configuration from file"""
        try:
            config_file = self.config_dir / f"{name}.json"

            if not config_file.exists():
                logger.warning(f"Configuration file not found: {config_file}")
                return None

            with open(config_file, 'r') as f:
                config_data = json.load(f)

            # Apply loaded configuration
            if 'servos' in config_data:
                self.servo_configs.clear()

                for channel_str, servo_data in config_data['servos'].items():
                    channel = int(channel_str)

                    # Create limits object
                    limits_data = servo_data.get('limits', {})
                    limits = ServoLimits(
                        min_position=limits_data.get('min_position', 992),
                        max_position=limits_data.get('max_position', 2000),
                        max_speed=limits_data.get('max_speed', 100),
                        max_acceleration=limits_data.get('max_acceleration', 50),
                        safe_min=limits_data.get('safe_min', 1200),
                        safe_max=limits_data.get('safe_max', 1800),
                        emergency_stop_speed=limits_data.get('emergency_stop_speed', 255)
                    )

                    # Create servo configuration
                    config = ServoConfiguration(
                        channel=channel,
                        name=servo_data.get('name', f'Servo_{channel}'),
                        servo_type=ServoType(servo_data.get('servo_type', 'utility')),
                        servo_range=ServoRange(servo_data.get('servo_range', 'limited')),
                        limits=limits,
                        home_position=servo_data.get('home_position', 1500),
                        default_speed=servo_data.get('default_speed', 50),
                        default_acceleration=servo_data.get('default_acceleration', 20),
                        enabled=servo_data.get('enabled', True),
                        inverted=servo_data.get('inverted', False),
                        safety_level=SafetyLevel(servo_data.get('safety_level', 'production'))
                    )

                    self.servo_configs[channel] = config

                # Update active profile
                if 'metadata' in config_data:
                    self.active_profile = config_data['metadata'].get('profile', 'default')

                logger.info(f"Configuration '{name}' loaded with {len(self.servo_configs)} servos")
                self._notify_config_change('loaded', -1, None)

            return config_data

        except Exception as e:
            logger.error(f"Failed to load configuration '{name}': {e}")
            return None

    def validate_configuration(self, config: Dict[str, Any]) -> List[str]:
        """Validate configuration and return any errors"""
        errors = []

        try:
            # Check metadata
            if 'metadata' not in config:
                errors.append("Missing metadata section")
            elif 'version' not in config['metadata']:
                errors.append("Missing version in metadata")

            # Check servos section
            if 'servos' not in config:
                errors.append("Missing servos section")
                return errors

            servos = config['servos']
            channels_used = set()

            for channel_str, servo_data in servos.items():
                try:
                    channel = int(channel_str)
                except ValueError:
                    errors.append(f"Invalid channel identifier: {channel_str}")
                    continue

                # Check for duplicate channels
                if channel in channels_used:
                    errors.append(f"Duplicate channel: {channel}")
                channels_used.add(channel)

                # Validate servo data
                if 'name' not in servo_data:
                    errors.append(f"Channel {channel}: Missing name")

                if 'limits' in servo_data:
                    limits = servo_data['limits']
                    min_pos = limits.get('min_position', 0)
                    max_pos = limits.get('max_position', 0)

                    if min_pos >= max_pos:
                        errors.append(f"Channel {channel}: Invalid position limits")

                    safe_min = limits.get('safe_min', min_pos)
                    safe_max = limits.get('safe_max', max_pos)

                    if safe_min < min_pos or safe_max > max_pos:
                        errors.append(f"Channel {channel}: Safe limits exceed position limits")

                # Validate home position
                home_pos = servo_data.get('home_position', 1500)
                if 'limits' in servo_data:
                    limits = servo_data['limits']
                    if not (limits.get('min_position', 0) <= home_pos <= limits.get('max_position', 3000)):
                        errors.append(f"Channel {channel}: Home position outside limits")

        except Exception as e:
            errors.append(f"Configuration validation error: {str(e)}")

        return errors

    def update_servo_config(self, channel: int, **kwargs) -> bool:
        """Update servo configuration parameters"""
        try:
            if channel not in self.servo_configs:
                logger.warning(f"Cannot update unconfigured channel {channel}")
                return False

            config = self.servo_configs[channel]
            updated = False

            # Update configuration fields
            for key, value in kwargs.items():
                if hasattr(config, key):
                    setattr(config, key, value)
                    updated = True
                elif key == 'limits' and isinstance(value, dict):
                    # Update limits
                    for limit_key, limit_value in value.items():
                        if hasattr(config.limits, limit_key):
                            setattr(config.limits, limit_key, limit_value)
                            updated = True

            if updated:
                self._notify_config_change('updated', channel, config)
                logger.info(f"Updated configuration for channel {channel}")

            return updated

        except Exception as e:
            logger.error(f"Failed to update servo config for channel {channel}: {e}")
            return False

    def get_servo_config(self, channel: int) -> Optional[ServoConfiguration]:
        """Get servo configuration for specific channel"""
        return self.servo_configs.get(channel)

    def get_all_configs(self) -> Dict[int, ServoConfiguration]:
        """Get all servo configurations"""
        return self.servo_configs.copy()

    def set_hardware_profile(self, profile_name: str) -> bool:
        """Set active hardware profile"""
        if profile_name not in self.hardware_profiles:
            logger.error(f"Unknown hardware profile: {profile_name}")
            return False

        self.active_profile = profile_name
        profile = self.hardware_profiles[profile_name]

        # Apply profile-specific defaults
        default_limits = profile.get('default_limits', DEFAULT_SAFETY_LIMITS)

        for channel, config in self.servo_configs.items():
            if channel in profile.get('recommended_channels', []):
                config.limits = default_limits

        logger.info(f"Applied hardware profile: {profile['name']}")
        self._notify_config_change('profile_changed', -1, None)
        return True

    def apply_safety_level(self, safety_level: SafetyLevel):
        """Apply safety level to all servo configurations"""
        for config in self.servo_configs.values():
            config.safety_level = safety_level

        logger.info(f"Applied safety level {safety_level.value} to all servos")
        self._notify_config_change('safety_level_changed', -1, None)

    def add_config_change_callback(self, callback: Callable):
        """Add callback for configuration changes"""
        self.config_change_callbacks.append(callback)

    def _notify_config_change(self, change_type: str, channel: int, config: Optional[ServoConfiguration]):
        """Notify callbacks of configuration changes"""
        for callback in self.config_change_callbacks:
            try:
                callback(change_type, channel, config)
            except Exception as e:
                logger.error(f"Config change callback error: {e}")

    def list_configurations(self) -> List[Dict[str, Any]]:
        """List all saved configurations"""
        configs = []

        try:
            for config_file in self.config_dir.glob("*.json"):
                try:
                    with open(config_file, 'r') as f:
                        config_data = json.load(f)

                    metadata = config_data.get('metadata', {})
                    configs.append({
                        'name': config_file.stem,
                        'display_name': metadata.get('name', config_file.stem),
                        'created': metadata.get('created', 0),
                        'version': metadata.get('version', 'unknown'),
                        'profile': metadata.get('profile', 'unknown'),
                        'servo_count': metadata.get('total_servos', 0),
                        'file_path': str(config_file)
                    })

                except Exception as e:
                    logger.warning(f"Error reading config file {config_file}: {e}")

        except Exception as e:
            logger.error(f"Error listing configurations: {e}")

        return sorted(configs, key=lambda x: x['created'], reverse=True)

    def export_configuration(self, name: str, export_path: str) -> bool:
        """Export configuration to external file"""
        try:
            config_file = self.config_dir / f"{name}.json"
            if not config_file.exists():
                logger.error(f"Configuration '{name}' not found")
                return False

            import shutil
            shutil.copy2(config_file, export_path)
            logger.info(f"Configuration '{name}' exported to {export_path}")
            return True

        except Exception as e:
            logger.error(f"Failed to export configuration '{name}': {e}")
            return False

    def import_configuration(self, import_path: str, name: str) -> bool:
        """Import configuration from external file"""
        try:
            import shutil
            config_file = self.config_dir / f"{name}.json"
            shutil.copy2(import_path, config_file)

            # Validate imported configuration
            loaded_config = self.load_configuration(name)
            if loaded_config is None:
                logger.error(f"Failed to import configuration from {import_path}")
                return False

            errors = self.validate_configuration(loaded_config)
            if errors:
                logger.warning(f"Imported configuration has validation errors: {errors}")

            logger.info(f"Configuration imported from {import_path} as '{name}'")
            return True

        except Exception as e:
            logger.error(f"Failed to import configuration: {e}")
            return False

    def get_hardware_profiles(self) -> Dict[str, Dict[str, Any]]:
        """Get available hardware profiles"""
        return self.hardware_profiles.copy()

    def reset_to_defaults(self):
        """Reset all configurations to defaults"""
        self.servo_configs.clear()
        self._initialize_default_configs()
        self.active_profile = "default"
        self._notify_config_change('reset', -1, None)
        logger.info("Configuration reset to defaults")