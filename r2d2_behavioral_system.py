#!/usr/bin/env python3
"""
R2D2 Advanced Behavioral System
Disney-Level Animatronic Character Implementation

This system manages R2D2's emotional states, character interactions,
and autonomous behaviors for immersive Star Wars experiences.
"""

import time
import random
import json
from enum import Enum
from dataclasses import dataclass
from typing import Dict, List, Optional, Callable
import threading
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EmotionalState(Enum):
    """R2D2's emotional states affecting all behaviors"""
    HAPPY = "happy"
    CURIOUS = "curious"
    CAUTIOUS = "cautious"
    EXCITED = "excited"
    WORRIED = "worried"
    SLEEPY = "sleepy"
    PLAYFUL = "playful"
    CONFIDENT = "confident"

class CharacterType(Enum):
    """Star Wars character types for specific interactions"""
    LUKE_SKYWALKER = "luke"
    PRINCESS_LEIA = "leia"
    DARTH_VADER = "vader"
    HAN_SOLO = "han"
    C3PO = "c3po"
    OBI_WAN = "obiwan"
    YODA = "yoda"
    STORMTROOPER = "stormtrooper"
    JEDI = "jedi"
    SITH = "sith"
    REBEL = "rebel"
    IMPERIAL = "imperial"
    UNKNOWN = "unknown"

class BehaviorType(Enum):
    """Types of behaviors R2D2 can perform"""
    GREETING = "greeting"
    ATTENTION = "attention"
    CURIOSITY = "curiosity"
    EXCITEMENT = "excitement"
    WARNING = "warning"
    PLAYFUL = "playful"
    STORYTELLING = "storytelling"
    SCANNING = "scanning"
    IDLE = "idle"
    EMERGENCY = "emergency"

@dataclass
class BehaviorSequence:
    """Defines a complete behavior sequence"""
    name: str
    behavior_type: BehaviorType
    emotional_state: EmotionalState
    duration: float
    servo_movements: List[Dict]
    audio_sequence: List[Dict]
    light_sequence: List[Dict]
    prerequisites: List[str] = None
    character_specific: Optional[CharacterType] = None
    priority: int = 1
    repeatable: bool = True

@dataclass
class InteractionContext:
    """Context for current interaction"""
    detected_characters: List[CharacterType]
    crowd_size: int
    noise_level: float
    time_since_last_interaction: float
    current_emotional_state: EmotionalState
    interaction_history: List[str]

