# WCB Hardware Command Reference
**Complete Command Documentation from Hardware Creator**

## ⚠️ CRITICAL: Carriage Return Requirement
**ALL serial commands MUST end with `\r` (carriage return)** to work properly with the hardware.

Example: `R0063` becomes `R0063\r` for serial transmission

---

## Command Systems Overview

R2-D2's control system uses 4 distinct command protocols:

1. **WCB Serial Commands** - Periscope, PSI, Holo control via WCB boards
2. **Maestro Commands** - Dome and body servo sequences
3. **FlthyHP Commands** - Holo Projector LED and servo control
4. **HCR Vocalizer** - Audio, emotions, and personality control

---

## 1. WCB Serial Commands

### Format: `;W[board];[command]\r`

### Periscope Commands (WCB2 - Board ;W2;)
```
;W2;S2:PS4\r     # Random fast periscope
;W2;S2:PS5\r     # Random slow periscope
;W2;S2:PS1\r     # Periscope down (retracted)
;W2;S2:PS2\r     # Periscope up (extended)
;W2;S2:PS0\r     # Sneaky periscope movement
```

### PSI Display Commands (WCB3 - Board ;W3;)
```
;W3;S34T6|20\r   # Leia PSI 20 seconds
;W3;S34T7\r      # Heart pattern
;W3;S30T3\r      # Pattern 3
;W30T3\r         # Global pattern 3
```

### Filthy Holo Projector (WCB3)
```
;W3;S2F0036\r    # Filthy holo sequence
;W3;S299\r       # Holo pattern 99
;W3;S2T1991\r    # Holo twitch mode
;W3;S2A051\r     # Holo animation 51
```

---

## 2. Maestro Commands

### Format: `;M[###]\r`

### Dome Maestro Commands (;M3##)
```
;M301\r          # Dome open
;M302\r          # Dome fast top movement
;M303\r          # Dome bye gesture
;M304\r          # Dome close
;M305\r          # Dome alternate open/close
;M306\r          # Dome fast alternate
;M307\r          # Dome breathing motion
;M308\r          # Dome long random sequence
;M309\r          # Dome scream movement
;M310\r          # Dome come here gesture
;M311\r          # Dome slow to fast acceleration
```

### Body/Arms Maestro Commands (;M1#)
```
;M11\r           # Arms open and close
;M12\r           # Arms wave
;M13\r           # Arms open
;M14\r           # Arms closed
;M15\r           # Arms random movement
```

---

## 3. FlthyHP Commands

### Command Structure: `[D][T][##][C][S/P]\r`

**Components:**
- `D` = Designator: `F` (Front), `R` (Rear), `T` (Top), `A` (All)
- `T` = Type: `0` (LED), `1` (Servo)
- `##` = Sequence number (01-99, 96-99 special)
- `C` = Color value (1-9, 0=random) - LED only
- `S` = Speed (0-9) - Dim pulse only
- `P` = Position (0-8) - Servo preset only

### LED Sequences (Type 0)

| Sequence | Code | Description | Needs Color | Needs Speed |
|----------|------|-------------|-------------|-------------|
| Leia | 01 | Random blue shades Leia hologram | No | No |
| Color Projector | 02 | Color projector using color value | Yes | No |
| Dim Pulse | 03 | Slow color pulse | Yes | Yes (0-9) |
| Cycle | 04 | Color cycle animation | Yes | No |
| Short Circuit | 05 | Flash slowing over time | No | No |
| Toggle Color | 06 | Solid color | Yes | No |
| Rainbow | 07 | Rainbow sequence | No | No |
| Clear/No Auto | 96 | Clear LED, disable auto | No | No |
| Clear/Auto Default | 971 | Clear, enable auto default | No | No |
| Clear/Auto Random | 972 | Clear, enable auto random | No | No |
| Clear/Off Color | 98 | Clear, enable off color | No | No |
| Clear/Off/Auto Def | 991 | Clear, off color, auto default | No | No |
| Clear/Off/Auto Rnd | 992 | Clear, off color, auto random | No | No |

