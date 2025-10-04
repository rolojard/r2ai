#!/usr/bin/env python3
"""
Vision System Logging Integration
Non-disruptive logging integration for the running stable_vision_system.py
Designed to be imported and integrated without restarting the service
"""

import threading
import time
import json
import requests
import websocket
from typing import Dict, Any, Optional
from pathlib import Path
import sys
import os

# Add the parent directory to Python path for imports
sys.path.append(str(Path(__file__).parent))

from r2d2_logging_framework import R2D2LoggerFactory


class VisionSystemMonitor:
    """
    Non-disruptive monitor for the vision system
    Monitors WebSocket traffic and system performance
    """

    def __init__(self, vision_ws_port: int = 8767):
        self.vision_ws_port = vision_ws_port
        self.monitoring = False
        self.monitor_thread = None

        # Initialize logging
        self.logging_components = R2D2LoggerFactory.create_service_logger(
            "vision_monitor",
            log_level="INFO",
            enable_performance_monitoring=True,
            enable_websocket_logging=True,
            enable_vision_logging=True
        )

        self.logger = self.logging_components["logger"]
        self.perf_logger = self.logging_components["performance_logger"]
        self.ws_logger = self.logging_components["websocket_logger"]
        self.vision_logger = self.logging_components["vision_logger"]

        self.frame_count = 0
        self.last_frame_time = time.time()
        self.fps_history = []

    def start_monitoring(self):
        """Start non-disruptive monitoring of vision system"""
        if self.monitoring:
            self.logger.warning("Vision monitoring already running")
            return

        self.monitoring = True
        self.monitor_thread = threading.Thread(
            target=self._monitor_loop,
            daemon=True,
            name="VisionMonitor"
        )
        self.monitor_thread.start()

        self.logger.info("Vision system monitoring started", extra={
            "event_type": "monitor_start",
            "target_port": self.vision_ws_port
        })

    def stop_monitoring(self):
        """Stop monitoring"""
        self.monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)

        self.logger.info("Vision system monitoring stopped", extra={
            "event_type": "monitor_stop"
        })

    def _monitor_loop(self):
        """Main monitoring loop"""
        self.logger.info("Starting vision system monitoring loop")

        while self.monitoring:
            try:
                # Monitor via WebSocket connection
                self._monitor_websocket_traffic()

                # Monitor system health
                self._monitor_system_health()

                # Log performance summary
                self._log_performance_summary()

                time.sleep(5)  # Monitor every 5 seconds

            except Exception as e:
                self.logger.error(f"Monitor loop error: {e}", extra={
                    "event_type": "monitor_error",
                    "error": str(e)
                }, exc_info=True)
                time.sleep(10)  # Wait longer on error

    def _monitor_websocket_traffic(self):
        """Monitor WebSocket traffic without disrupting service"""
        try:
            # Create a temporary WebSocket connection to monitor traffic
            ws_url = f"ws://localhost:{self.vision_ws_port}"

            # Use a short-lived connection to sample traffic
            def on_message(ws, message):
                try:
                    data = json.loads(message)
                    self._process_vision_message(data)
                except json.JSONDecodeError:
                    self.logger.warning("Received non-JSON WebSocket message", extra={
                        "event_type": "websocket_non_json",
                        "message_length": len(message)
                    })
                except Exception as e:
                    self.logger.error(f"Error processing WebSocket message: {e}")

            def on_error(ws, error):
                self.logger.debug(f"WebSocket monitoring error: {error}")

            def on_close(ws, close_status_code, close_msg):
                self.logger.debug("WebSocket monitoring connection closed")

            # Create temporary monitoring connection
            ws = websocket.WebSocketApp(
                ws_url,
                on_message=on_message,
                on_error=on_error,
                on_close=on_close
            )

            # Run for 2 seconds to sample traffic
            def run_ws():
                ws.run_forever()

            ws_thread = threading.Thread(target=run_ws, daemon=True)
            ws_thread.start()
            ws_thread.join(timeout=2)
            ws.close()

        except Exception as e:
            self.logger.debug(f"WebSocket monitoring sample failed: {e}")

    def _process_vision_message(self, data: Dict[str, Any]):
        """Process vision system messages for logging"""
        try:
            message_type = data.get('type', 'unknown')

            if message_type == 'frame_data':
                self._log_frame_data(data)
            elif message_type == 'detection_results':
                self._log_detection_results(data)
            elif message_type == 'system_status':
                self._log_system_status(data)
            else:
                self.logger.debug(f"Unknown message type: {message_type}", extra={
                    "event_type": "unknown_message_type",
                    "message_type": message_type,
                    "data_keys": list(data.keys())
                })

        except Exception as e:
            self.logger.error(f"Error processing vision message: {e}", extra={
                "event_type": "message_processing_error",
                "error": str(e),
                "data": data
            })

    def _log_frame_data(self, data: Dict[str, Any]):
        """Log frame processing data"""
        frame_id = data.get('frame_id', f'frame_{self.frame_count}')
        timestamp = data.get('timestamp', time.time())
        fps = data.get('fps', 0)
        detections = data.get('detections', [])

        # Calculate processing time if available
        processing_time = data.get('processing_time', 0)
        if not processing_time and 'start_time' in data:
            processing_time = timestamp - data['start_time']

        # Update frame statistics
        self.frame_count += 1
        current_time = time.time()
        time_delta = current_time - self.last_frame_time
        calculated_fps = 1.0 / time_delta if time_delta > 0 else 0
        self.last_frame_time = current_time

        # Keep FPS history
        self.fps_history.append(calculated_fps)
        if len(self.fps_history) > 30:  # Keep last 30 readings
            self.fps_history.pop(0)

        avg_fps = sum(self.fps_history) / len(self.fps_history)

        # Log frame processing
        frame_size = data.get('frame_size', (0, 0))
        self.vision_logger.log_frame_processing(
            frame_id=frame_id,
            processing_time=processing_time,
            frame_size=frame_size,
            detections=detections
        )

        # Log performance metrics
        self.perf_logger.log_performance_metric(
            "vision_fps",
            avg_fps,
            "fps",
            frame_id=frame_id,
            detection_count=len(detections)
        )

    def _log_detection_results(self, data: Dict[str, Any]):
        """Log detection results"""
        frame_id = data.get('frame_id', 'unknown')
        detections = data.get('detections', [])
        confidence_threshold = data.get('confidence_threshold', 0.5)

        self.vision_logger.log_detection_results(
            frame_id=frame_id,
            detections=detections,
            confidence_threshold=confidence_threshold
        )

    def _log_system_status(self, data: Dict[str, Any]):
        """Log system status messages"""
        status = data.get('status', 'unknown')
        details = data.get('details', {})

        self.logger.info(f"Vision system status: {status}", extra={
            "event_type": "system_status",
            "status": status,
            "details": details
        })

    def _monitor_system_health(self):
        """Monitor system health metrics"""
        try:
            import psutil

            # Get process info for vision system
            vision_processes = []
            for proc in psutil.process_iter(['pid', 'name', 'cmdline', 'memory_info', 'cpu_percent']):
                try:
                    if 'stable_vision_system.py' in ' '.join(proc.info['cmdline'] or []):
                        vision_processes.append({
                            'pid': proc.info['pid'],
                            'memory_mb': round(proc.info['memory_info'].rss / 1024**2, 2),
                            'cpu_percent': proc.info['cpu_percent']
                        })
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue

            if vision_processes:
                self.logger.info("Vision system health check", extra={
                    "event_type": "health_check",
                    "vision_processes": vision_processes,
                    "total_processes": len(vision_processes)
                })

        except Exception as e:
            self.logger.error(f"Health monitoring error: {e}")

    def _log_performance_summary(self):
        """Log performance summary"""
        if len(self.fps_history) > 5:
            avg_fps = sum(self.fps_history) / len(self.fps_history)
            min_fps = min(self.fps_history)
            max_fps = max(self.fps_history)

            # Get vision logger performance summary
            vision_summary = self.vision_logger.get_performance_summary()

            self.logger.info("Vision performance summary", extra={
                "event_type": "performance_summary",
                "fps_stats": {
                    "average": round(avg_fps, 2),
                    "minimum": round(min_fps, 2),
                    "maximum": round(max_fps, 2),
                    "samples": len(self.fps_history)
                },
                "vision_stats": vision_summary,
                "total_frames_monitored": self.frame_count
            })


