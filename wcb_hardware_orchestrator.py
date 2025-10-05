"""
WCB Hardware Orchestrator
Integrates hardware creator's commands with R2D2 behavioral intelligence
Uses actual hardware command format with \r termination
"""

import serial
import time
import logging
from enum import Enum
from typing import List, Dict, Optional
from wcb_hardware_commands import (
    WCBCommand, WCBCommandBuilder, CommonMoodCommands,
    PeriscopeCommand, MaestroDomeCommand, MaestroBodyCommand,
    PSIAddress, PSIMode, FlthyHPDesignator, FlthyHPLEDSequence,
    FlthyHPServoSequence, FlthyHPColor, FlthyHPPosition,
    HCRStimulus, WCBCommandValidator
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class R2D2Mood(Enum):
    """27 R2D2 Personality Moods"""
    # Primary Emotional (1-6)
    IDLE_RELAXED = 1
    IDLE_BORED = 2
    ALERT_CURIOUS = 3
    ALERT_CAUTIOUS = 4
    EXCITED_HAPPY = 5
    EXCITED_MISCHIEVOUS = 6

    # Social Interaction (7-10)
    GREETING_FRIENDLY = 7
    GREETING_SHY = 8
    FAREWELL_SAD = 9
    FAREWELL_HOPEFUL = 10

    # Character-Specific (11-14)
    STUBBORN_DEFIANT = 11
    STUBBORN_POUTY = 12
    PROTECTIVE_ALERT = 13
    PROTECTIVE_AGGRESSIVE = 14

    # Activity States (15-20)
    SCANNING_METHODICAL = 15
    SCANNING_FRANTIC = 16
    TRACKING_FOCUSED = 17
    TRACKING_PLAYFUL = 18
    DEMONSTRATING_CONFIDENT = 19
    DEMONSTRATING_NERVOUS = 20

    # Performance (21-24)
    ENTERTAINING_CROWD = 21
    ENTERTAINING_INTIMATE = 22
    JEDI_RESPECT = 23
    SITH_ALERT = 24

    # Special (25-27)
    MAINTENANCE_COOPERATIVE = 25
    EMERGENCY_CALM = 26
    EMERGENCY_PANIC = 27


class HardwareOrchestrator:
    """Orchestrate hardware commands for R2D2 moods"""

    def __init__(self, port: str = '/dev/ttyUSB0', baud: int = 9600, simulation: bool = False):
        self.port = port
        self.baud = baud
        self.simulation = simulation
        self.serial = None
        self.last_mood = None

        # Mood to hardware command mapping
        self.mood_commands = self._build_mood_command_map()

    def connect(self) -> bool:
        """Connect to WCB hardware"""
        if self.simulation:
            logger.info("🔧 Running in SIMULATION mode (no hardware)")
            return True

        try:
            self.serial = serial.Serial(self.port, self.baud, timeout=1)
            time.sleep(2)  # Allow connection to stabilize
            logger.info(f"✅ Connected to WCB hardware on {self.port}")
            return True
        except Exception as e:
            logger.error(f"❌ Hardware connection failed: {e}")
            return False

    def disconnect(self):
        """Disconnect from hardware"""
        if self.serial and self.serial.is_open:
            self.serial.close()
            logger.info("🔌 Disconnected from WCB hardware")

    def send_command(self, command: WCBCommand) -> bool:
        """Send single hardware command with validation"""
        # Validate command format
        valid, cmd_type = WCBCommandValidator.validate_any(command.command)
        if not valid:
            logger.error(f"❌ Invalid command format: {command.command}")
            return False

        serial_cmd = command.to_serial()

        if self.simulation:
            logger.info(f"🔧 [SIMULATION] [{cmd_type}] {serial_cmd!r} - {command.description}")
            return True

        try:
            if not self.serial or not self.serial.is_open:
                logger.error("❌ Serial port not connected")
                return False

            self.serial.write(command.to_bytes())
            self.serial.flush()
            logger.info(f"📤 [{cmd_type}] {serial_cmd!r} - {command.description}")
            return True

        except Exception as e:
            logger.error(f"❌ Command transmission failed: {e}")
            return False

    def send_command_sequence(self, commands: List[WCBCommand], delay_ms: int = 100) -> bool:
        """Send sequence of commands with timing"""
        success = True
        for i, cmd in enumerate(commands):
            if not self.send_command(cmd):
                logger.warning(f"⚠️ Command {i+1}/{len(commands)} failed, continuing...")
                success = False

            # Delay between commands (except last)
            if i < len(commands) - 1 and delay_ms > 0:
                time.sleep(delay_ms / 1000.0)

        return success

    def execute_mood(self, mood: R2D2Mood, priority: int = 7) -> bool:
        """Execute mood command sequence"""
        if mood not in self.mood_commands:
            logger.error(f"❌ Mood {mood.name} not configured")
            return False

        commands = self.mood_commands[mood]
        logger.info(f"🎭 Executing mood: {mood.name} (priority {priority})")
        logger.info(f"📋 Commands: {len(commands)}")

        success = self.send_command_sequence(commands)

        if success:
            self.last_mood = mood
            logger.info(f"✅ Mood {mood.name} executed successfully")
        else:
            logger.warning(f"⚠️ Mood {mood.name} completed with errors")

        return success

    def _build_mood_command_map(self) -> Dict[R2D2Mood, List[WCBCommand]]:
        """Build complete mood to hardware command mapping"""
        return {
            # === PRIMARY EMOTIONAL STATES ===

            R2D2Mood.IDLE_RELAXED: [
                WCBCommand(MaestroDomeCommand.CLOSE.value, "Dome centered/relaxed"),
                WCBCommandBuilder.psi_mode(PSIAddress.FRONT_PSI, PSIMode.SWIPE),
                WCBCommandBuilder.flthy_hp_led(FlthyHPDesignator.ALL,
                    FlthyHPLEDSequence.DIM_PULSE, FlthyHPColor.BLUE, 3),
                WCBCommandBuilder.hcr_emotion(HCRStimulus.HAPPY_MILD)
            ],

            R2D2Mood.IDLE_BORED: [
                WCBCommand(MaestroDomeCommand.BREATHING.value, "Dome slow breathing"),
                WCBCommandBuilder.psi_mode(PSIAddress.GLOBAL, PSIMode.ALARM_SLOW),
                WCBCommandBuilder.flthy_hp_led(FlthyHPDesignator.FRONT,
                    FlthyHPLEDSequence.DIM_PULSE, FlthyHPColor.CYAN, 2),
                WCBCommandBuilder.flthy_hp_servo(FlthyHPDesignator.REAR,
                    FlthyHPServoSequence.WAG_LEFT_RIGHT),
                WCBCommandBuilder.hcr_play_wav("A", 15)  # Bored sound
            ],

            R2D2Mood.ALERT_CURIOUS: [
                WCBCommand(MaestroDomeCommand.OPEN.value, "Dome open curious"),
                WCBCommand(PeriscopeCommand.UP.value, "Periscope extend"),
                WCBCommandBuilder.psi_mode(PSIAddress.GLOBAL, PSIMode.SWIPE),
                WCBCommandBuilder.flthy_hp_led(FlthyHPDesignator.FRONT,
                    FlthyHPLEDSequence.TOGGLE_COLOR, FlthyHPColor.CYAN),
                WCBCommandBuilder.hcr_emotion(HCRStimulus.HAPPY_MILD)
            ],

            R2D2Mood.ALERT_CAUTIOUS: [
                WCBCommand(MaestroDomeCommand.LONG_RANDOM.value, "Dome cautious scan"),
                WCBCommand(PeriscopeCommand.DOWN.value, "Periscope retract"),
                WCBCommandBuilder.psi_mode(PSIAddress.GLOBAL, PSIMode.ALARM_SLOW),
                WCBCommandBuilder.flthy_hp_led(FlthyHPDesignator.ALL,
                    FlthyHPLEDSequence.TOGGLE_COLOR, FlthyHPColor.ORANGE),
                WCBCommandBuilder.hcr_set_emotion("mad", 30)
            ],

            R2D2Mood.EXCITED_HAPPY: [
                WCBCommand(MaestroBodyCommand.ARMS_WAVE.value, "Arms wave"),
                WCBCommand(MaestroDomeCommand.FAST_ALT.value, "Dome fast alternating"),
                WCBCommand(PeriscopeCommand.RANDOM_FAST.value, "Periscope random fast"),
                WCBCommandBuilder.psi_mode(PSIAddress.GLOBAL, PSIMode.DISCO_BALL),
                WCBCommandBuilder.flthy_hp_led(FlthyHPDesignator.ALL,
                    FlthyHPLEDSequence.RAINBOW),
                WCBCommandBuilder.hcr_emotion(HCRStimulus.HAPPY_EXTREME),
                WCBCommandBuilder.hcr_play_wav("A", 25)
            ],

            R2D2Mood.EXCITED_MISCHIEVOUS: [
                WCBCommand(MaestroDomeCommand.FAST_TOP.value, "Dome fast peek"),
                WCBCommand(PeriscopeCommand.SNEAKY.value, "Periscope sneaky"),
                WCBCommandBuilder.psi_mode(PSIAddress.FRONT_PSI, PSIMode.KNIGHT_RIDER),
                WCBCommandBuilder.flthy_hp_led(FlthyHPDesignator.ALL,
                    FlthyHPLEDSequence.CYCLE, FlthyHPColor.RANDOM),
                WCBCommandBuilder.hcr_play_wav("A", 33)  # Mischievous giggle
            ],

            # === SOCIAL INTERACTION ===

            R2D2Mood.GREETING_FRIENDLY: [
                WCBCommand(MaestroBodyCommand.ARMS_WAVE.value, "Arms wave greeting"),
                WCBCommand(MaestroDomeCommand.OPEN.value, "Dome open"),
                WCBCommand(PeriscopeCommand.UP.value, "Periscope up greeting"),
                WCBCommandBuilder.psi_mode(PSIAddress.GLOBAL, PSIMode.HEART_U),
                WCBCommandBuilder.flthy_hp_led(FlthyHPDesignator.ALL,
                    FlthyHPLEDSequence.RAINBOW),
                WCBCommandBuilder.hcr_emotion(HCRStimulus.HAPPY_EXTREME),
                WCBCommandBuilder.hcr_play_wav("A", 10)  # Greeting beep
            ],

            R2D2Mood.GREETING_SHY: [
                WCBCommand(MaestroDomeCommand.BYE.value, "Dome turn away shy"),
                WCBCommand(PeriscopeCommand.DOWN.value, "Periscope down"),
                WCBCommandBuilder.psi_mode(PSIAddress.FRONT_PSI, PSIMode.SWIPE),
                WCBCommandBuilder.flthy_hp_led(FlthyHPDesignator.ALL,
                    FlthyHPLEDSequence.DIM_PULSE, FlthyHPColor.BLUE, 2),
                WCBCommandBuilder.hcr_emotion(HCRStimulus.HAPPY_MILD)
            ],

            R2D2Mood.FAREWELL_SAD: [
                WCBCommand(MaestroDomeCommand.BYE.value, "Dome goodbye"),
                WCBCommand(MaestroBodyCommand.ARMS_WAVE.value, "Arms sad wave"),
                WCBCommandBuilder.psi_mode(PSIAddress.GLOBAL, PSIMode.ALARM_SLOW),
                WCBCommandBuilder.flthy_hp_led(FlthyHPDesignator.ALL,
                    FlthyHPLEDSequence.DIM_PULSE, FlthyHPColor.BLUE, 1),
                WCBCommandBuilder.hcr_emotion(HCRStimulus.SAD_EXTREME),
                WCBCommandBuilder.hcr_play_wav("A", 18)  # Sad farewell
            ],

            R2D2Mood.FAREWELL_HOPEFUL: [
                WCBCommand(MaestroDomeCommand.BYE.value, "Dome hopeful goodbye"),
                WCBCommand(MaestroBodyCommand.ARMS_WAVE.value, "Arms wave"),
                WCBCommandBuilder.psi_mode(PSIAddress.GLOBAL, PSIMode.SWIPE),
                WCBCommandBuilder.flthy_hp_led(FlthyHPDesignator.ALL,
                    FlthyHPLEDSequence.TOGGLE_COLOR, FlthyHPColor.CYAN),
                WCBCommandBuilder.hcr_set_emotion("happy", 60),
                WCBCommandBuilder.hcr_play_wav("A", 12)  # Hopeful beep
            ],

            # === CHARACTER-SPECIFIC ===

            R2D2Mood.STUBBORN_DEFIANT: [
                WCBCommand(MaestroDomeCommand.SCREAM.value, "Dome defiant turn"),
                WCBCommand(MaestroBodyCommand.ARMS_CLOSED.value, "Arms closed defiant"),
                WCBCommandBuilder.psi_mode(PSIAddress.GLOBAL, PSIMode.FLASH_FAST),
                WCBCommandBuilder.flthy_hp_led(FlthyHPDesignator.ALL,
                    FlthyHPLEDSequence.TOGGLE_COLOR, FlthyHPColor.RED),
                WCBCommandBuilder.hcr_emotion(HCRStimulus.ANGRY_EXTREME),
                WCBCommandBuilder.hcr_play_wav("A", 55)  # Raspberry/defiant sound
            ],

            R2D2Mood.STUBBORN_POUTY: [
                WCBCommand(MaestroDomeCommand.BYE.value, "Dome turn away pouty"),
                WCBCommand(PeriscopeCommand.DOWN.value, "Periscope down"),
                WCBCommandBuilder.psi_mode(PSIAddress.GLOBAL, PSIMode.ALARM_SLOW),
                WCBCommandBuilder.flthy_hp_led(FlthyHPDesignator.ALL,
                    FlthyHPLEDSequence.DIM_PULSE, FlthyHPColor.PURPLE, 1),
                WCBCommandBuilder.hcr_emotion(HCRStimulus.SAD_MILD),
                WCBCommandBuilder.hcr_play_wav("A", 20)  # Pouty grumble
            ],

            R2D2Mood.PROTECTIVE_ALERT: [
                WCBCommand(MaestroDomeCommand.SCREAM.value, "Dome alert scan"),
                WCBCommand(PeriscopeCommand.UP.value, "Periscope alert position"),
                WCBCommand(MaestroBodyCommand.ARMS_OPEN.value, "Arms protective stance"),
                WCBCommandBuilder.psi_mode(PSIAddress.GLOBAL, PSIMode.ALARM_SLOW),
                WCBCommandBuilder.flthy_hp_led(FlthyHPDesignator.ALL,
                    FlthyHPLEDSequence.TOGGLE_COLOR, FlthyHPColor.YELLOW),
                WCBCommandBuilder.hcr_emotion(HCRStimulus.ANGRY_MILD),
                WCBCommandBuilder.hcr_play_wav("A", 40)  # Alert beep
            ],

            R2D2Mood.PROTECTIVE_AGGRESSIVE: [
                WCBCommand(MaestroDomeCommand.SCREAM.value, "Dome aggressive"),
                WCBCommand(MaestroBodyCommand.ARMS_OPEN.value, "Arms aggressive stance"),
                WCBCommand(PeriscopeCommand.UP.value, "Periscope full alert"),
                WCBCommandBuilder.psi_mode(PSIAddress.GLOBAL, PSIMode.FLASH_FAST),
                WCBCommandBuilder.flthy_hp_led(FlthyHPDesignator.ALL,
                    FlthyHPLEDSequence.TOGGLE_COLOR, FlthyHPColor.RED),
                WCBCommandBuilder.hcr_emotion(HCRStimulus.ANGRY_EXTREME),
                WCBCommandBuilder.hcr_play_wav("A", 58)  # Aggressive alarm
            ],

            # === ACTIVITY STATES ===

            R2D2Mood.SCANNING_METHODICAL: [
                WCBCommand(MaestroDomeCommand.LONG_RANDOM.value, "Dome slow methodical scan"),
                WCBCommand(PeriscopeCommand.RANDOM_SLOW.value, "Periscope methodical"),
                WCBCommandBuilder.psi_mode(PSIAddress.GLOBAL, PSIMode.KNIGHT_RIDER),
                WCBCommandBuilder.flthy_hp_servo(FlthyHPDesignator.ALL,
                    FlthyHPServoSequence.RANDOM_POS),
                WCBCommandBuilder.hcr_play_wav("A", 30)  # Scanning beeps
            ],

            R2D2Mood.SCANNING_FRANTIC: [
                WCBCommand(MaestroDomeCommand.FAST_ALT.value, "Dome frantic scan"),
                WCBCommand(PeriscopeCommand.RANDOM_FAST.value, "Periscope frantic"),
                WCBCommandBuilder.psi_mode(PSIAddress.GLOBAL, PSIMode.VU_METER_CONT),
                WCBCommandBuilder.flthy_hp_led(FlthyHPDesignator.ALL,
                    FlthyHPLEDSequence.CYCLE, FlthyHPColor.RANDOM),
                WCBCommandBuilder.hcr_emotion(HCRStimulus.SCARED_MILD),
                WCBCommandBuilder.hcr_play_wav("A", 35)  # Frantic beeps
            ],

            R2D2Mood.TRACKING_FOCUSED: [
                WCBCommand(MaestroDomeCommand.SLOW_TO_FAST.value, "Dome tracking"),
                WCBCommand(PeriscopeCommand.UP.value, "Periscope tracking"),
                WCBCommandBuilder.psi_mode(PSIAddress.GLOBAL, PSIMode.SWIPE),
                WCBCommandBuilder.flthy_hp_servo(FlthyHPDesignator.FRONT,
                    FlthyHPServoSequence.RANDOM_POS),
                WCBCommandBuilder.hcr_play_wav("A", 32)  # Focused tracking
            ],

            R2D2Mood.TRACKING_PLAYFUL: [
                WCBCommand(MaestroDomeCommand.FAST_TOP.value, "Dome playful tracking"),
                WCBCommand(PeriscopeCommand.SNEAKY.value, "Periscope playful"),
                WCBCommandBuilder.psi_mode(PSIAddress.GLOBAL, PSIMode.DISCO_BALL_CONT),
                WCBCommandBuilder.flthy_hp_led(FlthyHPDesignator.ALL,
                    FlthyHPLEDSequence.RAINBOW),
                WCBCommandBuilder.hcr_emotion(HCRStimulus.HAPPY_EXTREME)
            ],

            R2D2Mood.DEMONSTRATING_CONFIDENT: [
                WCBCommand(MaestroBodyCommand.ARMS_OPEN_CLOSE.value, "Arms demonstration"),
                WCBCommand(MaestroDomeCommand.OPEN.value, "Dome confident"),
                WCBCommandBuilder.psi_mode(PSIAddress.GLOBAL, PSIMode.STAR_WARS_SCROLL),
                WCBCommandBuilder.flthy_hp_led(FlthyHPDesignator.ALL,
                    FlthyHPLEDSequence.TOGGLE_COLOR, FlthyHPColor.GREEN),
                WCBCommandBuilder.hcr_set_emotion("happy", 90),
                WCBCommandBuilder.hcr_play_wav("A", 22)  # Confident beep
            ],

            R2D2Mood.DEMONSTRATING_NERVOUS: [
                WCBCommand(MaestroBodyCommand.ARMS_RANDOM.value, "Arms nervous"),
                WCBCommand(MaestroDomeCommand.BREATHING.value, "Dome nervous"),
                WCBCommandBuilder.psi_mode(PSIAddress.GLOBAL, PSIMode.ALARM_SLOW),
                WCBCommandBuilder.flthy_hp_led(FlthyHPDesignator.ALL,
                    FlthyHPLEDSequence.DIM_PULSE, FlthyHPColor.YELLOW, 5),
                WCBCommandBuilder.hcr_emotion(HCRStimulus.SCARED_MILD)
            ],

            # === PERFORMANCE STATES ===

            R2D2Mood.ENTERTAINING_CROWD: [
                WCBCommand(MaestroBodyCommand.ARMS_WAVE.value, "Arms crowd entertainment"),
                WCBCommand(MaestroDomeCommand.FAST_ALT.value, "Dome entertainment"),
                WCBCommand(PeriscopeCommand.RANDOM_FAST.value, "Periscope show"),
                WCBCommandBuilder.psi_mode(PSIAddress.GLOBAL, PSIMode.IMPERIAL_MARCH),
                WCBCommandBuilder.flthy_hp_led(FlthyHPDesignator.ALL,
                    FlthyHPLEDSequence.RAINBOW),
                WCBCommandBuilder.hcr_emotion(HCRStimulus.HAPPY_EXTREME),
                WCBCommandBuilder.hcr_play_wav("A", 50)  # Entertainment music
            ],

            R2D2Mood.ENTERTAINING_INTIMATE: [
                WCBCommand(MaestroBodyCommand.ARMS_WAVE.value, "Arms intimate performance"),
                WCBCommand(MaestroDomeCommand.OPEN.value, "Dome gentle"),
                WCBCommandBuilder.psi_mode(PSIAddress.GLOBAL, PSIMode.HEART_U),
                WCBCommandBuilder.flthy_hp_led(FlthyHPDesignator.ALL,
                    FlthyHPLEDSequence.DIM_PULSE, FlthyHPColor.MAGENTA, 4),
                WCBCommandBuilder.hcr_set_emotion("happy", 70),
                WCBCommandBuilder.hcr_play_wav("A", 28)  # Gentle music
            ],

            R2D2Mood.JEDI_RESPECT: [
                WCBCommand(MaestroDomeCommand.BYE.value, "Dome respectful bow"),
                WCBCommand(MaestroBodyCommand.ARMS_CLOSED.value, "Arms respectful"),
                WCBCommand(PeriscopeCommand.DOWN.value, "Periscope retract respect"),
                WCBCommandBuilder.psi_mode(PSIAddress.GLOBAL, PSIMode.HEART_U),
                WCBCommandBuilder.flthy_hp_led(FlthyHPDesignator.ALL,
                    FlthyHPLEDSequence.DIM_PULSE, FlthyHPColor.BLUE, 2),
                WCBCommandBuilder.hcr_set_emotion("happy", 80),
                WCBCommandBuilder.hcr_play_wav("A", 65)  # Reverent beep
            ],

            R2D2Mood.SITH_ALERT: [
                WCBCommand(MaestroDomeCommand.SCREAM.value, "Dome Sith alert"),
                WCBCommand(MaestroBodyCommand.ARMS_OPEN.value, "Arms defensive"),
                WCBCommand(PeriscopeCommand.UP.value, "Periscope alert"),
                WCBCommandBuilder.psi_mode(PSIAddress.GLOBAL, PSIMode.FLASH_FAST),
                WCBCommandBuilder.flthy_hp_led(FlthyHPDesignator.ALL,
                    FlthyHPLEDSequence.TOGGLE_COLOR, FlthyHPColor.RED),
                WCBCommandBuilder.hcr_emotion(HCRStimulus.SCARED_EXTREME),
                WCBCommandBuilder.hcr_play_wav("A", 70)  # Danger alarm
            ],

            # === SPECIAL STATES ===

            R2D2Mood.MAINTENANCE_COOPERATIVE: [
                WCBCommand(MaestroDomeCommand.CLOSE.value, "Dome maintenance position"),
                WCBCommand(MaestroBodyCommand.ARMS_OPEN.value, "Arms cooperative"),
                WCBCommand(PeriscopeCommand.DOWN.value, "Periscope safe"),
                WCBCommandBuilder.psi_mode(PSIAddress.GLOBAL, PSIMode.TEST_WHITE),
                WCBCommandBuilder.flthy_hp_led(FlthyHPDesignator.ALL,
                    FlthyHPLEDSequence.TOGGLE_COLOR, FlthyHPColor.WHITE),
                WCBCommandBuilder.hcr_set_emotion("happy", 50)
            ],

            R2D2Mood.EMERGENCY_CALM: [
                WCBCommand(MaestroDomeCommand.CLOSE.value, "Dome emergency center"),
                WCBCommand(MaestroBodyCommand.ARMS_CLOSED.value, "Arms safe position"),
                WCBCommand(PeriscopeCommand.DOWN.value, "Periscope retract safe"),
                WCBCommandBuilder.psi_mode(PSIAddress.GLOBAL, PSIMode.ALARM_SLOW),
                WCBCommandBuilder.flthy_hp_led(FlthyHPDesignator.ALL,
                    FlthyHPLEDSequence.TOGGLE_COLOR, FlthyHPColor.YELLOW),
                WCBCommandBuilder.hcr_set_emotion("scared", 40),
                WCBCommandBuilder.hcr_play_wav("A", 45)  # Calm emergency
            ],

            R2D2Mood.EMERGENCY_PANIC: [
                WCBCommand(MaestroDomeCommand.CLOSE.value, "Dome emergency lock"),
                WCBCommand(MaestroBodyCommand.ARMS_CLOSED.value, "Arms emergency lock"),
                WCBCommand(PeriscopeCommand.DOWN.value, "Periscope emergency retract"),
                WCBCommandBuilder.psi_mode(PSIAddress.GLOBAL, PSIMode.FLASH_FAST),
                WCBCommandBuilder.flthy_hp_led(FlthyHPDesignator.ALL,
                    FlthyHPLEDSequence.SHORT_CIRCUIT),
                WCBCommandBuilder.hcr_emotion(HCRStimulus.SCARED_EXTREME),
                WCBCommandBuilder.hcr_play_wav("A", 75)  # Panic alarm
            ],
        }

    def list_moods(self):
        """Display all available moods"""
        print("\n=== R2D2 Hardware Mood Library (27 Moods) ===\n")

        categories = {
            "Primary Emotional (1-6)": list(range(1, 7)),
            "Social Interaction (7-10)": list(range(7, 11)),
            "Character-Specific (11-14)": list(range(11, 15)),
            "Activity States (15-20)": list(range(15, 21)),
            "Performance (21-24)": list(range(21, 25)),
            "Special (25-27)": list(range(25, 28))
        }

        for category, mood_nums in categories.items():
            print(f"\n{category}:")
            for num in mood_nums:
                mood = R2D2Mood(num)
                cmd_count = len(self.mood_commands.get(mood, []))
                print(f"  {num:2d}. {mood.name:30s} ({cmd_count} commands)")

    def test_mood_sequence(self, mood: R2D2Mood):
        """Test a mood sequence with detailed output"""
        print(f"\n=== Testing Mood: {mood.name} ===\n")

        commands = self.mood_commands.get(mood, [])
        print(f"Total Commands: {len(commands)}\n")

        for i, cmd in enumerate(commands, 1):
            valid, cmd_type = WCBCommandValidator.validate_any(cmd.command)
            status = "✅" if valid else "❌"
            print(f"{i}. {status} [{cmd_type:8s}] {cmd.to_serial()!r:20s} - {cmd.description}")

        print("\n" + "="*60)


if __name__ == "__main__":
    # Initialize in simulation mode
    orchestrator = HardwareOrchestrator(simulation=True)
    orchestrator.connect()

    # List all moods
    orchestrator.list_moods()

    # Test some moods
    print("\n" + "="*60)
    test_moods = [
        R2D2Mood.IDLE_RELAXED,
        R2D2Mood.EXCITED_HAPPY,
        R2D2Mood.PROTECTIVE_ALERT,
        R2D2Mood.JEDI_RESPECT,
        R2D2Mood.EMERGENCY_PANIC
    ]

    for mood in test_moods:
        orchestrator.test_mood_sequence(mood)
        print()

    # Execute a mood
    print("\n" + "="*60)
    print("\n🎭 Executing EXCITED_HAPPY mood...\n")
    orchestrator.execute_mood(R2D2Mood.EXCITED_HAPPY, priority=7)

    orchestrator.disconnect()
