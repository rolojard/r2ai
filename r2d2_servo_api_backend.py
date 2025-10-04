#!/usr/bin/env python3
"""
R2D2 Servo API Backend
Flask REST API for Servo Control Integration with Vision Dashboard

This module provides a comprehensive REST API backend for integrating
the R2D2 servo control system with the existing vision dashboard,
enabling real-time servo control, monitoring, and sequence execution.

Features:
- RESTful API for servo control and monitoring
- WebSocket integration for real-time updates
- Safety system integration with emergency stop
- Sequence and script execution endpoints
- Hardware detection and configuration
- Performance monitoring and analytics
"""

import time
import logging
import threading
import json
from typing import Dict, List, Optional, Any
from flask import Flask, request, jsonify, Response
from flask_cors import CORS
from flask_socketio import SocketIO, emit
import eventlet

# Import our servo systems
from pololu_maestro_controller import PololuMaestroController, R2D2MaestroInterface
from maestro_hardware_detector import MaestroHardwareDetector
from r2d2_servo_config_manager import R2D2ServoConfigManager
from r2d2_animatronic_sequences import R2D2AnimatronicSequencer, R2D2Emotion
from r2d2_emergency_safety_system import R2D2EmergencySafetySystem
from maestro_script_engine import MaestroScriptEngine

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = 'r2d2-servo-control-secret'
CORS(app)

# Initialize SocketIO
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='eventlet')

class R2D2ServoAPIBackend:
    """Comprehensive R2D2 Servo Control API Backend"""

    def __init__(self):
        # Initialize servo systems
        self.hardware_detector = MaestroHardwareDetector()
        self.controller: Optional[PololuMaestroController] = None
        self.config_manager: Optional[R2D2ServoConfigManager] = None
        self.sequencer: Optional[R2D2AnimatronicSequencer] = None
        self.safety_system: Optional[R2D2EmergencySafetySystem] = None
        self.script_engine: Optional[MaestroScriptEngine] = None
        self.r2d2_interface: Optional[R2D2MaestroInterface] = None

        # System state
        self.system_initialized = False
        self.connected_clients = set()
        self.last_heartbeat = time.time()

        # Performance tracking
        self.api_calls = 0
        self.servo_commands = 0
        self.sequences_executed = 0
        self.system_start_time = time.time()

        # Status broadcasting
        self.status_broadcast_active = False
        self.status_thread: Optional[threading.Thread] = None

        # Initialize system
        self._initialize_system()

    def _initialize_system(self):
        """Initialize the complete servo control system"""
        logger.info("🚀 Initializing R2D2 Servo Control System...")

        try:
            # Detect hardware
            devices = self.hardware_detector.scan_for_maestro_devices()
            if devices:
                optimal_device = self.hardware_detector.get_optimal_device()
                logger.info(f"Using device: {optimal_device.variant.value} on {optimal_device.port}")

                # Initialize controller
                self.controller = PololuMaestroController(optimal_device.port, simulation_mode=False)
            else:
                logger.warning("No hardware detected - using simulation mode")
                self.controller = PololuMaestroController(simulation_mode=True)

            # Initialize configuration manager
            self.config_manager = R2D2ServoConfigManager(self.hardware_detector)
            self.config_manager.initialize_from_hardware()

            # Initialize safety system
            self.safety_system = R2D2EmergencySafetySystem(self.controller, self.config_manager)
            self.safety_system.start_safety_monitoring()

            # Initialize sequencer
            self.sequencer = R2D2AnimatronicSequencer(self.controller, self.config_manager)

            # Initialize script engine
            self.script_engine = MaestroScriptEngine(self.controller, self.config_manager, self.safety_system)

            # Initialize high-level interface
            self.r2d2_interface = R2D2MaestroInterface(self.controller)

            self.system_initialized = True
            logger.info("✅ R2D2 Servo Control System initialized successfully")

            # Start status broadcasting
            self._start_status_broadcasting()

        except Exception as e:
            logger.error(f"System initialization failed: {e}")
            self.system_initialized = False

    def _start_status_broadcasting(self):
        """Start real-time status broadcasting to connected clients"""
        if self.status_broadcast_active:
            return

        self.status_broadcast_active = True

        def status_broadcast_loop():
            while self.status_broadcast_active:
                try:
                    if self.connected_clients:
                        status = self.get_system_status()
                        socketio.emit('system_status', status)

                    time.sleep(1.0)  # 1Hz status updates

                except Exception as e:
                    logger.error(f"Status broadcast error: {e}")
                    time.sleep(5.0)

        self.status_thread = threading.Thread(target=status_broadcast_loop, daemon=True)
        self.status_thread.start()

    def get_system_status(self) -> Dict:
        """Get comprehensive system status"""
        if not self.system_initialized:
            return {"initialized": False, "error": "System not initialized"}

        try:
            # Collect status from all subsystems
            controller_status = self.controller.get_status_report()
            config_status = self.config_manager.get_status_report()
            safety_status = self.safety_system.get_safety_status()
            sequencer_status = self.sequencer.get_status_report()
            script_status = self.script_engine.get_execution_status()

            # Hardware status
            hardware_status = self.hardware_detector.get_status_report()

            # API performance
            uptime = time.time() - self.system_start_time
            api_performance = {
                "uptime": uptime,
                "api_calls": self.api_calls,
                "servo_commands": self.servo_commands,
                "sequences_executed": self.sequences_executed,
                "calls_per_minute": (self.api_calls / (uptime / 60)) if uptime > 0 else 0
            }

            return {
                "initialized": True,
                "timestamp": time.time(),
                "controller": controller_status,
                "configuration": config_status,
                "safety": safety_status,
                "sequencer": sequencer_status,
                "script_engine": script_status,
                "hardware": hardware_status,
                "performance": api_performance
            }

        except Exception as e:
            logger.error(f"Status collection error: {e}")
            return {"initialized": True, "error": str(e)}

