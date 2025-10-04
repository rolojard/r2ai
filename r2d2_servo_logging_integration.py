#!/usr/bin/env python3
"""
R2D2 Servo System Logging Integration
====================================

Comprehensive logging enhancement for servo control systems.
Provides structured logging for servo commands, position tracking,
error states, and performance monitoring.

Features:
- Servo command logging with timing
- Position tracking and validation
- Error state detection and recovery
- Performance metrics and analysis
- Safety system event logging
- Integration with existing servo API

Author: Expert Python Coder Agent
"""

import os
import sys
import time
import json
import logging
import threading
import functools
from typing import Dict, List, Any, Optional, Callable, Union
from datetime import datetime
from dataclasses import dataclass

# Import our logging framework
sys.path.append('/home/rolo/r2ai')
from r2d2_logging_framework import R2D2LoggerFactory

@dataclass
class ServoCommand:
    """Data class for servo command tracking"""
    channel: int
    position: int
    timestamp: float
    command_id: str
    target_position: Optional[int] = None
    duration: Optional[float] = None
    priority: str = "normal"

@dataclass
class ServoStatus:
    """Data class for servo status tracking"""
    channel: int
    current_position: int
    target_position: int
    is_moving: bool
    last_update: float
    error_state: bool = False
    error_message: str = ""

