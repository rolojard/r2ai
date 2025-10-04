#!/bin/bash
"""
R2D2 Maestro Servo System Startup Script
=========================================

Comprehensive startup script for the complete R2D2 Pololu Maestro servo integration system.
Coordinates all components for seamless operation:

- Enhanced Maestro Controller with hardware detection
- Servo Dashboard Integration Service
- Dashboard Web Server with servo controls
- Real-time WebSocket communication
- Safety monitoring and emergency systems

Author: Expert Project Manager
Target: NVIDIA Orin Nano R2D2 Systems
Hardware: Pololu Maestro Mini 12-Channel USB Servo Controller
"""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Configuration
PROJECT_DIR="/home/rolo/r2ai"
LOG_DIR="$PROJECT_DIR/logs"
SERVO_LOG_FILE="$LOG_DIR/servo_system.log"
DASHBOARD_LOG_FILE="$LOG_DIR/dashboard_server.log"
INTEGRATION_LOG_FILE="$LOG_DIR/servo_integration.log"

# Service ports
SERVO_API_PORT=5000
SERVO_WEBSOCKET_PORT=8767
DASHBOARD_PORT=8765
DASHBOARD_WEBSOCKET_PORT=8766

# Process tracking
SERVO_INTEGRATION_PID=""
DASHBOARD_SERVER_PID=""

echo -e "${CYAN}🤖 R2D2 Maestro Servo System Startup${NC}"
echo -e "${CYAN}========================================${NC}"
echo
echo -e "${BLUE}Project Directory: ${PROJECT_DIR}${NC}"
echo -e "${BLUE}Log Directory: ${LOG_DIR}${NC}"
echo

# Create log directory
mkdir -p "$LOG_DIR"

# Function to check if port is in use
check_port() {
    local port=$1
    if netstat -tuln 2>/dev/null | grep -q ":$port "; then
        return 0  # Port is in use
    else
        return 1  # Port is free
    fi
}

# Function to kill process on port
kill_port() {
    local port=$1
    echo -e "${YELLOW}Checking for processes on port $port...${NC}"

    local pid=$(lsof -ti tcp:$port 2>/dev/null)
    if [ ! -z "$pid" ]; then
        echo -e "${YELLOW}Killing process $pid on port $port${NC}"
        kill -9 $pid 2>/dev/null
        sleep 1
    fi
}

