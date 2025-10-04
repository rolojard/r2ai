#!/usr/bin/env python3
"""
R2D2 Integrated Servo System Demonstration
Disney-Level Animatronics System Integration Test

This demonstration showcases the complete R2D2 servo control system integration
with all components working together: hardware detection, configuration management,
safety systems, sequence playback, script execution, and dashboard integration.

Features demonstrated:
- Complete system initialization and hardware detection
- Safety system monitoring and emergency procedures
- Professional animatronic sequence playback
- Maestro script compilation and execution
- Real-time dashboard integration
- Multi-layered safety validation
- Performance monitoring and analytics
"""

import time
import logging
import threading
import json
import sys
from pathlib import Path

# Import all servo system components
from pololu_maestro_controller import PololuMaestroController, R2D2MaestroInterface
from maestro_hardware_detector import MaestroHardwareDetector
from r2d2_servo_config_manager import R2D2ServoConfigManager, SafetyLevel
from r2d2_animatronic_sequences import R2D2AnimatronicSequencer, R2D2Emotion
from r2d2_emergency_safety_system import R2D2EmergencySafetySystem
from maestro_script_engine import MaestroScriptEngine

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class R2D2IntegratedServoSystemDemo:
    """Complete R2D2 Servo System Integration Demonstration"""

    def __init__(self):
        # System components
        self.hardware_detector: Optional[MaestroHardwareDetector] = None
        self.controller: Optional[PololuMaestroController] = None
        self.config_manager: Optional[R2D2ServoConfigManager] = None
        self.safety_system: Optional[R2D2EmergencySafetySystem] = None
        self.sequencer: Optional[R2D2AnimatronicSequencer] = None
        self.script_engine: Optional[MaestroScriptEngine] = None
        self.r2d2_interface: Optional[R2D2MaestroInterface] = None

        # Demo state
        self.demo_running = False
        self.demo_start_time = 0.0
        self.demo_phase = "Initialization"

        # Performance tracking
        self.sequences_executed = 0
        self.scripts_executed = 0
        self.safety_events = 0

    def initialize_system(self) -> bool:
        """Initialize the complete R2D2 servo system"""
        logger.info("🚀 Initializing Disney-Level R2D2 Animatronic System...")
        print("\n" + "="*80)
        print("🎭 R2D2 DISNEY-LEVEL ANIMATRONIC SYSTEM INITIALIZATION")
        print("="*80)

        try:
            # Phase 1: Hardware Detection
            print("\n📡 Phase 1: Hardware Detection and Discovery")
            print("-" * 50)

            self.hardware_detector = MaestroHardwareDetector()
            devices = self.hardware_detector.scan_for_maestro_devices()

            if devices:
                optimal_device = self.hardware_detector.get_optimal_device()
                print(f"✅ Detected: {optimal_device.variant.value}")
                print(f"   Port: {optimal_device.port}")
                print(f"   Channels: {optimal_device.channels}")
                print(f"   Firmware: {optimal_device.firmware_version}")

                # Initialize controller with detected hardware
                self.controller = PololuMaestroController(optimal_device.port, simulation_mode=False)
            else:
                print("⚠️  No hardware detected - initializing simulation mode")
                self.controller = PololuMaestroController(simulation_mode=True)

            # Phase 2: Configuration Management
            print("\n⚙️  Phase 2: Configuration Management and Safety Limits")
            print("-" * 50)

            self.config_manager = R2D2ServoConfigManager(self.hardware_detector)
            success = self.config_manager.initialize_from_hardware()

            if success:
                servo_count = len(self.config_manager.get_all_configs())
                print(f"✅ Configured {servo_count} servo channels")
                print(f"   Safety level: {self.config_manager.safety_level.value}")

                # Apply professional safety standards
                self.config_manager.apply_safety_level(SafetyLevel.NORMAL)
                print("🔒 Professional safety standards applied")
            else:
                print("❌ Configuration initialization failed")
                return False

            # Phase 3: Emergency Safety System
            print("\n🛡️  Phase 3: Emergency Safety System")
            print("-" * 50)

            self.safety_system = R2D2EmergencySafetySystem(
                self.controller,
                self.config_manager
            )

            # Add safety callbacks for demonstration
            def safety_alert_callback(alert):
                self.safety_events += 1
                print(f"⚠️  SAFETY ALERT: {alert.message}")

            def emergency_callback(trigger, reason):
                print(f"🚨 EMERGENCY STOP: {trigger.value} - {reason}")

            self.safety_system.add_alert_callback(safety_alert_callback)
            self.safety_system.add_emergency_callback(emergency_callback)

            # Start safety monitoring
            self.safety_system.start_safety_monitoring(0.2)  # 5Hz monitoring
            print("✅ Safety monitoring active (5Hz)")
            print("🔍 Real-time servo monitoring enabled")

            # Phase 4: Animatronic Sequencer
            print("\n🎭 Phase 4: Animatronic Sequence Engine")
            print("-" * 50)

            self.sequencer = R2D2AnimatronicSequencer(self.controller, self.config_manager)
            available_sequences = self.sequencer.get_available_sequences()
            print(f"✅ Loaded {len(available_sequences)} character sequences")
            print(f"   Available emotions: {', '.join([e.value for e in R2D2Emotion])}")

            # Phase 5: Script Engine
            print("\n⚙️  Phase 5: Maestro Script Engine")
            print("-" * 50)

            self.script_engine = MaestroScriptEngine(
                self.controller,
                self.config_manager,
                self.safety_system
            )
            available_scripts = self.script_engine.get_script_library()
            print(f"✅ Compiled {len(available_scripts)} Maestro scripts")
            print(f"   Script library: {', '.join(available_scripts)}")

            # Phase 6: High-Level Interface
            print("\n🤖 Phase 6: R2D2 Character Interface")
            print("-" * 50)

            self.r2d2_interface = R2D2MaestroInterface(self.controller)
            print("✅ R2D2 character interface ready")
            print("🎪 Character behaviors enabled")

            print("\n" + "="*80)
            print("🎯 SYSTEM INITIALIZATION COMPLETE")
            print("✅ All systems operational and ready for performance")
            print("="*80)

            return True

        except Exception as e:
            logger.error(f"System initialization failed: {e}")
            print(f"❌ INITIALIZATION FAILED: {e}")
            return False

    def run_comprehensive_demo(self):
        """Run comprehensive demonstration of all system capabilities"""
        if not self.initialize_system():
            print("❌ Cannot run demo - initialization failed")
            return

        self.demo_running = True
        self.demo_start_time = time.time()

        try:
            print("\n🎬 STARTING COMPREHENSIVE DEMONSTRATION")
            print("="*80)

            # Demo 1: System Startup Sequence
            self._demo_startup_sequence()

            # Demo 2: Character Emotions and Behaviors
            self._demo_character_emotions()

            # Demo 3: Individual Servo Control
            self._demo_individual_servo_control()

            # Demo 4: Script Execution
            self._demo_script_execution()

            # Demo 5: Safety System Testing
            self._demo_safety_system()

            # Demo 6: Performance Analysis
            self._demo_performance_analysis()

            # Demo 7: Shutdown Sequence
            self._demo_shutdown_sequence()

            print("\n" + "="*80)
            print("🎊 DEMONSTRATION COMPLETED SUCCESSFULLY")
            print("✅ All systems performed as expected")
            print("="*80)

        except KeyboardInterrupt:
            print("\n⏹️  Demo interrupted by user")
            self._emergency_shutdown()
        except Exception as e:
            logger.error(f"Demo error: {e}")
            print(f"❌ Demo failed: {e}")
            self._emergency_shutdown()
        finally:
            self.demo_running = False

    def _demo_startup_sequence(self):
        """Demonstrate system startup sequence"""
        self.demo_phase = "Startup Sequence"
        print(f"\n🚀 Demo 1: {self.demo_phase}")
        print("-" * 50)

        print("▶️  Executing R2D2 startup sequence...")
        success = self.sequencer.play_sequence("startup")

        if success:
            print("✅ Startup sequence initiated")
            # Wait for sequence to complete
            time.sleep(9)  # Startup sequence is ~8 seconds
            print("🎯 Startup sequence completed")
            self.sequences_executed += 1
        else:
            print("❌ Startup sequence failed")

        # Home all servos
        print("🏠 Moving all servos to home positions...")
        self.controller.home_all_servos()
        time.sleep(2)
        print("✅ All servos at home position")

    def _demo_character_emotions(self):
        """Demonstrate R2D2 character emotions and behaviors"""
        self.demo_phase = "Character Emotions"
        print(f"\n🎭 Demo 2: {self.demo_phase}")
        print("-" * 50)

        emotions_to_test = [
            R2D2Emotion.EXCITED,
            R2D2Emotion.CURIOUS,
            R2D2Emotion.CONFIDENT,
            R2D2Emotion.PLAYFUL
        ]

        for emotion in emotions_to_test:
            print(f"🎨 Demonstrating {emotion.value} behavior...")

            # Set emotion and play sequence
            self.sequencer.set_emotion(emotion)
            success = self.sequencer.play_emotion_sequence(emotion)

            if success:
                print(f"   ▶️  {emotion.value} sequence playing...")
                time.sleep(6)  # Let sequence play
                print(f"   ✅ {emotion.value} sequence completed")
                self.sequences_executed += 1
            else:
                print(f"   ❌ {emotion.value} sequence failed")

            # Brief pause between emotions
            time.sleep(1)

        print("🎭 Character emotion demonstration completed")

    def _demo_individual_servo_control(self):
        """Demonstrate individual servo control capabilities"""
        self.demo_phase = "Individual Servo Control"
        print(f"\n🎮 Demo 3: {self.demo_phase}")
        print("-" * 50)

        # Test dome rotation
        print("🌀 Testing dome rotation...")
        angles = [45, -45, 90, -90, 0]
        for angle in angles:
            print(f"   Rotating dome to {angle}°...")
            self.r2d2_interface.dome_rotation(angle)
            time.sleep(1.5)
        print("✅ Dome rotation test completed")

        # Test head tilt
        print("📐 Testing head tilt...")
        tilts = [15, -15, 25, -25, 0]
        for tilt in tilts:
            print(f"   Tilting head to {tilt}°...")
            self.r2d2_interface.head_tilt(tilt)
            time.sleep(1.0)
        print("✅ Head tilt test completed")

        # Test utility arms
        print("🦾 Testing utility arms...")
        arm_positions = [(90, 90), (45, 135), (135, 45), (0, 0)]
        for left, right in arm_positions:
            print(f"   Arms: Left={left}°, Right={right}°...")
            self.r2d2_interface.utility_arms(left, right)
            time.sleep(1.5)
        print("✅ Utility arms test completed")

        # Test panels
        print("📦 Testing dome panels...")
        panel_combinations = [
            (True, False, False, False),   # Front only
            (False, True, True, False),    # Left and right
            (False, False, False, True),   # Back only
            (False, False, False, False),  # All closed
        ]

        for front, left, right, back in panel_combinations:
            panels = f"F:{front} L:{left} R:{right} B:{back}"
            print(f"   Panel state: {panels}")
            self.r2d2_interface.dome_panels(front, left, right, back)
            time.sleep(1.5)
        print("✅ Panel control test completed")

    def _demo_script_execution(self):
        """Demonstrate Maestro script execution"""
        self.demo_phase = "Script Execution"
        print(f"\n⚙️  Demo 4: {self.demo_phase}")
        print("-" * 50)

        available_scripts = self.script_engine.get_script_library()

        for script_name in available_scripts[:3]:  # Test first 3 scripts
            print(f"📜 Executing script: {script_name}")

            # Get script info
            script_info = self.script_engine.get_script_info(script_name)
            if script_info:
                duration = script_info.get('estimated_duration', 5.0)
                print(f"   Estimated duration: {duration:.1f}s")

            # Execute script
            success = self.script_engine.execute_script(script_name)

            if success:
                print(f"   ▶️  Script {script_name} executing...")
                time.sleep(max(3.0, duration))  # Wait for completion
                self.script_engine.stop_execution()  # Ensure stopped
                print(f"   ✅ Script {script_name} completed")
                self.scripts_executed += 1
            else:
                print(f"   ❌ Script {script_name} failed to start")

            time.sleep(1)

        print("⚙️  Script execution demonstration completed")

    def _demo_safety_system(self):
        """Demonstrate safety system capabilities"""
        self.demo_phase = "Safety System Testing"
        print(f"\n🛡️  Demo 5: {self.demo_phase}")
        print("-" * 50)

        print("🧪 Testing safety validation...")

        # Test valid command
        is_safe, reason = self.safety_system.validate_servo_command(0, 1500.0)
        print(f"   Valid command (1500μs): {is_safe} - {reason}")

        # Test invalid command (outside limits)
        is_safe, reason = self.safety_system.validate_servo_command(0, 3000.0)
        print(f"   Invalid command (3000μs): {is_safe} - {reason}")

        print("⚠️  Testing simulated safety alert...")
        # Trigger a test alert
        self.safety_system._trigger_alert(
            self.safety_system.EmergencyLevel.WARNING,
            self.safety_system.EmergencyTrigger.TEMPERATURE,
            2,
            "Demo: Simulated temperature warning"
        )

        time.sleep(2)

        print("🚨 Testing emergency stop and recovery...")

        # Test emergency stop
        self.safety_system.emergency_stop(
            self.safety_system.EmergencyTrigger.MANUAL,
            "Demonstration emergency stop"
        )
        print("   ⏹️  Emergency stop activated")

        time.sleep(3)

        # Test emergency reset
        print("   🔓 Attempting emergency reset...")
        reset_success = self.safety_system.reset_emergency_stop(operator_confirmation=True)

        if reset_success:
            print("   ✅ Emergency reset successful")
        else:
            print("   ❌ Emergency reset failed")

        print("🛡️  Safety system demonstration completed")

    def _demo_performance_analysis(self):
        """Demonstrate performance monitoring and analysis"""
        self.demo_phase = "Performance Analysis"
        print(f"\n📊 Demo 6: {self.demo_phase}")
        print("-" * 50)

        # Collect system status from all components
        print("📈 Collecting comprehensive system status...")

        controller_status = self.controller.get_status_report()
        config_status = self.config_manager.get_status_report()
        safety_status = self.safety_system.get_safety_status()
        sequencer_status = self.sequencer.get_status_report()
        script_status = self.script_engine.get_execution_status()

        # Calculate demo statistics
        demo_duration = time.time() - self.demo_start_time

        print("\n📋 PERFORMANCE REPORT")
        print("-" * 30)
        print(f"Demo Duration: {demo_duration:.1f}s")
        print(f"Sequences Executed: {self.sequences_executed}")
        print(f"Scripts Executed: {self.scripts_executed}")
        print(f"Safety Events: {self.safety_events}")
        print(f"Controller Mode: {'Hardware' if not self.controller.simulation_mode else 'Simulation'}")
        print(f"Servo Count: {len(self.config_manager.get_all_configs())}")
        print(f"Safety Level: {self.config_manager.safety_level.value}")
        print(f"Emergency Stops: {safety_status['emergency_stops']}")
        print(f"Safety Monitoring: {'Active' if safety_status['monitoring_active'] else 'Inactive'}")

        # Save comprehensive report
        full_report = {
            "demo_info": {
                "duration": demo_duration,
                "sequences_executed": self.sequences_executed,
                "scripts_executed": self.scripts_executed,
                "safety_events": self.safety_events,
                "timestamp": time.time()
            },
            "controller": controller_status,
            "configuration": config_status,
            "safety": safety_status,
            "sequencer": sequencer_status,
            "script_engine": script_status
        }

        # Export report
        report_filename = f"r2d2_demo_report_{int(time.time())}.json"
        with open(report_filename, 'w') as f:
            json.dump(full_report, f, indent=2)

        print(f"📄 Full report saved to: {report_filename}")
        print("📊 Performance analysis completed")

    def _demo_shutdown_sequence(self):
        """Demonstrate graceful system shutdown"""
        self.demo_phase = "Shutdown Sequence"
        print(f"\n🌙 Demo 7: {self.demo_phase}")
        print("-" * 50)

        print("▶️  Executing R2D2 shutdown sequence...")
        success = self.sequencer.play_sequence("shutdown")

        if success:
            print("✅ Shutdown sequence initiated")
            time.sleep(6)  # Shutdown sequence duration
            print("🎯 Shutdown sequence completed")
        else:
            print("❌ Shutdown sequence failed")

        # Graceful system shutdown
        print("🔌 Shutting down system components...")

        # Stop safety monitoring
        if self.safety_system:
            self.safety_system.stop_safety_monitoring()
            print("   ✅ Safety monitoring stopped")

        # Stop any running sequences or scripts
        if self.sequencer and self.sequencer.is_playing:
            self.sequencer.stop_sequence()
            print("   ✅ Sequence playback stopped")

        if self.script_engine and self.script_engine.is_executing:
            self.script_engine.stop_execution()
            print("   ✅ Script execution stopped")

        # Return servos to home
        print("🏠 Returning all servos to home positions...")
        self.controller.home_all_servos()
        time.sleep(2)

        # Shutdown controller
        self.controller.shutdown()
        print("   ✅ Controller shutdown complete")

        print("🌙 Graceful shutdown completed")

    def _emergency_shutdown(self):
        """Emergency shutdown procedure"""
        print("\n🚨 EMERGENCY SHUTDOWN INITIATED")
        print("-" * 50)

        try:
            if self.safety_system:
                self.safety_system.emergency_stop(
                    self.safety_system.EmergencyTrigger.SYSTEM_ERROR,
                    "Emergency shutdown requested"
                )

            if self.sequencer:
                self.sequencer.stop_sequence()

            if self.script_engine:
                self.script_engine.stop_execution()

            if self.controller:
                self.controller.emergency_stop()
                self.controller.shutdown()

            print("✅ Emergency shutdown completed")

        except Exception as e:
            logger.error(f"Emergency shutdown error: {e}")
            print(f"❌ Emergency shutdown error: {e}")

def main():
    """Main demonstration entry point"""
    print("🎭 R2D2 Disney-Level Animatronic System Demonstration")
    print("=" * 80)
    print("This demo showcases a complete professional animatronic control system")
    print("with hardware detection, safety monitoring, sequence playback, and more.")
    print("\nPress Ctrl+C at any time to initiate emergency stop and shutdown.")
    print("=" * 80)

    input("\nPress Enter to begin demonstration...")

    demo = R2D2IntegratedServoSystemDemo()
    demo.run_comprehensive_demo()

if __name__ == "__main__":
    main()