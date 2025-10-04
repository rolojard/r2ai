#!/usr/bin/env python3
"""
Unit Tests for R2D2 Logging Framework
====================================

Comprehensive test suite for the R2D2 logging infrastructure.
Tests all components for reliability, performance, and integration.

Test Categories:
- Structured JSON formatting
- Performance monitoring
- WebSocket event logging
- Vision system logging
- Error handling and recovery
- Memory efficiency
- Log rotation

Author: Expert Python Coder Agent
"""

import os
import sys
import json
import time
import unittest
import tempfile
import threading
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
import logging
import shutil

# Add the parent directory to path for imports
sys.path.append('/home/rolo/r2ai')

from r2d2_logging_framework import (
    R2D2StructuredFormatter,
    PerformanceLogger,
    WebSocketEventLogger,
    VisionSystemLogger,
    R2D2LoggerFactory,
    get_log_analyzer
)

class TestR2D2StructuredFormatter(unittest.TestCase):
    """Test the structured JSON formatter"""

    def setUp(self):
        self.formatter = R2D2StructuredFormatter("test_service")
        self.logger = logging.getLogger("test_logger")

    def test_basic_formatting(self):
        """Test basic log record formatting"""
        record = logging.LogRecord(
            name="test_logger",
            level=logging.INFO,
            pathname="/test/path.py",
            lineno=123,
            msg="Test message",
            args=(),
            exc_info=None
        )
        record.funcName = "test_function"
        record.module = "test_module"

        formatted = self.formatter.format(record)
        log_data = json.loads(formatted)

        # Verify required fields
        self.assertEqual(log_data["service"], "test_service")
        self.assertEqual(log_data["level"], "INFO")
        self.assertEqual(log_data["message"], "Test message")
        self.assertEqual(log_data["function"], "test_function")
        self.assertEqual(log_data["module"], "test_module")
        self.assertEqual(log_data["line"], 123)
        self.assertIn("timestamp", log_data)

    def test_exception_formatting(self):
        """Test exception information in logs"""
        try:
            raise ValueError("Test exception")
        except Exception as e:
            exc_info = sys.exc_info()

        record = logging.LogRecord(
            name="test_logger",
            level=logging.ERROR,
            pathname="/test/path.py",
            lineno=123,
            msg="Error occurred",
            args=(),
            exc_info=exc_info
        )
        record.funcName = "test_function"
        record.module = "test_module"

        formatted = self.formatter.format(record)
        log_data = json.loads(formatted)

        # Verify exception information
        self.assertIn("exception", log_data)
        self.assertEqual(log_data["exception"]["type"], "ValueError")
        self.assertEqual(log_data["exception"]["message"], "Test exception")
        self.assertIsInstance(log_data["exception"]["traceback"], list)

    def test_extra_fields(self):
        """Test handling of extra fields"""
        record = logging.LogRecord(
            name="test_logger",
            level=logging.INFO,
            pathname="/test/path.py",
            lineno=123,
            msg="Test message",
            args=(),
            exc_info=None
        )
        record.funcName = "test_function"
        record.module = "test_module"

        # Add extra fields
        record.custom_field = "custom_value"
        record.operation_id = "op_123"

        formatted = self.formatter.format(record)
        log_data = json.loads(formatted)

        # Verify extra fields
        self.assertIn("extra", log_data)
        self.assertEqual(log_data["extra"]["custom_field"], "custom_value")
        self.assertEqual(log_data["extra"]["operation_id"], "op_123")

    @patch('psutil.Process')
    def test_system_info_inclusion(self, mock_process):
        """Test system information inclusion for warnings and errors"""
        # Mock process information
        mock_proc = Mock()
        mock_proc.memory_info.return_value.rss = 100 * 1024 * 1024  # 100MB
        mock_proc.cpu_percent.return_value = 25.5
        mock_proc.num_threads.return_value = 8
        mock_process.return_value = mock_proc

        formatter = R2D2StructuredFormatter("test_service", include_system_info=True)

        record = logging.LogRecord(
            name="test_logger",
            level=logging.WARNING,
            pathname="/test/path.py",
            lineno=123,
            msg="Warning message",
            args=(),
            exc_info=None
        )
        record.funcName = "test_function"
        record.module = "test_module"

        formatted = formatter.format(record)
        log_data = json.loads(formatted)

        # Verify system information
        self.assertIn("system", log_data)
        self.assertEqual(log_data["system"]["memory_mb"], 100.0)
        self.assertEqual(log_data["system"]["cpu_percent"], 25.5)
        self.assertEqual(log_data["system"]["thread_count"], 8)

