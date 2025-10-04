#!/bin/bash
# R2D2 Enhanced Servo Control System Startup Script
# Production-Ready System Launch with Comprehensive Monitoring

set -e  # Exit on any error

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_DIR="${SCRIPT_DIR}/logs"
SERVO_API_PORT=5000
DASHBOARD_PORT=8765
WEBSOCKET_PORT=8767

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging function
log() {
    echo -e "${GREEN}[$(date '+%Y-%m-%d %H:%M:%S')]${NC} $1"
}

warn() {
    echo -e "${YELLOW}[$(date '+%Y-%m-%d %H:%M:%S')] WARNING:${NC} $1"
}

error() {
    echo -e "${RED}[$(date '+%Y-%m-%d %H:%M:%S')] ERROR:${NC} $1"
}

# Create log directory
mkdir -p "${LOG_DIR}"

# Function to check if port is available
check_port() {
    local port=$1
    if netstat -tuln | grep -q ":${port} "; then
        return 1  # Port is in use
    else
        return 0  # Port is available
    fi
}

# Function to wait for service to be ready
wait_for_service() {
    local url=$1
    local timeout=${2:-30}
    local counter=0

    log "Waiting for service at ${url}..."

    while [ $counter -lt $timeout ]; do
        if curl -s -f "${url}" > /dev/null 2>&1; then
            log "Service at ${url} is ready!"
            return 0
        fi

        sleep 1
        counter=$((counter + 1))
    done

    error "Service at ${url} failed to start within ${timeout} seconds"
    return 1
}

# Function to cleanup processes
cleanup() {
    log "Cleaning up processes..."

    # Kill background processes
    jobs -p | xargs -r kill

    # Kill any remaining servo processes
    pkill -f "r2d2_servo_api_server" || true
    pkill -f "dashboard-server" || true

    log "Cleanup complete"
    exit 0
}

# Set up signal handlers
trap cleanup SIGINT SIGTERM

# Check system requirements
log "🔍 Checking system requirements..."

# Check Python dependencies
python_deps=("fastapi" "uvicorn" "websockets" "pyserial" "psutil")
for dep in "${python_deps[@]}"; do
    if ! python3 -c "import ${dep}" 2>/dev/null; then
        warn "Python dependency ${dep} not found, attempting to install..."
        pip3 install "${dep}" || {
            error "Failed to install ${dep}"
            exit 1
        }
    fi
done

# Check Node.js dependencies
if ! command -v node >/dev/null 2>&1; then
    error "Node.js not found. Please install Node.js first."
    exit 1
fi

# Check for required files
required_files=(
    "r2d2_servo_api_server.py"
    "r2d2_servo_backend.py"
    "maestro_enhanced_controller.py"
    "pololu_maestro_controller.py"
    "dashboard-server.js"
)

for file in "${required_files[@]}"; do
    if [ ! -f "${SCRIPT_DIR}/${file}" ]; then
        error "Required file ${file} not found"
        exit 1
    fi
done

log "✅ System requirements check passed"

# Check port availability
log "🔍 Checking port availability..."

if ! check_port $SERVO_API_PORT; then
    error "Port ${SERVO_API_PORT} is already in use"
    exit 1
fi

if ! check_port $DASHBOARD_PORT; then
    error "Port ${DASHBOARD_PORT} is already in use"
    exit 1
fi

if ! check_port $WEBSOCKET_PORT; then
    warn "Port ${WEBSOCKET_PORT} is already in use, servo WebSocket may conflict"
fi

log "✅ Port availability check passed"

# Detect hardware
log "🔍 Detecting Pololu Maestro hardware..."

if [ -c /dev/ttyACM0 ]; then
    log "✅ Maestro detected at /dev/ttyACM0"
    HARDWARE_MODE="real"
elif [ -c /dev/ttyUSB0 ]; then
    log "✅ Maestro detected at /dev/ttyUSB0"
    HARDWARE_MODE="real"
