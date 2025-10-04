#!/usr/bin/env python3
"""
Simple YOLO Vision System for R2D2 Dashboard
"""

import cv2
import json
import time
import base64
import asyncio
import websockets
import logging
from datetime import datetime
import threading
import queue

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SimpleYOLOVision:
    def __init__(self):
        self.running = False
        self.camera = None
        self.yolo_model = None
        self.frame_queue = queue.Queue(maxsize=1)
        self.connected_clients = set()

        self._load_yolo()

    def _load_yolo(self):
        try:
            from ultralytics import YOLO
            self.yolo_model = YOLO('yolov8n.pt')
            logger.info("YOLO model loaded")
        except Exception as e:
            logger.error(f"YOLO load failed: {e}")

    def _init_camera(self):
        try:
            self.camera = cv2.VideoCapture(0)
            if not self.camera.isOpened():
                return False
            self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            return True
        except Exception as e:
            logger.error(f"Camera init failed: {e}")
            return False

    def _capture_loop(self):
        while self.running:
            try:
                ret, frame = self.camera.read()
                if ret:
                    try:
                        self.frame_queue.put_nowait(frame)
                    except queue.Full:
                        try:
                            self.frame_queue.get_nowait()
                            self.frame_queue.put_nowait(frame)
                        except:
                            pass
                time.sleep(1/15)  # 15 FPS
            except Exception as e:
                logger.error(f"Capture error: {e}")
                time.sleep(0.1)

    def _process_frame(self, frame):
        try:
            if self.yolo_model:
                results = self.yolo_model(frame, verbose=False)
                detections = []

                if results and len(results) > 0:
                    result = results[0]
                    if result.boxes is not None:
                        boxes = result.boxes.cpu().numpy()
                        for box in boxes:
                            x1, y1, x2, y2 = box.xyxy[0]
                            conf = float(box.conf[0])
                            cls_id = int(box.cls[0])
                            cls_name = self.yolo_model.names[cls_id]

                            if conf > 0.5:
                                detections.append({
                                    'class': cls_name,
                                    'confidence': conf,
                                    'bbox': [float(x1), float(y1), float(x2), float(y2)]
                                })

                                # Draw on frame
                                cv2.rectangle(frame, (int(x1), int(y1)), (int(x2), int(y2)), (0, 255, 0), 2)
                                cv2.putText(frame, f"{cls_name} {conf:.2f}",
                                           (int(x1), int(y1)-10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

                # Add title
                cv2.putText(frame, "R2D2 YOLO VISION", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 255), 2)

                return frame, detections
        except Exception as e:
            logger.error(f"Process error: {e}")

        return frame, []

    async def _handle_client(self, websocket):
        logger.info("Client connected")
        self.connected_clients.add(websocket)

        try:
            await websocket.send(json.dumps({
                'type': 'connection_status',
                'message': 'Connected to R2D2 Vision'
            }))

            while self.running:
                try:
                    if not self.frame_queue.empty():
                        frame = self.frame_queue.get_nowait()
                        processed_frame, detections = self._process_frame(frame)

                        # Encode frame
                        _, buffer = cv2.imencode('.jpg', processed_frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
                        frame_b64 = base64.b64encode(buffer).decode('utf-8')

                        # Create character detections from person detections
                        character_detections = []
                        for det in detections:
                            if det['class'] == 'person':
                                character_detections.append({
                                    'name': 'Detected Person',
                                    'character': 'human',
                                    'confidence': det['confidence'],
                                    'bbox': det['bbox'],
                                    'costume_match': 'civilian',
                                    'r2d2_reaction': {
                                        'primary_emotion': 'curious',
                                        'excitement_level': 'medium'
                                    }
                                })

                        message = {
                            'type': 'character_vision_data',
                            'frame': frame_b64,
                            'detections': detections,
                            'character_detections': character_detections,
                            'timestamp': datetime.now().isoformat(),
                            'stats': {
                                'fps': 15,
                                'detection_time': 0.05,
                                'total_detections': len(detections)
                            }
                        }

                        await websocket.send(json.dumps(message))
                        await asyncio.sleep(1/12)  # 12 FPS streaming
                    else:
                        await asyncio.sleep(0.1)

                except queue.Empty:
                    await asyncio.sleep(0.1)
                except Exception as e:
                    logger.error(f"Send error: {e}")
                    break

        except Exception as e:
            logger.error(f"Client error: {e}")
        finally:
            self.connected_clients.discard(websocket)
            logger.info("Client disconnected")

    async def _run_server(self):
        async with websockets.serve(self._handle_client, "localhost", 8767):
            logger.info("WebSocket server running on port 8767")
            await asyncio.Future()  # Run forever

    def start(self):
        if not self._init_camera():
            logger.error("Camera initialization failed")
            return False

        self.running = True

        # Start capture thread
        capture_thread = threading.Thread(target=self._capture_loop, daemon=True)
        capture_thread.start()

        # Start WebSocket server
        try:
            asyncio.run(self._run_server())
        except KeyboardInterrupt:
            logger.info("Stopping...")
        finally:
            self.running = False
            if self.camera:
                self.camera.release()

        return True

def main():
    vision = SimpleYOLOVision()
    print("Starting Simple YOLO Vision System...")
    print("Press Ctrl+C to stop")
    vision.start()

if __name__ == "__main__":
    main()