#!/usr/bin/env python3
"""
R2D2 Audio Intelligence System
==============================

Advanced audio intelligence layer that integrates with the canonical sound enhancer
to provide context-aware, emotionally-driven R2D2 sound selection and playback.

This system provides:
- Behavioral state → audio context mapping
- Real-time audio selection based on environmental conditions
- Synchronized audio-visual behavior coordination
- Multi-layered audio personality expression
- Performance-optimized audio playback with minimal latency

Key Features:
- Context-aware sound selection using canonical R2D2 sounds
- Emotional state-driven audio responses
- Environmental context audio adaptation
- Audio-servo synchronization for authentic character expression
- Queue management for complex audio sequences
- Real-time audio feedback integration

Author: Expert Python Coder
Target: NVIDIA Orin Nano R2D2 Systems
Integration: Canonical Sound Enhancer + Behavioral Intelligence + Environmental Awareness
"""

import asyncio
import time
import json
import logging
import threading
import queue
import random
import os
import sys
from typing import Dict, List, Optional, Any, Tuple, Callable
from dataclasses import dataclass, field
from enum import Enum
import subprocess
import pygame
from pathlib import Path

# Import system components
sys.path.append('/home/rolo/r2ai')
from r2d2_canonical_sound_enhancer import R2D2CanonicalSoundEnhancer, R2D2EmotionalContext, R2D2MemorySystem

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class AudioPlaybackState(Enum):
    """Current state of audio playback system"""
    IDLE = "idle"
    PLAYING = "playing"
    PAUSED = "paused"
    QUEUED = "queued"
    FAILED = "failed"

class AudioSyncMode(Enum):
    """Synchronization modes for audio-visual coordination"""
    IMMEDIATE = "immediate"       # Play immediately
    SERVO_SYNC = "servo_sync"     # Sync with servo movement
    DELAYED = "delayed"           # Play with specific delay
    SEQUENCE_SYNC = "sequence_sync"  # Part of choreographed sequence

class R2D2PersonalityAudioMode(Enum):
    """Audio personality modes for different behavioral contexts"""
    STANDARD = "standard"         # Normal R2D2 personality
    CURIOUS = "curious"          # Enhanced curiosity sounds
    PLAYFUL = "playful"          # More playful and energetic
    STUBBORN = "stubborn"        # Increased stubbornness
    EXCITED = "excited"          # High energy responses
    CALM = "calm"                # Gentle, measured responses
    ALERT = "alert"              # Heightened awareness sounds
    SOCIAL = "social"            # Enhanced social interaction

@dataclass
class AudioRequest:
    """Request for audio playback with context and parameters"""
    request_id: str
    audio_context: R2D2EmotionalContext
    priority: int = 1  # 1-10, higher = more urgent

    # Behavioral context
    behavioral_state: Optional[str] = None
    environmental_context: Optional[Dict[str, Any]] = None
    social_context: Optional[str] = None

    # Playback parameters
    sync_mode: AudioSyncMode = AudioSyncMode.IMMEDIATE
    delay_seconds: float = 0.0
    volume: float = 1.0  # 0.0-1.0

    # Personality modifiers
    personality_mode: R2D2PersonalityAudioMode = R2D2PersonalityAudioMode.STANDARD
    allow_stubborn: bool = True
    allow_sarcastic: bool = True
    force_specific_sound: Optional[str] = None

    # Timing and coordination
    max_duration_seconds: Optional[float] = None
    fade_in_seconds: float = 0.0
    fade_out_seconds: float = 0.0

    # Callback for completion
    completion_callback: Optional[Callable] = None

    # Request timing
    created_time: float = field(default_factory=time.time)
    expiry_time: Optional[float] = None

@dataclass
class AudioPlaybackSession:
    """Active audio playback session with monitoring"""
    session_id: str
    request: AudioRequest
    sound_file: str
    start_time: float

    state: AudioPlaybackState = AudioPlaybackState.PLAYING
    expected_duration: Optional[float] = None
    actual_duration: Optional[float] = None
    volume_level: float = 1.0

    # Performance tracking
    latency_ms: float = 0.0
    playback_quality: float = 1.0
    interruption_count: int = 0

