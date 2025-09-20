#!/usr/bin/env python3
"""
Disney-Level HCR Audio System Controller
======================================

Professional audio integration system for R2D2 with HCR sound board control,
real-time lip-sync automation, and spatial audio positioning. Designed for
convention-ready, crowd-pleasing audio-visual performances.

Features:
- HCR sound system serial communication
- Real-time audio analysis for lip-sync
- Spatial audio positioning and effects
- Disney-quality audio-visual synchronization
- Character personality-driven audio behaviors
- Convention-grade reliability and performance

Author: Imagineer Specialist Agent
Target: NVIDIA Orin Nano R2D2 Systems with HCR Audio
"""

import time
import math
import threading
import logging
import struct
import wave
import audioop
import asyncio
from typing import Dict, List, Tuple, Optional, Callable, Any, Union
from dataclasses import dataclass, field
from enum import Enum
import numpy as np
from collections import deque
import json
import serial
import pygame
import pyaudio
from scipy import signal
from scipy.fft import fft, fftfreq

# Configure logging for audio control
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AudioCommand(Enum):
    """HCR Audio System Commands"""
    PLAY_SOUND = 0x20
    STOP_SOUND = 0x21
    SET_VOLUME = 0x22
    PLAY_SEQUENCE = 0x23
    GET_STATUS = 0x24
    SET_SPATIAL_POS = 0x25
    ENABLE_LIPSYNC = 0x26
    DISABLE_LIPSYNC = 0x27
    SET_CHARACTER_MODE = 0x28
    EMERGENCY_STOP = 0x29

class CharacterMode(Enum):
    """R2D2 Character Personality Modes"""
    NORMAL = "normal"
    EXCITED = "excited"
    ALERT = "alert"
    CURIOUS = "curious"
    SLEEPY = "sleepy"
    ANGRY = "angry"
    HAPPY = "happy"
    SAD = "sad"
    CONFUSED = "confused"

class SpatialPosition(Enum):
    """Spatial audio positioning"""
    CENTER = "center"
    LEFT = "left"
    RIGHT = "right"
    FRONT = "front"
    BACK = "back"
    DOME = "dome"
    CHEST = "chest"

@dataclass
class AudioClip:
    """Audio clip metadata and processing information"""
    clip_id: int
    filename: str
    duration: float
    sample_rate: int = 44100
    channels: int = 1
    character_mode: CharacterMode = CharacterMode.NORMAL
    spatial_position: SpatialPosition = SpatialPosition.CENTER
    volume: float = 1.0
    loop: bool = False
    priority: int = 5  # 1-10, higher = more important
    lipsync_data: Optional[List[float]] = None

@dataclass
class LipSyncFrame:
    """Lip-sync animation frame data"""
    timestamp: float
    mouth_openness: float  # 0.0 to 1.0
    phoneme: str = ""
    energy: float = 0.0

@dataclass
class AudioState:
    """Current audio system state"""
    current_clip: Optional[AudioClip] = None
    volume_master: float = 0.8
    volume_effects: float = 0.7
    volume_voice: float = 0.9
    character_mode: CharacterMode = CharacterMode.NORMAL
    spatial_enabled: bool = True
    lipsync_enabled: bool = True
    is_playing: bool = False
    playback_position: float = 0.0

