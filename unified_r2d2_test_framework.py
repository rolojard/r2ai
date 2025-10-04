#!/usr/bin/env python3
"""
UNIFIED R2D2 TEST FRAMEWORK
===========================

Consolidated testing framework replacing scattered test files.
Provides comprehensive testing coverage with minimal file overhead.

CONSOLIDATED FUNCTIONALITY:
- Camera hardware validation
- Dashboard integration testing
- WebSocket stability testing
- Performance benchmarking
- System integration verification
- Regression protection

Replaces 15+ individual test files with unified framework.

Author: Elite Expert QA Tester
Target: Token optimization while maintaining quality coverage
"""

import asyncio
import websockets
import json
import time
import requests
import cv2
import numpy as np
import logging
import subprocess
import psutil
import threading
from datetime import datetime
from typing import Dict, List, Any, Optional
import queue
import os
import sys

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class UnifiedR2D2TestFramework:
    """
    Unified testing framework consolidating all essential R2D2 system tests
    """

    def __init__(self):
        self.test_results = {
            'camera_hardware': {},
            'dashboard_integration': {},
            'websocket_stability': {},
            'performance_metrics': {},
            'system_integration': {},
            'regression_protection': {}
        }

        # Test configuration
        self.dashboard_url = "http://localhost:8765"
        self.websocket_url = "ws://localhost:8767"
        self.camera_index = 0

        # Performance baselines
        self.performance_baselines = {
            'dashboard_response_time': 2.0,  # seconds
            'websocket_latency': 1.0,  # seconds
            'camera_fps': 10.0,  # minimum FPS
            'memory_usage_mb': 4096,  # max MB
            'cpu_usage_percent': 80.0  # max CPU %
        }

        logger.info("Unified R2D2 Test Framework initialized")

    def log_test_result(self, category: str, test_name: str, success: bool, details: str = ""):
        """Log test result with standardized format"""
        status = "✅ PASS" if success else "❌ FAIL"
        timestamp = datetime.now().strftime("%H:%M:%S")
        logger.info(f"[{timestamp}] {status} {category}.{test_name}")
        if details:
            logger.info(f"    Details: {details}")

        self.test_results[category][test_name] = {
            'success': success,
            'details': details,
            'timestamp': timestamp
        }

    # ===== CAMERA HARDWARE TESTING =====

    def test_camera_hardware_detection(self) -> bool:
        """Test camera hardware detection and basic functionality"""
        logger.info("🎥 Testing camera hardware detection...")

        try:
            # Try to open camera
            camera = cv2.VideoCapture(self.camera_index, cv2.CAP_V4L2)

            if not camera.isOpened():
                self.log_test_result('camera_hardware', 'detection', False,
                                   f"Camera at index {self.camera_index} not accessible")
                return False

            # Basic camera configuration
            camera.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            camera.set(cv2.CAP_PROP_BUFFERSIZE, 1)

            # Test frame capture
            frame_count = 0
            for i in range(10):
                ret, frame = camera.read()
                if ret and frame is not None:
                    frame_count += 1
                time.sleep(0.1)

            camera.release()

            success = frame_count >= 8
            self.log_test_result('camera_hardware', 'detection', success,
                               f"Captured {frame_count}/10 test frames")
            return success

        except Exception as e:
            self.log_test_result('camera_hardware', 'detection', False, f"Error: {e}")
            return False

    def test_camera_stability(self) -> bool:
        """Test camera stability under continuous operation"""
        logger.info("🎥 Testing camera stability...")

        try:
            camera = cv2.VideoCapture(self.camera_index, cv2.CAP_V4L2)

            if not camera.isOpened():
                self.log_test_result('camera_hardware', 'stability', False, "Camera not accessible")
                return False

            # Configure camera
            camera.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            camera.set(cv2.CAP_PROP_BUFFERSIZE, 1)

            # Test sustained operation
            start_time = time.time()
            frame_count = 0
            error_count = 0
            duration = 30  # 30 second test

            while time.time() - start_time < duration:
                ret, frame = camera.read()
                if ret and frame is not None:
                    frame_count += 1
                else:
                    error_count += 1
                time.sleep(0.033)  # ~30 FPS

            camera.release()

            error_rate = (error_count / max(frame_count + error_count, 1)) * 100
            fps = frame_count / duration

            success = error_rate < 5 and fps >= 10
            self.log_test_result('camera_hardware', 'stability', success,
                               f"FPS: {fps:.1f}, Error rate: {error_rate:.1f}%")
            return success

        except Exception as e:
            self.log_test_result('camera_hardware', 'stability', False, f"Error: {e}")
            return False

    # ===== DASHBOARD INTEGRATION TESTING =====

    def test_dashboard_accessibility(self) -> bool:
        """Test dashboard web interface accessibility"""
        logger.info("🌐 Testing dashboard accessibility...")

        try:
            start_time = time.time()
            response = requests.get(self.dashboard_url, timeout=5)
            response_time = time.time() - start_time

            success = (response.status_code == 200 and
                      response_time < self.performance_baselines['dashboard_response_time'])

            self.log_test_result('dashboard_integration', 'accessibility', success,
                               f"Status: {response.status_code}, Response time: {response_time:.2f}s")
            return success

        except Exception as e:
            self.log_test_result('dashboard_integration', 'accessibility', False, f"Error: {e}")
            return False

    def test_dashboard_content(self) -> bool:
        """Test dashboard content and essential elements"""
        logger.info("🌐 Testing dashboard content...")

        try:
            response = requests.get(self.dashboard_url, timeout=5)
            content = response.text.lower()

            # Check for essential dashboard elements
            required_elements = ['r2d2', 'video', 'websocket', 'camera']
            missing_elements = [elem for elem in required_elements if elem not in content]

            success = len(missing_elements) == 0 and response.status_code == 200

            details = f"Status: {response.status_code}"
            if missing_elements:
                details += f", Missing: {missing_elements}"

            self.log_test_result('dashboard_integration', 'content', success, details)
            return success

        except Exception as e:
            self.log_test_result('dashboard_integration', 'content', False, f"Error: {e}")
            return False

    # ===== WEBSOCKET STABILITY TESTING =====

    async def test_websocket_connection(self) -> bool:
        """Test WebSocket connection stability"""
        logger.info("🔌 Testing WebSocket connection...")

        try:
            # Test basic connection
            ws = await websockets.connect(self.websocket_url, timeout=5)

            # Test message reception
            message_count = 0
            start_time = time.time()

            for i in range(10):
                try:
                    message = await asyncio.wait_for(ws.recv(), timeout=2.0)
                    data = json.loads(message)
                    message_count += 1
                except asyncio.TimeoutError:
                    logger.warning(f"WebSocket timeout on message {i+1}")
                except json.JSONDecodeError:
                    logger.warning("Invalid JSON received")

            await ws.close()

            latency = (time.time() - start_time) / max(message_count, 1)
            success = (message_count >= 5 and
                      latency < self.performance_baselines['websocket_latency'])

            self.log_test_result('websocket_stability', 'connection', success,
                               f"Messages: {message_count}/10, Avg latency: {latency:.2f}s")
            return success

        except Exception as e:
            self.log_test_result('websocket_stability', 'connection', False, f"Error: {e}")
            return False

    async def test_websocket_data_integrity(self) -> bool:
        """Test WebSocket data integrity and format"""
        logger.info("🔌 Testing WebSocket data integrity...")

        try:
            ws = await websockets.connect(self.websocket_url, timeout=5)

            valid_messages = 0
            total_messages = 0

            for i in range(5):
                try:
                    message = await asyncio.wait_for(ws.recv(), timeout=3.0)
                    data = json.loads(message)
                    total_messages += 1

                    # Validate message structure
                    if (data.get('type') and
                        data.get('timestamp') and
                        isinstance(data, dict)):
                        valid_messages += 1

                except (asyncio.TimeoutError, json.JSONDecodeError):
                    total_messages += 1

            await ws.close()

            success_rate = (valid_messages / max(total_messages, 1)) * 100
            success = success_rate >= 80

            self.log_test_result('websocket_stability', 'data_integrity', success,
                               f"Valid messages: {valid_messages}/{total_messages} ({success_rate:.1f}%)")
            return success

        except Exception as e:
            self.log_test_result('websocket_stability', 'data_integrity', False, f"Error: {e}")
            return False

    # ===== PERFORMANCE METRICS TESTING =====

    def test_system_performance(self) -> bool:
        """Test overall system performance metrics"""
        logger.info("📊 Testing system performance...")

        try:
            # Collect system metrics
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            memory_mb = memory.used / 1024 / 1024

            # Performance checks
            cpu_ok = cpu_percent < self.performance_baselines['cpu_usage_percent']
            memory_ok = memory_mb < self.performance_baselines['memory_usage_mb']

            success = cpu_ok and memory_ok

            details = f"CPU: {cpu_percent:.1f}%, Memory: {memory_mb:.0f}MB"
            if not cpu_ok:
                details += " (CPU high)"
            if not memory_ok:
                details += " (Memory high)"

            self.log_test_result('performance_metrics', 'system_resources', success, details)
            return success

        except Exception as e:
            self.log_test_result('performance_metrics', 'system_resources', False, f"Error: {e}")
            return False

    # ===== SYSTEM INTEGRATION TESTING =====

    async def test_end_to_end_integration(self) -> bool:
        """Test complete end-to-end system integration"""
        logger.info("🎯 Testing end-to-end integration...")

        try:
            # Test 1: Dashboard accessible
            dashboard_response = requests.get(self.dashboard_url, timeout=5)
            dashboard_ok = dashboard_response.status_code == 200

            # Test 2: WebSocket connects and receives data
            ws = await websockets.connect(self.websocket_url, timeout=5)

            websocket_data_received = False
            for i in range(5):
                try:
                    message = await asyncio.wait_for(ws.recv(), timeout=2.0)
                    data = json.loads(message)
                    if data.get('type'):
                        websocket_data_received = True
                        break
                except (asyncio.TimeoutError, json.JSONDecodeError):
                    pass

            await ws.close()

            # Test 3: System performance acceptable
            cpu_percent = psutil.cpu_percent(interval=0.5)
            performance_ok = cpu_percent < 90

            success = dashboard_ok and websocket_data_received and performance_ok

            details = f"Dashboard: {dashboard_ok}, WebSocket: {websocket_data_received}, Performance: {performance_ok}"

            self.log_test_result('system_integration', 'end_to_end', success, details)
            return success

        except Exception as e:
            self.log_test_result('system_integration', 'end_to_end', False, f"Error: {e}")
            return False

    # ===== REGRESSION PROTECTION =====

    def test_regression_protection(self) -> bool:
        """Test key functionality to prevent regressions"""
        logger.info("🛡️ Testing regression protection...")

        # Core functionality checks
        checks = {
            'camera_basic': self._check_camera_basic(),
            'dashboard_basic': self._check_dashboard_basic(),
            'performance_acceptable': self._check_performance_acceptable()
        }

        success = all(checks.values())
        failed_checks = [name for name, result in checks.items() if not result]

        details = f"Checks: {len([r for r in checks.values() if r])}/{len(checks)} passed"
        if failed_checks:
            details += f", Failed: {failed_checks}"

        self.log_test_result('regression_protection', 'core_functionality', success, details)
        return success

    def _check_camera_basic(self) -> bool:
        """Basic camera functionality check"""
        try:
            camera = cv2.VideoCapture(self.camera_index, cv2.CAP_V4L2)
            if not camera.isOpened():
                return False
            ret, frame = camera.read()
            camera.release()
            return ret and frame is not None
        except:
            return False

    def _check_dashboard_basic(self) -> bool:
        """Basic dashboard functionality check"""
        try:
            response = requests.get(self.dashboard_url, timeout=3)
            return response.status_code == 200
        except:
            return False

    def _check_performance_acceptable(self) -> bool:
        """Basic performance check"""
        try:
            cpu_percent = psutil.cpu_percent(interval=0.5)
            memory = psutil.virtual_memory()
            return cpu_percent < 95 and memory.percent < 95
        except:
            return False

    # ===== MAIN TEST EXECUTION =====

    async def run_full_test_suite(self) -> bool:
        """Run complete unified test suite"""
        logger.info("🚀 UNIFIED R2D2 TEST FRAMEWORK - FULL SUITE")
        logger.info("=" * 60)

        # Run all test categories
        test_categories = [
            ("Camera Hardware", [
                self.test_camera_hardware_detection,
                self.test_camera_stability
            ]),
            ("Dashboard Integration", [
                self.test_dashboard_accessibility,
                self.test_dashboard_content
            ]),
            ("WebSocket Stability", [
                self.test_websocket_connection,
                self.test_websocket_data_integrity
            ]),
            ("Performance Metrics", [
                self.test_system_performance
            ]),
            ("System Integration", [
                self.test_end_to_end_integration
            ]),
            ("Regression Protection", [
                self.test_regression_protection
            ])
        ]

        overall_success = True

        for category_name, tests in test_categories:
            logger.info(f"\n📋 Running {category_name} Tests...")

            for test_func in tests:
                try:
                    if asyncio.iscoroutinefunction(test_func):
                        result = await test_func()
                    else:
                        result = test_func()

                    if not result:
                        overall_success = False

                except Exception as e:
                    logger.error(f"Test execution error: {e}")
                    overall_success = False

        # Generate summary report
        self.generate_test_report()

        return overall_success

    def generate_test_report(self):
        """Generate comprehensive test report"""
        logger.info("\n" + "=" * 60)
        logger.info("🎯 UNIFIED TEST FRAMEWORK REPORT")
        logger.info("=" * 60)

        total_tests = 0
        passed_tests = 0

        for category, tests in self.test_results.items():
            if tests:
                logger.info(f"\n📋 {category.upper().replace('_', ' ')}:")

                for test_name, result in tests.items():
                    status = "✅ PASS" if result['success'] else "❌ FAIL"
                    logger.info(f"  {status} {test_name}")
                    if result['details']:
                        logger.info(f"    {result['details']}")

                    total_tests += 1
                    if result['success']:
                        passed_tests += 1

        success_rate = (passed_tests / max(total_tests, 1)) * 100

        logger.info(f"\n📊 OVERALL RESULTS:")
        logger.info(f"   Tests Passed: {passed_tests}/{total_tests}")
        logger.info(f"   Success Rate: {success_rate:.1f}%")

        if success_rate >= 90:
            logger.info("🎉 EXCELLENT - System performing optimally")
        elif success_rate >= 75:
            logger.info("✅ GOOD - System functioning well")
        elif success_rate >= 50:
            logger.info("⚠️ ACCEPTABLE - Some issues detected")
        else:
            logger.info("❌ POOR - Significant issues require attention")

        logger.info("=" * 60)

async def main():
    """Main execution function"""
    framework = UnifiedR2D2TestFramework()

    try:
        logger.info("🤖 Starting Unified R2D2 Test Framework")
        success = await framework.run_full_test_suite()

        if success:
            logger.info("🎊 All tests completed successfully!")
            return 0
        else:
            logger.warning("⚠️ Some tests failed - review results above")
            return 1

    except KeyboardInterrupt:
        logger.info("\n🛑 Testing interrupted by user")
        return 1
    except Exception as e:
        logger.error(f"❌ Test framework error: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(asyncio.run(main()))