#!/usr/bin/env python3
"""
Quick test to verify live camera feed is working via WebSocket
"""

import asyncio
import websockets
import json
import base64
import cv2
import numpy as np

async def test_live_feed():
    """Test the live camera feed WebSocket connection"""
    try:
        async with websockets.connect("ws://localhost:8767") as websocket:
            print("✓ Connected to WebSocket server on port 8767")

            # Wait for a frame
            message = await asyncio.wait_for(websocket.recv(), timeout=5.0)
            data = json.loads(message)

            print(f"✓ Received data with keys: {list(data.keys())}")

            # Check if we have a frame
            if 'frame' in data:
                # Decode the frame to verify it's real camera data
                frame_data = base64.b64decode(data['frame'])
                nparr = np.frombuffer(frame_data, np.uint8)
                frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

                if frame is not None:
                    h, w, c = frame.shape
                    print(f"✓ Live camera frame received: {w}x{h}x{c}")

                    # Check if it's NOT a solid color (synthetic frame indicator)
                    unique_colors = len(np.unique(frame.reshape(-1, frame.shape[-1]), axis=0))
                    if unique_colors > 100:  # Real camera should have many colors
                        print("✓ LIVE CAMERA CONFIRMED: Real camera data detected")
                        print(f"  - Frame diversity: {unique_colors} unique colors")
                        status = "LIVE"
                    else:
                        print("⚠ WARNING: Frame appears synthetic (low color diversity)")
                        status = "SIMULATED"
                else:
                    print("✗ ERROR: Could not decode frame")
                    status = "ERROR"
            else:
                print("✗ ERROR: No frame data in message")
                status = "ERROR"

            # Check detection data
            if 'detections' in data:
                detections = data['detections']
                print(f"✓ Detection system active: {len(detections)} detections")

            # Check status field
            if 'status' in data:
                reported_status = data['status']
                print(f"✓ System reports status: {reported_status}")
                if reported_status.upper() == "LIVE":
                    print("✓ STATUS CONFIRMED: System reports LIVE mode")
                else:
                    print(f"⚠ WARNING: System reports {reported_status} mode")

            return status

    except asyncio.TimeoutError:
        print("✗ ERROR: Timeout waiting for frame data")
        return "TIMEOUT"
    except Exception as e:
        print(f"✗ ERROR: Connection failed: {e}")
        return "ERROR"

if __name__ == "__main__":
    print("=== Live Feed Verification Test ===")
    result = asyncio.run(test_live_feed())
    print(f"\nFINAL RESULT: {result}")

    if result == "LIVE":
        print("🎉 SUCCESS: Live camera feed is working!")
    else:
        print("❌ ISSUE: Live camera feed not confirmed")