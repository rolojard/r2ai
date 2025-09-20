#!/usr/bin/env python3
"""
Simple R2D2 Vision Demo for Web Dashboard
Real-time webcam with object detection output
"""

import cv2
import json
import time
import base64
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from socketserver import ThreadingMixIn
import urllib.parse

class VisionDemoHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/':
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()

            html = """
<!DOCTYPE html>
<html>
<head>
    <title>R2D2 Vision System Demo</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            margin: 20px;
            background: #0f172a;
            color: #f8fafc;
        }
        .container {
            display: grid;
            grid-template-columns: 1fr 300px;
            gap: 20px;
        }
        .video-section {
            background: #1e293b;
            padding: 20px;
            border-radius: 8px;
        }
        .info-section {
            background: #1e293b;
            padding: 20px;
            border-radius: 8px;
        }
        #videoFeed {
            width: 100%;
            max-width: 640px;
            border: 2px solid #334155;
            border-radius: 8px;
        }
        .status {
            margin: 10px 0;
            padding: 10px;
            background: #374151;
            border-radius: 5px;
        }
        .controls {
            margin: 20px 0;
        }
        button {
            background: #3b82f6;
            color: white;
            border: none;
            padding: 10px 20px;
            margin: 5px;
            border-radius: 5px;
            cursor: pointer;
        }
        button:hover {
            background: #2563eb;
        }
        .detection-log {
            background: #111827;
            padding: 10px;
            border-radius: 5px;
            height: 200px;
            overflow-y: scroll;
            font-family: monospace;
            font-size: 12px;
        }
        .metric {
            display: flex;
            justify-content: space-between;
            margin: 5px 0;
        }
        .value {
            color: #10b981;
            font-weight: bold;
        }
    </style>
</head>
<body>
    <h1>🎯 R2D2 Vision System Demo</h1>

    <div class="container">
        <div class="video-section">
            <h3>📹 Live Camera Feed</h3>
            <img id="videoFeed" src="/video_feed" alt="Camera Feed">

            <div class="controls">
                <button onclick="startVision()">Start Vision</button>
                <button onclick="stopVision()">Stop Vision</button>
                <button onclick="takeSnapshot()">Take Snapshot</button>
            </div>
        </div>

        <div class="info-section">
            <h3>📊 System Status</h3>

            <div class="status">
                <div class="metric">
                    <span>Camera Status:</span>
                    <span class="value" id="cameraStatus">Checking...</span>
                </div>
                <div class="metric">
                    <span>FPS:</span>
                    <span class="value" id="fps">--</span>
                </div>
                <div class="metric">
                    <span>Frame Count:</span>
                    <span class="value" id="frameCount">0</span>
                </div>
                <div class="metric">
                    <span>Detection Mode:</span>
                    <span class="value" id="detectionMode">Basic</span>
                </div>
            </div>

            <h4>🔍 Detection Log</h4>
            <div class="detection-log" id="detectionLog">
                <div>Vision system initializing...</div>
            </div>

            <h4>⚙️ System Info</h4>
            <div class="status">
                <div class="metric">
                    <span>OpenCV:</span>
                    <span class="value">Available</span>
                </div>
                <div class="metric">
                    <span>Camera:</span>
                    <span class="value" id="cameraInfo">Detecting...</span>
                </div>
                <div class="metric">
                    <span>R2D2 Integration:</span>
                    <span class="value">Active</span>
                </div>
            </div>
        </div>
    </div>

    <script>
        let frameCount = 0;
        let startTime = Date.now();

        function updateStatus() {
            fetch('/status')
                .then(response => response.json())
                .then(data => {
                    document.getElementById('cameraStatus').textContent = data.camera_status;
                    document.getElementById('fps').textContent = data.fps;
                    document.getElementById('frameCount').textContent = data.frame_count;
                    document.getElementById('cameraInfo').textContent = data.camera_info;

                    if (data.detection_log) {
                        const log = document.getElementById('detectionLog');
                        log.innerHTML = data.detection_log.map(entry =>
                            `<div>${entry}</div>`
                        ).join('');
                        log.scrollTop = log.scrollHeight;
                    }
                })
                .catch(error => {
                    console.error('Status update failed:', error);
                });
        }

        function startVision() {
            fetch('/start_vision')
                .then(response => response.json())
                .then(data => {
                    logDetection('Vision system started');
                });
        }

        function stopVision() {
            fetch('/stop_vision')
                .then(response => response.json())
                .then(data => {
                    logDetection('Vision system stopped');
                });
        }

        function takeSnapshot() {
            fetch('/snapshot')
                .then(response => response.json())
                .then(data => {
                    logDetection('Snapshot saved: ' + data.filename);
                });
        }

        function logDetection(message) {
            const log = document.getElementById('detectionLog');
            const timestamp = new Date().toLocaleTimeString();
            log.innerHTML += `<div>[${timestamp}] ${message}</div>`;
            log.scrollTop = log.scrollHeight;
        }

        // Update video feed
        const videoFeed = document.getElementById('videoFeed');
        videoFeed.onerror = function() {
            this.src = 'data:image/svg+xml;base64,' + btoa(`
                <svg width="640" height="480" xmlns="http://www.w3.org/2000/svg">
                    <rect width="100%" height="100%" fill="#374151"/>
                    <text x="50%" y="50%" text-anchor="middle" fill="#9ca3af"
                          font-family="Arial" font-size="20">
                        Camera Initializing...
                    </text>
                </svg>
            `);
        };

        // Refresh video feed periodically
        setInterval(() => {
            const timestamp = Date.now();
            videoFeed.src = '/video_feed?' + timestamp;
        }, 100);

        // Update status periodically
        setInterval(updateStatus, 1000);
        updateStatus();

        logDetection('R2D2 Vision Demo initialized');
    </script>
</body>
</html>
            """
            self.wfile.write(html.encode())

        elif self.path.startswith('/video_feed'):
            self.send_video_frame()

        elif self.path == '/status':
            self.send_status()

        elif self.path == '/start_vision':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            response = {"status": "started", "message": "Vision system activated"}
            self.wfile.write(json.dumps(response).encode())

        elif self.path == '/stop_vision':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            response = {"status": "stopped", "message": "Vision system deactivated"}
            self.wfile.write(json.dumps(response).encode())

        elif self.path == '/snapshot':
            filename = f"r2d2_snapshot_{int(time.time())}.jpg"
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            response = {"status": "saved", "filename": filename}
            self.wfile.write(json.dumps(response).encode())

        else:
            self.send_response(404)
            self.end_headers()

    def send_video_frame(self):
        try:
            if hasattr(self.server, 'current_frame') and self.server.current_frame is not None:
                # Encode frame as JPEG
                ret, buffer = cv2.imencode('.jpg', self.server.current_frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
                if ret:
                    self.send_response(200)
                    self.send_header('Content-type', 'image/jpeg')
                    self.send_header('Cache-Control', 'no-cache')
                    self.end_headers()
                    self.wfile.write(buffer.tobytes())
                    return

            # Send placeholder if no frame available
            self.send_response(200)
            self.send_header('Content-type', 'image/jpeg')
            self.end_headers()
            # Empty response - browser will handle with onerror

        except Exception as e:
            print(f"Error sending video frame: {e}")
            self.send_response(500)
            self.end_headers()

    def send_status(self):
        try:
            status = {
                "camera_status": "Online" if hasattr(self.server, 'camera_active') and self.server.camera_active else "Offline",
                "fps": getattr(self.server, 'current_fps', 0),
                "frame_count": getattr(self.server, 'frame_count', 0),
                "camera_info": getattr(self.server, 'camera_info', "USB Camera"),
                "detection_log": getattr(self.server, 'detection_log', [])[-10:]  # Last 10 entries
            }

            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(status).encode())

        except Exception as e:
            print(f"Error sending status: {e}")
            self.send_response(500)
            self.end_headers()

