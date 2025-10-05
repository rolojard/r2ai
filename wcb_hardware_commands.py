"""
WCB Hardware Command Library
Direct implementation from hardware creator's documentation
All commands require \r (carriage return) termination for serial communication
"""

from enum import Enum
from typing import List, Dict, Optional
from dataclasses import dataclass


class PeriscopeCommand(Enum):
    """Periscope WCB2 Commands - Board ;W2;"""
    RANDOM_FAST = ";W2;S2:PS4"     # Random fast periscope movement
    RANDOM_SLOW = ";W2;S2:PS5"     # Random slow periscope movement
    DOWN = ";W2;S2:PS1"             # Periscope down (retracted)
    UP = ";W2;S2:PS2"               # Periscope up (extended)
    SNEAKY = ";W2;S2:PS0"           # Sneaky periscope movement


class PSICommand(Enum):
    """PSI Display Commands - WCB3 Board ;W3;"""
    LEIA_20SEC = ";W3;S34T6|20"     # Leia hologram 20 seconds
    HEART = ";W3;S34T7"             # Heart pattern
    PATTERN_3 = ";W3;S30T3"         # Pattern 3
    PATTERN_50 = ";S50T3"           # Pattern 50 (address 5, rear PSI)
    GLOBAL_3 = ";W30T3"             # Global pattern 3


class PSIMode(Enum):
    """PSI T-Mode Commands - Requires address prefix"""
    OFF = 0                         # Turn panel off
    SWIPE = 1                       # Default swipe pattern
    FLASH_FAST = 2                  # Fast flash (4 sec) - caution with photosensitivity
    ALARM_SLOW = 3                  # Slow flash alarm (4 sec)
    SHORT_CIRCUIT = 4               # Short circuit effect (10 sec)
    SCREAM = 5                      # Scream effect (4 sec)
    LEIA_MESSAGE = 6                # Leia message (34 sec)
    HEART_U = 7                     # I heart U (10 sec)
    QUARTER_SWEEP = 8               # Quarter panel sweep (7 sec)
    HEART_PULSE = 9                 # Flashing red heart / pulse monitor
    STAR_WARS_SCROLL = 10           # Star Wars title scroll (15 sec)
    IMPERIAL_MARCH = 11             # Imperial March (47 sec)
    DISCO_BALL = 12                 # Disco ball (4 sec)
    DISCO_BALL_CONT = 13            # Disco ball continuous
    REBEL_SYMBOL = 14               # Rebel symbol (5 sec)
    KNIGHT_RIDER = 15               # Knight Rider effect (20 sec)
    TEST_WHITE = 16                 # Test sequence white continuous
    RED_ON = 17                     # Red on continuous
    GREEN_ON = 18                   # Green on continuous
    LIGHTSABER_BATTLE = 19          # Light saber battle
    SW_INTRO_SCROLL = 20            # Star Wars intro scroll
    VU_METER = 21                   # VU Meter (4 sec)
    VU_METER_CONT = 92              # VU Meter continuous


class PSIAddress(Enum):
    """PSI Address Modifiers for T commands"""
    GLOBAL = 0                      # All displays
    TFLD = 1                        # Top Front Logic Display
    BFLD = 2                        # Bottom Front Logic Display
    RLD = 3                         # Rear Logic Display
    FRONT_PSI = 4                   # Front PSI
    REAR_PSI = 5                    # Rear PSI
    FRONT_HOLO = 6                  # Front Holo (not implemented)
    REAR_HOLO = 7                   # Rear Holo (not implemented)
    TOP_HOLO = 8                    # Top Holo (not implemented)


class MaestroDomeCommand(Enum):
    """Maestro Dome Commands - Board ;M3##"""
    OPEN = ";M301"                  # Dome open
    FAST_TOP = ";M302"              # Fast top movement
    BYE = ";M303"                   # Bye gesture
    CLOSE = ";M304"                 # Dome close
    ALT_OPEN_CLOSE = ";M305"        # Alternate open/close
    FAST_ALT = ";M306"              # Fast alternate
    BREATHING = ";M307"             # Breathing movement
    LONG_RANDOM = ";M308"           # Long random sequence
    SCREAM = ";M309"                # Scream movement
    COME_HERE = ";M310"             # Come here gesture
    SLOW_TO_FAST = ";M311"          # Slow to fast acceleration


