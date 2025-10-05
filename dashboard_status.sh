#!/bin/bash
# R2D2 Dashboard - Status Check Script
# Shows current status of dashboard server and ports

echo "📊 R2D2 Dashboard Status Report"
echo "======================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to check if port is in use
check_port() {
    local port=$1
    if lsof -i :$port >/dev/null 2>&1; then
        return 0  # Port in use
    else
        return 1  # Port free
    fi
}

# Check dashboard processes
echo -e "\n${BLUE}Dashboard Processes:${NC}"
NODE_PIDS=$(pgrep -f "node.*dashboard-server.js" 2>/dev/null)

if [ -n "$NODE_PIDS" ]; then
    echo -e "${GREEN}Status: RUNNING${NC}"
    echo ""
    for pid in $NODE_PIDS; do
        # Get process details
        RUNTIME=$(ps -p $pid -o etime= 2>/dev/null | tr -d ' ')
        MEM=$(ps -p $pid -o %mem= 2>/dev/null | tr -d ' ')
        CPU=$(ps -p $pid -o %cpu= 2>/dev/null | tr -d ' ')

        echo "  PID: $pid"
        echo "  Runtime: $RUNTIME"
        echo "  CPU: ${CPU}%"
        echo "  Memory: ${MEM}%"
        echo ""
    done
else
    echo -e "${RED}Status: NOT RUNNING${NC}"
    echo ""
fi

# Check port status
echo -e "${BLUE}Port Status:${NC}"
PORTS=(8765 8766 8768)
PORT_NAMES=("HTTP Server" "WebSocket" "Behavioral WS")

for i in "${!PORTS[@]}"; do
    port="${PORTS[$i]}"
    name="${PORT_NAMES[$i]}"

    if check_port $port; then
        echo -e "${GREEN}  Port $port ($name): IN USE${NC}"

        # Show process using the port
        PID=$(lsof -ti :$port 2>/dev/null)
        if [ -n "$PID" ]; then
            CMD=$(ps -p $PID -o comm= 2>/dev/null)
            echo "    Process: PID $PID ($CMD)"
        fi
    else
        echo -e "${YELLOW}  Port $port ($name): FREE${NC}"
    fi
done

# Check log file
echo -e "\n${BLUE}Log File:${NC}"
LOG_FILE="/home/rolo/r2ai/dashboard.log"

if [ -f "$LOG_FILE" ]; then
    LOG_SIZE=$(du -h "$LOG_FILE" | cut -f1)
    LOG_LINES=$(wc -l < "$LOG_FILE")
    LOG_MODIFIED=$(stat -c %y "$LOG_FILE" | cut -d'.' -f1)

    echo "  Location: $LOG_FILE"
    echo "  Size: $LOG_SIZE"
    echo "  Lines: $LOG_LINES"
    echo "  Last Modified: $LOG_MODIFIED"
    echo ""
    echo "  Recent log entries (last 5 lines):"
    tail -5 "$LOG_FILE" 2>/dev/null | sed 's/^/    /'
else
    echo -e "${YELLOW}  No log file found${NC}"
fi

# Network connectivity test
echo -e "\n${BLUE}Network Connectivity:${NC}"
if curl -s --max-time 2 http://localhost:8765 > /dev/null 2>&1; then
    echo -e "${GREEN}  HTTP Server (8765): ACCESSIBLE${NC}"
else
    echo -e "${RED}  HTTP Server (8765): NOT ACCESSIBLE${NC}"
fi

# System resource summary
echo -e "\n${BLUE}System Resources:${NC}"
TOTAL_MEM=$(free -m | awk 'NR==2{printf "%.0f", $2}')
USED_MEM=$(free -m | awk 'NR==2{printf "%.0f", $3}')
MEM_PERCENT=$(awk "BEGIN {printf \"%.1f\", ($USED_MEM/$TOTAL_MEM)*100}")

CPU_LOAD=$(uptime | awk -F'load average:' '{ print $2 }' | awk '{ print $1 }' | tr -d ',')

echo "  CPU Load (1m): $CPU_LOAD"
echo "  Memory Used: ${USED_MEM}MB / ${TOTAL_MEM}MB (${MEM_PERCENT}%)"

echo ""
echo "======================================="

# Provide helpful commands
echo -e "\n${BLUE}Quick Commands:${NC}"
if [ -n "$NODE_PIDS" ]; then
    echo "  Stop Dashboard:    ./stop_dashboard.sh"
    echo "  Restart Dashboard: ./restart_dashboard.sh"
    echo "  View Logs:         tail -f /home/rolo/r2ai/dashboard.log"
else
    echo "  Start Dashboard:   ./start_dashboard.sh"
fi
echo ""
