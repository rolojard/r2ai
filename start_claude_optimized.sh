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