class ServoLoggingEnhancer:
    """
    Comprehensive logging enhancer for servo control systems
    """

    def __init__(self, service_name: str = "servo_system"):
        """Initialize the servo logging enhancer"""
        self.service_name = service_name
        self.enabled = True

        # Create logging components
        self.logging_components = R2D2LoggerFactory.create_service_logger(
            service_name,
            enable_performance_monitoring=True,
            enable_websocket_logging=False,  # Servo doesn't use WebSocket
            enable_vision_logging=False     # Not needed for servo
        )

        self.logger = self.logging_components["logger"]
        self.perf_logger = self.logging_components["performance_logger"]

        # Servo-specific tracking
        self.servo_states = {}  # channel -> ServoStatus
        self.command_history = []  # List of ServoCommand
        self.max_history = 1000
        self.active_sequences = {}  # sequence_id -> sequence_info
        self.safety_events = []  # Safety-related events
        self.performance_metrics = {
            "commands_sent": 0,
            "commands_successful": 0,
            "commands_failed": 0,
            "average_response_time": 0.0,
            "total_response_time": 0.0,
            "emergency_stops": 0,
            "safety_violations": 0
        }

        # Command response time tracking
        self.pending_commands = {}  # command_id -> start_time
        self.response_times = []
        self.max_response_times = 100

        self.logger.info("Servo logging enhancer initialized", extra={
            "event_type": "servo_enhancer_initialized",
            "service": service_name
        })

    def log_servo_command(self, channel: int, position: int, duration: Optional[float] = None,
                         command_type: str = "position", priority: str = "normal") -> str:
        """
        Log a servo command with comprehensive tracking

        Args:
            channel: Servo channel number
            position: Target position in microseconds
            duration: Expected duration in seconds
            command_type: Type of command (position, speed, etc.)
            priority: Command priority level

        Returns:
            command_id: Unique identifier for this command
        """
        command_id = f"cmd_{int(time.time() * 1000)}_{channel}"
        timestamp = time.time()

        command = ServoCommand(
            channel=channel,
            position=position,
            timestamp=timestamp,
            command_id=command_id,
            target_position=position,
            duration=duration,
            priority=priority
        )

        # Add to history
        self.command_history.append(command)
        if len(self.command_history) > self.max_history:
            self.command_history.pop(0)

        # Track pending command
        self.pending_commands[command_id] = timestamp

        # Update metrics
        self.performance_metrics["commands_sent"] += 1

        # Log the command
        self.logger.info(f"Servo command issued: Channel {channel} -> {position}µs", extra={
            "event_type": "servo_command",
            "command_id": command_id,
            "channel": channel,
            "position": position,
            "command_type": command_type,
            "priority": priority,
            "duration": duration,
            "total_commands": self.performance_metrics["commands_sent"]
        })

        return command_id

    def log_servo_response(self, command_id: str, success: bool, actual_position: Optional[int] = None,
                          error_message: Optional[str] = None):
        """
        Log the response to a servo command

        Args:
            command_id: The command identifier
            success: Whether the command was successful
            actual_position: The actual position reached
            error_message: Error message if command failed
        """
        if command_id in self.pending_commands:
            start_time = self.pending_commands.pop(command_id)
            response_time = time.time() - start_time

            # Track response times
            self.response_times.append(response_time)
            if len(self.response_times) > self.max_response_times:
                self.response_times.pop(0)

            # Update metrics
            self.performance_metrics["total_response_time"] += response_time
            if success:
                self.performance_metrics["commands_successful"] += 1
            else:
                self.performance_metrics["commands_failed"] += 1

            # Calculate average response time
            if self.response_times:
                self.performance_metrics["average_response_time"] = sum(self.response_times) / len(self.response_times)

            # Log the response
            log_level = logging.INFO if success else logging.ERROR
            message = f"Servo command {'completed' if success else 'failed'}: {command_id}"

            extra_data = {
                "event_type": "servo_response",
                "command_id": command_id,
                "success": success,
                "response_time_seconds": round(response_time, 4),
                "average_response_time": round(self.performance_metrics["average_response_time"], 4),
                "success_rate": round(
                    self.performance_metrics["commands_successful"] /
                    max(1, self.performance_metrics["commands_sent"]) * 100, 2
                )
            }

            if actual_position is not None:
                extra_data["actual_position"] = actual_position

            if error_message:
                extra_data["error_message"] = error_message

            self.logger.log(log_level, message, extra=extra_data)

        else:
            self.logger.warning(f"Received response for unknown command: {command_id}", extra={
                "event_type": "unknown_command_response",
                "command_id": command_id
            })

    def log_servo_status_update(self, channel: int, current_position: int, target_position: int,
                               is_moving: bool, error_state: bool = False, error_message: str = ""):
        """
        Log servo status update

        Args:
            channel: Servo channel
            current_position: Current position in microseconds
            target_position: Target position in microseconds
            is_moving: Whether servo is currently moving
            error_state: Whether servo is in error state
            error_message: Error description if in error state
        """
        timestamp = time.time()

        # Update servo state
        self.servo_states[channel] = ServoStatus(
            channel=channel,
            current_position=current_position,
            target_position=target_position,
            is_moving=is_moving,
            last_update=timestamp,
            error_state=error_state,
            error_message=error_message
        )

        # Log status update
        log_level = logging.ERROR if error_state else logging.DEBUG
        message = f"Servo {channel} status: {current_position}µs"

        if error_state:
            message += f" (ERROR: {error_message})"
        elif is_moving:
            message += f" (moving to {target_position}µs)"

        extra_data = {
            "event_type": "servo_status_update",
            "channel": channel,
            "current_position": current_position,
            "target_position": target_position,
            "is_moving": is_moving,
            "error_state": error_state,
            "position_error": abs(current_position - target_position)
        }

        if error_message:
            extra_data["error_message"] = error_message

        self.logger.log(log_level, message, extra=extra_data)

    def log_sequence_execution(self, sequence_id: str, sequence_name: str, keyframes: List[Dict],
                              action: str = "start"):
        """
        Log servo sequence execution

        Args:
            sequence_id: Unique sequence identifier
            sequence_name: Human-readable sequence name
            keyframes: List of keyframe data
            action: start, progress, complete, error
        """
        timestamp = time.time()

        if action == "start":
            self.active_sequences[sequence_id] = {
                "name": sequence_name,
                "keyframes": keyframes,
                "start_time": timestamp,
                "total_keyframes": len(keyframes),
                "completed_keyframes": 0
            }

            self.logger.info(f"Servo sequence started: {sequence_name}", extra={
                "event_type": "sequence_start",
                "sequence_id": sequence_id,
                "sequence_name": sequence_name,
                "total_keyframes": len(keyframes),
                "keyframes": keyframes
            })

        elif action == "progress" and sequence_id in self.active_sequences:
            sequence_info = self.active_sequences[sequence_id]
            sequence_info["completed_keyframes"] += 1
            progress = (sequence_info["completed_keyframes"] / sequence_info["total_keyframes"]) * 100

            self.logger.debug(f"Sequence progress: {sequence_name} ({progress:.1f}%)", extra={
                "event_type": "sequence_progress",
                "sequence_id": sequence_id,
                "sequence_name": sequence_name,
                "progress_percent": round(progress, 1),
                "completed_keyframes": sequence_info["completed_keyframes"],
                "total_keyframes": sequence_info["total_keyframes"]
            })

        elif action == "complete" and sequence_id in self.active_sequences:
            sequence_info = self.active_sequences.pop(sequence_id)
            duration = timestamp - sequence_info["start_time"]

            self.logger.info(f"Servo sequence completed: {sequence_name}", extra={
                "event_type": "sequence_complete",
                "sequence_id": sequence_id,
                "sequence_name": sequence_name,
                "duration_seconds": round(duration, 2),
                "total_keyframes": sequence_info["total_keyframes"]
            })

        elif action == "error":
            if sequence_id in self.active_sequences:
                sequence_info = self.active_sequences.pop(sequence_id)
                duration = timestamp - sequence_info["start_time"]
            else:
                duration = 0

            self.logger.error(f"Servo sequence failed: {sequence_name}", extra={
                "event_type": "sequence_error",
                "sequence_id": sequence_id,
                "sequence_name": sequence_name,
                "duration_seconds": round(duration, 2)
            })

    def log_safety_event(self, event_type: str, description: str, affected_channels: List[int] = None,
                        severity: str = "warning"):
        """
        Log safety-related events

        Args:
            event_type: Type of safety event (emergency_stop, position_limit, etc.)
            description: Detailed description of the event
            affected_channels: List of affected servo channels
            severity: Event severity (info, warning, error, critical)
        """
        timestamp = time.time()

        safety_event = {
            "timestamp": timestamp,
            "event_type": event_type,
            "description": description,
            "affected_channels": affected_channels or [],
            "severity": severity
        }

        self.safety_events.append(safety_event)
        if len(self.safety_events) > 100:  # Keep last 100 safety events
            self.safety_events.pop(0)

        # Update metrics
        if event_type == "emergency_stop":
            self.performance_metrics["emergency_stops"] += 1
        elif severity in ["error", "critical"]:
            self.performance_metrics["safety_violations"] += 1

        # Log the safety event
        log_level = getattr(logging, severity.upper(), logging.WARNING)
        message = f"Safety event - {event_type}: {description}"

        extra_data = {
            "event_type": "safety_event",
            "safety_event_type": event_type,
            "description": description,
            "severity": severity,
            "affected_channels": affected_channels or [],
            "total_emergency_stops": self.performance_metrics["emergency_stops"],
            "total_safety_violations": self.performance_metrics["safety_violations"]
        }

        self.logger.log(log_level, message, extra=extra_data)

    def log_calibration_event(self, channel: int, action: str, min_position: Optional[int] = None,
                            max_position: Optional[int] = None, home_position: Optional[int] = None):
        """
        Log servo calibration events

        Args:
            channel: Servo channel being calibrated
            action: Calibration action (start, complete, failed)
            min_position: Minimum position limit
            max_position: Maximum position limit
            home_position: Home position
        """
        extra_data = {
            "event_type": "servo_calibration",
            "channel": channel,
            "calibration_action": action
        }

        if min_position is not None:
            extra_data["min_position"] = min_position
        if max_position is not None:
            extra_data["max_position"] = max_position
        if home_position is not None:
            extra_data["home_position"] = home_position

        log_level = logging.INFO if action != "failed" else logging.ERROR
        message = f"Servo {channel} calibration {action}"

        self.logger.log(log_level, message, extra=extra_data)

    def create_performance_decorator(self):
        """
        Create a decorator for servo method performance monitoring
        """
        def servo_performance_decorator(func):
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                operation_name = f"servo_{func.__name__}"

                try:
                    with self.perf_logger.measure_operation(operation_name, **kwargs):
                        result = func(*args, **kwargs)
                    return result
                except Exception as e:
                    self.logger.error(f"Servo operation failed: {func.__name__}", exc_info=True, extra={
                        "event_type": "servo_operation_error",
                        "operation": func.__name__,
                        "error_message": str(e),
                        "args": str(args),
                        "kwargs": str(kwargs)
                    })
                    raise

            return wrapper
        return servo_performance_decorator

    def get_servo_performance_summary(self) -> Dict[str, Any]:
        """Get comprehensive servo performance summary"""
        current_time = time.time()
        active_servos = len(self.servo_states)
        moving_servos = sum(1 for status in self.servo_states.values() if status.is_moving)
        error_servos = sum(1 for status in self.servo_states.values() if status.error_state)

        summary = {
            "service": self.service_name,
            "timestamp": current_time,
            "servo_statistics": {
                "active_servos": active_servos,
                "moving_servos": moving_servos,
                "error_servos": error_servos,
                "total_commands": self.performance_metrics["commands_sent"],
                "successful_commands": self.performance_metrics["commands_successful"],
                "failed_commands": self.performance_metrics["commands_failed"],
                "success_rate_percent": round(
                    self.performance_metrics["commands_successful"] /
                    max(1, self.performance_metrics["commands_sent"]) * 100, 2
                ),
                "average_response_time_seconds": round(self.performance_metrics["average_response_time"], 4)
            },
            "safety_statistics": {
                "emergency_stops": self.performance_metrics["emergency_stops"],
                "safety_violations": self.performance_metrics["safety_violations"],
                "recent_safety_events": len([e for e in self.safety_events
                                           if current_time - e["timestamp"] < 3600])  # Last hour
            },
            "sequence_statistics": {
                "active_sequences": len(self.active_sequences),
                "recent_commands": len([c for c in self.command_history
                                      if current_time - c.timestamp < 300])  # Last 5 minutes
            }
        }

        return summary

    def get_servo_health_report(self) -> Dict[str, Any]:
        """Generate detailed servo health report"""
        health_report = {
            "timestamp": time.time(),
            "overall_health": "healthy",
            "servo_status": {},
            "warnings": [],
            "errors": []
        }

        overall_healthy = True

        for channel, status in self.servo_states.items():
            servo_health = {
                "channel": channel,
                "status": "healthy",
                "current_position": status.current_position,
                "target_position": status.target_position,
                "is_moving": status.is_moving,
                "last_update_age_seconds": round(time.time() - status.last_update, 2)
            }

            # Check for issues
            if status.error_state:
                servo_health["status"] = "error"
                servo_health["error_message"] = status.error_message
                health_report["errors"].append(f"Servo {channel}: {status.error_message}")
                overall_healthy = False

            elif status.last_update < time.time() - 30:  # No update in 30 seconds
                servo_health["status"] = "stale"
                health_report["warnings"].append(f"Servo {channel}: No recent status updates")

            elif status.is_moving and abs(status.current_position - status.target_position) > 100:
                # Large position error while moving
                health_report["warnings"].append(
                    f"Servo {channel}: Large position error while moving"
                )

            health_report["servo_status"][channel] = servo_health

        # Set overall health
        if health_report["errors"]:
            health_report["overall_health"] = "error"
        elif health_report["warnings"]:
            health_report["overall_health"] = "warning"

        return health_report

