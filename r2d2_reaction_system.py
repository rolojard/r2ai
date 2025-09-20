"""
R2-D2 Reaction System for Character Recognition
==============================================

Advanced behavioral reaction system that translates character recognition
into authentic R2-D2 responses based on Star Wars canon relationships.

This system provides:
- Character-specific reaction patterns
- Emotional state management
- Behavioral sequence generation
- Sound pattern synthesis
- Context-aware responses
"""

import random
import time
from enum import Enum
from dataclasses import dataclass
from typing import List, Dict, Optional, Tuple
from star_wars_character_database_schema import EmotionalResponse, RelationshipType, StarWarsCharacter


class BehaviorIntensity(Enum):
    """Intensity levels for R2-D2 behavioral responses"""
    SUBTLE = "subtle"           # Minimal response, brief acknowledgment
    MODERATE = "moderate"       # Standard response level
    ENTHUSIASTIC = "enthusiastic"  # High energy, extended response
    DRAMATIC = "dramatic"       # Maximum response, full sequence


class BehaviorType(Enum):
    """Types of physical behaviors R2-D2 can exhibit"""
    DOME_ROTATION = "dome_rotation"     # Head turning/spinning
    BODY_ROCK = "body_rock"             # Forward/backward rocking
    PERISCOPE_EXTEND = "periscope_extend"  # Extending periscope
    PANEL_OPEN = "panel_open"           # Opening utility panels
    ARM_EXTEND = "arm_extend"           # Extending utility arms
    HOLOGRAM_PROJECT = "hologram_project"  # Projecting holograms
    SHOCK_PROD = "shock_prod"           # Electrical shock (for C-3PO)
    THRUSTER_FIRE = "thruster_fire"     # Using rocket thrusters
    LED_FLASH = "led_flash"             # Flashing indicator lights


@dataclass
class BehaviorSequence:
    """A sequence of physical behaviors for R2-D2"""
    behaviors: List[BehaviorType]
    timing: List[float]  # Duration for each behavior in seconds
    intensity: BehaviorIntensity
    description: str
    total_duration: float


@dataclass
class SoundPattern:
    """Detailed sound pattern specification"""
    primary_emotion: EmotionalResponse
    sound_sequence: List[str]  # Sequence of specific sounds
    timing: List[float]  # Duration of each sound
    pitch_pattern: List[str]  # High, medium, low for each sound
    volume_pattern: List[str]  # Loud, medium, soft for each sound
    total_duration: float
    description: str


@dataclass
class R2D2ReactionSequence:
    """Complete reaction sequence combining sounds and behaviors"""
    character_name: str
    relationship_type: RelationshipType
    confidence_level: float
    sound_pattern: SoundPattern
    behavior_sequence: BehaviorSequence
    contextual_notes: str
    trigger_conditions: List[str]