### Servo Sequences (Type 1)

| Sequence | Code | Description | Needs Position |
|----------|------|-------------|----------------|
| Preset Position | 01 | Move to preset position | Yes (0-8) |
| RC Left/Right | 02 | Enable RC left/right control | No |
| RC Up/Down | 03 | Enable RC up/down control | No |
| Random Position | 04 | Move to random position | No |
| Wag Left/Right | 05 | Wag left/right | No |
| Wag Up/Down | 06 | Wag up/down | No |
| Disable Twitch | 98 | Disable auto twitch | No |
| Enable Twitch | 99 | Enable auto twitch | No |

### Color Values
```
1 = Red       6 = Magenta
2 = Yellow    7 = Orange
3 = Green     8 = Purple
4 = Cyan      9 = White
5 = Blue      0 = Random
```

### Preset Positions
```
0 = Down          5 = Lower Left
1 = Center        6 = Right
2 = Up            7 = Upper Right
3 = Left          8 = Lower Right
4 = Upper Left
```

### Example Commands
```
R0063\r          # Rear HP green solid
F00366\r         # Front HP magenta pulse, speed 6
T007\r           # Top HP rainbow
A098\r           # All HPs clear, disable auto
F1012\r          # Front HP to UP position
A1011\r          # All HPs to CENTER position
R104\r           # Rear HP random position
T199\r           # Top HP enable twitch
```

---

## 4. PSI T-Mode Commands

### Format: `[Address]T[Mode]\r`

### Address Modifiers
```
0 = Global (all displays)
1 = TFLD (Top Front Logic Display)
2 = BFLD (Bottom Front Logic Display)
3 = RLD (Rear Logic Display)
4 = Front PSI
5 = Rear PSI
6 = Front Holo (not implemented)
7 = Rear Holo (not implemented)
8 = Top Holo (not implemented)
```

### T-Mode Patterns

| Mode | Name | Duration | Description |
|------|------|----------|-------------|
| 0 | Off | - | Turn panel off |
| 1 | Swipe | - | Default swipe pattern |
| 2 | Flash Fast | 4s | Fast flash (caution: photosensitivity) |
| 3 | Alarm Slow | 4s | Slow flash alarm |
| 4 | Short Circuit | 10s | Short circuit effect |
| 5 | Scream | 4s | Scream effect |
| 6 | Leia Message | 34s | Leia hologram message |
| 7 | Heart U | 10s | I heart U animation |
| 8 | Quarter Sweep | 7s | Quarter panel sweep |
| 9 | Heart Pulse | - | Flashing red heart / pulse monitor |
| 10 | Star Wars Scroll | 15s | Star Wars title scroll |
| 11 | Imperial March | 47s | Imperial March animation |
| 12 | Disco Ball | 4s | Disco ball effect |
| 13 | Disco Ball Cont | - | Disco ball continuous |
| 14 | Rebel Symbol | 5s | Rebel Alliance symbol |
| 15 | Knight Rider | 20s | Knight Rider sweep |
| 16 | Test White | - | Test sequence white continuous |
| 17 | Red On | - | Red continuous |
| 18 | Green On | - | Green continuous |
| 19 | Lightsaber Battle | - | Light saber battle effect |
| 20 | SW Intro Scroll | - | Star Wars intro scroll |
| 21 | VU Meter | 4s | VU Meter |
| 92 | VU Meter Cont | - | VU Meter continuous |

### Example Commands
```
4T6\r            # Front PSI Leia message
0T1\r            # All displays swipe pattern
5T3\r            # Rear PSI alarm slow
4T12\r           # Front PSI disco ball
0T0\r            # All displays off
```

---

## 5. HCR Vocalizer Commands

### Format: `<[command]>\r`

Commands wrapped in angle brackets `<...>`. Multiple commands can be chained: `<cmd1,cmd2>\r` or `<cmd1><cmd2>\r`

