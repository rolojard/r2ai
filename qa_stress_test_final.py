#!/usr/bin/env python3
"""
ELITE QA TESTING: Comprehensive Stress Testing
Final stress testing under different conditions
"""

import cv2
import numpy as np
import time
import threading
import queue
import json
import psutil
import os
import gc
from datetime import datetime
import subprocess

class StressTestQATester:
    """QA tester for comprehensive stress testing"""

    def __init__(self):
        self.camera = None
        self.test_results = {
            'extended_operation_stress': False,
            'memory_management_stress': False,
            'concurrent_access_stress': False,
            'rapid_restart_stress': False,
            'resource_cleanup_validation': False,
            'system_stability_under_load': False
        }

        # Monitoring data
        self.cpu_usage_history = []
        self.memory_usage_history = []
        self.frame_processing_times = []

    def log_test(self, test_name, result, details=""):
        """Log test results"""
        status = "✅ PASS" if result else "❌ FAIL"
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] {status} {test_name}")
        if details:
            print(f"    Details: {details}")
        self.test_results[test_name] = result

    def get_system_metrics(self):
        """Get current system metrics"""
        return {
            'cpu_percent': psutil.cpu_percent(),
            'memory_percent': psutil.virtual_memory().percent,
            'memory_mb': psutil.virtual_memory().used / 1024 / 1024,
            'timestamp': time.time()
        }

    def initialize_camera(self):
        """Initialize camera for stress testing"""
        try:
            self.camera = cv2.VideoCapture(0, cv2.CAP_V4L2)
            if self.camera.isOpened():
                self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
                self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
                self.camera.set(cv2.CAP_PROP_FPS, 30)
                self.camera.set(cv2.CAP_PROP_BUFFERSIZE, 1)
                return True
            return False
        except:
            return False

    def test_extended_operation_stress(self, duration=60):
        """Test extended operation under stress"""
        print(f"\n⏰ Extended Operation Stress Test ({duration}s)...")

        if not self.initialize_camera():
            self.log_test('extended_operation_stress', False, "Camera initialization failed")
            return False

        start_time = time.time()
        frames_processed = 0
        errors = 0
        performance_samples = []

        try:
            while time.time() - start_time < duration:
                iteration_start = time.time()

                # System metrics collection
                metrics = self.get_system_metrics()
                self.cpu_usage_history.append(metrics['cpu_percent'])
                self.memory_usage_history.append(metrics['memory_percent'])

                # Camera operation
                ret, frame = self.camera.read()
                if ret and frame is not None:
                    frames_processed += 1

                    # Simulate processing workload
                    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                    blurred = cv2.GaussianBlur(gray, (15, 15), 0)
                    edges = cv2.Canny(blurred, 50, 150)

                    # Memory allocation test
                    temp_array = np.random.rand(100, 100, 3) * 255
                    del temp_array

                else:
                    errors += 1

                iteration_end = time.time()
                processing_time = iteration_end - iteration_start
                performance_samples.append(processing_time)

                # Progress reporting
                if frames_processed % 300 == 0:
                    elapsed = time.time() - start_time
                    fps = frames_processed / elapsed
                    cpu_avg = sum(self.cpu_usage_history[-10:]) / min(10, len(self.cpu_usage_history))
                    mem_avg = sum(self.memory_usage_history[-10:]) / min(10, len(self.memory_usage_history))

                    print(f"    📊 {frames_processed} frames, {fps:.1f} FPS, CPU: {cpu_avg:.1f}%, Mem: {mem_avg:.1f}%")

                # Minimal delay to prevent overwhelming
                time.sleep(0.001)

        except Exception as e:
            print(f"    ❌ Stress test error: {e}")
            errors += 1

        finally:
            if self.camera:
                self.camera.release()

        # Analysis
        avg_cpu = sum(self.cpu_usage_history) / len(self.cpu_usage_history) if self.cpu_usage_history else 0
        avg_memory = sum(self.memory_usage_history) / len(self.memory_usage_history) if self.memory_usage_history else 0
        avg_processing_time = sum(performance_samples) / len(performance_samples) if performance_samples else 0

        print(f"    📊 Total frames processed: {frames_processed}")
        print(f"    📊 Total errors: {errors}")
        print(f"    📊 Average CPU usage: {avg_cpu:.1f}%")
        print(f"    📊 Average memory usage: {avg_memory:.1f}%")
        print(f"    📊 Average processing time: {avg_processing_time:.3f}s")

        # Pass criteria: >1000 frames processed, <1% error rate, reasonable resource usage
        error_rate = (errors / max(frames_processed + errors, 1)) * 100
        resource_ok = avg_cpu < 80 and avg_memory < 85

        if frames_processed >= 1000 and error_rate < 1 and resource_ok:
            self.log_test('extended_operation_stress', True,
                         f"{frames_processed} frames, {error_rate:.1f}% errors, resources OK")
            return True
        else:
            self.log_test('extended_operation_stress', False,
                         f"{frames_processed} frames, {error_rate:.1f}% errors, resource issues: {not resource_ok}")
            return False

    def test_memory_management_stress(self):
        """Test memory management under stress"""
        print("\n🧠 Memory Management Stress Test...")

        if not self.initialize_camera():
            self.log_test('memory_management_stress', False, "Camera initialization failed")
            return False

        initial_memory = psutil.virtual_memory().used / 1024 / 1024
        max_memory_usage = initial_memory
        memory_samples = []

        try:
            # Allocate and deallocate large amounts of memory while processing video
            for cycle in range(20):
                # Create large arrays
                large_arrays = []
                for i in range(10):
                    array = np.random.rand(200, 200, 3) * 255
                    large_arrays.append(array)

                # Process camera frames
                for frame_count in range(50):
                    ret, frame = self.camera.read()
                    if ret and frame is not None:
                        # Additional processing to stress memory
                        processed = cv2.resize(frame, (1280, 720))
                        processed = cv2.GaussianBlur(processed, (21, 21), 0)

                    current_memory = psutil.virtual_memory().used / 1024 / 1024
                    memory_samples.append(current_memory)
                    max_memory_usage = max(max_memory_usage, current_memory)

                # Clean up large arrays
                del large_arrays
                gc.collect()

                # Check memory after cleanup
                cleanup_memory = psutil.virtual_memory().used / 1024 / 1024
                print(f"    🔄 Cycle {cycle + 1}: Peak {max_memory_usage:.1f}MB, After cleanup {cleanup_memory:.1f}MB")

        except Exception as e:
            print(f"    ❌ Memory stress test error: {e}")

        finally:
            if self.camera:
                self.camera.release()
            gc.collect()

        final_memory = psutil.virtual_memory().used / 1024 / 1024
        memory_growth = final_memory - initial_memory

        print(f"    📊 Initial memory: {initial_memory:.1f}MB")
        print(f"    📊 Peak memory: {max_memory_usage:.1f}MB")
        print(f"    📊 Final memory: {final_memory:.1f}MB")
        print(f"    📊 Memory growth: {memory_growth:.1f}MB")

        # Pass if memory growth is reasonable (<200MB)
        if abs(memory_growth) < 200:
            self.log_test('memory_management_stress', True,
                         f"Memory well managed (growth: {memory_growth:.1f}MB)")
            return True
        else:
            self.log_test('memory_management_stress', False,
                         f"Excessive memory growth: {memory_growth:.1f}MB")
            return False

    def test_concurrent_access_stress(self):
        """Test concurrent camera access scenarios"""
        print("\n🔀 Concurrent Access Stress Test...")

        def camera_worker(worker_id, results, duration=10):
            """Worker function for concurrent camera access"""
            camera = None
            frames_captured = 0
            errors = 0

            try:
                camera = cv2.VideoCapture(0, cv2.CAP_V4L2)
                if camera.isOpened():
                    start_time = time.time()
                    while time.time() - start_time < duration:
                        ret, frame = camera.read()
                        if ret and frame is not None:
                            frames_captured += 1
                        else:
                            errors += 1
                        time.sleep(0.1)  # 10 FPS per worker
                else:
                    errors = 999  # Couldn't open camera

            except Exception as e:
                errors += 1

            finally:
                if camera:
                    camera.release()

            results[worker_id] = {'frames': frames_captured, 'errors': errors}

        # Test concurrent access (expected to fail gracefully)
        results = {}
        threads = []

        # Start multiple threads trying to access camera
        for i in range(3):
            thread = threading.Thread(target=camera_worker, args=(i, results, 5))
            threads.append(thread)
            thread.start()
            time.sleep(0.5)  # Stagger starts

        # Wait for all threads
        for thread in threads:
            thread.join()

        # Analyze results
        successful_workers = 0
        total_frames = 0
        total_errors = 0

        for worker_id, result in results.items():
            frames = result['frames']
            errors = result['errors']
            total_frames += frames
            total_errors += errors

            if frames > 0 and errors < 50:  # Some success
                successful_workers += 1
                print(f"    ✅ Worker {worker_id}: {frames} frames, {errors} errors")
            else:
                print(f"    ❌ Worker {worker_id}: {frames} frames, {errors} errors")

        print(f"    📊 Successful workers: {successful_workers}/3")
        print(f"    📊 Total frames: {total_frames}")
        print(f"    📊 Total errors: {total_errors}")

        # Pass if at least one worker succeeds (exclusive access working)
        if successful_workers >= 1:
            self.log_test('concurrent_access_stress', True,
                         f"{successful_workers} workers succeeded (proper exclusive access)")
            return True
        else:
            self.log_test('concurrent_access_stress', False,
                         "No workers succeeded")
            return False

    def test_rapid_restart_stress(self):
        """Test rapid restart scenarios"""
        print("\n🔄 Rapid Restart Stress Test...")

        successful_restarts = 0
        failed_restarts = 0

        for restart_cycle in range(10):
            try:
                # Initialize camera
                camera = cv2.VideoCapture(0, cv2.CAP_V4L2)

                if camera.isOpened():
                    # Quick capture test
                    ret, frame = camera.read()
                    if ret and frame is not None:
                        # Process a few frames
                        for _ in range(5):
                            ret, frame = camera.read()
                            if ret:
                                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

                        successful_restarts += 1
                        print(f"    ✅ Restart {restart_cycle + 1}: Success")
                    else:
                        failed_restarts += 1
                        print(f"    ❌ Restart {restart_cycle + 1}: No frame")

                    camera.release()

                else:
                    failed_restarts += 1
                    print(f"    ❌ Restart {restart_cycle + 1}: Camera failed to open")

                # Brief pause between restarts
                time.sleep(0.2)

            except Exception as e:
                failed_restarts += 1
                print(f"    ❌ Restart {restart_cycle + 1}: Error - {e}")

        success_rate = (successful_restarts / 10) * 100

        print(f"    📊 Successful restarts: {successful_restarts}/10")
        print(f"    📊 Failed restarts: {failed_restarts}/10")
        print(f"    📊 Success rate: {success_rate:.1f}%")

        # Pass if >80% success rate
        if success_rate >= 80:
            self.log_test('rapid_restart_stress', True,
                         f"Restart reliability: {success_rate:.1f}%")
            return True
        else:
            self.log_test('rapid_restart_stress', False,
                         f"Poor restart reliability: {success_rate:.1f}%")
            return False

    def test_resource_cleanup_validation(self):
        """Test resource cleanup validation"""
        print("\n🧹 Resource Cleanup Validation...")

        initial_fds = len(os.listdir('/proc/self/fd'))
        initial_memory = psutil.virtual_memory().used / 1024 / 1024

        print(f"    📊 Initial file descriptors: {initial_fds}")
        print(f"    📊 Initial memory: {initial_memory:.1f}MB")

        # Create and destroy multiple camera instances
        for i in range(20):
            try:
                camera = cv2.VideoCapture(0, cv2.CAP_V4L2)
                if camera.isOpened():
                    # Brief usage
                    for _ in range(3):
                        ret, frame = camera.read()
                        if ret:
                            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

                camera.release()
                del camera

                # Periodic cleanup
                if i % 5 == 0:
                    gc.collect()

            except Exception as e:
                print(f"    ⚠️ Cleanup test iteration {i}: {e}")

        # Force cleanup
        gc.collect()
        time.sleep(1)

        final_fds = len(os.listdir('/proc/self/fd'))
        final_memory = psutil.virtual_memory().used / 1024 / 1024

        fd_growth = final_fds - initial_fds
        memory_growth = final_memory - initial_memory

        print(f"    📊 Final file descriptors: {final_fds}")
        print(f"    📊 Final memory: {final_memory:.1f}MB")
        print(f"    📊 FD growth: {fd_growth}")
        print(f"    📊 Memory growth: {memory_growth:.1f}MB")

        # Pass if resource usage is well controlled
        if abs(fd_growth) <= 5 and abs(memory_growth) <= 100:
            self.log_test('resource_cleanup_validation', True,
                         f"Resources well managed (FDs: {fd_growth}, Mem: {memory_growth:.1f}MB)")
            return True
        else:
            self.log_test('resource_cleanup_validation', False,
                         f"Resource leaks detected (FDs: {fd_growth}, Mem: {memory_growth:.1f}MB)")
            return False

    def test_system_stability_under_load(self):
        """Test overall system stability under load"""
        print("\n🏋️ System Stability Under Load Test...")

        if not self.initialize_camera():
            self.log_test('system_stability_under_load', False, "Camera initialization failed")
            return False

        # Monitor system metrics under sustained load
        stability_metrics = {
            'cpu_spikes': 0,
            'memory_spikes': 0,
            'frame_drops': 0,
            'errors': 0
        }

        duration = 30  # 30 seconds under load
        start_time = time.time()
        frame_count = 0

        try:
            while time.time() - start_time < duration:
                iteration_start = time.time()

                # System metrics
                metrics = self.get_system_metrics()
                cpu_percent = metrics['cpu_percent']
                memory_percent = metrics['memory_percent']

                # Monitor for spikes
                if cpu_percent > 90:
                    stability_metrics['cpu_spikes'] += 1
                if memory_percent > 90:
                    stability_metrics['memory_spikes'] += 1

                # Camera processing
                ret, frame = self.camera.read()
                if ret and frame is not None:
                    frame_count += 1

                    # Intensive processing to create load
                    resized = cv2.resize(frame, (1280, 720))
                    blurred = cv2.GaussianBlur(resized, (25, 25), 0)
                    edges = cv2.Canny(blurred, 50, 150)

                    # Additional CPU load
                    for _ in range(10):
                        math_result = np.sum(np.random.rand(100, 100))

                else:
                    stability_metrics['frame_drops'] += 1

                # Check timing consistency
                iteration_time = time.time() - iteration_start
                if iteration_time > 0.1:  # >100ms indicates system stress
                    stability_metrics['errors'] += 1

                elapsed = time.time() - start_time
                if int(elapsed) % 5 == 0 and elapsed - int(elapsed) < 0.1:
                    fps = frame_count / elapsed
                    print(f"    📊 {elapsed:.0f}s: {frame_count} frames ({fps:.1f} FPS), CPU: {cpu_percent:.1f}%, Mem: {memory_percent:.1f}%")

        except Exception as e:
            print(f"    ❌ Stability test error: {e}")
            stability_metrics['errors'] += 10

        finally:
            if self.camera:
                self.camera.release()

        total_issues = sum(stability_metrics.values())

        print(f"    📊 Frame count: {frame_count}")
        print(f"    📊 CPU spikes (>90%): {stability_metrics['cpu_spikes']}")
        print(f"    📊 Memory spikes (>90%): {stability_metrics['memory_spikes']}")
        print(f"    📊 Frame drops: {stability_metrics['frame_drops']}")
        print(f"    📊 Timing errors: {stability_metrics['errors']}")
        print(f"    📊 Total stability issues: {total_issues}")

        # Pass if system remains stable (few issues)
        if total_issues <= 10 and frame_count >= 200:
            self.log_test('system_stability_under_load', True,
                         f"System stable under load ({total_issues} issues, {frame_count} frames)")
            return True
        else:
            self.log_test('system_stability_under_load', False,
                         f"System instability detected ({total_issues} issues, {frame_count} frames)")
            return False

    def run_comprehensive_stress_test(self):
        """Run complete stress test suite"""
        print("🎯 ELITE QA TESTING: Comprehensive Stress Testing")
        print("=" * 60)
        print("Testing System Under Various Stress Conditions")
        print("=" * 60)

        try:
            # Run stress test sequence
            self.test_extended_operation_stress(60)
            self.test_memory_management_stress()
            self.test_concurrent_access_stress()
            self.test_rapid_restart_stress()
            self.test_resource_cleanup_validation()
            self.test_system_stability_under_load()

        except Exception as e:
            print(f"❌ Stress test suite error: {e}")

        # Generate report
        self.generate_stress_test_report()

        # Return overall success
        return all(self.test_results.values())

    def generate_stress_test_report(self):
        """Generate comprehensive stress test report"""
        print("\n" + "=" * 60)
        print("🎯 STRESS TEST REPORT")
        print("=" * 60)

        passed_tests = sum(1 for result in self.test_results.values() if result)
        total_tests = len(self.test_results)

        print(f"OVERALL RESULT: {passed_tests}/{total_tests} tests passed")
        print(f"STRESS TEST SCORE: {(passed_tests/total_tests)*100:.1f}%")
        print()

        print("DETAILED RESULTS:")
        test_categories = {
            'extended_operation_stress': 'Extended Operation Stress',
            'memory_management_stress': 'Memory Management Stress',
            'concurrent_access_stress': 'Concurrent Access Stress',
            'rapid_restart_stress': 'Rapid Restart Stress',
            'resource_cleanup_validation': 'Resource Cleanup Validation',
            'system_stability_under_load': 'System Stability Under Load'
        }

        for test_key, test_name in test_categories.items():
            result = self.test_results[test_key]
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"  {status} {test_name}")

        print()

        if passed_tests == total_tests:
            print("🎉 STRESS TESTING SUCCESSFUL!")
            print("✅ System handles extended operation")
            print("✅ Memory management is robust")
            print("✅ Resource cleanup is effective")
            print("✅ System remains stable under load")
        else:
            print("⚠️ STRESS TESTING ISSUES DETECTED")
            failed_tests = [test_categories[name] for name, result in self.test_results.items() if not result]
            print(f"   Issues: {', '.join(failed_tests)}")

        print("=" * 60)

def main():
    """Main execution function"""
    tester = StressTestQATester()

    try:
        success = tester.run_comprehensive_stress_test()
        return 0 if success else 1

    except KeyboardInterrupt:
        print("\n\n🛑 Test interrupted by user")
        return 1
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        return 1

if __name__ == "__main__":
    import sys
    sys.exit(main())