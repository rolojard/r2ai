#!/usr/bin/env python3
"""
R2D2 Disney-Level Behavior Patterns
Authentic Character Animation and Personality System

This module provides comprehensive R2D2 behavior patterns that capture
the authentic character personality from the Star Wars films, including:
- Authentic movement patterns and timing
- Emotional expression through motion
- Reactive behaviors and personality traits
- Interactive response systems
- Context-aware performance modes

Author: Imagineer Specialist
Version: 1.0.0
Date: 2024-09-22
"""

import time
import logging
import threading
import random
import math
from typing import Dict, List, Tuple, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum
import queue
import json

logger = logging.getLogger(__name__)

class EmotionalState(Enum):
    """R2D2's emotional states"""
    NEUTRAL = "neutral"
    HAPPY = "happy"
    EXCITED = "excited"
    CURIOUS = "curious"
    WORRIED = "worried"
    ALERT = "alert"
    SLEEPY = "sleepy"
    PLAYFUL = "playful"
    DETERMINED = "determined"
    CONFUSED = "confused"

class BehaviorTrigger(Enum):
    """Behavior trigger types"""
    PERSON_DETECTED = "person_detected"
    PERSON_APPROACHED = "person_approached"
    PERSON_LEFT = "person_left"
    VOICE_DETECTED = "voice_detected"
    LOUD_NOISE = "loud_noise"
    TOUCH_DETECTED = "touch_detected"
    TIMER = "timer"
    MANUAL = "manual"
    SYSTEM_EVENT = "system_event"

class MovementIntensity(Enum):
    """Movement intensity levels"""
    SUBTLE = 1
    GENTLE = 2
    NORMAL = 3
    ENERGETIC = 4
    DRAMATIC = 5

@dataclass
class BehaviorPattern:
    """Defines a specific behavior pattern"""
    name: str
    description: str
    emotional_state: EmotionalState
    movements: List[Dict] = field(default_factory=list)
    intensity: MovementIntensity = MovementIntensity.NORMAL
    duration: float = 0.0
    probability: float = 1.0
    conditions: List[str] = field(default_factory=list)
    personality_traits: Dict[str, float] = field(default_factory=dict)

@dataclass
class CharacterState:
    """Current character state and mood"""
    emotional_state: EmotionalState = EmotionalState.NEUTRAL
    energy_level: float = 0.7  # 0.0 to 1.0
    curiosity_level: float = 0.8
    sociability: float = 0.9
    alertness: float = 0.6
    playfulness: float = 0.7
    last_interaction: float = 0.0
    interaction_count: int = 0

