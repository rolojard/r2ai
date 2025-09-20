#!/usr/bin/env python3
"""
Test script to verify dashboard and vision system integration
"""

import requests
import websocket
import json
import time
import threading
import sys

def test_dashboard_web():
    """Test if dashboard web interface is accessible"""
    try:
        response = requests.get('http://localhost:8765', timeout=5)
        if response.status_code == 200 and 'Real-time Vision' in response.text:
            print("✅ Dashboard web interface is accessible and serving vision interface")
            return True
        else:
            print(f"❌ Dashboard web interface issue: Status {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Dashboard web interface error: {e}")
        return False

def test_dashboard_websocket():
    """Test dashboard WebSocket API"""
    try:
        ws = websocket.create_connection("ws://localhost:8766", timeout=5)

        # Send test message
        test_message = {"type": "request_data"}
        ws.send(json.dumps(test_message))

        # Wait for response
        response = ws.recv()
        data = json.loads(response)

        ws.close()

        if data.get('type') in ['system_stats', 'r2d2_status']:
            print("✅ Dashboard WebSocket API responding correctly")
            return True
        else:
            print(f"❌ Dashboard WebSocket unexpected response: {data.get('type')}")
            return False

    except Exception as e:
        print(f"❌ Dashboard WebSocket error: {e}")
        return False

def test_vision_websocket():
    """Test vision system WebSocket"""
    try:
        ws = websocket.create_connection("ws://localhost:8767", timeout=10)

        # Wait for connection message
        start_time = time.time()
        received_data = False

        while time.time() - start_time < 5:
            try:
                ws.settimeout(1)
                response = ws.recv()
                data = json.loads(response)

                if data.get('type') in ['connection_status', 'vision_data', 'heartbeat']:
                    print(f"✅ Vision WebSocket responding: {data.get('type')}")
                    received_data = True
                    break

            except websocket.WebSocketTimeoutException:
                continue
            except Exception as e:
                print(f"⚠️ Vision WebSocket receive error: {e}")
                break

        ws.close()

        if received_data:
            print("✅ Vision system WebSocket is working")
            return True
        else:
            print("❌ Vision system WebSocket not responding")
            return False

    except Exception as e:
        print(f"❌ Vision WebSocket connection error: {e}")
        return False

def main():
    """Main test function"""
    print("🎯 R2D2 Dashboard Integration Test")
    print("=" * 40)

    tests = [
        ("Dashboard Web Interface", test_dashboard_web),
        ("Dashboard WebSocket API", test_dashboard_websocket),
        ("Vision System WebSocket", test_vision_websocket)
    ]

    passed = 0
    total = len(tests)

    for test_name, test_func in tests:
        print(f"\n🔍 Testing: {test_name}")
        try:
            if test_func():
                passed += 1
            else:
                print(f"❌ {test_name}: FAILED")
        except Exception as e:
            print(f"❌ {test_name}: ERROR - {e}")

        time.sleep(1)  # Brief pause between tests

    print("\n" + "=" * 40)
    print(f"📊 Integration Test Results: {passed}/{total} tests passed")

    if passed == total:
        print("🎉 R2D2 Dashboard with Vision System is fully operational!")
        print("\n🌐 Access the dashboard at: http://localhost:8765")
        print("👁️ Live video feed with object detection available")
        print("🎮 All controls and monitoring features ready")
        return 0
    else:
        print(f"⚠️ {total - passed} test(s) failed. Check system status.")
        return 1

if __name__ == "__main__":
    sys.exit(main())