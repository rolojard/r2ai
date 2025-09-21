#!/usr/bin/env node
/**
 * R2D2 Dashboard Web Server
 * Serves the dashboard HTML and handles WebSocket connections
 */

const http = require('http');
const fs = require('fs');
const path = require('path');
const WebSocket = require('ws');

const PORT = 8765;
const WEBSOCKET_PORT = 8766;

// Create HTTP server for dashboard
const server = http.createServer((req, res) => {
    let filePath = '.' + req.url;
    if (filePath === './') {
        filePath = './r2d2_enhanced_dashboard.html';
    }

    const extname = String(path.extname(filePath)).toLowerCase();
    const mimeTypes = {
        '.html': 'text/html',
        '.js': 'text/javascript',
        '.css': 'text/css',
        '.json': 'application/json',
        '.png': 'image/png',
        '.jpg': 'image/jpg',
        '.gif': 'image/gif',
        '.svg': 'image/svg+xml',
        '.wav': 'audio/wav',
        '.mp4': 'video/mp4',
        '.woff': 'application/font-woff',
        '.ttf': 'application/font-ttf',
        '.eot': 'application/vnd.ms-fontobject',
        '.otf': 'application/font-otf',
        '.wasm': 'application/wasm'
    };

    const contentType = mimeTypes[extname] || 'application/octet-stream';

    fs.readFile(filePath, function(error, content) {
        if (error) {
            if (error.code === 'ENOENT') {
                // Serve default dashboard HTML
                const defaultHTML = `
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>R2D2 Multi-Agent Dashboard</title>
    <style>
        body {
            font-family: 'Inter', sans-serif;
            margin: 0;
            padding: 20px;
            background: #0f172a;
            color: #f8fafc;
        }
        .header {
            text-align: center;
            margin-bottom: 30px;
        }
        .status-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        .status-card {
            background: #1e293b;
            border: 1px solid #334155;
            border-radius: 8px;
            padding: 20px;
        }
        .metric {
            display: flex;
            justify-content: space-between;
            margin-bottom: 10px;
        }
        .value {
            font-weight: bold;
            color: #10b981;
        }
        .controls {
            display: flex;
            gap: 10px;
            margin-top: 20px;
        }
        button {
            background: #3b82f6;
            color: white;
            border: none;
            padding: 10px 20px;
            border-radius: 5px;
            cursor: pointer;
        }
        button:hover {
            background: #2563eb;
        }
        .alert {
            background: #dc2626;
            padding: 10px;
            border-radius: 5px;
            margin: 10px 0;
        }
        .success {
            background: #16a34a;
            padding: 10px;
            border-radius: 5px;
            margin: 10px 0;
        }
        #connectionStatus {
            position: fixed;
            top: 20px;
            right: 20px;
            padding: 10px;
            border-radius: 5px;
            background: #dc2626;
        }
        #connectionStatus.connected {
            background: #16a34a;
        }
    </style>
</head>
<body>
    <div id="connectionStatus">Disconnected</div>

    <div class="header">
        <h1>🎯 R2D2 Multi-Agent Dashboard</h1>
        <p>Real-time monitoring and control system</p>
    </div>

    <div class="status-grid">
        <div class="status-card">
            <h3>🖥️ System Performance</h3>
            <div class="metric">
                <span>CPU Usage:</span>
                <span class="value" id="cpuUsage">--%</span>
            </div>
            <div class="metric">
                <span>Memory Usage:</span>
                <span class="value" id="memoryUsage">--%</span>
            </div>
            <div class="metric">
                <span>Temperature:</span>
                <span class="value" id="temperature">--°C</span>
            </div>
            <div class="metric">
                <span>GPU Usage:</span>
                <span class="value" id="gpuUsage">--%</span>
            </div>
        </div>

        <div class="status-card">
            <h3>🎭 R2D2 Status</h3>
            <div class="metric">
                <span>Active Servos:</span>
                <span class="value" id="activeServos">--</span>
            </div>
            <div class="metric">
                <span>Audio System:</span>
                <span class="value" id="audioStatus">--</span>
            </div>
            <div class="metric">
                <span>Vision System:</span>
                <span class="value" id="visionStatus">--</span>
            </div>
            <div class="metric">
                <span>System Health:</span>
                <span class="value" id="systemHealth">--%</span>
            </div>
        </div>

        <div class="status-card">
            <h3>🎪 Performance Metrics</h3>
            <div class="metric">
                <span>Servo Timing:</span>
                <span class="value" id="servoTiming">-- ms</span>
            </div>
            <div class="metric">
                <span>Audio Latency:</span>
                <span class="value" id="audioLatency">-- ms</span>
            </div>
            <div class="metric">
                <span>Vision FPS:</span>
                <span class="value" id="visionFps">-- FPS</span>
            </div>
            <div class="metric">
                <span>Uptime:</span>
                <span class="value" id="uptime">--:--:--</span>
            </div>
        </div>
    </div>

    <div class="status-card">
        <h3>🎮 Control Panel</h3>
        <div class="controls">
            <button onclick="testServos()">Test Servos</button>
            <button onclick="testAudio()">Test Audio</button>
            <button onclick="testVision()">Test Vision</button>
            <button onclick="runFullDemo()">Full Demo</button>
            <button onclick="emergencyStop()">Emergency Stop</button>
        </div>
    </div>

    <div id="alerts"></div>

    <script>
        let ws = null;
        let reconnectInterval = null;

        function connect() {
            try {
                ws = new WebSocket('ws://localhost:${WEBSOCKET_PORT}');

                ws.onopen = function() {
                    document.getElementById('connectionStatus').textContent = 'Connected';
                    document.getElementById('connectionStatus').className = 'connected';
                    clearInterval(reconnectInterval);
                    requestSystemData();
                };

                ws.onmessage = function(event) {
                    const data = JSON.parse(event.data);
                    handleMessage(data);
                };

                ws.onclose = function() {
                    document.getElementById('connectionStatus').textContent = 'Disconnected';
                    document.getElementById('connectionStatus').className = '';
                    attemptReconnect();
                };

                ws.onerror = function(error) {
                    console.error('WebSocket error:', error);
                };
            } catch (error) {
                console.error('Connection failed:', error);
                attemptReconnect();
            }
        }

        function attemptReconnect() {
            if (!reconnectInterval) {
                reconnectInterval = setInterval(() => {
                    console.log('Attempting to reconnect...');
                    connect();
                }, 5000);
            }
        }

        function handleMessage(data) {
            switch(data.type) {
                case 'system_stats':
                    updateSystemStats(data.stats);
                    break;
                case 'r2d2_status':
                    updateR2D2Status(data.status);
                    break;
                case 'alert':
                    showAlert(data.message, data.level);
                    break;
            }
        }

        function updateSystemStats(stats) {
            if (stats.cpu !== undefined) document.getElementById('cpuUsage').textContent = stats.cpu + '%';
            if (stats.memory !== undefined) document.getElementById('memoryUsage').textContent = stats.memory + '%';
            if (stats.temperature !== undefined) document.getElementById('temperature').textContent = stats.temperature + '°C';
            if (stats.gpu !== undefined) document.getElementById('gpuUsage').textContent = stats.gpu + '%';
        }

        function updateR2D2Status(status) {
            if (status.servos !== undefined) document.getElementById('activeServos').textContent = status.servos;
            if (status.audio !== undefined) document.getElementById('audioStatus').textContent = status.audio;
            if (status.vision !== undefined) document.getElementById('visionStatus').textContent = status.vision;
            if (status.health !== undefined) document.getElementById('systemHealth').textContent = status.health + '%';
            if (status.servoTiming !== undefined) document.getElementById('servoTiming').textContent = status.servoTiming + ' ms';
            if (status.audioLatency !== undefined) document.getElementById('audioLatency').textContent = status.audioLatency + ' ms';
            if (status.visionFps !== undefined) document.getElementById('visionFps').textContent = status.visionFps + ' FPS';
        }

        function requestSystemData() {
            if (ws && ws.readyState === WebSocket.OPEN) {
                ws.send(JSON.stringify({type: 'request_data'}));
            }
        }

        function sendCommand(command, params = {}) {
            if (ws && ws.readyState === WebSocket.OPEN) {
                ws.send(JSON.stringify({type: 'command', command: command, params: params}));
            }
        }

        function testServos() {
            sendCommand('test_servos');
            showAlert('Testing servos...', 'info');
        }

        function testAudio() {
            sendCommand('test_audio');
            showAlert('Testing audio system...', 'info');
        }

        function testVision() {
            sendCommand('test_vision');
            showAlert('Testing vision system...', 'info');
        }

        function runFullDemo() {
            sendCommand('full_demo');
            showAlert('Running full R2D2 demonstration...', 'info');
        }

        function emergencyStop() {
            sendCommand('emergency_stop');
            showAlert('Emergency stop activated!', 'error');
        }

        function showAlert(message, level = 'info') {
            const alerts = document.getElementById('alerts');
            const alert = document.createElement('div');
            alert.className = level === 'error' ? 'alert' : 'success';
            alert.textContent = message;
            alerts.insertBefore(alert, alerts.firstChild);

            setTimeout(() => {
                if (alert.parentNode) {
                    alert.parentNode.removeChild(alert);
                }
            }, 5000);
        }

        function updateUptime() {
            const startTime = new Date();
            setInterval(() => {
                const now = new Date();
                const diff = Math.floor((now - startTime) / 1000);
                const hours = Math.floor(diff / 3600).toString().padStart(2, '0');
                const minutes = Math.floor((diff % 3600) / 60).toString().padStart(2, '0');
                const seconds = (diff % 60).toString().padStart(2, '0');
                document.getElementById('uptime').textContent = hours + ':' + minutes + ':' + seconds;
            }, 1000);
        }

        // Initialize
        connect();
        updateUptime();
        setInterval(requestSystemData, 5000);
    </script>
</body>
</html>`;
                res.writeHead(200, { 'Content-Type': 'text/html' });
                res.end(defaultHTML, 'utf-8');
            } else {
                res.writeHead(500);
                res.end('Server Error: ' + error.code + ' ..\n');
            }
        } else {
            res.writeHead(200, { 'Content-Type': contentType });
            res.end(content, 'utf-8');
        }
    });
});