class ServoSystemMonitor:
    """
    Non-disruptive monitor for the servo API system
    """

    def __init__(self, servo_api_port: int = 5000):
        self.servo_api_port = servo_api_port
        self.monitoring = False
        self.monitor_thread = None

        # Initialize logging
        self.logging_components = R2D2LoggerFactory.create_service_logger(
            "servo_monitor",
            log_level="INFO",
            enable_performance_monitoring=True
        )

        self.logger = self.logging_components["logger"]
        self.perf_logger = self.logging_components["performance_logger"]

    def start_monitoring(self):
        """Start servo API monitoring"""
        if self.monitoring:
            self.logger.warning("Servo monitoring already running")
            return

        self.monitoring = True
        self.monitor_thread = threading.Thread(
            target=self._monitor_loop,
            daemon=True,
            name="ServoMonitor"
        )
        self.monitor_thread.start()

        self.logger.info("Servo API monitoring started", extra={
            "event_type": "monitor_start",
            "target_port": self.servo_api_port
        })

    def stop_monitoring(self):
        """Stop monitoring"""
        self.monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)

        self.logger.info("Servo API monitoring stopped")

    def _monitor_loop(self):
        """Main monitoring loop for servo API"""
        while self.monitoring:
            try:
                # Test API health
                self._test_api_health()

                # Monitor servo processes
                self._monitor_servo_processes()

                time.sleep(10)  # Check every 10 seconds

            except Exception as e:
                self.logger.error(f"Servo monitor error: {e}", exc_info=True)
                time.sleep(15)

    def _test_api_health(self):
        """Test servo API health"""
        try:
            with self.perf_logger.measure_operation("servo_health_check"):
                response = requests.get(
                    f"http://localhost:{self.servo_api_port}/health",
                    timeout=5
                )

                if response.status_code == 200:
                    self.logger.info("Servo API health check passed", extra={
                        "event_type": "api_health_check",
                        "status": "healthy",
                        "response_time_ms": response.elapsed.total_seconds() * 1000
                    })
                else:
                    self.logger.warning("Servo API health check failed", extra={
                        "event_type": "api_health_check",
                        "status": "unhealthy",
                        "status_code": response.status_code
                    })

        except requests.exceptions.RequestException as e:
            self.logger.error("Servo API unreachable", extra={
                "event_type": "api_health_check",
                "status": "unreachable",
                "error": str(e)
            })

    def _monitor_servo_processes(self):
        """Monitor servo-related processes"""
        try:
            import psutil

            servo_processes = []
            for proc in psutil.process_iter(['pid', 'name', 'cmdline', 'memory_info', 'cpu_percent']):
                try:
                    cmdline = ' '.join(proc.info['cmdline'] or [])
                    if 'servo' in cmdline.lower() or 'maestro' in cmdline.lower():
                        servo_processes.append({
                            'pid': proc.info['pid'],
                            'name': proc.info['name'],
                            'memory_mb': round(proc.info['memory_info'].rss / 1024**2, 2),
                            'cpu_percent': proc.info['cpu_percent']
                        })
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue

            if servo_processes:
                self.logger.info("Servo system processes", extra={
                    "event_type": "servo_processes",
                    "processes": servo_processes,
                    "total_processes": len(servo_processes)
                })

        except Exception as e:
            self.logger.error(f"Servo process monitoring error: {e}")


