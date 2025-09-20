"""
Star Wars Character Recognition Database Schema for R2-D2
========================================================

This module defines the database schema for Star Wars character recognition
specifically designed for R2-D2's canonical relationships and behavioral responses.

Based on comprehensive Star Wars canon research including:
- Original Trilogy (1977-1983)
- Prequel Trilogy (1999-2005)
- Sequel Trilogy (2015-2019)
- The Clone Wars, Rebels, and other canon media
"""

from enum import Enum
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Set
import json


class FactionAlignment(Enum):
    """Faction alignments based on Star Wars canon"""
    JEDI = "jedi"
    SITH = "sith"
    REBEL_ALLIANCE = "rebel_alliance"
    RESISTANCE = "resistance"
    GALACTIC_EMPIRE = "galactic_empire"
    FIRST_ORDER = "first_order"
    GALACTIC_REPUBLIC = "galactic_republic"
    SEPARATIST = "separatist"
    MANDALORIAN = "mandalorian"
    BOUNTY_HUNTER = "bounty_hunter"
    SMUGGLER = "smuggler"
    CIVILIAN = "civilian"
    NEUTRAL = "neutral"
    DROID = "droid"


class RelationshipType(Enum):
    """R2-D2's relationship types based on canon interactions"""
    CLOSE_FRIEND = "close_friend"          # Luke, Leia, C-3PO
    TRUSTED_ALLY = "trusted_ally"          # Anakin, Padmé, Obi-Wan
    FELLOW_DROID = "fellow_droid"          # C-3PO, BB-8, other astromechs
    RESPECTED_LEADER = "respected_leader"   # Qui-Gon, Mace Windu, Ahsoka
    FORMER_ENEMY = "former_enemy"          # Vader (complex relationship)
    ENEMY = "enemy"                        # Imperial officers, Sith
    NEUTRAL = "neutral"                    # Unknown characters
    FAMILY_FRIEND = "family_friend"        # Skywalker/Organa family


class EmotionalResponse(Enum):
    """R2-D2's emotional response patterns based on canon behavior"""
    EXCITED_BEEPS = "excited_beeps"                    # Happy, enthusiastic sounds
    WORRIED_WARBLES = "worried_warbles"                # Concerned, anxious sounds
    ANGRY_BUZZES = "angry_buzzes"                      # Frustrated, annoyed sounds
    CAUTIOUS_CHIRPS = "cautious_chirps"                # Careful, uncertain sounds
    AFFECTIONATE_WHISTLES = "affectionate_whistles"    # Loving, gentle sounds
    WARNING_ALARMS = "warning_alarms"                  # Danger, alert sounds
    SURPRISED_SQUEAKS = "surprised_squeaks"            # Shock, surprise sounds
    PLAYFUL_TRILLS = "playful_trills"                  # Mischievous, fun sounds
    BINARY_PROFANITY = "binary_profanity"              # Foul language (canon confirmed)
    MECHANICAL_NEUTRAL = "mechanical_neutral"          # Standard acknowledgment
    RESPECTFUL_ACKNOWLEDGMENT = "respectful_acknowledgment"  # Formal respect


@dataclass
class VisualDescriptor:
    """Visual characteristics for character recognition"""
    primary_outfit: str
    distinctive_features: List[str]
    height_range: tuple  # (min_cm, max_cm)
    hair_color: Optional[str] = None
    eye_color: Optional[str] = None
    species: str = "human"
    notable_accessories: List[str] = field(default_factory=list)
    costume_variations: List[str] = field(default_factory=list)


@dataclass
class R2D2Reaction:
    """R2-D2's specific reaction to a character"""
    primary_emotion: EmotionalResponse
    secondary_emotions: List[EmotionalResponse] = field(default_factory=list)
    sound_pattern: str = ""  # Description of beep/whistle pattern
    behavioral_notes: str = ""  # Additional behavioral context
    confidence_modifier: float = 1.0  # Multiplier for recognition confidence


@dataclass
class CharacterTimeline:
    """Timeline information for character recognition across different eras"""
    prequel_era: bool = False  # Episodes I-III, Clone Wars
    original_era: bool = False  # Episodes IV-VI
    sequel_era: bool = False   # Episodes VII-IX
    standalone_era: bool = False  # Rogue One, Solo, etc.
    tv_series: List[str] = field(default_factory=list)  # Specific TV appearances


