#!/usr/bin/env python3
"""
R2D2 Real-time Vision System with WebSocket Streaming
Provides live webcam feed with YOLO object detection for dashboard integration
"""

import cv2
import numpy as np
import json
import time
import threading
import base64
import asyncio
import websockets
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional
import queue
import sys
import os

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class R2D2RealtimeVision:
    """Real-time vision system for R2D2 with WebSocket streaming"""

    def __init__(self, websocket_port=8767, camera_index=0):
        self.websocket_port = websocket_port
        self.camera_index = camera_index
        self.running = False
        self.camera = None
        self.model = None
        self.frame_queue = queue.Queue(maxsize=2)
        self.detection_queue = queue.Queue(maxsize=10)
        self.connected_clients = set()
        self.performance_stats = {
            'fps': 0,
            'detection_time': 0,
            'total_detections': 0,
            'confidence_threshold': 0.5
        }

        # Initialize model
        self._load_yolo_model()

    def _load_yolo_model(self):
        """Load YOLO model for object detection"""
        try:
            from ultralytics import YOLO
            logger.info("Loading YOLOv8 model...")

            # Try to load YOLOv8n model (lightweight for real-time performance)
            self.model = YOLO('yolov8n.pt')

            # Move to GPU if available
            import torch
            if torch.cuda.is_available():
                self.model.to('cuda')
                logger.info("YOLO model loaded on GPU")
            else:
                logger.info("YOLO model loaded on CPU")

            # Set model parameters for optimal performance
            self.model.overrides['verbose'] = False
            self.model.overrides['conf'] = 0.5  # Confidence threshold
            self.model.overrides['iou'] = 0.45   # IoU threshold

        except Exception as e:
            logger.error(f"Failed to load YOLO model: {e}")
            self.model = None

    def _initialize_camera(self):
        """Initialize camera capture"""
        try:
            self.camera = cv2.VideoCapture(self.camera_index)

            if not self.camera.isOpened():
                logger.error("Failed to open camera")
                return False

            # Set camera properties for optimal performance
            self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            self.camera.set(cv2.CAP_PROP_FPS, 30)
            self.camera.set(cv2.CAP_PROP_BUFFERSIZE, 1)

            # Test frame capture
            ret, frame = self.camera.read()
            if not ret:
                logger.error("Failed to read from camera")
                return False

            logger.info(f"Camera initialized: {frame.shape}")
            return True

        except Exception as e:
            logger.error(f"Camera initialization failed: {e}")
            return False

    def _capture_frames(self):
        """Continuous frame capture thread"""
        logger.info("Starting frame capture thread")
        frame_count = 0
        start_time = time.time()

        while self.running:
            try:
                ret, frame = self.camera.read()
                if not ret:
                    logger.warning("Failed to capture frame")
                    continue

                # Calculate FPS
                frame_count += 1
                if frame_count % 30 == 0:
                    elapsed = time.time() - start_time
                    self.performance_stats['fps'] = frame_count / elapsed

                # Add frame to queue (non-blocking)
                try:
                    self.frame_queue.put_nowait(frame.copy())
                except queue.Full:
                    # Remove old frame and add new one
                    try:
                        self.frame_queue.get_nowait()
                        self.frame_queue.put_nowait(frame.copy())
                    except queue.Empty:
                        pass

                time.sleep(0.01)  # Small delay to prevent overwhelming

            except Exception as e:
                logger.error(f"Frame capture error: {e}")
                break

    def _process_detections(self):
        """Process YOLO detections on captured frames"""
        logger.info("Starting detection processing thread")

        while self.running:
            try:
                # Get frame from queue
                frame = self.frame_queue.get(timeout=1.0)

                if self.model is None:
                    continue

                # Run YOLO detection
                start_time = time.time()
                results = self.model(frame, verbose=False)
                detection_time = time.time() - start_time

                self.performance_stats['detection_time'] = detection_time

                # Process detection results
                detections = []
                if results and len(results) > 0:
                    result = results[0]

                    if result.boxes is not None:
                        boxes = result.boxes.cpu().numpy()

                        for box in boxes:
                            # Extract box information
                            x1, y1, x2, y2 = box.xyxy[0]
                            confidence = box.conf[0]
                            class_id = int(box.cls[0])
                            class_name = self.model.names[class_id]

                            if confidence >= self.performance_stats['confidence_threshold']:
                                detections.append({
                                    'class': class_name,
                                    'confidence': float(confidence),
                                    'bbox': [float(x1), float(y1), float(x2), float(y2)],
                                    'class_id': class_id
                                })

                # Draw detections on frame
                annotated_frame = self._draw_detections(frame, detections)

                # Add to detection queue
                detection_data = {
                    'frame': annotated_frame,
                    'detections': detections,
                    'timestamp': datetime.now().isoformat(),
                    'stats': self.performance_stats.copy()
                }

                try:
                    self.detection_queue.put_nowait(detection_data)
                except queue.Full:
                    # Remove old detection and add new one
                    try:
                        self.detection_queue.get_nowait()
                        self.detection_queue.put_nowait(detection_data)
                    except queue.Empty:
                        pass

                self.performance_stats['total_detections'] += len(detections)

            except queue.Empty:
                continue
            except Exception as e:
                logger.error(f"Detection processing error: {e}")

    def _draw_detections(self, frame, detections):
        """Draw detection boxes and labels on frame"""
        annotated_frame = frame.copy()

        for detection in detections:
            x1, y1, x2, y2 = detection['bbox']
            confidence = detection['confidence']
            class_name = detection['class']

            # Draw bounding box
            color = self._get_class_color(detection['class_id'])
            cv2.rectangle(annotated_frame, (int(x1), int(y1)), (int(x2), int(y2)), color, 2)

            # Draw label
            label = f"{class_name} {confidence:.2f}"
            label_size = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)[0]

            # Background for label
            cv2.rectangle(annotated_frame,
                         (int(x1), int(y1) - label_size[1] - 10),
                         (int(x1) + label_size[0], int(y1)),
                         color, -1)

            # Label text
            cv2.putText(annotated_frame, label,
                       (int(x1), int(y1) - 5),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)

        # Add performance info
        fps_text = f"FPS: {self.performance_stats['fps']:.1f}"
        detection_text = f"Detections: {len(detections)}"
        timing_text = f"Detection Time: {self.performance_stats['detection_time']:.3f}s"

        cv2.putText(annotated_frame, fps_text, (10, 30),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        cv2.putText(annotated_frame, detection_text, (10, 60),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        cv2.putText(annotated_frame, timing_text, (10, 90),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

        return annotated_frame

    def _get_class_color(self, class_id):
        """Get consistent color for object class"""
        colors = [
            (255, 0, 0), (0, 255, 0), (0, 0, 255), (255, 255, 0),
            (255, 0, 255), (0, 255, 255), (128, 0, 128), (255, 165, 0),
            (0, 128, 255), (255, 20, 147), (50, 205, 50), (255, 69, 0)
        ]
        return colors[class_id % len(colors)]

    async def _handle_websocket_client(self, websocket):
        """Handle WebSocket client connections"""
        logger.info(f"New client connected: {websocket.remote_address}")
        self.connected_clients.add(websocket)

        try:
            await websocket.send(json.dumps({
                'type': 'connection_status',
                'status': 'connected',
                'message': 'R2D2 Vision System Connected'
            }))

            # Listen for incoming messages
            async def handle_incoming_messages():
                async for message in websocket:
                    try:
                        data = json.loads(message)
                        if data.get('type') == 'update_confidence':
                            threshold = data.get('threshold', 0.5)
                            self.performance_stats['confidence_threshold'] = threshold
                            logger.info(f"Updated confidence threshold to {threshold}")
                    except json.JSONDecodeError:
                        logger.warning("Received invalid JSON message")
                    except Exception as e:
                        logger.error(f"Error handling message: {e}")

            # Start message handler task
            import asyncio
            asyncio.create_task(handle_incoming_messages())

            # Send initial frame and detection data
            while self.running:
                try:
                    # Get latest detection data
                    detection_data = self.detection_queue.get(timeout=0.1)

                    # Encode frame as base64
                    _, buffer = cv2.imencode('.jpg', detection_data['frame'],
                                           [cv2.IMWRITE_JPEG_QUALITY, 80])
                    frame_base64 = base64.b64encode(buffer).decode('utf-8')

                    # Prepare WebSocket message
                    message = {
                        'type': 'vision_data',
                        'frame': frame_base64,
                        'detections': detection_data['detections'],
                        'timestamp': detection_data['timestamp'],
                        'stats': detection_data['stats']
                    }

                    # Send to client
                    await websocket.send(json.dumps(message))

                except queue.Empty:
                    # Send heartbeat
                    await websocket.send(json.dumps({
                        'type': 'heartbeat',
                        'timestamp': datetime.now().isoformat()
                    }))
                    await asyncio.sleep(0.1)

                except websockets.exceptions.ConnectionClosed:
                    break
                except Exception as e:
                    logger.error(f"WebSocket send error: {e}")
                    break

        except websockets.exceptions.ConnectionClosed:
            logger.info("Client disconnected")
        except Exception as e:
            logger.error(f"WebSocket client error: {e}")
        finally:
            self.connected_clients.discard(websocket)

    async def _run_websocket_server(self):
        """Run the WebSocket server"""
        async with websockets.serve(
            self._handle_websocket_client,
            "localhost",
            self.websocket_port
        ):
            logger.info(f"WebSocket server running on port {self.websocket_port}")
            # Keep the server running
            await asyncio.Future()  # Run forever

    def start(self):
        """Start the real-time vision system"""
        logger.info("Starting R2D2 Real-time Vision System")

        # Initialize camera
        if not self._initialize_camera():
            logger.error("Failed to initialize camera")
            return False

        if self.model is None:
            logger.error("YOLO model not available")
            return False

        self.running = True

        # Start capture thread
        capture_thread = threading.Thread(target=self._capture_frames, daemon=True)
        capture_thread.start()

        # Start detection processing thread
        detection_thread = threading.Thread(target=self._process_detections, daemon=True)
        detection_thread.start()

        logger.info(f"R2D2 Vision WebSocket server starting on port {self.websocket_port}")

        # Start WebSocket server using asyncio.run for modern Python
        try:
            asyncio.run(self._run_websocket_server())
        except KeyboardInterrupt:
            logger.info("Shutting down R2D2 Vision System")
        finally:
            self.stop()

        return True

    def stop(self):
        """Stop the vision system"""
        logger.info("Stopping R2D2 Vision System")
        self.running = False

        if self.camera:
            self.camera.release()

        # Close all WebSocket connections
        for client in self.connected_clients.copy():
            try:
                loop = asyncio.get_running_loop()
                loop.create_task(client.close())
            except RuntimeError:
                # No running loop, close synchronously
                asyncio.run(client.close())

def main():
    """Main function to run the R2D2 vision system"""
    print("R2D2 Real-time Vision System")
    print("=" * 40)
    print("Press Ctrl+C to stop")
    print("=" * 40)

    # Check for optional port and camera arguments
    port = 8767
    camera_index = 1  # Default to camera index 1 (C920e detected there)

    if len(sys.argv) > 1:
        try:
            port = int(sys.argv[1])
        except ValueError:
            logger.error("Invalid port number")
            sys.exit(1)

    if len(sys.argv) > 2:
        try:
            camera_index = int(sys.argv[2])
        except ValueError:
            logger.error("Invalid camera index")
            sys.exit(1)

    # Create and start vision system
    vision_system = R2D2RealtimeVision(websocket_port=port, camera_index=camera_index)

    try:
        success = vision_system.start()
        if not success:
            logger.error("Failed to start vision system")
            sys.exit(1)
    except KeyboardInterrupt:
        logger.info("Vision system stopped by user")
    except Exception as e:
        logger.error(f"Vision system error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()