// Create WebSocket server for real-time data
const wss = new WebSocket.Server({ port: WEBSOCKET_PORT });

wss.on('connection', function connection(ws) {
    console.log('Dashboard client connected');

    // Send initial data
    sendSystemStats(ws);

    ws.on('message', function incoming(message) {
        try {
            const data = JSON.parse(message);
            handleWebSocketMessage(ws, data);
        } catch (error) {
            console.error('Error parsing WebSocket message:', error);
        }
    });

    ws.on('close', function() {
        console.log('Dashboard client disconnected');
    });
});

function handleWebSocketMessage(ws, data) {
    switch(data.type) {
        case 'request_data':
            sendSystemStats(ws);
            sendR2D2Status(ws);
            break;
        case 'command':
            executeCommand(ws, data.command, data.params);
            break;
        case 'servo_command':
            handleServoCommand(ws, data);
            break;
        case 'audio_command':
            handleAudioCommand(ws, data);
            break;
        case 'audio_stop_all':
            handleAudioStopAll(ws, data);
            break;
        case 'behavior_pattern':
            handleBehaviorPattern(ws, data);
            break;
        case 'emergency_stop':
            handleEmergencyStop(ws, data);
            break;
    }
}

function sendSystemStats(ws) {
    // Mock system stats - replace with real data collection
    const stats = {
        type: 'system_stats',
        stats: {
            cpu: Math.floor(Math.random() * 30) + 40,
            memory: Math.floor(Math.random() * 20) + 30,
            temperature: Math.floor(Math.random() * 15) + 45,
            gpu: Math.floor(Math.random() * 40) + 30
        }
    };

    if (ws.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify(stats));
    }
}