### Emotional Stimuli
```
<SH0>\r          # Mild happy vocalization
<SH1>\r          # Extreme happy vocalization
<SS0>\r          # Mild sad vocalization
<SS1>\r          # Extreme sad vocalization
<SM0>\r          # Mild angry vocalization
<SM1>\r          # Extreme angry vocalization
<SC0>\r          # Mild scared vocalization
<SC1>\r          # Extreme scared vocalization
<SE>\r           # Overload/electrocution vocalization
```

### Muse (Background Sounds)
```
<M1>\r           # Enable muse
<M0>\r           # Disable muse
<MT>\r           # Toggle muse
<MM>\r           # Trigger single musing
<MN#>\r          # Set minimum gap (seconds) between musings
<MX#>\r          # Set maximum gap (seconds) between musings
```

### SD WAV Playback
```
<CA####>\r       # Play WAV file 0000-9999 on channel A
<CB####>\r       # Play WAV file 0000-9999 on channel B
<CA####C####>\r  # Play random WAV between range on channel A
<CB####C####>\r  # Play random WAV between range on channel B
```

Examples:
```
<CA0025>\r       # Play WAV file 25 on channel A
<CB0003C0185>\r  # Play random WAV 3-185 on channel B
```

### Stop Commands
```
<PSV>\r          # Stop vocalizer immediately
<PSG>\r          # Stop vocalizer gracefully
<PSA>\r          # Stop WAV channel A
<PSB>\r          # Stop WAV channel B
```

### Volume Control (0-100)
```
<PVV#>\r         # Set vocalizer volume
<PVA#>\r         # Set WAV channel A volume
<PVB#>\r         # Set WAV channel B volume
```

### Personality Override
```
<OA0>\r          # Disable canonical, enable improvisational
<OA1>\r          # Enable canonical, disable improvisational
<O1>\r           # Enable personality chip override
<O0>\r           # Disable personality chip override
<OR>\r           # Reset all emotions to 0
<OH#>\r          # Set happy emotion 0-100
<OS#>\r          # Set sad emotion 0-100
<OM#>\r          # Set mad emotion 0-100
<OC#>\r          # Set scared emotion 0-100
```

### Query Commands (Response in angle brackets)
```
<QEH>\r          # Query happy emotion → <QEH,#>
<QES>\r          # Query sad emotion → <QES,#>
<QEM>\r          # Query angry emotion → <QEM,#>
<QEC>\r          # Query scared emotion → <QEC,#>
<QE>\r           # Query all emotions → <QE,#,#,#,#>
<QO>\r           # Query override status → <QO,#>
<QM>\r           # Query muse status → <QM,#>
<QF>\r           # Query total WAV files → <QF,#>
<QT>\r           # Query vocalization duration → <QT,#>
<QPV>\r          # Query vocalizer playing → <QPV,#>
<QPA>\r          # Query WAV A file number → <QPA,#>
<QPB>\r          # Query WAV B file number → <QPB,#>
<QVV>\r          # Query vocalizer volume → <QVV,#>
<QVA>\r          # Query WAV A volume → <QVA,#>
<QVB>\r          # Query WAV B volume → <QVB,#>
<QD>\r           # Query all key metrics → <QD,#,...,#>
```

### Chained Command Examples
```
<SH1>\r          # Single command
<CA0025>\r       # Play WAV 25

<SH1,M1>\r       # Chained: happy + enable muse
<SH1><M1>\r      # Alternate syntax

<SM0,QM>\r       # Chained: angry + query muse → <QM0>
<OH80,CA0045>\r  # Set happy 80 + play WAV 45
```

---

## Integration with Mood System

### Priority Levels
```
10 = Emergency (highest)
9  = RC Control
7  = AI Mood Commands
5  = Normal Operations (lowest)
```

### Mood Command Combinations

**Idle Relaxed:**
```
;M304\r          # Dome center
4T1\r            # Front PSI swipe
F00353\r         # Front HP blue pulse slow
<SH0>\r          # Mild happy
```

