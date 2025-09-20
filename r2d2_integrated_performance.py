#!/usr/bin/env python3
"""
R2-D2 Integrated Performance System
Disney-Level Animatronic Integration

This system integrates servo control, audio playback, and lighting effects
for synchronized R2-D2 performances that match Disney-level quality.

Features:
- Synchronized servo movement with audio cues
- Coordinated lighting effects
- Emotion-driven performance selection
- Canon-compliant Star Wars behaviors
- Real-time performance monitoring
"""

import time
import threading
import logging
import random
import json
from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path

# Import our servo control system
from r2d2_servo_simple import R2D2ServoControllerSimple, R2D2Component, R2D2Choreographer

# Audio system imports
try:
    import pygame
    AUDIO_AVAILABLE = True
except ImportError:
    AUDIO_AVAILABLE = False
    logging.warning("Pygame not available - audio disabled")

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class R2D2Emotion(Enum):
    """R2-D2 emotional states for performance selection"""
    HAPPY = "happy"
    EXCITED = "excited"
    CURIOUS = "curious"
    ALERT = "alert"
    FRUSTRATED = "frustrated"
    SAD = "sad"
    PLAYFUL = "playful"
    SURPRISED = "surprised"
    SARCASTIC = "sarcastic"
    STUBBORN = "stubborn"
    SCANNING = "scanning"
    MAINTENANCE = "maintenance"

class LightingZone(Enum):
    """R2-D2 lighting zones for coordinated effects"""
    DOME_FRONT = "dome_front"
    DOME_REAR = "dome_rear"
    BODY_FRONT = "body_front"
    BODY_REAR = "body_rear"
    UTILITY_ARMS = "utility_arms"
    DATA_PANEL = "data_panel"
    HOLOPROJECTOR = "holoprojector"

@dataclass
class PerformanceEvent:
    """Defines a synchronized performance event"""
    timestamp: float
    servo_actions: Dict[R2D2Component, float] = field(default_factory=dict)
    audio_file: Optional[str] = None
    lighting_effects: Dict[LightingZone, Dict] = field(default_factory=dict)
    duration: float = 1.0

@dataclass
class PerformanceSequence:
    """Complete performance sequence with all integration"""
    name: str
    emotion: R2D2Emotion
    events: List[PerformanceEvent] = field(default_factory=list)
    total_duration: float = 0.0
    priority: int = 1

class R2D2AudioController:
    """Audio playback controller for R2-D2 sounds"""

    def __init__(self, sound_directory: str = "/home/rolo/r2ai/sounds"):
        self.sound_directory = Path(sound_directory)
        self.current_channel = None
        self.is_initialized = False

        if AUDIO_AVAILABLE:
            self._initialize_audio()

    def _initialize_audio(self):
        """Initialize pygame audio system"""
        try:
            pygame.mixer.init(frequency=22050, size=-16, channels=2, buffer=512)
            self.is_initialized = True
            logger.info("Audio system initialized successfully")
        except Exception as e:
            logger.error(f"Audio initialization failed: {e}")
            self.is_initialized = False

    def play_sound(self, sound_file: str, volume: float = 1.0) -> bool:
        """
        Play a sound file

        Args:
            sound_file: Name of sound file (with or without extension)
            volume: Playback volume (0.0 to 1.0)

        Returns:
            True if sound played successfully
        """
        if not self.is_initialized:
            logger.info(f"[AUDIO SIM] Playing: {sound_file} at volume {volume:.1f}")
            return True

        try:
            # Try different extensions
            sound_path = None
            for ext in ['.wav', '.mp3', '.ogg']:
                test_path = self.sound_directory / f"{sound_file}{ext}"
                if test_path.exists():
                    sound_path = test_path
                    break

                # Try without adding extension (file might already have it)
                test_path = self.sound_directory / sound_file
                if test_path.exists():
                    sound_path = test_path
                    break

            if sound_path and sound_path.exists():
                sound = pygame.mixer.Sound(str(sound_path))
                sound.set_volume(volume)
                self.current_channel = sound.play()
                logger.info(f"Playing: {sound_path.name}")
                return True
            else:
                logger.warning(f"Sound file not found: {sound_file}")
                logger.info(f"[AUDIO SIM] Playing: {sound_file}")
                return True

        except Exception as e:
            logger.error(f"Audio playback failed: {e}")
            return False

    def stop_current_sound(self):
        """Stop currently playing sound"""
        if self.current_channel and self.current_channel.get_busy():
            self.current_channel.stop()

    def is_playing(self) -> bool:
        """Check if audio is currently playing"""
        if not self.is_initialized:
            return False
        return self.current_channel and self.current_channel.get_busy()