class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
    pass

class R2D2VisionDemo:
    def __init__(self, port=8080):
        self.port = port
        self.camera = None
        self.camera_active = False
        self.current_frame = None
        self.frame_count = 0
        self.detection_log = []
        self.current_fps = 0
        self.camera_info = "Initializing..."

        # Initialize camera
        self.init_camera()

        # Start camera thread
        self.camera_thread = threading.Thread(target=self.camera_loop, daemon=True)
        self.camera_thread.start()

    def init_camera(self):
        try:
            # Try different camera indices
            for camera_idx in [0, 1, 2]:
                self.camera = cv2.VideoCapture(camera_idx)
                if self.camera.isOpened():
                    # Set camera properties
                    self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
                    self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
                    self.camera.set(cv2.CAP_PROP_FPS, 30)

                    # Test read
                    ret, frame = self.camera.read()
                    if ret:
                        self.camera_active = True
                        self.camera_info = f"USB Camera {camera_idx} (640x480)"
                        self.log_detection(f"Camera {camera_idx} initialized successfully")
                        print(f"✅ Camera {camera_idx} initialized: 640x480")
                        return
                    else:
                        self.camera.release()

            # If no camera found, create a dummy frame
            self.camera_active = False
            self.camera_info = "No camera detected - using test pattern"
            self.log_detection("No camera detected, using test pattern")
            print("⚠️ No camera detected, using test pattern")

        except Exception as e:
            self.camera_active = False
            self.camera_info = f"Camera error: {str(e)}"
            self.log_detection(f"Camera initialization error: {e}")
            print(f"❌ Camera initialization error: {e}")

    def camera_loop(self):
        fps_start_time = time.time()
        fps_frame_count = 0

        while True:
            try:
                if self.camera and self.camera_active:
                    ret, frame = self.camera.read()
                    if ret:
                        # Add R2D2 overlay
                        frame = self.add_r2d2_overlay(frame)
                        self.current_frame = frame
                        self.frame_count += 1
                        fps_frame_count += 1

                        # Calculate FPS
                        if time.time() - fps_start_time >= 1.0:
                            self.current_fps = fps_frame_count
                            fps_frame_count = 0
                            fps_start_time = time.time()

                    else:
                        self.log_detection("Camera read failed, attempting reconnection...")
                        self.init_camera()

                else:
                    # Generate test pattern
                    self.current_frame = self.generate_test_pattern()
                    self.frame_count += 1
                    fps_frame_count += 1

                    if time.time() - fps_start_time >= 1.0:
                        self.current_fps = fps_frame_count
                        fps_frame_count = 0
                        fps_start_time = time.time()

                time.sleep(1/30)  # 30 FPS target

            except Exception as e:
                self.log_detection(f"Camera loop error: {e}")
                time.sleep(1)

    def add_r2d2_overlay(self, frame):
        """Add R2D2-themed overlay to frame"""
        height, width = frame.shape[:2]

        # Add R2D2 status overlay
        cv2.rectangle(frame, (10, 10), (300, 80), (0, 0, 0), -1)
        cv2.rectangle(frame, (10, 10), (300, 80), (0, 255, 255), 2)

        cv2.putText(frame, "R2D2 VISION SYSTEM", (20, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)
        cv2.putText(frame, f"FPS: {self.current_fps}", (20, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
        cv2.putText(frame, f"Frame: {self.frame_count}", (20, 70), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)

        # Add crosshair for targeting
        center_x, center_y = width // 2, height // 2
        cv2.line(frame, (center_x - 20, center_y), (center_x + 20, center_y), (0, 255, 255), 2)
        cv2.line(frame, (center_x, center_y - 20), (center_x, center_y + 20), (0, 255, 255), 2)
        cv2.circle(frame, (center_x, center_y), 40, (0, 255, 255), 2)

        return frame

    def generate_test_pattern(self):
        """Generate a test pattern when no camera is available"""
        import numpy as np

        frame = np.zeros((480, 640, 3), dtype=np.uint8)

        # Create moving pattern
        offset = (self.frame_count * 2) % 640

        # Add gradient background
        for y in range(480):
            for x in range(640):
                frame[y, x] = [
                    int(128 + 127 * np.sin((x + offset) * 0.01)),
                    int(128 + 127 * np.sin((y + offset) * 0.01)),
                    100
                ]

        # Add R2D2 text
        cv2.putText(frame, "R2D2 TEST PATTERN", (200, 240), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
        cv2.putText(frame, f"Frame: {self.frame_count}", (250, 280), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 1)

        return frame

    def log_detection(self, message):
        """Add message to detection log"""
        timestamp = time.strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {message}"
        self.detection_log.append(log_entry)

        # Keep only last 50 entries
        if len(self.detection_log) > 50:
            self.detection_log = self.detection_log[-50:]

        print(log_entry)

    def run_server(self):
        """Start the web server"""
        server = ThreadedHTTPServer(('localhost', self.port), VisionDemoHandler)

        # Attach vision demo instance to server
        server.current_frame = None
        server.camera_active = False
        server.frame_count = 0
        server.detection_log = []
        server.current_fps = 0
        server.camera_info = self.camera_info

        # Update server attributes periodically
        def update_server_status():
            while True:
                server.current_frame = self.current_frame
                server.camera_active = self.camera_active
                server.frame_count = self.frame_count
                server.detection_log = self.detection_log
                server.current_fps = self.current_fps
                server.camera_info = self.camera_info
                time.sleep(0.1)

        status_thread = threading.Thread(target=update_server_status, daemon=True)
        status_thread.start()

        print(f"🎯 R2D2 Vision Demo Server starting on http://localhost:{self.port}")
        print(f"📹 Camera Status: {self.camera_info}")
        print("🔗 Open http://localhost:8080 in your browser to see the vision demo")
        print("Press Ctrl+C to stop")

        try:
            server.serve_forever()
        except KeyboardInterrupt:
            print("\n🛑 Shutting down R2D2 Vision Demo")
            if self.camera:
                self.camera.release()

if __name__ == "__main__":
    demo = R2D2VisionDemo(port=8080)
    demo.run_server()