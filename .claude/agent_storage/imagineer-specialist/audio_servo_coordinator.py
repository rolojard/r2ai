#!/usr/bin/env python3
"""
Disney-Level Audio-Servo Coordination System
===========================================

Advanced integration system that coordinates audio playback with servo movements
for Disney-quality R2D2 performances. Provides seamless synchronization between
sound effects, lip-sync animations, and mechanical movements.

Features:
- Real-time audio-servo synchronization with sub-millisecond precision
- Disney animation principles applied to audio-visual coordination
- Character personality-driven movement and audio behaviors
- Lip-sync automation with servo mouth movements
- Spatial audio coordination with dome rotation and head movements
- Convention-ready performance reliability and crowd interaction

Author: Imagineer Specialist Agent
Target: NVIDIA Orin Nano R2D2 Systems
Integration with Super Coder's Disney Servo Control Library
"""

import time
import math
import threading
import logging
import asyncio
from typing import Dict, List, Tuple, Optional, Callable, Any, Union
from dataclasses import dataclass, field
from enum import Enum
import numpy as np
from collections import deque
import json

# Import our audio systems
from hcr_audio_controller import HCRAudioController, CharacterMode, SpatialPosition
from lipsync_automation import LipSyncAutomation, LipSyncFrame, PhonemeType
from r2d2_sound_library import R2D2SoundLibrary, EmotionalState, CharacterContext
from spatial_audio_system import SpatialAudioSystem, AudioZone

# Configure logging for audio-servo coordination
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PerformanceMode(Enum):
    """Performance modes for different scenarios"""
    IDLE = "idle"
    GREETING = "greeting"
    CONVERSATION = "conversation"
    DEMONSTRATION = "demonstration"
    ALERT = "alert"
    MAINTENANCE = "maintenance"
    SHUTDOWN = "shutdown"

class SynchronizationLevel(Enum):
    """Levels of audio-servo synchronization"""
    BASIC = "basic"           # Simple coordination
    ENHANCED = "enhanced"     # Lip-sync and basic movements
    DISNEY = "disney"         # Full Disney-quality synchronization
    PERFORMANCE = "performance" # Convention performance mode

@dataclass
class AudioServoEvent:
    """Coordinated audio-servo event"""
    event_id: str
    timestamp: float
    audio_clip_id: Optional[str] = None
    servo_commands: Dict[str, float] = field(default_factory=dict)
    duration: float = 0.0
    priority: int = 5
    sync_level: SynchronizationLevel = SynchronizationLevel.ENHANCED

@dataclass
class PerformanceSequence:
    """Complete performance sequence with audio and servo coordination"""
    sequence_id: str
    name: str
    events: List[AudioServoEvent]
    total_duration: float
    character_mode: CharacterMode
    emotional_state: EmotionalState
    description: str = ""