class R2D2LightingController:
    """Lighting effects controller for R2-D2"""

    def __init__(self, simulation_mode: bool = True):
        self.simulation_mode = simulation_mode
        self.current_effects: Dict[LightingZone, Dict] = {}

    def set_lighting(self, zone: LightingZone, effect: Dict):
        """
        Set lighting effect for a zone

        Args:
            zone: Lighting zone to control
            effect: Effect parameters (color, brightness, pattern, etc.)
        """
        self.current_effects[zone] = effect

        if self.simulation_mode:
            logger.info(f"[LIGHTING] {zone.value}: {effect}")
        else:
            # This is where real lighting control would go
            # GPIO or I2C LED controller integration
            pass

    def clear_all_lighting(self):
        """Turn off all lighting effects"""
        for zone in LightingZone:
            self.set_lighting(zone, {"pattern": "off", "brightness": 0})

    def strobe_effect(self, zones: List[LightingZone], color: str = "blue", duration: float = 1.0):
        """Create strobe effect on specified zones"""
        for zone in zones:
            effect = {
                "pattern": "strobe",
                "color": color,
                "frequency": 5.0,
                "duration": duration
            }
            self.set_lighting(zone, effect)

    def pulse_effect(self, zones: List[LightingZone], color: str = "white", duration: float = 2.0):
        """Create pulse effect on specified zones"""
        for zone in zones:
            effect = {
                "pattern": "pulse",
                "color": color,
                "frequency": 1.0,
                "duration": duration
            }
            self.set_lighting(zone, effect)

