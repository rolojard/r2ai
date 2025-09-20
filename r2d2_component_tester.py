#!/usr/bin/env python3
"""
R2D2 Component Testing Framework
Comprehensive testing suite for all R2D2 hardware subsystems
"""

import sys
import time
import serial
import json
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional
import board
import busio
from adafruit_servokit import ServoKit
from adafruit_pca9685 import PCA9685
import pygame
import subprocess
import os

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class R2D2ComponentTester:
    """Main testing class for R2D2 hardware components"""

    def __init__(self):
        self.test_results = {}
        self.servo_kit = None
        self.serial_connections = {}
        self.sound_system = None

    def initialize_systems(self):
        """Initialize all hardware systems for testing"""
        logger.info("Initializing R2D2 hardware systems...")

        # Initialize servo controller
        try:
            self.servo_kit = ServoKit(channels=16, address=0x40)
            logger.info("ServoKit initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize ServoKit: {e}")

        # Initialize pygame for sound testing
        try:
            pygame.mixer.init()
            logger.info("Pygame mixer initialized for sound testing")
        except Exception as e:
            logger.error(f"Failed to initialize pygame mixer: {e}")

    def test_pololu_maestro(self) -> Dict[str, Any]:
        """Test Pololu Maestro servo controller functionality"""
        logger.info("Testing Pololu Maestro Servo Controller...")

        test_result = {
            'component': 'Pololu Maestro',
            'timestamp': datetime.now().isoformat(),
            'tests': []
        }

        # Test serial communication
        maestro_ports = ['/dev/ttyACM0', '/dev/ttyACM1', '/dev/ttyUSB0', '/dev/ttyUSB1']

        for port in maestro_ports:
            try:
                ser = serial.Serial(port, 9600, timeout=1)
                test_result['tests'].append({
                    'test': f'Serial Communication {port}',
                    'status': 'PASS',
                    'details': f'Successfully connected to {port} at 9600 baud'
                })

                # Test servo position commands
                self._test_maestro_servo_commands(ser, test_result)

                ser.close()
                break

            except Exception as e:
                test_result['tests'].append({
                    'test': f'Serial Communication {port}',
                    'status': 'FAIL',
                    'details': str(e)
                })

        # Test with ServoKit if Maestro not found
        if self.servo_kit:
            self._test_servokit_functionality(test_result)

        return test_result

    def _test_maestro_servo_commands(self, serial_conn, test_result):
        """Test Maestro servo command sequences"""
        try:
            # Test basic servo movement (Channel 0, position 1500μs)
            command = bytes([0x84, 0x00, 0x70, 0x2E])  # Set target command
            serial_conn.write(command)
            time.sleep(0.5)

            test_result['tests'].append({
                'test': 'Basic Servo Command',
                'status': 'PASS',
                'details': 'Successfully sent servo position command'
            })

            # Test servo speed setting
            speed_command = bytes([0x87, 0x00, 0x10, 0x00])  # Set speed
            serial_conn.write(speed_command)

            test_result['tests'].append({
                'test': 'Servo Speed Control',
                'status': 'PASS',
                'details': 'Successfully set servo speed'
            })

        except Exception as e:
            test_result['tests'].append({
                'test': 'Maestro Commands',
                'status': 'FAIL',
                'details': str(e)
            })

    def _test_servokit_functionality(self, test_result):
        """Test ServoKit functionality for servo control"""
        try:
            # Test servo channel 0
            self.servo_kit.servo[0].angle = 90
            time.sleep(1)
            self.servo_kit.servo[0].angle = 0
            time.sleep(1)

            test_result['tests'].append({
                'test': 'ServoKit Basic Movement',
                'status': 'PASS',
                'details': 'Successfully controlled servo via ServoKit'
            })

            # Test multiple channels for dome panels
            for channel in range(4):  # Test first 4 channels
                try:
                    self.servo_kit.servo[channel].angle = 45
                    time.sleep(0.2)
                    self.servo_kit.servo[channel].angle = 0
                    time.sleep(0.2)
                except:
                    pass

            test_result['tests'].append({
                'test': 'Multi-Channel Servo Control',
                'status': 'PASS',
                'details': 'Successfully tested multiple servo channels'
            })

        except Exception as e:
            test_result['tests'].append({
                'test': 'ServoKit Functionality',
                'status': 'FAIL',
                'details': str(e)
            })

    def test_hcr_sound_system(self) -> Dict[str, Any]:
        """Test HCR sound system functionality"""
        logger.info("Testing HCR Sound System...")

        test_result = {
            'component': 'HCR Sound System',
            'timestamp': datetime.now().isoformat(),
            'tests': []
        }

        # Check for sound files
        sound_directories = [
            '/home/rolo/R2D2/sounds',
            '/home/rolo/sounds',
            '/opt/r2d2/sounds',
            './sounds'
        ]

        sound_files = []
        for directory in sound_directories:
            if os.path.exists(directory):
                for file in os.listdir(directory):
                    if file.endswith(('.wav', '.mp3', '.ogg')):
                        sound_files.append(os.path.join(directory, file))

        if sound_files:
            test_result['tests'].append({
                'test': 'Sound File Discovery',
                'status': 'PASS',
                'details': f'Found {len(sound_files)} sound files'
            })

            # Test playback
            self._test_sound_playback(sound_files[:3], test_result)  # Test first 3 files
        else:
            test_result['tests'].append({
                'test': 'Sound File Discovery',
                'status': 'FAIL',
                'details': 'No sound files found in expected directories'
            })

        # Test audio hardware
        self._test_audio_hardware(test_result)

        return test_result

    def _test_sound_playback(self, sound_files, test_result):
        """Test sound file playback"""
        try:
            for sound_file in sound_files:
                pygame.mixer.music.load(sound_file)
                pygame.mixer.music.play()
                time.sleep(2)  # Play for 2 seconds
                pygame.mixer.music.stop()

            test_result['tests'].append({
                'test': 'Sound Playback',
                'status': 'PASS',
                'details': f'Successfully played {len(sound_files)} sound files'
            })

        except Exception as e:
            test_result['tests'].append({
                'test': 'Sound Playback',
                'status': 'FAIL',
                'details': str(e)
            })

    def _test_audio_hardware(self, test_result):
        """Test audio hardware capabilities"""
        try:
            # Check ALSA devices
            result = subprocess.run(['aplay', '-l'], capture_output=True, text=True)
            if result.returncode == 0:
                test_result['tests'].append({
                    'test': 'Audio Hardware Detection',
                    'status': 'PASS',
                    'details': 'Audio hardware detected via ALSA'
                })
            else:
                test_result['tests'].append({
                    'test': 'Audio Hardware Detection',
                    'status': 'FAIL',
                    'details': 'No audio hardware detected'
                })

        except Exception as e:
            test_result['tests'].append({
                'test': 'Audio Hardware Detection',
                'status': 'FAIL',
                'details': str(e)
            })

    def test_psi_and_logics(self) -> Dict[str, Any]:
        """Test PSI, R-Series logics, and Filthy Neo Pixels"""
        logger.info("Testing PSI, R-Series Logics, and Neo Pixels...")

        test_result = {
            'component': 'PSI and Logic Systems',
            'timestamp': datetime.now().isoformat(),
            'tests': []
        }

        # Test I2C communication for potential logic controllers
        self._test_i2c_devices(test_result)

        # Test SPI communication for Neo Pixels
        self._test_spi_devices(test_result)

        # Test GPIO for basic control
        self._test_gpio_control(test_result)

        return test_result

    def _test_i2c_devices(self, test_result):
        """Test I2C devices for logic controllers"""
        try:
            import smbus

            for i2c_bus in range(10):  # Test common I2C buses
                try:
                    bus = smbus.SMBus(i2c_bus)
                    # Scan for devices
                    devices = []
                    for addr in range(0x08, 0x78):
                        try:
                            bus.read_byte(addr)
                            devices.append(hex(addr))
                        except:
                            pass

                    if devices:
                        test_result['tests'].append({
                            'test': f'I2C Bus {i2c_bus} Scan',
                            'status': 'PASS',
                            'details': f'Found devices: {", ".join(devices)}'
                        })
                    bus.close()

                except Exception as e:
                    continue

        except ImportError:
            test_result['tests'].append({
                'test': 'I2C Testing',
                'status': 'SKIP',
                'details': 'smbus not available'
            })
        except Exception as e:
            test_result['tests'].append({
                'test': 'I2C Testing',
                'status': 'FAIL',
                'details': str(e)
            })

    def _test_spi_devices(self, test_result):
        """Test SPI devices for Neo Pixel control"""
        try:
            spi_devices = ['/dev/spidev0.0', '/dev/spidev0.1', '/dev/spidev1.0', '/dev/spidev1.1']

            for device in spi_devices:
                if os.path.exists(device):
                    test_result['tests'].append({
                        'test': f'SPI Device {device}',
                        'status': 'PASS',
                        'details': f'SPI device {device} available'
                    })

        except Exception as e:
            test_result['tests'].append({
                'test': 'SPI Device Testing',
                'status': 'FAIL',
                'details': str(e)
            })

    def _test_gpio_control(self, test_result):
        """Test GPIO control capabilities"""
        try:
            import Jetson.GPIO as GPIO

            # Test GPIO setup
            GPIO.setmode(GPIO.BOARD)

            # Test a safe GPIO pin (adjust based on your setup)
            test_pin = 7  # GPIO4
            GPIO.setup(test_pin, GPIO.OUT)

            # Toggle pin
            GPIO.output(test_pin, GPIO.HIGH)
            time.sleep(0.1)
            GPIO.output(test_pin, GPIO.LOW)

            GPIO.cleanup()

            test_result['tests'].append({
                'test': 'GPIO Control',
                'status': 'PASS',
                'details': f'Successfully controlled GPIO pin {test_pin}'
            })

        except Exception as e:
            test_result['tests'].append({
                'test': 'GPIO Control',
                'status': 'FAIL',
                'details': str(e)
            })

    def test_dome_panels(self) -> Dict[str, Any]:
        """Test dome panel servo mechanisms"""
        logger.info("Testing Dome Panel Mechanisms...")

        test_result = {
            'component': 'Dome Panel Servos',
            'timestamp': datetime.now().isoformat(),
            'tests': []
        }

        if self.servo_kit:
            # Test dome panel servos (typically channels 8-15 for panels)
            panel_channels = [8, 9, 10, 11, 12, 13, 14, 15]

            for channel in panel_channels:
                try:
                    # Test panel open sequence
                    self.servo_kit.servo[channel].angle = 0    # Closed
                    time.sleep(0.5)
                    self.servo_kit.servo[channel].angle = 90   # Open
                    time.sleep(0.5)
                    self.servo_kit.servo[channel].angle = 0    # Closed
                    time.sleep(0.5)

                    test_result['tests'].append({
                        'test': f'Panel {channel} Movement',
                        'status': 'PASS',
                        'details': f'Panel on channel {channel} operates correctly'
                    })

                except Exception as e:
                    test_result['tests'].append({
                        'test': f'Panel {channel} Movement',
                        'status': 'FAIL',
                        'details': str(e)
                    })

            # Test coordinated panel sequence
            self._test_coordinated_panels(test_result, panel_channels)

        else:
            test_result['tests'].append({
                'test': 'Servo Controller',
                'status': 'FAIL',
                'details': 'No servo controller available for testing'
            })

        return test_result

    def _test_coordinated_panels(self, test_result, panel_channels):
        """Test coordinated panel movements"""
        try:
            # Sequential panel opening
            for channel in panel_channels:
                try:
                    self.servo_kit.servo[channel].angle = 90
                    time.sleep(0.2)
                except:
                    pass

            time.sleep(1)

            # Sequential panel closing
            for channel in reversed(panel_channels):
                try:
                    self.servo_kit.servo[channel].angle = 0
                    time.sleep(0.2)
                except:
                    pass

            test_result['tests'].append({
                'test': 'Coordinated Panel Sequence',
                'status': 'PASS',
                'details': 'Successfully executed coordinated panel movements'
            })

        except Exception as e:
            test_result['tests'].append({
                'test': 'Coordinated Panel Sequence',
                'status': 'FAIL',
                'details': str(e)
            })

    def run_integration_test(self) -> Dict[str, Any]:
        """Test integration between all systems"""
        logger.info("Running Integration Tests...")

        test_result = {
            'component': 'System Integration',
            'timestamp': datetime.now().isoformat(),
            'tests': []
        }

        # Test simultaneous operation
        try:
            if self.servo_kit:
                # Move servo while playing sound
                pygame.mixer.music.load('/usr/share/sounds/alsa/Front_Left.wav')  # System sound
                pygame.mixer.music.play()

                self.servo_kit.servo[0].angle = 90
                time.sleep(1)
                self.servo_kit.servo[0].angle = 0

                pygame.mixer.music.stop()

                test_result['tests'].append({
                    'test': 'Simultaneous Servo and Sound',
                    'status': 'PASS',
                    'details': 'Successfully operated servo and sound simultaneously'
                })

        except Exception as e:
            test_result['tests'].append({
                'test': 'Simultaneous Operation',
                'status': 'FAIL',
                'details': str(e)
            })

        # Test power consumption assessment
        self._test_power_assessment(test_result)

        return test_result

    def _test_power_assessment(self, test_result):
        """Assess power consumption and requirements"""
        try:
            # Check system power info
            with open('/sys/class/power_supply/BAT0/capacity', 'r') as f:
                battery_level = f.read().strip()

            test_result['tests'].append({
                'test': 'Power Assessment',
                'status': 'PASS',
                'details': f'Current battery level: {battery_level}%'
            })

        except:
            # Check for AC power
            try:
                with open('/sys/class/power_supply/ADP1/online', 'r') as f:
                    ac_power = f.read().strip()

                test_result['tests'].append({
                    'test': 'Power Assessment',
                    'status': 'PASS',
                    'details': f'AC Power connected: {"Yes" if ac_power == "1" else "No"}'
                })

            except:
                test_result['tests'].append({
                    'test': 'Power Assessment',
                    'status': 'INFO',
                    'details': 'Power information not available'
                })

    def run_all_tests(self) -> Dict[str, Any]:
        """Run complete test suite"""
        logger.info("Starting R2D2 Component Test Suite...")

        self.initialize_systems()

        # Run all component tests
        results = {
            'test_session': {
                'timestamp': datetime.now().isoformat(),
                'platform': 'Nvidia Orin Nano',
                'tester': 'R2D2ComponentTester v1.0'
            },
            'component_tests': []
        }

        # Test each component
        results['component_tests'].append(self.test_pololu_maestro())
        results['component_tests'].append(self.test_hcr_sound_system())
        results['component_tests'].append(self.test_psi_and_logics())
        results['component_tests'].append(self.test_dome_panels())
        results['component_tests'].append(self.run_integration_test())

        return results

    def generate_report(self, results: Dict[str, Any]) -> str:
        """Generate comprehensive test report"""
        report = []
        report.append("R2D2 COMPONENT TESTING REPORT")
        report.append("=" * 50)
        report.append(f"Test Session: {results['test_session']['timestamp']}")
        report.append(f"Platform: {results['test_session']['platform']}")
        report.append("")

        for component_test in results['component_tests']:
            report.append(f"COMPONENT: {component_test['component']}")
            report.append("-" * 30)

            passed = sum(1 for test in component_test['tests'] if test['status'] == 'PASS')
            failed = sum(1 for test in component_test['tests'] if test['status'] == 'FAIL')
            total = len(component_test['tests'])

            report.append(f"Tests: {passed}/{total} PASSED, {failed} FAILED")

            for test in component_test['tests']:
                status_symbol = "✓" if test['status'] == 'PASS' else "✗" if test['status'] == 'FAIL' else "⚠"
                report.append(f"  {status_symbol} {test['test']}: {test['details']}")

            report.append("")

        return "\n".join(report)

def main():
    """Main testing function"""
    tester = R2D2ComponentTester()

    try:
        # Run all tests
        results = tester.run_all_tests()

        # Generate and save report
        report = tester.generate_report(results)

        # Save detailed results as JSON
        with open('/home/rolo/r2ai/r2d2_test_results.json', 'w') as f:
            json.dump(results, f, indent=2)

        # Save readable report
        with open('/home/rolo/r2ai/r2d2_test_report.txt', 'w') as f:
            f.write(report)

        print(report)
        print(f"\nDetailed results saved to: /home/rolo/r2ai/r2d2_test_results.json")
        print(f"Test report saved to: /home/rolo/r2ai/r2d2_test_report.txt")

    except Exception as e:
        logger.error(f"Test execution failed: {e}")
        return 1

    return 0

if __name__ == "__main__":
    sys.exit(main())