@dataclass
class StarWarsCharacter:
    """Complete Star Wars character profile for R2-D2 recognition system"""

    # Basic Identity (required fields first)
    name: str
    faction: FactionAlignment
    relationship_to_r2d2: RelationshipType
    r2d2_reaction: R2D2Reaction
    visual_descriptor: VisualDescriptor
    timeline: CharacterTimeline

    # Optional fields with defaults
    aliases: List[str] = field(default_factory=list)
    full_name: Optional[str] = None
    titles: List[str] = field(default_factory=list)
    species: str = "human"
    homeworld: Optional[str] = None
    trust_level: int = 5  # 1-10 scale (1=enemy, 10=closest friend)
    first_meeting_context: Optional[str] = None
    last_known_interaction: Optional[str] = None

    # Technical Recognition Data
    recognition_priority: int = 5  # 1-10 scale for processing priority
    confidence_threshold: float = 0.75  # Minimum confidence for positive ID
    false_positive_risk: float = 0.1  # Risk of misidentification

    # Metadata
    canon_status: str = "canon"  # canon, legends, expanded_universe
    last_updated: Optional[str] = None
    notes: str = ""


class CharacterDatabase:
    """Main database class for Star Wars character recognition"""

    def __init__(self):
        self.characters: Dict[str, StarWarsCharacter] = {}
        self.faction_groups: Dict[FactionAlignment, List[str]] = {}
        self.relationship_groups: Dict[RelationshipType, List[str]] = {}
        self.timeline_index: Dict[str, List[str]] = {}

    def add_character(self, character: StarWarsCharacter) -> None:
        """Add a character to the database with automatic indexing"""
        self.characters[character.name] = character

        # Update faction index
        if character.faction not in self.faction_groups:
            self.faction_groups[character.faction] = []
        self.faction_groups[character.faction].append(character.name)

        # Update relationship index
        if character.relationship_to_r2d2 not in self.relationship_groups:
            self.relationship_groups[character.relationship_to_r2d2] = []
        self.relationship_groups[character.relationship_to_r2d2].append(character.name)

        # Update timeline index
        timeline_periods = []
        if character.timeline.prequel_era:
            timeline_periods.append("prequel")
        if character.timeline.original_era:
            timeline_periods.append("original")
        if character.timeline.sequel_era:
            timeline_periods.append("sequel")
        if character.timeline.standalone_era:
            timeline_periods.append("standalone")

        for period in timeline_periods:
            if period not in self.timeline_index:
                self.timeline_index[period] = []
            self.timeline_index[period].append(character.name)

    def get_character(self, name: str) -> Optional[StarWarsCharacter]:
        """Retrieve a character by name or alias"""
        # Direct name match
        if name in self.characters:
            return self.characters[name]

        # Search aliases
        for character in self.characters.values():
            if name in character.aliases:
                return character

        return None

    def get_characters_by_faction(self, faction: FactionAlignment) -> List[StarWarsCharacter]:
        """Get all characters from a specific faction"""
        if faction in self.faction_groups:
            return [self.characters[name] for name in self.faction_groups[faction]]
        return []

    def get_characters_by_relationship(self, relationship: RelationshipType) -> List[StarWarsCharacter]:
        """Get all characters with a specific relationship to R2-D2"""
        if relationship in self.relationship_groups:
            return [self.characters[name] for name in self.relationship_groups[relationship]]
        return []

    def get_characters_by_timeline(self, era: str) -> List[StarWarsCharacter]:
        """Get all characters from a specific timeline era"""
        if era in self.timeline_index:
            return [self.characters[name] for name in self.timeline_index[era]]
        return []

    def get_high_priority_characters(self, min_priority: int = 7) -> List[StarWarsCharacter]:
        """Get characters with high recognition priority"""
        return [char for char in self.characters.values()
                if char.recognition_priority >= min_priority]

    def export_to_json(self, filepath: str) -> None:
        """Export database to JSON format"""
        export_data = {}
        for name, character in self.characters.items():
            export_data[name] = {
                'name': character.name,
                'aliases': character.aliases,
                'full_name': character.full_name,
                'titles': character.titles,
                'faction': character.faction.value,
                'species': character.species,
                'homeworld': character.homeworld,
                'relationship_to_r2d2': character.relationship_to_r2d2.value,
                'trust_level': character.trust_level,
                'recognition_priority': character.recognition_priority,
                'confidence_threshold': character.confidence_threshold,
                'r2d2_reaction': {
                    'primary_emotion': character.r2d2_reaction.primary_emotion.value,
                    'secondary_emotions': [e.value for e in character.r2d2_reaction.secondary_emotions],
                    'sound_pattern': character.r2d2_reaction.sound_pattern,
                    'behavioral_notes': character.r2d2_reaction.behavioral_notes,
                    'confidence_modifier': character.r2d2_reaction.confidence_modifier
                },
                'visual_descriptor': {
                    'primary_outfit': character.visual_descriptor.primary_outfit,
                    'distinctive_features': character.visual_descriptor.distinctive_features,
                    'height_range': character.visual_descriptor.height_range,
                    'hair_color': character.visual_descriptor.hair_color,
                    'eye_color': character.visual_descriptor.eye_color,
                    'species': character.visual_descriptor.species,
                    'notable_accessories': character.visual_descriptor.notable_accessories,
                    'costume_variations': character.visual_descriptor.costume_variations
                },
                'timeline': {
                    'prequel_era': character.timeline.prequel_era,
                    'original_era': character.timeline.original_era,
                    'sequel_era': character.timeline.sequel_era,
                    'standalone_era': character.timeline.standalone_era,
                    'tv_series': character.timeline.tv_series
                },
                'canon_status': character.canon_status,
                'notes': character.notes
            }

        with open(filepath, 'w') as f:
            json.dump(export_data, f, indent=2)

    def get_database_stats(self) -> Dict:
        """Get database statistics for monitoring and validation"""
        return {
            'total_characters': len(self.characters),
            'faction_distribution': {faction.value: len(chars)
                                   for faction, chars in self.faction_groups.items()},
            'relationship_distribution': {rel.value: len(chars)
                                        for rel, chars in self.relationship_groups.items()},
            'timeline_distribution': {era: len(chars)
                                    for era, chars in self.timeline_index.items()},
            'high_priority_count': len(self.get_high_priority_characters()),
            'average_trust_level': sum(char.trust_level for char in self.characters.values())
                                 / len(self.characters) if self.characters else 0
        }


