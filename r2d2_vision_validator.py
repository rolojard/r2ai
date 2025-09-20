#!/usr/bin/env python3
"""
R2D2 Computer Vision System Validator
Comprehensive validation for PyTorch 2.5.0a0, CUDA 12.6, and YOLOv8 integration
"""

import sys
import time
import json
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional
import numpy as np

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class R2D2VisionValidator:
    """Comprehensive computer vision system validator for R2D2"""

    def __init__(self):
        self.validation_results = {}
        self.gpu_available = False
        self.models_loaded = {}

    def validate_pytorch_cuda_setup(self) -> Dict[str, Any]:
        """Validate PyTorch and CUDA configuration"""
        logger.info("Validating PyTorch and CUDA setup...")

        results = {
            'component': 'PyTorch CUDA Validation',
            'timestamp': datetime.now().isoformat(),
            'validations': []
        }

        try:
            import torch

            # Check PyTorch version
            pytorch_version = torch.__version__
            expected_version = "2.5.0"

            if pytorch_version.startswith(expected_version):
                results['validations'].append({
                    'check': 'PyTorch Version',
                    'status': 'OPTIMAL',
                    'details': f'PyTorch {pytorch_version} - NVIDIA optimized version detected',
                    'confidence': 'HIGH'
                })
            else:
                results['validations'].append({
                    'check': 'PyTorch Version',
                    'status': 'WARNING',
                    'details': f'PyTorch {pytorch_version} - may have compatibility issues',
                    'confidence': 'MEDIUM'
                })

            # Check CUDA availability
            if torch.cuda.is_available():
                self.gpu_available = True
                gpu_name = torch.cuda.get_device_name(0)
                cuda_version = torch.version.cuda

                results['validations'].append({
                    'check': 'CUDA Availability',
                    'status': 'OPTIMAL',
                    'details': f'CUDA {cuda_version} available on {gpu_name}',
                    'confidence': 'HIGH'
                })

                # Test GPU memory
                gpu_memory = torch.cuda.get_device_properties(0).total_memory / (1024**3)
                if gpu_memory >= 8.0:  # Orin Nano has 8GB shared memory
                    results['validations'].append({
                        'check': 'GPU Memory',
                        'status': 'OPTIMAL',
                        'details': f'{gpu_memory:.1f}GB GPU memory available',
                        'confidence': 'HIGH'
                    })
                else:
                    results['validations'].append({
                        'check': 'GPU Memory',
                        'status': 'WARNING',
                        'details': f'{gpu_memory:.1f}GB GPU memory - may limit model size',
                        'confidence': 'MEDIUM'
                    })
            else:
                results['validations'].append({
                    'check': 'CUDA Availability',
                    'status': 'CRITICAL',
                    'details': 'CUDA not available - GPU acceleration disabled',
                    'confidence': 'HIGH'
                })

        except ImportError as e:
            results['validations'].append({
                'check': 'PyTorch Import',
                'status': 'CRITICAL',
                'details': f'PyTorch not available: {e}',
                'confidence': 'HIGH'
            })
        except Exception as e:
            results['validations'].append({
                'check': 'PyTorch CUDA Setup',
                'status': 'ERROR',
                'details': str(e),
                'confidence': 'MEDIUM'
            })

        return results

    def validate_yolo_integration(self) -> Dict[str, Any]:
        """Validate YOLO model loading and CUDA integration"""
        logger.info("Validating YOLO integration...")

        results = {
            'component': 'YOLO Integration Validation',
            'timestamp': datetime.now().isoformat(),
            'validations': []
        }

        try:
            from ultralytics import YOLO
            import ultralytics

            # Check Ultralytics version
            ultralytics_version = ultralytics.__version__
            results['validations'].append({
                'check': 'Ultralytics Version',
                'status': 'OPTIMAL',
                'details': f'Ultralytics {ultralytics_version} available',
                'confidence': 'HIGH'
            })

            # Test YOLO model loading
            try:
                start_time = time.time()
                model = YOLO('yolov8n.pt')
                load_time = time.time() - start_time

                results['validations'].append({
                    'check': 'YOLO Model Loading',
                    'status': 'OPTIMAL',
                    'details': f'YOLOv8n loaded in {load_time:.2f}s',
                    'confidence': 'HIGH'
                })

                self.models_loaded['yolo'] = model

                # Test CUDA assignment
                if self.gpu_available:
                    try:
                        model.to('cuda')
                        device_after = str(model.device)

                        if 'cuda' in device_after:
                            results['validations'].append({
                                'check': 'YOLO CUDA Assignment',
                                'status': 'OPTIMAL',
                                'details': f'YOLO model successfully moved to {device_after}',
                                'confidence': 'HIGH'
                            })
                        else:
                            results['validations'].append({
                                'check': 'YOLO CUDA Assignment',
                                'status': 'WARNING',
                                'details': f'YOLO model on {device_after} instead of CUDA',
                                'confidence': 'MEDIUM'
                            })
                    except Exception as e:
                        results['validations'].append({
                            'check': 'YOLO CUDA Assignment',
                            'status': 'CRITICAL',
                            'details': f'Failed to move YOLO to CUDA: {e}',
                            'confidence': 'HIGH'
                        })

                # Test inference
                try:
                    dummy_image = np.random.randint(0, 255, (640, 480, 3), dtype=np.uint8)

                    start_time = time.time()
                    results_inference = model(dummy_image, verbose=False)
                    inference_time = time.time() - start_time

                    if inference_time < 0.1:  # Under 100ms for real-time performance
                        status = 'OPTIMAL'
                        perf_rating = 'Real-time capable'
                    elif inference_time < 0.5:
                        status = 'GOOD'
                        perf_rating = 'Acceptable for R2D2'
                    else:
                        status = 'WARNING'
                        perf_rating = 'May need optimization'

                    results['validations'].append({
                        'check': 'YOLO Inference Performance',
                        'status': status,
                        'details': f'Inference: {inference_time:.3f}s ({perf_rating})',
                        'confidence': 'HIGH'
                    })

                except Exception as e:
                    results['validations'].append({
                        'check': 'YOLO Inference Test',
                        'status': 'CRITICAL',
                        'details': f'YOLO inference failed: {e}',
                        'confidence': 'HIGH'
                    })

            except Exception as e:
                results['validations'].append({
                    'check': 'YOLO Model Loading',
                    'status': 'CRITICAL',
                    'details': f'Failed to load YOLO model: {e}',
                    'confidence': 'HIGH'
                })

        except ImportError as e:
            results['validations'].append({
                'check': 'Ultralytics Import',
                'status': 'CRITICAL',
                'details': f'Ultralytics not available: {e}',
                'confidence': 'HIGH'
            })
        except Exception as e:
            results['validations'].append({
                'check': 'YOLO Integration',
                'status': 'ERROR',
                'details': str(e),
                'confidence': 'MEDIUM'
            })

        return results

    def validate_opencv_integration(self) -> Dict[str, Any]:
        """Validate OpenCV and camera integration"""
        logger.info("Validating OpenCV integration...")

        results = {
            'component': 'OpenCV Integration Validation',
            'timestamp': datetime.now().isoformat(),
            'validations': []
        }

        try:
            import cv2

            # Check OpenCV version
            opencv_version = cv2.__version__
            results['validations'].append({
                'check': 'OpenCV Version',
                'status': 'OPTIMAL',
                'details': f'OpenCV {opencv_version} available',
                'confidence': 'HIGH'
            })

            # Test camera access
            try:
                cap = cv2.VideoCapture(0)
                if cap.isOpened():
                    # Test camera properties
                    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                    fps = cap.get(cv2.CAP_PROP_FPS)

                    results['validations'].append({
                        'check': 'Camera Access',
                        'status': 'OPTIMAL',
                        'details': f'Camera accessible: {width}x{height} @ {fps} FPS',
                        'confidence': 'HIGH'
                    })

                    # Test frame capture
                    ret, frame = cap.read()
                    if ret and frame is not None:
                        results['validations'].append({
                            'check': 'Frame Capture',
                            'status': 'OPTIMAL',
                            'details': f'Frame captured: {frame.shape}',
                            'confidence': 'HIGH'
                        })
                    else:
                        results['validations'].append({
                            'check': 'Frame Capture',
                            'status': 'WARNING',
                            'details': 'Camera opened but frame capture failed',
                            'confidence': 'MEDIUM'
                        })

                    cap.release()
                else:
                    results['validations'].append({
                        'check': 'Camera Access',
                        'status': 'WARNING',
                        'details': 'Camera device not accessible',
                        'confidence': 'HIGH'
                    })

            except Exception as e:
                results['validations'].append({
                    'check': 'Camera Access',
                    'status': 'ERROR',
                    'details': f'Camera test failed: {e}',
                    'confidence': 'MEDIUM'
                })

            # Test OpenCV CUDA support
            try:
                cuda_support = cv2.cuda.getCudaEnabledDeviceCount() > 0
                if cuda_support:
                    results['validations'].append({
                        'check': 'OpenCV CUDA Support',
                        'status': 'OPTIMAL',
                        'details': f'OpenCV CUDA enabled with {cv2.cuda.getCudaEnabledDeviceCount()} device(s)',
                        'confidence': 'HIGH'
                    })
                else:
                    results['validations'].append({
                        'check': 'OpenCV CUDA Support',
                        'status': 'INFO',
                        'details': 'OpenCV CUDA support not available (CPU fallback)',
                        'confidence': 'MEDIUM'
                    })
            except:
                results['validations'].append({
                    'check': 'OpenCV CUDA Support',
                    'status': 'INFO',
                    'details': 'OpenCV CUDA support not built-in',
                    'confidence': 'LOW'
                })

        except ImportError as e:
            results['validations'].append({
                'check': 'OpenCV Import',
                'status': 'CRITICAL',
                'details': f'OpenCV not available: {e}',
                'confidence': 'HIGH'
            })
        except Exception as e:
            results['validations'].append({
                'check': 'OpenCV Integration',
                'status': 'ERROR',
                'details': str(e),
                'confidence': 'MEDIUM'
            })

        return results

    def validate_r2d2_vision_pipeline(self) -> Dict[str, Any]:
        """Validate complete R2D2 vision pipeline performance"""
        logger.info("Validating R2D2 vision pipeline...")

        results = {
            'component': 'R2D2 Vision Pipeline Validation',
            'timestamp': datetime.now().isoformat(),
            'validations': []
        }

        if 'yolo' not in self.models_loaded:
            results['validations'].append({
                'check': 'Pipeline Prerequisites',
                'status': 'CRITICAL',
                'details': 'YOLO model not loaded - cannot test pipeline',
                'confidence': 'HIGH'
            })
            return results

        try:
            import cv2
            import torch

            model = self.models_loaded['yolo']

            # Test real-time performance simulation
            frame_count = 100
            total_time = 0
            successful_detections = 0

            logger.info(f"Running {frame_count} frame simulation...")

            for i in range(frame_count):
                # Generate synthetic frame (simulating R2D2 camera feed)
                frame = np.random.randint(0, 255, (640, 480, 3), dtype=np.uint8)

                # Add some realistic features
                cv2.circle(frame, (320, 240), 50, (255, 255, 255), -1)  # Simulate person
                cv2.rectangle(frame, (100, 100), (200, 300), (128, 128, 128), -1)  # Simulate object

                start_time = time.time()

                try:
                    # Run detection
                    device_param = 'cuda' if self.gpu_available else 'cpu'
                    results_detection = model(frame, verbose=False, device=device_param)

                    inference_time = time.time() - start_time
                    total_time += inference_time

                    # Check if detection was successful
                    if results_detection and len(results_detection) > 0:
                        successful_detections += 1

                except Exception as e:
                    logger.warning(f"Detection failed on frame {i}: {e}")

            # Calculate performance metrics
            avg_inference_time = total_time / frame_count
            theoretical_fps = 1.0 / avg_inference_time if avg_inference_time > 0 else 0
            success_rate = (successful_detections / frame_count) * 100

            # Evaluate performance
            if avg_inference_time < 0.05 and theoretical_fps >= 20:
                status = 'OPTIMAL'
                performance_rating = 'Excellent real-time performance'
            elif avg_inference_time < 0.1 and theoretical_fps >= 10:
                status = 'GOOD'
                performance_rating = 'Good R2D2 interaction performance'
            elif avg_inference_time < 0.2:
                status = 'ACCEPTABLE'
                performance_rating = 'Acceptable for basic R2D2 functions'
            else:
                status = 'WARNING'
                performance_rating = 'May need optimization for real-time use'

            results['validations'].append({
                'check': 'Vision Pipeline Performance',
                'status': status,
                'details': f'{avg_inference_time:.3f}s avg, {theoretical_fps:.1f} FPS theoretical ({performance_rating})',
                'confidence': 'HIGH'
            })

            results['validations'].append({
                'check': 'Detection Success Rate',
                'status': 'OPTIMAL' if success_rate >= 95 else 'WARNING',
                'details': f'{success_rate:.1f}% successful detections over {frame_count} frames',
                'confidence': 'HIGH'
            })

            # Test memory usage
            if self.gpu_available:
                try:
                    import torch
                    gpu_memory_used = torch.cuda.memory_allocated() / (1024**3)
                    gpu_memory_cached = torch.cuda.memory_reserved() / (1024**3)

                    if gpu_memory_used < 2.0:  # Under 2GB usage
                        memory_status = 'OPTIMAL'
                        memory_details = f'Efficient GPU memory usage: {gpu_memory_used:.2f}GB used, {gpu_memory_cached:.2f}GB cached'
                    elif gpu_memory_used < 4.0:
                        memory_status = 'GOOD'
                        memory_details = f'Moderate GPU memory usage: {gpu_memory_used:.2f}GB used, {gpu_memory_cached:.2f}GB cached'
                    else:
                        memory_status = 'WARNING'
                        memory_details = f'High GPU memory usage: {gpu_memory_used:.2f}GB used, {gpu_memory_cached:.2f}GB cached'

                    results['validations'].append({
                        'check': 'GPU Memory Efficiency',
                        'status': memory_status,
                        'details': memory_details,
                        'confidence': 'HIGH'
                    })
                except:
                    pass

        except Exception as e:
            results['validations'].append({
                'check': 'Vision Pipeline Test',
                'status': 'ERROR',
                'details': str(e),
                'confidence': 'MEDIUM'
            })

        return results

    def run_complete_validation(self) -> Dict[str, Any]:
        """Run complete R2D2 vision system validation"""
        logger.info("Starting complete R2D2 vision system validation...")

        all_results = []

        # Run all validation phases
        all_results.append(self.validate_pytorch_cuda_setup())
        all_results.append(self.validate_yolo_integration())
        all_results.append(self.validate_opencv_integration())
        all_results.append(self.validate_r2d2_vision_pipeline())

        # Generate comprehensive report
        final_report = self._generate_validation_report(all_results)

        return final_report

    def _generate_validation_report(self, all_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate comprehensive validation report"""
        report = {
            'vision_validation_session': {
                'timestamp': datetime.now().isoformat(),
                'platform': 'NVIDIA Orin Nano',
                'validator': 'R2D2VisionValidator v1.0',
                'pytorch_version': None,
                'cuda_version': None,
                'system_status': 'UNKNOWN'
            },
            'validation_summary': {},
            'validation_results': all_results,
            'r2d2_vision_readiness': {}
        }

        # Extract version information
        try:
            import torch
            report['vision_validation_session']['pytorch_version'] = torch.__version__
            if torch.cuda.is_available():
                report['vision_validation_session']['cuda_version'] = torch.version.cuda
        except:
            pass

        # Calculate overall performance scores
        total_checks = 0
        optimal_checks = 0
        good_checks = 0
        critical_issues = 0

        for result in all_results:
            if 'validations' in result:
                for validation in result['validations']:
                    total_checks += 1
                    status = validation['status']

                    if status == 'OPTIMAL':
                        optimal_checks += 1
                    elif status in ['GOOD', 'ACCEPTABLE']:
                        good_checks += 1
                    elif status in ['CRITICAL']:
                        critical_issues += 1

        if total_checks > 0:
            optimal_rate = (optimal_checks / total_checks) * 100
            success_rate = ((optimal_checks + good_checks) / total_checks) * 100

            report['validation_summary'] = {
                'total_checks': total_checks,
                'optimal_checks': optimal_checks,
                'good_checks': good_checks,
                'critical_issues': critical_issues,
                'optimal_rate': f'{optimal_rate:.1f}%',
                'success_rate': f'{success_rate:.1f}%'
            }

            # Determine R2D2 vision readiness
            if critical_issues == 0 and optimal_rate >= 80:
                readiness_level = 'VISION_READY'
                readiness_description = 'R2D2 vision system optimally configured for deployment'
            elif critical_issues == 0 and success_rate >= 90:
                readiness_level = 'DEPLOYMENT_READY'
                readiness_description = 'R2D2 vision system ready with good performance'
            elif critical_issues <= 1 and success_rate >= 75:
                readiness_level = 'TESTING_READY'
                readiness_description = 'R2D2 vision system ready for testing with minor issues'
            else:
                readiness_level = 'OPTIMIZATION_NEEDED'
                readiness_description = 'R2D2 vision system requires optimization before deployment'

            report['r2d2_vision_readiness'] = {
                'level': readiness_level,
                'description': readiness_description,
                'recommendations': self._get_vision_recommendations(readiness_level, critical_issues)
            }

            report['vision_validation_session']['system_status'] = readiness_level

        return report

    def _get_vision_recommendations(self, readiness_level: str, critical_issues: int) -> List[str]:
        """Get recommendations based on vision system readiness"""
        if readiness_level == 'VISION_READY':
            return [
                "Deploy R2D2 vision system with confidence",
                "Monitor GPU temperature during extended operation",
                "Implement performance logging for production monitoring",
                "Test with real guest interaction scenarios"
            ]
        elif readiness_level == 'DEPLOYMENT_READY':
            return [
                "Complete final integration testing",
                "Validate performance under convention lighting conditions",
                "Test edge cases with costume detection",
                "Implement backup processing modes"
            ]
        elif readiness_level == 'TESTING_READY':
            return [
                "Address minor performance optimizations",
                "Complete comprehensive testing suite",
                "Validate memory usage under extended operation",
                "Test integration with R2D2 control systems"
            ]
        else:
            recommendations = [
                "Address all critical vision system issues",
                "Optimize CUDA/GPU performance configuration",
                "Validate PyTorch and YOLO model compatibility"
            ]

            if critical_issues > 0:
                recommendations.append("Critical: Fix CUDA or model loading issues before deployment")

            return recommendations

def main():
    """Main validation function"""
    print("R2D2 Computer Vision System Validation")
    print("=" * 50)
    print("PyTorch 2.5.0a0 + CUDA 12.6 + YOLOv8 Compatibility Test")
    print("=" * 50)

    validator = R2D2VisionValidator()

    try:
        # Run complete validation
        validation_report = validator.run_complete_validation()

        # Save validation report
        report_file = '/home/rolo/r2ai/r2d2_vision_validation_report.json'
        with open(report_file, 'w') as f:
            json.dump(validation_report, f, indent=2)

        # Generate readable summary
        summary_file = '/home/rolo/r2ai/r2d2_vision_validation_summary.txt'
        with open(summary_file, 'w') as f:
            f.write("R2D2 COMPUTER VISION SYSTEM VALIDATION\n")
            f.write("=" * 50 + "\n\n")
            f.write(f"Validation completed: {validation_report['vision_validation_session']['timestamp']}\n")
            f.write(f"Platform: {validation_report['vision_validation_session']['platform']}\n")

            if validation_report['vision_validation_session']['pytorch_version']:
                f.write(f"PyTorch: {validation_report['vision_validation_session']['pytorch_version']}\n")
            if validation_report['vision_validation_session']['cuda_version']:
                f.write(f"CUDA: {validation_report['vision_validation_session']['cuda_version']}\n")
            f.write("\n")

            if 'validation_summary' in validation_report:
                f.write("VALIDATION SUMMARY:\n")
                f.write("-" * 25 + "\n")
                summary = validation_report['validation_summary']
                f.write(f"Total Checks: {summary['total_checks']}\n")
                f.write(f"Optimal Results: {summary['optimal_checks']}\n")
                f.write(f"Good Results: {summary['good_checks']}\n")
                f.write(f"Critical Issues: {summary['critical_issues']}\n")
                f.write(f"Optimal Rate: {summary['optimal_rate']}\n")
                f.write(f"Success Rate: {summary['success_rate']}\n\n")

            if 'r2d2_vision_readiness' in validation_report:
                f.write("R2D2 VISION READINESS:\n")
                f.write("-" * 30 + "\n")
                readiness = validation_report['r2d2_vision_readiness']
                f.write(f"Status: {readiness['level']}\n")
                f.write(f"Assessment: {readiness['description']}\n\n")

                f.write("RECOMMENDATIONS:\n")
                f.write("-" * 20 + "\n")
                for rec in readiness['recommendations']:
                    f.write(f"• {rec}\n")
                f.write("\n")

            f.write("DETAILED VALIDATION RESULTS:\n")
            f.write("-" * 40 + "\n")
            for result in validation_report['validation_results']:
                f.write(f"\n{result['component']}:\n")

                if 'validations' in result:
                    for val in result['validations']:
                        status = val['status']
                        if status == 'OPTIMAL':
                            symbol = "✓"
                        elif status in ['GOOD', 'ACCEPTABLE']:
                            symbol = "○"
                        elif status in ['WARNING', 'INFO']:
                            symbol = "⚠"
                        elif status == 'CRITICAL':
                            symbol = "✗"
                        else:
                            symbol = "?"

                        f.write(f"  {symbol} {val['check']}: {val['details']}\n")

        print(f"\nValidation completed successfully!")
        print(f"Detailed report: {report_file}")
        print(f"Summary: {summary_file}")

        # Display key results
        if 'r2d2_vision_readiness' in validation_report:
            readiness = validation_report['r2d2_vision_readiness']
            print(f"\nR2D2 VISION STATUS: {readiness['level']}")
            print(f"Assessment: {readiness['description']}")

        if 'validation_summary' in validation_report:
            summary = validation_report['validation_summary']
            print(f"\nValidation Summary:")
            print(f"  Success Rate: {summary['success_rate']}")
            print(f"  Critical Issues: {summary['critical_issues']}")

        return 0

    except Exception as e:
        logger.error(f"Vision validation failed: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())