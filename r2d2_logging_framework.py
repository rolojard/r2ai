#!/usr/bin/env python3
"""
R2D2 Comprehensive Logging Framework
====================================

Advanced Python logging infrastructure for all R2D2 backend services.
Provides structured logging, performance monitoring, and agent-analyzable output.

Features:
- JSON structured logging for machine readability
- Performance metrics tracking
- Error correlation across services
- Non-disruptive integration with existing systems
- Memory-efficient log rotation
- WebSocket event logging
- System health monitoring

Author: Expert Python Coder Agent
"""

import os
import sys
import json
import time
import logging
import threading
import traceback
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional, Union
from pathlib import Path
from logging.handlers import RotatingFileHandler
from contextlib import contextmanager
import psutil
import queue

# Configure logging directory
LOG_DIR = Path("/home/rolo/r2ai/logs")
LOG_DIR.mkdir(exist_ok=True)

class R2D2StructuredFormatter(logging.Formatter):
    """
    Structured JSON formatter for R2D2 logs
    Provides machine-readable logs for other agents
    """

    def __init__(self, service_name: str, include_system_info: bool = True):
        self.service_name = service_name
        self.include_system_info = include_system_info
        super().__init__()

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as structured JSON"""

        # Base log structure
        log_entry = {
            "timestamp": datetime.fromtimestamp(record.created, tz=timezone.utc).isoformat(),
            "service": self.service_name,
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno
        }

        # Add exception information if present
        if record.exc_info:
            log_entry["exception"] = {
                "type": record.exc_info[0].__name__,
                "message": str(record.exc_info[1]),
                "traceback": traceback.format_exception(*record.exc_info)
            }

        # Add extra fields from log record
        extra_fields = {}
        for key, value in record.__dict__.items():
            if key not in ['name', 'msg', 'args', 'levelname', 'levelno', 'pathname',
                          'filename', 'module', 'exc_info', 'exc_text', 'stack_info',
                          'lineno', 'funcName', 'created', 'msecs', 'relativeCreated',
                          'thread', 'threadName', 'processName', 'process', 'getMessage']:
                extra_fields[key] = value

        if extra_fields:
            log_entry["extra"] = extra_fields

        # Add system information if enabled
        if self.include_system_info and record.levelno >= logging.WARNING:
            try:
                process = psutil.Process()
                log_entry["system"] = {
                    "memory_mb": round(process.memory_info().rss / 1024 / 1024, 2),
                    "cpu_percent": round(process.cpu_percent(), 2),
                    "thread_count": process.num_threads()
                }
            except:
                pass

        return json.dumps(log_entry, ensure_ascii=False)

class PerformanceLogger:
    """
    Performance monitoring and metrics logging
    """

    def __init__(self, logger: logging.Logger):
        self.logger = logger
        self.metrics_queue = queue.Queue()
        self._start_monitoring_thread()

    def _start_monitoring_thread(self):
        """Start background thread for metrics collection"""
        def monitor_loop():
            while True:
                try:
                    # Collect metrics every 30 seconds
                    metrics = self._collect_system_metrics()
                    self.logger.info("System performance metrics collected", extra={
                        "event_type": "performance_metrics",
                        "metrics": metrics
                    })
                    time.sleep(30)
                except Exception as e:
                    self.logger.error(f"Error collecting performance metrics: {e}")
                    time.sleep(60)  # Wait longer on error

        monitor_thread = threading.Thread(target=monitor_loop, daemon=True)
        monitor_thread.start()

    def _collect_system_metrics(self) -> Dict[str, Any]:
        """Collect comprehensive system metrics"""
        try:
            # System-wide metrics
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')

            # Process-specific metrics
            process = psutil.Process()
            process_memory = process.memory_info()

            return {
                "system": {
                    "cpu_percent": round(cpu_percent, 2),
                    "memory_percent": round(memory.percent, 2),
                    "memory_available_gb": round(memory.available / 1024**3, 2),
                    "disk_percent": round(disk.percent, 2),
                    "disk_free_gb": round(disk.free / 1024**3, 2)
                },
                "process": {
                    "memory_mb": round(process_memory.rss / 1024**2, 2),
                    "memory_vms_mb": round(process_memory.vms / 1024**2, 2),
                    "cpu_percent": round(process.cpu_percent(), 2),
                    "threads": process.num_threads(),
                    "open_files": len(process.open_files()),
                    "connections": len(process.connections())
                }
            }
        except Exception as e:
            return {"error": str(e)}

    @contextmanager
    def measure_operation(self, operation_name: str, **kwargs):
        """Context manager for measuring operation performance"""
        start_time = time.time()
        start_memory = None

        try:
            process = psutil.Process()
            start_memory = process.memory_info().rss
        except:
            pass

        operation_id = f"{operation_name}_{int(start_time * 1000)}"

        self.logger.debug(f"Starting operation: {operation_name}", extra={
            "event_type": "operation_start",
            "operation_id": operation_id,
            "operation_name": operation_name,
            **kwargs
        })

        try:
            yield operation_id

            # Success metrics
            duration = time.time() - start_time
            memory_delta = 0

            if start_memory:
                try:
                    current_memory = psutil.Process().memory_info().rss
                    memory_delta = current_memory - start_memory
                except:
                    pass

            self.logger.info(f"Operation completed: {operation_name}", extra={
                "event_type": "operation_complete",
                "operation_id": operation_id,
                "operation_name": operation_name,
                "duration_seconds": round(duration, 4),
                "memory_delta_mb": round(memory_delta / 1024**2, 2),
                "success": True,
                **kwargs
            })

        except Exception as e:
            # Error metrics
            duration = time.time() - start_time

            self.logger.error(f"Operation failed: {operation_name}", extra={
                "event_type": "operation_error",
                "operation_id": operation_id,
                "operation_name": operation_name,
                "duration_seconds": round(duration, 4),
                "error_message": str(e),
                "success": False,
                **kwargs
            }, exc_info=True)
            raise

class WebSocketEventLogger:
    """
    WebSocket event tracking and correlation
    """

    def __init__(self, logger: logging.Logger):
        self.logger = logger
        self.active_connections = {}
        self.message_stats = {
            "sent": 0,
            "received": 0,
            "errors": 0
        }

    def log_connection(self, client_id: str, remote_address: str, action: str):
        """Log WebSocket connection events"""
        if action == "connected":
            self.active_connections[client_id] = {
                "remote_address": remote_address,
                "connected_at": time.time(),
                "messages_sent": 0,
                "messages_received": 0
            }
        elif action == "disconnected" and client_id in self.active_connections:
            connection_info = self.active_connections.pop(client_id)
            duration = time.time() - connection_info["connected_at"]

            self.logger.info(f"WebSocket client disconnected: {client_id}", extra={
                "event_type": "websocket_disconnect",
                "client_id": client_id,
                "remote_address": remote_address,
                "session_duration_seconds": round(duration, 2),
                "messages_sent": connection_info["messages_sent"],
                "messages_received": connection_info["messages_received"]
            })
            return

        self.logger.info(f"WebSocket client {action}: {client_id}", extra={
            "event_type": f"websocket_{action}",
            "client_id": client_id,
            "remote_address": remote_address,
            "active_connections": len(self.active_connections)
        })

    def log_message(self, client_id: str, direction: str, message_type: str,
                   data_size: int, processing_time: Optional[float] = None):
        """Log WebSocket message events"""
        if direction == "sent":
            self.message_stats["sent"] += 1
            if client_id in self.active_connections:
                self.active_connections[client_id]["messages_sent"] += 1
        elif direction == "received":
            self.message_stats["received"] += 1
            if client_id in self.active_connections:
                self.active_connections[client_id]["messages_received"] += 1

        extra_data = {
            "event_type": f"websocket_message_{direction}",
            "client_id": client_id,
            "message_type": message_type,
            "data_size_bytes": data_size,
            "total_sent": self.message_stats["sent"],
            "total_received": self.message_stats["received"]
        }

        if processing_time is not None:
            extra_data["processing_time_seconds"] = round(processing_time, 4)

        self.logger.debug(f"WebSocket {direction}: {message_type}", extra=extra_data)

    def log_error(self, client_id: str, error_type: str, error_message: str):
        """Log WebSocket errors"""
        self.message_stats["errors"] += 1

        self.logger.error(f"WebSocket error: {error_type}", extra={
            "event_type": "websocket_error",
            "client_id": client_id,
            "error_type": error_type,
            "error_message": error_message,
            "total_errors": self.message_stats["errors"]
        })

class VisionSystemLogger:
    """
    Vision system specific logging
    """

    def __init__(self, logger: logging.Logger):
        self.logger = logger
        self.frame_stats = {
            "processed": 0,
            "failed": 0,
            "detections": 0
        }
        self.detection_history = []

    def log_frame_processing(self, frame_id: str, processing_time: float,
                           frame_size: tuple, detections: List[Dict]):
        """Log frame processing events"""
        self.frame_stats["processed"] += 1
        detection_count = len(detections)
        self.frame_stats["detections"] += detection_count

        # Keep detection history for analysis
        self.detection_history.append({
            "timestamp": time.time(),
            "detection_count": detection_count,
            "processing_time": processing_time
        })

        # Keep only last 100 entries
        if len(self.detection_history) > 100:
            self.detection_history.pop(0)

        self.logger.debug(f"Frame processed: {frame_id}", extra={
            "event_type": "frame_processed",
            "frame_id": frame_id,
            "processing_time_seconds": round(processing_time, 4),
            "frame_width": frame_size[0],
            "frame_height": frame_size[1],
            "detection_count": detection_count,
            "detections": detections,
            "total_frames": self.frame_stats["processed"],
            "total_detections": self.frame_stats["detections"]
        })

    def log_detection_results(self, frame_id: str, detections: List[Dict], confidence_threshold: float):
        """Log detailed detection results"""
        high_confidence_detections = [d for d in detections if d.get("confidence", 0) > confidence_threshold]

        self.logger.info(f"Detections found: {len(detections)}", extra={
            "event_type": "detection_results",
            "frame_id": frame_id,
            "total_detections": len(detections),
            "high_confidence_detections": len(high_confidence_detections),
            "confidence_threshold": confidence_threshold,
            "detections": detections
        })

    def log_frame_error(self, frame_id: str, error_type: str, error_message: str):
        """Log frame processing errors"""
        self.frame_stats["failed"] += 1

        self.logger.error(f"Frame processing error: {error_type}", extra={
            "event_type": "frame_error",
            "frame_id": frame_id,
            "error_type": error_type,
            "error_message": error_message,
            "total_failed": self.frame_stats["failed"]
        })

    def get_performance_summary(self) -> Dict[str, Any]:
        """Get vision system performance summary"""
        if not self.detection_history:
            return {"error": "No detection history available"}

        recent_detections = self.detection_history[-10:]  # Last 10 frames
        avg_processing_time = sum(d["processing_time"] for d in recent_detections) / len(recent_detections)
        avg_detections = sum(d["detection_count"] for d in recent_detections) / len(recent_detections)

        return {
            "total_frames_processed": self.frame_stats["processed"],
            "total_frames_failed": self.frame_stats["failed"],
            "total_detections": self.frame_stats["detections"],
            "success_rate": round(self.frame_stats["processed"] /
                                (self.frame_stats["processed"] + self.frame_stats["failed"]) * 100, 2)
                               if (self.frame_stats["processed"] + self.frame_stats["failed"]) > 0 else 0,
            "avg_processing_time_seconds": round(avg_processing_time, 4),
            "avg_detections_per_frame": round(avg_detections, 2)
        }

class R2D2LoggerFactory:
    """
    Factory for creating R2D2 service loggers with consistent configuration
    """

    @staticmethod
    def create_service_logger(service_name: str, log_level: str = "INFO",
                            enable_performance_monitoring: bool = True,
                            enable_websocket_logging: bool = False,
                            enable_vision_logging: bool = False) -> Dict[str, Any]:
        """
        Create a comprehensive logger setup for R2D2 services

        Returns:
            Dict containing logger, performance_logger, websocket_logger, vision_logger
        """

        # Create base logger
        logger = logging.getLogger(f"r2d2.{service_name}")
        logger.setLevel(getattr(logging, log_level.upper()))

        # Clear existing handlers
        logger.handlers.clear()

        # Console handler for immediate feedback
        console_handler = logging.StreamHandler(sys.stdout)
        console_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        console_handler.setFormatter(console_formatter)
        console_handler.setLevel(logging.INFO)
        logger.addHandler(console_handler)

        # Structured JSON file handler
        log_file = LOG_DIR / f"{service_name}.log"
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=50*1024*1024,  # 50MB
            backupCount=5,
            encoding='utf-8'
        )
        file_handler.setFormatter(R2D2StructuredFormatter(service_name))
        file_handler.setLevel(getattr(logging, log_level.upper()))
        logger.addHandler(file_handler)

        # Error-specific handler
        error_log_file = LOG_DIR / f"{service_name}_errors.log"
        error_handler = RotatingFileHandler(
            error_log_file,
            maxBytes=10*1024*1024,  # 10MB
            backupCount=3,
            encoding='utf-8'
        )
        error_handler.setFormatter(R2D2StructuredFormatter(service_name))
        error_handler.setLevel(logging.ERROR)
        logger.addHandler(error_handler)

        # Initialize specialized loggers
        components = {"logger": logger}

        if enable_performance_monitoring:
            components["performance_logger"] = PerformanceLogger(logger)

        if enable_websocket_logging:
            components["websocket_logger"] = WebSocketEventLogger(logger)

        if enable_vision_logging:
            components["vision_logger"] = VisionSystemLogger(logger)

        logger.info(f"R2D2 logging initialized for service: {service_name}", extra={
            "event_type": "logger_initialized",
            "service": service_name,
            "log_level": log_level,
            "components": list(components.keys()),
            "log_file": str(log_file)
        })

        return components

def get_log_analyzer() -> Dict[str, Any]:
    """
    Analyze logs for agent consumption
    Returns structured summary of log data
    """
    analysis = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "log_files": [],
        "summary": {
            "total_services": 0,
            "error_count": 0,
            "warning_count": 0,
            "performance_issues": []
        }
    }

    try:
        # Scan log directory
        for log_file in LOG_DIR.glob("*.log"):
            if not log_file.name.endswith("_errors.log"):
                file_stats = {
                    "service": log_file.stem,
                    "file": str(log_file),
                    "size_mb": round(log_file.stat().st_size / 1024**2, 2),
                    "modified": datetime.fromtimestamp(log_file.stat().st_mtime).isoformat()
                }
                analysis["log_files"].append(file_stats)
                analysis["summary"]["total_services"] += 1

        # Analyze recent error logs
        for error_file in LOG_DIR.glob("*_errors.log"):
            if error_file.exists() and error_file.stat().st_size > 0:
                try:
                    with open(error_file, 'r') as f:
                        lines = f.readlines()
                        analysis["summary"]["error_count"] += len(lines)
                except:
                    pass

    except Exception as e:
        analysis["analysis_error"] = str(e)

    return analysis

# Example usage and testing
if __name__ == "__main__":
    # Test the logging framework
    print("🔧 Testing R2D2 Logging Framework")
    print("=" * 50)

    # Create test logger
    components = R2D2LoggerFactory.create_service_logger(
        "test_service",
        enable_performance_monitoring=True,
        enable_websocket_logging=True,
        enable_vision_logging=True
    )

    logger = components["logger"]
    perf_logger = components["performance_logger"]
    ws_logger = components["websocket_logger"]
    vision_logger = components["vision_logger"]

    # Test basic logging
    logger.info("Testing basic logging functionality")
    logger.warning("Testing warning with extra data", extra={"test_field": "test_value"})

    # Test performance monitoring
    with perf_logger.measure_operation("test_operation", operation_type="test"):
        time.sleep(0.1)  # Simulate work

    # Test WebSocket logging
    ws_logger.log_connection("client_123", "192.168.1.100", "connected")
    ws_logger.log_message("client_123", "sent", "vision_data", 1024, 0.005)
    ws_logger.log_connection("client_123", "192.168.1.100", "disconnected")

    # Test vision logging
    vision_logger.log_frame_processing("frame_001", 0.033, (640, 480), [
        {"class": "person", "confidence": 0.85, "bbox": [100, 100, 200, 300]}
    ])

    # Test error logging
    try:
        raise ValueError("Test error for logging")
    except Exception as e:
        logger.error("Testing error logging", exc_info=True)

    print("✅ Logging framework test completed")
    print(f"📁 Log files created in: {LOG_DIR}")

    # Show log analysis
    print("\n📊 Log Analysis:")
    analysis = get_log_analyzer()
    print(json.dumps(analysis, indent=2))