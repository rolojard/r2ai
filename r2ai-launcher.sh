#!/bin/bash
# 🎯 R2AI System Launcher & Testing Menu

RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}"
echo "==============================================="
echo "🎯 R2AI SYSTEM LAUNCHER & TESTING MENU"
echo "==============================================="
echo -e "${NC}"

while true; do
    echo -e "${GREEN}QUICK TESTS:${NC}"
    echo "1) 🏥 System Health Check"
    echo "2) 🔧 Hardware Component Test"
    echo "3) 🎭 Servo Movement Test"
    echo "4) 🎵 Audio System Test"
    echo "5) 👁️  Vision System Test"
    echo ""
    echo -e "${BLUE}DASHBOARDS:${NC}"
    echo "6) 🖥️  Launch Web Dashboard"
    echo "7) 📊 System Performance Monitor"
    echo ""
    echo -e "${YELLOW}FULL DEMOS:${NC}"
    echo "8) 🎪 Enhanced Scenario Demo"
    echo "9) 🛡️  Security Validation"
    echo "10) 🏆 Convention Ready Demo"
    echo ""
    echo -e "${RED}SYSTEM:${NC}"
    echo "11) ℹ️  Quick Status"
    echo "12) 📖 Open Testing Guide"
    echo "0) ❌ Exit"
    echo ""
    read -p "Select option (0-12): " choice

    case $choice in
        1)
            echo -e "${GREEN}Running System Health Check...${NC}"
            python3 r2d2_integrated_performance.py
            ;;
        2)
            echo -e "${GREEN}Testing Hardware Components...${NC}"
            python3 r2d2_component_tester.py
            ;;
        3)
            echo -e "${GREEN}Testing Servo Movements...${NC}"
            python3 test_r2d2_servos.py
            ;;
        4)
            echo -e "${GREEN}Testing Audio System...${NC}"
            python3 r2d2_canonical_sound_validator.py
            ;;
        5)
            echo -e "${GREEN}Testing Vision System...${NC}"
            python3 r2d2_vision_validator.py
            ;;
        6)
            echo -e "${BLUE}Launching Web Dashboard...${NC}"
            echo "Dashboard will be available at: http://localhost:8765"
            ./start-dashboard.sh
            ;;
        7)
            echo -e "${BLUE}Starting Performance Monitor...${NC}"
            ./r2d2_system_performance.sh
            ;;
        8)
            echo -e "${YELLOW}Running Enhanced Scenario Demo...${NC}"
            python3 r2d2_enhanced_scenario_tester.py
            ;;
        9)
            echo -e "${YELLOW}Running Security Validation...${NC}"
            python3 r2d2_security_validator.py
            ;;
        10)
            echo -e "${YELLOW}Running Convention Ready Demo...${NC}"
            python3 r2d2_convention_load_test.py
            ;;
        11)
            echo -e "${RED}=== R2AI QUICK STATUS ===${NC}"
            python3 -c "
import psutil, subprocess, os
try:
    cpu = psutil.cpu_percent()
    mem = psutil.virtual_memory().percent
    temp_file = '/sys/class/thermal/thermal_zone0/temp'
    temp = int(open(temp_file).read().strip()) // 1000 if os.path.exists(temp_file) else 'N/A'
    gpu = subprocess.check_output(['nvidia-smi', '--query-gpu=utilization.gpu', '--format=csv,noheader,nounits'], stderr=subprocess.DEVNULL).decode().strip()
    print(f'🖥️  CPU: {cpu}%')
    print(f'💾 Memory: {mem}%')
    print(f'🌡️  Temperature: {temp}°C')
    print(f'🎮 GPU: {gpu}%')
    print('✅ System Status: OPERATIONAL')
except:
    print('⚠️  Status check failed - some components unavailable')
"
            ;;
        12)
            echo -e "${GREEN}Opening Testing Guide...${NC}"
            if command -v code &> /dev/null; then
                code R2AI_TESTING_GUIDE.md
            elif command -v nano &> /dev/null; then
                nano R2AI_TESTING_GUIDE.md
            else
                cat R2AI_TESTING_GUIDE.md
            fi
            ;;
        0)
            echo -e "${GREEN}Goodbye! R2AI System Ready! 🎯${NC}"
            exit 0
            ;;
        *)
            echo -e "${RED}Invalid option. Please try again.${NC}"
            ;;
    esac
    echo ""
    read -p "Press Enter to continue..."
    clear
done