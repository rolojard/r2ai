#!/bin/bash

# Deploy QA Protection Framework for R2D2 System
# Elite Quality Assurance Deployment Script

set -e  # Exit on any error

echo "🛡️ DEPLOYING R2D2 QA PROTECTION FRAMEWORK"
echo "========================================="

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    local color=$1
    local message=$2
    echo -e "${color}${message}${NC}"
}

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to check system requirements
check_requirements() {
    print_status $BLUE "📋 Checking system requirements..."

    local requirements_met=true

    # Check Python 3
    if command_exists python3; then
        print_status $GREEN "✅ Python 3 found: $(python3 --version)"
    else
        print_status $RED "❌ Python 3 not found"
        requirements_met=false
    fi

    # Check Node.js
    if command_exists node; then
        print_status $GREEN "✅ Node.js found: $(node --version)"
    else
        print_status $RED "❌ Node.js not found"
        requirements_met=false
    fi

    # Check Git
    if command_exists git; then
        print_status $GREEN "✅ Git found: $(git --version | head -1)"
    else
        print_status $RED "❌ Git not found"
        requirements_met=false
    fi

    # Check pip packages
    print_status $BLUE "📦 Checking Python packages..."

    local python_packages=("requests" "websockets" "asyncio" "psutil" "numpy" "opencv-python")
    for package in "${python_packages[@]}"; do
        if python3 -c "import $package" 2>/dev/null; then
            print_status $GREEN "✅ $package installed"
        else
            print_status $YELLOW "⚠️ $package not found - attempting to install..."
            pip3 install $package
        fi
    done

    if [ "$requirements_met" = false ]; then
        print_status $RED "❌ System requirements not met. Please install missing components."
        exit 1
    fi

    print_status $GREEN "✅ All system requirements met"
}

# Function to install QA protection scripts
install_qa_scripts() {
    print_status $BLUE "📥 Installing QA protection scripts..."

    # Make scripts executable
    chmod +x /home/rolo/r2ai/qa_comprehensive_protection_suite.py
    chmod +x /home/rolo/r2ai/qa_baseline_performance_documentation.py
    chmod +x /home/rolo/r2ai/qa_realtime_monitoring_system.py
    chmod +x /home/rolo/r2ai/qa_regression_alert_rollback_system.py

    print_status $GREEN "✅ QA scripts installed and made executable"
}

# Function to establish baseline metrics
establish_baseline() {
    print_status $BLUE "📊 Establishing system performance baseline..."

    # Check if system is running
    if ! curl -s http://localhost:8765/ > /dev/null; then
        print_status $RED "❌ Dashboard server not running. Please start the system first."
        print_status $YELLOW "Run: cd /home/rolo/r2ai && node dashboard-server.js &"
        exit 1
    fi

    if ! curl -s http://localhost:8767/ > /dev/null 2>&1; then
        print_status $YELLOW "⚠️ Vision system may not be running. Starting baseline without vision metrics."
    fi

    # Establish baseline
    python3 /home/rolo/r2ai/qa_baseline_performance_documentation.py

    if [ $? -eq 0 ]; then
        print_status $GREEN "✅ Baseline metrics established"
    else
        print_status $RED "❌ Failed to establish baseline metrics"
        exit 1
    fi
}

# Function to run initial protection tests
run_initial_tests() {
    print_status $BLUE "🧪 Running initial protection test suite..."

    python3 /home/rolo/r2ai/qa_comprehensive_protection_suite.py

    if [ $? -eq 0 ]; then
        print_status $GREEN "✅ Initial protection tests completed"
    else
        print_status $YELLOW "⚠️ Some protection tests failed. Review results before proceeding."
    fi
}

# Function to create monitoring service
create_monitoring_service() {
    print_status $BLUE "🔍 Setting up monitoring service..."

    # Create systemd service file for continuous monitoring
    cat > /tmp/r2d2-qa-monitor.service << EOF
[Unit]
Description=R2D2 QA Protection Monitoring Service
After=network.target
Wants=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=/home/rolo/r2ai
Environment=PATH=/usr/bin:/usr/local/bin:/home/rolo/.local/bin
ExecStart=/usr/bin/python3 /home/rolo/r2ai/qa_realtime_monitoring_system.py --monitor
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

    print_status $YELLOW "📝 Monitoring service configuration created at /tmp/r2d2-qa-monitor.service"
    print_status $YELLOW "To install as system service (requires sudo):"
    print_status $YELLOW "  sudo cp /tmp/r2d2-qa-monitor.service /etc/systemd/system/"
    print_status $YELLOW "  sudo systemctl enable r2d2-qa-monitor"
    print_status $YELLOW "  sudo systemctl start r2d2-qa-monitor"
}

