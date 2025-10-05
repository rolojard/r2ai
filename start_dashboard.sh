#!/bin/bash
# R2D2 Dashboard - Safe Start Script
# Checks for port conflicts and starts dashboard server

echo "🚀 Starting R2D2 Dashboard Server..."
echo "=================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Dashboard configuration
DASHBOARD_SCRIPT="/home/rolo/r2ai/dashboard-server.js"
PORTS=(8765 8766 8768)

# Function to check if port is in use
check_port() {
    local port=$1
    if lsof -i :$port >/dev/null 2>&1; then
        return 0  # Port in use
    else
        return 1  # Port free
    fi
}

# Function to check if dashboard is already running
check_dashboard_running() {
    if pgrep -f "node.*dashboard-server.js" >/dev/null 2>&1; then
        return 0  # Running
    else
        return 1  # Not running
    fi
}

# Check if dashboard is already running
echo -e "${YELLOW}Step 1: Checking for existing dashboard process...${NC}"
if check_dashboard_running; then
    echo -e "${RED}⚠️  Dashboard is already running!${NC}"
    echo ""
    echo "Current dashboard processes:"
    ps aux | grep "dashboard-server.js" | grep -v grep
    echo ""
    echo "To restart the dashboard:"
    echo "  1. Run: ./stop_dashboard.sh"
    echo "  2. Then: ./start_dashboard.sh"
    echo ""
    echo "Or use: ./restart_dashboard.sh"
    exit 1
fi
echo -e "${GREEN}  No existing dashboard process found${NC}"

# Check port availability
echo -e "\n${YELLOW}Step 2: Checking port availability...${NC}"
PORTS_AVAILABLE=true

for port in "${PORTS[@]}"; do
    if check_port $port; then
        echo -e "${RED}  Port $port: IN USE${NC}"
        PORTS_AVAILABLE=false

        # Show what's using the port
        PID=$(lsof -ti :$port 2>/dev/null)
        if [ -n "$PID" ]; then
            CMD=$(ps -p $PID -o comm= 2>/dev/null)
            echo -e "    Process: PID $PID ($CMD)"
        fi
    else
        echo -e "${GREEN}  Port $port: FREE${NC}"
    fi
done

if [ "$PORTS_AVAILABLE" = false ]; then
    echo -e "\n${RED}❌ Cannot start dashboard - ports in use${NC}"
    echo ""
    echo "Resolution:"
    echo "  Run: ./stop_dashboard.sh"
    echo "  Then try starting again"
    exit 1
fi

# Check if dashboard script exists
echo -e "\n${YELLOW}Step 3: Verifying dashboard script...${NC}"
if [ ! -f "$DASHBOARD_SCRIPT" ]; then
    echo -e "${RED}❌ Error: dashboard-server.js not found at $DASHBOARD_SCRIPT${NC}"
    exit 1
fi
echo -e "${GREEN}  Dashboard script found${NC}"

# Check for required Node modules
echo -e "\n${YELLOW}Step 4: Checking dependencies...${NC}"
if [ ! -d "/home/rolo/r2ai/node_modules" ]; then
    echo -e "${YELLOW}  Warning: node_modules not found${NC}"
    echo "  Installing dependencies..."
    npm install
fi
echo -e "${GREEN}  Dependencies OK${NC}"

# Start the dashboard
echo -e "\n${YELLOW}Step 5: Starting dashboard server...${NC}"
echo "  Command: node $DASHBOARD_SCRIPT"
echo ""

# Start in background and redirect output to log file
nohup node "$DASHBOARD_SCRIPT" > /home/rolo/r2ai/dashboard.log 2>&1 &
DASHBOARD_PID=$!

# Wait a moment for server to initialize
sleep 3

# Verify it started successfully
if ps -p $DASHBOARD_PID > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Dashboard started successfully!${NC}"
    echo ""
    echo "  PID: $DASHBOARD_PID"
    echo "  Log: /home/rolo/r2ai/dashboard.log"
    echo ""
    echo -e "${BLUE}📊 Available Dashboards:${NC}"
    echo "  • http://localhost:8765/ (Default - Vision Dashboard)"
    echo "  • http://localhost:8765/enhanced (Enhanced Dashboard)"
    echo "  • http://localhost:8765/servo (Servo Control Dashboard)"
    echo "  • http://localhost:8765/disney (Disney Behavioral Dashboard)"
    echo ""
    echo "  WebSocket Ports:"
    echo "  • 8766 (Real-time Data)"
    echo "  • 8768 (Behavioral Intelligence)"
    echo ""
    echo "To stop: ./stop_dashboard.sh"
    echo "To view logs: tail -f /home/rolo/r2ai/dashboard.log"
    exit 0
else
    echo -e "${RED}❌ Failed to start dashboard${NC}"
    echo ""
    echo "Check logs for errors:"
    echo "  cat /home/rolo/r2ai/dashboard.log"
    exit 1
fi
