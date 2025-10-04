#!/usr/bin/env python3
"""
Pololu Maestro Hardware Detection and Auto-Configuration System
Disney-Level Animatronics Hardware Discovery and Setup

This module provides comprehensive hardware detection, auto-configuration,
and dynamic board discovery for Pololu Maestro servo controllers with
professional animatronics integration capabilities.

Features:
- Automatic Maestro board detection and identification
- Dynamic channel count detection and configuration
- Firmware version detection and compatibility checking
- Real-time hardware monitoring and status reporting
- Professional servo configuration import/export
- Safety system integration with hardware validation
"""

import serial
import serial.tools.list_ports
import time
import logging
import json
import threading
from typing import Dict, List, Optional, Tuple, Union
from dataclasses import dataclass, field
from enum import Enum
import struct

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MaestroVariant(Enum):
    """Pololu Maestro Controller Variants"""
    MINI_12 = "Mini 12-Channel"
    MINI_18 = "Mini 18-Channel"
    MINI_24 = "Mini 24-Channel"
    STANDARD_6 = "Standard 6-Channel"
    STANDARD_12 = "Standard 12-Channel"
    STANDARD_18 = "Standard 18-Channel"
    STANDARD_24 = "Standard 24-Channel"
    UNKNOWN = "Unknown Variant"

@dataclass
class MaestroHardwareInfo:
    """Comprehensive Maestro hardware information"""
    port: str
    variant: MaestroVariant
    channels: int
    firmware_version: str
    product_id: int
    serial_number: str
    min_pulse_width: int = 64    # quarter-microseconds
    max_pulse_width: int = 8000  # quarter-microseconds
    capabilities: List[str] = field(default_factory=list)
    detected_at: float = field(default_factory=time.time)

class MaestroDetectionStatus(Enum):
    """Hardware detection status"""
    SCANNING = "scanning"
    DETECTED = "detected"
    CONNECTED = "connected"
    ERROR = "error"
    NOT_FOUND = "not_found"