# Function to create QA dashboard script
create_qa_dashboard() {
    print_status $BLUE "📈 Creating QA dashboard script..."

    cat > /home/rolo/r2ai/qa_dashboard.py << 'EOF'
#!/usr/bin/env python3
"""
QA Dashboard - Unified view of R2D2 system protection status
"""
import json
import os
import sys
from datetime import datetime

def load_latest_report(pattern):
    """Load the latest report file matching pattern"""
    import glob
    files = glob.glob(f"/home/rolo/r2ai/{pattern}")
    if not files:
        return None
    latest_file = max(files, key=os.path.getctime)
    try:
        with open(latest_file, 'r') as f:
            return json.load(f)
    except:
        return None

def display_dashboard():
    """Display comprehensive QA dashboard"""
    print("🛡️ R2D2 QUALITY ASSURANCE DASHBOARD")
    print("=" * 60)
    print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    # Protection Suite Status
    protection_report = load_latest_report("qa_protection_report_*.json")
    if protection_report:
        score = protection_report.get('protection_score', 0)
        status = protection_report.get('system_status', 'UNKNOWN')

        if score >= 90:
            status_icon = "✅"
        elif score >= 70:
            status_icon = "⚠️"
        else:
            status_icon = "❌"

        print(f"🛡️ PROTECTION STATUS: {status_icon} {status} ({score:.1f}%)")
        print(f"   Tests Passed: {protection_report.get('passed_tests', 0)}/{protection_report.get('total_tests', 0)}")
    else:
        print("🛡️ PROTECTION STATUS: ❓ No recent report found")

    # Baseline Status
    if os.path.exists("/home/rolo/r2ai/qa_system_baselines.json"):
        with open("/home/rolo/r2ai/qa_system_baselines.json", 'r') as f:
            baseline = json.load(f)
        print(f"📊 BASELINE: ✅ Established {baseline.get('timestamp', 'Unknown')}")
    else:
        print("📊 BASELINE: ❌ Not established")

    # Recent Alerts
    import glob
    alert_files = glob.glob("/home/rolo/r2ai/qa_alerts_*.json")
    if alert_files:
        latest_alerts = max(alert_files, key=os.path.getctime)
        try:
            with open(latest_alerts, 'r') as f:
                alerts = json.load(f)

            critical_alerts = [a for a in alerts if a.get('severity') == 'CRITICAL']
            warning_alerts = [a for a in alerts if a.get('severity') == 'WARNING']

            print(f"🚨 ALERTS: {len(critical_alerts)} Critical, {len(warning_alerts)} Warning")

            if critical_alerts:
                print("   Recent Critical Alerts:")
                for alert in critical_alerts[-3:]:  # Show last 3
                    print(f"     • {alert.get('type', 'Unknown')}: {alert.get('timestamp', '')}")

        except:
            print("🚨 ALERTS: ❓ Unable to read alert file")
    else:
        print("🚨 ALERTS: ✅ No alert files found")

    # Monitoring Status
    # Check if monitoring process is running
    import subprocess
    try:
        result = subprocess.run(['pgrep', '-f', 'qa_realtime_monitoring'],
                              capture_output=True, text=True)
        if result.returncode == 0:
            print("🔍 MONITORING: ✅ Active")
        else:
            print("🔍 MONITORING: ❌ Not running")
    except:
        print("🔍 MONITORING: ❓ Status unknown")

    # System Health
    try:
        import psutil
        cpu = psutil.cpu_percent()
        memory = psutil.virtual_memory().percent

        cpu_status = "✅" if cpu < 75 else "⚠️" if cpu < 90 else "❌"
        memory_status = "✅" if memory < 70 else "⚠️" if memory < 85 else "❌"

        print(f"💻 SYSTEM HEALTH:")
        print(f"   CPU: {cpu_status} {cpu:.1f}%")
        print(f"   Memory: {memory_status} {memory:.1f}%")
    except:
        print("💻 SYSTEM HEALTH: ❓ Unable to read")

    print()
    print("📋 QUICK COMMANDS:")
    print("   python3 qa_comprehensive_protection_suite.py  # Run protection tests")
    print("   python3 qa_realtime_monitoring_system.py      # Start monitoring")
    print("   python3 qa_regression_alert_rollback_system.py status  # Check rollback system")
    print("=" * 60)

if __name__ == "__main__":
    display_dashboard()
EOF

    chmod +x /home/rolo/r2ai/qa_dashboard.py
    print_status $GREEN "✅ QA dashboard created"
}

