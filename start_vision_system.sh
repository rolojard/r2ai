#!/bin/bash
# Start Vision System for R2D2 Dashboards
# Launches simple_vision_feed.py on port 8767

echo "🎥 Starting R2D2 Vision System..."
echo "=================================="

# Check if already running
if lsof -Pi :8767 -sTCP:LISTEN -t >/dev/null 2>&1; then
    echo "⚠️  Vision system already running on port 8767"
    PID=$(lsof -Pi :8767 -sTCP:LISTEN -t)
    echo "   PID: $PID"
    echo ""
    echo "To restart, run: ./stop_vision_system.sh && ./start_vision_system.sh"
    exit 1
fi

# Check if camera is available
if ! ls /dev/video* >/dev/null 2>&1; then
    echo "⚠️  WARNING: No camera detected at /dev/video*"
    echo "   Vision system will attempt to connect anyway..."
fi

# Check if script exists
if [ ! -f "simple_vision_feed.py" ]; then
    echo "❌ Error: simple_vision_feed.py not found"
    exit 1
fi

# Make executable
chmod +x simple_vision_feed.py

# Start vision system in background
nohup python3 simple_vision_feed.py > vision_system.log 2>&1 &
VISION_PID=$!

# Wait a moment for startup
sleep 2

# Check if it started successfully
if ps -p $VISION_PID > /dev/null; then
    echo "✅ Vision system started successfully!"
    echo ""
    echo "   PID: $VISION_PID"
    echo "   WebSocket: ws://localhost:8767"
    echo "   Log: $(pwd)/vision_system.log"
    echo ""
    echo "📹 Camera feed is now available to dashboards"
    echo ""
    echo "To view logs: tail -f vision_system.log"
    echo "To stop: ./stop_vision_system.sh"
else
    echo "❌ Failed to start vision system"
    echo "   Check vision_system.log for errors"
    exit 1
fi
