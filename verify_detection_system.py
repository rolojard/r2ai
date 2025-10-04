#!/usr/bin/env python3
"""
Detection System Verification
Tests that the vision system is sending detection data properly
"""
import asyncio
import websockets
import json
import sys

async def test_vision_feed():
    """Connect to vision WebSocket and verify detection data"""
    uri = "ws://localhost:8767"

    print("=" * 60)
    print("DETECTION SYSTEM VERIFICATION")
    print("=" * 60)
    print(f"Connecting to: {uri}\n")

    try:
        async with websockets.connect(uri) as websocket:
            print("✅ Connected to vision WebSocket\n")

            message_count = 0
            detection_count = 0

            # Monitor for 10 seconds or 20 messages
            while message_count < 20:
                try:
                    message = await asyncio.wait_for(websocket.recv(), timeout=2.0)
                    data = json.loads(message)
                    message_count += 1

                    msg_type = data.get('type', 'unknown')

                    if msg_type == 'character_vision_data':
                        detections = data.get('detections', [])
                        stats = data.get('stats', {})

                        if detections:
                            detection_count += len(detections)
                            print(f"\n📦 Message #{message_count} - DETECTIONS FOUND!")
                            print(f"   Detections: {len(detections)}")

                            for i, det in enumerate(detections[:3]):  # Show first 3
                                print(f"   [{i+1}] {det['class']}: {det['confidence']:.2f}")
                                print(f"       BBox: [{det['bbox'][0]:.0f}, {det['bbox'][1]:.0f}, "
                                      f"{det['bbox'][2]:.0f}, {det['bbox'][3]:.0f}]")
                        else:
                            print(f"Message #{message_count}: No detections (empty scene)")

                        # Show performance stats
                        fps = stats.get('fps', 0)
                        det_time = stats.get('detection_time', 0)
                        print(f"   Stats: FPS={fps:.1f}, Detection={det_time:.1f}ms")

                    elif msg_type == 'connection_status':
                        print(f"✅ {data.get('message', 'Connected')}\n")

                    elif msg_type == 'heartbeat':
                        print("💓 Heartbeat")

                except asyncio.TimeoutError:
                    print("⏱️  Timeout waiting for message")
                    break
                except Exception as e:
                    print(f"❌ Error processing message: {e}")
                    break

            print("\n" + "=" * 60)
            print("VERIFICATION SUMMARY")
            print("=" * 60)
            print(f"Messages received: {message_count}")
            print(f"Total detections: {detection_count}")

            if detection_count > 0:
                print("\n✅ SUCCESS: Detection system is working!")
                print("   - Detections are being sent to dashboard")
                print("   - Bounding boxes should be visible")
            else:
                print("\n⚠️  WARNING: No detections found")
                print("   This is normal if no objects are in camera view")
                print("   Try placing a person or object in front of camera")

            print("=" * 60)

    except ConnectionRefusedError:
        print("❌ ERROR: Could not connect to vision server")
        print("   Make sure r2d2_orin_nano_optimized_vision.py is running")
        sys.exit(1)
    except Exception as e:
        print(f"❌ ERROR: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(test_vision_feed())
