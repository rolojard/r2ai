#!/usr/bin/env python3
"""
WCB WebSocket Integration Test Suite
Tests WebSocket messaging between dashboard and WCB API
"""

import asyncio
import websockets
import json
import time
from datetime import datetime

WS_URL = "ws://localhost:8766"

class WCBWebSocketTester:
    def __init__(self):
        self.test_results = []
        self.messages_received = []

    async def connect_and_test(self):
        """Connect to WebSocket and run all tests"""
        print("=" * 80)
        print("WCB WEBSOCKET INTEGRATION TEST SUITE")
        print("=" * 80)
        print()

        try:
            async with websockets.connect(WS_URL) as websocket:
                print(f"✅ Connected to WebSocket: {WS_URL}")
                print()

                # Test 1: Connection Test
                await self.test_connection(websocket)

                # Test 2: WCB Mood List Request
                await self.test_mood_list_request(websocket)

                # Test 3: WCB Mood Status Request
                await self.test_mood_status_request(websocket)

                # Test 4: WCB Stats Request
                await self.test_stats_request(websocket)

                # Test 5: WCB Mood Execute
                await self.test_mood_execute(websocket)

                # Test 6: WCB Mood Stop
                await self.test_mood_stop(websocket)

                # Test 7: Auto-Broadcasting Test
                await self.test_auto_broadcasting(websocket)

                # Print Results
                self.print_results()

        except Exception as e:
            print(f"❌ WebSocket Connection Error: {e}")
            self.test_results.append({"test": "Connection", "status": "FAIL", "error": str(e)})
            self.print_results()

    async def test_connection(self, websocket):
        """Test 1: Basic Connection"""
        test_name = "WebSocket Connection"
        print(f"TEST 1: {test_name}")
        try:
            # WebSocket is already connected
            self.test_results.append({
                "test": test_name,
                "status": "PASS",
                "details": "Successfully connected to WebSocket server"
            })
            print(f"  ✅ PASS - Connected to {WS_URL}")
        except Exception as e:
            self.test_results.append({"test": test_name, "status": "FAIL", "error": str(e)})
            print(f"  ❌ FAIL - {e}")
        print()

    async def test_mood_list_request(self, websocket):
        """Test 2: WCB Mood List Request"""
        test_name = "WCB Mood List Request"
        print(f"TEST 2: {test_name}")
        try:
            # Send request
            request = {"type": "wcb_mood_list_request"}
            await websocket.send(json.dumps(request))
            print(f"  📤 Sent: {request}")

            # Receive response
            response_text = await asyncio.wait_for(websocket.recv(), timeout=5.0)
            response = json.loads(response_text)

            # Validate response
            if response.get("type") == "wcb_mood_list" and "moods" in response:
                mood_count = len(response["moods"])
                self.test_results.append({
                    "test": test_name,
                    "status": "PASS",
                    "details": f"Received {mood_count} moods"
                })
                print(f"  ✅ PASS - Received {mood_count} moods")
                print(f"  📊 First 3 moods: {[m['name'] for m in response['moods'][:3]]}")
            else:
                raise ValueError(f"Invalid response: {response}")

        except Exception as e:
            self.test_results.append({"test": test_name, "status": "FAIL", "error": str(e)})
            print(f"  ❌ FAIL - {e}")
        print()

    async def test_mood_status_request(self, websocket):
        """Test 3: WCB Mood Status Request"""
        test_name = "WCB Mood Status Request"
        print(f"TEST 3: {test_name}")
        try:
            request = {"type": "wcb_mood_status_request"}
            await websocket.send(json.dumps(request))
            print(f"  📤 Sent: {request}")

            response_text = await asyncio.wait_for(websocket.recv(), timeout=5.0)
            response = json.loads(response_text)

            if response.get("type") == "wcb_mood_status" and "active" in response:
                self.test_results.append({
                    "test": test_name,
                    "status": "PASS",
                    "details": f"Status: active={response['active']}, mood={response.get('mood')}"
                })
                print(f"  ✅ PASS - Active: {response['active']}, Mood: {response.get('mood', 'None')}")
            else:
                raise ValueError(f"Invalid response: {response}")

        except Exception as e:
            self.test_results.append({"test": test_name, "status": "FAIL", "error": str(e)})
            print(f"  ❌ FAIL - {e}")
        print()

    async def test_stats_request(self, websocket):
        """Test 4: WCB Stats Request"""
        test_name = "WCB Stats Request"
        print(f"TEST 4: {test_name}")
        try:
            request = {"type": "wcb_stats_request"}
            await websocket.send(json.dumps(request))
            print(f"  📤 Sent: {request}")

            response_text = await asyncio.wait_for(websocket.recv(), timeout=5.0)
            response = json.loads(response_text)

            if "moods_executed" in response:
                self.test_results.append({
                    "test": test_name,
                    "status": "PASS",
                    "details": f"Moods executed: {response['moods_executed']}, Commands sent: {response.get('total_commands_sent', 0)}"
                })
                print(f"  ✅ PASS - Moods Executed: {response['moods_executed']}")
                print(f"  📊 Commands Sent: {response.get('total_commands_sent', 0)}")
            else:
                raise ValueError(f"Invalid response: {response}")

        except Exception as e:
            self.test_results.append({"test": test_name, "status": "FAIL", "error": str(e)})
            print(f"  ❌ FAIL - {e}")
        print()

    async def test_mood_execute(self, websocket):
        """Test 5: WCB Mood Execute"""
        test_name = "WCB Mood Execute"
        print(f"TEST 5: {test_name}")
        try:
            # Execute JEDI_RESPECT (mood 23)
            request = {
                "type": "wcb_mood_execute",
                "mood_id": 23,
                "mood_name": "JEDI_RESPECT",
                "priority": 7
            }

            start_time = time.time()
            await websocket.send(json.dumps(request))
            print(f"  📤 Sent: Execute JEDI_RESPECT (ID: 23)")

            response_text = await asyncio.wait_for(websocket.recv(), timeout=10.0)
            response = json.loads(response_text)
            execution_time = (time.time() - start_time) * 1000

            if response.get("type") == "wcb_mood_result" and response.get("status") == "success":
                self.test_results.append({
                    "test": test_name,
                    "status": "PASS",
                    "details": f"Mood: {response['mood']}, Commands: {response.get('commands_sent', 0)}, Time: {execution_time:.0f}ms"
                })
                print(f"  ✅ PASS - Mood: {response['mood']}")
                print(f"  📊 Commands Sent: {response.get('commands_sent', 0)}")
                print(f"  ⏱️  Execution Time: {execution_time:.0f}ms")
            else:
                raise ValueError(f"Invalid response: {response}")

        except Exception as e:
            self.test_results.append({"test": test_name, "status": "FAIL", "error": str(e)})
            print(f"  ❌ FAIL - {e}")
        print()

    async def test_mood_stop(self, websocket):
        """Test 6: WCB Mood Stop"""
        test_name = "WCB Mood Stop"
        print(f"TEST 6: {test_name}")
        try:
            request = {"type": "wcb_mood_stop"}
            await websocket.send(json.dumps(request))
            print(f"  📤 Sent: Stop mood request")

            response_text = await asyncio.wait_for(websocket.recv(), timeout=5.0)
            response = json.loads(response_text)

            if response.get("type") == "wcb_mood_result":
                self.test_results.append({
                    "test": test_name,
                    "status": "PASS",
                    "details": f"Status: {response.get('status')}"
                })
                print(f"  ✅ PASS - Status: {response.get('status')}")
            else:
                raise ValueError(f"Invalid response: {response}")

        except Exception as e:
            self.test_results.append({"test": test_name, "status": "FAIL", "error": str(e)})
            print(f"  ❌ FAIL - {e}")
        print()

    async def test_auto_broadcasting(self, websocket):
        """Test 7: Auto-Broadcasting (1 second interval)"""
        test_name = "Auto-Broadcasting Status Updates"
        print(f"TEST 7: {test_name}")
        try:
            print(f"  ⏳ Waiting for auto-broadcast status updates (2 seconds)...")

            broadcast_count = 0
            start_time = time.time()

            while (time.time() - start_time) < 2.5:
                try:
                    response_text = await asyncio.wait_for(websocket.recv(), timeout=1.5)
                    response = json.loads(response_text)

                    if response.get("type") == "wcb_mood_status":
                        broadcast_count += 1
                        print(f"  📡 Received broadcast #{broadcast_count}: active={response.get('active')}, mood={response.get('mood')}")

                except asyncio.TimeoutError:
                    break

            if broadcast_count >= 1:
                self.test_results.append({
                    "test": test_name,
                    "status": "PASS",
                    "details": f"Received {broadcast_count} auto-broadcast status updates"
                })
                print(f"  ✅ PASS - Received {broadcast_count} auto-broadcast messages")
            else:
                raise ValueError("No auto-broadcast messages received")

        except Exception as e:
            self.test_results.append({"test": test_name, "status": "FAIL", "error": str(e)})
            print(f"  ❌ FAIL - {e}")
        print()

    def print_results(self):
        """Print test summary"""
        print()
        print("=" * 80)
        print("TEST RESULTS SUMMARY")
        print("=" * 80)

        passed = sum(1 for r in self.test_results if r["status"] == "PASS")
        failed = sum(1 for r in self.test_results if r["status"] == "FAIL")
        total = len(self.test_results)

        for result in self.test_results:
            status_icon = "✅" if result["status"] == "PASS" else "❌"
            print(f"{status_icon} {result['test']:40s} - {result['status']}")
            if "details" in result:
                print(f"   Details: {result['details']}")
            if "error" in result:
                print(f"   Error: {result['error']}")

        print()
        print(f"Total Tests: {total}")
        print(f"Passed: {passed} ✅")
        print(f"Failed: {failed} ❌")
        print(f"Success Rate: {(passed/total*100) if total > 0 else 0:.1f}%")
        print("=" * 80)


async def main():
    tester = WCBWebSocketTester()
    await tester.connect_and_test()


if __name__ == "__main__":
    asyncio.run(main())
