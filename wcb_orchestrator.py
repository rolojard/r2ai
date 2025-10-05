#!/usr/bin/env python3
"""
WCB Orchestrator - Mood-Based Behavior Coordination
===================================================

High-level orchestration layer that coordinates WCB commands across all three boards
to execute complete behavioral moods from the Disney Behavioral Intelligence system.

Integrates 27 personality moods with coordinated multi-board WCB commands.

Author: Expert Project Manager + Super Coder Team
Version: 1.0 Production
Target: NVIDIA Orin Nano R2D2 Systems
"""

import json
import logging
import time
import threading
from pathlib import Path
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass
from enum import Enum

# Import WCB controller components
from wcb_controller import (
    WCBController, WCB1BodyController, WCB2DomePlateController,
    WCB3DomeController, WCBCommand, WCBBoard, WCBSerialPort
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - [%(levelname)s] - %(message)s'
)
logger = logging.getLogger('WCBOrchestrator')

# =============================================
# MOOD SYSTEM INTEGRATION
# =============================================

class R2D2Mood(Enum):
    """R2D2 Personality Moods (27 total)"""
    # Primary Emotional States (1-6)
    IDLE_RELAXED = 1
    IDLE_BORED = 2
    ALERT_CURIOUS = 3
    ALERT_CAUTIOUS = 4
    EXCITED_HAPPY = 5
    EXCITED_MISCHIEVOUS = 6

    # Social Interaction States (7-10)
    GREETING_FRIENDLY = 7
    GREETING_SHY = 8
    CONVERSING_ENGAGED = 9
    CONVERSING_DISTRACTED = 10

    # Character-Specific States (11-14)
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

    # Performance States (21-24)
    ENTERTAINING_CROWD = 21
    ENTERTAINING_INTIMATE = 22
    JEDI_RESPECT = 23
    SITH_ALERT = 24

    # Special States (25-27)
    MAINTENANCE_COOPERATIVE = 25
    EMERGENCY_CALM = 26
    EMERGENCY_PANIC = 27

@dataclass
class MoodExecutionContext:
    """Context for mood execution"""
    mood: R2D2Mood
    start_time: float
    duration_ms: int
    commands_sent: int = 0
    commands_failed: int = 0
    completed: bool = False

# =============================================
# WCB MOOD COMMAND ORCHESTRATOR
# =============================================

