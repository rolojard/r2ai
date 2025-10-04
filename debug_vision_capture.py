#!/usr/bin/env python3
"""
Debug Vision System Capture
Quick test to see if camera capture is working
"""

import cv2
import time
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_camera_capture():
    """Test basic camera capture"""
    logger.info("Testing camera capture...")

    # Try different camera indices
    for camera_index in [0, 1, 2]:
        logger.info(f"Trying camera index {camera_index}...")

        try:
            camera = cv2.VideoCapture(camera_index)

            if not camera.isOpened():
                logger.warning(f"Camera {camera_index} not available")
                camera.release()
                continue

            # Test frame capture
            for attempt in range(3):
                ret, frame = camera.read()

                if ret:
                    height, width = frame.shape[:2]
                    logger.info(f"✓ Camera {camera_index}: Frame {attempt+1} - {width}x{height}")
                else:
                    logger.warning(f"✗ Camera {camera_index}: Failed to read frame {attempt+1}")

                time.sleep(0.1)

            camera.release()
            logger.info(f"✓ Camera {camera_index} working properly")
            return camera_index

        except Exception as e:
            logger.error(f"✗ Camera {camera_index} error: {e}")
            if 'camera' in locals():
                camera.release()

    logger.error("No working cameras found!")
    return None

def test_with_vision_settings():
    """Test camera with vision system settings"""
    camera_index = test_camera_capture()

    if camera_index is None:
        return False

    logger.info(f"Testing with vision system settings on camera {camera_index}...")

    try:
        camera = cv2.VideoCapture(camera_index)

        # Apply vision system settings
        camera.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        camera.set(cv2.CAP_PROP_FPS, 15)
        camera.set(cv2.CAP_PROP_BUFFERSIZE, 1)

        # Get actual settings
        width = int(camera.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(camera.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fps = camera.get(cv2.CAP_PROP_FPS)

        logger.info(f"Camera settings: {width}x{height} @ {fps:.1f} FPS")

        # Test continuous capture
        frames_captured = 0
        start_time = time.time()

        for i in range(30):  # Capture 30 frames
            ret, frame = camera.read()

            if ret:
                frames_captured += 1

            time.sleep(1/15)  # 15 FPS

        elapsed = time.time() - start_time
        actual_fps = frames_captured / elapsed

        logger.info(f"Captured {frames_captured}/30 frames in {elapsed:.2f}s ({actual_fps:.1f} FPS)")

        camera.release()

        return frames_captured >= 25  # Success if we got most frames

    except Exception as e:
        logger.error(f"Vision settings test error: {e}")
        if 'camera' in locals():
            camera.release()
        return False

if __name__ == "__main__":
    logger.info("=== VISION CAPTURE DEBUG TEST ===")

    success = test_with_vision_settings()

    if success:
        logger.info("✅ Camera capture is working properly")
        logger.info("The issue is likely in the vision system threading or queue handling")
    else:
        logger.error("❌ Camera capture has issues")
        logger.error("This explains why the vision system isn't sending frames")