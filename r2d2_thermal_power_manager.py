#!/usr/bin/env python3
"""
R2-D2 Thermal and Power Management for Orin Nano
Optimizes thermal and power settings for sustained convention operation
"""

import os
import time
import threading
import subprocess
import json
from datetime import datetime
import psutil

class R2D2ThermalPowerManager:
    def __init__(self):
        self.monitoring = False
        self.thermal_zones = []
        self.power_readings = []
        self.thermal_history = []
        self.power_history = []
        self.alert_threshold = 70.0  # °C
        self.critical_threshold = 80.0  # °C
        self.performance_mode = "balanced"

    def discover_thermal_zones(self):
        """Discover available thermal zones"""
        print("=== Discovering Thermal Zones ===")
        self.thermal_zones = []

        for i in range(10):  # Check up to 10 thermal zones
            temp_file = f"/sys/devices/virtual/thermal/thermal_zone{i}/temp"
            type_file = f"/sys/devices/virtual/thermal/thermal_zone{i}/type"

            try:
                if os.path.exists(temp_file) and os.path.exists(type_file):
                    with open(type_file, 'r') as f:
                        zone_type = f.read().strip()

                    with open(temp_file, 'r') as f:
                        temp_data = f.read()
                        if temp_data and temp_data.strip():
                            temp_raw = int(temp_data.strip())
                            temp_celsius = temp_raw / 1000.0
                        else:
                            continue  # Skip this zone

                    self.thermal_zones.append({
                        'id': i,
                        'type': zone_type,
                        'temp_file': temp_file,
                        'temperature': temp_celsius
                    })

                    print(f"✓ Zone {i}: {zone_type} - {temp_celsius:.1f}°C")

            except (FileNotFoundError, ValueError, PermissionError) as e:
                # Skip zones that can't be read
                continue

        print(f"✓ Found {len(self.thermal_zones)} thermal zones")
        return len(self.thermal_zones) > 0

    def get_thermal_readings(self):
        """Get current thermal readings"""
        readings = {}
        max_temp = 0.0

        for zone in self.thermal_zones:
            try:
                with open(zone['temp_file'], 'r') as f:
                    temp_data = f.read()
                    if temp_data and temp_data.strip():
                        temp_raw = int(temp_data.strip())
                        temp_celsius = temp_raw / 1000.0
                        readings[zone['type']] = temp_celsius
                        max_temp = max(max_temp, temp_celsius)
                    else:
                        readings[zone['type']] = None
            except Exception as e:
                readings[zone['type']] = None

        return readings, max_temp

    def get_power_readings(self):
        """Get power consumption readings"""
        power_info = {}

        # Check various power monitoring files
        power_files = [
            ("/sys/bus/i2c/drivers/ina3221x/1-0040/iio:device0/in_power0_input", "VDD_IN"),
            ("/sys/bus/i2c/drivers/ina3221x/1-0040/iio:device0/in_power1_input", "VDD_CPU_GPU_CV"),
            ("/sys/bus/i2c/drivers/ina3221x/1-0040/iio:device0/in_power2_input", "VDD_SOC"),
            ("/sys/bus/i2c/drivers/ina3221x/1-0041/iio:device1/in_power0_input", "VDD_SYS_5V"),
        ]

        total_power = 0.0

        for file_path, name in power_files:
            try:
                if os.path.exists(file_path):
                    with open(file_path, 'r') as f:
                        power_mw = int(f.read().strip())
                        power_w = power_mw / 1000.0
                        power_info[name] = power_w
                        total_power += power_w
            except:
                power_info[name] = None

        # Add system-level power info
        power_info['total_estimated'] = total_power
        power_info['cpu_percent'] = psutil.cpu_percent(interval=None)
        power_info['memory_percent'] = psutil.virtual_memory().percent

        return power_info

    def check_power_model(self):
        """Check and optimize power model"""
        print("\n=== Power Model Configuration ===")

        try:
            # Check current power model
            result = subprocess.run(['nvpmodel', '-q'],
                                  capture_output=True, text=True, timeout=10)

            if result.returncode == 0:
                output = result.stdout.strip()
                print(f"Current power model: {output}")

                # Extract power mode number
                if "MAXN_SUPER" in output:
                    print("✓ Already in maximum performance mode")
                    self.performance_mode = "maximum"
                elif "15W" in output:
                    print("⚠ In 15W mode - consider MAXN for better performance")
                    self.performance_mode = "balanced"
                elif "10W" in output:
                    print("⚠ In 10W mode - limited performance")
                    self.performance_mode = "power_save"

            else:
                print(f"✗ Could not check power model: {result.stderr}")

        except Exception as e:
            print(f"✗ Power model check failed: {e}")

    def optimize_cpu_governor(self):
        """Optimize CPU governor settings"""
        print("\n=== CPU Governor Optimization ===")

        try:
            # Check current governors
            governors = []
            for cpu in range(6):  # Orin Nano has 6 cores
                gov_file = f"/sys/devices/system/cpu/cpu{cpu}/cpufreq/scaling_governor"
                try:
                    with open(gov_file, 'r') as f:
                        governor = f.read().strip()
                        governors.append(governor)
                except:
                    governors.append("unknown")

            print(f"Current governors: {set(governors)}")

            # Try to get available governors
            try:
                with open("/sys/devices/system/cpu/cpu0/cpufreq/scaling_available_governors", 'r') as f:
                    available = f.read().strip().split()
                    print(f"Available governors: {available}")

                    if 'performance' in available:
                        print("📈 Performance governor available for R2-D2 high performance")
                    if 'schedutil' in available:
                        print("⚖️ Schedutil governor available for balanced performance")

            except:
                print("⚠ Could not read available governors")

        except Exception as e:
            print(f"✗ CPU governor check failed: {e}")

    def create_thermal_monitor(self):
        """Create thermal monitoring system"""
        print("\n=== Starting Thermal Monitor ===")

        def thermal_monitor_thread():
            """Background thermal monitoring"""
            alert_count = 0
            last_alert = 0

            while self.monitoring:
                try:
                    thermal_readings, max_temp = self.get_thermal_readings()
                    power_readings = self.get_power_readings()

                    # Record readings
                    timestamp = time.time()
                    self.thermal_history.append({
                        'timestamp': timestamp,
                        'max_temp': max_temp,
                        'readings': thermal_readings
                    })

                    self.power_history.append({
                        'timestamp': timestamp,
                        'readings': power_readings
                    })

                    # Keep only last 300 readings (5 minutes at 1 second intervals)
                    if len(self.thermal_history) > 300:
                        self.thermal_history.pop(0)
                    if len(self.power_history) > 300:
                        self.power_history.pop(0)

                    # Check for thermal alerts
                    current_time = time.time()
                    if max_temp > self.alert_threshold and (current_time - last_alert) > 30:
                        alert_count += 1
                        last_alert = current_time

                        if max_temp > self.critical_threshold:
                            print(f"🚨 CRITICAL THERMAL ALERT: {max_temp:.1f}°C")
                            print("   R2-D2 performance may be throttled")
                        else:
                            print(f"⚠️ Thermal warning: {max_temp:.1f}°C")

                    time.sleep(1)  # Monitor every second

                except Exception as e:
                    print(f"Thermal monitor error: {e}")
                    time.sleep(5)

        self.monitor_thread = threading.Thread(target=thermal_monitor_thread, daemon=True)
        self.monitor_thread.start()
        print("✓ Thermal monitor started")

    def start_monitoring(self):
        """Start comprehensive monitoring"""
        if not self.discover_thermal_zones():
            print("⚠ No thermal zones found, monitoring limited")

        self.check_power_model()
        self.optimize_cpu_governor()

        self.monitoring = True
        self.create_thermal_monitor()

    def stop_monitoring(self):
        """Stop monitoring"""
        self.monitoring = False
        if hasattr(self, 'monitor_thread'):
            self.monitor_thread.join(timeout=2)

    def get_status_report(self):
        """Generate current status report"""
        thermal_readings, max_temp = self.get_thermal_readings()
        power_readings = self.get_power_readings()

        report = {
            'timestamp': datetime.now().isoformat(),
            'thermal': {
                'max_temperature': max_temp,
                'readings': thermal_readings,
                'status': 'normal' if max_temp < self.alert_threshold else
                         'warning' if max_temp < self.critical_threshold else 'critical'
            },
            'power': power_readings,
            'performance_mode': self.performance_mode,
            'uptime_minutes': len(self.thermal_history) / 60.0
        }

        return report

    def run_thermal_stress_test(self, duration=60):
        """Run thermal stress test for R2-D2 convention scenario"""
        print(f"\n=== Running {duration}s Thermal Stress Test ===")
        print("Simulating R2-D2 convention load...")

        start_time = time.time()
        start_temp = self.get_thermal_readings()[1]

        print(f"Starting temperature: {start_temp:.1f}°C")

        # Import here to avoid dependency issues
        try:
            import torch
            import numpy as np

            # Simulate R2-D2 workload
            device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

            def simulate_vision_load():
                """Simulate computer vision load"""
                if torch.cuda.is_available():
                    for _ in range(10):
                        x = torch.randn(1, 3, 640, 480, device=device)
                        y = torch.nn.functional.conv2d(x, torch.randn(32, 3, 3, 3, device=device))
                        torch.cuda.synchronize()

            def simulate_servo_calculations():
                """Simulate servo control calculations"""
                positions = np.random.random(24) * 180  # 24 servos
                for _ in range(1000):
                    # Simulate kinematics calculations
                    angles = np.sin(positions * np.pi / 180)
                    torques = angles * np.random.random(24)

            # Run stress test
            test_iterations = 0
            while time.time() - start_time < duration:
                simulate_vision_load()
                simulate_servo_calculations()
                test_iterations += 1

                # Report every 10 seconds
                elapsed = time.time() - start_time
                if int(elapsed) % 10 == 0 and int(elapsed) > int(elapsed - 1):
                    current_temp = self.get_thermal_readings()[1]
                    power_info = self.get_power_readings()
                    total_power = power_info.get('total_estimated', 0)

                    print(f"  {int(elapsed)}s: {current_temp:.1f}°C, "
                          f"{total_power:.1f}W, {test_iterations} iterations")

        except ImportError:
            print("PyTorch not available, running CPU-only stress test")
            # CPU-only stress test
            while time.time() - start_time < duration:
                for _ in range(10000):
                    _ = sum(range(1000))

        end_temp = self.get_thermal_readings()[1]
        end_time = time.time()

        temp_rise = end_temp - start_temp
        avg_power = sum(reading['readings'].get('total_estimated', 0)
                       for reading in self.power_history[-60:]) / len(self.power_history[-60:])

        print(f"\n✓ Stress test completed:")
        print(f"  Duration: {end_time - start_time:.1f}s")
        print(f"  Temperature rise: {temp_rise:.1f}°C")
        print(f"  Final temperature: {end_temp:.1f}°C")
        print(f"  Average power: {avg_power:.1f}W")
        print(f"  Thermal status: {'PASS' if end_temp < self.alert_threshold else 'WARNING'}")

        return {
            'duration': end_time - start_time,
            'start_temp': start_temp,
            'end_temp': end_temp,
            'temp_rise': temp_rise,
            'avg_power': avg_power,
            'status': 'pass' if end_temp < self.alert_threshold else 'warning'
        }

