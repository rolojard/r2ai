#!/bin/bash
# R2D2 Dashboard - Safe Stop Script
# Terminates all dashboard-related processes and frees ports

echo "🛑 Stopping R2D2 Dashboard Server..."
echo "=================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
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

# Function to kill processes on specific port
kill_port_process() {
    local port=$1
    local pids=$(lsof -ti :$port 2>/dev/null)

    if [ -n "$pids" ]; then
        echo -e "${YELLOW}Found process(es) on port $port: $pids${NC}"
        for pid in $pids; do
            local cmd=$(ps -p $pid -o comm= 2>/dev/null)
            echo "  Killing PID $pid ($cmd)..."
            kill -TERM $pid 2>/dev/null || kill -KILL $pid 2>/dev/null
            sleep 0.5
        done
        return 0
    else
        echo -e "  Port $port is already free"
        return 1
    fi
}

# Kill all node dashboard-server.js processes
echo -e "\n${YELLOW}Step 1: Stopping Node.js dashboard processes...${NC}"
NODE_PIDS=$(pgrep -f "node.*dashboard-server.js" 2>/dev/null)

if [ -n "$NODE_PIDS" ]; then
    echo "Found dashboard processes: $NODE_PIDS"
    for pid in $NODE_PIDS; do
        echo "  Terminating PID $pid..."
        kill -TERM $pid 2>/dev/null
    done

    # Wait for graceful shutdown
    sleep 2

    # Force kill if still running
    NODE_PIDS=$(pgrep -f "node.*dashboard-server.js" 2>/dev/null)
    if [ -n "$NODE_PIDS" ]; then
        echo -e "${RED}  Processes still running, force killing...${NC}"
        for pid in $NODE_PIDS; do
            kill -KILL $pid 2>/dev/null
        done
    fi
    echo -e "${GREEN}  Node dashboard processes stopped${NC}"
else
    echo "  No Node dashboard processes found"
fi

# Check and free specific ports
echo -e "\n${YELLOW}Step 2: Freeing dashboard ports...${NC}"
PORTS=(8765 8766 8768)
FREED_PORTS=0

for port in "${PORTS[@]}"; do
    echo -e "\nChecking port $port..."
    if kill_port_process $port; then
        FREED_PORTS=$((FREED_PORTS + 1))
    fi
done

# Wait for ports to be fully released
sleep 1

# Verify all ports are free
echo -e "\n${YELLOW}Step 3: Verifying port availability...${NC}"
ALL_CLEAR=true

for port in "${PORTS[@]}"; do
    if check_port $port; then
        echo -e "${RED}  Port $port: STILL IN USE${NC}"
        ALL_CLEAR=false
    else
        echo -e "${GREEN}  Port $port: FREE${NC}"
    fi
done

echo -e "\n=================================="
if [ "$ALL_CLEAR" = true ]; then
    echo -e "${GREEN}✅ Dashboard stopped successfully!${NC}"
    echo "All ports are free and ready for restart"
    exit 0
else
    echo -e "${RED}⚠️  Warning: Some ports still in use${NC}"
    echo "You may need to manually investigate remaining processes"
    echo ""
    echo "Check with: lsof -i :8765 -i :8766 -i :8768"
    exit 1
fi
