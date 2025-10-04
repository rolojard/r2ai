#!/usr/bin/env python3
"""
Emergency Video Feed Connectivity Test
Tests the complete video feed pipeline: Vision System -> WebSocket -> Dashboard
"""

import asyncio
import websockets
import json
import time
import sys

async def test_vision_websocket():
    """Test connection to vision WebSocket server"""
    try:
        print("🔍 Testing vision WebSocket connection...")
        uri = "ws://localhost:8767"

        async with websockets.connect(uri) as websocket:
            print("✅ Vision WebSocket connected successfully!")

            # Wait for a frame
            print("⏳ Waiting for video frame...")
            frame_data = await asyncio.wait_for(websocket.recv(), timeout=10.0)

            try:
                data = json.loads(frame_data)

                # Handle connection status message
                if data.get('type') == 'connection_status':
                    print(f"📡 Vision system status: {data.get('message', 'Connected')}")
                    # Wait for actual frame data
                    frame_data = await asyncio.wait_for(websocket.recv(), timeout=10.0)
                    data = json.loads(frame_data)

                # Check for vision data with frame
                if data.get('type') == 'vision_data' and 'frame' in data:
                    print("✅ Video frame received successfully!")
                    print(f"   Frame size: {len(data['frame'])} bytes")
                    if 'detections' in data:
                        print(f"   Detections: {len(data['detections'])}")
                    if data.get('simulation'):
                        print("   📹 Using simulated camera (hardware camera unavailable)")
                    return True
                else:
                    print(f"❌ Unexpected message format: {data.get('type', 'unknown')}")
                    return False
            except json.JSONDecodeError:
                print("❌ Invalid JSON received from vision system")
                return False

    except asyncio.TimeoutError:
        print("❌ Timeout waiting for video frame")
        return False
    except Exception as e:
        print(f"❌ Vision WebSocket connection failed: {e}")
        return False

async def test_dashboard_websocket():
    """Test connection to dashboard WebSocket server"""
    try:
        print("🔍 Testing dashboard WebSocket connection...")
        uri = "ws://localhost:8766"

        async with websockets.connect(uri) as websocket:
            print("✅ Dashboard WebSocket connected successfully!")

            # Send a test message
            test_message = {"type": "status_request"}
            await websocket.send(json.dumps(test_message))

            # Wait for response
            response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
            print("✅ Dashboard WebSocket responding!")
            return True

    except Exception as e:
        print(f"❌ Dashboard WebSocket connection failed: {e}")
        return False

async def main():
    """Run comprehensive connectivity tests"""
    print("🚀 R2D2 Video Feed Connectivity Test")
    print("=" * 50)

    # Test vision system
    vision_ok = await test_vision_websocket()
    print()

    # Test dashboard WebSocket
    dashboard_ok = await test_dashboard_websocket()
    print()

    # Overall status
    print("=" * 50)
    if vision_ok and dashboard_ok:
        print("🎉 SUCCESS: Video feed connectivity restored!")
        print("✅ Vision system operational")
        print("✅ Dashboard system operational")
        print("\n🌐 Access dashboard at: http://localhost:8765")
        return 0
    else:
        print("❌ FAILURE: Video feed connectivity issues detected")
        if not vision_ok:
            print("❌ Vision system problems")
        if not dashboard_ok:
            print("❌ Dashboard system problems")
        return 1

if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n⚠️ Test interrupted by user")
        sys.exit(1)