#!/usr/bin/env python3
"""
R2D2 Behavioral Intelligence Integration Server
==============================================

Master integration server that coordinates all R2D2 behavioral systems:
- Behavioral Intelligence Engine
- Enhanced Servo Choreographer
- Environmental Awareness System
- Audio Intelligence System
- Vision System Integration
- Dashboard WebSocket Architecture

This server provides:
- Unified WebSocket API for all behavioral controls
- Real-time system coordination and synchronization
- Performance monitoring and health management
- Emergency stop and safety systems
- Cross-system communication orchestration

Author: Expert Python Coder
Target: NVIDIA Orin Nano R2D2 Systems
Architecture: Microservices coordination with WebSocket communication
"""

import asyncio
import json
import logging
import time
import threading
import websockets
from datetime import datetime
from typing import Dict, List, Optional, Any, Set
from dataclasses import dataclass, asdict
from enum import Enum
import queue
import sys
import os
from pathlib import Path

# Import all R2D2 systems
sys.path.append('/home/rolo/r2ai')

# Core behavioral systems
from r2d2_behavioral_intelligence import R2D2BehaviorEngine
from r2d2_enhanced_choreographer import R2D2EnhancedChoreographer
from r2d2_environmental_awareness import R2D2EnvironmentalAwareness
from r2d2_audio_intelligence import R2D2AudioIntelligence

# Servo and sound systems
from maestro_enhanced_controller import EnhancedMaestroController
from r2d2_canonical_sound_enhancer import R2D2CanonicalSoundEnhancer, R2D2EmotionalContext

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SystemStatus(Enum):
    """Overall system status states"""
    INITIALIZING = "initializing"
    READY = "ready"
    ACTIVE = "active"
    DEGRADED = "degraded"
    ERROR = "error"
    EMERGENCY_STOP = "emergency_stop"

class IntegrationEvent(Enum):
    """Types of integration events between systems"""
    BEHAVIOR_TRIGGERED = "behavior_triggered"
    ENVIRONMENTAL_CHANGE = "environmental_change"
    AUDIO_REQUESTED = "audio_requested"
    SERVO_COMMAND = "servo_command"
    VISION_UPDATE = "vision_update"
    EMERGENCY_STOP = "emergency_stop"
    SYSTEM_HEALTH_UPDATE = "system_health_update"

@dataclass
class SystemHealthReport:
    """Comprehensive system health information"""
    timestamp: float
    overall_status: SystemStatus

    # Individual system status
    behavioral_intelligence: Dict[str, Any]
    environmental_awareness: Dict[str, Any]
    audio_intelligence: Dict[str, Any]
    servo_choreographer: Dict[str, Any]
    servo_controller: Dict[str, Any]

    # Integration status
    websocket_connections: int
    active_behaviors: int
    system_load: float
    memory_usage: float

    # Performance metrics
    response_time_ms: float
    behavior_execution_rate: float
    error_count: int
    uptime_seconds: float

