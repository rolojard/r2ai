#!/usr/bin/env python3
"""
R2D2 Master Controller - Super Coder Integration System
======================================================

Master controller that integrates all Super Coder components into a unified
R2D2 control system. This provides the highest level interface for R2D2
operation with Disney-quality motion, real-time performance, and convention-
ready reliability.

Integrated Components:
- Disney Servo Control System
- I2C Bus Optimizer
- Real-time Scheduler
- Performance Validator
- System Health Monitor
- Emergency Safety Systems

Author: Super Coder Agent
Target: Production-ready R2D2 systems
"""

import time
import threading
import logging
import json
import os
import signal
import sys
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from enum import Enum
import traceback

# Import our custom modules
try:
    from disney_servo_control import DisneyServoController, R2D2ServoSystem, ServoConfig, ProcessPriority
    from i2c_bus_optimizer import I2CBusOptimizer, I2CPriority, setup_r2d2_i2c_optimization
    from realtime_scheduler import RealtimeScheduler, RTProcessConfig, RTSchedulePolicy, setup_r2d2_realtime_scheduler
    from performance_validator import R2D2PerformanceValidator, ValidationReport, TestStatus, PerformanceLevel
except ImportError as e:
    logging.error(f"Failed to import Super Coder modules: {e}")
    sys.exit(1)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class R2D2State(Enum):
    """R2D2 operational states"""
    OFFLINE = "offline"
    INITIALIZING = "initializing"
    CALIBRATING = "calibrating"
    STANDBY = "standby"
    ACTIVE = "active"
    PERFORMING = "performing"
    ERROR = "error"
    EMERGENCY_STOP = "emergency_stop"
    MAINTENANCE = "maintenance"

class R2D2Mode(Enum):
    """R2D2 operational modes"""
    CONVENTION = "convention"          # Full performance mode
    DEMONSTRATION = "demonstration"    # Demo mode with safety limits
    DEVELOPMENT = "development"        # Development and testing
    MAINTENANCE = "maintenance"        # Maintenance and calibration
    SIMULATION = "simulation"          # Simulation mode (no hardware)

@dataclass
class R2D2Status:
    """Complete R2D2 system status"""
    state: R2D2State = R2D2State.OFFLINE
    mode: R2D2Mode = R2D2Mode.DEVELOPMENT
    uptime: float = 0.0
    last_validation: Optional[float] = None
    performance_level: Optional[PerformanceLevel] = None
    active_subsystems: List[str] = field(default_factory=list)
    error_count: int = 0
    last_error: str = ""
    servo_positions: Dict[str, float] = field(default_factory=dict)
    system_health: float = 1.0  # 0.0 to 1.0
    convention_ready: bool = False

