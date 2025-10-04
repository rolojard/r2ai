#!/usr/bin/env python3
"""
R2D2 Servo Safety Module
Centralized safety system for all servo operations

This module provides comprehensive safety monitoring, validation, and
emergency response capabilities shared across all servo components.
"""

import time
import logging
import threading
from typing import Dict, List, Set, Optional, Callable, Any
from servo_base_classes import (
    SafetySystemBase,
    ServoCommand,
    ServoConfiguration,
    SafetyViolation,
    SafetyLevel,
    ServoCommandType,
    ServoLimits,
    validate_servo_position,
    apply_safety_constraints
)

logger = logging.getLogger(__name__)

class ServoSafetySystem(SafetySystemBase):
    """Comprehensive safety system for servo operations"""

    def __init__(self):
        super().__init__()
        self.servo_configs: Dict[int, ServoConfiguration] = {}
        self.position_history: Dict[int, List[Tuple[float, int]]] = {}
        self.velocity_limits: Dict[int, float] = {}
        self.emergency_stop_active = False
        self.safety_zones: Dict[str, Dict[str, Any]] = {}
        self.monitoring_thread = None
        self._stop_monitoring = False

        # Safety thresholds
        self.max_velocity = 500  # μs per second
        self.max_acceleration = 1000  # μs per second²
        self.position_tolerance = 50  # μs
        self.safety_check_interval = 0.1  # seconds

    def initialize_safety_configs(self, servo_configs: Dict[int, ServoConfiguration]):
        """Initialize safety configurations for all servos"""
        self.servo_configs = servo_configs.copy()

        # Initialize position history for each servo
        for channel in self.servo_configs:
            self.position_history[channel] = []
            self.velocity_limits[channel] = self.max_velocity

        logger.info(f"Safety system initialized for {len(self.servo_configs)} servos")

    def start_monitoring(self):
        """Start continuous safety monitoring"""
        if self.monitoring_thread and self.monitoring_thread.is_alive():
            return

        self._stop_monitoring = False
        self._monitoring = True
        self.monitoring_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
        self.monitoring_thread.start()
        logger.info("Safety monitoring started")

    def stop_monitoring(self):
        """Stop safety monitoring"""
        self._stop_monitoring = True
        self._monitoring = False
        if self.monitoring_thread:
            self.monitoring_thread.join(timeout=1)
        logger.info("Safety monitoring stopped")

    def validate_command(self, command: ServoCommand) -> bool:
        """Validate servo command against safety rules"""
        try:
            channel = command.channel

            # Check if channel is configured
            if channel not in self.servo_configs:
                self._record_violation(
                    "unknown_channel",
                    channel,
                    "critical",
                    f"Command for unconfigured channel {channel}",
                    "command_rejected"
                )
                return False

            config = self.servo_configs[channel]

            # Check if servo is enabled
            if not config.enabled:
                self._record_violation(
                    "servo_disabled",
                    channel,
                    "warning",
                    f"Command for disabled servo {channel}",
                    "command_rejected"
                )
                return False

            # Check emergency stop status
            if self.emergency_stop_active and command.command_type != ServoCommandType.EMERGENCY_STOP:
                self._record_violation(
                    "emergency_stop_active",
                    channel,
                    "critical",
                    "Command attempted while emergency stop is active",
                    "command_rejected"
                )
                return False

            # Validate position commands
            if command.command_type == ServoCommandType.POSITION:
                position = int(command.value)

                # Apply safety constraints
                safe_position = apply_safety_constraints(position, config)
                if safe_position != position:
                    self._record_violation(
                        "position_constrained",
                        channel,
                        "warning",
                        f"Position {position} constrained to {safe_position}",
                        "position_adjusted"
                    )
                    command.value = safe_position

                # Check velocity limits
                if not self._validate_velocity(channel, safe_position, command.duration):
                    return False

                # Check safety zones
                if not self._validate_safety_zones(channel, safe_position):
                    return False

            # Validate speed commands
            elif command.command_type == ServoCommandType.SPEED:
                if not self._validate_speed(channel, command.value):
                    return False

            # Validate acceleration commands
            elif command.command_type == ServoCommandType.ACCELERATION:
                if not self._validate_acceleration(channel, command.value):
                    return False

            return True

        except Exception as e:
            logger.error(f"Command validation error: {e}")
            self._record_violation(
                "validation_error",
                command.channel,
                "critical",
                f"Validation error: {str(e)}",
                "command_rejected"
            )
            return False

    def monitor_servo(self, channel: int, position: int) -> bool:
        """Monitor servo for safety violations"""
        try:
            if channel not in self.servo_configs:
                return False

            config = self.servo_configs[channel]
            current_time = time.time()

            # Record position in history
            if channel not in self.position_history:
                self.position_history[channel] = []

            self.position_history[channel].append((current_time, position))

            # Keep only recent history (last 5 seconds)
            cutoff_time = current_time - 5.0
            self.position_history[channel] = [
                (t, p) for t, p in self.position_history[channel] if t >= cutoff_time
            ]

            # Check position limits
            if not validate_servo_position(position, config.limits):
                self._record_violation(
                    "position_limit_exceeded",
                    channel,
                    "critical",
                    f"Position {position} exceeds limits",
                    "emergency_stop_triggered"
                )
                self.trigger_emergency_stop()
                return False

            # Check velocity
            if len(self.position_history[channel]) >= 2:
                recent_positions = self.position_history[channel][-2:]
                dt = recent_positions[1][0] - recent_positions[0][0]
                if dt > 0:
                    velocity = abs(recent_positions[1][1] - recent_positions[0][1]) / dt
                    if velocity > self.velocity_limits.get(channel, self.max_velocity):
                        self._record_violation(
                            "velocity_limit_exceeded",
                            channel,
                            "warning",
                            f"Velocity {velocity:.1f} exceeds limit",
                            "monitoring"
                        )

            return True

        except Exception as e:
            logger.error(f"Servo monitoring error: {e}")
            return False

    def trigger_emergency_stop(self):
        """Trigger emergency stop protocol"""
        self.emergency_stop_active = True
        self._record_violation(
            "emergency_stop",
            -1,
            "critical",
            "Emergency stop activated",
            "all_servos_stopped"
        )
        logger.critical("EMERGENCY STOP ACTIVATED")

    def reset_emergency_stop(self):
        """Reset emergency stop (requires manual intervention)"""
        self.emergency_stop_active = False
        logger.info("Emergency stop reset")

    def add_safety_zone(self, name: str, channels: List[int],
                       min_position: int, max_position: int):
        """Add a safety zone that restricts servo positions"""
        self.safety_zones[name] = {
            'channels': channels,
            'min_position': min_position,
            'max_position': max_position,
            'active': True
        }
        logger.info(f"Safety zone '{name}' added for channels {channels}")

    def remove_safety_zone(self, name: str):
        """Remove a safety zone"""
        if name in self.safety_zones:
            del self.safety_zones[name]
            logger.info(f"Safety zone '{name}' removed")

    def set_safety_level(self, level: SafetyLevel):
        """Set global safety level"""
        self.safety_level = level

        # Adjust safety parameters based on level
        if level == SafetyLevel.DEVELOPMENT:
            self.max_velocity = 1000
            self.max_acceleration = 2000
        elif level == SafetyLevel.TESTING:
            self.max_velocity = 750
            self.max_acceleration = 1500
        elif level == SafetyLevel.PRODUCTION:
            self.max_velocity = 500
            self.max_acceleration = 1000
        elif level == SafetyLevel.DEMONSTRATION:
            self.max_velocity = 300
            self.max_acceleration = 500
        elif level == SafetyLevel.EMERGENCY:
            self.max_velocity = 100
            self.max_acceleration = 200

        logger.info(f"Safety level set to {level.value}")

    def get_safety_status(self) -> Dict[str, Any]:
        """Get comprehensive safety status"""
        return {
            'safety_level': self.safety_level.value,
            'emergency_stop_active': self.emergency_stop_active,
            'monitoring_active': self._monitoring,
            'total_violations': len(self.violations),
            'recent_violations': len([
                v for v in self.violations
                if time.time() - v.timestamp < 300  # Last 5 minutes
            ]),
            'safety_zones': len(self.safety_zones),
            'monitored_servos': len(self.servo_configs),
            'velocity_limit': self.max_velocity,
            'acceleration_limit': self.max_acceleration
        }

    def get_violation_history(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get recent safety violations"""
        recent_violations = sorted(
            self.violations,
            key=lambda x: x.timestamp,
            reverse=True
        )[:limit]

        return [
            {
                'timestamp': v.timestamp,
                'type': v.violation_type,
                'channel': v.channel,
                'severity': v.severity,
                'description': v.description,
                'action_taken': v.action_taken,
                'resolved': v.resolved
            }
            for v in recent_violations
        ]

    def _validate_velocity(self, channel: int, target_position: int, duration: float) -> bool:
        """Validate movement velocity"""
        if not self.position_history.get(channel):
            return True  # No history to compare

        last_entry = self.position_history[channel][-1]
        last_position = last_entry[1]

        if duration <= 0:
            duration = 0.1  # Minimum duration for velocity calculation

        velocity = abs(target_position - last_position) / duration
        limit = self.velocity_limits.get(channel, self.max_velocity)

        if velocity > limit:
            self._record_violation(
                "velocity_limit_exceeded",
                channel,
                "warning",
                f"Commanded velocity {velocity:.1f} exceeds limit {limit}",
                "command_rejected"
            )
            return False

        return True

    def _validate_speed(self, channel: int, speed: float) -> bool:
        """Validate speed command"""
        config = self.servo_configs[channel]
        if speed > config.limits.max_speed:
            self._record_violation(
                "speed_limit_exceeded",
                channel,
                "warning",
                f"Speed {speed} exceeds limit {config.limits.max_speed}",
                "command_rejected"
            )
            return False
        return True

    def _validate_acceleration(self, channel: int, acceleration: float) -> bool:
        """Validate acceleration command"""
        config = self.servo_configs[channel]
        if acceleration > config.limits.max_acceleration:
            self._record_violation(
                "acceleration_limit_exceeded",
                channel,
                "warning",
                f"Acceleration {acceleration} exceeds limit {config.limits.max_acceleration}",
                "command_rejected"
            )
            return False
        return True

    def _validate_safety_zones(self, channel: int, position: int) -> bool:
        """Validate position against safety zones"""
        for zone_name, zone in self.safety_zones.items():
            if not zone.get('active', True):
                continue

            if channel in zone['channels']:
                if not (zone['min_position'] <= position <= zone['max_position']):
                    self._record_violation(
                        "safety_zone_violation",
                        channel,
                        "critical",
                        f"Position {position} violates safety zone '{zone_name}'",
                        "command_rejected"
                    )
                    return False

        return True

    def _record_violation(self, violation_type: str, channel: int, severity: str,
                         description: str, action_taken: str):
        """Record a safety violation"""
        violation = SafetyViolation(
            timestamp=time.time(),
            violation_type=violation_type,
            channel=channel,
            severity=severity,
            description=description,
            action_taken=action_taken
        )

        self._trigger_safety_violation(violation)
        logger.warning(f"Safety violation: {description}")

    def _monitoring_loop(self):
        """Background monitoring loop"""
        while not self._stop_monitoring:
            try:
                # Perform periodic safety checks
                self._check_system_health()
                self._cleanup_old_violations()

                time.sleep(self.safety_check_interval)

            except Exception as e:
                logger.error(f"Safety monitoring loop error: {e}")
                time.sleep(1)

    def _check_system_health(self):
        """Perform system health checks"""
        current_time = time.time()

        # Check for stale position data
        for channel, history in self.position_history.items():
            if history and current_time - history[-1][0] > 5.0:
                # Position data is stale
                self._record_violation(
                    "stale_position_data",
                    channel,
                    "warning",
                    f"No position updates for {current_time - history[-1][0]:.1f} seconds",
                    "monitoring"
                )

    def _cleanup_old_violations(self):
        """Clean up old violation records"""
        cutoff_time = time.time() - 3600  # Keep 1 hour of history
        self.violations = [
            v for v in self.violations if v.timestamp >= cutoff_time
        ]