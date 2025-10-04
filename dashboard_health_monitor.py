#!/usr/bin/env python3
"""
R2D2 Dashboard Health Monitor - Quality Gate System
Prevents video feed breakage by monitoring and auto-recovering services
"""

import asyncio
import websockets
import json
import time
import subprocess
import logging
import os
import signal
import sys
from datetime import datetime
from typing import Dict, List, Optional

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class DashboardHealthMonitor:
    """Monitors dashboard services and prevents video feed breakage"""

    def __init__(self):
        self.running = False
        self.required_services = {
            'dashboard_server': {'port': 8765, 'process': None, 'status': 'stopped'},
            'vision_system': {'port': 8767, 'process': None, 'status': 'stopped'},
            'websocket_server': {'port': 8766, 'process': None, 'status': 'stopped'}
        }

        # Health check intervals
        self.check_interval = 30  # seconds
        self.recovery_timeout = 10  # seconds

        # Recovery strategies
        self.recovery_attempts = 0
        self.max_recovery_attempts = 3

        # Quality gates
        self.quality_checks = {
            'video_frame_received': False,
            'websocket_responsive': False,
            'dashboard_accessible': False,
            'services_running': False
        }

    def check_port_availability(self, port: int) -> bool:
        """Check if a port is in use"""
        try:
            result = subprocess.run(['netstat', '-tlnp'], capture_output=True, text=True)
            return f":{port}" in result.stdout
        except Exception as e:
            logger.error(f"Port check failed: {e}")
            return False

    async def test_video_feed(self) -> bool:
        """Test video feed connectivity (quality gate)"""
        try:
            uri = "ws://localhost:8767"
            async with websockets.connect(uri, timeout=5) as websocket:
                # Wait for frame data
                message = await asyncio.wait_for(websocket.recv(), timeout=10)
                data = json.loads(message)

                # Handle connection status
                if data.get('type') == 'connection_status':
                    message = await asyncio.wait_for(websocket.recv(), timeout=10)
                    data = json.loads(message)

                # Check for valid frame data
                if data.get('type') == 'vision_data' and 'frame' in data:
                    self.quality_checks['video_frame_received'] = True
                    return True

        except Exception as e:
            logger.warning(f"Video feed test failed: {e}")
            self.quality_checks['video_frame_received'] = False

        return False

    async def test_dashboard_websocket(self) -> bool:
        """Test dashboard WebSocket connectivity (quality gate)"""
        try:
            uri = "ws://localhost:8766"
            async with websockets.connect(uri, timeout=5) as websocket:
                test_message = {"type": "health_check"}
                await websocket.send(json.dumps(test_message))

                response = await asyncio.wait_for(websocket.recv(), timeout=5)
                self.quality_checks['websocket_responsive'] = True
                return True

        except Exception as e:
            logger.warning(f"Dashboard WebSocket test failed: {e}")
            self.quality_checks['websocket_responsive'] = False

        return False

    def test_dashboard_http(self) -> bool:
        """Test dashboard HTTP accessibility (quality gate)"""
        try:
            import urllib.request
            response = urllib.request.urlopen("http://localhost:8765", timeout=5)
            self.quality_checks['dashboard_accessible'] = (response.getcode() == 200)
            return self.quality_checks['dashboard_accessible']
        except Exception as e:
            logger.warning(f"Dashboard HTTP test failed: {e}")
            self.quality_checks['dashboard_accessible'] = False
            return False

    def start_dashboard_server(self) -> bool:
        """Start dashboard server with monitoring"""
        try:
            logger.info("Starting dashboard server...")

            # Kill any existing processes
            subprocess.run(['pkill', '-f', 'dashboard-server.js'], capture_output=True)
            time.sleep(2)

            # Start new process
            cmd = ['nohup', 'node', 'dashboard-server.js']
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd='/home/rolo/r2ai',
                preexec_fn=os.setsid
            )

            # Give it time to start
            time.sleep(3)

            # Verify it's running
            if self.check_port_availability(8765):
                self.required_services['dashboard_server']['process'] = process
                self.required_services['dashboard_server']['status'] = 'running'
                logger.info("✅ Dashboard server started successfully")
                return True
            else:
                logger.error("❌ Dashboard server failed to start")
                return False

        except Exception as e:
            logger.error(f"Dashboard server start failed: {e}")
            return False

    def start_vision_system(self) -> bool:
        """Start vision system with fallback to simulated camera"""
        try:
            logger.info("Starting vision system...")

            # Kill any existing vision processes
            subprocess.run(['pkill', '-f', 'vision.py'], capture_output=True)
            time.sleep(2)

            # Try real camera first, fallback to simulated
            vision_scripts = [
                'r2d2_realtime_vision.py',      # Real camera
                'simulated_camera_vision.py'    # Fallback
            ]

            for script in vision_scripts:
                try:
                    logger.info(f"Attempting to start {script}...")

                    cmd = ['python3', script]
                    process = subprocess.Popen(
                        cmd,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        cwd='/home/rolo/r2ai',
                        preexec_fn=os.setsid
                    )

                    # Give it time to start
                    time.sleep(5)

                    # Test if it's working
                    if self.check_port_availability(8767):
                        self.required_services['vision_system']['process'] = process
                        self.required_services['vision_system']['status'] = 'running'
                        logger.info(f"✅ Vision system started with {script}")
                        return True

                except Exception as e:
                    logger.warning(f"Failed to start {script}: {e}")
                    continue

            logger.error("❌ All vision system attempts failed")
            return False

        except Exception as e:
            logger.error(f"Vision system start failed: {e}")
            return False

    async def recover_services(self) -> bool:
        """Attempt to recover failed services"""
        logger.warning("🔄 Attempting service recovery...")

        self.recovery_attempts += 1
        if self.recovery_attempts > self.max_recovery_attempts:
            logger.error(f"❌ Maximum recovery attempts ({self.max_recovery_attempts}) exceeded")
            return False

        recovery_success = True

        # Check and recover dashboard server
        if not self.check_port_availability(8765):
            logger.warning("Dashboard server down, attempting restart...")
            if not self.start_dashboard_server():
                recovery_success = False

        # Check and recover vision system
        if not self.check_port_availability(8767):
            logger.warning("Vision system down, attempting restart...")
            if not self.start_vision_system():
                recovery_success = False

        # Wait for services to stabilize
        if recovery_success:
            logger.info("⏳ Waiting for services to stabilize...")
            await asyncio.sleep(5)

            # Verify recovery with quality checks
            video_ok = await self.test_video_feed()
            websocket_ok = await self.test_dashboard_websocket()
            http_ok = self.test_dashboard_http()

            if video_ok and websocket_ok and http_ok:
                logger.info("✅ Service recovery successful!")
                self.recovery_attempts = 0  # Reset counter on success
                return True
            else:
                logger.error("❌ Service recovery verification failed")
                return False

        return False

    async def health_check_loop(self):
        """Main health monitoring loop"""
        logger.info("🏥 Starting dashboard health monitoring...")

        while self.running:
            try:
                logger.info("🔍 Performing health check...")

                # Quality Gate 1: Services running
                services_ok = (
                    self.check_port_availability(8765) and
                    self.check_port_availability(8766) and
                    self.check_port_availability(8767)
                )
                self.quality_checks['services_running'] = services_ok

                # Quality Gate 2: Video feed functional
                video_ok = await self.test_video_feed()

                # Quality Gate 3: WebSocket responsive
                websocket_ok = await self.test_dashboard_websocket()

                # Quality Gate 4: Dashboard accessible
                http_ok = self.test_dashboard_http()

                # Overall health assessment
                all_checks_passed = all(self.quality_checks.values())

                if all_checks_passed:
                    logger.info("✅ All quality gates passed - system healthy")
                else:
                    failed_checks = [k for k, v in self.quality_checks.items() if not v]
                    logger.warning(f"❌ Quality gate failures: {failed_checks}")

                    # Attempt recovery
                    recovery_success = await self.recover_services()
                    if not recovery_success:
                        logger.error("❌ Recovery failed - manual intervention required")

                # Log current status
                status_report = {
                    'timestamp': datetime.now().isoformat(),
                    'quality_checks': self.quality_checks,
                    'services': {k: v['status'] for k, v in self.required_services.items()},
                    'recovery_attempts': self.recovery_attempts
                }

                logger.info(f"📊 Health Report: {json.dumps(status_report, indent=2)}")

                # Wait before next check
                await asyncio.sleep(self.check_interval)

            except Exception as e:
                logger.error(f"Health check error: {e}")
                await asyncio.sleep(self.check_interval)

    def start_monitoring(self):
        """Start the health monitoring system"""
        self.running = True

        # Signal handlers for graceful shutdown
        def signal_handler(signum, frame):
            logger.info("🛑 Shutdown signal received")
            self.running = False
            sys.exit(0)

        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

        # Run monitoring loop
        asyncio.run(self.health_check_loop())

if __name__ == "__main__":
    monitor = DashboardHealthMonitor()

    # Initial startup
    logger.info("🚀 R2D2 Dashboard Health Monitor Starting...")

    # Start required services
    monitor.start_dashboard_server()
    monitor.start_vision_system()

    # Begin monitoring
    monitor.start_monitoring()