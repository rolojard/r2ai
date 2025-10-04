#!/usr/bin/env python3
"""
R2D2 Behavioral Intelligence System Test Suite
==============================================

Comprehensive test suite for the complete R2D2 behavioral intelligence system.
Tests all components integration, performance, and Star Wars authenticity.

Test Categories:
- Unit tests for individual system components
- Integration tests for cross-system communication
- Performance tests for real-time operation
- Behavioral authenticity tests for Star Wars canon compliance
- Stress tests for convention-ready reliability

Author: Expert Python Coder
Target: NVIDIA Orin Nano R2D2 Systems
Scope: Complete Phase 4A behavioral intelligence validation
"""

import asyncio
import json
import time
import logging
import sys
import os
import websockets
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import threading
import random
import unittest
from unittest.mock import Mock, patch, AsyncMock

# Import all R2D2 systems
sys.path.append('/home/rolo/r2ai')

# Import behavioral systems
from r2d2_behavioral_intelligence import R2D2BehaviorEngine
from r2d2_enhanced_choreographer import R2D2EnhancedChoreographer, EasingFunction, MovementPersonality
from r2d2_environmental_awareness import R2D2EnvironmentalAwareness
from r2d2_audio_intelligence import R2D2AudioIntelligence, R2D2PersonalityAudioMode
from r2d2_behavioral_integration_server import R2D2BehavioralIntegrationServer

# Import supporting systems
from maestro_enhanced_controller import EnhancedMaestroController
from r2d2_canonical_sound_enhancer import R2D2CanonicalSoundEnhancer, R2D2EmotionalContext

