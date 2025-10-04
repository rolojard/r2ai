#!/usr/bin/env python3
"""
Analyze Vision System Messages
"""

import asyncio
import websockets
import json
import time

async def analyze_messages():
    """Analyze the actual message format from vision system"""
    print("🔍 Analyzing vision system messages...")

    try:
        websocket = await websockets.connect("ws://localhost:8767")
        print("✅ Connected to vision system")

        # Analyze first few messages
        for i in range(5):
            try:
                message = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                data = json.loads(message)

                print(f"\n📨 Message {i+1}:")
                print(f"   Type: {data.get('type', 'MISSING')}")
                print(f"   Keys: {list(data.keys())}")

                # Check for frame data
                if 'frame' in data:
                    frame_data = data['frame']
                    if frame_data:
                        print(f"   Frame data: Present ({len(frame_data)} chars)")
                    else:
                        print(f"   Frame data: Empty")
                else:
                    print(f"   Frame data: None")

                # Print first 200 chars of message for debugging
                message_preview = str(data)[:200] + "..." if len(str(data)) > 200 else str(data)
                print(f"   Preview: {message_preview}")

            except asyncio.TimeoutError:
                print(f"⏰ Timeout on message {i+1}")
                break
            except Exception as e:
                print(f"❌ Error on message {i+1}: {e}")

        await websocket.close()

    except Exception as e:
        print(f"❌ Connection failed: {e}")

if __name__ == "__main__":
    asyncio.run(analyze_messages())