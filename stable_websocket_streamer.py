#!/usr/bin/env python3
"""
Stable WebSocket Video Streamer
Uses the flicker-free webcam foundation for perfect video streaming
"""

import asyncio
import websockets
import json
import base64
import cv2
import time
import logging
from flicker_free_webcam import FlickerFreeWebcam
import signal
import sys

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class StableWebSocketStreamer:
    """WebSocket video streamer with zero-flicker guarantee"""

    def __init__(self, port=8767, camera_index=0, target_fps=12):
        self.port = port
        self.camera_index = camera_index
        self.target_fps = target_fps
        self.stream_interval = 1.0 / target_fps

        # WebSocket management
        self.connected_clients = set()
        self.max_clients = 3  # Limit for stability
        self.server = None

        # Webcam system
        self.webcam = FlickerFreeWebcam(camera_index=camera_index, target_fps=15)  # Capture faster than stream

        # Streaming control
        self.running = False
        self.last_stream_time = 0
        self.frame_counter = 0
        self.stream_stats = {
            'clients_connected': 0,
            'frames_sent': 0,
            'stream_fps': 0,
            'encoding_time': 0,
            'total_data_sent': 0
        }

    async def handle_client_connection(self, websocket, path):
        """Handle individual client connections with anti-flicker protection"""
        client_addr = websocket.remote_address

        # Check connection limit
        if len(self.connected_clients) >= self.max_clients:
            logger.warning(f"Connection limit reached. Rejecting client: {client_addr}")
            await websocket.close(code=1013, reason="Server at capacity")
            return

        logger.info(f"New client connected: {client_addr}")
        self.connected_clients.add(websocket)
        self.stream_stats['clients_connected'] = len(self.connected_clients)

        try:
            # Send connection confirmation
            await websocket.send(json.dumps({
                'type': 'connection_status',
                'status': 'connected',
                'message': 'Stable R2D2 Video Stream Connected',
                'stream_fps': self.target_fps
            }))

            # Start frame streaming for this client
            await self._stream_frames_to_client(websocket)

        except websockets.exceptions.ConnectionClosed:
            logger.info(f"Client {client_addr} disconnected")
        except Exception as e:
            logger.error(f"Client error: {e}")
        finally:
            self.connected_clients.discard(websocket)
            self.stream_stats['clients_connected'] = len(self.connected_clients)
            logger.info(f"Client {client_addr} cleaned up. Active clients: {len(self.connected_clients)}")

    async def _stream_frames_to_client(self, websocket):
        """Stream frames to a specific client with precise timing"""
        last_send_time = time.time()
        client_frame_counter = 0

        while self.running and websocket in self.connected_clients:
            try:
                current_time = time.time()

                # Check if it's time to send next frame
                if current_time - last_send_time >= self.stream_interval:
                    # Get latest frame from webcam
                    frame_data = self.webcam.get_frame_for_streaming()

                    if frame_data:
                        # Encode frame with optimal settings
                        encode_start = time.time()
                        success, buffer = cv2.imencode('.jpg', frame_data['frame'],
                                                     [cv2.IMWRITE_JPEG_QUALITY, 85,
                                                      cv2.IMWRITE_JPEG_OPTIMIZE, 1])

                        if success:
                            frame_base64 = base64.b64encode(buffer).decode('utf-8')
                            encoding_time = time.time() - encode_start

                            # Create message
                            message = {
                                'type': 'video_frame',
                                'frame': frame_base64,
                                'timestamp': frame_data['timestamp'],
                                'frame_id': frame_data['frame_id'],
                                'encoding_time': encoding_time,
                                'webcam_stats': self.webcam.get_stats(),
                                'stream_stats': self.stream_stats.copy()
                            }

                            # Send to client
                            await websocket.send(json.dumps(message))

                            # Update statistics
                            client_frame_counter += 1
                            self.stream_stats['frames_sent'] += 1
                            self.stream_stats['encoding_time'] = encoding_time
                            self.stream_stats['total_data_sent'] += len(buffer)

                            # Calculate stream FPS
                            if client_frame_counter % 10 == 0:
                                elapsed = current_time - (last_send_time - 10 * self.stream_interval)
                                if elapsed > 0:
                                    self.stream_stats['stream_fps'] = 10 / elapsed

                            last_send_time = current_time
                        else:
                            logger.warning("Failed to encode frame")
                    else:
                        # Send heartbeat if no frame available
                        await websocket.send(json.dumps({
                            'type': 'heartbeat',
                            'timestamp': current_time
                        }))

                        last_send_time = current_time

                # Precise timing control
                sleep_time = max(0.001, self.stream_interval - (time.time() - last_send_time))
                await asyncio.sleep(sleep_time)

            except websockets.exceptions.ConnectionClosed:
                break
            except Exception as e:
                logger.error(f"Streaming error: {e}")
                break

    async def _periodic_stats_broadcast(self):
        """Broadcast system statistics periodically"""
        while self.running:
            try:
                if self.connected_clients:
                    stats_message = {
                        'type': 'system_stats',
                        'webcam_stats': self.webcam.get_stats(),
                        'stream_stats': self.stream_stats.copy(),
                        'timestamp': time.time()
                    }

                    # Send to all clients
                    disconnected_clients = []
                    for client in self.connected_clients.copy():
                        try:
                            await client.send(json.dumps(stats_message))
                        except websockets.exceptions.ConnectionClosed:
                            disconnected_clients.append(client)
                        except Exception as e:
                            logger.error(f"Stats broadcast error: {e}")
                            disconnected_clients.append(client)

                    # Clean up disconnected clients
                    for client in disconnected_clients:
                        self.connected_clients.discard(client)

                await asyncio.sleep(5)  # Broadcast stats every 5 seconds

            except Exception as e:
                logger.error(f"Stats broadcast error: {e}")
                await asyncio.sleep(1)

    async def start_server(self):
        """Start the WebSocket server"""
        logger.info(f"Starting WebSocket video streamer on port {self.port}")

        # Start webcam first
        if not self.webcam.start():
            logger.error("Failed to start webcam system")
            return False

        self.running = True

        # Start the WebSocket server
        self.server = await websockets.serve(
            self.handle_client_connection,
            "localhost",
            self.port,
            max_size=10**7,  # 10MB max message size for large frames
            ping_interval=20,
            ping_timeout=10
        )

        logger.info(f"✅ WebSocket server running on ws://localhost:{self.port}")
        logger.info(f"🎥 Streaming at {self.target_fps} FPS with zero-flicker guarantee")

        # Start stats broadcasting
        asyncio.create_task(self._periodic_stats_broadcast())

        return True

    async def stop_server(self):
        """Stop the WebSocket server"""
        logger.info("Stopping WebSocket video streamer")
        self.running = False

        # Close all client connections
        if self.connected_clients:
            await asyncio.gather(
                *[client.close() for client in self.connected_clients.copy()],
                return_exceptions=True
            )

        # Stop the server
        if self.server:
            self.server.close()
            await self.server.wait_closed()

        # Stop webcam
        self.webcam.stop()

        logger.info("WebSocket video streamer stopped")

