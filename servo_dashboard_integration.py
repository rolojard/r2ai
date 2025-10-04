#!/usr/bin/env python3
"""
R2D2 Servo Dashboard Integration Service
==========================================

Unified integration service that bridges the enhanced Maestro servo control system
with the dashboard server, providing real-time control, monitoring, and WebSocket
communication for the R2D2 advanced servo dashboard.

This service integrates:
- Enhanced Maestro Controller with auto-detection
- Advanced Servo Backend with WebSocket support
- Dashboard Server REST API integration
- Real-time monitoring and diagnostics
- Safety systems and emergency controls

Author: Expert Project Manager
Target: NVIDIA Orin Nano R2D2 Systems
Hardware: Pololu Maestro Mini 12-Channel USB Servo Controller
"""

import asyncio
import json
import logging
import threading
import time
import sys
import os
from typing import Dict, List, Optional, Any
from pathlib import Path
from flask import Flask, jsonify, request
from flask_cors import CORS
import websockets

# Add project path
sys.path.append('/home/rolo/r2ai')

# Import our servo control components
from maestro_enhanced_controller import (
    EnhancedMaestroController,
    HardwareDetectionStatus,
    SequenceStatus,
    DynamicServoConfig
)
from r2d2_servo_backend import (
    ServoControlBackend,
    WebSocketHandler,
    ServoRESTAPI,
    ConfigurationManager,
    SafetyMonitor
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ServoDashboardIntegration:
    """Unified servo dashboard integration service"""

    def __init__(self, auto_detect_hardware=True, simulation_mode=False):
        """Initialize the integration service"""
        self.auto_detect_hardware = auto_detect_hardware
        self.simulation_mode = simulation_mode
        self.running = False

        # Initialize components
        self.enhanced_controller: Optional[EnhancedMaestroController] = None
        self.servo_backend: Optional[ServoControlBackend] = None
        self.flask_app = Flask(__name__)
        CORS(self.flask_app)

        # Service state
        self.start_time = time.time()
        self.last_status_update = 0
        self.connection_status = "initializing"

        # Setup Flask routes
        self._setup_flask_routes()

        logger.info("Servo Dashboard Integration Service initialized")

    def _setup_flask_routes(self):
        """Setup Flask REST API routes"""

        @self.flask_app.route('/api/servo/status', methods=['GET'])
        def get_servo_status():
            """Get comprehensive servo system status"""
            try:
                if not self.enhanced_controller:
                    return jsonify({
                        "success": False,
                        "error": "Servo controller not initialized",
                        "data": {}
                    }), 503

                status = self.enhanced_controller.get_enhanced_status_report()

                return jsonify({
                    "success": True,
                    "data": {
                        "controller": {
                            "connected": status["controller"]["connected"],
                            "simulation_mode": status["controller"]["simulation_mode"],
                            "emergency_stop": status["controller"]["emergency_stop"],
                            "port": status["controller"]["port"],
                            "uptime": time.time() - self.start_time
                        },
                        "hardware_detection": status["hardware_detection"],
                        "servos": self._format_servo_data(),
                        "sequences": status["sequences"],
                        "system_health": self._get_system_health()
                    },
                    "timestamp": time.time()
                })

            except Exception as e:
                logger.error(f"Status request failed: {e}")
                return jsonify({
                    "success": False,
                    "error": str(e)
                }), 500

        @self.flask_app.route('/api/servo/<int:channel>/move', methods=['POST'])
        def move_servo(channel):
            """Move specific servo to position"""
            try:
                data = request.get_json()
                position = data.get('position')

                if position is None:
                    return jsonify({
                        "success": False,
                        "error": "Position parameter required"
                    }), 400

                success = self.enhanced_controller.move_servo_microseconds(channel, position)

                return jsonify({
                    "success": success,
                    "channel": channel,
                    "position": position,
                    "timestamp": time.time()
                })

            except Exception as e:
                logger.error(f"Servo move failed: {e}")
                return jsonify({
                    "success": False,
                    "error": str(e)
                }), 500

        @self.flask_app.route('/api/servo/<int:channel>/home', methods=['POST'])
        def home_servo(channel):
            """Move servo to home position"""
            try:
                if channel not in self.enhanced_controller.dynamic_configs:
                    return jsonify({
                        "success": False,
                        "error": f"Channel {channel} not configured"
                    }), 400

                config = self.enhanced_controller.dynamic_configs[channel]
                success = self.enhanced_controller.set_servo_position(
                    channel, config.home_position
                )

                return jsonify({
                    "success": success,
                    "channel": channel,
                    "position": config.home_position / 4.0,  # Convert to microseconds
                    "timestamp": time.time()
                })

            except Exception as e:
                logger.error(f"Servo home failed: {e}")
                return jsonify({
                    "success": False,
                    "error": str(e)
                }), 500

        @self.flask_app.route('/api/servo/emergency_stop', methods=['POST'])
        def emergency_stop():
            """Emergency stop all servos"""
            try:
                self.enhanced_controller.emergency_stop()

                return jsonify({
                    "success": True,
                    "message": "Emergency stop activated",
                    "timestamp": time.time()
                })

            except Exception as e:
                logger.error(f"Emergency stop failed: {e}")
                return jsonify({
                    "success": False,
                    "error": str(e)
                }), 500

        @self.flask_app.route('/api/servo/emergency_stop/clear', methods=['POST'])
        def clear_emergency_stop():
            """Clear emergency stop"""
            try:
                self.enhanced_controller.resume_operation()

                return jsonify({
                    "success": True,
                    "message": "Emergency stop cleared",
                    "timestamp": time.time()
                })

            except Exception as e:
                logger.error(f"Clear emergency stop failed: {e}")
                return jsonify({
                    "success": False,
                    "error": str(e)
                }), 500

        @self.flask_app.route('/api/servo/sequence/<sequence_name>/execute', methods=['POST'])
        def execute_sequence(sequence_name):
            """Execute servo sequence"""
            try:
                success = self.enhanced_controller.execute_sequence(sequence_name)

                return jsonify({
                    "success": success,
                    "sequence": sequence_name,
                    "timestamp": time.time()
                })

            except Exception as e:
                logger.error(f"Sequence execution failed: {e}")
                return jsonify({
                    "success": False,
                    "error": str(e)
                }), 500

        @self.flask_app.route('/api/servo/sequence/stop', methods=['POST'])
        def stop_sequence():
            """Stop current sequence"""
            try:
                success = self.enhanced_controller.stop_sequence()

                return jsonify({
                    "success": success,
                    "message": "Sequence stopped",
                    "timestamp": time.time()
                })

            except Exception as e:
                logger.error(f"Sequence stop failed: {e}")
                return jsonify({
                    "success": False,
                    "error": str(e)
                }), 500

        @self.flask_app.route('/api/servo/board/detect', methods=['POST'])
        def detect_board():
            """Detect Maestro board"""
            try:
                # Re-initialize controller with detection
                self._initialize_servo_controller()

                if self.enhanced_controller and self.enhanced_controller.hardware_info:
                    return jsonify({
                        "success": True,
                        "hardware_info": {
                            "port": self.enhanced_controller.hardware_info.port,
                            "device_name": self.enhanced_controller.hardware_info.device_name,
                            "serial_number": self.enhanced_controller.hardware_info.serial_number,
                            "channel_count": self.enhanced_controller.hardware_info.channel_count,
                            "connection_status": self.enhanced_controller.hardware_info.connection_status
                        },
                        "timestamp": time.time()
                    })
                else:
                    return jsonify({
                        "success": False,
                        "error": "No Maestro board detected",
                        "timestamp": time.time()
                    })

            except Exception as e:
                logger.error(f"Board detection failed: {e}")
                return jsonify({
                    "success": False,
                    "error": str(e)
                }), 500

    def _format_servo_data(self) -> Dict:
        """Format servo data for dashboard"""
        if not self.enhanced_controller:
            return {}

        servo_data = {}
        for channel, config in self.enhanced_controller.dynamic_configs.items():
            status = self.enhanced_controller.servo_status.get(channel)
            if status:
                servo_data[channel] = {
                    "name": config.display_name,
                    "enabled": config.enabled,
                    "position_us": status.position / 4.0,  # Convert to microseconds
                    "target_us": status.target / 4.0,
                    "home_us": config.home_position / 4.0,
                    "range_us": [config.min_position / 4.0, config.max_position / 4.0],
                    "moving": self.enhanced_controller.is_servo_moving(channel),
                    "last_update": status.last_update
                }

        return servo_data

    def _get_system_health(self) -> Dict:
        """Get system health metrics"""
        return {
            "overall_status": "excellent" if self.connection_status == "connected" else "warning",
            "connection_quality": "excellent" if not self.simulation_mode else "simulation",
            "response_time_ms": 1.2,  # Placeholder
            "error_count": 0,  # Placeholder
            "uptime_seconds": time.time() - self.start_time
        }

    async def _initialize_servo_controller(self):
        """Initialize the enhanced servo controller"""
        try:
            logger.info("🔧 Initializing Enhanced Maestro Controller...")

            # Initialize enhanced controller with auto-detection
            self.enhanced_controller = EnhancedMaestroController(
                auto_detect=self.auto_detect_hardware
            )

            # Update connection status
            if self.enhanced_controller.detection_status == HardwareDetectionStatus.CONNECTED:
                self.connection_status = "connected"
                logger.info("✅ Maestro hardware connected successfully")
            elif self.enhanced_controller.detection_status == HardwareDetectionStatus.SIMULATION:
                self.connection_status = "simulation"
                logger.info("🔄 Running in simulation mode")
            else:
                self.connection_status = "failed"
                logger.warning("⚠️ Maestro hardware detection failed")

        except Exception as e:
            logger.error(f"Servo controller initialization failed: {e}")
            self.connection_status = "failed"
            # Fall back to simulation mode
            self.enhanced_controller = EnhancedMaestroController(auto_detect=False)

    async def start_services(self,
                           rest_port=5000,
                           websocket_port=8767):
        """Start all integration services"""
        logger.info("🚀 Starting Servo Dashboard Integration Services...")

        # Initialize servo controller
        await self._initialize_servo_controller()

        # Start Flask REST API server in separate thread
        flask_thread = threading.Thread(
            target=self._run_flask_server,
            args=(rest_port,),
            daemon=True
        )
        flask_thread.start()

        # Start WebSocket server for real-time communication
        websocket_thread = threading.Thread(
            target=self._run_websocket_server,
            args=(websocket_port,),
            daemon=True
        )
        websocket_thread.start()

        self.running = True
        logger.info(f"✅ Services started - REST API: {rest_port}, WebSocket: {websocket_port}")

        # Start status monitoring loop
        await self._status_monitoring_loop()

    def _run_flask_server(self, port):
        """Run Flask REST API server"""
        try:
            self.flask_app.run(
                host='0.0.0.0',
                port=port,
                debug=False,
                use_reloader=False
            )
        except Exception as e:
            logger.error(f"Flask server failed: {e}")

    def _run_websocket_server(self, port):
        """Run WebSocket server in thread"""
        async def websocket_main():
            await self._start_websocket_server(port)

        # Run in new event loop
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(websocket_main())

    async def _start_websocket_server(self, port):
        """Start WebSocket server for real-time communication"""
        self.connected_clients = set()

        async def handle_client(websocket, path):
            """Handle WebSocket client connections"""
            self.connected_clients.add(websocket)
            logger.info(f"Dashboard client connected: {websocket.remote_address}")

            try:
                # Send initial status
                await self._send_status_update(websocket)

                async for message in websocket:
                    await self._handle_websocket_message(websocket, message)

            except websockets.exceptions.ConnectionClosed:
                logger.info("Dashboard client disconnected")
            except Exception as e:
                logger.error(f"WebSocket error: {e}")
            finally:
                self.connected_clients.discard(websocket)

        # Start server
        start_server = websockets.serve(handle_client, "localhost", port)
        await start_server
        logger.info(f"WebSocket server started on port {port}")

    async def _handle_websocket_message(self, websocket, message):
        """Handle incoming WebSocket messages"""
        try:
            data = json.loads(message)
            msg_type = data.get("type")

            if msg_type == "request_data":
                await self._send_status_update(websocket)
            elif msg_type == "servo_command":
                await self._handle_servo_websocket_command(websocket, data)
            elif msg_type == "sequence_command":
                await self._handle_sequence_websocket_command(websocket, data)
            elif msg_type == "emergency_stop":
                self.enhanced_controller.emergency_stop()
                await self._broadcast_alert("Emergency stop activated", "error")
            else:
                logger.warning(f"Unknown WebSocket message type: {msg_type}")

        except Exception as e:
            logger.error(f"WebSocket message handling error: {e}")

    async def _handle_servo_websocket_command(self, websocket, data):
        """Handle servo control via WebSocket"""
        try:
            channel = data["channel"]
            position = data["position"]

            success = self.enhanced_controller.move_servo_microseconds(channel, position)

            response = {
                "type": "servo_response",
                "channel": channel,
                "position": position,
                "success": success,
                "timestamp": time.time()
            }

            await websocket.send(json.dumps(response))

        except Exception as e:
            await self._send_websocket_error(websocket, f"Servo command error: {e}")

    async def _handle_sequence_websocket_command(self, websocket, data):
        """Handle sequence control via WebSocket"""
        try:
            action = data["action"]
            sequence_id = data.get("sequence_id")

            if action == "execute" and sequence_id:
                success = self.enhanced_controller.execute_sequence(sequence_id)
            elif action == "stop":
                success = self.enhanced_controller.stop_sequence()
            elif action == "list":
                sequences = list(self.enhanced_controller.saved_sequences.keys())
                response = {
                    "type": "sequence_list",
                    "sequences": sequences,
                    "timestamp": time.time()
                }
                await websocket.send(json.dumps(response))
                return
            else:
                success = False

            response = {
                "type": "sequence_response",
                "action": action,
                "success": success,
                "timestamp": time.time()
            }

            await websocket.send(json.dumps(response))

        except Exception as e:
            await self._send_websocket_error(websocket, f"Sequence command error: {e}")

    async def _send_status_update(self, websocket=None):
        """Send status update via WebSocket"""
        try:
            if not self.enhanced_controller:
                return

            status = self.enhanced_controller.get_enhanced_status_report()

            status_data = {
                "type": "servo_status",
                "data": {
                    "controller": {
                        "connected": status["controller"]["connected"],
                        "simulation_mode": status["controller"]["simulation_mode"],
                        "emergency_stop": status["controller"]["emergency_stop"],
                        "port": status["controller"]["port"],
                        "servo_count": len(self.enhanced_controller.dynamic_configs),
                        "uptime": time.time() - self.start_time
                    },
                    "servos": self._format_servo_data(),
                    "hardware_detection": status["hardware_detection"],
                    "sequences": status["sequences"]
                },
                "timestamp": time.time()
            }

            message = json.dumps(status_data)

            if websocket:
                await websocket.send(message)
            else:
                # Broadcast to all clients
                if hasattr(self, 'connected_clients') and self.connected_clients:
                    for client in self.connected_clients.copy():
                        try:
                            await client.send(message)
                        except:
                            self.connected_clients.discard(client)

        except Exception as e:
            logger.error(f"Status update error: {e}")

    async def _send_websocket_error(self, websocket, error_message):
        """Send error message via WebSocket"""
        try:
            error_data = {
                "type": "error",
                "message": error_message,
                "timestamp": time.time()
            }
            await websocket.send(json.dumps(error_data))
        except:
            pass

    async def _broadcast_alert(self, message, level="info"):
        """Broadcast alert to all connected clients"""
        if hasattr(self, 'connected_clients') and self.connected_clients:
            alert_data = {
                "type": "alert",
                "message": message,
                "level": level,
                "timestamp": time.time()
            }

            for client in self.connected_clients.copy():
                try:
                    await client.send(json.dumps(alert_data))
                except:
                    self.connected_clients.discard(client)

    async def _status_monitoring_loop(self):
        """Periodic status monitoring and broadcasting"""
        while self.running:
            try:
                # Broadcast status every 2 seconds
                await self._send_status_update()
                await asyncio.sleep(2.0)

            except Exception as e:
                logger.error(f"Status monitoring error: {e}")
                await asyncio.sleep(5.0)

    def shutdown(self):
        """Shutdown integration service"""
        logger.info("Shutting down Servo Dashboard Integration...")

        self.running = False

        if self.enhanced_controller:
            self.enhanced_controller.shutdown()

        logger.info("✅ Servo Dashboard Integration shutdown complete")

async def main():
    """Main service entry point"""
    logger.info("🤖 R2D2 Servo Dashboard Integration Service")
    logger.info("=" * 60)

    # Initialize integration service
    integration = ServoDashboardIntegration(
        auto_detect_hardware=True,
        simulation_mode=False
    )

    try:
        # Start all services
        await integration.start_services(
            rest_port=5000,
            websocket_port=8767
        )

    except KeyboardInterrupt:
        logger.info("Service interrupted by user")
    except Exception as e:
        logger.error(f"Service failed: {e}")
    finally:
        integration.shutdown()

if __name__ == "__main__":
    # Run the integration service
    asyncio.run(main())