def start_comprehensive_monitoring():
    """
    Start comprehensive monitoring of all R2D2 backend services
    This function can be called from any service to enable logging
    """

    # Create master logger
    master_components = R2D2LoggerFactory.create_service_logger(
        "r2d2_backend_monitor",
        log_level="INFO",
        enable_performance_monitoring=True
    )
    master_logger = master_components["logger"]

    master_logger.info("Starting comprehensive R2D2 backend monitoring", extra={
        "event_type": "monitoring_start",
        "components": ["vision_system", "servo_api", "dashboard_server"]
    })

    # Start vision monitoring
    vision_monitor = VisionSystemMonitor()
    vision_monitor.start_monitoring()

    # Start servo monitoring
    servo_monitor = ServoSystemMonitor()
    servo_monitor.start_monitoring()

    master_logger.info("All monitoring systems active", extra={
        "event_type": "monitoring_active",
        "monitors": ["vision", "servo"]
    })

    return {
        "master_logger": master_logger,
        "vision_monitor": vision_monitor,
        "servo_monitor": servo_monitor
    }


if __name__ == "__main__":
    print("🔍 Starting R2D2 Backend Monitoring System")
    print("=" * 50)

    # Start monitoring
    monitors = start_comprehensive_monitoring()

    try:
        print("✅ Monitoring systems started")
        print("📊 Monitoring vision system on port 8767")
        print("🔧 Monitoring servo API on port 5000")
        print("📁 Logs are being written to /home/rolo/r2ai/logs/")
        print("\nPress Ctrl+C to stop monitoring...")

        # Keep monitoring active
        while True:
            time.sleep(30)
            print(f"🔄 Monitoring active - {time.strftime('%H:%M:%S')}")

    except KeyboardInterrupt:
        print("\n🛑 Stopping monitoring systems...")
        monitors["vision_monitor"].stop_monitoring()
        monitors["servo_monitor"].stop_monitoring()
        print("✅ Monitoring stopped")