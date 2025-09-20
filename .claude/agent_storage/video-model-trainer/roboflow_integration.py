#!/usr/bin/env python3
"""
Roboflow Integration for R2D2 Computer Vision Dataset Management
Comprehensive dataset management, annotation workflows, and model deployment
"""

import requests
import json
import os
import cv2
import numpy as np
from pathlib import Path
import logging
from typing import Dict, List, Tuple, Optional, Any
import zipfile
import shutil
from datetime import datetime
import base64
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
import yaml

logger = logging.getLogger(__name__)

class RoboflowDatasetManager:
    """Roboflow dataset management for Star Wars costume recognition"""

    def __init__(self, api_key: str, workspace: str):
        self.api_key = api_key
        self.workspace = workspace
        self.base_url = "https://api.roboflow.com"
        self.headers = {"Authorization": f"Bearer {api_key}"}

        # Dataset configurations
        self.projects = {
            "star_wars_costumes": {
                "project_id": "star-wars-costumes",
                "version": 1,
                "classes": [
                    "jedi", "sith", "rebel_alliance", "stormtrooper",
                    "imperial_officer", "mandalorian", "civilian"
                ],
                "annotation_format": "coco"
            },
            "guest_detection": {
                "project_id": "convention-guests",
                "version": 1,
                "classes": ["person"],
                "annotation_format": "yolo"
            }
        }

        # Local dataset paths
        self.dataset_root = Path("/home/rolo/r2ai/.claude/agent_storage/video-model-trainer/datasets")
        self.dataset_root.mkdir(parents=True, exist_ok=True)

    def create_project(self, project_name: str, project_type: str = "object-detection") -> bool:
        """Create new Roboflow project"""
        try:
            url = f"{self.base_url}/v1/workspaces/{self.workspace}/projects"

            project_data = {
                "name": project_name,
                "type": project_type,
                "annotation": "coco" if project_type == "object-detection" else "classification"
            }

            response = requests.post(url, headers=self.headers, json=project_data)

            if response.status_code == 201:
                logger.info(f"Created Roboflow project: {project_name}")
                return True
            else:
                logger.error(f"Failed to create project: {response.status_code} - {response.text}")
                return False

        except Exception as e:
            logger.error(f"Error creating Roboflow project: {e}")
            return False

    def upload_image_batch(self, project_id: str, image_paths: List[str],
                          batch_name: str = None) -> Dict[str, Any]:
        """Upload batch of images to Roboflow project"""
        try:
            upload_url = f"{self.base_url}/v1/workspaces/{self.workspace}/projects/{project_id}/upload"

            successful_uploads = 0
            failed_uploads = 0
            upload_results = []

            # Create batch name if not provided
            if batch_name is None:
                batch_name = f"batch_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

            for image_path in image_paths:
                try:
                    # Read and encode image
                    with open(image_path, 'rb') as image_file:
                        image_data = base64.b64encode(image_file.read()).decode('utf-8')

                    # Prepare upload data
                    upload_data = {
                        "api_key": self.api_key,
                        "name": Path(image_path).name,
                        "image": image_data,
                        "batch": batch_name
                    }

                    # Upload image
                    response = requests.post(upload_url, json=upload_data)

                    if response.status_code == 200:
                        successful_uploads += 1
                        upload_results.append({
                            "image": Path(image_path).name,
                            "status": "success",
                            "response": response.json()
                        })
                    else:
                        failed_uploads += 1
                        upload_results.append({
                            "image": Path(image_path).name,
                            "status": "failed",
                            "error": response.text
                        })

                    # Rate limiting
                    time.sleep(0.1)

                except Exception as e:
                    failed_uploads += 1
                    upload_results.append({
                        "image": Path(image_path).name,
                        "status": "error",
                        "error": str(e)
                    })

            logger.info(f"Upload complete - Success: {successful_uploads}, Failed: {failed_uploads}")

            return {
                "batch_name": batch_name,
                "successful_uploads": successful_uploads,
                "failed_uploads": failed_uploads,
                "results": upload_results
            }

        except Exception as e:
            logger.error(f"Error uploading image batch: {e}")
            return {"successful_uploads": 0, "failed_uploads": len(image_paths), "error": str(e)}

    def download_dataset(self, project_id: str, version: int, format_type: str = "coco") -> str:
        """Download dataset from Roboflow"""
        try:
            download_url = f"{self.base_url}/v1/workspaces/{self.workspace}/projects/{project_id}/versions/{version}/download/{format_type}"

            params = {"api_key": self.api_key}
            response = requests.get(download_url, params=params, stream=True)

            if response.status_code == 200:
                # Create project directory
                project_dir = self.dataset_root / project_id
                project_dir.mkdir(parents=True, exist_ok=True)

                # Save zip file
                zip_path = project_dir / f"{project_id}_v{version}_{format_type}.zip"
                with open(zip_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)

                # Extract dataset
                extract_dir = project_dir / f"v{version}_{format_type}"
                with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                    zip_ref.extractall(extract_dir)

                # Remove zip file
                zip_path.unlink()

                logger.info(f"Downloaded dataset: {extract_dir}")
                return str(extract_dir)

            else:
                logger.error(f"Failed to download dataset: {response.status_code}")
                return ""

        except Exception as e:
            logger.error(f"Error downloading dataset: {e}")
            return ""

    def create_dataset_version(self, project_id: str, augmentation_config: Dict = None,
                             preprocessing_config: Dict = None) -> int:
        """Create new dataset version with augmentation and preprocessing"""
        try:
            url = f"{self.base_url}/v1/workspaces/{self.workspace}/projects/{project_id}/versions"

            # Default augmentation for Star Wars costumes
            default_augmentation = {
                "flip": {"horizontal": True, "vertical": False},
                "rotation": {"degrees": 15},
                "shear": {"horizontal": 5, "vertical": 5},
                "brightness": {"variance": 20},
                "exposure": {"variance": 20},
                "blur": {"pixels": 1},
                "noise": {"variance": 5}
            }

            # Default preprocessing
            default_preprocessing = {
                "resize": {"width": 640, "height": 640, "format": "stretch"},
                "auto-orient": True,
                "contrast": {"type": "adaptive"},
                "filter": {"type": "grayscale", "value": False}
            }

            version_config = {
                "augmentation": augmentation_config or default_augmentation,
                "preprocessing": preprocessing_config or default_preprocessing,
                "splits": {
                    "train": 70,
                    "valid": 20,
                    "test": 10
                }
            }

            response = requests.post(url, headers=self.headers, json=version_config)

            if response.status_code == 201:
                version_data = response.json()
                version_number = version_data.get("version", 1)
                logger.info(f"Created dataset version {version_number} for {project_id}")
                return version_number
            else:
                logger.error(f"Failed to create version: {response.status_code} - {response.text}")
                return 0

        except Exception as e:
            logger.error(f"Error creating dataset version: {e}")
            return 0

    def train_model(self, project_id: str, version: int, model_type: str = "yolov8n") -> str:
        """Trigger model training on Roboflow"""
        try:
            train_url = f"{self.base_url}/v1/workspaces/{self.workspace}/projects/{project_id}/versions/{version}/train"

            train_config = {
                "model": model_type,
                "epochs": 100,
                "batch_size": 16,
                "learning_rate": 0.001,
                "early_stopping_patience": 10
            }

            response = requests.post(train_url, headers=self.headers, json=train_config)

            if response.status_code == 200:
                training_data = response.json()
                training_id = training_data.get("training_id", "")
                logger.info(f"Started training job: {training_id}")
                return training_id
            else:
                logger.error(f"Failed to start training: {response.status_code} - {response.text}")
                return ""

        except Exception as e:
            logger.error(f"Error starting model training: {e}")
            return ""

    def check_training_status(self, project_id: str, training_id: str) -> Dict[str, Any]:
        """Check training status"""
        try:
            status_url = f"{self.base_url}/v1/workspaces/{self.workspace}/projects/{project_id}/training/{training_id}"

            response = requests.get(status_url, headers=self.headers)

            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Failed to get training status: {response.status_code}")
                return {}

        except Exception as e:
            logger.error(f"Error checking training status: {e}")
            return {}

    def deploy_model(self, project_id: str, version: int, deployment_config: Dict = None) -> Dict[str, Any]:
        """Deploy trained model for inference"""
        try:
            deploy_url = f"{self.base_url}/v1/workspaces/{self.workspace}/projects/{project_id}/versions/{version}/deploy"

            default_config = {
                "deployment_type": "hosted_api",
                "name": f"{project_id}_deployment",
                "confidence_threshold": 0.7,
                "overlap_threshold": 0.4
            }

            config = deployment_config or default_config

            response = requests.post(deploy_url, headers=self.headers, json=config)

            if response.status_code == 200:
                deployment_data = response.json()
                logger.info(f"Model deployed successfully: {deployment_data.get('endpoint', '')}")
                return deployment_data
            else:
                logger.error(f"Failed to deploy model: {response.status_code} - {response.text}")
                return {}

        except Exception as e:
            logger.error(f"Error deploying model: {e}")
            return {}

