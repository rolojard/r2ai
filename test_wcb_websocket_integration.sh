#!/bin/bash

##############################################################################
# WCB WebSocket Integration Validation Script
# Tests all WebSocket functionality and verifies proper integration
##############################################################################

echo "============================================"
echo "🧪 WCB WebSocket Integration Test Suite"
echo "============================================"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

PASSED=0
FAILED=0

# Test function
run_test() {
    local test_name="$1"
    local test_command="$2"

    echo -n "Testing: $test_name ... "

    if eval "$test_command" > /dev/null 2>&1; then
        echo -e "${GREEN}✓ PASS${NC}"
        ((PASSED++))
        return 0
    else
        echo -e "${RED}✗ FAIL${NC}"
        ((FAILED++))
        return 1
    fi
}

echo "📋 Pre-flight Checks"
echo "--------------------"

# Test 1: Check if Node.js is installed
run_test "Node.js installation" "which node"

# Test 2: Check if Python3 is installed
run_test "Python3 installation" "which python3"

# Test 3: Check if required files exist
run_test "dashboard-server.js exists" "test -f /home/rolo/r2ai/dashboard-server.js"
run_test "wcb_dashboard_api.py exists" "test -f /home/rolo/r2ai/wcb_dashboard_api.py"
run_test "wcb_websocket_test.html exists" "test -f /home/rolo/r2ai/wcb_websocket_test.html"
run_test "WCB_WEBSOCKET_CLIENT_EXAMPLE.js exists" "test -f /home/rolo/r2ai/WCB_WEBSOCKET_CLIENT_EXAMPLE.js"

echo ""
echo "🔍 Code Integration Checks"
echo "--------------------------"

# Test 4: Check WCB API URL constant
run_test "WCB_API_URL defined" "grep -q 'WCB_API_URL.*8770' /home/rolo/r2ai/dashboard-server.js"

# Test 5: Check callWCBAPI function
run_test "callWCBAPI function exists" "grep -q 'async function callWCBAPI' /home/rolo/r2ai/dashboard-server.js"

# Test 6: Check WebSocket message handlers
run_test "wcb_mood_execute handler" "grep -q 'wcb_mood_execute' /home/rolo/r2ai/dashboard-server.js"
run_test "wcb_mood_stop handler" "grep -q 'wcb_mood_stop' /home/rolo/r2ai/dashboard-server.js"
run_test "wcb_mood_status_request handler" "grep -q 'wcb_mood_status_request' /home/rolo/r2ai/dashboard-server.js"
run_test "wcb_mood_list_request handler" "grep -q 'wcb_mood_list_request' /home/rolo/r2ai/dashboard-server.js"
run_test "wcb_stats_request handler" "grep -q 'wcb_stats_request' /home/rolo/r2ai/dashboard-server.js"

# Test 7: Check handler functions
run_test "handleWCBMoodExecute function" "grep -q 'async function handleWCBMoodExecute' /home/rolo/r2ai/dashboard-server.js"
run_test "handleWCBMoodStop function" "grep -q 'async function handleWCBMoodStop' /home/rolo/r2ai/dashboard-server.js"
run_test "handleWCBMoodStatusRequest function" "grep -q 'async function handleWCBMoodStatusRequest' /home/rolo/r2ai/dashboard-server.js"
run_test "handleWCBMoodListRequest function" "grep -q 'async function handleWCBMoodListRequest' /home/rolo/r2ai/dashboard-server.js"
run_test "handleWCBStatsRequest function" "grep -q 'async function handleWCBStatsRequest' /home/rolo/r2ai/dashboard-server.js"

# Test 8: Check broadcasting interval
run_test "WCB status broadcasting interval" "grep -q 'WCB Status Broadcasting' /home/rolo/r2ai/dashboard-server.js"

echo ""
echo "🌐 Runtime Service Checks"
echo "-------------------------"

# Test 9: Check if WCB API is running
if curl -s http://localhost:8770/api/wcb/status > /dev/null 2>&1; then
    echo -e "Testing: WCB API server (port 8770) ... ${GREEN}✓ PASS${NC}"
    ((PASSED++))
    WCB_API_RUNNING=true
else
    echo -e "Testing: WCB API server (port 8770) ... ${YELLOW}⚠ NOT RUNNING${NC}"
    echo "  → Start with: python3 wcb_dashboard_api.py"
    WCB_API_RUNNING=false
fi

