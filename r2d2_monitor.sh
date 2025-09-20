#!/bin/bash
# R2D2 System Monitoring Script
LOG_DIR=/home/rolo/r2ai/logs
DATE=$(date +%Y%m%d_%H%M%S)

# Monitor system resources
echo "=== R2D2 System Monitor - $DATE ===" >> $LOG_DIR/r2d2_monitor_$DATE.log
echo "CPU Usage: $(cat /proc/loadavg)" >> $LOG_DIR/r2d2_monitor_$DATE.log
echo "Memory Usage: $(free -h)" >> $LOG_DIR/r2d2_monitor_$DATE.log
echo "Temperature: $(cat /sys/class/thermal/thermal_zone*/temp 2>/dev/null | head -5)" >> $LOG_DIR/r2d2_monitor_$DATE.log
echo "I2C Buses: $(ls /dev/i2c-* 2>/dev/null)" >> $LOG_DIR/r2d2_monitor_$DATE.log
