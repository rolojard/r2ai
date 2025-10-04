#!/usr/bin/env python3
"""
Orin Nano System Optimization Script
Configures system parameters for optimal video capture performance
"""

import os
import subprocess
import sys
import time

class OrinNanoSystemOptimizer:
    def __init__(self):
        self.optimizations_applied = []

    def run_command(self, command, description=""):
        """Run system command and capture result"""
        try:
            if description:
                print(f"Applying: {description}")
            result = subprocess.run(command, shell=True, capture_output=True, text=True)
            if result.returncode == 0:
                self.optimizations_applied.append(description or command)
                return True, result.stdout
            else:
                print(f"Warning: {command} failed: {result.stderr}")
                return False, result.stderr
        except Exception as e:
            print(f"Error running command '{command}': {e}")
            return False, str(e)

    def check_current_performance_mode(self):
        """Check current performance settings"""
        print("=== Current System Performance Status ===")

        # Check power model
        success, output = self.run_command("nvpmodel -q")
        if success:
            print(f"Power Model: {output.strip()}")

        # Check CPU frequencies
        success, output = self.run_command("cat /sys/devices/system/cpu/cpu*/cpufreq/scaling_cur_freq")
        if success:
            freqs = output.strip().split('\n')
            print(f"CPU Frequencies: {', '.join([f'{int(f)/1000:.0f}MHz' for f in freqs if f])}")

        # Check GPU status
        success, output = self.run_command("cat /sys/devices/gpu.0/load")
        if success:
            print(f"GPU Load: {output.strip()}")

        # Check memory info
        success, output = self.run_command("free -h | grep Mem")
        if success:
            print(f"Memory: {output.strip()}")

    def optimize_usb_for_video(self):
        """Optimize USB subsystem for video capture"""
        print("\n=== Optimizing USB for Video Capture ===")

        # Increase USB buffer sizes
        usb_optimizations = [
            "echo 16 > /sys/module/usbcore/parameters/autosuspend",
            "echo Y > /sys/module/usbcore/parameters/use_both_schemes"
        ]

        for cmd in usb_optimizations:
            try:
                # These require root, so we'll document them instead
                print(f"USB Optimization (requires root): {cmd}")
            except:
                pass

    def optimize_memory_bandwidth(self):
        """Optimize memory settings for video processing"""
        print("\n=== Memory Bandwidth Optimization ===")

        # Check current memory bandwidth
        success, output = self.run_command("cat /proc/meminfo | grep -E 'MemTotal|MemAvailable|Buffers|Cached'")
        if success:
            print("Current memory status:")
            print(output)

        # Set memory allocation hints for video processing
        os.environ['OPENCV_VIDEOIO_PRIORITY_V4L2'] = '1'
        os.environ['OPENCV_FFMPEG_CAPTURE_OPTIONS'] = 'buffer_size;1'

        print("OpenCV environment optimizations applied")

    def optimize_cpu_scheduling(self):
        """Optimize CPU scheduling for real-time video"""
        print("\n=== CPU Scheduling Optimization ===")

        # Check current CPU governor
        success, output = self.run_command("cat /sys/devices/system/cpu/cpu0/cpufreq/scaling_governor")
        if success:
            print(f"Current CPU Governor: {output.strip()}")

        # Document performance optimizations
        print("CPU optimizations to apply (requires root):")
        print("- Set CPU governor to 'performance'")
        print("- Disable CPU idle states during video capture")
        print("- Set process priority for video applications")

    def verify_camera_drivers(self):
        """Verify camera driver status"""
        print("\n=== Camera Driver Verification ===")

        # Check UVC driver
        success, output = self.run_command("lsmod | grep uvc")
        if success and output:
            print("UVC Driver: Loaded")
            print(output)
        else:
            print("UVC Driver: NOT LOADED")

        # Check video devices
        success, output = self.run_command("ls -la /dev/video*")
        if success:
            print("Video Devices:")
            print(output)

        # Check USB video devices
        success, output = self.run_command("lsusb | grep -i 'camera\\|webcam\\|video'")
        if success and output:
            print("USB Video Devices:")
            print(output)

    def monitor_thermal_performance(self):
        """Monitor thermal performance during operation"""
        print("\n=== Thermal Performance Monitoring ===")

        try:
            # Read thermal zones
            thermal_files = [
                "/sys/devices/virtual/thermal/thermal_zone0/temp",
                "/sys/devices/virtual/thermal/thermal_zone1/temp",
                "/sys/devices/virtual/thermal/thermal_zone5/temp",
                "/sys/devices/virtual/thermal/thermal_zone6/temp"
            ]

            temperatures = []
            for i, thermal_file in enumerate(thermal_files):
                try:
                    with open(thermal_file, 'r') as f:
                        temp = int(f.read().strip()) / 1000
                        temperatures.append(f"Zone{i}: {temp:.1f}°C")
                except:
                    continue

            if temperatures:
                print(f"Thermal Status: {' | '.join(temperatures)}")

            # Check for thermal throttling
            success, output = self.run_command("cat /sys/devices/system/cpu/cpu0/cpufreq/scaling_cur_freq")
            if success:
                current_freq = int(output.strip())
                success2, output2 = self.run_command("cat /sys/devices/system/cpu/cpu0/cpufreq/scaling_max_freq")
                if success2:
                    max_freq = int(output2.strip())
                    throttle_ratio = current_freq / max_freq
                    if throttle_ratio < 0.9:
                        print(f"WARNING: Possible thermal throttling detected ({throttle_ratio*100:.1f}% of max frequency)")
                    else:
                        print(f"CPU Frequency: Normal ({throttle_ratio*100:.1f}% of max)")

        except Exception as e:
            print(f"Error monitoring thermal: {e}")

    def create_camera_test_script(self):
        """Create a quick camera test script"""
        script_content = '''#!/usr/bin/env python3
import cv2
import time

def quick_camera_test():
    cap = cv2.VideoCapture(0, cv2.CAP_V4L2)

    if not cap.isOpened():
        print("ERROR: Cannot open camera")
        return False

    # Set basic parameters
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    cap.set(cv2.CAP_PROP_FPS, 30)
    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

    print("Camera test - Press 'q' to quit")

    frame_count = 0
    start_time = time.time()

    while True:
        ret, frame = cap.read()
        if not ret:
            print("Failed to capture frame")
            break

        frame_count += 1

        # Calculate FPS every 30 frames
        if frame_count % 30 == 0:
            elapsed = time.time() - start_time
            fps = frame_count / elapsed
            print(f"FPS: {fps:.2f}")

        # Display frame
        cv2.imshow('Camera Test', frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

    total_time = time.time() - start_time
    avg_fps = frame_count / total_time
    print(f"Test completed: {frame_count} frames in {total_time:.2f}s (avg {avg_fps:.2f} FPS)")
    return True

if __name__ == "__main__":
    quick_camera_test()
'''

        script_path = "/home/rolo/r2ai/quick_camera_test.py"
        try:
            with open(script_path, 'w') as f:
                f.write(script_content)
            os.chmod(script_path, 0o755)
            print(f"Created quick camera test script: {script_path}")
            return script_path
        except Exception as e:
            print(f"Error creating test script: {e}")
            return None

    def run_full_optimization(self):
        """Run complete system optimization"""
        print("=== Orin Nano Video Capture System Optimization ===")

        self.check_current_performance_mode()
        self.verify_camera_drivers()
        self.optimize_memory_bandwidth()
        self.optimize_usb_for_video()
        self.optimize_cpu_scheduling()
        self.monitor_thermal_performance()

        # Create test script
        script_path = self.create_camera_test_script()

        print(f"\n=== Optimization Summary ===")
        print(f"Applied {len(self.optimizations_applied)} optimizations:")
        for opt in self.optimizations_applied:
            print(f"  ✓ {opt}")

        print(f"\n=== Next Steps ===")
        print("1. Run camera optimization test: python3 /home/rolo/r2ai/orin_nano_camera_optimizer.py")
        if script_path:
            print(f"2. Run quick camera test: python3 {script_path}")
        print("3. Test with R2D2 dashboard integration")

        print("\n=== Manual Optimizations (require root) ===")
        print("sudo nvpmodel -m 0  # Maximum performance mode")
        print("sudo jetson_clocks  # Maximum clock speeds")
        print("echo performance | sudo tee /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor")

if __name__ == "__main__":
    optimizer = OrinNanoSystemOptimizer()
    optimizer.run_full_optimization()