#!/usr/bin/env python3
"""
R2D2 Basic Component Testing Framework
Simplified testing suite for R2D2 hardware subsystems without GPIO dependencies
"""

import sys
import time
import serial
import json
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional
import subprocess
import os
import glob

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class R2D2BasicTester:
    """Basic testing class for R2D2 hardware components"""

    def __init__(self):
        self.test_results = {}

    def test_pololu_maestro(self) -> Dict[str, Any]:
        """Test Pololu Maestro servo controller functionality"""
        logger.info("Testing Pololu Maestro Servo Controller...")

        test_result = {
            'component': 'Pololu Maestro',
            'timestamp': datetime.now().isoformat(),
            'tests': []
        }

        # Check for serial devices
        serial_devices = glob.glob('/dev/ttyACM*') + glob.glob('/dev/ttyUSB*')

        if serial_devices:
            test_result['tests'].append({
                'test': 'Serial Device Detection',
                'status': 'PASS',
                'details': f'Found serial devices: {", ".join(serial_devices)}'
            })

            # Test communication with each device
            for device in serial_devices:
                self._test_serial_device(device, test_result)

        else:
            test_result['tests'].append({
                'test': 'Serial Device Detection',
                'status': 'FAIL',
                'details': 'No serial devices found (ACM/USB)'
            })

        # Check for I2C devices (common for servo controllers)
        self._test_i2c_servo_controllers(test_result)

        return test_result

    def _test_serial_device(self, device, test_result):
        """Test individual serial device"""
        try:
            ser = serial.Serial(device, 9600, timeout=1)

            test_result['tests'].append({
                'test': f'Serial Connection {device}',
                'status': 'PASS',
                'details': f'Successfully opened {device} at 9600 baud'
            })

            # Try to send a Maestro command (get position)
            try:
                # Maestro "Get Position" command for channel 0
                ser.write(bytes([0x90, 0x00]))  # Get position command
                time.sleep(0.1)

                response = ser.read(2)
                if len(response) >= 2:
                    position = (response[1] << 8) | response[0]
                    test_result['tests'].append({
                        'test': f'Maestro Position Read {device}',
                        'status': 'PASS',
                        'details': f'Read position: {position} from channel 0'
                    })
                else:
                    test_result['tests'].append({
                        'test': f'Maestro Position Read {device}',
                        'status': 'FAIL',
                        'details': 'No response to position command'
                    })

            except Exception as e:
                test_result['tests'].append({
                    'test': f'Maestro Command Test {device}',
                    'status': 'FAIL',
                    'details': str(e)
                })

            ser.close()

        except Exception as e:
            test_result['tests'].append({
                'test': f'Serial Connection {device}',
                'status': 'FAIL',
                'details': str(e)
            })

    def _test_i2c_servo_controllers(self, test_result):
        """Test I2C servo controllers like PCA9685"""
        try:
            # Check available I2C buses
            i2c_buses = glob.glob('/dev/i2c-*')

            if i2c_buses:
                test_result['tests'].append({
                    'test': 'I2C Bus Detection',
                    'status': 'PASS',
                    'details': f'Found I2C buses: {", ".join(i2c_buses)}'
                })

                # Try to detect PCA9685 (common servo controller)
                self._scan_i2c_devices(test_result)

            else:
                test_result['tests'].append({
                    'test': 'I2C Bus Detection',
                    'status': 'FAIL',
                    'details': 'No I2C buses found'
                })

        except Exception as e:
            test_result['tests'].append({
                'test': 'I2C Controller Detection',
                'status': 'FAIL',
                'details': str(e)
            })

    def _scan_i2c_devices(self, test_result):
        """Scan I2C buses for devices"""
        try:
            # Use i2cdetect to scan for devices
            for i in range(0, 10):  # Check first 10 I2C buses
                try:
                    result = subprocess.run(['i2cdetect', '-y', str(i)],
                                         capture_output=True, text=True, timeout=5)

                    if result.returncode == 0 and result.stdout:
                        # Parse output for device addresses
                        devices = []
                        lines = result.stdout.split('\n')
                        for line in lines[1:]:  # Skip header
                            if ':' in line:
                                parts = line.split(':')[1].split()
                                for part in parts:
                                    if part not in ['--', '']:
                                        devices.append(f"0x{part}")

                        if devices:
                            test_result['tests'].append({
                                'test': f'I2C Bus {i} Device Scan',
                                'status': 'PASS',
                                'details': f'Found devices: {", ".join(devices)}'
                            })

                            # Check for common servo controller addresses
                            servo_controllers = ['0x40', '0x41', '0x70', '0x71']  # PCA9685 common addresses
                            found_controllers = [addr for addr in devices if addr in servo_controllers]

                            if found_controllers:
                                test_result['tests'].append({
                                    'test': f'Servo Controller Detection I2C-{i}',
                                    'status': 'PASS',
                                    'details': f'Potential servo controllers at: {", ".join(found_controllers)}'
                                })

                except subprocess.TimeoutExpired:
                    continue
                except Exception:
                    continue

        except Exception as e:
            test_result['tests'].append({
                'test': 'I2C Device Scan',
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

        # Check for sound hardware
        self._test_audio_hardware(test_result)

        # Check for sound files
        self._test_sound_files(test_result)

        # Test audio output capabilities
        self._test_audio_output(test_result)

        return test_result

    def _test_audio_hardware(self, test_result):
        """Test audio hardware detection"""
        try:
            # Check ALSA devices
            result = subprocess.run(['aplay', '-l'], capture_output=True, text=True)
            if result.returncode == 0:
                cards = result.stdout.count('card')
                test_result['tests'].append({
                    'test': 'Audio Hardware Detection',
                    'status': 'PASS',
                    'details': f'Found {cards} audio card(s) via ALSA'
                })

                # Get device details
                test_result['tests'].append({
                    'test': 'Audio Device List',
                    'status': 'INFO',
                    'details': result.stdout.strip()
                })

            else:
                test_result['tests'].append({
                    'test': 'Audio Hardware Detection',
                    'status': 'FAIL',
                    'details': 'No audio hardware detected via ALSA'
                })

        except Exception as e:
            test_result['tests'].append({
                'test': 'Audio Hardware Detection',
                'status': 'FAIL',
                'details': str(e)
            })

        # Check PulseAudio
        try:
            result = subprocess.run(['pactl', 'info'], capture_output=True, text=True)
            if result.returncode == 0:
                test_result['tests'].append({
                    'test': 'PulseAudio Status',
                    'status': 'PASS',
                    'details': 'PulseAudio running'
                })
            else:
                test_result['tests'].append({
                    'test': 'PulseAudio Status',
                    'status': 'FAIL',
                    'details': 'PulseAudio not running'
                })

        except Exception as e:
            test_result['tests'].append({
                'test': 'PulseAudio Status',
                'status': 'FAIL',
                'details': str(e)
            })

    def _test_sound_files(self, test_result):
        """Check for R2D2 sound files"""
        sound_directories = [
            '/home/rolo/R2D2/sounds',
            '/home/rolo/sounds',
            '/opt/r2d2/sounds',
            './sounds',
            '/usr/share/sounds'
        ]

        all_sound_files = []
        for directory in sound_directories:
            if os.path.exists(directory):
                sound_files = []
                for ext in ['*.wav', '*.mp3', '*.ogg', '*.flac']:
                    sound_files.extend(glob.glob(os.path.join(directory, ext)))
                    sound_files.extend(glob.glob(os.path.join(directory, '**', ext), recursive=True))

                if sound_files:
                    all_sound_files.extend(sound_files)
                    test_result['tests'].append({
                        'test': f'Sound Files in {directory}',
                        'status': 'PASS',
                        'details': f'Found {len(sound_files)} sound files'
                    })

        if all_sound_files:
            test_result['tests'].append({
                'test': 'Total Sound File Discovery',
                'status': 'PASS',
                'details': f'Total: {len(all_sound_files)} sound files found'
            })
        else:
            test_result['tests'].append({
                'test': 'Sound File Discovery',
                'status': 'FAIL',
                'details': 'No sound files found in expected directories'
            })

    def _test_audio_output(self, test_result):
        """Test basic audio output"""
        try:
            # Test with a system sound if available
            test_sound = '/usr/share/sounds/alsa/Front_Left.wav'
            if os.path.exists(test_sound):
                result = subprocess.run(['aplay', test_sound],
                                      capture_output=True, text=True, timeout=5)
                if result.returncode == 0:
                    test_result['tests'].append({
                        'test': 'Audio Playback Test',
                        'status': 'PASS',
                        'details': 'Successfully played test sound via aplay'
                    })
                else:
                    test_result['tests'].append({
                        'test': 'Audio Playback Test',
                        'status': 'FAIL',
                        'details': f'aplay failed: {result.stderr}'
                    })
            else:
                test_result['tests'].append({
                    'test': 'Audio Playback Test',
                    'status': 'SKIP',
                    'details': 'No test sound file available'
                })

        except Exception as e:
            test_result['tests'].append({
                'test': 'Audio Playback Test',
                'status': 'FAIL',
                'details': str(e)
            })

    def test_psi_and_logics(self) -> Dict[str, Any]:
        """Test PSI, R-Series logics, and Neo Pixels"""
        logger.info("Testing PSI, R-Series Logics, and Neo Pixels...")

        test_result = {
            'component': 'PSI and Logic Systems',
            'timestamp': datetime.now().isoformat(),
            'tests': []
        }

        # Test SPI devices (Neo Pixels often use SPI)
        self._test_spi_devices(test_result)

        # Test GPIO availability
        self._test_gpio_availability(test_result)

        # Check for LED control libraries
        self._test_led_libraries(test_result)

        return test_result

    def _test_spi_devices(self, test_result):
        """Test SPI devices for Neo Pixel control"""
        try:
            spi_devices = glob.glob('/dev/spidev*')

            if spi_devices:
                test_result['tests'].append({
                    'test': 'SPI Device Detection',
                    'status': 'PASS',
                    'details': f'Found SPI devices: {", ".join(spi_devices)}'
                })

                # Test SPI device permissions
                accessible_devices = []
                for device in spi_devices:
                    if os.access(device, os.R_OK | os.W_OK):
                        accessible_devices.append(device)

                if accessible_devices:
                    test_result['tests'].append({
                        'test': 'SPI Device Access',
                        'status': 'PASS',
                        'details': f'Accessible devices: {", ".join(accessible_devices)}'
                    })
                else:
                    test_result['tests'].append({
                        'test': 'SPI Device Access',
                        'status': 'FAIL',
                        'details': 'No SPI devices accessible (permission issue)'
                    })

            else:
                test_result['tests'].append({
                    'test': 'SPI Device Detection',
                    'status': 'FAIL',
                    'details': 'No SPI devices found'
                })

        except Exception as e:
            test_result['tests'].append({
                'test': 'SPI Device Testing',
                'status': 'FAIL',
                'details': str(e)
            })

    def _test_gpio_availability(self, test_result):
        """Test GPIO availability"""
        try:
            gpio_devices = glob.glob('/dev/gpiochip*')

            if gpio_devices:
                test_result['tests'].append({
                    'test': 'GPIO Device Detection',
                    'status': 'PASS',
                    'details': f'Found GPIO devices: {", ".join(gpio_devices)}'
                })

                # Check GPIO permissions
                accessible_gpio = []
                for device in gpio_devices:
                    if os.access(device, os.R_OK | os.W_OK):
                        accessible_gpio.append(device)

                if accessible_gpio:
                    test_result['tests'].append({
                        'test': 'GPIO Device Access',
                        'status': 'PASS',
                        'details': f'Accessible GPIO: {", ".join(accessible_gpio)}'
                    })
                else:
                    test_result['tests'].append({
                        'test': 'GPIO Device Access',
                        'status': 'FAIL',
                        'details': 'GPIO devices not accessible (permission issue)'
                    })

            else:
                test_result['tests'].append({
                    'test': 'GPIO Device Detection',
                    'status': 'FAIL',
                    'details': 'No GPIO devices found'
                })

        except Exception as e:
            test_result['tests'].append({
                'test': 'GPIO Availability Test',
                'status': 'FAIL',
                'details': str(e)
            })

    def _test_led_libraries(self, test_result):
        """Test for LED control libraries"""
        try:
            # Check for common LED/NeoPixel libraries
            led_libraries = [
                'adafruit-circuitpython-neopixel',
                'rpi_ws281x',
                'neopixel',
                'board',
                'adafruit-blinka'
            ]

            result = subprocess.run(['pip', 'list'], capture_output=True, text=True)
            installed_libs = result.stdout.lower()

            found_libs = []
            for lib in led_libraries:
                if lib.lower() in installed_libs:
                    found_libs.append(lib)

            if found_libs:
                test_result['tests'].append({
                    'test': 'LED Control Libraries',
                    'status': 'PASS',
                    'details': f'Found libraries: {", ".join(found_libs)}'
                })
            else:
                test_result['tests'].append({
                    'test': 'LED Control Libraries',
                    'status': 'FAIL',
                    'details': 'No LED control libraries found'
                })

        except Exception as e:
            test_result['tests'].append({
                'test': 'LED Library Detection',
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

        # Since we can't directly control servos without hardware setup,
        # we'll test for the presence of control systems
        self._test_servo_control_systems(test_result)

        return test_result

    def _test_servo_control_systems(self, test_result):
        """Test for servo control systems"""
        # Check for servo libraries
        try:
            result = subprocess.run(['pip', 'list'], capture_output=True, text=True)
            servo_libs = ['adafruit-servokit', 'adafruit-pca9685', 'adafruit-motor']

            found_servo_libs = []
            for lib in servo_libs:
                if lib in result.stdout.lower():
                    found_servo_libs.append(lib)

            if found_servo_libs:
                test_result['tests'].append({
                    'test': 'Servo Control Libraries',
                    'status': 'PASS',
                    'details': f'Found: {", ".join(found_servo_libs)}'
                })
            else:
                test_result['tests'].append({
                    'test': 'Servo Control Libraries',
                    'status': 'FAIL',
                    'details': 'No servo control libraries found'
                })

        except Exception as e:
            test_result['tests'].append({
                'test': 'Servo Library Detection',
                'status': 'FAIL',
                'details': str(e)
            })

        # Test PWM capabilities (needed for servo control)
        self._test_pwm_capabilities(test_result)

    def _test_pwm_capabilities(self, test_result):
        """Test PWM capabilities for servo control"""
        try:
            # Check for PWM devices
            pwm_devices = glob.glob('/sys/class/pwm/pwmchip*')

            if pwm_devices:
                test_result['tests'].append({
                    'test': 'PWM Device Detection',
                    'status': 'PASS',
                    'details': f'Found PWM devices: {", ".join(pwm_devices)}'
                })

                # Check PWM accessibility
                accessible_pwm = 0
                for device in pwm_devices:
                    try:
                        export_path = os.path.join(device, 'export')
                        if os.path.exists(export_path):
                            accessible_pwm += 1
                    except:
                        pass

                test_result['tests'].append({
                    'test': 'PWM Device Access',
                    'status': 'PASS' if accessible_pwm > 0 else 'WARN',
                    'details': f'{accessible_pwm} PWM devices accessible'
                })

            else:
                test_result['tests'].append({
                    'test': 'PWM Device Detection',
                    'status': 'FAIL',
                    'details': 'No PWM devices found'
                })

        except Exception as e:
            test_result['tests'].append({
                'test': 'PWM Capability Test',
                'status': 'FAIL',
                'details': str(e)
            })

    def test_integration_capabilities(self) -> Dict[str, Any]:
        """Test integration capabilities between systems"""
        logger.info("Testing Integration Capabilities...")

        test_result = {
            'component': 'System Integration',
            'timestamp': datetime.now().isoformat(),
            'tests': []
        }

        # Test power management
        self._test_power_management(test_result)

        # Test communication capabilities
        self._test_communication_systems(test_result)

        # Test timing and coordination
        self._test_timing_capabilities(test_result)

        return test_result

    def _test_power_management(self, test_result):
        """Test power management capabilities"""
        try:
            # Check CPU governor
            with open('/sys/devices/system/cpu/cpu0/cpufreq/scaling_governor', 'r') as f:
                governor = f.read().strip()

            test_result['tests'].append({
                'test': 'CPU Power Management',
                'status': 'PASS',
                'details': f'CPU governor: {governor}'
            })

        except Exception as e:
            test_result['tests'].append({
                'test': 'CPU Power Management',
                'status': 'FAIL',
                'details': str(e)
            })

        # Check thermal management
        try:
            thermal_zones = glob.glob('/sys/class/thermal/thermal_zone*/temp')
            temps = []
            for zone in thermal_zones:
                try:
                    with open(zone, 'r') as f:
                        temp = int(f.read().strip()) / 1000
                        temps.append(f"{temp:.1f}°C")
                except:
                    pass

            if temps:
                test_result['tests'].append({
                    'test': 'Thermal Management',
                    'status': 'PASS',
                    'details': f'Temperatures: {", ".join(temps)}'
                })

        except Exception as e:
            test_result['tests'].append({
                'test': 'Thermal Management',
                'status': 'FAIL',
                'details': str(e)
            })

    def _test_communication_systems(self, test_result):
        """Test communication system capabilities"""
        # Check network capabilities for remote control
        try:
            result = subprocess.run(['ip', 'addr'], capture_output=True, text=True)
            if 'inet ' in result.stdout:
                interfaces = result.stdout.count('inet ')
                test_result['tests'].append({
                    'test': 'Network Interfaces',
                    'status': 'PASS',
                    'details': f'Found {interfaces} network interface(s)'
                })
            else:
                test_result['tests'].append({
                    'test': 'Network Interfaces',
                    'status': 'FAIL',
                    'details': 'No network interfaces found'
                })

        except Exception as e:
            test_result['tests'].append({
                'test': 'Network Capabilities',
                'status': 'FAIL',
                'details': str(e)
            })

    def _test_timing_capabilities(self, test_result):
        """Test system timing capabilities"""
        try:
            # Test system clock resolution
            start_time = time.time()
            time.sleep(0.001)  # 1ms sleep
            end_time = time.time()

            resolution = (end_time - start_time) * 1000  # Convert to ms

            test_result['tests'].append({
                'test': 'Timing Resolution',
                'status': 'PASS',
                'details': f'Minimum timing resolution: {resolution:.2f}ms'
            })

        except Exception as e:
            test_result['tests'].append({
                'test': 'Timing Capabilities',
                'status': 'FAIL',
                'details': str(e)
            })

    def run_all_tests(self) -> Dict[str, Any]:
        """Run complete test suite"""
        logger.info("Starting R2D2 Basic Component Test Suite...")

        results = {
            'test_session': {
                'timestamp': datetime.now().isoformat(),
                'platform': 'Nvidia Orin Nano',
                'tester': 'R2D2BasicTester v1.0'
            },
            'component_tests': []
        }

        # Run all component tests
        results['component_tests'].append(self.test_pololu_maestro())
        results['component_tests'].append(self.test_hcr_sound_system())
        results['component_tests'].append(self.test_psi_and_logics())
        results['component_tests'].append(self.test_dome_panels())
        results['component_tests'].append(self.test_integration_capabilities())

        return results

    def generate_report(self, results: Dict[str, Any]) -> str:
        """Generate comprehensive test report"""
        report = []
        report.append("R2D2 COMPONENT TESTING REPORT")
        report.append("=" * 50)
        report.append(f"Test Session: {results['test_session']['timestamp']}")
        report.append(f"Platform: {results['test_session']['platform']}")
        report.append("")

        total_passed = 0
        total_failed = 0
        total_tests = 0

        for component_test in results['component_tests']:
            report.append(f"COMPONENT: {component_test['component']}")
            report.append("-" * 30)

            passed = sum(1 for test in component_test['tests'] if test['status'] == 'PASS')
            failed = sum(1 for test in component_test['tests'] if test['status'] == 'FAIL')
            total = len(component_test['tests'])

            total_passed += passed
            total_failed += failed
            total_tests += total

            report.append(f"Tests: {passed}/{total} PASSED, {failed} FAILED")

            for test in component_test['tests']:
                if test['status'] == 'PASS':
                    status_symbol = "✓"
                elif test['status'] == 'FAIL':
                    status_symbol = "✗"
                elif test['status'] == 'WARN':
                    status_symbol = "⚠"
                else:  # INFO, SKIP
                    status_symbol = "ℹ"

                report.append(f"  {status_symbol} {test['test']}: {test['details']}")

            report.append("")

        # Summary
        report.append("OVERALL SUMMARY")
        report.append("=" * 20)
        report.append(f"Total Tests: {total_tests}")
        report.append(f"Passed: {total_passed}")
        report.append(f"Failed: {total_failed}")
        report.append(f"Success Rate: {(total_passed/total_tests*100):.1f}%")

        return "\n".join(report)

def main():
    """Main testing function"""
    tester = R2D2BasicTester()

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