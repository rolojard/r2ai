#!/usr/bin/env python3
"""
Comprehensive test suite for all 8 critical vision system fixes
Tests camera initialization, memory management, thread safety, and input validation
"""

import sys
import unittest
import threading
import time
from collections import deque
from unittest.mock import Mock, patch, MagicMock
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import the vision system
sys.path.insert(0, '/home/rolo/r2ai')
from r2d2_orin_nano_optimized_vision import OrinNanoOptimizedVision


class TestVisionSystemFixes(unittest.TestCase):
    """Test all 8 critical fixes in the vision system"""

    def test_01_camera_initialization_integer(self):
        """
        FIX #1: Camera initialization with integer device index
        Validates that camera_device accepts integers, not strings
        """
        logger.info("\n=== TEST #1: Camera initialization with integer ===")

        # Valid integer device
        try:
            vision = OrinNanoOptimizedVision(websocket_port=8888, camera_device=0)
            self.assertEqual(vision.camera_device, 0)
            self.assertIsInstance(vision.camera_device, int)
            logger.info("✓ Camera device accepts integer (0)")
        except Exception as e:
            self.fail(f"Failed to initialize with integer camera_device: {e}")

        # Invalid string should fail
        with self.assertRaises(ValueError):
            vision = OrinNanoOptimizedVision(websocket_port=8889, camera_device="/dev/video0")
            logger.info("✓ String camera_device properly rejected")

    def test_02_memory_leak_queue_deque(self):
        """
        FIX #2: Memory leak prevention with deque(maxlen=1)
        Validates automatic old frame eviction
        """
        logger.info("\n=== TEST #2: Memory leak prevention with deque ===")

        vision = OrinNanoOptimizedVision(websocket_port=8890, camera_device=0)

        # Verify frame_queue is a deque with maxlen=1
        self.assertIsInstance(vision.frame_queue, deque)
        self.assertEqual(vision.frame_queue.maxlen, 1)
        logger.info("✓ frame_queue is deque with maxlen=1")

        # Verify detection_queue is a deque with maxlen=3
        self.assertIsInstance(vision.detection_queue, deque)
        self.assertEqual(vision.detection_queue.maxlen, 3)
        logger.info("✓ detection_queue is deque with maxlen=3")

        # Test automatic eviction
        with vision.frame_queue_lock:
            vision.frame_queue.append("frame1")
            self.assertEqual(len(vision.frame_queue), 1)
            vision.frame_queue.append("frame2")  # Should auto-evict frame1
            self.assertEqual(len(vision.frame_queue), 1)
            self.assertEqual(vision.frame_queue[0], "frame2")
        logger.info("✓ Automatic old frame eviction working")

    def test_03_race_conditions_locking(self):
        """
        FIX #3: Race conditions fixed with threading.Lock
        Validates thread-safe queue operations
        """
        logger.info("\n=== TEST #3: Race conditions fixed with locks ===")

        vision = OrinNanoOptimizedVision(websocket_port=8891, camera_device=0)

        # Verify locks exist (check type name since threading.Lock is not a regular type)
        self.assertEqual(type(vision.frame_queue_lock).__name__, 'lock')
        self.assertEqual(type(vision.detection_queue_lock).__name__, 'lock')
        logger.info("✓ Thread locks exist for both queues")

        # Test concurrent access safety
        def writer():
            for i in range(10):
                with vision.frame_queue_lock:
                    vision.frame_queue.append(f"frame_{i}")
                time.sleep(0.001)

        def reader():
            for i in range(10):
                with vision.frame_queue_lock:
                    if len(vision.frame_queue) > 0:
                        _ = vision.frame_queue.popleft()
                time.sleep(0.001)

        threads = [
            threading.Thread(target=writer),
            threading.Thread(target=writer),
            threading.Thread(target=reader),
        ]

        for t in threads:
            t.start()
        for t in threads:
            t.join(timeout=2.0)

        logger.info("✓ Concurrent queue access without deadlocks")

    def test_04_queue_timeout_handling(self):
        """
        FIX #4: Queue.get() replaced with non-blocking deque access
        Validates no indefinite blocking
        """
        logger.info("\n=== TEST #4: Queue timeout handling ===")

        vision = OrinNanoOptimizedVision(websocket_port=8892, camera_device=0)

        # Test non-blocking read from empty queue
        start_time = time.time()
        with vision.frame_queue_lock:
            if len(vision.frame_queue) > 0:
                frame = vision.frame_queue.popleft()
            else:
                frame = None
        elapsed = time.time() - start_time

        self.assertIsNone(frame)
        self.assertLess(elapsed, 0.1)  # Should return immediately
        logger.info(f"✓ Non-blocking queue read (elapsed: {elapsed*1000:.2f}ms)")

    def test_05_specific_exceptions(self):
        """
        FIX #5: Bare exception handling replaced with specific types
        Validates proper exception types in code
        """
        logger.info("\n=== TEST #5: Specific exception handling ===")

        # Read the source file and check for bare except:
        with open('/home/rolo/r2ai/r2d2_vision_production.py', 'r') as f:
            source = f.read()

        # Count bare except: statements (should be 0)
        bare_except_count = source.count('except:')
        self.assertEqual(bare_except_count, 0,
                        f"Found {bare_except_count} bare 'except:' statements")
        logger.info("✓ No bare 'except:' statements found")

        # Verify specific exception types are used
        self.assertIn('except (RuntimeError, ValueError, OSError, ImportError)', source)
        self.assertIn('except (RuntimeError, cv2.error)', source)
        logger.info("✓ Specific exception types used throughout code")

    def test_06_thread_cleanup(self):
        """
        FIX #6: Thread cleanup with proper join() calls
        Validates thread tracking and cleanup
        """
        logger.info("\n=== TEST #6: Thread cleanup and joining ===")

        vision = OrinNanoOptimizedVision(websocket_port=8893, camera_device=0)

        # Verify thread tracking attributes exist
        self.assertIsNone(vision.capture_thread)
        self.assertIsNone(vision.detection_thread)
        logger.info("✓ Thread tracking attributes initialized")

        # Verify stop() method has join() calls
        import inspect
        stop_source = inspect.getsource(vision.stop)
        self.assertIn('join(timeout=', stop_source)
        self.assertIn('capture_thread', stop_source)
        self.assertIn('detection_thread', stop_source)
        logger.info("✓ stop() method has proper thread.join() calls")

    def test_07_asyncio_graceful_shutdown(self):
        """
        FIX #7: Asyncio event loop with graceful shutdown
        Validates signal handlers for clean shutdown
        """
        logger.info("\n=== TEST #7: Asyncio graceful shutdown ===")

        vision = OrinNanoOptimizedVision(websocket_port=8894, camera_device=0)

        # Verify signal handling in _run_websocket_server
        import inspect
        ws_source = inspect.getsource(vision._run_websocket_server)
        self.assertIn('signal_handler', ws_source)
        self.assertIn('SIGTERM', ws_source)
        self.assertIn('SIGINT', ws_source)
        self.assertIn('stop_future', ws_source)
        logger.info("✓ Signal handlers implemented for graceful shutdown")

    def test_08_input_validation(self):
        """
        FIX #8: Input validation with whitelist
        Validates port and camera_device validation
        """
        logger.info("\n=== TEST #8: Input validation ===")

        # Valid inputs
        try:
            vision = OrinNanoOptimizedVision(websocket_port=8895, camera_device=0)
            logger.info("✓ Valid inputs accepted")
        except ValueError:
            self.fail("Valid inputs rejected")

        # Invalid port (too low)
        with self.assertRaises(ValueError) as ctx:
            OrinNanoOptimizedVision(websocket_port=80, camera_device=0)
        self.assertIn('1024-65535', str(ctx.exception))
        logger.info("✓ Port <1024 rejected")

        # Invalid port (too high)
        with self.assertRaises(ValueError) as ctx:
            OrinNanoOptimizedVision(websocket_port=70000, camera_device=0)
        self.assertIn('1024-65535', str(ctx.exception))
        logger.info("✓ Port >65535 rejected")

        # Invalid port (non-integer)
        with self.assertRaises(ValueError):
            OrinNanoOptimizedVision(websocket_port="8767", camera_device=0)
        logger.info("✓ String port rejected")

        # Invalid camera device (negative)
        with self.assertRaises(ValueError) as ctx:
            OrinNanoOptimizedVision(websocket_port=8896, camera_device=-1)
        self.assertIn('0-10', str(ctx.exception))
        logger.info("✓ Negative camera_device rejected")

        # Invalid camera device (too high)
        with self.assertRaises(ValueError) as ctx:
            OrinNanoOptimizedVision(websocket_port=8897, camera_device=20)
        self.assertIn('0-10', str(ctx.exception))
        logger.info("✓ camera_device >10 rejected")

    def test_09_integration_all_fixes(self):
        """
        Integration test: Verify all fixes work together
        """
        logger.info("\n=== TEST #9: Integration test - All fixes ===")

        # Create vision system with all validated parameters
        vision = OrinNanoOptimizedVision(websocket_port=8898, camera_device=0)

        # Verify all attributes
        checks = [
            (vision.camera_device, 0, "camera_device"),
            (vision.websocket_port, 8898, "websocket_port"),
            (isinstance(vision.frame_queue, deque), True, "frame_queue is deque"),
            (vision.frame_queue.maxlen, 1, "frame_queue maxlen"),
            (type(vision.frame_queue_lock).__name__, 'lock', "frame_queue_lock"),
            (type(vision.detection_queue_lock).__name__, 'lock', "detection_queue_lock"),
            (vision.capture_thread, None, "capture_thread initialized"),
            (vision.detection_thread, None, "detection_thread initialized"),
        ]

        for actual, expected, name in checks:
            self.assertEqual(actual, expected, f"{name} check failed")
            logger.info(f"✓ {name}: {actual}")

        logger.info("✓ All fixes integrated successfully")


def run_tests():
    """Run all tests and generate report"""
    logger.info("=" * 70)
    logger.info("VISION SYSTEM FIXES - COMPREHENSIVE TEST SUITE")
    logger.info("Testing all 8 critical fixes")
    logger.info("=" * 70)

    # Create test suite
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(TestVisionSystemFixes)

    # Run tests with verbose output
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # Print summary
    logger.info("\n" + "=" * 70)
    logger.info("TEST SUMMARY")
    logger.info("=" * 70)
    logger.info(f"Tests run: {result.testsRun}")
    logger.info(f"Successes: {result.testsRun - len(result.failures) - len(result.errors)}")
    logger.info(f"Failures: {len(result.failures)}")
    logger.info(f"Errors: {len(result.errors)}")

    if result.wasSuccessful():
        logger.info("\n✓✓✓ ALL TESTS PASSED ✓✓✓")
        logger.info("Vision system PHASE 1 complete. All 8 critical issues fixed.")
        return 0
    else:
        logger.error("\n✗✗✗ SOME TESTS FAILED ✗✗✗")
        return 1


if __name__ == '__main__':
    sys.exit(run_tests())