**Alert Curious:**
```
;M301\r          # Dome open
;W2;S2:PS2\r     # Periscope up
0T1\r            # All PSI swipe
F0064\r          # Front HP cyan solid
```

**Excited Happy:**
```
;M12\r           # Arms wave
;M306\r          # Dome fast alternate
;W2;S2:PS4\r     # Periscope random fast
0T12\r           # All PSI disco ball
A007\r           # All HP rainbow
<SH1>\r          # Extreme happy
<CA0025>\r       # Happy sound WAV 25
```

**Protective Alert:**
```
;M309\r          # Dome scream
;W2;S2:PS2\r     # Periscope up
0T3\r            # All PSI alarm slow
A0061\r          # All HP red solid
<SM0>\r          # Mild angry
```

**Emergency Panic:**
```
;M304\r          # Dome close/center
;W2;S2:PS1\r     # Periscope down (safe)
;M14\r           # Arms closed
0T2\r            # All PSI flash fast
A005\r           # All HP short circuit
<SC1>\r          # Extreme scared
<CA0047>\r       # Alarm sound WAV 47
```

**Jedi Respect:**
```
;M303\r          # Dome bow
;W2;S2:PS1\r     # Periscope retracted
0T7\r            # All PSI heart U
A00352\r         # All HP blue pulse slow
<OH80>\r         # Set happy emotion 80
```

---

## Command Timing Guidelines

1. **Send commands in order** - Hardware processes sequentially
2. **Allow processing time** - 50-100ms between complex commands
3. **Respect durations** - Match mood duration with command timing
4. **Emergency priority** - Emergency commands interrupt all others
5. **RC coexistence** - RC has priority 9, AI moods priority 7

---

## Safety Considerations

1. **Servo Range Validation** - Keep servos 500-2500µs (safe range)
2. **Photosensitivity Warning** - Use flash modes cautiously
3. **Sound Volume** - Adjust per environment
4. **Emergency Stop** - Always have kill switch ready
5. **Carriage Return** - Missing `\r` causes command failure

---

## Implementation Notes

- All commands terminate with `\r` for serial communication
- Commands can be sent as strings via UART/Serial/I2C
- HCR commands use angle bracket containers `<...>`
- FlthyHP commands are direct designator-type-sequence format
- Maestro/WCB commands use semicolon prefix `;M` or `;W`
- Validate command format before transmission
- Log all commands for debugging
- Handle response messages from query commands

---

## Quick Reference: Command Prefixes

| Prefix | System | Example |
|--------|--------|---------|
| `;W#;` | WCB Board | `;W2;S2:PS4\r` |
| `;M###` | Maestro | `;M309\r` |
| `[FRTA]0` | FlthyHP LED | `F0036\r` |
| `[FRTA]1` | FlthyHP Servo | `A1011\r` |
| `#T#` | PSI T-Mode | `4T6\r` |
| `<...>` | HCR Vocalizer | `<SH1>\r` |

**Remember: ALL commands need `\r` termination!**

---

## Python Implementation

See `wcb_hardware_commands.py` for:
- Complete enum definitions
- Command builders
- Validation functions
- Pre-built mood combinations
- Serial transmission utilities

## Testing

```python
from wcb_hardware_commands import *

# Build commands
cmd = WCBCommandBuilder.flthy_hp_led(
    FlthyHPDesignator.FRONT,
    FlthyHPLEDSequence.DIM_PULSE,
    FlthyHPColor.MAGENTA,
    speed=6
)

# Validate
valid, cmd_type = WCBCommandValidator.validate_any(cmd.command)

# Send
serial_cmd = cmd.to_serial()  # Adds \r automatically
serial_bytes = cmd.to_bytes()  # UTF-8 encoded with \r
```

---

**Document Version:** 1.0
**Last Updated:** 2025-10-05
**Source:** Hardware creator's official documentation
**Critical Note:** Serial commands REQUIRE `\r` termination
