# R2D2 WCB Hardware Integration Architecture
## Complete Integration Plan for Meshed WCB Network

**Document Version:** 1.0
**Created:** 2025-10-04
**Target Hardware:** 3x WCB Boards (Meshed Network)
**Integration Platform:** NVIDIA Orin Nano
**Author:** Expert Project Manager

---

## Executive Summary

This document defines the complete integration architecture for your R2D2's WCB (Wireless Communication Board) meshed network system. The architecture enables the NVIDIA Orin Nano to coordinate all R2D2 subsystems through three interconnected WCB boards controlling servos, lights, sound, and peripherals.

**Critical Integration Insight:**
WCB1 operates in "Kyber Local" mode, bridging Kyber ↔ Maestro communication. The Orin can inject Maestro commands directly to WCB1 Serial 1, which execute ALONGSIDE Kyber control, enabling seamless AI-driven behaviors without disrupting manual RC control.

---

## 1. Hardware Architecture Overview

### 1.1 WCB Meshed Network Topology

```
┌─────────────────────────────────────────────────────────────────────┐
│                      NVIDIA ORIN NANO (AI Control Center)            │
│                                                                       │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │  R2D2 Disney Behavioral Intelligence Engine                  │   │
│  │  - 50+ Behavioral Sequences                                  │   │
│  │  - Personality State Machine                                 │   │
│  │  - Environmental Awareness (Vision/Audio)                    │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                              │                                        │
│                              ▼                                        │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │  WCB Orchestration Layer (NEW)                              │   │
│  │  - Serial Command Router                                     │   │
│  │  - Mood-to-Command Translator                                │   │
│  │  - Multi-WCB Synchronization                                 │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                              │                                        │
│                    USB Serial Connection                              │
└─────────────────────────────┼─────────────────────────────────────┘
                               │
                               ▼
        ┌──────────────────────────────────────────────────────┐
        │          WCB MESHED NETWORK (Wireless)               │
        │                                                      │
        │  ┌──────────────┐   ┌──────────────┐   ┌─────────────┐
        │  │    WCB1      │◄─►│    WCB2      │◄─►│    WCB3     │
        │  │   (Body)     │   │ (Dome Plate)  │   │   (Dome)    │
        │  │   Master     │   │              │   │             │
        │  └──────────────┘   └──────────────┘   └─────────────┘
        │                                                      │
        └──────────────────────────────────────────────────────┘
```

### 1.2 WCB1 - Body Master Controller

**Physical Location:** R2D2 Body
**Role:** Primary control hub, Kyber bridge, sound system interface

**Serial Port Assignments:**

| Port | Device | Communication | Direction | Purpose |
|------|--------|---------------|-----------|---------|
| **Serial 1** | Maestro (Body Servos) | Pololu Protocol | **Bidirectional** | Body servo control |
| **Serial 2** | Kyber (MarcDuino Port) | MarcDuino Protocol | Input | RC control input |
| **Serial 3** | Kyber (Maestro Port) | Pololu Protocol | **Bidirectional** | Kyber ↔ Maestro bridge |
| **Serial 4** | HCR Sound System | Custom | Output | Audio playback control |
| **Serial 5** | [Available] | - | - | Future expansion |

**Critical Feature: Kyber Local Mode**
- WCB1 bridges Kyber commands to Maestro (Serial 3 → Serial 1)
- Orin commands sent to Serial 1 execute ALONGSIDE Kyber control
- Enables AI behaviors without disrupting RC operation
- Priority handling: Emergency RC commands override AI

**Controlled Hardware:**
- Body servos (dome rotation, utility arms, panels)
- HCR sound system (beeps, whistles, vocalizations)
- Body lighting (through future expansion)

### 1.3 WCB2 - Dome Plate Controller

**Physical Location:** R2D2 Dome Plate (rotating platform)
**Role:** Dome-mounted peripherals and specialty devices

**Serial Port Assignments:**

| Port | Device | Communication | Direction | Purpose |
|------|--------|---------------|-----------|---------|
| **Serial 1** | [Available] | - | - | Future servo expansion |
| **Serial 2** | Periscope Controller | Custom | Output | Periscope lift mechanism |
| **Serial 3** | [Available] | - | - | Future expansion |
| **Serial 4** | [Available] | - | - | Future expansion |
| **Serial 5** | [Available] | - | - | Future expansion |

