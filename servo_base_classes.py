#!/usr/bin/env python3
"""
R2D2 Servo System Base Classes
Shared Foundation for All Servo Components

This module provides common base classes, data structures, and utilities
shared across all R2D2 servo system components to eliminate code duplication
and provide a unified interface.
"""

import time
import logging
import threading
import uuid
from abc import ABC, abstractmethod
from typing import Dict, List, Tuple, Optional, Any, Callable
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path

# Configure logging
logger = logging.getLogger(__name__)

# ============================================================================
# COMMON ENUMERATIONS
# ============================================================================

class MotionType(Enum):
    """Types of servo motion with advanced easing"""
    LINEAR = "linear"
    SMOOTH = "smooth"
    EASE_IN = "ease_in"
    EASE_OUT = "ease_out"
    EASE_IN_OUT = "ease_in_out"
    BOUNCE = "bounce"
    ELASTIC = "elastic"
    CHOREOGRAPHED = "choreographed"

class ServoCommandType(Enum):
    """Servo command types"""
    POSITION = "position"
    SPEED = "speed"
    ACCELERATION = "acceleration"
    HOME = "home"
    STOP = "stop"
    SEQUENCE = "sequence"
    EMERGENCY_STOP = "emergency_stop"

class SystemHealthStatus(Enum):
    """System health status levels"""
    EXCELLENT = "excellent"
    GOOD = "good"
    WARNING = "warning"
    CRITICAL = "critical"
    FAILED = "failed"

class ConnectionStatus(Enum):
    """Connection status with Maestro hardware"""
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    ERROR = "error"
    RECONNECTING = "reconnecting"

class ServoType(Enum):
    """Servo function types for R2D2 animatronics"""
    PRIMARY = "primary"        # Main character movement (dome, head)
    UTILITY = "utility"        # Utility arms, periscope, radar
    PANEL = "panel"           # Access panels and doors
    DISPLAY = "display"       # Logic displays and visual elements
    SPECIAL = "special"       # Holoprojectors and unique features
    LIGHTING = "lighting"     # LED controllers and lighting
    AUDIO = "audio"          # Sound triggers and audio control
    DRIVE = "drive"          # Motor control and locomotion
    EXPANSION = "expansion"   # Future expansion and custom features

class ServoRange(Enum):
    """Servo movement range classifications"""
    BINARY = "binary"         # Simple open/close (panels, doors)
    LIMITED = "limited"       # Restricted range (head tilt, displays)
    FULL = "full"            # Full 180-degree range (dome rotation)
    CONTINUOUS = "continuous" # Continuous rotation (wheels, some motors)

class SafetyLevel(Enum):
    """Safety operation levels"""
    DEVELOPMENT = "development"    # Full range, reduced safety
    TESTING = "testing"           # Moderate safety restrictions
    PRODUCTION = "production"     # Full safety enforcement
    DEMONSTRATION = "demonstration" # Conservative safe operation
    EMERGENCY = "emergency"       # Minimum safe operation only

# ============================================================================
# SHARED DATA STRUCTURES
# ============================================================================

@dataclass
class ServoCommand:
    """Individual servo command with timing and motion parameters"""
    channel: int
    command_type: ServoCommandType
    value: float
    duration: float = 0.0
    motion_type: MotionType = MotionType.LINEAR
    delay: float = 0.0
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    timestamp: float = field(default_factory=time.time)

@dataclass
class ServoSequence:
    """Sequence of servo commands with choreography"""
    name: str
    commands: List[ServoCommand]
    loop: bool = False
    loop_count: int = 1
    description: str = ""
    author: str = "System"
    created: float = field(default_factory=time.time)
    duration: float = 0.0
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])

    def __post_init__(self):
        """Calculate total sequence duration"""
        if self.commands:
            self.duration = max(cmd.delay + cmd.duration for cmd in self.commands)

@dataclass
class ServoLimits:
    """Safety and operational limits for servo channels"""
    min_position: int = 992     # Minimum pulse width (μs)
    max_position: int = 2000    # Maximum pulse width (μs)
    max_speed: int = 100        # Maximum speed (0-255)
    max_acceleration: int = 50  # Maximum acceleration (0-255)
    safe_min: int = 1200       # Safe minimum position
    safe_max: int = 1800       # Safe maximum position
    emergency_stop_speed: int = 255  # Speed for emergency stops

