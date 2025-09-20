#!/usr/bin/env python3
"""
R2-D2 Convention Load Test
Simulates extended convention operation with realistic workloads
"""

import time
import threading
import numpy as np
import os
import json
from datetime import datetime, timedelta

# Try to import dependencies
try:
    import torch
    import torch.nn as nn
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False

try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False

class R2D2ConventionLoadTest:
    def __init__(self):
        self.device = torch.device('cuda' if TORCH_AVAILABLE and torch.cuda.is_available() else 'cpu')
        self.running = False
        self.test_data = {
            'start_time': None,
            'thermal_log': [],
            'performance_log': [],
            'interaction_log': [],
            'system_alerts': []
        }

    def get_thermal_status(self):
        """Get current thermal status"""
        temps = {}
        try:
            with open("/sys/devices/virtual/thermal/thermal_zone0/temp", 'r') as f:
                temps['cpu'] = int(f.read().strip()) / 1000.0
        except:
            temps['cpu'] = None

        try:
            with open("/sys/devices/virtual/thermal/thermal_zone1/temp", 'r') as f:
                temps['gpu'] = int(f.read().strip()) / 1000.0
        except:
            temps['gpu'] = None

        return temps

    def get_system_status(self):
        """Get system performance status"""
        status = {}

        if PSUTIL_AVAILABLE:
            status['cpu_percent'] = psutil.cpu_percent(interval=None)
            memory = psutil.virtual_memory()
            status['memory_percent'] = memory.percent
            status['memory_available_gb'] = memory.available / (1024**3)
        else:
            status['cpu_percent'] = None
            status['memory_percent'] = None
            status['memory_available_gb'] = None

        if TORCH_AVAILABLE and torch.cuda.is_available():
            status['gpu_memory_mb'] = torch.cuda.memory_allocated() / 1024**2
            status['gpu_memory_cached_mb'] = torch.cuda.memory_reserved() / 1024**2
        else:
            status['gpu_memory_mb'] = None
            status['gpu_memory_cached_mb'] = None

        return status

    def simulate_convention_interaction(self, interaction_type, duration_minutes):
        """Simulate different types of convention interactions"""
        print(f"🎭 Simulating {interaction_type} interaction for {duration_minutes} minutes...")

        start_time = time.time()
        interaction_count = 0

        while time.time() - start_time < duration_minutes * 60 and self.running:
            loop_start = time.time()

            if interaction_type == "crowd_scanning":
                # High-intensity computer vision for crowd scanning
                self.simulate_intensive_vision_processing()
                # Frequent head movements
                self.simulate_head_servo_movements(frequency='high')
                # Occasional sound effects
                if np.random.random() < 0.1:  # 10% chance per loop
                    self.simulate_audio_playback("scanning_sound")

            elif interaction_type == "photo_session":
                # Moderate computer vision for face detection
                self.simulate_face_detection_processing()
                # Pose servo movements
                self.simulate_pose_servo_movements()
                # Frequent R2-D2 sounds
                if np.random.random() < 0.3:  # 30% chance per loop
                    self.simulate_audio_playback("beep_sequence")

            elif interaction_type == "demonstration":
                # Light computer vision for general awareness
                self.simulate_general_vision_processing()
                # Demonstration servo sequence
                self.simulate_demonstration_servos()
                # Narration audio
                if np.random.random() < 0.2:  # 20% chance per loop
                    self.simulate_audio_playback("narration")

            elif interaction_type == "idle_patrol":
                # Minimal computer vision
                self.simulate_minimal_vision_processing()
                # Gentle idle movements
                self.simulate_idle_servo_movements()
                # Occasional ambient sounds
                if np.random.random() < 0.05:  # 5% chance per loop
                    self.simulate_audio_playback("ambient_beep")

            interaction_count += 1

            # Log interaction
            self.test_data['interaction_log'].append({
                'timestamp': time.time(),
                'type': interaction_type,
                'iteration': interaction_count,
                'thermal': self.get_thermal_status(),
                'system': self.get_system_status()
            })

            # Interaction frequency based on type
            if interaction_type == "crowd_scanning":
                time.sleep(max(0, 0.1 - (time.time() - loop_start)))  # 10 Hz
            elif interaction_type == "photo_session":
                time.sleep(max(0, 0.2 - (time.time() - loop_start)))  # 5 Hz
            elif interaction_type == "demonstration":
                time.sleep(max(0, 0.5 - (time.time() - loop_start)))  # 2 Hz
            else:  # idle_patrol
                time.sleep(max(0, 1.0 - (time.time() - loop_start)))  # 1 Hz

        print(f"✓ {interaction_type}: {interaction_count} interactions completed")

    def simulate_intensive_vision_processing(self):
        """Simulate intensive computer vision for crowd scanning"""
        if not TORCH_AVAILABLE or not torch.cuda.is_available():
            # CPU fallback
            frame = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
            gray = np.mean(frame, axis=2)
            edges = np.gradient(gray)
            return

        # GPU processing
        frame_tensor = torch.randn(1, 3, 640, 480, device=self.device)
        conv_layer = torch.nn.Conv2d(3, 64, 5, padding=2).to(self.device)

        with torch.no_grad():
            features = conv_layer(frame_tensor)
            pooled = torch.nn.functional.max_pool2d(features, 2)

        torch.cuda.synchronize()

    def simulate_face_detection_processing(self):
        """Simulate face detection processing"""
        if not TORCH_AVAILABLE or not torch.cuda.is_available():
            frame = np.random.randint(0, 255, (224, 224, 3), dtype=np.uint8)
            # Simple face detection simulation
            center = np.array([112, 112])
            return

        # GPU face detection simulation
        frame_tensor = torch.randn(1, 3, 224, 224, device=self.device)
        detector = torch.nn.Sequential(
            torch.nn.Conv2d(3, 32, 3, padding=1),
            torch.nn.ReLU(),
            torch.nn.MaxPool2d(2),
            torch.nn.AdaptiveAvgPool2d((1, 1)),
            torch.nn.Flatten(),
            torch.nn.Linear(32, 4)  # x, y, w, h
        ).to(self.device)

        with torch.no_grad():
            bbox = detector(frame_tensor)

        torch.cuda.synchronize()

    def simulate_general_vision_processing(self):
        """Simulate general computer vision processing"""
        if not TORCH_AVAILABLE or not torch.cuda.is_available():
            frame = np.random.randint(0, 255, (160, 120, 3), dtype=np.uint8)
            return

        frame_tensor = torch.randn(1, 3, 160, 120, device=self.device)
        simple_conv = torch.nn.Conv2d(3, 16, 3, padding=1).to(self.device)

        with torch.no_grad():
            _ = simple_conv(frame_tensor)

        torch.cuda.synchronize()

    def simulate_minimal_vision_processing(self):
        """Simulate minimal vision processing for idle state"""
        # Very light processing
        frame = np.random.randint(0, 255, (80, 60, 3), dtype=np.uint8)
        mean_brightness = np.mean(frame)

    def simulate_head_servo_movements(self, frequency='medium'):
        """Simulate head servo movements"""
        if frequency == 'high':
            servo_count = 6  # Head servos
        elif frequency == 'medium':
            servo_count = 4
        else:
            servo_count = 2

        # Simulate servo calculations
        positions = np.random.random(servo_count) * 180
        for pos in positions:
            angle_rad = pos * np.pi / 180
            torque = np.sin(angle_rad)

    def simulate_pose_servo_movements(self):
        """Simulate pose servo movements for photo sessions"""
        # More servos involved in posing
        servo_count = 12
        positions = np.random.random(servo_count) * 180

        # Simulate inverse kinematics calculations
        for i in range(servo_count):
            angle = positions[i] * np.pi / 180
            x = np.cos(angle)
            y = np.sin(angle)

    def simulate_demonstration_servos(self):
        """Simulate demonstration servo movements"""
        # Full body movement demonstration
        servo_count = 24
        positions = np.random.random(servo_count) * 180

        # Complex movement calculations
        for i in range(0, servo_count, 2):
            joint1 = positions[i] * np.pi / 180
            joint2 = positions[i+1] * np.pi / 180
            # Simulate kinematic chain
            end_effector_x = np.cos(joint1) + np.cos(joint1 + joint2)
            end_effector_y = np.sin(joint1) + np.sin(joint1 + joint2)

    def simulate_idle_servo_movements(self):
        """Simulate idle servo movements"""
        # Minimal movement
        servo_count = 3
        positions = np.random.random(servo_count) * 30  # Limited range

        for pos in positions:
            # Simple breathing-like movement
            breathing = np.sin(time.time() * 0.5) * pos

    def simulate_audio_playback(self, sound_type):
        """Simulate audio processing and playback"""
        if sound_type == "scanning_sound":
            duration = 0.5
            samples = int(22050 * duration)
        elif sound_type == "beep_sequence":
            duration = 1.0
            samples = int(22050 * duration)
        elif sound_type == "narration":
            duration = 2.0
            samples = int(22050 * duration)
        else:  # ambient_beep
            duration = 0.2
            samples = int(22050 * duration)

        # Simulate audio buffer processing
        audio_buffer = np.random.random(samples) * 0.1
        # Simple envelope
        envelope = np.linspace(1.0, 0.0, samples)
        processed_audio = audio_buffer * envelope

    def monitor_system_health(self, duration_minutes):
        """Monitor system health during convention operation"""
        print("📊 Starting system health monitoring...")

        end_time = time.time() + duration_minutes * 60
        alert_threshold_temp = 65.0  # °C
        alert_threshold_cpu = 80.0   # %
        alert_threshold_memory = 85.0  # %

        while time.time() < end_time and self.running:
            thermal = self.get_thermal_status()
            system = self.get_system_status()
            timestamp = time.time()

            # Log current status
            self.test_data['thermal_log'].append({
                'timestamp': timestamp,
                **thermal
            })

            self.test_data['performance_log'].append({
                'timestamp': timestamp,
                **system
            })

            # Check for alerts
            alerts = []

            if thermal['cpu'] and thermal['cpu'] > alert_threshold_temp:
                alerts.append(f"CPU temperature high: {thermal['cpu']:.1f}°C")

            if thermal['gpu'] and thermal['gpu'] > alert_threshold_temp:
                alerts.append(f"GPU temperature high: {thermal['gpu']:.1f}°C")

            if system['cpu_percent'] and system['cpu_percent'] > alert_threshold_cpu:
                alerts.append(f"CPU usage high: {system['cpu_percent']:.1f}%")

            if system['memory_percent'] and system['memory_percent'] > alert_threshold_memory:
                alerts.append(f"Memory usage high: {system['memory_percent']:.1f}%")

            if alerts:
                alert_entry = {
                    'timestamp': timestamp,
                    'alerts': alerts,
                    'thermal': thermal,
                    'system': system
                }
                self.test_data['system_alerts'].append(alert_entry)
                print(f"⚠️ ALERT: {', '.join(alerts)}")

            time.sleep(5)  # Monitor every 5 seconds

    def run_convention_scenario(self, scenario_name="full_day"):
        """Run a complete convention scenario"""
        print("\n" + "=" * 70)
        print("R2-D2 CONVENTION LOAD TEST")
        print("=" * 70)
        print(f"Scenario: {scenario_name}")
        print(f"Target: Extended operation simulation")
        print()

        self.running = True
        self.test_data['start_time'] = datetime.now()

        # Define convention schedule
        if scenario_name == "full_day":
            schedule = [
                ("idle_patrol", 2),      # 2 minutes startup/idle
                ("crowd_scanning", 3),   # 3 minutes crowd interaction
                ("photo_session", 4),    # 4 minutes photo session
                ("demonstration", 3),    # 3 minutes demonstration
                ("idle_patrol", 1),      # 1 minute break
                ("crowd_scanning", 2),   # 2 minutes more crowd
                ("photo_session", 2),    # 2 minutes more photos
                ("idle_patrol", 1),      # 1 minute cooldown
            ]
            total_duration = sum(duration for _, duration in schedule)
        elif scenario_name == "busy_hour":
            schedule = [
                ("crowd_scanning", 4),   # 4 minutes intensive scanning
                ("photo_session", 6),    # 6 minutes photo sessions
                ("demonstration", 5),    # 5 minutes demonstration
            ]
            total_duration = sum(duration for _, duration in schedule)
        else:  # stress_test
            schedule = [
                ("crowd_scanning", 10),  # 10 minutes continuous intensive operation
            ]
            total_duration = sum(duration for _, duration in schedule)

        print(f"📅 Convention Schedule ({total_duration} minutes):")
        for i, (activity, duration) in enumerate(schedule, 1):
            print(f"  {i}. {activity.replace('_', ' ').title()}: {duration} minutes")

        # Start system monitoring
        monitor_thread = threading.Thread(
            target=self.monitor_system_health,
            args=(total_duration,),
            name="SystemMonitor"
        )
        monitor_thread.start()

        # Execute schedule
        print(f"\n🎬 Starting convention simulation...")
        start_time = time.time()

        for i, (activity, duration) in enumerate(schedule, 1):
            if not self.running:
                break

            print(f"\n📍 Phase {i}/{len(schedule)}: {activity.replace('_', ' ').title()}")

            activity_thread = threading.Thread(
                target=self.simulate_convention_interaction,
                args=(activity, duration),
                name=f"Activity_{activity}"
            )
            activity_thread.start()
            activity_thread.join()

            # Brief pause between activities
            if i < len(schedule):
                print("   ⏸️ Brief transition pause...")
                time.sleep(5)

        self.running = False
        monitor_thread.join(timeout=10)

        total_time = time.time() - start_time
        print(f"\n✅ Convention simulation completed in {total_time/60:.1f} minutes")

        return self.analyze_convention_results()

    def analyze_convention_results(self):
        """Analyze convention test results"""
        print("\n" + "=" * 70)
        print("CONVENTION LOAD TEST ANALYSIS")
        print("=" * 70)

        if not self.test_data['thermal_log']:
            print("❌ No data collected for analysis")
            return None

        # Thermal analysis
        cpu_temps = [entry['cpu'] for entry in self.test_data['thermal_log'] if entry['cpu']]
        gpu_temps = [entry['gpu'] for entry in self.test_data['thermal_log'] if entry['gpu']]

        thermal_analysis = {
            'cpu_max': max(cpu_temps) if cpu_temps else None,
            'cpu_avg': np.mean(cpu_temps) if cpu_temps else None,
            'gpu_max': max(gpu_temps) if gpu_temps else None,
            'gpu_avg': np.mean(gpu_temps) if gpu_temps else None,
        }

        # Performance analysis
        cpu_usage = [entry['cpu_percent'] for entry in self.test_data['performance_log'] if entry['cpu_percent']]
        memory_usage = [entry['memory_percent'] for entry in self.test_data['performance_log'] if entry['memory_percent']]

        performance_analysis = {
            'cpu_max': max(cpu_usage) if cpu_usage else None,
            'cpu_avg': np.mean(cpu_usage) if cpu_usage else None,
            'memory_max': max(memory_usage) if memory_usage else None,
            'memory_avg': np.mean(memory_usage) if memory_usage else None,
        }

        # Interaction analysis
        interaction_types = {}
        for entry in self.test_data['interaction_log']:
            itype = entry['type']
            if itype not in interaction_types:
                interaction_types[itype] = 0
            interaction_types[itype] += 1

        # Print analysis
        print(f"\n🌡️ THERMAL PERFORMANCE:")
        if thermal_analysis['cpu_max']:
            print(f"  CPU Temperature: {thermal_analysis['cpu_avg']:.1f}°C avg, {thermal_analysis['cpu_max']:.1f}°C peak")
        if thermal_analysis['gpu_max']:
            print(f"  GPU Temperature: {thermal_analysis['gpu_avg']:.1f}°C avg, {thermal_analysis['gpu_max']:.1f}°C peak")

        thermal_status = "✅ EXCELLENT"
        if (thermal_analysis['cpu_max'] or 0) > 70 or (thermal_analysis['gpu_max'] or 0) > 70:
            thermal_status = "⚠️ WARM"
        if (thermal_analysis['cpu_max'] or 0) > 80 or (thermal_analysis['gpu_max'] or 0) > 80:
            thermal_status = "❌ HOT"
        print(f"  Thermal Status: {thermal_status}")

        print(f"\n📊 SYSTEM PERFORMANCE:")
        if performance_analysis['cpu_max']:
            print(f"  CPU Utilization: {performance_analysis['cpu_avg']:.1f}% avg, {performance_analysis['cpu_max']:.1f}% peak")
        if performance_analysis['memory_max']:
            print(f"  Memory Utilization: {performance_analysis['memory_avg']:.1f}% avg, {performance_analysis['memory_max']:.1f}% peak")

        performance_status = "✅ GOOD"
        if (performance_analysis['cpu_max'] or 0) > 80 or (performance_analysis['memory_max'] or 0) > 85:
            performance_status = "⚠️ HIGH"
        print(f"  Performance Status: {performance_status}")

        print(f"\n🎭 INTERACTION SUMMARY:")
        total_interactions = sum(interaction_types.values())
        for itype, count in interaction_types.items():
            print(f"  {itype.replace('_', ' ').title()}: {count} interactions")
        print(f"  Total Interactions: {total_interactions}")

        print(f"\n⚠️ SYSTEM ALERTS:")
        if self.test_data['system_alerts']:
            for alert in self.test_data['system_alerts']:
                timestamp = datetime.fromtimestamp(alert['timestamp'])
                print(f"  {timestamp.strftime('%H:%M:%S')}: {', '.join(alert['alerts'])}")
        else:
            print("  No system alerts - Excellent stability!")

        # Overall assessment
        print(f"\n🏆 CONVENTION READINESS:")
        thermal_ok = thermal_status == "✅ EXCELLENT"
        performance_ok = performance_status == "✅ GOOD"
        alerts_ok = len(self.test_data['system_alerts']) == 0
        interactions_ok = total_interactions > 0

        readiness_score = sum([thermal_ok, performance_ok, alerts_ok, interactions_ok])

        if readiness_score == 4:
            readiness = "🎉 FULLY READY"
            message = "System exceeds requirements for convention operation!"
        elif readiness_score == 3:
            readiness = "✅ READY"
            message = "System ready for convention with monitoring recommended."
        elif readiness_score == 2:
            readiness = "⚠️ CONDITIONAL"
            message = "System functional but may need optimization for extended use."
        else:
            readiness = "❌ NEEDS WORK"
            message = "System requires optimization before convention deployment."

        print(f"  Overall Status: {readiness}")
        print(f"  Assessment: {message}")

        # Save detailed results
        results_file = f"/home/rolo/r2ai/convention_test_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        detailed_results = {
            'test_info': {
                'start_time': self.test_data['start_time'].isoformat(),
                'duration_minutes': (time.time() - time.mktime(self.test_data['start_time'].timetuple())) / 60,
                'total_interactions': total_interactions
            },
            'thermal_analysis': thermal_analysis,
            'performance_analysis': performance_analysis,
            'interaction_summary': interaction_types,
            'alerts': self.test_data['system_alerts'],
            'readiness_score': readiness_score,
            'readiness_status': readiness
        }

        try:
            with open(results_file, 'w') as f:
                json.dump(detailed_results, f, indent=2, default=str)
            print(f"\n📄 Detailed results saved to: {results_file}")
        except Exception as e:
            print(f"⚠️ Could not save results: {e}")

        return detailed_results

def main():
    print("R2-D2 Convention Load Test")
    print("NVIDIA Orin Nano Extended Operation Validation")
    print("=" * 50)

    tester = R2D2ConventionLoadTest()

    print(f"\n🛠️ System Configuration:")
    print(f"  PyTorch: {'✅' if TORCH_AVAILABLE else '❌'} Available")
    if TORCH_AVAILABLE:
        print(f"  CUDA: {'✅' if torch.cuda.is_available() else '❌'} Available")
        if torch.cuda.is_available():
            print(f"  GPU: {torch.cuda.get_device_name(0)}")

    print(f"  System Monitoring: {'✅' if PSUTIL_AVAILABLE else '❌'} Available")

    # Run convention scenario
    print(f"\n🎯 Running convention simulation...")
    results = tester.run_convention_scenario("full_day")

    if results:
        print(f"\n{'🎉 CONVENTION LOAD TEST PASSED!' if results['readiness_score'] >= 3 else '⚠️ SYSTEM NEEDS OPTIMIZATION'}")
    else:
        print(f"\n❌ CONVENTION LOAD TEST FAILED!")

if __name__ == "__main__":
    main()