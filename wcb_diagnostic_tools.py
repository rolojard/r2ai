#!/usr/bin/env python3
"""
WCB Diagnostic Tools Suite
==========================

Comprehensive testing and diagnostic utilities for WCB meshed network.
Enables connection testing, hardware validation, and complete system diagnostics.

Features:
- Connection and communication testing
- Individual board testing (WCB1, WCB2, WCB3)
- Servo movement verification
- Sound system testing
- Light system testing
- Complete system health check

Author: Expert Project Manager + Super Coder Team
Version: 1.0 Production
Target: NVIDIA Orin Nano R2D2 Systems
"""

import sys
import time
import json
import argparse
import logging
from typing import Dict, List, Any
from dataclasses import dataclass, asdict
from pathlib import Path

# Import WCB components
from wcb_controller import (
    WCBController, WCB1BodyController, WCB2DomePlateController,
    WCB3DomeController, WCBBoard
)
from wcb_orchestrator import WCBOrchestrator, R2D2Mood

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - [%(levelname)s] - %(message)s'
)
logger = logging.getLogger('WCBDiagnostics')

# =============================================
# DIAGNOSTIC DATA STRUCTURES
# =============================================

@dataclass
class DiagnosticResult:
    """Result of a diagnostic test"""
    test_name: str
    passed: bool
    message: str
    duration_ms: float = 0.0
    details: Dict[str, Any] = None

@dataclass
class SystemDiagnosticReport:
    """Complete system diagnostic report"""
    timestamp: float
    overall_health: str  # 'excellent', 'good', 'fair', 'poor', 'critical'
    tests_passed: int
    tests_failed: int
    wcb_connection: DiagnosticResult
    wcb1_body: DiagnosticResult
    wcb2_dome_plate: DiagnosticResult
    wcb3_dome: DiagnosticResult
    mood_system: DiagnosticResult
    recommendations: List[str]

# =============================================
# WCB CONNECTION TESTER
# =============================================

class WCBConnectionTester:
    """Test WCB network connection and basic communication"""

    def __init__(self, port: str = None, auto_detect: bool = True):
        self.port = port
        self.auto_detect = auto_detect

    def test_connection(self) -> DiagnosticResult:
        """Test basic WCB network connection"""
        logger.info("🔍 Testing WCB network connection...")
        start_time = time.time()

        try:
            wcb = WCBController(
                port=self.port,
                auto_detect=self.auto_detect,
                simulation_mode=False
            )

            if wcb.status.connected:
                duration = (time.time() - start_time) * 1000
                wcb.shutdown()

                return DiagnosticResult(
                    test_name="WCB Connection Test",
                    passed=True,
                    message=f"✅ Successfully connected to WCB network on {wcb.port}",
                    duration_ms=duration,
                    details={'port': wcb.port, 'baudrate': wcb.baudrate}
                )
            else:
                return DiagnosticResult(
                    test_name="WCB Connection Test",
                    passed=False,
                    message="❌ Failed to connect to WCB network"
                )

        except Exception as e:
            return DiagnosticResult(
                test_name="WCB Connection Test",
                passed=False,
                message=f"❌ Connection error: {str(e)}"
            )

    def test_simulation_mode(self) -> DiagnosticResult:
        """Test simulation mode (for development without hardware)"""
        logger.info("🔍 Testing simulation mode...")
        start_time = time.time()

        try:
            wcb = WCBController(simulation_mode=True)

            if wcb.status.connected:
                duration = (time.time() - start_time) * 1000
                wcb.shutdown()

                return DiagnosticResult(
                    test_name="Simulation Mode Test",
                    passed=True,
                    message="✅ Simulation mode operational",
                    duration_ms=duration
                )
            else:
                return DiagnosticResult(
                    test_name="Simulation Mode Test",
                    passed=False,
                    message="❌ Simulation mode failed"
                )

        except Exception as e:
            return DiagnosticResult(
                test_name="Simulation Mode Test",
                passed=False,
                message=f"❌ Simulation error: {str(e)}"
            )

