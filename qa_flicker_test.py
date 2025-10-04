#!/usr/bin/env python3
"""
QA Flicker Test: Comprehensive Video Stability Analysis
Tests for flickering, frame drops, and video quality issues
"""

import cv2
import numpy as np
import time
import threading
import queue
import json
import sys
from datetime import datetime
import statistics

class FlickerAnalyzer:
    """Analyzes video feed for flickering and stability issues"""

    def __init__(self, camera_index=0):
        self.camera_index = camera_index
        self.frame_queue = queue.Queue(maxsize=100)
        self.analysis_results = []
        self.running = False
        self.total_frames = 0
        self.dropped_frames = 0
        self.brightness_history = []
        self.fps_history = []

    def capture_frames(self, duration_seconds=30):
        """Capture frames for analysis"""
        print(f"🎥 Starting frame capture for {duration_seconds} seconds...")

        cap = cv2.VideoCapture(self.camera_index)
        if not cap.isOpened():
            print(f"❌ Failed to open camera {self.camera_index}")
            return False

        # Set camera properties for optimal performance
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        cap.set(cv2.CAP_PROP_FPS, 30)
        cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

        self.running = True
        start_time = time.time()
        last_frame_time = start_time
        frame_times = []

        while self.running and (time.time() - start_time) < duration_seconds:
            ret, frame = cap.read()
            current_time = time.time()

            if ret and frame is not None:
                self.total_frames += 1

                # Calculate FPS
                if len(frame_times) > 0:
                    fps = 1.0 / (current_time - last_frame_time)
                    self.fps_history.append(fps)

                frame_times.append(current_time)
                last_frame_time = current_time

                # Add frame to queue for analysis
                try:
                    self.frame_queue.put_nowait({
                        'frame': frame.copy(),
                        'timestamp': current_time,
                        'frame_number': self.total_frames
                    })
                except queue.Full:
                    self.dropped_frames += 1

                # Calculate brightness
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                brightness = np.mean(gray)
                self.brightness_history.append(brightness)

            else:
                self.dropped_frames += 1

            # Small delay to prevent overwhelming the system
            time.sleep(0.001)

        cap.release()
        self.running = False
        print(f"✅ Capture complete: {self.total_frames} frames captured")
        return True

    def analyze_flickering(self):
        """Analyze frames for flickering patterns"""
        print("🔍 Analyzing for flickering patterns...")

        if len(self.brightness_history) < 10:
            print("❌ Insufficient data for flicker analysis")
            return None

        # Calculate brightness variance (indicator of flickering)
        brightness_std = statistics.stdev(self.brightness_history)
        brightness_mean = statistics.mean(self.brightness_history)
        brightness_cv = brightness_std / brightness_mean if brightness_mean > 0 else 0

        print(f"   📊 Brightness statistics:")
        print(f"      Mean: {brightness_mean:.2f}")
        print(f"      Std Dev: {brightness_std:.2f}")
        print(f"      Coefficient of Variation: {brightness_cv:.4f}")

        # Detect sudden brightness changes (flickering)
        flicker_events = 0
        threshold = brightness_std * 2  # 2 standard deviations

        for i in range(1, len(self.brightness_history)):
            change = abs(self.brightness_history[i] - self.brightness_history[i-1])
            if change > threshold:
                flicker_events += 1

        flicker_rate = flicker_events / len(self.brightness_history)
        print(f"   ⚡ Flicker events: {flicker_events}")
        print(f"   📈 Flicker rate: {flicker_rate:.4f}")

        # Classification
        if brightness_cv < 0.05 and flicker_rate < 0.01:
            flicker_level = "EXCELLENT"
        elif brightness_cv < 0.1 and flicker_rate < 0.02:
            flicker_level = "GOOD"
        elif brightness_cv < 0.15 and flicker_rate < 0.05:
            flicker_level = "ACCEPTABLE"
        else:
            flicker_level = "POOR"

        return {
            'brightness_cv': brightness_cv,
            'flicker_rate': flicker_rate,
            'flicker_events': flicker_events,
            'level': flicker_level
        }

    def analyze_fps_stability(self):
        """Analyze FPS stability"""
        print("📊 Analyzing FPS stability...")

        if len(self.fps_history) < 10:
            print("❌ Insufficient FPS data")
            return None

        fps_mean = statistics.mean(self.fps_history)
        fps_std = statistics.stdev(self.fps_history)
        fps_min = min(self.fps_history)
        fps_max = max(self.fps_history)
        fps_cv = fps_std / fps_mean if fps_mean > 0 else 0

        print(f"   🎯 FPS statistics:")
        print(f"      Mean FPS: {fps_mean:.2f}")
        print(f"      Std Dev: {fps_std:.2f}")
        print(f"      Min FPS: {fps_min:.2f}")
        print(f"      Max FPS: {fps_max:.2f}")
        print(f"      Coefficient of Variation: {fps_cv:.4f}")

        # Stability classification
        if fps_cv < 0.1 and fps_mean > 25:
            stability_level = "EXCELLENT"
        elif fps_cv < 0.2 and fps_mean > 20:
            stability_level = "GOOD"
        elif fps_cv < 0.3 and fps_mean > 15:
            stability_level = "ACCEPTABLE"
        else:
            stability_level = "POOR"

        return {
            'fps_mean': fps_mean,
            'fps_std': fps_std,
            'fps_min': fps_min,
            'fps_max': fps_max,
            'fps_cv': fps_cv,
            'stability_level': stability_level
        }

    def analyze_frame_consistency(self):
        """Analyze frame-to-frame consistency"""
        print("🔄 Analyzing frame consistency...")

        if self.frame_queue.empty():
            print("❌ No frames available for consistency analysis")
            return None

        frames = []
        while not self.frame_queue.empty():
            try:
                frame_data = self.frame_queue.get_nowait()
                frames.append(frame_data)
            except:
                break

        if len(frames) < 10:
            print("❌ Insufficient frames for consistency analysis")
            return None

        # Calculate frame differences
        differences = []
        for i in range(1, min(len(frames), 100)):  # Analyze first 100 frames
            frame1 = frames[i-1]['frame']
            frame2 = frames[i]['frame']

            # Convert to grayscale for comparison
            gray1 = cv2.cvtColor(frame1, cv2.COLOR_BGR2GRAY)
            gray2 = cv2.cvtColor(frame2, cv2.COLOR_BGR2GRAY)

            # Calculate structural similarity
            diff = cv2.absdiff(gray1, gray2)
            mean_diff = np.mean(diff)
            differences.append(mean_diff)

        if not differences:
            return None

        diff_mean = statistics.mean(differences)
        diff_std = statistics.stdev(differences) if len(differences) > 1 else 0

        print(f"   📏 Frame difference statistics:")
        print(f"      Mean difference: {diff_mean:.2f}")
        print(f"      Std Dev: {diff_std:.2f}")

        # Consistency classification
        if diff_mean < 5 and diff_std < 2:
            consistency_level = "EXCELLENT"
        elif diff_mean < 10 and diff_std < 5:
            consistency_level = "GOOD"
        elif diff_mean < 20 and diff_std < 10:
            consistency_level = "ACCEPTABLE"
        else:
            consistency_level = "POOR"

        return {
            'mean_difference': diff_mean,
            'std_difference': diff_std,
            'consistency_level': consistency_level
        }

