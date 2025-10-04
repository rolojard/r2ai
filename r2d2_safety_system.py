#!/usr/bin/env python3
"""
R2D2 Safety System and Emergency Protocols
Professional Safety Management for Animatronic Systems

This module provides comprehensive safety systems including:
- Multi-level emergency stop protocols
- Collision detection and avoidance
- Thermal protection and monitoring
- Electrical safety and fault detection
- User safety protocols
- Automated safety checks and validations
- Recovery procedures and fail-safes

Author: Imagineer Specialist
Version: 1.0.0
Date: 2024-09-22
"""

import time
import logging
import threading
import json
import numpy as np
from typing import Dict, List, Tuple, Optional, Callable, Set
from dataclasses import dataclass, field, asdict
from enum import Enum
from pathlib import Path
import queue
import signal
import psutil
import GPUtil

logger = logging.getLogger(__name__)

class SafetyLevel(Enum):
    """Safety system alert levels"""
    NORMAL = "normal"
    CAUTION = "caution"
    WARNING = "warning"
    CRITICAL = "critical"
    EMERGENCY = "emergency"

class EmergencyType(Enum):
    """Types of emergency conditions"""
    MANUAL_STOP = "manual_stop"
    COLLISION_DETECTED = "collision_detected"
    OVERHEATING = "overheating"
    POWER_FAULT = "power_fault"
    SERVO_FAILURE = "servo_failure"
    SYSTEM_FAULT = "system_fault"
    USER_SAFETY = "user_safety"
    COMMUNICATION_LOSS = "communication_loss"
    MECHANICAL_FAILURE = "mechanical_failure"

class SafetyState(Enum):
    """Overall safety system states"""
    SAFE = "safe"
    CAUTION = "caution"
    UNSAFE = "unsafe"
    EMERGENCY_STOP = "emergency_stop"
    MAINTENANCE = "maintenance"
    SYSTEM_FAULT = "system_fault"

@dataclass
class SafetyAlert:
    """Safety alert/incident record"""
    timestamp: float
    alert_type: EmergencyType
    level: SafetyLevel
    description: str
    affected_systems: List[str] = field(default_factory=list)
    recovery_actions: List[str] = field(default_factory=list)
    auto_resolved: bool = False
    user_acknowledged: bool = False
    resolution_timestamp: Optional[float] = None

@dataclass
class SafetyLimits:
    """Configurable safety limits and thresholds"""
    # Temperature limits (Celsius)
    max_servo_temperature: float = 70.0
    max_ambient_temperature: float = 45.0
    critical_temperature: float = 80.0

    # Position limits (quarter-microseconds)
    max_position_error: int = 200
    critical_position_error: int = 500

    # Speed limits (positions/second)
    max_servo_speed: float = 2000.0
    emergency_speed_limit: float = 500.0

    # Current limits (Amperes)
    max_servo_current: float = 1.5
    critical_current: float = 2.0
    total_current_limit: float = 15.0

    # Voltage limits
    min_voltage: float = 4.5
    max_voltage: float = 7.5
    critical_low_voltage: float = 4.0

    # Timing limits (seconds)
    max_communication_timeout: float = 2.0
    max_response_time: float = 0.5
    watchdog_timeout: float = 5.0

    # Movement limits
    max_continuous_operation: float = 3600.0  # 1 hour
    max_movement_range: Dict[int, Tuple[int, int]] = field(default_factory=dict)

@dataclass
class CollisionZone:
    """Defines a collision detection zone"""
    name: str
    servo_channel: int
    min_position: int
    max_position: int
    description: str
    severity: SafetyLevel = SafetyLevel.WARNING

@dataclass
class SafetyProfile:
    """Complete safety configuration profile"""
    name: str
    description: str
    limits: SafetyLimits
    collision_zones: List[CollisionZone] = field(default_factory=list)
    enabled_protocols: Set[str] = field(default_factory=set)
    emergency_actions: Dict[str, List[str]] = field(default_factory=dict)

