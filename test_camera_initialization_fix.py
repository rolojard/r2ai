#!/usr/bin/env python3
"""
Camera Initialization Fix Validation Test
Tests the camera initialization with various scenarios
"""

import cv2
import numpy as np
import sys
import time
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_camera_device_index():
    """Test camera with device index (correct way)"""
    logger.info("=" * 60)
    logger.info("TEST 1: Camera initialization with device index (0)")
    logger.info("=" * 60)

    try:
        camera = cv2.VideoCapture(0, cv2.CAP_V4L2)

        if not camera.isOpened():
            logger.error("FAIL: Camera failed to open with device index 0")
            return False

        logger.info("SUCCESS: Camera opened with device index 0")

        # Test frame capture
        ret, frame = camera.read()
        if not ret:
            logger.error("FAIL: Failed to capture frame")
            camera.release()
            return False

        logger.info(f"SUCCESS: Frame captured - shape: {frame.shape}, dtype: {frame.dtype}")
        logger.info(f"Frame stats - min: {frame.min()}, max: {frame.max()}, mean: {frame.mean():.1f}")

        # Verify frame is not black
        if frame.max() == 0:
            logger.error("FAIL: Captured frame is all black!")
            camera.release()
            return False

        logger.info("SUCCESS: Frame has valid pixel data")

        camera.release()
        return True

    except Exception as e:
        logger.error(f"FAIL: Exception during camera test: {e}")
        return False

def test_camera_device_path():
    """Test camera with device path (legacy way - may not work with V4L2)"""
    logger.info("=" * 60)
    logger.info("TEST 2: Camera initialization with device path (/dev/video0)")
    logger.info("=" * 60)

    try:
        # This may fail with V4L2 backend on some systems
        camera = cv2.VideoCapture('/dev/video0', cv2.CAP_V4L2)

        if not camera.isOpened():
            logger.warning("Camera failed to open with device path - this is EXPECTED behavior")
            logger.info("OpenCV V4L2 backend prefers integer device indices over paths")
            return True  # Not a failure - just documenting expected behavior

        logger.info("Camera opened with device path (some systems support this)")
        camera.release()
        return True

    except Exception as e:
        logger.warning(f"Exception with device path: {e} - this is EXPECTED")
        return True

def test_camera_without_backend():
    """Test camera without explicit backend (OpenCV auto-detect)"""
    logger.info("=" * 60)
    logger.info("TEST 3: Camera initialization without explicit backend")
    logger.info("=" * 60)

    try:
        camera = cv2.VideoCapture(0)

        if not camera.isOpened():
            logger.error("FAIL: Camera failed to open without backend specification")
            return False

        logger.info("SUCCESS: Camera opened without explicit backend")

        # Get backend name
        backend = camera.getBackendName()
        logger.info(f"Auto-detected backend: {backend}")

        # Test frame capture
        ret, frame = camera.read()
        if not ret:
            logger.error("FAIL: Failed to capture frame")
            camera.release()
            return False

        logger.info(f"SUCCESS: Frame captured - shape: {frame.shape}")

        camera.release()
        return True

    except Exception as e:
        logger.error(f"FAIL: Exception during camera test: {e}")
        return False