def main():
    """Main QA flicker test function"""
    print("🎬 R2D2 QA: Comprehensive Video Flicker Analysis")
    print("=" * 60)

    # Test camera index 0 (confirmed working)
    analyzer = FlickerAnalyzer(camera_index=0)

    # Capture frames for analysis
    success = analyzer.capture_frames(duration_seconds=15)

    if not success:
        print("❌ Failed to capture frames")
        return False

    # Perform analyses
    flicker_results = analyzer.analyze_flickering()
    fps_results = analyzer.analyze_fps_stability()
    consistency_results = analyzer.analyze_frame_consistency()

    # Generate comprehensive report
    print("\n" + "=" * 60)
    print("🎯 COMPREHENSIVE FLICKER ANALYSIS RESULTS")
    print("=" * 60)

    overall_score = 0
    max_score = 0

    if flicker_results:
        print(f"\n⚡ FLICKER ANALYSIS:")
        print(f"   Level: {flicker_results['level']}")
        print(f"   Flicker Rate: {flicker_results['flicker_rate']:.4f}")
        print(f"   Brightness CV: {flicker_results['brightness_cv']:.4f}")

        if flicker_results['level'] == "EXCELLENT":
            overall_score += 4
        elif flicker_results['level'] == "GOOD":
            overall_score += 3
        elif flicker_results['level'] == "ACCEPTABLE":
            overall_score += 2
        else:
            overall_score += 1
        max_score += 4

    if fps_results:
        print(f"\n📊 FPS STABILITY:")
        print(f"   Level: {fps_results['stability_level']}")
        print(f"   Mean FPS: {fps_results['fps_mean']:.2f}")
        print(f"   FPS CV: {fps_results['fps_cv']:.4f}")

        if fps_results['stability_level'] == "EXCELLENT":
            overall_score += 4
        elif fps_results['stability_level'] == "GOOD":
            overall_score += 3
        elif fps_results['stability_level'] == "ACCEPTABLE":
            overall_score += 2
        else:
            overall_score += 1
        max_score += 4

    if consistency_results:
        print(f"\n🔄 FRAME CONSISTENCY:")
        print(f"   Level: {consistency_results['consistency_level']}")
        print(f"   Mean Difference: {consistency_results['mean_difference']:.2f}")

        if consistency_results['consistency_level'] == "EXCELLENT":
            overall_score += 4
        elif consistency_results['consistency_level'] == "GOOD":
            overall_score += 3
        elif consistency_results['consistency_level'] == "ACCEPTABLE":
            overall_score += 2
        else:
            overall_score += 1
        max_score += 4

    # Calculate quality score
    quality_percentage = (overall_score / max_score * 100) if max_score > 0 else 0

    print(f"\n🏆 OVERALL VIDEO QUALITY SCORE: {quality_percentage:.1f}%")

    # Frame statistics
    drop_rate = (analyzer.dropped_frames / analyzer.total_frames * 100) if analyzer.total_frames > 0 else 0
    print(f"\n📋 CAPTURE STATISTICS:")
    print(f"   Total Frames: {analyzer.total_frames}")
    print(f"   Dropped Frames: {analyzer.dropped_frames}")
    print(f"   Drop Rate: {drop_rate:.2f}%")

    # Final assessment
    print(f"\n🎯 FINAL ASSESSMENT:")
    if quality_percentage >= 90:
        print("✅ EXCELLENT: Video feed is stable with no flickering issues")
        assessment = "PASS"
    elif quality_percentage >= 75:
        print("✅ GOOD: Video feed is stable with minimal issues")
        assessment = "PASS"
    elif quality_percentage >= 60:
        print("⚠️  ACCEPTABLE: Video feed has some stability issues")
        assessment = "CONDITIONAL_PASS"
    else:
        print("❌ POOR: Video feed has significant flickering/stability issues")
        assessment = "FAIL"

    # Save results
    results = {
        'timestamp': datetime.now().isoformat(),
        'camera_index': analyzer.camera_index,
        'quality_score': quality_percentage,
        'assessment': assessment,
        'flicker_analysis': flicker_results,
        'fps_analysis': fps_results,
        'consistency_analysis': consistency_results,
        'capture_stats': {
            'total_frames': analyzer.total_frames,
            'dropped_frames': analyzer.dropped_frames,
            'drop_rate': drop_rate
        }
    }

    with open('/home/rolo/r2ai/qa_flicker_test_results.json', 'w') as f:
        json.dump(results, f, indent=2)

    print(f"\n📄 Results saved to: qa_flicker_test_results.json")

    return assessment in ["PASS", "CONDITIONAL_PASS"]

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)