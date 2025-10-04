#!/usr/bin/env python3
"""
Orin Nano Performance Test for Video Capture
Comprehensive testing of camera performance and optimization validation
"""

import cv2
import time
import numpy as np
import threading
import queue
import sys
import argparse

class OrinNanoPerformanceTest:
    def __init__(self, device_id=0):
        self.device_id = device_id
        self.test_results = {}

    def test_basic_capture(self, duration=10):
        """Test basic camera capture performance"""
        print(f"Testing basic capture for {duration} seconds...")

        cap = cv2.VideoCapture(self.device_id, cv2.CAP_V4L2)
        if not cap.isOpened():
            return {"error": "Cannot open camera"}

        # Basic settings
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        cap.set(cv2.CAP_PROP_FPS, 30)

        frames_captured = 0
        start_time = time.time()
        frame_times = []

        while time.time() - start_time < duration:
            frame_start = time.time()
            ret, frame = cap.read()

            if ret:
                frames_captured += 1
                frame_times.append(time.time() - frame_start)
            else:
                print("Failed to capture frame")

        cap.release()

        total_time = time.time() - start_time
        avg_fps = frames_captured / total_time
        avg_frame_time = np.mean(frame_times) if frame_times else 0

        result = {
            "frames_captured": frames_captured,
            "duration": total_time,
            "avg_fps": avg_fps,
            "avg_frame_time_ms": avg_frame_time * 1000,
            "target_fps": 30
        }

        print(f"Basic capture: {avg_fps:.2f} FPS ({frames_captured} frames in {total_time:.2f}s)")
        return result

    def test_optimized_capture(self, duration=10):
        """Test optimized camera capture with Orin Nano settings"""
        print(f"Testing optimized capture for {duration} seconds...")

        cap = cv2.VideoCapture(self.device_id, cv2.CAP_V4L2)
        if not cap.isOpened():
            return {"error": "Cannot open camera"}

        # Orin Nano optimizations
        optimizations = [
            (cv2.CAP_PROP_FRAME_WIDTH, 640),
            (cv2.CAP_PROP_FRAME_HEIGHT, 480),
            (cv2.CAP_PROP_FPS, 30),
            (cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc('M','J','P','G')),
            (cv2.CAP_PROP_BUFFERSIZE, 1),
            (cv2.CAP_PROP_AUTO_EXPOSURE, 0.25),
            (cv2.CAP_PROP_EXPOSURE, -5),
        ]

        for prop, value in optimizations:
            cap.set(prop, value)

        # Warm up
        for _ in range(5):
            cap.read()

        frames_captured = 0
        start_time = time.time()
        frame_times = []

        while time.time() - start_time < duration:
            frame_start = time.time()

            # Use grab/retrieve for better performance
            cap.grab()
            ret, frame = cap.retrieve()

            if ret:
                frames_captured += 1
                frame_times.append(time.time() - frame_start)

        cap.release()

        total_time = time.time() - start_time
        avg_fps = frames_captured / total_time
        avg_frame_time = np.mean(frame_times) if frame_times else 0

        result = {
            "frames_captured": frames_captured,
            "duration": total_time,
            "avg_fps": avg_fps,
            "avg_frame_time_ms": avg_frame_time * 1000,
            "target_fps": 30
        }

        print(f"Optimized capture: {avg_fps:.2f} FPS ({frames_captured} frames in {total_time:.2f}s)")
        return result

    def test_threaded_capture(self, duration=10):
        """Test threaded capture for maximum performance"""
        print(f"Testing threaded capture for {duration} seconds...")

        cap = cv2.VideoCapture(self.device_id, cv2.CAP_V4L2)
        if not cap.isOpened():
            return {"error": "Cannot open camera"}

        # Apply optimizations
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        cap.set(cv2.CAP_PROP_FPS, 30)
        cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc('M','J','P','G'))
        cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

        frame_queue = queue.Queue(maxsize=2)
        frames_captured = 0
        capture_running = True

        def capture_worker():
            nonlocal frames_captured
            while capture_running:
                ret, frame = cap.read()
                if ret:
                    try:
                        frame_queue.put_nowait(frame)
                        frames_captured += 1
                    except queue.Full:
                        # Drop oldest frame
                        try:
                            frame_queue.get_nowait()
                            frame_queue.put_nowait(frame)
                        except queue.Empty:
                            pass

        # Start capture thread
        capture_thread = threading.Thread(target=capture_worker)
        capture_thread.daemon = True
        capture_thread.start()

        start_time = time.time()
        processed_frames = 0

        while time.time() - start_time < duration:
            try:
                frame = frame_queue.get(timeout=0.1)
                if frame is not None:
                    processed_frames += 1
                    # Simulate processing
                    time.sleep(0.001)
            except queue.Empty:
                continue

        capture_running = False
        capture_thread.join(timeout=1)
        cap.release()

        total_time = time.time() - start_time
        capture_fps = frames_captured / total_time
        processing_fps = processed_frames / total_time

        result = {
            "frames_captured": frames_captured,
            "frames_processed": processed_frames,
            "duration": total_time,
            "capture_fps": capture_fps,
            "processing_fps": processing_fps,
            "target_fps": 30
        }

        print(f"Threaded capture: {capture_fps:.2f} FPS capture, {processing_fps:.2f} FPS processing")
        return result

    def test_cpu_gpu_utilization(self, duration=5):
        """Test CPU/GPU utilization during video capture"""
        print(f"Testing system utilization for {duration} seconds...")

        # This is a placeholder for system monitoring
        # In a real implementation, you would monitor:
        # - CPU usage
        # - GPU usage
        # - Memory usage
        # - Temperature

        import subprocess

        def get_cpu_usage():
            try:
                result = subprocess.run(['cat', '/proc/loadavg'], capture_output=True, text=True)
                return result.stdout.split()[0] if result.returncode == 0 else 0
            except:
                return 0

        cap = cv2.VideoCapture(self.device_id, cv2.CAP_V4L2)
        if not cap.isOpened():
            return {"error": "Cannot open camera"}

        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        cap.set(cv2.CAP_PROP_FPS, 30)

        start_time = time.time()
        frames_captured = 0
        cpu_samples = []

        while time.time() - start_time < duration:
            ret, frame = cap.read()
            if ret:
                frames_captured += 1

                # Sample CPU usage
                if frames_captured % 30 == 0:  # Every ~1 second at 30 FPS
                    cpu_usage = get_cpu_usage()
                    cpu_samples.append(float(cpu_usage))

        cap.release()

        total_time = time.time() - start_time
        avg_fps = frames_captured / total_time
        avg_cpu = np.mean(cpu_samples) if cpu_samples else 0

        result = {
            "frames_captured": frames_captured,
            "duration": total_time,
            "avg_fps": avg_fps,
            "avg_cpu_load": avg_cpu,
            "cpu_samples": len(cpu_samples)
        }

        print(f"System utilization: {avg_fps:.2f} FPS, CPU load: {avg_cpu:.2f}")
        return result

    def run_all_tests(self):
        """Run comprehensive performance tests"""
        print("=== Orin Nano Camera Performance Test Suite ===")

        tests = [
            ("Basic Capture", self.test_basic_capture),
            ("Optimized Capture", self.test_optimized_capture),
            ("Threaded Capture", self.test_threaded_capture),
            ("System Utilization", self.test_cpu_gpu_utilization),
        ]

        results = {}

        for test_name, test_func in tests:
            print(f"\n--- {test_name} ---")
            try:
                result = test_func()
                results[test_name] = result
            except Exception as e:
                print(f"Test failed: {e}")
                results[test_name] = {"error": str(e)}

        return results

    def print_summary(self, results):
        """Print test summary"""
        print("\n=== Test Summary ===")

        for test_name, result in results.items():
            print(f"\n{test_name}:")
            if "error" in result:
                print(f"  ERROR: {result['error']}")
            else:
                if "avg_fps" in result:
                    fps = result["avg_fps"]
                    status = "PASS" if fps >= 25 else "FAIL"
                    print(f"  FPS: {fps:.2f} ({status})")

                if "avg_frame_time_ms" in result:
                    print(f"  Frame Time: {result['avg_frame_time_ms']:.2f} ms")

                if "capture_fps" in result:
                    print(f"  Capture FPS: {result['capture_fps']:.2f}")
                    print(f"  Processing FPS: {result['processing_fps']:.2f}")

                if "avg_cpu_load" in result:
                    print(f"  CPU Load: {result['avg_cpu_load']:.2f}")

        # Overall assessment
        basic_fps = results.get("Basic Capture", {}).get("avg_fps", 0)
        optimized_fps = results.get("Optimized Capture", {}).get("avg_fps", 0)
        threaded_fps = results.get("Threaded Capture", {}).get("capture_fps", 0)

        print(f"\n=== Performance Assessment ===")
        print(f"Basic FPS: {basic_fps:.2f}")
        print(f"Optimized FPS: {optimized_fps:.2f}")
        print(f"Threaded FPS: {threaded_fps:.2f}")

        improvement = ((optimized_fps - basic_fps) / basic_fps * 100) if basic_fps > 0 else 0
        print(f"Optimization Improvement: {improvement:.1f}%")

        if optimized_fps >= 25:
            print("STATUS: READY for R2D2 dashboard integration")
        else:
            print("STATUS: NEEDS further optimization")

def main():
    parser = argparse.ArgumentParser(description='Orin Nano Camera Performance Test')
    parser.add_argument('--device', '-d', type=int, default=0,
                       help='Camera device ID (default: 0)')
    parser.add_argument('--duration', '-t', type=int, default=10,
                       help='Test duration in seconds (default: 10)')

    args = parser.parse_args()

    tester = OrinNanoPerformanceTest(device_id=args.device)
    results = tester.run_all_tests()
    tester.print_summary(results)

if __name__ == "__main__":
    main()