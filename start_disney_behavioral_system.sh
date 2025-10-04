#!/bin/bash

# R2D2 Disney Behavioral Intelligence System Startup Script
# Phase 4A: Advanced Character AI Implementation
#
# This script launches the complete Disney-level behavioral intelligence
# system with all integrated components for authentic R2D2 character experience.

echo "🎭 R2D2 Disney Behavioral Intelligence System"
echo "=============================================="
echo "Phase 4A: Advanced Character AI Implementation"
echo "Starting Disney-level character intelligence..."
echo ""

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[0;33m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Configuration
PROJECT_DIR="/home/rolo/r2ai"
LOG_DIR="$PROJECT_DIR/logs"
PID_DIR="$PROJECT_DIR/pids"

# Create necessary directories
mkdir -p "$LOG_DIR"
mkdir -p "$PID_DIR"

# Function to check if a port is available
check_port() {
    local port=$1
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null ; then
        return 1
    else
        return 0
    fi
}

# Function to start a service with proper logging
start_service() {
    local service_name="$1"
    local command="$2"
    local log_file="$LOG_DIR/${service_name}.log"
    local pid_file="$PID_DIR/${service_name}.pid"

    echo -e "${BLUE}🚀 Starting $service_name...${NC}"

    # Remove old PID file if exists
    if [ -f "$pid_file" ]; then
        rm "$pid_file"
    fi

    # Start service in background
    nohup $command > "$log_file" 2>&1 &
    local pid=$!

    # Save PID
    echo $pid > "$pid_file"

    # Check if service started successfully
    sleep 2
    if ps -p $pid > /dev/null; then
        echo -e "${GREEN}✅ $service_name started successfully (PID: $pid)${NC}"
        echo "   Log: $log_file"
        return 0
    else
        echo -e "${RED}❌ Failed to start $service_name${NC}"
        echo "   Check log: $log_file"
        return 1
    fi
}

# Function to stop all services
cleanup() {
    echo ""
    echo -e "${YELLOW}🛑 Stopping all Disney Behavioral Intelligence services...${NC}"

    # Stop all services by PID
    for pid_file in "$PID_DIR"/*.pid; do
        if [ -f "$pid_file" ]; then
            local pid=$(cat "$pid_file")
            local service_name=$(basename "$pid_file" .pid)

            if ps -p $pid > /dev/null; then
                echo -e "${CYAN}Stopping $service_name (PID: $pid)...${NC}"
                kill -TERM $pid

                # Wait for graceful shutdown
                local count=0
                while ps -p $pid > /dev/null && [ $count -lt 10 ]; do
                    sleep 1
                    count=$((count + 1))
                done

                # Force kill if still running
                if ps -p $pid > /dev/null; then
                    echo -e "${YELLOW}Force killing $service_name...${NC}"
                    kill -KILL $pid
                fi

                echo -e "${GREEN}✅ $service_name stopped${NC}"
            fi

            rm "$pid_file"
        fi
    done

    echo -e "${GREEN}🏁 All services stopped successfully${NC}"
    exit 0
}

# Set up signal handlers for graceful shutdown
trap cleanup SIGINT SIGTERM

# System pre-checks
echo -e "${PURPLE}🔍 Performing system pre-checks...${NC}"

# Check Python environment
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python3 not found. Please install Python3.${NC}"
    exit 1
fi

# Check Node.js environment
if ! command -v node &> /dev/null; then
    echo -e "${RED}❌ Node.js not found. Please install Node.js.${NC}"
    exit 1
fi

# Check required Python packages
echo -e "${CYAN}Checking Python dependencies...${NC}"
python3 -c "
import sys
required_packages = ['websockets', 'asyncio', 'numpy', 'logging']
missing_packages = []

for package in required_packages:
    try:
        __import__(package)
    except ImportError:
        missing_packages.append(package)

if missing_packages:
    print('Missing packages:', ', '.join(missing_packages))
    sys.exit(1)
else:
    print('✅ All required Python packages available')
"

if [ $? -ne 0 ]; then
    echo -e "${RED}❌ Missing required Python packages${NC}"
    echo "Install with: pip3 install websockets numpy asyncio logging"
    exit 1
fi

# Check port availability
echo -e "${CYAN}Checking port availability...${NC}"

required_ports=(8765 8766 8767 8768 5000)
for port in "${required_ports[@]}"; do
    if ! check_port $port; then
        echo -e "${RED}❌ Port $port is already in use${NC}"
        echo "Please stop services using this port or change configuration"
        exit 1
    fi
done

echo -e "${GREEN}✅ All required ports available${NC}"

# Check hardware connections
echo -e "${CYAN}Checking hardware connections...${NC}"

# Check for Pololu Maestro controller
if [ -e /dev/ttyACM* ]; then
    echo -e "${GREEN}✅ Servo controller detected at $(ls /dev/ttyACM* | head -1)${NC}"
else
    echo -e "${YELLOW}⚠️ No servo controller detected - running in simulation mode${NC}"
fi

# Check for camera
if [ -e /dev/video* ]; then
    echo -e "${GREEN}✅ Camera detected at $(ls /dev/video* | head -1)${NC}"
else
    echo -e "${YELLOW}⚠️ No camera detected - vision system will use simulation${NC}"
fi

echo ""
echo -e "${GREEN}🎯 Pre-checks completed successfully!${NC}"
echo ""

# Start core services
echo -e "${PURPLE}🌟 Starting Disney Behavioral Intelligence Core Services...${NC}"
echo ""

# 1. Start Dashboard Server (with Behavioral Intelligence WebSocket)
if start_service "dashboard_server" "cd $PROJECT_DIR && node dashboard-server.js"; then
    echo -e "${CYAN}   Dashboard available at: http://localhost:8765${NC}"
    echo -e "${CYAN}   Disney Behavioral Dashboard: http://localhost:8765/disney${NC}"
    echo -e "${CYAN}   Enhanced Dashboard: http://localhost:8765/enhanced${NC}"
    echo -e "${CYAN}   Vision Dashboard: http://localhost:8765/vision${NC}"
else
    echo -e "${RED}❌ Failed to start Dashboard Server - aborting${NC}"
    exit 1
fi

echo ""

# 2. Start Vision System (if not already running)
if ! check_port 8767; then
    echo -e "${YELLOW}⚠️ Vision system already running on port 8767${NC}"
else
    echo -e "${CYAN}Starting Vision System...${NC}"
    if start_service "vision_system" "cd $PROJECT_DIR && python3 r2d2_realtime_vision.py"; then
        echo -e "${CYAN}   Vision WebSocket: ws://localhost:8767${NC}"
    else
        echo -e "${YELLOW}⚠️ Vision system failed to start - continuing without vision${NC}"
    fi
fi

echo ""

# 3. Start Disney Behavioral Intelligence Engine
sleep 3
echo -e "${PURPLE}🎭 Starting Disney Behavioral Intelligence Engine...${NC}"
if start_service "disney_behavioral_intelligence" "cd $PROJECT_DIR && python3 r2d2_disney_behavioral_intelligence.py"; then
    echo -e "${CYAN}   Behavioral Intelligence WebSocket: ws://localhost:8768${NC}"
    echo -e "${CYAN}   Personality States: 24 authentic R2D2 states${NC}"
    echo -e "${CYAN}   Behavior Library: 50+ Disney-quality sequences${NC}"
    echo -e "${CYAN}   Motion Choreography: Advanced servo coordination${NC}"
else
    echo -e "${RED}❌ Failed to start Disney Behavioral Intelligence - aborting${NC}"
    cleanup
    exit 1
fi

echo ""

# 4. Start Servo Backend (if available)
if [ -e /dev/ttyACM* ]; then
    echo -e "${CYAN}Starting Servo Control Backend...${NC}"
    if start_service "servo_backend" "cd $PROJECT_DIR && python3 r2d2_servo_backend.py"; then
        echo -e "${CYAN}   Servo API: http://localhost:5000/api${NC}"
        echo -e "${CYAN}   Servo WebSocket: ws://localhost:5000${NC}"
    else
        echo -e "${YELLOW}⚠️ Servo backend failed - using simulation mode${NC}"
    fi
else
    echo -e "${YELLOW}⚠️ No servo controller detected - skipping servo backend${NC}"
fi

echo ""
echo -e "${GREEN}🎉 Disney Behavioral Intelligence System Started Successfully!${NC}"
echo "================================================================"
echo ""
echo -e "${PURPLE}🎭 DISNEY R2D2 CHARACTER AI - PHASE 4A ACTIVE${NC}"
echo ""
echo -e "${CYAN}📊 System Access Points:${NC}"
echo -e "   • Main Dashboard:      http://localhost:8765"
echo -e "   • Disney Behavioral:   http://localhost:8765/disney"
echo -e "   • Enhanced Control:    http://localhost:8765/enhanced"
echo -e "   • Vision Monitor:      http://localhost:8765/vision"
echo ""
echo -e "${CYAN}🔗 WebSocket Endpoints:${NC}"
echo -e "   • Dashboard WS:        ws://localhost:8766"
echo -e "   • Vision WS:           ws://localhost:8767"
echo -e "   • Behavioral AI WS:    ws://localhost:8768"
echo -e "   • Servo Control WS:    ws://localhost:5000"
echo ""
echo -e "${CYAN}🎭 Character Features:${NC}"
echo -e "   • Personality States:   24 authentic emotional states"
echo -e "   • Behavior Library:     50+ Disney-quality sequences"
echo -e "   • Motion Choreography:  Natural servo coordination"
echo -e "   • Environmental AI:     Real-time context awareness"
echo -e "   • Character Recognition: Jedi, Sith, Droids detection"
echo -e "   • Convention Ready:     Crowd interaction modes"
echo ""
echo -e "${CYAN}📁 Log Files:${NC}"
echo -e "   • Dashboard:           $LOG_DIR/dashboard_server.log"
echo -e "   • Disney Behavioral:   $LOG_DIR/disney_behavioral_intelligence.log"
echo -e "   • Vision System:       $LOG_DIR/vision_system.log"
echo -e "   • Servo Backend:       $LOG_DIR/servo_backend.log"
echo ""
echo -e "${YELLOW}🎮 Ready for Disney-Level R2D2 Character Interaction!${NC}"
echo ""
echo -e "${GREEN}Press Ctrl+C to stop all services gracefully${NC}"
echo "================================================================"

# Keep script running and monitor services
while true; do
    # Check if any core services have died
    core_services=("dashboard_server" "disney_behavioral_intelligence")

    for service in "${core_services[@]}"; do
        pid_file="$PID_DIR/${service}.pid"
        if [ -f "$pid_file" ]; then
            pid=$(cat "$pid_file")
            if ! ps -p $pid > /dev/null; then
                echo -e "${RED}❌ Critical service $service has stopped unexpectedly${NC}"
                echo -e "${YELLOW}🔄 Attempting to restart...${NC}"

                # Restart the service
                case $service in
                    "dashboard_server")
                        start_service "dashboard_server" "cd $PROJECT_DIR && node dashboard-server.js"
                        ;;
                    "disney_behavioral_intelligence")
                        start_service "disney_behavioral_intelligence" "cd $PROJECT_DIR && python3 r2d2_disney_behavioral_intelligence.py"
                        ;;
                esac
            fi
        fi
    done

    sleep 30  # Check every 30 seconds
done