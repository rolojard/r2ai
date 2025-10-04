#!/bin/bash
# R2D2 Advanced Servo Control System Launcher
# Comprehensive production-ready servo control system startup

set -e

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_DIR="$SCRIPT_DIR/logs"
PID_DIR="$SCRIPT_DIR/pids"

# Create directories
mkdir -p "$LOG_DIR" "$PID_DIR"

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

error() {
    echo -e "${RED}[$(date '+%Y-%m-%d %H:%M:%S')] ERROR:${NC} $1" >&2
}

warning() {
    echo -e "${YELLOW}[$(date '+%Y-%m-%d %H:%M:%S')] WARNING:${NC} $1"
}

info() {
    echo -e "${BLUE}[$(date '+%Y-%m-%d %H:%M:%S')] INFO:${NC} $1"
}

# Check dependencies
check_dependencies() {
    log "🔍 Checking system dependencies..."

    # Check Python
    if ! command -v python3 &> /dev/null; then
        error "Python 3 is required but not installed"
        exit 1
    fi

    # Check Node.js
    if ! command -v node &> /dev/null; then
        error "Node.js is required but not installed"
        exit 1
    fi

    # Check required Python packages
    local python_packages=("flask" "flask-cors" "pyserial" "websockets")
    for package in "${python_packages[@]}"; do
        if ! python3 -c "import ${package//-/_}" 2>/dev/null; then
            warning "Python package '$package' not found. Installing..."
            pip3 install "$package" || {
                error "Failed to install $package"
                exit 1
            }
        fi
    done

    # Check required Node.js packages
    if [ ! -d "$SCRIPT_DIR/node_modules" ]; then
        warning "Node.js dependencies not found. Installing..."
        cd "$SCRIPT_DIR"
        npm install ws axios 2>/dev/null || {
            error "Failed to install Node.js dependencies"
            exit 1
        }
    fi

    info "✅ All dependencies satisfied"
}

# Check hardware
check_hardware() {
    log "🔌 Checking servo controller hardware..."

    # Check for Pololu Maestro
    if ls /dev/ttyACM* 2>/dev/null | grep -q .; then
        local maestro_port=$(ls /dev/ttyACM* | head -1)
        info "✅ Servo controller detected at $maestro_port"
        echo "$maestro_port" > "$PID_DIR/maestro_port.txt"
    else
        warning "⚠️  No servo controller detected. Running in simulation mode."
        echo "SIMULATION" > "$PID_DIR/maestro_port.txt"
    fi
}