class R2D2BehavioralSystem:
    """Main behavioral system managing R2D2's personality and interactions"""

    def __init__(self):
        self.current_emotional_state = EmotionalState.CURIOUS
        self.behavior_library = {}
        self.interaction_memory = {}
        self.current_behavior = None
        self.behavior_queue = []
        self.autonomous_mode = True
        self.safety_override = False

        # Initialize behavior library
        self._initialize_behavior_library()

        # Start autonomous behavior thread
        self.behavior_thread = threading.Thread(target=self._autonomous_behavior_loop, daemon=True)
        self.behavior_thread.start()

        logger.info("R2D2 Behavioral System initialized")

    def _initialize_behavior_library(self):
        """Initialize the comprehensive behavior library"""

        # GREETING BEHAVIORS
        self.behavior_library["luke_greeting"] = BehaviorSequence(
            name="Luke Skywalker Greeting",
            behavior_type=BehaviorType.GREETING,
            emotional_state=EmotionalState.EXCITED,
            duration=8.0,
            servo_movements=[
                {"action": "dome_rapid_spin", "duration": 2.0, "direction": "clockwise"},
                {"action": "dome_tilt_up", "angle": 15, "speed": "fast"},
                {"action": "front_panels_flutter", "duration": 1.5},
                {"action": "dome_shake_yes", "repetitions": 3}
            ],
            audio_sequence=[
                {"sound": "excited_whistle_ascending", "delay": 0.0},
                {"sound": "happy_beep_sequence", "delay": 2.0},
                {"sound": "affectionate_warble", "delay": 4.0}
            ],
            light_sequence=[
                {"action": "front_lights_pulse_blue", "duration": 8.0},
                {"action": "dome_lights_sparkle", "duration": 3.0, "delay": 2.0}
            ],
            character_specific=CharacterType.LUKE_SKYWALKER,
            priority=5
        )

        self.behavior_library["leia_greeting"] = BehaviorSequence(
            name="Princess Leia Greeting",
            behavior_type=BehaviorType.GREETING,
            emotional_state=EmotionalState.HAPPY,
            duration=10.0,
            servo_movements=[
                {"action": "dome_bow", "angle": 30, "duration": 2.0},
                {"action": "hologram_projector_extend", "duration": 1.0},
                {"action": "dome_slow_turn", "angle": 180, "duration": 3.0},
                {"action": "all_panels_open_ceremonial", "duration": 2.0}
            ],
            audio_sequence=[
                {"sound": "respectful_beep_low", "delay": 0.0},
                {"sound": "princess_theme_whistle", "delay": 2.0},
                {"sound": "happy_chirp_sequence", "delay": 6.0}
            ],
            light_sequence=[
                {"action": "front_lights_royal_blue", "duration": 10.0},
                {"action": "hologram_light_activate", "duration": 4.0, "delay": 2.0}
            ],
            character_specific=CharacterType.PRINCESS_LEIA,
            priority=5
        )

        self.behavior_library["vader_reaction"] = BehaviorSequence(
            name="Darth Vader Encounter",
            behavior_type=BehaviorType.WARNING,
            emotional_state=EmotionalState.WORRIED,
            duration=12.0,
            servo_movements=[
                {"action": "dome_shrink_back", "angle": -20, "speed": "slow"},
                {"action": "all_panels_close_tight", "duration": 1.0},
                {"action": "body_lean_away", "angle": 10, "duration": 2.0},
                {"action": "dome_nervous_twitch", "repetitions": 5},
                {"action": "shock_prod_extend_defensive", "duration": 1.0}
            ],
            audio_sequence=[
                {"sound": "worried_descending_tone", "delay": 0.0},
                {"sound": "nervous_beep_pattern", "delay": 2.0},
                {"sound": "cautious_whistle", "delay": 6.0},
                {"sound": "imperial_march_whistle_fearful", "delay": 8.0}
            ],
            light_sequence=[
                {"action": "lights_dim_all", "duration": 2.0},
                {"action": "warning_red_flash", "repetitions": 3, "delay": 4.0}
            ],
            character_specific=CharacterType.DARTH_VADER,
            priority=8
        )

        # CURIOSITY BEHAVIORS
        self.behavior_library["head_tracking"] = BehaviorSequence(
            name="Curious Head Tracking",
            behavior_type=BehaviorType.CURIOSITY,
            emotional_state=EmotionalState.CURIOUS,
            duration=15.0,
            servo_movements=[
                {"action": "dome_smooth_tracking", "target": "person", "duration": 15.0},
                {"action": "dome_tilt_inquisitive", "angle": 10, "frequency": 0.1},
                {"action": "sensor_panel_open", "duration": 0.5, "delay": 5.0}
            ],
            audio_sequence=[
                {"sound": "curious_beep_questioning", "delay": 3.0},
                {"sound": "scanning_tones", "delay": 7.0},
                {"sound": "interested_whistle", "delay": 11.0}
            ],
            light_sequence=[
                {"action": "scanner_light_active", "duration": 15.0},
                {"action": "front_lights_gentle_pulse", "duration": 15.0}
            ],
            repeatable=True
        )

        self.behavior_library["environmental_scan"] = BehaviorSequence(
            name="Environmental Scanning",
            behavior_type=BehaviorType.SCANNING,
            emotional_state=EmotionalState.CURIOUS,
            duration=20.0,
            servo_movements=[
                {"action": "dome_360_scan", "speed": "slow", "repetitions": 2},
                {"action": "sensor_array_deploy", "duration": 2.0},
                {"action": "dome_pause_and_focus", "positions": [0, 90, 180, 270], "pause_duration": 3.0}
            ],
            audio_sequence=[
                {"sound": "scanning_startup", "delay": 0.0},
                {"sound": "sensor_sweep_tones", "delay": 2.0, "duration": 16.0},
                {"sound": "scan_complete_beep", "delay": 18.0}
            ],
            light_sequence=[
                {"action": "scanner_sweep_pattern", "duration": 20.0},
                {"action": "data_processing_lights", "duration": 10.0, "delay": 5.0}
            ]
        )

        # PLAYFUL BEHAVIORS
        self.behavior_library["dome_dance"] = BehaviorSequence(
            name="Happy Dome Dance",
            behavior_type=BehaviorType.PLAYFUL,
            emotional_state=EmotionalState.PLAYFUL,
            duration=25.0,
            servo_movements=[
                {"action": "dome_spin_dance", "pattern": "rhythmic", "duration": 20.0},
                {"action": "panels_percussion", "rhythm": "cantina_beat", "duration": 20.0},
                {"action": "body_rock_gentle", "duration": 25.0}
            ],
            audio_sequence=[
                {"sound": "cantina_band_whistle", "delay": 0.0, "duration": 25.0},
                {"sound": "happy_beep_rhythm", "delay": 2.0, "pattern": "beat"}
            ],
            light_sequence=[
                {"action": "disco_light_show", "duration": 25.0},
                {"action": "color_cycling_dome", "duration": 25.0}
            ]
        )

        self.behavior_library["hide_and_seek"] = BehaviorSequence(
            name="Hide and Seek Game",
            behavior_type=BehaviorType.PLAYFUL,
            emotional_state=EmotionalState.PLAYFUL,
            duration=30.0,
            servo_movements=[
                {"action": "dome_peek_around", "direction": "left", "duration": 3.0},
                {"action": "all_panels_close", "duration": 1.0},
                {"action": "dome_hide_position", "duration": 5.0},
                {"action": "surprise_reveal", "duration": 2.0},
                {"action": "celebration_wiggle", "duration": 3.0}
            ],
            audio_sequence=[
                {"sound": "playful_anticipation", "delay": 0.0},
                {"sound": "hiding_quiet_beeps", "delay": 5.0},
                {"sound": "surprise_whistle", "delay": 15.0},
                {"sound": "playful_victory", "delay": 20.0}
            ],
            light_sequence=[
                {"action": "lights_off_stealth", "duration": 10.0, "delay": 5.0},
                {"action": "surprise_light_burst", "delay": 15.0},
                {"action": "celebration_sparkle", "duration": 10.0, "delay": 20.0}
            ]
        )

        # STORYTELLING BEHAVIORS
        self.behavior_library["death_star_story"] = BehaviorSequence(
            name="Death Star Story",
            behavior_type=BehaviorType.STORYTELLING,
            emotional_state=EmotionalState.EXCITED,
            duration=45.0,
            servo_movements=[
                {"action": "hologram_projector_extend", "duration": 2.0},
                {"action": "dome_dramatic_turns", "sequence": "story_beats", "duration": 40.0},
                {"action": "panels_emphasis", "timing": "story_points"},
                {"action": "body_lean_storytelling", "duration": 45.0}
            ],
            audio_sequence=[
                {"sound": "story_intro_beeps", "delay": 0.0},
                {"sound": "death_star_plans_theme", "delay": 5.0, "duration": 35.0},
                {"sound": "triumphant_conclusion", "delay": 40.0}
            ],
            light_sequence=[
                {"action": "hologram_simulation", "duration": 40.0, "delay": 2.0},
                {"action": "dramatic_lighting", "duration": 45.0}
            ]
        )

        # IDLE BEHAVIORS
        self.behavior_library["maintenance_routine"] = BehaviorSequence(
            name="Self Maintenance",
            behavior_type=BehaviorType.IDLE,
            emotional_state=EmotionalState.CURIOUS,
            duration=18.0,
            servo_movements=[
                {"action": "diagnostic_panel_check", "duration": 5.0},
                {"action": "sensor_cleaning_routine", "duration": 8.0},
                {"action": "dome_calibration", "duration": 5.0}
            ],
            audio_sequence=[
                {"sound": "diagnostic_beeps", "delay": 0.0},
                {"sound": "maintenance_sounds", "delay": 5.0},
                {"sound": "system_ready_chirp", "delay": 16.0}
            ],
            light_sequence=[
                {"action": "diagnostic_indicators", "duration": 18.0}
            ]
        )

        self.behavior_library["bored_fidget"] = BehaviorSequence(
            name="Bored Fidgeting",
            behavior_type=BehaviorType.IDLE,
            emotional_state=EmotionalState.SLEEPY,
            duration=12.0,
            servo_movements=[
                {"action": "dome_slow_random_turns", "duration": 12.0},
                {"action": "panel_idle_movements", "frequency": 0.05},
                {"action": "sleepy_sway", "duration": 12.0}
            ],
            audio_sequence=[
                {"sound": "bored_sigh_beep", "delay": 0.0},
                {"sound": "idle_electronic_sounds", "delay": 5.0}
            ],
            light_sequence=[
                {"action": "dim_idle_pulse", "duration": 12.0}
            ]
        )

        # CROWD INTERACTION BEHAVIORS
        self.behavior_library["crowd_entertainer"] = BehaviorSequence(
            name="Crowd Entertainment",
            behavior_type=BehaviorType.PLAYFUL,
            emotional_state=EmotionalState.EXCITED,
            duration=60.0,
            servo_movements=[
                {"action": "dome_crowd_scan", "duration": 10.0},
                {"action": "wave_greeting", "repetitions": 3},
                {"action": "photo_pose_sequence", "duration": 15.0},
                {"action": "crowd_interaction_dance", "duration": 30.0}
            ],
            audio_sequence=[
                {"sound": "crowd_greeting_medley", "delay": 0.0},
                {"sound": "photo_ready_beeps", "delay": 15.0},
                {"sound": "entertainment_sequence", "delay": 25.0}
            ],
            light_sequence=[
                {"action": "crowd_pleasing_lights", "duration": 60.0},
                {"action": "photo_flash_sequence", "delay": 15.0}
            ]
        )

        # EMERGENCY BEHAVIORS
        self.behavior_library["emergency_stop"] = BehaviorSequence(
            name="Emergency Stop",
            behavior_type=BehaviorType.EMERGENCY,
            emotional_state=EmotionalState.WORRIED,
            duration=5.0,
            servo_movements=[
                {"action": "all_servos_stop", "immediate": True},
                {"action": "safe_position", "duration": 2.0},
                {"action": "emergency_indicator", "duration": 3.0}
            ],
            audio_sequence=[
                {"sound": "emergency_alert", "delay": 0.0},
                {"sound": "system_shutdown", "delay": 2.0}
            ],
            light_sequence=[
                {"action": "emergency_red_flash", "duration": 5.0}
            ],
            priority=10,
            repeatable=False
        )

        logger.info(f"Initialized {len(self.behavior_library)} behaviors")

    def set_emotional_state(self, state: EmotionalState, duration: Optional[float] = None):
        """Set R2D2's emotional state"""
        logger.info(f"Emotional state changing from {self.current_emotional_state} to {state}")
        self.current_emotional_state = state

        if duration:
            # Automatically revert after duration
            threading.Timer(duration, self._revert_to_default_state).start()

    def _revert_to_default_state(self):
        """Revert to default curious state"""
        self.current_emotional_state = EmotionalState.CURIOUS
        logger.info("Reverted to default curious state")

    def detect_character(self, character_type: CharacterType, confidence: float = 1.0):
        """Process character detection and trigger appropriate behavior"""
        logger.info(f"Character detected: {character_type} (confidence: {confidence})")

        # Update interaction memory
        if character_type not in self.interaction_memory:
            self.interaction_memory[character_type] = {
                "encounter_count": 0,
                "last_interaction": 0,
                "favorite_behaviors": []
            }

        self.interaction_memory[character_type]["encounter_count"] += 1
        self.interaction_memory[character_type]["last_interaction"] = time.time()

        # Select appropriate behavior
        behavior = self._select_character_behavior(character_type)
        if behavior:
            self.execute_behavior(behavior)

    def _select_character_behavior(self, character_type: CharacterType) -> Optional[str]:
        """Select the most appropriate behavior for a character"""
        character_behaviors = [
            name for name, behavior in self.behavior_library.items()
            if behavior.character_specific == character_type
        ]

        if character_behaviors:
            # Select based on interaction history and randomness
            memory = self.interaction_memory.get(character_type, {})
            encounter_count = memory.get("encounter_count", 0)

            # First encounters get priority greetings
            if encounter_count <= 1:
                greeting_behaviors = [b for b in character_behaviors
                                    if self.behavior_library[b].behavior_type == BehaviorType.GREETING]
                if greeting_behaviors:
                    return greeting_behaviors[0]

            # Subsequent encounters get varied responses
            return random.choice(character_behaviors)

        # Fallback to general behaviors
        return self._select_general_behavior(BehaviorType.ATTENTION)

    def _select_general_behavior(self, behavior_type: BehaviorType) -> Optional[str]:
        """Select a general behavior of the specified type"""
        matching_behaviors = [
            name for name, behavior in self.behavior_library.items()
            if behavior.behavior_type == behavior_type and
               behavior.character_specific is None and
               behavior.emotional_state == self.current_emotional_state
        ]

        if matching_behaviors:
            return random.choice(matching_behaviors)

        # Fallback to any matching type regardless of emotional state
        fallback_behaviors = [
            name for name, behavior in self.behavior_library.items()
            if behavior.behavior_type == behavior_type and
               behavior.character_specific is None
        ]

        return random.choice(fallback_behaviors) if fallback_behaviors else None

    def execute_behavior(self, behavior_name: str):
        """Execute a specific behavior sequence"""
        if behavior_name not in self.behavior_library:
            logger.error(f"Behavior '{behavior_name}' not found")
            return

        behavior = self.behavior_library[behavior_name]
        logger.info(f"Executing behavior: {behavior.name}")

        # Update emotional state if different
        if behavior.emotional_state != self.current_emotional_state:
            self.set_emotional_state(behavior.emotional_state, behavior.duration)

        # Set current behavior
        self.current_behavior = behavior

        # Execute behavior components in parallel threads
        servo_thread = threading.Thread(target=self._execute_servo_movements, args=(behavior.servo_movements,))
        audio_thread = threading.Thread(target=self._execute_audio_sequence, args=(behavior.audio_sequence,))
        light_thread = threading.Thread(target=self._execute_light_sequence, args=(behavior.light_sequence,))

        servo_thread.start()
        audio_thread.start()
        light_thread.start()

        # Wait for completion
        servo_thread.join()
        audio_thread.join()
        light_thread.join()

        self.current_behavior = None
        logger.info(f"Completed behavior: {behavior.name}")

    def _execute_servo_movements(self, movements: List[Dict]):
        """Execute servo movement sequence"""
        for movement in movements:
            if self.safety_override:
                logger.warning("Safety override active - stopping servo movements")
                break

            # This would interface with actual servo control system
            logger.info(f"Servo movement: {movement}")

            # Simulate movement duration
            if "duration" in movement:
                time.sleep(movement["duration"])
            elif "delay" in movement:
                time.sleep(movement["delay"])

    def _execute_audio_sequence(self, audio_sequence: List[Dict]):
        """Execute audio sequence"""
        for audio in audio_sequence:
            if "delay" in audio:
                time.sleep(audio["delay"])

            # This would interface with actual audio system
            logger.info(f"Playing audio: {audio}")

            if "duration" in audio:
                time.sleep(audio["duration"])

    def _execute_light_sequence(self, light_sequence: List[Dict]):
        """Execute lighting sequence"""
        for light in light_sequence:
            if "delay" in light:
                time.sleep(light["delay"])

            # This would interface with actual lighting system
            logger.info(f"Light effect: {light}")

            if "duration" in light:
                time.sleep(light["duration"])

    def _autonomous_behavior_loop(self):
        """Autonomous behavior execution loop"""
        while True:
            if self.autonomous_mode and not self.current_behavior and not self.safety_override:
                # Select idle behavior
                idle_behavior = self._select_general_behavior(BehaviorType.IDLE)
                if idle_behavior:
                    self.execute_behavior(idle_behavior)

                # Wait before next autonomous behavior
                time.sleep(random.uniform(30, 90))  # 30-90 seconds between autonomous behaviors
            else:
                time.sleep(5)  # Check every 5 seconds

    def emergency_stop(self):
        """Trigger emergency stop behavior"""
        logger.critical("EMERGENCY STOP ACTIVATED")
        self.safety_override = True
        self.execute_behavior("emergency_stop")

    def resume_operation(self):
        """Resume normal operation after emergency stop"""
        logger.info("Resuming normal operation")
        self.safety_override = False

    def get_behavior_status(self) -> Dict:
        """Get current behavioral system status"""
        return {
            "current_emotional_state": self.current_emotional_state.value,
            "current_behavior": self.current_behavior.name if self.current_behavior else None,
            "autonomous_mode": self.autonomous_mode,
            "safety_override": self.safety_override,
            "interaction_memory_size": len(self.interaction_memory),
            "available_behaviors": len(self.behavior_library)
        }


