#!/bin/bash
# R2D2 Dashboard - Safe Restart Script
# Stops existing dashboard and starts a fresh instance

echo "🔄 Restarting R2D2 Dashboard Server..."
echo "======================================="

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Stop existing dashboard
echo -e "${YELLOW}Phase 1: Stopping existing dashboard...${NC}"
"$SCRIPT_DIR/stop_dashboard.sh"
STOP_RESULT=$?

if [ $STOP_RESULT -ne 0 ]; then
    echo "Warning: Stop script reported issues, but continuing..."
fi

# Wait a moment for cleanup
sleep 2

# Start fresh dashboard
echo -e "\n${YELLOW}Phase 2: Starting fresh dashboard...${NC}"
"$SCRIPT_DIR/start_dashboard.sh"
START_RESULT=$?

echo ""
echo "======================================="
if [ $START_RESULT -eq 0 ]; then
    echo -e "${GREEN}✅ Dashboard restart complete!${NC}"
    exit 0
else
    echo -e "${RED}❌ Dashboard restart failed${NC}"
    echo "Check the logs and try manual start"
    exit 1
fi