class R2D2IntegratedPerformer:
    """Main integrated performance controller for R2-D2"""

    def __init__(self, simulation_mode: bool = True):
        self.simulation_mode = simulation_mode

        # Initialize subsystems
        self.servo_controller = R2D2ServoControllerSimple(simulation_mode=simulation_mode)
        self.choreographer = R2D2Choreographer(self.servo_controller)
        self.audio_controller = R2D2AudioController()
        self.lighting_controller = R2D2LightingController(simulation_mode=simulation_mode)

        # Performance state
        self.current_performance = None
        self.performance_thread = None
        self.is_performing = False

        # Create performance library
        self.performances = {}
        self._create_performance_library()

        logger.info("R2-D2 Integrated Performance System initialized")

    def _create_performance_library(self):
        """Create library of integrated performances"""

        # Happy/Excited Performance
        happy_performance = PerformanceSequence(
            name="happy_greeting",
            emotion=R2D2Emotion.HAPPY,
            total_duration=5.0
        )

        # Event 1: Initial greeting sound with dome turn
        happy_performance.events.append(PerformanceEvent(
            timestamp=0.0,
            servo_actions={R2D2Component.DOME_ROTATION: 30},
            audio_file="r2d2_happy_greeting",
            lighting_effects={
                LightingZone.DOME_FRONT: {"pattern": "pulse", "color": "blue", "brightness": 0.8}
            },
            duration=1.5
        ))

        # Event 2: Panel flutter with excited sounds
        happy_performance.events.append(PerformanceEvent(
            timestamp=1.5,
            servo_actions={
                R2D2Component.DOME_PANEL_1: 90,
                R2D2Component.DOME_PANEL_2: 90
            },
            audio_file="r2d2_excited_chirp",
            lighting_effects={
                LightingZone.DOME_FRONT: {"pattern": "strobe", "color": "white", "brightness": 1.0}
            },
            duration=1.0
        ))

        # Event 3: Arm extension with happy beeps
        happy_performance.events.append(PerformanceEvent(
            timestamp=2.5,
            servo_actions={
                R2D2Component.UTILITY_ARM_1: 120,
                R2D2Component.UTILITY_ARM_2: 120
            },
            audio_file="r2d2_happy_beep",
            lighting_effects={
                LightingZone.UTILITY_ARMS: {"pattern": "pulse", "color": "green", "brightness": 0.9}
            },
            duration=1.5
        ))

        # Event 4: Return to neutral with content sound
        happy_performance.events.append(PerformanceEvent(
            timestamp=4.0,
            servo_actions={
                R2D2Component.DOME_ROTATION: 0,
                R2D2Component.DOME_PANEL_1: 0,
                R2D2Component.DOME_PANEL_2: 0,
                R2D2Component.UTILITY_ARM_1: 0,
                R2D2Component.UTILITY_ARM_2: 0
            },
            audio_file="r2d2_content_whistle",
            lighting_effects={},
            duration=1.0
        ))

        # Alert/Scanning Performance
        alert_performance = PerformanceSequence(
            name="security_alert",
            emotion=R2D2Emotion.ALERT,
            total_duration=8.0
        )

        # Event 1: Alert sound with head turn
        alert_performance.events.append(PerformanceEvent(
            timestamp=0.0,
            servo_actions={R2D2Component.PERISCOPE: 180},
            audio_file="r2d2_alert_warning",
            lighting_effects={
                LightingZone.DOME_FRONT: {"pattern": "strobe", "color": "red", "brightness": 1.0},
                LightingZone.DOME_REAR: {"pattern": "strobe", "color": "red", "brightness": 1.0}
            },
            duration=2.0
        ))

        # Event 2: 360-degree scan
        for angle in [90, 180, 270, 360]:
            alert_performance.events.append(PerformanceEvent(
                timestamp=2.0 + (angle / 90 - 1) * 1.5,
                servo_actions={R2D2Component.DOME_ROTATION: angle},
                audio_file="r2d2_scanning_beep" if angle % 180 == 0 else None,
                lighting_effects={
                    LightingZone.DOME_FRONT: {"pattern": "pulse", "color": "yellow", "brightness": 0.7}
                } if angle % 180 == 0 else {},
                duration=1.5
            ))

        # Event 3: Return to center with all-clear
        alert_performance.events.append(PerformanceEvent(
            timestamp=7.0,
            servo_actions={
                R2D2Component.DOME_ROTATION: 0,
                R2D2Component.PERISCOPE: 0
            },
            audio_file="r2d2_all_clear",
            lighting_effects={
                LightingZone.DOME_FRONT: {"pattern": "solid", "color": "green", "brightness": 0.5}
            },
            duration=1.0
        ))

        # Frustrated/Stubborn Performance
        frustrated_performance = PerformanceSequence(
            name="frustrated_response",
            emotion=R2D2Emotion.FRUSTRATED,
            total_duration=4.0
        )

        # Event 1: Frustrated sound with sharp head movement
        frustrated_performance.events.append(PerformanceEvent(
            timestamp=0.0,
            servo_actions={R2D2Component.DOME_ROTATION: -45},
            audio_file="r2d2_frustrated_grumble",
            lighting_effects={
                LightingZone.DOME_FRONT: {"pattern": "solid", "color": "red", "brightness": 0.6}
            },
            duration=1.0
        ))

        # Event 2: Panel slam (frustrated gesture)
        frustrated_performance.events.append(PerformanceEvent(
            timestamp=1.0,
            servo_actions={
                R2D2Component.DOME_PANEL_1: 120,
                R2D2Component.DOME_PANEL_3: 120
            },
            audio_file="r2d2_angry_beep",
            lighting_effects={},
            duration=0.5
        ))

        # Event 3: Quick panel close (dismissive)
        frustrated_performance.events.append(PerformanceEvent(
            timestamp=1.5,
            servo_actions={
                R2D2Component.DOME_PANEL_1: 0,
                R2D2Component.DOME_PANEL_3: 0
            },
            audio_file="r2d2_dismissive_whistle",
            lighting_effects={},
            duration=1.0
        ))

        # Event 4: Turn away (stubborn)
        frustrated_performance.events.append(PerformanceEvent(
            timestamp=2.5,
            servo_actions={R2D2Component.DOME_ROTATION: 90},
            audio_file="r2d2_stubborn_groan",
            lighting_effects={},
            duration=1.5
        ))

        # Store performances
        self.performances["happy_greeting"] = happy_performance
        self.performances["security_alert"] = alert_performance
        self.performances["frustrated_response"] = frustrated_performance

        logger.info(f"Created {len(self.performances)} integrated performances")

    def perform_emotion(self, emotion: R2D2Emotion) -> bool:
        """
        Perform a sequence based on emotional state

        Args:
            emotion: Desired emotional performance

        Returns:
            True if performance started successfully
        """
        # Find performance matching emotion
        matching_performances = [
            perf for perf in self.performances.values()
            if perf.emotion == emotion
        ]

        if not matching_performances:
            logger.warning(f"No performance found for emotion: {emotion}")
            return False

        # Select performance (random if multiple options)
        performance = random.choice(matching_performances)
        return self.perform_sequence(performance.name)

    def perform_sequence(self, sequence_name: str) -> bool:
        """
        Perform a named sequence

        Args:
            sequence_name: Name of sequence to perform

        Returns:
            True if performance started successfully
        """
        if sequence_name not in self.performances:
            logger.error(f"Unknown performance sequence: {sequence_name}")
            return False

        if self.is_performing:
            logger.warning("Performance already in progress")
            return False

        performance = self.performances[sequence_name]
        self.current_performance = performance

        logger.info(f"🎭 Starting integrated performance: {sequence_name}")

        # Start performance in separate thread
        self.performance_thread = threading.Thread(
            target=self._execute_performance,
            args=(performance,),
            daemon=True
        )
        self.performance_thread.start()

        return True

    def _execute_performance(self, performance: PerformanceSequence):
        """Execute a complete performance sequence"""
        self.is_performing = True
        start_time = time.time()

        try:
            for event in performance.events:
                # Wait for event time
                while time.time() - start_time < event.timestamp:
                    time.sleep(0.01)

                # Check for emergency stop
                if self.servo_controller.emergency_stopped:
                    logger.warning("Performance stopped due to emergency stop")
                    break

                # Execute servo actions
                if event.servo_actions:
                    self.servo_controller.move_multiple(event.servo_actions, smooth=True)

                # Execute audio
                if event.audio_file:
                    self.audio_controller.play_sound(event.audio_file)

                # Execute lighting effects
                for zone, effect in event.lighting_effects.items():
                    self.lighting_controller.set_lighting(zone, effect)

                logger.info(f"Executed event at {event.timestamp:.1f}s")

            # Wait for performance completion
            while time.time() - start_time < performance.total_duration:
                time.sleep(0.1)

            logger.info(f"✅ Performance '{performance.name}' completed successfully")

        except Exception as e:
            logger.error(f"Performance execution failed: {e}")
        finally:
            self.is_performing = False
            self.current_performance = None

    def stop_performance(self):
        """Stop current performance"""
        if self.is_performing:
            logger.info("Stopping current performance...")
            self.is_performing = False
            self.audio_controller.stop_current_sound()
            self.lighting_controller.clear_all_lighting()
            self.servo_controller.home_all_servos()

    def emergency_stop(self):
        """Emergency stop all systems"""
        logger.warning("🚨 EMERGENCY STOP - All systems halted")
        self.servo_controller.emergency_stop()
        self.stop_performance()

    def resume_operation(self):
        """Resume normal operation after emergency stop"""
        self.servo_controller.resume_operation()
        logger.info("✅ Emergency stop cleared - Ready for performances")

    def status_report(self):
        """Generate comprehensive status report"""
        logger.info("\n" + "="*60)
        logger.info("R2-D2 INTEGRATED PERFORMANCE STATUS")
        logger.info("="*60)

        logger.info(f"Performance Status: {'PERFORMING' if self.is_performing else 'READY'}")
        if self.current_performance:
            logger.info(f"Current Performance: {self.current_performance.name}")

        logger.info(f"Emergency Stop: {'ACTIVE' if self.servo_controller.emergency_stopped else 'CLEARED'}")
        logger.info(f"Audio System: {'READY' if self.audio_controller.is_initialized else 'SIMULATION'}")
        logger.info(f"Lighting System: {'SIMULATION' if self.lighting_controller.simulation_mode else 'HARDWARE'}")
        logger.info(f"Servo System: {'SIMULATION' if self.servo_controller.simulation_mode else 'HARDWARE'}")

        logger.info(f"\nAvailable Performances: {len(self.performances)}")
        for name, perf in self.performances.items():
            logger.info(f"  - {name} ({perf.emotion.value}, {perf.total_duration:.1f}s)")

        logger.info("="*60)

    def shutdown(self):
        """Safely shutdown all systems"""
        logger.info("Shutting down R2-D2 integrated performance system...")

        self.stop_performance()

        if self.performance_thread and self.performance_thread.is_alive():
            self.performance_thread.join(timeout=2.0)

        # Note: R2D2ServoControllerSimple doesn't have shutdown method
        # self.servo_controller.shutdown()
        self.lighting_controller.clear_all_lighting()

        logger.info("✅ Shutdown complete")