class WCBOrchestrator:
    """
    High-Level WCB Mood Orchestration System

    Coordinates mood-based behaviors across all three WCB boards,
    translating personality states into coordinated multi-board commands.
    """

    def __init__(self, wcb_controller: WCBController, mood_commands_file: str = None):
        """
        Initialize WCB Orchestrator

        Args:
            wcb_controller: Base WCB controller instance
            mood_commands_file: Path to mood commands JSON file
        """
        self.wcb = wcb_controller

        # Initialize board controllers
        self.wcb1 = WCB1BodyController(wcb_controller)
        self.wcb2 = WCB2DomePlateController(wcb_controller)
        self.wcb3 = WCB3DomeController(wcb_controller)

        # Load mood command table
        if mood_commands_file is None:
            mood_commands_file = "/home/rolo/r2ai/wcb_mood_commands.json"

        self.mood_commands = self._load_mood_commands(mood_commands_file)

        # Execution tracking
        self.active_mood: Optional[MoodExecutionContext] = None
        self.mood_history: List[MoodExecutionContext] = []
        self._lock = threading.Lock()

        # Statistics
        self.stats = {
            'moods_executed': 0,
            'total_commands_sent': 0,
            'total_commands_failed': 0,
            'average_execution_time_ms': 0.0
        }

        logger.info("WCB Orchestrator initialized")

    def _load_mood_commands(self, filepath: str) -> Dict:
        """Load mood command table from JSON file"""
        try:
            with open(filepath, 'r') as f:
                data = json.load(f)

            moods_loaded = len(data.get('moods', {}))
            logger.info(f"✅ Loaded {moods_loaded} mood command definitions")

            return data

        except Exception as e:
            logger.error(f"Failed to load mood commands: {e}")
            return {'moods': {}}

    def execute_mood(self, mood: R2D2Mood, blocking: bool = False) -> bool:
        """
        Execute complete mood behavior across all WCB boards

        Args:
            mood: R2D2Mood to execute
            blocking: If True, wait for mood completion

        Returns:
            True if mood execution started successfully
        """
        # Get mood command definition
        mood_key = self._mood_to_key(mood)
        mood_def = self.mood_commands.get('moods', {}).get(mood_key)

        if not mood_def:
            logger.error(f"No command definition for mood: {mood.name}")
            return False

        # Create execution context
        context = MoodExecutionContext(
            mood=mood,
            start_time=time.time(),
            duration_ms=mood_def.get('duration_ms', 5000)
        )

        with self._lock:
            self.active_mood = context

        logger.info(f"🎭 Executing mood: {mood.name} ({mood_def['description']})")

        # Execute mood in separate thread or blocking
        if blocking:
            self._execute_mood_internal(mood_def, context)
        else:
            mood_thread = threading.Thread(
                target=self._execute_mood_internal,
                args=(mood_def, context),
                daemon=True,
                name=f"Mood_{mood.name}"
            )
            mood_thread.start()

        return True

    def _execute_mood_internal(self, mood_def: Dict, context: MoodExecutionContext):
        """Internal mood execution (runs in thread)"""
        try:
            # Execute WCB1 commands (body)
            for cmd_def in mood_def.get('wcb1_commands', []):
                success = self._execute_wcb_command(self.wcb1.board, cmd_def)
                if success:
                    context.commands_sent += 1
                else:
                    context.commands_failed += 1

            # Execute WCB2 commands (dome plate)
            for cmd_def in mood_def.get('wcb2_commands', []):
                success = self._execute_wcb_command(self.wcb2.board, cmd_def)
                if success:
                    context.commands_sent += 1
                else:
                    context.commands_failed += 1

            # Execute WCB3 commands (dome)
            for cmd_def in mood_def.get('wcb3_commands', []):
                success = self._execute_wcb_command(self.wcb3.board, cmd_def)
                if success:
                    context.commands_sent += 1
                else:
                    context.commands_failed += 1

            # Update statistics
            self.stats['moods_executed'] += 1
            self.stats['total_commands_sent'] += context.commands_sent
            self.stats['total_commands_failed'] += context.commands_failed

            execution_time = (time.time() - context.start_time) * 1000
            current_avg = self.stats['average_execution_time_ms']
            count = self.stats['moods_executed']
            self.stats['average_execution_time_ms'] = (
                (current_avg * (count - 1) + execution_time) / count
            )

            # Mark completed
            context.completed = True

            with self._lock:
                self.mood_history.append(context)
                if self.active_mood == context:
                    self.active_mood = None

            logger.info(f"✅ Mood {context.mood.name} completed: "
                       f"{context.commands_sent} commands sent, "
                       f"{context.commands_failed} failed")

        except Exception as e:
            logger.error(f"Mood execution failed: {e}")
            context.completed = False

    def _execute_wcb_command(self, board: WCBBoard, cmd_def: Dict) -> bool:
        """Execute individual WCB command from definition"""
        try:
            port = WCBSerialPort(cmd_def['port'])
            data_hex = cmd_def['data']

            # Convert hex string to bytes
            data_bytes = self._hex_string_to_bytes(data_hex)

            # Create and send command
            command = WCBCommand(
                board=board,
                port=port,
                data=data_bytes,
                priority=7  # Mood commands have high priority
            )

            success = self.wcb.send_command(command)

            if success:
                logger.debug(f"WCB Command: Board {board.value}, Port {port.value}, "
                           f"Data: {data_hex} ({cmd_def.get('description', 'N/A')})")

            return success

        except Exception as e:
            logger.error(f"Failed to execute WCB command: {e}")
            return False

    def _hex_string_to_bytes(self, hex_string: str) -> bytes:
        """Convert hex string like '84 00 70 2E' to bytes"""
        hex_values = hex_string.split()
        return bytes([int(h, 16) for h in hex_values])

    def _mood_to_key(self, mood: R2D2Mood) -> str:
        """Convert mood enum to JSON key format"""
        return f"{mood.value}_{mood.name}"

    def stop_active_mood(self):
        """Stop currently executing mood"""
        with self._lock:
            if self.active_mood:
                logger.info(f"Stopping active mood: {self.active_mood.mood.name}")
                self.active_mood = None

    def get_mood_status(self) -> Dict[str, Any]:
        """Get current mood execution status"""
        with self._lock:
            if self.active_mood:
                elapsed_ms = (time.time() - self.active_mood.start_time) * 1000
                progress = min(100, (elapsed_ms / self.active_mood.duration_ms) * 100)

                return {
                    'active': True,
                    'mood': self.active_mood.mood.name,
                    'progress_percent': progress,
                    'elapsed_ms': elapsed_ms,
                    'duration_ms': self.active_mood.duration_ms,
                    'commands_sent': self.active_mood.commands_sent,
                    'commands_failed': self.active_mood.commands_failed
                }
            else:
                return {
                    'active': False,
                    'mood': None,
                    'progress_percent': 0
                }

    def get_statistics(self) -> Dict[str, Any]:
        """Get orchestrator statistics"""
        return {
            **self.stats,
            'mood_history_count': len(self.mood_history),
            'active_mood': self.active_mood.mood.name if self.active_mood else None
        }

# =============================================
# DISNEY BEHAVIORAL INTELLIGENCE INTEGRATION
# =============================================

