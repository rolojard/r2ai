#!/usr/bin/env python3
"""
R2D2 Maestro Script Engine
Advanced Script Management and Motion Interpolation for Pololu Maestro Controllers

This module provides comprehensive script management capabilities including:
- Maestro native script compilation and execution
- Smooth motion interpolation and trajectory planning
- Complex multi-servo choreography
- Real-time script modification and blending
- Professional animation timeline management

Author: Imagineer Specialist
Version: 1.0.0
Date: 2024-09-22
"""

import time
import logging
import threading
import json
import math
import struct
from typing import Dict, List, Tuple, Optional, Union, Callable
from dataclasses import dataclass, field, asdict
from enum import Enum
from pathlib import Path
import numpy as np
from scipy.interpolate import interp1d, CubicSpline
import queue

logger = logging.getLogger(__name__)

class MaestroScriptCommand(Enum):
    """Maestro Script Commands"""
    # Stack and flow control
    LITERAL = 0x30
    RETURN = 0x50
    JUMP = 0x28
    JUMP_Z = 0x29
    JUMP_NZ = 0x2A
    CALL = 0x2B

    # Servo control
    SERVO = 0x2C
    SPEED = 0x2D
    ACCELERATION = 0x2E
    GET_POSITION = 0x2F

    # Logic and math
    EQUALS = 0x31
    NOT_EQUALS = 0x32
    LESS_THAN = 0x33
    GREATER_THAN = 0x34
    AND = 0x35
    OR = 0x36
    NOT = 0x37
    PLUS = 0x38
    MINUS = 0x39
    TIMES = 0x3A
    DIVIDE = 0x3B

    # System commands
    DELAY = 0x40
    GET_MS = 0x41
    QUIT = 0x4F

class InterpolationType(Enum):
    """Motion interpolation types"""
    LINEAR = "linear"
    CUBIC = "cubic"
    BEZIER = "bezier"
    EASE_IN_OUT = "ease_in_out"
    BOUNCE = "bounce"
    ELASTIC = "elastic"

@dataclass
class KeyFrame:
    """Animation keyframe definition"""
    time: float
    channel: int
    position: int
    speed: Optional[int] = None
    acceleration: Optional[int] = None
    interpolation: InterpolationType = InterpolationType.CUBIC

@dataclass
class AnimationTrack:
    """Animation track for a single servo"""
    channel: int
    name: str
    keyframes: List[KeyFrame] = field(default_factory=list)
    enabled: bool = True
    loop: bool = False
    speed_multiplier: float = 1.0

@dataclass
class AnimationSequence:
    """Complete animation sequence with multiple tracks"""
    name: str
    description: str
    duration: float
    tracks: List[AnimationTrack] = field(default_factory=list)
    fps: int = 60
    loop: bool = False
    blend_mode: str = "replace"

@dataclass
class MaestroScript:
    """Compiled Maestro script with metadata"""
    name: str
    description: str
    bytecode: bytes
    subroutines: Dict[str, int] = field(default_factory=dict)
    parameters: Dict[str, int] = field(default_factory=dict)
    estimated_duration: float = 0.0
    safety_checks: bool = True

