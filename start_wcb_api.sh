#!/bin/bash
# WCB Dashboard API - Startup Script
# Production server launcher with configuration options

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}=========================================="
echo "WCB Dashboard API - Startup"
echo "==========================================${NC}"
echo ""

# Check if Python virtual environment exists
if [ -d "venv" ]; then
    echo -e "${GREEN}Activating virtual environment...${NC}"
    source venv/bin/activate
elif [ -d ".venv" ]; then
    echo -e "${GREEN}Activating virtual environment...${NC}"
    source .venv/bin/activate
else
    echo -e "${YELLOW}Warning: No virtual environment found${NC}"
    echo "Consider creating one: python3 -m venv venv"
fi

# Check Python dependencies
echo -e "${BLUE}Checking dependencies...${NC}"
DEPS_MISSING=0

python3 -c "import fastapi" 2>/dev/null || { echo -e "${RED}✗ fastapi not installed${NC}"; DEPS_MISSING=1; }
python3 -c "import uvicorn" 2>/dev/null || { echo -e "${RED}✗ uvicorn not installed${NC}"; DEPS_MISSING=1; }
python3 -c "import pydantic" 2>/dev/null || { echo -e "${RED}✗ pydantic not installed${NC}"; DEPS_MISSING=1; }
python3 -c "import serial" 2>/dev/null || { echo -e "${YELLOW}⚠ pyserial not installed (OK for simulation mode)${NC}"; }

if [ $DEPS_MISSING -eq 1 ]; then
    echo ""
    echo -e "${RED}Missing required dependencies!${NC}"
    echo "Install with: pip install fastapi uvicorn pydantic pyserial"
    exit 1
fi

echo -e "${GREEN}✓ All required dependencies found${NC}"
echo ""

# Configuration options
PORT=${WCB_API_PORT:-8770}
HOST=${WCB_API_HOST:-0.0.0.0}
MODE=${WCB_MODE:-simulation}
RELOAD=${WCB_RELOAD:-false}

echo -e "${BLUE}Configuration:${NC}"
echo "  Host: $HOST"
echo "  Port: $PORT"
echo "  Mode: $MODE"
echo "  Reload: $RELOAD"
echo ""

# Check if port is already in use
if lsof -Pi :$PORT -sTCP:LISTEN -t >/dev/null 2>&1 ; then
    echo -e "${RED}Error: Port $PORT is already in use!${NC}"
    echo "Kill existing process or use different port:"
    echo "  WCB_API_PORT=8771 $0"
    exit 1
fi

echo -e "${GREEN}Starting WCB Dashboard API...${NC}"
echo ""
echo -e "${YELLOW}Access points:${NC}"
echo "  API Root:       http://$HOST:$PORT/"
echo "  Documentation:  http://$HOST:$PORT/docs"
echo "  ReDoc:          http://$HOST:$PORT/redoc"
echo "  OpenAPI Schema: http://$HOST:$PORT/openapi.json"
echo ""
echo -e "${YELLOW}Press Ctrl+C to stop${NC}"
echo "=========================================="
echo ""

# Start the server
if [ "$RELOAD" = "true" ]; then
    python3 -m uvicorn wcb_dashboard_api:app \
        --host $HOST \
        --port $PORT \
        --reload \
        --log-level info
else
    python3 -m uvicorn wcb_dashboard_api:app \
        --host $HOST \
        --port $PORT \
        --log-level info
fi
