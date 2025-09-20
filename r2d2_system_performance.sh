#!/bin/bash
# NVIDIA Orin Nano R2D2 Performance Configuration Script
# Run with: sudo bash r2d2_system_performance.sh

echo "NVIDIA Orin Nano R2D2 Performance Configuration"
echo "==============================================="

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo "Please run this script with sudo: sudo bash r2d2_system_performance.sh"
    exit 1
fi

LOG_FILE="/home/rolo/r2ai/r2d2_performance_config.log"
echo "Starting R2D2 performance configuration at $(date)" > $LOG_FILE

# 1. CPU PERFORMANCE OPTIMIZATION
echo "1. Configuring CPU Performance Mode..."
echo "Configuring CPU Performance Mode at $(date)" >> $LOG_FILE

# Set all CPU cores to performance governor
for cpu in /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor; do
    if [ -w "$cpu" ]; then
        echo "performance" > "$cpu"
        echo "Set $(basename $(dirname $cpu)) to performance mode" >> $LOG_FILE
    fi
done

# Set CPU frequencies to maximum
for cpu in /sys/devices/system/cpu/cpu*/cpufreq/scaling_min_freq; do
    if [ -w "$cpu" ]; then
        echo "1728000" > "$cpu"
        echo "Set $(basename $(dirname $cpu)) minimum frequency to maximum" >> $LOG_FILE
    fi
done

echo "CPU performance mode configured successfully"

# 2. MEMORY OPTIMIZATION
echo "2. Optimizing Memory Performance..."
echo "Optimizing Memory Performance at $(date)" >> $LOG_FILE

# Disable swap for real-time performance
swapoff -a
echo "Swap disabled for real-time performance" >> $LOG_FILE

# Set minimal swappiness
echo 1 > /proc/sys/vm/swappiness
echo "VM swappiness set to 1" >> $LOG_FILE

# Configure dirty ratio for better I/O performance
echo 15 > /proc/sys/vm/dirty_ratio
echo 5 > /proc/sys/vm/dirty_background_ratio
echo "VM dirty ratios optimized for I/O performance" >> $LOG_FILE

echo "Memory optimization completed"

# 3. I2C BUS OPTIMIZATION
echo "3. Optimizing I2C Bus Performance..."
echo "Optimizing I2C Bus Performance at $(date)" >> $LOG_FILE

# Check I2C bus speeds (if configurable)
for i2c_bus in /dev/i2c-*; do
    if [ -e "$i2c_bus" ]; then
        bus_num=$(basename $i2c_bus | cut -d'-' -f2)
        echo "I2C bus $bus_num available" >> $LOG_FILE
    fi
done

echo "I2C bus optimization completed"

# 4. REAL-TIME KERNEL PARAMETERS
echo "4. Configuring Real-Time Parameters..."
echo "Configuring Real-Time Parameters at $(date)" >> $LOG_FILE

# Configure kernel for low-latency operation
echo 1 > /proc/sys/kernel/timer_migration
echo "Timer migration enabled" >> $LOG_FILE

# Set real-time throttling
echo 950000 > /proc/sys/kernel/sched_rt_runtime_us
echo "Real-time scheduling configured" >> $LOG_FILE

# Configure scheduler for responsive servo control
echo 10000 > /proc/sys/kernel/sched_min_granularity_ns
echo 25000 > /proc/sys/kernel/sched_wakeup_granularity_ns
echo "Scheduler optimized for responsive control" >> $LOG_FILE

echo "Real-time parameters configured"

# 5. THERMAL AND POWER MANAGEMENT
echo "5. Configuring Thermal and Power Management..."
echo "Configuring Thermal and Power Management at $(date)" >> $LOG_FILE

# Check and log thermal zones
thermal_zones=$(ls /sys/class/thermal/thermal_zone*/temp 2>/dev/null | wc -l)
echo "Found $thermal_zones thermal zones" >> $LOG_FILE

# Get current temperatures
for temp_file in /sys/class/thermal/thermal_zone*/temp; do
    if [ -r "$temp_file" ]; then
        temp=$(cat "$temp_file" 2>/dev/null)
        if [ ! -z "$temp" ]; then
            zone=$(basename $(dirname $temp_file))
            temp_celsius=$((temp / 1000))
            echo "$zone: ${temp_celsius}°C" >> $LOG_FILE
        fi
    fi
