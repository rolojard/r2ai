#!/usr/bin/env python3
"""
Disney-Level Spatial Audio Positioning System
============================================

Advanced spatial audio system for R2D2 providing immersive 3D audio experiences
with directional sound positioning, environmental audio effects, and crowd-aware
audio management for convention environments.

Features:
- 3D spatial audio positioning with HRTF processing
- Multi-speaker array management for directional audio
- Environmental audio effects and acoustic modeling
- Crowd-aware volume and directional adjustments
- Disney-quality immersive audio experience
- Real-time audio positioning based on guest interaction

Author: Imagineer Specialist Agent
Target: NVIDIA Orin Nano R2D2 Systems with Multi-Speaker Arrays
"""

import time
import math
import threading
import logging
import numpy as np
from typing import Dict, List, Tuple, Optional, Callable, Any, Union
from dataclasses import dataclass, field
from enum import Enum
import json
import pygame
import scipy.signal
from scipy.spatial.distance import euclidean
from scipy.interpolate import interp1d
import pyaudio

# Configure logging for spatial audio
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SpeakerLocation(Enum):
    """Physical speaker locations on R2D2"""
    DOME_FRONT = "dome_front"
    DOME_LEFT = "dome_left"
    DOME_RIGHT = "dome_right"
    DOME_BACK = "dome_back"
    CHEST_CENTER = "chest_center"
    CHEST_LEFT = "chest_left"
    CHEST_RIGHT = "chest_right"
    BODY_LEFT = "body_left"
    BODY_RIGHT = "body_right"
    BODY_REAR = "body_rear"
    LEG_LEFT = "leg_left"
    LEG_RIGHT = "leg_right"

class AudioZone(Enum):
    """Audio zones for spatial positioning"""
    INTIMATE = "intimate"      # Very close (0-2 feet)
    PERSONAL = "personal"      # Close interaction (2-4 feet)
    SOCIAL = "social"         # Normal conversation (4-8 feet)
    PUBLIC = "public"         # Crowd/performance (8+ feet)

class EnvironmentalEffect(Enum):
    """Environmental audio effects"""
    NONE = "none"
    REVERB_SMALL = "reverb_small"    # Small room
    REVERB_MEDIUM = "reverb_medium"  # Medium hall
    REVERB_LARGE = "reverb_large"    # Large convention hall
    ECHO = "echo"                    # Echo effect
    DELAY = "delay"                  # Delay effect
    CHORUS = "chorus"                # Chorus effect
    OUTDOORS = "outdoors"            # Outdoor acoustics

@dataclass
class SpeakerConfig:
    """Configuration for individual speaker"""
    speaker_id: str
    location: SpeakerLocation
    position: Tuple[float, float, float]  # x, y, z coordinates relative to R2D2 center
    max_volume: float = 1.0
    frequency_response: Tuple[int, int] = (80, 20000)  # Hz range
    directional_pattern: str = "omnidirectional"  # or "directional"
    active: bool = True

@dataclass
class AudioSource:
    """3D audio source definition"""
    source_id: str
    position: Tuple[float, float, float]  # x, y, z in world coordinates
    velocity: Tuple[float, float, float] = (0.0, 0.0, 0.0)
    volume: float = 1.0
    frequency: float = 440.0
    directional: bool = False
    cone_angle: float = 60.0  # degrees
    distance_attenuation: bool = True

@dataclass
class ListenerPosition:
    """3D listener (guest) position"""
    position: Tuple[float, float, float]
    orientation: Tuple[float, float, float]  # pitch, yaw, roll
    head_size: float = 0.2  # meters for HRTF calculation

@dataclass
class SpatialAudioFrame:
    """Single frame of spatial audio processing"""
    timestamp: float
    listener_position: ListenerPosition
    audio_sources: List[AudioSource]
    speaker_outputs: Dict[str, float]  # speaker_id -> volume
    environmental_effect: EnvironmentalEffect
    zone: AudioZone