class R2D2InteractionEngine:
    """Advanced interaction engine for crowd management and character recognition"""

    def __init__(self, behavioral_system: R2D2BehavioralSystem):
        self.behavioral_system = behavioral_system
        self.crowd_detector = CrowdDetector()
        self.character_recognizer = CharacterRecognizer()
        self.interaction_history = []

    def process_crowd_interaction(self, crowd_size: int, noise_level: float):
        """Process crowd interaction based on size and environment"""
        if crowd_size > 20:
            # Large crowd - entertainment mode
            self.behavioral_system.execute_behavior("crowd_entertainer")
        elif crowd_size > 5:
            # Medium crowd - general interaction
            behavior = random.choice(["dome_dance", "environmental_scan", "head_tracking"])
            self.behavioral_system.execute_behavior(behavior)
        elif crowd_size > 0:
            # Small group - personalized interaction
            self.behavioral_system.execute_behavior("head_tracking")
        else:
            # No crowd - autonomous behavior
            self.behavioral_system.autonomous_mode = True


class CrowdDetector:
    """Detects and analyzes crowd characteristics"""

    def __init__(self):
        self.detection_active = True

    def get_crowd_metrics(self) -> Dict:
        """Get current crowd metrics"""
        # Placeholder for actual crowd detection implementation
        return {
            "count": random.randint(0, 30),
            "noise_level": random.uniform(0.1, 1.0),
            "movement_level": random.uniform(0.0, 1.0),
            "average_distance": random.uniform(1.0, 5.0)
        }


