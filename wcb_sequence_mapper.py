#!/usr/bin/env python3
"""
WCB Sequence Mapper - Interactive tool to map existing Maestro/HCR/Light sequences to R2D2 moods

This tool helps document your existing programmed sequences and map them to the 27 R2D2 moods.
"""

import json
import serial
import time
from typing import Dict, List, Optional
from enum import Enum

class R2D2Mood(Enum):
    """27 R2D2 Personality Moods"""
    # Primary Emotional (1-6)
    IDLE_RELAXED = "1_IDLE_RELAXED"
    IDLE_BORED = "2_IDLE_BORED"
    ALERT_CURIOUS = "3_ALERT_CURIOUS"
    ALERT_CAUTIOUS = "4_ALERT_CAUTIOUS"
    EXCITED_HAPPY = "5_EXCITED_HAPPY"
    EXCITED_MISCHIEVOUS = "6_EXCITED_MISCHIEVOUS"

    # Social Interaction (7-10)
    GREETING_FRIENDLY = "7_GREETING_FRIENDLY"
    GREETING_SHY = "8_GREETING_SHY"
    CONVERSING_ENGAGED = "9_CONVERSING_ENGAGED"
    CONVERSING_DISTRACTED = "10_CONVERSING_DISTRACTED"

    # Character-Specific (11-14)
    STUBBORN_DEFIANT = "11_STUBBORN_DEFIANT"
    STUBBORN_POUTY = "12_STUBBORN_POUTY"
    PROTECTIVE_ALERT = "13_PROTECTIVE_ALERT"
    PROTECTIVE_AGGRESSIVE = "14_PROTECTIVE_AGGRESSIVE"

    # Activity States (15-20)
    SCANNING_METHODICAL = "15_SCANNING_METHODICAL"
    SCANNING_FRANTIC = "16_SCANNING_FRANTIC"
    TRACKING_FOCUSED = "17_TRACKING_FOCUSED"
    TRACKING_PLAYFUL = "18_TRACKING_PLAYFUL"
    DEMONSTRATING_CONFIDENT = "19_DEMONSTRATING_CONFIDENT"
    DEMONSTRATING_NERVOUS = "20_DEMONSTRATING_NERVOUS"

    # Performance (21-24)
    ENTERTAINING_CROWD = "21_ENTERTAINING_CROWD"
    ENTERTAINING_INTIMATE = "22_ENTERTAINING_INTIMATE"
    JEDI_RESPECT = "23_JEDI_RESPECT"
    SITH_ALERT = "24_SITH_ALERT"

    # Special (25-27)
    MAINTENANCE_COOPERATIVE = "25_MAINTENANCE_COOPERATIVE"
    EMERGENCY_CALM = "26_EMERGENCY_CALM"
    EMERGENCY_PANIC = "27_EMERGENCY_PANIC"


class WCBSequenceTester:
    """Test WCB commands to identify existing sequences"""

    def __init__(self, port: str = '/dev/ttyUSB0', baud: int = 9600):
        self.port = port
        self.baud = baud
        self.serial = None

    def connect(self) -> bool:
        """Connect to WCB"""
        try:
            self.serial = serial.Serial(self.port, self.baud, timeout=1)
            time.sleep(2)  # Allow connection to stabilize
            print(f"✅ Connected to WCB on {self.port}")
            return True
        except Exception as e:
            print(f"❌ Failed to connect: {e}")
            return False

    def send_command(self, command: str) -> bool:
        """Send WCB command"""
        try:
            if not self.serial or not self.serial.is_open:
                print("❌ Serial port not connected")
                return False

            # WCB expects commands ending with \r
            cmd = f"{command}\r"
            self.serial.write(cmd.encode())
            self.serial.flush()
            print(f"📤 Sent: {command}")
            return True
        except Exception as e:
            print(f"❌ Failed to send command: {e}")
            return False

    def test_maestro_sequence(self, wcb_id: int, sequence_num: int):
        """Test Maestro sequence: ;Mxyy"""
        command = f";M{wcb_id}{sequence_num:02d}"
        print(f"\n🎬 Testing Maestro {wcb_id}, Sequence {sequence_num}")
        return self.send_command(command)

    def test_sound(self, sound_command: str):
        """Test HCR sound command on WCB1 Serial 4: ;S4{sound}"""
        command = f";S4{sound_command}"
        print(f"\n🔊 Testing Sound: {sound_command}")
        return self.send_command(command)

    def test_psi_lights(self, pattern: str):
        """Test PSI lights on WCB3 Serial 4: ;W3;S4{pattern}"""
        command = f";W3;S4{pattern}"
        print(f"\n💡 Testing PSI Lights: {pattern}")
        return self.send_command(command)

    def test_logic_lights(self, pattern: str):
        """Test Logic lights on WCB3 Serial 5: ;W3;S5{pattern}"""
        command = f";W3;S5{pattern}"
        print(f"\n💡 Testing Logic Lights: {pattern}")
        return self.send_command(command)

    def test_chained_command(self, commands: List[str]):
        """Test chained commands with ^ delimiter"""
        chained = "^".join(commands)
        print(f"\n🔗 Testing Chained Commands:")
        for i, cmd in enumerate(commands, 1):
            print(f"   {i}. {cmd}")
        return self.send_command(chained)

    def disconnect(self):
        """Disconnect from WCB"""
        if self.serial and self.serial.is_open:
            self.serial.close()
            print("\n✅ Disconnected from WCB")


