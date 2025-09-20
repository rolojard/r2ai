"""
Star Wars Character Image Dataset Recommendations for R2-D2 Recognition System
=============================================================================

Comprehensive guidelines for collecting, organizing, and preparing Star Wars character
image datasets for training facial recognition models with R2-D2 specific requirements.

This module provides:
- Character-specific image collection guidelines
- Dataset organization structure
- Quality validation criteria
- Training/validation split recommendations
- Recognition accuracy thresholds
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple
from enum import Enum
import json


class ImageQuality(Enum):
    """Image quality categories for dataset inclusion"""
    EXCELLENT = "excellent"     # Perfect lighting, clear face, high resolution
    GOOD = "good"              # Good lighting, clear face, adequate resolution
    ACCEPTABLE = "acceptable"   # Usable but not ideal conditions
    POOR = "poor"              # Should be excluded from training


class ImageSource(Enum):
    """Types of image sources with different considerations"""
    OFFICIAL_STILLS = "official_stills"           # Studio photography, promotional materials
    MOVIE_FRAMES = "movie_frames"                 # Extracted from films
    TV_SERIES_FRAMES = "tv_series_frames"         # Extracted from TV shows
    BEHIND_SCENES = "behind_scenes"               # Production photography
    PROMOTIONAL = "promotional"                   # Marketing materials
    FAN_EVENTS = "fan_events"                     # Convention photos, public appearances
    COSPLAY = "cosplay"                           # High-quality cosplay (for negative examples)


class LightingCondition(Enum):
    """Lighting conditions R2-D2 might encounter"""
    BRIGHT_DAYLIGHT = "bright_daylight"
    INDOOR_LIGHTING = "indoor_lighting"
    DIM_LIGHTING = "dim_lighting"
    DRAMATIC_LIGHTING = "dramatic_lighting"       # High contrast, single light source
    COLORED_LIGHTING = "colored_lighting"         # Lightsaber illumination, etc.
    BACKLIGHTING = "backlighting"
    MIXED_LIGHTING = "mixed_lighting"


@dataclass
class ImageRequirements:
    """Specific image requirements for each character"""
    character_name: str
    minimum_images: int
    recommended_images: int
    required_costume_variations: List[str]
    required_lighting_conditions: List[LightingCondition]
    required_angles: List[str]
    age_variations_needed: bool
    special_considerations: List[str]
    excluded_sources: List[ImageSource] = field(default_factory=list)


@dataclass
class DatasetOrganization:
    """Dataset folder structure and organization"""
    base_path: str
    character_folders: Dict[str, str]
    costume_subfolders: Dict[str, List[str]]
    validation_split: float = 0.2
    test_split: float = 0.1
    augmentation_factor: int = 3


@dataclass
class QualityMetrics:
    """Quality metrics for image validation"""
    minimum_resolution: Tuple[int, int]
    maximum_blur_threshold: float
    minimum_face_size_pixels: int
    maximum_occlusion_percentage: float
    required_face_visibility: float
    color_balance_tolerance: float


class StarWarsImageDatasetManager:
    """Manager class for Star Wars character image datasets"""

    def __init__(self):
        self.character_requirements = self._define_character_requirements()
        self.quality_metrics = self._define_quality_metrics()
        self.dataset_organization = self._define_dataset_organization()

    def _define_character_requirements(self) -> Dict[str, ImageRequirements]:
        """Define image collection requirements for each character"""
        return {
            "Luke Skywalker": ImageRequirements(
                character_name="Luke Skywalker",
                minimum_images=500,
                recommended_images=1000,
                required_costume_variations=[
                    "farmboy_tunic",
                    "rebel_pilot_suit",
                    "bespin_fatigues",
                    "endor_camouflage",
                    "black_jedi_robes",
                    "ceremony_jacket"
                ],
                required_lighting_conditions=[
                    LightingCondition.BRIGHT_DAYLIGHT,
                    LightingCondition.INDOOR_LIGHTING,
                    LightingCondition.DRAMATIC_LIGHTING,
                    LightingCondition.COLORED_LIGHTING  # Lightsaber scenes
                ],
                required_angles=["front", "profile_left", "profile_right", "three_quarter", "slight_up", "slight_down"],
                age_variations_needed=True,  # Young Luke to older Luke
                special_considerations=[
                    "Include images with and without lightsaber illumination",
                    "Capture expressions during emotional scenes",
                    "Include helmet-wearing images (pilot)",
                    "Various hair lengths throughout saga",
                    "Mechanical hand visibility in some shots"
                ]
            ),

            "Leia Organa": ImageRequirements(
                character_name="Leia Organa",
                minimum_images=400,
                recommended_images=800,
                required_costume_variations=[
                    "white_alderaanian_dress",
                    "hoth_combat_gear",
                    "endor_camouflage",
                    "boushh_disguise",
                    "resistance_general_uniform",
                    "ceremony_gown"
                ],
                required_lighting_conditions=[
                    LightingCondition.BRIGHT_DAYLIGHT,
                    LightingCondition.INDOOR_LIGHTING,
                    LightingCondition.DIM_LIGHTING,
                    LightingCondition.DRAMATIC_LIGHTING
                ],
                required_angles=["front", "profile_left", "profile_right", "three_quarter"],
                age_variations_needed=True,  # Young Leia to General Leia
                special_considerations=[
                    "Include various hairstyle changes",
                    "Capture leadership expressions",
                    "Include armed/combat poses",
                    "Various royal jewelry and accessories",
                    "Disguised vs. revealed identity shots"
                ]
            ),

            "Han Solo": ImageRequirements(
                character_name="Han Solo",
                minimum_images=400,
                recommended_images=700,
                required_costume_variations=[
                    "smuggler_outfit",
                    "hoth_parka",
                    "endor_trench_coat",
                    "formal_wear",
                    "carbonite_preparation"
                ],
                required_lighting_conditions=[
                    LightingCondition.BRIGHT_DAYLIGHT,
                    LightingCondition.INDOOR_LIGHTING,
                    LightingCondition.DIM_LIGHTING,
                    LightingCondition.MIXED_LIGHTING
                ],
                required_angles=["front", "profile_left", "profile_right", "three_quarter"],
                age_variations_needed=True,
                special_considerations=[
                    "Include cocky expressions and smirks",
                    "Capture with and without blaster",
                    "Various states of facial hair",
                    "Include action poses",
                    "Weather-beaten appearances"
                ]
            ),

            "Chewbacca": ImageRequirements(
                character_name="Chewbacca",
                minimum_images=300,
                recommended_images=500,
                required_costume_variations=[
                    "standard_fur",
                    "endor_gear",
                    "formal_ceremony",
                    "battle_damaged"
                ],
                required_lighting_conditions=[
                    LightingCondition.BRIGHT_DAYLIGHT,
                    LightingCondition.INDOOR_LIGHTING,
                    LightingCondition.DIM_LIGHTING,
                    LightingCondition.DRAMATIC_LIGHTING
                ],
                required_angles=["front", "profile_left", "profile_right", "three_quarter", "full_height"],
                age_variations_needed=False,  # Wookiees age slowly
                special_considerations=[
                    "Focus on facial features within fur",
                    "Capture distinctive eye expressions",
                    "Include bowcaster carrying poses",
                    "Various fur conditions (clean vs. battle-worn)",
                    "Roaring and calm expressions"
                ]
            ),

            "C-3PO": ImageRequirements(
                character_name="C-3PO",
                minimum_images=250,
                recommended_images=400,
                required_costume_variations=[
                    "golden_plating",
                    "silver_leg",
                    "dismantled_parts",
                    "red_arm",
                    "ewok_deity_decoration"
                ],
                required_lighting_conditions=[
                    LightingCondition.BRIGHT_DAYLIGHT,
                    LightingCondition.INDOOR_LIGHTING,
                    LightingCondition.DRAMATIC_LIGHTING,
                    LightingCondition.COLORED_LIGHTING
                ],
                required_angles=["front", "profile_left", "profile_right", "three_quarter", "full_body"],
                age_variations_needed=False,  # Droid appearance consistent
                special_considerations=[
                    "Capture reflective plating under various lighting",
                    "Include damaged vs. pristine conditions",
                    "Focus on photoreceptor (eye) glow",
                    "Various states of assembly/disassembly",
                    "Include pose variations for protocol functions"
                ]
            ),

            "Obi-Wan Kenobi": ImageRequirements(
                character_name="Obi-Wan Kenobi",
                minimum_images=500,
                recommended_images=900,
                required_costume_variations=[
                    "jedi_robes_prequel",
                    "clone_wars_armor",
                    "tatooine_hermit_robes",
                    "young_padawan",
                    "formal_jedi_attire"
                ],
                required_lighting_conditions=[
                    LightingCondition.BRIGHT_DAYLIGHT,
                    LightingCondition.INDOOR_LIGHTING,
                    LightingCondition.DRAMATIC_LIGHTING,
                    LightingCondition.COLORED_LIGHTING
                ],
                required_angles=["front", "profile_left", "profile_right", "three_quarter"],
                age_variations_needed=True,  # Young Obi-Wan to Old Ben
                special_considerations=[
                    "Include images across major age changes",
                    "Capture with and without beard variations",
                    "Include lightsaber combat illumination",
                    "Various expressions from wise to concerned",
                    "Hood up vs. hood down variations"
                ]
            ),

            "Darth Vader": ImageRequirements(
                character_name="Darth Vader",
                minimum_images=300,
                recommended_images=500,
                required_costume_variations=[
                    "standard_black_armor",
                    "meditation_chamber",
                    "damaged_armor",
                    "cape_variations"
                ],
                required_lighting_conditions=[
                    LightingCondition.DRAMATIC_LIGHTING,
                    LightingCondition.DIM_LIGHTING,
                    LightingCondition.COLORED_LIGHTING,
                    LightingCondition.BACKLIGHTING
                ],
                required_angles=["front", "profile_left", "profile_right", "three_quarter", "imposing_low_angle"],
                age_variations_needed=False,  # Consistent armored appearance
                special_considerations=[
                    "Focus on mask details and reflection patterns",
                    "Capture distinctive silhouette",
                    "Include cape dramatic poses",
                    "Red lightsaber illumination effects",
                    "Control panel chest piece visibility",
                    "Intimidating poses and stances"
                ]
            ),

            "Anakin Skywalker": ImageRequirements(
                character_name="Anakin Skywalker",
                minimum_images=400,
                recommended_images=700,
                required_costume_variations=[
                    "slave_boy_clothes",
                    "padawan_robes",
                    "jedi_knight_robes",
                    "dark_side_transition",
                    "clone_wars_armor"
                ],
                required_lighting_conditions=[
                    LightingCondition.BRIGHT_DAYLIGHT,
                    LightingCondition.INDOOR_LIGHTING,
                    LightingCondition.DRAMATIC_LIGHTING,
                    LightingCondition.COLORED_LIGHTING
                ],
                required_angles=["front", "profile_left", "profile_right", "three_quarter"],
                age_variations_needed=True,  # Child to adult
                special_considerations=[
                    "Include major age transitions",
                    "Capture emotional range from innocent to angry",
                    "Include mechanical hand visibility",
                    "Various hair lengths and styles",
                    "Lightsaber combat scenes",
                    "Padawan braid vs. without"
                ]
            ),

            "Padmé Amidala": ImageRequirements(
                character_name="Padmé Amidala",
                minimum_images=350,
                recommended_images=600,
                required_costume_variations=[
                    "royal_gowns",
                    "handmaiden_disguise",
                    "senator_outfits",
                    "travel_clothes",
                    "geonosis_arena_outfit"
                ],
                required_lighting_conditions=[
                    LightingCondition.BRIGHT_DAYLIGHT,
                    LightingCondition.INDOOR_LIGHTING,
                    LightingCondition.DRAMATIC_LIGHTING,
                    LightingCondition.MIXED_LIGHTING
                ],
                required_angles=["front", "profile_left", "profile_right", "three_quarter"],
                age_variations_needed=True,  # Teen Queen to adult Senator
                special_considerations=[
                    "Include elaborate hairstyles and makeup",
                    "Capture royal bearing vs. disguised appearances",
                    "Various jewelry and headdresses",
                    "Leadership expressions",
                    "Combat-ready poses",
                    "Formal vs. casual appearances"
                ]
            ),

            "Rey": ImageRequirements(
                character_name="Rey",
                minimum_images=300,
                recommended_images=500,
                required_costume_variations=[
                    "jakku_scavenger_outfit",
                    "resistance_fighter_gear",
                    "jedi_training_robes",
                    "formal_attire"
                ],
                required_lighting_conditions=[
                    LightingCondition.BRIGHT_DAYLIGHT,
                    LightingCondition.DRAMATIC_LIGHTING,
                    LightingCondition.COLORED_LIGHTING,
                    LightingCondition.MIXED_LIGHTING
                ],
                required_angles=["front", "profile_left", "profile_right", "three_quarter"],
                age_variations_needed=False,  # Consistent age in sequel trilogy
                special_considerations=[
                    "Include determined and fierce expressions",
                    "Capture with staff weapon and lightsaber",
                    "Various hair bun styles",
                    "Desert environment adaptations",
                    "Force-user concentration expressions"
                ]
            ),

            "Finn": ImageRequirements(
                character_name="Finn",
                minimum_images=250,
                recommended_images=400,
                required_costume_variations=[
                    "stormtrooper_armor",
                    "resistance_jacket",
                    "resistance_uniform",
                    "formal_wear"
                ],
                required_lighting_conditions=[
                    LightingCondition.BRIGHT_DAYLIGHT,
                    LightingCondition.INDOOR_LIGHTING,
                    LightingCondition.DRAMATIC_LIGHTING,
                    LightingCondition.MIXED_LIGHTING
                ],
                required_angles=["front", "profile_left", "profile_right", "three_quarter"],
                age_variations_needed=False,
                special_considerations=[
                    "Include stormtrooper helmet vs. unmasked",
                    "Capture transition from soldier to hero",
                    "Various expressions showing character growth",
                    "Combat poses with different weapons"
                ]
            ),

            "Poe Dameron": ImageRequirements(
                character_name="Poe Dameron",
                minimum_images=200,
                recommended_images=350,
                required_costume_variations=[
                    "x_wing_pilot_suit",
                    "resistance_uniform",
                    "casual_jacket",
                    "undercover_disguise"
                ],
                required_lighting_conditions=[
                    LightingCondition.BRIGHT_DAYLIGHT,
                    LightingCondition.INDOOR_LIGHTING,
                    LightingCondition.DRAMATIC_LIGHTING,
                    LightingCondition.COLORED_LIGHTING
                ],
                required_angles=["front", "profile_left", "profile_right", "three_quarter"],
                age_variations_needed=False,
                special_considerations=[
                    "Include pilot helmet vs. unmasked",
                    "Capture confident pilot expressions",
                    "Various flight gear configurations",
                    "Leadership poses and expressions"
                ]
            ),

            "Kylo Ren": ImageRequirements(
                character_name="Kylo Ren",
                minimum_images=250,
                recommended_images=400,
                required_costume_variations=[
                    "masked_appearance",
                    "unmasked",
                    "supreme_leader_attire",
                    "redeemed_ben_solo"
                ],
                required_lighting_conditions=[
                    LightingCondition.DRAMATIC_LIGHTING,
                    LightingCondition.DIM_LIGHTING,
                    LightingCondition.COLORED_LIGHTING,
                    LightingCondition.BACKLIGHTING
                ],
                required_angles=["front", "profile_left", "profile_right", "three_quarter", "intimidating_angle"],
                age_variations_needed=True,  # Ben Solo child to adult Kylo Ren
                special_considerations=[
                    "Include masked vs. unmasked recognition",
                    "Capture scar progression",
                    "Various emotional states from calm to rage",
                    "Crossguard lightsaber illumination",
                    "Dramatic cape and hood positions"
                ]
            ),

            "Ahsoka Tano": ImageRequirements(
                character_name="Ahsoka Tano",
                minimum_images=300,
                recommended_images=500,
                required_costume_variations=[
                    "padawan_outfit",
                    "jedi_attire",
                    "civilian_disguise",
                    "rebel_agent_gear",
                    "white_robes"
                ],
                required_lighting_conditions=[
                    LightingCondition.BRIGHT_DAYLIGHT,
                    LightingCondition.INDOOR_LIGHTING,
                    LightingCondition.DRAMATIC_LIGHTING,
                    LightingCondition.COLORED_LIGHTING
                ],
                required_angles=["front", "profile_left", "profile_right", "three_quarter"],
                age_variations_needed=True,  # Young Padawan to adult
                special_considerations=[
                    "Include head-tail (lekku) growth stages",
                    "Capture distinctive Togruta markings",
                    "Various expressions from playful to serious",
                    "Twin lightsaber poses",
                    "Head-tail positioning variations"
                ]
            ),

            "BB-8": ImageRequirements(
                character_name="BB-8",
                minimum_images=200,
                recommended_images=300,
                required_costume_variations=[
                    "standard_orange_white",
                    "battle_damaged",
                    "disguised"
                ],
                required_lighting_conditions=[
                    LightingCondition.BRIGHT_DAYLIGHT,
                    LightingCondition.INDOOR_LIGHTING,
                    LightingCondition.DRAMATIC_LIGHTING,
                    LightingCondition.COLORED_LIGHTING
                ],
                required_angles=["front", "side", "three_quarter", "top_view"],
                age_variations_needed=False,
                special_considerations=[
                    "Focus on photoreceptor (eye) as main feature",
                    "Include rolling motion blur considerations",
                    "Various antenna and tool configurations",
                    "Distinctive spherical shape recognition",
                    "Orange and white pattern variations"
                ]
            )
        }

    def _define_quality_metrics(self) -> QualityMetrics:
        """Define quality standards for image inclusion"""
        return QualityMetrics(
            minimum_resolution=(224, 224),  # Minimum for modern CNN models
            maximum_blur_threshold=0.3,     # Laplacian variance threshold
            minimum_face_size_pixels=64,    # Minimum face bounding box size
            maximum_occlusion_percentage=30, # Maximum face occlusion allowed
            required_face_visibility=0.7,   # Minimum portion of face visible
            color_balance_tolerance=0.2     # RGB channel balance tolerance
        )

    def _define_dataset_organization(self) -> DatasetOrganization:
        """Define dataset folder structure"""
        base_path = "/home/rolo/r2ai/star_wars_dataset"

        character_folders = {
            char: f"{base_path}/{char.lower().replace(' ', '_')}"
            for char in self.character_requirements.keys()
        }

        costume_subfolders = {
            char: requirements.required_costume_variations
            for char, requirements in self.character_requirements.items()
        }

        return DatasetOrganization(
            base_path=base_path,
            character_folders=character_folders,
            costume_subfolders=costume_subfolders,
            validation_split=0.2,
            test_split=0.1,
            augmentation_factor=3
        )

    def generate_collection_guidelines(self) -> Dict[str, Dict]:
        """Generate comprehensive collection guidelines for each character"""
        guidelines = {}

        for char_name, requirements in self.character_requirements.items():
            guidelines[char_name] = {
                "collection_priority": self._calculate_collection_priority(char_name),
                "recommended_sources": self._get_recommended_sources(char_name),
                "search_terms": self._generate_search_terms(char_name, requirements),
                "quality_checklist": self._generate_quality_checklist(requirements),
                "organization_structure": self._generate_folder_structure(char_name, requirements),
                "augmentation_strategy": self._generate_augmentation_strategy(requirements),
                "validation_criteria": self._generate_validation_criteria(char_name)
            }

        return guidelines

    def _calculate_collection_priority(self, char_name: str) -> str:
        """Calculate collection priority based on R2-D2 relationship"""
        high_priority = ["Luke Skywalker", "C-3PO", "Leia Organa", "Anakin Skywalker"]
        medium_priority = ["Obi-Wan Kenobi", "Han Solo", "Ahsoka Tano", "Padmé Amidala"]

        if char_name in high_priority:
            return "HIGH"
        elif char_name in medium_priority:
            return "MEDIUM"
        else:
            return "STANDARD"

    def _get_recommended_sources(self, char_name: str) -> List[str]:
        """Get recommended image sources for each character"""
        base_sources = [
            "Official movie stills",
            "High-quality promotional materials",
            "Behind-the-scenes photography",
            "Official merchandise photography"
        ]

        character_specific = {
            "Luke Skywalker": base_sources + [
                "Star Wars official social media",
                "Lucasfilm archives",
                "Convention photography"
            ],
            "C-3PO": base_sources + [
                "Product photography",
                "Museum displays",
                "Technical documentation"
            ],
            "Ahsoka Tano": base_sources + [
                "Animation reference materials",
                "Clone Wars promotional materials",
                "Live-action series stills"
            ]
        }

        return character_specific.get(char_name, base_sources)

    def _generate_search_terms(self, char_name: str, requirements: ImageRequirements) -> List[str]:
        """Generate search terms for automated collection"""
        base_terms = [char_name]
        base_terms.extend(requirements.required_costume_variations)

        # Add character-specific terms
        character_specific_terms = {
            "Luke Skywalker": ["Mark Hamill", "Jedi Knight", "X-wing pilot", "Tatooine"],
            "C-3PO": ["protocol droid", "golden droid", "Anthony Daniels"],
            "Darth Vader": ["Sith Lord", "Dark Lord", "Imperial", "James Earl Jones"],
            "Leia Organa": ["Princess Leia", "Carrie Fisher", "General Organa"],
            "Ahsoka Tano": ["Togruta", "Snips", "Clone Wars", "Rebels"]
        }

        if char_name in character_specific_terms:
            base_terms.extend(character_specific_terms[char_name])

        return base_terms

    def _generate_quality_checklist(self, requirements: ImageRequirements) -> List[str]:
        """Generate quality checklist for image validation"""
        base_checklist = [
            "Face clearly visible and unobscured",
            "Adequate lighting for facial feature recognition",
            "Minimum resolution requirements met",
            "Image not significantly blurred or distorted",
            "Character is primary subject in frame",
            "No watermarks or text overlays on face"
        ]

        if requirements.special_considerations:
            base_checklist.extend([
                f"Special consideration: {consideration}"
                for consideration in requirements.special_considerations
            ])

        return base_checklist

    def _generate_folder_structure(self, char_name: str, requirements: ImageRequirements) -> Dict:
        """Generate folder structure for character dataset"""
        safe_name = char_name.lower().replace(' ', '_').replace('-', '_')

        structure = {
            "base_folder": safe_name,
            "subfolders": {
                "train": f"{safe_name}/train",
                "validation": f"{safe_name}/validation",
                "test": f"{safe_name}/test"
            },
            "costume_folders": {}
        }

        # Add costume variation folders
        for costume in requirements.required_costume_variations:
            safe_costume = costume.lower().replace(' ', '_')
            structure["costume_folders"][costume] = {
                "train": f"{safe_name}/train/{safe_costume}",
                "validation": f"{safe_name}/validation/{safe_costume}",
                "test": f"{safe_name}/test/{safe_costume}"
            }

        return structure

    def _generate_augmentation_strategy(self, requirements: ImageRequirements) -> Dict:
        """Generate data augmentation strategy"""
        base_augmentation = {
            "rotation": {"range": (-15, 15), "probability": 0.7},
            "brightness": {"range": (0.8, 1.2), "probability": 0.6},
            "contrast": {"range": (0.9, 1.1), "probability": 0.5},
            "horizontal_flip": {"probability": 0.5},
            "zoom": {"range": (0.9, 1.1), "probability": 0.4},
            "gaussian_noise": {"sigma": 0.01, "probability": 0.3}
        }

        # Character-specific augmentations
        if "lighting" in [consideration.lower() for consideration in requirements.special_considerations]:
            base_augmentation["lighting_variation"] = {
                "shadow_intensity": {"range": (0.7, 1.3), "probability": 0.6},
                "color_temperature": {"range": (0.8, 1.2), "probability": 0.4}
            }

        return base_augmentation

    def _generate_validation_criteria(self, char_name: str) -> Dict:
        """Generate validation criteria for recognition accuracy"""
        base_criteria = {
            "minimum_accuracy": 0.85,
            "minimum_precision": 0.80,
            "minimum_recall": 0.75,
            "maximum_false_positive_rate": 0.05
        }

        # Higher standards for priority characters
        high_priority_chars = ["Luke Skywalker", "C-3PO", "Leia Organa", "Anakin Skywalker"]
        if char_name in high_priority_chars:
            base_criteria.update({
                "minimum_accuracy": 0.90,
                "minimum_precision": 0.88,
                "minimum_recall": 0.85,
                "maximum_false_positive_rate": 0.03
            })

        return base_criteria

    def export_collection_guidelines(self, filepath: str):
        """Export collection guidelines to JSON file"""
        guidelines = self.generate_collection_guidelines()

        export_data = {
            "dataset_overview": {
                "total_characters": len(self.character_requirements),
                "estimated_total_images": sum(req.recommended_images for req in self.character_requirements.values()),
                "dataset_organization": {
                    "base_path": self.dataset_organization.base_path,
                    "validation_split": self.dataset_organization.validation_split,
                    "test_split": self.dataset_organization.test_split,
                    "augmentation_factor": self.dataset_organization.augmentation_factor
                },
                "quality_standards": {
                    "minimum_resolution": self.quality_metrics.minimum_resolution,
                    "maximum_blur_threshold": self.quality_metrics.maximum_blur_threshold,
                    "minimum_face_size": self.quality_metrics.minimum_face_size_pixels,
                    "maximum_occlusion": self.quality_metrics.maximum_occlusion_percentage
                }
            },
            "character_guidelines": guidelines,
            "technical_specifications": {
                "supported_formats": ["JPEG", "PNG"],
                "color_space": "RGB",
                "preprocessing_pipeline": [
                    "Face detection and alignment",
                    "Resize to 224x224 pixels",
                    "Normalization (0-1 range)",
                    "Augmentation application"
                ]
            }
        }

        with open(filepath, 'w') as f:
            json.dump(export_data, f, indent=2)

    def generate_dataset_statistics(self) -> Dict:
        """Generate statistics about the planned dataset"""
        total_min_images = sum(req.minimum_images for req in self.character_requirements.values())
        total_rec_images = sum(req.recommended_images for req in self.character_requirements.values())

        character_priorities = {}
        for char_name in self.character_requirements.keys():
            priority = self._calculate_collection_priority(char_name)
            if priority not in character_priorities:
                character_priorities[priority] = 0
            character_priorities[priority] += 1

        return {
            "total_characters": len(self.character_requirements),
            "total_minimum_images": total_min_images,
            "total_recommended_images": total_rec_images,
            "character_priorities": character_priorities,
            "unique_costumes": sum(len(req.required_costume_variations) for req in self.character_requirements.values()),
            "estimated_storage_gb": (total_rec_images * 0.5) / 1024,  # Rough estimate
            "training_time_estimate_hours": total_rec_images / 1000 * 2  # Very rough estimate
        }


if __name__ == "__main__":
    # Create dataset manager
    dataset_manager = StarWarsImageDatasetManager()

    # Export guidelines
    dataset_manager.export_collection_guidelines("/home/rolo/r2ai/image_collection_guidelines.json")

    # Print statistics
    stats = dataset_manager.generate_dataset_statistics()
    print("Star Wars Character Dataset Statistics:")
    print(f"Total Characters: {stats['total_characters']}")
    print(f"Minimum Images Needed: {stats['total_minimum_images']:,}")
    print(f"Recommended Images: {stats['total_recommended_images']:,}")
    print(f"Estimated Storage: {stats['estimated_storage_gb']:.1f} GB")
    print(f"Character Priorities: {stats['character_priorities']}")
    print(f"Unique Costume Variations: {stats['unique_costumes']}")

    print("\nCollection guidelines exported to: /home/rolo/r2ai/image_collection_guidelines.json")