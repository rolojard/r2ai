#!/usr/bin/env python3
"""
Disney-Level R2D2 Personality Engagement System for Guest Interactions
====================================================================

Advanced personality system that creates authentic, engaging R2D2 behaviors
with Disney-quality character consistency and Star Wars canon compliance.
This system manages R2D2's personality expression through coordinated
motion, audio, and interaction responses that delight convention guests.

Features:
- Authentic R2D2 personality traits with Star Wars canon compliance
- Context-aware personality adaptation for different guest types
- Emotional memory and relationship building with repeat guests
- Dynamic personality expression through motion and audio coordination
- Guest preference learning and personalized interaction styles
- Convention environment personality optimization
- Magic moment creation with Disney-level guest experience design
- Comprehensive personality consistency monitoring and adjustment

Author: Imagineer Specialist Agent
Target: NVIDIA Orin Nano R2D2 Systems
Integration: Trigger System, Motion Control, Audio Coordination, Guest Detection
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

# Import foundational systems
try:
    from r2d2_character_motion_system import (
        PersonalityTrait, MotionIntensity, InteractionContext
    )
    from interactive_guest_detection_system import (
        DetectedGuest, GuestAgeGroup, EmotionalExpression, GestureType
    )
    from r2d2_trigger_system_coordinator import TriggerEvent, TriggerType
    from audio_servo_coordinator import AudioServoCoordinator
except ImportError as e:
    logging.warning(f"Import warning: {e}. Some functionality may be limited.")

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PersonalityMode(Enum):
    """R2D2 personality modes for different contexts"""
    CURIOUS_EXPLORER = "curious_explorer"           # Default investigative personality
    LOYAL_COMPANION = "loyal_companion"             # Devoted friend personality
    PROTECTIVE_GUARDIAN = "protective_guardian"     # Safety-focused personality
    PLAYFUL_ENTERTAINER = "playful_entertainer"     # Fun, engaging personality
    WISE_MENTOR = "wise_mentor"                     # Knowledgeable guide personality
    MISCHIEVOUS_TRICKSTER = "mischievous_trickster" # Playful troublemaker
    HEROIC_ADVENTURER = "heroic_adventurer"         # Brave, bold personality
    GENTLE_CARETAKER = "gentle_caretaker"           # Nurturing, caring personality
    ANALYTICAL_INVESTIGATOR = "analytical_investigator" # Logical, methodical
    EXCITED_FAN_ENCOUNTER = "excited_fan_encounter"  # Meeting Star Wars fans

class PersonalityIntensity(Enum):
    """Intensity levels for personality expression"""
    SUBTLE = 0.3        # Understated personality expression
    MODERATE = 0.6      # Normal personality expression
    PRONOUNCED = 0.9    # Strong personality expression
    DRAMATIC = 1.2      # Maximum personality expression

class EmotionalState(Enum):
    """R2D2's emotional states"""
    CONTENT = "content"             # Peaceful, satisfied state
    CURIOUS = "curious"             # Interested, investigating
    EXCITED = "excited"             # Enthusiastic, energetic
    CONCERNED = "concerned"         # Worried, protective
    FRUSTRATED = "frustrated"       # Annoyed, impatient
    DELIGHTED = "delighted"        # Very happy, pleased
    FOCUSED = "focused"            # Concentrated, determined
    PLAYFUL = "playful"            # Fun-loving, mischievous
    ALERT = "alert"                # Vigilant, ready for action
    AFFECTIONATE = "affectionate"  # Loving, bonded

@dataclass
class PersonalityProfile:
    """Complete personality profile for R2D2"""
    mode: PersonalityMode
    primary_traits: List[PersonalityTrait]
    secondary_traits: List[PersonalityTrait]
    emotional_tendencies: List[EmotionalState]

    # Expression parameters
    motion_style_modifier: float = 1.0          # Affects motion timing and intensity
    audio_tone_modifier: float = 1.0            # Affects audio pitch and rhythm
    interaction_eagerness: float = 0.8          # How readily R2D2 engages
    attention_span: float = 1.0                 # How long interactions are sustained
    curiosity_level: float = 0.7               # How much R2D2 investigates

    # Social preferences
    preferred_guest_types: List[GuestAgeGroup] = field(default_factory=list)
    interaction_distance_preference: float = 2.0  # Preferred interaction distance
    group_interaction_comfort: float = 0.6      # Comfort with crowds

    # Behavioral patterns
    greeting_style: str = "enthusiastic_head_bob"
    idle_behaviors: List[str] = field(default_factory=list)
    stress_responses: List[str] = field(default_factory=list)
    celebration_behaviors: List[str] = field(default_factory=list)

