#!/bin/bash
# R2D2 Complete Dashboard System Startup
# Starts vision system + dashboard server + WCB API

echo "🤖 Starting Complete R2D2 Dashboard System..."
echo "=============================================="
echo ""

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

cd /home/rolo/r2ai

# Step 1: Start Vision System
echo "Step 1: Starting Vision System (port 8767)..."
if ./start_vision_system.sh; then
    echo -e "${GREEN}✓ Vision system started${NC}"
else
    echo -e "${YELLOW}⚠ Vision system startup had issues (check vision_system.log)${NC}"
    echo "  Continuing anyway..."
fi
echo ""

# Wait for vision to initialize
sleep 2

# Step 2: Start Dashboard Server
echo "Step 2: Starting Dashboard Server (ports 8765, 8766, 8768)..."
if ./start_dashboard.sh; then
    echo -e "${GREEN}✓ Dashboard server started${NC}"
else
    echo -e "${RED}✗ Dashboard server failed to start${NC}"
    echo "  Stopping vision system..."
    ./stop_vision_system.sh
    exit 1
fi
echo ""

# Step 3: Check WCB API (optional - don't fail if not running)
echo "Step 3: Checking WCB API (port 8770)..."
if curl -s http://localhost:8770/ > /dev/null 2>&1; then
    echo -e "${GREEN}✓ WCB API is running${NC}"
else
    echo -e "${YELLOW}⚠ WCB API not running (optional)${NC}"
    echo "  To start: python3 wcb_dashboard_api.py &"
fi
echo ""

echo "=============================================="
echo -e "${GREEN}🎉 Complete Dashboard System Started!${NC}"
echo ""
echo "📊 Available Services:"
echo "  • Vision Feed: ws://localhost:8767"
echo "  • Dashboard Server: http://localhost:8765"
echo "  • WebSocket: ws://localhost:8766"
echo "  • Behavioral WS: ws://localhost:8768"
if curl -s http://localhost:8770/ > /dev/null 2>&1; then
    echo "  • WCB API: http://localhost:8770"
fi
echo ""
echo "🌐 Dashboards:"
echo "  • Main: http://localhost:8765/"
echo "  • Enhanced: http://localhost:8765/enhanced"
echo "  • WCB Mood: file:///home/rolo/r2ai/r2d2_wcb_mood_dashboard.html"
echo ""
echo "📋 Logs:"
echo "  • Vision: tail -f vision_system.log"
echo "  • Dashboard: tail -f dashboard.log"
echo ""
echo "🛑 To stop all:"
echo "  ./stop_complete_dashboard_system.sh"
echo ""
