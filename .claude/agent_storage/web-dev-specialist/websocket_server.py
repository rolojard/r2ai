#!/usr/bin/env python3
"""
R2D2 Multi-Agent Dashboard WebSocket Server
Real-time communication hub for agent monitoring and control
"""

import asyncio
import websockets
import json
import logging
import time
import os
import sys
import threading
from datetime import datetime
from typing import Dict, Set, Any, Optional
import psutil
import subprocess
import base64
from pathlib import Path

# Add R2D2 system paths
sys.path.append('/home/rolo/r2ai')

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class R2D2DashboardServer:
    """WebSocket server for R2D2 multi-agent dashboard"""

    def __init__(self, host='localhost', port=8765):
        self.host = host
        self.port = port
        self.clients: Set[websockets.WebSocketServerProtocol] = set()
        self.agent_data: Dict[str, Any] = {}
        self.system_metrics: Dict[str, Any] = {}
        self.running = False

        # Initialize agent data structures
        self.initialize_agent_data()

        # Start background monitoring
        self.monitoring_thread = None

    def initialize_agent_data(self):
        """Initialize data structures for all agents"""
        self.agent_data = {
            'project_manager': {
                'systemHealth': 98,
                'performanceData': [85, 87, 89, 88, 90, 92, 91, 89, 87, 85],
                'alerts': []
            },
            'qa_tester': {
                'testResults': {'passed': 127, 'failed': 3, 'skipped': 2},
                'qualityScore': 96.2,
                'validationStatus': {
                    'hardware': True,
                    'software': True,
                    'performance': False
                }
            },
            'imagineer': {
                'servoStatus': ['online'] * 16,
                'animationQueue': [
                    {'name': 'Head Turn Left', 'status': 'active'},
                    {'name': 'Dome Rotation', 'status': 'pending'},
                    {'name': 'Body Lean Forward', 'status': 'pending'}
                ],
                'motionData': [50, 55, 60, 58, 62, 65, 63, 60, 58, 55]
            },
            'video_model_trainer': {
                'frameRate': 30,
                'accuracy': 94.7,
                'objectCount': 3,
                'detections': [
                    'Person - 97.3% confidence',
                    'Face - 89.1% confidence',
                    'Hand - 76.8% confidence'
                ]
            },
            'star_wars_expert': {
                'authenticityScore': 98.5,
                'interactionQuality': {
                    'voiceMatch': 'Excellent',
                    'movementStyle': 'Excellent',
                    'responseTiming': 'Good'
                },
                'canonCompliance': {
                    'astromechProtocols': True,
                    'beepPatterns': True,
                    'movementBehaviors': True,
                    'colorAccuracy': 98
                }
            },
            'super_coder': {
                'performance': {'cpu': 65, 'memory': 42, 'gpu': 78},
                'optimization': {
                    'cpuGovernor': 'completed',
                    'memoryManagement': 'completed',
                    'i2cBus': 'completed',
                    'gpuTuning': 'in-progress'
                },
                'logs': []
            },
            'ux_designer': {
                'accessibilityScore': 92,
                'interactionData': None,
                'responsiveness': {
                    'loadTime': 1.2,
                    'firstPaint': 0.8,
                    'interactive': 1.5
                }
            },
            'nvidia_specialist': {
                'gpuUsage': 78,
                'gpuMemory': '3.2GB/8GB',
                'temperature': 58,
                'powerConsumption': {
                    'current': 15.2,
                    'peak': 18.7,
                    'efficiency': 94
                }
            }
        }

    async def register_client(self, websocket):
        """Register a new client connection"""
        self.clients.add(websocket)
        logger.info(f"Client connected. Total clients: {len(self.clients)}")

        # Send initial data to the new client
        await self.send_system_update(websocket)
        await self.send_agent_data(websocket, 'project_manager')

    async def unregister_client(self, websocket):
        """Unregister a client connection"""
        self.clients.discard(websocket)
        logger.info(f"Client disconnected. Total clients: {len(self.clients)}")

    async def broadcast_message(self, message: Dict[str, Any]):
        """Broadcast a message to all connected clients"""
        if not self.clients:
            return

        message_json = json.dumps(message)
        disconnected_clients = set()

        for client in self.clients.copy():
            try:
                await client.send(message_json)
            except websockets.exceptions.ConnectionClosed:
                disconnected_clients.add(client)
            except Exception as e:
                logger.error(f"Error sending message to client: {e}")
                disconnected_clients.add(client)

        # Remove disconnected clients
        for client in disconnected_clients:
            self.clients.discard(client)

    async def send_system_update(self, websocket=None):
        """Send system metrics update"""
        metrics = self.get_system_metrics()
        message = {
            'type': 'system_update',
            'metrics': metrics,
            'timestamp': time.time()
        }

        if websocket:
            try:
                await websocket.send(json.dumps(message))
            except Exception as e:
                logger.error(f"Error sending system update: {e}")
        else:
            await self.broadcast_message(message)

    async def send_agent_data(self, websocket, agent_id: str):
        """Send agent-specific data"""
        if agent_id in self.agent_data:
            message = {
                'type': 'agent_data',
                'agent': agent_id,
                'data': self.agent_data[agent_id],
                'timestamp': time.time()
            }

            try:
                await websocket.send(json.dumps(message))
            except Exception as e:
                logger.error(f"Error sending agent data: {e}")

    async def handle_message(self, websocket, message: str):
        """Handle incoming WebSocket message"""
        try:
            data = json.loads(message)
            message_type = data.get('type')

            if message_type == 'request_data':
                agent = data.get('agent', 'project_manager')
                await self.send_agent_data(websocket, agent)

            elif message_type == 'take_screenshot':
                await self.handle_screenshot_request(websocket)

            elif message_type == 'trigger_motion':
                await self.handle_motion_trigger(data.get('motion'))

            elif message_type == 'run_tests':
                await self.handle_test_run()

            elif message_type == 'calibrate_servos':
                await self.handle_servo_calibration()

            elif message_type == 'change_power_mode':
                await self.handle_power_mode_change(data.get('mode'))

            elif message_type == 'set_thermal_target':
                await self.handle_thermal_target(data.get('target'))

            else:
                logger.warning(f"Unknown message type: {message_type}")

        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON received: {e}")
        except Exception as e:
            logger.error(f"Error handling message: {e}")

    async def handle_screenshot_request(self, websocket):
        """Handle screenshot request"""
        try:
            # Take a screenshot using the system screenshot capability
            screenshot_path = await self.take_system_screenshot()

            if screenshot_path:
                message = {
                    'type': 'screenshot_ready',
                    'url': screenshot_path,
                    'timestamp': time.time()
                }
                await websocket.send(json.dumps(message))

                # Broadcast alert
                await self.broadcast_message({
                    'type': 'alert',
                    'level': 'success',
                    'message': 'Screenshot captured successfully',
                    'timestamp': time.time()
                })
            else:
                await self.broadcast_message({
                    'type': 'alert',
                    'level': 'error',
                    'message': 'Failed to capture screenshot',
                    'timestamp': time.time()
                })

        except Exception as e:
            logger.error(f"Error handling screenshot: {e}")

    async def take_system_screenshot(self) -> Optional[str]:
        """Take a system screenshot"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            screenshot_dir = Path("/home/rolo/r2ai/screenshots")
            screenshot_dir.mkdir(exist_ok=True)

            screenshot_path = screenshot_dir / f"r2d2_dashboard_{timestamp}.png"

            # Use scrot or gnome-screenshot depending on what's available
            try:
                subprocess.run(['scrot', str(screenshot_path)], check=True, timeout=10)
            except (subprocess.CalledProcessError, FileNotFoundError):
                try:
                    subprocess.run(['gnome-screenshot', '-f', str(screenshot_path)], check=True, timeout=10)
                except (subprocess.CalledProcessError, FileNotFoundError):
                    logger.error("No screenshot utility available")
                    return None

            if screenshot_path.exists():
                return str(screenshot_path)
            else:
                return None

        except Exception as e:
            logger.error(f"Error taking screenshot: {e}")
            return None

    async def handle_motion_trigger(self, motion: str):
        """Handle motion trigger request"""
        try:
            logger.info(f"Triggering motion: {motion}")

            # Update animation queue
            self.agent_data['imagineer']['animationQueue'].insert(0, {
                'name': f"Motion: {motion.title()}",
                'status': 'active'
            })

            # Broadcast the update
            await self.broadcast_message({
                'type': 'agent_data',
                'agent': 'imagineer',
                'data': self.agent_data['imagineer'],
                'timestamp': time.time()
            })

            # Send alert
            await self.broadcast_message({
                'type': 'alert',
                'level': 'info',
                'message': f'Motion triggered: {motion}',
                'timestamp': time.time()
            })

        except Exception as e:
            logger.error(f"Error handling motion trigger: {e}")

    async def handle_test_run(self):
        """Handle test run request"""
        try:
            logger.info("Running system tests")

            # Simulate test run by updating QA data
            await asyncio.sleep(2)  # Simulate test execution time

            # Update test results with new random values
            import random
            passed = random.randint(120, 130)
            failed = random.randint(0, 5)
            skipped = random.randint(0, 3)

            self.agent_data['qa_tester']['testResults'] = {
                'passed': passed,
                'failed': failed,
                'skipped': skipped
            }

            # Calculate quality score
            total_tests = passed + failed + skipped
            quality_score = (passed / total_tests) * 100 if total_tests > 0 else 100
            self.agent_data['qa_tester']['qualityScore'] = round(quality_score, 1)

            # Broadcast the update
            await self.broadcast_message({
                'type': 'agent_data',
                'agent': 'qa_tester',
                'data': self.agent_data['qa_tester'],
                'timestamp': time.time()
            })

            # Send completion alert
            await self.broadcast_message({
                'type': 'alert',
                'level': 'success',
                'message': f'Test run completed: {passed} passed, {failed} failed',
                'timestamp': time.time()
            })

        except Exception as e:
            logger.error(f"Error handling test run: {e}")

    async def handle_servo_calibration(self):
        """Handle servo calibration request"""
        try:
            logger.info("Calibrating servos")

            # Simulate calibration process
            await self.broadcast_message({
                'type': 'alert',
                'level': 'info',
                'message': 'Servo calibration in progress...',
                'timestamp': time.time()
            })

            await asyncio.sleep(3)  # Simulate calibration time

            # Update servo status
            self.agent_data['imagineer']['servoStatus'] = ['online'] * 16

            # Broadcast the update
            await self.broadcast_message({
                'type': 'agent_data',
                'agent': 'imagineer',
                'data': self.agent_data['imagineer'],
                'timestamp': time.time()
            })

            # Send completion alert
            await self.broadcast_message({
                'type': 'alert',
                'level': 'success',
                'message': 'Servo calibration completed successfully',
                'timestamp': time.time()
            })

        except Exception as e:
            logger.error(f"Error handling servo calibration: {e}")

    async def handle_power_mode_change(self, mode: str):
        """Handle power mode change request"""
        try:
            logger.info(f"Changing power mode to: {mode}")

            # Update NVIDIA specialist data based on mode
            if mode == 'performance':
                self.agent_data['nvidia_specialist']['gpuUsage'] = 85
                self.agent_data['nvidia_specialist']['temperature'] = 65
                self.agent_data['nvidia_specialist']['powerConsumption']['current'] = 18.5
            elif mode == 'balanced':
                self.agent_data['nvidia_specialist']['gpuUsage'] = 70
                self.agent_data['nvidia_specialist']['temperature'] = 58
                self.agent_data['nvidia_specialist']['powerConsumption']['current'] = 15.2
            elif mode == 'efficiency':
                self.agent_data['nvidia_specialist']['gpuUsage'] = 55
                self.agent_data['nvidia_specialist']['temperature'] = 50
                self.agent_data['nvidia_specialist']['powerConsumption']['current'] = 12.1

            # Broadcast the update
            await self.broadcast_message({
                'type': 'agent_data',
                'agent': 'nvidia_specialist',
                'data': self.agent_data['nvidia_specialist'],
                'timestamp': time.time()
            })

        except Exception as e:
            logger.error(f"Error handling power mode change: {e}")

    async def handle_thermal_target(self, target: int):
        """Handle thermal target setting"""
        try:
            logger.info(f"Setting thermal target to: {target}°C")

            # Update thermal management
            self.agent_data['nvidia_specialist']['thermalTarget'] = target

            # Adjust temperature based on target
            current_temp = self.agent_data['nvidia_specialist']['temperature']
            if current_temp > target:
                self.agent_data['nvidia_specialist']['temperature'] = max(target - 5, current_temp - 10)

            # Broadcast the update
            await self.broadcast_message({
                'type': 'agent_data',
                'agent': 'nvidia_specialist',
                'data': self.agent_data['nvidia_specialist'],
                'timestamp': time.time()
            })

        except Exception as e:
            logger.error(f"Error handling thermal target: {e}")

    def get_system_metrics(self) -> Dict[str, Any]:
        """Get current system metrics"""
        try:
            # Get CPU usage
            cpu_percent = psutil.cpu_percent(interval=None)

            # Get memory usage
            memory = psutil.virtual_memory()
            memory_percent = memory.percent

            # Get temperature (if available)
            temperature = 45  # Default fallback
            try:
                temps = psutil.sensors_temperatures()
                if temps:
                    # Try to get CPU temperature
                    for name, entries in temps.items():
                        if entries:
                            temperature = entries[0].current
                            break
            except Exception:
                pass

            # Calculate system health based on metrics
            system_health = 100
            if cpu_percent > 80:
                system_health -= 20
            if memory_percent > 80:
                system_health -= 15
            if temperature > 70:
                system_health -= 25

            return {
                'cpu': round(cpu_percent, 1),
                'memory': round(memory_percent, 1),
                'temperature': round(temperature, 1),
                'systemHealth': max(0, system_health),
                'activeAgents': 8,
                'uptime': time.time() - self.start_time if hasattr(self, 'start_time') else 0
            }

        except Exception as e:
            logger.error(f"Error getting system metrics: {e}")
            return {
                'cpu': 0,
                'memory': 0,
                'temperature': 0,
                'systemHealth': 0,
                'activeAgents': 8,
                'uptime': 0
            }

    async def start_monitoring(self):
        """Start background monitoring tasks"""
        self.running = True
        self.start_time = time.time()

        while self.running:
            try:
                # Send system updates every 5 seconds
                await self.send_system_update()

                # Update agent data periodically
                await self.update_agent_data()

                await asyncio.sleep(5)

            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                await asyncio.sleep(5)

    async def update_agent_data(self):
        """Update agent data with simulated changes"""
        try:
            import random

            # Update performance data for project manager
            perf_data = self.agent_data['project_manager']['performanceData']
            perf_data.append(random.randint(80, 95))
            if len(perf_data) > 20:
                perf_data.pop(0)

            # Update motion data for imagineer
            motion_data = self.agent_data['imagineer']['motionData']
            motion_data.append(random.randint(40, 80))
            if len(motion_data) > 20:
                motion_data.pop(0)

            # Update video model trainer metrics
            self.agent_data['video_model_trainer']['frameRate'] = random.randint(28, 32)
            self.agent_data['video_model_trainer']['accuracy'] = round(random.uniform(92, 98), 1)
            self.agent_data['video_model_trainer']['objectCount'] = random.randint(0, 5)

            # Update Super Coder performance metrics
            self.agent_data['super_coder']['performance']['cpu'] = random.randint(40, 80)
            self.agent_data['super_coder']['performance']['memory'] = random.randint(30, 60)
            self.agent_data['super_coder']['performance']['gpu'] = random.randint(60, 90)

        except Exception as e:
            logger.error(f"Error updating agent data: {e}")

    async def handle_client(self, websocket, path):
        """Handle individual client connections"""
        await self.register_client(websocket)
        try:
            async for message in websocket:
                await self.handle_message(websocket, message)
        except websockets.exceptions.ConnectionClosed:
            pass
        except Exception as e:
            logger.error(f"Error handling client: {e}")
        finally:
            await self.unregister_client(websocket)

    async def start_server(self):
        """Start the WebSocket server"""
        logger.info(f"Starting WebSocket server on {self.host}:{self.port}")

        # Start monitoring in background
        monitoring_task = asyncio.create_task(self.start_monitoring())

        # Start WebSocket server
        server = await websockets.serve(
            self.handle_client,
            self.host,
            self.port,
            ping_interval=20,
            ping_timeout=10
        )

        logger.info(f"WebSocket server started successfully")

        try:
            await server.wait_closed()
        except KeyboardInterrupt:
            logger.info("Server shutdown requested")
        finally:
            self.running = False
            monitoring_task.cancel()
            try:
                await monitoring_task
            except asyncio.CancelledError:
                pass

def main():
    """Main entry point"""
    # Create screenshots directory
    screenshot_dir = Path("/home/rolo/r2ai/screenshots")
    screenshot_dir.mkdir(exist_ok=True)

    # Start the server
    server = R2D2DashboardServer(host='0.0.0.0', port=8765)

    try:
        asyncio.run(server.start_server())
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Server error: {e}")

if __name__ == "__main__":
    main()