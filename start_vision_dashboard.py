#!/usr/bin/env python3
"""
R2D2 Vision Dashboard Launcher
Starts both the dashboard server and vision system for real-time monitoring
"""

import subprocess
import time
import signal
import sys
import os
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class VisionDashboardLauncher:
    """Manages the startup and coordination of dashboard and vision systems"""

    def __init__(self):
        self.dashboard_process = None
        self.vision_process = None
        self.running = True

    def start_dashboard_server(self):
        """Start the Node.js dashboard server"""
        try:
            logger.info("Starting dashboard server...")

            # Change to the correct directory
            dashboard_script = Path("/home/rolo/r2ai/dashboard-server.js")

            if not dashboard_script.exists():
                logger.error(f"Dashboard server script not found: {dashboard_script}")
                return False

            # Start dashboard server
            self.dashboard_process = subprocess.Popen(
                ["node", str(dashboard_script)],
                cwd="/home/rolo/r2ai",
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True
            )

            # Give it a moment to start
            time.sleep(2)

            # Check if it's still running
            if self.dashboard_process.poll() is None:
                logger.info("✅ Dashboard server started successfully on port 8765")
                return True
            else:
                stdout, stderr = self.dashboard_process.communicate()
                logger.error(f"❌ Dashboard server failed to start")
                logger.error(f"STDOUT: {stdout}")
                logger.error(f"STDERR: {stderr}")
                return False

        except Exception as e:
            logger.error(f"Failed to start dashboard server: {e}")
            return False

    def start_vision_system(self):
        """Start the Python vision system"""
        try:
            logger.info("Starting vision system...")

            vision_script = Path("/home/rolo/r2ai/r2d2_realtime_vision.py")

            if not vision_script.exists():
                logger.error(f"Vision system script not found: {vision_script}")
                return False

            # Start vision system
            self.vision_process = subprocess.Popen(
                ["python3", str(vision_script)],
                cwd="/home/rolo/r2ai",
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True
            )

            # Give it a moment to start
            time.sleep(3)

            # Check if it's still running
            if self.vision_process.poll() is None:
                logger.info("✅ Vision system started successfully on port 8767")
                return True
            else:
                stdout, stderr = self.vision_process.communicate()
                logger.error(f"❌ Vision system failed to start")
                logger.error(f"STDOUT: {stdout}")
                logger.error(f"STDERR: {stderr}")
                return False

        except Exception as e:
            logger.error(f"Failed to start vision system: {e}")
            return False

    def check_dependencies(self):
        """Check if required dependencies are available"""
        logger.info("Checking system dependencies...")

        # Check Node.js
        try:
            result = subprocess.run(["node", "--version"], capture_output=True, text=True)
            if result.returncode == 0:
                logger.info(f"✅ Node.js available: {result.stdout.strip()}")
            else:
                logger.error("❌ Node.js not found")
                return False
        except FileNotFoundError:
            logger.error("❌ Node.js not found")
            return False

        # Check Python packages
        try:
            import cv2
            logger.info(f"✅ OpenCV available: {cv2.__version__}")
        except ImportError:
            logger.error("❌ OpenCV not available")
            return False

        try:
            import torch
            logger.info(f"✅ PyTorch available: {torch.__version__}")
            if torch.cuda.is_available():
                logger.info(f"✅ CUDA available: {torch.version.cuda}")
            else:
                logger.warning("⚠️ CUDA not available - using CPU")
        except ImportError:
            logger.error("❌ PyTorch not available")
            return False

        try:
            from ultralytics import YOLO
            import ultralytics
            logger.info(f"✅ Ultralytics YOLO available: {ultralytics.__version__}")
        except ImportError:
            logger.error("❌ Ultralytics YOLO not available")
            return False

        try:
            import websockets
            logger.info("✅ WebSockets library available")
        except ImportError:
            logger.error("❌ WebSockets library not available")
            return False

        return True

    def check_camera(self):
        """Check if camera is accessible"""
        try:
            import cv2
            cap = cv2.VideoCapture(0)
            if cap.isOpened():
                ret, frame = cap.read()
                cap.release()
                if ret:
                    logger.info("✅ Camera accessible")
                    return True
                else:
                    logger.warning("⚠️ Camera accessible but cannot capture frames")
                    return False
            else:
                logger.warning("⚠️ Camera not accessible")
                return False
        except Exception as e:
            logger.error(f"❌ Camera check failed: {e}")
            return False

    def setup_signal_handlers(self):
        """Setup signal handlers for graceful shutdown"""
        def signal_handler(sig, frame):
            logger.info("Received shutdown signal...")
            self.shutdown()
            sys.exit(0)

        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

    def shutdown(self):
        """Gracefully shutdown all processes"""
        logger.info("Shutting down R2D2 Vision Dashboard...")

        if self.vision_process and self.vision_process.poll() is None:
            logger.info("Stopping vision system...")
            self.vision_process.terminate()
            try:
                self.vision_process.wait(timeout=5)
                logger.info("✅ Vision system stopped")
            except subprocess.TimeoutExpired:
                logger.warning("Vision system didn't stop gracefully, forcing...")
                self.vision_process.kill()

        if self.dashboard_process and self.dashboard_process.poll() is None:
            logger.info("Stopping dashboard server...")
            self.dashboard_process.terminate()
            try:
                self.dashboard_process.wait(timeout=5)
                logger.info("✅ Dashboard server stopped")
            except subprocess.TimeoutExpired:
                logger.warning("Dashboard server didn't stop gracefully, forcing...")
                self.dashboard_process.kill()

        self.running = False

    def monitor_processes(self):
        """Monitor running processes and restart if needed"""
        while self.running:
            try:
                # Check dashboard process
                if self.dashboard_process and self.dashboard_process.poll() is not None:
                    logger.warning("Dashboard server stopped unexpectedly, restarting...")
                    if not self.start_dashboard_server():
                        logger.error("Failed to restart dashboard server")
                        break

                # Check vision process
                if self.vision_process and self.vision_process.poll() is not None:
                    logger.warning("Vision system stopped unexpectedly, restarting...")
                    if not self.start_vision_system():
                        logger.error("Failed to restart vision system")
                        # Continue without vision system

                time.sleep(5)  # Check every 5 seconds

            except KeyboardInterrupt:
                break
            except Exception as e:
                logger.error(f"Process monitoring error: {e}")

    def run(self):
        """Main run method"""
        logger.info("🎯 Starting R2D2 Vision Dashboard System")
        logger.info("=" * 50)

        # Setup signal handlers
        self.setup_signal_handlers()

        # Check dependencies
        if not self.check_dependencies():
            logger.error("❌ Dependency check failed")
            return False

        # Check camera (optional)
        camera_available = self.check_camera()
        if not camera_available:
            logger.warning("⚠️ Camera not available - vision system may not work properly")

        logger.info("=" * 50)

        # Start dashboard server
        if not self.start_dashboard_server():
            logger.error("❌ Failed to start dashboard server")
            return False

        # Start vision system
        if not self.start_vision_system():
            logger.error("❌ Failed to start vision system")
            logger.info("🌐 Dashboard will still be available without vision")

        logger.info("=" * 50)
        logger.info("🎯 R2D2 Vision Dashboard System Ready!")
        logger.info("📊 Dashboard: http://localhost:8765")
        logger.info("👁️ Vision WebSocket: ws://localhost:8767")
        logger.info("🎮 WebSocket API: ws://localhost:8766")
        logger.info("=" * 50)
        logger.info("Press Ctrl+C to stop all systems")
        logger.info("=" * 50)

        try:
            # Monitor processes
            self.monitor_processes()
        except KeyboardInterrupt:
            logger.info("Shutdown requested by user")
        finally:
            self.shutdown()

        return True

def main():
    """Main entry point"""
    launcher = VisionDashboardLauncher()

    try:
        success = launcher.run()
        sys.exit(0 if success else 1)
    except Exception as e:
        logger.error(f"Launcher failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()