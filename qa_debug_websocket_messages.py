#!/usr/bin/env python3
"""Debug WebSocket messages to see what's actually being sent"""

import asyncio
import websockets
import json

VISION_WS_URL = "ws://localhost:8767"
AUTH_TOKEN = "fd81ba71-43f6-4bb3-afb5-e8dc3f9eb12e"

async def debug_messages():
    ws_url = f"{VISION_WS_URL}?token={AUTH_TOKEN}"
    print(f"Connecting to {ws_url}...\n")

    async with websockets.connect(ws_url) as websocket:
        print("Connected! Receiving first 5 messages:\n")

        for i in range(5):
            message = await websocket.recv()
            data = json.loads(message)

            print(f"Message {i+1}:")
            print(f"  Type: {data.get('type', 'NO TYPE')}")
            print(f"  Keys: {list(data.keys())[:10]}")  # First 10 keys
            print(f"  Sample data:")

            for key, value in list(data.items())[:8]:
                if isinstance(value, str) and len(value) > 100:
                    print(f"    {key}: <long string, length {len(value)}>")
                elif isinstance(value, list) and len(value) > 5:
                    print(f"    {key}: <list with {len(value)} items>")
                else:
                    print(f"    {key}: {value}")
            print()

asyncio.run(debug_messages())
