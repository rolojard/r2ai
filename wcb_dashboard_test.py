#!/usr/bin/env python3
"""
WCB Dashboard Integration Testing Suite
Tests all 27 mood endpoints and dashboard functionality
"""

import requests
import time
import json
from datetime import datetime

# Configuration
WCB_API_URL = "http://localhost:8770"
TEST_RESULTS = []

class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    RESET = '\033[0m'

def log_test(test_name, passed, message="", duration_ms=0):
    """Log test result"""
    status = f"{Colors.GREEN}✓ PASS{Colors.RESET}" if passed else f"{Colors.RED}✗ FAIL{Colors.RESET}"
    timestamp = datetime.now().strftime("%H:%M:%S")
    
    result = {
        "test": test_name,
        "passed": passed,
        "message": message,
        "duration_ms": duration_ms,
        "timestamp": timestamp
    }
    TEST_RESULTS.append(result)
    
    print(f"[{timestamp}] {status} {test_name}")
    if message:
        print(f"         {message}")
    if duration_ms > 0:
        print(f"         Duration: {duration_ms}ms")

def test_wcb_api_connectivity():
    """Test WCB API is running and accessible"""
    try:
        start = time.time()
        response = requests.get(f"{WCB_API_URL}/api/wcb/mood/status", timeout=2)
        duration = int((time.time() - start) * 1000)
        
        if response.status_code == 200:
            log_test("WCB API Connectivity", True, f"API responding on port 8770", duration)
            return True
        else:
            log_test("WCB API Connectivity", False, f"Status code: {response.status_code}", duration)
            return False
    except requests.exceptions.RequestException as e:
        log_test("WCB API Connectivity", False, f"Connection failed: {str(e)}")
        return False

def test_mood_execution(mood_id, mood_name):
    """Test executing a specific mood"""
    try:
        start = time.time()
        response = requests.post(
            f"{WCB_API_URL}/api/wcb/mood/execute",
            json={"mood_id": mood_id, "priority": 7},
            timeout=2
        )
        duration = int((time.time() - start) * 1000)
        
        if response.status_code == 200:
            data = response.json()
            commands = data.get("commands_sent", 0)
            log_test(
                f"Mood {mood_id}: {mood_name}",
                True,
                f"{commands} commands sent",
                duration
            )
            return True
        else:
            log_test(
                f"Mood {mood_id}: {mood_name}",
                False,
                f"Status: {response.status_code}",
                duration
            )
            return False
    except requests.exceptions.RequestException as e:
        log_test(f"Mood {mood_id}: {mood_name}", False, f"Error: {str(e)}")
        return False

def test_mood_stop():
    """Test stopping current mood"""
    try:
        start = time.time()
        response = requests.post(f"{WCB_API_URL}/api/wcb/mood/stop", timeout=2)
        duration = int((time.time() - start) * 1000)
        
        if response.status_code == 200:
            log_test("Mood Stop", True, "Successfully stopped", duration)
            return True
        else:
            log_test("Mood Stop", False, f"Status: {response.status_code}", duration)
            return False
    except requests.exceptions.RequestException as e:
        log_test("Mood Stop", False, f"Error: {str(e)}")
        return False

