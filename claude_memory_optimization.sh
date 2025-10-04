#!/bin/bash

# Claude Memory Optimization Script for Nvidia Orin Nano (8GB RAM)
# Run with: sudo ./claude_memory_optimization.sh

echo "🤖 Claude Memory Optimization for R2D2 Project"
echo "============================================="

# 1. Set swappiness to reduce swap usage (prefer RAM)
echo "📝 Setting swappiness to 10 (prefer RAM over swap)..."
echo 'vm.swappiness=10' >> /etc/sysctl.conf
sysctl vm.swappiness=10

# 2. Set dirty ratio for better memory management
echo "📝 Optimizing dirty memory ratios..."
echo 'vm.dirty_ratio=15' >> /etc/sysctl.conf
echo 'vm.dirty_background_ratio=5' >> /etc/sysctl.conf
sysctl vm.dirty_ratio=15
sysctl vm.dirty_background_ratio=5

# 3. Enable memory overcommit for better Node.js handling
echo "📝 Configuring memory overcommit..."
echo 'vm.overcommit_memory=1' >> /etc/sysctl.conf
sysctl vm.overcommit_memory=1

# 4. Set up OOM killer protection for critical R2D2 processes
echo "📝 Creating R2D2 process protection..."
cat > /etc/systemd/system/r2d2-memory-protection.service << EOF
[Unit]
Description=R2D2 Memory Protection Service
After=multi-user.target

[Service]
Type=oneshot
ExecStart=/bin/bash -c 'pgrep -f "r2d2_.*\.py" | xargs -I {} sh -c "echo -15 > /proc/{}/oom_adj 2>/dev/null || true"'
RemainAfterExit=yes

[Install]
WantedBy=multi-user.target
EOF

systemctl enable r2d2-memory-protection.service
systemctl start r2d2-memory-protection.service

# 5. Create Claude startup script with memory limits
echo "📝 Creating optimized Claude startup script..."
cat > /home/rolo/start_claude_optimized.sh << 'EOF'
#!/bin/bash
export NODE_OPTIONS="--max-old-space-size=6144 --gc-interval=100"
export UV_THREADPOOL_SIZE=8
export V8_USE_EXTERNAL_STARTUP_DATA=1

# Clear any previous Claude processes
pkill -f claude 2>/dev/null || true
sleep 2

# Start Claude with memory optimizations
echo "🚀 Starting Claude with memory optimizations..."
cd /home/rolo/r2ai
claude "$@"
EOF

chmod +x /home/rolo/start_claude_optimized.sh
chown rolo:rolo /home/rolo/start_claude_optimized.sh

# 6. Create memory monitoring script
echo "📝 Creating memory monitoring script..."
cat > /home/rolo/r2ai/monitor_memory.sh << 'EOF'
#!/bin/bash

# Memory monitoring for R2D2 project
while true; do
    echo "=== Memory Status $(date) ==="
    free -h
    echo ""
    echo "Top Memory Consumers:"
    ps aux --sort=-%mem | head -10
    echo ""
    echo "Claude Processes:"
    pgrep -f claude | xargs -I {} ps -p {} -o pid,ppid,%cpu,%mem,cmd 2>/dev/null || echo "No Claude processes running"
    echo ""
    sleep 30
done
EOF

chmod +x /home/rolo/r2ai/monitor_memory.sh
chown rolo:rolo /home/rolo/r2ai/monitor_memory.sh

echo "✅ Memory optimization complete!"
echo ""
echo "🎯 Next Steps:"
echo "1. Restart your terminal or run: source ~/.bashrc"
echo "2. Use: ./start_claude_optimized.sh instead of 'claude'"
echo "3. Monitor memory: ./monitor_memory.sh"
echo ""
echo "⚡ Key Optimizations Applied:"
echo "- Node.js heap limit: 6GB (was 4GB)"
echo "- Swappiness reduced: 10 (was 60)"
echo "- Memory overcommit enabled"
echo "- R2D2 process OOM protection"
echo "- Optimized garbage collection"