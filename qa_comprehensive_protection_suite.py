#!/usr/bin/env python3
"""
Elite QA Protection Suite for R2D2 System
Comprehensive testing framework to protect working features during logging implementation
"""

import pytest
import asyncio
import aiohttp
import websockets
import json
import time
import threading
import subprocess
import psutil
import requests
import cv2
import numpy as np
from datetime import datetime
from typing import Dict, List, Any, Optional
import logging
import sys
import os

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class R2D2SystemProtectionSuite:
    """Elite QA protection suite for R2D2 system integrity"""

    def __init__(self):
        self.test_results = {
            'dashboard_tests': {},
            'vision_tests': {},
            'servo_tests': {},
            'performance_tests': {},
            'regression_tests': {}
        }

        # Working feature baselines
        self.baselines = {
            'dashboard_response_time': 2.0,  # seconds
            'vision_fps': 10.0,  # minimum FPS
            'websocket_latency': 1.0,  # seconds
            'memory_usage': 4096,  # MB (4GB heap)
            'detection_accuracy': 0.8  # minimum confidence
        }

        # System endpoints to protect
        self.endpoints = {
            'dashboard_main': 'http://localhost:8765/',
            'dashboard_vision': 'http://localhost:8765/vision',
            'dashboard_enhanced': 'http://localhost:8765/enhanced',
            'dashboard_servo': 'http://localhost:8765/servo',
            'dashboard_disney': 'http://localhost:8765/disney',
            'vision_websocket': 'ws://localhost:8767',
            'dashboard_websocket': 'ws://localhost:8766',
            'behavioral_websocket': 'ws://localhost:8768',
            'servo_api': 'http://localhost:5000/api'
        }

    def run_comprehensive_protection_tests(self) -> Dict[str, Any]:
        """Execute comprehensive protection test suite"""
        logger.info("🛡️ Starting Elite QA Protection Suite")

        # Test suite execution order
        test_phases = [
            ('System Health Check', self._test_system_health),
            ('Dashboard Endpoint Protection', self._test_dashboard_endpoints),
            ('Vision System Protection', self._test_vision_system),
            ('WebSocket Communication Protection', self._test_websocket_communication),
            ('Performance Baseline Validation', self._test_performance_baselines),
            ('Memory Management Protection', self._test_memory_management),
            ('Servo API Protection', self._test_servo_api),
            ('Integration Protection', self._test_system_integration)
        ]

        for phase_name, test_function in test_phases:
            logger.info(f"🔍 Executing {phase_name}")
            try:
                results = test_function()
                self.test_results[phase_name.lower().replace(' ', '_')] = results

                if not results.get('passed', False):
                    logger.error(f"❌ {phase_name} FAILED - System at risk!")
                    self._trigger_regression_alert(phase_name, results)
                else:
                    logger.info(f"✅ {phase_name} PASSED")

            except Exception as e:
                logger.error(f"💥 {phase_name} CRASHED: {e}")
                self._trigger_regression_alert(phase_name, {'error': str(e), 'passed': False})

        return self._generate_protection_report()

    def _test_system_health(self) -> Dict[str, Any]:
        """Test overall system health and process status"""
        results = {'passed': True, 'details': {}, 'issues': []}

        try:
            # Check if required processes are running
            required_processes = ['node', 'python3']
            running_processes = []

            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    if any(req_proc in proc.info['name'] for req_proc in required_processes):
                        if proc.info['cmdline']:
                            cmdline = ' '.join(proc.info['cmdline'])
                            if 'dashboard-server.js' in cmdline:
                                running_processes.append('dashboard-server')
                            elif 'r2d2_realtime_vision.py' in cmdline:
                                running_processes.append('vision-system')
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue

            results['details']['running_processes'] = running_processes

            # Check system resources
            cpu_usage = psutil.cpu_percent(interval=1)
            memory_usage = psutil.virtual_memory().percent

            results['details']['cpu_usage'] = cpu_usage
            results['details']['memory_usage'] = memory_usage

            # Validate system health
            if cpu_usage > 90:
                results['issues'].append(f"High CPU usage: {cpu_usage}%")
                results['passed'] = False

            if memory_usage > 85:
                results['issues'].append(f"High memory usage: {memory_usage}%")
                results['passed'] = False

            if 'dashboard-server' not in running_processes:
                results['issues'].append("Dashboard server not running")
                results['passed'] = False

        except Exception as e:
            results['passed'] = False
            results['issues'].append(f"System health check failed: {e}")

        return results

    def _test_dashboard_endpoints(self) -> Dict[str, Any]:
        """Test all dashboard endpoints for availability and performance"""
        results = {'passed': True, 'details': {}, 'issues': []}

        for endpoint_name, url in self.endpoints.items():
            if not endpoint_name.startswith('dashboard_'):
                continue

            try:
                start_time = time.time()
                response = requests.get(url, timeout=10)
                response_time = time.time() - start_time

                endpoint_result = {
                    'status_code': response.status_code,
                    'response_time': response_time,
                    'content_length': len(response.content),
                    'passed': False
                }

                # Validate response
                if response.status_code == 200:
                    if response_time <= self.baselines['dashboard_response_time']:
                        if len(response.content) > 1000:  # Reasonable HTML content size
                            endpoint_result['passed'] = True
                        else:
                            results['issues'].append(f"{endpoint_name}: Content too small")
                    else:
                        results['issues'].append(f"{endpoint_name}: Slow response ({response_time:.2f}s)")
                else:
                    results['issues'].append(f"{endpoint_name}: HTTP {response.status_code}")

                results['details'][endpoint_name] = endpoint_result

                if not endpoint_result['passed']:
                    results['passed'] = False

            except Exception as e:
                results['passed'] = False
                results['issues'].append(f"{endpoint_name}: {e}")
                results['details'][endpoint_name] = {'error': str(e), 'passed': False}

        return results

    def _test_vision_system(self) -> Dict[str, Any]:
        """Test vision system functionality and performance"""
        results = {'passed': True, 'details': {}, 'issues': []}

        try:
            # Test WebSocket connection to vision system
            async def test_vision_websocket():
                try:
                    uri = self.endpoints['vision_websocket']

                    async with websockets.connect(uri, timeout=10) as websocket:
                        # Wait for initial connection message
                        initial_message = await asyncio.wait_for(websocket.recv(), timeout=5)
                        initial_data = json.loads(initial_message)

                        # Test for expected vision data
                        frame_received = False
                        detection_received = False
                        fps_measured = 0
                        start_time = time.time()

                        # Collect data for 5 seconds
                        while time.time() - start_time < 5:
                            try:
                                message = await asyncio.wait_for(websocket.recv(), timeout=1)
                                data = json.loads(message)

                                if data.get('type') == 'character_vision_data':
                                    frame_received = True
                                    if data.get('detections'):
                                        detection_received = True
                                    fps_measured += 1

                            except asyncio.TimeoutError:
                                continue

                        # Calculate actual FPS
                        actual_fps = fps_measured / 5

                        return {
                            'connection_successful': True,
                            'frame_received': frame_received,
                            'detection_received': detection_received,
                            'fps_measured': actual_fps,
                            'initial_message': initial_data
                        }

                except Exception as e:
                    return {'error': str(e), 'connection_successful': False}

            # Run async test
            vision_test_result = asyncio.run(test_vision_websocket())
            results['details']['websocket_test'] = vision_test_result

            if not vision_test_result.get('connection_successful', False):
                results['passed'] = False
                results['issues'].append("Vision WebSocket connection failed")
            elif not vision_test_result.get('frame_received', False):
                results['passed'] = False
                results['issues'].append("No video frames received")
            elif vision_test_result.get('fps_measured', 0) < self.baselines['vision_fps']:
                results['passed'] = False
                results['issues'].append(f"Low FPS: {vision_test_result['fps_measured']:.1f}")

        except Exception as e:
            results['passed'] = False
            results['issues'].append(f"Vision system test failed: {e}")

        return results

    def _test_websocket_communication(self) -> Dict[str, Any]:
        """Test all WebSocket endpoints for proper communication"""
        results = {'passed': True, 'details': {}, 'issues': []}

        websocket_endpoints = {
            'dashboard': self.endpoints['dashboard_websocket'],
            'behavioral': self.endpoints['behavioral_websocket']
        }

        for ws_name, ws_url in websocket_endpoints.items():
            try:
                async def test_websocket_endpoint(url):
                    try:
                        async with websockets.connect(url, timeout=5) as websocket:
                            # Send test message
                            test_message = json.dumps({'type': 'request_data'})
                            await websocket.send(test_message)

                            # Wait for response
                            response = await asyncio.wait_for(websocket.recv(), timeout=5)
                            response_data = json.loads(response)

                            return {
                                'connected': True,
                                'response_received': True,
                                'response_data': response_data
                            }
                    except Exception as e:
                        return {'connected': False, 'error': str(e)}

                ws_result = asyncio.run(test_websocket_endpoint(ws_url))
                results['details'][ws_name] = ws_result

                if not ws_result.get('connected', False):
                    results['passed'] = False
                    results['issues'].append(f"{ws_name} WebSocket connection failed")

            except Exception as e:
                results['passed'] = False
                results['issues'].append(f"{ws_name} WebSocket test error: {e}")

        return results

    def _test_performance_baselines(self) -> Dict[str, Any]:
        """Test system performance against established baselines"""
        results = {'passed': True, 'details': {}, 'issues': []}

        try:
            # Memory usage test
            memory_info = psutil.virtual_memory()
            current_memory_mb = memory_info.used / 1024 / 1024

            results['details']['memory_usage_mb'] = current_memory_mb

            # CPU usage test
            cpu_usage = psutil.cpu_percent(interval=2)
            results['details']['cpu_usage'] = cpu_usage

            # Disk I/O test
            disk_usage = psutil.disk_usage('/')
            results['details']['disk_usage_percent'] = (disk_usage.used / disk_usage.total) * 100

            # Network connectivity test
            try:
                start_time = time.time()
                response = requests.get('http://localhost:8765/', timeout=5)
                network_latency = time.time() - start_time
                results['details']['network_latency'] = network_latency

                if network_latency > self.baselines['websocket_latency']:
                    results['issues'].append(f"High network latency: {network_latency:.2f}s")
                    results['passed'] = False

            except Exception as e:
                results['issues'].append(f"Network test failed: {e}")
                results['passed'] = False

            # Validate against baselines
            if cpu_usage > 80:
                results['issues'].append(f"High CPU usage: {cpu_usage}%")
                results['passed'] = False

        except Exception as e:
            results['passed'] = False
            results['issues'].append(f"Performance baseline test failed: {e}")

        return results

    def _test_memory_management(self) -> Dict[str, Any]:
        """Test memory management and leak detection"""
        results = {'passed': True, 'details': {}, 'issues': []}

        try:
            # Initial memory reading
            initial_memory = psutil.virtual_memory().used

            # Monitor memory over 30 seconds
            memory_samples = []
            for i in range(6):  # 6 samples over 30 seconds
                time.sleep(5)
                current_memory = psutil.virtual_memory().used
                memory_samples.append(current_memory)

            # Calculate memory trend
            memory_trend = (memory_samples[-1] - memory_samples[0]) / 1024 / 1024  # MB

            results['details']['initial_memory_mb'] = initial_memory / 1024 / 1024
            results['details']['final_memory_mb'] = memory_samples[-1] / 1024 / 1024
            results['details']['memory_trend_mb'] = memory_trend
            results['details']['memory_samples'] = [m / 1024 / 1024 for m in memory_samples]

            # Check for memory leaks
            if memory_trend > 100:  # More than 100MB increase
                results['issues'].append(f"Potential memory leak detected: +{memory_trend:.1f}MB")
                results['passed'] = False

            # Check absolute memory usage
            if memory_samples[-1] / 1024 / 1024 > 6000:  # More than 6GB
                results['issues'].append("Excessive memory usage detected")
                results['passed'] = False

        except Exception as e:
            results['passed'] = False
            results['issues'].append(f"Memory management test failed: {e}")

        return results

    def _test_servo_api(self) -> Dict[str, Any]:
        """Test servo API endpoints and functionality"""
        results = {'passed': True, 'details': {}, 'issues': []}

        try:
            # Test servo status endpoint
            servo_url = f"{self.endpoints['servo_api']}/servo/status"

            response = requests.get(servo_url, timeout=5)
            results['details']['servo_status_response'] = {
                'status_code': response.status_code,
                'response_time': response.elapsed.total_seconds()
            }

            # Servo API is in simulation mode, so we expect specific responses
            if response.status_code not in [200, 404, 500]:
                results['issues'].append(f"Unexpected servo API response: {response.status_code}")
                results['passed'] = False

        except requests.exceptions.ConnectionError:
            # Servo API not running is acceptable in simulation mode
            results['details']['servo_api_status'] = 'not_running_simulation_mode'
        except Exception as e:
            results['issues'].append(f"Servo API test error: {e}")
            results['passed'] = False

        return results

    def _test_system_integration(self) -> Dict[str, Any]:
        """Test overall system integration and end-to-end functionality"""
        results = {'passed': True, 'details': {}, 'issues': []}

        try:
            # Test dashboard to vision system integration
            async def test_integration():
                integration_results = {}

                # 1. Connect to dashboard WebSocket
                try:
                    async with websockets.connect(self.endpoints['dashboard_websocket'], timeout=5) as dashboard_ws:
                        # Send status request
                        await dashboard_ws.send(json.dumps({'type': 'request_data'}))
                        dashboard_response = await asyncio.wait_for(dashboard_ws.recv(), timeout=3)
                        integration_results['dashboard_communication'] = True
                except Exception as e:
                    integration_results['dashboard_communication'] = False
                    integration_results['dashboard_error'] = str(e)

                # 2. Connect to vision WebSocket
                try:
                    async with websockets.connect(self.endpoints['vision_websocket'], timeout=5) as vision_ws:
                        vision_message = await asyncio.wait_for(vision_ws.recv(), timeout=3)
                        vision_data = json.loads(vision_message)
                        integration_results['vision_communication'] = True
                        integration_results['vision_data_type'] = vision_data.get('type')
                except Exception as e:
                    integration_results['vision_communication'] = False
                    integration_results['vision_error'] = str(e)

                # 3. Test behavioral WebSocket
                try:
                    async with websockets.connect(self.endpoints['behavioral_websocket'], timeout=5) as behavior_ws:
                        await behavior_ws.send(json.dumps({'type': 'request_status'}))
                        behavior_response = await asyncio.wait_for(behavior_ws.recv(), timeout=3)
                        integration_results['behavioral_communication'] = True
                except Exception as e:
                    integration_results['behavioral_communication'] = False
                    integration_results['behavioral_error'] = str(e)

                return integration_results

            integration_test_results = asyncio.run(test_integration())
            results['details'].update(integration_test_results)

            # Validate integration
            required_integrations = ['dashboard_communication', 'vision_communication', 'behavioral_communication']
            for integration in required_integrations:
                if not integration_test_results.get(integration, False):
                    results['issues'].append(f"{integration} failed")
                    results['passed'] = False

        except Exception as e:
            results['passed'] = False
            results['issues'].append(f"Integration test failed: {e}")

        return results

    def _trigger_regression_alert(self, test_name: str, test_results: Dict[str, Any]):
        """Trigger regression alert for failed tests"""
        alert_message = f"""
🚨 REGRESSION ALERT 🚨
Test: {test_name}
Status: FAILED
Time: {datetime.now().isoformat()}
Issues: {test_results.get('issues', ['Unknown error'])}
Details: {test_results.get('details', {})}
        """

        logger.error(alert_message)

        # Save alert to file for persistence
        alert_file = f"/home/rolo/r2ai/qa_regression_alert_{int(time.time())}.json"
        with open(alert_file, 'w') as f:
            json.dump({
                'test_name': test_name,
                'test_results': test_results,
                'timestamp': datetime.now().isoformat(),
                'alert_level': 'CRITICAL'
            }, f, indent=2)

    def _generate_protection_report(self) -> Dict[str, Any]:
        """Generate comprehensive protection report"""
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results.values()
                          if isinstance(result, dict) and result.get('passed', False))

        protection_score = (passed_tests / total_tests) * 100 if total_tests > 0 else 0

        report = {
            'timestamp': datetime.now().isoformat(),
            'protection_score': protection_score,
            'total_tests': total_tests,
            'passed_tests': passed_tests,
            'failed_tests': total_tests - passed_tests,
            'system_status': 'PROTECTED' if protection_score >= 90 else 'AT_RISK',
            'test_results': self.test_results,
            'recommendations': self._generate_recommendations()
        }

        return report

    def _generate_recommendations(self) -> List[str]:
        """Generate recommendations based on test results"""
        recommendations = []

        for test_name, test_result in self.test_results.items():
            if isinstance(test_result, dict) and not test_result.get('passed', False):
                issues = test_result.get('issues', [])
                for issue in issues:
                    if 'memory' in issue.lower():
                        recommendations.append("Monitor memory usage and implement garbage collection")
                    elif 'cpu' in issue.lower():
                        recommendations.append("Optimize CPU-intensive operations")
                    elif 'websocket' in issue.lower():
                        recommendations.append("Investigate WebSocket connection stability")
                    elif 'fps' in issue.lower():
                        recommendations.append("Optimize vision system performance")
                    elif 'response time' in issue.lower():
                        recommendations.append("Optimize server response times")

        if not recommendations:
            recommendations.append("All systems operating within acceptable parameters")

        return list(set(recommendations))  # Remove duplicates