def create_servo_logging_wrapper():
    """
    Factory function to create a servo logging enhancer

    Usage:
        enhancer = create_servo_logging_wrapper()
        enhancer.log_servo_command(0, 1500)
    """
    return ServoLoggingEnhancer("servo_control_system")

# Enhanced servo API wrapper with logging
class LoggedServoAPI:
    """
    Wrapper around servo API that adds comprehensive logging
    """

    def __init__(self, original_api, enhancer: ServoLoggingEnhancer):
        self.api = original_api
        self.enhancer = enhancer
        self.logger = enhancer.logger

    def set_target(self, channel: int, target: int, duration: Optional[int] = None):
        """Set servo target with logging"""
        command_id = self.enhancer.log_servo_command(
            channel, target, duration/1000 if duration else None, "set_target"
        )

        try:
            result = self.api.set_target(channel, target, duration)
            self.enhancer.log_servo_response(command_id, True, target)
            return result
        except Exception as e:
            self.enhancer.log_servo_response(command_id, False, error_message=str(e))
            raise

    def get_position(self, channel: int) -> int:
        """Get servo position with logging"""
        try:
            with self.enhancer.perf_logger.measure_operation("get_position", channel=channel):
                position = self.api.get_position(channel)

            # Update servo status
            self.enhancer.log_servo_status_update(
                channel, position, position, False
            )

            return position
        except Exception as e:
            self.enhancer.log_safety_event(
                "position_read_error",
                f"Failed to read position for servo {channel}: {str(e)}",
                [channel],
                "error"
            )
            raise

    def emergency_stop(self):
        """Emergency stop with logging"""
        self.enhancer.log_safety_event(
            "emergency_stop",
            "Emergency stop activated",
            list(self.enhancer.servo_states.keys()),
            "critical"
        )

        try:
            result = self.api.emergency_stop()
            self.logger.info("Emergency stop executed successfully", extra={
                "event_type": "emergency_stop_success"
            })
            return result
        except Exception as e:
            self.logger.error("Emergency stop failed", exc_info=True, extra={
                "event_type": "emergency_stop_failed",
                "error_message": str(e)
            })
            raise