@dataclass
class ServoConfiguration:
    """Complete servo configuration with limits and behavior"""
    channel: int
    name: str = "Unnamed Servo"
    servo_type: ServoType = ServoType.UTILITY
    servo_range: ServoRange = ServoRange.LIMITED
    limits: ServoLimits = field(default_factory=ServoLimits)
    home_position: int = 1500   # Home position (μs)
    default_speed: int = 50     # Default movement speed
    default_acceleration: int = 20  # Default acceleration
    enabled: bool = True
    inverted: bool = False
    safety_level: SafetyLevel = SafetyLevel.PRODUCTION

@dataclass
class SafetyViolation:
    """Safety violation record"""
    timestamp: float
    violation_type: str
    channel: int
    severity: str
    description: str
    action_taken: str
    resolved: bool = False

@dataclass
class PerformanceMetrics:
    """Performance metrics for servo operations"""
    command_latency_ms: float
    position_accuracy: float
    movement_smoothness: float
    sequence_timing_precision: float
    hardware_response_time: float
    total_commands_processed: int
    success_rate: float

@dataclass
class DiagnosticData:
    """System diagnostic data point"""
    timestamp: float
    cpu_usage: float
    memory_usage: float
    temperature: float
    connection_status: ConnectionStatus
    active_servos: int
    sequence_count: int
    error_count: int
    last_command_latency: float

# ============================================================================
# BASE CLASSES
# ============================================================================

class ServoControllerBase(ABC):
    """Abstract base class for all servo controllers"""

    def __init__(self, name: str = "ServoController"):
        self.name = name
        self.is_connected = False
        self.last_error = None
        self.servo_configs: Dict[int, ServoConfiguration] = {}
        self.performance_metrics = PerformanceMetrics(0, 0, 0, 0, 0, 0, 0.0)
        self._lock = threading.Lock()

    @abstractmethod
    def connect(self) -> bool:
        """Connect to servo hardware"""
        pass

    @abstractmethod
    def disconnect(self) -> bool:
        """Disconnect from servo hardware"""
        pass

    @abstractmethod
    def move_servo(self, channel: int, position: int, duration: float = 0) -> bool:
        """Move servo to position"""
        pass

    @abstractmethod
    def get_servo_status(self, channel: int) -> Dict[str, Any]:
        """Get current servo status"""
        pass

    @abstractmethod
    def emergency_stop(self) -> bool:
        """Emergency stop all servos"""
        pass

class SafetySystemBase(ABC):
    """Abstract base class for safety systems"""

    def __init__(self):
        self.safety_level = SafetyLevel.PRODUCTION
        self.violations: List[SafetyViolation] = []
        self.safety_callbacks: List[Callable] = []
        self._monitoring = False

    @abstractmethod
    def validate_command(self, command: ServoCommand) -> bool:
        """Validate servo command against safety rules"""
        pass

    @abstractmethod
    def monitor_servo(self, channel: int, position: int) -> bool:
        """Monitor servo for safety violations"""
        pass

    def add_safety_callback(self, callback: Callable):
        """Add callback for safety violations"""
        self.safety_callbacks.append(callback)

    def _trigger_safety_violation(self, violation: SafetyViolation):
        """Trigger safety violation callbacks"""
        self.violations.append(violation)
        for callback in self.safety_callbacks:
            try:
                callback(violation)
            except Exception as e:
                logger.error(f"Safety callback error: {e}")

class ConfigurationManagerBase(ABC):
    """Abstract base class for configuration management"""

    def __init__(self, config_dir: str):
        self.config_dir = Path(config_dir)
        self.config_dir.mkdir(exist_ok=True)
        self.active_config = "default"

    @abstractmethod
    def save_configuration(self, name: str, config: Dict[str, Any]) -> bool:
        """Save configuration to file"""
        pass

    @abstractmethod
    def load_configuration(self, name: str) -> Optional[Dict[str, Any]]:
        """Load configuration from file"""
        pass

    @abstractmethod
    def validate_configuration(self, config: Dict[str, Any]) -> List[str]:
        """Validate configuration and return any errors"""
        pass

class WebSocketHandlerBase(ABC):
    """Abstract base class for WebSocket communication"""

    def __init__(self, port: int = 8767):
        self.port = port
        self.clients: set = set()
        self.server = None
        self._running = False

    @abstractmethod
    async def handle_client(self, websocket, path):
        """Handle new WebSocket client connection"""
        pass

    @abstractmethod
    async def handle_message(self, websocket, message):
        """Handle incoming WebSocket message"""
        pass

    @abstractmethod
    async def broadcast_status(self, status: Dict[str, Any]):
        """Broadcast status to all connected clients"""
        pass

