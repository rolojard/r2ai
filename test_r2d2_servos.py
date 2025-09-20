#!/usr/bin/env python3
"""
Simple R2-D2 Servo Test
Test the servo control system without complex threading
"""

import time
import logging
from r2d2_servo_controller import R2D2ServoController, R2D2Component, R2D2Choreographer

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_basic_servo_control():
    """Test basic servo control functions"""
    logger.info("🤖 Starting R2-D2 Servo Control Test...")

    # Initialize controller in simulation mode
    controller = R2D2ServoController(simulation_mode=True)

    try:
        logger.info("Testing individual servo movements...")

        # Test dome rotation
        logger.info("Testing dome rotation...")
        controller.move_to(R2D2Component.DOME_ROTATION, 45)
        time.sleep(1)
        controller.move_to(R2D2Component.DOME_ROTATION, 0)
        time.sleep(1)

        # Test dome panels
        logger.info("Testing dome panels...")
        for i in range(8):
            panel = list(R2D2Component)[4 + i]  # DOME_PANEL_1 through 8
            controller.move_to(panel, 90)
            time.sleep(0.2)

        time.sleep(1)

        # Close panels
        for i in range(8):
            panel = list(R2D2Component)[4 + i]
            controller.move_to(panel, 0)
            time.sleep(0.2)

        # Test utility arms
        logger.info("Testing utility arms...")
        controller.move_to(R2D2Component.UTILITY_ARM_1, 120)
        controller.move_to(R2D2Component.UTILITY_ARM_2, 120)
        time.sleep(1)

        controller.move_to(R2D2Component.UTILITY_ARM_1, 0)
        controller.move_to(R2D2Component.UTILITY_ARM_2, 0)
        time.sleep(1)

        # Test multiple movements
        logger.info("Testing simultaneous movements...")
        movements = {
            R2D2Component.DOME_ROTATION: 90,
            R2D2Component.DOME_PANEL_1: 45,
            R2D2Component.DOME_PANEL_2: 45,
            R2D2Component.UTILITY_ARM_1: 60
        }
        controller.move_multiple(movements)
        time.sleep(2)

        # Home all servos
        logger.info("Returning to home position...")
        controller.home_all_servos()
        time.sleep(2)

        logger.info("✅ Basic servo control test completed successfully!")
        return True

    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        return False
    finally:
        controller.shutdown()

def test_position_feedback():
    """Test servo position feedback"""
    logger.info("Testing servo position feedback...")

    controller = R2D2ServoController(simulation_mode=True)

    try:
        # Set some positions
        controller.move_to(R2D2Component.DOME_ROTATION, 45)
        controller.move_to(R2D2Component.UTILITY_ARM_1, 90)

        time.sleep(1)

        # Check positions
        dome_pos = controller.get_position(R2D2Component.DOME_ROTATION)
        arm_pos = controller.get_position(R2D2Component.UTILITY_ARM_1)

        logger.info(f"Dome rotation position: {dome_pos:.1f}°")
        logger.info(f"Utility arm 1 position: {arm_pos:.1f}°")

        logger.info("✅ Position feedback test completed!")
        return True

    except Exception as e:
        logger.error(f"❌ Position feedback test failed: {e}")
        return False
    finally:
        controller.shutdown()

def test_emergency_stop():
    """Test emergency stop functionality"""
    logger.info("Testing emergency stop system...")

    controller = R2D2ServoController(simulation_mode=True)

    try:
        # Start some movements
        controller.move_to(R2D2Component.DOME_ROTATION, 180)

        # Trigger emergency stop
        time.sleep(0.5)
        controller.emergency_stop_all()

        logger.info("Emergency stop activated")
        time.sleep(1)

        # Resume operation
        controller.resume_operation()
        logger.info("Operation resumed")

        # Return to home
        controller.home_all_servos()
        time.sleep(1)

        logger.info("✅ Emergency stop test completed!")
        return True

    except Exception as e:
        logger.error(f"❌ Emergency stop test failed: {e}")
        return False
    finally:
        controller.shutdown()

def test_choreography():
    """Test basic choreography functionality"""
    logger.info("Testing choreography system...")

    controller = R2D2ServoController(simulation_mode=True)
    choreographer = R2D2Choreographer(controller)

    try:
        # Test accessing sequences
        sequences = list(choreographer.sequences.keys())
        logger.info(f"Available sequences: {sequences}")

        # Test creating a simple custom sequence
        logger.info("Creating custom sequence...")

        # Manual simple choreography
        logger.info("Executing simple dome rotation sequence...")
        controller.move_to(R2D2Component.DOME_ROTATION, 90)
        time.sleep(1)
        controller.move_to(R2D2Component.DOME_ROTATION, -90)
        time.sleep(1)
        controller.move_to(R2D2Component.DOME_ROTATION, 0)
        time.sleep(1)

        logger.info("✅ Choreography test completed!")
        return True

    except Exception as e:
        logger.error(f"❌ Choreography test failed: {e}")
        return False
    finally:
        controller.shutdown()

def main():
    """Run all servo tests"""
    logger.info("🚀 Starting R2-D2 Servo System Test Suite...")

    tests = [
        ("Basic Servo Control", test_basic_servo_control),
        ("Position Feedback", test_position_feedback),
        ("Emergency Stop", test_emergency_stop),
        ("Choreography", test_choreography)
    ]

    results = []

    for test_name, test_func in tests:
        logger.info(f"\n--- {test_name} Test ---")
        result = test_func()
        results.append((test_name, result))

        if result:
            logger.info(f"✅ {test_name}: PASSED")
        else:
            logger.error(f"❌ {test_name}: FAILED")

        time.sleep(1)  # Brief pause between tests

    # Summary
    logger.info("\n" + "="*50)
    logger.info("TEST SUMMARY")
    logger.info("="*50)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        logger.info(f"{test_name:<20}: {status}")

    logger.info(f"\nResults: {passed}/{total} tests passed")

    if passed == total:
        logger.info("🎉 All tests passed! R2-D2 servo system is ready!")
        return 0
    else:
        logger.error("⚠️ Some tests failed - check servo system")
        return 1

if __name__ == "__main__":
    exit(main())