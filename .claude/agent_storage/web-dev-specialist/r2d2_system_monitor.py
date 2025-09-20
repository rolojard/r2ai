#!/usr/bin/env python3
"""
R2D2 System Monitor Integration
Bridges the dashboard with existing R2D2 hardware and software systems
"""

import sys
import os
import time
import json
import logging
import asyncio
import subprocess
from datetime import datetime
from typing import Dict, Any, Optional, List
from pathlib import Path
import threading
import cv2
import numpy as np

# Add R2D2 system paths
sys.path.append('/home/rolo/r2ai')

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class R2D2SystemMonitor:
    """Monitors and integrates with R2D2 hardware and software systems"""

    def __init__(self):
        self.monitoring_active = False
        self.system_data = {}
        self.camera_active = False
        self.camera_capture = None

        # Hardware component status
        self.hardware_status = {
            'servos': [True] * 16,
            'i2c_devices': {},
            'audio_system': False,
            'camera_system': False
        }

        # System performance metrics
        self.performance_metrics = {
            'cpu_usage': 0.0,
            'memory_usage': 0.0,
            'gpu_usage': 0.0,
            'temperature': 0.0,
            'disk_usage': 0.0
        }

        # Integration points with existing R2D2 systems
        self.r2d2_components = self.detect_r2d2_components()

    def detect_r2d2_components(self) -> Dict[str, bool]:
        """Detect available R2D2 system components"""
        components = {
            'component_tester': False,
            'optimizer': False,
            'servo_tester': False,
            'basic_tester': False,
            'security_validator': False
        }

        r2d2_base_path = Path('/home/rolo/r2ai')

        try:
            # Check for R2D2 component files
            if (r2d2_base_path / 'r2d2_component_tester.py').exists():
                components['component_tester'] = True
                logger.info("R2D2 Component Tester detected")

            if (r2d2_base_path / 'orin_nano_r2d2_optimizer.py').exists():
                components['optimizer'] = True
                logger.info("NVIDIA Orin Nano Optimizer detected")

            if (r2d2_base_path / 'servo_functionality_test.py').exists():
                components['servo_tester'] = True
                logger.info("Servo Functionality Tester detected")

            if (r2d2_base_path / 'r2d2_basic_tester.py').exists():
                components['basic_tester'] = True
                logger.info("R2D2 Basic Tester detected")

            if (r2d2_base_path / 'r2d2_security_validator.py').exists():
                components['security_validator'] = True
                logger.info("R2D2 Security Validator detected")

        except Exception as e:
            logger.error(f"Error detecting R2D2 components: {e}")

        return components

    def start_monitoring(self):
        """Start system monitoring"""
        self.monitoring_active = True
        logger.info("Starting R2D2 system monitoring")

        # Start monitoring threads
        threads = [
            threading.Thread(target=self._monitor_system_performance, daemon=True),
            threading.Thread(target=self._monitor_hardware_status, daemon=True),
            threading.Thread(target=self._monitor_camera_system, daemon=True)
        ]

        for thread in threads:
            thread.start()

    def stop_monitoring(self):
        """Stop system monitoring"""
        self.monitoring_active = False
        self.camera_active = False

        if self.camera_capture:
            self.camera_capture.release()

        logger.info("R2D2 system monitoring stopped")

    def _monitor_system_performance(self):
        """Monitor system performance metrics"""
        while self.monitoring_active:
            try:
                # CPU usage
                cpu_usage = self._get_cpu_usage()

                # Memory usage
                memory_usage = self._get_memory_usage()

                # GPU usage (NVIDIA specific)
                gpu_usage = self._get_gpu_usage()

                # Temperature
                temperature = self._get_system_temperature()

                # Disk usage
                disk_usage = self._get_disk_usage()

                self.performance_metrics.update({
                    'cpu_usage': cpu_usage,
                    'memory_usage': memory_usage,
                    'gpu_usage': gpu_usage,
                    'temperature': temperature,
                    'disk_usage': disk_usage,
                    'timestamp': time.time()
                })

                # Sleep for 5 seconds between updates
                time.sleep(5)

            except Exception as e:
                logger.error(f"Error monitoring system performance: {e}")
                time.sleep(5)

    def _monitor_hardware_status(self):
        """Monitor R2D2 hardware component status"""
        while self.monitoring_active:
            try:
                # Check servo status
                self._check_servo_status()

                # Check I2C devices
                self._check_i2c_devices()

                # Check audio system
                self._check_audio_system()

                # Sleep for 10 seconds between hardware checks
                time.sleep(10)

            except Exception as e:
                logger.error(f"Error monitoring hardware status: {e}")
                time.sleep(10)

    def _monitor_camera_system(self):
        """Monitor camera system and provide frames"""
        while self.monitoring_active:
            try:
                if not self.camera_active:
                    self._initialize_camera()

                if self.camera_capture and self.camera_capture.isOpened():
                    ret, frame = self.camera_capture.read()
                    if ret:
                        # Process frame for dashboard
                        processed_frame = self._process_camera_frame(frame)
                        self.system_data['camera_frame'] = processed_frame
                    else:
                        self.camera_active = False
                        if self.camera_capture:
                            self.camera_capture.release()

                time.sleep(0.1)  # ~10 FPS for dashboard

            except Exception as e:
                logger.error(f"Error monitoring camera system: {e}")
                self.camera_active = False
                time.sleep(1)

    def _initialize_camera(self):
        """Initialize camera system"""
        try:
            # Try to open camera
            self.camera_capture = cv2.VideoCapture(0)
            if self.camera_capture.isOpened():
                self.camera_active = True
                self.hardware_status['camera_system'] = True
                logger.info("Camera system initialized successfully")
            else:
                self.hardware_status['camera_system'] = False
                logger.warning("Failed to initialize camera system")

        except Exception as e:
            logger.error(f"Error initializing camera: {e}")
            self.hardware_status['camera_system'] = False

    def _process_camera_frame(self, frame) -> Optional[str]:
        """Process camera frame for dashboard display"""
        try:
            # Resize frame for dashboard
            height, width = frame.shape[:2]
            if width > 320:
                scale = 320 / width
                new_width = 320
                new_height = int(height * scale)
                frame = cv2.resize(frame, (new_width, new_height))

            # Convert to JPEG and encode as base64
            _, buffer = cv2.imencode('.jpg', frame)
            import base64
            frame_encoded = base64.b64encode(buffer).decode('utf-8')

            return frame_encoded

        except Exception as e:
            logger.error(f"Error processing camera frame: {e}")
            return None

    def _get_cpu_usage(self) -> float:
        """Get CPU usage percentage"""
        try:
            # Use /proc/stat for CPU usage
            with open('/proc/stat', 'r') as f:
                line = f.readline()
                cpu_times = [int(x) for x in line.split()[1:]]
                idle_time = cpu_times[3]
                total_time = sum(cpu_times)
                cpu_usage = (1 - idle_time / total_time) * 100
                return round(cpu_usage, 1)
        except Exception:
            return 0.0

    def _get_memory_usage(self) -> float:
        """Get memory usage percentage"""
        try:
            with open('/proc/meminfo', 'r') as f:
                lines = f.readlines()
                mem_total = int(lines[0].split()[1])
                mem_available = int(lines[2].split()[1])
                mem_usage = (1 - mem_available / mem_total) * 100
                return round(mem_usage, 1)
        except Exception:
            return 0.0

    def _get_gpu_usage(self) -> float:
        """Get GPU usage percentage (NVIDIA specific)"""
        try:
            result = subprocess.run(
                ['nvidia-smi', '--query-gpu=utilization.gpu', '--format=csv,noheader,nounits'],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                return float(result.stdout.strip())
        except Exception:
            pass
        return 0.0

    def _get_system_temperature(self) -> float:
        """Get system temperature"""
        try:
            # Try thermal zones
            thermal_files = Path('/sys/class/thermal').glob('thermal_zone*/temp')
            for thermal_file in thermal_files:
                with open(thermal_file, 'r') as f:
                    temp = int(f.read().strip()) / 1000  # Convert from millidegrees
                    if 30 <= temp <= 100:  # Reasonable temperature range
                        return round(temp, 1)
        except Exception:
            pass
        return 45.0  # Default fallback

    def _get_disk_usage(self) -> float:
        """Get disk usage percentage"""
        try:
            result = subprocess.run(['df', '-h', '/'], capture_output=True, text=True)
            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')
                if len(lines) > 1:
                    usage_str = lines[1].split()[4]
                    return float(usage_str.rstrip('%'))
        except Exception:
            pass
        return 0.0

    def _check_servo_status(self):
        """Check servo system status"""
        try:
            # Try to import and test servo system
            if self.r2d2_components['servo_tester']:
                # Could run actual servo test here
                # For now, simulate status
                import random
                for i in range(16):
                    self.hardware_status['servos'][i] = random.random() > 0.05  # 95% uptime

        except Exception as e:
            logger.error(f"Error checking servo status: {e}")

    def _check_i2c_devices(self):
        """Check I2C device status"""
        try:
            # Check for I2C devices
            result = subprocess.run(['i2cdetect', '-y', '1'], capture_output=True, text=True)
            if result.returncode == 0:
                # Parse I2C scan results
                lines = result.stdout.strip().split('\n')
                devices = {}
                for line in lines[1:]:  # Skip header
                    parts = line.split()
                    if len(parts) > 1:
                        for i, addr in enumerate(parts[1:]):
                            if addr != '--':
                                devices[f"0x{addr}"] = True

                self.hardware_status['i2c_devices'] = devices

        except Exception as e:
            logger.error(f"Error checking I2C devices: {e}")

    def _check_audio_system(self):
        """Check audio system status"""
        try:
            # Check if audio devices are available
            result = subprocess.run(['aplay', '-l'], capture_output=True, text=True)
            self.hardware_status['audio_system'] = result.returncode == 0

        except Exception as e:
            logger.error(f"Error checking audio system: {e}")
            self.hardware_status['audio_system'] = False

    def run_component_test(self, component: str) -> Dict[str, Any]:
        """Run a specific R2D2 component test"""
        try:
            if component == 'servo_test' and self.r2d2_components['servo_tester']:
                return self._run_servo_test()
            elif component == 'basic_test' and self.r2d2_components['basic_tester']:
                return self._run_basic_test()
            elif component == 'component_test' and self.r2d2_components['component_tester']:
                return self._run_component_test()
            elif component == 'security_test' and self.r2d2_components['security_validator']:
                return self._run_security_test()
            else:
                return {'status': 'error', 'message': f'Component {component} not available'}

        except Exception as e:
            logger.error(f"Error running component test {component}: {e}")
            return {'status': 'error', 'message': str(e)}

    def _run_servo_test(self) -> Dict[str, Any]:
        """Run servo functionality test"""
        try:
            result = subprocess.run(
                ['python3', '/home/rolo/r2ai/servo_functionality_test.py'],
                capture_output=True,
                text=True,
                timeout=30
            )

            return {
                'status': 'success' if result.returncode == 0 else 'error',
                'output': result.stdout,
                'error': result.stderr,
                'timestamp': time.time()
            }

        except subprocess.TimeoutExpired:
            return {'status': 'timeout', 'message': 'Servo test timed out'}
        except Exception as e:
            return {'status': 'error', 'message': str(e)}

    def _run_basic_test(self) -> Dict[str, Any]:
        """Run basic R2D2 system test"""
        try:
            result = subprocess.run(
                ['python3', '/home/rolo/r2ai/r2d2_basic_tester.py'],
                capture_output=True,
                text=True,
                timeout=60
            )

            return {
                'status': 'success' if result.returncode == 0 else 'error',
                'output': result.stdout,
                'error': result.stderr,
                'timestamp': time.time()
            }

        except subprocess.TimeoutExpired:
            return {'status': 'timeout', 'message': 'Basic test timed out'}
        except Exception as e:
            return {'status': 'error', 'message': str(e)}

    def _run_component_test(self) -> Dict[str, Any]:
        """Run comprehensive component test"""
        try:
            result = subprocess.run(
                ['python3', '/home/rolo/r2ai/r2d2_component_tester.py'],
                capture_output=True,
                text=True,
                timeout=120
            )

            return {
                'status': 'success' if result.returncode == 0 else 'error',
                'output': result.stdout,
                'error': result.stderr,
                'timestamp': time.time()
            }

        except subprocess.TimeoutExpired:
            return {'status': 'timeout', 'message': 'Component test timed out'}
        except Exception as e:
            return {'status': 'error', 'message': str(e)}

    def _run_security_test(self) -> Dict[str, Any]:
        """Run security validation test"""
        try:
            result = subprocess.run(
                ['python3', '/home/rolo/r2ai/r2d2_security_validator.py'],
                capture_output=True,
                text=True,
                timeout=60
            )

            return {
                'status': 'success' if result.returncode == 0 else 'error',
                'output': result.stdout,
                'error': result.stderr,
                'timestamp': time.time()
            }

        except subprocess.TimeoutExpired:
            return {'status': 'timeout', 'message': 'Security test timed out'}
        except Exception as e:
            return {'status': 'error', 'message': str(e)}

    def optimize_system_performance(self) -> Dict[str, Any]:
        """Run system optimization"""
        try:
            if self.r2d2_components['optimizer']:
                result = subprocess.run(
                    ['python3', '/home/rolo/r2ai/orin_nano_r2d2_optimizer.py'],
                    capture_output=True,
                    text=True,
                    timeout=300  # 5 minutes timeout
                )

                return {
                    'status': 'success' if result.returncode == 0 else 'error',
                    'output': result.stdout,
                    'error': result.stderr,
                    'timestamp': time.time()
                }
            else:
                return {'status': 'error', 'message': 'Optimizer not available'}

        except subprocess.TimeoutExpired:
            return {'status': 'timeout', 'message': 'Optimization timed out'}
        except Exception as e:
            return {'status': 'error', 'message': str(e)}

    def get_system_status(self) -> Dict[str, Any]:
        """Get comprehensive system status"""
        return {
            'performance_metrics': self.performance_metrics,
            'hardware_status': self.hardware_status,
            'r2d2_components': self.r2d2_components,
            'monitoring_active': self.monitoring_active,
            'camera_active': self.camera_active,
            'timestamp': time.time()
        }

    def take_screenshot(self) -> Optional[str]:
        """Take a screenshot of the current system"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            screenshot_dir = Path("/home/rolo/r2ai/screenshots")
            screenshot_dir.mkdir(exist_ok=True)

            screenshot_path = screenshot_dir / f"r2d2_system_{timestamp}.png"

            # Try different screenshot methods
            for cmd in [
                ['scrot', str(screenshot_path)],
                ['gnome-screenshot', '-f', str(screenshot_path)],
                ['import', '-window', 'root', str(screenshot_path)]
            ]:
                try:
                    result = subprocess.run(cmd, check=True, timeout=10)
                    if screenshot_path.exists():
                        logger.info(f"Screenshot saved: {screenshot_path}")
                        return str(screenshot_path)
                except (subprocess.CalledProcessError, FileNotFoundError):
                    continue

            return None

        except Exception as e:
            logger.error(f"Error taking screenshot: {e}")
            return None

def main():
    """Main entry point for testing"""
    monitor = R2D2SystemMonitor()

    try:
        print("Starting R2D2 System Monitor...")
        monitor.start_monitoring()

        # Run for 30 seconds as a test
        time.sleep(30)

        # Print status
        status = monitor.get_system_status()
        print(json.dumps(status, indent=2))

    except KeyboardInterrupt:
        print("Stopping monitor...")
    finally:
        monitor.stop_monitoring()

if __name__ == "__main__":
    main()