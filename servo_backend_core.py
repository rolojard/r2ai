#!/usr/bin/env python3
"""
R2D2 Servo Backend Core
Modularized core backend service for servo control

This module provides the main backend service orchestration, reduced from
the original 1,875-line monolithic backend by leveraging shared modules.
"""

import asyncio
import time
import logging
from typing import Dict, List, Optional, Any, Callable
from servo_base_classes import (
    ServoControllerBase,
    ConnectionStatus,
    SystemHealthStatus,
    ServoCommand,
    ServoSequence,
    PerformanceMetrics
)
from servo_websocket_module import ServoWebSocketHandler, StandardServoMessageHandlers
from servo_safety_module import ServoSafetySystem
from servo_config_module import ServoConfigurationManager

# Import existing controllers for compatibility
try:
    from maestro_enhanced_controller import EnhancedMaestroController
    from pololu_maestro_controller import PololuMaestroController
    MAESTRO_AVAILABLE = True
except ImportError:
    MAESTRO_AVAILABLE = False
    logger.warning("Maestro controllers not available")

logger = logging.getLogger(__name__)

class ServoBackendCore:
    """Core servo backend service with modular architecture"""

    def __init__(self, maestro_port=None, simulation_mode=False, auto_detect=True):
        """Initialize servo backend with modular components"""

        # Initialize core components using shared modules
        self.config_manager = ServoConfigurationManager()
        self.safety_system = ServoSafetySystem()
        self.websocket_handler = ServoWebSocketHandler()

        # Initialize servo controller
        if MAESTRO_AVAILABLE and not simulation_mode:
            if auto_detect:
                self.controller = EnhancedMaestroController(auto_detect=True)
            else:
                self.controller = EnhancedMaestroController(auto_detect=False)
        else:
            self.controller = SimulatedServoController()

        # Initialize message handlers
        self.message_handlers = StandardServoMessageHandlers(
            self.controller,
            self.safety_system,
            self,  # sequence engine
            self.config_manager
        )

        # Register WebSocket message handlers
        self._register_websocket_handlers()

        # Service state
        self.running = False
        self.start_time = time.time()
        self.connection_status = ConnectionStatus.DISCONNECTED
        self.health_status = SystemHealthStatus.GOOD
        self.performance_metrics = PerformanceMetrics(0, 0, 0, 0, 0, 0, 0.0)

        # Auto-reconnection settings
        self.auto_reconnect_enabled = True
        self.reconnect_interval = 10.0
        self.max_reconnect_attempts = 10
        self.reconnect_attempts = 0

        # Sequence management
        self.active_sequences: Dict[str, ServoSequence] = {}
        self.sequence_callbacks: List[Callable] = []

        # Setup safety system
        self.safety_system.initialize_safety_configs(self.config_manager.get_all_configs())
        self.safety_system.add_safety_callback(self._handle_safety_violation)

        # Initialize detected hardware
        if auto_detect and not simulation_mode:
            self._initialize_hardware()

        logger.info("Servo Backend Core initialized with modular architecture")

    def _register_websocket_handlers(self):
        """Register WebSocket message handlers"""
        self.websocket_handler.register_message_handler(
            'servo_command', self.message_handlers.handle_servo_command
        )
        self.websocket_handler.register_message_handler(
            'sequence_command', self.message_handlers.handle_sequence_command
        )
        self.websocket_handler.register_message_handler(
            'config_command', self.message_handlers.handle_config_command
        )
        self.websocket_handler.register_message_handler(
            'emergency_stop', self.message_handlers.handle_emergency_stop
        )

        # Add status callback
        self.websocket_handler.add_status_callback(self._get_system_status)

    def _initialize_hardware(self):
        """Initialize hardware configuration"""
        try:
            if hasattr(self.controller, 'connect'):
                success = self.controller.connect()
                if success:
                    self.connection_status = ConnectionStatus.CONNECTED
                    logger.info("Connected to servo hardware")
                else:
                    self.connection_status = ConnectionStatus.ERROR
                    logger.error("Failed to connect to servo hardware")
            else:
                self.connection_status = ConnectionStatus.DISCONNECTED

        except Exception as e:
            logger.error(f"Hardware initialization failed: {e}")
            self.connection_status = ConnectionStatus.ERROR

    async def start_services(self, websocket_port=8767):
        """Start all backend services"""
        logger.info("🚀 Starting R2D2 Servo Backend Services...")
        self.running = True

        try:
            # Start safety monitoring
            self.safety_system.start_monitoring()

            # Start WebSocket server
            await self.websocket_handler.start_server()

            # Start background tasks
            asyncio.create_task(self._health_monitoring_loop())
            asyncio.create_task(self._reconnection_loop())

            logger.info(f"✅ Servo backend services started on port {websocket_port}")
            return True

        except Exception as e:
            logger.error(f"Failed to start services: {e}")
            await self.stop_services()
            return False

    async def stop_services(self):
        """Stop all backend services"""
        logger.info("🛑 Stopping R2D2 Servo Backend Services...")
        self.running = False

        try:
            # Stop safety monitoring
            self.safety_system.stop_monitoring()

            # Stop WebSocket server
            await self.websocket_handler.stop_server()

            # Disconnect hardware
            if hasattr(self.controller, 'disconnect'):
                self.controller.disconnect()

            logger.info("✅ Servo backend services stopped")

        except Exception as e:
            logger.error(f"Error stopping services: {e}")

    async def execute_sequence(self, sequence: ServoSequence) -> bool:
        """Execute a servo sequence"""
        try:
            self.active_sequences[sequence.id] = sequence
            logger.info(f"Starting sequence: {sequence.name}")

            # Validate all commands in sequence
            for command in sequence.commands:
                if not self.safety_system.validate_command(command):
                    logger.error(f"Sequence {sequence.name} failed safety validation")
                    return False

            # Execute sequence commands
            for command in sequence.commands:
                if not self.running or sequence.id not in self.active_sequences:
                    break

                # Apply delay
                if command.delay > 0:
                    await asyncio.sleep(command.delay)

                # Execute command
                if command.command_type.value == 'position':
                    success = self.controller.move_servo(
                        command.channel,
                        int(command.value),
                        command.duration
                    )
                    if not success:
                        logger.error(f"Failed to execute command in sequence {sequence.name}")
                        break

                # Update performance metrics
                self._update_performance_metrics(command)

            # Handle looping
            if sequence.loop and sequence.id in self.active_sequences:
                if sequence.loop_count > 1:
                    sequence.loop_count -= 1
                    await self.execute_sequence(sequence)
                elif sequence.loop_count == -1:  # Infinite loop
                    await self.execute_sequence(sequence)

            # Clean up
            self.active_sequences.pop(sequence.id, None)
            logger.info(f"Sequence completed: {sequence.name}")
            return True

        except Exception as e:
            logger.error(f"Sequence execution error: {e}")
            self.active_sequences.pop(sequence.id, None)
            return False

    def stop_sequence(self, sequence_id: str) -> bool:
        """Stop a running sequence"""
        if sequence_id in self.active_sequences:
            self.active_sequences.pop(sequence_id)
            logger.info(f"Stopped sequence: {sequence_id}")
            return True
        return False

    def get_sequence_status(self, sequence_id: str) -> Dict[str, Any]:
        """Get status of a sequence"""
        if sequence_id in self.active_sequences:
            sequence = self.active_sequences[sequence_id]
            return {
                'id': sequence.id,
                'name': sequence.name,
                'status': 'running',
                'duration': sequence.duration,
                'commands': len(sequence.commands),
                'loop': sequence.loop,
                'loop_count': sequence.loop_count
            }
        return {'id': sequence_id, 'status': 'not_found'}

    def emergency_stop(self) -> bool:
        """Emergency stop all servos"""
        try:
            self.safety_system.trigger_emergency_stop()

            # Stop all sequences
            self.active_sequences.clear()

            # Emergency stop hardware
            if hasattr(self.controller, 'emergency_stop'):
                self.controller.emergency_stop()

            logger.critical("EMERGENCY STOP ACTIVATED")
            return True

        except Exception as e:
            logger.error(f"Emergency stop failed: {e}")
            return False

    def _handle_safety_violation(self, violation):
        """Handle safety violations"""
        logger.warning(f"Safety violation: {violation.description}")

        # Update health status
        if violation.severity == "critical":
            self.health_status = SystemHealthStatus.CRITICAL
        elif violation.severity == "warning" and self.health_status == SystemHealthStatus.GOOD:
            self.health_status = SystemHealthStatus.WARNING

    def _update_performance_metrics(self, command: ServoCommand):
        """Update performance metrics"""
        try:
            # Calculate command latency
            latency = (time.time() - command.timestamp) * 1000  # ms

            # Update metrics
            self.performance_metrics.command_latency_ms = latency
            self.performance_metrics.total_commands_processed += 1

            # Calculate success rate (simplified)
            if latency < 100:  # Under 100ms is considered successful
                success_count = int(self.performance_metrics.success_rate *
                                  self.performance_metrics.total_commands_processed)
                success_count += 1
                self.performance_metrics.success_rate = (
                    success_count / self.performance_metrics.total_commands_processed
                )

        except Exception as e:
            logger.error(f"Performance metrics update error: {e}")

    async def _get_system_status(self) -> Dict[str, Any]:
        """Get comprehensive system status"""
        return {
            'backend_status': {
                'running': self.running,
                'uptime': time.time() - self.start_time,
                'connection_status': self.connection_status.value,
                'health_status': self.health_status.value
            },
            'servo_status': {
                'total_servos': len(self.config_manager.get_all_configs()),
                'active_sequences': len(self.active_sequences),
                'emergency_stop': self.safety_system.emergency_stop_active
            },
            'performance': {
                'command_latency_ms': self.performance_metrics.command_latency_ms,
                'success_rate': self.performance_metrics.success_rate,
                'total_commands': self.performance_metrics.total_commands_processed
            },
            'safety': self.safety_system.get_safety_status()
        }

    async def _health_monitoring_loop(self):
        """Background health monitoring"""
        while self.running:
            try:
                # Update health status
                if self.connection_status == ConnectionStatus.CONNECTED:
                    if self.safety_system.emergency_stop_active:
                        self.health_status = SystemHealthStatus.CRITICAL
                    elif len(self.safety_system.violations) > 0:
                        self.health_status = SystemHealthStatus.WARNING
                    else:
                        self.health_status = SystemHealthStatus.GOOD
                else:
                    self.health_status = SystemHealthStatus.FAILED

                await asyncio.sleep(1)

            except Exception as e:
                logger.error(f"Health monitoring error: {e}")
                await asyncio.sleep(5)

    async def _reconnection_loop(self):
        """Background reconnection attempts"""
        while self.running:
            try:
                if (self.auto_reconnect_enabled and
                    self.connection_status == ConnectionStatus.ERROR and
                    self.reconnect_attempts < self.max_reconnect_attempts):

                    logger.info(f"Attempting reconnection ({self.reconnect_attempts + 1}/{self.max_reconnect_attempts})")

                    if hasattr(self.controller, 'connect'):
                        if self.controller.connect():
                            self.connection_status = ConnectionStatus.CONNECTED
                            self.reconnect_attempts = 0
                            logger.info("Reconnection successful")
                        else:
                            self.reconnect_attempts += 1

                await asyncio.sleep(self.reconnect_interval)

            except Exception as e:
                logger.error(f"Reconnection error: {e}")
                await asyncio.sleep(self.reconnect_interval)

class SimulatedServoController(ServoControllerBase):
    """Simulated servo controller for testing without hardware"""

    def __init__(self):
        super().__init__("SimulatedController")
        self.servo_positions: Dict[int, int] = {}

    def connect(self) -> bool:
        self.is_connected = True
        logger.info("Connected to simulated servo hardware")
        return True

    def disconnect(self) -> bool:
        self.is_connected = False
        logger.info("Disconnected from simulated servo hardware")
        return True

    def move_servo(self, channel: int, position: int, duration: float = 0) -> bool:
        if not self.is_connected:
            return False

        self.servo_positions[channel] = position
        logger.debug(f"Simulated servo {channel} moved to position {position}")
        return True

    def get_servo_status(self, channel: int) -> Dict[str, Any]:
        return {
            'channel': channel,
            'position': self.servo_positions.get(channel, 1500),
            'connected': self.is_connected,
            'moving': False
        }

    def emergency_stop(self) -> bool:
        logger.info("Emergency stop - simulated servos stopped")
        return True