class RoboflowAnnotationWorkflow:
    """Automated annotation workflow for Star Wars costumes"""

    def __init__(self, dataset_manager: RoboflowDatasetManager):
        self.dataset_manager = dataset_manager
        self.annotation_templates = self._load_annotation_templates()

    def _load_annotation_templates(self) -> Dict[str, Any]:
        """Load annotation templates for different costume types"""
        return {
            "jedi": {
                "color_ranges": {
                    "brown": [(10, 50, 20), (20, 255, 200)],  # HSV ranges
                    "beige": [(15, 30, 100), (25, 100, 255)]
                },
                "key_features": ["robe", "belt", "lightsaber"],
                "typical_poses": ["standing", "combat_stance"]
            },
            "sith": {
                "color_ranges": {
                    "black": [(0, 0, 0), (180, 255, 50)],
                    "red": [(0, 120, 70), (10, 255, 255)]
                },
                "key_features": ["dark_robe", "red_lightsaber", "hood"],
                "typical_poses": ["menacing", "combat_stance"]
            },
            "stormtrooper": {
                "color_ranges": {
                    "white": [(0, 0, 200), (180, 30, 255)]
                },
                "key_features": ["helmet", "armor", "blaster"],
                "typical_poses": ["standing", "marching"]
            },
            "rebel_alliance": {
                "color_ranges": {
                    "orange": [(5, 100, 100), (15, 255, 255)]
                },
                "key_features": ["pilot_suit", "helmet", "insignia"],
                "typical_poses": ["standing", "heroic"]
            }
        }

    def auto_suggest_annotations(self, image_path: str) -> List[Dict[str, Any]]:
        """Automatically suggest annotations for Star Wars costumes"""
        try:
            image = cv2.imread(image_path)
            if image is None:
                return []

            suggestions = []

            # Convert to HSV for better color detection
            hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)

            for costume_type, template in self.annotation_templates.items():
                confidence = self._calculate_costume_confidence(image, hsv, template)

                if confidence > 0.3:  # Threshold for suggestion
                    # Detect potential bounding box
                    bbox = self._detect_person_bbox(image)

                    if bbox:
                        suggestion = {
                            "class": costume_type,
                            "confidence": confidence,
                            "bbox": bbox,
                            "features_detected": self._detect_features(image, template)
                        }
                        suggestions.append(suggestion)

            # Sort by confidence
            suggestions.sort(key=lambda x: x["confidence"], reverse=True)
            return suggestions

        except Exception as e:
            logger.error(f"Error in auto-annotation: {e}")
            return []

    def _calculate_costume_confidence(self, image: np.ndarray, hsv: np.ndarray,
                                    template: Dict[str, Any]) -> float:
        """Calculate confidence score for costume detection"""
        try:
            color_confidence = 0.0
            total_pixels = image.shape[0] * image.shape[1]

            # Check color matches
            for color_name, (lower, upper) in template["color_ranges"].items():
                mask = cv2.inRange(hsv, np.array(lower), np.array(upper))
                color_pixels = cv2.countNonZero(mask)
                color_ratio = color_pixels / total_pixels

                if color_ratio > 0.1:  # At least 10% of image
                    color_confidence += color_ratio * 0.5

            # Add feature detection confidence (simplified)
            feature_confidence = len(template["key_features"]) * 0.1

            return min(color_confidence + feature_confidence, 1.0)

        except Exception as e:
            logger.error(f"Error calculating costume confidence: {e}")
            return 0.0

    def _detect_person_bbox(self, image: np.ndarray) -> Optional[Tuple[int, int, int, int]]:
        """Detect person bounding box using simple methods"""
        try:
            # Use OpenCV's HOG person detector as fallback
            hog = cv2.HOGDescriptor()
            hog.setSVMDetector(cv2.HOGDescriptor_getDefaultPeopleDetector())

            boxes, weights = hog.detectMultiScale(image, winStride=(8, 8))

            if len(boxes) > 0:
                # Return first detection
                x, y, w, h = boxes[0]
                return (x, y, x + w, y + h)

            return None

        except Exception as e:
            logger.error(f"Error detecting person bbox: {e}")
            return None

    def _detect_features(self, image: np.ndarray, template: Dict[str, Any]) -> List[str]:
        """Detect key costume features"""
        detected_features = []

        # Simplified feature detection
        for feature in template["key_features"]:
            if self._detect_single_feature(image, feature):
                detected_features.append(feature)

        return detected_features

    def _detect_single_feature(self, image: np.ndarray, feature: str) -> bool:
        """Detect single costume feature (simplified)"""
        # This would implement specific feature detection
        # For now, return random confidence for demonstration
        return np.random.random() > 0.5

    def batch_annotate_images(self, image_directory: str, output_directory: str) -> Dict[str, Any]:
        """Batch annotate images with suggestions"""
        try:
            image_dir = Path(image_directory)
            output_dir = Path(output_directory)
            output_dir.mkdir(parents=True, exist_ok=True)

            image_extensions = ['.jpg', '.jpeg', '.png', '.bmp']
            image_paths = []

            for ext in image_extensions:
                image_paths.extend(list(image_dir.glob(f'*{ext}')))
                image_paths.extend(list(image_dir.glob(f'*{ext.upper()}')))

            annotation_results = []

            for image_path in image_paths:
                suggestions = self.auto_suggest_annotations(str(image_path))

                if suggestions:
                    # Create annotation file
                    annotation_file = output_dir / f"{image_path.stem}.json"

                    annotation_data = {
                        "image_path": str(image_path),
                        "image_name": image_path.name,
                        "suggestions": suggestions,
                        "timestamp": datetime.now().isoformat(),
                        "status": "suggested"
                    }

                    with open(annotation_file, 'w') as f:
                        json.dump(annotation_data, f, indent=2)

                    annotation_results.append({
                        "image": image_path.name,
                        "suggestions_count": len(suggestions),
                        "annotation_file": str(annotation_file)
                    })

            logger.info(f"Batch annotation completed: {len(annotation_results)} images processed")

            return {
                "processed_images": len(annotation_results),
                "total_images": len(image_paths),
                "results": annotation_results
            }

        except Exception as e:
            logger.error(f"Error in batch annotation: {e}")
            return {"processed_images": 0, "error": str(e)}

