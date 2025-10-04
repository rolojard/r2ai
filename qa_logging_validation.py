#!/usr/bin/env python3
"""
QA Validation for R2D2 Logging Integration
Comprehensive validation tests for the deployed logging system
"""

import json
import time
import requests
import websocket
import threading
from pathlib import Path
from typing import Dict, List, Any
import sys
import subprocess

# Add parent directory to path
sys.path.append(str(Path(__file__).parent))

from r2d2_logging_framework import R2D2LoggerFactory, get_log_analyzer


class LoggingQAValidator:
    """
    QA validation for the R2D2 logging system
    Tests all aspects of the logging integration
    """

    def __init__(self):
        # Initialize QA logger
        self.logging_components = R2D2LoggerFactory.create_service_logger(
            "qa_validator",
            log_level="INFO",
            enable_performance_monitoring=True
        )
        self.logger = self.logging_components["logger"]
        self.perf_logger = self.logging_components["performance_logger"]

        self.validation_results = {
            "timestamp": time.time(),
            "tests": [],
            "summary": {
                "total_tests": 0,
                "passed": 0,
                "failed": 0,
                "errors": 0
            }
        }

    def log_test_result(self, test_name: str, passed: bool, details: Dict[str, Any] = None):
        """Log test result"""
        result = {
            "test_name": test_name,
            "passed": passed,
            "timestamp": time.time(),
            "details": details or {}
        }

        self.validation_results["tests"].append(result)
        self.validation_results["summary"]["total_tests"] += 1

        if passed:
            self.validation_results["summary"]["passed"] += 1
            self.logger.info(f"✅ QA Test PASSED: {test_name}", extra={
                "event_type": "qa_test_passed",
                "test_name": test_name,
                "details": details
            })
        else:
            self.validation_results["summary"]["failed"] += 1
            self.logger.error(f"❌ QA Test FAILED: {test_name}", extra={
                "event_type": "qa_test_failed",
                "test_name": test_name,
                "details": details
            })

    def test_log_directory_structure(self) -> bool:
        """Test 1: Validate log directory and file structure"""
        test_name = "Log Directory Structure"

        try:
            log_dir = Path("/home/rolo/r2ai/logs")

            # Check directory exists
            if not log_dir.exists():
                self.log_test_result(test_name, False, {"error": "Log directory does not exist"})
                return False

            # Check for expected log files
            expected_services = ["deployment_manager", "vision_monitor", "servo_monitor", "r2d2_backend_monitor"]
            found_services = []
            missing_services = []

            for service in expected_services:
                log_file = log_dir / f"{service}.log"
                error_file = log_dir / f"{service}_errors.log"

                if log_file.exists():
                    found_services.append(service)
                    # Check if error file exists
                    if not error_file.exists():
                        self.log_test_result(test_name, False, {
                            "error": f"Error log file missing for {service}"
                        })
                        return False
                else:
                    missing_services.append(service)

            if missing_services:
                self.log_test_result(test_name, False, {
                    "missing_services": missing_services,
                    "found_services": found_services
                })
                return False

            self.log_test_result(test_name, True, {
                "log_directory": str(log_dir),
                "services_found": found_services,
                "total_log_files": len(list(log_dir.glob("*.log")))
            })
            return True

        except Exception as e:
            self.log_test_result(test_name, False, {"exception": str(e)})
            return False

    def test_log_format_validation(self) -> bool:
        """Test 2: Validate JSON log format"""
        test_name = "Log Format Validation"

        try:
            log_dir = Path("/home/rolo/r2ai/logs")
            valid_entries = 0
            invalid_entries = 0
            sample_entries = []

            for log_file in log_dir.glob("*.log"):
                if log_file.name.endswith("_errors.log") or log_file.stat().st_size == 0:
                    continue

                with open(log_file, 'r') as f:
                    for line_num, line in enumerate(f.readlines(), 1):
                        if line.strip():
                            try:
                                data = json.loads(line.strip())

                                # Validate required fields
                                required_fields = ["timestamp", "service", "level", "logger", "message"]
                                if all(field in data for field in required_fields):
                                    valid_entries += 1
                                    if len(sample_entries) < 3:
                                        sample_entries.append({
                                            "file": log_file.name,
                                            "line": line_num,
                                            "fields": list(data.keys())
                                        })
                                else:
                                    invalid_entries += 1

                            except json.JSONDecodeError:
                                invalid_entries += 1

            if invalid_entries > 0:
                self.log_test_result(test_name, False, {
                    "valid_entries": valid_entries,
                    "invalid_entries": invalid_entries,
                    "error": "Found invalid JSON log entries"
                })
                return False

            self.log_test_result(test_name, True, {
                "valid_entries": valid_entries,
                "sample_entries": sample_entries
            })
            return True

        except Exception as e:
            self.log_test_result(test_name, False, {"exception": str(e)})
            return False

    def test_service_monitoring_active(self) -> bool:
        """Test 3: Verify service monitoring is active"""
        test_name = "Service Monitoring Active"

        try:
            # Check for monitoring processes
            result = subprocess.run(
                ["pgrep", "-f", "vision_logging_integration.py"],
                capture_output=True, text=True
            )

            monitoring_active = result.returncode == 0

            # Check recent log entries for monitoring activity
            log_dir = Path("/home/rolo/r2ai/logs")
            recent_activity = {}

            for log_file in log_dir.glob("*_monitor.log"):
                if log_file.stat().st_size > 0:
                    with open(log_file, 'r') as f:
                        lines = f.readlines()
                        if lines:
                            # Check last entry timestamp
                            try:
                                last_entry = json.loads(lines[-1].strip())
                                timestamp = last_entry.get("timestamp", "")
                                recent_activity[log_file.stem] = {
                                    "last_entry": timestamp,
                                    "total_entries": len(lines)
                                }
                            except:
                                pass

            if not recent_activity:
                self.log_test_result(test_name, False, {
                    "error": "No recent monitoring activity found"
                })
                return False

            self.log_test_result(test_name, True, {
                "monitoring_processes": monitoring_active,
                "recent_activity": recent_activity
            })
            return True

        except Exception as e:
            self.log_test_result(test_name, False, {"exception": str(e)})
            return False

    def test_performance_metrics_logging(self) -> bool:
        """Test 4: Validate performance metrics are being logged"""
        test_name = "Performance Metrics Logging"

        try:
            log_dir = Path("/home/rolo/r2ai/logs")
            performance_metrics_found = []

            for log_file in log_dir.glob("*.log"):
                if log_file.stat().st_size == 0:
                    continue

                with open(log_file, 'r') as f:
                    for line in f.readlines():
                        if line.strip():
                            try:
                                data = json.loads(line.strip())
                                extra = data.get("extra", {})

                                if extra.get("event_type") == "performance_metrics":
                                    metrics = extra.get("metrics", {})
                                    if "system" in metrics and "process" in metrics:
                                        performance_metrics_found.append({
                                            "service": data.get("service"),
                                            "timestamp": data.get("timestamp"),
                                            "cpu_percent": metrics["system"].get("cpu_percent"),
                                            "memory_percent": metrics["system"].get("memory_percent"),
                                            "process_memory_mb": metrics["process"].get("memory_mb")
                                        })

                            except json.JSONDecodeError:
                                pass

            if len(performance_metrics_found) < 3:
                self.log_test_result(test_name, False, {
                    "error": "Insufficient performance metrics found",
                    "found_count": len(performance_metrics_found)
                })
                return False

            self.log_test_result(test_name, True, {
                "metrics_found": len(performance_metrics_found),
                "sample_metrics": performance_metrics_found[:3]
            })
            return True

        except Exception as e:
            self.log_test_result(test_name, False, {"exception": str(e)})
            return False

    def test_error_logging_functionality(self) -> bool:
        """Test 5: Validate error logging functionality"""
        test_name = "Error Logging Functionality"

        try:
            # Generate a test error
            test_logger = self.logging_components["logger"]
            test_error_message = f"QA Test Error - {time.time()}"

            try:
                raise ValueError(test_error_message)
            except ValueError as e:
                test_logger.error("QA test error for validation", exc_info=True, extra={
                    "event_type": "qa_test_error",
                    "test_message": test_error_message
                })

            # Wait a moment for log to be written
            time.sleep(1)

            # Check if error was logged
            error_log_file = Path("/home/rolo/r2ai/logs/qa_validator_errors.log")
            if not error_log_file.exists():
                self.log_test_result(test_name, False, {
                    "error": "Error log file not created"
                })
                return False

            # Check error log content
            with open(error_log_file, 'r') as f:
                error_content = f.read()

            if test_error_message not in error_content:
                self.log_test_result(test_name, False, {
                    "error": "Test error message not found in error log"
                })
                return False

            # Validate JSON format of error entry
            with open(error_log_file, 'r') as f:
                lines = f.readlines()

            error_entry_found = False
            for line in lines:
                if line.strip():
                    try:
                        data = json.loads(line.strip())
                        if test_error_message in data.get("message", ""):
                            error_entry_found = True
                            if "exception" not in data:
                                self.log_test_result(test_name, False, {
                                    "error": "Exception information missing from error log"
                                })
                                return False
                            break
                    except json.JSONDecodeError:
                        pass

            if not error_entry_found:
                self.log_test_result(test_name, False, {
                    "error": "Test error entry not found in proper format"
                })
                return False

            self.log_test_result(test_name, True, {
                "error_log_file": str(error_log_file),
                "test_error_logged": True
            })
            return True

        except Exception as e:
            self.log_test_result(test_name, False, {"exception": str(e)})
            return False

    def test_log_rotation_setup(self) -> bool:
        """Test 6: Validate log rotation is properly configured"""
        test_name = "Log Rotation Setup"

        try:
            # Generate multiple log entries to test rotation setup
            test_logger = self.logging_components["logger"]

            for i in range(10):
                test_logger.info(f"QA log rotation test entry {i}", extra={
                    "event_type": "qa_rotation_test",
                    "entry_number": i
                })

            time.sleep(1)

            # Check log file sizes and rotation configuration
            log_dir = Path("/home/rolo/r2ai/logs")
            log_file = log_dir / "qa_validator.log"

            if not log_file.exists():
                self.log_test_result(test_name, False, {
                    "error": "QA validator log file not created"
                })
                return False

            # Check file size is reasonable (not too large)
            file_size_mb = log_file.stat().st_size / (1024 * 1024)

            # Check for backup files (if any)
            backup_files = list(log_dir.glob("qa_validator.log.*"))

            self.log_test_result(test_name, True, {
                "log_file_size_mb": round(file_size_mb, 3),
                "backup_files_count": len(backup_files),
                "rotation_configured": True
            })
            return True

        except Exception as e:
            self.log_test_result(test_name, False, {"exception": str(e)})
            return False

    def test_log_analyzer_functionality(self) -> bool:
        """Test 7: Validate log analyzer functionality"""
        test_name = "Log Analyzer Functionality"

        try:
            # Test the log analyzer
            analysis = get_log_analyzer()

            # Validate analysis structure
            required_keys = ["timestamp", "log_files", "summary"]
            if not all(key in analysis for key in required_keys):
                self.log_test_result(test_name, False, {
                    "error": "Log analyzer missing required keys",
                    "found_keys": list(analysis.keys())
                })
                return False

            # Check summary data
            summary = analysis["summary"]
            if summary["total_services"] < 3:
                self.log_test_result(test_name, False, {
                    "error": "Insufficient services detected by analyzer",
                    "total_services": summary["total_services"]
                })
                return False

            self.log_test_result(test_name, True, {
                "total_services": summary["total_services"],
                "error_count": summary["error_count"],
                "log_files_analyzed": len(analysis["log_files"])
            })
            return True

        except Exception as e:
            self.log_test_result(test_name, False, {"exception": str(e)})
            return False

    def test_service_health_monitoring(self) -> bool:
        """Test 8: Validate service health monitoring"""
        test_name = "Service Health Monitoring"

        try:
            # Check for health check entries in logs
            log_dir = Path("/home/rolo/r2ai/logs")
            health_checks_found = []

            for log_file in log_dir.glob("*_monitor.log"):
                if log_file.stat().st_size == 0:
                    continue

                with open(log_file, 'r') as f:
                    for line in f.readlines():
                        if line.strip():
                            try:
                                data = json.loads(line.strip())
                                extra = data.get("extra", {})

                                if extra.get("event_type") == "health_check":
                                    health_checks_found.append({
                                        "service": data.get("service"),
                                        "timestamp": data.get("timestamp"),
                                        "details": extra
                                    })

                            except json.JSONDecodeError:
                                pass

            if len(health_checks_found) < 2:
                self.log_test_result(test_name, False, {
                    "error": "Insufficient health checks found",
                    "found_count": len(health_checks_found)
                })
                return False

            self.log_test_result(test_name, True, {
                "health_checks_found": len(health_checks_found),
                "services_monitored": list(set(hc["service"] for hc in health_checks_found))
            })
            return True

        except Exception as e:
            self.log_test_result(test_name, False, {"exception": str(e)})
            return False

    def run_comprehensive_validation(self) -> Dict[str, Any]:
        """Run all QA validation tests"""
        self.logger.info("Starting comprehensive QA validation of logging system")

        tests = [
            self.test_log_directory_structure,
            self.test_log_format_validation,
            self.test_service_monitoring_active,
            self.test_performance_metrics_logging,
            self.test_error_logging_functionality,
            self.test_log_rotation_setup,
            self.test_log_analyzer_functionality,
            self.test_service_health_monitoring
        ]

        with self.perf_logger.measure_operation("qa_validation_suite"):
            for test_func in tests:
                try:
                    test_func()
                except Exception as e:
                    self.validation_results["summary"]["errors"] += 1
                    self.logger.error(f"QA Test Error: {test_func.__name__}", exc_info=True)

        # Calculate success rate
        total_tests = self.validation_results["summary"]["total_tests"]
        passed_tests = self.validation_results["summary"]["passed"]
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0

        self.validation_results["summary"]["success_rate"] = round(success_rate, 2)

        self.logger.info("QA validation completed", extra={
            "event_type": "qa_validation_complete",
            "summary": self.validation_results["summary"]
        })

        return self.validation_results


