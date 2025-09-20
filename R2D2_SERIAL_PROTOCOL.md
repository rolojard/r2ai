# R2D2 Convention Project - Unified Serial Communication Protocol

## System Overview
The R2D2 convention droid integrates multiple subsystems through a centralized Nvidia Orin Nano controller using a unified serial communication protocol.

## Hardware Architecture

### Central Controller
- **Primary**: Nvidia Orin Nano Super (Ubuntu + CUDA)
- **Role**: AI processing, guest recognition, behavior coordination
- **Interfaces**: USB, GPIO, UART, I2C

### Subsystem Controllers

#### 1. Pololu Maestro Servo Controller
- **Function**: Panel animations, head dome rotation
- **Protocol**: Serial UART (Compact Protocol recommended)
- **Baud Rate**: 115200 bps
- **Commands**: Position control, speed/acceleration limiting

#### 2. HCR Audio System
- **Function**: R2D2 vocalizations, sound effects
- **Interface**: Serial or I2C communication
- **Audio Format**: 16-bit 44.1kHz WAV files
- **Storage**: SD card with organized sound library

#### 3. Logic Display Controllers
- **Function**: Front/rear logic displays, PSI lights
- **Protocol**: Serial or I2C
- **Features**: Pattern sequences, brightness control

#### 4. Neo Pixel Controllers
- **Function**: RGB lighting effects
- **Protocol**: WS2812B data protocol
- **Integration**: GPIO pins from Orin Nano

## Unified Communication Protocol

### Message Structure
```
[SYNC][DEVICE_ID][COMMAND][LENGTH][DATA][CHECKSUM]
```

#### Field Definitions
- **SYNC**: 0xAA (170) - Message start marker
- **DEVICE_ID**: 8-bit device identifier
  - 0x01: Maestro Servo Controller
  - 0x02: HCR Audio System
  - 0x03: Front Logic Display
  - 0x04: Rear Logic Display
  - 0x05: PSI Light Controller
  - 0x06: Neo Pixel Controller
- **COMMAND**: 8-bit command code
- **LENGTH**: 8-bit data length (0-255 bytes)
- **DATA**: Variable length payload
- **CHECKSUM**: 8-bit XOR checksum of all previous bytes

### Device-Specific Commands

#### Maestro Servo Controller (0x01)
```
SET_POSITION    (0x10): [channel][target_low][target_high]
SET_SPEED       (0x11): [channel][speed]
SET_ACCELERATION(0x12): [channel][accel]
GET_POSITION    (0x13): [channel]
GET_MOVING      (0x14): []
SEQUENCE_START  (0x15): [sequence_id]
SEQUENCE_STOP   (0x16): []
```

#### HCR Audio System (0x02)
```
PLAY_SOUND      (0x20): [sound_id]
STOP_SOUND      (0x21): []
SET_VOLUME      (0x22): [volume_level]
PLAY_SEQUENCE   (0x23): [sequence_id]
GET_STATUS      (0x24): []
```

#### Logic Display Controllers (0x03, 0x04)
```
SET_PATTERN     (0x30): [pattern_id][speed][brightness]
SET_PIXEL       (0x31): [x][y][state]
CLEAR_DISPLAY   (0x32): []
SET_BRIGHTNESS  (0x33): [brightness]
ANIMATE         (0x34): [animation_id]
```

#### PSI Light Controller (0x05)
```
SET_MODE        (0x40): [mode][color][brightness]
PULSE           (0x41): [rate][intensity]
FLASH           (0x42): [count][duration]
RAINBOW         (0x43): [speed]
```

#### Neo Pixel Controller (0x06)
```
SET_COLOR       (0x50): [pixel_id][red][green][blue]
SET_BRIGHTNESS  (0x51): [brightness]
FILL_COLOR      (0x52): [red][green][blue]
PATTERN         (0x53): [pattern_id][speed]
EFFECT          (0x54): [effect_id][param1][param2]
```

## Behavior Coordination System

### AI-Driven Responses
The Orin Nano processes camera input and coordinates responses:

1. **Character Detection**: YOLOv8 identifies Star Wars characters/items
2. **Guest Recognition**: Face detection with short-term memory
3. **Behavior Trigger**: Contextual R2D2 responses
4. **Multi-System Coordination**: Synchronized audio, lighting, movement

### Example Interaction Sequence
```python
# Guest wearing Jedi costume detected
def handle_jedi_interaction():
    # 1. Excited dome movement
    send_command(MAESTRO, SET_POSITION, [dome_channel, excited_position])

    # 2. Happy R2D2 sounds
    send_command(HCR_AUDIO, PLAY_SOUND, [happy_beep_sequence])

    # 3. Blue PSI lights (lightsaber color)
    send_command(PSI_LIGHTS, SET_MODE, [pulse_mode, blue, high_brightness])

    # 4. Logic display animation
    send_command(FRONT_LOGIC, ANIMATE, [excitement_pattern])

    # 5. Panel animations
    send_command(MAESTRO, SEQUENCE_START, [panel_flutter_sequence])
```

## Safety and Error Handling

### Watchdog System
- Heartbeat messages every 100ms
- Automatic safe mode if communication lost
- Emergency stop capability for all systems

### Error Codes
```
0x00: Success
0x01: Invalid command
0x02: Checksum error
0x03: Device timeout
0x04: Hardware error
0xFF: Emergency stop
```

### Safe Mode Behaviors
- All servos return to home position
- Audio system mutes
- Lights dim to minimum
- Dome stops rotation

## Implementation Priority
1. **Phase 1**: Basic servo control and audio integration
2. **Phase 2**: Logic displays and lighting effects
3. **Phase 3**: AI behavior coordination
4. **Phase 4**: Guest recognition and memory system
5. **Phase 5**: Advanced interactive behaviors

This unified protocol ensures reliable, coordinated operation of all R2D2 subsystems while maintaining the authentic character personality and behavior patterns.