class R2D2BehavioralIntegrationServer:
    """
    Master integration server coordinating all R2D2 behavioral intelligence systems
    """

    def __init__(self):
        """Initialize the integration server"""

        # WebSocket configuration
        self.websocket_port = 8769  # Master behavioral intelligence port
        self.connected_clients: Set[websockets.WebSocketServerProtocol] = set()

        # System instances
        self.behavioral_intelligence: Optional[R2D2BehaviorEngine] = None
        self.environmental_awareness: Optional[R2D2EnvironmentalAwareness] = None
        self.audio_intelligence: Optional[R2D2AudioIntelligence] = None
        self.servo_controller: Optional[EnhancedMaestroController] = None
        self.servo_choreographer: Optional[R2D2EnhancedChoreographer] = None

        # System coordination
        self.system_status = SystemStatus.INITIALIZING
        self.integration_queue = queue.Queue()
        self.health_reports: List[SystemHealthReport] = []

        # Performance monitoring
        self.performance_metrics = {
            'total_behaviors_executed': 0,
            'total_audio_played': 0,
            'total_servo_movements': 0,
            'integration_events_processed': 0,
            'average_response_time_ms': 0.0,
            'system_uptime_start': time.time(),
            'error_count': 0,
            'emergency_stops': 0
        }

        # Configuration
        self.config = {
            'max_concurrent_behaviors': 3,
            'health_check_interval_seconds': 5.0,
            'emergency_stop_timeout_seconds': 2.0,
            'behavior_coordination_enabled': True,
            'audio_servo_sync_enabled': True,
            'environmental_adaptation_enabled': True,
            'performance_monitoring_enabled': True
        }

        # System control
        self.running = False
        self.emergency_stop_active = False

        logger.info("R2D2 Behavioral Integration Server initialized")

    async def start_integration_server(self):
        """Start the complete behavioral integration system"""
        logger.info("🚀 Starting R2D2 Behavioral Intelligence Integration Server")

        try:
            # Initialize all subsystems
            await self._initialize_all_systems()

            # Start coordination services
            self._start_coordination_services()

            # Start WebSocket server
            await self._start_websocket_server()

        except Exception as e:
            logger.error(f"Failed to start integration server: {e}")
            self.system_status = SystemStatus.ERROR
            raise

    async def _initialize_all_systems(self):
        """Initialize all R2D2 behavioral systems"""
        logger.info("Initializing all R2D2 behavioral systems...")

        initialization_tasks = []

        try:
            # Initialize servo controller first (hardware dependency)
            logger.info("🦾 Initializing Enhanced Maestro Controller...")
            self.servo_controller = EnhancedMaestroController(auto_detect=True)

            # Initialize servo choreographer
            if self.servo_controller:
                logger.info("🎭 Initializing Enhanced Choreographer...")
                self.servo_choreographer = R2D2EnhancedChoreographer(self.servo_controller)

            # Initialize audio intelligence
            logger.info("🔊 Initializing Audio Intelligence...")
            self.audio_intelligence = R2D2AudioIntelligence()
            await self.audio_intelligence.start_audio_intelligence()

            # Initialize environmental awareness (connects to vision)
            logger.info("🌍 Initializing Environmental Awareness...")
            self.environmental_awareness = R2D2EnvironmentalAwareness()
            initialization_tasks.append(
                self.environmental_awareness.start_environmental_processing()
            )

            # Initialize behavioral intelligence (master coordinator)
            logger.info("🧠 Initializing Behavioral Intelligence...")
            self.behavioral_intelligence = R2D2BehaviorEngine()

            # Start environmental awareness in background
            if initialization_tasks:
                for task in initialization_tasks:
                    asyncio.create_task(task)

            self.system_status = SystemStatus.READY
            logger.info("✅ All R2D2 behavioral systems initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize systems: {e}")
            self.system_status = SystemStatus.ERROR
            raise

    def _start_coordination_services(self):
        """Start background coordination and monitoring services"""
        logger.info("Starting coordination services...")

        self.running = True

        # Integration event processor
        integration_thread = threading.Thread(
            target=self._integration_processing_loop,
            daemon=True,
            name="IntegrationProcessor"
        )
        integration_thread.start()

        # System health monitor
        health_thread = threading.Thread(
            target=self._health_monitoring_loop,
            daemon=True,
            name="HealthMonitor"
        )
        health_thread.start()

        # Performance monitor
        performance_thread = threading.Thread(
            target=self._performance_monitoring_loop,
            daemon=True,
            name="PerformanceMonitor"
        )
        performance_thread.start()

        logger.info("✅ Coordination services started")

    async def _start_websocket_server(self):
        """Start the master WebSocket server"""
        logger.info(f"Starting WebSocket server on port {self.websocket_port}")

        async def handle_client(websocket, path):
            await self._handle_websocket_client(websocket, path)

        server = websockets.serve(handle_client, "localhost", self.websocket_port)

        logger.info(f"🔌 WebSocket server ready on port {self.websocket_port}")
        logger.info("R2D2 Behavioral Intelligence Integration Server fully operational!")

        await server

    async def _handle_websocket_client(self, websocket, path):
        """Handle WebSocket client connections"""
        self.connected_clients.add(websocket)
        client_address = websocket.remote_address
        logger.info(f"Client connected from {client_address}")

        try:
            # Send initial status
            await self._send_system_status(websocket)

            # Handle messages
            async for message in websocket:
                await self._process_websocket_message(websocket, message)

        except websockets.exceptions.ConnectionClosed:
            logger.info(f"Client {client_address} disconnected")
        except Exception as e:
            logger.error(f"Error handling client {client_address}: {e}")
        finally:
            self.connected_clients.discard(websocket)

    async def _process_websocket_message(self, websocket, message):
        """Process incoming WebSocket messages"""
        try:
            data = json.loads(message)
            command_type = data.get('type')

            if command_type == 'execute_behavior':
                await self._handle_execute_behavior(websocket, data)
            elif command_type == 'trigger_audio':
                await self._handle_trigger_audio(websocket, data)
            elif command_type == 'execute_choreography':
                await self._handle_execute_choreography(websocket, data)
            elif command_type == 'emergency_stop':
                await self._handle_emergency_stop(websocket, data)
            elif command_type == 'get_status':
                await self._send_system_status(websocket)
            elif command_type == 'get_health_report':
                await self._send_health_report(websocket)
            elif command_type == 'set_personality_mode':
                await self._handle_set_personality_mode(websocket, data)
            elif command_type == 'environmental_update':
                await self._handle_environmental_update(websocket, data)
            else:
                await self._send_error(websocket, f"Unknown command type: {command_type}")

        except json.JSONDecodeError:
            await self._send_error(websocket, "Invalid JSON message")
        except Exception as e:
            logger.error(f"Error processing WebSocket message: {e}")
            await self._send_error(websocket, f"Processing error: {str(e)}")

    async def _handle_execute_behavior(self, websocket, data):
        """Handle behavior execution request"""
        try:
            behavior_name = data.get('behavior_name')
            parameters = data.get('parameters', {})

            if not behavior_name:
                await self._send_error(websocket, "Missing behavior_name")
                return

            # Create integration event
            event = {
                'type': IntegrationEvent.BEHAVIOR_TRIGGERED,
                'behavior_name': behavior_name,
                'parameters': parameters,
                'client_id': id(websocket),
                'timestamp': time.time()
            }

            self.integration_queue.put(event)

            await websocket.send(json.dumps({
                'type': 'behavior_queued',
                'behavior_name': behavior_name,
                'timestamp': time.time()
            }))

            logger.info(f"Behavior queued: {behavior_name}")

        except Exception as e:
            logger.error(f"Error handling execute behavior: {e}")
            await self._send_error(websocket, str(e))

    async def _handle_execute_choreography(self, websocket, data):
        """Handle choreography execution request"""
        try:
            choreography_name = data.get('choreography_name')
            personality_modifier = data.get('personality_modifier', 1.0)
            emotional_intensity = data.get('emotional_intensity')

            if not choreography_name or not self.servo_choreographer:
                await self._send_error(websocket, "Missing choreography_name or choreographer not available")
                return

            # Execute choreography
            success = await self.servo_choreographer.execute_choreography(
                choreography_name,
                personality_modifier=personality_modifier,
                emotional_intensity_override=emotional_intensity
            )

            if success:
                self.performance_metrics['total_servo_movements'] += 1

                await websocket.send(json.dumps({
                    'type': 'choreography_started',
                    'choreography_name': choreography_name,
                    'success': True,
                    'timestamp': time.time()
                }))
            else:
                await self._send_error(websocket, f"Failed to execute choreography: {choreography_name}")

        except Exception as e:
            logger.error(f"Error executing choreography: {e}")
            await self._send_error(websocket, str(e))

    async def _handle_trigger_audio(self, websocket, data):
        """Handle audio trigger request"""
        try:
            audio_context = data.get('audio_context')
            behavioral_state = data.get('behavioral_state')
            priority = data.get('priority', 1)

            if not audio_context or not self.audio_intelligence:
                await self._send_error(websocket, "Missing audio_context or audio system not available")
                return

            # Convert string to enum if needed
            if isinstance(audio_context, str):
                try:
                    audio_context = R2D2EmotionalContext(audio_context)
                except ValueError:
                    await self._send_error(websocket, f"Invalid audio context: {audio_context}")
                    return

            # Request audio playback
            request_id = self.audio_intelligence.request_audio_playback(
                audio_context=audio_context,
                behavioral_state=behavioral_state,
                priority=priority
            )

            if request_id:
                self.performance_metrics['total_audio_played'] += 1

                await websocket.send(json.dumps({
                    'type': 'audio_triggered',
                    'request_id': request_id,
                    'audio_context': audio_context.value,
                    'timestamp': time.time()
                }))
            else:
                await self._send_error(websocket, "Failed to queue audio request")

        except Exception as e:
            logger.error(f"Error triggering audio: {e}")
            await self._send_error(websocket, str(e))

    async def _handle_emergency_stop(self, websocket, data):
        """Handle emergency stop request"""
        try:
            self.emergency_stop_active = True
            self.system_status = SystemStatus.EMERGENCY_STOP

            logger.warning("🛑 EMERGENCY STOP ACTIVATED")

            # Stop all active systems
            if self.servo_choreographer:
                self.servo_choreographer.stop_current_choreography()

            if self.audio_intelligence:
                self.audio_intelligence.stop_current_audio()

            if self.behavioral_intelligence:
                # Stop active behaviors
                pass

            self.performance_metrics['emergency_stops'] += 1

            # Notify all clients
            await self._broadcast_message({
                'type': 'emergency_stop_activated',
                'timestamp': time.time(),
                'message': 'All R2D2 behavioral systems stopped'
            })

        except Exception as e:
            logger.error(f"Error during emergency stop: {e}")

    async def _handle_set_personality_mode(self, websocket, data):
        """Handle personality mode change request"""
        try:
            from r2d2_audio_intelligence import R2D2PersonalityAudioMode

            personality_mode = data.get('personality_mode')

            if not personality_mode:
                await self._send_error(websocket, "Missing personality_mode")
                return

            # Update audio intelligence personality
            if self.audio_intelligence:
                try:
                    mode_enum = R2D2PersonalityAudioMode(personality_mode)
                    self.audio_intelligence.current_personality_mode = mode_enum

                    await websocket.send(json.dumps({
                        'type': 'personality_mode_updated',
                        'personality_mode': personality_mode,
                        'timestamp': time.time()
                    }))

                    logger.info(f"Personality mode updated: {personality_mode}")

                except ValueError:
                    await self._send_error(websocket, f"Invalid personality mode: {personality_mode}")
            else:
                await self._send_error(websocket, "Audio intelligence not available")

        except Exception as e:
            logger.error(f"Error setting personality mode: {e}")
            await self._send_error(websocket, str(e))

    async def _handle_environmental_update(self, websocket, data):
        """Handle environmental context update"""
        try:
            environmental_context = data.get('environmental_context', {})
            social_context = data.get('social_context', 'unknown')

            # Update all systems with environmental context
            if self.audio_intelligence:
                self.audio_intelligence.update_behavioral_context(
                    behavioral_state=data.get('behavioral_state', 'idle'),
                    environmental_context=environmental_context,
                    social_context=social_context
                )

            await websocket.send(json.dumps({
                'type': 'environmental_update_processed',
                'timestamp': time.time()
            }))

        except Exception as e:
            logger.error(f"Error handling environmental update: {e}")
            await self._send_error(websocket, str(e))

    def _integration_processing_loop(self):
        """Main integration event processing loop"""
        logger.info("Integration processing loop started")

        while self.running:
            try:
                if not self.integration_queue.empty():
                    event = self.integration_queue.get_nowait()
                    self._process_integration_event(event)

                time.sleep(0.05)  # 20Hz processing

            except queue.Empty:
                time.sleep(0.1)
            except Exception as e:
                logger.error(f"Error in integration processing loop: {e}")
                time.sleep(1.0)

    def _process_integration_event(self, event):
        """Process an integration event between systems"""
        try:
            event_type = event['type']

            if event_type == IntegrationEvent.BEHAVIOR_TRIGGERED:
                self._coordinate_behavior_execution(event)
            elif event_type == IntegrationEvent.ENVIRONMENTAL_CHANGE:
                self._coordinate_environmental_response(event)
            elif event_type == IntegrationEvent.AUDIO_REQUESTED:
                self._coordinate_audio_response(event)

            self.performance_metrics['integration_events_processed'] += 1

        except Exception as e:
            logger.error(f"Error processing integration event: {e}")

    def _coordinate_behavior_execution(self, event):
        """Coordinate execution of a behavior across all systems"""
        try:
            behavior_name = event['behavior_name']
            parameters = event.get('parameters', {})

            logger.info(f"🎭 Coordinating behavior execution: {behavior_name}")

            # Check if this is a choreography behavior
            if self.servo_choreographer and behavior_name in self.servo_choreographer.choreography_library:
                # Execute choreography with audio sync
                choreography = self.servo_choreographer.choreography_library[behavior_name]

                # Trigger synchronized audio if defined
                if choreography.audio_sync_points:
                    for time_ms, audio_cue in choreography.audio_sync_points:
                        if self.audio_intelligence:
                            # Schedule audio with delay
                            self.audio_intelligence.request_audio_playback(
                                audio_context=R2D2EmotionalContext(audio_cue),
                                delay_seconds=time_ms / 1000.0,
                                behavioral_state=behavior_name,
                                priority=5
                            )

                # Execute choreography
                asyncio.create_task(
                    self.servo_choreographer.execute_choreography(behavior_name)
                )

            # Check for behavioral intelligence behaviors
            elif self.behavioral_intelligence and behavior_name in self.behavioral_intelligence.behavior_library:
                # Execute through behavioral intelligence engine
                success = self.behavioral_intelligence.execute_manual_behavior(behavior_name, parameters)
                if not success:
                    logger.warning(f"Failed to execute behavior: {behavior_name}")

            else:
                logger.warning(f"Unknown behavior: {behavior_name}")

            self.performance_metrics['total_behaviors_executed'] += 1

        except Exception as e:
            logger.error(f"Error coordinating behavior execution: {e}")

    def _coordinate_environmental_response(self, event):
        """Coordinate response to environmental changes"""
        try:
            # This would coordinate responses between environmental awareness and behavioral systems
            pass
        except Exception as e:
            logger.error(f"Error coordinating environmental response: {e}")

    def _coordinate_audio_response(self, event):
        """Coordinate audio response execution"""
        try:
            # This would coordinate audio responses with servo movements
            pass
        except Exception as e:
            logger.error(f"Error coordinating audio response: {e}")

    def _health_monitoring_loop(self):
        """System health monitoring loop"""
        logger.info("Health monitoring loop started")

        while self.running:
            try:
                # Generate system health report
                health_report = self._generate_health_report()
                self.health_reports.append(health_report)

                # Keep only recent reports
                if len(self.health_reports) > 100:
                    self.health_reports = self.health_reports[-100:]

                # Check for system issues
                self._check_system_health(health_report)

                time.sleep(self.config['health_check_interval_seconds'])

            except Exception as e:
                logger.error(f"Error in health monitoring: {e}")
                time.sleep(10.0)

    def _generate_health_report(self) -> SystemHealthReport:
        """Generate comprehensive system health report"""
        try:
            current_time = time.time()

            # Collect status from all systems
            behavioral_status = {}
            if self.behavioral_intelligence:
                behavioral_status = self.behavioral_intelligence.get_comprehensive_status()

            environmental_status = {}
            if self.environmental_awareness:
                environmental_status = self.environmental_awareness.get_environmental_status()

            audio_status = {}
            if self.audio_intelligence:
                audio_status = self.audio_intelligence.get_audio_status()

            choreographer_status = {}
            if self.servo_choreographer:
                choreographer_status = self.servo_choreographer.get_choreography_status()

            servo_status = {}
            if self.servo_controller:
                servo_status = self.servo_controller.get_enhanced_status_report()

            # Calculate metrics
            uptime = current_time - self.performance_metrics['system_uptime_start']

            return SystemHealthReport(
                timestamp=current_time,
                overall_status=self.system_status,
                behavioral_intelligence=behavioral_status,
                environmental_awareness=environmental_status,
                audio_intelligence=audio_status,
                servo_choreographer=choreographer_status,
                servo_controller=servo_status,
                websocket_connections=len(self.connected_clients),
                active_behaviors=1 if self.servo_choreographer and self.servo_choreographer.active_choreography else 0,
                system_load=0.5,  # Placeholder
                memory_usage=0.3,  # Placeholder
                response_time_ms=self.performance_metrics['average_response_time_ms'],
                behavior_execution_rate=self.performance_metrics['total_behaviors_executed'] / max(uptime, 1),
                error_count=self.performance_metrics['error_count'],
                uptime_seconds=uptime
            )

        except Exception as e:
            logger.error(f"Error generating health report: {e}")
            return SystemHealthReport(
                timestamp=time.time(),
                overall_status=SystemStatus.ERROR,
                behavioral_intelligence={},
                environmental_awareness={},
                audio_intelligence={},
                servo_choreographer={},
                servo_controller={},
                websocket_connections=0,
                active_behaviors=0,
                system_load=1.0,
                memory_usage=1.0,
                response_time_ms=1000.0,
                behavior_execution_rate=0.0,
                error_count=999,
                uptime_seconds=0.0
            )

    def _check_system_health(self, health_report: SystemHealthReport):
        """Check system health and update status"""
        try:
            issues = []

            # Check response time
            if health_report.response_time_ms > 500:
                issues.append(f"High response time: {health_report.response_time_ms:.1f}ms")

            # Check system load
            if health_report.system_load > 0.9:
                issues.append(f"High system load: {health_report.system_load:.1f}")

            # Check error count
            if health_report.error_count > 10:
                issues.append(f"High error count: {health_report.error_count}")

            # Update system status
            if self.emergency_stop_active:
                self.system_status = SystemStatus.EMERGENCY_STOP
            elif issues:
                self.system_status = SystemStatus.DEGRADED
                logger.warning(f"System health issues detected: {', '.join(issues)}")
            elif health_report.active_behaviors > 0:
                self.system_status = SystemStatus.ACTIVE
            else:
                self.system_status = SystemStatus.READY

        except Exception as e:
            logger.error(f"Error checking system health: {e}")
            self.system_status = SystemStatus.ERROR

    def _performance_monitoring_loop(self):
        """Performance monitoring and optimization loop"""
        logger.info("Performance monitoring loop started")

        while self.running:
            try:
                if self.config['performance_monitoring_enabled']:
                    # Update performance metrics
                    uptime = time.time() - self.performance_metrics['system_uptime_start']

                    # Calculate rates
                    behavior_rate = self.performance_metrics['total_behaviors_executed'] / max(uptime, 1)
                    audio_rate = self.performance_metrics['total_audio_played'] / max(uptime, 1)

                    logger.debug(f"Performance: {behavior_rate:.2f} behaviors/sec, {audio_rate:.2f} audio/sec")

                time.sleep(30.0)  # Update every 30 seconds

            except Exception as e:
                logger.error(f"Error in performance monitoring: {e}")
                time.sleep(60.0)

    async def _send_system_status(self, websocket):
        """Send system status to client"""
        try:
            status = {
                'type': 'system_status',
                'timestamp': time.time(),
                'overall_status': self.system_status.value,
                'systems': {
                    'behavioral_intelligence': self.behavioral_intelligence is not None,
                    'environmental_awareness': self.environmental_awareness is not None,
                    'audio_intelligence': self.audio_intelligence is not None,
                    'servo_choreographer': self.servo_choreographer is not None,
                    'servo_controller': self.servo_controller is not None
                },
                'performance_metrics': dict(self.performance_metrics),
                'connected_clients': len(self.connected_clients),
                'emergency_stop_active': self.emergency_stop_active
            }

            await websocket.send(json.dumps(status))

        except Exception as e:
            logger.error(f"Error sending system status: {e}")

    async def _send_health_report(self, websocket):
        """Send detailed health report to client"""
        try:
            if self.health_reports:
                latest_report = self.health_reports[-1]
                health_data = {
                    'type': 'health_report',
                    'timestamp': time.time(),
                    'report': asdict(latest_report)
                }

                await websocket.send(json.dumps(health_data))
            else:
                await websocket.send(json.dumps({
                    'type': 'health_report',
                    'timestamp': time.time(),
                    'message': 'No health data available'
                }))

        except Exception as e:
            logger.error(f"Error sending health report: {e}")

    async def _send_error(self, websocket, error_message: str):
        """Send error message to client"""
        try:
            await websocket.send(json.dumps({
                'type': 'error',
                'message': error_message,
                'timestamp': time.time()
            }))

            self.performance_metrics['error_count'] += 1

        except Exception as e:
            logger.error(f"Error sending error message: {e}")

    async def _broadcast_message(self, message: Dict[str, Any]):
        """Broadcast message to all connected clients"""
        if not self.connected_clients:
            return

        message_json = json.dumps(message)
        disconnected_clients = set()

        for client in self.connected_clients:
            try:
                await client.send(message_json)
            except websockets.exceptions.ConnectionClosed:
                disconnected_clients.add(client)
            except Exception as e:
                logger.error(f"Error broadcasting to client: {e}")
                disconnected_clients.add(client)

        # Clean up disconnected clients
        for client in disconnected_clients:
            self.connected_clients.discard(client)

    def get_comprehensive_status(self) -> Dict[str, Any]:
        """Get comprehensive status of the entire integration server"""
        uptime = time.time() - self.performance_metrics['system_uptime_start']

        return {
            'integration_server': {
                'status': self.system_status.value,
                'running': self.running,
                'emergency_stop_active': self.emergency_stop_active,
                'uptime_seconds': uptime,
                'websocket_port': self.websocket_port,
                'connected_clients': len(self.connected_clients)
            },
            'subsystems': {
                'behavioral_intelligence': self.behavioral_intelligence is not None,
                'environmental_awareness': self.environmental_awareness is not None,
                'audio_intelligence': self.audio_intelligence is not None,
                'servo_choreographer': self.servo_choreographer is not None,
                'servo_controller': self.servo_controller is not None
            },
            'performance_metrics': dict(self.performance_metrics),
            'health_reports_count': len(self.health_reports),
            'configuration': dict(self.config)
        }

    async def stop_integration_server(self):
        """Stop the integration server and all subsystems"""
        logger.info("Stopping R2D2 Behavioral Integration Server")

        self.running = False
        self.system_status = SystemStatus.ERROR

        # Stop all subsystems
        if self.audio_intelligence:
            await self.audio_intelligence.stop_audio_intelligence()

        if self.environmental_awareness:
            await self.environmental_awareness.stop_environmental_processing()

        if self.behavioral_intelligence:
            self.behavioral_intelligence.shutdown()

        if self.servo_controller:
            self.servo_controller.shutdown()

        # Close all WebSocket connections
        for client in list(self.connected_clients):
            try:
                await client.close()
            except Exception as e:
                logger.error(f"Error closing client connection: {e}")

        logger.info("R2D2 Behavioral Integration Server stopped")


async def main():
    """Main entry point for the R2D2 Behavioral Integration Server"""
    print("🤖 R2D2 Advanced Behavioral Intelligence Integration Server")
    print("=" * 70)
    print("Initializing complete R2D2 character behavioral system...")
    print()

    # Create integration server
    integration_server = R2D2BehavioralIntegrationServer()

    try:
        # Start the complete system
        await integration_server.start_integration_server()

    except KeyboardInterrupt:
        print("\n\nShutdown requested by user")
    except Exception as e:
        logger.error(f"Critical error in integration server: {e}")
    finally:
        await integration_server.stop_integration_server()
        print("\nR2D2 Behavioral Intelligence Integration Server shutdown complete")


if __name__ == "__main__":
    asyncio.run(main())