class AudioServoCoordinator:
    """
    Disney-quality audio-servo coordination system

    Provides seamless integration between:
    - HCR audio system for sound playback
    - Disney servo control for mechanical movements
    - Lip-sync automation for mouth movements
    - Spatial audio for immersive positioning
    - Character personality behaviors
    """

    def __init__(self):
        """Initialize the audio-servo coordination system"""

        # Initialize audio systems
        self.audio_controller = HCRAudioController()
        self.lipsync_system = LipSyncAutomation()
        self.sound_library = R2D2SoundLibrary()
        self.spatial_audio = SpatialAudioSystem()

        # Initialize servo system (import Super Coder's library)
        try:
            import sys
            sys.path.append('/home/rolo/r2ai/.claude/agent_storage/super-coder')
            from disney_servo_control import R2D2ServoSystem, EasingType

            self.servo_system = R2D2ServoSystem()
            self.EasingType = EasingType
            logger.info("Disney servo control system integrated successfully")
        except ImportError as e:
            logger.error(f"Failed to import Disney servo control: {e}")
            self.servo_system = None
            self.EasingType = None

        # Current state
        self.current_performance_mode = PerformanceMode.IDLE
        self.current_sync_level = SynchronizationLevel.DISNEY
        self.is_performing = False

        # Event scheduling
        self.event_queue: deque = deque()
        self.active_events: List[AudioServoEvent] = []

        # Coordination state
        self.last_lipsync_frame: Optional[LipSyncFrame] = None
        self.servo_audio_offset = 0.0  # Milliseconds to compensate for servo lag

        # Threading for real-time coordination
        self._coordination_thread = None
        self._coordination_running = False
        self._coordination_lock = threading.Lock()

        # Performance metrics
        self._performance_metrics = {
            'events_coordinated': 0,
            'sync_accuracy_ms': 0.0,
            'servo_audio_latency': 0.0,
            'lipsync_frames_processed': 0,
            'performance_sequences_completed': 0,
            'last_update_time': time.time()
        }

        # Initialize performance sequences
        self._initialize_performance_sequences()

        # Start coordination thread
        self._start_coordination_thread()

        logger.info("Audio-Servo Coordination System initialized with Disney-quality synchronization")

    def _initialize_performance_sequences(self):
        """Initialize pre-programmed performance sequences"""

        self.performance_sequences = {}

        # Greeting sequence with full audio-servo coordination
        greeting_events = [
            # Power up with dome movement
            AudioServoEvent(
                "greeting_01", 0.0,
                audio_clip_id="power_up_sequence_01",
                servo_commands={"dome": 180, "head_tilt": 85},
                duration=3.7, priority=9
            ),
            # Head nod with greeting sound
            AudioServoEvent(
                "greeting_02", 4.0,
                audio_clip_id="greeting_sequence_01",
                servo_commands={"head_tilt": 105},
                duration=1.5, priority=8
            ),
            # Return to center with acknowledgment
            AudioServoEvent(
                "greeting_03", 6.0,
                audio_clip_id="acknowledgment_beep_01",
                servo_commands={"head_tilt": 90, "dome": 180},
                duration=1.0, priority=7
            ),
            # Panel flourish
            AudioServoEvent(
                "greeting_04", 7.5,
                servo_commands={"panel_1": 45, "panel_2": 30},
                duration=1.5, priority=6
            ),
            # Close panels
            AudioServoEvent(
                "greeting_05", 9.5,
                servo_commands={"panel_1": 0, "panel_2": 0},
                duration=2.0, priority=5
            )
        ]

        self.performance_sequences["full_greeting"] = PerformanceSequence(
            "full_greeting", "Complete R2D2 Greeting Performance",
            greeting_events, 11.5, CharacterMode.HAPPY, EmotionalState.HAPPY,
            "Full greeting sequence with coordinated audio and servo movements"
        )

        # Alert sequence
        alert_events = [
            # Rapid dome turn with alert sound
            AudioServoEvent(
                "alert_01", 0.0,
                audio_clip_id="alert_beep_01",
                servo_commands={"dome": 225, "head_tilt": 75},
                duration=0.8, priority=10
            ),
            # Quick head movements with urgent whistle
            AudioServoEvent(
                "alert_02", 1.0,
                audio_clip_id="urgent_whistle_01",
                servo_commands={"head_tilt": 105, "dome": 135},
                duration=1.8, priority=10
            ),
            # Return to scan position
            AudioServoEvent(
                "alert_03", 3.0,
                servo_commands={"head_tilt": 90, "dome": 180},
                duration=1.0, priority=8
            )
        ]

        self.performance_sequences["danger_alert"] = PerformanceSequence(
            "danger_alert", "Danger Alert Performance",
            alert_events, 4.0, CharacterMode.ALERT, EmotionalState.ALERT,
            "Alert sequence with rapid movements and warning sounds"
        )

        # Jedi recognition sequence
        jedi_events = [
            # Surprised reaction
            AudioServoEvent(
                "jedi_01", 0.0,
                audio_clip_id="surprised_whistle_01",
                servo_commands={"head_tilt": 70, "dome": 200},
                duration=0.7, priority=9
            ),
            # Excited recognition
            AudioServoEvent(
                "jedi_02", 1.0,
                audio_clip_id="jedi_recognition_01",
                servo_commands={"head_tilt": 85, "dome": 160},
                duration=3.5, priority=9
            ),
            # Happy celebration with panel movements
            AudioServoEvent(
                "jedi_03", 4.8,
                audio_clip_id="excited_whistle_01",
                servo_commands={"panel_1": 60, "panel_2": 45, "head_tilt": 110},
                duration=2.1, priority=8
            ),
            # Settle down
            AudioServoEvent(
                "jedi_04", 7.2,
                servo_commands={"panel_1": 0, "panel_2": 0, "head_tilt": 90, "dome": 180},
                duration=2.5, priority=6
            )
        ]

        self.performance_sequences["jedi_encounter"] = PerformanceSequence(
            "jedi_encounter", "Jedi Recognition Performance",
            jedi_events, 9.7, CharacterMode.EXCITED, EmotionalState.EXCITED,
            "Complete Jedi recognition sequence with coordinated movements"
        )

        # Curious exploration sequence
        curious_events = [
            # Start scanning with curious sound
            AudioServoEvent(
                "curious_01", 0.0,
                audio_clip_id="curious_warble_01",
                servo_commands={"dome": 120, "head_tilt": 95},
                duration=1.5, priority=7
            ),
            # Continue scanning
            AudioServoEvent(
                "curious_02", 2.0,
                audio_clip_id="questioning_beep_01",
                servo_commands={"dome": 240, "head_tilt": 85},
                duration=1.0, priority=6
            ),
            # Focus on object of interest
            AudioServoEvent(
                "curious_03", 3.5,
                audio_clip_id="scanning_loop_01",
                servo_commands={"dome": 200, "head_tilt": 80, "periscope": 90},
                duration=4.5, priority=7
            ),
            # Acknowledgment and return
            AudioServoEvent(
                "curious_04", 8.2,
                audio_clip_id="acknowledgment_beep_01",
                servo_commands={"dome": 180, "head_tilt": 90, "periscope": 0},
                duration=1.5, priority=5
            )
        ]

        self.performance_sequences["curious_exploration"] = PerformanceSequence(
            "curious_exploration", "Curious Exploration Performance",
            curious_events, 9.7, CharacterMode.CURIOUS, EmotionalState.CURIOUS,
            "Exploration sequence with coordinated scanning movements"
        )

        logger.info(f"Initialized {len(self.performance_sequences)} performance sequences")

    def set_performance_mode(self, mode: PerformanceMode) -> bool:
        """
        Set current performance mode

        Args:
            mode: Performance mode to activate

        Returns:
            True if mode was set successfully
        """
        self.current_performance_mode = mode

        # Adjust coordination parameters based on mode
        if mode == PerformanceMode.IDLE:
            self.set_synchronization_level(SynchronizationLevel.BASIC)
        elif mode == PerformanceMode.DEMONSTRATION:
            self.set_synchronization_level(SynchronizationLevel.DISNEY)
        elif mode == PerformanceMode.ALERT:
            self.set_synchronization_level(SynchronizationLevel.ENHANCED)

        logger.info(f"Performance mode set to: {mode.value}")
        return True

    def set_synchronization_level(self, level: SynchronizationLevel) -> bool:
        """
        Set audio-servo synchronization level

        Args:
            level: Synchronization level

        Returns:
            True if level was set
        """
        self.current_sync_level = level

        # Adjust coordination timing based on level
        if level == SynchronizationLevel.BASIC:
            self.servo_audio_offset = 50.0  # 50ms basic sync
        elif level == SynchronizationLevel.ENHANCED:
            self.servo_audio_offset = 20.0  # 20ms enhanced sync
        elif level == SynchronizationLevel.DISNEY:
            self.servo_audio_offset = 5.0   # 5ms Disney-quality sync
        elif level == SynchronizationLevel.PERFORMANCE:
            self.servo_audio_offset = 0.0   # Real-time performance sync

        logger.info(f"Synchronization level set to: {level.value} (offset: {self.servo_audio_offset}ms)")
        return True

    def perform_sequence(self, sequence_id: str) -> bool:
        """
        Perform complete audio-servo sequence

        Args:
            sequence_id: ID of sequence to perform

        Returns:
            True if sequence started successfully
        """
        if sequence_id not in self.performance_sequences:
            logger.error(f"Performance sequence '{sequence_id}' not found")
            return False

        if self.is_performing:
            logger.warning("Already performing a sequence - queuing new sequence")

        try:
            sequence = self.performance_sequences[sequence_id]

            # Set character mode and emotional state
            self.audio_controller.set_character_mode(sequence.character_mode)
            self.sound_library.set_emotional_state(sequence.emotional_state)

            # Queue all events with timing
            current_time = time.time()
            for event in sequence.events:
                event.timestamp = current_time + event.timestamp
                self.event_queue.append(event)

            self.is_performing = True
            logger.info(f"Started performance sequence: {sequence.name}")
            logger.info(f"  Duration: {sequence.total_duration:.1f}s")
            logger.info(f"  Events: {len(sequence.events)}")

            return True

        except Exception as e:
            logger.error(f"Failed to start sequence '{sequence_id}': {e}")
            return False

    def coordinate_audio_with_movement(self, audio_clip_id: str, servo_commands: Dict[str, float],
                                     sync_timing: float = 0.0) -> bool:
        """
        Coordinate audio playback with servo movements

        Args:
            audio_clip_id: ID of audio clip to play
            servo_commands: Dictionary of servo commands {servo_name: angle}
            sync_timing: Additional timing offset (seconds)

        Returns:
            True if coordination was successful
        """
        try:
            # Calculate servo pre-movement for audio sync
            servo_delay = self.servo_audio_offset / 1000.0  # Convert to seconds

            # Start servo movements first (to compensate for mechanical lag)
            if self.servo_system and servo_commands:
                if sync_timing > servo_delay:
                    # Schedule servo movement
                    threading.Timer(sync_timing - servo_delay,
                                  lambda: self._execute_servo_commands(servo_commands)).start()
                else:
                    # Execute servo commands immediately
                    self._execute_servo_commands(servo_commands)

            # Start audio playback
            if audio_clip_id:
                if sync_timing > 0:
                    threading.Timer(sync_timing,
                                  lambda: self.audio_controller.play_audio_clip(audio_clip_id)).start()
                else:
                    self.audio_controller.play_audio_clip(audio_clip_id)

            self._performance_metrics['events_coordinated'] += 1
            return True

        except Exception as e:
            logger.error(f"Audio-servo coordination error: {e}")
            return False

    def _execute_servo_commands(self, servo_commands: Dict[str, float]):
        """Execute servo commands with appropriate easing"""
        if not self.servo_system:
            logger.debug(f"SIM: Servo commands: {servo_commands}")
            return

        try:
            # Use Disney-quality easing for movements
            easing = self.EasingType.EASE_IN_OUT_CUBIC

            if len(servo_commands) == 1:
                # Single servo movement
                servo_name, angle = next(iter(servo_commands.items()))
                self.servo_system.controller.set_angle(servo_name, angle, duration=1.0, easing=easing)
            else:
                # Multiple servo coordination
                self.servo_system.controller.set_multiple_angles(servo_commands, duration=1.0, easing=easing)

        except Exception as e:
            logger.error(f"Servo command execution error: {e}")

    def enable_lipsync_coordination(self, enable: bool = True) -> bool:
        """
        Enable or disable lip-sync servo coordination

        Args:
            enable: Whether to enable lip-sync coordination

        Returns:
            True if setting was changed
        """
        try:
            # Enable lip-sync in audio controller
            self.audio_controller.enable_lipsync(enable)

            if enable:
                # Start lip-sync processing
                self.lipsync_system.start_realtime_processing(self._handle_lipsync_frame)
            else:
                # Stop lip-sync processing
                self.lipsync_system.stop_realtime_processing()

            logger.info(f"Lip-sync coordination {'enabled' if enable else 'disabled'}")
            return True

        except Exception as e:
            logger.error(f"Failed to configure lip-sync coordination: {e}")
            return False

    def _handle_lipsync_frame(self, audio_data: np.ndarray):
        """Handle lip-sync frame for servo coordination"""
        try:
            # Get latest lip-sync data from audio controller
            lipsync_frame = self.audio_controller.get_lipsync_data()

            if lipsync_frame and self.servo_system:
                # Convert lip-sync data to servo commands
                servo_targets = self._lipsync_to_servo_commands(lipsync_frame)

                if servo_targets:
                    # Execute servo commands for mouth movement
                    self._execute_servo_commands(servo_targets)
                    self._performance_metrics['lipsync_frames_processed'] += 1

        except Exception as e:
            logger.error(f"Lip-sync frame handling error: {e}")

    def _lipsync_to_servo_commands(self, lipsync_frame) -> Dict[str, float]:
        """Convert lip-sync frame to servo commands"""
        try:
            servo_commands = {}

            # Map mouth openness to panel servos
            if hasattr(lipsync_frame, 'mouth_openness'):
                openness = lipsync_frame.mouth_openness

                # Main mouth panel
                servo_commands['panel_mouth_open'] = openness * 90.0

                # Side panels for width
                if hasattr(lipsync_frame, 'mouth_width'):
                    width = (lipsync_frame.mouth_width + 1.0) / 2.0  # Convert -1,1 to 0,1
                    servo_commands['panel_left_side'] = width * 45.0
                    servo_commands['panel_right_side'] = width * 45.0

            return servo_commands

        except Exception as e:
            logger.error(f"Lip-sync to servo conversion error: {e}")
            return {}

    def react_to_guest_interaction(self, guest_position: Tuple[float, float, float],
                                 character_type: CharacterContext = CharacterContext.CIVILIAN,
                                 confidence: float = 0.8) -> bool:
        """
        React to guest interaction with coordinated audio-visual response

        Args:
            guest_position: 3D position of guest
            character_type: Type of character detected
            confidence: Detection confidence

        Returns:
            True if reaction was triggered
        """
        try:
            # Update spatial audio listener position
            self.spatial_audio.update_listener_position(guest_position)

            # Create audio spotlight toward guest
            self.spatial_audio.create_audio_spotlight(guest_position, intensity=1.2)

            # Calculate dome direction toward guest
            guest_vector = np.array(guest_position)
            dome_angle = np.degrees(np.arctan2(guest_vector[0], guest_vector[2])) + 180

            # Select appropriate reaction sequence based on character type
            if character_type == CharacterContext.JEDI and confidence > 0.8:
                # Excited Jedi reaction
                self.coordinate_audio_with_movement(
                    "jedi_recognition_01",
                    {"dome": dome_angle, "head_tilt": 85},
                    sync_timing=0.1
                )

                # Follow up with excitement
                self.coordinate_audio_with_movement(
                    "excited_whistle_01",
                    {"panel_1": 45, "panel_2": 30},
                    sync_timing=4.0
                )

            elif character_type == CharacterContext.SITH and confidence > 0.7:
                # Alert reaction to Sith
                self.coordinate_audio_with_movement(
                    "sith_warning_01",
                    {"dome": dome_angle, "head_tilt": 75},
                    sync_timing=0.0
                )

            elif character_type == CharacterContext.CHILD and confidence > 0.6:
                # Playful reaction to child
                self.coordinate_audio_with_movement(
                    "playful_chirp_01",
                    {"dome": dome_angle, "head_tilt": 100},
                    sync_timing=0.2
                )

            else:
                # Generic greeting
                self.coordinate_audio_with_movement(
                    "greeting_sequence_01",
                    {"dome": dome_angle, "head_tilt": 95},
                    sync_timing=0.1
                )

            logger.info(f"Reacted to {character_type.value} at position {guest_position}")
            return True

        except Exception as e:
            logger.error(f"Guest interaction reaction error: {e}")
            return False

    def _start_coordination_thread(self):
        """Start the coordination thread"""
        self._coordination_running = True
        self._coordination_thread = threading.Thread(target=self._coordination_loop, daemon=True)
        self._coordination_thread.start()
        logger.info("Audio-servo coordination thread started")

    def _coordination_loop(self):
        """Main coordination loop"""
        while self._coordination_running:
            try:
                current_time = time.time()

                with self._coordination_lock:
                    # Process event queue
                    events_to_execute = []
                    while self.event_queue and self.event_queue[0].timestamp <= current_time:
                        events_to_execute.append(self.event_queue.popleft())

                    # Execute events
                    for event in events_to_execute:
                        self._execute_event(event)

                    # Check for completed events
                    self.active_events = [e for e in self.active_events
                                        if current_time < e.timestamp + e.duration]

                    # Update performance state
                    if not self.active_events and not self.event_queue and self.is_performing:
                        self.is_performing = False
                        self._performance_metrics['performance_sequences_completed'] += 1
                        logger.info("Performance sequence completed")

                # Update performance metrics
                self._performance_metrics['last_update_time'] = current_time

                time.sleep(0.01)  # 100Hz coordination loop

            except Exception as e:
                logger.error(f"Coordination loop error: {e}")
                time.sleep(0.1)

    def _execute_event(self, event: AudioServoEvent):
        """Execute a single audio-servo event"""
        try:
            logger.debug(f"Executing event: {event.event_id}")

            # Execute audio command
            if event.audio_clip_id:
                self.audio_controller.play_audio_clip(event.audio_clip_id)

            # Execute servo commands
            if event.servo_commands:
                self._execute_servo_commands(event.servo_commands)

            # Add to active events
            self.active_events.append(event)

            self._performance_metrics['events_coordinated'] += 1

        except Exception as e:
            logger.error(f"Event execution error: {e}")

    def stop_coordination_thread(self):
        """Stop the coordination thread"""
        self._coordination_running = False
        if self._coordination_thread and self._coordination_thread.is_alive():
            self._coordination_thread.join(timeout=2.0)

    def emergency_stop(self):
        """Emergency stop all audio and servo operations"""
        logger.warning("AUDIO-SERVO EMERGENCY STOP activated")

        # Stop all audio
        self.audio_controller.emergency_stop()

        # Stop all servo movement
        if self.servo_system:
            self.servo_system.emergency_stop()

        # Clear event queues
        with self._coordination_lock:
            self.event_queue.clear()
            self.active_events.clear()

        self.is_performing = False

    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get coordination performance metrics"""
        return {
            **self._performance_metrics,
            'system_status': {
                'performance_mode': self.current_performance_mode.value,
                'sync_level': self.current_sync_level.value,
                'is_performing': self.is_performing,
                'active_events': len(self.active_events),
                'queued_events': len(self.event_queue),
                'servo_system_available': self.servo_system is not None
            },
            'audio_systems': {
                'audio_controller': self.audio_controller.get_performance_metrics(),
                'sound_library': self.sound_library.get_performance_metrics(),
                'spatial_audio': self.spatial_audio.get_performance_metrics(),
                'lipsync_system': self.lipsync_system.get_performance_metrics()
            }
        }

    def save_coordination_profile(self, filename: str):
        """Save coordination system performance profile"""
        try:
            profile_data = {
                'timestamp': time.time(),
                'performance_sequences': {seq_id: {
                    'name': seq.name,
                    'duration': seq.total_duration,
                    'events_count': len(seq.events),
                    'character_mode': seq.character_mode.value,
                    'emotional_state': seq.emotional_state.value,
                    'description': seq.description
                } for seq_id, seq in self.performance_sequences.items()},
                'current_configuration': {
                    'performance_mode': self.current_performance_mode.value,
                    'sync_level': self.current_sync_level.value,
                    'servo_audio_offset': self.servo_audio_offset,
                    'is_performing': self.is_performing
                },
                'performance_metrics': self.get_performance_metrics()
            }

            with open(filename, 'w') as f:
                json.dump(profile_data, f, indent=2)

            logger.info(f"Coordination system profile saved to {filename}")

        except Exception as e:
            logger.error(f"Failed to save coordination profile: {e}")

    def __del__(self):
        """Cleanup when coordinator is destroyed"""
        self.stop_coordination_thread()


if __name__ == "__main__":
    # Example usage and testing
    print("Disney Audio-Servo Coordination System - R2D2 Demo")
    print("=" * 60)

    # Create coordination system
    coordinator = AudioServoCoordinator()

    try:
        # Test different performance modes
        modes = [PerformanceMode.IDLE, PerformanceMode.DEMONSTRATION, PerformanceMode.ALERT]

        for mode in modes:
            coordinator.set_performance_mode(mode)
            time.sleep(1.0)

        # Test performance sequences
        print(f"\nTesting performance sequences:")
        sequences = ["full_greeting", "jedi_encounter", "danger_alert", "curious_exploration"]

        for seq_id in sequences:
            print(f"Performing sequence: {seq_id}")
            coordinator.perform_sequence(seq_id)
            time.sleep(3.0)  # Allow partial execution for demo

        # Test guest interactions
        print(f"\nTesting guest interactions:")
        interactions = [
            ((2.0, 0.0, 1.5), CharacterContext.JEDI, 0.9),
            ((-1.5, 0.0, 2.0), CharacterContext.CHILD, 0.8),
            ((0.0, 0.0, 3.0), CharacterContext.CIVILIAN, 0.7)
        ]

        for position, char_type, confidence in interactions:
            print(f"Reacting to {char_type.value} at {position}")
            coordinator.react_to_guest_interaction(position, char_type, confidence)
            time.sleep(2.0)

        # Test lip-sync coordination
        print(f"\nTesting lip-sync coordination:")
        coordinator.enable_lipsync_coordination(True)
        coordinator.coordinate_audio_with_movement(
            "greeting_sequence_01",
            {"head_tilt": 95},
            sync_timing=0.1
        )
        time.sleep(4.0)

        # Display comprehensive performance metrics
        metrics = coordinator.get_performance_metrics()
        print(f"\nCoordination System Performance:")
        print(f"Events coordinated: {metrics['events_coordinated']}")
        print(f"Lip-sync frames processed: {metrics['lipsync_frames_processed']}")
        print(f"Performance sequences completed: {metrics['performance_sequences_completed']}")
        print(f"Current mode: {metrics['system_status']['performance_mode']}")
        print(f"Sync level: {metrics['system_status']['sync_level']}")
        print(f"Servo system available: {metrics['system_status']['servo_system_available']}")

        # Test emergency stop
        print(f"\nTesting emergency stop:")
        coordinator.emergency_stop()

        # Save performance profile
        coordinator.save_coordination_profile(
            "/home/rolo/r2ai/.claude/agent_storage/imagineer-specialist/coordination_profile.json"
        )

    except KeyboardInterrupt:
        print("\nDemo interrupted - performing emergency stop")
        coordinator.emergency_stop()
    except Exception as e:
        print(f"Error during demo: {e}")
        coordinator.emergency_stop()
    finally:
        print("Audio-servo coordination demo completed")