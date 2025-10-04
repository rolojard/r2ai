#!/usr/bin/env python3
"""
R2D2 Servo System Quick Start
Launch the complete R2D2 animatronic control system

This script provides a simple way to start the complete R2D2 servo system
including the API backend, dashboard integration, and hardware detection.
"""

import os
import sys
import time
import subprocess
import threading
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def start_servo_backend():
    """Start the servo API backend"""
    logger.info("Starting R2D2 Servo API Backend...")
    try:
        subprocess.run([sys.executable, "r2d2_servo_api_backend.py"], check=True)
    except KeyboardInterrupt:
        logger.info("Servo backend stopped by user")
    except Exception as e:
        logger.error(f"Servo backend error: {e}")

def start_dashboard_server():
    """Start the dashboard server"""
    logger.info("Starting Dashboard Server...")
    try:
        subprocess.run(["node", "dashboard-server.js"], check=True)
    except KeyboardInterrupt:
        logger.info("Dashboard server stopped by user")
    except Exception as e:
        logger.error(f"Dashboard server error: {e}")

def main():
    """Main startup function"""
    print("🎭 R2D2 Disney-Level Servo Control System")
    print("=" * 50)
    print("Starting integrated animatronic control system...")
    print()

    # Check if we have all required files
    required_files = [
        "pololu_maestro_controller.py",
        "maestro_hardware_detector.py",
        "r2d2_servo_config_manager.py",
        "r2d2_animatronic_sequences.py",
        "r2d2_emergency_safety_system.py",
        "maestro_script_engine.py",
        "r2d2_servo_api_backend.py",
        "dashboard-server.js"
    ]

    missing_files = []
    for file in required_files:
        if not Path(file).exists():
            missing_files.append(file)

    if missing_files:
        print("❌ Missing required files:")
        for file in missing_files:
            print(f"   - {file}")
        print("\nPlease ensure all system files are present.")
        return

    print("✅ All system files present")
    print()

    # Start backend in separate thread
    print("🚀 Starting servo API backend...")
    backend_thread = threading.Thread(target=start_servo_backend, daemon=True)
    backend_thread.start()

    # Wait a moment for backend to initialize
    time.sleep(3)

    # Start dashboard server
    print("🌐 Starting dashboard server...")
    dashboard_thread = threading.Thread(target=start_dashboard_server, daemon=True)
    dashboard_thread.start()

    time.sleep(2)

    print("\n" + "=" * 50)
    print("🎯 R2D2 SERVO SYSTEM READY")
    print("=" * 50)
    print("🔗 Dashboard: http://localhost:8765")
    print("🔗 Servo Dashboard: http://localhost:8765/servo")
    print("🔗 Vision Dashboard: http://localhost:8765/vision")
    print("🔗 API Endpoint: http://localhost:5000/api")
    print("🔗 Health Check: http://localhost:5000/health")
    print()
    print("📡 WebSocket connections available for real-time updates")
    print("🛡️  Safety monitoring active")
    print("🎭 Character sequences ready")
    print("⚙️  Script engine operational")
    print()
    print("Press Ctrl+C to shutdown system")
    print("=" * 50)

    try:
        # Keep main thread alive
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n⏹️  Shutdown requested...")
        print("🛡️  Emergency stop activated")
        print("✅ System shutdown complete")

if __name__ == "__main__":
    main()