class MaestroBodyCommand(Enum):
    """Maestro Body/Arms Commands - Board ;M1#"""
    ARMS_OPEN_CLOSE = ";M11"        # Arms open and close
    ARMS_WAVE = ";M12"              # Arms wave
    ARMS_OPEN = ";M13"              # Arms open
    ARMS_CLOSED = ";M14"            # Arms closed
    ARMS_RANDOM = ";M15"            # Arms random movement


class FlthyHPDesignator(Enum):
    """Holo Projector Designators"""
    FRONT = "F"                     # Front HP
    REAR = "R"                      # Rear HP
    TOP = "T"                       # Top HP
    ALL = "A"                       # All 3 HPs


class FlthyHPLEDSequence(Enum):
    """LED Function Sequences (Type 0)"""
    LEIA = "01"                     # Leia sequence, random blue shades
    COLOR_PROJECTOR = "02"          # Color projector using color value
    DIM_PULSE = "03"                # Color slowly pulses (with speed)
    CYCLE = "04"                    # Cycle using color value
    SHORT_CIRCUIT = "05"            # LED flash slowing over time
    TOGGLE_COLOR = "06"             # Solid color
    RAINBOW = "07"                  # Rainbow sequence
    CLEAR_NO_AUTO = "96"            # Clear LED, disable auto
    CLEAR_AUTO_DEFAULT = "971"      # Clear, enable auto default
    CLEAR_AUTO_RANDOM = "972"       # Clear, enable auto random
    CLEAR_OFF_COLOR = "98"          # Clear, enable off color
    CLEAR_OFF_AUTO_DEFAULT = "991"  # Clear, off color, auto default
    CLEAR_OFF_AUTO_RANDOM = "992"   # Clear, off color, auto random


class FlthyHPServoSequence(Enum):
    """Servo Function Sequences (Type 1)"""
    PRESET_POS = "01"               # Send to preset position (needs P value)
    RC_LEFT_RIGHT = "02"            # Enable RC left/right
    RC_UP_DOWN = "03"               # Enable RC up/down
    RANDOM_POS = "04"               # Random position
    WAG_LEFT_RIGHT = "05"           # Wag left/right
    WAG_UP_DOWN = "06"              # Wag up/down
    DISABLE_TWITCH = "98"           # Disable auto twitch
    ENABLE_TWITCH = "99"            # Enable auto twitch


class FlthyHPColor(Enum):
    """HP Color Values"""
    RED = "1"
    YELLOW = "2"
    GREEN = "3"
    CYAN = "4"
    BLUE = "5"
    MAGENTA = "6"
    ORANGE = "7"
    PURPLE = "8"
    WHITE = "9"
    RANDOM = "0"


class FlthyHPPosition(Enum):
    """HP Preset Positions"""
    DOWN = "0"
    CENTER = "1"
    UP = "2"
    LEFT = "3"
    UPPER_LEFT = "4"
    LOWER_LEFT = "5"
    RIGHT = "6"
    UPPER_RIGHT = "7"
    LOWER_RIGHT = "8"


class HCRStimulus(Enum):
    """HCR Vocalizer Emotional Stimulus Commands"""
    HAPPY_MILD = "SH0"              # Mild happy vocalization
    HAPPY_EXTREME = "SH1"           # Extreme happy vocalization
    SAD_MILD = "SS0"                # Mild sad vocalization
    SAD_EXTREME = "SS1"             # Extreme sad vocalization
    ANGRY_MILD = "SM0"              # Mild angry vocalization
    ANGRY_EXTREME = "SM1"           # Extreme angry vocalization
    SCARED_MILD = "SC0"             # Mild scared vocalization
    SCARED_EXTREME = "SC1"          # Extreme scared vocalization
    ELECTROCUTION = "SE"            # Overload/electrocution


