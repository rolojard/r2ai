#!/usr/bin/env python3
"""
QA Phase 2 - WebSocket and Metrics Validation Test
Simplified focused test for WebSocket connectivity and metrics data
"""

import asyncio
import websockets
import json
import time
from datetime import datetime

# Configuration
VISION_WS_URL = "ws://localhost:8767"
AUTH_TOKEN = "fd81ba71-43f6-4bb3-afb5-e8dc3f9eb12e"
TEST_DURATION = 30  # seconds

# Results tracking
test_results = {
    "websocket_connected": False,
    "messages_received": 0,
    "video_frames": 0,
    "fps_values": [],
    "gpu_values": [],
    "memory_values": [],
    "temp_values": [],
    "cpu_values": [],
    "detections_count": 0,
    "errors": []
}

async def test_websocket_connection():
    """Test WebSocket connection and data collection"""
    global test_results

    print("=" * 80)
    print("QA PHASE 2 - WEBSOCKET & METRICS VALIDATION TEST")
    print("=" * 80)
    print(f"Start Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Test Duration: {TEST_DURATION} seconds")
    print("=" * 80 + "\n")

    try:
        ws_url = f"{VISION_WS_URL}?token={AUTH_TOKEN}"
        print(f"Connecting to {VISION_WS_URL}...")

        async with websockets.connect(ws_url, ping_interval=20, ping_timeout=10) as websocket:
            print("✅ WebSocket connected successfully\n")
            test_results["websocket_connected"] = True

            # Collect data for specified duration
            start_time = time.time()
            last_status_time = start_time

            while (time.time() - start_time) < TEST_DURATION:
                try:
                    # Receive message with timeout
                    message = await asyncio.wait_for(websocket.recv(), timeout=2.0)
                    data = json.loads(message)
                    test_results["messages_received"] += 1

                    # Process different message types
                    msg_type = data.get('type', 'unknown')

                    if msg_type in ['video_frame', 'vision_data']:
                        # Count video frames
                        if 'frame' in data:
                            test_results["video_frames"] += 1

                        # Collect metrics
                        if 'fps' in data:
                            test_results["fps_values"].append(data['fps'])

                        if 'gpu_utilization' in data:
                            test_results["gpu_values"].append(data['gpu_utilization'])

                        if 'system_memory_mb' in data:
                            test_results["memory_values"].append(data['system_memory_mb'])

                        if 'temperature_c' in data:
                            test_results["temp_values"].append(data['temperature_c'])

                        if 'cpu_utilization' in data:
                            test_results["cpu_values"].append(data['cpu_utilization'])

                        # Count detections
                        if 'detections' in data:
                            test_results["detections_count"] += len(data['detections'])

                    # Print status every 5 seconds
                    if time.time() - last_status_time >= 5:
                        elapsed = int(time.time() - start_time)
                        print(f"[{elapsed}s] Messages: {test_results['messages_received']}, "
                              f"Frames: {test_results['video_frames']}, "
                              f"Detections: {test_results['detections_count']}")
                        last_status_time = time.time()

                except asyncio.TimeoutError:
                    print("⚠️  Timeout waiting for message (2s)")
                    continue
                except json.JSONDecodeError as e:
                    test_results["errors"].append(f"JSON decode error: {str(e)}")
                    continue

    except Exception as e:
        print(f"\n❌ Connection error: {str(e)}")
        test_results["errors"].append(f"Connection error: {str(e)}")
        return False

    return True