class DisneyBehaviorEngine:
    """Disney-level R2D2 behavior and personality engine"""

    def __init__(self, servo_system, script_engine):
        """Initialize behavior engine"""
        self.servo_system = servo_system
        self.script_engine = script_engine

        # Character state
        self.character_state = CharacterState()
        self.behavior_patterns: Dict[str, BehaviorPattern] = {}

        # Behavior execution
        self.behavior_active = True
        self.behavior_thread: Optional[threading.Thread] = None
        self.trigger_queue = queue.Queue()

        # Timing and randomization
        self.last_autonomous_behavior = time.time()
        self.autonomous_interval = 15.0  # Seconds between autonomous behaviors

        # Context awareness
        self.environment_context: Dict = {}
        self.interaction_history: List[Dict] = []

        logger.info("🎭 Disney Behavior Engine initialized")

        # Initialize behavior patterns
        self._initialize_behavior_patterns()

        # Start behavior processing
        self._start_behavior_processing()

    def _initialize_behavior_patterns(self):
        """Initialize authentic R2D2 behavior patterns"""
        logger.info("🎬 Initializing R2D2 behavior patterns...")

        # Greeting behaviors
        cheerful_greeting = BehaviorPattern(
            name="cheerful_greeting",
            description="Happy, energetic greeting when person approaches",
            emotional_state=EmotionalState.HAPPY,
            movements=[
                {"action": "dome_rotation", "angle": 20, "duration": 0.5},
                {"action": "dome_panels", "panels": {"front": True}, "duration": 0.3},
                {"action": "dome_panels", "panels": {}, "duration": 0.3},
                {"action": "dome_rotation", "angle": -20, "duration": 0.5},
                {"action": "utility_arms", "left": 45, "right": 45, "duration": 0.8},
                {"action": "dome_rotation", "angle": 0, "duration": 0.5},
                {"action": "utility_arms", "left": 0, "right": 0, "duration": 0.8},
            ],
            intensity=MovementIntensity.ENERGETIC,
            duration=3.7,
            personality_traits={"friendliness": 0.9, "energy": 0.8}
        )

        shy_greeting = BehaviorPattern(
            name="shy_greeting",
            description="Cautious, reserved greeting for new people",
            emotional_state=EmotionalState.CURIOUS,
            movements=[
                {"action": "head_tilt", "angle": 10, "duration": 1.0},
                {"action": "dome_rotation", "angle": 15, "duration": 1.5},
                {"action": "dome_panels", "panels": {"front": True}, "duration": 0.2},
                {"action": "dome_panels", "panels": {}, "duration": 0.2},
                {"action": "dome_rotation", "angle": 0, "duration": 1.0},
                {"action": "head_tilt", "angle": 0, "duration": 1.0},
            ],
            intensity=MovementIntensity.GENTLE,
            duration=4.9,
            personality_traits={"caution": 0.7, "curiosity": 0.8}
        )

        # Excitement behaviors
        extreme_excitement = BehaviorPattern(
            name="extreme_excitement",
            description="Very excited reaction to favorite people or events",
            emotional_state=EmotionalState.EXCITED,
            movements=[
                {"action": "dome_rotation", "angle": 45, "duration": 0.2},
                {"action": "dome_rotation", "angle": -45, "duration": 0.2},
                {"action": "dome_rotation", "angle": 30, "duration": 0.2},
                {"action": "dome_panels", "panels": {"left": True, "right": True}, "duration": 0.1},
                {"action": "dome_panels", "panels": {"front": True, "back": True}, "duration": 0.1},
                {"action": "dome_panels", "panels": {}, "duration": 0.1},
                {"action": "utility_arms", "left": 90, "right": 90, "duration": 0.3},
                {"action": "dome_rotation", "angle": -30, "duration": 0.2},
                {"action": "utility_arms", "left": 0, "right": 0, "duration": 0.3},
                {"action": "dome_rotation", "angle": 0, "duration": 0.4},
            ],
            intensity=MovementIntensity.DRAMATIC,
            duration=2.3,
            personality_traits={"excitement": 1.0, "expressiveness": 0.9}
        )

        # Curiosity behaviors
        investigate_person = BehaviorPattern(
            name="investigate_person",
            description="Curious investigation of new person",
            emotional_state=EmotionalState.CURIOUS,
            movements=[
                {"action": "head_tilt", "angle": 15, "duration": 1.2},
                {"action": "dome_rotation", "angle": 30, "duration": 1.5},
                {"action": "periscope", "extend": True, "duration": 1.0},
                {"action": "dome_rotation", "angle": -30, "duration": 2.0},
                {"action": "dome_rotation", "angle": 10, "duration": 1.0},
                {"action": "periscope", "extend": False, "duration": 1.0},
                {"action": "head_tilt", "angle": -5, "duration": 1.0},
                {"action": "dome_rotation", "angle": 0, "duration": 1.0},
                {"action": "head_tilt", "angle": 0, "duration": 1.0},
            ],
            intensity=MovementIntensity.NORMAL,
            duration=10.7,
            personality_traits={"curiosity": 0.9, "patience": 0.7}
        )

        confused_investigation = BehaviorPattern(
            name="confused_investigation",
            description="Confused head movements when trying to understand something",
            emotional_state=EmotionalState.CONFUSED,
            movements=[
                {"action": "head_tilt", "angle": 20, "duration": 0.8},
                {"action": "head_tilt", "angle": -15, "duration": 0.8},
                {"action": "dome_rotation", "angle": 25, "duration": 1.0},
                {"action": "head_tilt", "angle": 10, "duration": 0.6},
                {"action": "dome_rotation", "angle": -20, "duration": 1.0},
                {"action": "head_tilt", "angle": -10, "duration": 0.6},
                {"action": "dome_rotation", "angle": 0, "duration": 0.8},
                {"action": "head_tilt", "angle": 0, "duration": 0.8},
            ],
            intensity=MovementIntensity.GENTLE,
            duration=6.4,
            personality_traits={"confusion": 0.8, "persistence": 0.6}
        )

        # Alert/Warning behaviors
        security_alert = BehaviorPattern(
            name="security_alert",
            description="Alert scanning behavior for security situations",
            emotional_state=EmotionalState.ALERT,
            movements=[
                {"action": "dome_rotation", "angle": 90, "duration": 0.5},
                {"action": "dome_panels", "panels": {"front": True, "back": True}, "duration": 0.1},
                {"action": "dome_panels", "panels": {}, "duration": 0.1},
                {"action": "dome_rotation", "angle": -90, "duration": 0.8},
                {"action": "dome_panels", "panels": {"left": True, "right": True}, "duration": 0.1},
                {"action": "dome_panels", "panels": {}, "duration": 0.1},
                {"action": "dome_rotation", "angle": 45, "duration": 0.4},
                {"action": "periscope", "extend": True, "duration": 0.5},
                {"action": "dome_rotation", "angle": -45, "duration": 0.8},
                {"action": "dome_rotation", "angle": 0, "duration": 0.4},
                {"action": "periscope", "extend": False, "duration": 0.5},
            ],
            intensity=MovementIntensity.ENERGETIC,
            duration=4.3,
            personality_traits={"alertness": 1.0, "protectiveness": 0.8}
        )

        # Playful behaviors
        playful_dance = BehaviorPattern(
            name="playful_dance",
            description="Playful dancing behavior when in good mood",
            emotional_state=EmotionalState.PLAYFUL,
            movements=[
                {"action": "dome_rotation", "angle": 30, "duration": 0.4},
                {"action": "utility_arms", "left": 60, "right": 30, "duration": 0.5},
                {"action": "dome_rotation", "angle": -30, "duration": 0.4},
                {"action": "utility_arms", "left": 30, "right": 60, "duration": 0.5},
                {"action": "dome_panels", "panels": {"left": True}, "duration": 0.2},
                {"action": "dome_rotation", "angle": 15, "duration": 0.3},
                {"action": "dome_panels", "panels": {"right": True}, "duration": 0.2},
                {"action": "dome_rotation", "angle": -15, "duration": 0.3},
                {"action": "dome_panels", "panels": {}, "duration": 0.2},
                {"action": "utility_arms", "left": 0, "right": 0, "duration": 0.5},
                {"action": "dome_rotation", "angle": 0, "duration": 0.4},
            ],
            intensity=MovementIntensity.ENERGETIC,
            duration=4.0,
            personality_traits={"playfulness": 0.9, "joy": 0.8}
        )

        # Worried behaviors
        worried_scanning = BehaviorPattern(
            name="worried_scanning",
            description="Nervous scanning when something seems wrong",
            emotional_state=EmotionalState.WORRIED,
            movements=[
                {"action": "head_tilt", "angle": -10, "duration": 0.8},
                {"action": "dome_rotation", "angle": 40, "duration": 1.2},
                {"action": "dome_rotation", "angle": -40, "duration": 1.5},
                {"action": "dome_rotation", "angle": 20, "duration": 0.8},
                {"action": "dome_panels", "panels": {"front": True}, "duration": 0.15},
                {"action": "dome_panels", "panels": {}, "duration": 0.15},
                {"action": "dome_rotation", "angle": -20, "duration": 0.8},
                {"action": "dome_rotation", "angle": 0, "duration": 1.0},
                {"action": "head_tilt", "angle": 0, "duration": 0.8},
            ],
            intensity=MovementIntensity.NORMAL,
            duration=7.1,
            personality_traits={"worry": 0.8, "vigilance": 0.7}
        )

        # Sleep/Low Energy behaviors
        sleepy_drift = BehaviorPattern(
            name="sleepy_drift",
            description="Slow, drowsy movements when tired",
            emotional_state=EmotionalState.SLEEPY,
            movements=[
                {"action": "head_tilt", "angle": -15, "duration": 3.0},
                {"action": "dome_rotation", "angle": 10, "duration": 4.0},
                {"action": "dome_rotation", "angle": -5, "duration": 3.0},
                {"action": "dome_rotation", "angle": 0, "duration": 2.0},
                {"action": "head_tilt", "angle": -20, "duration": 2.0},
            ],
            intensity=MovementIntensity.SUBTLE,
            duration=14.0,
            personality_traits={"sleepiness": 0.9, "relaxation": 0.8}
        )

        # Determined behaviors
        determined_scan = BehaviorPattern(
            name="determined_scan",
            description="Focused, purposeful scanning behavior",
            emotional_state=EmotionalState.DETERMINED,
            movements=[
                {"action": "dome_rotation", "angle": 60, "duration": 2.0},
                {"action": "periscope", "extend": True, "duration": 1.0},
                {"action": "dome_rotation", "angle": -60, "duration": 3.0},
                {"action": "dome_rotation", "angle": 0, "duration": 2.0},
                {"action": "periscope", "extend": False, "duration": 1.0},
                {"action": "head_tilt", "angle": 5, "duration": 1.0},
                {"action": "head_tilt", "angle": 0, "duration": 1.0},
            ],
            intensity=MovementIntensity.NORMAL,
            duration=11.0,
            personality_traits={"determination": 0.9, "focus": 0.8}
        )

        # Store all behavior patterns
        patterns = [
            cheerful_greeting, shy_greeting, extreme_excitement,
            investigate_person, confused_investigation, security_alert,
            playful_dance, worried_scanning, sleepy_drift, determined_scan
        ]

        for pattern in patterns:
            self.behavior_patterns[pattern.name] = pattern
            logger.info(f"  ✓ Loaded behavior: {pattern.name}")

    def _start_behavior_processing(self):
        """Start behavior processing thread"""
        self.behavior_thread = threading.Thread(
            target=self._behavior_loop,
            daemon=True,
            name="BehaviorProcessor"
        )
        self.behavior_thread.start()

    def _behavior_loop(self):
        """Main behavior processing loop"""
        while self.behavior_active:
            try:
                # Process trigger queue
                if not self.trigger_queue.empty():
                    trigger_data = self.trigger_queue.get(timeout=1.0)
                    self._process_behavior_trigger(trigger_data)

                # Check for autonomous behaviors
                self._check_autonomous_behaviors()

                # Update character state
                self._update_character_state()

                time.sleep(0.5)  # 2Hz processing

            except queue.Empty:
                continue
            except Exception as e:
                logger.error(f"Behavior loop error: {e}")
                time.sleep(1.0)

    def _process_behavior_trigger(self, trigger_data: Dict):
        """Process a behavior trigger"""
        trigger_type = BehaviorTrigger(trigger_data.get("type"))
        context = trigger_data.get("context", {})

        logger.info(f"🎭 Processing trigger: {trigger_type.value}")

        # Select appropriate behavior based on trigger and current state
        behavior_name = self._select_behavior(trigger_type, context)

        if behavior_name:
            self._execute_behavior(behavior_name)

    def _select_behavior(self, trigger: BehaviorTrigger, context: Dict) -> Optional[str]:
        """Select appropriate behavior based on trigger and character state"""
        # Behavior selection logic based on trigger type and character state
        current_emotion = self.character_state.emotional_state
        energy = self.character_state.energy_level

        if trigger == BehaviorTrigger.PERSON_DETECTED:
            if self.character_state.interaction_count < 3:
                return "shy_greeting" if energy < 0.5 else "cheerful_greeting"
            else:
                return "extreme_excitement"

        elif trigger == BehaviorTrigger.PERSON_APPROACHED:
            if current_emotion == EmotionalState.SLEEPY:
                return "investigate_person"
            elif energy > 0.8:
                return "extreme_excitement"
            else:
                return "cheerful_greeting"

        elif trigger == BehaviorTrigger.VOICE_DETECTED:
            if random.random() < 0.3:  # Sometimes confused by voices
                return "confused_investigation"
            else:
                return "investigate_person"

        elif trigger == BehaviorTrigger.LOUD_NOISE:
            return "security_alert"

        elif trigger == BehaviorTrigger.TOUCH_DETECTED:
            return "playful_dance" if energy > 0.6 else "cheerful_greeting"

        elif trigger == BehaviorTrigger.TIMER:
            # Autonomous behavior selection
            behaviors = self._get_autonomous_behaviors()
            return random.choice(behaviors) if behaviors else None

        return None

    def _get_autonomous_behaviors(self) -> List[str]:
        """Get list of appropriate autonomous behaviors for current state"""
        current_emotion = self.character_state.emotional_state
        energy = self.character_state.energy_level

        if energy < 0.3:
            return ["sleepy_drift"]
        elif energy > 0.8 and current_emotion in [EmotionalState.HAPPY, EmotionalState.PLAYFUL]:
            return ["playful_dance", "extreme_excitement"]
        elif current_emotion == EmotionalState.CURIOUS:
            return ["investigate_person", "determined_scan"]
        elif current_emotion == EmotionalState.WORRIED:
            return ["worried_scanning", "security_alert"]
        else:
            return ["investigate_person", "determined_scan", "cheerful_greeting"]

    def _execute_behavior(self, behavior_name: str):
        """Execute a specific behavior pattern"""
        if behavior_name not in self.behavior_patterns:
            logger.error(f"Unknown behavior: {behavior_name}")
            return

        pattern = self.behavior_patterns[behavior_name]
        logger.info(f"🎬 Executing behavior: {pattern.name} ({pattern.emotional_state.value})")

        try:
            # Update character state based on behavior
            self._update_character_state_from_behavior(pattern)

            # Execute the behavior movements
            for movement in pattern.movements:
                if not self.behavior_active:
                    break

                # Execute movement through servo system
                self._execute_behavior_movement(movement)

                # Wait for movement duration
                time.sleep(movement.get("duration", 1.0))

            # Record behavior execution
            self.interaction_history.append({
                "behavior": behavior_name,
                "emotional_state": pattern.emotional_state.value,
                "timestamp": time.time(),
                "duration": pattern.duration
            })

            # Keep history limited
            if len(self.interaction_history) > 50:
                self.interaction_history = self.interaction_history[-25:]

            logger.info(f"✅ Behavior completed: {behavior_name}")

        except Exception as e:
            logger.error(f"Behavior execution failed: {e}")

    def _execute_behavior_movement(self, movement: Dict):
        """Execute a single behavior movement"""
        # This would interface with the servo system
        if self.servo_system and hasattr(self.servo_system, 'active_controller'):
            controller = self.servo_system.active_controller
            if not controller:
                return

            action = movement.get("action")

            if action == "dome_rotation":
                angle = movement.get("angle", 0)
                controller.move_servo_angle(0, angle + 180, (0, 360))

            elif action == "head_tilt":
                angle = movement.get("angle", 0)
                controller.move_servo_angle(1, angle + 30, (0, 60))

            elif action == "dome_panels":
                panels = movement.get("panels", {})
                panel_map = {
                    "front": 6, "left": 7, "right": 8, "back": 9
                }
                for panel_name, servo_channel in panel_map.items():
                    is_open = panels.get(panel_name, False)
                    position = 1800 if is_open else 1200
                    controller.move_servo_microseconds(servo_channel, position)

            elif action == "utility_arms":
                left = movement.get("left", 0)
                right = movement.get("right", 0)
                controller.move_servo_angle(4, left)
                controller.move_servo_angle(5, right)

            elif action == "periscope":
                extend = movement.get("extend", False)
                position = 1800 if extend else 1200
                controller.move_servo_microseconds(2, position)

    def _update_character_state_from_behavior(self, pattern: BehaviorPattern):
        """Update character emotional state based on executed behavior"""
        # Gradually shift emotional state
        self.character_state.emotional_state = pattern.emotional_state

        # Adjust energy based on behavior intensity
        if pattern.intensity == MovementIntensity.DRAMATIC:
            self.character_state.energy_level = min(1.0, self.character_state.energy_level + 0.2)
        elif pattern.intensity == MovementIntensity.SUBTLE:
            self.character_state.energy_level = max(0.1, self.character_state.energy_level - 0.1)

        # Update interaction count and timing
        self.character_state.last_interaction = time.time()
        self.character_state.interaction_count += 1

    def _check_autonomous_behaviors(self):
        """Check if autonomous behaviors should be triggered"""
        current_time = time.time()
        time_since_last = current_time - self.last_autonomous_behavior

        # Adjust autonomous interval based on character state
        interval = self.autonomous_interval
        if self.character_state.energy_level > 0.8:
            interval *= 0.7  # More frequent when energetic
        elif self.character_state.energy_level < 0.3:
            interval *= 2.0  # Less frequent when tired

        if time_since_last >= interval:
            # Trigger autonomous behavior
            self.trigger_behavior(BehaviorTrigger.TIMER)
            self.last_autonomous_behavior = current_time

    def _update_character_state(self):
        """Update character state over time"""
        current_time = time.time()
        time_since_interaction = current_time - self.character_state.last_interaction

        # Gradually decrease energy over time
        energy_decay = 0.01 * (time_since_interaction / 60.0)  # 1% per minute
        self.character_state.energy_level = max(0.1, self.character_state.energy_level - energy_decay)

        # Return to neutral emotional state over time
        if time_since_interaction > 300:  # 5 minutes
            self.character_state.emotional_state = EmotionalState.NEUTRAL

        # Increase sleepiness over time
        if time_since_interaction > 600:  # 10 minutes
            self.character_state.emotional_state = EmotionalState.SLEEPY

    # Public API Methods

    def trigger_behavior(self, trigger_type: BehaviorTrigger, context: Dict = None):
        """Trigger a behavior based on external input"""
        trigger_data = {
            "type": trigger_type.value,
            "context": context or {},
            "timestamp": time.time()
        }
        self.trigger_queue.put(trigger_data)
        logger.info(f"📋 Queued behavior trigger: {trigger_type.value}")

    def set_emotional_state(self, emotion: EmotionalState):
        """Manually set emotional state"""
        self.character_state.emotional_state = emotion
        logger.info(f"🎭 Emotional state set to: {emotion.value}")

    def set_energy_level(self, level: float):
        """Set energy level (0.0 to 1.0)"""
        self.character_state.energy_level = max(0.0, min(1.0, level))
        logger.info(f"⚡ Energy level set to: {level:.1f}")

    def get_character_status(self) -> Dict:
        """Get current character status"""
        return {
            "emotional_state": self.character_state.emotional_state.value,
            "energy_level": self.character_state.energy_level,
            "curiosity_level": self.character_state.curiosity_level,
            "sociability": self.character_state.sociability,
            "alertness": self.character_state.alertness,
            "playfulness": self.character_state.playfulness,
            "interaction_count": self.character_state.interaction_count,
            "last_interaction": self.character_state.last_interaction,
            "available_behaviors": list(self.behavior_patterns.keys()),
            "recent_behaviors": [h["behavior"] for h in self.interaction_history[-5:]]
        }

    def list_behaviors(self) -> List[Dict]:
        """List available behavior patterns"""
        return [
            {
                "name": pattern.name,
                "description": pattern.description,
                "emotional_state": pattern.emotional_state.value,
                "intensity": pattern.intensity.value,
                "duration": pattern.duration
            }
            for pattern in self.behavior_patterns.values()
        ]

    def execute_specific_behavior(self, behavior_name: str):
        """Execute a specific behavior by name"""
        if behavior_name in self.behavior_patterns:
            self._execute_behavior(behavior_name)
            return True
        else:
            logger.error(f"Unknown behavior: {behavior_name}")
            return False

    def shutdown(self):
        """Shutdown behavior engine"""
        logger.info("🔄 Shutting down behavior engine...")

        self.behavior_active = False

        # Wait for thread to finish
        if self.behavior_thread and self.behavior_thread.is_alive():
            self.behavior_thread.join(timeout=2.0)

        logger.info("✅ Behavior engine shutdown complete")