# =============================================
# WCB BOARD TESTERS
# =============================================

class WCB1BodyTester:
    """Test WCB1 body controller functionality"""

    def __init__(self, wcb1: WCB1BodyController):
        self.wcb1 = wcb1

    def test_servo_control(self) -> DiagnosticResult:
        """Test WCB1 servo control (Maestro on Serial 1)"""
        logger.info("🔍 Testing WCB1 servo control...")
        start_time = time.time()

        try:
            # Test servo movements
            test_positions = [
                (0, 1500),  # Channel 0 (dome rotation) center
                (0, 1600),  # Right
                (0, 1400),  # Left
                (0, 1500),  # Center return
            ]

            success_count = 0
            for channel, position in test_positions:
                if self.wcb1.move_servo(channel, position):
                    success_count += 1
                time.sleep(0.1)

            duration = (time.time() - start_time) * 1000

            if success_count == len(test_positions):
                return DiagnosticResult(
                    test_name="WCB1 Servo Control",
                    passed=True,
                    message=f"✅ All {success_count} servo commands sent successfully",
                    duration_ms=duration,
                    details={'commands_sent': success_count}
                )
            else:
                return DiagnosticResult(
                    test_name="WCB1 Servo Control",
                    passed=False,
                    message=f"⚠️  Only {success_count}/{len(test_positions)} servo commands succeeded",
                    duration_ms=duration
                )

        except Exception as e:
            return DiagnosticResult(
                test_name="WCB1 Servo Control",
                passed=False,
                message=f"❌ Servo control error: {str(e)}"
            )

    def test_sound_system(self) -> DiagnosticResult:
        """Test WCB1 sound system (HCR on Serial 4)"""
        logger.info("🔍 Testing WCB1 sound system...")
        start_time = time.time()

        try:
            # Test sound commands
            test_sounds = [
                (0, 1),  # Bank 0, Sound 1
                (1, 3),  # Bank 1, Sound 3
            ]

            success_count = 0
            for bank, sound_id in test_sounds:
                if self.wcb1.play_sound(bank, sound_id):
                    success_count += 1
                time.sleep(0.2)

            # Test volume control
            if self.wcb1.set_volume(200):
                success_count += 1

            duration = (time.time() - start_time) * 1000

            if success_count == len(test_sounds) + 1:
                return DiagnosticResult(
                    test_name="WCB1 Sound System",
                    passed=True,
                    message="✅ Sound system commands sent successfully",
                    duration_ms=duration,
                    details={'sounds_tested': len(test_sounds)}
                )
            else:
                return DiagnosticResult(
                    test_name="WCB1 Sound System",
                    passed=False,
                    message=f"⚠️  Sound system partially operational ({success_count} commands)",
                    duration_ms=duration
                )

        except Exception as e:
            return DiagnosticResult(
                test_name="WCB1 Sound System",
                passed=False,
                message=f"❌ Sound system error: {str(e)}"
            )

class WCB2DomePlateTester:
    """Test WCB2 dome plate controller functionality"""

    def __init__(self, wcb2: WCB2DomePlateController):
        self.wcb2 = wcb2

    def test_periscope(self) -> DiagnosticResult:
        """Test WCB2 periscope control (Serial 2)"""
        logger.info("🔍 Testing WCB2 periscope control...")
        start_time = time.time()

        try:
            # Test periscope movements
            tests = [
                self.wcb2.periscope_extend(True),   # Extend
                self.wcb2.periscope_extend(False),  # Retract
                self.wcb2.periscope_position(128),  # Mid position
            ]

            duration = (time.time() - start_time) * 1000

            if all(tests):
                return DiagnosticResult(
                    test_name="WCB2 Periscope Control",
                    passed=True,
                    message="✅ Periscope control operational",
                    duration_ms=duration
                )
            else:
                return DiagnosticResult(
                    test_name="WCB2 Periscope Control",
                    passed=False,
                    message="⚠️  Periscope control partially functional",
                    duration_ms=duration
                )

        except Exception as e:
            return DiagnosticResult(
                test_name="WCB2 Periscope Control",
                passed=False,
                message=f"❌ Periscope error: {str(e)}"
            )

