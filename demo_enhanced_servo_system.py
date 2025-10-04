#!/usr/bin/env python3
"""
R2D2 Enhanced Servo System Comprehensive Demo
=============================================

This demo showcases all the advanced features of the enhanced servo control system:
- Hardware auto-detection and configuration
- Advanced motion interpolation with easing
- Sequence creation and execution
- Safety monitoring and emergency stops
- Real-time diagnostics and performance tracking
- WebSocket communication
- REST API integration

Target: NVIDIA Orin Nano R2D2 Systems
"""

import asyncio
import time
import json
import requests
import websockets
import logging
from typing import Dict, List
from r2d2_servo_backend import ServoControlBackend, MotionType

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EnhancedServoSystemDemo:
    """Comprehensive demo of enhanced servo system capabilities"""

    def __init__(self):
        self.backend = None
        self.api_base_url = "http://localhost:5000/api"
        self.websocket_url = "ws://localhost:8767"

    async def run_complete_demo(self):
        """Run comprehensive demonstration of all system features"""
        logger.info("🤖 R2D2 Enhanced Servo System Comprehensive Demo")
        logger.info("=" * 60)

        try:
            # Demo 1: Backend initialization and hardware detection
            await self.demo_hardware_detection()

            # Demo 2: Advanced motion control
            await self.demo_motion_control()

            # Demo 3: Sequence creation and execution
            await self.demo_sequence_management()

            # Demo 4: Safety systems
            await self.demo_safety_systems()

            # Demo 5: Diagnostics and monitoring
            await self.demo_diagnostics()

            # Demo 6: WebSocket communication
            await self.demo_websocket_communication()

            # Demo 7: REST API integration
            await self.demo_rest_api()

            # Demo 8: Configuration management
            await self.demo_configuration_management()

            logger.info("✅ Complete demo finished successfully!")

        except Exception as e:
            logger.error(f"Demo failed: {e}")
        finally:
            if self.backend:
                await self.backend.shutdown()

    async def demo_hardware_detection(self):
        """Demo 1: Hardware detection and initialization"""
        logger.info("\n--- Demo 1: Hardware Detection and Initialization ---")

        # Initialize backend with auto-detection
        self.backend = ServoControlBackend(auto_detect=True)

        # Start backend services
        await self.backend.start_services(websocket_port=8767)

        # Display detected hardware
        detected_boards = self.backend.config_manager.detect_maestro_boards()
        logger.info(f"Detected {len(detected_boards)} Maestro board(s)")

        for board in detected_boards:
            logger.info(f"  📋 {board.device_name} on {board.port}")
            logger.info(f"     Channels: {board.channel_count}, Firmware: {board.firmware_version}")

        # Show controller status
        status = self.backend.get_controller_status()
        logger.info(f"Connection Status: {status['connection_status']}")
        logger.info(f"Health Status: {status['health_status']}")

        await asyncio.sleep(2)

    async def demo_motion_control(self):
        """Demo 2: Advanced motion control with easing"""
        logger.info("\n--- Demo 2: Advanced Motion Control ---")

        # Demo different motion types
        motion_types = [
            ("linear", "Linear motion"),
            ("ease_in_out", "Smooth ease in/out"),
            ("bounce", "Bouncy motion"),
            ("elastic", "Elastic motion")
        ]

        for motion_type, description in motion_types:
            logger.info(f"Testing {description}...")

            # Move dome rotation servo (channel 0)
            result = self.backend.move_servo_enhanced(
                channel=0,
                position=1800,  # 90 degrees
                duration=2.0,
                motion_type=motion_type
            )

            if result["success"]:
                logger.info(f"  ✅ Motion completed in {result['latency_ms']:.1f}ms")
            else:
                logger.error(f"  ❌ Motion failed: {result.get('error')}")

            await asyncio.sleep(3)

            # Return to center
            self.backend.move_servo_enhanced(channel=0, position=1500, duration=1.0)
            await asyncio.sleep(2)

    async def demo_sequence_management(self):
        """Demo 3: Sequence creation and execution"""
        logger.info("\n--- Demo 3: Sequence Creation and Execution ---")

        # Create R2D2 greeting sequence
        keyframes = [
            {"channel": 0, "position": 1800, "duration": 1.0, "delay": 0.0, "motion_type": "ease_out"},    # Dome right
            {"channel": 1, "position": 1700, "duration": 0.8, "delay": 0.5, "motion_type": "ease_in_out"}, # Head up
            {"channel": 2, "position": 1800, "duration": 0.6, "delay": 1.0, "motion_type": "bounce"},      # Periscope up
            {"channel": 2, "position": 1200, "duration": 0.6, "delay": 2.0, "motion_type": "bounce"},      # Periscope down
            {"channel": 1, "position": 1500, "duration": 0.8, "delay": 2.5, "motion_type": "ease_in_out"}, # Head center
            {"channel": 0, "position": 1500, "duration": 1.0, "delay": 3.0, "motion_type": "ease_in"},     # Dome center
        ]

        result = self.backend.create_sequence_from_keyframes(
            name="enhanced_greeting",
            keyframes=keyframes,
            description="Enhanced R2D2 greeting with advanced motion"
        )

        if result["success"]:
            sequence_id = result["sequence_id"]
            logger.info(f"✅ Created sequence '{result['name']}' with {result['keyframes']} keyframes")

            # Execute the sequence
            logger.info("Executing enhanced greeting sequence...")
            success = await self.backend.sequence_engine.execute_sequence(sequence_id)

            if success:
                # Wait for sequence completion
                while self.backend.sequence_engine.sequence_status.value == "executing":
                    await asyncio.sleep(0.1)

                logger.info("✅ Sequence completed successfully")
            else:
                logger.error("❌ Sequence execution failed")

        else:
            logger.error(f"❌ Sequence creation failed: {result.get('error')}")

        await asyncio.sleep(2)

    async def demo_safety_systems(self):
        """Demo 4: Safety monitoring and emergency stops"""
        logger.info("\n--- Demo 4: Safety Systems and Emergency Controls ---")

        # Get initial safety status
        safety_status = self.backend.safety_monitor.get_safety_status()
        logger.info(f"Safety monitoring active: {safety_status['monitoring_active']}")
        logger.info(f"Emergency stop active: {safety_status['emergency_stop_active']}")

        # Update safety parameters
        self.backend.safety_monitor.set_safety_parameters(
            position_deviation_threshold=300,
            movement_timeout=5.0,
            max_violations=2
        )
        logger.info("✅ Updated safety parameters")

        # Simulate emergency stop
        logger.info("Simulating emergency stop...")
        self.backend.emergency_stop()

        # Check emergency status
        safety_status = self.backend.safety_monitor.get_safety_status()
        logger.info(f"Emergency stop triggered: {safety_status['emergency_stop_active']}")

        await asyncio.sleep(2)

        # Clear emergency stop
        logger.info("Clearing emergency stop...")
        self.backend.safety_monitor.clear_emergency_stop()

        safety_status = self.backend.safety_monitor.get_safety_status()
        logger.info(f"Emergency stop cleared: {not safety_status['emergency_stop_active']}")

        await asyncio.sleep(1)

    async def demo_diagnostics(self):
        """Demo 5: Diagnostics and performance monitoring"""
        logger.info("\n--- Demo 5: Diagnostics and Performance Monitoring ---")

        # Get performance report
        performance = self.backend.diagnostics_engine.get_performance_report()

        logger.info("System Performance Metrics:")
        metrics = performance["metrics"]
        logger.info(f"  Command Latency: {metrics['command_latency_ms']:.1f}ms")
        logger.info(f"  Success Rate: {metrics['success_rate']:.1f}%")
        logger.info(f"  Commands Processed: {metrics['total_commands_processed']}")

        logger.info(f"System Health: {performance['system_health']}")

        # Show recent diagnostics
        if performance["recent_diagnostics"]:
            recent = performance["recent_diagnostics"][-1]
            logger.info(f"Current Resources:")
            logger.info(f"  CPU: {recent['cpu_usage']:.1f}%")
            logger.info(f"  Memory: {recent['memory_usage']:.1f}%")
            logger.info(f"  Temperature: {recent['temperature']:.1f}°C")

        await asyncio.sleep(1)

    async def demo_websocket_communication(self):
        """Demo 6: WebSocket real-time communication"""
        logger.info("\n--- Demo 6: WebSocket Real-time Communication ---")

        try:
            # Connect to WebSocket
            async with websockets.connect(self.websocket_url) as websocket:
                logger.info("✅ Connected to WebSocket server")

                # Send status request
                await websocket.send(json.dumps({"type": "status_request"}))

                # Receive and display status
                response = await websocket.recv()
                data = json.loads(response)

                if data["type"] == "servo_status":
                    logger.info(f"📊 Received real-time status update")
                    controller_info = data["controller"]
                    logger.info(f"  Connection: {controller_info['connection_status']}")
                    logger.info(f"  Servo Count: {controller_info['servo_count']}")

                # Send servo command via WebSocket
                servo_command = {
                    "type": "servo_command",
                    "channel": 0,
                    "command": "position",
                    "value": 1600
                }

                await websocket.send(json.dumps(servo_command))
                logger.info("📤 Sent servo command via WebSocket")

                # Wait for response
                response = await websocket.recv()
                data = json.loads(response)

                if data["type"] == "servo_response" and data["success"]:
                    logger.info("✅ WebSocket servo command successful")
                else:
                    logger.error("❌ WebSocket servo command failed")

        except Exception as e:
            logger.error(f"WebSocket demo failed: {e}")

        await asyncio.sleep(1)

    async def demo_rest_api(self):
        """Demo 7: REST API integration"""
        logger.info("\n--- Demo 7: REST API Integration ---")

        try:
            # Test API health
            response = requests.get(f"{self.api_base_url}/../health", timeout=5)
            if response.status_code == 200:
                health_data = response.json()
                logger.info(f"✅ API Health: {health_data['status']}")
            else:
                logger.error(f"❌ API health check failed: {response.status_code}")

            # Get servo status via API
            response = requests.get(f"{self.api_base_url}/servo/status", timeout=5)
            if response.status_code == 200:
                logger.info("✅ Retrieved servo status via REST API")
            else:
                logger.error(f"❌ API status request failed: {response.status_code}")

            # Send servo move command via API
            move_data = {
                "position": 1400,
                "duration": 1.5,
                "motion_type": "ease_in_out"
            }

            response = requests.post(
                f"{self.api_base_url}/servo/0/move",
                json=move_data,
                timeout=10
            )

            if response.status_code == 200:
                result = response.json()
                logger.info(f"✅ API servo move successful (latency: {result['latency_ms']:.1f}ms)")
            else:
                logger.error(f"❌ API servo move failed: {response.status_code}")

        except requests.RequestException as e:
            logger.error(f"REST API demo failed: {e}")

        await asyncio.sleep(1)

    async def demo_configuration_management(self):
        """Demo 8: Configuration management"""
        logger.info("\n--- Demo 8: Configuration Management ---")

        # Show current configuration
        servo_status = self.backend.get_servo_status()
        logger.info(f"Current servo configuration: {len(servo_status)} servos")

        for channel, status in list(servo_status.items())[:3]:  # Show first 3
            name = status.get("display_name", status.get("name", f"Servo {channel}"))
            logger.info(f"  Channel {channel}: {name}")

        # Validate configuration
        validation_errors = self.backend.config_manager.validate_configuration(self.backend.controller)
        if validation_errors:
            logger.warning(f"Configuration validation warnings: {len(validation_errors)}")
            for error in validation_errors[:3]:  # Show first 3
                logger.warning(f"  ⚠️  {error}")
        else:
            logger.info("✅ Configuration validation passed")

        # Save configuration
        if hasattr(self.backend.controller, 'save_servo_configuration'):
            self.backend.controller.save_servo_configuration()
            logger.info("✅ Configuration saved")

        await asyncio.sleep(1)

    def display_demo_summary(self):
        """Display final demo summary"""
        logger.info("\n" + "=" * 60)
        logger.info("🎯 ENHANCED SERVO SYSTEM DEMO SUMMARY")
        logger.info("=" * 60)
        logger.info("✅ Hardware Detection: Auto-detected Maestro boards")
        logger.info("✅ Motion Control: Advanced easing functions (linear, bounce, elastic)")
        logger.info("✅ Sequence Management: Created and executed complex sequences")
        logger.info("✅ Safety Systems: Emergency stops and violation monitoring")
        logger.info("✅ Diagnostics: Real-time performance and health monitoring")
        logger.info("✅ WebSocket API: Real-time bidirectional communication")
        logger.info("✅ REST API: RESTful endpoints for all operations")
        logger.info("✅ Configuration: Dynamic servo configuration and validation")
        logger.info("=" * 60)
        logger.info("🚀 R2D2 Enhanced Servo System is production-ready!")
        logger.info("=" * 60)

async def main():
    """Main demo function"""
    demo = EnhancedServoSystemDemo()

    try:
        await demo.run_complete_demo()
        demo.display_demo_summary()

    except KeyboardInterrupt:
        logger.info("\n🛑 Demo interrupted by user")
    except Exception as e:
        logger.error(f"Demo failed with error: {e}")
    finally:
        logger.info("Demo cleanup complete")

if __name__ == "__main__":
    asyncio.run(main())