# Function to create quick start script
create_quick_start() {
    print_status $BLUE "🚀 Creating quick start script..."

    cat > /home/rolo/r2ai/start_qa_protection.sh << 'EOF'
#!/bin/bash

# Quick Start Script for R2D2 QA Protection
echo "🛡️ Starting R2D2 QA Protection System"

# Check if system is running
if ! curl -s http://localhost:8765/ > /dev/null; then
    echo "❌ Dashboard server not running. Please start with:"
    echo "   cd /home/rolo/r2ai && node dashboard-server.js &"
    exit 1
fi

echo "✅ Dashboard server detected"

# Start monitoring in background
echo "🔍 Starting real-time monitoring..."
nohup python3 /home/rolo/r2ai/qa_realtime_monitoring_system.py --monitor > qa_monitor.log 2>&1 &
MONITOR_PID=$!
echo "Monitor PID: $MONITOR_PID"

# Start regression system in background
echo "🚨 Starting regression alert system..."
nohup python3 /home/rolo/r2ai/qa_regression_alert_rollback_system.py start > qa_regression.log 2>&1 &
REGRESSION_PID=$!
echo "Regression PID: $REGRESSION_PID"

# Save PIDs for later cleanup
echo "$MONITOR_PID" > /tmp/qa_monitor.pid
echo "$REGRESSION_PID" > /tmp/qa_regression.pid

echo "✅ QA Protection System started successfully"
echo "📊 View status with: python3 qa_dashboard.py"
echo "🛑 Stop with: ./stop_qa_protection.sh"
EOF

    cat > /home/rolo/r2ai/stop_qa_protection.sh << 'EOF'
#!/bin/bash

# Stop QA Protection System
echo "🛑 Stopping R2D2 QA Protection System"

# Kill monitoring processes
if [ -f /tmp/qa_monitor.pid ]; then
    MONITOR_PID=$(cat /tmp/qa_monitor.pid)
    if kill -0 $MONITOR_PID 2>/dev/null; then
        kill $MONITOR_PID
        echo "✅ Stopped monitoring (PID: $MONITOR_PID)"
    fi
    rm /tmp/qa_monitor.pid
fi

if [ -f /tmp/qa_regression.pid ]; then
    REGRESSION_PID=$(cat /tmp/qa_regression.pid)
    if kill -0 $REGRESSION_PID 2>/dev/null; then
        kill $REGRESSION_PID
        echo "✅ Stopped regression system (PID: $REGRESSION_PID)"
    fi
    rm /tmp/qa_regression.pid
fi

# Also kill any remaining processes
pkill -f "qa_realtime_monitoring_system.py"
pkill -f "qa_regression_alert_rollback_system.py"

echo "✅ QA Protection System stopped"
EOF

    chmod +x /home/rolo/r2ai/start_qa_protection.sh
    chmod +x /home/rolo/r2ai/stop_qa_protection.sh

    print_status $GREEN "✅ Quick start scripts created"
}

# Function to create usage documentation
create_documentation() {
    print_status $BLUE "📚 Creating usage documentation..."

    cat > /home/rolo/r2ai/QA_PROTECTION_USAGE.md << 'EOF'
# R2D2 QA Protection Framework Usage Guide

## Quick Start

### 1. Start the Protection System
```bash
./start_qa_protection.sh
```

### 2. View System Status
```bash
python3 qa_dashboard.py
```

### 3. Run Manual Tests
```bash
python3 qa_comprehensive_protection_suite.py
```

### 4. Stop Protection System
```bash
./stop_qa_protection.sh
```

## Individual Components

### Protection Test Suite
```bash
python3 qa_comprehensive_protection_suite.py
python3 qa_comprehensive_protection_suite.py --monitor  # Continuous monitoring
```

### Baseline Documentation
```bash
python3 qa_baseline_performance_documentation.py
python3 qa_baseline_performance_documentation.py --compare  # Compare with baseline
```

### Real-time Monitoring
```bash
python3 qa_realtime_monitoring_system.py
python3 qa_realtime_monitoring_system.py --monitor  # Background monitoring
```

### Regression Alert & Rollback
```bash
python3 qa_regression_alert_rollback_system.py start
python3 qa_regression_alert_rollback_system.py status
python3 qa_regression_alert_rollback_system.py rollback "Manual rollback reason"
```

## Log Files

- `qa_monitor.log` - Real-time monitoring logs
- `qa_regression.log` - Regression system logs
- `qa_alerts_*.json` - Alert history files
- `qa_protection_report_*.json` - Protection test reports
- `qa_system_baselines.json` - Performance baselines

## Alert Files

- `critical_alert_*.json` - Critical system alerts
- `warning_alert_*.json` - Warning alerts
- `qa_regression_alert_*.json` - Regression alerts

## Emergency Procedures

### Manual Rollback
```bash
python3 qa_regression_alert_rollback_system.py rollback "Emergency rollback"
```

### Force System Restart
```bash
pkill -f "dashboard-server.js"
pkill -f "r2d2_realtime_vision.py"
cd /home/rolo/r2ai
node dashboard-server.js &
python3 r2d2_realtime_vision.py &
```

### Check System Health
```bash
python3 qa_comprehensive_protection_suite.py --quick-check
```

## Integration with Development

### Before Making Changes
1. `python3 qa_baseline_performance_documentation.py`
2. `python3 qa_comprehensive_protection_suite.py`
3. Ensure all tests pass before proceeding

### During Development
1. Keep monitoring running: `./start_qa_protection.sh`
2. Check status regularly: `python3 qa_dashboard.py`
3. Watch for alerts in log files

### After Changes
1. `python3 qa_comprehensive_protection_suite.py`
2. `python3 qa_baseline_performance_documentation.py --compare`
3. Ensure no regressions detected

## Troubleshooting

### Protection Tests Failing
1. Check if all services are running
2. Verify system resources (CPU < 90%, Memory < 85%)
3. Check network connectivity to localhost endpoints

### Monitoring Not Working
1. Check if Python packages are installed
2. Verify file permissions
3. Check log files for error messages

### Baseline Issues
1. Ensure system is stable before establishing baseline
2. Run baseline multiple times for consistency
3. Check if baseline file exists and is readable
EOF

    print_status $GREEN "✅ Usage documentation created"
}

