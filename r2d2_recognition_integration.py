#!/usr/bin/env python3
"""
R2D2 Recognition Integration System
Connects person recognition with R2D2's reaction and behavior systems
Handles different reaction triggers based on familiarity and character recognition
"""

import json
import time
import logging
import threading
import asyncio
import websockets
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass
import queue
import numpy as np

from r2d2_person_recognition_system import R2D2PersonRecognitionSystem, PersonIdentity
from r2d2_memory_manager import R2D2MemoryManager

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class R2D2Response:
    """R2D2 behavioral response configuration"""
    response_id: str
    response_type: str
    audio_sequence: str
    movement_pattern: str
    light_pattern: str
    duration_seconds: float
    excitement_level: int  # 1-10 scale
    priority: int  # 1-10 scale (10 = highest)
    context: Dict[str, Any]

@dataclass
class InteractionEvent:
    """Interaction event for tracking and learning"""
    event_id: str
    timestamp: datetime
    person_identity: PersonIdentity
    r2d2_response: R2D2Response
    interaction_duration: float
    effectiveness_score: Optional[float] = None
    audience_reaction: Optional[str] = None
    environmental_context: Optional[Dict] = None

class R2D2BehaviorCoordinator:
    """Coordinates R2D2 behaviors based on person recognition"""

    def __init__(self, config: Dict = None):
        self.config = config or self._get_default_config()

        # Core systems
        self.recognition_system = R2D2PersonRecognitionSystem(config.get('recognition', {}))
        self.memory_manager = R2D2MemoryManager(config.get('memory', {}))

        # Behavior management
        self.active_response = None
        self.response_queue = queue.PriorityQueue()
        self.interaction_history = []

        # System state
        self.running = False
        self.behavior_thread = None
        self.processing_thread = None

        # Response definitions
        self.response_templates = self._load_response_templates()

        # Callback registration for external systems
        self.reaction_callbacks = {}

        # Performance tracking
        self.performance_stats = {
            'total_interactions': 0,
            'successful_recognitions': 0,
            'failed_recognitions': 0,
            'average_response_time': 0,
            'behavior_effectiveness': {}
        }

        logger.info("R2D2 Recognition Integration System initialized")

    def _get_default_config(self) -> Dict:
        """Get default configuration"""
        return {
            "recognition": {
                "person_detection": {
                    "confidence_threshold": 0.7,
                    "iou_threshold": 0.45
                },
                "face_recognition": {
                    "similarity_threshold": 0.6,
                    "face_quality_threshold": 0.4
                }
            },
            "memory": {
                "temp_retention_days": 7,
                "cleanup_interval_hours": 6
            },
            "behavior": {
                "response_timeout_seconds": 10,
                "max_concurrent_responses": 1,
                "interaction_cooldown_seconds": 3,
                "learning_enabled": True,
                "effectiveness_tracking": True
            },
            "integration": {
                "servo_control_enabled": True,
                "audio_system_enabled": True,
                "light_system_enabled": True,
                "websocket_broadcast": True
            }
        }

    def _load_response_templates(self) -> Dict[str, R2D2Response]:
        """Load R2D2 response templates for different scenarios"""
        templates = {
            # Stranger responses (familiarity level 1)
            "curious_cautious": R2D2Response(
                response_id="curious_cautious",
                response_type="stranger_greeting",
                audio_sequence="curious_beeps_short",
                movement_pattern="head_tilt_slow",
                light_pattern="blue_pulse_gentle",
                duration_seconds=3.0,
                excitement_level=3,
                priority=5,
                context={"familiarity_required": 1, "character_type": "any"}
            ),

            # Acquaintance responses (familiarity level 2)
            "friendly_recognition": R2D2Response(
                response_id="friendly_recognition",
                response_type="acquaintance_greeting",
                audio_sequence="recognition_beeps",
                movement_pattern="dome_turn_acknowledge",
                light_pattern="blue_pulse_bright",
                duration_seconds=4.0,
                excitement_level=5,
                priority=6,
                context={"familiarity_required": 2, "character_type": "any"}
            ),

            # Friend responses (familiarity level 3+)
            "warm_greeting": R2D2Response(
                response_id="warm_greeting",
                response_type="friend_greeting",
                audio_sequence="happy_whistles",
                movement_pattern="happy_wiggle",
                light_pattern="rainbow_pulse",
                duration_seconds=5.0,
                excitement_level=7,
                priority=7,
                context={"familiarity_required": 3, "character_type": "any"}
            ),

            # Close friend responses (familiarity level 4+)
            "enthusiastic_welcome": R2D2Response(
                response_id="enthusiastic_welcome",
                response_type="close_friend_greeting",
                audio_sequence="excited_celebration",
                movement_pattern="excited_dance",
                light_pattern="rainbow_celebration",
                duration_seconds=6.0,
                excitement_level=9,
                priority=8,
                context={"familiarity_required": 4, "character_type": "any"}
            ),

            # Star Wars character specific responses
            "jedi_respect": R2D2Response(
                response_id="jedi_respect",
                response_type="character_recognition",
                audio_sequence="respectful_acknowledgment",
                movement_pattern="formal_bow",
                light_pattern="blue_honor_pattern",
                duration_seconds=5.0,
                excitement_level=8,
                priority=9,
                context={"familiarity_required": 1, "character_type": "jedi"}
            ),

            "princess_respect": R2D2Response(
                response_id="princess_respect",
                response_type="character_recognition",
                audio_sequence="princess_acknowledgment",
                movement_pattern="royal_bow",
                light_pattern="white_royal_pattern",
                duration_seconds=6.0,
                excitement_level=10,
                priority=10,
                context={"familiarity_required": 1, "character_type": "princess_leia"}
            ),

            "sith_caution": R2D2Response(
                response_id="sith_caution",
                response_type="character_recognition",
                audio_sequence="cautious_warbles",
                movement_pattern="defensive_posture",
                light_pattern="red_warning_pattern",
                duration_seconds=4.0,
                excitement_level=6,
                priority=8,
                context={"familiarity_required": 1, "character_type": "sith"}
            ),

            "rebel_solidarity": R2D2Response(
                response_id="rebel_solidarity",
                response_type="character_recognition",
                audio_sequence="alliance_pride_sounds",
                movement_pattern="solidarity_stance",
                light_pattern="orange_rebellion_pattern",
                duration_seconds=5.0,
                excitement_level=9,
                priority=9,
                context={"familiarity_required": 1, "character_type": "rebel_pilot"}
            ),

            # Default fallback
            "default_friendly": R2D2Response(
                response_id="default_friendly",
                response_type="general_greeting",
                audio_sequence="friendly_beeps",
                movement_pattern="gentle_movement",
                light_pattern="gentle_blue",
                duration_seconds=3.0,
                excitement_level=4,
                priority=3,
                context={"familiarity_required": 0, "character_type": "any"}
            )
        }

        return templates

    def register_reaction_callback(self, system_name: str, callback: Callable):
        """Register callback function for external system integration"""
        self.reaction_callbacks[system_name] = callback
        logger.info(f"Registered reaction callback for {system_name}")

    def start_integration_system(self):
        """Start the recognition integration system"""
        try:
            self.running = True

            # Start memory manager
            self.memory_manager.start_memory_service()

            # Start behavior coordination thread
            self.behavior_thread = threading.Thread(target=self._behavior_coordination_loop, daemon=True)
            self.behavior_thread.start()

            # Start frame processing thread
            self.processing_thread = threading.Thread(target=self._frame_processing_loop, daemon=True)
            self.processing_thread.start()

            logger.info("R2D2 Recognition Integration System started")

        except Exception as e:
            logger.error(f"Error starting integration system: {e}")
            raise

    def stop_integration_system(self):
        """Stop the recognition integration system"""
        try:
            self.running = False

            # Stop memory manager
            self.memory_manager.stop_memory_service()

            # Wait for threads to complete
            if self.behavior_thread and self.behavior_thread.is_alive():
                self.behavior_thread.join(timeout=5)

            if self.processing_thread and self.processing_thread.is_alive():
                self.processing_thread.join(timeout=5)

            logger.info("R2D2 Recognition Integration System stopped")

        except Exception as e:
            logger.error(f"Error stopping integration system: {e}")

    def process_frame_for_recognition(self, frame, context: Dict = None):
        """Process frame for person recognition and trigger appropriate responses"""
        try:
            start_time = time.time()

            # Process frame through recognition system
            recognition_result = self.recognition_system.process_frame(frame)

            if "results" in recognition_result and recognition_result["results"]:
                for result in recognition_result["results"]:
                    person_identity = self._dict_to_person_identity(result["person_identity"])
                    character_detected = result.get("character_detected")

                    # Generate and queue appropriate response
                    response = self._select_appropriate_response(person_identity, character_detected, context)

                    if response:
                        # Create interaction event
                        interaction_event = InteractionEvent(
                            event_id=f"interaction_{int(time.time())}_{np.random.randint(1000, 9999)}",
                            timestamp=datetime.now(),
                            person_identity=person_identity,
                            r2d2_response=response,
                            interaction_duration=0.0,  # Will be updated when complete
                            environmental_context=context
                        )

                        # Queue response with priority
                        self.response_queue.put((10 - response.priority, time.time(), interaction_event))

                        # Update performance stats
                        self.performance_stats['successful_recognitions'] += 1

            # Update processing time
            processing_time = time.time() - start_time
            self.performance_stats['average_response_time'] = (
                (self.performance_stats['average_response_time'] * self.performance_stats['total_interactions'] + processing_time) /
                (self.performance_stats['total_interactions'] + 1)
            )
            self.performance_stats['total_interactions'] += 1

        except Exception as e:
            logger.error(f"Error processing frame for recognition: {e}")
            self.performance_stats['failed_recognitions'] += 1

    def _dict_to_person_identity(self, identity_dict: Dict) -> PersonIdentity:
        """Convert dictionary to PersonIdentity object"""
        return PersonIdentity(
            person_id=identity_dict['person_id'],
            identity_type=identity_dict['identity_type'],
            first_seen=datetime.fromisoformat(identity_dict['first_seen']),
            last_seen=datetime.fromisoformat(identity_dict['last_seen']),
            visit_count=identity_dict['visit_count'],
            costume_type=identity_dict.get('costume_type'),
            character_name=identity_dict.get('character_name'),
            familiarity_level=identity_dict['familiarity_level'],
            recognition_confidence=identity_dict['recognition_confidence']
        )

    def _select_appropriate_response(self, person_identity: PersonIdentity, character_detected: str, context: Dict = None) -> Optional[R2D2Response]:
        """Select the most appropriate R2D2 response for the person"""
        try:
            familiarity = person_identity.familiarity_level
            character = character_detected or person_identity.character_name

            # Check for character-specific responses first
            if character:
                character_response = self._get_character_specific_response(character, familiarity)
                if character_response:
                    return character_response

            # Fall back to familiarity-based responses
            familiarity_response = self._get_familiarity_based_response(familiarity)
            if familiarity_response:
                return familiarity_response

            # Default response
            return self.response_templates["default_friendly"]

        except Exception as e:
            logger.error(f"Error selecting appropriate response: {e}")
            return self.response_templates["default_friendly"]

    def _get_character_specific_response(self, character: str, familiarity: int) -> Optional[R2D2Response]:
        """Get character-specific response"""
        character_map = {
            "jedi": "jedi_respect",
            "princess_leia": "princess_respect",
            "sith": "sith_caution",
            "rebel_pilot": "rebel_solidarity"
        }

        response_id = character_map.get(character)
        if response_id and response_id in self.response_templates:
            response = self.response_templates[response_id]
            # Enhance response based on familiarity
            if familiarity >= 3:
                response.excitement_level = min(10, response.excitement_level + 1)
                response.duration_seconds += 1.0
            return response

        return None

    def _get_familiarity_based_response(self, familiarity: int) -> Optional[R2D2Response]:
        """Get response based on familiarity level"""
        familiarity_map = {
            1: "curious_cautious",
            2: "friendly_recognition",
            3: "warm_greeting",
            4: "enthusiastic_welcome",
            5: "enthusiastic_welcome"
        }

        response_id = familiarity_map.get(familiarity, "curious_cautious")
        return self.response_templates.get(response_id)

    def _behavior_coordination_loop(self):
        """Main behavior coordination loop"""
        logger.info("Behavior coordination loop started")

        while self.running:
            try:
                # Get next response from queue (with timeout)
                try:
                    priority, timestamp, interaction_event = self.response_queue.get(timeout=1.0)
                except queue.Empty:
                    continue

                # Check if response is still relevant (not too old)
                response_age = time.time() - timestamp
                if response_age > self.config['behavior']['response_timeout_seconds']:
                    logger.warning(f"Skipping stale response (age: {response_age:.1f}s)")
                    continue

                # Execute response
                self._execute_r2d2_response(interaction_event)

                # Apply cooldown
                time.sleep(self.config['behavior']['interaction_cooldown_seconds'])

            except Exception as e:
                logger.error(f"Error in behavior coordination loop: {e}")
                time.sleep(1)

    def _execute_r2d2_response(self, interaction_event: InteractionEvent):
        """Execute R2D2 response through registered callbacks"""
        try:
            response = interaction_event.r2d2_response
            start_time = time.time()

            logger.info(f"Executing R2D2 response: {response.response_type} (excitement: {response.excitement_level})")

            # Execute through registered callbacks
            execution_results = {}

            # Audio system
            if "audio_system" in self.reaction_callbacks:
                try:
                    result = self.reaction_callbacks["audio_system"](response.audio_sequence, response.duration_seconds)
                    execution_results["audio"] = result
                except Exception as e:
                    logger.error(f"Audio system callback error: {e}")

            # Movement/servo system
            if "servo_system" in self.reaction_callbacks:
                try:
                    result = self.reaction_callbacks["servo_system"](response.movement_pattern, response.duration_seconds)
                    execution_results["movement"] = result
                except Exception as e:
                    logger.error(f"Servo system callback error: {e}")

            # Light system
            if "light_system" in self.reaction_callbacks:
                try:
                    result = self.reaction_callbacks["light_system"](response.light_pattern, response.duration_seconds)
                    execution_results["lights"] = result
                except Exception as e:
                    logger.error(f"Light system callback error: {e}")

            # WebSocket broadcast
            if "websocket_system" in self.reaction_callbacks:
                try:
                    broadcast_data = {
                        "type": "r2d2_response",
                        "response": {
                            "response_id": response.response_id,
                            "response_type": response.response_type,
                            "excitement_level": response.excitement_level,
                            "duration": response.duration_seconds
                        },
                        "person_info": {
                            "familiarity_level": interaction_event.person_identity.familiarity_level,
                            "visit_count": interaction_event.person_identity.visit_count,
                            "character": interaction_event.person_identity.character_name
                        },
                        "timestamp": interaction_event.timestamp.isoformat()
                    }
                    self.reaction_callbacks["websocket_system"](broadcast_data)
                    execution_results["websocket"] = True
                except Exception as e:
                    logger.error(f"WebSocket system callback error: {e}")

            # Update interaction event
            execution_time = time.time() - start_time
            interaction_event.interaction_duration = execution_time

            # Store interaction for learning
            self.interaction_history.append(interaction_event)

            # Update behavior effectiveness tracking
            if response.response_type not in self.performance_stats['behavior_effectiveness']:
                self.performance_stats['behavior_effectiveness'][response.response_type] = {
                    'count': 0,
                    'average_execution_time': 0
                }

            behavior_stats = self.performance_stats['behavior_effectiveness'][response.response_type]
            behavior_stats['count'] += 1
            behavior_stats['average_execution_time'] = (
                (behavior_stats['average_execution_time'] * (behavior_stats['count'] - 1) + execution_time) /
                behavior_stats['count']
            )

            logger.info(f"R2D2 response executed successfully in {execution_time:.2f}s")

        except Exception as e:
            logger.error(f"Error executing R2D2 response: {e}")

    def _frame_processing_loop(self):
        """Placeholder for continuous frame processing"""
        # This would be implemented to work with camera feed
        logger.info("Frame processing loop started (placeholder)")

        while self.running:
            try:
                # In a real implementation, this would:
                # 1. Capture frames from camera
                # 2. Process through recognition system
                # 3. Trigger appropriate responses
                time.sleep(1)

            except Exception as e:
                logger.error(f"Error in frame processing loop: {e}")
                time.sleep(5)

    def get_integration_status(self) -> Dict[str, Any]:
        """Get current integration system status"""
        try:
            recognition_status = self.recognition_system.get_system_status()
            memory_status = self.memory_manager.get_memory_status()

            status = {
                "integration_system": {
                    "running": self.running,
                    "active_response": self.active_response.response_id if self.active_response else None,
                    "queued_responses": self.response_queue.qsize(),
                    "registered_callbacks": list(self.reaction_callbacks.keys())
                },
                "recognition_system": recognition_status,
                "memory_system": memory_status,
                "performance_stats": self.performance_stats,
                "recent_interactions": [
                    {
                        "timestamp": event.timestamp.isoformat(),
                        "response_type": event.r2d2_response.response_type,
                        "person_familiarity": event.person_identity.familiarity_level,
                        "character": event.person_identity.character_name,
                        "duration": event.interaction_duration
                    }
                    for event in self.interaction_history[-10:]  # Last 10 interactions
                ],
                "system_health": {
                    "recognition_success_rate": (
                        self.performance_stats['successful_recognitions'] /
                        max(1, self.performance_stats['total_interactions'])
                    ) * 100,
                    "average_response_time": self.performance_stats['average_response_time']
                }
            }

            return status

        except Exception as e:
            logger.error(f"Error getting integration status: {e}")
            return {"error": str(e)}

    def simulate_interaction(self, person_type: str = "stranger", character: str = None) -> Dict[str, Any]:
        """Simulate an interaction for testing purposes"""
        try:
            # Create simulated person identity
            if person_type == "stranger":
                familiarity = 1
                visit_count = 1
            elif person_type == "acquaintance":
                familiarity = 2
                visit_count = 3
            elif person_type == "friend":
                familiarity = 3
                visit_count = 7
            else:  # close_friend
                familiarity = 4
                visit_count = 15

            person_identity = PersonIdentity(
                person_id=f"sim_{int(time.time())}",
                identity_type="temporary",
                first_seen=datetime.now() - timedelta(days=visit_count),
                last_seen=datetime.now(),
                visit_count=visit_count,
                character_name=character,
                familiarity_level=familiarity,
                recognition_confidence=0.9
            )

            # Generate response
            response = self._select_appropriate_response(person_identity, character)

            # Create interaction event
            interaction_event = InteractionEvent(
                event_id=f"sim_interaction_{int(time.time())}",
                timestamp=datetime.now(),
                person_identity=person_identity,
                r2d2_response=response,
                interaction_duration=0.0
            )

            # Execute response
            self._execute_r2d2_response(interaction_event)

            return {
                "simulation_successful": True,
                "person_type": person_type,
                "character": character,
                "response_executed": response.response_type,
                "familiarity_level": familiarity,
                "visit_count": visit_count
            }

        except Exception as e:
            logger.error(f"Error in simulation: {e}")
            return {"simulation_successful": False, "error": str(e)}

