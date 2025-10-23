#!/bin/bash
# Start Vision System for R2D2 Dashboards
# Launches GPU-Accelerated YOLO Vision System on port 8767

echo "🎥 Starting R2D2 GPU-Accelerated Vision System..."
echo "================================================="
echo "🚀 YOLOv8n Object Detection with CUDA Acceleration"
echo ""

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
if [ ! -f "r2d2_orin_nano_optimized_vision.py" ]; then
    echo "❌ Error: r2d2_orin_nano_optimized_vision.py not found"
    exit 1
fi

# Make executable
chmod +x r2d2_orin_nano_optimized_vision.py

# Start GPU-accelerated YOLO vision system in background
nohup python3 r2d2_orin_nano_optimized_vision.py 8767 > vision_system.log 2>&1 &
VISION_PID=$!

# Wait a moment for startup
sleep 2

# Check if it started successfully
if ps -p $VISION_PID > /dev/null; then
    echo "✅ GPU-Accelerated Vision System started successfully!"
    echo ""
    echo "   PID: $VISION_PID"
    echo "   WebSocket: ws://localhost:8767"
    echo "   Log: $(pwd)/vision_system.log"
    echo ""
    echo "🎯 YOLO Object Detection Features:"
    echo "   - Real-time bounding boxes on 80 object classes"
    echo "   - GPU-accelerated inference with CUDA"
    echo "   - 12-15 FPS with V4L2 hardware optimization"
    echo "   - Confidence threshold: 0.5 (50%)"
    echo ""
    echo "📹 Camera feed with YOLO detections now available"
    echo ""
    echo "To view logs: tail -f vision_system.log"
    echo "To stop: ./stop_vision_system.sh"
    echo "Dashboard: http://localhost:8765/enhanced"
else
    echo "❌ Failed to start vision system"
    echo "   Check vision_system.log for errors"
    exit 1
fi