**Controlled Hardware:**
- Periscope lift mechanism (iconic R2D2 scanning device)
- Future: Dome sensors, additional servos

### 1.4 WCB3 - Dome Controller

**Physical Location:** R2D2 Dome
**Role:** Dome-specific lighting and logic displays

**Serial Port Assignments:**

| Port | Device | Communication | Direction | Purpose |
|------|--------|---------------|-----------|---------|
| **Serial 1** | Maestro (Dome Servos) | Pololu Protocol | Bidirectional | Dome servo control |
| **Serial 2** | [Available] | - | - | Future expansion |
| **Serial 3** | [Available] | - | - | Future expansion |
| **Serial 4** | PSI Lights | Custom | Output | Rear logic displays |
| **Serial 5** | Logic Lights | Custom | Output | Front logic displays |

**Controlled Hardware:**
- Dome servos (head tilt, radar eye, dome panels)
- PSI lights (rear logic displays - animated patterns)
- Front logic displays (LED matrix patterns)

---

## 2. Communication Protocols

### 2.1 Pololu Maestro Protocol (Servos)

The Maestro servo controllers use a compact binary protocol for position control:

**Set Target Command:**
```
Command: 0x84
Format: [0x84, Channel, Target_Low, Target_High]

Where:
- Channel: 0-11 (servo channel number)
- Target: 14-bit position value (0-16383)
  - Sent as two 7-bit bytes
  - Target_Low = position & 0x7F
  - Target_High = (position >> 7) & 0x7F
  - Position in quarter-microseconds (divide by 4 for µs)
```

**Example: Move servo 0 to 1500µs (center)**
```python
position = 1500 * 4  # Convert to quarter-microseconds = 6000
channel = 0
low_byte = position & 0x7F        # = 112 (0x70)
high_byte = (position >> 7) & 0x7F # = 46 (0x2E)

command = bytes([0x84, channel, low_byte, high_byte])
# Result: [0x84, 0x00, 0x70, 0x2E]
```

**Additional Maestro Commands:**
```
SET_SPEED:        0x87  [cmd, channel, speed_low, speed_high]
SET_ACCELERATION: 0x89  [cmd, channel, accel_low, accel_high]
GET_POSITION:     0x90  [cmd, channel] → returns 2 bytes
GET_MOVING_STATE: 0x93  [cmd] → returns 2 bytes (bitfield)
GET_ERRORS:       0xA1  [cmd] → returns 2 bytes (error flags)
GO_HOME:          0xA2  [cmd] → moves all servos to home
```

### 2.2 MarcDuino Protocol (Kyber Integration)

Kyber uses MarcDuino command protocol for droid control:

**Panel Commands:**
```
:OP00    Open all panels
:CL00    Close all panels
:OP01    Open dome panel 1
:CL01    Close dome panel 1
:OP02-10 Open specific panels
:ST00    Stop all panel servos
```

**Sound Commands:**
```
$87      Play random sound from bank 7
$+       Volume up
$-       Volume down
$c       Volume to 50%
$f       Volume to max
```

**Servo Animation Commands:**
```
:SE01    Start servo animation 1
:SE02    Start servo animation 2
:SE51    Magic Panel wave
```

**Kyber Bridge Behavior:**
- WCB1 Serial 2 receives Kyber/MarcDuino commands from RC
- WCB1 translates to Maestro protocol
- Commands forwarded to Serial 1 (Body Maestro)
- Orin can send same Maestro commands to Serial 1
- **Both sources coexist** - last command wins

### 2.3 WCB Serial Communication Format

WCB boards accept commands via serial at 9600 baud:

**Basic Command Structure:**
```
[Target_Board][Port][Command_Bytes]

Target_Board:
  - 0x01 = WCB1 (Body)
  - 0x02 = WCB2 (Dome Plate)
  - 0x03 = WCB3 (Dome)
  - 0xFF = Broadcast (all boards)

Port:
  - 0x01-0x05 = Serial 1-5

Command_Bytes:
  - Device-specific protocol data
```

**Example: Send Maestro command to WCB1 Serial 1**
```python
target_board = 0x01  # WCB1
port = 0x01          # Serial 1 (Maestro)
maestro_cmd = [0x84, 0x00, 0x70, 0x2E]  # Move servo 0

wcb_command = bytes([target_board, port] + maestro_cmd)
# Result: [0x01, 0x01, 0x84, 0x00, 0x70, 0x2E]
```