function sendR2D2Status(ws) {
    // Mock R2D2 status - replace with real system integration
    const status = {
        type: 'r2d2_status',
        status: {
            servos: '21/21',
            audio: 'Online',
            vision: 'Active',
            health: Math.floor(Math.random() * 10) + 90,
            servoTiming: '1.13',
            audioLatency: '1.16',
            visionFps: '30.2'
        }
    };

    if (ws.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify(status));
    }
}

function executeCommand(ws, command, params) {
    console.log('Executing command:', command, params);

    // Here you would integrate with your Python scripts
    const { spawn } = require('child_process');

    let scriptName = '';
    switch(command) {
        case 'test_servos':
            scriptName = 'test_r2d2_servos.py';
            break;
        case 'test_audio':
            scriptName = 'r2d2_canonical_sound_validator.py';
            break;
        case 'test_vision':
            scriptName = 'r2d2_vision_validator.py';
            break;
        case 'full_demo':
            scriptName = 'r2d2_enhanced_scenario_tester.py';
            break;
        case 'emergency_stop':
            // Emergency stop logic
            sendAlert(ws, 'Emergency stop executed!', 'error');
            return;
    }

    if (scriptName) {
        const pythonProcess = spawn('python3', [scriptName]);

        pythonProcess.stdout.on('data', (data) => {
            console.log(command + ' output:', data.toString());
        });

        pythonProcess.stderr.on('data', (data) => {
            console.error(command + ' error:', data.toString());
        });

        pythonProcess.on('close', (code) => {
            const message = code === 0 ?
                command + ' completed successfully' :
                command + ' failed with code ' + code;
            sendAlert(ws, message, code === 0 ? 'success' : 'error');
        });

        sendAlert(ws, 'Started ' + command + '...', 'info');
    }
}

function sendAlert(ws, message, level) {
    const alert = {
        type: 'alert',
        message: message,
        level: level,
        timestamp: Date.now()
    };

    if (ws.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify(alert));
    }
}

