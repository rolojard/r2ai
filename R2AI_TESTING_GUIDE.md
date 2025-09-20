# 🎯 R2AI System Testing & Dashboard Guide

## 🚀 QUICK START COMMANDS

### **System Health Check**
```bash
# Quick system status
python3 r2d2_integrated_performance.py

# Component status check
python3 r2d2_component_tester.py

# Thermal monitoring
python3 r2d2_simple_thermal_monitor.py
```

### **Hardware Testing**
```bash
# Test all servos
python3 test_r2d2_servos.py

# Servo functionality test
python3 servo_functionality_test.py

# Basic system test
python3 r2d2_basic_tester.py
```

### **Performance & Validation**
```bash
# Enhanced scenario testing
python3 r2d2_enhanced_scenario_tester.py

# Multimodal validation
python3 r2d2_multimodal_validator.py

# Vision system validation
python3 r2d2_vision_validator.py
```

## 🖥️ DASHBOARD LAUNCH

### **Web Dashboard** (with memory fix)
```bash
# Launch dashboard with 4GB memory
./start-dashboard.sh

# Alternative direct launch
export NODE_OPTIONS="--max-old-space-size=4096"
node .claude/agent_storage/web-dev-specialist/dashboard_script.js
```

### **System Performance Dashboard**
```bash
# Real-time system monitoring
./r2d2_system_performance.sh

# System monitoring with logging
./r2d2_monitor.sh
```

## 🎭 PERFORMANCE TESTING

### **Motion & Animation**
```bash
# Test individual servo movements
python3 r2d2_servo_controller.py

# Simple servo testing
python3 r2d2_servo_simple.py

# Optimized performance testing
python3 r2d2_optimized_tester.py
```

### **Audio & Sound Testing**
```bash
# Canonical sound enhancement
python3 r2d2_canonical_sound_enhancer.py

# Sound validation
python3 r2d2_canonical_sound_validator.py

# Personality enhancement
python3 r2d2_personality_enhancer.py
```

## 🔧 SYSTEM VALIDATION

### **Security & Quality Assurance**
```bash
# Security validation
python3 r2d2_security_validator.py

# Convention load testing
python3 r2d2_convention_load_test.py

# GPU optimization testing
python3 r2d2_gpu_optimization.py
```

### **Thermal & Power Management**
```bash
# Thermal power manager
python3 r2d2_thermal_power_manager.py

# CUDA performance test
python3 cuda_performance_test.py
```

## 📊 QUICK STATUS COMMANDS

### **One-Line System Check**
```bash
# Quick health check
echo "=== R2AI STATUS ===" && python3 -c "
import psutil, subprocess
print(f'CPU: {psutil.cpu_percent()}%')
print(f'Memory: {psutil.virtual_memory().percent}%')
print(f'Temp: {open(\"/sys/class/thermal/thermal_zone0/temp\").read().strip()[:2]}°C')
print('GPU:', subprocess.check_output(['nvidia-smi', '--query-gpu=utilization.gpu', '--format=csv,noheader,nounits']).decode().strip() + '%')
"
```

### **Servo Status Check**
```bash
# Check I2C devices (servo controllers)
i2cdetect -y 1

# Test camera
v4l2-ctl --list-devices
```

## 🎪 PERFORMANCE DEMOS

### **Convention Ready Demos**
```bash
# Full system demonstration
python3 r2d2_enhanced_scenario_tester.py --demo-mode

# Guest interaction simulation
python3 r2d2_multimodal_validator.py --interactive

# Security alert demonstration
python3 r2d2_optimized_tester.py --security-demo
```

## 🔍 TROUBLESHOOTING

### **If Tests Fail**
1. **Check dependencies**: `pip3 install adafruit-servokit pygame opencv-python`
2. **Check I2C**: `sudo chmod 666 /dev/i2c-*`
3. **Check GPU**: `nvidia-smi`
4. **Check audio**: `pactl list short sinks`

### **Emergency Commands**
```bash
# Stop all servos
sudo pkill -f "servo"

# Kill all R2D2 processes
sudo pkill -f "r2d2"

# System reset
sudo reboot
```

## 📱 MONITORING URLS

Once dashboard is running:
- **Main Dashboard**: http://localhost:8765
- **System Monitor**: http://localhost:3000 (if configured)
- **Camera Feed**: http://localhost:8080/stream (if configured)

## 🎯 RECOMMENDED TEST SEQUENCE

1. **Start with**: `python3 r2d2_integrated_performance.py`
2. **Test hardware**: `python3 test_r2d2_servos.py`
3. **Launch dashboard**: `./start-dashboard.sh`
4. **Run full demo**: `python3 r2d2_enhanced_scenario_tester.py`

Your R2AI system is **CONVENTION READY** - all tests should pass with excellent performance metrics!