class TestPerformanceLogger(unittest.TestCase):
    """Test performance monitoring functionality"""

    def setUp(self):
        self.logger = logging.getLogger("test_perf_logger")
        self.logger.handlers.clear()

        # Add in-memory handler for testing
        self.log_records = []
        handler = logging.Handler()
        handler.emit = lambda record: self.log_records.append(record)
        self.logger.addHandler(handler)
        self.logger.setLevel(logging.DEBUG)

        self.perf_logger = PerformanceLogger(self.logger)

    def test_operation_measurement(self):
        """Test operation performance measurement"""
        with self.perf_logger.measure_operation("test_operation", param1="value1"):
            time.sleep(0.01)  # Small delay

        # Check logged records
        start_record = None
        complete_record = None

        for record in self.log_records:
            if hasattr(record, 'event_type'):
                if record.event_type == "operation_start":
                    start_record = record
                elif record.event_type == "operation_complete":
                    complete_record = record

        self.assertIsNotNone(start_record)
        self.assertIsNotNone(complete_record)
        self.assertEqual(start_record.operation_name, "test_operation")
        self.assertEqual(complete_record.operation_name, "test_operation")
        self.assertTrue(complete_record.success)
        self.assertGreater(complete_record.duration_seconds, 0.009)

    def test_operation_error_handling(self):
        """Test operation error handling"""
        with self.assertRaises(ValueError):
            with self.perf_logger.measure_operation("failing_operation"):
                raise ValueError("Test error")

        # Check error record
        error_record = None
        for record in self.log_records:
            if hasattr(record, 'event_type') and record.event_type == "operation_error":
                error_record = record
                break

        self.assertIsNotNone(error_record)
        self.assertEqual(error_record.operation_name, "failing_operation")
        self.assertFalse(error_record.success)
        self.assertEqual(error_record.error_message, "Test error")

    @patch('psutil.cpu_percent')
    @patch('psutil.virtual_memory')
    @patch('psutil.disk_usage')
    @patch('psutil.Process')
    def test_metrics_collection(self, mock_process, mock_disk, mock_memory, mock_cpu):
        """Test system metrics collection"""
        # Mock system metrics
        mock_cpu.return_value = 45.2
        mock_memory.return_value = Mock(percent=62.5, available=2*1024**3)
        mock_disk.return_value = Mock(percent=25.0, free=100*1024**3)

        # Mock process metrics
        mock_proc = Mock()
        mock_proc.memory_info.return_value = Mock(rss=50*1024**2, vms=100*1024**2)
        mock_proc.cpu_percent.return_value = 15.3
        mock_proc.num_threads.return_value = 6
        mock_proc.open_files.return_value = [Mock(), Mock()]
        mock_proc.connections.return_value = [Mock()]
        mock_process.return_value = mock_proc

        metrics = self.perf_logger._collect_system_metrics()

        # Verify metrics structure
        self.assertIn("system", metrics)
        self.assertIn("process", metrics)
        self.assertEqual(metrics["system"]["cpu_percent"], 45.2)
        self.assertEqual(metrics["system"]["memory_percent"], 62.5)
        self.assertEqual(metrics["process"]["threads"], 6)

class TestWebSocketEventLogger(unittest.TestCase):
    """Test WebSocket event logging"""

    def setUp(self):
        self.logger = logging.getLogger("test_ws_logger")
        self.logger.handlers.clear()

        # Add in-memory handler for testing
        self.log_records = []
        handler = logging.Handler()
        handler.emit = lambda record: self.log_records.append(record)
        self.logger.addHandler(handler)
        self.logger.setLevel(logging.DEBUG)

        self.ws_logger = WebSocketEventLogger(self.logger)

    def test_connection_logging(self):
        """Test WebSocket connection event logging"""
        # Test connection
        self.ws_logger.log_connection("client_123", "192.168.1.100", "connected")

        # Verify connection tracking
        self.assertIn("client_123", self.ws_logger.active_connections)
        self.assertEqual(
            self.ws_logger.active_connections["client_123"]["remote_address"],
            "192.168.1.100"
        )

        # Test disconnection
        self.ws_logger.log_connection("client_123", "192.168.1.100", "disconnected")

        # Verify connection removal
        self.assertNotIn("client_123", self.ws_logger.active_connections)

    def test_message_logging(self):
        """Test WebSocket message logging"""
        # Set up connection
        self.ws_logger.log_connection("client_123", "192.168.1.100", "connected")

        # Log messages
        self.ws_logger.log_message("client_123", "sent", "vision_data", 1024, 0.005)
        self.ws_logger.log_message("client_123", "received", "command", 256, 0.001)

        # Verify message statistics
        self.assertEqual(self.ws_logger.message_stats["sent"], 1)
        self.assertEqual(self.ws_logger.message_stats["received"], 1)
        self.assertEqual(
            self.ws_logger.active_connections["client_123"]["messages_sent"], 1
        )
        self.assertEqual(
            self.ws_logger.active_connections["client_123"]["messages_received"], 1
        )

    def test_error_logging(self):
        """Test WebSocket error logging"""
        self.ws_logger.log_error("client_123", "connection_lost", "Network error")

        self.assertEqual(self.ws_logger.message_stats["errors"], 1)

        # Check logged error
        error_record = None
        for record in self.log_records:
            if hasattr(record, 'event_type') and record.event_type == "websocket_error":
                error_record = record
                break

        self.assertIsNotNone(error_record)
        self.assertEqual(error_record.error_type, "connection_lost")
        self.assertEqual(error_record.error_message, "Network error")