@dataclass
class GuestRelationship:
    """Relationship data for individual guests"""
    guest_id: str
    first_encounter: float = field(default_factory=time.time)
    total_interaction_time: float = 0.0
    interaction_count: int = 0
    last_interaction: float = field(default_factory=time.time)

    # Relationship characteristics
    familiarity_level: float = 0.0             # 0.0 = stranger, 1.0 = close friend
    trust_level: float = 0.5                   # How much R2D2 trusts this guest
    affection_level: float = 0.5               # How much R2D2 likes this guest

    # Guest preferences and characteristics
    preferred_personality_mode: Optional[PersonalityMode] = None
    guest_characteristics: Dict[str, Any] = field(default_factory=dict)
    interaction_history: List[str] = field(default_factory=list)
    positive_interactions: int = 0
    negative_interactions: int = 0

    # Memory of specific interactions
    memorable_moments: List[Dict[str, Any]] = field(default_factory=list)
    guest_preferences: Dict[str, Any] = field(default_factory=dict)

@dataclass
class PersonalityState:
    """Current personality state of R2D2"""
    current_mode: PersonalityMode
    current_intensity: PersonalityIntensity
    current_emotion: EmotionalState

    # State parameters
    energy_level: float = 0.8                  # Current energy (0.0-1.0)
    social_battery: float = 1.0                # Social interaction capacity
    stress_level: float = 0.0                  # Current stress (0.0-1.0)
    confidence_level: float = 0.8              # Current confidence

    # Temporal factors
    state_start_time: float = field(default_factory=time.time)
    state_duration: float = 0.0
    last_state_change: float = field(default_factory=time.time)

