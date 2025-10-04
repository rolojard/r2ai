#!/usr/bin/env python3
"""
Debug script to check frame capture status
"""

import asyncio
import websockets
import json
import time

async def debug_frame_status():
    """Debug the frame capture and streaming status"""
    try:
        async with websockets.connect("ws://localhost:8767") as websocket:
            print("✓ Connected to WebSocket server")

            # Receive multiple messages to see patterns
            for i in range(10):
                try:
                    message = await asyncio.wait_for(websocket.recv(), timeout=2.0)
                    data = json.loads(message)

                    print(f"Message {i+1}:")
                    print(f"  Type: {data.get('type', 'unknown')}")
                    print(f"  Status: {data.get('status', 'unknown')}")
                    print(f"  Keys: {list(data.keys())}")

                    if 'frame' in data:
                        print(f"  Frame data: {len(data['frame'])} bytes")
                        print("  ✓ FRAME DATA FOUND!")
                    else:
                        print("  ⚠ No frame data")

                    if 'detections' in data:
                        print(f"  Detections: {len(data['detections'])}")

                    print()

                except asyncio.TimeoutError:
                    print(f"Message {i+1}: Timeout - no data received")
                    break

                await asyncio.sleep(0.1)

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    print("=== Frame Status Debug ===")
    asyncio.run(debug_frame_status())