class SequenceMapper:
    """Interactive mapper for documenting and mapping sequences"""

    def __init__(self):
        self.sequences = {
            "maestro_body": {},      # WCB1 Maestro sequences
            "maestro_dome": {},      # WCB3 Maestro sequences
            "sounds": {},            # HCR sound commands
            "psi_lights": {},        # PSI light patterns
            "logic_lights": {},      # Logic light patterns
        }
        self.mood_mappings = {}

    def document_maestro_sequences(self, maestro_name: str, wcb_id: int):
        """Interactive documentation of Maestro sequences"""
        print(f"\n{'='*60}")
        print(f"📝 Documenting {maestro_name} Sequences (Maestro ID {wcb_id})")
        print(f"{'='*60}")
        print("Enter sequence numbers and descriptions (empty number to finish)")

        sequences = {}
        while True:
            seq_num = input(f"\nSequence number (or press Enter to finish): ").strip()
            if not seq_num:
                break

            try:
                seq_num = int(seq_num)
                description = input(f"  Description for sequence {seq_num}: ").strip()
                sequences[seq_num] = description
                print(f"  ✅ Added: Sequence {seq_num} = {description}")
            except ValueError:
                print("  ❌ Invalid number, try again")

        if maestro_name == "Body":
            self.sequences["maestro_body"] = sequences
        elif maestro_name == "Dome":
            self.sequences["maestro_dome"] = sequences

    def document_sounds(self):
        """Interactive documentation of HCR sounds"""
        print(f"\n{'='*60}")
        print(f"🔊 Documenting HCR Sound Commands")
        print(f"{'='*60}")
        print("Enter sound commands and descriptions (empty command to finish)")
        print("Example: #SD01, #SD05, <SH1,M1>, etc.")

        sounds = {}
        while True:
            cmd = input(f"\nSound command (or press Enter to finish): ").strip()
            if not cmd:
                break

            description = input(f"  Description for '{cmd}': ").strip()
            sounds[cmd] = description
            print(f"  ✅ Added: {cmd} = {description}")

        self.sequences["sounds"] = sounds

    def document_lights(self, light_type: str):
        """Interactive documentation of light patterns"""
        print(f"\n{'='*60}")
        print(f"💡 Documenting {light_type} Light Patterns")
        print(f"{'='*60}")
        print("Enter pattern commands and descriptions (empty command to finish)")
        print("Example: :PP100, :SE00, etc.")

        patterns = {}
        while True:
            cmd = input(f"\nLight pattern command (or press Enter to finish): ").strip()
            if not cmd:
                break

            description = input(f"  Description for '{cmd}': ").strip()
            patterns[cmd] = description
            print(f"  ✅ Added: {cmd} = {description}")

        if light_type == "PSI":
            self.sequences["psi_lights"] = patterns
        elif light_type == "Logic":
            self.sequences["logic_lights"] = patterns

    def map_mood_to_sequences(self, mood: R2D2Mood):
        """Map a mood to specific sequences"""
        print(f"\n{'='*60}")
        print(f"🎭 Mapping Mood: {mood.value}")
        print(f"{'='*60}")

        mapping = {
            "mood": mood.value,
            "body_maestro": None,
            "dome_maestro": None,
            "sound": None,
            "psi_lights": None,
            "logic_lights": None,
            "description": ""
        }

        # Body Maestro
        if self.sequences["maestro_body"]:
            print("\nAvailable Body Maestro sequences:")
            for num, desc in self.sequences["maestro_body"].items():
                print(f"  {num}: {desc}")
            seq = input("Select Body Maestro sequence (or Enter to skip): ").strip()
            if seq:
                mapping["body_maestro"] = int(seq)

        # Dome Maestro
        if self.sequences["maestro_dome"]:
            print("\nAvailable Dome Maestro sequences:")
            for num, desc in self.sequences["maestro_dome"].items():
                print(f"  {num}: {desc}")
            seq = input("Select Dome Maestro sequence (or Enter to skip): ").strip()
            if seq:
                mapping["dome_maestro"] = int(seq)

        # Sound
        if self.sequences["sounds"]:
            print("\nAvailable Sounds:")
            for cmd, desc in self.sequences["sounds"].items():
                print(f"  {cmd}: {desc}")
            snd = input("Select Sound command (or Enter to skip): ").strip()
            if snd:
                mapping["sound"] = snd

        # PSI Lights
        if self.sequences["psi_lights"]:
            print("\nAvailable PSI Light Patterns:")
            for cmd, desc in self.sequences["psi_lights"].items():
                print(f"  {cmd}: {desc}")
            psi = input("Select PSI pattern (or Enter to skip): ").strip()
            if psi:
                mapping["psi_lights"] = psi

        # Logic Lights
        if self.sequences["logic_lights"]:
            print("\nAvailable Logic Light Patterns:")
            for cmd, desc in self.sequences["logic_lights"].items():
                print(f"  {cmd}: {desc}")
            logic = input("Select Logic pattern (or Enter to skip): ").strip()
            if logic:
                mapping["logic_lights"] = logic

        # Description
        mapping["description"] = input("\nMood description: ").strip()

        self.mood_mappings[mood.value] = mapping
        print(f"\n✅ Mapped {mood.value}")

    def save_to_json(self, filename: str = "wcb_sequence_mappings.json"):
        """Save mappings to JSON file"""
        data = {
            "available_sequences": self.sequences,
            "mood_mappings": self.mood_mappings
        }

        with open(filename, 'w') as f:
            json.dump(data, f, indent=2)

        print(f"\n✅ Saved mappings to {filename}")

    def load_from_json(self, filename: str = "wcb_sequence_mappings.json"):
        """Load mappings from JSON file"""
        try:
            with open(filename, 'r') as f:
                data = json.load(f)

            self.sequences = data.get("available_sequences", {})
            self.mood_mappings = data.get("mood_mappings", {})

            print(f"\n✅ Loaded mappings from {filename}")
            return True
        except FileNotFoundError:
            print(f"\n⚠️  File {filename} not found")
            return False