# Function to check dependencies
check_dependencies() {
    echo -e "${BLUE}🔍 Checking dependencies...${NC}"

    # Check Python dependencies
    local python_deps=("flask" "flask-cors" "websockets" "serial" "psutil" "asyncio")
    local missing_deps=()

    for dep in "${python_deps[@]}"; do
        if ! python3 -c "import $dep" 2>/dev/null; then
            missing_deps+=("$dep")
        fi
    done

    if [ ${#missing_deps[@]} -gt 0 ]; then
        echo -e "${RED}❌ Missing Python dependencies: ${missing_deps[*]}${NC}"
        echo -e "${YELLOW}Installing missing dependencies...${NC}"
        pip3 install "${missing_deps[@]}"
    fi

    # Check Node.js dependencies
    if [ ! -d "$PROJECT_DIR/node_modules" ]; then
        echo -e "${YELLOW}Installing Node.js dependencies...${NC}"
        cd "$PROJECT_DIR"
        npm install ws axios
    fi

    # Check for required files
    local required_files=(
        "servo_dashboard_integration.py"
        "maestro_enhanced_controller.py"
        "pololu_maestro_controller.py"
        "r2d2_advanced_servo_dashboard.html"
        "dashboard-server.js"
    )

    for file in "${required_files[@]}"; do
        if [ ! -f "$PROJECT_DIR/$file" ]; then
            echo -e "${RED}❌ Missing required file: $file${NC}"
            exit 1
        fi
    done

    echo -e "${GREEN}✅ All dependencies checked${NC}"
}

# Function to detect Maestro hardware
detect_maestro() {
    echo -e "${BLUE}🔍 Detecting Pololu Maestro hardware...${NC}"

    # Check for USB serial devices
    local maestro_found=false

    # Look for common Maestro device paths
    for device in /dev/ttyACM* /dev/ttyUSB*; do
        if [ -e "$device" ]; then
            echo -e "${CYAN}Found potential device: $device${NC}"

            # Test if it's a Maestro by checking permissions and basic communication
            if [ -w "$device" ] && [ -r "$device" ]; then
                echo -e "${GREEN}✅ Device $device is accessible${NC}"
                maestro_found=true
                break
            fi
        fi
    done

    if [ "$maestro_found" = false ]; then
        echo -e "${YELLOW}⚠️  No Maestro hardware detected - will run in simulation mode${NC}"
    else
        echo -e "${GREEN}✅ Maestro hardware detected${NC}"
    fi
}

# Function to start servo integration service
start_servo_integration() {
    echo -e "${BLUE}🚀 Starting Servo Integration Service...${NC}"

    # Kill any existing processes on servo ports
    kill_port $SERVO_API_PORT
    kill_port $SERVO_WEBSOCKET_PORT

    cd "$PROJECT_DIR"

    # Start servo integration service
    python3 servo_dashboard_integration.py > "$INTEGRATION_LOG_FILE" 2>&1 &
    SERVO_INTEGRATION_PID=$!

    echo -e "${CYAN}Servo Integration PID: $SERVO_INTEGRATION_PID${NC}"

    # Wait for service to start
    echo -e "${YELLOW}Waiting for servo integration service to start...${NC}"
    sleep 3

    # Check if service is running
    if ps -p $SERVO_INTEGRATION_PID > /dev/null; then
        echo -e "${GREEN}✅ Servo Integration Service started successfully${NC}"
        echo -e "${CYAN}   - REST API: http://localhost:$SERVO_API_PORT${NC}"
        echo -e "${CYAN}   - WebSocket: ws://localhost:$SERVO_WEBSOCKET_PORT${NC}"
    else
        echo -e "${RED}❌ Servo Integration Service failed to start${NC}"
        echo -e "${YELLOW}Check log: $INTEGRATION_LOG_FILE${NC}"
        return 1
    fi
}

# Function to start dashboard server
start_dashboard_server() {
    echo -e "${BLUE}🌐 Starting Dashboard Server...${NC}"

    # Kill any existing processes on dashboard ports
    kill_port $DASHBOARD_PORT
    kill_port $DASHBOARD_WEBSOCKET_PORT

    cd "$PROJECT_DIR"

    # Start dashboard server
    node dashboard-server.js > "$DASHBOARD_LOG_FILE" 2>&1 &
    DASHBOARD_SERVER_PID=$!

    echo -e "${CYAN}Dashboard Server PID: $DASHBOARD_SERVER_PID${NC}"

    # Wait for server to start
    echo -e "${YELLOW}Waiting for dashboard server to start...${NC}"
    sleep 2

    # Check if server is running
    if ps -p $DASHBOARD_SERVER_PID > /dev/null; then
        echo -e "${GREEN}✅ Dashboard Server started successfully${NC}"
        echo -e "${CYAN}   - Web Interface: http://localhost:$DASHBOARD_PORT${NC}"
        echo -e "${CYAN}   - Servo Dashboard: http://localhost:$DASHBOARD_PORT/servo${NC}"
        echo -e "${CYAN}   - WebSocket: ws://localhost:$DASHBOARD_WEBSOCKET_PORT${NC}"
    else
        echo -e "${RED}❌ Dashboard Server failed to start${NC}"
        echo -e "${YELLOW}Check log: $DASHBOARD_LOG_FILE${NC}"
        return 1
    fi
}

# Function to verify system integration
verify_integration() {
    echo -e "${BLUE}🔬 Verifying system integration...${NC}"

    # Test servo API
    echo -e "${YELLOW}Testing servo API...${NC}"
    if curl -s "http://localhost:$SERVO_API_PORT/api/servo/status" > /dev/null; then
        echo -e "${GREEN}✅ Servo API responding${NC}"
    else
        echo -e "${RED}❌ Servo API not responding${NC}"
        return 1
    fi

    # Test dashboard
    echo -e "${YELLOW}Testing dashboard...${NC}"
    if curl -s "http://localhost:$DASHBOARD_PORT/" > /dev/null; then
        echo -e "${GREEN}✅ Dashboard responding${NC}"
    else
        echo -e "${RED}❌ Dashboard not responding${NC}"
        return 1
    fi

    echo -e "${GREEN}✅ System integration verified${NC}"
}

# Function to display system status
show_status() {
    echo
    echo -e "${PURPLE}═══════════════════════════════════════${NC}"
    echo -e "${PURPLE}🎯 R2D2 Maestro Servo System Status${NC}"
    echo -e "${PURPLE}═══════════════════════════════════════${NC}"
    echo
    echo -e "${CYAN}🔧 Services Running:${NC}"
    echo -e "   Servo Integration: PID $SERVO_INTEGRATION_PID"
    echo -e "   Dashboard Server:  PID $DASHBOARD_SERVER_PID"
    echo
    echo -e "${CYAN}🌐 Access Points:${NC}"
    echo -e "   Main Dashboard:    http://localhost:$DASHBOARD_PORT/"
    echo -e "   Servo Dashboard:   http://localhost:$DASHBOARD_PORT/servo"
    echo -e "   Enhanced Dashboard: http://localhost:$DASHBOARD_PORT/enhanced"
    echo -e "   Vision Dashboard:  http://localhost:$DASHBOARD_PORT/vision"
    echo
    echo -e "${CYAN}🔌 API Endpoints:${NC}"
    echo -e "   Servo API:         http://localhost:$SERVO_API_PORT/api/servo/"
    echo -e "   WebSocket (Servo): ws://localhost:$SERVO_WEBSOCKET_PORT"
    echo -e "   WebSocket (Dashboard): ws://localhost:$DASHBOARD_WEBSOCKET_PORT"
    echo
    echo -e "${CYAN}📊 Logs:${NC}"
    echo -e "   Servo Integration: $INTEGRATION_LOG_FILE"
    echo -e "   Dashboard Server:  $DASHBOARD_LOG_FILE"
    echo -e "   System Log:        $SERVO_LOG_FILE"
    echo
    echo -e "${GREEN}✅ R2D2 Maestro Servo System is ready!${NC}"
    echo -e "${YELLOW}Press Ctrl+C to stop all services${NC}"
    echo
}

# Function to cleanup on exit
cleanup() {
    echo
    echo -e "${YELLOW}🛑 Shutting down R2D2 Maestro Servo System...${NC}"

    # Kill servo integration service
    if [ ! -z "$SERVO_INTEGRATION_PID" ]; then
        echo -e "${YELLOW}Stopping Servo Integration Service (PID: $SERVO_INTEGRATION_PID)${NC}"
        kill $SERVO_INTEGRATION_PID 2>/dev/null
    fi

    # Kill dashboard server
    if [ ! -z "$DASHBOARD_SERVER_PID" ]; then
        echo -e "${YELLOW}Stopping Dashboard Server (PID: $DASHBOARD_SERVER_PID)${NC}"
        kill $DASHBOARD_SERVER_PID 2>/dev/null
    fi

    # Kill any remaining processes on our ports
    kill_port $SERVO_API_PORT
    kill_port $SERVO_WEBSOCKET_PORT
    kill_port $DASHBOARD_PORT
    kill_port $DASHBOARD_WEBSOCKET_PORT

    echo -e "${GREEN}✅ All services stopped${NC}"
    echo -e "${CYAN}Thank you for using R2D2 Maestro Servo System!${NC}"
    exit 0
}

# Function to monitor services
monitor_services() {
    while true; do
        sleep 5

        # Check servo integration service
        if [ ! -z "$SERVO_INTEGRATION_PID" ] && ! ps -p $SERVO_INTEGRATION_PID > /dev/null; then
            echo -e "${RED}❌ Servo Integration Service crashed! Restarting...${NC}"
            start_servo_integration
        fi

        # Check dashboard server
        if [ ! -z "$DASHBOARD_SERVER_PID" ] && ! ps -p $DASHBOARD_SERVER_PID > /dev/null; then
            echo -e "${RED}❌ Dashboard Server crashed! Restarting...${NC}"
            start_dashboard_server
        fi
    done
}

# Set up signal handlers
trap cleanup SIGINT SIGTERM

# Main execution flow
main() {
    echo -e "${CYAN}Starting R2D2 Maestro Servo System...${NC}"
    echo

    # Change to project directory
    cd "$PROJECT_DIR" || {
        echo -e "${RED}❌ Cannot access project directory: $PROJECT_DIR${NC}"
        exit 1
    }

    # Check dependencies
    check_dependencies
    echo

    # Detect hardware
    detect_maestro
    echo

    # Start services
    if start_servo_integration; then
        echo
        if start_dashboard_server; then
            echo
            if verify_integration; then
                show_status

                # Start monitoring in background
                monitor_services &

                # Wait for interrupt
                while true; do
                    sleep 1
                done
            else
                echo -e "${RED}❌ System integration verification failed${NC}"
                cleanup
                exit 1
            fi
        else
            echo -e "${RED}❌ Dashboard server startup failed${NC}"
            cleanup
            exit 1
        fi
    else
        echo -e "${RED}❌ Servo integration service startup failed${NC}"
        cleanup
        exit 1
    fi
}

# Check if script is being sourced or executed
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi