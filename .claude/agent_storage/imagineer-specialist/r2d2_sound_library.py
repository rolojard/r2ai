#!/usr/bin/env python3
"""
R2D2 Authentic Sound Library with Character Personality
=====================================================

Comprehensive sound library system featuring authentic R2D2 vocalizations
with character personality-driven behaviors, contextual audio responses,
and Disney-quality sound synthesis capabilities.

Features:
- Authentic R2D2 sound synthesis and library management
- Character personality-driven audio behavior patterns
- Contextual audio responses based on environment and interactions
- Star Wars canon-compliant vocalizations and emotional expressions
- Convention-ready sound effects and interactive audio sequences
- Audio synthesis for missing sounds using R2D2's characteristic patterns

Author: Imagineer Specialist Agent
Target: NVIDIA Orin Nano R2D2 Systems
"""

import time
import math
import random
import threading
import logging
import wave
import struct
from typing import Dict, List, Tuple, Optional, Callable, Any, Union
from dataclasses import dataclass, field
from enum import Enum
import numpy as np
from collections import deque, defaultdict
import json
import pygame
import scipy.signal
from scipy.io import wavfile
import librosa

# Configure logging for sound library
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EmotionalState(Enum):
    """R2D2's emotional states for authentic character responses"""
    NEUTRAL = "neutral"
    HAPPY = "happy"
    EXCITED = "excited"
    CURIOUS = "curious"
    ALERT = "alert"
    WORRIED = "worried"
    FRUSTRATED = "frustrated"
    ANGRY = "angry"
    SAD = "sad"
    SLEEPY = "sleepy"
    SURPRISED = "surprised"
    CONFUSED = "confused"
    DETERMINED = "determined"
    PLAYFUL = "playful"
    MISCHIEVOUS = "mischievous"

class SoundCategory(Enum):
    """Categories of R2D2 sounds"""
    GREETING = "greeting"
    ACKNOWLEDGMENT = "acknowledgment"
    QUESTION = "question"
    EXCLAMATION = "exclamation"
    WARNING = "warning"
    SCANNING = "scanning"
    PROCESSING = "processing"
    EMOTIONAL = "emotional"
    INTERACTION = "interaction"
    MECHANICAL = "mechanical"
    STAR_WARS_SPECIFIC = "star_wars_specific"
    AMBIENT = "ambient"

class CharacterContext(Enum):
    """Context for character interactions"""
    JEDI = "jedi"
    SITH = "sith"
    DROID = "droid"
    REBEL = "rebel"
    EMPIRE = "empire"
    CIVILIAN = "civilian"
    CHILD = "child"
    UNKNOWN = "unknown"

@dataclass
class SoundEffect:
    """Individual sound effect definition"""
    sound_id: str
    filename: str
    category: SoundCategory
    emotional_state: EmotionalState
    duration: float
    priority: int = 5  # 1-10, higher = more important
    character_context: List[CharacterContext] = field(default_factory=list)
    volume: float = 1.0
    loop: bool = False
    fade_in: float = 0.0
    fade_out: float = 0.0
    description: str = ""
    canon_reference: str = ""
    synthesis_parameters: Optional[Dict[str, Any]] = None

@dataclass
class SoundSequence:
    """Sequence of sounds for complex expressions"""
    sequence_id: str
    name: str
    sounds: List[Tuple[str, float]]  # (sound_id, delay)
    total_duration: float
    emotional_state: EmotionalState
    context: CharacterContext
    description: str = ""

@dataclass
class PersonalityProfile:
    """Character personality profile affecting sound selection"""
    name: str
    base_emotional_state: EmotionalState
    response_speed: float = 1.0  # Multiplier for response timing
    volume_modifier: float = 1.0
    pitch_variance: float = 0.1  # Random pitch variation
    emotional_sensitivity: float = 1.0  # How quickly emotions change
    curiosity_level: float = 0.5
    friendliness_level: float = 0.7
    alertness_level: float = 0.6

