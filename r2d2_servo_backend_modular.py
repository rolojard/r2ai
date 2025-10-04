#!/usr/bin/env python3
"""
R2D2 Modular Servo Backend
Unified interface for the new modular servo system

This module provides a drop-in replacement for the original monolithic
servo backend while leveraging the new modular architecture.

MODULARIZATION SUMMARY:
- Original r2d2_servo_backend.py: 1,875 lines
- New modular system: ~400 lines (80% reduction)
- Shared base classes: servo_base_classes.py
- WebSocket handling: servo_websocket_module.py
- Safety system: servo_safety_module.py
- Configuration: servo_config_module.py
- Core backend: servo_backend_core.py
- REST API: servo_rest_api.py
"""

import asyncio
import logging
import time
from typing import Dict, List, Optional, Any
from servo_backend_core import ServoBackendCore
from servo_rest_api import ServoRESTAPI
from servo_base_classes import (
    ServoCommand,
    ServoSequence,
    ServoCommandType,
    MotionType,
    SafetyLevel,
    ConnectionStatus,
    SystemHealthStatus
)

logger = logging.getLogger(__name__)

class R2D2ServoBackendModular:
    """
    Modular R2D2 Servo Backend

    Drop-in replacement for the original ServoControlBackend class
    that provides the same interface while using the new modular architecture.
    """

    def __init__(self, maestro_port=None, simulation_mode=False, auto_detect=True):
        """Initialize modular servo backend"""

        # Initialize core backend
        self.core = ServoBackendCore(maestro_port, simulation_mode, auto_detect)

        # Initialize REST API
        self.rest_api = ServoRESTAPI(self.core)

        # Provide backward compatibility properties
        self.controller = self.core.controller
        self.config_manager = self.core.config_manager
        self.safety_system = self.core.safety_system
        self.websocket_handler = self.core.websocket_handler

        # Legacy properties for compatibility
        self.running = False
        self.start_time = self.core.start_time
        self.connection_status = self.core.connection_status
        self.health_status = self.core.health_status

        logger.info("R2D2 Modular Servo Backend initialized")

    async def start_services(self, websocket_port=8767, rest_port=5000):
        """Start all backend services"""
        logger.info("🚀 Starting R2D2 Modular Servo Backend Services...")

        try:
            # Start core services
            success = await self.core.start_services(websocket_port)
            if not success:
                return False

            # Start REST API in background thread
            import threading
            api_thread = threading.Thread(
                target=lambda: self.rest_api.run(host='0.0.0.0', port=rest_port, debug=False),
                daemon=True
            )
            api_thread.start()

            self.running = True
            logger.info(f"✅ Modular servo backend started - WebSocket: {websocket_port}, REST: {rest_port}")
            return True

        except Exception as e:
            logger.error(f"Failed to start modular backend: {e}")
            return False

    async def stop_services(self):
        """Stop all backend services"""
        logger.info("🛑 Stopping R2D2 Modular Servo Backend...")
        self.running = False
        await self.core.stop_services()
        logger.info("✅ Modular servo backend stopped")

    # ============================================================================
    # BACKWARD COMPATIBILITY METHODS
    # ============================================================================

    def move_servo(self, channel: int, position: int, duration: float = 0) -> bool:
        """Move servo to position (legacy compatibility)"""
        command = ServoCommand(
            channel=channel,
            command_type=ServoCommandType.POSITION,
            value=position,
            duration=duration
        )

        if self.safety_system.validate_command(command):
            return self.controller.move_servo(channel, position, duration)
        return False

    def get_servo_status(self, channel: int) -> Dict[str, Any]:
        """Get servo status (legacy compatibility)"""
        return self.controller.get_servo_status(channel)

    def execute_sequence(self, sequence: ServoSequence) -> bool:
        """Execute sequence (legacy compatibility - sync wrapper)"""
        try:
            loop = asyncio.get_event_loop()
            return loop.run_until_complete(self.core.execute_sequence(sequence))
        except RuntimeError:
            # No event loop running
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                return loop.run_until_complete(self.core.execute_sequence(sequence))
            finally:
                loop.close()

    def emergency_stop(self) -> bool:
        """Emergency stop all servos (legacy compatibility)"""
        return self.core.emergency_stop()

    def get_system_status(self) -> Dict[str, Any]:
        """Get system status (legacy compatibility)"""
        try:
            loop = asyncio.get_event_loop()
            return loop.run_until_complete(self.core._get_system_status())
        except RuntimeError:
            # Return basic status if no event loop
            return {
                'backend_status': {
                    'running': self.running,
                    'uptime': time.time() - self.start_time,
                    'connection_status': self.connection_status.value,
                    'health_status': self.health_status.value
                },
                'servo_status': {
                    'total_servos': len(self.config_manager.get_all_configs()),
                    'emergency_stop': self.safety_system.emergency_stop_active
                }
            }

    def save_configuration(self, name: str = "default") -> bool:
        """Save configuration (legacy compatibility)"""
        return self.config_manager.save_configuration(name)

    def load_configuration(self, name: str) -> bool:
        """Load configuration (legacy compatibility)"""
        config = self.config_manager.load_configuration(name)
        return config is not None

    def set_safety_level(self, level: SafetyLevel):
        """Set safety level (legacy compatibility)"""
        self.safety_system.set_safety_level(level)
        self.config_manager.apply_safety_level(level)

    @property
    def performance_metrics(self):
        """Get performance metrics (legacy compatibility)"""
        return self.core.performance_metrics

    def get_active_sequences(self) -> Dict[str, Any]:
        """Get active sequences (legacy compatibility)"""
        return {
            seq_id: {
                'id': sequence.id,
                'name': sequence.name,
                'status': 'running',
                'commands': len(sequence.commands)
            }
            for seq_id, sequence in self.core.active_sequences.items()
        }

