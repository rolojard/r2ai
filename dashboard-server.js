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
const BEHAVIORAL_WEBSOCKET_PORT = 8768;
const SERVO_API_URL = 'http://localhost:5000/api';
const SERVO_WEBSOCKET_URL = 'ws://localhost:5000';
const WCB_API_URL = 'http://localhost:8770';

// Import axios for HTTP requests
const axios = require('axios');

// WCB API Client Helper Function
async function callWCBAPI(endpoint, method = 'GET', body = null) {
    try {
        const options = {
            method: method,
            headers: {'Content-Type': 'application/json'}
        };
        if (body) options.data = body;

        const response = await axios({
            url: `${WCB_API_URL}${endpoint}`,
            ...options
        });
        return response.data;
    } catch (error) {
        console.error('WCB API Error:', error.message);
        throw error;
    }
}

// Track child processes for proper cleanup
const childProcesses = new Set();

// Memory management configuration
const MEMORY_CONFIG = {
    MAX_CHILD_PROCESSES: 5,
    CLEANUP_INTERVAL: 30000, // 30 seconds
    FORCE_GC_INTERVAL: 60000, // 1 minute
    MAX_MEMORY_MB: 512
};

// Create HTTP server for dashboard
const server = http.createServer((req, res) => {
    let filePath = '.' + req.url;
    if (filePath === './') {
        filePath = './dashboard_with_vision.html';  // DEFAULT TO VISION-ENABLED DASHBOARD
    } else if (filePath === './servo' || filePath === './servo/') {
        filePath = './r2d2_advanced_servo_dashboard.html';
    } else if (filePath === './enhanced' || filePath === './enhanced/') {
        filePath = './r2d2_enhanced_dashboard.html';
    } else if (filePath === './vision' || filePath === './vision/') {
        filePath = './dashboard_with_vision.html';
    } else if (filePath === './servo-only' || filePath === './servo-only/') {
        filePath = './r2d2_servo_dashboard.html';  // SERVO-ONLY AVAILABLE AT /servo-only
    } else if (filePath === './disney' || filePath === './disney/') {
        filePath = './r2d2_disney_behavioral_dashboard.html';  // DISNEY BEHAVIORAL INTELLIGENCE DASHBOARD
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
                res.writeHead(302, { 'Location': '/dashboard_with_vision.html' });
                res.end();
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

// Create WebSocket server for behavioral intelligence system
const behaviorWss = new WebSocket.Server({ port: BEHAVIORAL_WEBSOCKET_PORT });

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

// ===== BEHAVIORAL INTELLIGENCE WEBSOCKET SERVER =====

let currentPersonality = 'curious';
let currentControlMode = 'auto';
let behaviorQueue = [];
let environmentData = {
    motionLevel: 'low',
    noiseLevel: 'quiet',
    peopleCount: 0,
    proximityLevel: 'normal'
};
let behaviorStatus = {
    current: 'Idle - Curious',
    progress: 0,
    duration: 0,
    totalDuration: 0,
    isExecuting: false
};
let servoActivityData = {
    active: [],
    totalChannels: 8
};
let audioActivityData = {
    current: null,
    queue: [],
    isPlaying: false
};

behaviorWss.on('connection', function connection(behaviorWs) {
    console.log('Behavioral intelligence client connected');

    // Send initial behavioral status
    sendBehavioralStatus(behaviorWs);
    sendEnvironmentUpdate(behaviorWs);
    sendQueueUpdate(behaviorWs);

    behaviorWs.on('message', function incoming(message) {
        try {
            const data = JSON.parse(message);
            handleBehavioralMessage(behaviorWs, data);
        } catch (error) {
            console.error('Error parsing behavioral WebSocket message:', error);
        }
    });

    behaviorWs.on('close', function() {
        console.log('Behavioral intelligence client disconnected');
    });
});

function handleBehavioralMessage(behaviorWs, data) {
    console.log('Behavioral command received:', data.type, data.command);

    switch(data.type) {
        case 'behavior_command':
            executeBehaviorCommand(behaviorWs, data.command, data.data);
            break;
        case 'request_status':
            sendBehavioralStatus(behaviorWs);
            sendEnvironmentUpdate(behaviorWs);
            sendQueueUpdate(behaviorWs);
            break;
    }
}

function executeBehaviorCommand(behaviorWs, command, data) {
    switch(command) {
        case 'initialize':
            handleBehaviorInitialize(behaviorWs, data);
            break;
        case 'personality_change':
            handlePersonalityChange(behaviorWs, data);
            break;
        case 'control_mode_change':
            handleControlModeChange(behaviorWs, data);
            break;
        case 'sensitivity_update':
            handleSensitivityUpdate(behaviorWs, data);
            break;
        case 'execute_behavior':
            handleExecuteBehavior(behaviorWs, data);
            break;
        case 'queue_pause':
            handleQueuePause(behaviorWs, data);
            break;
        case 'queue_resume':
            handleQueueResume(behaviorWs, data);
            break;
        case 'queue_clear':
            handleQueueClear(behaviorWs, data);
            break;
        case 'queue_update':
            handleQueueUpdate(behaviorWs, data);
            break;
        case 'demo_start':
            handleDemoStart(behaviorWs, data);
            break;
        default:
            console.log('Unknown behavioral command:', command);
    }
}

function handleBehaviorInitialize(behaviorWs, data) {
    if (data.personality) currentPersonality = data.personality;
    if (data.mode) currentControlMode = data.mode;

    console.log(`Behavioral system initialized: ${currentPersonality} mode, ${currentControlMode} control`);

    behaviorStatus.current = `Idle - ${currentPersonality.charAt(0).toUpperCase() + currentPersonality.slice(1)}`;

    sendBehavioralStatus(behaviorWs);
    broadcastToAllBehavioralClients('initialization_complete', {
        personality: currentPersonality,
        mode: currentControlMode
    });
}

function handlePersonalityChange(behaviorWs, data) {
    currentPersonality = data.mode;
    console.log(`Personality changed to: ${currentPersonality}`);

    behaviorStatus.current = `Idle - ${currentPersonality.charAt(0).toUpperCase() + currentPersonality.slice(1)}`;

    sendBehavioralStatus(behaviorWs);
    broadcastToAllBehavioralClients('personality_changed', { mode: currentPersonality });

    // Simulate personality-based environmental sensitivity changes
    simulatePersonalityEffects(currentPersonality);
}

function handleControlModeChange(behaviorWs, data) {
    currentControlMode = data.mode;
    console.log(`Control mode changed to: ${currentControlMode}`);

    broadcastToAllBehavioralClients('control_mode_changed', { mode: currentControlMode });
}

function handleSensitivityUpdate(behaviorWs, data) {
    console.log(`Sensitivity update: ${data.type} = ${data.value}%`);

    // Store sensitivity settings (you could persist these)
    const sensitivityData = {
        type: data.type,
        value: data.value,
        timestamp: Date.now()
    };

    broadcastToAllBehavioralClients('sensitivity_updated', sensitivityData);
}

function handleExecuteBehavior(behaviorWs, data) {
    console.log(`Executing behavior: ${data.name}`);

    behaviorStatus = {
        current: data.name,
        progress: 0,
        duration: 0,
        totalDuration: data.duration || 3000,
        isExecuting: true
    };

    sendBehavioralStatus(behaviorWs);

    // Simulate servo activity based on behavior actions
    if (data.actions) {
        simulateServoActivity(data.actions);
    }

    // Simulate audio activity
    simulateAudioActivity(data.name);

    // Simulate behavior execution progress
    simulateBehaviorExecution(data.duration || 3000);

    broadcastToAllBehavioralClients('behavior_execution_started', {
        name: data.name,
        actions: data.actions,
        duration: data.duration
    });
}

function handleQueuePause(behaviorWs, data) {
    console.log('Behavior queue paused');
    broadcastToAllBehavioralClients('queue_paused', {});
}

function handleQueueResume(behaviorWs, data) {
    console.log('Behavior queue resumed');
    broadcastToAllBehavioralClients('queue_resumed', {});
}

function handleQueueClear(behaviorWs, data) {
    behaviorQueue = [];
    console.log('Behavior queue cleared');
    sendQueueUpdate();
    broadcastToAllBehavioralClients('queue_cleared', {});
}

function handleQueueUpdate(behaviorWs, data) {
    if (data.queue) {
        behaviorQueue = data.queue;
        sendQueueUpdate();
    }
}

function handleDemoStart(behaviorWs, data) {
    console.log(`Starting demo: ${data.type}`);

    if (data.demo && data.demo.behaviors) {
        behaviorQueue = data.demo.behaviors.map((behavior, index) => ({
            id: Date.now() + index,
            name: behavior.name,
            duration: behavior.duration,
            timestamp: new Date().toLocaleTimeString(),
            actions: behavior.actions || []
        }));

        sendQueueUpdate();
    }

    broadcastToAllBehavioralClients('demo_started', {
        type: data.type,
        behaviorCount: behaviorQueue.length
    });
}

// Broadcasting functions
function sendBehavioralStatus(behaviorWs = null) {
    const statusUpdate = {
        type: 'behavior_status_update',
        status: behaviorStatus,
        timestamp: Date.now()
    };

    if (behaviorWs) {
        if (behaviorWs.readyState === WebSocket.OPEN) {
            behaviorWs.send(JSON.stringify(statusUpdate));
        }
    } else {
        broadcastToAllBehavioralClients('behavior_status_update', behaviorStatus);
    }
}

function sendEnvironmentUpdate(behaviorWs = null) {
    const environmentUpdate = {
        type: 'environment_update',
        environment: environmentData,
        timestamp: Date.now()
    };

    if (behaviorWs) {
        if (behaviorWs.readyState === WebSocket.OPEN) {
            behaviorWs.send(JSON.stringify(environmentUpdate));
        }
    } else {
        broadcastToAllBehavioralClients('environment_update', environmentData);
    }
}

function sendQueueUpdate(behaviorWs = null) {
    const queueUpdate = {
        type: 'queue_update',
        queue: behaviorQueue,
        timestamp: Date.now()
    };

    if (behaviorWs) {
        if (behaviorWs.readyState === WebSocket.OPEN) {
            behaviorWs.send(JSON.stringify(queueUpdate));
        }
    } else {
        broadcastToAllBehavioralClients('queue_update', behaviorQueue);
    }
}

function sendServoActivityUpdate() {
    broadcastToAllBehavioralClients('servo_activity_update', servoActivityData);
}

function sendAudioStatusUpdate() {
    broadcastToAllBehavioralClients('audio_status_update', audioActivityData);
}

function sendCharacterUpdate(characters = []) {
    broadcastToAllBehavioralClients('character_update', characters);
}

function broadcastToAllBehavioralClients(type, data) {
    const message = {
        type: type,
        ...data,
        timestamp: Date.now()
    };

    behaviorWss.clients.forEach((client) => {
        if (client.readyState === WebSocket.OPEN) {
            client.send(JSON.stringify(message));
        }
    });
}

// Simulation functions for realistic behavioral responses
function simulatePersonalityEffects(personality) {
    // Adjust environmental responsiveness based on personality
    switch(personality) {
        case 'curious':
            environmentData.motionLevel = 'moderate';
            environmentData.noiseLevel = 'attentive';
            break;
        case 'excited':
            environmentData.motionLevel = 'high';
            environmentData.noiseLevel = 'responsive';
            break;
        case 'cautious':
            environmentData.motionLevel = 'low';
            environmentData.noiseLevel = 'alert';
            break;
        case 'playful':
            environmentData.motionLevel = 'high';
            environmentData.noiseLevel = 'interactive';
            break;
        case 'protective':
            environmentData.motionLevel = 'scanning';
            environmentData.noiseLevel = 'monitoring';
            break;
        case 'maintenance':
            environmentData.motionLevel = 'systematic';
            environmentData.noiseLevel = 'diagnostic';
            break;
    }

    sendEnvironmentUpdate();
}

function simulateServoActivity(actions) {
    // Reset all servos to idle
    servoActivityData.active = [];

    if (actions && actions.length > 0) {
        // Simulate servo activation based on actions
        actions.forEach(action => {
            switch(action) {
                case 'head_tilt':
                case 'head_nods':
                case 'head_shake':
                case 'greeting_nod':
                    servoActivityData.active.push(0, 1); // Dome and head servos
                    break;
                case 'dome_spin':
                case 'dome_wiggle':
                case 'rapid_dome_turn':
                case 'slow_dome_turn':
                case 'full_dome_spin':
                    servoActivityData.active.push(0); // Dome rotation
                    break;
                case 'panels_open':
                case 'panel_flutter':
                case 'all_panels_open':
                    servoActivityData.active.push(6, 7, 8); // All panels
                    break;
                case 'periscope_extend':
                    servoActivityData.active.push(2); // Periscope
                    break;
                case 'defensive_posture':
                    servoActivityData.active.push(0, 1, 2); // Dome, head, periscope
                    break;
                default:
                    // Random servo activity for unknown actions
                    servoActivityData.active.push(Math.floor(Math.random() * 8));
            }
        });

        // Remove duplicates
        servoActivityData.active = [...new Set(servoActivityData.active)];
    }

    sendServoActivityUpdate();

    // Reset servo activity after a delay
    setTimeout(() => {
        servoActivityData.active = [];
        sendServoActivityUpdate();
    }, 2000);
}

function simulateAudioActivity(behaviorName) {
    // Set current audio based on behavior
    const audioMap = {
        'Curious Investigation': 'investigating_beeps',
        'Excited Celebration': 'happy_chirps',
        'Worried Response': 'concerned_beeps',
        'Playful Interaction': 'playful_sounds',
        'Friendly Greeting': 'friendly_whistle',
        'Alert State': 'alert_tone',
        'Victory Celebration': 'victory_beeps',
        'Sleepy Mode': 'yawn_sounds'
    };

    audioActivityData.current = audioMap[behaviorName] || 'r2d2_beep';
    audioActivityData.isPlaying = true;
    audioActivityData.description = `Playing for ${behaviorName}`;

    sendAudioStatusUpdate();

    // Clear audio activity after behavior duration
    setTimeout(() => {
        audioActivityData.current = null;
        audioActivityData.isPlaying = false;
        audioActivityData.description = null;
        sendAudioStatusUpdate();
    }, 3000);
}

function simulateBehaviorExecution(duration) {
    const startTime = Date.now();
    const updateInterval = 100;

    const progressInterval = setInterval(() => {
        const elapsed = Date.now() - startTime;
        const progress = Math.min((elapsed / duration) * 100, 100);

        behaviorStatus.progress = progress;
        behaviorStatus.duration = elapsed;

        if (progress >= 100) {
            clearInterval(progressInterval);

            // Return to idle state
            setTimeout(() => {
                behaviorStatus = {
                    current: `Idle - ${currentPersonality.charAt(0).toUpperCase() + currentPersonality.slice(1)}`,
                    progress: 0,
                    duration: 0,
                    totalDuration: 0,
                    isExecuting: false
                };
                sendBehavioralStatus();
            }, 500);
        }

        sendBehavioralStatus();
    }, updateInterval);
}

// Periodic environmental updates
function simulateEnvironmentalChanges() {
    // Randomly update people count
    if (Math.random() < 0.1) { // 10% chance per update
        environmentData.peopleCount = Math.floor(Math.random() * 5);
        sendEnvironmentUpdate();

        // Simulate character detection
        if (environmentData.peopleCount > 0) {
            const characters = Array(environmentData.peopleCount).fill().map((_, i) => ({
                id: i,
                name: ['Luke Skywalker', 'Princess Leia', 'Han Solo', 'Chewbacca', 'Obi-Wan'][i] || 'Unknown Person',
                confidence: 0.7 + Math.random() * 0.3,
                emoji: ['👤', '👩', '👨', '🧔', '👴'][i] || '👤',
                reaction: ['Friendly', 'Curious', 'Excited', 'Cautious'][Math.floor(Math.random() * 4)]
            }));

            sendCharacterUpdate(characters);
        } else {
            sendCharacterUpdate([]);
        }
    }

    // Randomly adjust noise and motion levels
    if (Math.random() < 0.15) { // 15% chance per update
        const motionLevels = ['low', 'moderate', 'high', 'scanning'];
        const noiseLevels = ['quiet', 'moderate', 'active', 'noisy'];

        environmentData.motionLevel = motionLevels[Math.floor(Math.random() * motionLevels.length)];
        environmentData.noiseLevel = noiseLevels[Math.floor(Math.random() * noiseLevels.length)];

        sendEnvironmentUpdate();
    }
}

async function handleWebSocketMessage(ws, data) {
    switch(data.type) {
        case 'request_data':
            sendSystemStats(ws);
            sendR2D2Status(ws);
            sendServoStatus(ws);
            break;
        case 'command':
            executeCommand(ws, data.command, data.params);
            break;
        case 'servo_command':
            handleServoCommand(ws, data);
            break;
        case 'servo_sequence':
            handleServoSequence(ws, data);
            break;
        case 'servo_config':
            handleServoConfig(ws, data);
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
        // WCB Mood Control WebSocket Handlers
        case 'wcb_mood_execute':
            await handleWCBMoodExecute(ws, data);
            break;
        case 'wcb_mood_stop':
            await handleWCBMoodStop(ws, data);
            break;
        case 'wcb_mood_status_request':
            await handleWCBMoodStatusRequest(ws, data);
            break;
        case 'wcb_mood_list_request':
            await handleWCBMoodListRequest(ws, data);
            break;
        case 'wcb_stats_request':
            await handleWCBStatsRequest(ws, data);
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
        // Check if we have too many child processes
        if (childProcesses.size >= MEMORY_CONFIG.MAX_CHILD_PROCESSES) {
            sendAlert(ws, 'Too many active processes. Please wait...', 'warning');
            return;
        }

        const pythonProcess = spawn('python3', [scriptName], {
            timeout: 30000, // 30 second timeout
            killSignal: 'SIGKILL'
        });

        childProcesses.add(pythonProcess);

        pythonProcess.stdout.on('data', (data) => {
            console.log(command + ' output:', data.toString());
        });

        pythonProcess.stderr.on('data', (data) => {
            console.error(command + ' error:', data.toString());
        });

        pythonProcess.on('close', (code) => {
            childProcesses.delete(pythonProcess);
            const message = code === 0 ?
                command + ' completed successfully' :
                command + ' failed with code ' + code;
            sendAlert(ws, message, code === 0 ? 'success' : 'error');
        });

        pythonProcess.on('error', (error) => {
            childProcesses.delete(pythonProcess);
            console.error('Process error:', error);
            sendAlert(ws, 'Process error: ' + error.message, 'error');
        });

        // Auto-cleanup after timeout
        setTimeout(() => {
            if (childProcesses.has(pythonProcess)) {
                pythonProcess.kill('SIGKILL');
                childProcesses.delete(pythonProcess);
                sendAlert(ws, command + ' timed out and was terminated', 'warning');
            }
        }, 30000);

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
    console.log('🧠 Behavioral Intelligence WebSocket server running on port ' + BEHAVIORAL_WEBSOCKET_PORT);
    console.log('📊 Dashboard ready for R2AI system monitoring!');
    console.log('\n🎮 Available Dashboard Routes:');
    console.log('  • http://localhost:' + PORT + '/ (Default Dashboard)');
    console.log('  • http://localhost:' + PORT + '/enhanced (Enhanced Dashboard)');
    console.log('  • http://localhost:' + PORT + '/vision (Vision Dashboard)');
    console.log('  • http://localhost:' + PORT + '/servo (Servo Dashboard)');
});

// Memory-optimized broadcast intervals
let broadcastInterval, behaviorBroadcastInterval, intelligenceMonitoringInterval, memoryCleanupInterval;

// Memory management functions
function cleanupDeadConnections() {
    // Clean up WebSocket connections
    const deadConnections = [];
    wss.clients.forEach((ws) => {
        if (ws.readyState !== WebSocket.OPEN) {
            deadConnections.push(ws);
        }
    });
    deadConnections.forEach(ws => ws.terminate());

    const deadBehaviorConnections = [];
    behaviorWss.clients.forEach((ws) => {
        if (ws.readyState !== WebSocket.OPEN) {
            deadBehaviorConnections.push(ws);
        }
    });
    deadBehaviorConnections.forEach(ws => ws.terminate());

    console.log(`Cleaned up ${deadConnections.length + deadBehaviorConnections.length} dead connections`);
}

function forceGarbageCollection() {
    if (global.gc) {
        const memBefore = process.memoryUsage().heapUsed / 1024 / 1024;
        global.gc();
        const memAfter = process.memoryUsage().heapUsed / 1024 / 1024;
        console.log(`GC: ${memBefore.toFixed(2)}MB -> ${memAfter.toFixed(2)}MB`);
    }
}

function monitorMemoryUsage() {
    const usage = process.memoryUsage();
    const heapUsedMB = usage.heapUsed / 1024 / 1024;

    console.log(`Memory: ${heapUsedMB.toFixed(2)}MB heap, ${childProcesses.size} child processes`);

    if (heapUsedMB > MEMORY_CONFIG.MAX_MEMORY_MB) {
        console.warn(`High memory usage: ${heapUsedMB.toFixed(2)}MB`);

        // Kill oldest child processes if too many
        if (childProcesses.size > 0) {
            const processArray = Array.from(childProcesses);
            const oldestProcess = processArray[0];
            oldestProcess.kill('SIGTERM');
            childProcesses.delete(oldestProcess);
            console.log('Killed oldest child process due to high memory usage');
        }

        forceGarbageCollection();
    }
}

// Reduced frequency broadcast with better memory management
broadcastInterval = setInterval(() => {
    // Clean up dead connections first
    const activeClients = [];
    wss.clients.forEach((ws) => {
        if (ws.readyState === WebSocket.OPEN) {
            activeClients.push(ws);
            sendSystemStats(ws);
            sendR2D2Status(ws);
        } else {
            ws.terminate();
        }
    });

    // Force garbage collection every 10 cycles (50 seconds)
    if (global.gc && Math.random() < 0.1) {
        global.gc();
    }
}, 10000); // Reduced from 5000ms to 10000ms

behaviorBroadcastInterval = setInterval(() => {
    const activeClients = [];
    behaviorWss.clients.forEach((behaviorWs) => {
        if (behaviorWs.readyState === WebSocket.OPEN) {
            activeClients.push(behaviorWs);
            sendBehavioralStatus(behaviorWs);
        } else {
            behaviorWs.terminate();
        }
    });

    // Only simulate changes if there are active clients
    if (activeClients.length > 0) {
        simulateEnvironmentalChanges();
    }
}, 5000); // Reduced from 3000ms to 5000ms

intelligenceMonitoringInterval = setInterval(() => {
    // Only send updates if there are active behavioral clients
    if (behaviorWss.clients.size > 0) {
        const performanceData = {
            responseTime: Math.floor(Math.random() * 50) + 50,
            processingLoad: Math.floor(Math.random() * 30) + 20,
            memoryUsage: Math.floor(Math.random() * 25) + 30,
            queueLength: behaviorQueue.length
        };
        broadcastToAllBehavioralClients('performance_update', performanceData);
    }
}, 5000); // Reduced from 2000ms to 5000ms

// Memory cleanup interval
memoryCleanupInterval = setInterval(() => {
    cleanupDeadConnections();
    monitorMemoryUsage();
}, MEMORY_CONFIG.CLEANUP_INTERVAL);

// Forced garbage collection interval
setInterval(() => {
    forceGarbageCollection();
}, MEMORY_CONFIG.FORCE_GC_INTERVAL);

// WCB Status Broadcasting Interval (1 second)
setInterval(async () => {
    try {
        // Fetch WCB status and stats from API
        const status = await callWCBAPI('/api/wcb/mood/status');
        const stats = await callWCBAPI('/api/wcb/stats');

        // Broadcast to all connected WebSocket clients
        wss.clients.forEach((client) => {
            if (client.readyState === WebSocket.OPEN) {
                // Send status update
                client.send(JSON.stringify({
                    type: 'wcb_mood_status',
                    active: status.active || false,
                    mood: status.mood || null,
                    progress_percent: status.progress_percent || 0,
                    commands_sent: status.commands_sent || 0,
                    started_at: status.started_at || null,
                    timestamp: Date.now()
                }));

                // Send stats update
                client.send(JSON.stringify({
                    type: 'wcb_stats',
                    moods_executed: stats.moods_executed || 0,
                    total_commands_sent: stats.total_commands_sent || 0,
                    average_execution_time_ms: stats.average_execution_time_ms || 0,
                    uptime_seconds: stats.uptime_seconds || 0,
                    timestamp: Date.now()
                }));
            }
        });
    } catch (error) {
        // Silently fail if WCB API is not available
        // Only log on first occurrence to avoid spam
        if (!global.wcbBroadcastErrorLogged) {
            console.log('WCB status broadcast: API not available (will retry silently)');
            global.wcbBroadcastErrorLogged = true;
        }
    }
}, 1000); // Every 1 second

// Graceful shutdown
process.on('SIGINT', () => {
    console.log('Shutting down gracefully...');

    // Clear all intervals
    clearInterval(broadcastInterval);
    clearInterval(behaviorBroadcastInterval);
    clearInterval(intelligenceMonitoringInterval);
    clearInterval(memoryCleanupInterval);

    // Kill all child processes
    childProcesses.forEach(proc => {
        try {
            proc.kill('SIGTERM');
        } catch (e) {
            console.error('Error killing process:', e.message);
        }
    });
    childProcesses.clear();

    // Close servers
    server.close();
    wss.close();
    behaviorWss.close();

    console.log('Cleanup complete');
    process.exit(0);
});

// Handle uncaught exceptions
process.on('uncaughtException', (error) => {
    console.error('Uncaught Exception:', error);
    // Don't exit on uncaught exceptions, just log them
});

process.on('unhandledRejection', (reason, promise) => {
    console.error('Unhandled Rejection at:', promise, 'reason:', reason);
});

// Enhanced command handlers for R2D2 control

function handleServoCommand(ws, data) {
    console.log(`Servo command: Channel ${data.channel} -> ${data.position}µs`);

    // Send command to servo integration backend
    axios.post(`${SERVO_API_URL}/servo/${data.channel}/move`, {
        position: data.position
    })
    .then(response => {
        if (response.data.success) {
            sendAlert(ws, `Servo ${data.channel} moved to ${data.position}µs`, 'success');

            // Send confirmation back to client
            const confirmation = {
                type: 'servo_response',
                channel: data.channel,
                position: data.position,
                success: true,
                timestamp: Date.now()
            };

            if (ws.readyState === WebSocket.OPEN) {
                ws.send(JSON.stringify(confirmation));
            }
        } else {
            sendAlert(ws, `Servo command failed: ${response.data.error}`, 'error');
        }
    })
    .catch(error => {
        console.error('Servo command error:', error.message);
        sendAlert(ws, `Servo error: Channel ${data.channel}`, 'error');

        // Fallback to direct command execution
        const { spawn } = require('child_process');

        const servoScript = spawn('python3', [
            'servo_control_interface.py',
            '--channel', data.channel.toString(),
            '--position', data.position.toString()
        ], {
            timeout: 10000
        });

        childProcesses.add(servoScript);

        servoScript.on('close', (code) => {
            childProcesses.delete(servoScript);
            if (code === 0) {
                sendAlert(ws, `Servo ${data.channel} moved (fallback)`, 'info');
            } else {
                sendAlert(ws, `Servo command failed completely`, 'error');
            }
        });

        servoScript.on('error', (error) => {
            childProcesses.delete(servoScript);
            sendAlert(ws, 'Servo script error: ' + error.message, 'error');
        });
    });
}

function handleAudioCommand(ws, data) {
    console.log(`Audio command: Playing ${data.sound}`);

    const { spawn } = require('child_process');

    const audioScript = spawn('python3', [
        'r2d2_audio_player.py',
        '--sound', data.sound
    ], {
        timeout: 15000
    });

    childProcesses.add(audioScript);

    audioScript.stdout.on('data', (output) => {
        console.log('Audio output:', output.toString());
    });

    audioScript.stderr.on('data', (error) => {
        console.error('Audio error:', error.toString());
        sendAlert(ws, `Audio error: ${data.sound}`, 'error');
    });

    audioScript.on('close', (code) => {
        childProcesses.delete(audioScript);
        if (code === 0) {
            sendAlert(ws, `Playing: ${data.sound}`, 'info');
        } else {
            sendAlert(ws, `Audio playback failed`, 'error');
        }
    });

    audioScript.on('error', (error) => {
        childProcesses.delete(audioScript);
        sendAlert(ws, 'Audio script error: ' + error.message, 'error');
    });
}

function handleAudioStopAll(ws, data) {
    console.log('Stopping all audio');

    const { spawn } = require('child_process');

    const stopScript = spawn('python3', [
        'r2d2_audio_player.py',
        '--stop-all'
    ], {
        timeout: 5000
    });

    childProcesses.add(stopScript);

    stopScript.on('close', (code) => {
        childProcesses.delete(stopScript);
        sendAlert(ws, 'All audio stopped', 'info');
    });

    stopScript.on('error', (error) => {
        childProcesses.delete(stopScript);
        sendAlert(ws, 'Stop audio error: ' + error.message, 'error');
    });
}

function handleBehaviorPattern(ws, data) {
    console.log(`Executing behavior pattern: ${data.pattern}`);

    const { spawn } = require('child_process');

    const behaviorScript = spawn('python3', [
        'r2d2_behavior_controller.py',
        '--pattern', data.pattern
    ], {
        timeout: 20000
    });

    childProcesses.add(behaviorScript);

    behaviorScript.stdout.on('data', (output) => {
        console.log('Behavior output:', output.toString());
    });

    behaviorScript.stderr.on('data', (error) => {
        console.error('Behavior error:', error.toString());
        sendAlert(ws, `Behavior pattern error: ${data.pattern}`, 'error');
    });

    behaviorScript.on('close', (code) => {
        childProcesses.delete(behaviorScript);
        if (code === 0) {
            sendAlert(ws, `Executed pattern: ${data.pattern}`, 'success');
        } else {
            sendAlert(ws, `Behavior pattern failed: ${data.pattern}`, 'error');
        }
    });

    behaviorScript.on('error', (error) => {
        childProcesses.delete(behaviorScript);
        sendAlert(ws, 'Behavior script error: ' + error.message, 'error');
    });
}

function handleEmergencyStop(ws, data) {
    console.log(`EMERGENCY STOP: ${data.system}`);

    // Send emergency stop to servo integration backend
    axios.post(`${SERVO_API_URL}/servo/emergency_stop`)
        .then(response => {
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
        })
        .catch(error => {
            console.error('Emergency stop API error:', error.message);

            // Fallback to direct emergency stop
            const { spawn } = require('child_process');

            const emergencyScript = spawn('python3', [
                'r2d2_emergency_stop.py',
                '--system', data.system
            ], {
                timeout: 5000
            });

            childProcesses.add(emergencyScript);

            emergencyScript.on('close', (code) => {
                childProcesses.delete(emergencyScript);
                sendAlert(ws, `EMERGENCY STOP EXECUTED (fallback): ${data.system}`, 'error');

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

            emergencyScript.on('error', (error) => {
                childProcesses.delete(emergencyScript);
                sendAlert(ws, 'Emergency stop error: ' + error.message, 'error');
            });
        });
}

// Additional handlers for advanced servo dashboard features

function sendServoStatus(ws) {
    // Try to fetch real servo status from backend
    axios.get(`${SERVO_API_URL}/servo/status`)
        .then(response => {
            const servoData = {
                type: 'servo_status',
                data: response.data.data,
                timestamp: Date.now()
            };

            if (ws.readyState === WebSocket.OPEN) {
                ws.send(JSON.stringify(servoData));
            }
        })
        .catch(error => {
            console.log('Servo backend not available, using mock data');
            // Fallback to mock data if backend not available
            const servoStatus = {
                type: 'board_detected',
                boardType: 'Pololu Maestro Mini 12',
                port: '/dev/ttyACM0',
                channels: 12,
                firmware: '1.04',
                connected: false,
                error: 'Backend not available'
            };

            if (ws.readyState === WebSocket.OPEN) {
                ws.send(JSON.stringify(servoStatus));
            }
        });
}

function handleServoSequence(ws, data) {
    console.log(`Executing servo sequence: ${data.sequence_name}`);

    const { spawn } = require('child_process');

    const sequenceScript = spawn('python3', [
        'r2d2_sequence_player.py',
        '--sequence', data.sequence_name,
        '--keyframes', JSON.stringify(data.keyframes)
    ], {
        timeout: 60000
    });

    childProcesses.add(sequenceScript);

    sequenceScript.stdout.on('data', (output) => {
        console.log('Sequence output:', output.toString());

        // Send sequence progress updates
        try {
            const progress = JSON.parse(output.toString());
            if (progress.type === 'sequence_progress') {
                if (ws.readyState === WebSocket.OPEN) {
                    ws.send(JSON.stringify({
                        type: 'sequence_update',
                        progress: progress.progress,
                        current_keyframe: progress.keyframe
                    }));
                }
            }
        } catch (e) {
            // Ignore non-JSON output
        }
    });

    sequenceScript.stderr.on('data', (error) => {
        console.error('Sequence error:', error.toString());
        sendAlert(ws, `Sequence error: ${data.sequence_name}`, 'error');
    });

    sequenceScript.on('close', (code) => {
        childProcesses.delete(sequenceScript);
        if (code === 0) {
            sendAlert(ws, `Sequence completed: ${data.sequence_name}`, 'success');
        } else {
            sendAlert(ws, `Sequence failed: ${data.sequence_name}`, 'error');
        }
    });

    sequenceScript.on('error', (error) => {
        childProcesses.delete(sequenceScript);
        sendAlert(ws, 'Sequence script error: ' + error.message, 'error');
    });
}

function handleServoConfig(ws, data) {
    console.log(`Updating servo configuration: ${data.config_type}`);

    switch(data.config_type) {
        case 'servo_count':
            sendAlert(ws, `Servo count updated to ${data.value}`, 'info');
            break;
        case 'update_rate':
            sendAlert(ws, `Update rate set to ${data.value} Hz`, 'info');
            break;
        case 'safety_mode':
            sendAlert(ws, `Safety mode set to ${data.value}`, 'info');
            break;
        default:
            sendAlert(ws, `Configuration updated: ${data.config_type}`, 'info');
    }

    // Broadcast configuration changes to all clients
    wss.clients.forEach((client) => {
        if (client.readyState === WebSocket.OPEN && client !== ws) {
            client.send(JSON.stringify({
                type: 'config_update',
                config_type: data.config_type,
                value: data.value,
                timestamp: Date.now()
            }));
        }
    });
}

// ===== WCB MOOD CONTROL WEBSOCKET HANDLERS =====

async function handleWCBMoodExecute(ws, data) {
    console.log(`WCB Mood Execute: ${data.mood_id} (${data.mood_name || 'unnamed'}), Priority: ${data.priority || 7}`);

    try {
        const result = await callWCBAPI('/api/wcb/mood/execute', 'POST', {
            mood_id: data.mood_id,
            mood_name: data.mood_name,
            priority: data.priority || 7
        });

        if (ws.readyState === WebSocket.OPEN) {
            ws.send(JSON.stringify({
                type: 'wcb_mood_result',
                status: result.status || 'success',
                mood: result.mood || data.mood_name,
                commands_sent: result.commands_sent || 0,
                execution_time_ms: result.execution_time_ms || 0,
                message: result.message,
                timestamp: Date.now()
            }));
        }

        console.log(`WCB Mood Execute Success: ${result.mood}`);
    } catch (error) {
        console.error('WCB Mood Execute Error:', error.message);

        if (ws.readyState === WebSocket.OPEN) {
            ws.send(JSON.stringify({
                type: 'wcb_error',
                error: 'Mood execution failed',
                details: error.message,
                timestamp: Date.now()
            }));
        }
    }
}

async function handleWCBMoodStop(ws, data) {
    console.log('WCB Mood Stop requested');

    try {
        const result = await callWCBAPI('/api/wcb/mood/stop', 'POST');

        if (ws.readyState === WebSocket.OPEN) {
            ws.send(JSON.stringify({
                type: 'wcb_mood_result',
                status: result.status || 'success',
                message: result.message || 'Mood stopped',
                timestamp: Date.now()
            }));
        }

        console.log('WCB Mood Stop Success');
    } catch (error) {
        console.error('WCB Mood Stop Error:', error.message);

        if (ws.readyState === WebSocket.OPEN) {
            ws.send(JSON.stringify({
                type: 'wcb_error',
                error: 'Stop failed',
                details: error.message,
                timestamp: Date.now()
            }));
        }
    }
}

async function handleWCBMoodStatusRequest(ws, data) {
    console.log('WCB Mood Status requested');

    try {
        const status = await callWCBAPI('/api/wcb/mood/status');

        if (ws.readyState === WebSocket.OPEN) {
            ws.send(JSON.stringify({
                type: 'wcb_mood_status',
                active: status.active || false,
                mood: status.mood || null,
                progress_percent: status.progress_percent || 0,
                commands_sent: status.commands_sent || 0,
                started_at: status.started_at || null,
                timestamp: Date.now()
            }));
        }
    } catch (error) {
        console.error('WCB Mood Status Error:', error.message);

        if (ws.readyState === WebSocket.OPEN) {
            ws.send(JSON.stringify({
                type: 'wcb_error',
                error: 'Status request failed',
                details: error.message,
                timestamp: Date.now()
            }));
        }
    }
}

async function handleWCBMoodListRequest(ws, data) {
    console.log('WCB Mood List requested');

    try {
        const moodList = await callWCBAPI('/api/wcb/mood/list');

        if (ws.readyState === WebSocket.OPEN) {
            ws.send(JSON.stringify({
                type: 'wcb_mood_list',
                moods: moodList.moods || [],
                total: moodList.total || 0,
                timestamp: Date.now()
            }));
        }
    } catch (error) {
        console.error('WCB Mood List Error:', error.message);

        if (ws.readyState === WebSocket.OPEN) {
            ws.send(JSON.stringify({
                type: 'wcb_error',
                error: 'Mood list failed',
                details: error.message,
                timestamp: Date.now()
            }));
        }
    }
}

async function handleWCBStatsRequest(ws, data) {
    console.log('WCB Stats requested');

    try {
        const stats = await callWCBAPI('/api/wcb/stats');

        if (ws.readyState === WebSocket.OPEN) {
            ws.send(JSON.stringify({
                type: 'wcb_stats',
                moods_executed: stats.moods_executed || 0,
                total_commands_sent: stats.total_commands_sent || 0,
                average_execution_time_ms: stats.average_execution_time_ms || 0,
                uptime_seconds: stats.uptime_seconds || 0,
                timestamp: Date.now()
            }));
        }
    } catch (error) {
        console.error('WCB Stats Error:', error.message);

        if (ws.readyState === WebSocket.OPEN) {
            ws.send(JSON.stringify({
                type: 'wcb_error',
                error: 'Stats request failed',
                details: error.message,
                timestamp: Date.now()
            }));
        }
    }
}

module.exports = { server, wss };