# Demo function
def demo_behavior_engine():
    """Demo the behavior engine"""
    logger.info("🎭 Starting Disney Behavior Engine Demo...")

    # This would normally use real servo system and script engine
    class MockServoSystem:
        def __init__(self):
            self.active_controller = MockController()

    class MockController:
        def move_servo_angle(self, channel, angle, range_tuple=None):
            logger.info(f"[MOCK] Servo {channel} -> {angle}°")

        def move_servo_microseconds(self, channel, microseconds):
            logger.info(f"[MOCK] Servo {channel} -> {microseconds}μs")

    servo_system = MockServoSystem()
    behavior_engine = DisneyBehaviorEngine(servo_system, None)

    try:
        # Display available behaviors
        behaviors = behavior_engine.list_behaviors()
        logger.info(f"Available behaviors: {len(behaviors)}")

        # Demo different emotional states
        emotions = [EmotionalState.HAPPY, EmotionalState.CURIOUS, EmotionalState.EXCITED]

        for emotion in emotions:
            logger.info(f"\n🎭 Setting emotional state: {emotion.value}")
            behavior_engine.set_emotional_state(emotion)

            # Trigger some behaviors
            behavior_engine.trigger_behavior(BehaviorTrigger.PERSON_DETECTED)
            time.sleep(5)

            behavior_engine.trigger_behavior(BehaviorTrigger.VOICE_DETECTED)
            time.sleep(3)

        # Display character status
        status = behavior_engine.get_character_status()
        logger.info(f"\n📊 Character Status:")
        logger.info(f"  Emotional State: {status['emotional_state']}")
        logger.info(f"  Energy Level: {status['energy_level']:.1f}")
        logger.info(f"  Interaction Count: {status['interaction_count']}")
        logger.info(f"  Recent Behaviors: {status['recent_behaviors']}")

        logger.info("\n✅ Behavior engine demo completed!")

    except KeyboardInterrupt:
        logger.info("Demo interrupted")
    except Exception as e:
        logger.error(f"Demo failed: {e}")
    finally:
        behavior_engine.shutdown()

if __name__ == "__main__":
    demo_behavior_engine()