# ============================================================================
# FACTORY FUNCTIONS FOR EASY INITIALIZATION
# ============================================================================

def create_modular_servo_backend(maestro_port=None, simulation_mode=False, auto_detect=True):
    """Factory function to create modular servo backend"""
    return R2D2ServoBackendModular(maestro_port, simulation_mode, auto_detect)

async def start_complete_servo_system(websocket_port=8767, rest_port=5000,
                                    maestro_port=None, simulation_mode=False):
    """Start complete modular servo system"""
    backend = create_modular_servo_backend(maestro_port, simulation_mode)
    success = await backend.start_services(websocket_port, rest_port)

    if success:
        logger.info(f"🎯 Complete R2D2 Servo System Online!")
        logger.info(f"   WebSocket API: ws://localhost:{websocket_port}")
        logger.info(f"   REST API: http://localhost:{rest_port}/api/status")
        logger.info(f"   Configuration: {len(backend.config_manager.get_all_configs())} servos configured")
        logger.info(f"   Safety Level: {backend.safety_system.safety_level.value}")

    return backend if success else None

# ============================================================================
# COMPATIBILITY ALIASES
# ============================================================================

# Provide aliases for backward compatibility
ServoControlBackend = R2D2ServoBackendModular
EnhancedServoBackend = R2D2ServoBackendModular

# ============================================================================
# DEMONSTRATION AND TESTING
# ============================================================================

async def demo_modular_servo_system():
    """Demonstration of the modular servo system"""
    logger.info("🎬 Starting Modular Servo System Demo...")

    # Create backend
    backend = create_modular_servo_backend(simulation_mode=True)

    # Start services
    await backend.start_services(websocket_port=8767, rest_port=5000)

    try:
        # Demonstrate servo movement
        logger.info("Moving dome rotation servo...")
        success = backend.move_servo(0, 1800, duration=2.0)
        logger.info(f"Dome movement: {'✅ Success' if success else '❌ Failed'}")

        # Demonstrate sequence execution
        from servo_base_classes import ServoCommand, ServoSequence

        commands = [
            ServoCommand(channel=0, command_type=ServoCommandType.POSITION, value=1200, delay=0.0, duration=1.0),
            ServoCommand(channel=1, command_type=ServoCommandType.POSITION, value=1600, delay=0.5, duration=1.0),
            ServoCommand(channel=0, command_type=ServoCommandType.POSITION, value=1800, delay=1.0, duration=1.0),
        ]

        sequence = ServoSequence(
            name="Demo Sequence",
            commands=commands,
            description="Modular system demonstration"
        )

        logger.info("Executing demo sequence...")
        success = await backend.core.execute_sequence(sequence)
        logger.info(f"Sequence execution: {'✅ Success' if success else '❌ Failed'}")

        # Show system status
        status = await backend.core._get_system_status()
        logger.info(f"System Status: {status['backend_status']['health_status']}")
        logger.info(f"Performance: {status['performance']['success_rate']:.2%} success rate")

        # Keep running for a bit
        await asyncio.sleep(5)

    finally:
        # Stop services
        await backend.stop_services()
        logger.info("🏁 Demo completed")

if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Run demonstration
    asyncio.run(demo_modular_servo_system())