class SequenceEngineBase(ABC):
    """Abstract base class for sequence execution engines"""

    def __init__(self):
        self.active_sequences: Dict[str, ServoSequence] = {}
        self.sequence_callbacks: List[Callable] = []

    @abstractmethod
    async def execute_sequence(self, sequence: ServoSequence) -> bool:
        """Execute a servo sequence"""
        pass

    @abstractmethod
    def stop_sequence(self, sequence_id: str) -> bool:
        """Stop a running sequence"""
        pass

    @abstractmethod
    def get_sequence_status(self, sequence_id: str) -> Dict[str, Any]:
        """Get status of a sequence"""
        pass

# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def validate_servo_position(position: int, limits: ServoLimits) -> bool:
    """Validate servo position against limits"""
    return limits.min_position <= position <= limits.max_position

def calculate_motion_trajectory(start: int, end: int, duration: float,
                              motion_type: MotionType) -> List[Tuple[float, int]]:
    """Calculate motion trajectory points for smooth movement"""
    if duration <= 0:
        return [(0, end)]

    steps = max(10, int(duration * 20))  # 20 steps per second
    trajectory = []

    for i in range(steps + 1):
        t = i / steps

        if motion_type == MotionType.LINEAR:
            progress = t
        elif motion_type == MotionType.EASE_IN:
            progress = t * t
        elif motion_type == MotionType.EASE_OUT:
            progress = 1 - (1 - t) * (1 - t)
        elif motion_type == MotionType.EASE_IN_OUT:
            progress = 3 * t * t - 2 * t * t * t
        elif motion_type == MotionType.BOUNCE:
            if t < 0.5:
                progress = 2 * t * t
            else:
                progress = 1 - 2 * (1 - t) * (1 - t)
        else:
            progress = t  # Default to linear

        position = int(start + (end - start) * progress)
        timestamp = t * duration
        trajectory.append((timestamp, position))

    return trajectory

def create_default_servo_config(channel: int, name: str = None) -> ServoConfiguration:
    """Create default servo configuration for a channel"""
    return ServoConfiguration(
        channel=channel,
        name=name or f"Servo_{channel}",
        servo_type=ServoType.UTILITY,
        servo_range=ServoRange.LIMITED,
        limits=ServoLimits(),
        home_position=1500,
        default_speed=50,
        default_acceleration=20,
        enabled=True,
        inverted=False,
        safety_level=SafetyLevel.PRODUCTION
    )

def apply_safety_constraints(position: int, config: ServoConfiguration) -> int:
    """Apply safety constraints to servo position"""
    limits = config.limits

    if config.safety_level == SafetyLevel.PRODUCTION:
        # Use safe limits in production
        min_pos = max(limits.min_position, limits.safe_min)
        max_pos = min(limits.max_position, limits.safe_max)
    else:
        # Use full limits in development/testing
        min_pos = limits.min_position
        max_pos = limits.max_position

    return max(min_pos, min(max_pos, position))

# ============================================================================
# SHARED CONSTANTS
# ============================================================================

# Standard R2D2 servo channel assignments
R2D2_SERVO_CHANNELS = {
    'DOME_ROTATION': 0,
    'HEAD_TILT': 1,
    'PERISCOPE': 2,
    'RADAR_EYE': 3,
    'FRONT_ARM': 4,
    'REAR_ARM': 5,
    'UTILITY_ARM_1': 6,
    'UTILITY_ARM_2': 7,
    'DOOR_PANEL_1': 8,
    'DOOR_PANEL_2': 9,
    'DOOR_PANEL_3': 10,
    'HOLOPROJECTOR': 11,
    'LOGIC_DISPLAY_1': 12,
    'LOGIC_DISPLAY_2': 13,
    'AUX_1': 14,
    'AUX_2': 15
}

# Default safety limits
DEFAULT_SAFETY_LIMITS = ServoLimits(
    min_position=992,
    max_position=2000,
    max_speed=100,
    max_acceleration=50,
    safe_min=1200,
    safe_max=1800,
    emergency_stop_speed=255
)

# Performance thresholds
PERFORMANCE_THRESHOLDS = {
    'max_latency_ms': 50,
    'min_accuracy': 0.95,
    'min_smoothness': 0.90,
    'min_timing_precision': 0.98,
    'max_response_time_ms': 100
}