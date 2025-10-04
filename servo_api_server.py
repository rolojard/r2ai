#!/usr/bin/env python3
"""
R2D2 Servo API Server
====================

Flask-based API server for controlling the Enhanced Maestro Controller.
Provides REST API and WebSocket endpoints for real-time servo control.

Author: Expert Project Manager + Super Coder Agent
"""

import os
import sys
import time
import json
import logging
import threading
from datetime import datetime
from flask import Flask, request, jsonify
from flask_cors import CORS

# Import our enhanced servo controller
sys.path.append('/home/rolo/r2ai')
from maestro_enhanced_controller import EnhancedMaestroController

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Flask application
app = Flask(__name__)
CORS(app)

# Global controller instance
controller = None
controller_lock = threading.Lock()

def initialize_controller():
    """Initialize the Enhanced Maestro Controller"""
    global controller

    try:
        with controller_lock:
            if controller is None:
                logger.info("Initializing Enhanced Maestro Controller...")
                controller = EnhancedMaestroController(auto_detect=True)
                logger.info("✅ Enhanced Maestro Controller initialized")
            return True
    except Exception as e:
        logger.error(f"Failed to initialize controller: {e}")
        return False

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat()
    })

@app.route('/api/status', methods=['GET'])
def get_system_status():
    """Get comprehensive system status"""
    try:
        if not controller:
            return jsonify({'error': 'Controller not initialized'}), 500

        with controller_lock:
            status_report = controller.get_enhanced_status_report()

        return jsonify({
            'success': True,
            'data': status_report,
            'timestamp': datetime.now().isoformat()
        })

    except Exception as e:
        logger.error(f"Error getting system status: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/servos', methods=['GET'])
def get_servo_configs():
    """Get all servo configurations"""
    try:
        if not controller:
            return jsonify({'error': 'Controller not initialized'}), 500

        with controller_lock:
            configs = []
            for channel, config in controller.dynamic_configs.items():
                configs.append({
                    'channel': config.channel,
                    'name': config.name,
                    'display_name': config.display_name,
                    'min_position': config.min_position,
                    'max_position': config.max_position,
                    'home_position': config.home_position,
                    'enabled': config.enabled
                })

        return jsonify({
            'success': True,
            'data': configs,
            'count': len(configs)
        })

    except Exception as e:
        logger.error(f"Error getting servo configs: {e}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    logger.info("🚀 Starting R2D2 Servo API Server...")
    initialize_controller()
    app.run(host='0.0.0.0', port=5000, debug=False)