class CharacterRecognizer:
    """Recognizes Star Wars characters and costumes"""

    def __init__(self):
        self.recognition_active = True
        self.character_confidence_threshold = 0.7

    def identify_character(self, visual_input) -> tuple[CharacterType, float]:
        """Identify character from visual input"""
        # Placeholder for actual character recognition implementation
        characters = list(CharacterType)
        detected_character = random.choice(characters)
        confidence = random.uniform(0.5, 1.0)

        return detected_character, confidence


# Example usage and testing
if __name__ == "__main__":
    # Initialize R2D2 behavioral system
    r2d2 = R2D2BehavioralSystem()

    # Initialize interaction engine
    interaction_engine = R2D2InteractionEngine(r2d2)

    # Simulate character encounters
    print("=== R2D2 Behavioral System Demo ===")

    # Luke Skywalker encounter
    print("\n--- Luke Skywalker Detected ---")
    r2d2.detect_character(CharacterType.LUKE_SKYWALKER)
    time.sleep(2)

    # Princess Leia encounter
    print("\n--- Princess Leia Detected ---")
    r2d2.detect_character(CharacterType.PRINCESS_LEIA)
    time.sleep(2)

    # Darth Vader encounter
    print("\n--- Darth Vader Detected ---")
    r2d2.detect_character(CharacterType.DARTH_VADER)
    time.sleep(2)

    # Crowd interaction
    print("\n--- Large Crowd Detected ---")
    interaction_engine.process_crowd_interaction(25, 0.8)
    time.sleep(2)

    # Display status
    print("\n--- Current Status ---")
    status = r2d2.get_behavior_status()
    for key, value in status.items():
        print(f"{key}: {value}")

    print("\n=== Demo Complete ===")