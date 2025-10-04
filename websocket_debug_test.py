#!/usr/bin/env python3
"""
WebSocket Debug Test for R2D2 Vision System
Tests WebSocket connectivity and video frame reception
"""

import asyncio
import websockets
import json
import time
import base64
from datetime import datetime

class WebSocketDebugger:
    def __init__(self):
        self.connection_attempts = 0
        self.frames_received = 0
        self.last_frame_time = None
        self.connection_start_time = None

    async def test_websocket_connection(self, url="ws://localhost:8767"):
        """Test WebSocket connection to vision system"""
        print(f"🔍 Testing WebSocket connection to: {url}")

        try:
            self.connection_attempts += 1
            self.connection_start_time = time.time()

            # Attempt connection with timeout
            async with websockets.connect(url, timeout=10) as websocket:
                print(f"✅ WebSocket connected successfully!")
                print(f"   Connection time: {time.time() - self.connection_start_time:.2f}s")

                # Test communication
                start_time = time.time()
                timeout_duration = 30  # 30 seconds test

                while time.time() - start_time < timeout_duration:
                    try:
                        # Wait for message with timeout
                        message = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                        data = json.loads(message)

                        message_type = data.get('type', 'unknown')
                        current_time = datetime.now().strftime("%H:%M:%S.%f")[:-3]

                        if message_type == 'connection_status':
                            print(f"📡 [{current_time}] Connection Status: {data.get('status')}")
                            print(f"   Message: {data.get('message')}")
                            print(f"   Optimizations: {data.get('optimizations_enabled')}")

                        elif message_type == 'video_frame':
                            self.frames_received += 1
                            frame_data = data.get('frame')

                            if frame_data:
                                # Validate base64 frame data
                                try:
                                    decoded_frame = base64.b64decode(frame_data)
                                    frame_size = len(decoded_frame)
                                    print(f"🎥 [{current_time}] Video Frame #{self.frames_received}")
                                    print(f"   Frame size: {frame_size:,} bytes ({frame_size/1024:.1f} KB)")

                                    # Calculate FPS
                                    if self.last_frame_time:
                                        fps = 1.0 / (time.time() - self.last_frame_time)
                                        print(f"   Current FPS: {fps:.1f}")

                                    self.last_frame_time = time.time()

                                except Exception as e:
                                    print(f"❌ Invalid frame data: {e}")
                            else:
                                print(f"⚠️  [{current_time}] Empty video frame received")

                        elif message_type == 'character_vision_data':
                            self.frames_received += 1
                            frame_data = data.get('frame')
                            detections = data.get('detections', [])

                            print(f"👁️  [{current_time}] Character Vision Frame #{self.frames_received}")
                            print(f"   Detections: {len(detections)}")

                            if frame_data:
                                try:
                                    decoded_frame = base64.b64decode(frame_data)
                                    frame_size = len(decoded_frame)
                                    print(f"   Frame size: {frame_size:,} bytes")
                                except Exception as e:
                                    print(f"❌ Invalid character frame data: {e}")

                        elif message_type == 'heartbeat':
                            system_status = data.get('system_status', {})
                            print(f"💓 [{current_time}] Heartbeat")
                            print(f"   System FPS: {system_status.get('fps', 'N/A')}")
                            print(f"   Memory: {system_status.get('memory_usage_mb', 'N/A')} MB")
                            print(f"   Errors: {system_status.get('error_count', 'N/A')}")

                        else:
                            print(f"❓ [{current_time}] Unknown message type: {message_type}")

                    except asyncio.TimeoutError:
                        print(f"⏰ No message received in 5 seconds")
                        break
                    except json.JSONDecodeError as e:
                        print(f"❌ JSON decode error: {e}")
                    except Exception as e:
                        print(f"❌ Message processing error: {e}")

                # Summary
                total_time = time.time() - start_time
                avg_fps = self.frames_received / total_time if total_time > 0 else 0

                print(f"\n📊 Test Summary:")
                print(f"   Duration: {total_time:.1f}s")
                print(f"   Frames received: {self.frames_received}")
                print(f"   Average FPS: {avg_fps:.1f}")
                print(f"   Connection stable: {'✅ Yes' if self.frames_received > 0 else '❌ No'}")

        except ConnectionRefusedError:
            print(f"❌ Connection refused - Vision system may not be running")
        except asyncio.TimeoutError:
            print(f"❌ Connection timeout - Vision system not responding")
        except OSError as e:
            print(f"❌ Network error: {e}")
        except Exception as e:
            print(f"❌ WebSocket error: {e}")

    async def test_dashboard_connectivity(self):
        """Test connectivity to dashboard system"""
        dashboard_url = "ws://localhost:8766"
        print(f"\n🔍 Testing Dashboard WebSocket connection to: {dashboard_url}")

        try:
            async with websockets.connect(dashboard_url, timeout=5) as websocket:
                print(f"✅ Dashboard WebSocket connected!")
                # Send test message
                await websocket.send(json.dumps({
                    'type': 'test',
                    'message': 'WebSocket debug test'
                }))
                print(f"📤 Test message sent")
        except ConnectionRefusedError:
            print(f"❌ Dashboard connection refused - Dashboard system may not be running")
        except Exception as e:
            print(f"❌ Dashboard WebSocket error: {e}")

async def main():
    """Main debug routine"""
    print("🚀 R2D2 Vision System WebSocket Debugger")
    print("=" * 50)

    debugger = WebSocketDebugger()

    # Test vision system WebSocket
    await debugger.test_websocket_connection()

    # Test dashboard system WebSocket
    await debugger.test_dashboard_connectivity()

    print("\n🏁 Debug test completed")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n⛔ Debug test interrupted by user")
    except Exception as e:
        print(f"\n❌ Debug test failed: {e}")