class HCRMuseCommand(Enum):
    """HCR Muse (Background Sounds) Commands"""
    ENABLE = "M1"                   # Enable muse
    DISABLE = "M0"                  # Disable muse
    TOGGLE = "MT"                   # Toggle muse
    TRIGGER_SINGLE = "MM"           # Trigger single musing


class HCRPlaybackCommand(Enum):
    """HCR Audio Playback Commands"""
    STOP_VOC_IMMEDIATE = "PSV"      # Stop vocalizer immediately
    STOP_VOC_GRACEFUL = "PSG"       # Stop vocalizer gracefully
    STOP_WAV_A = "PSA"              # Stop WAV channel A
    STOP_WAV_B = "PSB"              # Stop WAV channel B


class HCROverrideCommand(Enum):
    """HCR Personality Override Commands"""
    IMPROVISED_MODE = "OA0"         # Enable improvisational mode
    CANONICAL_MODE = "OA1"          # Enable canonical mode
    ENABLE_OVERRIDE = "O1"          # Enable personality override
    DISABLE_OVERRIDE = "O0"         # Disable personality override
    RESET_EMOTIONS = "OR"           # Reset all emotions to 0


@dataclass
class WCBCommand:
    """Complete WCB command with carriage return"""
    command: str
    description: str

    def to_serial(self) -> str:
        """Convert to serial format with \r termination"""
        return f"{self.command}\r"

    def to_bytes(self) -> bytes:
        """Convert to bytes for serial transmission"""
        return self.to_serial().encode('utf-8')


class WCBCommandBuilder:
    """Build complex WCB commands from components"""

    @staticmethod
    def psi_mode(address: PSIAddress, mode: PSIMode) -> WCBCommand:
        """Build PSI T-mode command: address + T + mode"""
        cmd = f"{address.value}T{mode.value}"
        return WCBCommand(
            command=cmd,
            description=f"PSI {address.name} mode {mode.name}"
        )

    @staticmethod
    def flthy_hp_led(designator: FlthyHPDesignator, sequence: FlthyHPLEDSequence,
                     color: Optional[FlthyHPColor] = None, speed: Optional[int] = None) -> WCBCommand:
        """Build FlthyHP LED command: D + 0 + sequence + [color] + [speed]"""
        cmd = f"{designator.value}0{sequence.value}"
        desc_parts = [f"{designator.name} HP LED {sequence.name}"]

        if color and sequence.value in ["02", "03", "04", "06"]:
            cmd += color.value
            desc_parts.append(f"color {color.name}")

        if speed is not None and sequence.value == "03":
            cmd += str(speed)
            desc_parts.append(f"speed {speed}")

        return WCBCommand(command=cmd, description=" ".join(desc_parts))

    @staticmethod
    def flthy_hp_servo(designator: FlthyHPDesignator, sequence: FlthyHPServoSequence,
                       position: Optional[FlthyHPPosition] = None) -> WCBCommand:
        """Build FlthyHP servo command: D + 1 + sequence + [position]"""
        cmd = f"{designator.value}1{sequence.value}"
        desc_parts = [f"{designator.name} HP servo {sequence.name}"]

        if position and sequence.value == "01":
            cmd += position.value
            desc_parts.append(f"position {position.name}")

        return WCBCommand(command=cmd, description=" ".join(desc_parts))

    @staticmethod
    def hcr_emotion(stimulus: HCRStimulus) -> WCBCommand:
        """Build HCR emotional command: <stimulus>"""
        return WCBCommand(
            command=f"<{stimulus.value}>",
            description=f"HCR {stimulus.name} emotion"
        )

    @staticmethod
    def hcr_play_wav(channel: str, file_num: int, random_end: Optional[int] = None) -> WCBCommand:
        """Build HCR WAV playback: <C[A|B]####[C####]>"""
        if random_end:
            cmd = f"<C{channel}{file_num:04d}C{random_end:04d}>"
            desc = f"Play random WAV {file_num}-{random_end} on channel {channel}"
        else:
            cmd = f"<C{channel}{file_num:04d}>"
            desc = f"Play WAV {file_num} on channel {channel}"

        return WCBCommand(command=cmd, description=desc)

    @staticmethod
    def hcr_set_emotion(emotion: str, value: int) -> WCBCommand:
        """Build HCR emotion setter: <O[H|S|M|C]#>"""
        emotion_map = {"happy": "H", "sad": "S", "mad": "M", "scared": "C"}
        letter = emotion_map.get(emotion.lower(), "H")
        return WCBCommand(
            command=f"<O{letter}{value}>",
            description=f"Set {emotion} emotion to {value}"
        )

    @staticmethod
    def hcr_chain(*commands: str) -> WCBCommand:
        """Chain multiple HCR commands: <cmd1,cmd2,...>"""
        chained = ",".join(commands)
        return WCBCommand(
            command=f"<{chained}>",
            description=f"Chained HCR: {len(commands)} commands"
        )