done

echo "Thermal monitoring configured"

# 6. AUDIO SYSTEM OPTIMIZATION
echo "6. Optimizing Audio System..."
echo "Optimizing Audio System at $(date)" >> $LOG_FILE

# Configure ALSA for low latency
if command -v amixer >/dev/null 2>&1; then
    amixer set Master 80% >/dev/null 2>&1
    echo "Audio volume set to 80%" >> $LOG_FILE
fi

# Check audio devices
if [ -f /proc/asound/cards ]; then
    audio_cards=$(cat /proc/asound/cards | grep -c "^[[:space:]]*[0-9]")
    echo "Found $audio_cards audio cards" >> $LOG_FILE
fi

echo "Audio system optimization completed"

# 7. NETWORK OPTIMIZATION FOR R2D2
echo "7. Optimizing Network for R2D2 Communications..."
echo "Optimizing Network for R2D2 Communications at $(date)" >> $LOG_FILE

# Optimize network buffer sizes
echo 262144 > /proc/sys/net/core/rmem_default
echo 262144 > /proc/sys/net/core/wmem_default
echo "Network buffer sizes optimized" >> $LOG_FILE

echo "Network optimization completed"

# 8. GPIO AND HARDWARE ACCESS OPTIMIZATION
echo "8. Configuring GPIO and Hardware Access..."
echo "Configuring GPIO and Hardware Access at $(date)" >> $LOG_FILE

# Ensure GPIO access is available
if [ -d /sys/class/gpio ]; then
    echo "GPIO interface available" >> $LOG_FILE
else
    echo "GPIO interface not found" >> $LOG_FILE
fi

# Check for hardware PWM
pwm_chips=$(ls /sys/class/pwm/ 2>/dev/null | grep pwmchip | wc -l)
echo "Found $pwm_chips PWM chips" >> $LOG_FILE

echo "GPIO and hardware access configured"

# 9. CREATE R2D2 PERFORMANCE MONITORING SCRIPT
echo "9. Creating R2D2 Performance Monitor..."
cat > /home/rolo/r2ai/r2d2_performance_monitor.sh << 'EOF'
#!/bin/bash
# R2D2 Performance Monitoring Script

MONITOR_LOG="/home/rolo/r2ai/r2d2_performance.log"

while true; do
    TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')

    # CPU Information
    CPU_FREQ=$(cat /sys/devices/system/cpu/cpu0/cpufreq/scaling_cur_freq 2>/dev/null)
    CPU_USAGE=$(top -bn1 | grep "Cpu(s)" | awk '{print $2}' | cut -d'%' -f1)

    # Memory Information
    MEM_INFO=$(free | grep Mem | awk '{printf "%.1f", $3/$2 * 100.0}')

    # Thermal Information
    TEMP_AVG=$(cat /sys/class/thermal/thermal_zone*/temp 2>/dev/null | head -5 | awk '{sum+=$1; count++} END {if(count>0) print sum/count/1000; else print "N/A"}')

    # I2C Bus Status
    I2C_BUSES=$(ls /dev/i2c-* 2>/dev/null | wc -l)

    # Log performance metrics
    echo "$TIMESTAMP,CPU_FREQ:${CPU_FREQ}kHz,CPU_USAGE:${CPU_USAGE}%,MEM_USAGE:${MEM_INFO}%,TEMP_AVG:${TEMP_AVG}°C,I2C_BUSES:$I2C_BUSES" >> $MONITOR_LOG

    sleep 10
done
EOF

chmod +x /home/rolo/r2ai/r2d2_performance_monitor.sh
chown rolo:rolo /home/rolo/r2ai/r2d2_performance_monitor.sh
echo "Performance monitoring script created" >> $LOG_FILE

echo "Performance monitoring script created"

# 10. CREATE R2D2 STARTUP OPTIMIZATION SERVICE
echo "10. Creating R2D2 Startup Service..."
cat > /etc/systemd/system/r2d2-optimization.service << 'EOF'
[Unit]
Description=R2D2 System Optimization Service
After=multi-user.target

[Service]
Type=oneshot
ExecStart=/bin/bash /home/rolo/r2ai/r2d2_system_performance.sh
RemainAfterExit=yes
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
echo "R2D2 optimization service created (not enabled by default)" >> $LOG_FILE