def main():
    """Interactive main menu"""
    mapper = SequenceMapper()
    tester = None

    while True:
        print(f"\n{'='*60}")
        print("WCB Sequence Mapper - Main Menu")
        print(f"{'='*60}")
        print("1. Document Maestro Sequences (Body)")
        print("2. Document Maestro Sequences (Dome)")
        print("3. Document HCR Sounds")
        print("4. Document PSI Light Patterns")
        print("5. Document Logic Light Patterns")
        print("6. Map Moods to Sequences")
        print("7. Test Commands (requires WCB connection)")
        print("8. Save Mappings to JSON")
        print("9. Load Mappings from JSON")
        print("10. Generate WCB Stored Commands")
        print("0. Exit")

        choice = input("\nSelect option: ").strip()

        if choice == "1":
            mapper.document_maestro_sequences("Body", wcb_id=1)

        elif choice == "2":
            mapper.document_maestro_sequences("Dome", wcb_id=3)

        elif choice == "3":
            mapper.document_sounds()

        elif choice == "4":
            mapper.document_lights("PSI")

        elif choice == "5":
            mapper.document_lights("Logic")

        elif choice == "6":
            print("\nAvailable Moods:")
            for i, mood in enumerate(R2D2Mood, 1):
                print(f"  {i}. {mood.value}")

            mood_num = input("\nSelect mood number (or Enter to skip): ").strip()
            if mood_num:
                try:
                    mood = list(R2D2Mood)[int(mood_num) - 1]
                    mapper.map_mood_to_sequences(mood)
                except (ValueError, IndexError):
                    print("❌ Invalid mood number")

        elif choice == "7":
            if not tester:
                port = input("Enter serial port (default /dev/ttyUSB0): ").strip() or "/dev/ttyUSB0"
                tester = WCBSequenceTester(port)
                if not tester.connect():
                    tester = None
                    continue

            print("\nTest Options:")
            print("1. Test Maestro Sequence")
            print("2. Test Sound")
            print("3. Test PSI Lights")
            print("4. Test Logic Lights")
            print("5. Test Chained Command")

            test_choice = input("Select test: ").strip()

            if test_choice == "1":
                wcb = int(input("Maestro WCB ID (1 or 3): ").strip())
                seq = int(input("Sequence number: ").strip())
                tester.test_maestro_sequence(wcb, seq)

            elif test_choice == "2":
                cmd = input("Sound command (e.g., #SD01): ").strip()
                tester.test_sound(cmd)

            elif test_choice == "3":
                pattern = input("PSI pattern (e.g., :PP100): ").strip()
                tester.test_psi_lights(pattern)

            elif test_choice == "4":
                pattern = input("Logic pattern (e.g., :PP100): ").strip()
                tester.test_logic_lights(pattern)

            elif test_choice == "5":
                print("Enter commands (empty to finish):")
                commands = []
                while True:
                    cmd = input(f"  Command {len(commands)+1}: ").strip()
                    if not cmd:
                        break
                    commands.append(cmd)
                if commands:
                    tester.test_chained_command(commands)

        elif choice == "8":
            filename = input("Filename (default wcb_sequence_mappings.json): ").strip()
            mapper.save_to_json(filename or "wcb_sequence_mappings.json")

        elif choice == "9":
            filename = input("Filename (default wcb_sequence_mappings.json): ").strip()
            mapper.load_from_json(filename or "wcb_sequence_mappings.json")

        elif choice == "10":
            generate_stored_commands(mapper)

        elif choice == "0":
            if tester:
                tester.disconnect()
            print("\n👋 Goodbye!")
            break