// Start servers
server.listen(PORT, () => {
    console.log('🎯 R2D2 Dashboard Server running at http://localhost:' + PORT);
    console.log('🔌 WebSocket server running on port ' + WEBSOCKET_PORT);
    console.log('📊 Dashboard ready for R2AI system monitoring!');
});

// Broadcast system stats periodically with cleanup
const broadcastInterval = setInterval(() => {
    wss.clients.forEach((ws) => {
        if (ws.readyState === WebSocket.OPEN) {
            sendSystemStats(ws);
            sendR2D2Status(ws);
        } else {
            // Clean up dead connections
            ws.terminate();
        }
    });

    // Force garbage collection if available
    if (global.gc) {
        global.gc();
    }
}, 5000);

// Graceful shutdown
process.on('SIGINT', () => {
    console.log('Shutting down gracefully...');
    clearInterval(broadcastInterval);
    server.close();
    wss.close();
    process.exit(0);
});

// Enhanced command handlers for R2D2 control

function handleServoCommand(ws, data) {
    console.log(`Servo command: Channel ${data.channel} -> ${data.position}µs`);

    // Execute servo command via Python script
    const { spawn } = require('child_process');

    const servoScript = spawn('python3', [
        'servo_control_interface.py',
        '--channel', data.channel.toString(),
        '--position', data.position.toString()
    ]);

    servoScript.stdout.on('data', (output) => {
        console.log('Servo output:', output.toString());
    });

    servoScript.stderr.on('data', (error) => {
        console.error('Servo error:', error.toString());
        sendAlert(ws, `Servo error: Channel ${data.channel}`, 'error');
    });

    servoScript.on('close', (code) => {
        if (code === 0) {
            sendAlert(ws, `Servo ${data.channel} moved to ${data.position}µs`, 'success');
        } else {
            sendAlert(ws, `Servo command failed: Code ${code}`, 'error');
        }
    });
}

function handleAudioCommand(ws, data) {
    console.log(`Audio command: Playing ${data.sound}`);

    const { spawn } = require('child_process');

    const audioScript = spawn('python3', [
        'r2d2_audio_player.py',
        '--sound', data.sound
    ]);

    audioScript.stdout.on('data', (output) => {
        console.log('Audio output:', output.toString());
    });

    audioScript.stderr.on('data', (error) => {
        console.error('Audio error:', error.toString());
        sendAlert(ws, `Audio error: ${data.sound}`, 'error');
    });

    audioScript.on('close', (code) => {
        if (code === 0) {
            sendAlert(ws, `Playing: ${data.sound}`, 'info');
        } else {
            sendAlert(ws, `Audio playback failed`, 'error');
        }
    });
}

function handleAudioStopAll(ws, data) {
    console.log('Stopping all audio');

    const { spawn } = require('child_process');

    const stopScript = spawn('python3', [
        'r2d2_audio_player.py',
        '--stop-all'
    ]);

    stopScript.on('close', (code) => {
        sendAlert(ws, 'All audio stopped', 'info');
    });
}

function handleBehaviorPattern(ws, data) {
    console.log(`Executing behavior pattern: ${data.pattern}`);

    const { spawn } = require('child_process');

    const behaviorScript = spawn('python3', [
        'r2d2_behavior_controller.py',
        '--pattern', data.pattern
    ]);

    behaviorScript.stdout.on('data', (output) => {
        console.log('Behavior output:', output.toString());
    });

    behaviorScript.stderr.on('data', (error) => {
        console.error('Behavior error:', error.toString());
        sendAlert(ws, `Behavior pattern error: ${data.pattern}`, 'error');
    });

    behaviorScript.on('close', (code) => {
        if (code === 0) {
            sendAlert(ws, `Executed pattern: ${data.pattern}`, 'success');
        } else {
            sendAlert(ws, `Behavior pattern failed: ${data.pattern}`, 'error');
        }
    });
}

function handleEmergencyStop(ws, data) {
    console.log(`EMERGENCY STOP: ${data.system}`);

    const { spawn } = require('child_process');

    // Stop all systems
    const emergencyScript = spawn('python3', [
        'r2d2_emergency_stop.py',
        '--system', data.system
    ]);

    emergencyScript.stdout.on('data', (output) => {
        console.log('Emergency stop output:', output.toString());
    });

    emergencyScript.on('close', (code) => {
        sendAlert(ws, `EMERGENCY STOP EXECUTED: ${data.system}`, 'error');

        // Broadcast emergency stop to all clients
        wss.clients.forEach((client) => {
            if (client.readyState === WebSocket.OPEN) {
                client.send(JSON.stringify({
                    type: 'emergency_stop_alert',
                    system: data.system,
                    timestamp: Date.now()
                }));
            }
        });
    });
}

module.exports = { server, wss };