def run_protection_monitoring():
    """Run continuous protection monitoring"""
    logger.info("🛡️ Starting R2D2 System Protection Monitoring")

    protection_suite = R2D2SystemProtectionSuite()

    while True:
        try:
            # Run protection tests
            report = protection_suite.run_comprehensive_protection_tests()

            # Save report
            report_file = f"/home/rolo/r2ai/qa_protection_report_{int(time.time())}.json"
            with open(report_file, 'w') as f:
                json.dump(report, f, indent=2)

            logger.info(f"Protection Score: {report['protection_score']:.1f}%")
            logger.info(f"System Status: {report['system_status']}")

            if report['system_status'] == 'AT_RISK':
                logger.error("🚨 SYSTEM AT RISK - IMMEDIATE ATTENTION REQUIRED")

            # Wait before next monitoring cycle
            time.sleep(60)  # Check every minute

        except KeyboardInterrupt:
            logger.info("Protection monitoring stopped by user")
            break
        except Exception as e:
            logger.error(f"Protection monitoring error: {e}")
            time.sleep(30)  # Wait 30 seconds before retry

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--monitor":
        run_protection_monitoring()
    else:
        # Run single test cycle
        suite = R2D2SystemProtectionSuite()
        report = suite.run_comprehensive_protection_tests()

        print("\n" + "="*60)
        print("🛡️ R2D2 SYSTEM PROTECTION REPORT")
        print("="*60)
        print(f"Protection Score: {report['protection_score']:.1f}%")
        print(f"System Status: {report['system_status']}")
        print(f"Tests Passed: {report['passed_tests']}/{report['total_tests']}")
        print("\nRecommendations:")
        for rec in report['recommendations']:
            print(f"  • {rec}")
        print("="*60)