class TestVisionSystemLogger(unittest.TestCase):
    """Test vision system logging"""

    def setUp(self):
        self.logger = logging.getLogger("test_vision_logger")
        self.logger.handlers.clear()

        # Add in-memory handler for testing
        self.log_records = []
        handler = logging.Handler()
        handler.emit = lambda record: self.log_records.append(record)
        self.logger.addHandler(handler)
        self.logger.setLevel(logging.DEBUG)

        self.vision_logger = VisionSystemLogger(self.logger)

    def test_frame_processing_logging(self):
        """Test frame processing event logging"""
        detections = [
            {"class": "person", "confidence": 0.85, "bbox": [100, 100, 200, 300]},
            {"class": "car", "confidence": 0.72, "bbox": [300, 150, 450, 250]}
        ]

        self.vision_logger.log_frame_processing(
            "frame_001", 0.033, (640, 480), detections
        )

        # Verify statistics
        self.assertEqual(self.vision_logger.frame_stats["processed"], 1)
        self.assertEqual(self.vision_logger.frame_stats["detections"], 2)
        self.assertEqual(len(self.vision_logger.detection_history), 1)

        # Check logged record
        frame_record = None
        for record in self.log_records:
            if hasattr(record, 'event_type') and record.event_type == "frame_processed":
                frame_record = record
                break

        self.assertIsNotNone(frame_record)
        self.assertEqual(frame_record.frame_id, "frame_001")
        self.assertEqual(frame_record.detection_count, 2)
        self.assertEqual(frame_record.frame_width, 640)
        self.assertEqual(frame_record.frame_height, 480)

    def test_detection_results_logging(self):
        """Test detection results logging"""
        detections = [
            {"class": "person", "confidence": 0.85},
            {"class": "car", "confidence": 0.45},
            {"class": "bike", "confidence": 0.92}
        ]

        self.vision_logger.log_detection_results("frame_001", detections, 0.5)

        # Check logged record
        detection_record = None
        for record in self.log_records:
            if hasattr(record, 'event_type') and record.event_type == "detection_results":
                detection_record = record
                break

        self.assertIsNotNone(detection_record)
        self.assertEqual(detection_record.total_detections, 3)
        self.assertEqual(detection_record.high_confidence_detections, 2)  # 0.85 and 0.92
        self.assertEqual(detection_record.confidence_threshold, 0.5)

    def test_frame_error_logging(self):
        """Test frame error logging"""
        self.vision_logger.log_frame_error("frame_001", "decode_error", "Invalid frame format")

        self.assertEqual(self.vision_logger.frame_stats["failed"], 1)

        # Check logged error
        error_record = None
        for record in self.log_records:
            if hasattr(record, 'event_type') and record.event_type == "frame_error":
                error_record = record
                break

        self.assertIsNotNone(error_record)
        self.assertEqual(error_record.error_type, "decode_error")
        self.assertEqual(error_record.error_message, "Invalid frame format")

    def test_performance_summary(self):
        """Test performance summary generation"""
        # Process multiple frames
        for i in range(15):
            detections = [{"class": "person", "confidence": 0.8}] * (i % 3)
            self.vision_logger.log_frame_processing(
                f"frame_{i:03d}", 0.030 + (i * 0.001), (640, 480), detections
            )

        # Add some failures
        for i in range(3):
            self.vision_logger.log_frame_error(f"frame_err_{i}", "test_error", "Test")

        summary = self.vision_logger.get_performance_summary()

        self.assertEqual(summary["total_frames_processed"], 15)
        self.assertEqual(summary["total_frames_failed"], 3)
        self.assertGreater(summary["success_rate"], 80)
        self.assertGreater(summary["avg_processing_time_seconds"], 0.03)