def main():
    """Main QA validation execution"""
    print("🔍 R2D2 Logging Integration QA Validation")
    print("=" * 50)

    # Create QA validator
    validator = LoggingQAValidator()

    # Run validation
    results = validator.run_comprehensive_validation()

    # Display results
    print("\n📊 QA VALIDATION RESULTS")
    print("=" * 30)

    summary = results["summary"]
    print(f"📝 Total Tests: {summary['total_tests']}")
    print(f"✅ Passed: {summary['passed']}")
    print(f"❌ Failed: {summary['failed']}")
    print(f"⚠️  Errors: {summary['errors']}")
    print(f"📈 Success Rate: {summary['success_rate']}%")

    print("\n📋 Test Details:")
    for test in results["tests"]:
        status = "✅ PASS" if test["passed"] else "❌ FAIL"
        print(f"  {status} - {test['test_name']}")
        if not test["passed"] and "error" in test["details"]:
            print(f"    Error: {test['details']['error']}")

    # Save detailed results
    results_file = Path("/home/rolo/r2ai/qa_logging_validation_report.json")
    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2, default=str)

    print(f"\n📄 Detailed report saved to: {results_file}")

    # Determine overall success
    overall_success = summary["success_rate"] >= 85  # 85% pass rate required

    if overall_success:
        print("\n🎉 QA VALIDATION SUCCESSFUL!")
        print("✅ R2D2 logging integration is ready for production use")
    else:
        print("\n⚠️  QA VALIDATION FAILED!")
        print("❌ R2D2 logging integration needs fixes before production use")

    return overall_success


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)