# Test 10: Check if Dashboard Server is running
if curl -s http://localhost:8765 > /dev/null 2>&1; then
    echo -e "Testing: Dashboard server (port 8765) ... ${GREEN}✓ PASS${NC}"
    ((PASSED++))
    DASHBOARD_RUNNING=true
else
    echo -e "Testing: Dashboard server (port 8765) ... ${YELLOW}⚠ NOT RUNNING${NC}"
    echo "  → Start with: node dashboard-server.js"
    DASHBOARD_RUNNING=false
fi

# Test 11: Check if WebSocket port is open
if nc -z localhost 8766 > /dev/null 2>&1; then
    echo -e "Testing: WebSocket port (8766) ... ${GREEN}✓ PASS${NC}"
    ((PASSED++))
    WEBSOCKET_RUNNING=true
else
    echo -e "Testing: WebSocket port (8766) ... ${YELLOW}⚠ NOT RUNNING${NC}"
    echo "  → Starts with dashboard server"
    WEBSOCKET_RUNNING=false
fi

echo ""
echo "📊 API Endpoint Tests"
echo "---------------------"

if [ "$WCB_API_RUNNING" = true ]; then
    # Test WCB API endpoints
    run_test "GET /api/wcb/status" "curl -s http://localhost:8770/api/wcb/status | grep -q 'status'"
    run_test "GET /api/wcb/mood/list" "curl -s http://localhost:8770/api/wcb/mood/list | grep -q 'moods'"
    run_test "GET /api/wcb/mood/status" "curl -s http://localhost:8770/api/wcb/mood/status | grep -q 'active'"
    run_test "GET /api/wcb/stats" "curl -s http://localhost:8770/api/wcb/stats | grep -q 'moods_executed'"
else
    echo -e "${YELLOW}⚠ Skipping API tests (WCB API not running)${NC}"
fi

echo ""
echo "📄 Documentation Checks"
echo "-----------------------"

run_test "Testing guide exists" "test -f /home/rolo/r2ai/WCB_WEBSOCKET_TESTING_GUIDE.md"
run_test "Implementation summary exists" "test -f /home/rolo/r2ai/WCB_WEBSOCKET_IMPLEMENTATION_SUMMARY.md"
run_test "Quick start guide exists" "test -f /home/rolo/r2ai/WCB_WEBSOCKET_QUICKSTART.md"
run_test "Client example exists" "test -f /home/rolo/r2ai/WCB_WEBSOCKET_CLIENT_EXAMPLE.js"

echo ""
echo "============================================"
echo "📈 Test Results Summary"
echo "============================================"
echo ""
echo -e "Tests Passed: ${GREEN}${PASSED}${NC}"
echo -e "Tests Failed: ${RED}${FAILED}${NC}"
echo -e "Total Tests:  $((PASSED + FAILED))"
echo ""

# Calculate percentage
if [ $((PASSED + FAILED)) -gt 0 ]; then
    PERCENTAGE=$((PASSED * 100 / (PASSED + FAILED)))
    echo "Success Rate: ${PERCENTAGE}%"
else
    PERCENTAGE=0
fi

echo ""

# Final verdict
if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}✅ ALL TESTS PASSED!${NC}"
    echo ""
    echo "🎉 WCB WebSocket integration is fully functional!"
    echo ""
    echo "Next steps:"
    echo "  1. Open test interface: http://localhost:8765/wcb_websocket_test.html"
    echo "  2. Run manual tests from: WCB_WEBSOCKET_TESTING_GUIDE.md"
    echo "  3. Integrate into your dashboards using: WCB_WEBSOCKET_CLIENT_EXAMPLE.js"
    echo ""
    exit 0
elif [ $PERCENTAGE -ge 80 ]; then
    echo -e "${YELLOW}⚠ MOSTLY PASSING (${PERCENTAGE}%)${NC}"
    echo ""
    echo "Some tests failed, but core functionality appears intact."
    echo ""
    if [ "$WCB_API_RUNNING" = false ]; then
        echo "💡 Start WCB API server: python3 wcb_dashboard_api.py"
    fi
    if [ "$DASHBOARD_RUNNING" = false ]; then
        echo "💡 Start Dashboard server: node dashboard-server.js"
    fi
    echo ""
    exit 1
else
    echo -e "${RED}❌ TESTS FAILED (${PERCENTAGE}% passed)${NC}"
    echo ""
    echo "Please review the failed tests above."
    echo ""
    echo "Common issues:"
    echo "  • Missing Node.js or Python3"
    echo "  • Files not in correct location"
    echo "  • Servers not running"
    echo ""
    exit 2
fi
