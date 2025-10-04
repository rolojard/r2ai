#!/usr/bin/env python3
"""
R2D2 Servo REST API Module
Consolidated REST API endpoints for servo control

This module provides a lightweight REST API that leverages the modular
servo backend core, eliminating duplication from the original API backend.
"""

import time
import json
import logging
from typing import Dict, List, Optional, Any
from flask import Flask, request, jsonify, Response
from flask_cors import CORS
from servo_base_classes import ServoCommand, ServoSequence, ServoCommandType, MotionType
from servo_backend_core import ServoBackendCore

logger = logging.getLogger(__name__)

class ServoRESTAPI:
    """Lightweight REST API for servo control"""

    def __init__(self, backend_core: ServoBackendCore, port: int = 5000):
        self.backend = backend_core
        self.port = port

        # Initialize Flask app
        self.app = Flask(__name__)
        self.app.config['SECRET_KEY'] = 'r2d2-servo-api'
        CORS(self.app)

        # Register routes
        self._register_routes()

    def _register_routes(self):
        """Register all API routes"""

        @self.app.route('/api/status', methods=['GET'])
        def get_status():
            """Get system status"""
            try:
                # Note: This is synchronous, but backend method is async
                # In production, you'd use async Flask or convert this properly
                status = {
                    'timestamp': time.time(),
                    'running': self.backend.running,
                    'connection_status': self.backend.connection_status.value,
                    'health_status': self.backend.health_status.value,
                    'uptime': time.time() - self.backend.start_time,
                    'servo_count': len(self.backend.config_manager.get_all_configs()),
                    'active_sequences': len(self.backend.active_sequences),
                    'emergency_stop': self.backend.safety_system.emergency_stop_active
                }
                return jsonify({'success': True, 'data': status})
            except Exception as e:
                logger.error(f"Status API error: {e}")
                return jsonify({'success': False, 'error': str(e)}), 500

        @self.app.route('/api/servo/<int:channel>/move', methods=['POST'])
        def move_servo(channel):
            """Move specific servo to position"""
            try:
                data = request.get_json()
                position = data.get('position')
                duration = data.get('duration', 0)

                if position is None:
                    return jsonify({'success': False, 'error': 'Position required'}), 400

                # Create command
                command = ServoCommand(
                    channel=channel,
                    command_type=ServoCommandType.POSITION,
                    value=float(position),
                    duration=float(duration)
                )

                # Validate with safety system
                if not self.backend.safety_system.validate_command(command):
                    return jsonify({
                        'success': False,
                        'error': 'Command failed safety validation'
                    }), 400

                # Execute command
                success = self.backend.controller.move_servo(channel, int(position), duration)

                return jsonify({
                    'success': success,
                    'command_id': command.id,
                    'channel': channel,
                    'position': position
                })

            except Exception as e:
                logger.error(f"Move servo API error: {e}")
                return jsonify({'success': False, 'error': str(e)}), 500

        @self.app.route('/api/servo/<int:channel>/status', methods=['GET'])
        def get_servo_status(channel):
            """Get servo status"""
            try:
                status = self.backend.controller.get_servo_status(channel)
                config = self.backend.config_manager.get_servo_config(channel)

                response_data = {
                    'channel': channel,
                    'status': status,
                    'config': {
                        'name': config.name if config else f'Servo_{channel}',
                        'enabled': config.enabled if config else False,
                        'home_position': config.home_position if config else 1500
                    } if config else None
                }

                return jsonify({'success': True, 'data': response_data})

            except Exception as e:
                logger.error(f"Servo status API error: {e}")
                return jsonify({'success': False, 'error': str(e)}), 500

        @self.app.route('/api/sequence/execute', methods=['POST'])
        def execute_sequence():
            """Execute servo sequence"""
            try:
                data = request.get_json()
                sequence_name = data.get('name', 'API_Sequence')
                commands_data = data.get('commands', [])

                # Convert to ServoCommand objects
                commands = []
                for cmd_data in commands_data:
                    command = ServoCommand(
                        channel=cmd_data.get('channel'),
                        command_type=ServoCommandType(cmd_data.get('type', 'position')),
                        value=cmd_data.get('value'),
                        duration=cmd_data.get('duration', 0),
                        delay=cmd_data.get('delay', 0),
                        motion_type=MotionType(cmd_data.get('motion_type', 'linear'))
                    )
                    commands.append(command)

                # Create sequence
                sequence = ServoSequence(
                    name=sequence_name,
                    commands=commands,
                    loop=data.get('loop', False),
                    loop_count=data.get('loop_count', 1)
                )

                # Execute asynchronously (simplified for REST)
                import asyncio
                try:
                    loop = asyncio.get_event_loop()
                except RuntimeError:
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)

                task = loop.create_task(self.backend.execute_sequence(sequence))

                return jsonify({
                    'success': True,
                    'sequence_id': sequence.id,
                    'name': sequence.name,
                    'command_count': len(commands)
                })

            except Exception as e:
                logger.error(f"Execute sequence API error: {e}")
                return jsonify({'success': False, 'error': str(e)}), 500

        @self.app.route('/api/sequence/<sequence_id>/stop', methods=['POST'])
        def stop_sequence(sequence_id):
            """Stop running sequence"""
            try:
                success = self.backend.stop_sequence(sequence_id)
                return jsonify({
                    'success': success,
                    'sequence_id': sequence_id,
                    'message': 'Sequence stopped' if success else 'Sequence not found'
                })

            except Exception as e:
                logger.error(f"Stop sequence API error: {e}")
                return jsonify({'success': False, 'error': str(e)}), 500

        @self.app.route('/api/emergency_stop', methods=['POST'])
        def emergency_stop():
            """Emergency stop all servos"""
            try:
                success = self.backend.emergency_stop()
                return jsonify({
                    'success': success,
                    'timestamp': time.time(),
                    'message': 'Emergency stop activated' if success else 'Emergency stop failed'
                })

            except Exception as e:
                logger.error(f"Emergency stop API error: {e}")
                return jsonify({'success': False, 'error': str(e)}), 500

        @self.app.route('/api/config/servos', methods=['GET'])
        def get_servo_configs():
            """Get all servo configurations"""
            try:
                configs = self.backend.config_manager.get_all_configs()
                config_data = {}

                for channel, config in configs.items():
                    config_data[str(channel)] = {
                        'channel': config.channel,
                        'name': config.name,
                        'type': config.servo_type.value,
                        'range': config.servo_range.value,
                        'enabled': config.enabled,
                        'home_position': config.home_position,
                        'limits': {
                            'min_position': config.limits.min_position,
                            'max_position': config.limits.max_position,
                            'safe_min': config.limits.safe_min,
                            'safe_max': config.limits.safe_max
                        }
                    }

                return jsonify({'success': True, 'data': config_data})

            except Exception as e:
                logger.error(f"Get configs API error: {e}")
                return jsonify({'success': False, 'error': str(e)}), 500

        @self.app.route('/api/config/servo/<int:channel>', methods=['PUT'])
        def update_servo_config(channel):
            """Update servo configuration"""
            try:
                data = request.get_json()
                success = self.backend.config_manager.update_servo_config(channel, **data)

                return jsonify({
                    'success': success,
                    'channel': channel,
                    'message': 'Configuration updated' if success else 'Update failed'
                })

            except Exception as e:
                logger.error(f"Update config API error: {e}")
                return jsonify({'success': False, 'error': str(e)}), 500

        @self.app.route('/api/safety/status', methods=['GET'])
        def get_safety_status():
            """Get safety system status"""
            try:
                status = self.backend.safety_system.get_safety_status()
                violations = self.backend.safety_system.get_violation_history(limit=50)

                return jsonify({
                    'success': True,
                    'data': {
                        'status': status,
                        'recent_violations': violations
                    }
                })

            except Exception as e:
                logger.error(f"Safety status API error: {e}")
                return jsonify({'success': False, 'error': str(e)}), 500

        @self.app.route('/api/safety/reset_emergency', methods=['POST'])
        def reset_emergency_stop():
            """Reset emergency stop"""
            try:
                self.backend.safety_system.reset_emergency_stop()
                return jsonify({
                    'success': True,
                    'message': 'Emergency stop reset',
                    'timestamp': time.time()
                })

            except Exception as e:
                logger.error(f"Reset emergency API error: {e}")
                return jsonify({'success': False, 'error': str(e)}), 500

        @self.app.route('/api/performance', methods=['GET'])
        def get_performance_metrics():
            """Get performance metrics"""
            try:
                metrics = {
                    'command_latency_ms': self.backend.performance_metrics.command_latency_ms,
                    'success_rate': self.backend.performance_metrics.success_rate,
                    'total_commands_processed': self.backend.performance_metrics.total_commands_processed,
                    'uptime': time.time() - self.backend.start_time,
                    'connection_status': self.backend.connection_status.value,
                    'health_status': self.backend.health_status.value
                }

                return jsonify({'success': True, 'data': metrics})

            except Exception as e:
                logger.error(f"Performance metrics API error: {e}")
                return jsonify({'success': False, 'error': str(e)}), 500

        @self.app.errorhandler(404)
        def not_found(error):
            return jsonify({
                'success': False,
                'error': 'Endpoint not found',
                'available_endpoints': [
                    '/api/status',
                    '/api/servo/<channel>/move',
                    '/api/servo/<channel>/status',
                    '/api/sequence/execute',
                    '/api/emergency_stop',
                    '/api/config/servos',
                    '/api/safety/status',
                    '/api/performance'
                ]
            }), 404

        @self.app.errorhandler(500)
        def internal_error(error):
            return jsonify({
                'success': False,
                'error': 'Internal server error',
                'timestamp': time.time()
            }), 500

    def run(self, host='0.0.0.0', port=None, debug=False):
        """Run the REST API server"""
        if port is not None:
            self.port = port
        logger.info(f"Starting servo REST API on {host}:{self.port}")
        self.app.run(host=host, port=self.port, debug=debug)

    def get_app(self):
        """Get Flask app for external deployment"""
        return self.app

# Factory function for easy initialization
def create_servo_api(backend_core: ServoBackendCore, port: int = 5000) -> ServoRESTAPI:
    """Create and configure servo REST API"""
    return ServoRESTAPI(backend_core, port)