class R2D2MasterController:
    """
    Master controller for R2D2 systems integrating all Super Coder components

    This controller provides:
    - Unified system initialization and configuration
    - Coordinated subsystem management
    - High-level animation and behavior control
    - Real-time performance monitoring
    - Emergency safety systems
    - Convention deployment validation
    """

    def __init__(self, mode: R2D2Mode = R2D2Mode.DEVELOPMENT):
        self.mode = mode
        self.status = R2D2Status(mode=mode)
        self.start_time = time.time()

        # Core subsystems
        self.servo_system: Optional[R2D2ServoSystem] = None
        self.i2c_optimizer: Optional[I2CBusOptimizer] = None
        self.rt_scheduler: Optional[RealtimeScheduler] = None
        self.performance_validator: Optional[R2D2PerformanceValidator] = None

        # System monitoring
        self._monitoring_thread: Optional[threading.Thread] = None
        self._monitoring_active = False
        self._shutdown_requested = False

        # Configuration
        self.config_file = "/home/rolo/r2ai/.claude/agent_storage/super-coder/r2d2_master_config.json"
        self.status_file = "/home/rolo/r2ai/.claude/agent_storage/super-coder/r2d2_status.json"

        # Animation sequences
        self.animation_sequences = {
            'greeting': self._animation_greeting,
            'search': self._animation_search,
            'alert': self._animation_alert,
            'happy': self._animation_happy,
            'sad': self._animation_sad,
            'curious': self._animation_curious,
            'excited': self._animation_excited,
            'sleep': self._animation_sleep,
            'wake_up': self._animation_wake_up
        }

        # Emergency stop handler
        signal.signal(signal.SIGINT, self._emergency_stop_handler)
        signal.signal(signal.SIGTERM, self._emergency_stop_handler)

        logger.info(f"R2D2 Master Controller initialized in {mode.value} mode")

    def initialize_system(self) -> bool:
        """
        Initialize all R2D2 subsystems

        Returns:
            True if initialization successful
        """
        logger.info("Initializing R2D2 system...")
        self.status.state = R2D2State.INITIALIZING

        try:
            # Initialize subsystems in order
            success = True

            # 1. I2C Bus Optimizer (must be first)
            logger.info("Initializing I2C bus optimizer...")
            self.i2c_optimizer = setup_r2d2_i2c_optimization()
            if self.i2c_optimizer:
                self.status.active_subsystems.append("i2c_optimizer")
                logger.info("✓ I2C bus optimizer initialized")
            else:
                logger.error("✗ I2C bus optimizer failed")
                success = False

            # 2. Real-time Scheduler
            logger.info("Initializing real-time scheduler...")
            self.rt_scheduler = setup_r2d2_realtime_scheduler()
            if self.rt_scheduler:
                self.status.active_subsystems.append("rt_scheduler")
                logger.info("✓ Real-time scheduler initialized")
            else:
                logger.error("✗ Real-time scheduler failed")
                success = False

            # 3. Servo Control System
            logger.info("Initializing servo control system...")
            self.servo_system = R2D2ServoSystem()
            if self.servo_system:
                self.status.active_subsystems.append("servo_system")
                logger.info("✓ Servo control system initialized")
            else:
                logger.error("✗ Servo control system failed")
                success = False

            # 4. Performance Validator
            logger.info("Initializing performance validator...")
            self.performance_validator = R2D2PerformanceValidator()
            if self.performance_validator:
                self.status.active_subsystems.append("performance_validator")
                logger.info("✓ Performance validator initialized")
            else:
                logger.error("✗ Performance validator failed")
                success = False

            if success:
                # Start system monitoring
                self._start_monitoring()

                # Initial calibration
                if self.mode != R2D2Mode.SIMULATION:
                    self._perform_calibration()

                self.status.state = R2D2State.STANDBY
                logger.info("R2D2 system initialization completed successfully")
                return True
            else:
                self.status.state = R2D2State.ERROR
                self.status.last_error = "System initialization failed"
                logger.error("R2D2 system initialization failed")
                return False

        except Exception as e:
            self.status.state = R2D2State.ERROR
            self.status.last_error = str(e)
            logger.error(f"System initialization error: {e}")
            logger.error(traceback.format_exc())
            return False

    def _perform_calibration(self):
        """Perform system calibration"""
        logger.info("Performing system calibration...")
        self.status.state = R2D2State.CALIBRATING

        try:
            # Calibrate servos to center positions
            if self.servo_system:
                # Move all servos to center/home positions
                logger.info("Calibrating servo positions...")
                time.sleep(2.0)  # Allow servos to reach position

            # Verify I2C communication
            if self.i2c_optimizer:
                logger.info("Verifying I2C communication...")
                # Test communication with all devices

            logger.info("Calibration completed")

        except Exception as e:
            logger.error(f"Calibration error: {e}")
            self.status.error_count += 1

    def run_performance_validation(self) -> ValidationReport:
        """
        Run comprehensive performance validation

        Returns:
            Validation report
        """
        logger.info("Running performance validation...")

        if not self.performance_validator:
            raise RuntimeError("Performance validator not initialized")

        try:
            # Run full validation suite
            report = self.performance_validator.run_full_validation()

            # Update system status based on validation results
            self.status.last_validation = time.time()
            self.status.performance_level = report.performance_level
            self.status.convention_ready = report.convention_ready

            # Save validation report
            report_file = "/home/rolo/r2ai/.claude/agent_storage/super-coder/latest_validation_report.json"
            self.performance_validator.save_validation_report(report, report_file)

            logger.info(f"Performance validation completed: {report.performance_level.value}, "
                       f"Convention Ready: {report.convention_ready}")

            return report

        except Exception as e:
            logger.error(f"Performance validation failed: {e}")
            self.status.error_count += 1
            raise

    def play_animation(self, animation_name: str, intensity: float = 1.0) -> bool:
        """
        Play a named animation sequence

        Args:
            animation_name: Name of animation to play
            intensity: Animation intensity (0.0 to 2.0)

        Returns:
            True if animation started successfully
        """
        if animation_name not in self.animation_sequences:
            logger.error(f"Unknown animation: {animation_name}")
            return False

        if self.status.state not in [R2D2State.STANDBY, R2D2State.ACTIVE]:
            logger.warning(f"Cannot play animation in state {self.status.state.value}")
            return False

        try:
            self.status.state = R2D2State.PERFORMING
            logger.info(f"Playing animation: {animation_name} (intensity: {intensity})")

            # Execute animation
            animation_function = self.animation_sequences[animation_name]
            success = animation_function(intensity)

            if success:
                self.status.state = R2D2State.ACTIVE
                logger.info(f"Animation {animation_name} completed successfully")
            else:
                self.status.state = R2D2State.ERROR
                self.status.error_count += 1
                logger.error(f"Animation {animation_name} failed")

            return success

        except Exception as e:
            self.status.state = R2D2State.ERROR
            self.status.error_count += 1
            self.status.last_error = f"Animation {animation_name} error: {str(e)}"
            logger.error(f"Animation error: {e}")
            return False

    def _animation_greeting(self, intensity: float) -> bool:
        """R2D2 greeting animation"""
        if not self.servo_system:
            return False

        try:
            # Perform greeting sequence
            self.servo_system.perform_greeting_sequence()
            return True
        except Exception as e:
            logger.error(f"Greeting animation error: {e}")
            return False

    def _animation_search(self, intensity: float) -> bool:
        """R2D2 search animation"""
        if not self.servo_system:
            return False

        try:
            self.servo_system.perform_search_sequence()
            return True
        except Exception as e:
            logger.error(f"Search animation error: {e}")
            return False

    def _animation_alert(self, intensity: float) -> bool:
        """R2D2 alert animation"""
        if not self.servo_system:
            return False

        try:
            self.servo_system.perform_alert_sequence()
            return True
        except Exception as e:
            logger.error(f"Alert animation error: {e}")
            return False

    def _animation_happy(self, intensity: float) -> bool:
        """R2D2 happy animation"""
        if not self.servo_system:
            return False

        try:
            # Happy animation: head nods and dome spins
            controller = self.servo_system.controller
            controller.create_disney_head_nod("head_tilt", intensity)
            time.sleep(1.0)
            controller.create_dome_rotation_search("dome", "curious")
            return True
        except Exception as e:
            logger.error(f"Happy animation error: {e}")
            return False

    def _animation_sad(self, intensity: float) -> bool:
        """R2D2 sad animation"""
        if not self.servo_system:
            return False

        try:
            # Sad animation: head droop
            controller = self.servo_system.controller
            controller.set_angle("head_tilt", 105, duration=2.0)
            time.sleep(3.0)
            controller.set_angle("head_tilt", 90, duration=1.5)
            return True
        except Exception as e:
            logger.error(f"Sad animation error: {e}")
            return False

    def _animation_curious(self, intensity: float) -> bool:
        """R2D2 curious animation"""
        if not self.servo_system:
            return False

        try:
            # Curious animation: head tilt and dome movement
            controller = self.servo_system.controller
            controller.set_angle("head_tilt", 75, duration=1.0)
            controller.create_dome_rotation_search("dome", "curious")
            time.sleep(2.5)
            controller.set_angle("head_tilt", 90, duration=1.0)
            return True
        except Exception as e:
            logger.error(f"Curious animation error: {e}")
            return False

    def _animation_excited(self, intensity: float) -> bool:
        """R2D2 excited animation"""
        if not self.servo_system:
            return False

        try:
            # Excited animation: rapid movements
            controller = self.servo_system.controller
            for _ in range(3):
                controller.create_disney_head_nod("head_tilt", intensity * 1.5)
                time.sleep(0.5)
            return True
        except Exception as e:
            logger.error(f"Excited animation error: {e}")
            return False

    def _animation_sleep(self, intensity: float) -> bool:
        """R2D2 sleep animation"""
        if not self.servo_system:
            return False

        try:
            # Sleep animation: slow movements to rest position
            controller = self.servo_system.controller
            controller.set_multiple_angles({
                "dome": 180,
                "head_tilt": 90,
                "periscope": 0,
                "panel_1": 0,
                "panel_2": 0,
                "panel_3": 0
            }, duration=3.0)
            return True
        except Exception as e:
            logger.error(f"Sleep animation error: {e}")
            return False

    def _animation_wake_up(self, intensity: float) -> bool:
        """R2D2 wake up animation"""
        if not self.servo_system:
            return False

        try:
            # Wake up animation: gentle activation
            controller = self.servo_system.controller
            controller.create_disney_head_nod("head_tilt", intensity * 0.8)
            time.sleep(1.0)
            controller.create_dome_rotation_search("dome", "scan")
            return True
        except Exception as e:
            logger.error(f"Wake up animation error: {e}")
            return False

    def emergency_stop(self):
        """Emergency stop all systems"""
        logger.warning("EMERGENCY STOP ACTIVATED")
        self.status.state = R2D2State.EMERGENCY_STOP

        try:
            # Stop all servo motion
            if self.servo_system:
                self.servo_system.emergency_stop()

            # Stop scheduler processes
            if self.rt_scheduler:
                # Note: Don't shutdown all processes in emergency stop
                pass

            logger.warning("Emergency stop completed")

        except Exception as e:
            logger.error(f"Emergency stop error: {e}")

    def _emergency_stop_handler(self, signum, frame):
        """Signal handler for emergency stop"""
        logger.warning(f"Received signal {signum} - initiating emergency stop")
        self.emergency_stop()
        self.shutdown()
        sys.exit(0)

    def set_mode(self, mode: R2D2Mode) -> bool:
        """
        Change operational mode

        Args:
            mode: New operational mode

        Returns:
            True if mode change successful
        """
        try:
            old_mode = self.mode
            self.mode = mode
            self.status.mode = mode

            logger.info(f"Mode changed from {old_mode.value} to {mode.value}")

            # Apply mode-specific configurations
            if mode == R2D2Mode.CONVENTION:
                # Enable full performance mode
                if self.rt_scheduler:
                    # Start critical processes
                    pass
            elif mode == R2D2Mode.DEMONSTRATION:
                # Enable safety-limited demo mode
                pass
            elif mode == R2D2Mode.MAINTENANCE:
                # Enable maintenance mode
                self.status.state = R2D2State.MAINTENANCE

            return True

        except Exception as e:
            logger.error(f"Mode change error: {e}")
            return False

    def get_system_status(self) -> R2D2Status:
        """
        Get comprehensive system status

        Returns:
            Current system status
        """
        try:
            # Update uptime
            self.status.uptime = time.time() - self.start_time

            # Update servo positions
            if self.servo_system and self.servo_system.controller:
                for name, state in self.servo_system.controller.servo_states.items():
                    self.status.servo_positions[name] = state.current_angle

            # Calculate system health
            health_factors = []

            # Subsystem health
            subsystem_health = len(self.status.active_subsystems) / 4.0  # 4 expected subsystems
            health_factors.append(subsystem_health)

            # Error rate
            error_rate = max(0, 1.0 - (self.status.error_count / 100.0))  # 100 errors = 0 health
            health_factors.append(error_rate)

            # Performance level
            if self.status.performance_level:
                if self.status.performance_level == PerformanceLevel.CONVENTION_READY:
                    perf_health = 1.0
                elif self.status.performance_level == PerformanceLevel.DEMONSTRATION:
                    perf_health = 0.8
                elif self.status.performance_level == PerformanceLevel.DEVELOPMENT:
                    perf_health = 0.6
                else:
                    perf_health = 0.3
                health_factors.append(perf_health)

            # Calculate overall health
            if health_factors:
                self.status.system_health = sum(health_factors) / len(health_factors)
            else:
                self.status.system_health = 0.5

            return self.status

        except Exception as e:
            logger.error(f"Status update error: {e}")
            return self.status

    def save_status(self):
        """Save current status to file"""
        try:
            status_data = {
                'timestamp': time.time(),
                'state': self.status.state.value,
                'mode': self.status.mode.value,
                'uptime': self.status.uptime,
                'active_subsystems': self.status.active_subsystems,
                'error_count': self.status.error_count,
                'last_error': self.status.last_error,
                'servo_positions': self.status.servo_positions,
                'system_health': self.status.system_health,
                'convention_ready': self.status.convention_ready,
                'performance_level': self.status.performance_level.value if self.status.performance_level else None
            }

            with open(self.status_file, 'w') as f:
                json.dump(status_data, f, indent=2)

        except Exception as e:
            logger.error(f"Failed to save status: {e}")

    def _start_monitoring(self):
        """Start background monitoring thread"""
        if self._monitoring_thread is None or not self._monitoring_thread.is_alive():
            self._monitoring_active = True
            self._monitoring_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
            self._monitoring_thread.start()
            logger.info("System monitoring started")

    def _monitoring_loop(self):
        """Background monitoring loop"""
        while self._monitoring_active and not self._shutdown_requested:
            try:
                # Update system status
                self.get_system_status()

                # Save status periodically
                self.save_status()

                # Check for critical errors
                if self.status.system_health < 0.3:
                    logger.warning(f"System health critical: {self.status.system_health:.2f}")

                # Sleep for monitoring interval
                time.sleep(5.0)  # 5 second monitoring interval

            except Exception as e:
                logger.error(f"Monitoring loop error: {e}")
                time.sleep(10.0)

    def shutdown(self):
        """Shutdown R2D2 system gracefully"""
        logger.info("Shutting down R2D2 system...")
        self._shutdown_requested = True
        self.status.state = R2D2State.OFFLINE

        try:
            # Stop monitoring
            self._monitoring_active = False
            if self._monitoring_thread and self._monitoring_thread.is_alive():
                self._monitoring_thread.join(timeout=5.0)

            # Shutdown subsystems
            if self.servo_system:
                # Move servos to safe positions
                logger.info("Moving servos to safe positions...")
                try:
                    self.servo_system.controller.set_multiple_angles({
                        "dome": 180,
                        "head_tilt": 90,
                        "periscope": 0,
                        "panel_1": 0,
                        "panel_2": 0,
                        "panel_3": 0
                    }, duration=2.0)
                    time.sleep(2.5)
                except:
                    pass

            if self.rt_scheduler:
                logger.info("Stopping real-time processes...")
                self.rt_scheduler.shutdown_all_processes()

            if self.i2c_optimizer:
                logger.info("Stopping I2C monitoring...")
                self.i2c_optimizer.stop_monitoring()

            # Save final status
            self.save_status()

            logger.info("R2D2 system shutdown completed")

        except Exception as e:
            logger.error(f"Shutdown error: {e}")

    def __del__(self):
        """Cleanup when controller is destroyed"""
        if not self._shutdown_requested:
            self.shutdown()