class SafetySystem:
    """Comprehensive safety management system"""

    def __init__(self, servo_system, monitoring_system, config_path: str = "/home/rolo/r2ai/configs/safety_config.json"):
        """Initialize safety system"""
        self.servo_system = servo_system
        self.monitoring_system = monitoring_system
        self.config_path = Path(config_path)
        self.config_path.parent.mkdir(parents=True, exist_ok=True)

        # Safety state
        self.current_state = SafetyState.SAFE
        self.emergency_active = False
        self.safety_alerts: List[SafetyAlert] = []
        self.safety_log: List[Dict] = []

        # Safety configuration
        self.safety_profile = self._create_default_safety_profile()
        self.safety_limits = self.safety_profile.limits

        # Monitoring and control
        self.safety_active = True
        self.monitoring_thread: Optional[threading.Thread] = None
        self.watchdog_thread: Optional[threading.Thread] = None
        self.emergency_callbacks: List[Callable] = []

        # System monitoring
        self.last_heartbeat = time.time()
        self.communication_ok = True
        self.system_health_ok = True

        # Performance tracking
        self.servo_operation_time: Dict[int, float] = {}
        self.last_position_check: Dict[int, Tuple[float, int]] = {}

        logger.info("🛡️ Safety system initialized")

        # Load configuration
        self._load_safety_configuration()

        # Start safety monitoring
        self._start_safety_monitoring()

        # Setup signal handlers for emergency stops
        self._setup_signal_handlers()

    def _create_default_safety_profile(self) -> SafetyProfile:
        """Create default safety profile for R2D2"""
        limits = SafetyLimits()

        # Define safe movement ranges for R2D2 servos
        limits.max_movement_range = {
            0: (2000, 8000),   # Dome rotation - full range
            1: (4000, 8000),   # Head tilt - limited range
            2: (4000, 7500),   # Periscope - safe extension range
            3: (4000, 8000),   # Radar eye - safe rotation
            4: (2000, 8000),   # Utility arm left
            5: (2000, 8000),   # Utility arm right
            6: (4000, 7000),   # Dome panel front
            7: (4000, 7000),   # Dome panel left
            8: (4000, 7000),   # Dome panel right
            9: (4000, 7000),   # Dome panel back
            10: (4000, 7000),  # Body door left
            11: (4000, 7000),  # Body door right
        }

        # Define collision zones
        collision_zones = [
            CollisionZone("dome_rotation_limit", 0, 1500, 2000, "Dome rotation lower limit", SafetyLevel.CRITICAL),
            CollisionZone("dome_rotation_upper", 0, 8000, 8500, "Dome rotation upper limit", SafetyLevel.CRITICAL),
            CollisionZone("head_tilt_down", 1, 3500, 4000, "Head tilt down limit", SafetyLevel.WARNING),
            CollisionZone("periscope_retract", 2, 3500, 4000, "Periscope retraction limit", SafetyLevel.WARNING),
            CollisionZone("periscope_extend", 2, 7500, 8000, "Periscope extension limit", SafetyLevel.CRITICAL),
        ]

        # Emergency action protocols
        emergency_actions = {
            "servo_overheating": ["emergency_stop", "log_incident", "notify_maintenance"],
            "collision_detected": ["stop_movement", "retract_to_safe", "log_incident"],
            "power_fault": ["emergency_stop", "safe_shutdown", "log_incident"],
            "communication_loss": ["maintain_position", "attempt_reconnect", "emergency_stop_if_timeout"],
            "mechanical_failure": ["emergency_stop", "disable_affected_servo", "log_incident"],
        }

        enabled_protocols = {
            "collision_detection",
            "thermal_protection",
            "electrical_monitoring",
            "communication_watchdog",
            "position_validation",
            "speed_limiting",
            "emergency_stop",
        }

        return SafetyProfile(
            name="R2D2_Default",
            description="Default safety profile for R2D2 animatronics",
            limits=limits,
            collision_zones=collision_zones,
            enabled_protocols=enabled_protocols,
            emergency_actions=emergency_actions
        )

    def _start_safety_monitoring(self):
        """Start safety monitoring threads"""
        # Main safety monitoring thread
        self.monitoring_thread = threading.Thread(
            target=self._safety_monitoring_loop,
            daemon=True,
            name="SafetyMonitor"
        )
        self.monitoring_thread.start()

        # Watchdog thread
        self.watchdog_thread = threading.Thread(
            target=self._watchdog_loop,
            daemon=True,
            name="SafetyWatchdog"
        )
        self.watchdog_thread.start()

        logger.info("✅ Safety monitoring started")

    def _safety_monitoring_loop(self):
        """Main safety monitoring loop"""
        check_interval = 0.1  # 10Hz safety checks

        while self.safety_active:
            try:
                start_time = time.time()

                # Update heartbeat
                self.last_heartbeat = time.time()

                # Perform safety checks
                if "thermal_protection" in self.safety_profile.enabled_protocols:
                    self._check_thermal_safety()

                if "position_validation" in self.safety_profile.enabled_protocols:
                    self._check_position_safety()

                if "collision_detection" in self.safety_profile.enabled_protocols:
                    self._check_collision_zones()

                if "speed_limiting" in self.safety_profile.enabled_protocols:
                    self._check_speed_limits()

                if "electrical_monitoring" in self.safety_profile.enabled_protocols:
                    self._check_electrical_safety()

                if "communication_watchdog" in self.safety_profile.enabled_protocols:
                    self._check_communication_health()

                # Update overall safety state
                self._update_safety_state()

                # Clean up old alerts
                self._cleanup_old_alerts()

                # Sleep until next check
                elapsed = time.time() - start_time
                sleep_time = max(0, check_interval - elapsed)
                if sleep_time > 0:
                    time.sleep(sleep_time)

            except Exception as e:
                logger.error(f"Safety monitoring error: {e}")
                self._trigger_emergency(EmergencyType.SYSTEM_FAULT, f"Safety monitoring error: {e}")
                time.sleep(1.0)

    def _watchdog_loop(self):
        """Safety watchdog loop"""
        while self.safety_active:
            try:
                current_time = time.time()

                # Check if main safety thread is responsive
                if current_time - self.last_heartbeat > self.safety_limits.watchdog_timeout:
                    logger.critical("🚨 Safety watchdog timeout - triggering emergency stop")
                    self._trigger_emergency(EmergencyType.SYSTEM_FAULT, "Safety watchdog timeout")

                time.sleep(1.0)  # 1Hz watchdog checks

            except Exception as e:
                logger.critical(f"Watchdog error: {e}")
                time.sleep(1.0)

    def _check_thermal_safety(self):
        """Check thermal safety conditions"""
        if not self.monitoring_system:
            return

        metrics = self.monitoring_system.get_current_metrics()

        for channel, metric in metrics.items():
            # Check servo temperature
            if metric.temperature > self.safety_limits.critical_temperature:
                self._trigger_emergency(
                    EmergencyType.OVERHEATING,
                    f"Servo {channel} critical temperature: {metric.temperature:.1f}°C"
                )
            elif metric.temperature > self.safety_limits.max_servo_temperature:
                self._create_safety_alert(
                    EmergencyType.OVERHEATING,
                    SafetyLevel.WARNING,
                    f"Servo {channel} high temperature: {metric.temperature:.1f}°C",
                    [f"servo_{channel}"]
                )

        # Check system temperature
        try:
            cpu_temp = self._get_cpu_temperature()
            if cpu_temp and cpu_temp > self.safety_limits.max_ambient_temperature:
                self._create_safety_alert(
                    EmergencyType.OVERHEATING,
                    SafetyLevel.WARNING,
                    f"System temperature high: {cpu_temp:.1f}°C",
                    ["system"]
                )
        except Exception as e:
            logger.debug(f"Could not check system temperature: {e}")

    def _check_position_safety(self):
        """Check servo position safety"""
        if not self.monitoring_system:
            return

        metrics = self.monitoring_system.get_current_metrics()

        for channel, metric in metrics.items():
            # Check position error
            if metric.position_error > self.safety_limits.critical_position_error:
                self._trigger_emergency(
                    EmergencyType.SERVO_FAILURE,
                    f"Servo {channel} critical position error: {metric.position_error}"
                )
            elif metric.position_error > self.safety_limits.max_position_error:
                self._create_safety_alert(
                    EmergencyType.SERVO_FAILURE,
                    SafetyLevel.WARNING,
                    f"Servo {channel} position error: {metric.position_error}",
                    [f"servo_{channel}"]
                )

            # Check position within safe range
            if channel in self.safety_limits.max_movement_range:
                min_pos, max_pos = self.safety_limits.max_movement_range[channel]
                if metric.position < min_pos or metric.position > max_pos:
                    self._create_safety_alert(
                        EmergencyType.MECHANICAL_FAILURE,
                        SafetyLevel.CRITICAL,
                        f"Servo {channel} position out of safe range: {metric.position}",
                        [f"servo_{channel}"]
                    )

    def _check_collision_zones(self):
        """Check for collision zone violations"""
        if not self.monitoring_system:
            return

        metrics = self.monitoring_system.get_current_metrics()

        for zone in self.safety_profile.collision_zones:
            if zone.servo_channel in metrics:
                metric = metrics[zone.servo_channel]

                if zone.min_position <= metric.position <= zone.max_position:
                    if zone.severity == SafetyLevel.CRITICAL:
                        self._trigger_emergency(
                            EmergencyType.COLLISION_DETECTED,
                            f"Critical collision zone violation: {zone.name}"
                        )
                    else:
                        self._create_safety_alert(
                            EmergencyType.COLLISION_DETECTED,
                            zone.severity,
                            f"Collision zone warning: {zone.name}",
                            [f"servo_{zone.servo_channel}"]
                        )

    def _check_speed_limits(self):
        """Check servo speed limits"""
        if not self.monitoring_system:
            return

        metrics = self.monitoring_system.get_current_metrics()

        for channel, metric in metrics.items():
            if metric.speed > self.safety_limits.max_servo_speed:
                self._create_safety_alert(
                    EmergencyType.MECHANICAL_FAILURE,
                    SafetyLevel.WARNING,
                    f"Servo {channel} speed limit exceeded: {metric.speed:.1f}",
                    [f"servo_{channel}"]
                )

    def _check_electrical_safety(self):
        """Check electrical safety conditions"""
        if not self.monitoring_system:
            return

        metrics = self.monitoring_system.get_current_metrics()
        total_current = sum(metric.current for metric in metrics.values())

        # Check total current
        if total_current > self.safety_limits.total_current_limit:
            self._trigger_emergency(
                EmergencyType.POWER_FAULT,
                f"Total current limit exceeded: {total_current:.2f}A"
            )

        # Check individual servo currents and voltages
        for channel, metric in metrics.items():
            if metric.current > self.safety_limits.critical_current:
                self._trigger_emergency(
                    EmergencyType.POWER_FAULT,
                    f"Servo {channel} critical current: {metric.current:.2f}A"
                )
            elif metric.current > self.safety_limits.max_servo_current:
                self._create_safety_alert(
                    EmergencyType.POWER_FAULT,
                    SafetyLevel.WARNING,
                    f"Servo {channel} high current: {metric.current:.2f}A",
                    [f"servo_{channel}"]
                )

            # Check voltage
            if metric.voltage < self.safety_limits.critical_low_voltage:
                self._trigger_emergency(
                    EmergencyType.POWER_FAULT,
                    f"Critical low voltage: {metric.voltage:.2f}V"
                )
            elif metric.voltage < self.safety_limits.min_voltage or metric.voltage > self.safety_limits.max_voltage:
                self._create_safety_alert(
                    EmergencyType.POWER_FAULT,
                    SafetyLevel.WARNING,
                    f"Voltage out of range: {metric.voltage:.2f}V",
                    ["power_supply"]
                )

    def _check_communication_health(self):
        """Check communication system health"""
        # This would check actual communication with servo controller
        # For now, simulate based on system responsiveness
        if self.servo_system and hasattr(self.servo_system, 'active_controller'):
            controller = self.servo_system.active_controller
            if controller and not controller.simulation_mode:
                # In real implementation, would test actual communication
                self.communication_ok = True
            else:
                # In simulation mode, assume communication is OK
                self.communication_ok = True
        else:
            self.communication_ok = False

        if not self.communication_ok:
            self._create_safety_alert(
                EmergencyType.COMMUNICATION_LOSS,
                SafetyLevel.CRITICAL,
                "Communication with servo controller lost",
                ["communication"]
            )

    def _get_cpu_temperature(self) -> Optional[float]:
        """Get CPU temperature for system thermal monitoring"""
        try:
            # Try to get GPU temperature first (Jetson Nano)
            try:
                gpus = GPUtil.getGPUs()
                if gpus:
                    return gpus[0].temperature
            except:
                pass

            # Try CPU temperature
            temps = psutil.sensors_temperatures()
            if 'cpu_thermal' in temps:
                return temps['cpu_thermal'][0].current
            elif 'coretemp' in temps:
                return temps['coretemp'][0].current

        except Exception:
            pass

        return None

    def _update_safety_state(self):
        """Update overall safety state based on current conditions"""
        if self.emergency_active:
            self.current_state = SafetyState.EMERGENCY_STOP
            return

        critical_alerts = [a for a in self.safety_alerts if a.level == SafetyLevel.CRITICAL]
        warning_alerts = [a for a in self.safety_alerts if a.level == SafetyLevel.WARNING]

        if critical_alerts:
            self.current_state = SafetyState.UNSAFE
        elif len(warning_alerts) > 3:  # Multiple warnings
            self.current_state = SafetyState.CAUTION
        elif warning_alerts:
            self.current_state = SafetyState.CAUTION
        else:
            self.current_state = SafetyState.SAFE

    def _trigger_emergency(self, emergency_type: EmergencyType, description: str):
        """Trigger emergency stop and safety protocols"""
        if self.emergency_active:
            return  # Already in emergency state

        logger.critical(f"🚨 EMERGENCY TRIGGERED: {emergency_type.value} - {description}")

        self.emergency_active = True
        self.current_state = SafetyState.EMERGENCY_STOP

        # Create emergency alert
        alert = SafetyAlert(
            timestamp=time.time(),
            alert_type=emergency_type,
            level=SafetyLevel.EMERGENCY,
            description=description,
            affected_systems=["all"]
        )
        self.safety_alerts.append(alert)

        # Execute emergency stop
        self._execute_emergency_stop()

        # Execute specific emergency actions
        actions = self.safety_profile.emergency_actions.get(emergency_type.value, [])
        for action in actions:
            self._execute_emergency_action(action, emergency_type, description)

        # Notify callbacks
        for callback in self.emergency_callbacks:
            try:
                callback(emergency_type, description)
            except Exception as e:
                logger.error(f"Emergency callback failed: {e}")

    def _execute_emergency_stop(self):
        """Execute immediate emergency stop"""
        try:
            # Stop all servo movement
            if self.servo_system and hasattr(self.servo_system, 'emergency_stop'):
                self.servo_system.emergency_stop()

            # Stop all active sequences
            if hasattr(self.servo_system, 'script_engine') and self.servo_system.script_engine:
                self.servo_system.script_engine.stop_execution()

            # Stop behavior engine
            if hasattr(self.servo_system, 'behavior_engine') and self.servo_system.behavior_engine:
                self.servo_system.behavior_engine.behavior_active = False

            logger.info("✅ Emergency stop executed successfully")

        except Exception as e:
            logger.critical(f"Emergency stop execution failed: {e}")

    def _execute_emergency_action(self, action: str, emergency_type: EmergencyType, description: str):
        """Execute specific emergency action"""
        try:
            if action == "emergency_stop":
                self._execute_emergency_stop()

            elif action == "log_incident":
                self._log_safety_incident(emergency_type, description)

            elif action == "notify_maintenance":
                self._notify_maintenance(emergency_type, description)

            elif action == "safe_shutdown":
                self._initiate_safe_shutdown()

            elif action == "retract_to_safe":
                self._retract_to_safe_positions()

            elif action == "disable_affected_servo":
                self._disable_affected_servos(emergency_type)

            else:
                logger.warning(f"Unknown emergency action: {action}")

        except Exception as e:
            logger.error(f"Emergency action '{action}' failed: {e}")

    def _create_safety_alert(self, alert_type: EmergencyType, level: SafetyLevel,
                           description: str, affected_systems: List[str]):
        """Create a safety alert"""
        # Check for duplicate alerts
        for alert in self.safety_alerts:
            if (alert.alert_type == alert_type and
                alert.description == description and
                not alert.auto_resolved):
                return  # Don't create duplicate

        alert = SafetyAlert(
            timestamp=time.time(),
            alert_type=alert_type,
            level=level,
            description=description,
            affected_systems=affected_systems
        )

        self.safety_alerts.append(alert)

        # Log the alert
        log_level = {
            SafetyLevel.NORMAL: logging.INFO,
            SafetyLevel.CAUTION: logging.WARNING,
            SafetyLevel.WARNING: logging.WARNING,
            SafetyLevel.CRITICAL: logging.CRITICAL,
            SafetyLevel.EMERGENCY: logging.CRITICAL
        }.get(level, logging.INFO)

        logger.log(log_level, f"🛡️ Safety Alert ({level.value}): {description}")

    def _cleanup_old_alerts(self):
        """Clean up old resolved alerts"""
        current_time = time.time()
        alert_retention = 3600.0  # 1 hour

        # Remove old alerts that are auto-resolved
        self.safety_alerts = [
            alert for alert in self.safety_alerts
            if not (alert.auto_resolved and current_time - alert.timestamp > alert_retention)
        ]

    def _log_safety_incident(self, emergency_type: EmergencyType, description: str):
        """Log safety incident to permanent record"""
        incident = {
            "timestamp": time.time(),
            "type": emergency_type.value,
            "description": description,
            "system_state": self.current_state.value,
            "active_alerts": len(self.safety_alerts)
        }
        self.safety_log.append(incident)

        # Save to file
        try:
            log_file = Path("/home/rolo/r2ai/logs/safety_incidents.json")
            log_file.parent.mkdir(parents=True, exist_ok=True)

            incidents = []
            if log_file.exists():
                with open(log_file, 'r') as f:
                    incidents = json.load(f)

            incidents.append(incident)

            # Keep only last 1000 incidents
            if len(incidents) > 1000:
                incidents = incidents[-1000:]

            with open(log_file, 'w') as f:
                json.dump(incidents, f, indent=2)

        except Exception as e:
            logger.error(f"Failed to log safety incident: {e}")

    def _notify_maintenance(self, emergency_type: EmergencyType, description: str):
        """Notify maintenance system of critical issues"""
        logger.info(f"🔧 Maintenance notification: {emergency_type.value} - {description}")
        # In real implementation, would send notifications to maintenance team

    def _initiate_safe_shutdown(self):
        """Initiate safe system shutdown"""
        logger.info("🔄 Initiating safe shutdown...")
        # Implementation would safely shut down all systems

    def _retract_to_safe_positions(self):
        """Retract all servos to safe positions"""
        logger.info("🏠 Retracting to safe positions...")
        # Implementation would move all servos to safe positions

    def _disable_affected_servos(self, emergency_type: EmergencyType):
        """Disable servos affected by emergency"""
        logger.info(f"⚠️ Disabling affected servos for {emergency_type.value}")
        # Implementation would disable specific servos

    def _setup_signal_handlers(self):
        """Setup signal handlers for emergency stops"""
        def emergency_stop_handler(signum, frame):
            logger.critical("🚨 Emergency stop signal received")
            self._trigger_emergency(EmergencyType.MANUAL_STOP, "Manual emergency stop signal")

        # Setup Ctrl+C and other emergency signals
        signal.signal(signal.SIGINT, emergency_stop_handler)
        signal.signal(signal.SIGTERM, emergency_stop_handler)

    def _load_safety_configuration(self):
        """Load safety configuration from file"""
        try:
            if self.config_path.exists():
                with open(self.config_path, 'r') as f:
                    config = json.load(f)

                # Load safety limits
                if "safety_limits" in config:
                    limits_data = config["safety_limits"]
                    self.safety_limits = SafetyLimits(**limits_data)

                logger.info(f"✅ Safety configuration loaded from {self.config_path}")

        except Exception as e:
            logger.error(f"Failed to load safety configuration: {e}")

    # Public API Methods

    def manual_emergency_stop(self):
        """Manually trigger emergency stop"""
        self._trigger_emergency(EmergencyType.MANUAL_STOP, "Manual emergency stop activated")

    def reset_emergency(self, user_confirmation: bool = False) -> bool:
        """Reset emergency state after resolving issues"""
        if not user_confirmation:
            logger.warning("Emergency reset requires user confirmation")
            return False

        if not self.emergency_active:
            logger.info("No emergency state to reset")
            return True

        # Check if it's safe to reset
        critical_alerts = [a for a in self.safety_alerts if a.level == SafetyLevel.CRITICAL]
        if critical_alerts:
            logger.error("Cannot reset emergency - critical alerts still active")
            return False

        logger.info("🔄 Resetting emergency state...")
        self.emergency_active = False
        self.current_state = SafetyState.SAFE

        # Clear emergency alerts
        self.safety_alerts = [a for a in self.safety_alerts if a.level != SafetyLevel.EMERGENCY]

        # Resume servo operations
        if self.servo_system and hasattr(self.servo_system, 'resume_operation'):
            self.servo_system.resume_operation()

        logger.info("✅ Emergency state reset complete")
        return True

    def get_safety_status(self) -> Dict:
        """Get current safety status"""
        return {
            "current_state": self.current_state.value,
            "emergency_active": self.emergency_active,
            "active_alerts": len(self.safety_alerts),
            "critical_alerts": len([a for a in self.safety_alerts if a.level == SafetyLevel.CRITICAL]),
            "communication_ok": self.communication_ok,
            "system_health_ok": self.system_health_ok,
            "safety_profile": self.safety_profile.name,
            "enabled_protocols": list(self.safety_profile.enabled_protocols)
        }

    def get_active_alerts(self) -> List[SafetyAlert]:
        """Get current active safety alerts"""
        return [alert for alert in self.safety_alerts if not alert.auto_resolved]

    def acknowledge_alert(self, alert_index: int) -> bool:
        """Acknowledge a safety alert"""
        if 0 <= alert_index < len(self.safety_alerts):
            self.safety_alerts[alert_index].user_acknowledged = True
            logger.info(f"Alert {alert_index} acknowledged by user")
            return True
        return False

    def add_emergency_callback(self, callback: Callable):
        """Add callback for emergency notifications"""
        self.emergency_callbacks.append(callback)

    def save_safety_configuration(self):
        """Save current safety configuration"""
        try:
            config = {
                "safety_profile": asdict(self.safety_profile),
                "safety_limits": asdict(self.safety_limits)
            }

            with open(self.config_path, 'w') as f:
                json.dump(config, f, indent=2)

            logger.info(f"✅ Safety configuration saved to {self.config_path}")

        except Exception as e:
            logger.error(f"Failed to save safety configuration: {e}")

    def shutdown(self):
        """Shutdown safety system"""
        logger.info("🔄 Shutting down safety system...")

        self.safety_active = False

        # Wait for threads to finish
        if self.monitoring_thread and self.monitoring_thread.is_alive():
            self.monitoring_thread.join(timeout=2.0)

        if self.watchdog_thread and self.watchdog_thread.is_alive():
            self.watchdog_thread.join(timeout=2.0)

        # Save final safety log
        self.save_safety_configuration()

        logger.info("✅ Safety system shutdown complete")