class WCB3DomeTester:
    """Test WCB3 dome controller functionality"""

    def __init__(self, wcb3: WCB3DomeController):
        self.wcb3 = wcb3

    def test_servo_control(self) -> DiagnosticResult:
        """Test WCB3 servo control (Maestro on Serial 1)"""
        logger.info("🔍 Testing WCB3 servo control...")
        start_time = time.time()

        try:
            # Test dome servo movements
            test_positions = [
                (1, 1500),  # Channel 1 (head tilt) center
                (1, 1650),  # Up
                (1, 1350),  # Down
                (1, 1500),  # Center return
            ]

            success_count = 0
            for channel, position in test_positions:
                if self.wcb3.move_servo(channel, position):
                    success_count += 1
                time.sleep(0.1)

            duration = (time.time() - start_time) * 1000

            if success_count == len(test_positions):
                return DiagnosticResult(
                    test_name="WCB3 Servo Control",
                    passed=True,
                    message=f"✅ All {success_count} dome servo commands sent",
                    duration_ms=duration
                )
            else:
                return DiagnosticResult(
                    test_name="WCB3 Servo Control",
                    passed=False,
                    message=f"⚠️  Only {success_count}/{len(test_positions)} commands succeeded"
                )

        except Exception as e:
            return DiagnosticResult(
                test_name="WCB3 Servo Control",
                passed=False,
                message=f"❌ Servo error: {str(e)}"
            )

    def test_lights(self) -> DiagnosticResult:
        """Test WCB3 light systems (PSI and Logic)"""
        logger.info("🔍 Testing WCB3 light systems...")
        start_time = time.time()

        try:
            success_count = 0

            # Test PSI lights (Serial 4)
            if self.wcb3.set_psi_pattern(1, 255):
                success_count += 1
            if self.wcb3.set_psi_color(0, 0, 255):  # Blue
                success_count += 1

            # Test Logic lights (Serial 5)
            if self.wcb3.set_logic_pattern(1, 200):
                success_count += 1

            duration = (time.time() - start_time) * 1000

            if success_count == 3:
                return DiagnosticResult(
                    test_name="WCB3 Light Systems",
                    passed=True,
                    message="✅ PSI and Logic lights operational",
                    duration_ms=duration
                )
            else:
                return DiagnosticResult(
                    test_name="WCB3 Light Systems",
                    passed=False,
                    message=f"⚠️  Light systems partially functional ({success_count}/3)"
                )

        except Exception as e:
            return DiagnosticResult(
                test_name="WCB3 Light Systems",
                passed=False,
                message=f"❌ Light system error: {str(e)}"
            )

# =============================================
# COMPREHENSIVE SYSTEM DIAGNOSTIC
# =============================================