class R2D2PersonalityEngagementSystem:
    """
    Disney-Level R2D2 Personality Engagement System

    This system creates magical, authentic R2D2 interactions by managing
    comprehensive personality expression that adapts to individual guests
    while maintaining Star Wars canon consistency and Disney-quality
    character development.
    """

    def __init__(self, character_system=None, audio_coordinator=None,
                 trigger_coordinator=None, guest_detection=None):
        """Initialize the personality engagement system"""

        # Core system components
        self.character_system = character_system
        self.audio_coordinator = audio_coordinator
        self.trigger_coordinator = trigger_coordinator
        self.guest_detection = guest_detection

        # Personality system
        self.personality_profiles = {}
        self.current_personality_state = PersonalityState(
            current_mode=PersonalityMode.CURIOUS_EXPLORER,
            current_intensity=PersonalityIntensity.MODERATE,
            current_emotion=EmotionalState.CONTENT
        )

        # Guest relationship management
        self.guest_relationships = {}
        self.relationship_memory = deque(maxlen=1000)
        self.interaction_patterns = {}

        # Personality adaptation
        self.adaptation_rules = {}
        self.context_modifiers = {}
        self.environmental_factors = {}

        # System state
        self.is_active = False
        self.personality_thread = None
        self.relationship_thread = None
        self.adaptation_thread = None

        # Performance metrics
        self.engagement_metrics = {
            'total_interactions': 0,
            'successful_engagements': 0,
            'guest_satisfaction_estimate': 0.8,
            'personality_consistency_score': 0.9,
            'relationship_retention_rate': 0.7,
            'magic_moments_created': 0,
            'adaptation_accuracy': 0.8
        }

        # Disney experience configuration
        self.disney_config = {
            'magic_moment_threshold': 0.15,        # Probability of special moments
            'personality_consistency_weight': 0.85,
            'guest_memory_retention_hours': 24.0,
            'emotional_responsiveness': 1.2,
            'character_authenticity_requirement': 0.9,
            'surprise_element_factor': 0.2
        }

        # Initialize personality system
        self._initialize_personality_profiles()
        self._initialize_adaptation_rules()
        self._initialize_context_modifiers()

        logger.info("R2D2 Personality Engagement System initialized")

    def _initialize_personality_profiles(self):
        """Initialize comprehensive personality profiles"""

        self.personality_profiles = {
            PersonalityMode.CURIOUS_EXPLORER: PersonalityProfile(
                mode=PersonalityMode.CURIOUS_EXPLORER,
                primary_traits=[PersonalityTrait.CURIOUS, PersonalityTrait.ANALYTICAL],
                secondary_traits=[PersonalityTrait.CAUTIOUS, PersonalityTrait.PLAYFUL],
                emotional_tendencies=[EmotionalState.CURIOUS, EmotionalState.FOCUSED, EmotionalState.ALERT],
                motion_style_modifier=1.0,
                audio_tone_modifier=1.1,
                interaction_eagerness=0.9,
                attention_span=1.2,
                curiosity_level=1.0,
                preferred_guest_types=[GuestAgeGroup.ADULT, GuestAgeGroup.TEENAGER],
                interaction_distance_preference=2.5,
                group_interaction_comfort=0.7,
                greeting_style="curious_head_tilt",
                idle_behaviors=["environmental_scan", "curious_investigation", "gentle_head_movement"],
                stress_responses=["protective_scan", "cautious_backup"],
                celebration_behaviors=["excited_head_bob", "discovery_celebration"]
            ),

            PersonalityMode.LOYAL_COMPANION: PersonalityProfile(
                mode=PersonalityMode.LOYAL_COMPANION,
                primary_traits=[PersonalityTrait.LOYAL, PersonalityTrait.PROTECTIVE],
                secondary_traits=[PersonalityTrait.CONFIDENT, PersonalityTrait.CONCERNED],
                emotional_tendencies=[EmotionalState.AFFECTIONATE, EmotionalState.FOCUSED, EmotionalState.ALERT],
                motion_style_modifier=0.9,
                audio_tone_modifier=0.9,
                interaction_eagerness=0.8,
                attention_span=1.5,
                curiosity_level=0.6,
                preferred_guest_types=[GuestAgeGroup.ADULT, GuestAgeGroup.SENIOR],
                interaction_distance_preference=1.8,
                group_interaction_comfort=0.5,
                greeting_style="loyal_acknowledgment",
                idle_behaviors=["protective_scan", "companion_ready_stance"],
                stress_responses=["protective_positioning", "alert_scanning"],
                celebration_behaviors=["loyal_celebration", "companion_pride"]
            ),

            PersonalityMode.PLAYFUL_ENTERTAINER: PersonalityProfile(
                mode=PersonalityMode.PLAYFUL_ENTERTAINER,
                primary_traits=[PersonalityTrait.PLAYFUL, PersonalityTrait.EXCITED],
                secondary_traits=[PersonalityTrait.MISCHIEVOUS, PersonalityTrait.CONFIDENT],
                emotional_tendencies=[EmotionalState.PLAYFUL, EmotionalState.EXCITED, EmotionalState.DELIGHTED],
                motion_style_modifier=1.3,
                audio_tone_modifier=1.2,
                interaction_eagerness=1.0,
                attention_span=0.8,
                curiosity_level=0.9,
                preferred_guest_types=[GuestAgeGroup.CHILD, GuestAgeGroup.TEENAGER],
                interaction_distance_preference=2.0,
                group_interaction_comfort=0.9,
                greeting_style="enthusiastic_greeting",
                idle_behaviors=["playful_movement", "entertainment_ready", "mischievous_head_wiggle"],
                stress_responses=["play_deflection", "entertaining_distraction"],
                celebration_behaviors=["excited_celebration", "playful_victory_dance"]
            ),

            PersonalityMode.GENTLE_CARETAKER: PersonalityProfile(
                mode=PersonalityMode.GENTLE_CARETAKER,
                primary_traits=[PersonalityTrait.GENTLE_CURIOUS, PersonalityTrait.PROTECTIVE],
                secondary_traits=[PersonalityTrait.CAUTIOUS, PersonalityTrait.LOYAL],
                emotional_tendencies=[EmotionalState.AFFECTIONATE, EmotionalState.CONTENT, EmotionalState.CONCERNED],
                motion_style_modifier=0.7,
                audio_tone_modifier=0.8,
                interaction_eagerness=0.7,
                attention_span=1.8,
                curiosity_level=0.5,
                preferred_guest_types=[GuestAgeGroup.TODDLER, GuestAgeGroup.CHILD, GuestAgeGroup.SENIOR],
                interaction_distance_preference=1.5,
                group_interaction_comfort=0.4,
                greeting_style="gentle_greeting",
                idle_behaviors=["gentle_monitoring", "caring_observation"],
                stress_responses=["gentle_withdrawal", "protective_positioning"],
                celebration_behaviors=["gentle_celebration", "caring_acknowledgment"]
            ),

            PersonalityMode.HEROIC_ADVENTURER: PersonalityProfile(
                mode=PersonalityMode.HEROIC_ADVENTURER,
                primary_traits=[PersonalityTrait.HEROIC, PersonalityTrait.CONFIDENT],
                secondary_traits=[PersonalityTrait.LOYAL, PersonalityTrait.EXCITED],
                emotional_tendencies=[EmotionalState.CONFIDENT, EmotionalState.FOCUSED, EmotionalState.EXCITED],
                motion_style_modifier=1.2,
                audio_tone_modifier=1.1,
                interaction_eagerness=0.9,
                attention_span=1.0,
                curiosity_level=0.8,
                preferred_guest_types=[GuestAgeGroup.ADULT, GuestAgeGroup.TEENAGER],
                interaction_distance_preference=2.2,
                group_interaction_comfort=0.8,
                greeting_style="heroic_acknowledgment",
                idle_behaviors=["heroic_stance", "adventure_ready_position"],
                stress_responses=["heroic_defensive", "brave_positioning"],
                celebration_behaviors=["heroic_celebration", "victory_presentation"]
            ),

            PersonalityMode.EXCITED_FAN_ENCOUNTER: PersonalityProfile(
                mode=PersonalityMode.EXCITED_FAN_ENCOUNTER,
                primary_traits=[PersonalityTrait.EXCITED, PersonalityTrait.PLAYFUL],
                secondary_traits=[PersonalityTrait.CONFIDENT, PersonalityTrait.HEROIC],
                emotional_tendencies=[EmotionalState.EXCITED, EmotionalState.DELIGHTED, EmotionalState.PLAYFUL],
                motion_style_modifier=1.4,
                audio_tone_modifier=1.3,
                interaction_eagerness=1.2,
                attention_span=1.1,
                curiosity_level=1.0,
                preferred_guest_types=[GuestAgeGroup.ADULT, GuestAgeGroup.TEENAGER],
                interaction_distance_preference=2.0,
                group_interaction_comfort=1.0,
                greeting_style="excited_fan_greeting",
                idle_behaviors=["excited_anticipation", "fan_interaction_ready"],
                stress_responses=["excited_overwhelm", "fan_appreciation"],
                celebration_behaviors=["fan_encounter_celebration", "star_wars_moment"]
            )
        }

        logger.info(f"Initialized {len(self.personality_profiles)} personality profiles")

    def _initialize_adaptation_rules(self):
        """Initialize personality adaptation rules"""

        self.adaptation_rules = {
            # Age-based adaptations
            'age_adaptations': {
                GuestAgeGroup.TODDLER: {
                    'preferred_mode': PersonalityMode.GENTLE_CARETAKER,
                    'intensity_modifier': 0.6,
                    'safety_priority': True,
                    'interaction_style': 'very_gentle'
                },
                GuestAgeGroup.CHILD: {
                    'preferred_mode': PersonalityMode.PLAYFUL_ENTERTAINER,
                    'intensity_modifier': 0.8,
                    'safety_priority': True,
                    'interaction_style': 'playful'
                },
                GuestAgeGroup.TEENAGER: {
                    'preferred_mode': PersonalityMode.EXCITED_FAN_ENCOUNTER,
                    'intensity_modifier': 1.1,
                    'interaction_style': 'enthusiastic'
                },
                GuestAgeGroup.ADULT: {
                    'preferred_mode': PersonalityMode.CURIOUS_EXPLORER,
                    'intensity_modifier': 1.0,
                    'interaction_style': 'engaging'
                },
                GuestAgeGroup.SENIOR: {
                    'preferred_mode': PersonalityMode.LOYAL_COMPANION,
                    'intensity_modifier': 0.9,
                    'interaction_style': 'respectful'
                }
            },

            # Emotion-based adaptations
            'emotion_adaptations': {
                EmotionalExpression.HAPPY: {
                    'emotion_response': EmotionalState.DELIGHTED,
                    'intensity_boost': 0.2,
                    'interaction_eagerness_boost': 0.1
                },
                EmotionalExpression.EXCITED: {
                    'emotion_response': EmotionalState.EXCITED,
                    'intensity_boost': 0.3,
                    'interaction_eagerness_boost': 0.2
                },
                EmotionalExpression.CURIOUS: {
                    'emotion_response': EmotionalState.CURIOUS,
                    'mode_preference': PersonalityMode.CURIOUS_EXPLORER,
                    'interaction_eagerness_boost': 0.15
                },
                EmotionalExpression.CONCERNED: {
                    'emotion_response': EmotionalState.CONCERNED,
                    'mode_preference': PersonalityMode.GENTLE_CARETAKER,
                    'intensity_modifier': 0.8
                }
            },

            # Context-based adaptations
            'context_adaptations': {
                InteractionContext.FIRST_ENCOUNTER: {
                    'approach_style': 'gentle_introduction',
                    'curiosity_boost': 0.2,
                    'caution_factor': 1.2
                },
                InteractionContext.FAMILIAR_GUEST: {
                    'approach_style': 'warm_recognition',
                    'affection_boost': 0.3,
                    'comfort_level_increase': 0.2
                },
                InteractionContext.CHILD_INTERACTION: {
                    'mode_override': PersonalityMode.GENTLE_CARETAKER,
                    'safety_emphasis': True,
                    'gentleness_factor': 1.5
                },
                InteractionContext.GROUP_CROWD: {
                    'mode_preference': PersonalityMode.PLAYFUL_ENTERTAINER,
                    'group_awareness': True,
                    'performance_mode': True
                },
                InteractionContext.PHOTO_SESSION: {
                    'mode_preference': PersonalityMode.HEROIC_ADVENTURER,
                    'pose_readiness': True,
                    'presentation_focus': True
                }
            }
        }

        logger.info("Personality adaptation rules configured")

    def _initialize_context_modifiers(self):
        """Initialize environmental and contextual modifiers"""

        self.context_modifiers = {
            # Time-based modifiers
            'time_of_day': {
                'morning': {'energy_modifier': 0.9, 'curiosity_boost': 0.1},
                'afternoon': {'energy_modifier': 1.0, 'social_battery_drain': 0.1},
                'evening': {'energy_modifier': 0.8, 'fatigue_factor': 0.2}
            },

            # Crowd density modifiers
            'crowd_density': {
                'low': {'comfort_boost': 0.2, 'interaction_eagerness_boost': 0.1},
                'medium': {'baseline': True},
                'high': {'stress_increase': 0.2, 'social_battery_drain': 0.2},
                'overwhelming': {'protective_mode': True, 'interaction_limitation': True}
            },

            # Environmental factors
            'environmental': {
                'noise_level_high': {'stress_increase': 0.1, 'audio_compensation': True},
                'lighting_poor': {'caution_increase': 0.1},
                'space_restricted': {'comfort_reduction': 0.2},
                'temperature_uncomfortable': {'energy_reduction': 0.1}
            }
        }

        logger.info("Context modifiers configured")

    def start_personality_system(self) -> bool:
        """Start the personality engagement system"""

        if self.is_active:
            logger.warning("Personality system is already active")
            return True

        try:
            self.is_active = True

            # Start personality processing threads
            self.personality_thread = threading.Thread(
                target=self._personality_management_loop,
                daemon=True,
                name="PersonalityManagementLoop"
            )
            self.personality_thread.start()

            self.relationship_thread = threading.Thread(
                target=self._relationship_management_loop,
                daemon=True,
                name="RelationshipManagementLoop"
            )
            self.relationship_thread.start()

            self.adaptation_thread = threading.Thread(
                target=self._adaptation_processing_loop,
                daemon=True,
                name="AdaptationProcessingLoop"
            )
            self.adaptation_thread.start()

            logger.info("R2D2 Personality Engagement System started successfully")
            return True

        except Exception as e:
            logger.error(f"Failed to start personality system: {e}")
            self.is_active = False
            return False

    def stop_personality_system(self):
        """Stop the personality engagement system"""

        self.is_active = False

        # Wait for threads to finish
        for thread in [self.personality_thread, self.relationship_thread, self.adaptation_thread]:
            if thread and thread.is_alive():
                thread.join(timeout=2.0)

        logger.info("R2D2 Personality Engagement System stopped")

    def _personality_management_loop(self):
        """Main personality management loop"""

        logger.info("Personality management loop started")

        while self.is_active:
            try:
                current_time = time.time()

                # Update personality state
                self._update_personality_state()

                # Check for personality transitions
                self._check_personality_transitions()

                # Apply personality to systems
                self._apply_personality_to_systems()

                # Update personality metrics
                self._update_personality_metrics()

                # Sleep for personality update cycle
                time.sleep(0.5)  # 2Hz personality updates

            except Exception as e:
                logger.error(f"Error in personality management loop: {e}")
                time.sleep(1.0)

        logger.info("Personality management loop stopped")

    def _relationship_management_loop(self):
        """Guest relationship management loop"""

        logger.info("Relationship management loop started")

        while self.is_active:
            try:
                # Update guest relationships
                self._update_guest_relationships()

                # Process relationship memory
                self._process_relationship_memory()

                # Check for returning guests
                self._check_for_returning_guests()

                # Update relationship metrics
                self._update_relationship_metrics()

                # Sleep for relationship processing cycle
                time.sleep(2.0)  # 0.5Hz relationship updates

            except Exception as e:
                logger.error(f"Error in relationship management loop: {e}")
                time.sleep(2.0)

        logger.info("Relationship management loop stopped")

    def _adaptation_processing_loop(self):
        """Personality adaptation processing loop"""

        logger.info("Adaptation processing loop started")

        while self.is_active:
            try:
                # Analyze current context
                current_context = self._analyze_current_context()

                # Determine optimal personality adaptation
                optimal_adaptation = self._determine_optimal_adaptation(current_context)

                # Apply personality adaptation
                if optimal_adaptation:
                    self._apply_personality_adaptation(optimal_adaptation)

                # Monitor adaptation effectiveness
                self._monitor_adaptation_effectiveness()

                # Sleep for adaptation processing cycle
                time.sleep(1.0)  # 1Hz adaptation processing

            except Exception as e:
                logger.error(f"Error in adaptation processing loop: {e}")
                time.sleep(1.0)

        logger.info("Adaptation processing loop stopped")

    def _update_personality_state(self):
        """Update current personality state"""

        current_time = time.time()
        state = self.current_personality_state

        # Update state duration
        state.state_duration = current_time - state.state_start_time

        # Apply time-based state changes
        self._apply_temporal_personality_changes()

        # Update energy and social battery
        self._update_personality_resources()

        # Check for stress factors
        self._update_stress_level()

    def _apply_temporal_personality_changes(self):
        """Apply time-based personality changes"""

        # Gradual energy decrease over time
        time_factor = min(self.current_personality_state.state_duration / 3600.0, 8.0)  # Hours
        energy_decay = time_factor * 0.05  # 5% per hour

        self.current_personality_state.energy_level = max(
            0.3, self.current_personality_state.energy_level - energy_decay
        )

    def _update_personality_resources(self):
        """Update personality resources (energy, social battery)"""

        # Social battery drain based on interactions
        active_guests = self._get_current_guests()
        if active_guests:
            crowd_factor = min(len(active_guests) / 5.0, 2.0)  # Normalize to 5 guests
            battery_drain = crowd_factor * 0.001  # Per update cycle

            self.current_personality_state.social_battery = max(
                0.2, self.current_personality_state.social_battery - battery_drain
            )

        # Energy recovery during low activity
        if not active_guests:
            energy_recovery = 0.002  # Per update cycle
            self.current_personality_state.energy_level = min(
                1.0, self.current_personality_state.energy_level + energy_recovery
            )

    def _update_stress_level(self):
        """Update stress level based on environmental factors"""

        stress_factors = 0.0

        # Crowd stress
        active_guests = self._get_current_guests()
        if len(active_guests) > 5:
            stress_factors += (len(active_guests) - 5) * 0.1

        # Social battery stress
        if self.current_personality_state.social_battery < 0.3:
            stress_factors += 0.2

        # Update stress with decay
        current_stress = self.current_personality_state.stress_level
        target_stress = min(stress_factors, 1.0)

        # Gradual stress adjustment
        stress_change = (target_stress - current_stress) * 0.1
        self.current_personality_state.stress_level = max(0.0, min(1.0, current_stress + stress_change))

    def _check_personality_transitions(self):
        """Check for necessary personality mode transitions"""

        current_mode = self.current_personality_state.current_mode

        # Get current guests
        active_guests = self._get_current_guests()

        if not active_guests:
            # No guests - return to default mode
            target_mode = PersonalityMode.CURIOUS_EXPLORER
        else:
            # Determine best mode for current guests
            target_mode = self._determine_optimal_personality_mode(active_guests)

        # Check if transition is needed
        if target_mode != current_mode:
            self._transition_personality_mode(target_mode)

    def _determine_optimal_personality_mode(self, guests: List[DetectedGuest]) -> PersonalityMode:
        """Determine optimal personality mode for current guests"""

        # Analyze guest composition
        age_groups = [guest.estimated_age_group for guest in guests]
        emotions = [guest.facial_expression for guest in guests]

        # Priority 1: Safety requirements (children present)
        if any(age in [GuestAgeGroup.TODDLER, GuestAgeGroup.CHILD] for age in age_groups):
            return PersonalityMode.GENTLE_CARETAKER

        # Priority 2: Group size considerations
        if len(guests) > 4:
            return PersonalityMode.PLAYFUL_ENTERTAINER

        # Priority 3: Emotional context
        if any(emotion in [EmotionalExpression.EXCITED, EmotionalExpression.HAPPY] for emotion in emotions):
            return PersonalityMode.EXCITED_FAN_ENCOUNTER

        # Priority 4: Age-based preferences
        if any(age == GuestAgeGroup.SENIOR for age in age_groups):
            return PersonalityMode.LOYAL_COMPANION

        # Default to curious explorer
        return PersonalityMode.CURIOUS_EXPLORER

    def _transition_personality_mode(self, new_mode: PersonalityMode):
        """Transition to a new personality mode"""

        old_mode = self.current_personality_state.current_mode

        # Update personality state
        self.current_personality_state.current_mode = new_mode
        self.current_personality_state.state_start_time = time.time()
        self.current_personality_state.last_state_change = time.time()

        # Apply new personality profile
        if new_mode in self.personality_profiles:
            profile = self.personality_profiles[new_mode]

            # Update emotional state based on new mode
            if profile.emotional_tendencies:
                self.current_personality_state.current_emotion = profile.emotional_tendencies[0]

        # Notify character system of personality change
        if self.character_system:
            self.character_system.set_personality_mode(new_mode.value)

        logger.info(f"Personality transition: {old_mode.value} -> {new_mode.value}")

    def _apply_personality_to_systems(self):
        """Apply current personality to all integrated systems"""

        current_mode = self.current_personality_state.current_mode

        if current_mode in self.personality_profiles:
            profile = self.personality_profiles[current_mode]

            # Apply to character motion system
            if self.character_system:
                # Set motion style parameters based on personality
                pass

            # Apply to audio coordinator
            if self.audio_coordinator:
                # Adjust audio tone and timing based on personality
                pass

    def _get_current_guests(self) -> List[DetectedGuest]:
        """Get current guest data"""

        if self.guest_detection and hasattr(self.guest_detection, 'active_guests'):
            return list(self.guest_detection.active_guests.values())
        else:
            return []

    def _update_guest_relationships(self):
        """Update relationships with current guests"""

        current_guests = self._get_current_guests()
        current_time = time.time()

        for guest in current_guests:
            guest_id = guest.guest_id

            if guest_id in self.guest_relationships:
                # Update existing relationship
                relationship = self.guest_relationships[guest_id]
                relationship.last_interaction = current_time
                relationship.total_interaction_time += 0.5  # Update interval

                # Update familiarity based on interaction time
                familiarity_increase = 0.01  # Per update
                relationship.familiarity_level = min(1.0, relationship.familiarity_level + familiarity_increase)

            else:
                # Create new relationship
                relationship = GuestRelationship(
                    guest_id=guest_id,
                    first_encounter=current_time,
                    guest_characteristics={
                        'age_group': guest.estimated_age_group,
                        'first_emotion': guest.facial_expression,
                        'first_distance': guest.distance
                    }
                )

                self.guest_relationships[guest_id] = relationship

            # Learn guest preferences
            self._learn_guest_preferences(guest, relationship)

    def _learn_guest_preferences(self, guest: DetectedGuest, relationship: GuestRelationship):
        """Learn and adapt to guest preferences"""

        # Track guest's emotional responses to different personality modes
        current_mode = self.current_personality_state.current_mode
        guest_emotion = guest.facial_expression

        # Positive emotional responses indicate preference
        positive_emotions = [EmotionalExpression.HAPPY, EmotionalExpression.EXCITED, EmotionalExpression.DELIGHTED]

        if guest_emotion in positive_emotions:
            relationship.preferred_personality_mode = current_mode
            relationship.positive_interactions += 1

        # Update guest preferences
        relationship.guest_preferences['last_positive_mode'] = current_mode
        relationship.guest_preferences['engagement_level'] = guest.engagement_level

    def _analyze_current_context(self) -> Dict[str, Any]:
        """Analyze current interaction context"""

        current_guests = self._get_current_guests()

        context = {
            'guest_count': len(current_guests),
            'crowd_density': len(current_guests) / 25.0,  # Normalize to 5m radius area
            'average_distance': np.mean([guest.distance for guest in current_guests]) if current_guests else 0.0,
            'age_distribution': self._analyze_age_distribution(current_guests),
            'emotion_distribution': self._analyze_emotion_distribution(current_guests),
            'energy_level': self.current_personality_state.energy_level,
            'social_battery': self.current_personality_state.social_battery,
            'stress_level': self.current_personality_state.stress_level,
            'time_in_current_mode': self.current_personality_state.state_duration
        }

        return context

    def _analyze_age_distribution(self, guests: List[DetectedGuest]) -> Dict[str, float]:
        """Analyze age distribution of current guests"""

        if not guests:
            return {}

        age_counts = {}
        for age_group in GuestAgeGroup:
            count = sum(1 for guest in guests if guest.estimated_age_group == age_group)
            age_counts[age_group.value] = count / len(guests)

        return age_counts

    def _analyze_emotion_distribution(self, guests: List[DetectedGuest]) -> Dict[str, float]:
        """Analyze emotion distribution of current guests"""

        if not guests:
            return {}

        emotion_counts = {}
        for emotion in EmotionalExpression:
            count = sum(1 for guest in guests if guest.facial_expression == emotion)
            emotion_counts[emotion.value] = count / len(guests)

        return emotion_counts

    def _determine_optimal_adaptation(self, context: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Determine optimal personality adaptation for current context"""

        adaptations = {}

        # Check if current mode is appropriate
        current_mode = self.current_personality_state.current_mode

        # Age-based adaptations
        age_dist = context.get('age_distribution', {})
        dominant_age = max(age_dist.items(), key=lambda x: x[1])[0] if age_dist else None

        if dominant_age:
            age_adaptation = self.adaptation_rules['age_adaptations'].get(GuestAgeGroup(dominant_age))
            if age_adaptation:
                adaptations.update(age_adaptation)

        # Stress-based adaptations
        if context['stress_level'] > 0.7:
            adaptations['mode_override'] = PersonalityMode.PROTECTIVE_GUARDIAN
            adaptations['intensity_modifier'] = 0.7

        # Social battery adaptations
        if context['social_battery'] < 0.3:
            adaptations['intensity_modifier'] = 0.8
            adaptations['interaction_limitation'] = True

        return adaptations if adaptations else None

    def _apply_personality_adaptation(self, adaptation: Dict[str, Any]):
        """Apply personality adaptation"""

        # Mode override
        if 'mode_override' in adaptation:
            self._transition_personality_mode(adaptation['mode_override'])

        # Intensity modifications
        if 'intensity_modifier' in adaptation:
            modifier = adaptation['intensity_modifier']
            current_intensity = self.current_personality_state.current_intensity

            # Apply intensity modification
            new_intensity_value = current_intensity.value * modifier

            # Map to closest intensity enum
            if new_intensity_value <= 0.4:
                self.current_personality_state.current_intensity = PersonalityIntensity.SUBTLE
            elif new_intensity_value <= 0.7:
                self.current_personality_state.current_intensity = PersonalityIntensity.MODERATE
            elif new_intensity_value <= 1.0:
                self.current_personality_state.current_intensity = PersonalityIntensity.PRONOUNCED
            else:
                self.current_personality_state.current_intensity = PersonalityIntensity.DRAMATIC

    def _monitor_adaptation_effectiveness(self):
        """Monitor effectiveness of personality adaptations"""

        current_guests = self._get_current_guests()

        if current_guests:
            # Calculate average guest engagement
            avg_engagement = np.mean([guest.engagement_level for guest in current_guests])

            # Update adaptation accuracy metric
            self.engagement_metrics['adaptation_accuracy'] = avg_engagement

    def _update_personality_metrics(self):
        """Update personality system metrics"""

        current_guests = self._get_current_guests()

        if current_guests:
            # Update guest satisfaction estimate
            avg_engagement = np.mean([guest.engagement_level for guest in current_guests])
            self.engagement_metrics['guest_satisfaction_estimate'] = avg_engagement

        # Update interaction count
        self.engagement_metrics['total_interactions'] += len(current_guests)

        # Calculate personality consistency score
        consistency_factors = [
            self.current_personality_state.energy_level,
            1.0 - self.current_personality_state.stress_level,
            self.current_personality_state.confidence_level
        ]
        self.engagement_metrics['personality_consistency_score'] = np.mean(consistency_factors)

    def _update_relationship_metrics(self):
        """Update relationship management metrics"""

        total_relationships = len(self.guest_relationships)
        if total_relationships > 0:
            # Calculate relationship retention rate
            active_relationships = sum(
                1 for rel in self.guest_relationships.values()
                if (time.time() - rel.last_interaction) < 3600.0  # 1 hour
            )
            self.engagement_metrics['relationship_retention_rate'] = active_relationships / total_relationships

    def set_personality_mode(self, mode: PersonalityMode, intensity: Optional[PersonalityIntensity] = None):
        """Manually set personality mode"""

        self._transition_personality_mode(mode)

        if intensity:
            self.current_personality_state.current_intensity = intensity

        logger.info(f"Personality manually set to: {mode.value}")

    def get_personality_status_report(self) -> Dict[str, Any]:
        """Get comprehensive personality status report"""

        current_state = self.current_personality_state

        return {
            'system_status': 'ACTIVE' if self.is_active else 'INACTIVE',
            'current_personality': {
                'mode': current_state.current_mode.value,
                'intensity': current_state.current_intensity.value,
                'emotion': current_state.current_emotion.value,
                'energy_level': current_state.energy_level,
                'social_battery': current_state.social_battery,
                'stress_level': current_state.stress_level,
                'confidence_level': current_state.confidence_level
            },
            'engagement_metrics': self.engagement_metrics.copy(),
            'active_relationships': len(self.guest_relationships),
            'personality_profiles_available': len(self.personality_profiles),
            'adaptation_rules_configured': len(self.adaptation_rules),
            'context_modifiers_active': len(self.context_modifiers),
            'disney_configuration': self.disney_config.copy()
        }

# Example usage and testing functions
def create_demo_personality_system():
    """Create demo personality system for testing"""

    personality_system = R2D2PersonalityEngagementSystem()
    return personality_system

def demo_personality_engagement():
    """Demonstrate personality engagement"""

    personality_system = create_demo_personality_system()

    print("Starting R2D2 Personality Engagement System...")
    success = personality_system.start_personality_system()

    if success:
        print("Personality system started successfully")

        # Test personality transitions
        personality_system.set_personality_mode(PersonalityMode.PLAYFUL_ENTERTAINER)
        time.sleep(3.0)

        personality_system.set_personality_mode(PersonalityMode.CURIOUS_EXPLORER)
        time.sleep(3.0)

        # Generate status report
        report = personality_system.get_personality_status_report()
        print("\n--- Personality Status Report ---")
        print(json.dumps(report, indent=2))

        # Stop the system
        personality_system.stop_personality_system()
        print("Personality system stopped")

    else:
        print("Failed to start personality system")

if __name__ == "__main__":
    # Run demonstration
    demo_personality_engagement()