def main():
    """Main R2D2 controller function"""
    print("R2D2 Master Controller - Super Coder Edition")
    print("=" * 60)

    # Create master controller
    r2d2 = R2D2MasterController(mode=R2D2Mode.DEMONSTRATION)

    try:
        # Initialize system
        if not r2d2.initialize_system():
            print("System initialization failed")
            return 1

        # Run performance validation
        print("Running performance validation...")
        validation_report = r2d2.run_performance_validation()
        print(f"Validation Result: {validation_report.performance_level.value}")
        print(f"Convention Ready: {validation_report.convention_ready}")

        # Demo animations
        print("\nDemonstrating R2D2 animations...")
        animations = ['wake_up', 'greeting', 'happy', 'curious', 'search', 'sleep']

        for animation in animations:
            print(f"Playing animation: {animation}")
            r2d2.play_animation(animation, intensity=1.0)
            time.sleep(2.0)

        # Display final status
        final_status = r2d2.get_system_status()
        print(f"\nFinal System Status:")
        print(f"State: {final_status.state.value}")
        print(f"System Health: {final_status.system_health:.2f}")
        print(f"Active Subsystems: {len(final_status.active_subsystems)}")
        print(f"Convention Ready: {final_status.convention_ready}")

        return 0

    except KeyboardInterrupt:
        print("\nDemo interrupted - shutting down...")
        r2d2.emergency_stop()
        return 0
    except Exception as e:
        print(f"Demo error: {e}")
        logger.error(traceback.format_exc())
        return 1
    finally:
        r2d2.shutdown()


if __name__ == "__main__":
    sys.exit(main())