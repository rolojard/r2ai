#!/usr/bin/env python3
"""
R2D2 Logging Integration Deployment
Non-disruptive deployment of logging to running services
"""

import os
import sys
import time
import json
import signal
import subprocess
from pathlib import Path
from typing import Dict, Any

# Add parent directory to path
sys.path.append(str(Path(__file__).parent))

from r2d2_logging_framework import R2D2LoggerFactory, get_log_analyzer
from vision_logging_integration import start_comprehensive_monitoring


class LoggingDeploymentManager:
    """
    Manages the deployment of logging to running R2D2 services
    """

    def __init__(self):
        # Initialize deployment logger
        self.logging_components = R2D2LoggerFactory.create_service_logger(
            "deployment_manager",
            log_level="INFO",
            enable_performance_monitoring=True
        )
        self.logger = self.logging_components["logger"]
        self.perf_logger = self.logging_components["performance_logger"]

        self.deployment_status = {
            "vision_system": {"status": "pending", "pid": None},
            "servo_api": {"status": "pending", "pid": None},
            "dashboard_server": {"status": "pending", "pid": None},
            "logging_monitor": {"status": "pending", "pid": None}
        }

    def detect_running_services(self) -> Dict[str, Any]:
        """Detect currently running R2D2 services"""
        self.logger.info("Detecting running R2D2 services")

        running_services = {}

        try:
            # Check for vision system
            result = subprocess.run(
                ["pgrep", "-f", "stable_vision_system.py"],
                capture_output=True, text=True
            )
            if result.returncode == 0:
                pids = result.stdout.strip().split('\n')
                # Use the last PID (most recent process)
                pid = int(pids[-1])
                running_services["vision_system"] = {
                    "pid": pid,
                    "command": "stable_vision_system.py",
                    "port": 8767,
                    "all_pids": [int(p) for p in pids]
                }
                self.deployment_status["vision_system"]["pid"] = pid

            # Check for servo API
            result = subprocess.run(
                ["pgrep", "-f", "servo_api_server.py"],
                capture_output=True, text=True
            )
            if result.returncode == 0:
                pids = result.stdout.strip().split('\n')
                pid = int(pids[-1])  # Use the last PID
                running_services["servo_api"] = {
                    "pid": pid,
                    "command": "servo_api_server.py",
                    "port": 5000,
                    "all_pids": [int(p) for p in pids if p.strip()]
                }
                self.deployment_status["servo_api"]["pid"] = pid

            # Check for dashboard server
            result = subprocess.run(
                ["pgrep", "-f", "dashboard-server.js"],
                capture_output=True, text=True
            )
            if result.returncode == 0:
                pids = result.stdout.strip().split('\n')
                pid = int(pids[-1])  # Use the last PID
                running_services["dashboard_server"] = {
                    "pid": pid,
                    "command": "dashboard-server.js",
                    "ports": [8765, 8766, 8768],
                    "all_pids": [int(p) for p in pids if p.strip()]
                }
                self.deployment_status["dashboard_server"]["pid"] = pid

            self.logger.info("Service detection completed", extra={
                "event_type": "service_detection",
                "running_services": list(running_services.keys()),
                "total_services": len(running_services)
            })

            return running_services

        except Exception as e:
            self.logger.error(f"Error detecting services: {e}", exc_info=True)
            return {}

    def validate_service_health(self, running_services: Dict[str, Any]) -> bool:
        """Validate that all services are healthy before logging integration"""
        self.logger.info("Validating service health before logging integration")

        try:
            for service_name, service_info in running_services.items():
                with self.perf_logger.measure_operation(f"health_check_{service_name}"):
                    if service_name == "vision_system":
                        # Check vision system WebSocket
                        import websocket
                        import threading

                        health_ok = False
                        def on_open(ws):
                            nonlocal health_ok
                            health_ok = True
                            ws.close()

                        try:
                            ws = websocket.WebSocketApp(
                                f"ws://localhost:{service_info['port']}",
                                on_open=on_open
                            )
                            ws_thread = threading.Thread(target=ws.run_forever, daemon=True)
                            ws_thread.start()
                            ws_thread.join(timeout=3)

                            if not health_ok:
                                self.logger.error(f"Vision system health check failed - WebSocket not responding")
                                return False

                        except Exception as e:
                            self.logger.error(f"Vision system health check failed: {e}")
                            return False

                    elif service_name == "servo_api":
                        # Check servo API port availability
                        import socket
                        try:
                            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                            sock.settimeout(3)
                            result = sock.connect_ex(('localhost', service_info['port']))
                            sock.close()
                            if result != 0:
                                self.logger.error(f"Servo API port {service_info['port']} not responding")
                                return False
                        except Exception as e:
                            self.logger.error(f"Servo API health check failed: {e}")
                            return False

                    elif service_name == "dashboard_server":
                        # Check dashboard server ports
                        import socket
                        for port in service_info["ports"]:
                            try:
                                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                                sock.settimeout(2)
                                result = sock.connect_ex(('localhost', port))
                                sock.close()
                                if result != 0:
                                    self.logger.error(f"Dashboard server port {port} not responding")
                                    return False
                            except Exception as e:
                                self.logger.error(f"Dashboard server health check failed on port {port}: {e}")
                                return False

            self.logger.info("All services passed health validation", extra={
                "event_type": "health_validation_passed",
                "validated_services": list(running_services.keys())
            })
            return True

        except Exception as e:
            self.logger.error(f"Health validation error: {e}", exc_info=True)
            return False

    def deploy_logging_monitor(self) -> bool:
        """Deploy the non-disruptive logging monitor"""
        self.logger.info("Deploying logging monitor")

        try:
            with self.perf_logger.measure_operation("deploy_logging_monitor"):
                # Start the monitoring system
                monitors = start_comprehensive_monitoring()

                if monitors:
                    self.deployment_status["logging_monitor"]["status"] = "active"
                    self.logger.info("Logging monitor deployed successfully", extra={
                        "event_type": "monitor_deployed",
                        "monitors": list(monitors.keys())
                    })
                    return True
                else:
                    self.logger.error("Failed to start monitoring system")
                    return False

        except Exception as e:
            self.logger.error(f"Error deploying logging monitor: {e}", exc_info=True)
            return False

    def verify_logging_integration(self) -> Dict[str, Any]:
        """Verify that logging integration is working properly"""
        self.logger.info("Verifying logging integration")

        verification_results = {
            "timestamp": time.time(),
            "log_files_created": [],
            "services_monitored": [],
            "total_log_entries": 0,
            "verification_success": False
        }

        try:
            # Wait a moment for logs to be generated
            time.sleep(5)

            # Check for log files
            log_dir = Path("/home/rolo/r2ai/logs")
            if log_dir.exists():
                for log_file in log_dir.glob("*.log"):
                    if not log_file.name.endswith("_errors.log"):
                        verification_results["log_files_created"].append({
                            "service": log_file.stem,
                            "file": str(log_file),
                            "size_bytes": log_file.stat().st_size,
                            "entries": len(log_file.read_text().strip().split('\n')) if log_file.stat().st_size > 0 else 0
                        })

            # Count total log entries
            total_entries = sum(f["entries"] for f in verification_results["log_files_created"])
            verification_results["total_log_entries"] = total_entries

            # Get log analysis
            analysis = get_log_analyzer()
            verification_results["log_analysis"] = analysis

            # Determine success
            verification_results["verification_success"] = (
                len(verification_results["log_files_created"]) > 0 and
                total_entries > 0
            )

            self.logger.info("Logging integration verification completed", extra={
                "event_type": "verification_completed",
                "verification_results": verification_results
            })

            return verification_results

        except Exception as e:
            self.logger.error(f"Verification error: {e}", exc_info=True)
            verification_results["error"] = str(e)
            return verification_results

    def generate_deployment_report(self, running_services: Dict[str, Any],
                                 verification_results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate comprehensive deployment report"""
        report = {
            "deployment_timestamp": time.time(),
            "deployment_status": self.deployment_status,
            "running_services": running_services,
            "verification_results": verification_results,
            "deployment_summary": {
                "total_services_detected": len(running_services),
                "logging_monitor_active": self.deployment_status["logging_monitor"]["status"] == "active",
                "log_files_created": len(verification_results.get("log_files_created", [])),
                "total_log_entries": verification_results.get("total_log_entries", 0),
                "deployment_success": verification_results.get("verification_success", False)
            },
            "next_steps": []
        }

        # Add recommendations
        if report["deployment_summary"]["deployment_success"]:
            report["next_steps"].extend([
                "Logging integration deployed successfully",
                "Monitor logs in /home/rolo/r2ai/logs/ directory",
                "Use get_log_analyzer() for structured log analysis",
                "QA testing can now validate logging functionality"
            ])
        else:
            report["next_steps"].extend([
                "Review deployment errors in logs",
                "Verify service health manually",
                "Check for permission issues in log directory",
                "Retry deployment after resolving issues"
            ])

        self.logger.info("Deployment report generated", extra={
            "event_type": "deployment_report",
            "report_summary": report["deployment_summary"]
        })

        return report

    def execute_deployment(self) -> Dict[str, Any]:
        """Execute complete logging deployment process"""
        self.logger.info("Starting R2D2 logging integration deployment")

        try:
            # Step 1: Detect running services
            running_services = self.detect_running_services()
            if not running_services:
                self.logger.error("No running services detected - deployment aborted")
                return {"error": "No running services detected"}

            # Step 2: Validate service health
            if not self.validate_service_health(running_services):
                self.logger.error("Service health validation failed - deployment aborted")
                return {"error": "Service health validation failed"}

            # Step 3: Deploy logging monitor
            if not self.deploy_logging_monitor():
                self.logger.error("Logging monitor deployment failed")
                return {"error": "Logging monitor deployment failed"}

            # Step 4: Verify integration
            verification_results = self.verify_logging_integration()

            # Step 5: Generate report
            deployment_report = self.generate_deployment_report(running_services, verification_results)

            self.logger.info("Logging deployment completed", extra={
                "event_type": "deployment_completed",
                "success": deployment_report["deployment_summary"]["deployment_success"]
            })

            return deployment_report

        except Exception as e:
            self.logger.error(f"Deployment execution error: {e}", exc_info=True)
            return {"error": str(e), "traceback": str(e)}


def main():
    """Main deployment execution"""
    print("🚀 R2D2 Logging Integration Deployment")
    print("=" * 50)

    # Create deployment manager
    deployment_manager = LoggingDeploymentManager()

    # Execute deployment
    deployment_report = deployment_manager.execute_deployment()

    # Display results
    print("\n📊 DEPLOYMENT REPORT")
    print("=" * 30)

    if "error" in deployment_report:
        print(f"❌ Deployment failed: {deployment_report['error']}")
        return False

    summary = deployment_report["deployment_summary"]
    print(f"✅ Services detected: {summary['total_services_detected']}")
    print(f"🔍 Logging monitor active: {summary['logging_monitor_active']}")
    print(f"📁 Log files created: {summary['log_files_created']}")
    print(f"📝 Total log entries: {summary['total_log_entries']}")
    print(f"🎯 Deployment success: {summary['deployment_success']}")

    print("\n📋 Next Steps:")
    for step in deployment_report["next_steps"]:
        print(f"  • {step}")

    # Save detailed report
    report_file = Path("/home/rolo/r2ai/logging_deployment_report.json")
    with open(report_file, 'w') as f:
        json.dump(deployment_report, f, indent=2, default=str)

    print(f"\n📄 Detailed report saved to: {report_file}")

    return summary["deployment_success"]


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)