# Function to verify installation
verify_installation() {
    print_status $BLUE "🔍 Verifying installation..."

    local verification_passed=true

    # Check if all scripts exist and are executable
    local scripts=(
        "qa_comprehensive_protection_suite.py"
        "qa_baseline_performance_documentation.py"
        "qa_realtime_monitoring_system.py"
        "qa_regression_alert_rollback_system.py"
        "qa_dashboard.py"
        "start_qa_protection.sh"
        "stop_qa_protection.sh"
    )

    for script in "${scripts[@]}"; do
        if [ -x "/home/rolo/r2ai/$script" ]; then
            print_status $GREEN "✅ $script - OK"
        else
            print_status $RED "❌ $script - Missing or not executable"
            verification_passed=false
        fi
    done

    # Check if baseline exists
    if [ -f "/home/rolo/r2ai/qa_system_baselines.json" ]; then
        print_status $GREEN "✅ Baseline data established"
    else
        print_status $YELLOW "⚠️ Baseline data not yet established"
    fi

    # Test script execution
    if python3 /home/rolo/r2ai/qa_dashboard.py > /dev/null 2>&1; then
        print_status $GREEN "✅ QA Dashboard functional"
    else
        print_status $RED "❌ QA Dashboard test failed"
        verification_passed=false
    fi

    if [ "$verification_passed" = true ]; then
        print_status $GREEN "✅ Installation verification successful"
        return 0
    else
        print_status $RED "❌ Installation verification failed"
        return 1
    fi
}

# Function to display final instructions
display_final_instructions() {
    print_status $GREEN "🎯 QA PROTECTION FRAMEWORK DEPLOYMENT COMPLETE"
    echo
    print_status $BLUE "📋 NEXT STEPS:"
    echo "1. Ensure your R2D2 system is running:"
    echo "   cd /home/rolo/r2ai && node dashboard-server.js &"
    echo "   cd /home/rolo/r2ai && python3 r2d2_realtime_vision.py &"
    echo
    echo "2. Start QA protection:"
    echo "   ./start_qa_protection.sh"
    echo
    echo "3. View system status:"
    echo "   python3 qa_dashboard.py"
    echo
    echo "4. Follow collaboration guidelines:"
    echo "   cat qa_sub_agent_collaboration_framework.md"
    echo
    print_status $YELLOW "⚠️ IMPORTANT: All sub-agents must follow the QA guidelines"
    print_status $YELLOW "   before making any changes to the system!"
    echo
    print_status $GREEN "🛡️ Your R2D2 system is now protected by elite QA framework!"
}

# Main deployment sequence
main() {
    echo "Starting QA Protection Framework deployment..."
    echo

    # Check requirements
    check_requirements
    echo

    # Install QA scripts
    install_qa_scripts
    echo

    # Create supporting tools
    create_qa_dashboard
    create_quick_start
    create_monitoring_service
    create_documentation
    echo

    # Establish baseline if system is running
    if curl -s http://localhost:8765/ > /dev/null; then
        establish_baseline
        echo

        # Run initial tests
        run_initial_tests
        echo
    else
        print_status $YELLOW "⚠️ System not running - skipping baseline and initial tests"
        print_status $YELLOW "   Please start your R2D2 system and run:"
        print_status $YELLOW "   python3 qa_baseline_performance_documentation.py"
        print_status $YELLOW "   python3 qa_comprehensive_protection_suite.py"
        echo
    fi

    # Verify installation
    verify_installation
    echo

    # Display final instructions
    display_final_instructions
}

# Run main function
main "$@"