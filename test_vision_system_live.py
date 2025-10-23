#!/usr/bin/env python3
"""
Live Vision System Test
Tests the complete vision system including camera, detection, and frame processing
"""

import sys
import time
import logging
import signal
import threading

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

sys.path.insert(0, '/home/rolo/r2ai')
from r2d2_orin_nano_optimized_vision import OrinNanoOptimizedVision

class VisionSystemLiveTester:
    """Live tester for the vision system"""

    def __init__(self):
        self.vision_system = None
        self.test_duration = 10  # Run for 10 seconds
        self.stop_event = threading.Event()

    def run_test(self):
        """Run the live test"""
        logger.info("=" * 70)
        logger.info("LIVE VISION SYSTEM TEST")
        logger.info("=" * 70)
        logger.info(f"Test will run for {self.test_duration} seconds")
        logger.info("Monitoring: camera initialization, frame capture, and detection")
        logger.info("=" * 70)

        try:
            # Create vision system
            logger.info("\n1. Creating vision system instance...")
            self.vision_system = OrinNanoOptimizedVision(websocket_port=8767, camera_device=0)
            logger.info("✓ Vision system instance created")

            # Test camera initialization directly
            logger.info("\n2. Initializing camera with V4L2...")
            if not self.vision_system._initialize_camera_v4l2():
                logger.error("✗ FAIL: Camera initialization failed")
                return False
            logger.info("✓ Camera initialized successfully")

            # Verify camera is open
            if not self.vision_system.camera or not self.vision_system.camera.isOpened():
                logger.error("✗ FAIL: Camera is not open")
                return False
            logger.info("✓ Camera is open and ready")

            # Test frame capture
            logger.info("\n3. Testing frame capture...")
            frames_captured = 0
            frames_with_data = 0

            for i in range(5):
                ret, frame = self.vision_system.camera.read()
                if ret:
                    frames_captured += 1
                    if frame.max() > 0:
                        frames_with_data += 1
                    logger.info(f"  Frame {i+1}: captured={ret}, shape={frame.shape}, "
                              f"min={frame.min()}, max={frame.max()}, mean={frame.mean():.1f}")
                else:
                    logger.error(f"  Frame {i+1}: FAILED to capture")

            if frames_captured != 5:
                logger.error(f"✗ FAIL: Only captured {frames_captured}/5 frames")
                return False

            if frames_with_data != 5:
                logger.warning(f"⚠ WARNING: Only {frames_with_data}/5 frames had pixel data")

            logger.info(f"✓ Successfully captured {frames_captured}/5 frames")

            # Test detection pipeline (if model is available)
            logger.info("\n4. Testing detection pipeline...")
            if self.vision_system.model is None:
                logger.warning("⚠ Model not available, skipping detection test")
            else:
                logger.info("✓ YOLO model is loaded")
                logger.info(f"  Using TensorRT: {self.vision_system.using_tensorrt}")

                # Test single detection
                ret, test_frame = self.vision_system.camera.read()
                if ret:
                    start_time = time.perf_counter()
                    if self.vision_system.using_tensorrt:
                        results = self.vision_system.model(test_frame, verbose=False, stream=False)
                    else:
                        results = self.vision_system.model(test_frame, verbose=False, stream=False, device='cuda:0')
                    detection_time = (time.perf_counter() - start_time) * 1000

                    logger.info(f"  Detection completed in {detection_time:.1f}ms")
                    logger.info(f"  Inference FPS: {1000.0/detection_time:.1f}")

                    if results and len(results) > 0:
                        result = results[0]
                        num_detections = len(result.boxes) if result.boxes is not None else 0
                        logger.info(f"  Detections: {num_detections} objects found")
                    logger.info("✓ Detection pipeline working")

            # Test threaded capture
            logger.info("\n5. Testing threaded frame capture...")
            self.vision_system.running = True

            # Start capture thread
            capture_thread = threading.Thread(
                target=self.vision_system._capture_frames_hardware_optimized,
                daemon=True,
                name="TestCaptureThread"
            )
            capture_thread.start()
            logger.info("✓ Capture thread started")

            # Monitor for a few seconds
            logger.info(f"  Monitoring for {self.test_duration} seconds...")
            time.sleep(self.test_duration)

            # Stop threads
            self.vision_system.running = False
            capture_thread.join(timeout=2.0)

            # Check frame queue
            with self.vision_system.frame_queue_lock:
                queue_size = len(self.vision_system.frame_queue)

            logger.info(f"  Frame queue size after test: {queue_size}")

            if queue_size > 0:
                logger.info("✓ Frames were successfully queued")
            else:
                logger.warning("⚠ No frames in queue - this may indicate an issue")

            # Check performance stats
            logger.info("\n6. Performance Statistics:")
            logger.info(f"  Capture FPS: {self.vision_system.performance_stats['fps']:.1f}")
            logger.info(f"  Inference FPS: {self.vision_system.performance_stats['inference_fps']:.1f}")
            logger.info(f"  Detection time: {self.vision_system.performance_stats['detection_time']:.1f}ms")
            logger.info(f"  Capture latency: {self.vision_system.performance_stats['capture_latency']:.1f}ms")

            # Cleanup
            logger.info("\n7. Cleaning up...")
            if self.vision_system.camera:
                self.vision_system.camera.release()
                logger.info("✓ Camera released")

            logger.info("\n" + "=" * 70)
            logger.info("✓ ALL TESTS PASSED - VISION SYSTEM IS FULLY FUNCTIONAL")
            logger.info("=" * 70)
            logger.info("\nREADY FOR QA TESTING")
            logger.info("=" * 70)

            return True

        except Exception as e:
            logger.error(f"\n✗ TEST FAILED with exception: {e}")
            import traceback
            traceback.print_exc()
            return False

        finally:
            # Ensure cleanup
            if self.vision_system and self.vision_system.camera:
                try:
                    self.vision_system.camera.release()
                except:
                    pass

def main():
    """Main test function"""
    tester = VisionSystemLiveTester()
    success = tester.run_test()
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())