class R2D2ReactionEngine:
    """Main engine for generating R2-D2 reactions to character recognition"""

    def __init__(self):
        self.sound_library = self._initialize_sound_library()
        self.behavior_library = self._initialize_behavior_library()
        self.reaction_memory = {}  # Store recent reactions to avoid repetition
        self.emotional_state = EmotionalResponse.MECHANICAL_NEUTRAL
        self.last_reaction_time = 0
        self.energy_level = 1.0  # Affects reaction intensity

    def _initialize_sound_library(self) -> Dict[EmotionalResponse, Dict]:
        """Initialize detailed sound patterns for each emotional response"""
        return {
            EmotionalResponse.EXCITED_BEEPS: {
                "variants": [
                    {
                        "sequence": ["rising_whistle", "rapid_beeps", "happy_chirp", "confirmation_beep"],
                        "timing": [0.8, 1.2, 0.6, 0.4],
                        "pitch": ["medium_to_high", "high", "high", "medium"],
                        "volume": ["medium", "loud", "medium", "soft"],
                        "description": "Classic excitement pattern for close friends"
                    },
                    {
                        "sequence": ["enthusiastic_warble", "ascending_beeps", "playful_trill"],
                        "timing": [1.0, 1.5, 1.0],
                        "pitch": ["medium", "low_to_high", "medium_to_high"],
                        "volume": ["loud", "loud", "medium"],
                        "description": "Extended excitement for very close relationships"
                    },
                    {
                        "sequence": ["surprised_squeak", "happy_whistle", "confirmation_chirp"],
                        "timing": [0.3, 1.2, 0.5],
                        "pitch": ["high", "medium_to_high", "medium"],
                        "volume": ["medium", "loud", "soft"],
                        "description": "Surprised excitement for unexpected encounters"
                    }
                ]
            },
            EmotionalResponse.AFFECTIONATE_WHISTLES: {
                "variants": [
                    {
                        "sequence": ["gentle_whistle", "caring_warble", "soft_beep"],
                        "timing": [1.5, 2.0, 0.5],
                        "pitch": ["medium", "medium", "low"],
                        "volume": ["soft", "medium", "soft"],
                        "description": "Tender recognition for beloved friends"
                    },
                    {
                        "sequence": ["melodic_trill", "warm_whistle", "content_hum"],
                        "timing": [1.8, 1.2, 1.0],
                        "pitch": ["medium_to_high", "medium", "low"],
                        "volume": ["medium", "soft", "very_soft"],
                        "description": "Deep affection for family-like relationships"
                    }
                ]
            },
            EmotionalResponse.WORRIED_WARBLES: {
                "variants": [
                    {
                        "sequence": ["concerned_warble", "anxious_beep", "questioning_chirp"],
                        "timing": [2.0, 1.0, 0.8],
                        "pitch": ["medium_fluctuating", "medium", "medium_to_high"],
                        "volume": ["medium", "soft", "medium"],
                        "description": "Standard worry pattern for concerning situations"
                    },
                    {
                        "sequence": ["distressed_warble", "nervous_trill", "uncertain_beep", "worried_sigh"],
                        "timing": [2.5, 1.5, 0.8, 1.2],
                        "pitch": ["low_to_medium", "medium_fluctuating", "medium", "low"],
                        "volume": ["loud", "medium", "soft", "very_soft"],
                        "description": "Deep concern for complex emotional situations"
                    }
                ]
            },
            EmotionalResponse.CAUTIOUS_CHIRPS: {
                "variants": [
                    {
                        "sequence": ["hesitant_chirp", "questioning_beep", "uncertain_warble"],
                        "timing": [0.8, 1.0, 1.5],
                        "pitch": ["medium", "medium_to_high", "medium"],
                        "volume": ["soft", "medium", "soft"],
                        "description": "Careful assessment of unknown individuals"
                    }
                ]
            },
            EmotionalResponse.ANGRY_BUZZES: {
                "variants": [
                    {
                        "sequence": ["frustrated_buzz", "angry_beep", "indignant_raspberry"],
                        "timing": [1.0, 0.5, 1.5],
                        "pitch": ["low", "medium", "low_to_medium"],
                        "volume": ["loud", "loud", "loud"],
                        "description": "Standard frustration pattern"
                    },
                    {
                        "sequence": ["electronic_raspberry", "harsh_buzz", "dismissive_beep"],
                        "timing": [2.0, 1.0, 0.5],
                        "pitch": ["low", "low", "medium"],
                        "volume": ["very_loud", "loud", "medium"],
                        "description": "Intense anger and dismissal"
                    }
                ]
            },
            EmotionalResponse.BINARY_PROFANITY: {
                "variants": [
                    {
                        "sequence": ["harsh_static", "rapid_angry_beeps", "electronic_curse"],
                        "timing": [0.8, 1.5, 1.2],
                        "pitch": ["low", "medium", "low_to_medium"],
                        "volume": ["loud", "very_loud", "loud"],
                        "description": "R2-D2's famous binary swearing"
                    }
                ]
            },
            EmotionalResponse.WARNING_ALARMS: {
                "variants": [
                    {
                        "sequence": ["danger_beep", "urgent_warble", "alarm_repeat"],
                        "timing": [0.3, 0.7, 2.0],
                        "pitch": ["high", "high", "high"],
                        "volume": ["very_loud", "loud", "loud"],
                        "description": "Immediate danger warning"
                    }
                ]
            },
            EmotionalResponse.PLAYFUL_TRILLS: {
                "variants": [
                    {
                        "sequence": ["mischievous_trill", "playful_beep", "amused_warble"],
                        "timing": [1.2, 0.8, 1.5],
                        "pitch": ["medium_to_high", "high", "medium"],
                        "volume": ["medium", "medium", "soft"],
                        "description": "Playful interaction pattern"
                    }
                ]
            },
            EmotionalResponse.SURPRISED_SQUEAKS: {
                "variants": [
                    {
                        "sequence": ["startled_squeak", "surprise_beep"],
                        "timing": [0.3, 0.7],
                        "pitch": ["very_high", "high"],
                        "volume": ["loud", "medium"],
                        "description": "Sudden surprise reaction"
                    }
                ]
            },
            EmotionalResponse.MECHANICAL_NEUTRAL: {
                "variants": [
                    {
                        "sequence": ["acknowledgment_beep"],
                        "timing": [0.5],
                        "pitch": ["medium"],
                        "volume": ["medium"],
                        "description": "Standard neutral acknowledgment"
                    }
                ]
            }
        }

    def _initialize_behavior_library(self) -> Dict[EmotionalResponse, List[BehaviorSequence]]:
        """Initialize physical behavior patterns for each emotional response"""
        return {
            EmotionalResponse.EXCITED_BEEPS: [
                BehaviorSequence(
                    behaviors=[BehaviorType.DOME_ROTATION, BehaviorType.BODY_ROCK, BehaviorType.PERISCOPE_EXTEND],
                    timing=[1.0, 2.0, 1.5],
                    intensity=BehaviorIntensity.ENTHUSIASTIC,
                    description="Excited recognition with full body animation",
                    total_duration=4.5
                ),
                BehaviorSequence(
                    behaviors=[BehaviorType.DOME_ROTATION, BehaviorType.LED_FLASH, BehaviorType.PANEL_OPEN],
                    timing=[2.0, 1.0, 1.5],
                    intensity=BehaviorIntensity.DRAMATIC,
                    description="Maximum excitement with light show",
                    total_duration=4.5
                )
            ],
            EmotionalResponse.AFFECTIONATE_WHISTLES: [
                BehaviorSequence(
                    behaviors=[BehaviorType.DOME_ROTATION, BehaviorType.GENTLE_SWAY],
                    timing=[2.0, 3.0],
                    intensity=BehaviorIntensity.MODERATE,
                    description="Gentle, caring acknowledgment",
                    total_duration=5.0
                )
            ],
            EmotionalResponse.WORRIED_WARBLES: [
                BehaviorSequence(
                    behaviors=[BehaviorType.BODY_ROCK, BehaviorType.DOME_ROTATION, BehaviorType.PERISCOPE_EXTEND],
                    timing=[3.0, 1.5, 2.0],
                    intensity=BehaviorIntensity.MODERATE,
                    description="Nervous fidgeting and scanning",
                    total_duration=6.5
                )
            ],
            EmotionalResponse.CAUTIOUS_CHIRPS: [
                BehaviorSequence(
                    behaviors=[BehaviorType.DOME_ROTATION, BehaviorType.PERISCOPE_EXTEND],
                    timing=[1.5, 2.0],
                    intensity=BehaviorIntensity.SUBTLE,
                    description="Careful observation and assessment",
                    total_duration=3.5
                )
            ],
            EmotionalResponse.ANGRY_BUZZES: [
                BehaviorSequence(
                    behaviors=[BehaviorType.BODY_ROCK, BehaviorType.DOME_ROTATION, BehaviorType.PANEL_OPEN],
                    timing=[1.5, 1.0, 1.0],
                    intensity=BehaviorIntensity.DRAMATIC,
                    description="Frustrated agitation with aggressive movements",
                    total_duration=3.5
                )
            ],
            EmotionalResponse.BINARY_PROFANITY: [
                BehaviorSequence(
                    behaviors=[BehaviorType.SHOCK_PROD, BehaviorType.DOME_ROTATION, BehaviorType.ANGRY_WIGGLE],
                    timing=[0.5, 2.0, 1.0],
                    intensity=BehaviorIntensity.DRAMATIC,
                    description="Aggressive response with shock prod (for C-3PO)",
                    total_duration=3.5
                )
            ],
            EmotionalResponse.WARNING_ALARMS: [
                BehaviorSequence(
                    behaviors=[BehaviorType.LED_FLASH, BehaviorType.DOME_ROTATION, BehaviorType.BODY_ROCK],
                    timing=[2.0, 1.0, 1.0],
                    intensity=BehaviorIntensity.DRAMATIC,
                    description="Full alert mode with flashing lights",
                    total_duration=4.0
                )
            ],
            EmotionalResponse.PLAYFUL_TRILLS: [
                BehaviorSequence(
                    behaviors=[BehaviorType.DOME_ROTATION, BehaviorType.PLAYFUL_WIGGLE, BehaviorType.PANEL_OPEN],
                    timing=[1.5, 2.0, 1.0],
                    intensity=BehaviorIntensity.MODERATE,
                    description="Mischievous and playful movements",
                    total_duration=4.5
                )
            ],
            EmotionalResponse.SURPRISED_SQUEAKS: [
                BehaviorSequence(
                    behaviors=[BehaviorType.STARTLED_JUMP, BehaviorType.DOME_ROTATION],
                    timing=[0.5, 1.0],
                    intensity=BehaviorIntensity.DRAMATIC,
                    description="Startled reaction with quick recovery",
                    total_duration=1.5
                )
            ],
            EmotionalResponse.MECHANICAL_NEUTRAL: [
                BehaviorSequence(
                    behaviors=[BehaviorType.DOME_ROTATION],
                    timing=[1.0],
                    intensity=BehaviorIntensity.SUBTLE,
                    description="Simple acknowledgment turn",
                    total_duration=1.0
                )
            ]
        }

    def generate_reaction(self, character: StarWarsCharacter, confidence: float,
                         context: Optional[str] = None) -> R2D2ReactionSequence:
        """Generate a complete reaction sequence for a recognized character"""

        # Determine reaction intensity based on relationship and confidence
        intensity = self._calculate_reaction_intensity(character, confidence)

        # Select appropriate sound pattern
        sound_pattern = self._select_sound_pattern(character.r2d2_reaction.primary_emotion, intensity)

        # Select appropriate behavior sequence
        behavior_sequence = self._select_behavior_sequence(character.r2d2_reaction.primary_emotion, intensity)

        # Create contextual modifications
        contextual_notes = self._generate_contextual_notes(character, confidence, context)

        # Define trigger conditions
        trigger_conditions = self._get_trigger_conditions(character)

        reaction = R2D2ReactionSequence(
            character_name=character.name,
            relationship_type=character.relationship_to_r2d2,
            confidence_level=confidence,
            sound_pattern=sound_pattern,
            behavior_sequence=behavior_sequence,
            contextual_notes=contextual_notes,
            trigger_conditions=trigger_conditions
        )

        # Update emotional state and memory
        self._update_emotional_state(character.r2d2_reaction.primary_emotion)
        self._record_reaction(character.name, reaction)

        return reaction

    def _calculate_reaction_intensity(self, character: StarWarsCharacter, confidence: float) -> BehaviorIntensity:
        """Calculate reaction intensity based on relationship strength and confidence"""
        base_intensity = 0.5

        # Relationship modifier
        relationship_modifiers = {
            RelationshipType.CLOSE_FRIEND: 1.0,
            RelationshipType.FELLOW_DROID: 0.9,
            RelationshipType.FAMILY_FRIEND: 0.9,
            RelationshipType.TRUSTED_ALLY: 0.7,
            RelationshipType.RESPECTED_LEADER: 0.6,
            RelationshipType.FORMER_ENEMY: 0.4,
            RelationshipType.NEUTRAL: 0.3,
            RelationshipType.ENEMY: 0.2
        }

        # Calculate final intensity
        intensity_score = (base_intensity +
                          relationship_modifiers.get(character.relationship_to_r2d2, 0.3) +
                          confidence * 0.3 +
                          character.trust_level / 10 * 0.2) * self.energy_level

        # Map to intensity enum
        if intensity_score >= 0.8:
            return BehaviorIntensity.DRAMATIC
        elif intensity_score >= 0.6:
            return BehaviorIntensity.ENTHUSIASTIC
        elif intensity_score >= 0.4:
            return BehaviorIntensity.MODERATE
        else:
            return BehaviorIntensity.SUBTLE

    def _select_sound_pattern(self, emotion: EmotionalResponse, intensity: BehaviorIntensity) -> SoundPattern:
        """Select appropriate sound pattern based on emotion and intensity"""
        emotion_sounds = self.sound_library.get(emotion, self.sound_library[EmotionalResponse.MECHANICAL_NEUTRAL])
        variants = emotion_sounds["variants"]

        # Select variant based on intensity
        if intensity == BehaviorIntensity.DRAMATIC and len(variants) > 1:
            selected_variant = variants[-1]  # Most dramatic variant
        elif intensity == BehaviorIntensity.SUBTLE:
            selected_variant = variants[0]   # Simplest variant
        else:
            selected_variant = random.choice(variants)  # Random selection for variety

        return SoundPattern(
            primary_emotion=emotion,
            sound_sequence=selected_variant["sequence"],
            timing=selected_variant["timing"],
            pitch_pattern=selected_variant["pitch"],
            volume_pattern=selected_variant["volume"],
            total_duration=sum(selected_variant["timing"]),
            description=selected_variant["description"]
        )

    def _select_behavior_sequence(self, emotion: EmotionalResponse, intensity: BehaviorIntensity) -> BehaviorSequence:
        """Select appropriate behavior sequence based on emotion and intensity"""
        emotion_behaviors = self.behavior_library.get(emotion, self.behavior_library[EmotionalResponse.MECHANICAL_NEUTRAL])

        # Filter by intensity
        suitable_behaviors = [b for b in emotion_behaviors if b.intensity == intensity]
        if not suitable_behaviors:
            suitable_behaviors = emotion_behaviors  # Fallback to any available

        return random.choice(suitable_behaviors)

    def _generate_contextual_notes(self, character: StarWarsCharacter, confidence: float,
                                  context: Optional[str]) -> str:
        """Generate contextual notes for the reaction"""
        notes = []

        # Confidence-based notes
        if confidence >= 0.9:
            notes.append("High confidence recognition - full reaction sequence")
        elif confidence >= 0.7:
            notes.append("Standard recognition confidence")
        else:
            notes.append("Lower confidence - subdued reaction")

        # Relationship-based notes
        if character.relationship_to_r2d2 == RelationshipType.CLOSE_FRIEND:
            notes.append("Maximum enthusiasm for close friend")
        elif character.relationship_to_r2d2 == RelationshipType.FORMER_ENEMY:
            notes.append("Conflicted emotions - recognition but caution")

        # Context-specific notes
        if context:
            notes.append(f"Context: {context}")

        # Memory-based notes
        if character.name in self.reaction_memory:
            last_reaction = self.reaction_memory[character.name]
            time_since = time.time() - last_reaction.get('timestamp', 0)
            if time_since < 300:  # 5 minutes
                notes.append("Recent interaction - may show continued familiarity")

        return "; ".join(notes)

    def _get_trigger_conditions(self, character: StarWarsCharacter) -> List[str]:
        """Define conditions that trigger specific reactions"""
        conditions = ["Face recognition above confidence threshold"]

        # Character-specific triggers
        if character.name == "Luke Skywalker":
            conditions.extend(["Lightsaber ignition sound", "Force-sensitive presence"])
        elif character.name == "C-3PO":
            conditions.extend(["Protocol droid vocal patterns", "Golden plating reflection"])
        elif character.name == "Darth Vader":
            conditions.extend(["Mechanical breathing sounds", "Dark side presence"])
        elif character.name == "Leia Organa":
            conditions.extend(["Royal bearing detection", "Leadership voice patterns"])

        # Faction-based triggers
        if character.faction.value in ["jedi", "sith"]:
            conditions.append("Force presence detection")
        elif character.faction.value == "droid":
            conditions.append("Droid communication protocols")

        return conditions

    def _update_emotional_state(self, new_emotion: EmotionalResponse):
        """Update R2-D2's current emotional state"""
        self.emotional_state = new_emotion
        self.last_reaction_time = time.time()

        # Adjust energy level based on emotion
        if new_emotion in [EmotionalResponse.EXCITED_BEEPS, EmotionalResponse.PLAYFUL_TRILLS]:
            self.energy_level = min(1.2, self.energy_level + 0.1)
        elif new_emotion in [EmotionalResponse.WORRIED_WARBLES, EmotionalResponse.ANGRY_BUZZES]:
            self.energy_level = max(0.8, self.energy_level - 0.1)

    def _record_reaction(self, character_name: str, reaction: R2D2ReactionSequence):
        """Record reaction in memory for context"""
        self.reaction_memory[character_name] = {
            'reaction': reaction,
            'timestamp': time.time(),
            'count': self.reaction_memory.get(character_name, {}).get('count', 0) + 1
        }

    def get_reaction_summary(self, reaction: R2D2ReactionSequence) -> str:
        """Generate human-readable summary of reaction"""
        summary = f"""R2-D2 Reaction to {reaction.character_name}:

RELATIONSHIP: {reaction.relationship_type.value.replace('_', ' ').title()}
CONFIDENCE: {reaction.confidence_level:.2f}

SOUND PATTERN:
- Primary Emotion: {reaction.sound_pattern.primary_emotion.value.replace('_', ' ').title()}
- Duration: {reaction.sound_pattern.total_duration:.1f} seconds
- Description: {reaction.sound_pattern.description}
- Sequence: {' → '.join(reaction.sound_pattern.sound_sequence)}

BEHAVIOR SEQUENCE:
- Intensity: {reaction.behavior_sequence.intensity.value.title()}
- Duration: {reaction.behavior_sequence.total_duration:.1f} seconds
- Description: {reaction.behavior_sequence.description}
- Behaviors: {' → '.join([b.value.replace('_', ' ').title() for b in reaction.behavior_sequence.behaviors])}

CONTEXT: {reaction.contextual_notes}

TRIGGERS: {', '.join(reaction.trigger_conditions)}
"""
        return summary