### 2.4 HCR Sound System Protocol

The HCR sound system on WCB1 Serial 4 uses custom commands:

**Sound Playback Commands:**
```
Play Sound:    [0x01, bank, sound_id]
Set Volume:    [0x02, volume]  (0-255)
Stop All:      [0x03]
Random Sound:  [0x04, bank]
```

**Sound Bank Organization:**
```
Bank 0: Beeps and chirps (happy sounds)
Bank 1: Whistles and alerts (attention sounds)
Bank 2: Grumbles and raspberries (attitude sounds)
Bank 3: Processing sounds (working/scanning)
Bank 4: Alarm sounds (danger/warning)
Bank 5: Musical sequences (entertainment)
Bank 6: Character-specific (Jedi, Sith reactions)
Bank 7: Random assortment (general use)
```

### 2.5 PSI and Logic Light Protocols (WCB3)

**PSI Light Commands (Serial 4):**
```
Pattern Select:  [0x01, pattern_id]
Set Color:       [0x02, r, g, b]
Set Brightness:  [0x03, brightness]
Animation Speed: [0x04, speed]
Random Mode:     [0x05]

Patterns:
  0 = Off
  1 = Normal (standard R2 pattern)
  2 = Alarm (rapid flashing)
  3 = Alert (slow pulse)
  4 = Rainbow cycle
  5 = Lightsaber clash
```

**Logic Light Commands (Serial 5):**
```
Display Pattern: [0x01, pattern_id]
Scroll Text:     [0x02, speed, "text"]
Set Brightness:  [0x03, brightness]
Color Mode:      [0x04, mode]  (0=red, 1=blue, 2=rainbow)
```

---

## 3. Behavioral Mood System Integration

### 3.1 27 Disney R2D2 Moods

The R2D2 behavioral intelligence system defines 27 distinct personality states that must map to coordinated WCB commands:

#### 3.1.1 Primary Emotional States (6 moods)

| Mood | State | Servo Behavior | Sound | Lights |
|------|-------|----------------|-------|--------|
| **1** | IDLE_RELAXED | Gentle drift, occasional small movements | Soft ambient beeps | Normal PSI, calm logic |
| **2** | IDLE_BORED | Restless scanning, fidgeting | Questioning chirps | Dim PSI, slow pulse |
| **3** | ALERT_CURIOUS | Active scanning, head tilt | Interested beeps | Bright PSI, active logic |
| **4** | ALERT_CAUTIOUS | Quick turns, defensive posture | Warning chirps | Pulsing PSI, amber logic |
| **5** | EXCITED_HAPPY | Bouncing movements, rapid dome rotation | Happy whistles | Bright flashing PSI |
| **6** | EXCITED_MISCHIEVOUS | Quick sneaky movements | Giggling beeps | Playful color shifts |

#### 3.1.2 Social Interaction States (4 moods)

| Mood | State | WCB1 Commands | WCB2 Commands | WCB3 Commands |
|------|-------|---------------|---------------|---------------|
| **7** | GREETING_FRIENDLY | Body servos: wave motion | Periscope: up | Dome servos: nod, PSI: bright |
| **8** | GREETING_SHY | Body servos: turn away slightly | Periscope: down | Dome: tilt down, PSI: dim |
| **9** | CONVERSING_ENGAGED | Body: active gestures | Periscope: moderate | Dome: attentive tracking |
| **10** | CONVERSING_DISTRACTED | Body: minimal movement | Periscope: random | Dome: wandering gaze |

#### 3.1.3 Character-Specific States (4 moods)

| Mood | State | Signature Behavior | Sound Bank | Special Effects |
|------|-------|-------------------|------------|-----------------|
| **11** | STUBBORN_DEFIANT | Turn away sharply, refuse to return | Raspberry sounds (Bank 2) | Red PSI flash |
| **12** | STUBBORN_POUTY | Slow reluctant movements | Grumbling (Bank 2) | Dim logic displays |
| **13** | PROTECTIVE_ALERT | Scanning sweep, ready stance | Alert beeps (Bank 1) | Yellow PSI pulse |
| **14** | PROTECTIVE_AGGRESSIVE | Rapid turns, defensive posture | Warning alarms (Bank 4) | Red flashing PSI |