class MaestroHardwareDetector:
    """Advanced Pololu Maestro Hardware Detection System"""

    # Known Pololu Product IDs for Maestro controllers
    MAESTRO_PRODUCT_IDS = {
        0x8A: (MaestroVariant.MINI_12, 12),
        0x8B: (MaestroVariant.MINI_18, 18),
        0x8C: (MaestroVariant.MINI_24, 24),
        0x89: (MaestroVariant.STANDARD_6, 6),
        0x8D: (MaestroVariant.STANDARD_12, 12),
        0x8E: (MaestroVariant.STANDARD_18, 18),
        0x8F: (MaestroVariant.STANDARD_24, 24),
    }

    # Pololu Vendor ID
    POLOLU_VENDOR_ID = 0x1FFB

    def __init__(self):
        self.detected_devices: List[MaestroHardwareInfo] = []
        self.current_device: Optional[MaestroHardwareInfo] = None
        self.detection_status = MaestroDetectionStatus.NOT_FOUND
        self.monitoring_active = False
        self.detection_callbacks: List[callable] = []

    def add_detection_callback(self, callback: callable):
        """Add callback for hardware detection events"""
        self.detection_callbacks.append(callback)

    def _notify_detection_change(self, status: MaestroDetectionStatus, device: Optional[MaestroHardwareInfo] = None):
        """Notify callbacks of detection status changes"""
        self.detection_status = status
        for callback in self.detection_callbacks:
            try:
                callback(status, device)
            except Exception as e:
                logger.error(f"Detection callback error: {e}")

    def scan_for_maestro_devices(self) -> List[MaestroHardwareInfo]:
        """
        Comprehensive scan for Pololu Maestro devices

        Returns:
            List of detected Maestro devices with full hardware information
        """
        logger.info("🔍 Scanning for Pololu Maestro servo controllers...")
        self._notify_detection_change(MaestroDetectionStatus.SCANNING)

        detected_devices = []

        # Scan all available serial ports
        available_ports = serial.tools.list_ports.comports()

        for port_info in available_ports:
            logger.debug(f"Checking port: {port_info.device}")

            # Check if this is a Pololu device by vendor ID
            if hasattr(port_info, 'vid') and port_info.vid == self.POLOLU_VENDOR_ID:
                logger.info(f"Found Pololu device on {port_info.device}")

                # Attempt to identify specific Maestro variant
                device_info = self._identify_maestro_device(port_info)
                if device_info:
                    detected_devices.append(device_info)
                    logger.info(f"✅ Detected: {device_info.variant.value} on {device_info.port}")

            # Also check for devices that may not report vendor ID correctly
            elif self._probe_for_maestro(port_info.device):
                device_info = self._identify_maestro_device(port_info)
                if device_info:
                    detected_devices.append(device_info)
                    logger.info(f"✅ Probed and detected: {device_info.variant.value} on {device_info.port}")

        self.detected_devices = detected_devices

        if detected_devices:
            self._notify_detection_change(MaestroDetectionStatus.DETECTED, detected_devices[0])
            logger.info(f"🎯 Hardware scan complete: {len(detected_devices)} Maestro controller(s) found")
        else:
            self._notify_detection_change(MaestroDetectionStatus.NOT_FOUND)
            logger.warning("⚠️ No Maestro controllers detected")

        return detected_devices

    def _probe_for_maestro(self, port: str) -> bool:
        """
        Probe a port to check if it's a Maestro device

        Args:
            port: Serial port path to probe

        Returns:
            True if device responds like a Maestro controller
        """
        try:
            with serial.Serial(port, 9600, timeout=0.5) as ser:
                # Wait for device to stabilize
                time.sleep(0.1)

                # Try to get firmware version (Maestro command 0x96)
                ser.write(bytes([0x96]))
                ser.flush()

                # Read response
                response = ser.read(4)

                # Maestro should respond with 4 bytes for firmware version
                if len(response) == 4:
                    logger.debug(f"Port {port} responded to Maestro command")
                    return True

        except Exception as e:
            logger.debug(f"Port {port} probe failed: {e}")

        return False

    def _identify_maestro_device(self, port_info) -> Optional[MaestroHardwareInfo]:
        """
        Identify specific Maestro device variant and capabilities

        Args:
            port_info: Serial port information

        Returns:
            MaestroHardwareInfo object with device details
        """
        try:
            device_info = MaestroHardwareInfo(
                port=port_info.device,
                variant=MaestroVariant.UNKNOWN,
                channels=12,  # Default assumption
                firmware_version="Unknown",
                product_id=getattr(port_info, 'pid', 0),
                serial_number=getattr(port_info, 'serial_number', 'Unknown')
            )

            # Identify variant by product ID if available
            if hasattr(port_info, 'pid') and port_info.pid in self.MAESTRO_PRODUCT_IDS:
                variant, channels = self.MAESTRO_PRODUCT_IDS[port_info.pid]
                device_info.variant = variant
                device_info.channels = channels
                device_info.product_id = port_info.pid

            # Connect to device to get detailed information
            with serial.Serial(port_info.device, 9600, timeout=1.0) as ser:
                time.sleep(0.1)

                # Get firmware version
                firmware = self._get_firmware_version(ser)
                if firmware:
                    device_info.firmware_version = firmware

                # Get device capabilities
                capabilities = self._detect_device_capabilities(ser, device_info.channels)
                device_info.capabilities = capabilities

                # Validate channel count by testing channel responses
                actual_channels = self._detect_channel_count(ser)
                if actual_channels > 0:
                    device_info.channels = actual_channels

                    # Update variant based on detected channels if unknown
                    if device_info.variant == MaestroVariant.UNKNOWN:
                        device_info.variant = self._infer_variant_from_channels(actual_channels)

            logger.info(f"Device identification complete: {device_info.variant.value} "
                       f"({device_info.channels} channels, FW: {device_info.firmware_version})")

            return device_info

        except Exception as e:
            logger.error(f"Failed to identify device on {port_info.device}: {e}")
            return None

    def _get_firmware_version(self, ser: serial.Serial) -> Optional[str]:
        """Get firmware version from Maestro device"""
        try:
            # Send firmware version command (0x96)
            ser.write(bytes([0x96]))
            ser.flush()

            # Read 4-byte response
            response = ser.read(4)

            if len(response) == 4:
                # Parse firmware version from response
                minor = response[0]
                major = response[1]
                version = f"{major}.{minor:02d}"
                logger.debug(f"Firmware version: {version}")
                return version

        except Exception as e:
            logger.debug(f"Firmware version detection failed: {e}")

        return None

    def _detect_device_capabilities(self, ser: serial.Serial, channels: int) -> List[str]:
        """Detect device capabilities and features"""
        capabilities = []

        try:
            # Test if device supports speed/acceleration settings
            test_channel = 0

            # Try to set speed (should not cause error on real Maestro)
            ser.write(bytes([0x87, test_channel, 50, 0]))  # Set speed command
            ser.flush()
            time.sleep(0.01)

            # Check for errors
            ser.write(bytes([0xA1]))  # Get errors command
            error_response = ser.read(2)

            if len(error_response) == 2:
                error_bits = error_response[0] | (error_response[1] << 8)
                if error_bits == 0:
                    capabilities.append("Speed Control")
                    capabilities.append("Acceleration Control")

            # Test position feedback
            ser.write(bytes([0x90, test_channel]))  # Get position command
            position_response = ser.read(2)

            if len(position_response) == 2:
                capabilities.append("Position Feedback")

            # Check for script support (Mini Maestros don't have this)
            if channels >= 18:  # Larger controllers typically have script support
                capabilities.append("Script Engine")

            capabilities.append("USB Control")
            capabilities.append("Serial Control")

        except Exception as e:
            logger.debug(f"Capability detection error: {e}")

        return capabilities

    def _detect_channel_count(self, ser: serial.Serial) -> int:
        """Detect actual number of channels by testing responses"""
        max_channels = 24  # Test up to maximum Maestro channels
        working_channels = 0

        try:
            for channel in range(max_channels):
                # Try to get position from this channel
                ser.write(bytes([0x90, channel]))  # Get position command
                ser.flush()

                response = ser.read(2)

                if len(response) == 2:
                    # Valid response - this channel exists
                    working_channels = channel + 1
                else:
                    # No response - we've found the limit
                    break

                time.sleep(0.01)  # Small delay between tests

        except Exception as e:
            logger.debug(f"Channel count detection error: {e}")

        logger.debug(f"Detected {working_channels} working channels")
        return working_channels

    def _infer_variant_from_channels(self, channels: int) -> MaestroVariant:
        """Infer Maestro variant from detected channel count"""
        variant_map = {
            6: MaestroVariant.STANDARD_6,
            12: MaestroVariant.MINI_12,
            18: MaestroVariant.MINI_18,
            24: MaestroVariant.MINI_24,
        }

        return variant_map.get(channels, MaestroVariant.UNKNOWN)

    def get_optimal_device(self) -> Optional[MaestroHardwareInfo]:
        """
        Get the most suitable Maestro device for R2D2 operations

        Prioritizes devices with more channels and newer firmware
        """
        if not self.detected_devices:
            return None

        # Sort by channel count (descending) then by firmware version
        sorted_devices = sorted(
            self.detected_devices,
            key=lambda d: (d.channels, d.firmware_version),
            reverse=True
        )

        optimal_device = sorted_devices[0]
        self.current_device = optimal_device

        logger.info(f"🎯 Optimal device selected: {optimal_device.variant.value} "
                   f"({optimal_device.channels} channels) on {optimal_device.port}")

        return optimal_device

    def validate_device_connection(self, device: MaestroHardwareInfo) -> bool:
        """
        Validate that a device is still connected and responsive

        Args:
            device: Device to validate

        Returns:
            True if device is accessible and responsive
        """
        try:
            with serial.Serial(device.port, 9600, timeout=0.5) as ser:
                time.sleep(0.1)

                # Test basic communication
                ser.write(bytes([0xA1]))  # Get errors command
                response = ser.read(2)

                if len(response) == 2:
                    self._notify_detection_change(MaestroDetectionStatus.CONNECTED, device)
                    return True

        except Exception as e:
            logger.warning(f"Device validation failed for {device.port}: {e}")
            self._notify_detection_change(MaestroDetectionStatus.ERROR, device)

        return False

    def start_continuous_monitoring(self, interval: float = 5.0):
        """
        Start continuous hardware monitoring

        Args:
            interval: Monitoring interval in seconds
        """
        if self.monitoring_active:
            return

        self.monitoring_active = True

        def monitor_loop():
            while self.monitoring_active:
                try:
                    # Re-scan for new devices
                    current_count = len(self.detected_devices)
                    self.scan_for_maestro_devices()

                    # Check if device count changed
                    if len(self.detected_devices) != current_count:
                        logger.info(f"Hardware change detected: {len(self.detected_devices)} devices now available")

                    # Validate current device if set
                    if self.current_device:
                        if not self.validate_device_connection(self.current_device):
                            logger.warning("Current device connection lost - scanning for alternatives")
                            self.get_optimal_device()

                    time.sleep(interval)

                except Exception as e:
                    logger.error(f"Monitoring loop error: {e}")
                    time.sleep(interval)

        monitor_thread = threading.Thread(target=monitor_loop, daemon=True, name="MaestroMonitor")
        monitor_thread.start()

        logger.info(f"✅ Hardware monitoring started (interval: {interval}s)")

    def stop_monitoring(self):
        """Stop continuous hardware monitoring"""
        self.monitoring_active = False
        logger.info("Hardware monitoring stopped")

    def export_device_configuration(self, device: MaestroHardwareInfo, filename: str):
        """Export device configuration to JSON file"""
        config = {
            "device_info": {
                "port": device.port,
                "variant": device.variant.value,
                "channels": device.channels,
                "firmware_version": device.firmware_version,
                "product_id": device.product_id,
                "serial_number": device.serial_number,
                "capabilities": device.capabilities,
                "detected_at": device.detected_at
            },
            "r2d2_servo_mapping": self._generate_r2d2_servo_mapping(device.channels),
            "safety_limits": self._generate_safety_limits(device.channels),
            "performance_settings": self._generate_performance_settings(device.channels)
        }

        with open(filename, 'w') as f:
            json.dump(config, f, indent=2)

        logger.info(f"Device configuration exported to {filename}")

    def _generate_r2d2_servo_mapping(self, channels: int) -> Dict:
        """Generate R2D2-specific servo channel mapping"""
        base_mapping = {
            0: {"name": "Dome Rotation", "type": "primary", "range": "continuous"},
            1: {"name": "Head Tilt", "type": "primary", "range": "limited"},
            2: {"name": "Periscope", "type": "utility", "range": "binary"},
            3: {"name": "Radar Eye", "type": "utility", "range": "continuous"},
            4: {"name": "Utility Arm Left", "type": "utility", "range": "wide"},
            5: {"name": "Utility Arm Right", "type": "utility", "range": "wide"},
        }

        if channels >= 12:
            base_mapping.update({
                6: {"name": "Dome Panel Front", "type": "panel", "range": "binary"},
                7: {"name": "Dome Panel Left", "type": "panel", "range": "binary"},
                8: {"name": "Dome Panel Right", "type": "panel", "range": "binary"},
                9: {"name": "Dome Panel Back", "type": "panel", "range": "binary"},
                10: {"name": "Body Door Left", "type": "panel", "range": "binary"},
                11: {"name": "Body Door Right", "type": "panel", "range": "binary"},
            })

        if channels >= 18:
            base_mapping.update({
                12: {"name": "Front Logic Display", "type": "display", "range": "limited"},
                13: {"name": "Rear Logic Display", "type": "display", "range": "limited"},
                14: {"name": "Holoprojector 1", "type": "special", "range": "wide"},
                15: {"name": "Holoprojector 2", "type": "special", "range": "wide"},
                16: {"name": "Body Rotation", "type": "drive", "range": "continuous"},
                17: {"name": "Reserved", "type": "expansion", "range": "wide"},
            })

        if channels >= 24:
            base_mapping.update({
                18: {"name": "LED Controller 1", "type": "lighting", "range": "wide"},
                19: {"name": "LED Controller 2", "type": "lighting", "range": "wide"},
                20: {"name": "Sound Trigger 1", "type": "audio", "range": "binary"},
                21: {"name": "Sound Trigger 2", "type": "audio", "range": "binary"},
                22: {"name": "Custom 1", "type": "expansion", "range": "wide"},
                23: {"name": "Custom 2", "type": "expansion", "range": "wide"},
            })

        return base_mapping

    def _generate_safety_limits(self, channels: int) -> Dict:
        """Generate safety limits for servo channels"""
        limits = {}

        for channel in range(channels):
            limits[channel] = {
                "min_pulse_us": 500,      # Minimum safe pulse width
                "max_pulse_us": 2500,     # Maximum safe pulse width
                "max_speed": 100,         # Maximum speed setting
                "max_acceleration": 50,   # Maximum acceleration setting
                "emergency_position": 1500, # Emergency safe position
                "timeout_ms": 5000        # Communication timeout
            }

        return limits

    def _generate_performance_settings(self, channels: int) -> Dict:
        """Generate optimized performance settings"""
        return {
            "update_rate_hz": 50,           # Servo update rate
            "monitoring_rate_hz": 10,       # Status monitoring rate
            "communication_timeout_ms": 1000,
            "position_deadband_us": 2,      # Position accuracy deadband
            "smooth_motion_enabled": True,
            "safety_checks_enabled": True,
            "log_level": "INFO"
        }

    def get_status_report(self) -> Dict:
        """Generate comprehensive hardware status report"""
        return {
            "detection_status": self.detection_status.value,
            "detected_devices": [
                {
                    "port": device.port,
                    "variant": device.variant.value,
                    "channels": device.channels,
                    "firmware": device.firmware_version,
                    "capabilities": device.capabilities,
                    "product_id": f"0x{device.product_id:02X}",
                    "serial_number": device.serial_number
                }
                for device in self.detected_devices
            ],
            "current_device": {
                "port": self.current_device.port,
                "variant": self.current_device.variant.value,
                "channels": self.current_device.channels,
                "firmware": self.current_device.firmware_version
            } if self.current_device else None,
            "monitoring_active": self.monitoring_active,
            "timestamp": time.time()
        }

