#!/usr/bin/env python3
"""Verify exact structure of stats object from WebSocket"""

import asyncio
import websockets
import json

async def verify_stats():
    ws_url = "ws://localhost:8767?token=fd81ba71-43f6-4bb3-afb5-e8dc3f9eb12e"
    async with websockets.connect(ws_url) as ws:
        for i in range(3):
            msg = await ws.recv()
            data = json.loads(msg)
            if 'stats' in data:
                print(f"\nMessage {i+1} stats structure:")
                print(json.dumps(data['stats'], indent=2))
                return data['stats']

stats = asyncio.run(verify_stats())
print("\n=== STATS KEYS ===")
for key in sorted(stats.keys()):
    print(f"  {key}: {stats[key]}")