#### 3.1.4 Activity States (6 moods)

| Mood | State | Multi-WCB Coordination |
|------|-------|------------------------|
| **15** | SCANNING_METHODICAL | WCB1: Slow dome rotation, WCB3: Systematic head sweep, Logic: scanning pattern |
| **16** | SCANNING_FRANTIC | WCB1: Rapid dome spins, WCB2: Periscope up, WCB3: Quick head jerks, PSI: rapid flash |
| **17** | TRACKING_FOCUSED | WCB1: Smooth dome follow, WCB3: Precise head positioning, Logic: lock-on pattern |
| **18** | TRACKING_PLAYFUL | WCB1: Bouncy following, WCB3: Playful head tilts, PSI: happy colors |
| **19** | DEMONSTRATING_CONFIDENT | WCB1: Proud posture, WCB2: Periscope full extend, WCB3: Upward tilt, Sound: fanfare |
| **20** | DEMONSTRATING_NERVOUS | WCB1: Fidgeting servos, WCB3: Uncertain movements, PSI: irregular pulse |

#### 3.1.5 Performance States (4 moods)

| Mood | State | Choreography Notes |
|------|-------|-------------------|
| **21** | ENTERTAINING_CROWD | All servos: big movements, Sound: musical (Bank 5), Lights: rainbow patterns |
| **22** | ENTERTAINING_INTIMATE | Gentle movements, soft sounds, warm lighting |
| **23** | JEDI_RESPECT | Respectful bow (head tilt down), reverent beeps (Bank 6), blue PSI glow |
| **24** | SITH_ALERT | Defensive stance, warning sounds (Bank 4), red PSI, rapid logic flash |

#### 3.1.6 Special States (3 moods)

| Mood | State | Emergency Protocols |
|------|-------|---------------------|
| **25** | MAINTENANCE_COOPERATIVE | All servos: home position, Sound: acknowledgment, Lights: white diagnostic |
| **26** | EMERGENCY_CALM | Controlled shutdown sequence, Status beeps, Amber safe-mode lights |
| **27** | EMERGENCY_PANIC | Rapid alerts, alarm sounds (Bank 4), Red flashing all lights, priority override |

### 3.2 Mood-to-Command Translation Matrix

Each mood translates to a coordinated sequence of WCB commands across all three boards:

**Example: GREETING_FRIENDLY (Mood 7)**

```python
MOOD_7_GREETING_FRIENDLY = {
    'wcb1_commands': [
        # Dome rotation (body servo channel 0)
        {'port': 1, 'cmd': [0x84, 0x00, 0x70, 0x2E]},  # Dome to 1500µs
        # Sound: friendly beep
        {'port': 4, 'cmd': [0x01, 0x00, 0x03]},  # Play bank 0, sound 3
    ],
    'wcb2_commands': [
        # Periscope up
        {'port': 2, 'cmd': [0x01, 0x01]},  # Custom: extend periscope
    ],
    'wcb3_commands': [
        # Head tilt (dome servo channel 1)
        {'port': 1, 'cmd': [0x84, 0x01, 0x00, 0x38]},  # Head tilt up (1750µs)
        # PSI lights: bright and happy
        {'port': 4, 'cmd': [0x01, 0x01]},  # Pattern: normal
        {'port': 4, 'cmd': [0x03, 0xFF]},  # Brightness: full
        # Logic lights: welcoming pattern
        {'port': 5, 'cmd': [0x01, 0x05]},  # Pattern: rainbow
    ],
    'duration_ms': 2000,
    'emotional_context': 'friendly_welcoming'
}
```

---

## 4. Python WCB Interface Library Architecture

### 4.1 Class Hierarchy

```
WCBController (Base)
├── WCB1BodyController
│   ├── MaestroServoInterface
│   ├── KyberBridgeInterface
│   └── HCRSoundInterface
├── WCB2DomePlateController
│   └── PeriscopeInterface
├── WCB3DomeController
│   ├── MaestroServoInterface
│   ├── PSILightInterface
│   └── LogicLightInterface
└── WCBOrchestrator
    ├── MoodTranslator
    ├── CommandSynchronizer
    └── SafetyMonitor
```

### 4.2 Core Interface Classes