def generate_stored_commands(mapper: SequenceMapper):
    """Generate WCB stored commands from mappings"""
    print(f"\n{'='*60}")
    print("🔧 Generating WCB Stored Commands")
    print(f"{'='*60}")

    if not mapper.mood_mappings:
        print("❌ No mood mappings found. Map moods first.")
        return

    print("\nCopy and paste these commands to your WCB via serial:")
    print(f"{'='*60}\n")

    for mood_name, mapping in mapper.mood_mappings.items():
        commands = []

        # Body Maestro
        if mapping.get("body_maestro"):
            commands.append(f";M1{mapping['body_maestro']:02d}")

        # Dome Maestro (via WCB3)
        if mapping.get("dome_maestro"):
            commands.append(f";W3;M3{mapping['dome_maestro']:02d}")

        # Sound (WCB1 Serial 4)
        if mapping.get("sound"):
            commands.append(f";S4{mapping['sound']}")

        # PSI Lights (WCB3 Serial 4)
        if mapping.get("psi_lights"):
            commands.append(f";W3;S4{mapping['psi_lights']}")

        # Logic Lights (WCB3 Serial 5)
        if mapping.get("logic_lights"):
            commands.append(f";W3;S5{mapping['logic_lights']}")

        if commands:
            # Create chained command
            chained = "^".join(commands)

            # Generate store command
            mood_key = mood_name.lower().replace("_", "")
            store_cmd = f"?CS{mood_key},{chained}"

            print(f"# {mood_name}")
            if mapping.get("description"):
                print(f"# {mapping['description']}")
            print(store_cmd)
            print()

    print(f"{'='*60}")
    print("\n✅ To store these in WCB1, send each ?CS command via serial")
    print("✅ Then trigger with: ;c{mood_key}")


if __name__ == "__main__":
    main()
