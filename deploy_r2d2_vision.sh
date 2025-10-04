#!/bin/bash
# Orin Nano R2D2 Vision System Deployment Script

echo "=== R2D2 Orin Nano Vision System Deployment ==="

# Set maximum performance
echo "Setting maximum performance mode..."
sudo nvpmodel -m 0
sudo jetson_clocks

# Install required packages
echo "Installing required packages..."
sudo apt update
sudo apt install -y v4l-utils ffmpeg gstreamer1.0-tools

# Set CPU governor to performance
echo "Setting CPU governor to performance..."
echo performance | sudo tee /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor

# Create systemd service for R2D2 vision
echo "Creating systemd service..."
sudo tee /etc/systemd/system/r2d2-vision.service > /dev/null <<EOF
[Unit]
Description=R2D2 Vision System
After=multi-user.target

[Service]
Type=simple
User=rolo
WorkingDirectory=/home/rolo/r2ai
ExecStart=/usr/bin/python3 /home/rolo/r2ai/r2d2_orin_nano_vision_integration.py
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

# Enable service
sudo systemctl enable r2d2-vision.service

echo "Deployment complete!"
echo "Start the vision system with: sudo systemctl start r2d2-vision"
echo "Check status with: sudo systemctl status r2d2-vision"