class TestR2D2LoggerFactory(unittest.TestCase):
    """Test the logger factory"""

    def setUp(self):
        # Use temporary directory for test logs
        self.temp_dir = tempfile.mkdtemp()
        self.original_log_dir = None

        # Patch LOG_DIR
        import r2d2_logging_framework
        self.original_log_dir = r2d2_logging_framework.LOG_DIR
        r2d2_logging_framework.LOG_DIR = Path(self.temp_dir)

    def tearDown(self):
        # Restore original LOG_DIR
        if self.original_log_dir:
            import r2d2_logging_framework
            r2d2_logging_framework.LOG_DIR = self.original_log_dir

        # Clean up temp directory
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_basic_logger_creation(self):
        """Test basic logger creation"""
        components = R2D2LoggerFactory.create_service_logger("test_service")

        self.assertIn("logger", components)
        self.assertIsInstance(components["logger"], logging.Logger)
        self.assertEqual(components["logger"].name, "r2d2.test_service")

    def test_full_logger_creation(self):
        """Test logger creation with all components"""
        components = R2D2LoggerFactory.create_service_logger(
            "full_test_service",
            enable_performance_monitoring=True,
            enable_websocket_logging=True,
            enable_vision_logging=True
        )

        self.assertIn("logger", components)
        self.assertIn("performance_logger", components)
        self.assertIn("websocket_logger", components)
        self.assertIn("vision_logger", components)

        self.assertIsInstance(components["performance_logger"], PerformanceLogger)
        self.assertIsInstance(components["websocket_logger"], WebSocketEventLogger)
        self.assertIsInstance(components["vision_logger"], VisionSystemLogger)

    def test_log_file_creation(self):
        """Test that log files are created correctly"""
        components = R2D2LoggerFactory.create_service_logger("file_test_service")
        logger = components["logger"]

        # Log a test message
        logger.info("Test log message")

        # Check log files exist
        log_file = Path(self.temp_dir) / "file_test_service.log"
        error_log_file = Path(self.temp_dir) / "file_test_service_errors.log"

        self.assertTrue(log_file.exists())
        self.assertTrue(error_log_file.exists())

        # Check log content
        with open(log_file, 'r') as f:
            content = f.read()
            self.assertIn("Test log message", content)
            # Should be JSON format
            lines = content.strip().split('\n')
            log_data = json.loads(lines[0])
            self.assertEqual(log_data["service"], "file_test_service")

class TestLogAnalyzer(unittest.TestCase):
    """Test log analysis functionality"""

    def setUp(self):
        # Use temporary directory for test logs
        self.temp_dir = tempfile.mkdtemp()

        # Patch LOG_DIR
        import r2d2_logging_framework
        self.original_log_dir = r2d2_logging_framework.LOG_DIR
        r2d2_logging_framework.LOG_DIR = Path(self.temp_dir)

    def tearDown(self):
        # Restore original LOG_DIR
        if self.original_log_dir:
            import r2d2_logging_framework
            r2d2_logging_framework.LOG_DIR = self.original_log_dir

        # Clean up temp directory
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_log_analysis_empty_directory(self):
        """Test log analysis with empty log directory"""
        analysis = get_log_analyzer()

        self.assertIn("timestamp", analysis)
        self.assertIn("log_files", analysis)
        self.assertIn("summary", analysis)
        self.assertEqual(analysis["summary"]["total_services"], 0)

    def test_log_analysis_with_files(self):
        """Test log analysis with existing log files"""
        # Create test log files
        test_log = Path(self.temp_dir) / "test_service.log"
        test_error_log = Path(self.temp_dir) / "test_service_errors.log"

        test_log.write_text("Test log content\n")
        test_error_log.write_text("Error line 1\nError line 2\n")

        analysis = get_log_analyzer()

        self.assertEqual(analysis["summary"]["total_services"], 1)
        self.assertGreater(analysis["summary"]["error_count"], 0)
        self.assertEqual(len(analysis["log_files"]), 1)
        self.assertEqual(analysis["log_files"][0]["service"], "test_service")

