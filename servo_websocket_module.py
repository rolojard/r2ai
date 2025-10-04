#!/usr/bin/env python3
"""
R2D2 Servo WebSocket Communication Module
Centralized WebSocket handling for all servo systems

This module provides a unified WebSocket communication layer for all servo
components, eliminating duplication across different servo modules.
"""

import asyncio
import websockets
import json
import logging
import time
from typing import Dict, List, Set, Any, Optional, Callable
from servo_base_classes import (
    WebSocketHandlerBase,
    ServoCommand,
    ServoSequence,
    ServoCommandType,
    ConnectionStatus,
    SystemHealthStatus
)

logger = logging.getLogger(__name__)

class ServoWebSocketHandler(WebSocketHandlerBase):
    """Centralized WebSocket handler for servo communication"""

    def __init__(self, port: int = 8767):
        super().__init__(port)
        self.message_handlers: Dict[str, Callable] = {}
        self.status_callbacks: List[Callable] = []
        self.client_info: Dict[Any, Dict[str, Any]] = {}
        self.last_status_broadcast = 0
        self.broadcast_interval = 0.1  # 10 Hz status updates

    def register_message_handler(self, message_type: str, handler: Callable):
        """Register handler for specific message types"""
        self.message_handlers[message_type] = handler

    def add_status_callback(self, callback: Callable):
        """Add callback for status updates"""
        self.status_callbacks.append(callback)

    async def start_server(self):
        """Start the WebSocket server"""
        try:
            self.server = await websockets.serve(
                self.handle_client,
                "localhost",
                self.port,
                ping_interval=30,
                ping_timeout=10
            )
            self._running = True
            logger.info(f"Servo WebSocket server started on port {self.port}")

            # Start status broadcast task
            asyncio.create_task(self._status_broadcast_loop())

        except Exception as e:
            logger.error(f"Failed to start WebSocket server: {e}")
            return False
        return True

    async def stop_server(self):
        """Stop the WebSocket server"""
        self._running = False
        if self.server:
            self.server.close()
            await self.server.wait_closed()
            logger.info("Servo WebSocket server stopped")

    async def handle_client(self, websocket, path):
        """Handle new WebSocket client connection"""
        client_id = f"{websocket.remote_address[0]}:{websocket.remote_address[1]}"
        logger.info(f"New servo WebSocket client connected: {client_id}")

        # Register client
        self.clients.add(websocket)
        self.client_info[websocket] = {
            'id': client_id,
            'connected_at': time.time(),
            'message_count': 0,
            'last_activity': time.time()
        }

        try:
            # Send initial status
            await self._send_initial_status(websocket)

            # Handle messages
            async for message in websocket:
                await self.handle_message(websocket, message)

        except websockets.exceptions.ConnectionClosed:
            logger.info(f"Servo WebSocket client disconnected: {client_id}")
        except Exception as e:
            logger.error(f"WebSocket error for client {client_id}: {e}")
        finally:
            # Cleanup
            self.clients.discard(websocket)
            self.client_info.pop(websocket, None)

    async def handle_message(self, websocket, message):
        """Handle incoming WebSocket message"""
        try:
            data = json.loads(message)
            message_type = data.get('type', 'unknown')

            # Update client activity
            if websocket in self.client_info:
                self.client_info[websocket]['last_activity'] = time.time()
                self.client_info[websocket]['message_count'] += 1

            # Route to appropriate handler
            if message_type in self.message_handlers:
                try:
                    await self.message_handlers[message_type](websocket, data)
                except Exception as e:
                    logger.error(f"Handler error for {message_type}: {e}")
                    await self.send_error(websocket, f"Handler error: {str(e)}")
            else:
                logger.warning(f"Unknown message type: {message_type}")
                await self.send_error(websocket, f"Unknown message type: {message_type}")

        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in WebSocket message: {e}")
            await self.send_error(websocket, "Invalid JSON format")
        except Exception as e:
            logger.error(f"WebSocket message handling error: {e}")
            await self.send_error(websocket, f"Message handling error: {str(e)}")

    async def broadcast_status(self, status: Dict[str, Any]):
        """Broadcast status to all connected clients"""
        if not self.clients:
            return

        message = {
            'type': 'status_update',
            'timestamp': time.time(),
            'data': status
        }

        # Send to all clients
        disconnected_clients = set()
        for client in self.clients.copy():
            try:
                await client.send(json.dumps(message))
            except websockets.exceptions.ConnectionClosed:
                disconnected_clients.add(client)
            except Exception as e:
                logger.error(f"Error broadcasting to client: {e}")
                disconnected_clients.add(client)

        # Remove disconnected clients
        for client in disconnected_clients:
            self.clients.discard(client)
            self.client_info.pop(client, None)

    async def send_error(self, websocket, error_message: str):
        """Send error message to specific client"""
        try:
            error_data = {
                'type': 'error',
                'timestamp': time.time(),
                'message': error_message
            }
            await websocket.send(json.dumps(error_data))
        except Exception as e:
            logger.error(f"Failed to send error message: {e}")

    async def send_response(self, websocket, response_data: Dict[str, Any]):
        """Send response to specific client"""
        try:
            response = {
                'type': 'response',
                'timestamp': time.time(),
                'data': response_data
            }
            await websocket.send(json.dumps(response))
        except Exception as e:
            logger.error(f"Failed to send response: {e}")

    async def _send_initial_status(self, websocket):
        """Send initial status to newly connected client"""
        try:
            # Gather status from callbacks
            status_data = await self._gather_status_data()

            initial_message = {
                'type': 'initial_status',
                'timestamp': time.time(),
                'data': status_data
            }
            await websocket.send(json.dumps(initial_message))
        except Exception as e:
            logger.error(f"Failed to send initial status: {e}")

    async def _status_broadcast_loop(self):
        """Background task for regular status broadcasts"""
        while self._running:
            try:
                current_time = time.time()
                if current_time - self.last_status_broadcast >= self.broadcast_interval:
                    status_data = await self._gather_status_data()
                    await self.broadcast_status(status_data)
                    self.last_status_broadcast = current_time

                await asyncio.sleep(0.05)  # 20 Hz loop
            except Exception as e:
                logger.error(f"Status broadcast loop error: {e}")
                await asyncio.sleep(1)

    async def _gather_status_data(self) -> Dict[str, Any]:
        """Gather status data from all registered callbacks"""
        status_data = {
            'server_time': time.time(),
            'connected_clients': len(self.clients),
            'websocket_status': 'running' if self._running else 'stopped'
        }

        # Gather data from status callbacks
        for callback in self.status_callbacks:
            try:
                callback_data = await callback() if asyncio.iscoroutinefunction(callback) else callback()
                if isinstance(callback_data, dict):
                    status_data.update(callback_data)
            except Exception as e:
                logger.error(f"Status callback error: {e}")

        return status_data

    def get_client_stats(self) -> Dict[str, Any]:
        """Get statistics about connected clients"""
        return {
            'total_clients': len(self.clients),
            'client_details': [
                {
                    'id': info['id'],
                    'connected_duration': time.time() - info['connected_at'],
                    'message_count': info['message_count'],
                    'last_activity': time.time() - info['last_activity']
                }
                for info in self.client_info.values()
            ]
        }

