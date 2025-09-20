#!/usr/bin/env python3
"""
YOLO Model Training Pipeline for R2D2 Guest Detection
Optimized training pipeline for person detection with R2D2-specific requirements
"""

import torch
import torch.nn as nn
from ultralytics import YOLO
import cv2
import numpy as np
import json
import os
import time
from pathlib import Path
import logging
from typing import Dict, List, Tuple, Optional, Any
import matplotlib.pyplot as plt
from datetime import datetime
import yaml
from roboflow import Roboflow
import tensorrt as trt
import pycuda.driver as cuda
import pycuda.autoinit

logger = logging.getLogger(__name__)

class R2D2YOLOTrainer:
    """Specialized YOLO trainer for R2D2 guest detection requirements"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.model = None
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

        # Training paths
        self.model_dir = Path("/home/rolo/r2ai/.claude/agent_storage/video-model-trainer/models")
        self.data_dir = Path("/home/rolo/r2ai/.claude/agent_storage/video-model-trainer/datasets")
        self.results_dir = Path("/home/rolo/r2ai/.claude/agent_storage/video-model-trainer/results")

        # Create directories
        for directory in [self.model_dir, self.data_dir, self.results_dir]:
            directory.mkdir(parents=True, exist_ok=True)

        # R2D2 specific requirements
        self.r2d2_requirements = {
            'max_inference_time': 0.05,  # 50ms for real-time interaction
            'min_accuracy': 0.95,        # 95% accuracy for reliable interactions
            'distance_range': (0.5, 8.0), # Detection range in meters
            'angle_coverage': 120,        # Degrees of coverage
            'lighting_conditions': ['indoor', 'outdoor', 'mixed', 'low_light']
        }

    def prepare_dataset(self, roboflow_workspace: str = None, roboflow_project: str = None):
        """Prepare dataset optimized for R2D2 guest detection"""
        logger.info("Preparing R2D2-optimized guest detection dataset...")

        try:
            if roboflow_workspace and roboflow_project:
                # Download from Roboflow
                rf = Roboflow(api_key=self.config.get('roboflow_api_key'))
                project = rf.workspace(roboflow_workspace).project(roboflow_project)
                dataset = project.version(self.config.get('dataset_version', 1)).download("yolov8")
                dataset_path = Path(dataset.location)
            else:
                # Use local dataset or create synthetic data
                dataset_path = self.data_dir / "guest_detection"
                self._create_r2d2_optimized_dataset(dataset_path)

            # Modify dataset.yaml for R2D2 requirements
            self._optimize_dataset_config(dataset_path)

            logger.info(f"Dataset prepared at: {dataset_path}")
            return dataset_path

        except Exception as e:
            logger.error(f"Error preparing dataset: {e}")
            return None

    def _create_r2d2_optimized_dataset(self, dataset_path: Path):
        """Create R2D2-optimized dataset configuration"""
        dataset_path.mkdir(parents=True, exist_ok=True)

        # Create dataset.yaml optimized for R2D2
        dataset_config = {
            'path': str(dataset_path),
            'train': 'train/images',
            'val': 'val/images',
            'test': 'test/images',
            'names': {
                0: 'person'  # Focus on person detection
            },
            'nc': 1,  # Number of classes

            # R2D2 specific metadata
            'r2d2_optimization': {
                'target_environment': 'convention_hall',
                'distance_range': self.r2d2_requirements['distance_range'],
                'lighting_conditions': self.r2d2_requirements['lighting_conditions'],
                'crowd_scenarios': ['single_person', 'small_group', 'crowd'],
                'costume_diversity': True,
                'age_diversity': ['child', 'teenager', 'adult', 'senior']
            }
        }

        with open(dataset_path / 'dataset.yaml', 'w') as f:
            yaml.dump(dataset_config, f, default_flow_style=False)

    def _optimize_dataset_config(self, dataset_path: Path):
        """Optimize dataset configuration for R2D2 requirements"""
        yaml_path = dataset_path / 'dataset.yaml'

        if yaml_path.exists():
            with open(yaml_path, 'r') as f:
                config = yaml.safe_load(f)

            # Add R2D2 optimization parameters
            config['r2d2_optimization'] = {
                'target_fps': 30,
                'max_inference_time': self.r2d2_requirements['max_inference_time'],
                'min_confidence': 0.7,
                'nms_threshold': 0.4,
                'input_size': [640, 640],  # Optimized for Orin Nano
                'batch_size': 1,           # Real-time single frame processing
            }

            with open(yaml_path, 'w') as f:
                yaml.dump(config, f, default_flow_style=False)

    def train_model(self, dataset_path: Path, model_size: str = 'n') -> bool:
        """Train YOLO model optimized for R2D2 requirements"""
        logger.info(f"Starting YOLO{model_size} training for R2D2 guest detection...")

        try:
            # Initialize model
            base_model = f'yolov8{model_size}.pt'
            self.model = YOLO(base_model)

            # Training parameters optimized for R2D2
            training_args = {
                'data': str(dataset_path / 'dataset.yaml'),
                'epochs': self.config.get('epochs', 100),
                'batch': self.config.get('batch_size', 16),
                'imgsz': 640,  # Optimal for Orin Nano
                'device': 'cuda' if torch.cuda.is_available() else 'cpu',
                'workers': 8,
                'project': str(self.results_dir),
                'name': f'r2d2_guest_detection_{model_size}',
                'exist_ok': True,
                'pretrained': True,
                'optimizer': 'AdamW',
                'lr0': 0.01,
                'lrf': 0.01,
                'momentum': 0.937,
                'weight_decay': 0.0005,
                'warmup_epochs': 3,
                'warmup_momentum': 0.8,
                'warmup_bias_lr': 0.1,
                'box': 7.5,
                'cls': 0.5,
                'dfl': 1.5,
                'pose': 12.0,
                'kobj': 1.0,
                'label_smoothing': 0.0,
                'nbs': 64,
                'overlap_mask': True,
                'mask_ratio': 4,
                'dropout': 0.0,
                'val': True,
                'plots': True,
                'save': True,
                'save_period': 10,
                'cache': False,
                'copy_paste': 0.0,
                'mixup': 0.0,
                'degrees': 0.0,
                'translate': 0.1,
                'scale': 0.5,
                'shear': 0.0,
                'perspective': 0.0,
                'flipud': 0.0,
                'fliplr': 0.5,
                'mosaic': 1.0,
                'close_mosaic': 10,
                'erasing': 0.4,
                'crop_fraction': 1.0,
                'auto_augment': 'randaugment',
                'hsv_h': 0.015,
                'hsv_s': 0.7,
                'hsv_v': 0.4
            }

            # Start training
            start_time = time.time()
            results = self.model.train(**training_args)
            training_time = time.time() - start_time

            # Save training results
            self._save_training_results(results, training_time, model_size)

            logger.info(f"Training completed in {training_time/3600:.2f} hours")
            return True

        except Exception as e:
            logger.error(f"Error during training: {e}")
            return False

    def _save_training_results(self, results, training_time: float, model_size: str):
        """Save comprehensive training results"""
        try:
            results_data = {
                'model_size': model_size,
                'training_time_hours': training_time / 3600,
                'timestamp': datetime.now().isoformat(),
                'r2d2_requirements': self.r2d2_requirements,
                'training_config': self.config,
                'results_summary': {
                    'best_fitness': float(results.fitness) if hasattr(results, 'fitness') else None,
                    'final_epoch': len(results.results) if hasattr(results, 'results') else None,
                }
            }

            # Save to JSON
            results_file = self.results_dir / f'training_results_{model_size}_{int(time.time())}.json'
            with open(results_file, 'w') as f:
                json.dump(results_data, f, indent=2)

            logger.info(f"Training results saved to: {results_file}")

        except Exception as e:
            logger.error(f"Error saving training results: {e}")

    def validate_model(self, model_path: str) -> Dict[str, Any]:
        """Validate model against R2D2 requirements"""
        logger.info("Validating model against R2D2 requirements...")

        try:
            # Load model
            model = YOLO(model_path)

            # Performance validation
            validation_results = {
                'inference_speed': self._test_inference_speed(model),
                'accuracy_metrics': self._test_accuracy(model),
                'robustness_tests': self._test_robustness(model),
                'r2d2_compliance': {}
            }

            # Check R2D2 compliance
            compliance = self._check_r2d2_compliance(validation_results)
            validation_results['r2d2_compliance'] = compliance

            # Save validation results
            validation_file = self.results_dir / f'validation_results_{int(time.time())}.json'
            with open(validation_file, 'w') as f:
                json.dump(validation_results, f, indent=2)

            logger.info(f"Validation completed. Results saved to: {validation_file}")
            return validation_results

        except Exception as e:
            logger.error(f"Error during validation: {e}")
            return {}

    def _test_inference_speed(self, model) -> Dict[str, float]:
        """Test inference speed on sample images"""
        logger.info("Testing inference speed...")

        # Create test image
        test_image = np.random.randint(0, 255, (640, 640, 3), dtype=np.uint8)

        # Warmup
        for _ in range(10):
            model(test_image, verbose=False)

        # Time inference
        times = []
        for _ in range(100):
            start_time = time.time()
            model(test_image, verbose=False)
            times.append(time.time() - start_time)

        return {
            'avg_inference_time': np.mean(times),
            'min_inference_time': np.min(times),
            'max_inference_time': np.max(times),
            'fps_estimate': 1.0 / np.mean(times)
        }

    def _test_accuracy(self, model) -> Dict[str, float]:
        """Test model accuracy"""
        logger.info("Testing model accuracy...")

        try:
            # Run validation on test set
            val_results = model.val()

            return {
                'map50': float(val_results.box.map50),
                'map50_95': float(val_results.box.map),
                'precision': float(val_results.box.mp),
                'recall': float(val_results.box.mr)
            }
        except Exception as e:
            logger.warning(f"Could not run accuracy test: {e}")
            return {}

    def _test_robustness(self, model) -> Dict[str, Any]:
        """Test model robustness under various conditions"""
        logger.info("Testing model robustness...")

        robustness_results = {
            'lighting_conditions': {},
            'image_quality': {},
            'crowd_scenarios': {}
        }

        # Test different lighting conditions
        for lighting in ['normal', 'low_light', 'bright', 'mixed']:
            test_image = self._generate_test_image(lighting_condition=lighting)
            results = model(test_image, verbose=False)
            robustness_results['lighting_conditions'][lighting] = {
                'detections': len(results[0].boxes) if results[0].boxes is not None else 0,
                'avg_confidence': float(np.mean(results[0].boxes.conf.cpu())) if results[0].boxes is not None and len(results[0].boxes) > 0 else 0.0
            }

        return robustness_results

    def _generate_test_image(self, lighting_condition: str = 'normal') -> np.ndarray:
        """Generate synthetic test image for robustness testing"""
        # Create base image
        img = np.random.randint(0, 255, (640, 640, 3), dtype=np.uint8)

        # Modify based on lighting condition
        if lighting_condition == 'low_light':
            img = (img * 0.3).astype(np.uint8)
        elif lighting_condition == 'bright':
            img = np.clip(img * 1.5, 0, 255).astype(np.uint8)
        elif lighting_condition == 'mixed':
            # Add gradient lighting
            gradient = np.linspace(0.3, 1.2, 640).reshape(1, -1, 1)
            img = np.clip(img * gradient, 0, 255).astype(np.uint8)

        return img

    def _check_r2d2_compliance(self, validation_results: Dict[str, Any]) -> Dict[str, bool]:
        """Check if model meets R2D2 requirements"""
        compliance = {}

        # Check inference speed
        avg_time = validation_results.get('inference_speed', {}).get('avg_inference_time', float('inf'))
        compliance['inference_speed'] = avg_time <= self.r2d2_requirements['max_inference_time']

        # Check accuracy
        map50 = validation_results.get('accuracy_metrics', {}).get('map50', 0.0)
        compliance['accuracy'] = map50 >= self.r2d2_requirements['min_accuracy']

        # Check FPS
        fps = validation_results.get('inference_speed', {}).get('fps_estimate', 0.0)
        compliance['real_time_performance'] = fps >= 30.0  # 30 FPS minimum

        # Overall compliance
        compliance['overall'] = all(compliance.values())

        return compliance

    def optimize_for_tensorrt(self, model_path: str) -> str:
        """Optimize model for TensorRT deployment on Orin Nano"""
        logger.info("Optimizing model for TensorRT deployment...")

        try:
            # Load model
            model = YOLO(model_path)

            # Export to TensorRT
            trt_path = model_path.replace('.pt', '_tensorrt.engine')
            model.export(
                format='engine',
                device=0,
                half=True,  # FP16 precision
                workspace=4,  # 4GB workspace
                verbose=True
            )

            # Validate TensorRT model
            self._validate_tensorrt_model(trt_path)

            logger.info(f"TensorRT model created: {trt_path}")
            return trt_path

        except Exception as e:
            logger.error(f"Error creating TensorRT model: {e}")
            return ""

    def _validate_tensorrt_model(self, trt_path: str):
        """Validate TensorRT model performance"""
        try:
            # Load TensorRT engine
            model = YOLO(trt_path)

            # Test inference speed
            test_image = np.random.randint(0, 255, (640, 640, 3), dtype=np.uint8)

            # Warmup
            for _ in range(10):
                model(test_image, verbose=False)

            # Time inference
            times = []
            for _ in range(50):
                start_time = time.time()
                model(test_image, verbose=False)
                times.append(time.time() - start_time)

            avg_time = np.mean(times)
            fps = 1.0 / avg_time

            logger.info(f"TensorRT Performance: {avg_time*1000:.1f}ms avg, {fps:.1f} FPS")

            # Check if meets requirements
            if avg_time <= self.r2d2_requirements['max_inference_time']:
                logger.info("✅ TensorRT model meets R2D2 speed requirements")
            else:
                logger.warning("⚠️  TensorRT model does not meet speed requirements")

        except Exception as e:
            logger.error(f"Error validating TensorRT model: {e}")

    def create_deployment_package(self, model_path: str) -> str:
        """Create complete deployment package for R2D2"""
        logger.info("Creating R2D2 deployment package...")

        try:
            package_dir = self.model_dir / f"r2d2_deployment_{int(time.time())}"
            package_dir.mkdir(parents=True, exist_ok=True)

            # Copy model files
            model_files = [model_path]
            if model_path.endswith('.pt'):
                # Try to include TensorRT version
                trt_path = model_path.replace('.pt', '_tensorrt.engine')
                if Path(trt_path).exists():
                    model_files.append(trt_path)

            for model_file in model_files:
                if Path(model_file).exists():
                    import shutil
                    shutil.copy2(model_file, package_dir / Path(model_file).name)

            # Create deployment configuration
            deployment_config = {
                'model_info': {
                    'primary_model': Path(model_path).name,
                    'tensorrt_model': Path(model_path.replace('.pt', '_tensorrt.engine')).name if Path(model_path.replace('.pt', '_tensorrt.engine')).exists() else None,
                    'input_size': [640, 640],
                    'classes': ['person'],
                    'confidence_threshold': 0.7,
                    'nms_threshold': 0.4
                },
                'r2d2_requirements': self.r2d2_requirements,
                'deployment_instructions': {
                    'target_device': 'Nvidia Orin Nano',
                    'runtime': 'TensorRT',
                    'precision': 'FP16',
                    'batch_size': 1,
                    'memory_requirement': '2GB',
                    'expected_performance': '30+ FPS'
                },
                'integration_api': {
                    'input_format': 'BGR numpy array',
                    'output_format': 'Detection objects with bbox, confidence, class',
                    'callback_functions': ['motion_api_callback', 'audio_api_callback']
                }
            }

            with open(package_dir / 'deployment_config.json', 'w') as f:
                json.dump(deployment_config, f, indent=2)

            # Create integration script
            self._create_integration_script(package_dir)

            logger.info(f"Deployment package created: {package_dir}")
            return str(package_dir)

        except Exception as e:
            logger.error(f"Error creating deployment package: {e}")
            return ""

    def _create_integration_script(self, package_dir: Path):
        """Create integration script for R2D2 system"""
        integration_script = '''#!/usr/bin/env python3
"""
R2D2 YOLO Model Integration Script
Ready-to-use guest detection for R2D2 interactions
"""

import cv2
import numpy as np
from ultralytics import YOLO
import json
import time
from pathlib import Path

class R2D2GuestDetector:
    """Optimized guest detector for R2D2 real-time interactions"""

    def __init__(self, model_path: str, config_path: str = "deployment_config.json"):
        self.model = YOLO(model_path)

        # Load configuration
        with open(config_path, 'r') as f:
            self.config = json.load(f)

        self.confidence_threshold = self.config['model_info']['confidence_threshold']
        self.nms_threshold = self.config['model_info']['nms_threshold']

    def detect_guests(self, frame: np.ndarray) -> list:
        """Detect guests in frame with R2D2 optimization"""
        start_time = time.time()

        # Run inference
        results = self.model(frame,
                           conf=self.confidence_threshold,
                           iou=self.nms_threshold,
                           verbose=False)

        # Extract detections
        detections = []
        if results[0].boxes is not None:
            for box in results[0].boxes:
                x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                confidence = float(box.conf[0])

                detections.append({
                    'bbox': [int(x1), int(y1), int(x2-x1), int(y2-y1)],
                    'confidence': confidence,
                    'class': 'person',
                    'timestamp': time.time()
                })

        inference_time = time.time() - start_time

        return {
            'detections': detections,
            'inference_time': inference_time,
            'fps_estimate': 1.0 / inference_time if inference_time > 0 else 0
        }

# Example usage
if __name__ == "__main__":
    detector = R2D2GuestDetector("best.pt")

    # Initialize camera
    cap = cv2.VideoCapture(0)

    while True:
        ret, frame = cap.read()
        if ret:
            results = detector.detect_guests(frame)
            print(f"Detected {len(results['detections'])} guests, "
                  f"FPS: {results['fps_estimate']:.1f}")

            # Visualize
            for detection in results['detections']:
                x, y, w, h = detection['bbox']
                cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
                cv2.putText(frame, f"Guest {detection['confidence']:.2f}",
                           (x, y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

            cv2.imshow('R2D2 Guest Detection', frame)

            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

    cap.release()
    cv2.destroyAllWindows()
'''

        with open(package_dir / 'r2d2_integration.py', 'w') as f:
            f.write(integration_script)

# Training configuration for R2D2 guest detection
def get_r2d2_training_config():
    """Get optimized training configuration for R2D2 guest detection"""
    return {
        'epochs': 100,
        'batch_size': 16,
        'roboflow_api_key': None,  # Set your Roboflow API key
        'dataset_version': 1,
        'model_sizes': ['n', 's'],  # Start with nano and small for speed
        'optimization_target': 'speed',  # 'speed' or 'accuracy'
        'tensorrt_optimization': True,
        'fp16_precision': True
    }

# Main training execution
async def main():
    """Main training execution for R2D2 guest detection"""
    config = get_r2d2_training_config()
    trainer = R2D2YOLOTrainer(config)

    # Prepare dataset
    dataset_path = trainer.prepare_dataset()
    if not dataset_path:
        logger.error("Failed to prepare dataset")
        return

    # Train models
    trained_models = []
    for model_size in config['model_sizes']:
        logger.info(f"Training YOLO{model_size} for R2D2...")

        if trainer.train_model(dataset_path, model_size):
            model_path = trainer.results_dir / f'r2d2_guest_detection_{model_size}' / 'weights' / 'best.pt'
            if model_path.exists():
                # Validate model
                validation_results = trainer.validate_model(str(model_path))

                # Check if meets R2D2 requirements
                if validation_results.get('r2d2_compliance', {}).get('overall', False):
                    logger.info(f"✅ YOLO{model_size} meets R2D2 requirements")

                    # Optimize for TensorRT
                    trt_model = trainer.optimize_for_tensorrt(str(model_path))

                    # Create deployment package
                    package_path = trainer.create_deployment_package(str(model_path))

                    trained_models.append({
                        'size': model_size,
                        'model_path': str(model_path),
                        'tensorrt_path': trt_model,
                        'package_path': package_path,
                        'validation': validation_results
                    })
                else:
                    logger.warning(f"⚠️  YOLO{model_size} does not meet R2D2 requirements")

    # Generate final report
    report = {
        'training_completion': time.time(),
        'successful_models': len(trained_models),
        'models': trained_models,
        'r2d2_requirements': trainer.r2d2_requirements,
        'recommendations': []
    }

    # Add recommendations
    if trained_models:
        best_model = min(trained_models,
                        key=lambda x: x['validation']['inference_speed']['avg_inference_time'])
        report['recommendations'].append(f"Use {best_model['size']} model for optimal speed")

    # Save final report
    report_path = trainer.results_dir / 'r2d2_training_final_report.json'
    with open(report_path, 'w') as f:
        json.dump(report, f, indent=2)

    logger.info(f"Training completed. Final report: {report_path}")

if __name__ == "__main__":
    import asyncio
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())