def create_test_client():
    """Create a simple test client to verify streaming"""
    html_content = f"""<!DOCTYPE html>
<html>
<head>
    <title>R2D2 Video Stream Test</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background: #1a1a1a;
            color: white;
        }}
        .container {{
            display: grid;
            grid-template-columns: 2fr 1fr;
            gap: 20px;
        }}
        .video-container {{
            text-align: center;
        }}
        #videoFrame {{
            max-width: 100%;
            border: 2px solid #333;
            border-radius: 8px;
        }}
        .stats {{
            background: #2a2a2a;
            padding: 20px;
            border-radius: 8px;
        }}
        .stat-item {{
            display: flex;
            justify-content: space-between;
            margin: 10px 0;
            padding: 5px 0;
            border-bottom: 1px solid #444;
        }}
        .status {{
            padding: 10px;
            border-radius: 5px;
            margin: 10px 0;
        }}
        .connected {{ background: #16a34a; }}
        .disconnected {{ background: #dc2626; }}
        .controls button {{
            background: #3b82f6;
            color: white;
            border: none;
            padding: 10px 20px;
            margin: 5px;
            border-radius: 5px;
            cursor: pointer;
        }}
    </style>
</head>
<body>
    <h1>🤖 R2D2 Stable Video Stream Test</h1>

    <div class="container">
        <div class="video-container">
            <h3>Live Video Feed</h3>
            <img id="videoFrame" src="data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg==" alt="Video Stream">
            <div id="connectionStatus" class="status disconnected">Disconnected</div>
        </div>

        <div class="stats">
            <h3>📊 Stream Statistics</h3>
            <div class="stat-item">
                <span>Stream FPS:</span>
                <span id="streamFps">--</span>
            </div>
            <div class="stat-item">
                <span>Webcam FPS:</span>
                <span id="webcamFps">--</span>
            </div>
            <div class="stat-item">
                <span>Timing Accuracy:</span>
                <span id="timingAccuracy">--</span>
            </div>
            <div class="stat-item">
                <span>Frames Sent:</span>
                <span id="framesSent">--</span>
            </div>
            <div class="stat-item">
                <span>Encoding Time:</span>
                <span id="encodingTime">--</span>
            </div>
            <div class="stat-item">
                <span>Data Sent:</span>
                <span id="dataSent">--</span>
            </div>
            <div class="stat-item">
                <span>Frame Drops:</span>
                <span id="frameDrops">--</span>
            </div>

            <div class="controls">
                <button onclick="connect()">Connect</button>
                <button onclick="disconnect()">Disconnect</button>
                <button onclick="resetStats()">Reset Stats</button>
            </div>
        </div>
    </div>

    <script>
        let ws = null;
        let frameCount = 0;
        let startTime = Date.now();

        function connect() {{
            if (ws) ws.close();

            ws = new WebSocket('ws://localhost:8767');

            ws.onopen = function() {{
                document.getElementById('connectionStatus').textContent = 'Connected';
                document.getElementById('connectionStatus').className = 'status connected';
                console.log('Connected to R2D2 video stream');
            }};

            ws.onmessage = function(event) {{
                const data = JSON.parse(event.data);
                handleMessage(data);
            }};

            ws.onclose = function() {{
                document.getElementById('connectionStatus').textContent = 'Disconnected';
                document.getElementById('connectionStatus').className = 'status disconnected';
                console.log('Disconnected from video stream');
            }};

            ws.onerror = function(error) {{
                console.error('WebSocket error:', error);
            }};
        }}

        function disconnect() {{
            if (ws) {{
                ws.close();
                ws = null;
            }}
        }}

        function handleMessage(data) {{
            switch(data.type) {{
                case 'video_frame':
                    document.getElementById('videoFrame').src = 'data:image/jpeg;base64,' + data.frame;
                    updateStreamStats(data);
                    frameCount++;
                    break;
                case 'system_stats':
                    updateSystemStats(data);
                    break;
                case 'connection_status':
                    console.log('Connection status:', data.message);
                    break;
            }}
        }}

        function updateStreamStats(data) {{
            if (data.stream_stats) {{
                document.getElementById('streamFps').textContent = data.stream_stats.stream_fps?.toFixed(2) || '--';
                document.getElementById('framesSent').textContent = data.stream_stats.frames_sent || '--';
                document.getElementById('encodingTime').textContent = (data.stream_stats.encoding_time * 1000)?.toFixed(2) + ' ms' || '--';
                document.getElementById('dataSent').textContent = formatBytes(data.stream_stats.total_data_sent) || '--';
            }}

            if (data.webcam_stats) {{
                document.getElementById('webcamFps').textContent = data.webcam_stats.actual_fps?.toFixed(2) || '--';
                document.getElementById('timingAccuracy').textContent = (data.webcam_stats.timing_accuracy * 100)?.toFixed(1) + '%' || '--';
                document.getElementById('frameDrops').textContent = data.webcam_stats.frame_drops || '--';
            }}
        }}

        function updateSystemStats(data) {{
            // Handle periodic system stats updates
            updateStreamStats(data);
        }}

        function formatBytes(bytes) {{
            if (bytes === 0) return '0 B';
            const k = 1024;
            const sizes = ['B', 'KB', 'MB', 'GB'];
            const i = Math.floor(Math.log(bytes) / Math.log(k));
            return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
        }}

        function resetStats() {{
            frameCount = 0;
            startTime = Date.now();
        }}

        // Auto-connect on page load
        window.onload = function() {{
            connect();
        }};
    </script>
</body>
</html>"""

    # Write test client HTML
    with open('/home/rolo/r2ai/video_stream_test.html', 'w') as f:
        f.write(html_content)

    logger.info("Test client created: video_stream_test.html")

async def main():
    """Main function"""
    # Create test client
    create_test_client()

    # Create and start streamer
    streamer = StableWebSocketStreamer(port=8767, camera_index=0, target_fps=12)

    # Handle graceful shutdown
    def signal_handler(signum, frame):
        logger.info("Received shutdown signal")
        asyncio.create_task(streamer.stop_server())

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    try:
        if await streamer.start_server():
            logger.info("🌟 Server started successfully!")
            logger.info("📱 Open video_stream_test.html in your browser to test")
            logger.info("🔌 WebSocket URL: ws://localhost:8767")
            logger.info("Press Ctrl+C to stop")

            # Keep running
            await asyncio.Future()  # Run forever
        else:
            logger.error("Failed to start server")
            sys.exit(1)

    except KeyboardInterrupt:
        logger.info("Shutting down...")
    finally:
        await streamer.stop_server()

if __name__ == "__main__":
    asyncio.run(main())