class WCBSystemDiagnostic:
    """Comprehensive WCB system health check"""

    def __init__(self, simulation_mode: bool = False):
        self.simulation_mode = simulation_mode
        self.results: List[DiagnosticResult] = []

    def run_comprehensive_diagnostic(self) -> SystemDiagnosticReport:
        """Run complete system diagnostic"""
        logger.info("=" * 60)
        logger.info("🔧 WCB COMPREHENSIVE SYSTEM DIAGNOSTIC")
        logger.info("=" * 60)

        timestamp = time.time()

        # Test 1: Connection
        logger.info("\n📡 PHASE 1: Connection Testing")
        if self.simulation_mode:
            connection_test = WCBConnectionTester().test_simulation_mode()
        else:
            connection_test = WCBConnectionTester().test_connection()

        self.results.append(connection_test)
        print(f"   {connection_test.message}")

        if not connection_test.passed:
            return self._generate_report(timestamp, connection_test)

        # Initialize WCB system
        wcb = WCBController(simulation_mode=self.simulation_mode)
        wcb1 = WCB1BodyController(wcb)
        wcb2 = WCB2DomePlateController(wcb)
        wcb3 = WCB3DomeController(wcb)

        # Test 2: WCB1 Body
        logger.info("\n🤖 PHASE 2: WCB1 Body Testing")
        wcb1_tester = WCB1BodyTester(wcb1)

        wcb1_servo_test = wcb1_tester.test_servo_control()
        self.results.append(wcb1_servo_test)
        print(f"   {wcb1_servo_test.message}")

        wcb1_sound_test = wcb1_tester.test_sound_system()
        self.results.append(wcb1_sound_test)
        print(f"   {wcb1_sound_test.message}")

        # Test 3: WCB2 Dome Plate
        logger.info("\n🔭 PHASE 3: WCB2 Dome Plate Testing")
        wcb2_tester = WCB2DomePlateTester(wcb2)

        wcb2_test = wcb2_tester.test_periscope()
        self.results.append(wcb2_test)
        print(f"   {wcb2_test.message}")

        # Test 4: WCB3 Dome
        logger.info("\n🎭 PHASE 4: WCB3 Dome Testing")
        wcb3_tester = WCB3DomeTester(wcb3)

        wcb3_servo_test = wcb3_tester.test_servo_control()
        self.results.append(wcb3_servo_test)
        print(f"   {wcb3_servo_test.message}")

        wcb3_lights_test = wcb3_tester.test_lights()
        self.results.append(wcb3_lights_test)
        print(f"   {wcb3_lights_test.message}")

        # Test 5: Mood System
        logger.info("\n🎬 PHASE 5: Mood System Testing")
        mood_test = self._test_mood_system(wcb)
        self.results.append(mood_test)
        print(f"   {mood_test.message}")

        # Cleanup
        wcb.shutdown()

        # Generate final report
        return self._generate_report(timestamp, connection_test, wcb1_servo_test,
                                     wcb2_test, wcb3_servo_test, mood_test)

    def _test_mood_system(self, wcb: WCBController) -> DiagnosticResult:
        """Test mood orchestration system"""
        start_time = time.time()

        try:
            orchestrator = WCBOrchestrator(wcb)

            # Test simple mood execution
            success = orchestrator.execute_mood(R2D2Mood.IDLE_RELAXED, blocking=True)

            duration = (time.time() - start_time) * 1000

            if success:
                stats = orchestrator.get_statistics()
                return DiagnosticResult(
                    test_name="Mood System",
                    passed=True,
                    message="✅ Mood orchestration system operational",
                    duration_ms=duration,
                    details={'moods_available': 27, 'test_mood_executed': True}
                )
            else:
                return DiagnosticResult(
                    test_name="Mood System",
                    passed=False,
                    message="⚠️  Mood system partially functional"
                )

        except Exception as e:
            return DiagnosticResult(
                test_name="Mood System",
                passed=False,
                message=f"❌ Mood system error: {str(e)}"
            )

    def _generate_report(self, timestamp: float, *key_results) -> SystemDiagnosticReport:
        """Generate comprehensive diagnostic report"""
        tests_passed = sum(1 for r in self.results if r.passed)
        tests_failed = len(self.results) - tests_passed

        # Determine overall health
        pass_rate = tests_passed / len(self.results) if self.results else 0
        if pass_rate >= 0.95:
            health = 'excellent'
        elif pass_rate >= 0.80:
            health = 'good'
        elif pass_rate >= 0.60:
            health = 'fair'
        elif pass_rate >= 0.40:
            health = 'poor'
        else:
            health = 'critical'

        # Generate recommendations
        recommendations = self._generate_recommendations()

        # Create report (use first available results for each category)
        connection = key_results[0] if len(key_results) > 0 else self.results[0]
        wcb1 = key_results[1] if len(key_results) > 1 else DiagnosticResult("WCB1", False, "Not tested")
        wcb2 = key_results[2] if len(key_results) > 2 else DiagnosticResult("WCB2", False, "Not tested")
        wcb3 = key_results[3] if len(key_results) > 3 else DiagnosticResult("WCB3", False, "Not tested")
        mood = key_results[4] if len(key_results) > 4 else DiagnosticResult("Mood", False, "Not tested")

        return SystemDiagnosticReport(
            timestamp=timestamp,
            overall_health=health,
            tests_passed=tests_passed,
            tests_failed=tests_failed,
            wcb_connection=connection,
            wcb1_body=wcb1,
            wcb2_dome_plate=wcb2,
            wcb3_dome=wcb3,
            mood_system=mood,
            recommendations=recommendations
        )

    def _generate_recommendations(self) -> List[str]:
        """Generate recommendations based on test results"""
        recommendations = []

        failed_tests = [r for r in self.results if not r.passed]

        if not failed_tests:
            recommendations.append("✅ All systems operational - no action required")
        else:
            for test in failed_tests:
                if "Connection" in test.test_name:
                    recommendations.append("🔌 Check WCB network USB connection")
                    recommendations.append("📡 Verify WCB boards are powered on")
                elif "Servo" in test.test_name:
                    recommendations.append("⚙️  Check Maestro servo controller connections")
                    recommendations.append("🔧 Verify servo power supply")
                elif "Sound" in test.test_name:
                    recommendations.append("🔊 Check HCR sound system connection")
                elif "Periscope" in test.test_name:
                    recommendations.append("🔭 Verify periscope controller wiring")
                elif "Light" in test.test_name:
                    recommendations.append("💡 Check PSI and Logic light connections")
                elif "Mood" in test.test_name:
                    recommendations.append("📝 Verify mood command JSON file is present")

        return recommendations