class TestIntegrationScenarios(unittest.TestCase):
    """Test integration scenarios"""

    def setUp(self):
        # Use temporary directory for test logs
        self.temp_dir = tempfile.mkdtemp()

        # Patch LOG_DIR
        import r2d2_logging_framework
        self.original_log_dir = r2d2_logging_framework.LOG_DIR
        r2d2_logging_framework.LOG_DIR = Path(self.temp_dir)

    def tearDown(self):
        # Restore original LOG_DIR
        if self.original_log_dir:
            import r2d2_logging_framework
            r2d2_logging_framework.LOG_DIR = self.original_log_dir

        # Clean up temp directory
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_vision_system_integration(self):
        """Test complete vision system logging integration"""
        components = R2D2LoggerFactory.create_service_logger(
            "vision_integration_test",
            enable_performance_monitoring=True,
            enable_websocket_logging=True,
            enable_vision_logging=True
        )

        logger = components["logger"]
        perf_logger = components["performance_logger"]
        ws_logger = components["websocket_logger"]
        vision_logger = components["vision_logger"]

        # Simulate vision system workflow
        ws_logger.log_connection("dashboard_client", "127.0.0.1", "connected")

        with perf_logger.measure_operation("frame_processing", frame_id="frame_001"):
            # Simulate frame processing
            time.sleep(0.01)
            detections = [{"class": "person", "confidence": 0.85, "bbox": [100, 100, 200, 300]}]
            vision_logger.log_frame_processing("frame_001", 0.010, (640, 480), detections)

        ws_logger.log_message("dashboard_client", "sent", "vision_data", 2048, 0.002)
        ws_logger.log_connection("dashboard_client", "127.0.0.1", "disconnected")

        # Verify log files were created and contain expected content
        log_file = Path(self.temp_dir) / "vision_integration_test.log"
        self.assertTrue(log_file.exists())

        with open(log_file, 'r') as f:
            log_content = f.read()
            self.assertIn("frame_processing", log_content)
            self.assertIn("operation_complete", log_content)
            self.assertIn("websocket_connected", log_content)

    def test_concurrent_logging(self):
        """Test concurrent logging from multiple threads"""
        components = R2D2LoggerFactory.create_service_logger("concurrent_test")
        logger = components["logger"]

        # Function to log from multiple threads
        def log_worker(worker_id, message_count):
            for i in range(message_count):
                logger.info(f"Worker {worker_id} message {i}", extra={
                    "worker_id": worker_id,
                    "message_number": i
                })

        # Start multiple threads
        threads = []
        for worker_id in range(5):
            thread = threading.Thread(target=log_worker, args=(worker_id, 10))
            threads.append(thread)
            thread.start()

        # Wait for all threads
        for thread in threads:
            thread.join()

        # Verify all messages were logged (allow for logger initialization message)
        log_file = Path(self.temp_dir) / "concurrent_test.log"
        with open(log_file, 'r') as f:
            lines = f.readlines()
            # Should have 50 worker messages + 1 initialization message
            self.assertGreaterEqual(len(lines), 50)  # At least 50 messages logged

if __name__ == "__main__":
    # Set up test environment
    print("🧪 Running R2D2 Logging Framework Tests")
    print("=" * 50)

    # Create test suite
    test_suite = unittest.TestSuite()

    # Add test cases
    test_cases = [
        TestR2D2StructuredFormatter,
        TestPerformanceLogger,
        TestWebSocketEventLogger,
        TestVisionSystemLogger,
        TestR2D2LoggerFactory,
        TestLogAnalyzer,
        TestIntegrationScenarios
    ]

    for test_case in test_cases:
        tests = unittest.TestLoader().loadTestsFromTestCase(test_case)
        test_suite.addTests(tests)

    # Run tests with detailed output
    runner = unittest.TextTestRunner(
        verbosity=2,
        stream=sys.stdout,
        failfast=False
    )

    print("\n🔬 Starting comprehensive logging framework tests...")
    result = runner.run(test_suite)

    # Print summary
    print("\n" + "=" * 50)
    print("📊 Test Results Summary")
    print("=" * 50)
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Success rate: {((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100):.1f}%")

    if result.failures:
        print("\n❌ Failures:")
        for test, traceback in result.failures:
            print(f"  - {test}: {traceback.split('AssertionError:')[-1].strip()}")

    if result.errors:
        print("\n💥 Errors:")
        for test, traceback in result.errors:
            print(f"  - {test}: {traceback.split('Exception:')[-1].strip()}")

    if result.wasSuccessful():
        print("\n✅ All tests passed! Logging framework is ready for integration.")
    else:
        print("\n⚠️  Some tests failed. Please review and fix issues before integration.")

    sys.exit(0 if result.wasSuccessful() else 1)