# Demonstration and testing functions
def demo_integrated_performance():
    """Comprehensive demonstration of integrated R2-D2 performance"""
    logger.info("🤖 Starting R2-D2 Integrated Performance Demo...")

    performer = R2D2IntegratedPerformer(simulation_mode=True)

    try:
        # Status report
        performer.status_report()

        # Demo 1: Happy greeting
        logger.info("\n--- Demo 1: Happy Greeting Performance ---")
        performer.perform_emotion(R2D2Emotion.HAPPY)
        time.sleep(6)  # Wait for completion

        # Demo 2: Security alert
        logger.info("\n--- Demo 2: Security Alert Performance ---")
        performer.perform_emotion(R2D2Emotion.ALERT)
        time.sleep(9)  # Wait for completion

        # Demo 3: Frustrated response
        logger.info("\n--- Demo 3: Frustrated Response Performance ---")
        performer.perform_emotion(R2D2Emotion.FRUSTRATED)
        time.sleep(5)  # Wait for completion

        # Demo 4: Emergency stop test
        logger.info("\n--- Demo 4: Emergency Stop Test ---")
        performer.perform_emotion(R2D2Emotion.HAPPY)
        time.sleep(1)
        performer.emergency_stop()
        time.sleep(2)
        performer.resume_operation()

        # Final status
        performer.status_report()

        logger.info("🎉 Integrated performance demo completed successfully!")

    except KeyboardInterrupt:
        logger.info("Demo interrupted by user")
    except Exception as e:
        logger.error(f"Demo failed: {e}")
    finally:
        performer.shutdown()

if __name__ == "__main__":
    demo_integrated_performance()