class WCBBehavioralBridge:
    """
    Bridge between Disney Behavioral Intelligence Engine and WCB Orchestrator

    Maps personality states from the behavioral intelligence system to
    appropriate WCB moods for execution.
    """

    # Mapping from behavioral intelligence personality states to WCB moods
    PERSONALITY_TO_MOOD_MAP = {
        'IDLE_RELAXED': R2D2Mood.IDLE_RELAXED,
        'IDLE_BORED': R2D2Mood.IDLE_BORED,
        'ALERT_CURIOUS': R2D2Mood.ALERT_CURIOUS,
        'ALERT_CAUTIOUS': R2D2Mood.ALERT_CAUTIOUS,
        'EXCITED_HAPPY': R2D2Mood.EXCITED_HAPPY,
        'EXCITED_MISCHIEVOUS': R2D2Mood.EXCITED_MISCHIEVOUS,
        'GREETING_FRIENDLY': R2D2Mood.GREETING_FRIENDLY,
        'GREETING_SHY': R2D2Mood.GREETING_SHY,
        'CONVERSING_ENGAGED': R2D2Mood.CONVERSING_ENGAGED,
        'CONVERSING_DISTRACTED': R2D2Mood.CONVERSING_DISTRACTED,
        'STUBBORN_DEFIANT': R2D2Mood.STUBBORN_DEFIANT,
        'STUBBORN_POUTY': R2D2Mood.STUBBORN_POUTY,
        'PROTECTIVE_ALERT': R2D2Mood.PROTECTIVE_ALERT,
        'PROTECTIVE_AGGRESSIVE': R2D2Mood.PROTECTIVE_AGGRESSIVE,
        'SCANNING_METHODICAL': R2D2Mood.SCANNING_METHODICAL,
        'SCANNING_FRANTIC': R2D2Mood.SCANNING_FRANTIC,
        'TRACKING_FOCUSED': R2D2Mood.TRACKING_FOCUSED,
        'TRACKING_PLAYFUL': R2D2Mood.TRACKING_PLAYFUL,
        'DEMONSTRATING_CONFIDENT': R2D2Mood.DEMONSTRATING_CONFIDENT,
        'DEMONSTRATING_NERVOUS': R2D2Mood.DEMONSTRATING_NERVOUS,
        'ENTERTAINING_CROWD': R2D2Mood.ENTERTAINING_CROWD,
        'ENTERTAINING_INTIMATE': R2D2Mood.ENTERTAINING_INTIMATE,
        'MAINTENANCE_COOPERATIVE': R2D2Mood.MAINTENANCE_COOPERATIVE,
        'EMERGENCY_CALM': R2D2Mood.EMERGENCY_CALM,
        'EMERGENCY_PANIC': R2D2Mood.EMERGENCY_PANIC
    }

    def __init__(self, orchestrator: WCBOrchestrator):
        self.orchestrator = orchestrator
        logger.info("WCB Behavioral Bridge initialized")

    def execute_personality_state(self, state_name: str) -> bool:
        """
        Execute WCB mood based on personality state name

        Args:
            state_name: Personality state name (e.g., 'GREETING_FRIENDLY')

        Returns:
            True if mood executed successfully
        """
        mood = self.PERSONALITY_TO_MOOD_MAP.get(state_name.upper())

        if not mood:
            logger.warning(f"No mood mapping for personality state: {state_name}")
            return False

        return self.orchestrator.execute_mood(mood)

    def emergency_stop(self):
        """Execute emergency stop across all systems"""
        logger.warning("🚨 Emergency stop initiated")
        self.orchestrator.stop_active_mood()
        self.orchestrator.wcb.emergency_stop()

# =============================================
# DEMONSTRATION AND TESTING
# =============================================

def demo_wcb_orchestrator():
    """Demonstration of WCB orchestrator with mood behaviors"""
    logger.info("🎭 WCB Orchestrator Demo - Mood Behaviors")
    logger.info("=" * 60)

    # Initialize system (simulation mode for testing)
    wcb = WCBController(simulation_mode=True)
    orchestrator = WCBOrchestrator(wcb)
    bridge = WCBBehavioralBridge(orchestrator)

    try:
        # Demo 1: Execute greeting mood
        logger.info("\n--- Demo 1: Friendly Greeting ---")
        orchestrator.execute_mood(R2D2Mood.GREETING_FRIENDLY, blocking=True)
        time.sleep(1.0)

        # Demo 2: Execute alert mood
        logger.info("\n--- Demo 2: Protective Alert ---")
        orchestrator.execute_mood(R2D2Mood.PROTECTIVE_ALERT, blocking=True)
        time.sleep(1.0)

        # Demo 3: Execute entertainment mood
        logger.info("\n--- Demo 3: Entertaining Crowd ---")
        orchestrator.execute_mood(R2D2Mood.ENTERTAINING_CROWD, blocking=True)
        time.sleep(1.0)

        # Demo 4: Behavioral bridge integration
        logger.info("\n--- Demo 4: Behavioral Bridge ---")
        bridge.execute_personality_state('EXCITED_HAPPY')
        time.sleep(2.0)

        # Demo 5: Mood status and statistics
        logger.info("\n--- Demo 5: Status and Statistics ---")
        status = orchestrator.get_mood_status()
        stats = orchestrator.get_statistics()

        print("\nMood Status:")
        print(json.dumps(status, indent=2))

        print("\nOrchestrator Statistics:")
        print(json.dumps(stats, indent=2))

        logger.info("\n✅ WCB Orchestrator demo completed successfully!")

    except KeyboardInterrupt:
        logger.info("Demo interrupted by user")
    except Exception as e:
        logger.error(f"Demo failed: {e}")
    finally:
        wcb.shutdown()

if __name__ == "__main__":
    demo_wcb_orchestrator()
