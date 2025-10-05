#!/bin/bash
# Stop Vision System

echo "🛑 Stopping R2D2 Vision System..."
echo "================================="

# Find vision system process
VISION_PIDS=$(pgrep -f "simple_vision_feed.py")

if [ -z "$VISION_PIDS" ]; then
    echo "✓ No vision system process found"

    # Double check port 8767
    if lsof -Pi :8767 -sTCP:LISTEN -t >/dev/null 2>&1; then
        PORT_PID=$(lsof -Pi :8767 -sTCP:LISTEN -t)
        echo "⚠️  Found process on port 8767: PID $PORT_PID"
        echo "   Killing..."
        kill $PORT_PID 2>/dev/null
        sleep 1
        if lsof -Pi :8767 -sTCP:LISTEN -t >/dev/null 2>&1; then
            echo "   Force killing..."
            kill -9 $PORT_PID 2>/dev/null
        fi
        echo "✓ Port 8767 freed"
    fi
else
    echo "Found vision system process(es): $VISION_PIDS"

    for PID in $VISION_PIDS; do
        echo "  Stopping PID $PID..."
        kill $PID 2>/dev/null
    done

    sleep 2

    # Check if still running
    REMAINING=$(pgrep -f "simple_vision_feed.py")
    if [ ! -z "$REMAINING" ]; then
        echo "  Force killing remaining processes..."
        pkill -9 -f "simple_vision_feed.py"
    fi

    echo "✓ Vision system stopped"
fi

# Verify port is free
if lsof -Pi :8767 -sTCP:LISTEN -t >/dev/null 2>&1; then
    echo "❌ Port 8767 still in use"
    exit 1
else
    echo "✓ Port 8767 is free"
fi

echo ""
echo "Vision system stopped successfully"
