#!/usr/bin/env python3
"""
Webcam Diagnostic Tool
Tests basic webcam access and identifies hardware/driver issues
"""

import cv2
import numpy as np
import time
import sys
import os

def test_camera_access():
    """Test basic camera access and enumerate available cameras"""
    print("🔍 Testing Camera Access")
    print("=" * 50)

    available_cameras = []

    # Test camera indices 0-5
    for i in range(6):
        print(f"Testing camera index {i}...", end=" ")
        try:
            cap = cv2.VideoCapture(i)
            if cap.isOpened():
                ret, frame = cap.read()
                if ret and frame is not None:
                    h, w = frame.shape[:2]
                    print(f"✅ WORKING - Resolution: {w}x{h}")
                    available_cameras.append({
                        'index': i,
                        'resolution': (w, h),
                        'capture': cap
                    })
                else:
                    print("❌ Can open but no frame")
                    cap.release()
            else:
                print("❌ Cannot open")
                cap.release()
        except Exception as e:
            print(f"❌ Error: {e}")

    return available_cameras

def test_camera_properties(camera_info):
    """Test camera properties and optimal settings"""
    print(f"\n🔧 Testing Camera {camera_info['index']} Properties")
    print("-" * 40)

    cap = camera_info['capture']

    # Test current properties
    properties = {
        'Width': cv2.CAP_PROP_FRAME_WIDTH,
        'Height': cv2.CAP_PROP_FRAME_HEIGHT,
        'FPS': cv2.CAP_PROP_FPS,
        'Buffer Size': cv2.CAP_PROP_BUFFERSIZE,
        'Backend': cv2.CAP_PROP_BACKEND,
        'Brightness': cv2.CAP_PROP_BRIGHTNESS,
        'Contrast': cv2.CAP_PROP_CONTRAST,
        'Saturation': cv2.CAP_PROP_SATURATION,
    }

    for name, prop in properties.items():
        try:
            value = cap.get(prop)
            print(f"{name}: {value}")
        except:
            print(f"{name}: N/A")

    # Test setting optimal properties
    print("\n🎯 Setting Optimal Properties")
    optimal_settings = [
        (cv2.CAP_PROP_FRAME_WIDTH, 640),
        (cv2.CAP_PROP_FRAME_HEIGHT, 480),
        (cv2.CAP_PROP_FPS, 30),
        (cv2.CAP_PROP_BUFFERSIZE, 1),
    ]

    for prop, value in optimal_settings:
        try:
            cap.set(prop, value)
            actual = cap.get(prop)
            prop_name = [k for k, v in properties.items() if v == prop][0]
            print(f"{prop_name}: Set {value} -> Got {actual}")
        except Exception as e:
            print(f"Failed to set property: {e}")

def test_frame_capture_stability(camera_info, duration=10):
    """Test frame capture stability and timing"""
    print(f"\n📹 Testing Frame Capture Stability ({duration}s)")
    print("-" * 40)

    cap = camera_info['capture']

    frame_times = []
    successful_frames = 0
    failed_frames = 0

    start_time = time.time()
    last_frame_time = start_time

    while time.time() - start_time < duration:
        ret, frame = cap.read()
        current_time = time.time()

        if ret and frame is not None:
            frame_interval = current_time - last_frame_time
            frame_times.append(frame_interval)
            successful_frames += 1
            last_frame_time = current_time
        else:
            failed_frames += 1

        # Small delay to prevent overwhelming the camera
        time.sleep(0.01)

    # Calculate statistics
    if frame_times:
        avg_interval = np.mean(frame_times)
        std_interval = np.std(frame_times)
        fps = 1.0 / avg_interval if avg_interval > 0 else 0

        print(f"Successful frames: {successful_frames}")
        print(f"Failed frames: {failed_frames}")
        print(f"Average FPS: {fps:.2f}")
        print(f"Frame interval: {avg_interval:.4f}s ± {std_interval:.4f}s")
        print(f"Frame rate stability: {'Good' if std_interval < 0.01 else 'Poor'}")

        return {
            'fps': fps,
            'stability': std_interval,
            'success_rate': successful_frames / (successful_frames + failed_frames)
        }
    else:
        print("❌ No successful frames captured!")
        return None

def test_memory_usage():
    """Test memory usage during capture"""
    print(f"\n💾 Testing Memory Usage")
    print("-" * 40)

    try:
        import psutil
        process = psutil.Process()
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        print(f"Initial memory: {initial_memory:.2f} MB")
        return initial_memory
    except ImportError:
        print("psutil not available - cannot test memory usage")
        return None

def main():
    """Main diagnostic function"""
    print("🤖 R2D2 Webcam Diagnostic Tool")
    print("=" * 50)

    # Test memory before starting
    initial_memory = test_memory_usage()

    # Test camera access
    cameras = test_camera_access()

    if not cameras:
        print("\n❌ No working cameras found!")
        print("Possible issues:")
        print("- Camera not connected")
        print("- Driver issues")
        print("- Permission problems")
        print("- Camera in use by another application")
        sys.exit(1)

    print(f"\n✅ Found {len(cameras)} working camera(s)")

    # Test each camera in detail
    for camera_info in cameras:
        test_camera_properties(camera_info)
        stability = test_frame_capture_stability(camera_info)

        if stability:
            print(f"\n📊 Camera {camera_info['index']} Summary:")
            print(f"  FPS: {stability['fps']:.2f}")
            print(f"  Stability: {stability['stability']:.4f}")
            print(f"  Success Rate: {stability['success_rate']:.2%}")

            # Recommend best camera
            if stability['fps'] > 15 and stability['stability'] < 0.02 and stability['success_rate'] > 0.95:
                print(f"  🌟 RECOMMENDED for R2D2 Vision System")
            else:
                print(f"  ⚠️  May have stability issues")

    # Clean up
    for camera_info in cameras:
        camera_info['capture'].release()

    # Final memory check
    if initial_memory:
        try:
            import psutil
            process = psutil.Process()
            final_memory = process.memory_info().rss / 1024 / 1024  # MB
            memory_diff = final_memory - initial_memory
            print(f"\nMemory usage change: {memory_diff:+.2f} MB")
        except:
            pass

    print("\n🏁 Diagnostic Complete")

if __name__ == "__main__":
    main()