class StandardServoMessageHandlers:
    """Standard message handlers for common servo operations"""

    def __init__(self, servo_controller, safety_system, sequence_engine, config_manager):
        self.servo_controller = servo_controller
        self.safety_system = safety_system
        self.sequence_engine = sequence_engine
        self.config_manager = config_manager

    async def handle_servo_command(self, websocket, data):
        """Handle servo movement commands"""
        try:
            command_data = data.get('command', {})
            channel = command_data.get('channel')
            position = command_data.get('position')
            duration = command_data.get('duration', 0)

            if channel is None or position is None:
                await websocket.send(json.dumps({
                    'type': 'error',
                    'message': 'Missing channel or position'
                }))
                return

            # Create and validate command
            command = ServoCommand(
                channel=channel,
                command_type=ServoCommandType.POSITION,
                value=position,
                duration=duration
            )

            if not self.safety_system.validate_command(command):
                await websocket.send(json.dumps({
                    'type': 'error',
                    'message': 'Command failed safety validation'
                }))
                return

            # Execute command
            success = self.servo_controller.move_servo(channel, position, duration)

            await websocket.send(json.dumps({
                'type': 'command_response',
                'success': success,
                'command_id': command.id
            }))

        except Exception as e:
            logger.error(f"Servo command error: {e}")
            await websocket.send(json.dumps({
                'type': 'error',
                'message': f'Command execution error: {str(e)}'
            }))

    async def handle_sequence_command(self, websocket, data):
        """Handle sequence execution commands"""
        try:
            sequence_data = data.get('sequence', {})
            sequence_name = sequence_data.get('name', 'unnamed')
            commands_data = sequence_data.get('commands', [])

            # Convert to ServoCommand objects
            commands = []
            for cmd_data in commands_data:
                command = ServoCommand(
                    channel=cmd_data.get('channel'),
                    command_type=ServoCommandType(cmd_data.get('type', 'position')),
                    value=cmd_data.get('value'),
                    duration=cmd_data.get('duration', 0),
                    delay=cmd_data.get('delay', 0)
                )
                commands.append(command)

            # Create sequence
            sequence = ServoSequence(
                name=sequence_name,
                commands=commands,
                loop=sequence_data.get('loop', False),
                loop_count=sequence_data.get('loop_count', 1)
            )

            # Execute sequence
            success = await self.sequence_engine.execute_sequence(sequence)

            await websocket.send(json.dumps({
                'type': 'sequence_response',
                'success': success,
                'sequence_id': sequence.id
            }))

        except Exception as e:
            logger.error(f"Sequence command error: {e}")
            await websocket.send(json.dumps({
                'type': 'error',
                'message': f'Sequence execution error: {str(e)}'
            }))

    async def handle_config_command(self, websocket, data):
        """Handle configuration commands"""
        try:
            config_data = data.get('config', {})
            action = config_data.get('action', 'get')

            if action == 'get':
                # Get current configuration
                config = self.config_manager.get_all_configs()
                await websocket.send(json.dumps({
                    'type': 'config_response',
                    'action': 'get',
                    'config': config
                }))

            elif action == 'set':
                # Set configuration
                channel = config_data.get('channel')
                new_config = config_data.get('servo_config', {})

                if channel is not None:
                    success = self.config_manager.update_servo_config(channel, **new_config)
                    await websocket.send(json.dumps({
                        'type': 'config_response',
                        'action': 'set',
                        'success': success,
                        'channel': channel
                    }))

            elif action == 'save':
                # Save configuration
                name = config_data.get('name', 'default')
                success = self.config_manager.save_configuration(name)
                await websocket.send(json.dumps({
                    'type': 'config_response',
                    'action': 'save',
                    'success': success,
                    'name': name
                }))

        except Exception as e:
            logger.error(f"Config command error: {e}")
            await websocket.send(json.dumps({
                'type': 'error',
                'message': f'Configuration error: {str(e)}'
            }))

    async def handle_emergency_stop(self, websocket, data):
        """Handle emergency stop commands"""
        try:
            success = self.servo_controller.emergency_stop()
            await websocket.send(json.dumps({
                'type': 'emergency_response',
                'success': success,
                'timestamp': time.time()
            }))
        except Exception as e:
            logger.error(f"Emergency stop error: {e}")
            await websocket.send(json.dumps({
                'type': 'error',
                'message': f'Emergency stop error: {str(e)}'
            }))