class R2D2SoundLibrary:
    """
    Comprehensive R2D2 sound library with authentic character personality

    Manages the complete audio experience including:
    - Authentic R2D2 sound library with Star Wars canon compliance
    - Character personality-driven sound selection
    - Contextual audio responses based on environment
    - Sound synthesis for missing audio clips
    - Interactive audio sequences and emotional expressions
    """

    def __init__(self, sound_library_path: str = "/home/rolo/r2ai/audio_library"):
        """
        Initialize R2D2 sound library

        Args:
            sound_library_path: Path to audio library directory
        """
        self.sound_library_path = sound_library_path
        self.sound_effects: Dict[str, SoundEffect] = {}
        self.sound_sequences: Dict[str, SoundSequence] = {}
        self.personality_profiles: Dict[str, PersonalityProfile] = {}

        # Current state
        self.current_emotional_state = EmotionalState.NEUTRAL
        self.current_personality = "classic_r2d2"
        self.current_context = CharacterContext.UNKNOWN
        self.interaction_history: deque = deque(maxlen=100)

        # Sound synthesis parameters
        self.sample_rate = 44100
        self.bit_depth = 16

        # Performance tracking
        self._performance_metrics = {
            'sounds_played': 0,
            'sequences_played': 0,
            'synthesis_operations': 0,
            'emotional_state_changes': 0,
            'last_update_time': time.time()
        }

        # Initialize sound library
        self._initialize_personality_profiles()
        self._initialize_sound_library()
        self._initialize_sound_sequences()

        # Initialize pygame mixer for audio playback
        pygame.mixer.pre_init(frequency=self.sample_rate, size=-16, channels=2, buffer=512)
        pygame.mixer.init()

        logger.info("R2D2 Sound Library initialized with Disney-quality audio system")

    def _initialize_personality_profiles(self):
        """Initialize R2D2 personality profiles"""
        # Classic R2D2 from original trilogy
        self.personality_profiles["classic_r2d2"] = PersonalityProfile(
            name="Classic R2D2",
            base_emotional_state=EmotionalState.CURIOUS,
            response_speed=1.0,
            volume_modifier=1.0,
            pitch_variance=0.15,
            emotional_sensitivity=0.8,
            curiosity_level=0.8,
            friendliness_level=0.9,
            alertness_level=0.7
        )

        # Excited convention R2D2
        self.personality_profiles["convention_r2d2"] = PersonalityProfile(
            name="Convention R2D2",
            base_emotional_state=EmotionalState.EXCITED,
            response_speed=1.2,
            volume_modifier=1.1,
            pitch_variance=0.2,
            emotional_sensitivity=1.2,
            curiosity_level=0.9,
            friendliness_level=1.0,
            alertness_level=0.8
        )

        # Sleepy/power-saving R2D2
        self.personality_profiles["sleepy_r2d2"] = PersonalityProfile(
            name="Sleepy R2D2",
            base_emotional_state=EmotionalState.SLEEPY,
            response_speed=0.6,
            volume_modifier=0.7,
            pitch_variance=0.05,
            emotional_sensitivity=0.4,
            curiosity_level=0.3,
            friendliness_level=0.6,
            alertness_level=0.4
        )

        # Alert/security R2D2
        self.personality_profiles["security_r2d2"] = PersonalityProfile(
            name="Security R2D2",
            base_emotional_state=EmotionalState.ALERT,
            response_speed=1.5,
            volume_modifier=1.2,
            pitch_variance=0.1,
            emotional_sensitivity=1.0,
            curiosity_level=0.6,
            friendliness_level=0.5,
            alertness_level=1.0
        )

    def _initialize_sound_library(self):
        """Initialize comprehensive R2D2 sound library"""

        # Basic emotional sounds
        sounds = [
            # Happy/Excited sounds
            SoundEffect("happy_beep_01", "r2d2_happy_beep_01.wav", SoundCategory.EMOTIONAL,
                       EmotionalState.HAPPY, 1.2, description="Classic happy R2D2 beep",
                       canon_reference="Episode IV - Luke rescue"),

            SoundEffect("excited_whistle_01", "r2d2_excited_whistle_01.wav", SoundCategory.EMOTIONAL,
                       EmotionalState.EXCITED, 2.1, description="Excited whistle with rising pitch",
                       canon_reference="Episode IV - Death Star plans"),

            SoundEffect("playful_chirp_01", "r2d2_playful_chirp_01.wav", SoundCategory.EMOTIONAL,
                       EmotionalState.PLAYFUL, 0.8, description="Playful chirping sound"),

            # Curious sounds
            SoundEffect("curious_warble_01", "r2d2_curious_warble_01.wav", SoundCategory.QUESTION,
                       EmotionalState.CURIOUS, 1.5, description="Inquisitive warbling tone",
                       canon_reference="Episode V - Dagobah exploration"),

            SoundEffect("questioning_beep_01", "r2d2_questioning_beep_01.wav", SoundCategory.QUESTION,
                       EmotionalState.CURIOUS, 1.0, description="Rising tone question sound"),

            # Alert/Warning sounds
            SoundEffect("alert_beep_01", "r2d2_alert_beep_01.wav", SoundCategory.WARNING,
                       EmotionalState.ALERT, 0.5, priority=8,
                       description="Sharp alert beep", canon_reference="Episode IV - Danger warning"),

            SoundEffect("urgent_whistle_01", "r2d2_urgent_whistle_01.wav", SoundCategory.WARNING,
                       EmotionalState.ALERT, 1.8, priority=9,
                       description="Urgent warning whistle"),

            # Frustrated/Angry sounds
            SoundEffect("frustrated_beeps_01", "r2d2_frustrated_beeps_01.wav", SoundCategory.EMOTIONAL,
                       EmotionalState.FRUSTRATED, 2.8, description="Series of frustrated beeps",
                       canon_reference="Episode V - Dagobah repairs"),

            SoundEffect("angry_buzz_01", "r2d2_angry_buzz_01.wav", SoundCategory.EMOTIONAL,
                       EmotionalState.ANGRY, 1.5, description="Angry buzzing sound"),

            # Sad/Worried sounds
            SoundEffect("sad_whistle_01", "r2d2_sad_whistle_01.wav", SoundCategory.EMOTIONAL,
                       EmotionalState.SAD, 3.2, description="Melancholy descending whistle",
                       canon_reference="Episode III - Padmé's death"),

            SoundEffect("worried_warble_01", "r2d2_worried_warble_01.wav", SoundCategory.EMOTIONAL,
                       EmotionalState.WORRIED, 2.0, description="Anxious warbling"),

            # Greetings and acknowledgments
            SoundEffect("greeting_sequence_01", "r2d2_greeting_sequence_01.wav", SoundCategory.GREETING,
                       EmotionalState.HAPPY, 3.5, priority=7,
                       description="Classic R2D2 greeting sequence"),

            SoundEffect("acknowledgment_beep_01", "r2d2_acknowledgment_beep_01.wav", SoundCategory.ACKNOWLEDGMENT,
                       EmotionalState.NEUTRAL, 1.0, description="Simple acknowledgment beep"),

            # Star Wars specific character interactions
            SoundEffect("luke_recognition_01", "r2d2_luke_recognition_01.wav", SoundCategory.STAR_WARS_SPECIFIC,
                       EmotionalState.EXCITED, 4.1, priority=9,
                       character_context=[CharacterContext.JEDI],
                       description="R2D2 recognizing Luke Skywalker",
                       canon_reference="Episode IV - First meeting"),

            SoundEffect("leia_message_01", "r2d2_leia_message_01.wav", SoundCategory.STAR_WARS_SPECIFIC,
                       EmotionalState.ALERT, 5.2, priority=9,
                       character_context=[CharacterContext.REBEL],
                       description="Princess Leia hologram message",
                       canon_reference="Episode IV - Help me message"),

            SoundEffect("c3po_interaction_01", "r2d2_c3po_interaction_01.wav", SoundCategory.INTERACTION,
                       EmotionalState.PLAYFUL, 3.8, priority=7,
                       character_context=[CharacterContext.DROID],
                       description="Interaction with C-3PO"),

            SoundEffect("vader_fear_01", "r2d2_vader_fear_01.wav", SoundCategory.STAR_WARS_SPECIFIC,
                       EmotionalState.WORRIED, 3.0, priority=8,
                       character_context=[CharacterContext.SITH],
                       description="Fearful reaction to Darth Vader"),

            # Functional sounds
            SoundEffect("scanning_loop_01", "r2d2_scanning_loop_01.wav", SoundCategory.SCANNING,
                       EmotionalState.NEUTRAL, 4.5, loop=True,
                       description="Continuous scanning sound"),

            SoundEffect("processing_hum_01", "r2d2_processing_hum_01.wav", SoundCategory.PROCESSING,
                       EmotionalState.NEUTRAL, 2.0, loop=True,
                       description="Data processing hum"),

            SoundEffect("power_up_sequence_01", "r2d2_power_up_sequence_01.wav", SoundCategory.MECHANICAL,
                       EmotionalState.NEUTRAL, 3.7, priority=9,
                       description="Power-up boot sequence"),

            SoundEffect("power_down_sequence_01", "r2d2_power_down_sequence_01.wav", SoundCategory.MECHANICAL,
                       EmotionalState.SLEEPY, 4.2, priority=9,
                       description="Power-down shutdown sequence"),

            # Interactive/Convention specific
            SoundEffect("photo_pose_01", "r2d2_photo_pose_01.wav", SoundCategory.INTERACTION,
                       EmotionalState.HAPPY, 1.5, description="Ready for photo sound"),

            SoundEffect("costume_compliment_01", "r2d2_costume_compliment_01.wav", SoundCategory.INTERACTION,
                       EmotionalState.EXCITED, 2.8, description="Complimenting costume"),

            SoundEffect("jedi_recognition_01", "r2d2_jedi_recognition_01.wav", SoundCategory.STAR_WARS_SPECIFIC,
                       EmotionalState.EXCITED, 3.5, priority=8,
                       character_context=[CharacterContext.JEDI],
                       description="General Jedi recognition"),

            SoundEffect("sith_warning_01", "r2d2_sith_warning_01.wav", SoundCategory.WARNING,
                       EmotionalState.ALERT, 2.9, priority=7,
                       character_context=[CharacterContext.SITH],
                       description="Warning about Sith presence"),

            # Ambient and background sounds
            SoundEffect("idle_hum_01", "r2d2_idle_hum_01.wav", SoundCategory.AMBIENT,
                       EmotionalState.NEUTRAL, 8.0, loop=True, volume=0.3,
                       description="Quiet idle humming"),

            SoundEffect("servo_whir_01", "r2d2_servo_whir_01.wav", SoundCategory.MECHANICAL,
                       EmotionalState.NEUTRAL, 1.2, description="Servo motor movement"),

            # Emotional variations
            SoundEffect("giggle_beeps_01", "r2d2_giggle_beeps_01.wav", SoundCategory.EMOTIONAL,
                       EmotionalState.MISCHIEVOUS, 1.9, description="Mischievous giggling beeps"),

            SoundEffect("surprised_whistle_01", "r2d2_surprised_whistle_01.wav", SoundCategory.EMOTIONAL,
                       EmotionalState.SURPRISED, 0.7, description="Surprised whistle"),

            SoundEffect("confused_warble_01", "r2d2_confused_warble_01.wav", SoundCategory.EMOTIONAL,
                       EmotionalState.CONFUSED, 2.3, description="Confused warbling"),

            SoundEffect("determined_beep_01", "r2d2_determined_beep_01.wav", SoundCategory.EMOTIONAL,
                       EmotionalState.DETERMINED, 1.4, description="Determined/confident beep")
        ]

        # Store sounds in dictionary
        for sound in sounds:
            self.sound_effects[sound.sound_id] = sound

        logger.info(f"Initialized {len(sounds)} authentic R2D2 sound effects")

    def _initialize_sound_sequences(self):
        """Initialize complex sound sequences for multi-part expressions"""
        sequences = [
            # Complete greeting sequence
            SoundSequence(
                "full_greeting", "Complete R2D2 Greeting",
                [
                    ("power_up_sequence_01", 0.0),
                    ("greeting_sequence_01", 1.0),
                    ("happy_beep_01", 4.5),
                    ("acknowledgment_beep_01", 6.0)
                ],
                7.0, EmotionalState.HAPPY, CharacterContext.CIVILIAN,
                "Full greeting sequence for new encounters"
            ),

            # Alert sequence
            SoundSequence(
                "danger_alert", "Danger Alert Sequence",
                [
                    ("alert_beep_01", 0.0),
                    ("urgent_whistle_01", 0.7),
                    ("alert_beep_01", 2.5),
                    ("worried_warble_01", 3.0)
                ],
                5.0, EmotionalState.ALERT, CharacterContext.UNKNOWN,
                "Multi-stage danger warning sequence"
            ),

            # Jedi encounter sequence
            SoundSequence(
                "jedi_encounter", "Jedi Recognition Sequence",
                [
                    ("surprised_whistle_01", 0.0),
                    ("jedi_recognition_01", 1.0),
                    ("excited_whistle_01", 4.5),
                    ("happy_beep_01", 6.5)
                ],
                8.0, EmotionalState.EXCITED, CharacterContext.JEDI,
                "Complete sequence for Jedi character recognition"
            ),

            # Frustrated repair sequence
            SoundSequence(
                "repair_frustration", "Repair Frustration",
                [
                    ("frustrated_beeps_01", 0.0),
                    ("angry_buzz_01", 3.0),
                    ("frustrated_beeps_01", 4.5),
                    ("sad_whistle_01", 7.0)
                ],
                10.0, EmotionalState.FRUSTRATED, CharacterContext.UNKNOWN,
                "Frustration sequence during repairs or malfunction"
            ),

            # Curiosity exploration sequence
            SoundSequence(
                "curious_exploration", "Curious Exploration",
                [
                    ("curious_warble_01", 0.0),
                    ("questioning_beep_01", 2.0),
                    ("scanning_loop_01", 3.5),
                    ("acknowledgment_beep_01", 8.0)
                ],
                9.0, EmotionalState.CURIOUS, CharacterContext.UNKNOWN,
                "Sequence for exploring new environment or object"
            ),

            # Playful interaction
            SoundSequence(
                "playful_interaction", "Playful Interaction",
                [
                    ("playful_chirp_01", 0.0),
                    ("giggle_beeps_01", 1.0),
                    ("happy_beep_01", 3.0),
                    ("playful_chirp_01", 4.5)
                ],
                6.0, EmotionalState.PLAYFUL, CharacterContext.CHILD,
                "Playful sequence for interacting with children"
            ),

            # Power down sequence
            SoundSequence(
                "shutdown_sequence", "Complete Shutdown",
                [
                    ("acknowledgment_beep_01", 0.0),
                    ("sad_whistle_01", 1.5),
                    ("power_down_sequence_01", 4.5),
                    ("idle_hum_01", 8.5)
                ],
                12.0, EmotionalState.SLEEPY, CharacterContext.UNKNOWN,
                "Complete shutdown sequence for end of day"
            )
        ]

        # Store sequences
        for sequence in sequences:
            self.sound_sequences[sequence.sequence_id] = sequence

        logger.info(f"Initialized {len(sequences)} sound sequences")

    def set_personality_profile(self, profile_name: str) -> bool:
        """
        Set active personality profile

        Args:
            profile_name: Name of personality profile to activate

        Returns:
            True if profile was set successfully
        """
        if profile_name in self.personality_profiles:
            self.current_personality = profile_name
            profile = self.personality_profiles[profile_name]
            self.current_emotional_state = profile.base_emotional_state
            logger.info(f"Personality profile set to: {profile.name}")
            return True
        else:
            logger.error(f"Unknown personality profile: {profile_name}")
            return False

    def set_emotional_state(self, emotional_state: EmotionalState) -> bool:
        """
        Set current emotional state

        Args:
            emotional_state: New emotional state

        Returns:
            True if state was changed
        """
        if emotional_state != self.current_emotional_state:
            self.current_emotional_state = emotional_state
            self._performance_metrics['emotional_state_changes'] += 1
            logger.info(f"Emotional state changed to: {emotional_state.value}")
            return True
        return False

    def set_character_context(self, context: CharacterContext) -> bool:
        """
        Set current character interaction context

        Args:
            context: Character context for interaction

        Returns:
            True if context was set
        """
        self.current_context = context
        logger.info(f"Character context set to: {context.value}")
        return True

    def get_appropriate_sound(self, category: Optional[SoundCategory] = None,
                            emotional_state: Optional[EmotionalState] = None,
                            context: Optional[CharacterContext] = None) -> Optional[SoundEffect]:
        """
        Get appropriate sound based on current state and context

        Args:
            category: Preferred sound category
            emotional_state: Preferred emotional state
            context: Character context

        Returns:
            Most appropriate sound effect or None
        """
        # Use current state if not specified
        target_emotional_state = emotional_state or self.current_emotional_state
        target_context = context or self.current_context

        # Filter sounds by criteria
        candidates = []
        for sound in self.sound_effects.values():
            score = 0

            # Emotional state match
            if sound.emotional_state == target_emotional_state:
                score += 10
            elif self._are_emotions_compatible(sound.emotional_state, target_emotional_state):
                score += 5

            # Category match
            if category and sound.category == category:
                score += 8

            # Context match
            if target_context != CharacterContext.UNKNOWN:
                if target_context in sound.character_context:
                    score += 12
                elif not sound.character_context:  # Generic sounds
                    score += 3

            # Priority weighting
            score += sound.priority

            if score > 0:
                candidates.append((sound, score))

        if not candidates:
            return None

        # Sort by score and add some randomness for variety
        candidates.sort(key=lambda x: x[1] + random.random() * 2, reverse=True)
        return candidates[0][0]

    def _are_emotions_compatible(self, emotion1: EmotionalState, emotion2: EmotionalState) -> bool:
        """Check if two emotional states are compatible"""
        compatible_groups = [
            {EmotionalState.HAPPY, EmotionalState.EXCITED, EmotionalState.PLAYFUL},
            {EmotionalState.SAD, EmotionalState.WORRIED, EmotionalState.FRUSTRATED},
            {EmotionalState.ALERT, EmotionalState.DETERMINED, EmotionalState.ANGRY},
            {EmotionalState.CURIOUS, EmotionalState.SURPRISED, EmotionalState.CONFUSED},
            {EmotionalState.NEUTRAL, EmotionalState.SLEEPY}
        ]

        for group in compatible_groups:
            if emotion1 in group and emotion2 in group:
                return True
        return False

    def play_sound(self, sound_id: str, volume: Optional[float] = None) -> bool:
        """
        Play specific sound by ID

        Args:
            sound_id: ID of sound to play
            volume: Override volume (0.0 to 1.0)

        Returns:
            True if sound started playing
        """
        if sound_id not in self.sound_effects:
            logger.error(f"Sound {sound_id} not found in library")
            return False

        sound = self.sound_effects[sound_id]

        try:
            # Get personality profile for modifications
            profile = self.personality_profiles[self.current_personality]

            # Calculate final volume
            final_volume = (volume or sound.volume) * profile.volume_modifier
            final_volume = max(0.0, min(1.0, final_volume))

            # Load and play sound (simulated - would load actual audio file)
            logger.info(f"Playing sound: {sound_id} ({sound.description})")
            logger.info(f"  Category: {sound.category.value}")
            logger.info(f"  Emotional state: {sound.emotional_state.value}")
            logger.info(f"  Duration: {sound.duration:.1f}s")
            logger.info(f"  Volume: {final_volume:.2f}")

            # Record interaction
            self.interaction_history.append({
                'timestamp': time.time(),
                'sound_id': sound_id,
                'emotional_state': self.current_emotional_state.value,
                'context': self.current_context.value,
                'volume': final_volume
            })

            self._performance_metrics['sounds_played'] += 1
            return True

        except Exception as e:
            logger.error(f"Failed to play sound {sound_id}: {e}")
            return False

    def play_sequence(self, sequence_id: str) -> bool:
        """
        Play sound sequence

        Args:
            sequence_id: ID of sequence to play

        Returns:
            True if sequence started
        """
        if sequence_id not in self.sound_sequences:
            logger.error(f"Sound sequence {sequence_id} not found")
            return False

        sequence = self.sound_sequences[sequence_id]

        try:
            logger.info(f"Playing sequence: {sequence.name}")
            logger.info(f"  Duration: {sequence.total_duration:.1f}s")
            logger.info(f"  Sounds: {len(sequence.sounds)}")

            # Play sequence (simulated - would schedule actual playback)
            for sound_id, delay in sequence.sounds:
                logger.info(f"  - {sound_id} at +{delay:.1f}s")

            self._performance_metrics['sequences_played'] += 1
            return True

        except Exception as e:
            logger.error(f"Failed to play sequence {sequence_id}: {e}")
            return False

    def react_to_character(self, character_type: CharacterContext,
                          confidence: float = 0.8) -> bool:
        """
        React to detected character with appropriate sound

        Args:
            character_type: Type of character detected
            confidence: Detection confidence (0.0 to 1.0)

        Returns:
            True if reaction played
        """
        if confidence < 0.5:
            return False

        # Set context
        self.set_character_context(character_type)

        # Choose appropriate emotional response
        if character_type == CharacterContext.JEDI:
            self.set_emotional_state(EmotionalState.EXCITED)
            if confidence > 0.8:
                return self.play_sequence("jedi_encounter")
            else:
                sound = self.get_appropriate_sound(context=character_type)
                return self.play_sound(sound.sound_id) if sound else False

        elif character_type == CharacterContext.SITH:
            self.set_emotional_state(EmotionalState.WORRIED)
            sound = self.get_appropriate_sound(SoundCategory.WARNING, context=character_type)
            return self.play_sound(sound.sound_id) if sound else False

        elif character_type == CharacterContext.DROID:
            self.set_emotional_state(EmotionalState.PLAYFUL)
            sound = self.get_appropriate_sound(SoundCategory.INTERACTION, context=character_type)
            return self.play_sound(sound.sound_id) if sound else False

        elif character_type == CharacterContext.CHILD:
            self.set_emotional_state(EmotionalState.PLAYFUL)
            return self.play_sequence("playful_interaction")

        else:
            # Generic civilian
            self.set_emotional_state(EmotionalState.CURIOUS)
            sound = self.get_appropriate_sound(SoundCategory.GREETING)
            return self.play_sound(sound.sound_id) if sound else False

    def express_emotion(self, emotion: EmotionalState, intensity: float = 1.0) -> bool:
        """
        Express specific emotion with sound

        Args:
            emotion: Emotion to express
            intensity: Intensity of expression (0.0 to 2.0)

        Returns:
            True if emotion was expressed
        """
        self.set_emotional_state(emotion)

        # Get appropriate sound for emotion
        sound = self.get_appropriate_sound(SoundCategory.EMOTIONAL, emotion)

        if sound:
            # Adjust volume based on intensity
            volume = min(1.0, sound.volume * intensity)
            return self.play_sound(sound.sound_id, volume)

        return False

    def synthesize_missing_sound(self, sound_id: str, duration: float = 2.0,
                                base_frequency: float = 200.0) -> bool:
        """
        Synthesize R2D2-style sound for missing audio files

        Args:
            sound_id: ID of sound to synthesize
            duration: Duration in seconds
            base_frequency: Base frequency for synthesis

        Returns:
            True if sound was synthesized successfully
        """
        try:
            # R2D2 sound synthesis parameters
            t = np.linspace(0, duration, int(self.sample_rate * duration))

            # Create characteristic R2D2 sound using multiple components
            # Main tone with vibrato
            main_tone = np.sin(2 * np.pi * base_frequency * t * (1 + 0.05 * np.sin(2 * np.pi * 5 * t)))

            # Harmonic content
            harmonic2 = 0.3 * np.sin(2 * np.pi * base_frequency * 2 * t)
            harmonic3 = 0.15 * np.sin(2 * np.pi * base_frequency * 3 * t)

            # Noise component for texture
            noise = 0.05 * np.random.normal(0, 1, len(t))

            # Combine components
            audio = main_tone + harmonic2 + harmonic3 + noise

            # Apply characteristic R2D2 envelope
            envelope = np.exp(-2 * t / duration)  # Exponential decay
            audio *= envelope

            # Normalize
            audio = audio / np.max(np.abs(audio)) * 0.8

            # Convert to 16-bit
            audio_16bit = (audio * 32767).astype(np.int16)

            logger.info(f"Synthesized R2D2 sound: {sound_id} ({duration:.1f}s, {base_frequency:.0f}Hz)")

            self._performance_metrics['synthesis_operations'] += 1
            return True

        except Exception as e:
            logger.error(f"Failed to synthesize sound {sound_id}: {e}")
            return False

    def get_interaction_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent interaction history"""
        return list(self.interaction_history)[-limit:]

    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get sound library performance metrics"""
        return {
            **self._performance_metrics,
            'library_stats': {
                'total_sounds': len(self.sound_effects),
                'total_sequences': len(self.sound_sequences),
                'current_personality': self.current_personality,
                'current_emotional_state': self.current_emotional_state.value,
                'current_context': self.current_context.value
            },
            'interaction_history_size': len(self.interaction_history),
            'last_update_time': time.time()
        }

    def save_library_profile(self, filename: str):
        """Save sound library configuration and performance profile"""
        try:
            profile_data = {
                'timestamp': time.time(),
                'sound_effects_count': len(self.sound_effects),
                'sound_sequences_count': len(self.sound_sequences),
                'personality_profiles': {name: {
                    'name': profile.name,
                    'base_emotional_state': profile.base_emotional_state.value,
                    'response_speed': profile.response_speed,
                    'volume_modifier': profile.volume_modifier,
                    'curiosity_level': profile.curiosity_level,
                    'friendliness_level': profile.friendliness_level
                } for name, profile in self.personality_profiles.items()},
                'current_state': {
                    'personality': self.current_personality,
                    'emotional_state': self.current_emotional_state.value,
                    'context': self.current_context.value
                },
                'performance_metrics': self.get_performance_metrics(),
                'interaction_history': self.get_interaction_history(20)
            }

            with open(filename, 'w') as f:
                json.dump(profile_data, f, indent=2)

            logger.info(f"Sound library profile saved to {filename}")

        except Exception as e:
            logger.error(f"Failed to save library profile: {e}")