# Stop any existing services
stop_services() {
    log "🛑 Stopping existing servo control services..."

    # Stop processes by PID files
    for pid_file in "$PID_DIR"/*.pid; do
        if [ -f "$pid_file" ]; then
            local pid=$(cat "$pid_file")
            local process_name=$(basename "$pid_file" .pid)

            if kill -0 "$pid" 2>/dev/null; then
                info "Stopping $process_name (PID: $pid)"
                kill "$pid" 2>/dev/null || true
                sleep 1

                # Force kill if still running
                if kill -0 "$pid" 2>/dev/null; then
                    warning "Force killing $process_name"
                    kill -9 "$pid" 2>/dev/null || true
                fi
            fi

            rm -f "$pid_file"
        fi
    done

    # Kill any processes using our ports
    local ports=(5000 8765 8766 8767)
    for port in "${ports[@]}"; do
        local pid=$(lsof -ti :$port 2>/dev/null || true)
        if [ -n "$pid" ]; then
            warning "Killing process using port $port (PID: $pid)"
            kill -9 "$pid" 2>/dev/null || true
        fi
    done

    sleep 2
    info "✅ Cleanup completed"
}

# Start servo backend API
start_servo_backend() {
    log "🚀 Starting R2D2 Servo Backend API..."

    local maestro_port=$(cat "$PID_DIR/maestro_port.txt" 2>/dev/null || echo "SIMULATION")
    local simulation_flag=""

    if [ "$maestro_port" = "SIMULATION" ]; then
        simulation_flag="--simulation"
        maestro_port="/dev/ttyACM0"
    fi

    cd "$SCRIPT_DIR"
    nohup python3 servo_api_server.py \
        --port 5000 \
        --websocket-port 8767 \
        --maestro-port "$maestro_port" \
        $simulation_flag \
        > "$LOG_DIR/servo_backend.log" 2>&1 &

    local backend_pid=$!
    echo $backend_pid > "$PID_DIR/servo_backend.pid"

    # Wait for backend to start
    sleep 3

    if kill -0 $backend_pid 2>/dev/null; then
        info "✅ Servo Backend API started (PID: $backend_pid) on port 5000"
        info "✅ Servo WebSocket started on port 8767"
    else
        error "Failed to start Servo Backend API"
        return 1
    fi
}

# Start dashboard server
start_dashboard() {
    log "🌐 Starting R2D2 Dashboard Server..."

    cd "$SCRIPT_DIR"
    nohup node dashboard-server.js \
        > "$LOG_DIR/dashboard.log" 2>&1 &

    local dashboard_pid=$!
    echo $dashboard_pid > "$PID_DIR/dashboard.pid"

    # Wait for dashboard to start
    sleep 2

    if kill -0 $dashboard_pid 2>/dev/null; then
        info "✅ Dashboard Server started (PID: $dashboard_pid) on port 8765"
        info "✅ Dashboard WebSocket started on port 8766"
    else
        error "Failed to start Dashboard Server"
        return 1
    fi
}

# Health check
health_check() {
    log "🔍 Performing system health check..."

    local all_healthy=true

    # Check servo backend API
    if curl -s http://localhost:5000/api/health > /dev/null 2>&1; then
        info "✅ Servo Backend API: Healthy"
    else
        error "❌ Servo Backend API: Not responding"
        all_healthy=false
    fi

    # Check dashboard server
    if curl -s http://localhost:8765 > /dev/null 2>&1; then
        info "✅ Dashboard Server: Healthy"
    else
        error "❌ Dashboard Server: Not responding"
        all_healthy=false
    fi

    # Check WebSocket ports
    local websocket_ports=(8766 8767)
    for port in "${websocket_ports[@]}"; do
        if nc -z localhost $port 2>/dev/null; then
            info "✅ WebSocket port $port: Open"
        else
            warning "⚠️  WebSocket port $port: Not accessible"
        fi
    done

    if [ "$all_healthy" = true ]; then
        log "🎉 All systems healthy!"
        return 0
    else
        error "⚠️  Some systems are not healthy"
        return 1
    fi
}

# Display system status
show_status() {
    log "📊 R2D2 Advanced Servo Control System Status"
    echo
    echo "🌐 Dashboard URLs:"
    echo "   Main Dashboard:     http://localhost:8765"
    echo "   Servo Dashboard:    http://localhost:8765/servo"
    echo "   Enhanced Dashboard: http://localhost:8765/enhanced"
    echo "   Vision Dashboard:   http://localhost:8765/vision"
    echo
    echo "🔗 API Endpoints:"
    echo "   Servo API:          http://localhost:5000/api"
    echo "   Health Check:       http://localhost:5000/api/health"
    echo "   System Status:      http://localhost:5000/api/status"
    echo
    echo "🔌 WebSocket Connections:"
    echo "   Dashboard:          ws://localhost:8766"
    echo "   Servo Control:      ws://localhost:8767"
    echo
    echo "📁 Log Files:"
    echo "   Servo Backend:      $LOG_DIR/servo_backend.log"
    echo "   Dashboard:          $LOG_DIR/dashboard.log"
    echo
    echo "🎮 Hardware Status:"
    local maestro_port=$(cat "$PID_DIR/maestro_port.txt" 2>/dev/null || echo "Unknown")
    if [ "$maestro_port" = "SIMULATION" ]; then
        echo "   Mode:               Simulation (No hardware detected)"
    else
        echo "   Maestro Controller: $maestro_port"
    fi
    echo
}

# Monitor services
monitor_services() {
    log "👀 Monitoring servo control services (Press Ctrl+C to stop)..."

    while true; do
        local failed_services=""

        # Check each service
        for pid_file in "$PID_DIR"/*.pid; do
            if [ -f "$pid_file" ]; then
                local pid=$(cat "$pid_file")
                local service_name=$(basename "$pid_file" .pid)

                if ! kill -0 "$pid" 2>/dev/null; then
                    failed_services="$failed_services $service_name"
                fi
            fi
        done

        if [ -n "$failed_services" ]; then
            error "Services failed:$failed_services"
            error "Check log files for details"
            break
        fi

        sleep 10
    done
}

# Signal handlers
cleanup() {
    echo
    log "🛑 Shutting down R2D2 Servo Control System..."
    stop_services
    log "✅ Shutdown complete"
    exit 0
}

trap cleanup INT TERM

# Main execution
main() {
    echo "🤖 R2D2 Advanced Servo Control System"
    echo "=====================================/"
    echo

    case "${1:-start}" in
        "start")
            check_dependencies
            check_hardware
            stop_services
            start_servo_backend || exit 1
            start_dashboard || exit 1
            health_check
            show_status

            if [ "${2:-}" = "--monitor" ]; then
                monitor_services
            else
                log "🎉 R2D2 Servo Control System started successfully!"
                log "💡 Use '$0 status' to check system health"
                log "💡 Use '$0 stop' to shutdown all services"
                log "💡 Use '$0 start --monitor' to start with monitoring"
            fi
            ;;

        "stop")
            stop_services
            ;;

        "restart")
            stop_services
            sleep 2
            "$0" start "${2:-}"
            ;;

        "status")
            health_check
            show_status
            ;;

        "monitor")
            monitor_services
            ;;

        "logs")
            if [ -n "${2:-}" ]; then
                if [ -f "$LOG_DIR/$2.log" ]; then
                    tail -f "$LOG_DIR/$2.log"
                else
                    error "Log file not found: $LOG_DIR/$2.log"
                    echo "Available logs:"
                    ls -1 "$LOG_DIR"/*.log 2>/dev/null || echo "No log files found"
                    exit 1
                fi
            else
                echo "Usage: $0 logs <service>"
                echo "Available services:"
                ls -1 "$LOG_DIR"/*.log 2>/dev/null | sed 's/.*\///;s/\.log$//' || echo "No log files found"
            fi
            ;;

        "help"|"-h"|"--help")
            echo "R2D2 Advanced Servo Control System"
            echo "Usage: $0 [command] [options]"
            echo
            echo "Commands:"
            echo "  start [--monitor]  Start all services (optionally with monitoring)"
            echo "  stop               Stop all services"
            echo "  restart [--monitor] Restart all services"
            echo "  status             Show system status and health"
            echo "  monitor            Monitor running services"
            echo "  logs <service>     View logs for specific service"
            echo "  help               Show this help message"
            echo
            echo "Examples:"
            echo "  $0 start           # Start all services"
            echo "  $0 start --monitor # Start and monitor services"
            echo "  $0 logs servo_backend # View servo backend logs"
            echo "  $0 status          # Check system health"
            ;;

        *)
            error "Unknown command: $1"
            echo "Use '$0 help' for usage information"
            exit 1
            ;;
    esac
}

# Run main function
main "$@"