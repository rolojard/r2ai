#!/bin/bash
# R2D2 Dashboard Startup Script with increased memory allocation

# Kill any existing dashboard servers
pkill -f "dashboard-server.js" 2>/dev/null

# Set Node.js heap size to 4GB (adjust as needed)
export NODE_OPTIONS="--max-old-space-size=4096"

echo "🎯 Starting R2AI Dashboard Server..."
echo "📍 Dashboard will be available at: http://localhost:8765"
echo "🔌 WebSocket on port: 8766"
echo ""

# Start the dashboard server
node dashboard-server.js