# Pre-built common command sets for mood integration
class CommonMoodCommands:
    """Ready-to-use command combinations for mood orchestration"""

    @staticmethod
    def idle_relaxed() -> List[WCBCommand]:
        """Idle relaxed state commands"""
        return [
            WCBCommand(";M304", "Dome close/center"),
            WCBCommandBuilder.psi_mode(PSIAddress.FRONT_PSI, PSIMode.SWIPE),
            WCBCommandBuilder.flthy_hp_led(FlthyHPDesignator.ALL, FlthyHPLEDSequence.DIM_PULSE,
                                          FlthyHPColor.BLUE, 3),
            WCBCommandBuilder.hcr_emotion(HCRStimulus.HAPPY_MILD)
        ]

    @staticmethod
    def alert_curious() -> List[WCBCommand]:
        """Alert curious state commands"""
        return [
            WCBCommand(";M301", "Dome open"),
            WCBCommand(";W2;S2:PS2", "Periscope up"),
            WCBCommandBuilder.psi_mode(PSIAddress.GLOBAL, PSIMode.SWIPE),
            WCBCommandBuilder.flthy_hp_led(FlthyHPDesignator.FRONT, FlthyHPLEDSequence.TOGGLE_COLOR,
                                          FlthyHPColor.CYAN)
        ]

    @staticmethod
    def excited_happy() -> List[WCBCommand]:
        """Excited happy state commands"""
        return [
            WCBCommand(";M12", "Arms wave"),
            WCBCommand(";M306", "Dome fast alternate"),
            WCBCommand(";W2;S2:PS4", "Periscope random fast"),
            WCBCommandBuilder.psi_mode(PSIAddress.GLOBAL, PSIMode.DISCO_BALL),
            WCBCommandBuilder.flthy_hp_led(FlthyHPDesignator.ALL, FlthyHPLEDSequence.RAINBOW),
            WCBCommandBuilder.hcr_emotion(HCRStimulus.HAPPY_EXTREME),
            WCBCommandBuilder.hcr_play_wav("A", 25)  # Happy sound
        ]

    @staticmethod
    def protective_alert() -> List[WCBCommand]:
        """Protective alert state commands"""
        return [
            WCBCommand(";M309", "Dome scream movement"),
            WCBCommand(";W2;S2:PS2", "Periscope up alert"),
            WCBCommandBuilder.psi_mode(PSIAddress.GLOBAL, PSIMode.ALARM_SLOW),
            WCBCommandBuilder.flthy_hp_led(FlthyHPDesignator.ALL, FlthyHPLEDSequence.TOGGLE_COLOR,
                                          FlthyHPColor.RED),
            WCBCommandBuilder.hcr_emotion(HCRStimulus.ANGRY_MILD)
        ]

    @staticmethod
    def emergency_panic() -> List[WCBCommand]:
        """Emergency panic state commands"""
        return [
            WCBCommand(";M304", "Dome close/center"),
            WCBCommand(";W2;S2:PS1", "Periscope down (safe)"),
            WCBCommand(";M14", "Arms closed"),
            WCBCommandBuilder.psi_mode(PSIAddress.GLOBAL, PSIMode.FLASH_FAST),
            WCBCommandBuilder.flthy_hp_led(FlthyHPDesignator.ALL, FlthyHPLEDSequence.SHORT_CIRCUIT),
            WCBCommandBuilder.hcr_emotion(HCRStimulus.SCARED_EXTREME),
            WCBCommandBuilder.hcr_play_wav("A", 47)  # Alarm sound
        ]

    @staticmethod
    def jedi_respect() -> List[WCBCommand]:
        """Jedi respect gesture commands"""
        return [
            WCBCommand(";M303", "Dome bye/bow"),
            WCBCommand(";W2;S2:PS1", "Periscope retracted"),
            WCBCommandBuilder.psi_mode(PSIAddress.GLOBAL, PSIMode.HEART_U),
            WCBCommandBuilder.flthy_hp_led(FlthyHPDesignator.ALL, FlthyHPLEDSequence.DIM_PULSE,
                                          FlthyHPColor.BLUE, 2),
            WCBCommandBuilder.hcr_set_emotion("happy", 80)
        ]