class HCRAudioController:
    """
    Disney-level HCR audio system controller with advanced features

    Provides comprehensive audio control including:
    - Serial communication with HCR sound boards
    - Real-time audio analysis for lip-sync
    - Spatial audio positioning
    - Character personality-driven behaviors
    - Disney-quality audio-visual synchronization
    """

    def __init__(self, serial_port: str = "/dev/ttyUSB0", baud_rate: int = 115200):
        """
        Initialize HCR audio controller

        Args:
            serial_port: Serial port for HCR communication
            baud_rate: Communication baud rate
        """
        self.serial_port = serial_port
        self.baud_rate = baud_rate
        self.serial_connection: Optional[serial.Serial] = None

        # Audio system state
        self.audio_state = AudioState()
        self.audio_clips: Dict[int, AudioClip] = {}
        self.lipsync_queue: deque = deque(maxlen=1000)

        # Real-time audio processing
        self.pyaudio_instance = None
        self.audio_stream = None
        self.sample_rate = 44100
        self.chunk_size = 1024
        self.audio_buffer: deque = deque(maxlen=100)

        # Threading for real-time processing
        self._audio_thread = None
        self._lipsync_thread = None
        self._audio_running = False
        self._audio_lock = threading.Lock()

        # Performance metrics
        self._performance_metrics = {
            'audio_latency_ms': 0.0,
            'lipsync_accuracy': 0.0,
            'commands_sent': 0,
            'errors_count': 0,
            'last_update_time': time.time()
        }

        # Character behavior patterns
        self._character_behaviors = self._initialize_character_behaviors()

        # Initialize subsystems
        self._initialize_serial_communication()
        self._initialize_audio_system()
        self._load_audio_library()

        # Start processing threads
        self._start_audio_threads()

        logger.info("HCR Audio Controller initialized successfully")

    def _initialize_serial_communication(self):
        """Initialize serial communication with HCR sound board"""
        try:
            self.serial_connection = serial.Serial(
                port=self.serial_port,
                baudrate=self.baud_rate,
                bytesize=serial.EIGHTBITS,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
                timeout=1.0,
                write_timeout=1.0
            )

            # Send handshake
            if self._send_command(AudioCommand.GET_STATUS, []):
                logger.info(f"HCR audio board connected on {self.serial_port}")
            else:
                logger.warning("HCR audio board not responding - using simulation mode")
                self.serial_connection = None

        except Exception as e:
            logger.error(f"Failed to initialize serial communication: {e}")
            self.serial_connection = None

    def _initialize_audio_system(self):
        """Initialize PyAudio for real-time audio processing"""
        try:
            self.pyaudio_instance = pyaudio.PyAudio()

            # Configure audio stream for real-time analysis
            self.audio_stream = self.pyaudio_instance.open(
                format=pyaudio.paFloat32,
                channels=1,
                rate=self.sample_rate,
                input=True,
                frames_per_buffer=self.chunk_size,
                stream_callback=self._audio_callback
            )

            # Initialize pygame mixer for playback
            pygame.mixer.pre_init(
                frequency=self.sample_rate,
                size=-16,
                channels=2,
                buffer=512
            )
            pygame.mixer.init()

            logger.info("Audio system initialized for real-time processing")

        except Exception as e:
            logger.error(f"Failed to initialize audio system: {e}")
            self.pyaudio_instance = None
            self.audio_stream = None

    def _initialize_character_behaviors(self) -> Dict[CharacterMode, Dict[str, Any]]:
        """Initialize character-specific audio behaviors"""
        return {
            CharacterMode.NORMAL: {
                'volume_modifier': 1.0,
                'pitch_modifier': 1.0,
                'speed_modifier': 1.0,
                'reverb_level': 0.2,
                'response_delay': 0.1
            },
            CharacterMode.EXCITED: {
                'volume_modifier': 1.2,
                'pitch_modifier': 1.1,
                'speed_modifier': 1.15,
                'reverb_level': 0.1,
                'response_delay': 0.05
            },
            CharacterMode.ALERT: {
                'volume_modifier': 1.3,
                'pitch_modifier': 1.2,
                'speed_modifier': 1.3,
                'reverb_level': 0.0,
                'response_delay': 0.0
            },
            CharacterMode.CURIOUS: {
                'volume_modifier': 0.9,
                'pitch_modifier': 1.05,
                'speed_modifier': 0.95,
                'reverb_level': 0.15,
                'response_delay': 0.2
            },
            CharacterMode.SLEEPY: {
                'volume_modifier': 0.7,
                'pitch_modifier': 0.9,
                'speed_modifier': 0.8,
                'reverb_level': 0.3,
                'response_delay': 0.5
            },
            CharacterMode.ANGRY: {
                'volume_modifier': 1.4,
                'pitch_modifier': 0.85,
                'speed_modifier': 1.2,
                'reverb_level': 0.05,
                'response_delay': 0.0
            },
            CharacterMode.HAPPY: {
                'volume_modifier': 1.1,
                'pitch_modifier': 1.15,
                'speed_modifier': 1.1,
                'reverb_level': 0.2,
                'response_delay': 0.1
            }
        }

    def _load_audio_library(self):
        """Load R2D2 audio library with character behaviors"""
        # Define comprehensive R2D2 sound library
        audio_library = [
            # Basic responses
            AudioClip(1, "r2d2_happy_beep.wav", 1.2, character_mode=CharacterMode.HAPPY),
            AudioClip(2, "r2d2_sad_whistle.wav", 2.1, character_mode=CharacterMode.SAD),
            AudioClip(3, "r2d2_excited_chirp.wav", 0.8, character_mode=CharacterMode.EXCITED),
            AudioClip(4, "r2d2_alert_beep.wav", 0.5, character_mode=CharacterMode.ALERT),
            AudioClip(5, "r2d2_curious_whistle.wav", 1.5, character_mode=CharacterMode.CURIOUS),

            # Greetings and interactions
            AudioClip(10, "r2d2_greeting_sequence.wav", 3.2, character_mode=CharacterMode.HAPPY),
            AudioClip(11, "r2d2_acknowledgment.wav", 1.0, character_mode=CharacterMode.NORMAL),
            AudioClip(12, "r2d2_goodbye.wav", 2.5, character_mode=CharacterMode.NORMAL),
            AudioClip(13, "r2d2_question_sound.wav", 1.8, character_mode=CharacterMode.CURIOUS),

            # Emotional responses
            AudioClip(20, "r2d2_frustrated_beeps.wav", 2.8, character_mode=CharacterMode.ANGRY),
            AudioClip(21, "r2d2_worried_whistle.wav", 2.2, character_mode=CharacterMode.SAD),
            AudioClip(22, "r2d2_laugh_sequence.wav", 1.9, character_mode=CharacterMode.HAPPY),
            AudioClip(23, "r2d2_surprise_beep.wav", 0.7, character_mode=CharacterMode.EXCITED),

            # Star Wars specific
            AudioClip(30, "r2d2_luke_recognition.wav", 4.1, character_mode=CharacterMode.EXCITED, priority=8),
            AudioClip(31, "r2d2_leia_message.wav", 5.2, character_mode=CharacterMode.ALERT, priority=9),
            AudioClip(32, "r2d2_c3po_interaction.wav", 3.8, character_mode=CharacterMode.NORMAL, priority=7),
            AudioClip(33, "r2d2_vader_fear.wav", 3.0, character_mode=CharacterMode.SAD, priority=8),

            # Functional sounds
            AudioClip(40, "r2d2_scanning.wav", 4.5, character_mode=CharacterMode.NORMAL, loop=True),
            AudioClip(41, "r2d2_processing.wav", 2.0, character_mode=CharacterMode.NORMAL, loop=True),
            AudioClip(42, "r2d2_power_up.wav", 3.7, character_mode=CharacterMode.NORMAL, priority=9),
            AudioClip(43, "r2d2_power_down.wav", 4.2, character_mode=CharacterMode.SLEEPY, priority=9),

            # Interactive responses
            AudioClip(50, "r2d2_photo_pose.wav", 1.5, character_mode=CharacterMode.HAPPY),
            AudioClip(51, "r2d2_costume_compliment.wav", 2.8, character_mode=CharacterMode.EXCITED),
            AudioClip(52, "r2d2_jedi_recognition.wav", 3.5, character_mode=CharacterMode.EXCITED, priority=8),
            AudioClip(53, "r2d2_sith_warning.wav", 2.9, character_mode=CharacterMode.ALERT, priority=7)
        ]

        # Store audio clips in dictionary
        for clip in audio_library:
            self.audio_clips[clip.clip_id] = clip

        logger.info(f"Loaded {len(audio_library)} audio clips into library")

    def _send_command(self, command: AudioCommand, data: List[int]) -> bool:
        """
        Send command to HCR audio board using unified protocol

        Args:
            command: Audio command to send
            data: Command data payload

        Returns:
            True if command sent successfully
        """
        if self.serial_connection is None:
            logger.debug(f"SIM: Audio command {command.name} with data {data}")
            return True

        try:
            # Unified protocol: [SYNC][DEVICE_ID][COMMAND][LENGTH][DATA][CHECKSUM]
            sync = 0xAA
            device_id = 0x02  # HCR Audio System
            cmd_byte = command.value
            length = len(data)

            # Build message
            message = [sync, device_id, cmd_byte, length] + data

            # Calculate XOR checksum
            checksum = 0
            for byte in message:
                checksum ^= byte

            message.append(checksum)

            # Send message
            self.serial_connection.write(bytes(message))
            self.serial_connection.flush()

            # Wait for acknowledgment
            response = self.serial_connection.read(3)  # Expecting ACK response

            if len(response) >= 1 and response[0] == 0x06:  # ACK
                self._performance_metrics['commands_sent'] += 1
                return True
            else:
                logger.warning(f"No ACK received for command {command.name}")
                self._performance_metrics['errors_count'] += 1
                return False

        except Exception as e:
            logger.error(f"Failed to send command {command.name}: {e}")
            self._performance_metrics['errors_count'] += 1
            return False

    def play_audio_clip(self, clip_id: int, volume: Optional[float] = None,
                       spatial_position: Optional[SpatialPosition] = None) -> bool:
        """
        Play audio clip with character personality and spatial positioning

        Args:
            clip_id: ID of audio clip to play
            volume: Override volume (0.0 to 1.0)
            spatial_position: Override spatial position

        Returns:
            True if playback started successfully
        """
        if clip_id not in self.audio_clips:
            logger.error(f"Audio clip {clip_id} not found")
            return False

        clip = self.audio_clips[clip_id]

        # Apply character behavior modifications
        behavior = self._character_behaviors[self.audio_state.character_mode]

        # Calculate final volume
        final_volume = (volume or clip.volume) * behavior['volume_modifier']
        final_volume = max(0.0, min(1.0, final_volume))

        # Prepare command data
        volume_byte = int(final_volume * 255)
        position_byte = (spatial_position or clip.spatial_position).value
        mode_byte = self.audio_state.character_mode.value

        command_data = [
            clip_id & 0xFF,
            (clip_id >> 8) & 0xFF,
            volume_byte,
            ord(position_byte[0]) if position_byte else 0,
            ord(mode_byte[0]) if mode_byte else 0
        ]

        # Send play command to HCR
        success = self._send_command(AudioCommand.PLAY_SOUND, command_data)

        if success:
            with self._audio_lock:
                self.audio_state.current_clip = clip
                self.audio_state.is_playing = True
                self.audio_state.playback_position = 0.0

            # Generate lip-sync data if enabled
            if self.audio_state.lipsync_enabled and clip.lipsync_data:
                self._start_lipsync_sequence(clip)

            logger.info(f"Playing audio clip {clip_id}: {clip.filename}")

        return success

    def stop_audio(self) -> bool:
        """Stop current audio playback"""
        success = self._send_command(AudioCommand.STOP_SOUND, [])

        if success:
            with self._audio_lock:
                self.audio_state.current_clip = None
                self.audio_state.is_playing = False
                self.audio_state.playback_position = 0.0
                self.lipsync_queue.clear()

        return success

    def set_character_mode(self, mode: CharacterMode) -> bool:
        """
        Set character personality mode

        Args:
            mode: Character mode to activate

        Returns:
            True if mode changed successfully
        """
        mode_data = [ord(mode.value[0])]
        success = self._send_command(AudioCommand.SET_CHARACTER_MODE, mode_data)

        if success:
            self.audio_state.character_mode = mode
            logger.info(f"Character mode changed to {mode.value}")

        return success

    def set_spatial_position(self, position: SpatialPosition,
                           distance: float = 1.0, azimuth: float = 0.0) -> bool:
        """
        Set spatial audio positioning

        Args:
            position: Spatial position preset
            distance: Distance factor (0.0 to 2.0)
            azimuth: Azimuth angle in degrees (-180 to 180)

        Returns:
            True if position set successfully
        """
        distance_byte = int(max(0, min(255, distance * 127)))
        azimuth_byte = int(max(0, min(255, (azimuth + 180) / 360 * 255)))
        position_byte = ord(position.value[0])

        command_data = [position_byte, distance_byte, azimuth_byte]
        success = self._send_command(AudioCommand.SET_SPATIAL_POS, command_data)

        return success

    def enable_lipsync(self, enable: bool = True) -> bool:
        """Enable or disable lip-sync automation"""
        command = AudioCommand.ENABLE_LIPSYNC if enable else AudioCommand.DISABLE_LIPSYNC
        success = self._send_command(command, [])

        if success:
            self.audio_state.lipsync_enabled = enable
            logger.info(f"Lip-sync {'enabled' if enable else 'disabled'}")

        return success

    def _audio_callback(self, in_data, frame_count, time_info, status):
        """PyAudio callback for real-time audio analysis"""
        try:
            # Convert audio data to numpy array
            audio_data = np.frombuffer(in_data, dtype=np.float32)

            # Store in buffer for processing
            self.audio_buffer.append(audio_data.copy())

            # Process for lip-sync if enabled
            if self.audio_state.lipsync_enabled and self.audio_state.is_playing:
                self._process_lipsync_frame(audio_data)

        except Exception as e:
            logger.error(f"Audio callback error: {e}")

        return (None, pyaudio.paContinue)

    def _process_lipsync_frame(self, audio_data: np.ndarray):
        """Process audio frame for lip-sync data"""
        try:
            # Calculate audio energy
            energy = np.sqrt(np.mean(audio_data ** 2))

            # Simple mouth openness calculation based on energy
            mouth_openness = min(1.0, energy * 10.0)  # Scale factor

            # Create lip-sync frame
            timestamp = time.time()
            lipsync_frame = LipSyncFrame(
                timestamp=timestamp,
                mouth_openness=mouth_openness,
                energy=energy
            )

            # Add to queue for servo coordination
            self.lipsync_queue.append(lipsync_frame)

        except Exception as e:
            logger.error(f"Lip-sync processing error: {e}")

    def _start_lipsync_sequence(self, clip: AudioClip):
        """Start pre-computed lip-sync sequence for audio clip"""
        if not clip.lipsync_data:
            return

        def lipsync_playback():
            start_time = time.time()

            for i, mouth_value in enumerate(clip.lipsync_data):
                target_time = start_time + (i * 0.02)  # 50Hz update rate
                current_time = time.time()

                if current_time < target_time:
                    time.sleep(target_time - current_time)

                # Create lip-sync frame
                lipsync_frame = LipSyncFrame(
                    timestamp=current_time,
                    mouth_openness=mouth_value,
                    energy=mouth_value
                )

                self.lipsync_queue.append(lipsync_frame)

                # Check if playback stopped
                if not self.audio_state.is_playing:
                    break

        # Start lip-sync thread
        lipsync_thread = threading.Thread(target=lipsync_playback, daemon=True)
        lipsync_thread.start()

    def get_lipsync_data(self) -> Optional[LipSyncFrame]:
        """Get latest lip-sync data for servo coordination"""
        try:
            return self.lipsync_queue.popleft()
        except IndexError:
            return None

    def _start_audio_threads(self):
        """Start audio processing threads"""
        self._audio_running = True

        # Start audio stream
        if self.audio_stream:
            self.audio_stream.start_stream()

        # Start audio monitoring thread
        self._audio_thread = threading.Thread(target=self._audio_monitor_loop, daemon=True)
        self._audio_thread.start()

        logger.info("Audio processing threads started")

    def _audio_monitor_loop(self):
        """Audio monitoring and processing loop"""
        while self._audio_running:
            try:
                current_time = time.time()

                # Update playback position
                if self.audio_state.is_playing and self.audio_state.current_clip:
                    elapsed = current_time - self.audio_state.playback_position

                    if elapsed >= self.audio_state.current_clip.duration:
                        # Clip finished
                        with self._audio_lock:
                            self.audio_state.is_playing = False
                            self.audio_state.current_clip = None
                            self.audio_state.playback_position = 0.0

                # Calculate audio latency
                if len(self.audio_buffer) > 0:
                    buffer_duration = len(self.audio_buffer) * self.chunk_size / self.sample_rate
                    self._performance_metrics['audio_latency_ms'] = buffer_duration * 1000

                # Update performance metrics
                self._performance_metrics['last_update_time'] = current_time

                time.sleep(0.01)  # 100Hz monitoring

            except Exception as e:
                logger.error(f"Audio monitor loop error: {e}")
                time.sleep(0.1)

    def stop_audio_threads(self):
        """Stop audio processing threads"""
        self._audio_running = False

        if self.audio_stream:
            self.audio_stream.stop_stream()

        if self._audio_thread and self._audio_thread.is_alive():
            self._audio_thread.join(timeout=2.0)

    def emergency_stop(self):
        """Emergency stop all audio operations"""
        logger.warning("AUDIO EMERGENCY STOP activated")

        # Stop all audio
        self.stop_audio()

        # Send emergency stop to HCR
        self._send_command(AudioCommand.EMERGENCY_STOP, [])

        # Clear all queues
        self.lipsync_queue.clear()
        self.audio_buffer.clear()

    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get audio system performance metrics"""
        return {
            **self._performance_metrics,
            'audio_state': {
                'is_playing': self.audio_state.is_playing,
                'character_mode': self.audio_state.character_mode.value,
                'volume_master': self.audio_state.volume_master,
                'lipsync_enabled': self.audio_state.lipsync_enabled,
                'current_clip_id': self.audio_state.current_clip.clip_id if self.audio_state.current_clip else None
            },
            'buffer_status': {
                'audio_buffer_size': len(self.audio_buffer),
                'lipsync_queue_size': len(self.lipsync_queue)
            },
            'hardware_status': {
                'serial_connected': self.serial_connection is not None,
                'audio_stream_active': self.audio_stream is not None and self.audio_stream.is_active()
            }
        }

    def save_performance_profile(self, filename: str):
        """Save audio performance profile"""
        try:
            profile_data = {
                'timestamp': time.time(),
                'audio_clips_loaded': len(self.audio_clips),
                'character_behaviors': {mode.value: behavior for mode, behavior in self._character_behaviors.items()},
                'performance_metrics': self.get_performance_metrics(),
                'system_config': {
                    'serial_port': self.serial_port,
                    'baud_rate': self.baud_rate,
                    'sample_rate': self.sample_rate,
                    'chunk_size': self.chunk_size
                }
            }

            with open(filename, 'w') as f:
                json.dump(profile_data, f, indent=2)

            logger.info(f"Audio performance profile saved to {filename}")

        except Exception as e:
            logger.error(f"Failed to save audio performance profile: {e}")

    def __del__(self):
        """Cleanup when controller is destroyed"""
        self.stop_audio_threads()

        if self.audio_stream:
            self.audio_stream.close()

        if self.pyaudio_instance:
            self.pyaudio_instance.terminate()

        if self.serial_connection:
            self.serial_connection.close()


# R2D2 Character Audio Behaviors
class R2D2AudioPersonality:
    """
    R2D2 character-specific audio personality and behaviors
    """

    def __init__(self, audio_controller: HCRAudioController):
        self.audio_controller = audio_controller
        self._interaction_history: deque = deque(maxlen=50)
        self._personality_state = {
            'excitement_level': 0.5,
            'curiosity_level': 0.5,
            'alertness_level': 0.5,
            'last_interaction': 0.0
        }

    def react_to_jedi(self, confidence: float = 0.8) -> bool:
        """React to Jedi character detection"""
        if confidence > 0.7:
            self.audio_controller.set_character_mode(CharacterMode.EXCITED)
            return self.audio_controller.play_audio_clip(52)  # Jedi recognition
        return False

    def react_to_sith(self, confidence: float = 0.8) -> bool:
        """React to Sith character detection"""
        if confidence > 0.7:
            self.audio_controller.set_character_mode(CharacterMode.ALERT)
            return self.audio_controller.play_audio_clip(53)  # Sith warning
        return False

    def greet_guest(self, is_repeat_visitor: bool = False) -> bool:
        """Greet convention guest"""
        if is_repeat_visitor:
            self.audio_controller.set_character_mode(CharacterMode.HAPPY)
            return self.audio_controller.play_audio_clip(11)  # Acknowledgment
        else:
            self.audio_controller.set_character_mode(CharacterMode.NORMAL)
            return self.audio_controller.play_audio_clip(10)  # Greeting sequence

    def express_curiosity(self, stimulus_strength: float = 0.5) -> bool:
        """Express curiosity about environment"""
        self.audio_controller.set_character_mode(CharacterMode.CURIOUS)
        return self.audio_controller.play_audio_clip(5)  # Curious whistle

    def alert_sequence(self, urgency: float = 0.5) -> bool:
        """Play alert sequence based on urgency"""
        if urgency > 0.8:
            self.audio_controller.set_character_mode(CharacterMode.ALERT)
            return self.audio_controller.play_audio_clip(4)  # Alert beep
        else:
            self.audio_controller.set_character_mode(CharacterMode.CURIOUS)
            return self.audio_controller.play_audio_clip(13)  # Question sound


if __name__ == "__main__":
    # Example usage and testing
    print("Disney HCR Audio Controller - R2D2 Demo")
    print("=" * 50)

    # Create audio controller
    audio_controller = HCRAudioController()
    r2d2_personality = R2D2AudioPersonality(audio_controller)

    try:
        # Demo sequence
        print("Starting audio demo sequence...")

        # Greeting
        r2d2_personality.greet_guest()
        time.sleep(4)

        # Curious reaction
        r2d2_personality.express_curiosity()
        time.sleep(2)

        # Jedi reaction
        r2d2_personality.react_to_jedi(0.9)
        time.sleep(4)

        # Alert sequence
        r2d2_personality.alert_sequence(0.6)
        time.sleep(3)

        # Display performance metrics
        metrics = audio_controller.get_performance_metrics()
        print(f"\nAudio Performance Metrics:")
        print(f"Commands Sent: {metrics['commands_sent']}")
        print(f"Audio Latency: {metrics['audio_latency_ms']:.1f}ms")
        print(f"Lip-sync Enabled: {metrics['audio_state']['lipsync_enabled']}")

        # Save performance profile
        audio_controller.save_performance_profile(
            "/home/rolo/r2ai/.claude/agent_storage/imagineer-specialist/audio_performance_profile.json"
        )

    except KeyboardInterrupt:
        print("\nDemo interrupted - performing emergency stop")
        audio_controller.emergency_stop()
    except Exception as e:
        print(f"Error during demo: {e}")
        audio_controller.emergency_stop()
    finally:
        print("Audio demo completed")