class SpatialAudioSystem:
    """
    Disney-quality spatial audio system with 3D positioning

    Provides immersive audio experience through:
    - Multi-speaker array management for directional audio
    - Real-time 3D audio positioning and HRTF processing
    - Environmental effects and acoustic modeling
    - Crowd-aware audio management and volume adjustment
    - Guest interaction-based audio positioning
    """

    def __init__(self, sample_rate: int = 44100):
        """
        Initialize spatial audio system

        Args:
            sample_rate: Audio sample rate
        """
        self.sample_rate = sample_rate
        self.buffer_size = 512

        # Speaker configuration
        self.speakers: Dict[str, SpeakerConfig] = {}
        self.audio_sources: Dict[str, AudioSource] = {}

        # Current listener state
        self.primary_listener = ListenerPosition((0.0, 2.0, 0.0), (0.0, 0.0, 0.0))
        self.secondary_listeners: List[ListenerPosition] = []

        # Environmental settings
        self.current_environment = EnvironmentalEffect.REVERB_MEDIUM
        self.ambient_noise_level = 0.1
        self.crowd_density = 0.5  # 0.0 to 1.0

        # Processing state
        self.audio_processing_active = False
        self._processing_thread = None
        self._audio_lock = threading.Lock()

        # Performance metrics
        self._performance_metrics = {
            'frames_processed': 0,
            'speaker_updates': 0,
            'listener_updates': 0,
            'environmental_changes': 0,
            'processing_latency_ms': 0.0,
            'last_update_time': time.time()
        }

        # HRTF data (simplified - would load actual HRTF datasets)
        self._hrtf_data = self._initialize_hrtf_data()

        # Initialize R2D2 speaker array
        self._initialize_r2d2_speakers()

        # Initialize environmental effects
        self._initialize_environmental_effects()

        logger.info("Spatial audio system initialized with Disney-quality processing")

    def _initialize_r2d2_speakers(self):
        """Initialize R2D2's speaker array configuration"""
        # Dome speakers for directional head audio
        self.speakers["dome_front"] = SpeakerConfig(
            "dome_front", SpeakerLocation.DOME_FRONT,
            (0.0, 1.1, 0.3), max_volume=0.9, directional_pattern="directional"
        )

        self.speakers["dome_left"] = SpeakerConfig(
            "dome_left", SpeakerLocation.DOME_LEFT,
            (-0.2, 1.1, 0.0), max_volume=0.8
        )

        self.speakers["dome_right"] = SpeakerConfig(
            "dome_right", SpeakerLocation.DOME_RIGHT,
            (0.2, 1.1, 0.0), max_volume=0.8
        )

        self.speakers["dome_back"] = SpeakerConfig(
            "dome_back", SpeakerLocation.DOME_BACK,
            (0.0, 1.1, -0.2), max_volume=0.7
        )

        # Chest speakers for main audio output
        self.speakers["chest_center"] = SpeakerConfig(
            "chest_center", SpeakerLocation.CHEST_CENTER,
            (0.0, 0.6, 0.25), max_volume=1.0, directional_pattern="directional"
        )

        self.speakers["chest_left"] = SpeakerConfig(
            "chest_left", SpeakerLocation.CHEST_LEFT,
            (-0.15, 0.6, 0.2), max_volume=0.9
        )

        self.speakers["chest_right"] = SpeakerConfig(
            "chest_right", SpeakerLocation.CHEST_RIGHT,
            (0.15, 0.6, 0.2), max_volume=0.9
        )

        # Body speakers for surround effects
        self.speakers["body_left"] = SpeakerConfig(
            "body_left", SpeakerLocation.BODY_LEFT,
            (-0.25, 0.3, 0.0), max_volume=0.7
        )

        self.speakers["body_right"] = SpeakerConfig(
            "body_right", SpeakerLocation.BODY_RIGHT,
            (0.25, 0.3, 0.0), max_volume=0.7
        )

        self.speakers["body_rear"] = SpeakerConfig(
            "body_rear", SpeakerLocation.BODY_REAR,
            (0.0, 0.3, -0.3), max_volume=0.6
        )

        # Leg speakers for low-frequency effects
        self.speakers["leg_left"] = SpeakerConfig(
            "leg_left", SpeakerLocation.LEG_LEFT,
            (-0.15, 0.1, 0.1), max_volume=0.8, frequency_response=(40, 200)
        )

        self.speakers["leg_right"] = SpeakerConfig(
            "leg_right", SpeakerLocation.LEG_RIGHT,
            (0.15, 0.1, 0.1), max_volume=0.8, frequency_response=(40, 200)
        )

        logger.info(f"Initialized {len(self.speakers)} speakers in R2D2 array")

    def _initialize_hrtf_data(self) -> Dict[str, Any]:
        """Initialize simplified HRTF (Head-Related Transfer Function) data"""
        # Simplified HRTF approximation
        # In a real implementation, this would load measured HRTF datasets

        angles = np.arange(0, 360, 15)  # 15-degree resolution
        hrtf_left = {}
        hrtf_right = {}

        for angle in angles:
            # Simple HRTF approximation based on angle
            rad = np.radians(angle)

            # Left ear response
            if angle <= 90 or angle >= 270:
                # Sound from front/right side
                left_gain = 0.5 + 0.5 * np.cos(rad)
                left_delay = 0.0
            else:
                # Sound from back/left side
                left_gain = 0.3 + 0.4 * np.cos(rad + np.pi)
                left_delay = 0.0006  # Head shadow delay

            # Right ear response
            if angle <= 180:
                # Sound from front/left side
                right_gain = 0.5 + 0.5 * np.cos(rad + np.pi)
                right_delay = 0.0006 if angle > 90 else 0.0
            else:
                # Sound from back/right side
                right_gain = 0.3 + 0.4 * np.cos(rad)
                right_delay = 0.0

            hrtf_left[angle] = {'gain': left_gain, 'delay': left_delay}
            hrtf_right[angle] = {'gain': right_gain, 'delay': right_delay}

        return {'left': hrtf_left, 'right': hrtf_right}

    def _initialize_environmental_effects(self):
        """Initialize environmental audio effects"""
        self.environmental_effects = {
            EnvironmentalEffect.NONE: {
                'reverb_time': 0.0,
                'reverb_level': 0.0,
                'high_freq_damping': 0.0,
                'echo_delay': 0.0,
                'echo_level': 0.0
            },
            EnvironmentalEffect.REVERB_SMALL: {
                'reverb_time': 0.8,
                'reverb_level': 0.2,
                'high_freq_damping': 0.3,
                'echo_delay': 0.0,
                'echo_level': 0.0
            },
            EnvironmentalEffect.REVERB_MEDIUM: {
                'reverb_time': 1.5,
                'reverb_level': 0.3,
                'high_freq_damping': 0.4,
                'echo_delay': 0.0,
                'echo_level': 0.0
            },
            EnvironmentalEffect.REVERB_LARGE: {
                'reverb_time': 3.0,
                'reverb_level': 0.5,
                'high_freq_damping': 0.6,
                'echo_delay': 0.0,
                'echo_level': 0.0
            },
            EnvironmentalEffect.ECHO: {
                'reverb_time': 1.0,
                'reverb_level': 0.2,
                'high_freq_damping': 0.3,
                'echo_delay': 0.3,
                'echo_level': 0.4
            },
            EnvironmentalEffect.OUTDOORS: {
                'reverb_time': 0.2,
                'reverb_level': 0.05,
                'high_freq_damping': 0.8,
                'echo_delay': 0.0,
                'echo_level': 0.0
            }
        }

    def add_audio_source(self, source_id: str, position: Tuple[float, float, float],
                        volume: float = 1.0, directional: bool = False) -> bool:
        """
        Add 3D audio source

        Args:
            source_id: Unique identifier for audio source
            position: 3D position (x, y, z)
            volume: Source volume (0.0 to 1.0)
            directional: Whether source is directional

        Returns:
            True if source was added successfully
        """
        try:
            self.audio_sources[source_id] = AudioSource(
                source_id=source_id,
                position=position,
                volume=volume,
                directional=directional
            )

            logger.info(f"Added audio source '{source_id}' at position {position}")
            return True

        except Exception as e:
            logger.error(f"Failed to add audio source '{source_id}': {e}")
            return False

    def update_listener_position(self, position: Tuple[float, float, float],
                               orientation: Tuple[float, float, float] = (0.0, 0.0, 0.0)) -> bool:
        """
        Update primary listener (guest) position

        Args:
            position: 3D position of listener
            orientation: Orientation (pitch, yaw, roll) in radians

        Returns:
            True if position was updated
        """
        try:
            self.primary_listener = ListenerPosition(position, orientation)
            self._performance_metrics['listener_updates'] += 1

            # Determine audio zone based on distance from R2D2
            distance = euclidean(position, (0.0, 0.0, 0.0))

            if distance <= 0.6:  # 2 feet
                zone = AudioZone.INTIMATE
            elif distance <= 1.2:  # 4 feet
                zone = AudioZone.PERSONAL
            elif distance <= 2.4:  # 8 feet
                zone = AudioZone.SOCIAL
            else:
                zone = AudioZone.PUBLIC

            logger.debug(f"Listener position updated: {position}, zone: {zone.value}")
            return True

        except Exception as e:
            logger.error(f"Failed to update listener position: {e}")
            return False

    def calculate_speaker_outputs(self, audio_source: AudioSource) -> Dict[str, float]:
        """
        Calculate speaker output levels for 3D audio positioning

        Args:
            audio_source: Audio source to position

        Returns:
            Dictionary of speaker outputs
        """
        try:
            speaker_outputs = {}

            # Calculate distance and angle from each speaker to listener
            listener_pos = self.primary_listener.position

            for speaker_id, speaker in self.speakers.items():
                if not speaker.active:
                    speaker_outputs[speaker_id] = 0.0
                    continue

                # Vector from speaker to listener
                speaker_pos = speaker.position
                vector_to_listener = np.array(listener_pos) - np.array(speaker_pos)
                distance = np.linalg.norm(vector_to_listener)

                # Distance attenuation (inverse square law with minimum distance)
                min_distance = 0.1  # Prevent division by zero
                distance_factor = 1.0 / max(distance ** 2, min_distance)

                # Angle calculation for directional speakers
                if speaker.directional_pattern == "directional":
                    # Calculate angle between speaker direction and listener
                    speaker_direction = np.array([0.0, 0.0, 1.0])  # Forward direction
                    if np.linalg.norm(vector_to_listener) > 0:
                        angle = np.arccos(np.clip(
                            np.dot(speaker_direction, vector_to_listener / np.linalg.norm(vector_to_listener)),
                            -1.0, 1.0
                        ))
                        directional_factor = max(0.1, np.cos(angle))
                    else:
                        directional_factor = 1.0
                else:
                    directional_factor = 1.0

                # Audio zone adjustments
                zone_distance = euclidean(listener_pos, (0.0, 0.0, 0.0))
                if zone_distance <= 0.6:  # Intimate
                    zone_factor = 0.7  # Reduce volume for very close interaction
                elif zone_distance <= 1.2:  # Personal
                    zone_factor = 1.0
                elif zone_distance <= 2.4:  # Social
                    zone_factor = 1.1
                else:  # Public
                    zone_factor = 1.3

                # Crowd density adjustment
                crowd_factor = 1.0 + (self.crowd_density * 0.5)

                # Calculate final output level
                output_level = (audio_source.volume *
                              distance_factor *
                              directional_factor *
                              zone_factor *
                              crowd_factor *
                              speaker.max_volume)

                # Clamp to valid range
                speaker_outputs[speaker_id] = max(0.0, min(1.0, output_level))

            return speaker_outputs

        except Exception as e:
            logger.error(f"Failed to calculate speaker outputs: {e}")
            return {speaker_id: 0.0 for speaker_id in self.speakers.keys()}

    def apply_hrtf_processing(self, audio_source: AudioSource) -> Tuple[np.ndarray, np.ndarray]:
        """
        Apply HRTF processing for binaural audio

        Args:
            audio_source: Audio source to process

        Returns:
            Tuple of (left_channel, right_channel) audio
        """
        try:
            # Calculate angle from listener to source
            listener_pos = np.array(self.primary_listener.position)
            source_pos = np.array(audio_source.position)

            vector = source_pos - listener_pos
            if np.linalg.norm(vector) == 0:
                angle = 0
            else:
                # Calculate azimuth angle
                angle = np.degrees(np.arctan2(vector[0], vector[2])) % 360

            # Find nearest HRTF data points
            hrtf_angles = list(self._hrtf_data['left'].keys())
            nearest_angle = min(hrtf_angles, key=lambda x: abs(x - angle))

            # Get HRTF coefficients
            left_hrtf = self._hrtf_data['left'][nearest_angle]
            right_hrtf = self._hrtf_data['right'][nearest_angle]

            # Generate test audio (would be replaced with actual audio data)
            duration = 1.0
            t = np.linspace(0, duration, int(self.sample_rate * duration))
            test_audio = np.sin(2 * np.pi * audio_source.frequency * t) * audio_source.volume

            # Apply HRTF
            left_audio = test_audio * left_hrtf['gain']
            right_audio = test_audio * right_hrtf['gain']

            # Apply delays (simplified)
            if left_hrtf['delay'] > 0:
                delay_samples = int(left_hrtf['delay'] * self.sample_rate)
                left_audio = np.concatenate([np.zeros(delay_samples), left_audio[:-delay_samples]])

            if right_hrtf['delay'] > 0:
                delay_samples = int(right_hrtf['delay'] * self.sample_rate)
                right_audio = np.concatenate([np.zeros(delay_samples), right_audio[:-delay_samples]])

            return left_audio, right_audio

        except Exception as e:
            logger.error(f"HRTF processing error: {e}")
            return np.zeros(self.sample_rate), np.zeros(self.sample_rate)

    def set_environmental_effect(self, effect: EnvironmentalEffect) -> bool:
        """
        Set environmental audio effect

        Args:
            effect: Environmental effect to apply

        Returns:
            True if effect was set
        """
        self.current_environment = effect
        self._performance_metrics['environmental_changes'] += 1
        logger.info(f"Environmental effect set to: {effect.value}")
        return True

    def set_crowd_density(self, density: float) -> bool:
        """
        Set crowd density for audio adjustment

        Args:
            density: Crowd density (0.0 to 1.0)

        Returns:
            True if density was set
        """
        self.crowd_density = max(0.0, min(1.0, density))
        logger.info(f"Crowd density set to: {self.crowd_density:.2f}")
        return True

    def process_spatial_audio_frame(self, timestamp: float) -> SpatialAudioFrame:
        """
        Process single frame of spatial audio

        Args:
            timestamp: Frame timestamp

        Returns:
            Spatial audio frame with speaker outputs
        """
        try:
            start_time = time.time()

            # Determine current audio zone
            distance = euclidean(self.primary_listener.position, (0.0, 0.0, 0.0))
            if distance <= 0.6:
                zone = AudioZone.INTIMATE
            elif distance <= 1.2:
                zone = AudioZone.PERSONAL
            elif distance <= 2.4:
                zone = AudioZone.SOCIAL
            else:
                zone = AudioZone.PUBLIC

            # Calculate speaker outputs for all active sources
            combined_outputs = {speaker_id: 0.0 for speaker_id in self.speakers.keys()}

            for source in self.audio_sources.values():
                source_outputs = self.calculate_speaker_outputs(source)

                # Combine outputs (simple addition, would use proper mixing in real implementation)
                for speaker_id, level in source_outputs.items():
                    combined_outputs[speaker_id] = min(1.0, combined_outputs[speaker_id] + level)

            # Apply environmental effects (simplified)
            env_effect = self.environmental_effects[self.current_environment]
            for speaker_id in combined_outputs:
                # Apply reverb level reduction for environmental effects
                combined_outputs[speaker_id] *= (1.0 - env_effect['reverb_level'] * 0.2)

            # Create spatial audio frame
            frame = SpatialAudioFrame(
                timestamp=timestamp,
                listener_position=self.primary_listener,
                audio_sources=list(self.audio_sources.values()),
                speaker_outputs=combined_outputs,
                environmental_effect=self.current_environment,
                zone=zone
            )

            # Update performance metrics
            processing_time = (time.time() - start_time) * 1000
            self._performance_metrics['processing_latency_ms'] = processing_time
            self._performance_metrics['frames_processed'] += 1

            return frame

        except Exception as e:
            logger.error(f"Spatial audio frame processing error: {e}")
            return SpatialAudioFrame(
                timestamp=timestamp,
                listener_position=self.primary_listener,
                audio_sources=[],
                speaker_outputs={speaker_id: 0.0 for speaker_id in self.speakers.keys()},
                environmental_effect=self.current_environment,
                zone=AudioZone.PUBLIC
            )

    def start_realtime_processing(self):
        """Start real-time spatial audio processing"""
        self.audio_processing_active = True
        self._processing_thread = threading.Thread(target=self._spatial_processing_loop, daemon=True)
        self._processing_thread.start()
        logger.info("Real-time spatial audio processing started")

    def _spatial_processing_loop(self):
        """Real-time spatial audio processing loop"""
        while self.audio_processing_active:
            try:
                timestamp = time.time()

                # Process spatial audio frame
                frame = self.process_spatial_audio_frame(timestamp)

                # Apply speaker outputs (would send to actual audio hardware)
                for speaker_id, level in frame.speaker_outputs.items():
                    if level > 0.01:  # Only log significant outputs
                        logger.debug(f"Speaker {speaker_id}: {level:.3f}")

                # Update performance metrics
                self._performance_metrics['speaker_updates'] += len(frame.speaker_outputs)
                self._performance_metrics['last_update_time'] = timestamp

                # Sleep for next frame (50Hz update rate)
                time.sleep(0.02)

            except Exception as e:
                logger.error(f"Spatial processing loop error: {e}")
                time.sleep(0.1)

    def stop_realtime_processing(self):
        """Stop real-time spatial audio processing"""
        self.audio_processing_active = False
        if self._processing_thread and self._processing_thread.is_alive():
            self._processing_thread.join(timeout=2.0)
        logger.info("Real-time spatial audio processing stopped")

    def create_audio_spotlight(self, target_position: Tuple[float, float, float],
                             intensity: float = 1.0) -> bool:
        """
        Create focused audio "spotlight" effect toward specific position

        Args:
            target_position: Target position for audio focus
            intensity: Spotlight intensity (0.0 to 2.0)

        Returns:
            True if spotlight was created
        """
        try:
            # Calculate directional speaker adjustments
            target_vector = np.array(target_position)
            r2d2_center = np.array([0.0, 0.0, 0.0])

            direction = target_vector - r2d2_center
            if np.linalg.norm(direction) > 0:
                direction = direction / np.linalg.norm(direction)

            # Adjust speaker volumes based on direction
            for speaker_id, speaker in self.speakers.items():
                speaker_pos = np.array(speaker.position)
                speaker_direction = speaker_pos / np.linalg.norm(speaker_pos) if np.linalg.norm(speaker_pos) > 0 else np.array([0, 1, 0])

                # Calculate alignment with target direction
                alignment = np.dot(speaker_direction, direction)
                spotlight_factor = max(0.1, (alignment + 1) / 2) * intensity

                # Store spotlight factor for speaker (would be applied during playback)
                speaker.max_volume = min(1.0, spotlight_factor)

            logger.info(f"Audio spotlight created toward position {target_position} with intensity {intensity}")
            return True

        except Exception as e:
            logger.error(f"Failed to create audio spotlight: {e}")
            return False

    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get spatial audio performance metrics"""
        return {
            **self._performance_metrics,
            'system_status': {
                'active_speakers': sum(1 for s in self.speakers.values() if s.active),
                'total_speakers': len(self.speakers),
                'active_sources': len(self.audio_sources),
                'current_environment': self.current_environment.value,
                'crowd_density': self.crowd_density,
                'processing_active': self.audio_processing_active
            },
            'listener_info': {
                'position': self.primary_listener.position,
                'orientation': self.primary_listener.orientation,
                'secondary_listeners': len(self.secondary_listeners)
            }
        }

    def save_spatial_profile(self, filename: str):
        """Save spatial audio configuration and performance profile"""
        try:
            profile_data = {
                'timestamp': time.time(),
                'speaker_configuration': {speaker_id: {
                    'location': speaker.location.value,
                    'position': speaker.position,
                    'max_volume': speaker.max_volume,
                    'frequency_response': speaker.frequency_response,
                    'directional_pattern': speaker.directional_pattern,
                    'active': speaker.active
                } for speaker_id, speaker in self.speakers.items()},
                'environmental_effects': {effect.value: params for effect, params in self.environmental_effects.items()},
                'current_state': {
                    'environment': self.current_environment.value,
                    'crowd_density': self.crowd_density,
                    'ambient_noise_level': self.ambient_noise_level,
                    'listener_position': self.primary_listener.position,
                    'active_sources': len(self.audio_sources)
                },
                'performance_metrics': self.get_performance_metrics()
            }

            with open(filename, 'w') as f:
                json.dump(profile_data, f, indent=2)

            logger.info(f"Spatial audio profile saved to {filename}")

        except Exception as e:
            logger.error(f"Failed to save spatial audio profile: {e}")


if __name__ == "__main__":
    # Example usage and testing
    print("Disney Spatial Audio System - R2D2 Demo")
    print("=" * 50)

    # Create spatial audio system
    spatial_audio = SpatialAudioSystem()

    try:
        # Test listener position updates
        positions = [
            (1.0, 0.0, 1.5),  # Front right
            (-1.0, 0.0, 1.5), # Front left
            (0.0, 0.0, 2.5),  # Front center, far
            (0.0, 0.0, 0.8),  # Front center, close
        ]

        for pos in positions:
            spatial_audio.update_listener_position(pos)

            # Add test audio source
            spatial_audio.add_audio_source("test_voice", (0.0, 0.6, 0.25), volume=0.8)

            # Process spatial audio frame
            frame = spatial_audio.process_spatial_audio_frame(time.time())

            print(f"\nListener at {pos}:")
            print(f"  Audio zone: {frame.zone.value}")
            print(f"  Top speaker outputs:")
            sorted_outputs = sorted(frame.speaker_outputs.items(), key=lambda x: x[1], reverse=True)
            for speaker_id, level in sorted_outputs[:3]:
                if level > 0.01:
                    print(f"    {speaker_id}: {level:.3f}")

        # Test environmental effects
        print(f"\nTesting environmental effects:")
        environments = [
            EnvironmentalEffect.REVERB_SMALL,
            EnvironmentalEffect.REVERB_LARGE,
            EnvironmentalEffect.ECHO,
            EnvironmentalEffect.OUTDOORS
        ]

        for env in environments:
            spatial_audio.set_environmental_effect(env)
            print(f"  Environment: {env.value}")

        # Test crowd density effects
        print(f"\nTesting crowd density effects:")
        densities = [0.1, 0.5, 0.9]
        for density in densities:
            spatial_audio.set_crowd_density(density)
            spatial_audio.update_listener_position((0.0, 0.0, 1.5))
            frame = spatial_audio.process_spatial_audio_frame(time.time())
            avg_output = sum(frame.speaker_outputs.values()) / len(frame.speaker_outputs)
            print(f"  Density {density}: Average output {avg_output:.3f}")

        # Test audio spotlight
        print(f"\nTesting audio spotlight:")
        target_positions = [
            (2.0, 0.0, 2.0),   # Front right
            (-2.0, 0.0, 2.0),  # Front left
            (0.0, 0.0, -2.0)   # Behind
        ]

        for target in target_positions:
            spatial_audio.create_audio_spotlight(target, intensity=1.5)
            print(f"  Spotlight toward {target}")

        # Test HRTF processing
        print(f"\nTesting HRTF processing:")
        test_source = spatial_audio.audio_sources["test_voice"]
        left_audio, right_audio = spatial_audio.apply_hrtf_processing(test_source)
        print(f"  Generated binaural audio: L={len(left_audio)} samples, R={len(right_audio)} samples")

        # Display performance metrics
        metrics = spatial_audio.get_performance_metrics()
        print(f"\nSpatial Audio Performance:")
        print(f"Frames processed: {metrics['frames_processed']}")
        print(f"Processing latency: {metrics['processing_latency_ms']:.1f}ms")
        print(f"Active speakers: {metrics['system_status']['active_speakers']}")
        print(f"Active sources: {metrics['system_status']['active_sources']}")
        print(f"Current environment: {metrics['system_status']['current_environment']}")

        # Save performance profile
        spatial_audio.save_spatial_profile(
            "/home/rolo/r2ai/.claude/agent_storage/imagineer-specialist/spatial_audio_profile.json"
        )

    except Exception as e:
        print(f"Error during demo: {e}")
    finally:
        spatial_audio.stop_realtime_processing()
        print("Spatial audio demo completed")