class R2D2AudioIntelligence:
    """
    Advanced audio intelligence system providing context-aware R2D2 sound selection
    and playback with behavioral synchronization
    """

    def __init__(self, sound_directory: str = "/home/rolo/r2ai/My R2/R2"):
        """Initialize the audio intelligence system"""

        # Core sound system integration
        self.sound_enhancer = R2D2CanonicalSoundEnhancer(sound_directory)
        self.sound_directory = sound_directory

        # Audio playback system
        self.audio_queue = queue.PriorityQueue()
        self.active_sessions: Dict[str, AudioPlaybackSession] = {}
        self.current_session: Optional[AudioPlaybackSession] = None

        # Behavioral integration
        self.current_personality_mode = R2D2PersonalityAudioMode.STANDARD
        self.behavioral_state: Optional[str] = None
        self.environmental_context: Dict[str, Any] = {}
        self.social_context: str = "alone"

        # Audio context mapping
        self.behavioral_audio_mappings = self._create_behavioral_audio_mappings()
        self.personality_modifiers = self._create_personality_modifiers()
        self.contextual_triggers = self._create_contextual_triggers()

        # Performance and metrics
        self.performance_metrics = {
            'requests_processed': 0,
            'sounds_played': 0,
            'average_latency_ms': 0.0,
            'success_rate': 1.0,
            'uptime_start': time.time(),
            'context_hits': 0,
            'personality_adjustments': 0
        }

        # Configuration
        self.config = {
            'max_concurrent_sounds': 1,  # R2D2 typically plays one sound at a time
            'default_volume': 0.8,
            'max_queue_size': 10,
            'audio_fade_duration': 0.1,
            'latency_target_ms': 50.0,
            'personality_adaptation_rate': 0.1,
            'context_memory_duration': 300.0  # 5 minutes
        }

        # System control
        self.running = False
        self.audio_thread: Optional[threading.Thread] = None

        # Initialize pygame mixer for audio playback
        self._initialize_audio_system()

        logger.info("R2D2 Audio Intelligence System initialized")
        self._log_system_status()

    def _initialize_audio_system(self):
        """Initialize the audio playback system"""
        try:
            pygame.mixer.pre_init(frequency=22050, size=-16, channels=2, buffer=512)
            pygame.mixer.init()

            # Test audio system
            logger.info("✅ Pygame audio system initialized")
            logger.info(f"   Frequency: {pygame.mixer.get_init()[0]} Hz")
            logger.info(f"   Channels: {pygame.mixer.get_init()[2]}")

        except Exception as e:
            logger.error(f"Failed to initialize audio system: {e}")
            logger.warning("Audio system will operate in simulation mode")

    def _create_behavioral_audio_mappings(self) -> Dict[str, Dict[str, Any]]:
        """Create mappings between behavioral states and audio contexts"""
        return {
            # Greeting behaviors
            'greeting_enthusiastic_friend': {
                'primary_context': R2D2EmotionalContext.GREETING_FRIENDS,
                'secondary_contexts': [R2D2EmotionalContext.HAPPY_EXCITED],
                'personality_emphasis': 1.2,
                'allow_playful': True
            },
            'greeting_curious_stranger': {
                'primary_context': R2D2EmotionalContext.CURIOUS_INQUISITIVE,
                'secondary_contexts': [R2D2EmotionalContext.CHATTING_CASUAL],
                'personality_emphasis': 0.9,
                'allow_questioning': True
            },

            # Character recognition behaviors
            'jedi_recognition_respect': {
                'primary_context': R2D2EmotionalContext.JEDI_RECOGNITION,
                'secondary_contexts': [R2D2EmotionalContext.ALERT_WARNING],
                'personality_emphasis': 1.0,
                'force_respectful': True
            },
            'droid_excitement': {
                'primary_context': R2D2EmotionalContext.ASTROMECH_DUTIES,
                'secondary_contexts': [R2D2EmotionalContext.HAPPY_EXCITED],
                'personality_emphasis': 1.3,
                'allow_excited': True
            },

            # Personality behaviors
            'stubborn_resistance': {
                'primary_context': R2D2EmotionalContext.FRUSTRATED_STUBBORN,
                'secondary_contexts': [R2D2EmotionalContext.EXPRESSING_SARCASM],
                'personality_emphasis': 1.5,
                'force_stubborn': True,
                'allow_sarcastic': True
            },
            'playful_entertainment': {
                'primary_context': R2D2EmotionalContext.PLAYFUL_MISCHIEVOUS,
                'secondary_contexts': [R2D2EmotionalContext.MUSICAL_ENTERTAINMENT],
                'personality_emphasis': 1.4,
                'allow_playful': True,
                'prefer_musical': True
            },

            # Environmental behaviors
            'environmental_scan': {
                'primary_context': R2D2EmotionalContext.CURIOUS_INQUISITIVE,
                'secondary_contexts': [R2D2EmotionalContext.ASTROMECH_DUTIES],
                'personality_emphasis': 0.8,
                'systematic_sounds': True
            },
            'alert_response': {
                'primary_context': R2D2EmotionalContext.ALERT_WARNING,
                'secondary_contexts': [R2D2EmotionalContext.SAD_WORRIED],
                'personality_emphasis': 1.1,
                'urgent_priority': True
            },

            # System behaviors
            'system_startup': {
                'primary_context': R2D2EmotionalContext.POWER_UP_DOWN,
                'secondary_contexts': [R2D2EmotionalContext.ASTROMECH_DUTIES],
                'personality_emphasis': 1.0,
                'systematic_sequence': True
            },
            'maintenance_check': {
                'primary_context': R2D2EmotionalContext.ASTROMECH_DUTIES,
                'secondary_contexts': [R2D2EmotionalContext.POWER_UP_DOWN],
                'personality_emphasis': 0.7,
                'technical_focus': True
            }
        }

    def _create_personality_modifiers(self) -> Dict[R2D2PersonalityAudioMode, Dict[str, Any]]:
        """Create personality-specific audio modifiers"""
        return {
            R2D2PersonalityAudioMode.STANDARD: {
                'stubbornness_factor': 0.3,
                'playfulness_factor': 0.6,
                'curiosity_factor': 0.8,
                'energy_modifier': 1.0,
                'sarcasm_tolerance': 0.4
            },
            R2D2PersonalityAudioMode.CURIOUS: {
                'stubbornness_factor': 0.2,
                'playfulness_factor': 0.7,
                'curiosity_factor': 1.2,
                'energy_modifier': 1.1,
                'preferred_contexts': [R2D2EmotionalContext.CURIOUS_INQUISITIVE,
                                     R2D2EmotionalContext.RESPONDING_QUESTIONS]
            },
            R2D2PersonalityAudioMode.PLAYFUL: {
                'stubbornness_factor': 0.1,
                'playfulness_factor': 1.4,
                'curiosity_factor': 0.9,
                'energy_modifier': 1.3,
                'preferred_contexts': [R2D2EmotionalContext.PLAYFUL_MISCHIEVOUS,
                                     R2D2EmotionalContext.MUSICAL_ENTERTAINMENT]
            },
            R2D2PersonalityAudioMode.STUBBORN: {
                'stubbornness_factor': 0.8,
                'playfulness_factor': 0.3,
                'curiosity_factor': 0.5,
                'energy_modifier': 0.9,
                'sarcasm_tolerance': 0.7,
                'preferred_contexts': [R2D2EmotionalContext.FRUSTRATED_STUBBORN,
                                     R2D2EmotionalContext.EXPRESSING_SARCASM]
            },
            R2D2PersonalityAudioMode.EXCITED: {
                'stubbornness_factor': 0.1,
                'playfulness_factor': 1.2,
                'curiosity_factor': 1.1,
                'energy_modifier': 1.5,
                'preferred_contexts': [R2D2EmotionalContext.HAPPY_EXCITED,
                                     R2D2EmotionalContext.PLAYFUL_MISCHIEVOUS]
            },
            R2D2PersonalityAudioMode.CALM: {
                'stubbornness_factor': 0.2,
                'playfulness_factor': 0.4,
                'curiosity_factor': 0.6,
                'energy_modifier': 0.7,
                'preferred_contexts': [R2D2EmotionalContext.ASTROMECH_DUTIES,
                                     R2D2EmotionalContext.POWER_UP_DOWN]
            },
            R2D2PersonalityAudioMode.ALERT: {
                'stubbornness_factor': 0.4,
                'playfulness_factor': 0.2,
                'curiosity_factor': 1.0,
                'energy_modifier': 1.2,
                'preferred_contexts': [R2D2EmotionalContext.ALERT_WARNING,
                                     R2D2EmotionalContext.CURIOUS_INQUISITIVE]
            },
            R2D2PersonalityAudioMode.SOCIAL: {
                'stubbornness_factor': 0.2,
                'playfulness_factor': 0.9,
                'curiosity_factor': 0.8,
                'energy_modifier': 1.1,
                'preferred_contexts': [R2D2EmotionalContext.GREETING_FRIENDS,
                                     R2D2EmotionalContext.CHATTING_CASUAL,
                                     R2D2EmotionalContext.SHOWING_AFFECTION]
            }
        }

    def _create_contextual_triggers(self) -> Dict[str, Dict[str, Any]]:
        """Create context-based audio trigger mappings"""
        return {
            'person_detected_first_time': {
                'contexts': [R2D2EmotionalContext.CURIOUS_INQUISITIVE],
                'priority_boost': 2,
                'delay_range': (0.5, 1.5)
            },
            'person_detected_familiar': {
                'contexts': [R2D2EmotionalContext.GREETING_FRIENDS],
                'priority_boost': 3,
                'delay_range': (0.2, 0.8)
            },
            'multiple_people_detected': {
                'contexts': [R2D2EmotionalContext.PLAYFUL_MISCHIEVOUS],
                'personality_switch': R2D2PersonalityAudioMode.SOCIAL,
                'priority_boost': 1
            },
            'child_detected': {
                'contexts': [R2D2EmotionalContext.HAPPY_EXCITED],
                'personality_switch': R2D2PersonalityAudioMode.PLAYFUL,
                'energy_boost': 1.2
            },
            'jedi_character_detected': {
                'contexts': [R2D2EmotionalContext.JEDI_RECOGNITION],
                'priority_boost': 5,
                'force_respectful': True
            },
            'crowd_environment': {
                'contexts': [R2D2EmotionalContext.MUSICAL_ENTERTAINMENT],
                'personality_switch': R2D2PersonalityAudioMode.EXCITED,
                'performance_mode': True
            },
            'quiet_environment': {
                'contexts': [R2D2EmotionalContext.ASTROMECH_DUTIES],
                'personality_switch': R2D2PersonalityAudioMode.CALM,
                'volume_modifier': 0.7
            }
        }

    async def start_audio_intelligence(self):
        """Start the audio intelligence processing system"""
        logger.info("🔊 Starting R2D2 Audio Intelligence System")

        self.running = True

        # Start audio processing thread
        self.audio_thread = threading.Thread(
            target=self._audio_processing_loop,
            daemon=True,
            name="AudioIntelligence"
        )
        self.audio_thread.start()

        logger.info("Audio Intelligence System running")

    def _audio_processing_loop(self):
        """Main audio processing loop"""
        logger.info("Audio processing loop started")

        while self.running:
            try:
                # Process audio queue
                if not self.audio_queue.empty():
                    priority, timestamp, request = self.audio_queue.get_nowait()

                    # Check if request is still valid
                    if request.expiry_time is None or time.time() < request.expiry_time:
                        self._process_audio_request(request)
                    else:
                        logger.debug(f"Audio request expired: {request.request_id}")

                # Monitor active playback sessions
                self._monitor_playback_sessions()

                # Clean up completed sessions
                self._cleanup_completed_sessions()

                time.sleep(0.05)  # 20Hz processing

            except queue.Empty:
                time.sleep(0.1)
            except Exception as e:
                logger.error(f"Error in audio processing loop: {e}")
                time.sleep(1.0)

    def request_audio_playback(self, audio_context: R2D2EmotionalContext,
                             behavioral_state: Optional[str] = None,
                             environmental_context: Optional[Dict[str, Any]] = None,
                             priority: int = 1,
                             sync_mode: AudioSyncMode = AudioSyncMode.IMMEDIATE,
                             **kwargs) -> str:
        """Request audio playback with intelligent context selection"""
        try:
            # Generate request ID
            request_id = f"audio_{int(time.time() * 1000)}_{random.randint(1000, 9999)}"

            # Create audio request
            request = AudioRequest(
                request_id=request_id,
                audio_context=audio_context,
                priority=priority,
                behavioral_state=behavioral_state,
                environmental_context=environmental_context or {},
                social_context=self.social_context,
                sync_mode=sync_mode,
                personality_mode=self.current_personality_mode,
                **kwargs
            )

            # Set expiry time if not provided
            if request.expiry_time is None:
                request.expiry_time = time.time() + 30.0  # 30 second default expiry

            # Add to priority queue (negative priority for high-priority-first)
            priority_score = -request.priority
            self.audio_queue.put((priority_score, time.time(), request))

            logger.debug(f"Queued audio request: {request_id} (context: {audio_context.value})")

            return request_id

        except Exception as e:
            logger.error(f"Error requesting audio playback: {e}")
            return ""

    def _process_audio_request(self, request: AudioRequest):
        """Process an individual audio request"""
        try:
            start_time = time.time()

            # Select appropriate sound based on context and personality
            selected_sound = self._select_contextual_sound(request)

            if not selected_sound:
                logger.warning(f"No suitable sound found for context: {request.audio_context.value}")
                return

            # Apply personality and behavioral modifiers
            final_sound = self._apply_personality_modifiers(selected_sound, request)

            # Create playback session
            session = AudioPlaybackSession(
                session_id=f"session_{request.request_id}",
                request=request,
                sound_file=final_sound,
                start_time=time.time(),
                latency_ms=(time.time() - start_time) * 1000
            )

            # Execute playback based on sync mode
            success = self._execute_audio_playback(session)

            if success:
                self.active_sessions[session.session_id] = session

                # Update current session if immediate playback
                if request.sync_mode == AudioSyncMode.IMMEDIATE:
                    self.current_session = session

                # Update metrics
                self.performance_metrics['requests_processed'] += 1
                self.performance_metrics['sounds_played'] += 1

                # Update average latency
                current_avg = self.performance_metrics['average_latency_ms']
                count = self.performance_metrics['requests_processed']
                new_avg = (current_avg * (count - 1) + session.latency_ms) / count
                self.performance_metrics['average_latency_ms'] = new_avg

                logger.info(f"🔊 Playing: {final_sound} (latency: {session.latency_ms:.1f}ms)")

            else:
                logger.error(f"Failed to play audio: {final_sound}")
                session.state = AudioPlaybackState.FAILED

        except Exception as e:
            logger.error(f"Error processing audio request {request.request_id}: {e}")

    def _select_contextual_sound(self, request: AudioRequest) -> Optional[str]:
        """Select appropriate sound based on context and current state"""
        try:
            # Check for forced specific sound
            if request.force_specific_sound:
                return request.force_specific_sound

            # Get behavioral audio mapping if available
            behavioral_mapping = None
            if request.behavioral_state:
                behavioral_mapping = self.behavioral_audio_mappings.get(request.behavioral_state)

            # Get personality modifiers
            personality_modifier = self.personality_modifiers.get(
                request.personality_mode,
                self.personality_modifiers[R2D2PersonalityAudioMode.STANDARD]
            )

            # Select primary context
            primary_context = request.audio_context
            if behavioral_mapping:
                primary_context = behavioral_mapping['primary_context']

            # Try to get sound for primary context first
            selected_sound = self.sound_enhancer.get_sound_for_context(
                primary_context,
                allow_stubborn=request.allow_stubborn and personality_modifier.get('sarcasm_tolerance', 0.5) > 0.3,
                allow_sarcastic=request.allow_sarcastic and personality_modifier.get('sarcasm_tolerance', 0.5) > 0.5
            )

            # Try secondary contexts if primary failed
            if not selected_sound and behavioral_mapping:
                for secondary_context in behavioral_mapping.get('secondary_contexts', []):
                    selected_sound = self.sound_enhancer.get_sound_for_context(
                        secondary_context,
                        allow_stubborn=request.allow_stubborn,
                        allow_sarcastic=request.allow_sarcastic
                    )
                    if selected_sound:
                        break

            # Try stubborn response if personality allows
            if not selected_sound and personality_modifier.get('stubbornness_factor', 0.3) > 0.5:
                selected_sound = self.sound_enhancer.get_stubborn_response(primary_context)

            # Try sarcastic response if personality allows
            if not selected_sound and personality_modifier.get('sarcasm_tolerance', 0.3) > 0.6:
                selected_sound = self.sound_enhancer.get_sarcastic_response(primary_context)

            # Fallback to any sound in context
            if not selected_sound:
                selected_sound = self.sound_enhancer.get_sound_for_context(primary_context)

            return selected_sound

        except Exception as e:
            logger.error(f"Error selecting contextual sound: {e}")
            return None

    def _apply_personality_modifiers(self, sound_file: str, request: AudioRequest) -> str:
        """Apply personality-based modifications to sound selection"""
        try:
            # Get personality modifiers
            personality_modifier = self.personality_modifiers.get(
                request.personality_mode,
                self.personality_modifiers[R2D2PersonalityAudioMode.STANDARD]
            )

            # Check if we should switch to a personality-preferred sound
            preferred_contexts = personality_modifier.get('preferred_contexts', [])
            if preferred_contexts and random.random() < 0.3:  # 30% chance to use preferred
                for preferred_context in preferred_contexts:
                    preferred_sound = self.sound_enhancer.get_sound_for_context(preferred_context)
                    if preferred_sound:
                        logger.debug(f"Switched to personality-preferred sound: {preferred_sound}")
                        return preferred_sound

            # Update personality metrics
            self.performance_metrics['personality_adjustments'] += 1

            return sound_file

        except Exception as e:
            logger.error(f"Error applying personality modifiers: {e}")
            return sound_file

    def _execute_audio_playback(self, session: AudioPlaybackSession) -> bool:
        """Execute audio playback for a session"""
        try:
            sound_file = session.sound_file
            request = session.request

            # Construct full path to sound file
            sound_path = os.path.join(self.sound_directory, sound_file)

            if not os.path.exists(sound_path):
                logger.error(f"Sound file not found: {sound_path}")
                return False

            # Handle different sync modes
            if request.sync_mode == AudioSyncMode.IMMEDIATE:
                return self._play_audio_immediate(session, sound_path)
            elif request.sync_mode == AudioSyncMode.DELAYED:
                return self._play_audio_delayed(session, sound_path)
            elif request.sync_mode == AudioSyncMode.SERVO_SYNC:
                return self._play_audio_servo_sync(session, sound_path)
            else:
                return self._play_audio_immediate(session, sound_path)

        except Exception as e:
            logger.error(f"Error executing audio playback: {e}")
            return False

    def _play_audio_immediate(self, session: AudioPlaybackSession, sound_path: str) -> bool:
        """Play audio immediately"""
        try:
            # Load and play sound using pygame
            sound = pygame.mixer.Sound(sound_path)

            # Apply volume
            sound.set_volume(session.request.volume * self.config['default_volume'])

            # Play sound
            channel = sound.play()
            if channel:
                session.state = AudioPlaybackState.PLAYING

                # Estimate duration (pygame doesn't provide direct duration)
                # This is a rough estimate - in production you might use a library like mutagen
                session.expected_duration = 2.0  # Default 2 seconds for R2D2 sounds

                logger.debug(f"Audio playing: {os.path.basename(sound_path)}")
                return True
            else:
                logger.error(f"Failed to get audio channel for: {sound_path}")
                return False

        except pygame.error as e:
            logger.error(f"Pygame audio error: {e}")
            return False
        except Exception as e:
            logger.error(f"Error playing audio immediately: {e}")
            return False

    def _play_audio_delayed(self, session: AudioPlaybackSession, sound_path: str) -> bool:
        """Play audio with specified delay"""
        try:
            # Schedule delayed playback
            def delayed_playback():
                time.sleep(session.request.delay_seconds)
                self._play_audio_immediate(session, sound_path)

            delay_thread = threading.Thread(target=delayed_playback, daemon=True)
            delay_thread.start()

            session.state = AudioPlaybackState.QUEUED
            return True

        except Exception as e:
            logger.error(f"Error scheduling delayed audio: {e}")
            return False

    def _play_audio_servo_sync(self, session: AudioPlaybackSession, sound_path: str) -> bool:
        """Play audio synchronized with servo movement"""
        try:
            # For servo sync, we queue the audio and let the behavioral system trigger it
            # This would integrate with the servo choreographer
            session.state = AudioPlaybackState.QUEUED
            logger.debug(f"Audio queued for servo sync: {os.path.basename(sound_path)}")
            return True

        except Exception as e:
            logger.error(f"Error setting up servo sync audio: {e}")
            return False

    def _monitor_playback_sessions(self):
        """Monitor active audio playback sessions"""
        try:
            current_time = time.time()

            for session_id, session in list(self.active_sessions.items()):
                if session.state == AudioPlaybackState.PLAYING:
                    # Check if expected to be finished
                    if session.expected_duration:
                        elapsed = current_time - session.start_time
                        if elapsed >= session.expected_duration:
                            session.state = AudioPlaybackState.IDLE
                            session.actual_duration = elapsed

                            # Call completion callback if provided
                            if session.request.completion_callback:
                                try:
                                    session.request.completion_callback(session)
                                except Exception as e:
                                    logger.error(f"Error in completion callback: {e}")

                            logger.debug(f"Audio session completed: {session_id}")

        except Exception as e:
            logger.error(f"Error monitoring playback sessions: {e}")

    def _cleanup_completed_sessions(self):
        """Clean up completed audio sessions"""
        try:
            sessions_to_remove = []
            current_time = time.time()

            for session_id, session in self.active_sessions.items():
                # Remove sessions that are idle or failed for more than 30 seconds
                if session.state in [AudioPlaybackState.IDLE, AudioPlaybackState.FAILED]:
                    if current_time - session.start_time > 30.0:
                        sessions_to_remove.append(session_id)

            for session_id in sessions_to_remove:
                del self.active_sessions[session_id]

                # Clear current session if it's the one being removed
                if self.current_session and self.current_session.session_id == session_id:
                    self.current_session = None

        except Exception as e:
            logger.error(f"Error cleaning up sessions: {e}")

    def update_behavioral_context(self, behavioral_state: str,
                                environmental_context: Dict[str, Any],
                                social_context: str):
        """Update behavioral context for intelligent audio selection"""
        try:
            self.behavioral_state = behavioral_state
            self.environmental_context = environmental_context
            self.social_context = social_context

            # Check for contextual triggers
            self._process_contextual_triggers(environmental_context)

            # Adapt personality mode based on context
            self._adapt_personality_mode(environmental_context, social_context)

            logger.debug(f"Updated behavioral context: {behavioral_state} | {social_context}")

        except Exception as e:
            logger.error(f"Error updating behavioral context: {e}")

    def _process_contextual_triggers(self, environmental_context: Dict[str, Any]):
        """Process environmental context for automatic audio triggers"""
        try:
            people_count = environmental_context.get('people_count', 0)
            children_present = environmental_context.get('children_present', False)
            characters_detected = environmental_context.get('characters_detected', 0)

            # Check for contextual trigger conditions
            triggers_to_fire = []

            if people_count == 1 and self.social_context == "alone":
                triggers_to_fire.append('person_detected_first_time')
            elif people_count > 1:
                triggers_to_fire.append('multiple_people_detected')
            elif children_present:
                triggers_to_fire.append('child_detected')
            elif characters_detected > 0:
                triggers_to_fire.append('jedi_character_detected')
            elif people_count > 4:
                triggers_to_fire.append('crowd_environment')
            elif people_count == 0:
                triggers_to_fire.append('quiet_environment')

            # Fire appropriate triggers
            for trigger_name in triggers_to_fire:
                trigger_config = self.contextual_triggers.get(trigger_name)
                if trigger_config:
                    self._fire_contextual_trigger(trigger_name, trigger_config)

        except Exception as e:
            logger.error(f"Error processing contextual triggers: {e}")

    def _fire_contextual_trigger(self, trigger_name: str, trigger_config: Dict[str, Any]):
        """Fire a specific contextual audio trigger"""
        try:
            contexts = trigger_config.get('contexts', [])
            priority_boost = trigger_config.get('priority_boost', 0)

            if contexts:
                selected_context = random.choice(contexts)

                # Calculate delay
                delay_range = trigger_config.get('delay_range', (0.0, 0.0))
                delay = random.uniform(delay_range[0], delay_range[1])

                # Request audio playback
                request_id = self.request_audio_playback(
                    audio_context=selected_context,
                    priority=5 + priority_boost,
                    delay_seconds=delay,
                    behavioral_state=f"contextual_trigger_{trigger_name}"
                )

                logger.debug(f"Fired contextual trigger: {trigger_name} -> {selected_context.value}")

        except Exception as e:
            logger.error(f"Error firing contextual trigger {trigger_name}: {e}")

    def _adapt_personality_mode(self, environmental_context: Dict[str, Any], social_context: str):
        """Adapt personality mode based on current context"""
        try:
            current_mode = self.current_personality_mode
            new_mode = current_mode

            people_count = environmental_context.get('people_count', 0)
            children_present = environmental_context.get('children_present', False)

            # Adaptation logic
            if children_present and current_mode != R2D2PersonalityAudioMode.PLAYFUL:
                new_mode = R2D2PersonalityAudioMode.PLAYFUL
            elif people_count > 3 and current_mode != R2D2PersonalityAudioMode.SOCIAL:
                new_mode = R2D2PersonalityAudioMode.SOCIAL
            elif people_count == 0 and current_mode != R2D2PersonalityAudioMode.CALM:
                new_mode = R2D2PersonalityAudioMode.CALM
            elif people_count == 1 and social_context == "one_on_one":
                new_mode = R2D2PersonalityAudioMode.CURIOUS

            # Apply personality change with adaptation rate
            if new_mode != current_mode and random.random() < self.config['personality_adaptation_rate']:
                self.current_personality_mode = new_mode
                logger.info(f"🎭 Personality mode adapted: {current_mode.value} → {new_mode.value}")

        except Exception as e:
            logger.error(f"Error adapting personality mode: {e}")

    def stop_current_audio(self) -> bool:
        """Stop currently playing audio"""
        try:
            pygame.mixer.stop()

            if self.current_session:
                self.current_session.state = AudioPlaybackState.IDLE
                self.current_session = None

            logger.info("🔇 Current audio stopped")
            return True

        except Exception as e:
            logger.error(f"Error stopping audio: {e}")
            return False

    def get_audio_status(self) -> Dict[str, Any]:
        """Get comprehensive audio system status"""
        uptime = time.time() - self.performance_metrics['uptime_start']

        return {
            'system_status': {
                'running': self.running,
                'uptime_seconds': uptime,
                'audio_system_initialized': pygame.mixer.get_init() is not None,
                'sound_enhancer_available': self.sound_enhancer is not None
            },
            'playback_status': {
                'current_session': {
                    'session_id': self.current_session.session_id if self.current_session else None,
                    'sound_file': self.current_session.sound_file if self.current_session else None,
                    'state': self.current_session.state.value if self.current_session else 'idle',
                    'elapsed_time': (time.time() - self.current_session.start_time) if self.current_session else 0
                },
                'active_sessions': len(self.active_sessions),
                'queue_size': self.audio_queue.qsize()
            },
            'behavioral_context': {
                'personality_mode': self.current_personality_mode.value,
                'behavioral_state': self.behavioral_state,
                'social_context': self.social_context,
                'environmental_context': dict(self.environmental_context)
            },
            'performance_metrics': dict(self.performance_metrics),
            'sound_library': {
                'total_sounds': len(self.sound_enhancer.canonical_mappings) if self.sound_enhancer else 0,
                'contexts_available': len(self.sound_enhancer.emotional_context_groups) if self.sound_enhancer else 0
            }
        }

    def _log_system_status(self):
        """Log current system status for debugging"""
        try:
            status = self.get_audio_status()
            logger.info("🎵 Audio Intelligence System Status:")
            logger.info(f"   Sound Library: {status['sound_library']['total_sounds']} sounds")
            logger.info(f"   Audio Contexts: {status['sound_library']['contexts_available']} available")
            logger.info(f"   Personality Mode: {status['behavioral_context']['personality_mode']}")
            logger.info(f"   Behavioral Mappings: {len(self.behavioral_audio_mappings)} configured")

        except Exception as e:
            logger.error(f"Error logging system status: {e}")

    async def stop_audio_intelligence(self):
        """Stop the audio intelligence system"""
        logger.info("Stopping R2D2 Audio Intelligence System")

        self.running = False

        # Stop all audio
        self.stop_current_audio()

        # Clean up pygame
        pygame.mixer.quit()

        logger.info("Audio Intelligence System stopped")


def main():
    """Demonstrate the Audio Intelligence System"""
    print("🔊 R2D2 Advanced Audio Intelligence System")
    print("=" * 50)

    try:
        # Initialize audio intelligence
        audio_intelligence = R2D2AudioIntelligence()

        # Show system status
        status = audio_intelligence.get_audio_status()
        print(f"\n📊 System Status:")
        print(f"   Audio System: {'✅ Ready' if status['system_status']['audio_system_initialized'] else '❌ Failed'}")
        print(f"   Sound Library: {status['sound_library']['total_sounds']} canonical sounds")
        print(f"   Audio Contexts: {status['sound_library']['contexts_available']} available")

        # Test audio request
        print(f"\n🎵 Testing audio playback...")
        request_id = audio_intelligence.request_audio_playback(
            R2D2EmotionalContext.GREETING_FRIENDS,
            behavioral_state="greeting_test",
            priority=5
        )

        if request_id:
            print(f"   Audio request queued: {request_id}")

        print(f"\n🎭 Audio Intelligence System ready for R2D2 behavioral integration!")

    except Exception as e:
        logger.error(f"Demo error: {e}")


if __name__ == "__main__":
    main()