**File: `/home/rolo/r2ai/wcb_controller.py`** (Production Implementation)

```python
#!/usr/bin/env python3
"""
WCB Hardware Integration Library
Production-Ready Interface for R2D2 WCB Meshed Network
"""

import serial
import time
import logging
import threading
from typing import Dict, List, Optional, Tuple, Callable
from dataclasses import dataclass
from enum import Enum

class WCBBoard(Enum):
    """WCB Board Identifiers"""
    WCB1_BODY = 0x01
    WCB2_DOME_PLATE = 0x02
    WCB3_DOME = 0x03
    BROADCAST = 0xFF

class WCBSerialPort(Enum):
    """WCB Serial Port Numbers"""
    SERIAL_1 = 0x01
    SERIAL_2 = 0x02
    SERIAL_3 = 0x03
    SERIAL_4 = 0x04
    SERIAL_5 = 0x05

@dataclass
class WCBCommand:
    """WCB command structure"""
    board: WCBBoard
    port: WCBSerialPort
    data: bytes
    priority: int = 5  # 1-10, higher = more important
    timeout_ms: int = 100

class WCBController:
    """Base WCB controller with serial communication"""

    def __init__(self, port: str = "/dev/ttyUSB0", baudrate: int = 9600):
        self.port = port
        self.baudrate = baudrate
        self.serial_conn: Optional[serial.Serial] = None
        self.command_queue: List[WCBCommand] = []
        self.is_connected = False
        self._lock = threading.Lock()

        self.connect()

    def connect(self) -> bool:
        """Establish connection to WCB network"""
        try:
            self.serial_conn = serial.Serial(
                port=self.port,
                baudrate=self.baudrate,
                timeout=1.0,
                write_timeout=1.0
            )
            time.sleep(0.1)
            self.is_connected = True
            logging.info(f"✅ Connected to WCB network: {self.port}")
            return True
        except Exception as e:
            logging.error(f"WCB connection failed: {e}")
            self.is_connected = False
            return False

    def send_command(self, command: WCBCommand) -> bool:
        """Send command to WCB network"""
        if not self.is_connected:
            logging.warning("WCB not connected - command ignored")
            return False

        try:
            with self._lock:
                # Build WCB frame: [Board, Port, Data...]
                frame = bytes([command.board.value, command.port.value]) + command.data
                self.serial_conn.write(frame)
                self.serial_conn.flush()

                logging.debug(f"WCB → Board {command.board.value}, "
                            f"Port {command.port.value}: {command.data.hex()}")
                return True
        except Exception as e:
            logging.error(f"WCB send failed: {e}")
            return False
```

### 4.3 Specialized Controllers

**WCB1 Body Controller:**
```python
class WCB1BodyController:
    """WCB1 Body controller with Maestro and sound"""

    def __init__(self, wcb: WCBController):
        self.wcb = wcb
        self.board = WCBBoard.WCB1_BODY

    def move_servo(self, channel: int, position_us: float) -> bool:
        """Move body servo (Maestro on Serial 1)"""
        # Convert microseconds to quarter-microseconds
        quarters = int(position_us * 4)

        # Build Maestro SET_TARGET command
        low_byte = quarters & 0x7F
        high_byte = (quarters >> 7) & 0x7F
        maestro_cmd = bytes([0x84, channel, low_byte, high_byte])

        command = WCBCommand(
            board=self.board,
            port=WCBSerialPort.SERIAL_1,
            data=maestro_cmd
        )

        return self.wcb.send_command(command)

    def play_sound(self, bank: int, sound_id: int) -> bool:
        """Play sound through HCR (Serial 4)"""
        hcr_cmd = bytes([0x01, bank, sound_id])

        command = WCBCommand(
            board=self.board,
            port=WCBSerialPort.SERIAL_4,
            data=hcr_cmd
        )

        return self.wcb.send_command(command)
```