class ScriptCompiler:
    """Compiles high-level animation descriptions into Maestro bytecode"""

    def __init__(self):
        self.subroutine_counter = 0
        self.label_counter = 0
        self.current_script = bytearray()

    def compile_animation_sequence(self, sequence: AnimationSequence) -> MaestroScript:
        """Compile animation sequence to Maestro script"""
        logger.info(f"🔧 Compiling animation sequence: {sequence.name}")

        self.current_script = bytearray()
        self.subroutine_counter = 0

        try:
            # Generate main script
            self._compile_sequence_main(sequence)

            # Create script object
            script = MaestroScript(
                name=sequence.name,
                description=sequence.description,
                bytecode=bytes(self.current_script),
                estimated_duration=sequence.duration
            )

            logger.info(f"✅ Compiled script: {len(script.bytecode)} bytes")
            return script

        except Exception as e:
            logger.error(f"Script compilation failed: {e}")
            raise

    def _compile_sequence_main(self, sequence: AnimationSequence):
        """Compile main sequence logic"""
        frame_duration_ms = int(1000 / sequence.fps)
        total_frames = int(sequence.duration * sequence.fps)

        # Initialize all servos to starting positions
        self._initialize_servo_positions(sequence)

        # Main animation loop
        for frame in range(total_frames):
            frame_time = frame / sequence.fps

            # Generate commands for this frame
            frame_commands = self._generate_frame_commands(sequence, frame_time)

            # Add frame commands to script
            for command in frame_commands:
                self.current_script.extend(command)

            # Frame delay
            self._add_delay(frame_duration_ms)

        # Loop if required
        if sequence.loop:
            self._add_jump_to_start()

        # End script
        self._add_quit()

    def _initialize_servo_positions(self, sequence: AnimationSequence):
        """Initialize servo positions at sequence start"""
        for track in sequence.tracks:
            if track.keyframes and track.enabled:
                first_keyframe = track.keyframes[0]
                self._add_servo_command(track.channel, first_keyframe.position)

                if first_keyframe.speed is not None:
                    self._add_speed_command(track.channel, first_keyframe.speed)

                if first_keyframe.acceleration is not None:
                    self._add_acceleration_command(track.channel, first_keyframe.acceleration)

    def _generate_frame_commands(self, sequence: AnimationSequence, frame_time: float) -> List[bytes]:
        """Generate servo commands for a specific frame"""
        commands = []

        for track in sequence.tracks:
            if not track.enabled:
                continue

            # Calculate interpolated position for this frame
            position = self._interpolate_position(track, frame_time)

            if position is not None:
                # Add servo position command
                command = self._create_servo_command(track.channel, position)
                commands.append(command)

        return commands

    def _interpolate_position(self, track: AnimationTrack, time: float) -> Optional[int]:
        """Interpolate servo position at given time using keyframes"""
        if not track.keyframes:
            return None

        # Adjust time for speed multiplier
        adjusted_time = time / track.speed_multiplier

        # Handle time beyond keyframes
        if adjusted_time <= track.keyframes[0].time:
            return track.keyframes[0].position

        if adjusted_time >= track.keyframes[-1].time:
            return track.keyframes[-1].position

        # Find surrounding keyframes
        prev_kf = None
        next_kf = None

        for i, keyframe in enumerate(track.keyframes):
            if keyframe.time <= adjusted_time:
                prev_kf = keyframe
                if i + 1 < len(track.keyframes):
                    next_kf = track.keyframes[i + 1]
                break

        if prev_kf is None or next_kf is None:
            return track.keyframes[-1].position

        # Interpolate between keyframes
        return self._interpolate_between_keyframes(prev_kf, next_kf, adjusted_time)

    def _interpolate_between_keyframes(self, kf1: KeyFrame, kf2: KeyFrame, time: float) -> int:
        """Interpolate position between two keyframes"""
        # Calculate interpolation factor (0.0 to 1.0)
        duration = kf2.time - kf1.time
        if duration <= 0:
            return kf1.position

        t = (time - kf1.time) / duration
        t = max(0.0, min(1.0, t))  # Clamp to [0, 1]

        # Apply interpolation type
        if kf2.interpolation == InterpolationType.LINEAR:
            factor = t
        elif kf2.interpolation == InterpolationType.CUBIC:
            factor = self._cubic_ease_in_out(t)
        elif kf2.interpolation == InterpolationType.EASE_IN_OUT:
            factor = self._ease_in_out(t)
        elif kf2.interpolation == InterpolationType.BOUNCE:
            factor = self._bounce_ease_out(t)
        elif kf2.interpolation == InterpolationType.ELASTIC:
            factor = self._elastic_ease_out(t)
        else:
            factor = t  # Default to linear

        # Interpolate position
        position_diff = kf2.position - kf1.position
        interpolated_position = kf1.position + int(position_diff * factor)

        return interpolated_position

    def _cubic_ease_in_out(self, t: float) -> float:
        """Cubic ease-in-out interpolation"""
        if t < 0.5:
            return 4 * t * t * t
        else:
            return 1 - pow(-2 * t + 2, 3) / 2

    def _ease_in_out(self, t: float) -> float:
        """Smooth ease-in-out interpolation"""
        return t * t * (3.0 - 2.0 * t)

    def _bounce_ease_out(self, t: float) -> float:
        """Bounce ease-out effect"""
        if t < 1 / 2.75:
            return 7.5625 * t * t
        elif t < 2 / 2.75:
            t -= 1.5 / 2.75
            return 7.5625 * t * t + 0.75
        elif t < 2.5 / 2.75:
            t -= 2.25 / 2.75
            return 7.5625 * t * t + 0.9375
        else:
            t -= 2.625 / 2.75
            return 7.5625 * t * t + 0.984375

    def _elastic_ease_out(self, t: float) -> float:
        """Elastic ease-out effect"""
        if t == 0 or t == 1:
            return t

        c4 = (2 * math.pi) / 3
        return pow(2, -10 * t) * math.sin((t * 10 - 0.75) * c4) + 1

    def _add_servo_command(self, channel: int, position: int):
        """Add servo position command to script"""
        command = self._create_servo_command(channel, position)
        self.current_script.extend(command)

    def _create_servo_command(self, channel: int, position: int) -> bytes:
        """Create servo position command bytes"""
        # Maestro servo command format
        return bytes([
            MaestroScriptCommand.LITERAL.value, channel,  # Channel
            MaestroScriptCommand.LITERAL.value, position & 0x7F,  # Position low
            MaestroScriptCommand.LITERAL.value, (position >> 7) & 0x7F,  # Position high
            MaestroScriptCommand.SERVO.value  # Servo command
        ])

    def _add_speed_command(self, channel: int, speed: int):
        """Add speed limit command"""
        self.current_script.extend([
            MaestroScriptCommand.LITERAL.value, channel,
            MaestroScriptCommand.LITERAL.value, speed & 0x7F,
            MaestroScriptCommand.LITERAL.value, (speed >> 7) & 0x7F,
            MaestroScriptCommand.SPEED.value
        ])

    def _add_acceleration_command(self, channel: int, acceleration: int):
        """Add acceleration limit command"""
        self.current_script.extend([
            MaestroScriptCommand.LITERAL.value, channel,
            MaestroScriptCommand.LITERAL.value, acceleration & 0x7F,
            MaestroScriptCommand.LITERAL.value, (acceleration >> 7) & 0x7F,
            MaestroScriptCommand.ACCELERATION.value
        ])

    def _add_delay(self, milliseconds: int):
        """Add delay command"""
        self.current_script.extend([
            MaestroScriptCommand.LITERAL.value, milliseconds & 0x7F,
            MaestroScriptCommand.LITERAL.value, (milliseconds >> 7) & 0x7F,
            MaestroScriptCommand.DELAY.value
        ])

    def _add_jump_to_start(self):
        """Add jump to start for looping"""
        self.current_script.extend([
            MaestroScriptCommand.LITERAL.value, 0,  # Jump to address 0
            MaestroScriptCommand.JUMP.value
        ])

    def _add_quit(self):
        """Add quit command to end script"""
        self.current_script.append(MaestroScriptCommand.QUIT.value)