def main():
    print("R2-D2 Thermal and Power Management")
    print("=" * 40)

    manager = R2D2ThermalPowerManager()

    # Start monitoring
    manager.start_monitoring()

    try:
        # Let monitoring run for a few seconds
        time.sleep(3)

        # Generate initial report
        report = manager.get_status_report()
        print(f"\n=== Initial Status Report ===")
        print(f"Max Temperature: {report['thermal']['max_temperature']:.1f}°C")
        print(f"Thermal Status: {report['thermal']['status']}")
        print(f"CPU Usage: {report['power']['cpu_percent']:.1f}%")
        print(f"Memory Usage: {report['power']['memory_percent']:.1f}%")

        if report['power']['total_estimated'] > 0:
            print(f"Total Power: {report['power']['total_estimated']:.1f}W")

        # Run stress test
        stress_results = manager.run_thermal_stress_test(30)

        # Final report
        final_report = manager.get_status_report()
        print(f"\n=== Final Optimization Report ===")
        print(f"📊 THERMAL PERFORMANCE:")
        print(f"  Peak temperature: {final_report['thermal']['max_temperature']:.1f}°C")
        print(f"  Thermal headroom: {70 - final_report['thermal']['max_temperature']:.1f}°C")
        print(f"  R2-D2 ready: {'Yes' if final_report['thermal']['max_temperature'] < 65 else 'Monitor closely'}")

        print(f"\n⚡ POWER EFFICIENCY:")
        print(f"  CPU utilization: {final_report['power']['cpu_percent']:.1f}%")
        print(f"  Memory utilization: {final_report['power']['memory_percent']:.1f}%")
        print(f"  Power mode: {final_report['performance_mode']}")

        print(f"\n🎯 CONVENTION READINESS:")
        if stress_results['status'] == 'pass':
            print("  ✅ Thermal performance suitable for extended operation")
            print("  ✅ Can handle sustained R2-D2 workload")
        else:
            print("  ⚠️ May need additional cooling for extended operation")
            print("  ⚠️ Monitor temperatures during convention use")

        print(f"\n📈 RECOMMENDATIONS:")
        print("  • Monitor temperatures during initial convention runs")
        print("  • Ensure adequate ventilation around Orin Nano")
        print("  • Consider fan cooling for extended operation")
        print("  • Test with full R2-D2 load before event")

    finally:
        manager.stop_monitoring()

if __name__ == "__main__":
    main()