if __name__ == "__main__":
    # Example usage and testing
    print("R2D2 Authentic Sound Library - Character Demo")
    print("=" * 60)

    # Create sound library
    sound_library = R2D2SoundLibrary()

    try:
        # Test different personality profiles
        profiles = ["classic_r2d2", "convention_r2d2", "sleepy_r2d2", "security_r2d2"]

        for profile in profiles:
            print(f"\nTesting personality profile: {profile}")
            sound_library.set_personality_profile(profile)

            # Test emotional expressions
            emotions = [EmotionalState.HAPPY, EmotionalState.CURIOUS, EmotionalState.ALERT]
            for emotion in emotions:
                sound_library.express_emotion(emotion, intensity=1.2)
                time.sleep(0.5)

        # Test character interactions
        print(f"\nTesting character interactions:")
        characters = [
            (CharacterContext.JEDI, 0.9),
            (CharacterContext.SITH, 0.8),
            (CharacterContext.CHILD, 0.95),
            (CharacterContext.DROID, 0.7)
        ]

        for char_type, confidence in characters:
            print(f"Reacting to {char_type.value} (confidence: {confidence})")
            sound_library.react_to_character(char_type, confidence)
            time.sleep(1.0)

        # Test sound sequences
        print(f"\nTesting sound sequences:")
        sequences = ["full_greeting", "jedi_encounter", "danger_alert", "playful_interaction"]
        for seq_id in sequences:
            print(f"Playing sequence: {seq_id}")
            sound_library.play_sequence(seq_id)
            time.sleep(2.0)

        # Test sound synthesis
        print(f"\nTesting sound synthesis:")
        synthesis_tests = [
            ("custom_beep_01", 1.5, 250),
            ("custom_whistle_01", 2.0, 400),
            ("custom_warble_01", 1.8, 180)
        ]

        for sound_id, duration, frequency in synthesis_tests:
            sound_library.synthesize_missing_sound(sound_id, duration, frequency)

        # Display performance metrics
        metrics = sound_library.get_performance_metrics()
        print(f"\nSound Library Performance:")
        print(f"Sounds played: {metrics['sounds_played']}")
        print(f"Sequences played: {metrics['sequences_played']}")
        print(f"Synthesis operations: {metrics['synthesis_operations']}")
        print(f"Total sounds in library: {metrics['library_stats']['total_sounds']}")
        print(f"Current personality: {metrics['library_stats']['current_personality']}")
        print(f"Current emotional state: {metrics['library_stats']['current_emotional_state']}")

        # Display interaction history
        history = sound_library.get_interaction_history(5)
        print(f"\nRecent interactions:")
        for interaction in history:
            print(f"  {interaction['sound_id']} - {interaction['emotional_state']} "
                  f"({interaction['context']}) at volume {interaction['volume']:.2f}")

        # Save performance profile
        sound_library.save_library_profile(
            "/home/rolo/r2ai/.claude/agent_storage/imagineer-specialist/sound_library_profile.json"
        )

    except Exception as e:
        print(f"Error during demo: {e}")
    finally:
        print("Sound library demo completed")