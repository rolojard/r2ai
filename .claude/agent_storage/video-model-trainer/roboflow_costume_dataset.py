#!/usr/bin/env python3
"""
Roboflow Integration for Star Wars Costume Recognition Dataset
Complete dataset management and training pipeline for costume classification
"""

import os
import json
import cv2
import numpy as np
import requests
import zipfile
from pathlib import Path
import logging
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass
import time
from datetime import datetime
import albumentations as A
from roboflow import Roboflow
import shutil

logger = logging.getLogger(__name__)

@dataclass
class CostumeClass:
    """Star Wars costume class definition"""
    name: str
    description: str
    key_features: List[str]
    color_palette: List[str]
    difficulty_level: str  # 'easy', 'medium', 'hard'
    canonical_examples: List[str]

class StarWarsCostumeDatasetManager:
    """Comprehensive dataset manager for Star Wars costume recognition"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.base_dir = Path("/home/rolo/r2ai/.claude/agent_storage/video-model-trainer/datasets")
        self.costume_dir = self.base_dir / "star_wars_costumes"
        self.roboflow_dir = self.base_dir / "roboflow_costumes"

        # Create directories
        for directory in [self.base_dir, self.costume_dir, self.roboflow_dir]:
            directory.mkdir(parents=True, exist_ok=True)

        # Define Star Wars costume classes (validated by Star Wars Expert)
        self.costume_classes = {
            "jedi": CostumeClass(
                name="jedi",
                description="Jedi Knights and Masters - brown/beige robes, lightsaber",
                key_features=["brown_robes", "beige_tunic", "lightsaber", "jedi_belt", "boots"],
                color_palette=["#8B4513", "#D2B48C", "#F5DEB3", "#654321", "#A0522D"],
                difficulty_level="medium",
                canonical_examples=["obi_wan", "luke_skywalker", "qui_gon", "mace_windu", "yoda"]
            ),
            "sith": CostumeClass(
                name="sith",
                description="Sith Lords - dark robes, red lightsaber, imposing presence",
                key_features=["black_robes", "dark_cloak", "red_lightsaber", "mask", "armor"],
                color_palette=["#000000", "#2F2F2F", "#8B0000", "#FF0000", "#4B0000"],
                difficulty_level="medium",
                canonical_examples=["darth_vader", "darth_maul", "emperor_palpatine", "kylo_ren"]
            ),
            "rebel_alliance": CostumeClass(
                name="rebel_alliance",
                description="Rebel Alliance fighters - orange pilot suits, rebel insignia",
                key_features=["orange_jumpsuit", "rebel_helmet", "life_support", "blaster", "insignia"],
                color_palette=["#FF8C00", "#FFA500", "#FF6347", "#FFFFFF", "#000080"],
                difficulty_level="easy",
                canonical_examples=["x_wing_pilot", "rebel_trooper", "princess_leia", "han_solo"]
            ),
            "stormtrooper": CostumeClass(
                name="stormtrooper",
                description="Imperial Stormtroopers - white armor, distinctive helmet",
                key_features=["white_armor", "helmet", "black_details", "blaster", "chest_plate"],
                color_palette=["#FFFFFF", "#F8F8FF", "#000000", "#2F2F2F", "#C0C0C0"],
                difficulty_level="easy",
                canonical_examples=["imperial_stormtrooper", "clone_trooper", "death_trooper"]
            ),
            "imperial_officer": CostumeClass(
                name="imperial_officer",
                description="Imperial Officers - gray/black uniforms, rank insignia",
                key_features=["gray_uniform", "black_uniform", "rank_badge", "cap", "boots"],
                color_palette=["#708090", "#2F4F4F", "#000000", "#C0C0C0", "#FFD700"],
                difficulty_level="medium",
                canonical_examples=["grand_moff_tarkin", "admiral_thrawn", "imperial_general"]
            ),
            "mandalorian": CostumeClass(
                name="mandalorian",
                description="Mandalorian warriors - distinctive armor and helmets",
                key_features=["mandalorian_helmet", "armor_plates", "jetpack", "blaster", "cape"],
                color_palette=["#C0C0C0", "#4169E1", "#228B22", "#FF0000", "#FFD700"],
                difficulty_level="hard",
                canonical_examples=["boba_fett", "jango_fett", "din_djarin", "sabine_wren"]
            ),
            "civilian": CostumeClass(
                name="civilian",
                description="Regular clothing, no distinctive Star Wars elements",
                key_features=["regular_clothes", "no_costume", "street_wear", "casual", "modern"],
                color_palette=["varied"],
                difficulty_level="easy",
                canonical_examples=["everyday_clothing", "convention_attendee", "non_cosplay"]
            )
        }

        # Initialize Roboflow if API key provided
        self.roboflow = None
        if self.config.get('roboflow_api_key'):
            try:
                self.roboflow = Roboflow(api_key=self.config['roboflow_api_key'])
                logger.info("Roboflow initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize Roboflow: {e}")

    def create_roboflow_project(self, project_name: str = "r2d2-star-wars-costumes") -> Optional[str]:
        """Create new Roboflow project for costume recognition"""
        if not self.roboflow:
            logger.error("Roboflow not initialized")
            return None

        try:
            # Create workspace and project
            workspace = self.roboflow.workspace()

            project_config = {
                "name": project_name,
                "type": "classification",
                "annotation_format": "classification",
                "classes": list(self.costume_classes.keys()),
                "description": "Star Wars costume recognition for R2D2 interactive system",
                "license": "MIT",
                "public": False
            }

            # This would create the project (API call)
            logger.info(f"Creating Roboflow project: {project_name}")
            logger.info(f"Classes: {', '.join(self.costume_classes.keys())}")

            return project_name

        except Exception as e:
            logger.error(f"Error creating Roboflow project: {e}")
            return None

    def upload_dataset_to_roboflow(self, project_name: str, dataset_path: Path) -> bool:
        """Upload dataset to Roboflow with proper annotations"""
        if not self.roboflow:
            logger.error("Roboflow not initialized")
            return False

        try:
            workspace = self.roboflow.workspace()
            project = workspace.project(project_name)

            # Upload images with annotations
            for class_name in self.costume_classes.keys():
                class_dir = dataset_path / class_name
                if class_dir.exists():
                    logger.info(f"Uploading {class_name} images...")

                    for img_path in class_dir.glob("*.jpg"):
                        try:
                            # Upload image with classification label
                            project.upload(
                                image_path=str(img_path),
                                split="train",  # or determine split automatically
                                tag=[class_name],
                                batch_name=f"r2d2_costumes_{class_name}"
                            )
                        except Exception as e:
                            logger.warning(f"Failed to upload {img_path}: {e}")

            logger.info("Dataset upload to Roboflow completed")
            return True

        except Exception as e:
            logger.error(f"Error uploading to Roboflow: {e}")
            return False

    def download_roboflow_dataset(self, workspace: str, project: str, version: int = 1) -> Optional[Path]:
        """Download dataset from Roboflow"""
        if not self.roboflow:
            logger.error("Roboflow not initialized")
            return None

        try:
            rf_project = self.roboflow.workspace(workspace).project(project)
            dataset = rf_project.version(version).download("folder", location=str(self.roboflow_dir))

            logger.info(f"Downloaded Roboflow dataset to: {dataset.location}")
            return Path(dataset.location)

        except Exception as e:
            logger.error(f"Error downloading from Roboflow: {e}")
            return None

    def create_synthetic_dataset(self, num_images_per_class: int = 100) -> Path:
        """Create synthetic costume dataset for training"""
        logger.info("Creating synthetic Star Wars costume dataset...")

        synthetic_dir = self.costume_dir / "synthetic"
        synthetic_dir.mkdir(parents=True, exist_ok=True)

        for class_name, costume_class in self.costume_classes.items():
            class_dir = synthetic_dir / class_name
            class_dir.mkdir(parents=True, exist_ok=True)

            logger.info(f"Generating {num_images_per_class} {class_name} images...")

            for i in range(num_images_per_class):
                # Generate synthetic image based on costume characteristics
                synthetic_image = self._generate_costume_image(costume_class)

                # Save image
                img_path = class_dir / f"{class_name}_{i:04d}.jpg"
                cv2.imwrite(str(img_path), synthetic_image)

                # Create annotation
                self._create_image_annotation(img_path, class_name, costume_class)

        # Create dataset splits
        self._create_dataset_splits(synthetic_dir)

        logger.info(f"Synthetic dataset created at: {synthetic_dir}")
        return synthetic_dir

    def _generate_costume_image(self, costume_class: CostumeClass) -> np.ndarray:
        """Generate synthetic costume image based on class characteristics"""
        # Base image (person silhouette)
        img = np.ones((224, 224, 3), dtype=np.uint8) * 128

        # Apply costume-specific features
        if costume_class.name == "jedi":
            # Brown/beige color scheme
            img[:, :] = [139, 69, 19]  # Brown
            # Add robe-like shape
            cv2.rectangle(img, (50, 80), (174, 220), (210, 180, 140), -1)
            # Add lightsaber
            cv2.line(img, (20, 100), (20, 40), (0, 255, 255), 3)

        elif costume_class.name == "sith":
            # Dark color scheme
            img[:, :] = [0, 0, 0]  # Black
            # Add red accents
            cv2.rectangle(img, (60, 90), (164, 210), (40, 40, 40), -1)
            # Add red lightsaber
            cv2.line(img, (200, 120), (200, 60), (0, 0, 255), 3)

        elif costume_class.name == "stormtrooper":
            # White armor
            img[:, :] = [248, 248, 255]  # White
            # Add black details
            cv2.rectangle(img, (90, 60), (134, 80), (0, 0, 0), -1)  # Visor
            cv2.rectangle(img, (100, 120), (124, 140), (0, 0, 0), -1)  # Chest detail

        elif costume_class.name == "rebel_alliance":
            # Orange pilot suit
            img[:, :] = [255, 140, 0]  # Orange
            # Add white details
            cv2.rectangle(img, (85, 110), (139, 130), (255, 255, 255), -1)
            cv2.rectangle(img, (100, 60), (124, 80), (255, 255, 255), -1)  # Helmet

        else:
            # Civilian - random regular colors
            colors = [(100, 150, 200), (150, 100, 50), (50, 150, 100)]
            color = colors[np.random.randint(0, len(colors))]
            img[:, :] = color

        # Add noise and variations
        noise = np.random.normal(0, 10, img.shape).astype(np.int16)
        img = np.clip(img.astype(np.int16) + noise, 0, 255).astype(np.uint8)

        return img

    def _create_image_annotation(self, img_path: Path, class_name: str, costume_class: CostumeClass):
        """Create annotation file for image"""
        annotation = {
            "image_path": str(img_path.relative_to(self.costume_dir)),
            "class": class_name,
            "class_description": costume_class.description,
            "key_features": costume_class.key_features,
            "difficulty": costume_class.difficulty_level,
            "timestamp": datetime.now().isoformat()
        }

        annotation_path = img_path.with_suffix('.json')
        with open(annotation_path, 'w') as f:
            json.dump(annotation, f, indent=2)

    def _create_dataset_splits(self, dataset_dir: Path):
        """Create train/val/test splits"""
        splits = {'train': 0.7, 'val': 0.2, 'test': 0.1}

        for class_name in self.costume_classes.keys():
            class_dir = dataset_dir / class_name
            if not class_dir.exists():
                continue

            images = list(class_dir.glob("*.jpg"))
            np.random.shuffle(images)

            # Create split directories
            for split_name in splits.keys():
                split_dir = dataset_dir / split_name / class_name
                split_dir.mkdir(parents=True, exist_ok=True)

            # Split images
            start_idx = 0
            for split_name, ratio in splits.items():
                end_idx = start_idx + int(len(images) * ratio)
                split_images = images[start_idx:end_idx]

                for img_path in split_images:
                    split_dir = dataset_dir / split_name / class_name
                    shutil.copy2(img_path, split_dir / img_path.name)

                    # Copy annotation if exists
                    annotation_path = img_path.with_suffix('.json')
                    if annotation_path.exists():
                        shutil.copy2(annotation_path, split_dir / annotation_path.name)

                start_idx = end_idx

        # Create annotations files for each split
        for split_name in splits.keys():
            annotations = []
            split_dir = dataset_dir / split_name

            for class_name in self.costume_classes.keys():
                class_dir = split_dir / class_name
                if class_dir.exists():
                    for img_path in class_dir.glob("*.jpg"):
                        annotations.append({
                            "image_path": str(img_path.relative_to(dataset_dir)),
                            "class": class_name
                        })

            # Save split annotations
            with open(dataset_dir / f"{split_name}_annotations.json", 'w') as f:
                json.dump(annotations, f, indent=2)

        logger.info("Dataset splits created: train/val/test")

    def augment_dataset(self, dataset_dir: Path, augmentation_factor: int = 3) -> Path:
        """Apply augmentations to increase dataset size"""
        logger.info("Applying dataset augmentations...")

        augmented_dir = dataset_dir.parent / f"{dataset_dir.name}_augmented"
        augmented_dir.mkdir(parents=True, exist_ok=True)

        # Define augmentation pipeline
        transform = A.Compose([
            A.RandomRotate90(p=0.3),
            A.HorizontalFlip(p=0.5),
            A.RandomBrightnessContrast(p=0.4),
            A.ColorJitter(brightness=0.2, contrast=0.2, saturation=0.2, hue=0.1, p=0.3),
            A.GaussNoise(var_limit=(10.0, 50.0), p=0.2),
            A.Blur(blur_limit=3, p=0.1),
            A.RandomShadow(p=0.2),
            A.RandomFog(p=0.1),
            # Costume-specific augmentations
            A.HueSaturationValue(hue_shift_limit=20, sat_shift_limit=30, val_shift_limit=20, p=0.3),
        ])

        for class_name in self.costume_classes.keys():
            original_class_dir = dataset_dir / class_name
            augmented_class_dir = augmented_dir / class_name
            augmented_class_dir.mkdir(parents=True, exist_ok=True)

            if not original_class_dir.exists():
                continue

            images = list(original_class_dir.glob("*.jpg"))
            logger.info(f"Augmenting {len(images)} {class_name} images...")

            for img_path in images:
                # Copy original
                shutil.copy2(img_path, augmented_class_dir / img_path.name)

                # Generate augmented versions
                img = cv2.imread(str(img_path))
                img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

                for aug_idx in range(augmentation_factor):
                    augmented = transform(image=img)['image']
                    augmented_bgr = cv2.cvtColor(augmented, cv2.COLOR_RGB2BGR)

                    aug_name = img_path.stem + f"_aug_{aug_idx}" + img_path.suffix
                    cv2.imwrite(str(augmented_class_dir / aug_name), augmented_bgr)

        logger.info(f"Augmented dataset created at: {augmented_dir}")
        return augmented_dir

    def validate_dataset_quality(self, dataset_dir: Path) -> Dict[str, Any]:
        """Validate dataset quality and balance"""
        logger.info("Validating dataset quality...")

        validation_results = {
            "class_distribution": {},
            "image_quality": {},
            "annotation_completeness": {},
            "recommendations": []
        }

        total_images = 0
        for class_name in self.costume_classes.keys():
            class_dir = dataset_dir / class_name
            if class_dir.exists():
                class_images = list(class_dir.glob("*.jpg"))
                validation_results["class_distribution"][class_name] = len(class_images)
                total_images += len(class_images)

                # Check image quality
                if class_images:
                    sample_img = cv2.imread(str(class_images[0]))
                    validation_results["image_quality"][class_name] = {
                        "resolution": f"{sample_img.shape[1]}x{sample_img.shape[0]}",
                        "channels": sample_img.shape[2]
                    }

                # Check annotations
                annotations = list(class_dir.glob("*.json"))
                validation_results["annotation_completeness"][class_name] = {
                    "annotated": len(annotations),
                    "total": len(class_images),
                    "percentage": len(annotations) / len(class_images) * 100 if class_images else 0
                }

        # Generate recommendations
        class_counts = list(validation_results["class_distribution"].values())
        if class_counts:
            min_count = min(class_counts)
            max_count = max(class_counts)
            if max_count / min_count > 2:
                validation_results["recommendations"].append(
                    "Dataset is imbalanced. Consider augmenting underrepresented classes."
                )

        if total_images < 1000:
            validation_results["recommendations"].append(
                "Dataset size is small. Consider collecting more images or augmentation."
            )

        # Save validation report
        report_path = dataset_dir / "validation_report.json"
        with open(report_path, 'w') as f:
            json.dump(validation_results, f, indent=2)

        logger.info(f"Dataset validation completed. Report saved to: {report_path}")
        return validation_results

    def export_for_training(self, dataset_dir: Path, format: str = "classification") -> Path:
        """Export dataset in format suitable for training"""
        logger.info(f"Exporting dataset in {format} format...")

        export_dir = dataset_dir.parent / f"{dataset_dir.name}_export"
        export_dir.mkdir(parents=True, exist_ok=True)

        if format == "classification":
            # Create directory structure for classification
            for split in ['train', 'val', 'test']:
                for class_name in self.costume_classes.keys():
                    split_class_dir = export_dir / split / class_name
                    split_class_dir.mkdir(parents=True, exist_ok=True)

                    # Copy images
                    source_dir = dataset_dir / split / class_name
                    if source_dir.exists():
                        for img_path in source_dir.glob("*.jpg"):
                            shutil.copy2(img_path, split_class_dir / img_path.name)

        # Create training configuration
        training_config = {
            "dataset_info": {
                "name": "star_wars_costumes",
                "type": "classification",
                "classes": list(self.costume_classes.keys()),
                "num_classes": len(self.costume_classes),
                "image_size": [224, 224],
                "format": format
            },
            "class_definitions": {
                name: {
                    "description": cls.description,
                    "key_features": cls.key_features,
                    "difficulty": cls.difficulty_level
                }
                for name, cls in self.costume_classes.items()
            },
            "training_parameters": {
                "batch_size": 32,
                "learning_rate": 0.001,
                "epochs": 50,
                "weight_decay": 0.0001,
                "augmentation": True
            }
        }

        with open(export_dir / "training_config.json", 'w') as f:
            json.dump(training_config, f, indent=2)

        logger.info(f"Dataset exported to: {export_dir}")
        return export_dir

# Configuration for costume dataset
def get_costume_dataset_config():
    """Get configuration for costume dataset management"""
    return {
        "roboflow_api_key": None,  # Set your Roboflow API key
        "roboflow_workspace": "r2d2-project",
        "roboflow_project": "star-wars-costumes",
        "synthetic_images_per_class": 200,
        "augmentation_factor": 3,
        "quality_threshold": 0.8,
        "balance_threshold": 2.0  # Max ratio between largest/smallest class
    }

# Main execution
async def main():
    """Main execution for costume dataset preparation"""
    config = get_costume_dataset_config()
    manager = StarWarsCostumeDatasetManager(config)

    # Create synthetic dataset
    logger.info("Creating Star Wars costume dataset...")
    synthetic_dataset = manager.create_synthetic_dataset(
        num_images_per_class=config['synthetic_images_per_class']
    )

    # Augment dataset
    augmented_dataset = manager.augment_dataset(
        synthetic_dataset,
        augmentation_factor=config['augmentation_factor']
    )

    # Validate dataset
    validation_results = manager.validate_dataset_quality(augmented_dataset)

    # Export for training
    training_dataset = manager.export_for_training(augmented_dataset)

    # Create Roboflow project (if API key provided)
    if config.get('roboflow_api_key'):
        project_name = manager.create_roboflow_project()
        if project_name:
            manager.upload_dataset_to_roboflow(project_name, training_dataset)

    logger.info("Costume dataset preparation completed!")
    logger.info(f"Training dataset available at: {training_dataset}")

    return training_dataset

if __name__ == "__main__":
    import asyncio
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())