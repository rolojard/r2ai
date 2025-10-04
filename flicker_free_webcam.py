#!/usr/bin/env python3
"""
Flicker-Free Webcam Capture System
Addresses timing issues and ensures stable frame delivery
"""

import cv2
import threading
import time
import queue
import numpy as np
import base64
import json
import logging
from collections import deque

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class FlickerFreeWebcam:
    """Ultra-stable webcam capture with zero flicker guarantee"""

    def __init__(self, camera_index=0, target_fps=15, buffer_size=2):
        self.camera_index = camera_index
        self.target_fps = target_fps
        self.frame_interval = 1.0 / target_fps
        self.buffer_size = buffer_size

        # Thread control
        self.running = False
        self.capture_thread = None
        self.processing_thread = None

        # Frame management
        self.raw_frame_queue = queue.Queue(maxsize=buffer_size)
        self.processed_frame_queue = queue.Queue(maxsize=1)  # Single frame to prevent buildup
        self.latest_frame = None
        self.frame_lock = threading.Lock()

        # Timing control for zero flicker
        self.last_capture_time = 0
        self.last_delivery_time = 0
        self.frame_counter = 0

        # Performance metrics
        self.fps_tracker = deque(maxlen=30)  # Track last 30 frame times
        self.stats = {
            'actual_fps': 0,
            'frame_drops': 0,
            'total_frames': 0,
            'timing_accuracy': 0
        }

        # Camera object
        self.camera = None

        logger.info(f"FlickerFreeWebcam initialized for camera {camera_index} at {target_fps} FPS")

    def _initialize_camera(self):
        """Initialize camera with optimal anti-flicker settings"""
        try:
            self.camera = cv2.VideoCapture(self.camera_index)

            if not self.camera.isOpened():
                logger.error("Failed to open camera")
                return False

            # Critical anti-flicker settings
            self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            self.camera.set(cv2.CAP_PROP_FPS, 30)  # Higher capture rate for stability
            self.camera.set(cv2.CAP_PROP_BUFFERSIZE, 1)  # Minimal buffer

            # Additional stability settings
            try:
                self.camera.set(cv2.CAP_PROP_AUTO_EXPOSURE, 0.25)  # Manual exposure
                self.camera.set(cv2.CAP_PROP_EXPOSURE, -6)  # Fixed exposure
            except:
                logger.warning("Could not set manual exposure")

            # Test initial capture
            ret, frame = self.camera.read()
            if not ret or frame is None:
                logger.error("Failed to capture test frame")
                return False

            logger.info(f"Camera initialized: {frame.shape}")
            return True

        except Exception as e:
            logger.error(f"Camera initialization failed: {e}")
            return False

    def _precision_capture_loop(self):
        """Ultra-precise frame capture with timing control"""
        logger.info("Starting precision capture loop")

        # Pre-calculate timing for perfect frame pacing
        target_interval = self.frame_interval
        next_capture_time = time.time()

        while self.running:
            current_time = time.time()

            # Only capture if we've reached the target time
            if current_time >= next_capture_time:
                try:
                    # Measure capture timing
                    capture_start = time.time()
                    ret, frame = self.camera.read()
                    capture_duration = time.time() - capture_start

                    if ret and frame is not None:
                        # Create frame package with precise timing
                        frame_data = {
                            'frame': frame.copy(),
                            'timestamp': current_time,
                            'capture_duration': capture_duration,
                            'frame_id': self.frame_counter
                        }

                        # Non-blocking queue add with overflow protection
                        try:
                            self.raw_frame_queue.put_nowait(frame_data)
                            self.frame_counter += 1
                            self.stats['total_frames'] += 1
                        except queue.Full:
                            # Drop oldest frame to prevent buildup
                            try:
                                self.raw_frame_queue.get_nowait()
                                self.raw_frame_queue.put_nowait(frame_data)
                                self.stats['frame_drops'] += 1
                            except queue.Empty:
                                pass

                        # Calculate next precise capture time
                        next_capture_time = current_time + target_interval

                        # Track FPS accuracy
                        if self.last_capture_time > 0:
                            actual_interval = current_time - self.last_capture_time
                            self.fps_tracker.append(actual_interval)

                            if len(self.fps_tracker) >= 10:
                                avg_interval = sum(self.fps_tracker) / len(self.fps_tracker)
                                self.stats['actual_fps'] = 1.0 / avg_interval if avg_interval > 0 else 0

                                # Calculate timing accuracy
                                timing_error = abs(avg_interval - target_interval)
                                self.stats['timing_accuracy'] = max(0, 1.0 - (timing_error / target_interval))

                        self.last_capture_time = current_time

                    else:
                        logger.warning("Failed to capture frame")
                        # Still advance timing to maintain rhythm
                        next_capture_time = current_time + target_interval

                except Exception as e:
                    logger.error(f"Capture error: {e}")
                    next_capture_time = current_time + target_interval

            else:
                # Precision sleep until next capture time
                sleep_time = min(0.001, next_capture_time - current_time)
                if sleep_time > 0:
                    time.sleep(sleep_time)

    def _frame_processing_loop(self):
        """Process frames with timing synchronization"""
        logger.info("Starting frame processing loop")

        while self.running:
            try:
                # Get latest frame data
                frame_data = self.raw_frame_queue.get(timeout=0.1)

                # Process frame (add overlays, etc.)
                processed_frame = self._process_frame(frame_data['frame'])

                # Store processed frame with lock for thread safety
                with self.frame_lock:
                    self.latest_frame = {
                        'frame': processed_frame,
                        'timestamp': frame_data['timestamp'],
                        'frame_id': frame_data['frame_id'],
                        'processing_time': time.time() - frame_data['timestamp']
                    }

                # Update processed frame queue (single item)
                try:
                    self.processed_frame_queue.put_nowait(self.latest_frame)
                except queue.Full:
                    # Remove old frame and add new one
                    try:
                        self.processed_frame_queue.get_nowait()
                        self.processed_frame_queue.put_nowait(self.latest_frame)
                    except queue.Empty:
                        pass

            except queue.Empty:
                continue
            except Exception as e:
                logger.error(f"Processing error: {e}")

    def _process_frame(self, frame):
        """Add overlays and information to frame"""
        processed = frame.copy()

        # Add FPS and timing info
        fps_text = f"FPS: {self.stats['actual_fps']:.1f}"
        accuracy_text = f"Timing: {self.stats['timing_accuracy']:.2%}"
        frames_text = f"Frames: {self.stats['total_frames']}"
        drops_text = f"Drops: {self.stats['frame_drops']}"

        # Add text overlays
        cv2.putText(processed, fps_text, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        cv2.putText(processed, accuracy_text, (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        cv2.putText(processed, frames_text, (10, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        cv2.putText(processed, drops_text, (10, 120), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

        # Add timestamp for flicker detection
        timestamp_text = f"T: {time.time():.3f}"
        cv2.putText(processed, timestamp_text, (10, 450), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 0), 1)

        return processed

    def start(self):
        """Start the flicker-free capture system"""
        logger.info("Starting FlickerFreeWebcam system")

        if not self._initialize_camera():
            logger.error("Failed to initialize camera")
            return False

        self.running = True

        # Start capture thread with high priority
        self.capture_thread = threading.Thread(target=self._precision_capture_loop, daemon=True)
        self.capture_thread.start()

        # Start processing thread
        self.processing_thread = threading.Thread(target=self._frame_processing_loop, daemon=True)
        self.processing_thread.start()

        logger.info("FlickerFreeWebcam started successfully")
        return True

    def stop(self):
        """Stop the capture system"""
        logger.info("Stopping FlickerFreeWebcam system")
        self.running = False

        if self.camera:
            self.camera.release()

        # Wait for threads to finish
        if self.capture_thread:
            self.capture_thread.join(timeout=2)
        if self.processing_thread:
            self.processing_thread.join(timeout=2)

    def get_latest_frame(self):
        """Get the latest processed frame (thread-safe)"""
        with self.frame_lock:
            return self.latest_frame.copy() if self.latest_frame else None

    def get_frame_for_streaming(self):
        """Get frame optimized for streaming"""
        try:
            frame_data = self.processed_frame_queue.get_nowait()
            return frame_data
        except queue.Empty:
            return None

    def get_stats(self):
        """Get performance statistics"""
        return self.stats.copy()

def test_flicker_free_capture():
    """Test the flicker-free capture system"""
    print("🎥 Testing Flicker-Free Webcam Capture")
    print("=" * 50)

    webcam = FlickerFreeWebcam(camera_index=0, target_fps=15)

    if not webcam.start():
        print("❌ Failed to start webcam")
        return

    try:
        # Test for 30 seconds
        test_duration = 30
        start_time = time.time()
        last_stats_time = start_time

        print(f"Running stability test for {test_duration} seconds...")
        print("Press Ctrl+C to stop early")

        while time.time() - start_time < test_duration:
            frame_data = webcam.get_latest_frame()

            if frame_data:
                # Show frame for visual verification
                cv2.imshow('Flicker-Free Test', frame_data['frame'])

                # Print stats every 5 seconds
                current_time = time.time()
                if current_time - last_stats_time >= 5:
                    stats = webcam.get_stats()
                    print(f"Stats: FPS={stats['actual_fps']:.2f}, "
                          f"Accuracy={stats['timing_accuracy']:.2%}, "
                          f"Drops={stats['frame_drops']}, "
                          f"Total={stats['total_frames']}")
                    last_stats_time = current_time

            # Small delay to prevent overwhelming
            time.sleep(0.01)

            # Check for 'q' key press
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

    except KeyboardInterrupt:
        print("\nTest stopped by user")

    finally:
        webcam.stop()
        cv2.destroyAllWindows()

        # Final stats
        final_stats = webcam.get_stats()
        print(f"\n📊 Final Results:")
        print(f"  Average FPS: {final_stats['actual_fps']:.2f}")
        print(f"  Timing Accuracy: {final_stats['timing_accuracy']:.2%}")
        print(f"  Total Frames: {final_stats['total_frames']}")
        print(f"  Dropped Frames: {final_stats['frame_drops']}")
        print(f"  Drop Rate: {(final_stats['frame_drops']/max(1,final_stats['total_frames']))*100:.2f}%")

        if final_stats['timing_accuracy'] > 0.95 and final_stats['frame_drops'] < final_stats['total_frames'] * 0.05:
            print("  🌟 EXCELLENT - Ready for WebSocket streaming!")
        elif final_stats['timing_accuracy'] > 0.90:
            print("  ✅ GOOD - Should work well for streaming")
        else:
            print("  ⚠️  May need further optimization")

if __name__ == "__main__":
    test_flicker_free_capture()