# Database validation and integrity functions
def validate_character_data(character: StarWarsCharacter) -> List[str]:
    """Validate character data for consistency and completeness"""
    issues = []

    # Trust level validation
    if not 1 <= character.trust_level <= 10:
        issues.append(f"Trust level {character.trust_level} out of range (1-10)")

    # Recognition priority validation
    if not 1 <= character.recognition_priority <= 10:
        issues.append(f"Recognition priority {character.recognition_priority} out of range (1-10)")

    # Confidence threshold validation
    if not 0.0 <= character.confidence_threshold <= 1.0:
        issues.append(f"Confidence threshold {character.confidence_threshold} out of range (0.0-1.0)")

    # Timeline validation
    timeline = character.timeline
    if not any([timeline.prequel_era, timeline.original_era,
                timeline.sequel_era, timeline.standalone_era]):
        issues.append("Character must appear in at least one timeline era")

    # Visual descriptor validation
    height_min, height_max = character.visual_descriptor.height_range
    if height_min > height_max:
        issues.append(f"Invalid height range: {height_min} > {height_max}")

    return issues


def validate_relationship_consistency(db: CharacterDatabase) -> List[str]:
    """Validate relationship consistency across the database"""
    issues = []

    # Check for relationship logic
    for character in db.characters.values():
        # Sith should generally not be close friends
        if (character.faction == FactionAlignment.SITH and
            character.relationship_to_r2d2 == RelationshipType.CLOSE_FRIEND):
            issues.append(f"Sith character {character.name} marked as close friend")

        # High trust levels should match relationship types
        if (character.trust_level >= 8 and
            character.relationship_to_r2d2 in [RelationshipType.ENEMY, RelationshipType.NEUTRAL]):
            issues.append(f"High trust level {character.trust_level} inconsistent with relationship {character.relationship_to_r2d2.value} for {character.name}")

    return issues