**WCB3 Dome Controller:**
```python
class WCB3DomeController:
    """WCB3 Dome controller with servos and lights"""

    def __init__(self, wcb: WCBController):
        self.wcb = wcb
        self.board = WCBBoard.WCB3_DOME

    def move_servo(self, channel: int, position_us: float) -> bool:
        """Move dome servo (Maestro on Serial 1)"""
        quarters = int(position_us * 4)
        low_byte = quarters & 0x7F
        high_byte = (quarters >> 7) & 0x7F
        maestro_cmd = bytes([0x84, channel, low_byte, high_byte])

        command = WCBCommand(
            board=self.board,
            port=WCBSerialPort.SERIAL_1,
            data=maestro_cmd
        )

        return self.wcb.send_command(command)

    def set_psi_pattern(self, pattern_id: int, brightness: int = 255) -> bool:
        """Set PSI light pattern (Serial 4)"""
        psi_cmd = bytes([0x01, pattern_id])
        brightness_cmd = bytes([0x03, brightness])

        # Send both commands
        self.wcb.send_command(WCBCommand(
            board=self.board,
            port=WCBSerialPort.SERIAL_4,
            data=psi_cmd
        ))

        self.wcb.send_command(WCBCommand(
            board=self.board,
            port=WCBSerialPort.SERIAL_4,
            data=brightness_cmd
        ))

        return True
```

---

## 5. Mood Command Orchestration

### 5.1 WCBOrchestrator Integration

The orchestrator coordinates mood-based behaviors across all three WCB boards:

```python
class WCBOrchestrator:
    """High-level orchestration of WCB mood behaviors"""

    def __init__(self, wcb_controller: WCBController):
        self.wcb = wcb_controller
        self.wcb1 = WCB1BodyController(wcb_controller)
        self.wcb2 = WCB2DomePlateController(wcb_controller)
        self.wcb3 = WCB3DomeController(wcb_controller)

        # Load mood command tables
        self.mood_commands = self._load_mood_command_table()

    def execute_mood(self, mood_id: int) -> bool:
        """Execute complete mood behavior across all WCB boards"""
        if mood_id not in self.mood_commands:
            logging.error(f"Unknown mood: {mood_id}")
            return False

        mood = self.mood_commands[mood_id]
        logging.info(f"Executing mood: {mood['name']}")

        # Execute WCB1 commands (body)
        for cmd in mood.get('wcb1_commands', []):
            self.wcb1.execute_raw_command(cmd['port'], cmd['data'])

        # Execute WCB2 commands (dome plate)
        for cmd in mood.get('wcb2_commands', []):
            self.wcb2.execute_raw_command(cmd['port'], cmd['data'])

        # Execute WCB3 commands (dome)
        for cmd in mood.get('wcb3_commands', []):
            self.wcb3.execute_raw_command(cmd['port'], cmd['data'])

        return True
```

### 5.2 Disney Behavioral Intelligence Integration

Modify existing `r2d2_disney_behavioral_intelligence.py` to use WCB orchestrator:

```python
class DisneyBehavioralIntelligenceEngine:
    def __init__(self):
        # ... existing initialization ...

        # NEW: WCB Integration
        self.wcb_controller = WCBController(port="/dev/ttyUSB0")
        self.wcb_orchestrator = WCBOrchestrator(self.wcb_controller)

    async def _execute_coordinated_performance(self, behavior: BehaviorSequence):
        """Execute coordinated multi-system performance"""

        # Map personality state to mood ID
        mood_id = self._personality_state_to_mood(behavior.personality_state)

        # Execute WCB mood behavior
        self.wcb_orchestrator.execute_mood(mood_id)

        # Continue with existing servo choreography...
        # (Maestro commands now go through WCB1 Serial 1)
```

---

## 6. Implementation Files

### 6.1 Core Library Files (To Be Created)

1. **`wcb_controller.py`** - Base WCB communication layer
2. **`wcb_maestro_bridge.py`** - Maestro protocol integration
3. **`wcb_orchestrator.py`** - Mood-based command orchestration
4. **`wcb_mood_commands.json`** - Complete mood command table (27 moods)
5. **`wcb_diagnostic_tools.py`** - Testing and diagnostic utilities
6. **`wcb_stored_commands.py`** - WCB programming script generator

### 6.2 Integration Files (To Be Modified)

1. **`r2d2_disney_behavioral_intelligence.py`** - Add WCB orchestrator
2. **`maestro_enhanced_controller.py`** - Route through WCB1 Serial 1

### 6.3 Testing Files (To Be Created)

1. **`test_wcb_connection.py`** - Connection and communication test
2. **`test_wcb_maestro.py`** - Maestro command injection test
3. **`test_wcb_moods.py`** - All 27 mood behavior test
4. **`wcb_system_diagnostic.py`** - Complete system health check