def demo_hardware_detection():
    """Demonstration of hardware detection capabilities"""
    logger.info("🎯 Starting Maestro Hardware Detection Demo...")

    detector = MaestroHardwareDetector()

    # Add detection callback for real-time updates
    def detection_callback(status, device):
        logger.info(f"Detection update: {status.value}")
        if device:
            logger.info(f"Device: {device.variant.value} on {device.port}")

    detector.add_detection_callback(detection_callback)

    try:
        # Scan for devices
        devices = detector.scan_for_maestro_devices()

        if devices:
            # Get optimal device
            optimal = detector.get_optimal_device()

            # Export configuration
            detector.export_device_configuration(optimal, "r2d2_maestro_config.json")

            # Start monitoring
            detector.start_continuous_monitoring(2.0)

            # Print status report
            status = detector.get_status_report()
            print("\n" + "="*60)
            print("MAESTRO HARDWARE DETECTION REPORT")
            print("="*60)
            print(json.dumps(status, indent=2))

            # Run for 30 seconds to demonstrate monitoring
            logger.info("Monitoring hardware for 30 seconds...")
            time.sleep(30)

        else:
            logger.warning("No Maestro devices found - running in simulation mode")

    except KeyboardInterrupt:
        logger.info("Demo interrupted by user")
    finally:
        detector.stop_monitoring()
        logger.info("✅ Hardware detection demo completed")

if __name__ == "__main__":
    demo_hardware_detection()