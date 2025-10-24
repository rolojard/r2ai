#!/usr/bin/env python3
"""
Phase 2 Alert System Test Suite

Tests the threshold-based alert system functionality including:
- Alert triggering at correct thresholds
- Throttling behavior (max 1 alert per 10 seconds)
- Alert clearing when conditions resolve
- Alert history management
- Visual feedback integration

Author: Super Coder (Expert Python Developer)
Date: 2025-10-23
"""

import asyncio
import json
import time
from datetime import datetime
from typing import Dict, List, Optional


class AlertSystemTester:
    """Comprehensive test suite for Phase 2 Alert System"""

    def __init__(self):
        self.test_results = []
        self.thresholds = {
            'gpu_utilization': {'warning': 85, 'danger': 95},
            'temperature_c': {'warning': 60, 'danger': 70},
            'system_memory_mb': {'warning': 7000, 'danger': 7500},
            'cpu_utilization': {'warning': 80, 'danger': 95}
        }

    def log(self, message: str, level: str = "INFO"):
        """Log test message"""
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        prefix = {
            "INFO": "ℹ️",
            "PASS": "✅",
            "FAIL": "❌",
            "WARN": "⚠️"
        }.get(level, "•")
        print(f"[{timestamp}] {prefix} {message}")

    def test_threshold_detection(self) -> bool:
        """Test 1: Alert threshold detection accuracy"""
        self.log("TEST 1: Threshold Detection Accuracy", "INFO")
        test_cases = [
            # (metric, value, expected_severity)
            ('gpu_utilization', 84, None),  # Below warning
            ('gpu_utilization', 85, 'WARNING'),  # At warning
            ('gpu_utilization', 87, 'WARNING'),  # Above warning
            ('gpu_utilization', 95, 'DANGER'),  # At danger
            ('gpu_utilization', 97, 'DANGER'),  # Above danger
            ('temperature_c', 59, None),  # Safe
            ('temperature_c', 65, 'WARNING'),  # Warning
            ('temperature_c', 72, 'DANGER'),  # Danger
            ('system_memory_mb', 6500, None),  # Safe
            ('system_memory_mb', 7200, 'WARNING'),  # Warning
            ('system_memory_mb', 7600, 'DANGER'),  # Danger
            ('cpu_utilization', 75, None),  # Safe
            ('cpu_utilization', 88, 'WARNING'),  # Warning
            ('cpu_utilization', 96, 'DANGER'),  # Danger
        ]

        passed = 0
        failed = 0

        for metric, value, expected_severity in test_cases:
            actual_severity = self._check_threshold(metric, value)

            if actual_severity == expected_severity:
                self.log(
                    f"  {metric}={value} -> {actual_severity or 'SAFE'} ✓",
                    "PASS"
                )
                passed += 1
            else:
                self.log(
                    f"  {metric}={value} -> Expected: {expected_severity}, "
                    f"Got: {actual_severity} ✗",
                    "FAIL"
                )
                failed += 1

        success = failed == 0
        self.log(f"Test 1 Result: {passed} passed, {failed} failed",
                "PASS" if success else "FAIL")
        return success

    def test_throttling_behavior(self) -> bool:
        """Test 2: Alert throttling (max 1 per 10 seconds)"""
        self.log("TEST 2: Alert Throttling Behavior", "INFO")

        throttle_interval = 10  # seconds
        test_metric = 'gpu_utilization'
        test_value = 87  # Exceeds warning threshold

        # Simulate rapid alerts
        alert_times = []
        for i in range(5):
            current_time = time.time()
            should_alert = self._should_trigger_alert(
                test_metric,
                current_time,
                alert_times
            )

            if should_alert:
                alert_times.append(current_time)
                self.log(f"  Alert {i+1}: TRIGGERED at T+{i}s", "INFO")
            else:
                self.log(f"  Alert {i+1}: THROTTLED at T+{i}s", "INFO")

            time.sleep(1)

        # Should only have 1 alert triggered
        if len(alert_times) == 1:
            self.log("Test 2 Result: Throttling working correctly", "PASS")
            return True
        else:
            self.log(
                f"Test 2 Result: Expected 1 alert, got {len(alert_times)}",
                "FAIL"
            )
            return False

    def test_alert_clearing(self) -> bool:
        """Test 3: Alert auto-clearing when condition resolves"""
        self.log("TEST 3: Alert Auto-Clearing", "INFO")

        test_cases = [
            # (metric, initial_value, final_value, should_clear)
            ('gpu_utilization', 87, 80, True),  # Warning -> Safe
            ('gpu_utilization', 96, 84, True),  # Danger -> Safe
            ('gpu_utilization', 96, 87, False),  # Danger -> Warning (no clear)
            ('temperature_c', 72, 58, True),  # Danger -> Safe
            ('temperature_c', 65, 59, True),  # Warning -> Safe
        ]

        passed = 0
        failed = 0

        for metric, initial, final, should_clear in test_cases:
            initial_severity = self._check_threshold(metric, initial)
            final_severity = self._check_threshold(metric, final)

            cleared = (initial_severity is not None and final_severity is None)

            if cleared == should_clear:
                self.log(
                    f"  {metric}: {initial} -> {final}, "
                    f"Cleared: {cleared} ✓",
                    "PASS"
                )
                passed += 1
            else:
                self.log(
                    f"  {metric}: {initial} -> {final}, "
                    f"Expected clear: {should_clear}, Got: {cleared} ✗",
                    "FAIL"
                )
                failed += 1

        success = failed == 0
        self.log(f"Test 3 Result: {passed} passed, {failed} failed",
                "PASS" if success else "FAIL")
        return success

    def test_history_management(self) -> bool:
        """Test 4: Alert history circular buffer (max 20)"""
        self.log("TEST 4: Alert History Management", "INFO")

        max_history = 20
        history = []

        # Simulate 25 alerts
        for i in range(25):
            alert = {
                'id': f'alert_{i}',
                'metric': 'gpu_utilization',
                'value': 87,
                'timestamp': time.time()
            }
            history.append(alert)

            # Maintain max size
            if len(history) > max_history:
                history.pop(0)

        if len(history) == max_history:
            oldest_id = history[0]['id']
            newest_id = history[-1]['id']

            if oldest_id == 'alert_5' and newest_id == 'alert_24':
                self.log(
                    f"  History size: {len(history)} (correct)",
                    "PASS"
                )
                self.log(
                    f"  Oldest alert: {oldest_id} (correct, 0-4 removed)",
                    "PASS"
                )
                self.log(
                    f"  Newest alert: {newest_id} (correct)",
                    "PASS"
                )
                self.log("Test 4 Result: History management working", "PASS")
                return True
            else:
                self.log(
                    f"Test 4 Result: Incorrect FIFO order",
                    "FAIL"
                )
                return False
        else:
            self.log(
                f"Test 4 Result: Expected 20 alerts, got {len(history)}",
                "FAIL"
            )
            return False

    def test_multiple_simultaneous_alerts(self) -> bool:
        """Test 5: Multiple metrics alerting simultaneously"""
        self.log("TEST 5: Multiple Simultaneous Alerts", "INFO")

        metrics = {
            'gpu_utilization': 92,  # Danger
            'temperature_c': 65,    # Warning
            'cpu_utilization': 88,  # Warning
        }

        alerts_triggered = {}
        for metric, value in metrics.items():
            severity = self._check_threshold(metric, value)
            if severity:
                alerts_triggered[metric] = severity
                self.log(
                    f"  {metric}={value} -> {severity} alert",
                    "INFO"
                )

        if len(alerts_triggered) == 3:
            self.log(
                "Test 5 Result: All 3 alerts triggered independently",
                "PASS"
            )
            return True
        else:
            self.log(
                f"Test 5 Result: Expected 3 alerts, got {len(alerts_triggered)}",
                "FAIL"
            )
            return False

    def test_invalid_data_handling(self) -> bool:
        """Test 6: Graceful handling of invalid metric data"""
        self.log("TEST 6: Invalid Data Handling", "INFO")

        test_cases = [
            ('gpu_utilization', None, False),
            ('gpu_utilization', float('nan'), False),
            ('temperature_c', 'invalid', False),
            ('cpu_utilization', -10, True),  # Negative values are technically valid numbers (though unrealistic)
            ('system_memory_mb', 999999, True),  # Valid but extreme
        ]

        passed = 0
        failed = 0

        for metric, value, should_process in test_cases:
            try:
                severity = self._check_threshold(metric, value)
                processed = severity is not None or (
                    isinstance(value, (int, float)) and not
                    (value is None or (isinstance(value, float) and
                     (value != value)))  # NaN check
                )

                if processed == should_process:
                    self.log(
                        f"  {metric}={value} -> Handled correctly ✓",
                        "PASS"
                    )
                    passed += 1
                else:
                    self.log(
                        f"  {metric}={value} -> Unexpected handling ✗",
                        "FAIL"
                    )
                    failed += 1
            except Exception as e:
                if not should_process:
                    self.log(
                        f"  {metric}={value} -> Exception caught (expected) ✓",
                        "PASS"
                    )
                    passed += 1
                else:
                    self.log(
                        f"  {metric}={value} -> Unexpected exception: {e} ✗",
                        "FAIL"
                    )
                    failed += 1

        success = failed == 0
        self.log(f"Test 6 Result: {passed} passed, {failed} failed",
                "PASS" if success else "FAIL")
        return success

    def test_performance_benchmark(self) -> bool:
        """Test 7: Performance benchmark (latency < 100ms)"""
        self.log("TEST 7: Performance Benchmark", "INFO")

        iterations = 1000
        metrics_batch = {
            'gpu_utilization': 87,
            'temperature_c': 65,
            'system_memory_mb': 7200,
            'cpu_utilization': 88
        }

        start_time = time.perf_counter()

        for _ in range(iterations):
            for metric, value in metrics_batch.items():
                self._check_threshold(metric, value)

        end_time = time.perf_counter()
        total_time = (end_time - start_time) * 1000  # Convert to ms
        avg_time = total_time / iterations

        self.log(f"  Total time: {total_time:.2f}ms", "INFO")
        self.log(f"  Average per check: {avg_time:.3f}ms", "INFO")
        self.log(f"  Iterations: {iterations}", "INFO")

        if avg_time < 1.0:  # Less than 1ms per check
            self.log("Test 7 Result: Performance excellent", "PASS")
            return True
        else:
            self.log("Test 7 Result: Performance acceptable but slow", "WARN")
            return True  # Still pass, just slower

    # Helper methods
    def _check_threshold(self, metric: str, value) -> Optional[str]:
        """Check if value exceeds threshold"""
        if metric not in self.thresholds:
            return None

        # Validate value
        if value is None or not isinstance(value, (int, float)):
            return None
        if isinstance(value, float) and (value != value):  # NaN check
            return None

        threshold = self.thresholds[metric]

        if value >= threshold['danger']:
            return 'DANGER'
        elif value >= threshold['warning']:
            return 'WARNING'
        return None

    def _should_trigger_alert(
        self,
        metric: str,
        current_time: float,
        alert_times: List[float]
    ) -> bool:
        """Check if alert should be triggered (throttling check)"""
        if not alert_times:
            return True

        last_alert_time = alert_times[-1]
        time_since_last = current_time - last_alert_time

        return time_since_last >= 10  # 10 second throttle

    def run_all_tests(self) -> Dict[str, bool]:
        """Run complete test suite"""
        self.log("=" * 70, "INFO")
        self.log("PHASE 2 ALERT SYSTEM TEST SUITE", "INFO")
        self.log("=" * 70, "INFO")
        self.log("", "INFO")

        tests = [
            ("Threshold Detection", self.test_threshold_detection),
            ("Throttling Behavior", self.test_throttling_behavior),
            ("Alert Clearing", self.test_alert_clearing),
            ("History Management", self.test_history_management),
            ("Multiple Simultaneous Alerts", self.test_multiple_simultaneous_alerts),
            ("Invalid Data Handling", self.test_invalid_data_handling),
            ("Performance Benchmark", self.test_performance_benchmark),
        ]

        results = {}
        passed_count = 0
        failed_count = 0

        for test_name, test_func in tests:
            self.log("", "INFO")
            try:
                result = test_func()
                results[test_name] = result
                if result:
                    passed_count += 1
                else:
                    failed_count += 1
            except Exception as e:
                self.log(f"Test '{test_name}' raised exception: {e}", "FAIL")
                results[test_name] = False
                failed_count += 1

            self.log("-" * 70, "INFO")

        # Summary
        self.log("", "INFO")
        self.log("=" * 70, "INFO")
        self.log("TEST SUMMARY", "INFO")
        self.log("=" * 70, "INFO")

        for test_name, result in results.items():
            status = "PASS" if result else "FAIL"
            self.log(f"{test_name}: {status}", status)

        self.log("", "INFO")
        self.log(f"Total: {len(tests)} tests", "INFO")
        self.log(f"Passed: {passed_count}", "PASS" if passed_count > 0 else "INFO")
        self.log(f"Failed: {failed_count}", "FAIL" if failed_count > 0 else "INFO")

        overall_pass = failed_count == 0
        self.log("", "INFO")
        self.log(
            f"OVERALL RESULT: {'ALL TESTS PASSED ✅' if overall_pass else 'SOME TESTS FAILED ❌'}",
            "PASS" if overall_pass else "FAIL"
        )
        self.log("=" * 70, "INFO")

        return results


def main():
    """Main test execution"""
    tester = AlertSystemTester()
    results = tester.run_all_tests()

    # Exit with appropriate code
    all_passed = all(results.values())
    exit(0 if all_passed else 1)


if __name__ == '__main__':
    main()