class R2D2DatasetPipeline:
    """Complete dataset pipeline for R2D2 computer vision"""

    def __init__(self, api_key: str, workspace: str):
        self.dataset_manager = RoboflowDatasetManager(api_key, workspace)
        self.annotation_workflow = RoboflowAnnotationWorkflow(self.dataset_manager)

        # Pipeline configuration
        self.pipeline_config = {
            "star_wars_costumes": {
                "collection_sources": [
                    "convention_photos",
                    "cosplay_references",
                    "movie_stills"
                ],
                "quality_requirements": {
                    "min_resolution": (640, 480),
                    "min_person_size": (100, 200),
                    "brightness_range": (50, 200),
                    "blur_threshold": 50
                },
                "augmentation_strategy": "conservative"  # Preserve costume authenticity
            }
        }

    def setup_complete_pipeline(self) -> bool:
        """Setup complete data pipeline for R2D2"""
        try:
            logger.info("Setting up complete R2D2 data pipeline...")

            # 1. Create projects if they don't exist
            for project_name, config in self.dataset_manager.projects.items():
                project_id = config["project_id"]

                # Create project (will fail gracefully if exists)
                self.dataset_manager.create_project(project_name, "object-detection")

            # 2. Setup local dataset structure
            self._setup_local_dataset_structure()

            # 3. Create initial dataset versions
            for project_name, config in self.dataset_manager.projects.items():
                project_id = config["project_id"]

                # Create augmentation config specific to Star Wars
                aug_config = self._get_star_wars_augmentation_config()

                version = self.dataset_manager.create_dataset_version(
                    project_id, aug_config
                )

                if version > 0:
                    logger.info(f"Created version {version} for {project_id}")

            logger.info("R2D2 data pipeline setup completed")
            return True

        except Exception as e:
            logger.error(f"Error setting up pipeline: {e}")
            return False

    def _setup_local_dataset_structure(self):
        """Setup local dataset directory structure"""
        base_dir = self.dataset_manager.dataset_root

        # Create directory structure
        directories = [
            "star_wars_costumes/raw_images",
            "star_wars_costumes/annotated",
            "star_wars_costumes/processed",
            "guest_detection/raw_images",
            "guest_detection/annotated",
            "validation_sets",
            "test_sets",
            "deployment_models"
        ]

        for directory in directories:
            (base_dir / directory).mkdir(parents=True, exist_ok=True)

    def _get_star_wars_augmentation_config(self) -> Dict[str, Any]:
        """Get Star Wars specific augmentation configuration"""
        return {
            "flip": {"horizontal": True, "vertical": False},
            "rotation": {"degrees": 10},  # Conservative rotation
            "brightness": {"variance": 15},  # Preserve costume colors
            "exposure": {"variance": 10},
            "blur": {"pixels": 0.5},  # Minimal blur to preserve details
            "noise": {"variance": 3},  # Minimal noise
            "crop": {"percent": 5},  # Small crops to maintain costume visibility
            "shear": {"horizontal": 3, "vertical": 3}  # Minimal shear
        }

    def run_full_training_pipeline(self, project_id: str) -> Dict[str, Any]:
        """Run complete training pipeline"""
        try:
            logger.info(f"Running full training pipeline for {project_id}...")

            pipeline_results = {
                "project_id": project_id,
                "stages": {},
                "start_time": datetime.now().isoformat()
            }

            # Stage 1: Data upload and annotation
            logger.info("Stage 1: Data upload and annotation")
            upload_results = self._upload_and_annotate_data(project_id)
            pipeline_results["stages"]["upload"] = upload_results

            # Stage 2: Create dataset version
            logger.info("Stage 2: Create dataset version")
            version = self.dataset_manager.create_dataset_version(
                project_id, self._get_star_wars_augmentation_config()
            )
            pipeline_results["stages"]["version_creation"] = {"version": version}

            if version == 0:
                raise Exception("Failed to create dataset version")

            # Stage 3: Start training
            logger.info("Stage 3: Start model training")
            training_id = self.dataset_manager.train_model(project_id, version, "yolov8n")
            pipeline_results["stages"]["training"] = {"training_id": training_id}

            if not training_id:
                raise Exception("Failed to start training")

            # Stage 4: Monitor training (simplified)
            logger.info("Stage 4: Monitor training progress")
            training_status = self._monitor_training(project_id, training_id)
            pipeline_results["stages"]["training_status"] = training_status

            # Stage 5: Deploy model (if training successful)
            if training_status.get("status") == "completed":
                logger.info("Stage 5: Deploy model")
                deployment = self.dataset_manager.deploy_model(project_id, version)
                pipeline_results["stages"]["deployment"] = deployment

            pipeline_results["end_time"] = datetime.now().isoformat()
            pipeline_results["success"] = True

            logger.info(f"Training pipeline completed for {project_id}")
            return pipeline_results

        except Exception as e:
            logger.error(f"Error in training pipeline: {e}")
            return {
                "project_id": project_id,
                "success": False,
                "error": str(e),
                "end_time": datetime.now().isoformat()
            }

    def _upload_and_annotate_data(self, project_id: str) -> Dict[str, Any]:
        """Upload and annotate data for project"""
        try:
            # Find images in local dataset
            project_dir = self.dataset_manager.dataset_root / project_id.replace("-", "_") / "raw_images"

            if not project_dir.exists():
                return {"uploaded_images": 0, "error": "No raw images directory found"}

            # Get image files
            image_extensions = ['.jpg', '.jpeg', '.png']
            image_paths = []

            for ext in image_extensions:
                image_paths.extend(list(project_dir.glob(f'*{ext}')))

            if not image_paths:
                return {"uploaded_images": 0, "error": "No images found"}

            # Upload images
            upload_results = self.dataset_manager.upload_image_batch(
                project_id, [str(p) for p in image_paths]
            )

            # Generate annotations
            annotation_dir = self.dataset_manager.dataset_root / project_id.replace("-", "_") / "annotated"
            annotation_results = self.annotation_workflow.batch_annotate_images(
                str(project_dir), str(annotation_dir)
            )

            return {
                "upload_results": upload_results,
                "annotation_results": annotation_results
            }

        except Exception as e:
            logger.error(f"Error uploading and annotating data: {e}")
            return {"error": str(e)}

    def _monitor_training(self, project_id: str, training_id: str, max_wait_time: int = 3600) -> Dict[str, Any]:
        """Monitor training progress (simplified)"""
        try:
            start_time = time.time()
            last_status = {}

            while time.time() - start_time < max_wait_time:
                status = self.dataset_manager.check_training_status(project_id, training_id)

                if status.get("status") in ["completed", "failed"]:
                    return status

                # Log progress if changed
                if status != last_status:
                    logger.info(f"Training status: {status.get('status', 'unknown')}")
                    last_status = status

                time.sleep(60)  # Check every minute

            return {"status": "timeout", "message": "Training monitoring timed out"}

        except Exception as e:
            logger.error(f"Error monitoring training: {e}")
            return {"status": "error", "error": str(e)}

# Configuration and setup
def get_roboflow_config() -> Dict[str, str]:
    """Get Roboflow configuration"""
    # In production, these would come from environment variables
    return {
        "api_key": os.getenv("ROBOFLOW_API_KEY", "your_api_key_here"),
        "workspace": os.getenv("ROBOFLOW_WORKSPACE", "r2d2-computer-vision")
    }

# Main workflow
def main():
    """Main Roboflow integration workflow"""
    try:
        config = get_roboflow_config()

        # Initialize pipeline
        pipeline = R2D2DatasetPipeline(config["api_key"], config["workspace"])

        # Setup complete pipeline
        if pipeline.setup_complete_pipeline():
            logger.info("Pipeline setup successful")

            # Run training for Star Wars costumes
            results = pipeline.run_full_training_pipeline("star-wars-costumes")

            logger.info(f"Training pipeline results: {results['success']}")

            if results["success"]:
                # Save results
                results_path = pipeline.dataset_manager.dataset_root / "training_results.json"
                with open(results_path, 'w') as f:
                    json.dump(results, f, indent=2)

                logger.info(f"Results saved to: {results_path}")

        else:
            logger.error("Pipeline setup failed")

    except Exception as e:
        logger.error(f"Error in main workflow: {e}")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()