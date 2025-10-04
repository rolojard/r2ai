#!/usr/bin/env python3
"""
Final Dashboard Video Verification
Comprehensive test of all dashboard video components
"""

import websocket
import json
import time
import threading
import sys
from datetime import datetime

def test_websocket_connection(port, name, timeout=10):
    """Test WebSocket connection"""
    try:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Testing {name} on port {port}...")

        ws = websocket.create_connection(f'ws://localhost:{port}', timeout=timeout)
        print(f"✓ {name}: Connected successfully")

        # Try to receive first message
        ws.settimeout(5)
        try:
            message = ws.recv()
            data = json.loads(message)
            print(f"✓ {name}: Received initial message - {data.get('type', 'unknown')}")

            # For vision system, try to get a few more messages
            if port == 8767:
                frames = 0
                for _ in range(5):
                    try:
                        message = ws.recv()
                        data = json.loads(message)
                        if data.get('type') == 'vision_data':
                            frames += 1
                            frame_size = len(data.get('frame', ''))
                            detections = len(data.get('detections', []))
                            print(f"✓ {name}: Frame {frames} - {frame_size} bytes, {detections} detections")
                    except websocket._exceptions.WebSocketTimeoutException:
                        break
                    except:
                        break

                if frames > 0:
                    print(f"✓ {name}: Video streaming working ({frames} frames)")
                    ws.close()
                    return True, frames
                else:
                    print(f"⚠ {name}: Connected but no video frames")
                    ws.close()
                    return True, 0

        except websocket._exceptions.WebSocketTimeoutException:
            print(f"⚠ {name}: Connected but no immediate response")

        ws.close()
        return True, 0

    except Exception as e:
        print(f"✗ {name}: Connection failed - {str(e)}")
        return False, 0

def generate_dashboard_status_report():
    """Generate comprehensive dashboard status report"""
    print("\n" + "="*60)
    print("R2D2 DASHBOARD VIDEO VERIFICATION REPORT")
    print("="*60)
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    # Test vision system
    vision_connected, vision_frames = test_websocket_connection(8767, "Vision System", timeout=15)

    # Test behavioral system
    behavioral_connected, _ = test_websocket_connection(8768, "Behavioral System", timeout=10)

    print("\n" + "="*60)
    print("DASHBOARD READINESS ASSESSMENT")
    print("="*60)

    print(f"Vision WebSocket (8767):")
    print(f"  Connection: {'✓ WORKING' if vision_connected else '✗ FAILED'}")
    print(f"  Video Frames: {'✓ STREAMING' if vision_frames > 0 else '✗ NO FRAMES'}")
    print(f"  Frame Count: {vision_frames}")

    print(f"\nBehavioral WebSocket (8768):")
    print(f"  Connection: {'✓ WORKING' if behavioral_connected else '✗ FAILED'}")

    # Overall assessment
    vision_ready = vision_connected and vision_frames > 0
    dashboard_ready = vision_ready and behavioral_connected

    print(f"\n=== OVERALL STATUS ===")
    if dashboard_ready:
        print("🎉 DASHBOARD FULLY READY")
        print("✓ Both WebSocket connections working")
        print("✓ Video streaming active")
        print("✓ Dashboard should display video feeds properly")
        print("\nNext steps:")
        print("1. Open dashboard_with_vision.html in Firefox")
        print("2. Check video feed displays")
        print("3. Verify connection status shows 'Connected'")

    elif vision_ready:
        print("⚠️ PARTIAL READINESS")
        print("✓ Vision system working with video")
        print("✗ Behavioral system issues")
        print("Dashboard will show video but may lack other features")

    elif vision_connected:
        print("⚠️ LIMITED FUNCTIONALITY")
        print("✓ Vision system connected")
        print("✗ No video frames being streamed")
        print("✗ Behavioral system issues")
        print("Dashboard connections work but no video display")

    else:
        print("❌ DASHBOARD NOT READY")
        print("✗ Vision system not working")
        print("✗ Video streaming not available")
        print("Dashboard will show connection errors")

    print(f"\n{'='*60}")
    return dashboard_ready, vision_ready, vision_connected, behavioral_connected

if __name__ == "__main__":
    print("🎯 R2D2 Dashboard Video Verification")
    print("Testing all WebSocket connections and video streaming...")
    print()

    # Run comprehensive test
    dashboard_ready, vision_ready, vision_connected, behavioral_connected = generate_dashboard_status_report()

    # Exit with appropriate code
    if dashboard_ready:
        print("\n🚀 READY FOR DASHBOARD TESTING!")
        sys.exit(0)
    elif vision_ready:
        print("\n🔶 PARTIAL SUCCESS - VIDEO WORKING")
        sys.exit(1)
    else:
        print("\n🔴 ISSUES DETECTED - SEE REPORT ABOVE")
        sys.exit(2)