def test_camera_parameters():
    """Test setting camera parameters as in the vision system"""
    logger.info("=" * 60)
    logger.info("TEST 4: Camera parameter configuration")
    logger.info("=" * 60)

    try:
        camera = cv2.VideoCapture(0, cv2.CAP_V4L2)

        if not camera.isOpened():
            logger.error("FAIL: Camera failed to open")
            return False

        # Set parameters as in OrinNanoOptimizedVision
        params = {
            'width': 640,
            'height': 480,
            'fps': 15,
            'buffer_size': 1,
            'codec': cv2.VideoWriter_fourcc('M', 'J', 'P', 'G')
        }

        success_count = 0
        total_count = 0

        total_count += 1
        if camera.set(cv2.CAP_PROP_FRAME_WIDTH, params['width']):
            success_count += 1

        total_count += 1
        if camera.set(cv2.CAP_PROP_FRAME_HEIGHT, params['height']):
            success_count += 1

        total_count += 1
        if camera.set(cv2.CAP_PROP_FPS, params['fps']):
            success_count += 1

        total_count += 1
        if camera.set(cv2.CAP_PROP_BUFFERSIZE, params['buffer_size']):
            success_count += 1

        total_count += 1
        if camera.set(cv2.CAP_PROP_FOURCC, params['codec']):
            success_count += 1

        logger.info(f"Parameter setting success rate: {success_count}/{total_count}")

        # Verify actual settings
        actual_width = int(camera.get(cv2.CAP_PROP_FRAME_WIDTH))
        actual_height = int(camera.get(cv2.CAP_PROP_FRAME_HEIGHT))
        actual_fps = camera.get(cv2.CAP_PROP_FPS)
        actual_buffer = int(camera.get(cv2.CAP_PROP_BUFFERSIZE))

        logger.info(f"Actual camera config: {actual_width}x{actual_height} @ {actual_fps}fps, buffer: {actual_buffer}")

        # Capture multiple frames to verify stability
        logger.info("Capturing 10 frames to verify stability...")
        for i in range(10):
            ret, frame = camera.read()
            if not ret:
                logger.error(f"FAIL: Failed to capture frame {i+1}/10")
                camera.release()
                return False

            if i == 0:
                logger.info(f"Frame {i+1}: shape={frame.shape}, min={frame.min()}, max={frame.max()}, mean={frame.mean():.1f}")

        logger.info("SUCCESS: All 10 frames captured successfully")

        camera.release()
        return True

    except Exception as e:
        logger.error(f"FAIL: Exception during parameter test: {e}")
        return False

def test_vision_system_import():
    """Test importing and initializing the actual vision system"""
    logger.info("=" * 60)
    logger.info("TEST 5: Vision system class initialization")
    logger.info("=" * 60)

    try:
        # Import the vision system
        sys.path.insert(0, '/home/rolo/r2ai')
        from r2d2_orin_nano_optimized_vision import OrinNanoOptimizedVision

        logger.info("SUCCESS: Vision system module imported")

        # Create instance (but don't start it)
        vision = OrinNanoOptimizedVision(websocket_port=8767, camera_device=0)
        logger.info("SUCCESS: Vision system instance created")

        # Check initialization
        logger.info(f"Camera device configured: {vision.camera_device}")
        logger.info(f"Camera device type: {type(vision.camera_device)}")

        if vision.camera_device != 0:
            logger.error(f"FAIL: Camera device should be 0, got {vision.camera_device}")
            return False

        if not isinstance(vision.camera_device, int):
            logger.error(f"FAIL: Camera device should be int, got {type(vision.camera_device)}")
            return False

        logger.info("SUCCESS: Camera device is correctly configured as integer index")

        return True

    except Exception as e:
        logger.error(f"FAIL: Exception during vision system test: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all tests"""
    logger.info("\n" + "=" * 60)
    logger.info("CAMERA INITIALIZATION FIX VALIDATION TEST SUITE")
    logger.info("=" * 60 + "\n")

    tests = [
        ("Camera Device Index", test_camera_device_index),
        ("Camera Device Path", test_camera_device_path),
        ("Camera Auto-Backend", test_camera_without_backend),
        ("Camera Parameters", test_camera_parameters),
        ("Vision System Import", test_vision_system_import)
    ]

    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
            logger.info("")
            time.sleep(0.5)  # Brief pause between tests
        except Exception as e:
            logger.error(f"Test {test_name} crashed: {e}")
            results.append((test_name, False))

    # Summary
    logger.info("\n" + "=" * 60)
    logger.info("TEST SUMMARY")
    logger.info("=" * 60)

    passed = 0
    failed = 0

    for test_name, result in results:
        status = "PASS" if result else "FAIL"
        symbol = "✓" if result else "✗"
        logger.info(f"{symbol} {test_name}: {status}")
        if result:
            passed += 1
        else:
            failed += 1

    logger.info("=" * 60)
    logger.info(f"Total: {len(results)} tests | Passed: {passed} | Failed: {failed}")
    logger.info("=" * 60)

    if failed == 0:
        logger.info("\n✓ ALL TESTS PASSED - Camera initialization fix is WORKING")
        logger.info("✓ Vision system is READY for QA testing")
        return 0
    else:
        logger.error(f"\n✗ {failed} TEST(S) FAILED - Camera initialization needs attention")
        return 1

if __name__ == "__main__":
    sys.exit(main())
