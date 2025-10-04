#!/bin/bash
# R2D2 Complete Dashboard System Startup Script
# Starts both dashboard server and video feed system

echo "🎯 Starting R2D2 Complete Dashboard System"
echo "============================================"

# Function to check if port is in use
check_port() {
    netstat -tuln | grep ":$1 " > /dev/null
    return $?
}

# Function to kill processes on specific ports
cleanup_port() {
    local port=$1
    local pids=$(lsof -ti:$port 2>/dev/null)
    if [ ! -z "$pids" ]; then
        echo "🧹 Cleaning up existing processes on port $port"
        kill -9 $pids 2>/dev/null || true
        sleep 1
    fi
}

# Cleanup existing processes
echo "🧹 Cleaning up any existing services..."
cleanup_port 8765
cleanup_port 8766
cleanup_port 8767

# Kill any existing dashboard or vision processes
pkill -f "dashboard-server.js" 2>/dev/null || true
pkill -f "test_dashboard_video_feed.py" 2>/dev/null || true
sleep 2

echo "🚀 Starting Dashboard HTTP and WebSocket Server..."
npm start &
DASHBOARD_PID=$!

# Wait for dashboard to start
sleep 3

echo "🎥 Starting Live Video Feed System..."
python3 r2d2_ultra_stable_vision.py &
VIDEO_PID=$!

# Wait for services to initialize
sleep 5

echo "🔍 Checking service status..."

# Check if services are running
if check_port 8765; then
    echo "✅ Dashboard HTTP Server (8765): Running"
else
    echo "❌ Dashboard HTTP Server (8765): Failed to start"
fi

if check_port 8766; then
    echo "✅ Dashboard WebSocket Server (8766): Running"
else
    echo "❌ Dashboard WebSocket Server (8766): Failed to start"
fi

if check_port 8767; then
    echo "✅ Vision WebSocket Server (8767): Running"
else
    echo "❌ Vision WebSocket Server (8767): Failed to start"
fi

echo ""
echo "🎉 R2D2 Dashboard System Started!"
echo "============================================"
echo "🌐 Dashboard URL: http://localhost:8765"
echo ""
echo "📊 Expected Features:"
echo "   - Live video feed with Star Wars character detection"
echo "   - Real-time character recognition display"
echo "   - R2D2 emotional reactions"
echo "   - Servo control interface"
echo "   - Audio system controls"
echo ""
echo "🔧 Service Information:"
echo "   - Dashboard PID: $DASHBOARD_PID"
echo "   - Video Feed PID: $VIDEO_PID"
echo ""
echo "⏹️  To stop services:"
echo "   kill $DASHBOARD_PID $VIDEO_PID"
echo "   Or run: pkill -f 'dashboard-server.js|test_dashboard_video_feed.py'"
echo ""
echo "✨ Open your browser to http://localhost:8765 to access the dashboard!"