# Create global backend instance
backend = R2D2ServoAPIBackend()

# === REST API ENDPOINTS ===

@app.route('/api/status', methods=['GET'])
def get_status():
    """Get system status"""
    backend.api_calls += 1
    try:
        status = backend.get_system_status()
        return jsonify({"success": True, "data": status})
    except Exception as e:
        logger.error(f"Status endpoint error: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/servo/<int:channel>/move', methods=['POST'])
def move_servo(channel):
    """Move specific servo to position"""
    backend.api_calls += 1
    backend.servo_commands += 1

    if not backend.system_initialized:
        return jsonify({"success": False, "error": "System not initialized"}), 503

    try:
        data = request.get_json()
        position = data.get('position')

        if position is None:
            return jsonify({"success": False, "error": "Position required"}), 400

        # Validate command with safety system
        is_safe, reason = backend.safety_system.validate_servo_command(channel, position)
        if not is_safe:
            return jsonify({"success": False, "error": f"Safety validation failed: {reason}"}), 403

        # Execute command
        success = backend.controller.move_servo_microseconds(channel, position)

        if success:
            # Broadcast update to connected clients
            socketio.emit('servo_moved', {
                'channel': channel,
                'position': position,
                'timestamp': time.time()
            })

            return jsonify({"success": True, "data": {"channel": channel, "position": position}})
        else:
            return jsonify({"success": False, "error": "Servo command failed"}), 500

    except Exception as e:
        logger.error(f"Move servo error: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/servo/<int:channel>/config', methods=['GET', 'POST'])
def servo_config(channel):
    """Get or update servo configuration"""
    backend.api_calls += 1

    if not backend.system_initialized:
        return jsonify({"success": False, "error": "System not initialized"}), 503

    try:
        if request.method == 'GET':
            config = backend.config_manager.get_servo_config(channel)
            if config:
                config_data = {
                    "channel": config.channel,
                    "name": config.name,
                    "servo_type": config.servo_type.value,
                    "servo_range": config.servo_range.value,
                    "enabled": config.enabled,
                    "reverse": config.reverse,
                    "description": config.description,
                    "limits": {
                        "min_pulse_us": config.limits.min_pulse_us,
                        "max_pulse_us": config.limits.max_pulse_us,
                        "home_pulse_us": config.limits.home_pulse_us,
                        "max_speed": config.limits.max_speed,
                        "max_acceleration": config.limits.max_acceleration
                    }
                }
                return jsonify({"success": True, "data": config_data})
            else:
                return jsonify({"success": False, "error": "Servo not found"}), 404

        elif request.method == 'POST':
            data = request.get_json()
            success = backend.config_manager.update_servo_config(channel, **data)

            if success:
                return jsonify({"success": True, "data": {"channel": channel, "updated": True}})
            else:
                return jsonify({"success": False, "error": "Configuration update failed"}), 500

    except Exception as e:
        logger.error(f"Servo config error: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/sequence/<sequence_name>/play', methods=['POST'])
def play_sequence(sequence_name):
    """Play animation sequence"""
    backend.api_calls += 1
    backend.sequences_executed += 1

    if not backend.system_initialized:
        return jsonify({"success": False, "error": "System not initialized"}), 503

    try:
        data = request.get_json() or {}
        loop = data.get('loop', False)

        success = backend.sequencer.play_sequence(sequence_name, loop)

        if success:
            # Broadcast to connected clients
            socketio.emit('sequence_started', {
                'sequence_name': sequence_name,
                'loop': loop,
                'timestamp': time.time()
            })

            return jsonify({"success": True, "data": {"sequence": sequence_name, "started": True}})
        else:
            return jsonify({"success": False, "error": "Sequence not found or failed to start"}), 404

    except Exception as e:
        logger.error(f"Play sequence error: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/sequence/stop', methods=['POST'])
def stop_sequence():
    """Stop current sequence"""
    backend.api_calls += 1

    if not backend.system_initialized:
        return jsonify({"success": False, "error": "System not initialized"}), 503

    try:
        backend.sequencer.stop_sequence()

        # Broadcast to connected clients
        socketio.emit('sequence_stopped', {'timestamp': time.time()})

        return jsonify({"success": True, "data": {"stopped": True}})

    except Exception as e:
        logger.error(f"Stop sequence error: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/sequences', methods=['GET'])
def get_sequences():
    """Get available animation sequences"""
    backend.api_calls += 1

    if not backend.system_initialized:
        return jsonify({"success": False, "error": "System not initialized"}), 503

    try:
        sequences = backend.sequencer.get_available_sequences()
        sequence_info = []

        for seq_name in sequences:
            info = backend.sequencer.get_sequence_info(seq_name)
            if info:
                sequence_info.append(info)

        return jsonify({"success": True, "data": sequence_info})

    except Exception as e:
        logger.error(f"Get sequences error: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/emotion/<emotion>', methods=['POST'])
def set_emotion(emotion):
    """Set R2D2 emotional state and play appropriate sequence"""
    backend.api_calls += 1

    if not backend.system_initialized:
        return jsonify({"success": False, "error": "System not initialized"}), 503

    try:
        # Convert emotion string to enum
        emotion_map = {
            'excited': R2D2Emotion.EXCITED,
            'curious': R2D2Emotion.CURIOUS,
            'worried': R2D2Emotion.WORRIED,
            'frustrated': R2D2Emotion.FRUSTRATED,
            'neutral': R2D2Emotion.NEUTRAL,
            'playful': R2D2Emotion.PLAYFUL,
            'confident': R2D2Emotion.CONFIDENT
        }

        if emotion.lower() not in emotion_map:
            return jsonify({"success": False, "error": "Invalid emotion"}), 400

        r2d2_emotion = emotion_map[emotion.lower()]
        backend.sequencer.set_emotion(r2d2_emotion)
        success = backend.sequencer.play_emotion_sequence(r2d2_emotion)

        if success:
            # Broadcast to connected clients
            socketio.emit('emotion_changed', {
                'emotion': emotion,
                'timestamp': time.time()
            })

            return jsonify({"success": True, "data": {"emotion": emotion, "sequence_started": True}})
        else:
            return jsonify({"success": False, "error": "Failed to play emotion sequence"}), 500

    except Exception as e:
        logger.error(f"Set emotion error: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/emergency_stop', methods=['POST'])
def emergency_stop():
    """Execute emergency stop"""
    backend.api_calls += 1

    if not backend.system_initialized:
        return jsonify({"success": False, "error": "System not initialized"}), 503

    try:
        data = request.get_json() or {}
        reason = data.get('reason', 'API emergency stop request')

        backend.safety_system.emergency_stop('MANUAL', reason)

        # Broadcast emergency alert to all clients
        socketio.emit('emergency_stop', {
            'reason': reason,
            'timestamp': time.time()
        })

        return jsonify({"success": True, "data": {"emergency_stop": True, "reason": reason}})

    except Exception as e:
        logger.error(f"Emergency stop error: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/emergency_reset', methods=['POST'])
def emergency_reset():
    """Reset emergency stop"""
    backend.api_calls += 1

    if not backend.system_initialized:
        return jsonify({"success": False, "error": "System not initialized"}), 503

    try:
        data = request.get_json() or {}
        confirmation = data.get('confirmation', False)

        if not confirmation:
            return jsonify({"success": False, "error": "Operator confirmation required"}), 400

        success = backend.safety_system.reset_emergency_stop(operator_confirmation=True)

        if success:
            # Broadcast reset to all clients
            socketio.emit('emergency_reset', {'timestamp': time.time()})

            return jsonify({"success": True, "data": {"emergency_reset": True}})
        else:
            return jsonify({"success": False, "error": "Emergency reset failed"}), 500

    except Exception as e:
        logger.error(f"Emergency reset error: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/script/<script_name>/execute', methods=['POST'])
def execute_script(script_name):
    """Execute Maestro script"""
    backend.api_calls += 1

    if not backend.system_initialized:
        return jsonify({"success": False, "error": "System not initialized"}), 503

    try:
        data = request.get_json() or {}
        loop = data.get('loop', False)

        success = backend.script_engine.execute_script(script_name, loop)

        if success:
            # Broadcast to connected clients
            socketio.emit('script_started', {
                'script_name': script_name,
                'loop': loop,
                'timestamp': time.time()
            })

            return jsonify({"success": True, "data": {"script": script_name, "started": True}})
        else:
            return jsonify({"success": False, "error": "Script not found or failed to start"}), 404

    except Exception as e:
        logger.error(f"Execute script error: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/scripts', methods=['GET'])
def get_scripts():
    """Get available scripts"""
    backend.api_calls += 1

    if not backend.system_initialized:
        return jsonify({"success": False, "error": "System not initialized"}), 503

    try:
        scripts = backend.script_engine.get_script_library()
        script_info = []

        for script_name in scripts:
            info = backend.script_engine.get_script_info(script_name)
            if info:
                script_info.append(info)

        return jsonify({"success": True, "data": script_info})

    except Exception as e:
        logger.error(f"Get scripts error: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/r2d2/dome_rotation', methods=['POST'])
def r2d2_dome_rotation():
    """Control R2D2 dome rotation"""
    backend.api_calls += 1
    backend.servo_commands += 1

    if not backend.system_initialized:
        return jsonify({"success": False, "error": "System not initialized"}), 503

    try:
        data = request.get_json()
        angle = data.get('angle', 0.0)  # -180 to 180 degrees

        success = backend.r2d2_interface.dome_rotation(angle)

        if success:
            return jsonify({"success": True, "data": {"dome_angle": angle}})
        else:
            return jsonify({"success": False, "error": "Dome rotation failed"}), 500

    except Exception as e:
        logger.error(f"Dome rotation error: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/r2d2/panels', methods=['POST'])
def r2d2_panels():
    """Control R2D2 dome panels"""
    backend.api_calls += 1
    backend.servo_commands += 1

    if not backend.system_initialized:
        return jsonify({"success": False, "error": "System not initialized"}), 503

    try:
        data = request.get_json()
        front = data.get('front', False)
        left = data.get('left', False)
        right = data.get('right', False)
        back = data.get('back', False)

        success = backend.r2d2_interface.dome_panels(front, left, right, back)

        if success:
            return jsonify({"success": True, "data": {"panels": {"front": front, "left": left, "right": right, "back": back}}})
        else:
            return jsonify({"success": False, "error": "Panel control failed"}), 500

    except Exception as e:
        logger.error(f"Panel control error: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

# === WEBSOCKET EVENTS ===

@socketio.on('connect')
def handle_connect():
    """Handle client connection"""
    backend.connected_clients.add(request.sid)
    logger.info(f"Client connected: {request.sid}")

    # Send initial status
    status = backend.get_system_status()
    emit('system_status', status)

@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection"""
    backend.connected_clients.discard(request.sid)
    logger.info(f"Client disconnected: {request.sid}")

@socketio.on('heartbeat')
def handle_heartbeat():
    """Handle client heartbeat"""
    backend.last_heartbeat = time.time()
    emit('heartbeat_ack', {'timestamp': time.time()})

@socketio.on('request_status')
def handle_status_request():
    """Handle status request"""
    status = backend.get_system_status()
    emit('system_status', status)

# === ERROR HANDLERS ===

@app.errorhandler(404)
def not_found(error):
    return jsonify({"success": False, "error": "Endpoint not found"}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({"success": False, "error": "Internal server error"}), 500

# === HEALTH CHECK ===

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy" if backend.system_initialized else "initializing",
        "timestamp": time.time(),
        "uptime": time.time() - backend.system_start_time
    })

if __name__ == '__main__':
    logger.info("🚀 Starting R2D2 Servo API Backend...")
    logger.info("📡 Server will be available at http://localhost:5000")
    logger.info("🔌 WebSocket available at ws://localhost:5000")

    try:
        # Run the server
        socketio.run(app, host='0.0.0.0', port=5000, debug=False)
    except KeyboardInterrupt:
        logger.info("Server shutdown requested")
    except Exception as e:
        logger.error(f"Server error: {e}")
    finally:
        # Cleanup
        if backend.system_initialized:
            if backend.safety_system:
                backend.safety_system.stop_safety_monitoring()
            if backend.sequencer:
                backend.sequencer.stop_sequence()
            if backend.script_engine:
                backend.script_engine.stop_execution()
            if backend.controller:
                backend.controller.shutdown()

        logger.info("✅ R2D2 Servo API Backend shutdown complete")