if __name__ == "__main__":
    print("🔧 R2D2 Servo Logging Integration")
    print("=" * 50)

    # Test the enhancer
    enhancer = create_servo_logging_wrapper()

    print("✅ Servo logging enhancer created")
    print(f"📁 Logs will be written to: /home/rolo/r2ai/logs/")

    # Simulate some servo operations
    print("\n🔄 Simulating servo operations...")

    # Test servo commands
    cmd1 = enhancer.log_servo_command(0, 1500, 2.0, "position", "high")
    time.sleep(0.1)
    enhancer.log_servo_response(cmd1, True, 1500)

    cmd2 = enhancer.log_servo_command(1, 2000, 1.5, "position", "normal")
    time.sleep(0.05)
    enhancer.log_servo_response(cmd2, False, error_message="Position out of range")

    # Test status updates
    enhancer.log_servo_status_update(0, 1500, 1500, False)
    enhancer.log_servo_status_update(1, 1200, 2000, True)

    # Test sequence execution
    sequence_id = "seq_001"
    keyframes = [
        {"channel": 0, "position": 1000, "duration": 1000},
        {"channel": 0, "position": 2000, "duration": 1000}
    ]
    enhancer.log_sequence_execution(sequence_id, "Test Sequence", keyframes, "start")
    enhancer.log_sequence_execution(sequence_id, "Test Sequence", keyframes, "progress")
    enhancer.log_sequence_execution(sequence_id, "Test Sequence", keyframes, "complete")

    # Test safety event
    enhancer.log_safety_event(
        "position_limit_exceeded",
        "Servo 2 exceeded maximum position limit",
        [2],
        "warning"
    )

    # Test calibration
    enhancer.log_calibration_event(3, "start")
    enhancer.log_calibration_event(3, "complete", 500, 2500, 1500)

    print("✅ Servo operations logged successfully")

    # Show performance summary
    print("\n📊 Performance Summary:")
    summary = enhancer.get_servo_performance_summary()
    for section, data in summary.items():
        if isinstance(data, dict):
            print(f"  {section}:")
            for key, value in data.items():
                print(f"    {key}: {value}")
        else:
            print(f"  {section}: {data}")

    # Show health report
    print("\n🏥 Health Report:")
    health = enhancer.get_servo_health_report()
    print(f"  Overall Health: {health['overall_health']}")
    print(f"  Active Servos: {len(health['servo_status'])}")
    print(f"  Warnings: {len(health['warnings'])}")
    print(f"  Errors: {len(health['errors'])}")

    print("\n✅ Servo logging integration module ready!")