# =============================================
# CLI INTERFACE
# =============================================

def main():
    """Main CLI interface for WCB diagnostics"""
    parser = argparse.ArgumentParser(
        description="WCB Diagnostic Tools Suite",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument(
        '--test',
        choices=['connection', 'wcb1', 'wcb2', 'wcb3', 'mood', 'comprehensive'],
        default='comprehensive',
        help='Diagnostic test to run (default: comprehensive)'
    )

    parser.add_argument(
        '--simulation',
        action='store_true',
        help='Run in simulation mode (no hardware required)'
    )

    parser.add_argument(
        '--port',
        type=str,
        help='Serial port path (e.g., /dev/ttyUSB0)'
    )

    parser.add_argument(
        '--output',
        type=str,
        help='Save diagnostic report to JSON file'
    )

    args = parser.parse_args()

    # Run diagnostic
    diagnostic = WCBSystemDiagnostic(simulation_mode=args.simulation)
    report = diagnostic.run_comprehensive_diagnostic()

    # Print summary
    logger.info("\n" + "=" * 60)
    logger.info("📊 DIAGNOSTIC SUMMARY")
    logger.info("=" * 60)
    logger.info(f"Overall Health: {report.overall_health.upper()}")
    logger.info(f"Tests Passed: {report.tests_passed}")
    logger.info(f"Tests Failed: {report.tests_failed}")
    logger.info("\n🔧 RECOMMENDATIONS:")
    for rec in report.recommendations:
        logger.info(f"   {rec}")
    logger.info("=" * 60)

    # Save report if requested
    if args.output:
        report_dict = asdict(report)
        with open(args.output, 'w') as f:
            json.dump(report_dict, f, indent=2)
        logger.info(f"\n✅ Diagnostic report saved to {args.output}")

if __name__ == "__main__":
    main()