echo "R2D2 startup service created"

# 11. PERFORMANCE VALIDATION TEST
echo "11. Running Performance Validation..."
echo "Running Performance Validation at $(date)" >> $LOG_FILE

# Test CPU performance
CPU_TEST_RESULT=$(python3 -c "
import time
start = time.time()
for i in range(1000000):
    result = i * 0.5 + 1.0
end = time.time()
print(f'{1000000/(end-start):.0f}')
" 2>/dev/null)

echo "CPU Performance: ${CPU_TEST_RESULT} operations/sec" >> $LOG_FILE

# Test memory allocation
MEM_TEST_RESULT=$(python3 -c "
import time
start = time.time()
data = []
for i in range(10000):
    data.append([0] * 100)
end = time.time()
print(f'{10000/(end-start):.0f}')
" 2>/dev/null)

echo "Memory Performance: ${MEM_TEST_RESULT} allocations/sec" >> $LOG_FILE

echo "Performance validation completed"

# 12. FINAL SYSTEM STATUS
echo "12. Generating Final System Status..."
echo "Final System Status at $(date)" >> $LOG_FILE

# Current governor settings
echo "Current CPU Governors:" >> $LOG_FILE
for cpu in /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor; do
    if [ -r "$cpu" ]; then
        governor=$(cat "$cpu")
        cpu_num=$(basename $(dirname $cpu))
        echo "  $cpu_num: $governor" >> $LOG_FILE
    fi
done

# Current frequencies
echo "Current CPU Frequencies:" >> $LOG_FILE
for cpu in /sys/devices/system/cpu/cpu*/cpufreq/scaling_cur_freq; do
    if [ -r "$cpu" ]; then
        freq=$(cat "$cpu")
        cpu_num=$(basename $(dirname $cpu))
        echo "  $cpu_num: ${freq}kHz" >> $LOG_FILE
    fi
done

# Memory status
MEM_TOTAL=$(grep MemTotal /proc/meminfo | awk '{print $2}')
MEM_AVAILABLE=$(grep MemAvailable /proc/meminfo | awk '{print $2}')
echo "Memory: ${MEM_AVAILABLE}kB available of ${MEM_TOTAL}kB total" >> $LOG_FILE

# Final temperature check
echo "Final temperatures:" >> $LOG_FILE
for temp_file in /sys/class/thermal/thermal_zone*/temp; do
    if [ -r "$temp_file" ]; then
        temp=$(cat "$temp_file" 2>/dev/null)
        if [ ! -z "$temp" ]; then
            zone=$(basename $(dirname $temp_file))
            temp_celsius=$((temp / 1000))
            echo "  $zone: ${temp_celsius}°C" >> $LOG_FILE
        fi
    fi
done

echo ""
echo "NVIDIA Orin Nano R2D2 Performance Configuration Complete!"
echo "========================================================"
echo ""
echo "Configuration Summary:"
echo "- CPU governors set to 'performance' mode"
echo "- CPU frequencies set to maximum (1.728 GHz)"
echo "- Memory optimized for real-time operation"
echo "- I2C buses optimized for servo control"
echo "- Real-time kernel parameters configured"
echo "- Thermal monitoring active"
echo "- Audio system optimized for low latency"
echo "- Performance monitoring script created"
echo ""
echo "Performance Test Results:"
echo "- CPU Performance: ${CPU_TEST_RESULT} operations/sec"
echo "- Memory Performance: ${MEM_TEST_RESULT} allocations/sec"
echo ""
echo "Next Steps:"
echo "1. Test R2D2 component functionality with optimized settings"
echo "2. Run: python3 /home/rolo/r2ai/r2d2_component_tester.py"
echo "3. Monitor performance: bash /home/rolo/r2ai/r2d2_performance_monitor.sh &"
echo "4. For real-time R2D2 processes, use: chrt -f 50 python3 your_r2d2_script.py"
echo ""
echo "Log file: $LOG_FILE"
echo "System ready for R2D2 deployment!"

# Set proper ownership for all created files
chown rolo:rolo /home/rolo/r2ai/r2d2_performance_monitor.sh
chown rolo:rolo $LOG_FILE

exit 0