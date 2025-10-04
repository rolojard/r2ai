#!/usr/bin/env python3
"""
Simple WebSocket Test for R2D2 Vision System
"""

import asyncio
import websockets
import json
import time

async def test_vision_websocket():
    """Test basic WebSocket connectivity"""
    print("🔍 Testing WebSocket connection to ws://localhost:8767")

    try:
        # Simple connection test
        websocket = await websockets.connect("ws://localhost:8767")
        print("✅ WebSocket connected successfully!")

        # Listen for a few messages
        for i in range(10):
            try:
                message = await asyncio.wait_for(websocket.recv(), timeout=3.0)
                data = json.loads(message)
                msg_type = data.get('type', 'unknown')
                print(f"📨 Message {i+1}: {msg_type}")

                if msg_type == 'video_frame':
                    frame_data = data.get('frame')
                    if frame_data:
                        print(f"   🎥 Video frame received (size: {len(frame_data)} chars)")
                    else:
                        print(f"   ⚠️ Empty video frame")

                elif msg_type == 'character_vision_data':
                    frame_data = data.get('frame')
                    detections = data.get('detections', [])
                    print(f"   👁️ Character vision frame with {len(detections)} detections")
                    if frame_data:
                        print(f"   🎥 Frame data present (size: {len(frame_data)} chars)")
                    else:
                        print(f"   ⚠️ No frame data")

                elif msg_type == 'heartbeat':
                    print(f"   💓 Heartbeat received")

            except asyncio.TimeoutError:
                print(f"⏰ Timeout waiting for message {i+1}")
                break
            except Exception as e:
                print(f"❌ Error processing message {i+1}: {e}")

        await websocket.close()

    except Exception as e:
        print(f"❌ Connection failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_vision_websocket())