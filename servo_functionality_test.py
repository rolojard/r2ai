#!/usr/bin/env python3
"""
Servo Functionality Test
Test actual servo control capabilities with the installed ServoKit library
"""

import time
import logging
from adafruit_servokit import ServoKit

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_servo_kit():
    """Test ServoKit functionality"""
    try:
        # Initialize ServoKit with 16 channels at default address 0x40
        kit = ServoKit(channels=16, address=0x40)
        logger.info("ServoKit initialized successfully at address 0x40")

        # Test basic servo control
        logger.info("Testing basic servo movement on channel 0...")
        kit.servo[0].angle = 0
        time.sleep(1)
        kit.servo[0].angle = 90
        time.sleep(1)
        kit.servo[0].angle = 180
        time.sleep(1)
        kit.servo[0].angle = 90
        time.sleep(1)

        logger.info("✅ Servo control test completed successfully")
        return True

    except Exception as e:
        logger.error(f"❌ Servo control test failed: {e}")
        return False

def test_dome_panel_sequence():
    """Test dome panel opening sequence"""
    try:
        kit = ServoKit(channels=16, address=0x40)
        panel_channels = [8, 9, 10, 11, 12, 13, 14, 15]

        logger.info("Testing dome panel sequence...")

        # Sequential opening
        for i, channel in enumerate(panel_channels):
            logger.info(f"Opening panel {i+1} on channel {channel}")
            kit.servo[channel].angle = 90
            time.sleep(0.3)

        time.sleep(2)

        # Sequential closing
        for i, channel in enumerate(reversed(panel_channels)):
            logger.info(f"Closing panel {8-i} on channel {channel}")
            kit.servo[channel].angle = 0
            time.sleep(0.3)

        logger.info("✅ Dome panel sequence test completed")
        return True

    except Exception as e:
        logger.error(f"❌ Dome panel test failed: {e}")
        return False

def main():
    """Main test function"""
    logger.info("Starting servo functionality tests...")

    # Test basic servo control
    servo_basic = test_servo_kit()

    # Test dome panel sequence
    dome_panels = test_dome_panel_sequence()

    # Summary
    if servo_basic and dome_panels:
        logger.info("🎉 All servo tests passed - R2D2 servo system ready!")
        return 0
    else:
        logger.error("⚠️ Some servo tests failed - check hardware connections")
        return 1

if __name__ == "__main__":
    exit(main())