class MotionPlanner:
    """Advanced motion planning and trajectory generation"""

    def __init__(self):
        self.trajectory_cache: Dict[str, np.ndarray] = {}

    def plan_smooth_motion(self, start_pos: int, end_pos: int, duration: float,
                          motion_type: str = "cubic") -> List[Tuple[float, int]]:
        """Plan smooth motion trajectory between two positions"""
        # Generate time points
        fps = 60
        num_points = int(duration * fps)
        time_points = np.linspace(0, duration, num_points)

        # Generate trajectory based on motion type
        if motion_type == "cubic":
            trajectory = self._cubic_trajectory(start_pos, end_pos, time_points)
        elif motion_type == "quintic":
            trajectory = self._quintic_trajectory(start_pos, end_pos, time_points)
        elif motion_type == "s_curve":
            trajectory = self._s_curve_trajectory(start_pos, end_pos, time_points)
        else:
            trajectory = self._linear_trajectory(start_pos, end_pos, time_points)

        # Return time-position pairs
        return list(zip(time_points, trajectory.astype(int)))

    def _cubic_trajectory(self, start: int, end: int, time_points: np.ndarray) -> np.ndarray:
        """Generate cubic polynomial trajectory"""
        t = time_points / time_points[-1]  # Normalize to [0, 1]

        # Cubic polynomial with zero velocity at endpoints
        trajectory = start + (end - start) * (3 * t**2 - 2 * t**3)
        return trajectory

    def _quintic_trajectory(self, start: int, end: int, time_points: np.ndarray) -> np.ndarray:
        """Generate quintic polynomial trajectory (smoother)"""
        t = time_points / time_points[-1]  # Normalize to [0, 1]

        # Quintic polynomial with zero velocity and acceleration at endpoints
        trajectory = start + (end - start) * (10 * t**3 - 15 * t**4 + 6 * t**5)
        return trajectory

    def _s_curve_trajectory(self, start: int, end: int, time_points: np.ndarray) -> np.ndarray:
        """Generate S-curve trajectory with acceleration limits"""
        t = time_points / time_points[-1]  # Normalize to [0, 1]

        # S-curve with smooth acceleration/deceleration
        def s_curve(x):
            if x < 0.5:
                return 2 * x**2
            else:
                return 1 - 2 * (1 - x)**2

        s_values = np.array([s_curve(ti) for ti in t])
        trajectory = start + (end - start) * s_values
        return trajectory

    def _linear_trajectory(self, start: int, end: int, time_points: np.ndarray) -> np.ndarray:
        """Generate linear trajectory"""
        t = time_points / time_points[-1]  # Normalize to [0, 1]
        trajectory = start + (end - start) * t
        return trajectory

    def plan_multi_servo_motion(self, servo_goals: Dict[int, int], duration: float) -> Dict[int, List[Tuple[float, int]]]:
        """Plan coordinated motion for multiple servos"""
        trajectories = {}

        for channel, end_position in servo_goals.items():
            # Assume current position is home position (6000 quarter-microseconds)
            start_position = 6000

            # Plan trajectory for this servo
            trajectory = self.plan_smooth_motion(
                start_position, end_position, duration, "quintic"
            )
            trajectories[channel] = trajectory

        return trajectories

