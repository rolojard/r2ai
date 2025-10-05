# WCB System Deployment and Testing Guide
## Complete Setup Instructions for R2D2 WCB Meshed Network

**Document Version:** 1.0
**Created:** 2025-10-04
**Target Hardware:** 3x WCB Boards + NVIDIA Orin Nano
**Prerequisites:** See Hardware Requirements section

---

## Table of Contents

1. [Hardware Requirements](#1-hardware-requirements)
2. [Software Installation](#2-software-installation)
3. [WCB Network Setup](#3-wcb-network-setup)
4. [System Configuration](#4-system-configuration)
5. [Testing and Validation](#5-testing-and-validation)
6. [Integration with Behavioral Intelligence](#6-integration-with-behavioral-intelligence)
7. [Troubleshooting](#7-troubleshooting)
8. [Performance Optimization](#8-performance-optimization)
9. [Maintenance and Monitoring](#9-maintenance-and-monitoring)

---

## 1. Hardware Requirements

### Required Hardware

#### WCB Boards (3x)
- **WCB1 (Body):** Master controller with Kyber bridge
- **WCB2 (Dome Plate):** Periscope and sensor controller
- **WCB3 (Dome):** Dome servos and lights controller

#### Servo Controllers (2x)
- **Pololu Maestro Mini 12-Channel USB** (Body servos - WCB1 Serial 1)
- **Pololu Maestro Mini 12-Channel USB** (Dome servos - WCB3 Serial 1)

#### Sound System
- **HCR Sound System** (Connected to WCB1 Serial 4)

#### Lights
- **PSI Lights** (Connected to WCB3 Serial 4)
- **Front Logic Displays** (Connected to WCB3 Serial 5)

#### Control System
- **NVIDIA Orin Nano** (AI control center)
- **Kyber RC System** (Manual control - WCB1 Serial 2)

#### Cables and Power
- USB Serial cables for WCB connection
- 5V/6V power supply for servos (adequate amperage)
- 12V power for lights
- Proper gauge wire for high-current devices

### Connection Diagram

```
NVIDIA Orin Nano
       │
       │ USB Serial
       ▼
  ┌─────────┐     Wireless      ┌─────────┐     Wireless      ┌─────────┐
  │  WCB1   │◄─────Mesh────────►│  WCB2   │◄─────Mesh────────►│  WCB3   │
  │ (Body)  │                   │ (Plate) │                   │ (Dome)  │
  └─────────┘                   └─────────┘                   └─────────┘
       │                               │                            │
  ┌────┴────┬────────┬─────────┐      │                      ┌─────┴──────┬────────┬────────┐
  │         │        │         │      │                      │            │        │        │
Maestro   Kyber    Kyber     HCR   Periscope              Maestro       PSI     Logic    [Open]
(Serial1) (S2)     (S3)      (S4)    (S2)                 (Serial1)    (S4)     (S5)
```

---

## 2. Software Installation

### Step 1: Install System Dependencies

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Python dependencies
sudo apt install python3 python3-pip python3-venv -y

# Install serial communication libraries
sudo pip3 install pyserial

# Install additional dependencies
sudo pip3 install numpy websockets
```

### Step 2: Install WCB Library

```bash
# Navigate to R2AI directory
cd /home/rolo/r2ai

# Verify WCB files are present
ls -la wcb_*.py

# Expected files:
# - wcb_controller.py
# - wcb_orchestrator.py
# - wcb_diagnostic_tools.py
# - wcb_mood_commands.json

# Make scripts executable
chmod +x wcb_controller.py
chmod +x wcb_orchestrator.py
chmod +x wcb_diagnostic_tools.py
```

### Step 3: Configure Serial Permissions

```bash
# Add user to dialout group (for serial port access)
sudo usermod -a -G dialout $USER

# Apply changes (logout/login may be required)
newgrp dialout

# Verify serial devices
ls -l /dev/ttyUSB* /dev/ttyACM*

# Expected output: Character devices with dialout group
```

---

## 3. WCB Network Setup

### Step 1: Physical Connections

1. **Connect WCB1 (Body)**
   - USB Serial cable from Orin Nano to WCB1
   - Maestro servo controller to WCB1 Serial 1
   - Kyber RC receiver to WCB1 Serial 2
   - Kyber bridge to WCB1 Serial 3
   - HCR sound system to WCB1 Serial 4

2. **Configure WCB2 (Dome Plate)**
   - Ensure wireless mesh connection to WCB1
   - Connect periscope controller to WCB2 Serial 2

3. **Configure WCB3 (Dome)**
   - Ensure wireless mesh connection to WCB1/WCB2
   - Maestro servo controller to WCB3 Serial 1
   - PSI lights to WCB3 Serial 4
   - Logic displays to WCB3 Serial 5

### Step 2: Power Up Sequence

```bash
# Proper power-up sequence to avoid issues:

# 1. Power servo supplies (5V/6V) - FIRST
# 2. Power WCB boards (meshed network)
# 3. Power Orin Nano
# 4. Wait 30 seconds for mesh network to establish
# 5. Verify green status LEDs on all WCB boards
```

### Step 3: Verify USB Connection

```bash
# Check USB serial device
ls -l /dev/ttyUSB*

# Expected: /dev/ttyUSB0 (or ttyUSB1, etc.)

# Test basic communication
sudo screen /dev/ttyUSB0 9600
# (Press Ctrl+A, then K to exit screen)

# If no device appears:
dmesg | tail -20
# Look for USB serial device messages
```

---

## 4. System Configuration

### Step 1: Test WCB Connection

```bash
# Run connection diagnostic
python3 wcb_diagnostic_tools.py --test connection

# Expected output:
# ✅ Successfully connected to WCB network on /dev/ttyUSB0

# If connection fails, try simulation mode first:
python3 wcb_diagnostic_tools.py --test connection --simulation
```

### Step 2: Configure Servo Limits

Edit servo configuration if needed (optional):

```python
# Create custom servo config (optional)
# File: /home/rolo/r2ai/config/custom_servo_config.json

{
  "wcb1_servos": {
    "0": {
      "name": "dome_rotation",
      "min_us": 600,
      "max_us": 2400,
      "home_us": 1500
    },
    "1": {
      "name": "utility_arm_left",
      "min_us": 700,
      "max_us": 2300,
      "home_us": 1500
    }
  },
  "wcb3_servos": {
    "1": {
      "name": "head_tilt",
      "min_us": 900,
      "max_us": 2100,
      "home_us": 1500
    }
  }
}
```

### Step 3: Verify Mood Command Table

```bash
# Verify mood commands file exists
ls -l wcb_mood_commands.json

# Check JSON validity
python3 -m json.tool wcb_mood_commands.json > /dev/null && echo "✅ Valid JSON" || echo "❌ Invalid JSON"

# View mood definitions
cat wcb_mood_commands.json | jq '.moods | keys'
```

---

## 5. Testing and Validation

### Test 1: Connection Test

```bash
# Basic connection test
python3 wcb_diagnostic_tools.py --test connection

# Expected output:
# 🔍 Testing WCB network connection...
# ✅ Successfully connected to WCB network on /dev/ttyUSB0
```

### Test 2: WCB1 Body Test

```bash
# Test WCB1 servos and sound
python3 wcb_diagnostic_tools.py --test wcb1

# Expected output:
# 🔍 Testing WCB1 servo control...
# ✅ All 4 servo commands sent successfully
# 🔍 Testing WCB1 sound system...
# ✅ Sound system commands sent successfully
```

### Test 3: WCB2 Dome Plate Test

```bash
# Test WCB2 periscope
python3 wcb_diagnostic_tools.py --test wcb2

# Expected output:
# 🔍 Testing WCB2 periscope control...
# ✅ Periscope control operational
```

### Test 4: WCB3 Dome Test

```bash
# Test WCB3 servos and lights
python3 wcb_diagnostic_tools.py --test wcb3

# Expected output:
# 🔍 Testing WCB3 servo control...
# ✅ All 4 dome servo commands sent
# 🔍 Testing WCB3 light systems...
# ✅ PSI and Logic lights operational
```

### Test 5: Mood System Test

```bash
# Test mood orchestration
python3 wcb_diagnostic_tools.py --test mood

# Expected output:
# 🔍 Testing mood orchestration system...
# ✅ Mood orchestration system operational
```

### Test 6: Comprehensive System Test

```bash
# Run complete diagnostic
python3 wcb_diagnostic_tools.py --test comprehensive --output diagnostic_report.json

# Review report
cat diagnostic_report.json | jq '.overall_health'

# Expected: "excellent" or "good"
```

### Manual Servo Test

```python
# Test individual servo movement
# File: test_servo_manual.py

from wcb_controller import WCBController, WCB1BodyController
import time

wcb = WCBController()
wcb1 = WCB1BodyController(wcb)

# Slowly move dome servo
for position in range(1200, 1801, 50):
    wcb1.move_servo(0, position)
    print(f"Servo at {position}µs")
    time.sleep(0.3)

# Return to center
wcb1.move_servo(0, 1500)
print("Test complete")

wcb.shutdown()
```

```bash
# Run manual test
python3 test_servo_manual.py
```

---

## 6. Integration with Behavioral Intelligence

### Step 1: Verify Existing Systems

```bash
# Check behavioral intelligence system
ls -l r2d2_disney_behavioral_intelligence.py

# Check existing mood definitions
python3 -c "from r2d2_disney_behavioral_intelligence import R2D2PersonalityState; print(list(R2D2PersonalityState))"
```

### Step 2: Create Integration Bridge

```python
# File: /home/rolo/r2ai/wcb_behavioral_bridge.py

from wcb_controller import WCBController
from wcb_orchestrator import WCBOrchestrator, WCBBehavioralBridge
from r2d2_disney_behavioral_intelligence import DisneyBehavioralIntelligenceEngine

class EnhancedDisneyEngine(DisneyBehavioralIntelligenceEngine):
    """Enhanced Disney Engine with WCB Integration"""

    def __init__(self):
        super().__init__()

        # Initialize WCB system
        self.wcb_controller = WCBController(auto_detect=True)
        self.wcb_orchestrator = WCBOrchestrator(self.wcb_controller)
        self.wcb_bridge = WCBBehavioralBridge(self.wcb_orchestrator)

    async def _execute_coordinated_performance(self, behavior):
        """Override to use WCB for hardware control"""

        # Execute WCB mood behavior
        personality_state_name = behavior.personality_state.name
        self.wcb_bridge.execute_personality_state(personality_state_name)

        # Continue with existing choreography
        await super()._execute_coordinated_performance(behavior)

    def shutdown(self):
        """Enhanced shutdown with WCB cleanup"""
        super().shutdown()
        self.wcb_controller.shutdown()
```

### Step 3: Test Integrated System

```python
# File: test_integrated_system.py

from wcb_behavioral_bridge import EnhancedDisneyEngine
import asyncio

async def test_integrated_moods():
    engine = EnhancedDisneyEngine()

    # Test greeting behavior
    engine.execute_manual_behavior("enthusiastic_greeting")
    await asyncio.sleep(7)

    # Test alert behavior
    engine.execute_manual_behavior("jedi_respect")
    await asyncio.sleep(8)

    # Test entertainment behavior
    engine.execute_manual_behavior("musical_performance")
    await asyncio.sleep(21)

    engine.shutdown()

asyncio.run(test_integrated_moods())
```

```bash
# Run integration test
python3 test_integrated_system.py
```

---

## 7. Troubleshooting

### Issue 1: WCB Connection Failed

**Symptoms:**
```
❌ Failed to connect to WCB network
```

**Solutions:**
```bash
# 1. Check USB connection
ls -l /dev/ttyUSB*

# 2. Check permissions
groups | grep dialout

# 3. Check dmesg for errors
dmesg | tail -20

# 4. Try different USB port
# Unplug and replug USB cable

# 5. Verify WCB board power
# Check green status LED on WCB1

# 6. Test with screen
sudo screen /dev/ttyUSB0 9600
```

### Issue 2: Servos Not Moving

**Symptoms:**
- Commands sent but servos don't move
- Servos jitter or behave erratically

**Solutions:**
```bash
# 1. Check servo power supply
# Verify 5V/6V supply is adequate (check amperage)

# 2. Test Maestro directly
# Use Pololu Maestro Control Center to test

# 3. Verify command format
python3 -c "
from wcb_controller import WCBController, WCB1BodyController
wcb = WCBController(simulation_mode=True)
wcb1 = WCB1BodyController(wcb)
wcb1.move_servo(0, 1500)  # Should show command bytes
"

# 4. Check servo limits
# Ensure positions are within 500-2500µs range
```

### Issue 3: Sound System Silent

**Symptoms:**
- Sound commands sent but no audio

**Solutions:**
```bash
# 1. Check HCR connection to WCB1 Serial 4
# Verify physical connection

# 2. Test volume level
python3 -c "
from wcb_controller import WCBController, WCB1BodyController
wcb = WCBController()
wcb1 = WCB1BodyController(wcb)
wcb1.set_volume(255)  # Max volume
wcb1.play_sound(0, 1)  # Test sound
"

# 3. Verify HCR power
# Check 5V power to sound board

# 4. Test HCR directly with serial commands
```

### Issue 4: Lights Not Working

**Symptoms:**
- Light commands sent but PSI/Logic lights don't respond

**Solutions:**
```bash
# 1. Check power to lights (usually 12V)
# Verify voltage with multimeter

# 2. Test basic light command
python3 -c "
from wcb_controller import WCBController, WCB3DomeController
wcb = WCBController()
wcb3 = WCB3DomeController(wcb)
wcb3.set_psi_pattern(1, 255)  # Full brightness
"

# 3. Check WCB3 Serial 4/5 connections
# Verify physical wiring

# 4. Test with multimeter
# Check signal on data lines
```

### Issue 5: Kyber RC Override Not Working

**Symptoms:**
- RC commands don't override AI commands

**Solutions:**
```python
# Verify Kyber bridge configuration
# WCB1 should be in "Kyber Local" mode

# Test RC priority (implement in code):
from wcb_controller import WCBCommand, WCBBoard

# RC commands should have priority 9
rc_command = WCBCommand(
    board=WCBBoard.WCB1_BODY,
    port=...,
    data=...,
    priority=9  # Higher than AI (7)
)
```

---

## 8. Performance Optimization

### Optimization 1: Command Queue Tuning

```python
# Adjust command processing rate
# File: wcb_controller.py (modify if needed)

# In _command_processing_loop:
time.sleep(0.005)  # 5ms = 200 commands/second (faster)
# Default: 0.01 (10ms = 100 commands/second)
```

### Optimization 2: Servo Speed Optimization

```python
# Set optimal servo speeds for smooth motion
from wcb_controller import WCBController, WCB1BodyController

wcb = WCBController()
wcb1 = WCB1BodyController(wcb)

# Slower = smoother (0-255)
wcb1.set_servo_speed(0, 30)  # Dome rotation - smooth
wcb1.set_servo_speed(1, 50)  # Utility arms - moderate
```

### Optimization 3: Batch Command Sending

```python
# Send multiple commands at once
commands = [
    (0, 1600),  # Dome right
    (1, 1700),  # Head tilt up
]

for channel, position in commands:
    wcb1.move_servo(channel, position)
# All sent in quick succession
```

### Optimization 4: Reduce Logging Overhead

```python
# Set logging level to WARNING in production
import logging
logging.basicConfig(level=logging.WARNING)

# Only INFO/DEBUG during development
```

---

## 9. Maintenance and Monitoring

### Daily Checks

```bash
# Run quick diagnostic
python3 wcb_diagnostic_tools.py --test comprehensive --output daily_check.json

# Check status
cat daily_check.json | jq '{health: .overall_health, passed: .tests_passed, failed: .tests_failed}'
```

### Weekly Maintenance

```bash
# 1. Full system diagnostic
python3 wcb_diagnostic_tools.py --test comprehensive --output weekly_report_$(date +%Y%m%d).json

# 2. Verify all moods
python3 -c "
from wcb_orchestrator import WCBOrchestrator, R2D2Mood, WCBController
wcb = WCBController(simulation_mode=True)
orch = WCBOrchestrator(wcb)

for mood in R2D2Mood:
    print(f'Testing {mood.name}...')
    orch.execute_mood(mood, blocking=True)

wcb.shutdown()
print('All moods tested')
"

# 3. Check servo wear
# Manually test all servos for smoothness

# 4. Verify connections
# Check all cable connections
```

### System Logs

```python
# Enable comprehensive logging
# File: wcb_system_logger.py

import logging
from logging.handlers import RotatingFileHandler

# Create rotating log file
handler = RotatingFileHandler(
    '/home/rolo/r2ai/logs/wcb_system.log',
    maxBytes=10*1024*1024,  # 10MB
    backupCount=5
)

formatter = logging.Formatter(
    '%(asctime)s - %(name)s - [%(levelname)s] - %(message)s'
)
handler.setFormatter(formatter)

logging.root.addHandler(handler)
logging.root.setLevel(logging.INFO)
```

### Performance Monitoring

```python
# Monitor WCB performance
from wcb_controller import WCBController
import time

wcb = WCBController()

# Collect stats periodically
while True:
    stats = wcb.get_status()
    print(f"Commands sent: {stats['statistics']['commands_sent']}")
    print(f"Queue size: {stats['statistics']['queue_size']}")
    print(f"Uptime: {stats['statistics']['uptime_seconds']}s")
    time.sleep(10)
```

---

## Conclusion

This deployment guide provides complete instructions for:
- ✅ Hardware setup and connections
- ✅ Software installation and configuration
- ✅ System testing and validation
- ✅ Integration with behavioral intelligence
- ✅ Troubleshooting common issues
- ✅ Performance optimization
- ✅ Ongoing maintenance

Your R2D2 WCB meshed network system is now ready for operation!

For additional support:
- Review `/home/rolo/r2ai/WCB_HARDWARE_INTEGRATION_ARCHITECTURE.md`
- Check diagnostic logs in `/home/rolo/r2ai/logs/`
- Test with simulation mode before hardware deployment

---

**END OF DEPLOYMENT GUIDE**