# Demo function
def demo_safety_system():
    """Demo the safety system"""
    logger.info("🛡️ Starting Safety System Demo...")

    # Mock servo and monitoring systems
    class MockServoSystem:
        def emergency_stop(self):
            logger.info("[MOCK] Emergency stop executed")

        def resume_operation(self):
            logger.info("[MOCK] Operations resumed")

    class MockMonitoringSystem:
        def get_current_metrics(self):
            # Return mock metrics with some alerts
            return {
                0: type('MockMetric', (), {
                    'temperature': 75.0,  # High temperature
                    'position_error': 250,  # High position error
                    'speed': 1500.0,
                    'current': 0.8,
                    'voltage': 6.0,
                    'position': 6000
                })(),
                1: type('MockMetric', (), {
                    'temperature': 40.0,
                    'position_error': 20,
                    'speed': 500.0,
                    'current': 0.3,
                    'voltage': 6.0,
                    'position': 5000
                })()
            }

    servo_system = MockServoSystem()
    monitoring_system = MockMonitoringSystem()
    safety_system = SafetySystem(servo_system, monitoring_system)

    try:
        # Let safety system run and detect issues
        logger.info("Running safety checks...")
        time.sleep(3)

        # Display safety status
        status = safety_system.get_safety_status()
        logger.info(f"\n🛡️ Safety Status:")
        logger.info(f"  State: {status['current_state']}")
        logger.info(f"  Emergency Active: {status['emergency_active']}")
        logger.info(f"  Active Alerts: {status['active_alerts']}")
        logger.info(f"  Critical Alerts: {status['critical_alerts']}")

        # Display active alerts
        alerts = safety_system.get_active_alerts()
        logger.info(f"\n🚨 Active Alerts ({len(alerts)}):")
        for i, alert in enumerate(alerts[:5]):  # Show first 5
            logger.info(f"  {i}: {alert.level.value} - {alert.description}")

        # Test manual emergency stop
        logger.info("\n🚨 Testing manual emergency stop...")
        safety_system.manual_emergency_stop()
        time.sleep(1)

        # Check status after emergency
        status = safety_system.get_safety_status()
        logger.info(f"Emergency Active: {status['emergency_active']}")

        # Test emergency reset
        logger.info("\n🔄 Testing emergency reset...")
        reset_success = safety_system.reset_emergency(user_confirmation=True)
        logger.info(f"Emergency reset successful: {reset_success}")

        logger.info("\n✅ Safety system demo completed!")

    except KeyboardInterrupt:
        logger.info("Demo interrupted")
    except Exception as e:
        logger.error(f"Demo failed: {e}")
    finally:
        safety_system.shutdown()

if __name__ == "__main__":
    demo_safety_system()