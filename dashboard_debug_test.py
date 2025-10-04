#!/usr/bin/env python3
"""
Dashboard Video Debug Test
Comprehensive verification of WebSocket streaming and dashboard functionality
"""

import websocket
import json
import time
import threading
import base64
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class DashboardDebugger:
    def __init__(self):
        self.vision_connected = False
        self.behavioral_connected = False
        self.vision_frames_received = 0
        self.behavioral_messages_received = 0
        self.last_frame_size = 0
        self.last_detection_count = 0
        self.test_duration = 30  # seconds

    def test_vision_websocket(self):
        """Test vision WebSocket connection and streaming"""
        logger.info("Testing Vision WebSocket (port 8767)...")

        try:
            ws = websocket.create_connection('ws://localhost:8767', timeout=10)
            self.vision_connected = True
            logger.info("✓ Vision WebSocket connected")

            # Set timeout for receiving messages
            ws.settimeout(5)

            start_time = time.time()
            while time.time() - start_time < self.test_duration:
                try:
                    message = ws.recv()
                    data = json.loads(message)

                    if data.get('type') == 'vision_data':
                        self.vision_frames_received += 1

                        # Check frame data
                        if 'frame' in data:
                            self.last_frame_size = len(data['frame'])

                        # Check detections
                        if 'detections' in data:
                            self.last_detection_count = len(data['detections'])

                        # Log progress every 10 frames
                        if self.vision_frames_received % 10 == 0:
                            logger.info(f"Vision frames received: {self.vision_frames_received}")

                    elif data.get('type') == 'connection_status':
                        logger.info(f"Vision status: {data.get('message', 'Connected')}")

                except websocket._exceptions.WebSocketTimeoutException:
                    # Normal timeout, continue
                    continue
                except json.JSONDecodeError as e:
                    # Might be binary data or invalid JSON
                    logger.warning(f"Non-JSON data received: {len(message)} bytes")
                    continue
                except Exception as e:
                    logger.error(f"Error receiving vision data: {e}")
                    break

            ws.close()
            logger.info(f"✓ Vision test completed: {self.vision_frames_received} frames received")

        except Exception as e:
            logger.error(f"✗ Vision WebSocket test failed: {e}")
            self.vision_connected = False

    def test_behavioral_websocket(self):
        """Test behavioral WebSocket connection"""
        logger.info("Testing Behavioral WebSocket (port 8768)...")

        try:
            ws = websocket.create_connection('ws://localhost:8768', timeout=10)
            self.behavioral_connected = True
            logger.info("✓ Behavioral WebSocket connected")

            # Send test command
            test_command = {
                'type': 'request_data',
                'timestamp': datetime.now().isoformat()
            }
            ws.send(json.dumps(test_command))

            # Receive responses for a short time
            ws.settimeout(5)
            start_time = time.time()

            while time.time() - start_time < 10:  # Shorter test for behavioral
                try:
                    message = ws.recv()
                    self.behavioral_messages_received += 1
                    data = json.loads(message)
                    logger.info(f"Behavioral message type: {data.get('type', 'unknown')}")

                except websocket._exceptions.WebSocketTimeoutException:
                    continue
                except Exception as e:
                    logger.error(f"Error receiving behavioral data: {e}")
                    break

            ws.close()
            logger.info(f"✓ Behavioral test completed: {self.behavioral_messages_received} messages received")

        except Exception as e:
            logger.error(f"✗ Behavioral WebSocket test failed: {e}")
            self.behavioral_connected = False

    def run_comprehensive_test(self):
        """Run comprehensive dashboard debug test"""
        logger.info("=== DASHBOARD VIDEO DEBUG TEST STARTING ===")

        # Test both WebSockets in parallel
        vision_thread = threading.Thread(target=self.test_vision_websocket)
        behavioral_thread = threading.Thread(target=self.test_behavioral_websocket)

        vision_thread.start()
        time.sleep(2)  # Stagger the start
        behavioral_thread.start()

        # Wait for both tests to complete
        vision_thread.join()
        behavioral_thread.join()

        # Generate report
        self.generate_report()

    def generate_report(self):
        """Generate comprehensive test report"""
        logger.info("\n" + "="*60)
        logger.info("DASHBOARD VIDEO DEBUG REPORT")
        logger.info("="*60)

        logger.info(f"Vision WebSocket (8767):")
        logger.info(f"  Status: {'✓ CONNECTED' if self.vision_connected else '✗ FAILED'}")
        logger.info(f"  Frames received: {self.vision_frames_received}")
        logger.info(f"  Last frame size: {self.last_frame_size} bytes")
        logger.info(f"  Last detection count: {self.last_detection_count}")

        logger.info(f"\nBehavioral WebSocket (8768):")
        logger.info(f"  Status: {'✓ CONNECTED' if self.behavioral_connected else '✗ FAILED'}")
        logger.info(f"  Messages received: {self.behavioral_messages_received}")

        # Overall assessment
        vision_ok = self.vision_connected and self.vision_frames_received > 0
        behavioral_ok = self.behavioral_connected

        logger.info(f"\n=== OVERALL ASSESSMENT ===")
        logger.info(f"Vision Streaming: {'✓ WORKING' if vision_ok else '✗ ISSUES'}")
        logger.info(f"Behavioral System: {'✓ WORKING' if behavioral_ok else '✗ ISSUES'}")

        if vision_ok and behavioral_ok:
            logger.info("🎉 DASHBOARD READY - Video feeds should be working properly!")
        elif vision_ok:
            logger.info("⚠️  PARTIAL SUCCESS - Vision working, behavioral system issues")
        elif behavioral_ok:
            logger.info("⚠️  PARTIAL SUCCESS - Behavioral working, vision system issues")
        else:
            logger.info("❌ BOTH SYSTEMS HAVE ISSUES - Dashboard not ready")

        return vision_ok and behavioral_ok

if __name__ == "__main__":
    debugger = DashboardDebugger()
    success = debugger.run_comprehensive_test()

    if success:
        print("\n🎯 READY FOR DASHBOARD TESTING")
        print("You can now:")
        print("1. Open dashboard_with_vision.html in Firefox")
        print("2. Check that video feeds are displaying")
        print("3. Verify WebSocket connections show 'Connected'")
    else:
        print("\n⚠️  ISSUES DETECTED - Check logs above for details")