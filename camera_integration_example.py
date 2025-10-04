#!/usr/bin/env python3
"""
Example: Safe Camera Integration for Agents
"""

from orin_nano_camera_resource_manager import acquire_camera
from orin_nano_memory_optimizer import get_memory_status, emergency_cleanup
import cv2
import time

def safe_camera_processing():
    """Example of safe camera processing"""

    # Check memory before starting
    memory_status = get_memory_status()
    if memory_status['system']['used_percent'] > 80:
        print("Warning: High memory usage before camera operation")
        emergency_cleanup()

    # Safe camera access
    try:
        with acquire_camera(0) as camera:
            print("Camera acquired successfully")

            for i in range(50):  # Process 50 frames
                ret, frame = camera.read()
                if not ret:
                    print(f"Frame capture failed at {i}")
                    break

                # Process frame (your AI/vision code here)
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

                # Monitor memory during processing
                if i % 10 == 0:
                    memory_status = get_memory_status()
                    if memory_status['system']['used_percent'] > 85:
                        print("High memory usage detected, performing cleanup")
                        emergency_cleanup()

                time.sleep(0.1)  # Simulate processing time

            print("Camera processing completed successfully")

    except Exception as e:
        print(f"Camera processing failed: {e}")
        # Emergency cleanup on error
        emergency_cleanup()

if __name__ == "__main__":
    safe_camera_processing()