class ScriptEngine:
    """Advanced script execution and management engine"""

    def __init__(self, maestro_controller):
        self.controller = maestro_controller
        self.compiler = ScriptCompiler()
        self.motion_planner = MotionPlanner()

        # Script management
        self.loaded_scripts: Dict[str, MaestroScript] = {}
        self.animation_sequences: Dict[str, AnimationSequence] = {}

        # Execution state
        self.current_script: Optional[str] = None
        self.script_thread: Optional[threading.Thread] = None
        self.execution_active = False
        self.script_queue = queue.Queue()

        # Real-time blending
        self.blend_active = False
        self.blend_sequences: List[str] = []
        self.blend_weights: List[float] = []

        logger.info("🎬 Script Engine initialized")

        # Initialize default sequences
        self._create_default_sequences()

        # Start execution thread
        self._start_execution_thread()

    def _create_default_sequences(self):
        """Create default R2D2 animation sequences"""
        # Smooth dome scan sequence
        dome_scan = AnimationSequence(
            name="dome_scan",
            description="Smooth dome scanning motion",
            duration=8.0,
            fps=60
        )

        # Create dome rotation track
        dome_track = AnimationTrack(channel=0, name="Dome Rotation")
        dome_track.keyframes = [
            KeyFrame(0.0, 0, 6000, interpolation=InterpolationType.CUBIC),
            KeyFrame(2.0, 0, 8000, interpolation=InterpolationType.CUBIC),
            KeyFrame(4.0, 0, 4000, interpolation=InterpolationType.CUBIC),
            KeyFrame(6.0, 0, 7000, interpolation=InterpolationType.CUBIC),
            KeyFrame(8.0, 0, 6000, interpolation=InterpolationType.CUBIC)
        ]
        dome_scan.tracks.append(dome_track)

        # Panel flutter sequence
        panel_flutter = AnimationSequence(
            name="panel_flutter",
            description="Excited panel flutter animation",
            duration=3.0,
            fps=30
        )

        # Create panel tracks
        for i, panel_name in enumerate(["Front", "Left", "Right", "Back"]):
            panel_track = AnimationTrack(channel=6+i, name=f"Panel {panel_name}")
            panel_track.keyframes = [
                KeyFrame(0.0, 6+i, 4000),
                KeyFrame(0.3, 6+i, 7000, interpolation=InterpolationType.BOUNCE),
                KeyFrame(0.6, 6+i, 4000),
                KeyFrame(1.0, 6+i, 7000, interpolation=InterpolationType.BOUNCE),
                KeyFrame(1.3, 6+i, 4000),
                KeyFrame(1.8, 6+i, 6500, interpolation=InterpolationType.ELASTIC),
                KeyFrame(2.5, 6+i, 4500),
                KeyFrame(3.0, 6+i, 4000)
            ]
            panel_flutter.tracks.append(panel_track)

        # Curiosity sequence
        curiosity = AnimationSequence(
            name="curiosity",
            description="Curious investigation with head tilt and periscope",
            duration=10.0,
            fps=60
        )

        # Head tilt track
        head_track = AnimationTrack(channel=1, name="Head Tilt")
        head_track.keyframes = [
            KeyFrame(0.0, 1, 6000),
            KeyFrame(1.5, 1, 7000, interpolation=InterpolationType.EASE_IN_OUT),
            KeyFrame(4.0, 1, 7000),
            KeyFrame(6.0, 1, 5000, interpolation=InterpolationType.EASE_IN_OUT),
            KeyFrame(8.5, 1, 5000),
            KeyFrame(10.0, 1, 6000, interpolation=InterpolationType.CUBIC)
        ]
        curiosity.tracks.append(head_track)

        # Periscope track
        periscope_track = AnimationTrack(channel=2, name="Periscope")
        periscope_track.keyframes = [
            KeyFrame(0.0, 2, 4000),
            KeyFrame(2.0, 2, 4000),
            KeyFrame(3.0, 2, 7500, interpolation=InterpolationType.CUBIC),
            KeyFrame(7.0, 2, 7500),
            KeyFrame(8.5, 2, 4000, interpolation=InterpolationType.CUBIC),
            KeyFrame(10.0, 2, 4000)
        ]
        curiosity.tracks.append(periscope_track)

        # Dome rotation for curiosity
        dome_curious_track = AnimationTrack(channel=0, name="Dome Rotation")
        dome_curious_track.keyframes = [
            KeyFrame(0.0, 0, 6000),
            KeyFrame(2.5, 0, 7500, interpolation=InterpolationType.CUBIC),
            KeyFrame(5.0, 0, 4500, interpolation=InterpolationType.CUBIC),
            KeyFrame(7.5, 0, 6500, interpolation=InterpolationType.CUBIC),
            KeyFrame(10.0, 0, 6000, interpolation=InterpolationType.CUBIC)
        ]
        curiosity.tracks.append(dome_curious_track)

        # Store sequences
        sequences = [dome_scan, panel_flutter, curiosity]
        for seq in sequences:
            self.animation_sequences[seq.name] = seq
            logger.info(f"  ✓ Created sequence: {seq.name}")

    def _start_execution_thread(self):
        """Start script execution thread"""
        self.execution_active = True
        self.script_thread = threading.Thread(
            target=self._execution_loop,
            daemon=True,
            name="ScriptExecutor"
        )
        self.script_thread.start()

    def _execution_loop(self):
        """Main script execution loop"""
        while self.execution_active:
            try:
                if not self.script_queue.empty():
                    script_name = self.script_queue.get(timeout=1.0)
                    self._execute_script_internal(script_name)
                else:
                    time.sleep(0.1)
            except queue.Empty:
                continue
            except Exception as e:
                logger.error(f"Script execution error: {e}")
                time.sleep(1.0)

    def compile_sequence(self, sequence_name: str) -> bool:
        """Compile animation sequence to Maestro script"""
        if sequence_name not in self.animation_sequences:
            logger.error(f"Unknown sequence: {sequence_name}")
            return False

        try:
            sequence = self.animation_sequences[sequence_name]
            script = self.compiler.compile_animation_sequence(sequence)
            self.loaded_scripts[sequence_name] = script

            logger.info(f"✅ Compiled sequence '{sequence_name}' to script")
            return True

        except Exception as e:
            logger.error(f"Failed to compile sequence '{sequence_name}': {e}")
            return False

    def execute_sequence(self, sequence_name: str) -> bool:
        """Execute animation sequence"""
        # Compile if not already compiled
        if sequence_name not in self.loaded_scripts:
            if not self.compile_sequence(sequence_name):
                return False

        # Queue for execution
        self.script_queue.put(sequence_name)
        logger.info(f"📋 Queued sequence for execution: {sequence_name}")
        return True

    def _execute_script_internal(self, script_name: str):
        """Internal script execution"""
        if script_name not in self.loaded_scripts:
            logger.error(f"Script not loaded: {script_name}")
            return

        script = self.loaded_scripts[script_name]
        sequence = self.animation_sequences[script_name]

        logger.info(f"🎬 Executing script: {script_name}")

        try:
            # Execute the sequence using real-time interpolation
            self._execute_sequence_realtime(sequence)

            logger.info(f"✅ Script execution completed: {script_name}")

        except Exception as e:
            logger.error(f"Script execution failed: {e}")

    def _execute_sequence_realtime(self, sequence: AnimationSequence):
        """Execute sequence with real-time interpolation"""
        start_time = time.time()
        frame_duration = 1.0 / sequence.fps

        while True:
            current_time = time.time() - start_time

            # Check if sequence is complete
            if current_time >= sequence.duration:
                if sequence.loop:
                    start_time = time.time()  # Reset for loop
                    current_time = 0
                else:
                    break

            # Calculate positions for all tracks at current time
            for track in sequence.tracks:
                if not track.enabled:
                    continue

                position = self._interpolate_track_position(track, current_time)
                if position is not None and self.controller:
                    self.controller.set_servo_position(track.channel, position, validate=True)

            # Wait for next frame
            next_frame_time = start_time + ((int(current_time / frame_duration) + 1) * frame_duration)
            sleep_time = next_frame_time - time.time()
            if sleep_time > 0:
                time.sleep(sleep_time)

    def _interpolate_track_position(self, track: AnimationTrack, time: float) -> Optional[int]:
        """Interpolate track position at given time"""
        if not track.keyframes:
            return None

        # Adjust time for speed multiplier
        adjusted_time = time / track.speed_multiplier

        # Handle edge cases
        if adjusted_time <= track.keyframes[0].time:
            return track.keyframes[0].position

        if adjusted_time >= track.keyframes[-1].time:
            return track.keyframes[-1].position

        # Find surrounding keyframes
        for i in range(len(track.keyframes) - 1):
            kf1 = track.keyframes[i]
            kf2 = track.keyframes[i + 1]

            if kf1.time <= adjusted_time <= kf2.time:
                return self.compiler._interpolate_between_keyframes(kf1, kf2, adjusted_time)

        return track.keyframes[-1].position

    def create_custom_sequence(self, name: str, description: str, keyframe_data: Dict) -> bool:
        """Create custom animation sequence from keyframe data"""
        try:
            sequence = AnimationSequence(
                name=name,
                description=description,
                duration=keyframe_data.get("duration", 5.0),
                fps=keyframe_data.get("fps", 60),
                loop=keyframe_data.get("loop", False)
            )

            # Create tracks from data
            for track_data in keyframe_data.get("tracks", []):
                track = AnimationTrack(
                    channel=track_data["channel"],
                    name=track_data["name"],
                    enabled=track_data.get("enabled", True),
                    speed_multiplier=track_data.get("speed_multiplier", 1.0)
                )

                # Create keyframes
                for kf_data in track_data.get("keyframes", []):
                    keyframe = KeyFrame(
                        time=kf_data["time"],
                        channel=track.channel,
                        position=kf_data["position"],
                        speed=kf_data.get("speed"),
                        acceleration=kf_data.get("acceleration"),
                        interpolation=InterpolationType(kf_data.get("interpolation", "cubic"))
                    )
                    track.keyframes.append(keyframe)

                sequence.tracks.append(track)

            # Store sequence
            self.animation_sequences[name] = sequence
            logger.info(f"✅ Created custom sequence: {name}")
            return True

        except Exception as e:
            logger.error(f"Failed to create custom sequence: {e}")
            return False

    def get_sequence_info(self, sequence_name: str) -> Optional[Dict]:
        """Get information about a sequence"""
        if sequence_name not in self.animation_sequences:
            return None

        sequence = self.animation_sequences[sequence_name]
        return {
            "name": sequence.name,
            "description": sequence.description,
            "duration": sequence.duration,
            "fps": sequence.fps,
            "loop": sequence.loop,
            "tracks": len(sequence.tracks),
            "compiled": sequence_name in self.loaded_scripts
        }

    def list_sequences(self) -> List[str]:
        """List available sequences"""
        return list(self.animation_sequences.keys())

    def stop_execution(self):
        """Stop script execution"""
        logger.info("🛑 Stopping script execution...")

        # Clear queue
        while not self.script_queue.empty():
            try:
                self.script_queue.get_nowait()
            except queue.Empty:
                break

        # Emergency stop controller
        if self.controller:
            self.controller.emergency_stop()

    def shutdown(self):
        """Shutdown script engine"""
        logger.info("🔄 Shutting down script engine...")

        self.execution_active = False
        self.stop_execution()

        # Wait for thread to finish
        if self.script_thread and self.script_thread.is_alive():
            self.script_thread.join(timeout=2.0)

        logger.info("✅ Script engine shutdown complete")

# Demo function
def demo_script_engine():
    """Demo the script engine capabilities"""
    logger.info("🎬 Starting Script Engine Demo...")

    # This would normally use a real controller
    from pololu_maestro_controller import PololuMaestroController
    controller = PololuMaestroController(simulation_mode=True)

    # Create script engine
    engine = ScriptEngine(controller)

    try:
        # List available sequences
        sequences = engine.list_sequences()
        logger.info(f"Available sequences: {sequences}")

        # Demo each sequence
        for seq_name in ["dome_scan", "panel_flutter", "curiosity"]:
            logger.info(f"\n🎭 Demonstrating {seq_name}...")

            # Get sequence info
            info = engine.get_sequence_info(seq_name)
            logger.info(f"Duration: {info['duration']}s, Tracks: {info['tracks']}")

            # Execute sequence
            engine.execute_sequence(seq_name)

            # Wait for completion
            time.sleep(info['duration'] + 1)

        logger.info("\n✅ Script engine demo completed!")

    except KeyboardInterrupt:
        logger.info("Demo interrupted")
    except Exception as e:
        logger.error(f"Demo failed: {e}")
    finally:
        engine.shutdown()
        controller.shutdown()

if __name__ == "__main__":
    demo_script_engine()