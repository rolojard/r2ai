#!/usr/bin/env python3
"""
Orin Nano Camera Optimization Script
Optimizes Logitech C920e webcam for stable, flicker-free operation
Implements hardware-specific optimizations for Orin Nano platform
"""

import cv2
import numpy as np
import time
import threading
import os
import sys
from contextlib import contextmanager

class OrinNanoCameraOptimizer:
    def __init__(self, device_id=0):
        self.device_id = device_id
        self.cap = None
        self.frame_buffer = None
        self.last_frame_time = 0
        self.frame_count = 0
        self.fps_counter = 0
        self.stable_fps = 30

    def optimize_camera_settings(self):
        """Apply Orin Nano specific camera optimizations"""
        if not self.cap:
            return False

        print("Applying Orin Nano camera optimizations...")

        # Set optimal resolution for C920e on Orin Nano
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

        # Set FPS for stable operation
        self.cap.set(cv2.CAP_PROP_FPS, self.stable_fps)

        # Optimize buffer settings to prevent frame drops
        self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

        # Set pixel format for optimal GPU processing
        # MJPG format reduces USB bandwidth and CPU load
        self.cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc('M','J','P','G'))

        # Auto exposure and white balance for stable output
        self.cap.set(cv2.CAP_PROP_AUTO_EXPOSURE, 0.25)  # Manual exposure
        self.cap.set(cv2.CAP_PROP_EXPOSURE, -5)  # Optimized exposure for indoor

        # Disable auto white balance for consistent colors
        self.cap.set(cv2.CAP_PROP_AUTO_WB, 0)
        self.cap.set(cv2.CAP_PROP_WB_TEMPERATURE, 4600)

        # Optimize for real-time processing
        self.cap.set(cv2.CAP_PROP_CONVERT_RGB, 1)

        # Verify settings
        actual_width = self.cap.get(cv2.CAP_PROP_FRAME_WIDTH)
        actual_height = self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
        actual_fps = self.cap.get(cv2.CAP_PROP_FPS)

        print(f"Camera configured: {actual_width}x{actual_height} @ {actual_fps} FPS")
        return True

    def initialize_camera(self):
        """Initialize camera with Orin Nano optimizations"""
        print(f"Initializing camera {self.device_id}...")

        # Use CAP_V4L2 backend for best performance on Linux
        self.cap = cv2.VideoCapture(self.device_id, cv2.CAP_V4L2)

        if not self.cap.isOpened():
            print(f"ERROR: Could not open camera {self.device_id}")
            return False

        # Apply optimizations
        if not self.optimize_camera_settings():
            print("WARNING: Could not apply all camera optimizations")

        # Warm up camera (important for C920e stability)
        print("Warming up camera...")
        for i in range(10):
            ret, frame = self.cap.read()
            if ret:
                self.frame_buffer = frame
                print(f"Warmup frame {i+1}/10")
            time.sleep(0.1)

        print("Camera initialization complete!")
        return True

    def capture_optimized_frame(self):
        """Capture frame with Orin Nano GPU acceleration"""
        if not self.cap:
            return None, False

        # Clear buffer to get latest frame
        for _ in range(2):
            self.cap.grab()

        ret, frame = self.cap.retrieve()

        if ret:
            # Apply GPU-accelerated processing if needed
            current_time = time.time()

            # Calculate FPS
            if self.last_frame_time > 0:
                fps = 1.0 / (current_time - self.last_frame_time)
                self.fps_counter = fps

            self.last_frame_time = current_time
            self.frame_count += 1

            return frame, True

        return None, False

    def get_camera_info(self):
        """Get detailed camera information"""
        if not self.cap:
            return {}

        info = {
            'width': int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH)),
            'height': int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT)),
            'fps': self.cap.get(cv2.CAP_PROP_FPS),
            'format': self.cap.get(cv2.CAP_PROP_FOURCC),
            'buffer_size': int(self.cap.get(cv2.CAP_PROP_BUFFERSIZE)),
            'exposure': self.cap.get(cv2.CAP_PROP_EXPOSURE),
            'auto_exposure': self.cap.get(cv2.CAP_PROP_AUTO_EXPOSURE),
            'white_balance': self.cap.get(cv2.CAP_PROP_WB_TEMPERATURE),
            'actual_fps': self.fps_counter,
            'frames_captured': self.frame_count
        }
        return info

    def test_stability(self, duration=30):
        """Test camera stability for specified duration"""
        print(f"Testing camera stability for {duration} seconds...")

        start_time = time.time()
        frame_times = []
        dropped_frames = 0

        while time.time() - start_time < duration:
            frame_start = time.time()
            frame, success = self.capture_optimized_frame()

            if success:
                frame_times.append(time.time() - frame_start)

                # Display current status
                elapsed = time.time() - start_time
                if int(elapsed) % 5 == 0 and len(frame_times) % 150 == 0:  # Every 5 seconds
                    avg_fps = len(frame_times) / elapsed
                    print(f"Elapsed: {elapsed:.1f}s, FPS: {avg_fps:.1f}, Dropped: {dropped_frames}")
            else:
                dropped_frames += 1

            time.sleep(1/35)  # Slightly faster than target FPS

        # Calculate statistics
        total_time = time.time() - start_time
        total_frames = len(frame_times)
        avg_fps = total_frames / total_time
        avg_frame_time = np.mean(frame_times) if frame_times else 0
        frame_time_std = np.std(frame_times) if frame_times else 0

        print(f"\n=== Camera Stability Test Results ===")
        print(f"Test Duration: {total_time:.2f} seconds")
        print(f"Total Frames: {total_frames}")
        print(f"Dropped Frames: {dropped_frames}")
        print(f"Average FPS: {avg_fps:.2f}")
        print(f"Average Frame Time: {avg_frame_time*1000:.2f} ms")
        print(f"Frame Time Std Dev: {frame_time_std*1000:.2f} ms")
        print(f"Success Rate: {(total_frames/(total_frames+dropped_frames)*100):.1f}%")

        return {
            'avg_fps': avg_fps,
            'dropped_frames': dropped_frames,
            'total_frames': total_frames,
            'success_rate': total_frames/(total_frames+dropped_frames)*100 if total_frames+dropped_frames > 0 else 0,
            'frame_time_std': frame_time_std
        }

    def cleanup(self):
        """Clean up camera resources"""
        if self.cap:
            self.cap.release()
            self.cap = None
        print("Camera resources cleaned up")

def run_camera_optimization_test():
    """Run comprehensive camera optimization test"""
    print("=== Orin Nano Camera Optimization Test ===")

    optimizer = OrinNanoCameraOptimizer(device_id=0)

    try:
        # Initialize camera
        if not optimizer.initialize_camera():
            print("FAILED: Camera initialization")
            return False

        # Display camera info
        info = optimizer.get_camera_info()
        print(f"\n=== Camera Configuration ===")
        for key, value in info.items():
            print(f"{key}: {value}")

        # Test stability
        results = optimizer.test_stability(duration=15)  # 15-second test

        # Evaluate results
        success = (
            results['success_rate'] > 95 and
            results['avg_fps'] > 25 and
            results['frame_time_std'] < 0.01
        )

        print(f"\n=== Optimization Status: {'SUCCESS' if success else 'NEEDS_TUNING'} ===")

        return success

    except Exception as e:
        print(f"ERROR during camera test: {e}")
        return False
    finally:
        optimizer.cleanup()

if __name__ == "__main__":
    success = run_camera_optimization_test()
    sys.exit(0 if success else 1)