else
    warn "No Maestro hardware detected, running in simulation mode"
    HARDWARE_MODE="simulation"
fi

# Start services
log "🚀 Starting R2D2 Enhanced Servo Control System..."

# Start the servo API server
log "Starting Servo API Server on port ${SERVO_API_PORT}..."
python3 "${SCRIPT_DIR}/r2d2_servo_api_server.py" > "${LOG_DIR}/servo_api.log" 2>&1 &
SERVO_API_PID=$!

# Wait for API server to be ready
if ! wait_for_service "http://localhost:${SERVO_API_PORT}/health" 60; then
    error "Servo API server failed to start"
    kill $SERVO_API_PID 2>/dev/null || true
    exit 1
fi

log "✅ Servo API Server running (PID: ${SERVO_API_PID})"

# Start the dashboard server
log "Starting Dashboard Server on port ${DASHBOARD_PORT}..."
cd "${SCRIPT_DIR}"
node dashboard-server.js > "${LOG_DIR}/dashboard.log" 2>&1 &
DASHBOARD_PID=$!

# Wait for dashboard server to be ready
if ! wait_for_service "http://localhost:${DASHBOARD_PORT}" 30; then
    error "Dashboard server failed to start"
    kill $SERVO_API_PID $DASHBOARD_PID 2>/dev/null || true
    exit 1
fi

log "✅ Dashboard Server running (PID: ${DASHBOARD_PID})"

# Display system status
log "🎯 R2D2 Enhanced Servo Control System is READY!"
echo
echo "===================== SYSTEM STATUS ====================="
echo -e "${GREEN}Servo API Server:${NC}     http://localhost:${SERVO_API_PORT}"
echo -e "${GREEN}API Documentation:${NC}    http://localhost:${SERVO_API_PORT}/docs"
echo -e "${GREEN}Dashboard:${NC}            http://localhost:${DASHBOARD_PORT}"
echo -e "${GREEN}Advanced Dashboard:${NC}   http://localhost:${DASHBOARD_PORT}/servo"
echo -e "${GREEN}WebSocket Endpoint:${NC}   ws://localhost:${WEBSOCKET_PORT}"
echo -e "${GREEN}Hardware Mode:${NC}        ${HARDWARE_MODE}"
echo -e "${GREEN}Log Directory:${NC}        ${LOG_DIR}"
echo "======================================================"
echo

# Monitor services
log "📊 Monitoring services (Press Ctrl+C to stop)..."

# Function to check if process is still running
check_process() {
    local pid=$1
    local name=$2

    if ! kill -0 $pid 2>/dev/null; then
        error "${name} process (PID: ${pid}) has died"
        return 1
    fi
    return 0
}

# Monitoring loop
while true; do
    sleep 5

    # Check servo API server
    if ! check_process $SERVO_API_PID "Servo API Server"; then
        error "Servo API Server failed, restarting..."
        python3 "${SCRIPT_DIR}/r2d2_servo_api_server.py" > "${LOG_DIR}/servo_api.log" 2>&1 &
        SERVO_API_PID=$!
        log "Servo API Server restarted (PID: ${SERVO_API_PID})"
    fi

    # Check dashboard server
    if ! check_process $DASHBOARD_PID "Dashboard Server"; then
        error "Dashboard Server failed, restarting..."
        cd "${SCRIPT_DIR}"
        node dashboard-server.js > "${LOG_DIR}/dashboard.log" 2>&1 &
        DASHBOARD_PID=$!
        log "Dashboard Server restarted (PID: ${DASHBOARD_PID})"
    fi

    # Check API health
    if ! curl -s -f "http://localhost:${SERVO_API_PORT}/health" > /dev/null 2>&1; then
        warn "Servo API health check failed"
    fi

    # Optional: Display brief status every minute
    if [ $(($(date +%s) % 60)) -eq 0 ]; then
        echo -ne "\r${GREEN}[$(date '+%H:%M:%S')]${NC} Services running... API: ✅ Dashboard: ✅"
    fi
done