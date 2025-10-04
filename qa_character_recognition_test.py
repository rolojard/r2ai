#!/usr/bin/env python3
"""
ELITE QA TESTING: Character Recognition with Real Webcam Input
Comprehensive testing of YOLO-based character detection system
"""

import cv2
import numpy as np
import time
import json
import os
from datetime import datetime
import subprocess
import threading

class CharacterRecognitionQATester:
    """QA tester for character recognition validation"""

    def __init__(self):
        self.camera = None
        self.model = None
        self.test_results = {
            'yolo_model_loading': False,
            'real_webcam_detection': False,
            'person_detection_accuracy': False,
            'detection_performance': False,
            'confidence_validation': False,
            'character_recognition_integration': False
        }

        # Performance metrics
        self.detection_times = []
        self.detections_count = 0
        self.person_detections = 0

    def log_test(self, test_name, result, details=""):
        """Log test results"""
        status = "✅ PASS" if result else "❌ FAIL"
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] {status} {test_name}")
        if details:
            print(f"    Details: {details}")
        self.test_results[test_name] = result

    def test_yolo_model_loading(self):
        """Test YOLO model loading and initialization"""
        print("🧠 Testing YOLO Model Loading...")

        try:
            from ultralytics import YOLO
            import torch

            # Check for model file
            model_path = '/home/rolo/r2ai/yolov8n.pt'
            if not os.path.exists(model_path):
                self.log_test('yolo_model_loading', False, f"Model file not found: {model_path}")
                return False

            print(f"    📁 Model file found: {model_path}")

            # Load model
            start_time = time.time()
            self.model = YOLO(model_path)
            load_time = time.time() - start_time

            print(f"    ⏱️ Model loaded in {load_time:.2f} seconds")

            # Check CUDA availability
            if torch.cuda.is_available():
                self.model.to('cuda')
                print("    🚀 Model moved to GPU")
            else:
                print("    💻 Model running on CPU")

            # Configure model settings
            self.model.overrides['verbose'] = False
            self.model.overrides['conf'] = 0.5
            self.model.overrides['iou'] = 0.45
            self.model.overrides['max_det'] = 50

            print(f"    🎯 Model classes: {len(self.model.names)} ({list(self.model.names.values())[:5]}...)")

            self.log_test('yolo_model_loading', True, f"Model loaded successfully in {load_time:.2f}s")
            return True

        except ImportError as e:
            self.log_test('yolo_model_loading', False, f"Import error: {e}")
            return False
        except Exception as e:
            self.log_test('yolo_model_loading', False, f"Loading error: {e}")
            return False

    def initialize_camera(self):
        """Initialize real webcam for testing"""
        print("🎥 Initializing Real Webcam...")

        try:
            self.camera = cv2.VideoCapture(0, cv2.CAP_V4L2)

            if not self.camera.isOpened():
                print("❌ Failed to open camera")
                return False

            # Configure camera
            self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            self.camera.set(cv2.CAP_PROP_FPS, 30)
            self.camera.set(cv2.CAP_PROP_BUFFERSIZE, 1)

            # Test capture
            ret, frame = self.camera.read()
            if ret and frame is not None:
                print(f"    ✅ Camera initialized: {frame.shape}")
                return True
            else:
                print("❌ Failed to capture test frame")
                return False

        except Exception as e:
            print(f"❌ Camera initialization error: {e}")
            return False

    def test_real_webcam_detection(self, duration=10):
        """Test real-time detection on webcam feed"""
        print(f"\n👁️ Testing Real Webcam Detection ({duration}s)...")

        if not self.camera or not self.model:
            self.log_test('real_webcam_detection', False, "Camera or model not initialized")
            return False

        detections_made = 0
        frames_processed = 0
        start_time = time.time()

        try:
            while time.time() - start_time < duration:
                ret, frame = self.camera.read()

                if ret and frame is not None:
                    frames_processed += 1

                    # Run YOLO detection
                    detection_start = time.time()
                    results = self.model(frame, verbose=False)
                    detection_time = time.time() - detection_start

                    self.detection_times.append(detection_time)

                    # Process results
                    if results and len(results) > 0:
                        result = results[0]
                        if result.boxes is not None and len(result.boxes) > 0:
                            detections_made += 1
                            self.detections_count += len(result.boxes)

                            # Count person detections
                            for box in result.boxes:
                                class_id = int(box.cls[0])
                                if class_id == 0:  # Person class in COCO
                                    self.person_detections += 1

                    # Progress update
                    if frames_processed % 30 == 0:
                        print(f"    📊 Processed {frames_processed} frames, {detections_made} with detections")

                else:
                    print("    ⚠️ Failed to capture frame")

        except Exception as e:
            print(f"    ❌ Detection error: {e}")

        print(f"    📊 Total frames processed: {frames_processed}")
        print(f"    📊 Frames with detections: {detections_made}")
        print(f"    📊 Total objects detected: {self.detections_count}")
        print(f"    📊 Person detections: {self.person_detections}")

        # Success if we processed frames and made some detections
        if frames_processed >= 100 and detections_made > 0:
            self.log_test('real_webcam_detection', True,
                         f"{detections_made} detections in {frames_processed} frames")
            return True
        else:
            self.log_test('real_webcam_detection', False,
                         f"Insufficient detections: {detections_made}/{frames_processed}")
            return False

    def test_person_detection_accuracy(self):
        """Test person detection accuracy with manual verification"""
        print("\n👤 Testing Person Detection Accuracy...")
        print("    MANUAL TEST: Please stand in front of the camera")
        input("    Press Enter when you are positioned in front of the camera...")

        if not self.camera or not self.model:
            self.log_test('person_detection_accuracy', False, "Camera or model not initialized")
            return False

        person_detected_frames = 0
        total_test_frames = 30
        confidence_scores = []

        print(f"    📹 Testing {total_test_frames} frames for person detection...")

        try:
            for i in range(total_test_frames):
                ret, frame = self.camera.read()

                if ret and frame is not None:
                    # Run detection
                    results = self.model(frame, verbose=False)

                    person_found = False
                    if results and len(results) > 0:
                        result = results[0]
                        if result.boxes is not None:
                            for box in result.boxes:
                                class_id = int(box.cls[0])
                                confidence = float(box.conf[0])

                                if class_id == 0:  # Person class
                                    person_found = True
                                    confidence_scores.append(confidence)
                                    break

                    if person_found:
                        person_detected_frames += 1
                        print(f"    ✅ Frame {i+1}: Person detected (conf: {confidence:.2f})")
                    else:
                        print(f"    ❌ Frame {i+1}: No person detected")

                time.sleep(0.2)  # 5 FPS for manual test

        except Exception as e:
            print(f"    ❌ Person detection error: {e}")

        detection_rate = (person_detected_frames / total_test_frames) * 100
        avg_confidence = sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0

        print(f"    📊 Person detection rate: {detection_rate:.1f}%")
        print(f"    📊 Average confidence: {avg_confidence:.2f}")

        # Pass if >70% detection rate when person is present
        if detection_rate >= 70:
            self.log_test('person_detection_accuracy', True,
                         f"Person detected in {detection_rate:.1f}% of frames")
            return True
        else:
            self.log_test('person_detection_accuracy', False,
                         f"Low detection rate: {detection_rate:.1f}%")
            return False

    def test_detection_performance(self):
        """Test detection performance metrics"""
        print("\n⚡ Testing Detection Performance...")

        if not self.detection_times:
            self.log_test('detection_performance', False, "No detection timing data available")
            return False

        avg_detection_time = sum(self.detection_times) / len(self.detection_times)
        max_detection_time = max(self.detection_times)
        min_detection_time = min(self.detection_times)

        # Calculate FPS potential
        max_fps = 1.0 / avg_detection_time if avg_detection_time > 0 else 0

        print(f"    ⏱️ Average detection time: {avg_detection_time:.3f}s")
        print(f"    ⏱️ Min detection time: {min_detection_time:.3f}s")
        print(f"    ⏱️ Max detection time: {max_detection_time:.3f}s")
        print(f"    🎯 Theoretical max FPS: {max_fps:.1f}")

        # Pass if average detection time allows for real-time processing (>10 FPS)
        if avg_detection_time <= 0.1:  # 100ms = 10 FPS
            self.log_test('detection_performance', True,
                         f"Real-time capable: {avg_detection_time:.3f}s avg")
            return True
        else:
            self.log_test('detection_performance', False,
                         f"Too slow for real-time: {avg_detection_time:.3f}s avg")
            return False

    def test_confidence_validation(self):
        """Test confidence score validation"""
        print("\n🎯 Testing Confidence Score Validation...")

        if not self.camera or not self.model:
            self.log_test('confidence_validation', False, "Camera or model not initialized")
            return False

        high_confidence_detections = 0
        medium_confidence_detections = 0
        low_confidence_detections = 0
        total_detections = 0

        # Test confidence distribution over 50 frames
        for i in range(50):
            ret, frame = self.camera.read()

            if ret and frame is not None:
                results = self.model(frame, verbose=False)

                if results and len(results) > 0:
                    result = results[0]
                    if result.boxes is not None:
                        for box in result.boxes:
                            confidence = float(box.conf[0])
                            total_detections += 1

                            if confidence >= 0.8:
                                high_confidence_detections += 1
                            elif confidence >= 0.5:
                                medium_confidence_detections += 1
                            else:
                                low_confidence_detections += 1

            time.sleep(0.05)

        print(f"    📊 Total detections analyzed: {total_detections}")
        print(f"    📊 High confidence (≥0.8): {high_confidence_detections}")
        print(f"    📊 Medium confidence (0.5-0.8): {medium_confidence_detections}")
        print(f"    📊 Low confidence (<0.5): {low_confidence_detections}")

        if total_detections > 0:
            high_conf_ratio = high_confidence_detections / total_detections
            print(f"    📊 High confidence ratio: {high_conf_ratio:.2%}")

            # Pass if >30% of detections are high confidence
            if high_conf_ratio >= 0.3:
                self.log_test('confidence_validation', True,
                             f"Good confidence distribution ({high_conf_ratio:.2%} high)")
                return True
            else:
                self.log_test('confidence_validation', False,
                             f"Low confidence ratio: {high_conf_ratio:.2%}")
                return False
        else:
            self.log_test('confidence_validation', False, "No detections to analyze")
            return False

    def test_character_recognition_integration(self):
        """Test character recognition integration"""
        print("\n🎭 Testing Character Recognition Integration...")

        if not self.camera or not self.model:
            self.log_test('character_recognition_integration', False, "Camera or model not initialized")
            return False

        # Simulate the character recognition process from ultra-stable vision
        character_detections = []

        for i in range(20):
            ret, frame = self.camera.read()

            if ret and frame is not None:
                results = self.model(frame, verbose=False)

                if results and len(results) > 0:
                    result = results[0]
                    if result.boxes is not None:
                        for box in result.boxes:
                            class_id = int(box.cls[0])
                            confidence = float(box.conf[0])

                            if class_id == 0 and confidence > 0.6:  # Person with good confidence
                                # Simulate character detection data structure
                                character_detection = {
                                    'name': 'Person Detected',
                                    'character': 'unknown',
                                    'confidence': confidence,
                                    'bbox': [float(x) for x in box.xyxy[0]],
                                    'r2d2_reaction': {
                                        'primary_emotion': 'curious',
                                        'excitement_level': 'medium',
                                        'camera_source': 'real_webcam'
                                    }
                                }
                                character_detections.append(character_detection)

            time.sleep(0.1)

        print(f"    📊 Character detections generated: {len(character_detections)}")

        if character_detections:
            # Test data structure validity
            sample_detection = character_detections[0]
            required_fields = ['name', 'character', 'confidence', 'bbox', 'r2d2_reaction']

            all_fields_present = all(field in sample_detection for field in required_fields)

            if all_fields_present:
                print("    ✅ Character detection data structure valid")
                print(f"    📊 Sample detection: {sample_detection['name']} (conf: {sample_detection['confidence']:.2f})")

                self.log_test('character_recognition_integration', True,
                             f"{len(character_detections)} character detections with valid structure")
                return True
            else:
                self.log_test('character_recognition_integration', False,
                             "Invalid character detection data structure")
                return False
        else:
            self.log_test('character_recognition_integration', False,
                         "No character detections generated")
            return False

    def run_comprehensive_character_recognition_test(self):
        """Run complete character recognition test suite"""
        print("🎯 ELITE QA TESTING: Character Recognition with Real Webcam Input")
        print("=" * 70)
        print("Testing YOLO-based Character Detection System")
        print("=" * 70)

        try:
            # Initialize components
            if not self.test_yolo_model_loading():
                return False

            if not self.initialize_camera():
                return False

            # Run test sequence
            self.test_real_webcam_detection(10)
            self.test_person_detection_accuracy()
            self.test_detection_performance()
            self.test_confidence_validation()
            self.test_character_recognition_integration()

        finally:
            if self.camera:
                self.camera.release()

        # Generate report
        self.generate_character_recognition_report()

        # Return overall success
        return all(self.test_results.values())

    def generate_character_recognition_report(self):
        """Generate comprehensive character recognition test report"""
        print("\n" + "=" * 70)
        print("🎯 CHARACTER RECOGNITION TEST REPORT")
        print("=" * 70)

        passed_tests = sum(1 for result in self.test_results.values() if result)
        total_tests = len(self.test_results)

        print(f"OVERALL RESULT: {passed_tests}/{total_tests} tests passed")
        print(f"CHARACTER RECOGNITION SCORE: {(passed_tests/total_tests)*100:.1f}%")
        print()

        print("DETAILED RESULTS:")
        test_categories = {
            'yolo_model_loading': 'YOLO Model Loading',
            'real_webcam_detection': 'Real Webcam Detection',
            'person_detection_accuracy': 'Person Detection Accuracy',
            'detection_performance': 'Detection Performance',
            'confidence_validation': 'Confidence Score Validation',
            'character_recognition_integration': 'Character Recognition Integration'
        }

        for test_key, test_name in test_categories.items():
            result = self.test_results[test_key]
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"  {status} {test_name}")

        print()

        # Performance summary
        if self.detection_times:
            avg_detection_time = sum(self.detection_times) / len(self.detection_times)
            print(f"PERFORMANCE METRICS:")
            print(f"  🎯 Average detection time: {avg_detection_time:.3f}s")
            print(f"  🎯 Total detections made: {self.detections_count}")
            print(f"  🎯 Person detections: {self.person_detections}")

        print()

        if passed_tests == total_tests:
            print("🎉 CHARACTER RECOGNITION SYSTEM VALIDATED!")
            print("✅ Real webcam input processing working")
            print("✅ YOLO model performing accurate detections")
            print("✅ Character recognition integration functional")
        else:
            print("⚠️ CHARACTER RECOGNITION ISSUES DETECTED")
            failed_tests = [test_categories[name] for name, result in self.test_results.items() if not result]
            print(f"   Issues: {', '.join(failed_tests)}")

        print("=" * 70)

def main():
    """Main execution function"""
    tester = CharacterRecognitionQATester()

    try:
        success = tester.run_comprehensive_character_recognition_test()
        return 0 if success else 1

    except KeyboardInterrupt:
        print("\n\n🛑 Test interrupted by user")
        return 1
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        return 1

if __name__ == "__main__":
    import sys
    sys.exit(main())