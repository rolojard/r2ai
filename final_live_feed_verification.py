#!/usr/bin/env python3
"""
Final Live Feed Verification - Confirms live camera is working
"""

import asyncio
import websockets
import json
import base64
import cv2
import numpy as np

async def verify_live_feed():
    """Verify the live camera feed is working properly"""
    try:
        async with websockets.connect("ws://localhost:8767") as websocket:
            print("✓ Connected to WebSocket server on port 8767")

            frame_found = False
            live_confirmed = False

            # Check multiple messages to find frame data
            for attempt in range(5):
                try:
                    message = await asyncio.wait_for(websocket.recv(), timeout=3.0)
                    data = json.loads(message)

                    if data.get('type') == 'character_vision_data' and 'frame' in data:
                        frame_found = True
                        print(f"✓ Frame data received: {len(data['frame'])} bytes")

                        # Decode and analyze frame
                        frame_data = base64.b64decode(data['frame'])
                        nparr = np.frombuffer(frame_data, np.uint8)
                        frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

                        if frame is not None:
                            h, w, c = frame.shape
                            print(f"✓ Frame decoded successfully: {w}x{h}x{c}")

                            # Check for real camera indicators
                            unique_colors = len(np.unique(frame.reshape(-1, frame.shape[-1]), axis=0))
                            mean_brightness = np.mean(frame)

                            print(f"✓ Color diversity: {unique_colors} unique colors")
                            print(f"✓ Mean brightness: {mean_brightness:.1f}")

                            # Real camera should have high color diversity
                            if unique_colors > 1000:
                                live_confirmed = True
                                print("✅ LIVE CAMERA CONFIRMED!")
                                break
                            else:
                                print("⚠ Low color diversity - may be synthetic")

                        # Check metadata
                        if 'camera_type' in data:
                            print(f"✓ Camera type: {data['camera_type']}")
                        if 'source' in data:
                            print(f"✓ Source: {data['source']}")

                        break

                except asyncio.TimeoutError:
                    print(f"Attempt {attempt + 1}: Waiting for frame data...")
                    continue

            return frame_found and live_confirmed

    except Exception as e:
        print(f"✗ Connection error: {e}")
        return False

if __name__ == "__main__":
    print("=== Final Live Feed Verification ===")
    result = asyncio.run(verify_live_feed())

    if result:
        print("\n🎉 SUCCESS: Live camera feed is fully operational!")
        print("  - Camera hardware: ✓ Working")
        print("  - WebSocket streaming: ✓ Working")
        print("  - Frame capture: ✓ Working")
        print("  - Live feed confirmed: ✓ Working")
    else:
        print("\n❌ ISSUE: Live camera feed verification failed")