# Command validation and testing utilities
class WCBCommandValidator:
    """Validate command format before transmission"""

    @staticmethod
    def validate_wcb_command(cmd: str) -> bool:
        """Validate WCB board command format"""
        return cmd.startswith(";W") and len(cmd) > 3

    @staticmethod
    def validate_psi_t_command(cmd: str) -> bool:
        """Validate PSI T-mode command format (address + T + mode)"""
        if len(cmd) < 2:
            return False
        # Format: #T# or #T## (address, T, mode number)
        parts = cmd.split('T')
        if len(parts) != 2:
            return False
        try:
            int(parts[0])  # Address must be numeric
            int(parts[1])  # Mode must be numeric
            return True
        except ValueError:
            return False

    @staticmethod
    def validate_maestro_command(cmd: str) -> bool:
        """Validate Maestro command format"""
        return cmd.startswith(";M") and len(cmd) >= 4

    @staticmethod
    def validate_flthy_hp_command(cmd: str) -> bool:
        """Validate FlthyHP command format"""
        if len(cmd) < 4:
            return False
        designator = cmd[0]
        type_code = cmd[1]
        return (designator in ["F", "R", "T", "A"] and
                type_code in ["0", "1"])

    @staticmethod
    def validate_hcr_command(cmd: str) -> bool:
        """Validate HCR command format"""
        return cmd.startswith("<") and cmd.endswith(">")

    @staticmethod
    def validate_any(cmd: str) -> tuple[bool, str]:
        """Validate any command type and return type"""
        validators = [
            (WCBCommandValidator.validate_wcb_command, "WCB"),
            (WCBCommandValidator.validate_maestro_command, "Maestro"),
            (WCBCommandValidator.validate_flthy_hp_command, "FlthyHP"),
            (WCBCommandValidator.validate_hcr_command, "HCR"),
            (WCBCommandValidator.validate_psi_t_command, "PSI-T")
        ]

        for validator, cmd_type in validators:
            if validator(cmd):
                return True, cmd_type

        return False, "Unknown"


if __name__ == "__main__":
    # Example usage and testing
    print("=== WCB Hardware Command Library ===\n")

    # Test PSI command
    psi_cmd = WCBCommandBuilder.psi_mode(PSIAddress.FRONT_PSI, PSIMode.LEIA_MESSAGE)
    print(f"PSI Command: {psi_cmd.to_serial()!r} - {psi_cmd.description}")

    # Test FlthyHP LED
    hp_led = WCBCommandBuilder.flthy_hp_led(FlthyHPDesignator.FRONT,
                                             FlthyHPLEDSequence.DIM_PULSE,
                                             FlthyHPColor.MAGENTA, 6)
    print(f"HP LED: {hp_led.to_serial()!r} - {hp_led.description}")

    # Test HCR emotion
    hcr = WCBCommandBuilder.hcr_emotion(HCRStimulus.HAPPY_EXTREME)
    print(f"HCR: {hcr.to_serial()!r} - {hcr.description}")

    # Test mood command set
    print("\n=== Excited Happy Mood Commands ===")
    for cmd in CommonMoodCommands.excited_happy():
        valid, cmd_type = WCBCommandValidator.validate_any(cmd.command)
        status = "✅" if valid else "❌"
        print(f"{status} [{cmd_type}] {cmd.to_serial()!r} - {cmd.description}")
