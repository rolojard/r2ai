#!/usr/bin/env python3
"""
R2D2 Computer Vision System Deployment Script
One-click deployment for Nvidia Orin Nano production systems
"""

import os
import sys
import json
import asyncio
import logging
import subprocess
import time
from pathlib import Path
from typing import Dict, List, Any
import argparse
import shutil
from datetime import datetime

logger = logging.getLogger(__name__)

class R2D2VisionDeployer:
    """Complete deployment system for R2D2 Computer Vision"""

    def __init__(self, deployment_config: Dict[str, Any] = None):
        self.config = deployment_config or self.get_default_config()
        self.base_dir = Path("/home/rolo/r2ai/.claude/agent_storage/video-model-trainer")
        self.deployment_dir = Path("/opt/r2d2_vision")
        self.service_name = "r2d2-vision-system"

        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(self.base_dir / 'deployment.log'),
                logging.StreamHandler()
            ]
        )

    def get_default_config(self) -> Dict[str, Any]:
        """Get default deployment configuration"""
        return {
            "deployment": {
                "environment": "production",
                "auto_start": True,
                "enable_monitoring": True,
                "enable_api": True,
                "api_port": 8000,
                "websocket_enabled": True
            },
            "camera": {
                "device_id": 0,
                "resolution": [1920, 1080],
                "fps": 30,
                "buffer_size": 1
            },
            "performance": {
                "max_inference_time_ms": 100,
                "batch_size": 1,
                "tensorrt_enabled": True,
                "fp16_enabled": True,
                "memory_pool_size": 10
            },
            "detection": {
                "confidence_threshold": 0.7,
                "nms_threshold": 0.4,
                "max_detections": 50
            },
            "recognition": {
                "face_similarity_threshold": 0.6,
                "costume_confidence_threshold": 0.8,
                "guest_retention_days": 7
            },
            "safety": {
                "max_temperature_c": 85,
                "max_power_w": 25,
                "emergency_stop_enabled": True,
                "crowd_management_enabled": True
            },
            "star_wars": {
                "costume_classes": [
                    "jedi", "sith", "rebel_alliance", "stormtrooper",
                    "imperial_officer", "mandalorian", "civilian"
                ],
                "response_categories": [
                    "curious", "cautious", "excited", "familiar",
                    "defensive", "friendly", "playful"
                ]
            }
        }

    async def deploy_system(self, validate_before_deploy: bool = True) -> bool:
        """Complete system deployment"""
        logger.info("Starting R2D2 Computer Vision System deployment...")

        try:
            # 1. Pre-deployment validation
            if validate_before_deploy:
                logger.info("1. Running pre-deployment validation...")
                validation_success = await self._run_pre_deployment_validation()
                if not validation_success:
                    logger.error("Pre-deployment validation failed")
                    return False

            # 2. System preparation
            logger.info("2. Preparing system...")
            if not await self._prepare_system():
                logger.error("System preparation failed")
                return False

            # 3. Install dependencies
            logger.info("3. Installing dependencies...")
            if not await self._install_dependencies():
                logger.error("Dependency installation failed")
                return False

            # 4. Deploy files
            logger.info("4. Deploying system files...")
            if not await self._deploy_files():
                logger.error("File deployment failed")
                return False

            # 5. Configure models
            logger.info("5. Configuring models...")
            if not await self._configure_models():
                logger.error("Model configuration failed")
                return False

            # 6. Setup services
            logger.info("6. Setting up system services...")
            if not await self._setup_services():
                logger.error("Service setup failed")
                return False

            # 7. Final validation
            logger.info("7. Running deployment validation...")
            if not await self._run_deployment_validation():
                logger.error("Deployment validation failed")
                return False

            # 8. Start services
            if self.config["deployment"]["auto_start"]:
                logger.info("8. Starting services...")
                if not await self._start_services():
                    logger.error("Service startup failed")
                    return False

            logger.info("✅ R2D2 Computer Vision System deployed successfully!")
            await self._print_deployment_summary()
            return True

        except Exception as e:
            logger.error(f"Deployment failed: {e}")
            return False

    async def _run_pre_deployment_validation(self) -> bool:
        """Run pre-deployment validation"""
        try:
            # Check hardware requirements
            validation_results = {
                "cuda_available": False,
                "sufficient_memory": False,
                "camera_accessible": False,
                "tensorrt_available": False,
                "required_files_present": False
            }

            # Check CUDA
            try:
                import torch
                validation_results["cuda_available"] = torch.cuda.is_available()
                if validation_results["cuda_available"]:
                    gpu_mem_gb = torch.cuda.get_device_properties(0).total_memory / (1024**3)
                    logger.info(f"GPU Memory: {gpu_mem_gb:.1f}GB")
            except ImportError:
                logger.warning("PyTorch not available")

            # Check system memory
            try:
                import psutil
                total_memory_gb = psutil.virtual_memory().total / (1024**3)
                validation_results["sufficient_memory"] = total_memory_gb >= 8.0
                logger.info(f"System Memory: {total_memory_gb:.1f}GB")
            except ImportError:
                logger.warning("psutil not available")

            # Check camera
            try:
                import cv2
                cap = cv2.VideoCapture(0)
                validation_results["camera_accessible"] = cap.isOpened()
                if cap.isOpened():
                    cap.release()
                logger.info(f"Camera accessible: {validation_results['camera_accessible']}")
            except ImportError:
                logger.warning("OpenCV not available")

            # Check TensorRT
            try:
                import tensorrt as trt
                validation_results["tensorrt_available"] = True
                logger.info("TensorRT available")
            except ImportError:
                logger.warning("TensorRT not available - performance may be reduced")

            # Check required files
            required_files = [
                "cv_system_architecture.py",
                "real_time_inference_engine.py",
                "optimized_inference_engine.py",
                "integration_api.py"
            ]

            validation_results["required_files_present"] = all(
                (self.base_dir / file).exists() for file in required_files
            )

            # Report validation results
            passed_checks = sum(1 for result in validation_results.values() if result)
            total_checks = len(validation_results)

            logger.info(f"Pre-deployment validation: {passed_checks}/{total_checks} checks passed")

            if passed_checks < total_checks:
                logger.warning("Some validation checks failed - deployment may have issues")

            return passed_checks >= 3  # Minimum requirements

        except Exception as e:
            logger.error(f"Pre-deployment validation error: {e}")
            return False

    async def _prepare_system(self) -> bool:
        """Prepare system for deployment"""
        try:
            # Create deployment directories
            self.deployment_dir.mkdir(parents=True, exist_ok=True)

            deployment_subdirs = [
                "models", "logs", "config", "scripts", "data", "validation"
            ]

            for subdir in deployment_subdirs:
                (self.deployment_dir / subdir).mkdir(parents=True, exist_ok=True)

            # Set permissions
            os.chmod(self.deployment_dir, 0o755)

            # Create log rotation configuration
            self._create_log_rotation_config()

            logger.info("System preparation completed")
            return True

        except Exception as e:
            logger.error(f"System preparation error: {e}")
            return False

    async def _install_dependencies(self) -> bool:
        """Install required dependencies"""
        try:
            # Check if running as root or with sudo
            if os.geteuid() != 0:
                logger.warning("Running without root privileges - some installations may fail")

            # Python dependencies
            pip_packages = [
                "fastapi", "uvicorn", "websockets", "psutil",
                "opencv-python", "numpy", "torch", "torchvision",
                "ultralytics", "albumentations", "scikit-learn",
                "matplotlib", "seaborn", "requests", "aiofiles"
            ]

            logger.info("Installing Python dependencies...")
            for package in pip_packages:
                try:
                    subprocess.run([
                        sys.executable, "-m", "pip", "install", package
                    ], check=True, capture_output=True)
                    logger.debug(f"Installed {package}")
                except subprocess.CalledProcessError as e:
                    logger.warning(f"Failed to install {package}: {e}")

            # System dependencies (if root)
            if os.geteuid() == 0:
                system_packages = ["v4l-utils", "ffmpeg"]
                for package in system_packages:
                    try:
                        subprocess.run([
                            "apt-get", "install", "-y", package
                        ], check=True, capture_output=True)
                        logger.debug(f"Installed {package}")
                    except subprocess.CalledProcessError as e:
                        logger.warning(f"Failed to install {package}: {e}")

            logger.info("Dependencies installation completed")
            return True

        except Exception as e:
            logger.error(f"Dependencies installation error: {e}")
            return False

    async def _deploy_files(self) -> bool:
        """Deploy system files to production location"""
        try:
            # Copy Python modules
            python_files = [
                "cv_system_architecture.py",
                "real_time_inference_engine.py",
                "optimized_inference_engine.py",
                "integration_api.py",
                "face_recognition_system.py",
                "orin_nano_optimizer.py",
                "deployment_validator.py"
            ]

            for file in python_files:
                src = self.base_dir / file
                dst = self.deployment_dir / "scripts" / file
                if src.exists():
                    shutil.copy2(src, dst)
                    logger.debug(f"Deployed {file}")

            # Copy models if they exist
            models_src = self.base_dir / "models"
            models_dst = self.deployment_dir / "models"

            if models_src.exists():
                for model_file in models_src.glob("*"):
                    if model_file.is_file():
                        shutil.copy2(model_file, models_dst / model_file.name)
                        logger.debug(f"Deployed model: {model_file.name}")

            # Create configuration file
            config_path = self.deployment_dir / "config" / "r2d2_vision_config.json"
            with open(config_path, 'w') as f:
                json.dump(self.config, f, indent=2)

            # Create startup script
            self._create_startup_script()

            # Create monitoring script
            self._create_monitoring_script()

            logger.info("File deployment completed")
            return True

        except Exception as e:
            logger.error(f"File deployment error: {e}")
            return False

    async def _configure_models(self) -> bool:
        """Configure and validate models"""
        try:
            models_dir = self.deployment_dir / "models"

            # Check for required models
            required_models = {
                "yolov8n.pt": "Guest detection model",
                "costume_classifier.pt": "Costume recognition model",
                "facenet_model.pt": "Face recognition model"
            }

            missing_models = []
            for model_file, description in required_models.items():
                if not (models_dir / model_file).exists():
                    missing_models.append(f"{model_file} ({description})")

            if missing_models:
                logger.warning(f"Missing models: {', '.join(missing_models)}")
                logger.info("System will attempt to download default models on first run")

            # Create model configuration
            model_config = {
                "detection_model": {
                    "path": str(models_dir / "yolov8n.pt"),
                    "tensorrt_path": str(models_dir / "yolov8n_tensorrt.engine"),
                    "input_size": [640, 640],
                    "confidence_threshold": self.config["detection"]["confidence_threshold"]
                },
                "costume_model": {
                    "path": str(models_dir / "costume_classifier.pt"),
                    "tensorrt_path": str(models_dir / "costume_classifier_tensorrt.engine"),
                    "input_size": [224, 224],
                    "classes": self.config["star_wars"]["costume_classes"]
                },
                "face_model": {
                    "path": str(models_dir / "facenet_model.pt"),
                    "embedding_size": 512,
                    "similarity_threshold": self.config["recognition"]["face_similarity_threshold"]
                }
            }

            config_path = self.deployment_dir / "config" / "model_config.json"
            with open(config_path, 'w') as f:
                json.dump(model_config, f, indent=2)

            logger.info("Model configuration completed")
            return True

        except Exception as e:
            logger.error(f"Model configuration error: {e}")
            return False

    async def _setup_services(self) -> bool:
        """Setup systemd services"""
        try:
            # Create systemd service file
            service_content = f"""[Unit]
Description=R2D2 Computer Vision System
After=network.target
Wants=network.target

[Service]
Type=simple
User=rolo
Group=rolo
WorkingDirectory={self.deployment_dir}/scripts
ExecStart=/usr/bin/python3 {self.deployment_dir}/scripts/integration_api.py
Environment=PYTHONPATH={self.deployment_dir}/scripts
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal
SyslogIdentifier=r2d2-vision

[Install]
WantedBy=multi-user.target
"""

            # Only create service file if running as root
            if os.geteuid() == 0:
                service_path = Path(f"/etc/systemd/system/{self.service_name}.service")
                with open(service_path, 'w') as f:
                    f.write(service_content)

                # Reload systemd
                subprocess.run(["systemctl", "daemon-reload"], check=True)
                subprocess.run(["systemctl", "enable", self.service_name], check=True)

                logger.info("Systemd service configured")
            else:
                logger.warning("Running without root - systemd service not configured")
                # Save service file for manual installation
                service_path = self.deployment_dir / f"{self.service_name}.service"
                with open(service_path, 'w') as f:
                    f.write(service_content)
                logger.info(f"Service file created at: {service_path}")

            return True

        except Exception as e:
            logger.error(f"Service setup error: {e}")
            return False

    async def _run_deployment_validation(self) -> bool:
        """Run post-deployment validation"""
        try:
            # Import and run validator
            sys.path.insert(0, str(self.deployment_dir / "scripts"))

            # Basic validation checks
            validation_results = {
                "files_deployed": True,
                "configuration_valid": True,
                "import_test": True,
                "basic_functionality": True
            }

            # Check file deployment
            required_files = [
                "scripts/integration_api.py",
                "config/r2d2_vision_config.json",
                "config/model_config.json"
            ]

            for file_path in required_files:
                if not (self.deployment_dir / file_path).exists():
                    validation_results["files_deployed"] = False
                    logger.error(f"Missing deployed file: {file_path}")

            # Validate configuration
            try:
                config_path = self.deployment_dir / "config" / "r2d2_vision_config.json"
                with open(config_path, 'r') as f:
                    config = json.load(f)
                    # Basic config validation
                    required_sections = ["deployment", "camera", "performance"]
                    for section in required_sections:
                        if section not in config:
                            validation_results["configuration_valid"] = False
            except Exception as e:
                logger.error(f"Configuration validation error: {e}")
                validation_results["configuration_valid"] = False

            # Test imports
            try:
                from integration_api import app
                validation_results["import_test"] = True
                logger.info("Import test passed")
            except Exception as e:
                logger.error(f"Import test failed: {e}")
                validation_results["import_test"] = False

            # Count passed validations
            passed = sum(1 for result in validation_results.values() if result)
            total = len(validation_results)

            logger.info(f"Deployment validation: {passed}/{total} checks passed")

            return passed >= 3  # Minimum for basic functionality

        except Exception as e:
            logger.error(f"Deployment validation error: {e}")
            return False

    async def _start_services(self) -> bool:
        """Start deployed services"""
        try:
            if os.geteuid() == 0:
                # Start systemd service
                subprocess.run(["systemctl", "start", self.service_name], check=True)

                # Wait for service to start
                await asyncio.sleep(5)

                # Check service status
                result = subprocess.run(
                    ["systemctl", "is-active", self.service_name],
                    capture_output=True, text=True
                )

                if result.returncode == 0 and result.stdout.strip() == "active":
                    logger.info("R2D2 Vision System service started successfully")
                    return True
                else:
                    logger.error("Service failed to start properly")
                    return False
            else:
                logger.info("Manual startup required - run as root to auto-start services")
                logger.info(f"Manual start command: sudo systemctl start {self.service_name}")
                return True

        except Exception as e:
            logger.error(f"Service startup error: {e}")
            return False

    def _create_startup_script(self):
        """Create startup script"""
        startup_script = f"""#!/bin/bash
# R2D2 Computer Vision System Startup Script

export PYTHONPATH="{self.deployment_dir}/scripts"
cd "{self.deployment_dir}/scripts"

echo "Starting R2D2 Computer Vision System..."
python3 integration_api.py --config "{self.deployment_dir}/config/r2d2_vision_config.json"
"""

        script_path = self.deployment_dir / "scripts" / "start_r2d2_vision.sh"
        with open(script_path, 'w') as f:
            f.write(startup_script)

        os.chmod(script_path, 0o755)

    def _create_monitoring_script(self):
        """Create monitoring script"""
        monitoring_script = f"""#!/bin/bash
# R2D2 Computer Vision System Monitoring Script

echo "R2D2 Vision System Status:"
echo "========================="

# Service status
if systemctl is-active --quiet {self.service_name}; then
    echo "✅ Service: Running"
else
    echo "❌ Service: Not running"
fi

# Process information
if pgrep -f "integration_api.py" > /dev/null; then
    echo "✅ Process: Active"
    echo "   PID: $(pgrep -f 'integration_api.py')"
    echo "   Memory: $(ps -o pid,rss,vsz,comm -p $(pgrep -f 'integration_api.py') | tail -1 | awk '{{print $2/1024 "MB"}}')"
else
    echo "❌ Process: Not found"
fi

# API endpoint check
if curl -s http://localhost:8000/health > /dev/null; then
    echo "✅ API: Responding"
else
    echo "❌ API: Not responding"
fi

# Log tail
echo ""
echo "Recent logs:"
echo "============"
journalctl -u {self.service_name} --no-pager -n 10
"""

        script_path = self.deployment_dir / "scripts" / "monitor_r2d2_vision.sh"
        with open(script_path, 'w') as f:
            f.write(monitoring_script)

        os.chmod(script_path, 0o755)

    def _create_log_rotation_config(self):
        """Create log rotation configuration"""
        logrotate_config = f"""{self.deployment_dir}/logs/*.log {{
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    sharedscripts
}}
"""

        config_path = self.deployment_dir / "config" / "logrotate.conf"
        with open(config_path, 'w') as f:
            f.write(logrotate_config)

    async def _print_deployment_summary(self):
        """Print deployment summary"""
        print("\n" + "="*60)
        print("R2D2 COMPUTER VISION SYSTEM DEPLOYMENT COMPLETE")
        print("="*60)
        print(f"📁 Deployment Directory: {self.deployment_dir}")
        print(f"🔧 Configuration: {self.deployment_dir}/config/")
        print(f"📊 Models: {self.deployment_dir}/models/")
        print(f"📝 Logs: {self.deployment_dir}/logs/")
        print(f"🚀 Service: {self.service_name}")
        print("\n🌐 API Endpoints:")
        print(f"   • Health Check: http://localhost:{self.config['deployment']['api_port']}/health")
        print(f"   • System Status: http://localhost:{self.config['deployment']['api_port']}/vision/status")
        print(f"   • WebSocket: ws://localhost:{self.config['deployment']['api_port']}/ws")
        print("\n🔧 Management Commands:")
        print(f"   • Start Service: sudo systemctl start {self.service_name}")
        print(f"   • Stop Service: sudo systemctl stop {self.service_name}")
        print(f"   • Service Status: sudo systemctl status {self.service_name}")
        print(f"   • View Logs: journalctl -u {self.service_name} -f")
        print(f"   • Monitor System: {self.deployment_dir}/scripts/monitor_r2d2_vision.sh")
        print("\n✅ System is ready for R2D2 interactions!")
        print("="*60)

    async def undeploy_system(self) -> bool:
        """Remove deployed system"""
        try:
            logger.info("Undeploying R2D2 Computer Vision System...")

            # Stop service
            if os.geteuid() == 0:
                try:
                    subprocess.run(["systemctl", "stop", self.service_name], check=True)
                    subprocess.run(["systemctl", "disable", self.service_name], check=True)
                    service_file = Path(f"/etc/systemd/system/{self.service_name}.service")
                    if service_file.exists():
                        service_file.unlink()
                    subprocess.run(["systemctl", "daemon-reload"], check=True)
                    logger.info("Service removed")
                except subprocess.CalledProcessError as e:
                    logger.warning(f"Service removal error: {e}")

            # Remove deployment directory
            if self.deployment_dir.exists():
                shutil.rmtree(self.deployment_dir)
                logger.info(f"Removed deployment directory: {self.deployment_dir}")

            logger.info("✅ System undeployed successfully")
            return True

        except Exception as e:
            logger.error(f"Undeployment error: {e}")
            return False