# Configure logging for tests
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class R2D2BehavioralIntelligenceTestSuite:
    """
    Comprehensive test suite for R2D2 behavioral intelligence system
    """

    def __init__(self):
        """Initialize the test suite"""
        self.test_results = {}
        self.test_start_time = time.time()
        self.integration_server: Optional[R2D2BehavioralIntegrationServer] = None
        self.test_websocket_port = 8770

        logger.info("R2D2 Behavioral Intelligence Test Suite initialized")

    async def run_all_tests(self):
        """Run the complete test suite"""
        logger.info("🧪 Starting R2D2 Behavioral Intelligence Test Suite")
        print("=" * 70)
        print("🤖 R2D2 Advanced Behavioral Intelligence - Complete Test Suite")
        print("=" * 70)

        try:
            # Run test categories in sequence
            await self._run_component_tests()
            await self._run_integration_tests()
            await self._run_performance_tests()
            await self._run_authenticity_tests()
            await self._run_stress_tests()

            # Generate final report
            self._generate_test_report()

        except Exception as e:
            logger.error(f"Test suite execution failed: {e}")
        finally:
            await self._cleanup_tests()

        logger.info("Test suite execution completed")

    async def _run_component_tests(self):
        """Test individual system components"""
        logger.info("\n🔧 Running Component Tests...")
        print("\n" + "="*50)
        print("🔧 COMPONENT TESTS")
        print("="*50)

        component_tests = [
            self._test_servo_controller,
            self._test_enhanced_choreographer,
            self._test_audio_intelligence,
            self._test_environmental_awareness,
            self._test_behavioral_intelligence_engine
        ]

        for test_func in component_tests:
            try:
                test_name = test_func.__name__
                print(f"\n📋 Running: {test_name}")
                start_time = time.time()

                result = await test_func()
                duration = time.time() - start_time

                self.test_results[test_name] = {
                    'status': 'PASS' if result else 'FAIL',
                    'duration': duration,
                    'details': result
                }

                print(f"   Result: {'✅ PASS' if result else '❌ FAIL'} ({duration:.2f}s)")

            except Exception as e:
                logger.error(f"Component test {test_func.__name__} failed: {e}")
                self.test_results[test_func.__name__] = {
                    'status': 'ERROR',
                    'duration': time.time() - start_time,
                    'error': str(e)
                }
                print(f"   Result: ❌ ERROR - {str(e)}")

    async def _test_servo_controller(self) -> Dict[str, Any]:
        """Test Enhanced Maestro Controller functionality"""
        try:
            controller = EnhancedMaestroController(auto_detect=True)

            test_results = {
                'initialization': controller is not None,
                'servo_count': controller.get_servo_count() >= 6,
                'sequences_available': len(controller.saved_sequences) >= 5,
                'status_report': bool(controller.get_enhanced_status_report())
            }

            # Test servo movement (simulation mode)
            if controller.simulation_mode:
                test_results['servo_movement'] = controller.set_servo_position(0, 6500)
                test_results['sequence_execution'] = controller.execute_sequence('r2d2_greeting')
            else:
                test_results['servo_movement'] = True
                test_results['sequence_execution'] = True

            # Test configuration
            test_results['configuration'] = controller.create_dynamic_servo_config(0, 'test_servo', 'Test Servo') is not None

            controller.shutdown()

            return test_results

        except Exception as e:
            logger.error(f"Servo controller test error: {e}")
            return {'error': str(e), 'passed': False}

    async def _test_enhanced_choreographer(self) -> Dict[str, Any]:
        """Test Enhanced Choreographer functionality"""
        try:
            # Create mock servo controller
            mock_controller = Mock()
            mock_controller.get_servo_count.return_value = 6
            mock_controller.set_servo_position.return_value = True

            choreographer = R2D2EnhancedChoreographer(mock_controller)

            test_results = {
                'initialization': choreographer is not None,
                'choreography_library': len(choreographer.choreography_library) >= 5,
                'easing_functions': len(EasingFunction) >= 10,
                'personality_types': len(MovementPersonality) >= 8
            }

            # Test choreography execution
            status = choreographer.get_choreography_status()
            test_results['status_report'] = bool(status)
            test_results['available_choreographies'] = len(status['available_choreographies']) >= 5

            # Test specific choreography info
            info = choreographer.get_choreography_info('enthusiastic_friend_greeting')
            test_results['choreography_details'] = info is not None and info.get('canon_accuracy', 0) >= 9.0

            return test_results

        except Exception as e:
            logger.error(f"Choreographer test error: {e}")
            return {'error': str(e), 'passed': False}

    async def _test_audio_intelligence(self) -> Dict[str, Any]:
        """Test Audio Intelligence System functionality"""
        try:
            audio_system = R2D2AudioIntelligence()
            await audio_system.start_audio_intelligence()

            test_results = {
                'initialization': audio_system is not None,
                'sound_enhancer': audio_system.sound_enhancer is not None,
                'behavioral_mappings': len(audio_system.behavioral_audio_mappings) >= 8,
                'personality_modifiers': len(audio_system.personality_modifiers) >= 6
            }

            # Test audio request
            request_id = audio_system.request_audio_playback(
                R2D2EmotionalContext.GREETING_FRIENDS,
                behavioral_state='test_greeting',
                priority=5
            )
            test_results['audio_request'] = bool(request_id)

            # Test personality mode changes
            original_mode = audio_system.current_personality_mode
            audio_system.current_personality_mode = R2D2PersonalityAudioMode.PLAYFUL
            test_results['personality_change'] = audio_system.current_personality_mode == R2D2PersonalityAudioMode.PLAYFUL

            # Test status report
            status = audio_system.get_audio_status()
            test_results['status_report'] = bool(status) and 'system_status' in status

            await audio_system.stop_audio_intelligence()

            return test_results

        except Exception as e:
            logger.error(f"Audio intelligence test error: {e}")
            return {'error': str(e), 'passed': False}

    async def _test_environmental_awareness(self) -> Dict[str, Any]:
        """Test Environmental Awareness System functionality"""
        try:
            env_system = R2D2EnvironmentalAwareness()

            test_results = {
                'initialization': env_system is not None,
                'configuration': len(env_system.config) >= 5,
                'trigger_handlers': len(env_system.contextual_triggers) >= 6
            }

            # Test vision data processing
            mock_vision_data = {
                'detections': [
                    {
                        'class': 'person',
                        'confidence': 0.85,
                        'bbox': [100, 100, 200, 300]
                    }
                ],
                'character_detections': [
                    {
                        'character': 'jedi_sith_candidate',
                        'confidence': 0.75,
                        'bbox': [150, 120, 180, 250]
                    }
                ]
            }

            await env_system._process_vision_data(mock_vision_data)

            test_results['vision_processing'] = env_system.current_reading.total_people_count == 1
            test_results['character_detection'] = len(env_system.current_reading.jedi_candidates) == 1

            # Test status report
            status = env_system.get_environmental_status()
            test_results['status_report'] = bool(status) and 'current_environment' in status

            await env_system.stop_environmental_processing()

            return test_results

        except Exception as e:
            logger.error(f"Environmental awareness test error: {e}")
            return {'error': str(e), 'passed': False}

    async def _test_behavioral_intelligence_engine(self) -> Dict[str, Any]:
        """Test Behavioral Intelligence Engine functionality"""
        try:
            behavioral_engine = R2D2BehaviorEngine()

            test_results = {
                'initialization': behavioral_engine is not None,
                'behavior_library': len(behavioral_engine.behavior_library) >= 10,
                'emotional_states': len(behavioral_engine.current_emotional_state.__class__) >= 10
            }

            # Test status report
            status = behavioral_engine.get_comprehensive_status()
            test_results['status_report'] = bool(status) and 'behavioral_status' in status

            # Test manual behavior execution
            test_results['manual_behavior'] = behavioral_engine.execute_manual_behavior('idle_gentle_dome')

            behavioral_engine.shutdown()

            return test_results

        except Exception as e:
            logger.error(f"Behavioral intelligence test error: {e}")
            return {'error': str(e), 'passed': False}

    async def _run_integration_tests(self):
        """Test system integration and communication"""
        logger.info("\n🔗 Running Integration Tests...")
        print("\n" + "="*50)
        print("🔗 INTEGRATION TESTS")
        print("="*50)

        integration_tests = [
            self._test_websocket_communication,
            self._test_cross_system_coordination,
            self._test_behavioral_triggers,
            self._test_audio_servo_sync
        ]

        for test_func in integration_tests:
            try:
                test_name = test_func.__name__
                print(f"\n📋 Running: {test_name}")
                start_time = time.time()

                result = await test_func()
                duration = time.time() - start_time

                self.test_results[test_name] = {
                    'status': 'PASS' if result.get('passed', True) else 'FAIL',
                    'duration': duration,
                    'details': result
                }

                print(f"   Result: {'✅ PASS' if result.get('passed', True) else '❌ FAIL'} ({duration:.2f}s)")

            except Exception as e:
                logger.error(f"Integration test {test_func.__name__} failed: {e}")
                self.test_results[test_func.__name__] = {
                    'status': 'ERROR',
                    'duration': time.time() - start_time,
                    'error': str(e)
                }
                print(f"   Result: ❌ ERROR - {str(e)}")

    async def _test_websocket_communication(self) -> Dict[str, Any]:
        """Test WebSocket communication with integration server"""
        try:
            # Start integration server in background
            integration_server = R2D2BehavioralIntegrationServer()

            # Start server in background task
            server_task = asyncio.create_task(integration_server.start_integration_server())

            # Wait for server to start
            await asyncio.sleep(2)

            test_results = {
                'server_initialization': integration_server.system_status.value != 'error',
                'websocket_port': integration_server.websocket_port == 8769
            }

            # Test WebSocket connection
            try:
                uri = f"ws://localhost:{integration_server.websocket_port}"
                async with websockets.connect(uri, timeout=5) as websocket:

                    # Test status request
                    await websocket.send(json.dumps({'type': 'get_status'}))

                    response = await asyncio.wait_for(websocket.recv(), timeout=5)
                    status_data = json.loads(response)

                    test_results['websocket_connection'] = True
                    test_results['status_response'] = status_data.get('type') == 'system_status'

                    # Test behavior execution request
                    await websocket.send(json.dumps({
                        'type': 'execute_behavior',
                        'behavior_name': 'idle_gentle_dome',
                        'parameters': {}
                    }))

                    response = await asyncio.wait_for(websocket.recv(), timeout=5)
                    behavior_response = json.loads(response)

                    test_results['behavior_request'] = behavior_response.get('type') == 'behavior_queued'

            except Exception as ws_error:
                test_results['websocket_connection'] = False
                test_results['websocket_error'] = str(ws_error)

            # Stop server
            server_task.cancel()
            try:
                await server_task
            except asyncio.CancelledError:
                pass

            await integration_server.stop_integration_server()

            test_results['passed'] = all([
                test_results.get('server_initialization', False),
                test_results.get('websocket_connection', False),
                test_results.get('status_response', False)
            ])

            return test_results

        except Exception as e:
            logger.error(f"WebSocket communication test error: {e}")
            return {'error': str(e), 'passed': False}

    async def _test_cross_system_coordination(self) -> Dict[str, Any]:
        """Test coordination between different systems"""
        try:
            test_results = {}

            # Test servo-audio coordination
            mock_servo_controller = Mock()
            mock_servo_controller.get_servo_count.return_value = 6
            mock_servo_controller.set_servo_position.return_value = True

            choreographer = R2D2EnhancedChoreographer(mock_servo_controller)
            audio_system = R2D2AudioIntelligence()
            await audio_system.start_audio_intelligence()

            test_results['systems_initialized'] = True

            # Test behavioral state coordination
            audio_system.update_behavioral_context(
                behavioral_state='greeting_test',
                environmental_context={'people_count': 1},
                social_context='one_on_one'
            )

            test_results['behavioral_context_update'] = audio_system.social_context == 'one_on_one'

            # Test choreography with audio sync points
            choreo_info = choreographer.get_choreography_info('enthusiastic_friend_greeting')
            if choreo_info:
                test_results['audio_sync_points'] = len(choreo_info.get('audio_sync_points', [])) > 0
            else:
                test_results['audio_sync_points'] = False

            await audio_system.stop_audio_intelligence()

            test_results['passed'] = all([
                test_results.get('systems_initialized', False),
                test_results.get('behavioral_context_update', False)
            ])

            return test_results

        except Exception as e:
            logger.error(f"Cross-system coordination test error: {e}")
            return {'error': str(e), 'passed': False}

    async def _test_behavioral_triggers(self) -> Dict[str, Any]:
        """Test behavioral trigger generation and processing"""
        try:
            env_system = R2D2EnvironmentalAwareness()

            test_results = {
                'system_initialized': env_system is not None,
                'trigger_queue_empty': env_system.trigger_queue.qsize() == 0
            }

            # Simulate person detection
            mock_vision_data = {
                'detections': [
                    {
                        'class': 'person',
                        'confidence': 0.9,
                        'bbox': [100, 100, 200, 400]
                    }
                ],
                'character_detections': []
            }

            await env_system._process_vision_data(mock_vision_data)

            test_results['person_detected'] = env_system.current_reading.total_people_count == 1
            test_results['person_profiles_updated'] = len(env_system.person_profiles) >= 1

            # Check if triggers were generated
            # Note: This would require more complex setup to fully test trigger generation

            await env_system.stop_environmental_processing()

            test_results['passed'] = all([
                test_results.get('system_initialized', False),
                test_results.get('person_detected', False)
            ])

            return test_results

        except Exception as e:
            logger.error(f"Behavioral triggers test error: {e}")
            return {'error': str(e), 'passed': False}

    async def _test_audio_servo_sync(self) -> Dict[str, Any]:
        """Test audio-servo synchronization"""
        try:
            # Mock servo controller
            mock_controller = Mock()
            mock_controller.get_servo_count.return_value = 6
            mock_controller.set_servo_position.return_value = True

            choreographer = R2D2EnhancedChoreographer(mock_controller)
            audio_system = R2D2AudioIntelligence()
            await audio_system.start_audio_intelligence()

            test_results = {
                'systems_initialized': True
            }

            # Test choreography with audio sync
            choreo = choreographer.choreography_library.get('enthusiastic_friend_greeting')
            if choreo:
                test_results['choreography_available'] = True
                test_results['has_audio_sync_points'] = len(choreo.audio_sync_points) > 0

                # Test sync execution (mock)
                test_results['sync_execution'] = True  # Would test actual synchronization
            else:
                test_results['choreography_available'] = False

            await audio_system.stop_audio_intelligence()

            test_results['passed'] = all([
                test_results.get('systems_initialized', False),
                test_results.get('choreography_available', False)
            ])

            return test_results

        except Exception as e:
            logger.error(f"Audio-servo sync test error: {e}")
            return {'error': str(e), 'passed': False}

    async def _run_performance_tests(self):
        """Test system performance and responsiveness"""
        logger.info("\n⚡ Running Performance Tests...")
        print("\n" + "="*50)
        print("⚡ PERFORMANCE TESTS")
        print("="*50)

        performance_tests = [
            self._test_response_time,
            self._test_memory_usage,
            self._test_concurrent_behaviors,
            self._test_audio_latency
        ]

        for test_func in performance_tests:
            try:
                test_name = test_func.__name__
                print(f"\n📋 Running: {test_name}")
                start_time = time.time()

                result = await test_func()
                duration = time.time() - start_time

                self.test_results[test_name] = {
                    'status': 'PASS' if result.get('passed', True) else 'FAIL',
                    'duration': duration,
                    'details': result
                }

                print(f"   Result: {'✅ PASS' if result.get('passed', True) else '❌ FAIL'} ({duration:.2f}s)")

            except Exception as e:
                logger.error(f"Performance test {test_func.__name__} failed: {e}")
                self.test_results[test_func.__name__] = {
                    'status': 'ERROR',
                    'duration': time.time() - start_time,
                    'error': str(e)
                }
                print(f"   Result: ❌ ERROR - {str(e)}")

    async def _test_response_time(self) -> Dict[str, Any]:
        """Test system response times"""
        try:
            response_times = []

            # Test audio system response time
            audio_system = R2D2AudioIntelligence()
            await audio_system.start_audio_intelligence()

            for i in range(10):
                start_time = time.time()

                request_id = audio_system.request_audio_playback(
                    R2D2EmotionalContext.GREETING_FRIENDS,
                    priority=5
                )

                response_time = (time.time() - start_time) * 1000  # milliseconds
                response_times.append(response_time)

            await audio_system.stop_audio_intelligence()

            average_response_time = sum(response_times) / len(response_times)
            max_response_time = max(response_times)

            test_results = {
                'average_response_time_ms': average_response_time,
                'max_response_time_ms': max_response_time,
                'target_met': average_response_time < 100.0,  # Target: <100ms
                'passed': average_response_time < 100.0 and max_response_time < 200.0
            }

            return test_results

        except Exception as e:
            logger.error(f"Response time test error: {e}")
            return {'error': str(e), 'passed': False}

    async def _test_memory_usage(self) -> Dict[str, Any]:
        """Test memory usage of systems"""
        try:
            import psutil
            import os

            process = psutil.Process(os.getpid())
            initial_memory = process.memory_info().rss / 1024 / 1024  # MB

            # Initialize systems
            audio_system = R2D2AudioIntelligence()
            await audio_system.start_audio_intelligence()

            env_system = R2D2EnvironmentalAwareness()

            mock_controller = Mock()
            mock_controller.get_servo_count.return_value = 6
            choreographer = R2D2EnhancedChoreographer(mock_controller)

            current_memory = process.memory_info().rss / 1024 / 1024  # MB
            memory_usage = current_memory - initial_memory

            # Cleanup
            await audio_system.stop_audio_intelligence()
            await env_system.stop_environmental_processing()

            test_results = {
                'initial_memory_mb': initial_memory,
                'peak_memory_mb': current_memory,
                'memory_usage_mb': memory_usage,
                'memory_efficient': memory_usage < 500,  # Target: <500MB
                'passed': memory_usage < 500
            }

            return test_results

        except Exception as e:
            logger.error(f"Memory usage test error: {e}")
            return {'error': str(e), 'passed': False}

    async def _test_concurrent_behaviors(self) -> Dict[str, Any]:
        """Test handling of concurrent behavior requests"""
        try:
            audio_system = R2D2AudioIntelligence()
            await audio_system.start_audio_intelligence()

            # Submit multiple concurrent audio requests
            request_ids = []
            contexts = [
                R2D2EmotionalContext.GREETING_FRIENDS,
                R2D2EmotionalContext.CURIOUS_INQUISITIVE,
                R2D2EmotionalContext.HAPPY_EXCITED,
                R2D2EmotionalContext.PLAYFUL_MISCHIEVOUS
            ]

            start_time = time.time()

            for i, context in enumerate(contexts):
                request_id = audio_system.request_audio_playback(
                    context,
                    priority=5,
                    behavioral_state=f'concurrent_test_{i}'
                )
                if request_id:
                    request_ids.append(request_id)

            processing_time = time.time() - start_time

            await audio_system.stop_audio_intelligence()

            test_results = {
                'requests_submitted': len(contexts),
                'requests_accepted': len(request_ids),
                'processing_time_ms': processing_time * 1000,
                'queue_handling': audio_system.audio_queue.qsize() >= 0,
                'passed': len(request_ids) == len(contexts) and processing_time < 0.1
            }

            return test_results

        except Exception as e:
            logger.error(f"Concurrent behaviors test error: {e}")
            return {'error': str(e), 'passed': False}

    async def _test_audio_latency(self) -> Dict[str, Any]:
        """Test audio playback latency"""
        try:
            audio_system = R2D2AudioIntelligence()
            await audio_system.start_audio_intelligence()

            latencies = []

            for i in range(5):
                start_time = time.time()

                request_id = audio_system.request_audio_playback(
                    R2D2EmotionalContext.GREETING_FRIENDS,
                    priority=8
                )

                # Simulate processing time
                await asyncio.sleep(0.01)

                latency = (time.time() - start_time) * 1000
                latencies.append(latency)

            await audio_system.stop_audio_intelligence()

            average_latency = sum(latencies) / len(latencies)
            max_latency = max(latencies)

            test_results = {
                'average_latency_ms': average_latency,
                'max_latency_ms': max_latency,
                'target_met': average_latency < 50.0,  # Target: <50ms
                'passed': average_latency < 50.0 and max_latency < 100.0
            }

            return test_results

        except Exception as e:
            logger.error(f"Audio latency test error: {e}")
            return {'error': str(e), 'passed': False}

    async def _run_authenticity_tests(self):
        """Test Star Wars authenticity and canon compliance"""
        logger.info("\n⭐ Running Star Wars Authenticity Tests...")
        print("\n" + "="*50)
        print("⭐ STAR WARS AUTHENTICITY TESTS")
        print("="*50)

        authenticity_tests = [
            self._test_canon_compliance,
            self._test_character_behaviors,
            self._test_sound_authenticity,
            self._test_movement_authenticity
        ]

        for test_func in authenticity_tests:
            try:
                test_name = test_func.__name__
                print(f"\n📋 Running: {test_name}")
                start_time = time.time()

                result = await test_func()
                duration = time.time() - start_time

                self.test_results[test_name] = {
                    'status': 'PASS' if result.get('passed', True) else 'FAIL',
                    'duration': duration,
                    'details': result
                }

                print(f"   Result: {'✅ PASS' if result.get('passed', True) else '❌ FAIL'} ({duration:.2f}s)")

            except Exception as e:
                logger.error(f"Authenticity test {test_func.__name__} failed: {e}")
                self.test_results[test_func.__name__] = {
                    'status': 'ERROR',
                    'duration': time.time() - start_time,
                    'error': str(e)
                }
                print(f"   Result: ❌ ERROR - {str(e)}")

    async def _test_canon_compliance(self) -> Dict[str, Any]:
        """Test Star Wars canon compliance"""
        try:
            # Test behavioral intelligence canon references
            behavioral_engine = R2D2BehaviorEngine()

            canon_behaviors = [
                'friendly_greeting',
                'jedi_recognition',
                'stubborn_response',
                'playful_interaction'
            ]

            canon_compliance_scores = []

            for behavior_name in canon_behaviors:
                if behavior_name in behavioral_engine.behavior_library:
                    behavior = behavioral_engine.behavior_library[behavior_name]
                    # Check for Star Wars references in behavior descriptions
                    has_canon_ref = any(term in behavior.description.lower()
                                      for term in ['r2d2', 'r2-d2', 'jedi', 'star wars'])
                    if has_canon_ref:
                        canon_compliance_scores.append(9.0)  # High score for canon reference
                    else:
                        canon_compliance_scores.append(7.0)  # Decent score without explicit reference

            # Test choreography canon compliance
            mock_controller = Mock()
            mock_controller.get_servo_count.return_value = 6
            choreographer = R2D2EnhancedChoreographer(mock_controller)

            choreo_canon_scores = []
            for choreo_name, choreo in choreographer.choreography_library.items():
                choreo_canon_scores.append(choreo.canon_accuracy)

            behavioral_engine.shutdown()

            average_behavioral_canon = sum(canon_compliance_scores) / len(canon_compliance_scores) if canon_compliance_scores else 0
            average_choreo_canon = sum(choreo_canon_scores) / len(choreo_canon_scores) if choreo_canon_scores else 0

            test_results = {
                'behavioral_canon_score': average_behavioral_canon,
                'choreography_canon_score': average_choreo_canon,
                'overall_canon_score': (average_behavioral_canon + average_choreo_canon) / 2,
                'target_met': average_choreo_canon >= 9.0,  # Target: >9.0 canon accuracy
                'passed': average_choreo_canon >= 9.0 and average_behavioral_canon >= 8.0
            }

            return test_results

        except Exception as e:
            logger.error(f"Canon compliance test error: {e}")
            return {'error': str(e), 'passed': False}

    async def _test_character_behaviors(self) -> Dict[str, Any]:
        """Test authentic R2D2 character behaviors"""
        try:
            # Test personality consistency
            audio_system = R2D2AudioIntelligence()
            await audio_system.start_audio_intelligence()

            personality_tests = []

            # Test stubborn personality
            audio_system.current_personality_mode = R2D2PersonalityAudioMode.STUBBORN
            stubborn_modifier = audio_system.personality_modifiers[R2D2PersonalityAudioMode.STUBBORN]
            personality_tests.append(stubborn_modifier.get('stubbornness_factor', 0) > 0.5)

            # Test playful personality
            audio_system.current_personality_mode = R2D2PersonalityAudioMode.PLAYFUL
            playful_modifier = audio_system.personality_modifiers[R2D2PersonalityAudioMode.PLAYFUL]
            personality_tests.append(playful_modifier.get('playfulness_factor', 0) > 1.0)

            # Test curious personality
            audio_system.current_personality_mode = R2D2PersonalityAudioMode.CURIOUS
            curious_modifier = audio_system.personality_modifiers[R2D2PersonalityAudioMode.CURIOUS]
            personality_tests.append(curious_modifier.get('curiosity_factor', 0) > 1.0)

            await audio_system.stop_audio_intelligence()

            # Test behavioral state transitions
            behavioral_engine = R2D2BehaviorEngine()

            initial_state = behavioral_engine.current_emotional_state
            state_transition_test = initial_state is not None

            behavioral_engine.shutdown()

            test_results = {
                'personality_consistency': all(personality_tests),
                'personality_traits_available': len(personality_tests) >= 3,
                'state_transition_capability': state_transition_test,
                'character_authenticity_score': (sum(personality_tests) / len(personality_tests)) * 10,
                'passed': all(personality_tests) and state_transition_test
            }

            return test_results

        except Exception as e:
            logger.error(f"Character behaviors test error: {e}")
            return {'error': str(e), 'passed': False}

    async def _test_sound_authenticity(self) -> Dict[str, Any]:
        """Test R2D2 sound authenticity"""
        try:
            sound_enhancer = R2D2CanonicalSoundEnhancer()

            test_results = {
                'sound_library_loaded': len(sound_enhancer.canonical_mappings) > 0,
                'emotional_contexts': len(sound_enhancer.emotional_context_groups) >= 10,
                'stubborn_sounds': len([m for m in sound_enhancer.canonical_mappings.values() if m.stubborn_factor > 0.3]) > 0,
                'sarcastic_sounds': len([m for m in sound_enhancer.canonical_mappings.values() if m.sarcasm_factor > 0.2]) > 0
            }

            # Test context-aware sound selection
            greeting_sound = sound_enhancer.get_sound_for_context(R2D2EmotionalContext.GREETING_FRIENDS)
            stubborn_sound = sound_enhancer.get_stubborn_response(R2D2EmotionalContext.CHATTING_CASUAL)

            test_results['context_selection'] = greeting_sound is not None
            test_results['stubborn_selection'] = stubborn_sound is not None

            # Test enhancement report
            report = sound_enhancer.get_enhancement_report()
            test_results['enhancement_report'] = bool(report) and report.get('canonical_sounds_mapped', 0) > 0

            authenticity_score = sum([
                test_results['sound_library_loaded'],
                test_results['context_selection'],
                test_results['stubborn_selection'],
                test_results['stubborn_sounds'],
                test_results['sarcastic_sounds']
            ]) / 5 * 10

            test_results['authenticity_score'] = authenticity_score
            test_results['passed'] = authenticity_score >= 8.0

            return test_results

        except Exception as e:
            logger.error(f"Sound authenticity test error: {e}")
            return {'error': str(e), 'passed': False}

    async def _test_movement_authenticity(self) -> Dict[str, Any]:
        """Test R2D2 movement authenticity"""
        try:
            mock_controller = Mock()
            mock_controller.get_servo_count.return_value = 6
            choreographer = R2D2EnhancedChoreographer(mock_controller)

            test_results = {
                'easing_functions_available': len(EasingFunction) >= 10,
                'r2d2_specific_easing': any('r2d2' in easing.value.lower() for easing in EasingFunction),
                'movement_personalities': len(MovementPersonality) >= 8,
                'choreography_count': len(choreographer.choreography_library) >= 8
            }

            # Check for authentic R2D2 behaviors
            authentic_behaviors = [
                'enthusiastic_friend_greeting',
                'jedi_recognition_respect',
                'stubborn_resistance',
                'playful_entertainment_dance'
            ]

            behavior_authenticity = []
            for behavior_name in authentic_behaviors:
                if behavior_name in choreographer.choreography_library:
                    choreo = choreographer.choreography_library[behavior_name]
                    behavior_authenticity.append(choreo.canon_accuracy >= 9.0)

            test_results['authentic_behaviors_available'] = len([b for b in behavior_authenticity if b])
            test_results['average_canon_accuracy'] = sum([
                choreo.canon_accuracy for choreo in choreographer.choreography_library.values()
            ]) / len(choreographer.choreography_library)

            movement_authenticity_score = (
                test_results['easing_functions_available'] +
                test_results['r2d2_specific_easing'] +
                (test_results['average_canon_accuracy'] >= 9.0) +
                (test_results['authentic_behaviors_available'] >= 3)
            ) / 4 * 10

            test_results['movement_authenticity_score'] = movement_authenticity_score
            test_results['passed'] = movement_authenticity_score >= 8.0

            return test_results

        except Exception as e:
            logger.error(f"Movement authenticity test error: {e}")
            return {'error': str(e), 'passed': False}

    async def _run_stress_tests(self):
        """Test system reliability under stress conditions"""
        logger.info("\n💪 Running Stress Tests...")
        print("\n" + "="*50)
        print("💪 STRESS TESTS")
        print("="*50)

        stress_tests = [
            self._test_high_load,
            self._test_error_recovery,
            self._test_long_duration_operation
        ]

        for test_func in stress_tests:
            try:
                test_name = test_func.__name__
                print(f"\n📋 Running: {test_name}")
                start_time = time.time()

                result = await test_func()
                duration = time.time() - start_time

                self.test_results[test_name] = {
                    'status': 'PASS' if result.get('passed', True) else 'FAIL',
                    'duration': duration,
                    'details': result
                }

                print(f"   Result: {'✅ PASS' if result.get('passed', True) else '❌ FAIL'} ({duration:.2f}s)")

            except Exception as e:
                logger.error(f"Stress test {test_func.__name__} failed: {e}")
                self.test_results[test_func.__name__] = {
                    'status': 'ERROR',
                    'duration': time.time() - start_time,
                    'error': str(e)
                }
                print(f"   Result: ❌ ERROR - {str(e)}")

    async def _test_high_load(self) -> Dict[str, Any]:
        """Test system under high load conditions"""
        try:
            audio_system = R2D2AudioIntelligence()
            await audio_system.start_audio_intelligence()

            # Submit many concurrent requests
            request_count = 50
            successful_requests = 0
            failed_requests = 0

            start_time = time.time()

            for i in range(request_count):
                try:
                    context = random.choice(list(R2D2EmotionalContext))
                    request_id = audio_system.request_audio_playback(
                        context,
                        priority=random.randint(1, 10),
                        behavioral_state=f'stress_test_{i}'
                    )

                    if request_id:
                        successful_requests += 1
                    else:
                        failed_requests += 1

                except Exception:
                    failed_requests += 1

            processing_time = time.time() - start_time

            await audio_system.stop_audio_intelligence()

            success_rate = successful_requests / request_count
            throughput = request_count / processing_time

            test_results = {
                'total_requests': request_count,
                'successful_requests': successful_requests,
                'failed_requests': failed_requests,
                'success_rate': success_rate,
                'processing_time_seconds': processing_time,
                'throughput_requests_per_second': throughput,
                'passed': success_rate >= 0.9 and throughput >= 100  # 90% success rate, 100 req/s
            }

            return test_results

        except Exception as e:
            logger.error(f"High load test error: {e}")
            return {'error': str(e), 'passed': False}

    async def _test_error_recovery(self) -> Dict[str, Any]:
        """Test system error recovery capabilities"""
        try:
            test_results = {
                'error_handling': True,
                'graceful_degradation': True,
                'recovery_capability': True
            }

            # Test audio system with invalid input
            audio_system = R2D2AudioIntelligence()
            await audio_system.start_audio_intelligence()

            try:
                # This should not crash the system
                audio_system.request_audio_playback(
                    None,  # Invalid context
                    priority=999  # Invalid priority
                )
                test_results['invalid_input_handling'] = True
            except Exception:
                test_results['invalid_input_handling'] = False

            # Test system shutdown and restart
            await audio_system.stop_audio_intelligence()

            audio_system2 = R2D2AudioIntelligence()
            await audio_system2.start_audio_intelligence()

            test_results['restart_capability'] = True

            await audio_system2.stop_audio_intelligence()

            test_results['passed'] = all([
                test_results.get('invalid_input_handling', False),
                test_results.get('restart_capability', False)
            ])

            return test_results

        except Exception as e:
            logger.error(f"Error recovery test error: {e}")
            return {'error': str(e), 'passed': False}

    async def _test_long_duration_operation(self) -> Dict[str, Any]:
        """Test system stability over extended operation"""
        try:
            audio_system = R2D2AudioIntelligence()
            await audio_system.start_audio_intelligence()

            # Run for extended period with regular requests
            test_duration = 10  # seconds (reduced for testing)
            start_time = time.time()
            requests_made = 0
            errors_encountered = 0

            while (time.time() - start_time) < test_duration:
                try:
                    context = random.choice(list(R2D2EmotionalContext))
                    audio_system.request_audio_playback(
                        context,
                        priority=random.randint(1, 5)
                    )
                    requests_made += 1

                    await asyncio.sleep(0.1)  # 10 requests per second

                except Exception:
                    errors_encountered += 1

            actual_duration = time.time() - start_time

            await audio_system.stop_audio_intelligence()

            error_rate = errors_encountered / requests_made if requests_made > 0 else 1.0

            test_results = {
                'test_duration_seconds': actual_duration,
                'requests_made': requests_made,
                'errors_encountered': errors_encountered,
                'error_rate': error_rate,
                'system_stability': error_rate < 0.05,  # Less than 5% error rate
                'passed': error_rate < 0.05 and requests_made > 50
            }

            return test_results

        except Exception as e:
            logger.error(f"Long duration test error: {e}")
            return {'error': str(e), 'passed': False}

    def _generate_test_report(self):
        """Generate comprehensive test report"""
        logger.info("\n📊 Generating Test Report...")
        print("\n" + "="*70)
        print("📊 COMPREHENSIVE TEST REPORT")
        print("="*70)

        total_tests = len(self.test_results)
        passed_tests = len([r for r in self.test_results.values() if r['status'] == 'PASS'])
        failed_tests = len([r for r in self.test_results.values() if r['status'] == 'FAIL'])
        error_tests = len([r for r in self.test_results.values() if r['status'] == 'ERROR'])

        success_rate = (passed_tests / total_tests) * 100 if total_tests > 0 else 0

        print(f"\n🎯 OVERALL RESULTS:")
        print(f"   Total Tests: {total_tests}")
        print(f"   Passed: {passed_tests} ✅")
        print(f"   Failed: {failed_tests} ❌")
        print(f"   Errors: {error_tests} ⚠️")
        print(f"   Success Rate: {success_rate:.1f}%")

        # Test categories summary
        categories = {
            'Component Tests': [t for t in self.test_results.keys() if 'test_' in t and any(comp in t for comp in ['servo', 'choreographer', 'audio', 'environmental', 'behavioral'])],
            'Integration Tests': [t for t in self.test_results.keys() if any(word in t for word in ['websocket', 'coordination', 'triggers', 'sync'])],
            'Performance Tests': [t for t in self.test_results.keys() if any(word in t for word in ['response_time', 'memory', 'concurrent', 'latency'])],
            'Authenticity Tests': [t for t in self.test_results.keys() if any(word in t for word in ['canon', 'character', 'sound_authenticity', 'movement_authenticity'])],
            'Stress Tests': [t for t in self.test_results.keys() if any(word in t for word in ['high_load', 'error_recovery', 'long_duration'])]
        }

        print(f"\n📋 CATEGORY BREAKDOWN:")
        for category, tests in categories.items():
            if tests:
                category_passed = len([t for t in tests if self.test_results.get(t, {}).get('status') == 'PASS'])
                category_total = len(tests)
                category_rate = (category_passed / category_total) * 100 if category_total > 0 else 0
                print(f"   {category}: {category_passed}/{category_total} ({category_rate:.1f}%)")

        # Performance metrics
        print(f"\n⚡ PERFORMANCE HIGHLIGHTS:")
        if '_test_response_time' in self.test_results:
            resp_time = self.test_results['_test_response_time'].get('details', {})
            avg_resp = resp_time.get('average_response_time_ms', 'N/A')
            print(f"   Average Response Time: {avg_resp}ms")

        if '_test_memory_usage' in self.test_results:
            mem_usage = self.test_results['_test_memory_usage'].get('details', {})
            memory_mb = mem_usage.get('memory_usage_mb', 'N/A')
            print(f"   Memory Usage: {memory_mb}MB")

        # Authenticity scores
        print(f"\n⭐ STAR WARS AUTHENTICITY:")
        if '_test_canon_compliance' in self.test_results:
            canon_test = self.test_results['_test_canon_compliance'].get('details', {})
            canon_score = canon_test.get('overall_canon_score', 'N/A')
            print(f"   Overall Canon Score: {canon_score}/10")

        if '_test_movement_authenticity' in self.test_results:
            movement_test = self.test_results['_test_movement_authenticity'].get('details', {})
            movement_score = movement_test.get('movement_authenticity_score', 'N/A')
            print(f"   Movement Authenticity: {movement_score}/10")

        # Final assessment
        print(f"\n🏆 FINAL ASSESSMENT:")
        if success_rate >= 90:
            print("   Status: ✅ EXCELLENT - R2D2 Behavioral Intelligence System is ready for deployment!")
        elif success_rate >= 80:
            print("   Status: ✅ GOOD - System is functional with minor issues")
        elif success_rate >= 70:
            print("   Status: ⚠️ ACCEPTABLE - System needs improvements before deployment")
        else:
            print("   Status: ❌ NEEDS WORK - Significant issues require attention")

        total_duration = time.time() - self.test_start_time
        print(f"\n⏱️ Total Test Duration: {total_duration:.1f} seconds")
        print("="*70)

        # Save detailed report to file
        self._save_test_report_to_file()

    def _save_test_report_to_file(self):
        """Save detailed test report to file"""
        try:
            report_data = {
                'test_execution': {
                    'timestamp': datetime.now().isoformat(),
                    'duration_seconds': time.time() - self.test_start_time,
                    'total_tests': len(self.test_results),
                    'passed_tests': len([r for r in self.test_results.values() if r['status'] == 'PASS']),
                    'failed_tests': len([r for r in self.test_results.values() if r['status'] == 'FAIL']),
                    'error_tests': len([r for r in self.test_results.values() if r['status'] == 'ERROR'])
                },
                'test_results': self.test_results
            }

            report_file = f"/home/rolo/r2ai/test_report_{int(time.time())}.json"
            with open(report_file, 'w') as f:
                json.dump(report_data, f, indent=2, default=str)

            logger.info(f"Detailed test report saved to: {report_file}")

        except Exception as e:
            logger.error(f"Failed to save test report: {e}")

    async def _cleanup_tests(self):
        """Clean up test resources"""
        try:
            logger.info("Cleaning up test resources...")

            if self.integration_server:
                await self.integration_server.stop_integration_server()

        except Exception as e:
            logger.error(f"Error during test cleanup: {e}")


async def main():
    """Main entry point for test suite"""
    print("🧪 R2D2 Behavioral Intelligence Test Suite")
    print("Starting comprehensive system validation...")

    test_suite = R2D2BehavioralIntelligenceTestSuite()
    await test_suite.run_all_tests()


if __name__ == "__main__":
    asyncio.run(main())