def create_character_specific_reactions():
    """Create specialized reaction patterns for key characters"""
    special_reactions = {
        "Luke Skywalker": {
            "reunion_after_separation": {
                "sound_override": "extended_excited_sequence_with_relief",
                "behavior_override": "full_body_celebration_with_periscope_extension",
                "duration_multiplier": 1.5,
                "notes": "Special reunion sequence when Luke returns after absence"
            },
            "in_danger": {
                "sound_override": "worried_protective_sequence",
                "behavior_override": "urgent_warning_with_positioning",
                "notes": "Protective mode when Luke is threatened"
            }
        },
        "C-3PO": {
            "argument_mode": {
                "sound_override": "binary_profanity_sequence",
                "behavior_override": "shock_prod_threat_display",
                "notes": "Classic argument pattern with threat of shocking"
            },
            "affectionate_moment": {
                "sound_override": "gentle_droid_communication",
                "behavior_override": "synchronized_movement",
                "notes": "Rare moments of droid harmony"
            }
        },
        "Darth Vader": {
            "recognition_conflict": {
                "sound_override": "conflicted_warble_sequence",
                "behavior_override": "hesitant_approach_with_caution",
                "notes": "Internal conflict between fear of Vader and recognition of Anakin"
            }
        }
    }
    return special_reactions


if __name__ == "__main__":
    # Example usage
    from star_wars_character_database import create_star_wars_character_database

    # Initialize system
    db = create_star_wars_character_database()
    reaction_engine = R2D2ReactionEngine()

    # Test reactions for key characters
    test_characters = ["Luke Skywalker", "C-3PO", "Darth Vader", "Rey"]

    print("R2-D2 Character Recognition Reaction Tests")
    print("=" * 50)

    for char_name in test_characters:
        character = db.get_character(char_name)
        if character:
            confidence = 0.85  # High confidence recognition
            reaction = reaction_engine.generate_reaction(character, confidence)
            print(reaction_engine.get_reaction_summary(reaction))
            print("-" * 50)