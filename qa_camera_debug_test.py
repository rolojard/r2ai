#!/usr/bin/env python3
"""
QA Camera Debug Test
Quick test to verify camera functionality and identify issues
"""

import cv2
import time
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_camera_access():
    """Test basic camera access"""
    logger.info("Testing camera access...")

    try:
        # Test camera initialization
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            logger.error("Failed to open camera")
            return False

        # Test frame capture
        ret, frame = cap.read()
        if not ret:
            logger.error("Failed to capture frame")
            cap.release()
            return False

        logger.info(f"Camera working! Frame shape: {frame.shape}")

        # Test multiple frames
        for i in range(5):
            ret, frame = cap.read()
            if ret:
                logger.info(f"Frame {i+1}: OK - {frame.shape}")
            else:
                logger.error(f"Frame {i+1}: FAILED")

        cap.release()
        logger.info("Camera test completed successfully")
        return True

    except Exception as e:
        logger.error(f"Camera test failed: {e}")
        return False

def test_video_device_info():
    """Get video device information"""
    logger.info("Checking video device info...")

    import subprocess
    try:
        # Get device info
        result = subprocess.run(['v4l2-ctl', '--device=/dev/video0', '--info'],
                              capture_output=True, text=True)
        if result.returncode == 0:
            logger.info(f"Video device info:\n{result.stdout}")
        else:
            logger.warning("v4l2-ctl not available or failed")

        # Check available formats
        result = subprocess.run(['v4l2-ctl', '--device=/dev/video0', '--list-formats-ext'],
                              capture_output=True, text=True)
        if result.returncode == 0:
            logger.info(f"Available formats:\n{result.stdout}")

    except Exception as e:
        logger.warning(f"Could not get device info: {e}")

if __name__ == "__main__":
    logger.info("=== QA Camera Debug Test ===")

    # Test 1: Basic camera access
    camera_works = test_camera_access()

    # Test 2: Device information
    test_video_device_info()

    # Results
    if camera_works:
        logger.info("✅ CAMERA IS WORKING - Issue is in vision system implementation")
    else:
        logger.error("❌ CAMERA ACCESS FAILED - Hardware or permission issue")