---

## 7. Deployment Strategy

### 7.1 Phase 1: Foundation (Week 1)
- Create `wcb_controller.py` base library
- Implement WCB serial communication
- Test basic command sending to each board

### 7.2 Phase 2: Protocol Integration (Week 2)
- Implement Maestro protocol bridge
- Add HCR sound system interface
- Create PSI/Logic light controllers

### 7.3 Phase 3: Mood System (Week 3)
- Design complete 27-mood command table
- Implement WCB orchestrator
- Test mood-to-command translation

### 7.4 Phase 4: Behavioral Integration (Week 4)
- Integrate with Disney behavioral intelligence
- Connect vision system triggers to moods
- Test complete AI → WCB pipeline

### 7.5 Phase 5: Production Hardening (Week 5)
- Add comprehensive error handling
- Implement emergency stop protocols
- Create diagnostic tools and monitoring
- Performance optimization and stress testing

---

## 8. Safety and Emergency Protocols

### 8.1 Emergency Stop Hierarchy

1. **Hardware E-Stop:** Physical kill switch (highest priority)
2. **RC Override:** Kyber manual control always available
3. **WCB Emergency Command:** Software emergency stop
4. **Timeout Protection:** Auto-shutdown if commands fail

### 8.2 Command Priority System

```
Priority Levels (1-10):
10 = Emergency stop/safety commands
9  = RC manual override (Kyber)
8  = Critical system commands
7  = Behavioral mood changes
6  = Animation sequences
5  = Normal servo movements (default)
4  = Ambient behaviors
3  = Background lighting effects
2  = Diagnostic commands
1  = Low-priority logging
```

### 8.3 Kyber Coexistence Protocol

**Challenge:** Orin AI and Kyber RC both send Maestro commands to WCB1 Serial 1

**Solution:**
1. WCB1 accepts commands from both sources
2. Last command wins (position override)
3. RC commands have higher implicit priority
4. AI monitors for RC activity and yields control
5. AI resumes when RC idle for >5 seconds

**Implementation:**
```python
class KyberCoexistenceManager:
    def __init__(self):
        self.last_rc_activity = time.time()
        self.rc_active_threshold = 5.0  # seconds

    def is_rc_active(self) -> bool:
        """Check if RC controller is currently active"""
        # Monitor for Kyber command signatures
        return (time.time() - self.last_rc_activity) < self.rc_active_threshold

    def can_send_ai_command(self) -> bool:
        """Determine if AI can safely send commands"""
        return not self.is_rc_active()
```

---

## 9. Testing and Validation

### 9.1 Connection Test
```bash
python test_wcb_connection.py
```
- Verify USB serial connection
- Test each WCB board communication
- Validate mesh network integrity

### 9.2 Maestro Command Test
```bash
python test_wcb_maestro.py --board WCB1 --channel 0 --position 1500
```
- Send Maestro commands through WCB1 Serial 1
- Verify servo response
- Test command injection alongside Kyber

### 9.3 Mood Behavior Test
```bash
python test_wcb_moods.py --mood GREETING_FRIENDLY
```
- Execute complete mood sequence
- Verify multi-WCB coordination
- Validate timing and synchronization

### 9.4 System Diagnostic
```bash
python wcb_system_diagnostic.py --comprehensive
```
- Test all WCB boards and ports
- Verify all connected devices
- Generate health report

---

## 10. Next Steps

### Immediate Actions:
1. ✅ **Review this architecture document**
2. 📝 **Create `wcb_controller.py` production library**
3. 📊 **Design complete 27-mood command table**
4. 🔧 **Implement WCB diagnostic tools**
5. 🎭 **Integrate with Disney behavioral intelligence**

### Documentation Deliverables:
- WCB Python API Reference
- Mood Command Table (JSON)
- Integration Guide for Developers
- Troubleshooting and FAQ
- Performance Tuning Guide

---

## Document Control

**Version History:**
- v1.0 (2025-10-04): Initial architecture document

**Review Status:** ✅ Ready for Implementation

**Approvals Required:**
- [ ] Hardware Configuration Verified
- [ ] Protocol Specifications Confirmed
- [ ] Safety Protocols Reviewed
- [ ] Integration Plan Approved

---

**END OF ARCHITECTURE DOCUMENT**