def main():
    """Main function for testing the integration system"""
    print("R2D2 Recognition Integration System")
    print("=" * 50)

    # Initialize integration system
    integration_system = R2D2BehaviorCoordinator()

    # Register dummy callbacks for testing
    def dummy_audio_callback(sequence, duration):
        print(f"🎵 Audio: {sequence} for {duration}s")
        return {"executed": True, "sequence": sequence}

    def dummy_servo_callback(pattern, duration):
        print(f"🤖 Movement: {pattern} for {duration}s")
        return {"executed": True, "pattern": pattern}

    def dummy_light_callback(pattern, duration):
        print(f"💡 Lights: {pattern} for {duration}s")
        return {"executed": True, "pattern": pattern}

    def dummy_websocket_callback(data):
        print(f"📡 WebSocket: {json.dumps(data, indent=2)}")
        return {"broadcasted": True}

    # Register callbacks
    integration_system.register_reaction_callback("audio_system", dummy_audio_callback)
    integration_system.register_reaction_callback("servo_system", dummy_servo_callback)
    integration_system.register_reaction_callback("light_system", dummy_light_callback)
    integration_system.register_reaction_callback("websocket_system", dummy_websocket_callback)

    # Start system
    integration_system.start_integration_system()

    print("Integration system started. Testing interactions...")

    try:
        # Test different interaction scenarios
        test_scenarios = [
            ("stranger", None),
            ("acquaintance", None),
            ("friend", "jedi"),
            ("close_friend", "princess_leia"),
            ("stranger", "sith"),
            ("friend", "rebel_pilot")
        ]

        for person_type, character in test_scenarios:
            print(f"\n--- Testing {person_type}" + (f" ({character})" if character else "") + " ---")
            result = integration_system.simulate_interaction(person_type, character)
            print(f"Result: {json.dumps(result, indent=2)}")
            time.sleep(3)

        # Print final status
        print("\n--- System Status ---")
        status = integration_system.get_integration_status()
        print(json.dumps(status, indent=2, default=str))

    except KeyboardInterrupt:
        print("\nStopping integration system...")
    finally:
        integration_system.stop_integration_system()
        print("Integration system stopped")

if __name__ == "__main__":
    main()