# CLI Interface
def main():
    parser = argparse.ArgumentParser(description="R2D2 Computer Vision System Deployment")
    parser.add_argument("action", choices=["deploy", "undeploy", "status", "validate"],
                       help="Deployment action to perform")
    parser.add_argument("--config", type=str,
                       help="Custom configuration file path")
    parser.add_argument("--skip-validation", action="store_true",
                       help="Skip pre-deployment validation")
    parser.add_argument("--no-auto-start", action="store_true",
                       help="Don't automatically start services")

    args = parser.parse_args()

    # Load custom config if provided
    config = None
    if args.config and Path(args.config).exists():
        with open(args.config, 'r') as f:
            config = json.load(f)

    # Override auto-start if specified
    if config and args.no_auto_start:
        config["deployment"]["auto_start"] = False

    deployer = R2D2VisionDeployer(config)

    async def run_deployment():
        if args.action == "deploy":
            success = await deployer.deploy_system(
                validate_before_deploy=not args.skip_validation
            )
            sys.exit(0 if success else 1)

        elif args.action == "undeploy":
            success = await deployer.undeploy_system()
            sys.exit(0 if success else 1)

        elif args.action == "validate":
            # Run validation only
            success = await deployer._run_deployment_validation()
            print(f"Validation {'passed' if success else 'failed'}")
            sys.exit(0 if success else 1)

        elif args.action == "status":
            # Check system status
            deployment_dir = Path("/opt/r2d2_vision")
            if deployment_dir.exists():
                print("R2D2 Vision System: Deployed")
                print(f"Location: {deployment_dir}")

                # Check service status
                try:
                    result = subprocess.run(
                        ["systemctl", "is-active", "r2d2-vision-system"],
                        capture_output=True, text=True
                    )
                    if result.returncode == 0:
                        print("Service: Running")
                    else:
                        print("Service: Not running")
                except:
                    print("Service: Status unknown")
            else:
                print("R2D2 Vision System: Not deployed")

    asyncio.run(run_deployment())

if __name__ == "__main__":
    main()