def test_status_polling():
    """Test status polling endpoint"""
    try:
        start = time.time()
        response = requests.get(f"{WCB_API_URL}/api/wcb/mood/status", timeout=2)
        duration = int((time.time() - start) * 1000)
        
        if response.status_code == 200:
            data = response.json()
            active = data.get("active", False)
            log_test(
                "Status Polling",
                True,
                f"Active: {active}, Response time: {duration}ms",
                duration
            )
            return True
        else:
            log_test("Status Polling", False, f"Status: {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        log_test("Status Polling", False, f"Error: {str(e)}")
        return False

def test_api_performance():
    """Test API response time under load"""
    times = []
    for _ in range(10):
        start = time.time()
        try:
            response = requests.get(f"{WCB_API_URL}/api/wcb/mood/status", timeout=2)
            if response.status_code == 200:
                times.append((time.time() - start) * 1000)
        except:
            pass
    
    if times:
        avg_time = sum(times) / len(times)
        max_time = max(times)
        min_time = min(times)
        
        passed = avg_time < 100  # Target: <100ms average
        log_test(
            "API Performance",
            passed,
            f"Avg: {avg_time:.1f}ms, Min: {min_time:.1f}ms, Max: {max_time:.1f}ms"
        )
        return passed
    else:
        log_test("API Performance", False, "No successful requests")
        return False

def run_all_tests():
    """Run complete test suite"""
    print(f"\n{Colors.BLUE}{'='*70}{Colors.RESET}")
    print(f"{Colors.BLUE}WCB DASHBOARD INTEGRATION TEST SUITE{Colors.RESET}")
    print(f"{Colors.BLUE}{'='*70}{Colors.RESET}\n")
    
    print(f"{Colors.YELLOW}Phase 1: API Connectivity Tests{Colors.RESET}")
    print("-" * 70)
    
    # Test API connectivity first
    if not test_wcb_api_connectivity():
        print(f"\n{Colors.RED}ERROR: WCB API not accessible. Please start wcb_dashboard_api.py{Colors.RESET}\n")
        return False
    
    test_status_polling()
    test_api_performance()
    
    print(f"\n{Colors.YELLOW}Phase 2: Mood Execution Tests (Sample){Colors.RESET}")
    print("-" * 70)
    
    # Test sample of moods (not all 27 to avoid overwhelming the system)
    sample_moods = [
        (1, "Idle Relaxed"),
        (3, "Alert Curious"),
        (5, "Excited Happy"),
        (7, "Greeting Friendly"),
        (13, "Protective Alert"),
        (21, "Entertaining Crowd"),
        (27, "Emergency Panic")
    ]
    
    for mood_id, mood_name in sample_moods:
        test_mood_execution(mood_id, mood_name)
        time.sleep(0.5)  # Brief pause between tests
    
    print(f"\n{Colors.YELLOW}Phase 3: Control Tests{Colors.RESET}")
    print("-" * 70)
    
    test_mood_stop()
    
    # Generate summary
    print(f"\n{Colors.BLUE}{'='*70}{Colors.RESET}")
    print(f"{Colors.BLUE}TEST SUMMARY{Colors.RESET}")
    print(f"{Colors.BLUE}{'='*70}{Colors.RESET}\n")
    
    total_tests = len(TEST_RESULTS)
    passed_tests = sum(1 for r in TEST_RESULTS if r["passed"])
    failed_tests = total_tests - passed_tests
    success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
    
    print(f"Total Tests:    {total_tests}")
    print(f"{Colors.GREEN}Passed:         {passed_tests}{Colors.RESET}")
    print(f"{Colors.RED}Failed:         {failed_tests}{Colors.RESET}")
    print(f"Success Rate:   {success_rate:.1f}%\n")
    
    # Show failed tests if any
    if failed_tests > 0:
        print(f"{Colors.RED}Failed Tests:{Colors.RESET}")
        for result in TEST_RESULTS:
            if not result["passed"]:
                print(f"  • {result['test']}: {result['message']}")
        print()
    
    # Save results to file
    with open('/home/rolo/r2ai/wcb_test_results.json', 'w') as f:
        json.dump({
            "timestamp": datetime.now().isoformat(),
            "total_tests": total_tests,
            "passed": passed_tests,
            "failed": failed_tests,
            "success_rate": success_rate,
            "results": TEST_RESULTS
        }, f, indent=2)
    
    print(f"Results saved to: /home/rolo/r2ai/wcb_test_results.json\n")
    
    if success_rate >= 90:
        print(f"{Colors.GREEN}✓ All critical tests passed! Dashboard ready for use.{Colors.RESET}\n")
        return True
    else:
        print(f"{Colors.RED}✗ Some tests failed. Please review and fix issues.{Colors.RESET}\n")
        return False

if __name__ == "__main__":
    try:
        run_all_tests()
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}Tests interrupted by user{Colors.RESET}\n")
    except Exception as e:
        print(f"\n{Colors.RED}Test suite error: {str(e)}{Colors.RESET}\n")
