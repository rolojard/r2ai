#!/bin/bash
# WCB Dashboard API - Test Commands
# Comprehensive test suite for all API endpoints

API_BASE="http://localhost:8770"

echo "=========================================="
echo "WCB Dashboard API Test Suite"
echo "=========================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print test header
test_header() {
    echo -e "${BLUE}==> $1${NC}"
}

# Function to print success
success() {
    echo -e "${GREEN}✓ $1${NC}"
}

# ============================================================================
# 1. HEALTH CHECK
# ============================================================================
test_header "1. Health Check"
curl -X GET "${API_BASE}/" | jq '.'
echo ""
sleep 1

# ============================================================================
# 2. LIST ALL MOODS
# ============================================================================
test_header "2. List All Available Moods"
curl -X GET "${API_BASE}/api/wcb/mood/list" | jq '.'
echo ""
sleep 1

# ============================================================================
# 3. GET CURRENT STATUS
# ============================================================================
test_header "3. Get Current Mood Status (should be inactive)"
curl -X GET "${API_BASE}/api/wcb/mood/status" | jq '.'
echo ""
sleep 1

# ============================================================================
# 4. EXECUTE MOOD - IDLE_RELAXED (ID: 1)
# ============================================================================
test_header "4. Execute IDLE_RELAXED Mood (ID: 1)"
curl -X POST "${API_BASE}/api/wcb/mood/execute" \
  -H "Content-Type: application/json" \
  -d '{
    "mood_id": 1,
    "priority": 7
  }' | jq '.'
echo ""
sleep 2

# ============================================================================
# 5. EXECUTE MOOD - EXCITED_HAPPY (ID: 5)
# ============================================================================
test_header "5. Execute EXCITED_HAPPY Mood (ID: 5) with mood_name validation"
curl -X POST "${API_BASE}/api/wcb/mood/execute" \
  -H "Content-Type: application/json" \
  -d '{
    "mood_id": 5,
    "mood_name": "EXCITED_HAPPY",
    "priority": 8
  }' | jq '.'
echo ""
sleep 2

# ============================================================================
# 6. EXECUTE MOOD - PROTECTIVE_ALERT (ID: 13)
# ============================================================================
test_header "6. Execute PROTECTIVE_ALERT Mood (ID: 13)"
curl -X POST "${API_BASE}/api/wcb/mood/execute" \
  -H "Content-Type: application/json" \
  -d '{
    "mood_id": 13,
    "priority": 9
  }' | jq '.'
echo ""
sleep 2

# ============================================================================
# 7. EXECUTE MOOD - JEDI_RESPECT (ID: 23)
# ============================================================================
test_header "7. Execute JEDI_RESPECT Mood (ID: 23)"
curl -X POST "${API_BASE}/api/wcb/mood/execute" \
  -H "Content-Type: application/json" \
  -d '{
    "mood_id": 23,
    "priority": 7
  }' | jq '.'
echo ""
sleep 2

# ============================================================================
# 8. EXECUTE MOOD - EMERGENCY_PANIC (ID: 27)
# ============================================================================
test_header "8. Execute EMERGENCY_PANIC Mood (ID: 27)"
curl -X POST "${API_BASE}/api/wcb/mood/execute" \
  -H "Content-Type: application/json" \
  -d '{
    "mood_id": 27,
    "priority": 10
  }' | jq '.'
echo ""
sleep 2

# ============================================================================
# 9. GET STATUS AFTER EXECUTIONS
# ============================================================================
test_header "9. Get Status After Multiple Executions"
curl -X GET "${API_BASE}/api/wcb/mood/status" | jq '.'
echo ""
sleep 1

# ============================================================================
# 10. GET STATISTICS
# ============================================================================
test_header "10. Get API Statistics"
curl -X GET "${API_BASE}/api/wcb/stats" | jq '.'
echo ""
sleep 1

# ============================================================================
# 11. GET BOARDS STATUS
# ============================================================================
test_header "11. Get WCB Boards Status"
curl -X GET "${API_BASE}/api/wcb/boards/status" | jq '.'
echo ""
sleep 1

# ============================================================================
# 12. STOP MOOD (if any running)
# ============================================================================
test_header "12. Stop Current Mood"
curl -X POST "${API_BASE}/api/wcb/mood/stop" | jq '.'
echo ""
sleep 1

# ============================================================================
# 13. ERROR TEST - Invalid Mood ID
# ============================================================================
test_header "13. Error Test - Invalid Mood ID (should fail)"
curl -X POST "${API_BASE}/api/wcb/mood/execute" \
  -H "Content-Type: application/json" \
  -d '{
    "mood_id": 99,
    "priority": 7
  }' | jq '.'
echo ""
sleep 1

# ============================================================================
# 14. ERROR TEST - Mood Name Mismatch
# ============================================================================
test_header "14. Error Test - Mood Name Mismatch (should fail)"
curl -X POST "${API_BASE}/api/wcb/mood/execute" \
  -H "Content-Type: application/json" \
  -d '{
    "mood_id": 5,
    "mood_name": "WRONG_NAME",
    "priority": 7
  }' | jq '.'
echo ""
sleep 1

# ============================================================================
# 15. COMPREHENSIVE MOOD TEST - All Primary Emotional Moods
# ============================================================================
test_header "15. Test All Primary Emotional Moods (1-6)"

for mood_id in {1..6}; do
    echo -e "${YELLOW}Testing Mood ID: $mood_id${NC}"
    curl -X POST "${API_BASE}/api/wcb/mood/execute" \
      -H "Content-Type: application/json" \
      -d "{\"mood_id\": $mood_id, \"priority\": 7}" | jq '.mood, .commands_sent, .execution_time_ms'
    echo ""
    sleep 1
done

# ============================================================================
# FINAL STATISTICS
# ============================================================================
test_header "Final Statistics Summary"
curl -X GET "${API_BASE}/api/wcb/stats" | jq '.'
echo ""

echo -e "${GREEN}=========================================="
echo "Test Suite Completed!"
echo "==========================================${NC}"
echo ""
echo "To view API documentation, visit:"
echo "http://localhost:8770/docs"
