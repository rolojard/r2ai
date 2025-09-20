#!/usr/bin/env python3
"""
Quick test script to validate vision system setup
"""

import sys
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_imports():
    """Test all required imports"""
    logger.info("Testing required imports...")

    try:
        import cv2
        logger.info(f"✅ OpenCV: {cv2.__version__}")
    except ImportError as e:
        logger.error(f"❌ OpenCV: {e}")
        return False

    try:
        import torch
        logger.info(f"✅ PyTorch: {torch.__version__}")
        if torch.cuda.is_available():
            logger.info(f"✅ CUDA: {torch.version.cuda} on {torch.cuda.get_device_name(0)}")
        else:
            logger.warning("⚠️ CUDA not available")
    except ImportError as e:
        logger.error(f"❌ PyTorch: {e}")
        return False

    try:
        from ultralytics import YOLO
        import ultralytics
        logger.info(f"✅ Ultralytics: {ultralytics.__version__}")
    except ImportError as e:
        logger.error(f"❌ Ultralytics: {e}")
        return False

    try:
        import websockets
        logger.info("✅ WebSockets available")
    except ImportError as e:
        logger.error(f"❌ WebSockets: {e}")
        return False

    try:
        import numpy as np
        logger.info(f"✅ NumPy: {np.__version__}")
    except ImportError as e:
        logger.error(f"❌ NumPy: {e}")
        return False

    return True

def test_camera():
    """Test camera access"""
    logger.info("Testing camera access...")

    try:
        import cv2
        cap = cv2.VideoCapture(0)

        if cap.isOpened():
            ret, frame = cap.read()
            if ret and frame is not None:
                logger.info(f"✅ Camera: {frame.shape} resolution")
                cap.release()
                return True
            else:
                logger.warning("⚠️ Camera opened but no frame captured")
                cap.release()
                return False
        else:
            logger.warning("⚠️ Camera not accessible")
            return False

    except Exception as e:
        logger.error(f"❌ Camera test failed: {e}")
        return False

def test_yolo():
    """Test YOLO model loading"""
    logger.info("Testing YOLO model...")

    try:
        from ultralytics import YOLO
        import torch
        import numpy as np

        # Load model
        model = YOLO('yolov8n.pt')
        logger.info("✅ YOLO model loaded")

        # Test GPU assignment
        if torch.cuda.is_available():
            model.to('cuda')
            logger.info("✅ Model moved to GPU")

        # Test inference
        dummy_frame = np.random.randint(0, 255, (640, 480, 3), dtype=np.uint8)
        results = model(dummy_frame, verbose=False)
        logger.info("✅ YOLO inference test passed")

        return True

    except Exception as e:
        logger.error(f"❌ YOLO test failed: {e}")
        return False

def test_websocket_server():
    """Test WebSocket server functionality"""
    logger.info("Testing WebSocket server setup...")

    try:
        import websockets
        import asyncio
        import json

        async def test_server():
            try:
                # Simple echo server for testing
                async def echo_handler(websocket, path):
                    await websocket.send(json.dumps({"type": "test", "message": "hello"}))

                # This just tests that we can create a server
                server = await websockets.serve(echo_handler, "localhost", 8768)
                logger.info("✅ WebSocket server can be created")
                server.close()
                await server.wait_closed()
                return True

            except Exception as e:
                logger.error(f"❌ WebSocket server test failed: {e}")
                return False

        # Run the test
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(test_server())
        loop.close()

        return result

    except Exception as e:
        logger.error(f"❌ WebSocket test failed: {e}")
        return False

def main():
    """Main test function"""
    logger.info("🎯 R2D2 Vision System Setup Validation")
    logger.info("=" * 50)

    tests = [
        ("Import Dependencies", test_imports),
        ("Camera Access", test_camera),
        ("YOLO Model", test_yolo),
        ("WebSocket Server", test_websocket_server)
    ]

    passed = 0
    total = len(tests)

    for test_name, test_func in tests:
        logger.info(f"\n🔍 Testing: {test_name}")
        try:
            if test_func():
                passed += 1
                logger.info(f"✅ {test_name}: PASSED")
            else:
                logger.error(f"❌ {test_name}: FAILED")
        except Exception as e:
            logger.error(f"❌ {test_name}: ERROR - {e}")

    logger.info("=" * 50)
    logger.info(f"📊 Test Results: {passed}/{total} tests passed")

    if passed == total:
        logger.info("🎉 All tests passed! Vision system ready for deployment.")
        return 0
    else:
        logger.warning(f"⚠️ {total - passed} test(s) failed. Please check the issues above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())