def print_test_results():
    """Print comprehensive test results"""
    print("\n" + "=" * 80)
    print("TEST RESULTS SUMMARY")
    print("=" * 80 + "\n")

    # Connection status
    print(f"WebSocket Connected: {'✅ YES' if test_results['websocket_connected'] else '❌ NO'}")
    print(f"Total Messages Received: {test_results['messages_received']}")
    print(f"Video Frames Received: {test_results['video_frames']}")
    print(f"Total Detections: {test_results['detections_count']}\n")

    # FPS Analysis
    if test_results['fps_values']:
        avg_fps = sum(test_results['fps_values']) / len(test_results['fps_values'])
        min_fps = min(test_results['fps_values'])
        max_fps = max(test_results['fps_values'])
        print(f"FPS Stats:")
        print(f"  Average: {avg_fps:.2f}")
        print(f"  Min: {min_fps:.2f}")
        print(f"  Max: {max_fps:.2f}")
        print(f"  Samples: {len(test_results['fps_values'])}")
        print(f"  Status: {'✅ PASS' if avg_fps >= 8.9 else '❌ FAIL'} (Required: >= 8.9 FPS)\n")
    else:
        print("FPS Stats: ❌ NO DATA\n")

    # GPU Analysis
    if test_results['gpu_values']:
        avg_gpu = sum(test_results['gpu_values']) / len(test_results['gpu_values'])
        min_gpu = min(test_results['gpu_values'])
        max_gpu = max(test_results['gpu_values'])
        print(f"GPU Utilization:")
        print(f"  Average: {avg_gpu:.1f}%")
        print(f"  Min: {min_gpu:.1f}%")
        print(f"  Max: {max_gpu:.1f}%")
        print(f"  Samples: {len(test_results['gpu_values'])}")
        print(f"  Status: {'⚠️  WARNING' if avg_gpu >= 85 else '✅ SAFE'}\n")
    else:
        print("GPU Utilization: ❌ NO DATA\n")

    # Memory Analysis
    if test_results['memory_values']:
        avg_mem = sum(test_results['memory_values']) / len(test_results['memory_values'])
        min_mem = min(test_results['memory_values'])
        max_mem = max(test_results['memory_values'])
        print(f"System Memory:")
        print(f"  Average: {avg_mem:.1f} MB ({avg_mem/1024:.2f} GB)")
        print(f"  Min: {min_mem:.1f} MB")
        print(f"  Max: {max_mem:.1f} MB")
        print(f"  Samples: {len(test_results['memory_values'])}")
        print(f"  Status: {'⚠️  WARNING' if avg_mem >= 7000 else '✅ SAFE'}\n")
    else:
        print("System Memory: ❌ NO DATA\n")

    # Temperature Analysis
    if test_results['temp_values']:
        avg_temp = sum(test_results['temp_values']) / len(test_results['temp_values'])
        min_temp = min(test_results['temp_values'])
        max_temp = max(test_results['temp_values'])
        print(f"Temperature:")
        print(f"  Average: {avg_temp:.1f}°C")
        print(f"  Min: {min_temp:.1f}°C")
        print(f"  Max: {max_temp:.1f}°C")
        print(f"  Samples: {len(test_results['temp_values'])}")
        print(f"  Status: {'❌ DANGER' if avg_temp >= 70 else '⚠️  WARNING' if avg_temp >= 60 else '✅ SAFE'}\n")
    else:
        print("Temperature: ❌ NO DATA\n")

    # CPU Analysis
    if test_results['cpu_values']:
        avg_cpu = sum(test_results['cpu_values']) / len(test_results['cpu_values'])
        min_cpu = min(test_results['cpu_values'])
        max_cpu = max(test_results['cpu_values'])
        print(f"CPU Utilization:")
        print(f"  Average: {avg_cpu:.1f}%")
        print(f"  Min: {min_cpu:.1f}%")
        print(f"  Max: {max_cpu:.1f}%")
        print(f"  Samples: {len(test_results['cpu_values'])}")
        print(f"  Status: {'⚠️  WARNING' if avg_cpu >= 80 else '✅ SAFE'}\n")
    else:
        print("CPU Utilization: ❌ NO DATA\n")

    # Errors
    if test_results['errors']:
        print(f"Errors Encountered: {len(test_results['errors'])}")
        for i, error in enumerate(test_results['errors'], 1):
            print(f"  {i}. {error}")
        print()

    # Overall Assessment
    print("=" * 80)
    print("OVERALL ASSESSMENT")
    print("=" * 80)

    passed_checks = 0
    total_checks = 0

    # Check 1: WebSocket connected
    total_checks += 1
    if test_results['websocket_connected']:
        passed_checks += 1
        print("✅ WebSocket Connection: PASS")
    else:
        print("❌ WebSocket Connection: FAIL")

    # Check 2: Messages received
    total_checks += 1
    if test_results['messages_received'] > 10:
        passed_checks += 1
        print("✅ Message Reception: PASS")
    else:
        print("❌ Message Reception: FAIL")

    # Check 3: Video frames
    total_checks += 1
    if test_results['video_frames'] > 10:
        passed_checks += 1
        print("✅ Video Frame Reception: PASS")
    else:
        print("❌ Video Frame Reception: FAIL")

    # Check 4: FPS acceptable
    total_checks += 1
    if test_results['fps_values'] and sum(test_results['fps_values'])/len(test_results['fps_values']) >= 8.9:
        passed_checks += 1
        print("✅ FPS Performance: PASS")
    else:
        print("❌ FPS Performance: FAIL")

    # Check 5: Metrics data present
    total_checks += 1
    if all([test_results['gpu_values'], test_results['memory_values'],
            test_results['temp_values'], test_results['cpu_values']]):
        passed_checks += 1
        print("✅ Metrics Data Collection: PASS")
    else:
        print("❌ Metrics Data Collection: FAIL")

    pass_rate = (passed_checks / total_checks * 100) if total_checks > 0 else 0

    print(f"\nPass Rate: {passed_checks}/{total_checks} ({pass_rate:.1f}%)")

    if pass_rate == 100:
        print("\n✅ ALL AUTOMATED TESTS PASSED - Ready for manual browser testing")
        return True
    elif pass_rate >= 80:
        print("\n⚠️  MOST TESTS PASSED - Minor issues detected")
        return True
    else:
        print("\n❌ CRITICAL FAILURES - Not ready for production")
        return False

async def main():
    """Main test execution"""
    success = await test_websocket_connection()
    overall_pass = print_test_results()

    print("\n" + "=" * 80)
    if overall_pass:
        print("TEST SUITE: ✅ PASSED")
    else:
        print("TEST SUITE: ❌ FAILED")
    print("=" * 80 + "\n")

    return 0 if overall_pass else 1

if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        exit(exit_code)
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
        exit(2)
    except Exception as e:
        print(f"\n\nFATAL ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        exit(3)
