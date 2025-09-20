/**
 * R2D2 Multi-Agent Dashboard JavaScript
 * Handles real-time monitoring, WebSocket communication, and interactive controls
 */

class R2D2Dashboard {
    constructor() {
        this.websocket = null;
        this.isConnected = false;
        this.currentAgent = 'project_manager';
        this.systemData = {};
        this.chartInstances = {};
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 5;

        this.init();
    }

    init() {
        this.setupEventListeners();
        this.initializeCharts();
        this.connectWebSocket();
        this.startSystemMonitoring();
        this.populateServoGrid();
        this.updateUptime();

        // Set initial agent panel
        this.switchAgent(this.currentAgent);
    }

    setupEventListeners() {
        // Agent navigation
        document.querySelectorAll('.agent-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const agent = e.currentTarget.dataset.agent;
                this.switchAgent(agent);
            });
        });

        // Screenshot functionality
        document.getElementById('screenshotBtn').addEventListener('click', () => {
            this.takeScreenshot();
        });

        // Panel action buttons
        document.querySelectorAll('.refresh-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                this.refreshCurrentPanel();
            });
        });

        // Motion control buttons
        document.querySelectorAll('.motion-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const motion = e.currentTarget.dataset.motion;
                this.triggerMotion(motion);
            });
        });

        // Test controls
        const runTestsBtn = document.querySelector('.run-tests-btn');
        if (runTestsBtn) {
            runTestsBtn.addEventListener('click', () => {
                this.runTests();
            });
        }

        // Hardware controls
        const calibrateBtn = document.querySelector('.calibrate-btn');
        if (calibrateBtn) {
            calibrateBtn.addEventListener('click', () => {
                this.calibrateServos();
            });
        }

        // NVIDIA controls
        const powerModeSelect = document.getElementById('powerMode');
        if (powerModeSelect) {
            powerModeSelect.addEventListener('change', (e) => {
                this.changePowerMode(e.target.value);
            });
        }

        const thermalTargetSlider = document.getElementById('thermalTarget');
        if (thermalTargetSlider) {
            thermalTargetSlider.addEventListener('input', (e) => {
                document.getElementById('thermalValue').textContent = `${e.target.value}°C`;
                this.setThermalTarget(e.target.value);
            });
        }

        // Window resize handler
        window.addEventListener('resize', () => {
            this.handleResize();
        });
    }

    connectWebSocket() {
        try {
            // Use secure WebSocket in production, regular WebSocket for local development
            const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
            const host = window.location.hostname || 'localhost';
            const port = '8765';

            this.websocket = new WebSocket(`${protocol}//${host}:${port}`);

            this.websocket.onopen = () => {
                console.log('WebSocket connected');
                this.isConnected = true;
                this.reconnectAttempts = 0;
                this.updateConnectionStatus('connected', 'Connected');

                // Request initial data
                this.sendWebSocketMessage({
                    type: 'request_data',
                    agent: this.currentAgent
                });
            };

            this.websocket.onmessage = (event) => {
                try {
                    const data = JSON.parse(event.data);
                    this.handleWebSocketMessage(data);
                } catch (error) {
                    console.error('Error parsing WebSocket message:', error);
                }
            };

            this.websocket.onclose = () => {
                console.log('WebSocket disconnected');
                this.isConnected = false;
                this.updateConnectionStatus('disconnected', 'Disconnected');
                this.attemptReconnect();
            };

            this.websocket.onerror = (error) => {
                console.error('WebSocket error:', error);
                this.updateConnectionStatus('error', 'Connection Error');
            };

        } catch (error) {
            console.error('Failed to connect WebSocket:', error);
            this.updateConnectionStatus('disconnected', 'Connection Failed');
            this.attemptReconnect();
        }
    }

    attemptReconnect() {
        if (this.reconnectAttempts < this.maxReconnectAttempts) {
            this.reconnectAttempts++;
            console.log(`Attempting to reconnect... (${this.reconnectAttempts}/${this.maxReconnectAttempts})`);
            this.updateConnectionStatus('connecting', `Reconnecting... (${this.reconnectAttempts}/${this.maxReconnectAttempts})`);

            setTimeout(() => {
                this.connectWebSocket();
            }, 2000 * this.reconnectAttempts); // Exponential backoff
        } else {
            console.log('Max reconnection attempts reached');
            this.updateConnectionStatus('disconnected', 'Connection Failed');
        }
    }

    sendWebSocketMessage(message) {
        if (this.websocket && this.websocket.readyState === WebSocket.OPEN) {
            this.websocket.send(JSON.stringify(message));
        }
    }

    handleWebSocketMessage(data) {
        switch (data.type) {
            case 'system_update':
                this.updateSystemMetrics(data.metrics);
                break;
            case 'agent_data':
                this.updateAgentData(data.agent, data.data);
                break;
            case 'alert':
                this.addAlert(data.level, data.message);
                break;
            case 'test_result':
                this.handleTestResult(data.result);
                break;
            case 'motion_status':
                this.updateMotionStatus(data.status);
                break;
            case 'screenshot_ready':
                this.handleScreenshotReady(data.url);
                break;
            default:
                console.log('Unknown message type:', data.type);
        }
    }

    updateConnectionStatus(status, text) {
        const indicator = document.getElementById('connectionStatus').querySelector('.connection-indicator');
        const textElement = document.getElementById('connectionStatus').querySelector('.connection-text');

        indicator.className = `connection-indicator ${status}`;
        textElement.textContent = text;
    }

    switchAgent(agentId) {
        // Update navigation
        document.querySelectorAll('.agent-btn').forEach(btn => {
            btn.classList.remove('active');
        });
        document.querySelector(`[data-agent="${agentId}"]`).classList.add('active');

        // Update panels
        document.querySelectorAll('.agent-panel').forEach(panel => {
            panel.classList.remove('active');
        });
        document.getElementById(`panel-${agentId}`).classList.add('active');

        this.currentAgent = agentId;

        // Request fresh data for the new agent
        this.sendWebSocketMessage({
            type: 'request_data',
            agent: agentId
        });

        // Update charts for the new agent
        this.updateChartsForAgent(agentId);
    }

    updateSystemMetrics(metrics) {
        // Update quick stats
        const cpuUsage = document.getElementById('cpuUsage');
        const memoryUsage = document.getElementById('memoryUsage');
        const temperature = document.getElementById('temperature');
        const activeAgents = document.getElementById('activeAgents');

        if (cpuUsage) cpuUsage.textContent = `${metrics.cpu || 0}%`;
        if (memoryUsage) memoryUsage.textContent = `${metrics.memory || 0}%`;
        if (temperature) temperature.textContent = `${metrics.temperature || 0}°C`;
        if (activeAgents) activeAgents.textContent = metrics.activeAgents || 8;

        // Update system status
        const systemStatus = document.getElementById('systemStatus');
        if (systemStatus) {
            const indicator = systemStatus.querySelector('.status-indicator');
            const text = systemStatus.querySelector('.status-text');

            if (metrics.systemHealth > 90) {
                indicator.className = 'status-indicator online';
                text.textContent = 'System Online';
            } else if (metrics.systemHealth > 70) {
                indicator.className = 'status-indicator warning';
                text.textContent = 'System Warning';
            } else {
                indicator.className = 'status-indicator error';
                text.textContent = 'System Error';
            }
        }

        this.systemData = { ...this.systemData, ...metrics };
    }

    updateAgentData(agent, data) {
        // Store the data for the specific agent
        this.systemData[agent] = data;

        // Update the UI if this is the currently active agent
        if (agent === this.currentAgent) {
            this.updateCurrentAgentDisplay(data);
        }
    }

    updateCurrentAgentDisplay(data) {
        switch (this.currentAgent) {
            case 'project_manager':
                this.updateProjectManagerDisplay(data);
                break;
            case 'qa_tester':
                this.updateQADisplay(data);
                break;
            case 'imagineer':
                this.updateImagineerDisplay(data);
                break;
            case 'video_model_trainer':
                this.updateVideoModelDisplay(data);
                break;
            case 'star_wars_expert':
                this.updateStarWarsDisplay(data);
                break;
            case 'super_coder':
                this.updateSuperCoderDisplay(data);
                break;
            case 'ux_designer':
                this.updateUXDisplay(data);
                break;
            case 'nvidia_specialist':
                this.updateNvidiaDisplay(data);
                break;
        }
    }

    updateProjectManagerDisplay(data) {
        // Update health indicator
        const healthScore = document.querySelector('.health-score');
        const healthStatus = document.querySelector('.health-status');
        if (healthScore && data.systemHealth !== undefined) {
            healthScore.textContent = `${data.systemHealth}%`;

            if (data.systemHealth > 90) {
                healthScore.parentElement.className = 'health-indicator excellent';
                healthStatus.textContent = 'Excellent';
            } else if (data.systemHealth > 70) {
                healthScore.parentElement.className = 'health-indicator good';
                healthStatus.textContent = 'Good';
            } else {
                healthScore.parentElement.className = 'health-indicator poor';
                healthStatus.textContent = 'Poor';
            }
        }

        // Update performance chart
        if (data.performanceData && this.chartInstances.performanceChart) {
            this.chartInstances.performanceChart.data.datasets[0].data = data.performanceData;
            this.chartInstances.performanceChart.update();
        }
    }

    updateQADisplay(data) {
        if (data.testResults) {
            const passedCount = document.querySelector('.test-stat.passed .test-count');
            const failedCount = document.querySelector('.test-stat.failed .test-count');
            const skippedCount = document.querySelector('.test-stat.skipped .test-count');

            if (passedCount) passedCount.textContent = data.testResults.passed || 0;
            if (failedCount) failedCount.textContent = data.testResults.failed || 0;
            if (skippedCount) skippedCount.textContent = data.testResults.skipped || 0;
        }

        if (data.qualityScore) {
            const qualityScore = document.querySelector('.quality-score');
            if (qualityScore) qualityScore.textContent = `${data.qualityScore}%`;
        }
    }

    updateImagineerDisplay(data) {
        if (data.servoStatus) {
            this.updateServoGrid(data.servoStatus);
        }

        if (data.animationQueue) {
            this.updateAnimationQueue(data.animationQueue);
        }

        // Update motion visualizer
        if (data.motionData && this.chartInstances.motionVisualizer) {
            this.updateMotionVisualizer(data.motionData);
        }
    }

    updateVideoModelDisplay(data) {
        if (data.frameRate) {
            const frameRateElement = document.getElementById('frameRate');
            if (frameRateElement) frameRateElement.textContent = `${data.frameRate} FPS`;
        }

        if (data.accuracy) {
            const accuracyElement = document.getElementById('detectionAccuracy');
            if (accuracyElement) accuracyElement.textContent = `${data.accuracy}%`;
        }

        if (data.objectCount !== undefined) {
            const objectCountElement = document.getElementById('objectCount');
            if (objectCountElement) objectCountElement.textContent = data.objectCount;
        }

        // Update camera feed
        if (data.cameraFrame) {
            this.updateCameraFeed(data.cameraFrame);
        }
    }

    updateStarWarsDisplay(data) {
        if (data.authenticityScore) {
            const authScore = document.querySelector('.authenticity-score');
            if (authScore) authScore.textContent = `${data.authenticityScore}%`;
        }

        if (data.interactionQuality) {
            // Update interaction quality metrics
            // Implementation would depend on specific data structure
        }
    }

    updateSuperCoderDisplay(data) {
        if (data.performance) {
            const cpuBar = document.querySelector('.perf-metric:nth-child(1) .perf-fill');
            const memoryBar = document.querySelector('.perf-metric:nth-child(2) .perf-fill');
            const gpuBar = document.querySelector('.perf-metric:nth-child(3) .perf-fill');

            if (cpuBar) cpuBar.style.width = `${data.performance.cpu || 0}%`;
            if (memoryBar) memoryBar.style.width = `${data.performance.memory || 0}%`;
            if (gpuBar) gpuBar.style.width = `${data.performance.gpu || 0}%`;

            // Update corresponding values
            const cpuValue = document.querySelector('.perf-metric:nth-child(1) .perf-value');
            const memoryValue = document.querySelector('.perf-metric:nth-child(2) .perf-value');
            const gpuValue = document.querySelector('.perf-metric:nth-child(3) .perf-value');

            if (cpuValue) cpuValue.textContent = `${data.performance.cpu || 0}%`;
            if (memoryValue) memoryValue.textContent = `${data.performance.memory || 0}%`;
            if (gpuValue) gpuValue.textContent = `${data.performance.gpu || 0}%`;
        }
    }

    updateUXDisplay(data) {
        if (data.accessibilityScore) {
            const accessibilityScore = document.querySelector('.accessibility-score');
            if (accessibilityScore) accessibilityScore.textContent = `${data.accessibilityScore}%`;
        }

        // Update interaction heatmap
        if (data.interactionData && this.chartInstances.interactionHeatmap) {
            this.updateInteractionHeatmap(data.interactionData);
        }
    }

    updateNvidiaDisplay(data) {
        if (data.gpuUsage) {
            // Update GPU meter
            const gpuStats = document.querySelectorAll('.gpu-stat span:last-child');
            if (gpuStats[0]) gpuStats[0].textContent = `${data.gpuUsage}%`;
            if (gpuStats[1] && data.gpuMemory) gpuStats[1].textContent = data.gpuMemory;
        }

        if (data.temperature) {
            const tempValue = document.querySelector('.temp-value');
            if (tempValue) tempValue.textContent = `${data.temperature}°C`;

            const tempStatus = document.querySelector('.temp-status');
            if (tempStatus) {
                if (data.temperature < 60) {
                    tempStatus.textContent = 'Safe';
                    tempStatus.className = 'temp-status safe';
                } else if (data.temperature < 75) {
                    tempStatus.textContent = 'Warm';
                    tempStatus.className = 'temp-status warning';
                } else {
                    tempStatus.textContent = 'Hot';
                    tempStatus.className = 'temp-status danger';
                }
            }
        }

        if (data.powerConsumption) {
            const powerItems = document.querySelectorAll('.power-item span:last-child');
            if (powerItems[0]) powerItems[0].textContent = `${data.powerConsumption.current}W`;
            if (powerItems[1]) powerItems[1].textContent = `${data.powerConsumption.peak}W`;
            if (powerItems[2]) powerItems[2].textContent = `${data.powerConsumption.efficiency}%`;
        }
    }

    initializeCharts() {
        // Initialize performance chart for Project Manager
        const performanceCanvas = document.getElementById('performanceChart');
        if (performanceCanvas) {
            const ctx = performanceCanvas.getContext('2d');
            this.chartInstances.performanceChart = this.createLineChart(ctx, 'System Performance', ['CPU', 'Memory', 'GPU']);
        }

        // Initialize accuracy chart for Video Model Trainer
        const accuracyCanvas = document.getElementById('accuracyChart');
        if (accuracyCanvas) {
            const ctx = accuracyCanvas.getContext('2d');
            this.chartInstances.accuracyChart = this.createLineChart(ctx, 'Detection Accuracy', ['Accuracy']);
        }

        // Initialize motion visualizer for Imagineer
        const motionCanvas = document.getElementById('motionVisualizer');
        if (motionCanvas) {
            this.initializeMotionVisualizer(motionCanvas);
        }

        // Initialize GPU chart for NVIDIA Specialist
        const gpuCanvas = document.getElementById('gpuChart');
        if (gpuCanvas) {
            this.initializeGPUChart(gpuCanvas);
        }

        // Initialize thermal chart
        const thermalCanvas = document.getElementById('thermalChart');
        if (thermalCanvas) {
            const ctx = thermalCanvas.getContext('2d');
            this.chartInstances.thermalChart = this.createLineChart(ctx, 'Temperature', ['Temperature']);
        }

        // Initialize interaction heatmap for UX Designer
        const heatmapCanvas = document.getElementById('interactionHeatmap');
        if (heatmapCanvas) {
            this.initializeInteractionHeatmap(heatmapCanvas);
        }
    }

    createLineChart(ctx, label, datasets) {
        // Simple chart implementation without Chart.js dependency
        return {
            data: {
                labels: Array.from({length: 20}, (_, i) => i),
                datasets: datasets.map((name, index) => ({
                    label: name,
                    data: Array.from({length: 20}, () => Math.random() * 100),
                    color: `hsl(${index * 120}, 70%, 50%)`
                }))
            },
            update: function() {
                // Simple update method - in production, use Chart.js or similar
                console.log('Chart updated');
            }
        };
    }

    initializeMotionVisualizer(canvas) {
        const ctx = canvas.getContext('2d');
        this.chartInstances.motionVisualizer = {
            canvas: canvas,
            ctx: ctx,
            draw: (data) => {
                ctx.clearRect(0, 0, canvas.width, canvas.height);
                ctx.fillStyle = '#334155';
                ctx.fillRect(0, 0, canvas.width, canvas.height);

                // Draw motion data representation
                if (data) {
                    ctx.strokeStyle = '#7c3aed';
                    ctx.lineWidth = 2;
                    ctx.beginPath();
                    data.forEach((point, index) => {
                        const x = (index / data.length) * canvas.width;
                        const y = (1 - point / 100) * canvas.height;
                        if (index === 0) ctx.moveTo(x, y);
                        else ctx.lineTo(x, y);
                    });
                    ctx.stroke();
                }
            }
        };
    }

    initializeGPUChart(canvas) {
        const ctx = canvas.getContext('2d');
        this.chartInstances.gpuChart = {
            canvas: canvas,
            ctx: ctx,
            draw: (usage) => {
                const centerX = canvas.width / 2;
                const centerY = canvas.height / 2;
                const radius = Math.min(centerX, centerY) - 10;

                ctx.clearRect(0, 0, canvas.width, canvas.height);

                // Draw background circle
                ctx.beginPath();
                ctx.arc(centerX, centerY, radius, 0, 2 * Math.PI);
                ctx.strokeStyle = '#475569';
                ctx.lineWidth = 8;
                ctx.stroke();

                // Draw usage arc
                const angle = (usage / 100) * 2 * Math.PI - Math.PI / 2;
                ctx.beginPath();
                ctx.arc(centerX, centerY, radius, -Math.PI / 2, angle);
                ctx.strokeStyle = '#16a34a';
                ctx.lineWidth = 8;
                ctx.stroke();

                // Draw usage text
                ctx.fillStyle = '#f8fafc';
                ctx.font = '24px Inter';
                ctx.textAlign = 'center';
                ctx.fillText(`${usage}%`, centerX, centerY + 8);
            }
        };
    }

    initializeInteractionHeatmap(canvas) {
        const ctx = canvas.getContext('2d');
        this.chartInstances.interactionHeatmap = {
            canvas: canvas,
            ctx: ctx,
            draw: (data) => {
                ctx.clearRect(0, 0, canvas.width, canvas.height);

                // Draw heatmap grid
                const gridSize = 20;
                const rows = Math.floor(canvas.height / gridSize);
                const cols = Math.floor(canvas.width / gridSize);

                for (let i = 0; i < rows; i++) {
                    for (let j = 0; j < cols; j++) {
                        const intensity = data ? (data[i * cols + j] || 0) : Math.random();
                        const alpha = intensity * 0.8 + 0.1;
                        ctx.fillStyle = `rgba(190, 24, 93, ${alpha})`;
                        ctx.fillRect(j * gridSize, i * gridSize, gridSize - 1, gridSize - 1);
                    }
                }
            }
        };
    }

    updateChartsForAgent(agentId) {
        switch (agentId) {
            case 'project_manager':
                if (this.chartInstances.performanceChart) {
                    // Update with mock data - replace with real data
                    this.chartInstances.performanceChart.update();
                }
                break;
            case 'video_model_trainer':
                if (this.chartInstances.accuracyChart) {
                    this.chartInstances.accuracyChart.update();
                }
                break;
            case 'imagineer':
                if (this.chartInstances.motionVisualizer) {
                    const mockData = Array.from({length: 20}, () => Math.random() * 100);
                    this.chartInstances.motionVisualizer.draw(mockData);
                }
                break;
            case 'nvidia_specialist':
                if (this.chartInstances.gpuChart) {
                    this.chartInstances.gpuChart.draw(78); // Mock GPU usage
                }
                if (this.chartInstances.thermalChart) {
                    this.chartInstances.thermalChart.update();
                }
                break;
            case 'ux_designer':
                if (this.chartInstances.interactionHeatmap) {
                    this.chartInstances.interactionHeatmap.draw();
                }
                break;
        }
    }

    populateServoGrid() {
        const servoGrid = document.getElementById('servoGrid');
        if (servoGrid) {
            servoGrid.innerHTML = '';
            for (let i = 0; i < 16; i++) {
                const servoItem = document.createElement('div');
                servoItem.className = 'servo-item';
                servoItem.innerHTML = `
                    <div class="servo-number">${i + 1}</div>
                    <div class="servo-status"></div>
                `;
                servoGrid.appendChild(servoItem);
            }
        }
    }

    updateServoGrid(servoStatus) {
        const servoItems = document.querySelectorAll('.servo-item');
        servoItems.forEach((item, index) => {
            const statusIndicator = item.querySelector('.servo-status');
            if (servoStatus && servoStatus[index]) {
                statusIndicator.style.backgroundColor = servoStatus[index] === 'online' ? '#10b981' : '#ef4444';
            }
        });
    }

    updateAnimationQueue(queue) {
        const queueContainer = document.querySelector('.animation-queue');
        if (queueContainer && queue) {
            queueContainer.innerHTML = '';
            queue.forEach((item, index) => {
                const queueItem = document.createElement('div');
                queueItem.className = `queue-item ${index === 0 ? 'active' : 'pending'}`;
                queueItem.textContent = item.name;
                queueContainer.appendChild(queueItem);
            });
        }
    }

    startSystemMonitoring() {
        // Simulate system monitoring with mock data
        setInterval(() => {
            if (this.isConnected) {
                const mockMetrics = {
                    cpu: Math.floor(Math.random() * 30) + 40,
                    memory: Math.floor(Math.random() * 20) + 30,
                    temperature: Math.floor(Math.random() * 15) + 45,
                    systemHealth: Math.floor(Math.random() * 10) + 90,
                    activeAgents: 8
                };
                this.updateSystemMetrics(mockMetrics);
            }
        }, 5000);
    }

    updateUptime() {
        const uptimeElement = document.getElementById('uptime');
        if (uptimeElement) {
            const startTime = new Date();
            setInterval(() => {
                const now = new Date();
                const diff = Math.floor((now - startTime) / 1000);
                const hours = Math.floor(diff / 3600).toString().padStart(2, '0');
                const minutes = Math.floor((diff % 3600) / 60).toString().padStart(2, '0');
                const seconds = (diff % 60).toString().padStart(2, '0');
                uptimeElement.textContent = `Uptime: ${hours}:${minutes}:${seconds}`;
            }, 1000);
        }
    }

    addAlert(level, message) {
        const alertList = document.getElementById('alertList');
        if (alertList) {
            const alertItem = document.createElement('div');
            alertItem.className = `alert-item ${level}`;
            alertItem.textContent = message;

            alertList.insertBefore(alertItem, alertList.firstChild);

            // Remove old alerts if there are too many
            while (alertList.children.length > 5) {
                alertList.removeChild(alertList.lastChild);
            }
        }
    }

    takeScreenshot() {
        this.sendWebSocketMessage({
            type: 'take_screenshot',
            timestamp: Date.now()
        });

        // Show loading state
        const btn = document.getElementById('screenshotBtn');
        const originalText = btn.textContent;
        btn.textContent = 'Taking...';
        btn.disabled = true;

        setTimeout(() => {
            btn.textContent = originalText;
            btn.disabled = false;
        }, 3000);
    }

    handleScreenshotReady(url) {
        // Create a download link for the screenshot
        const link = document.createElement('a');
        link.href = url;
        link.download = `r2d2-screenshot-${Date.now()}.png`;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    }

    refreshCurrentPanel() {
        this.sendWebSocketMessage({
            type: 'request_data',
            agent: this.currentAgent,
            force_refresh: true
        });
    }

    triggerMotion(motion) {
        this.sendWebSocketMessage({
            type: 'trigger_motion',
            motion: motion,
            timestamp: Date.now()
        });

        this.addAlert('info', `Motion triggered: ${motion}`);
    }

    runTests() {
        this.sendWebSocketMessage({
            type: 'run_tests',
            timestamp: Date.now()
        });

        this.addAlert('info', 'Running comprehensive tests...');
    }

    calibrateServos() {
        this.sendWebSocketMessage({
            type: 'calibrate_servos',
            timestamp: Date.now()
        });

        this.addAlert('info', 'Calibrating servos...');
    }

    changePowerMode(mode) {
        this.sendWebSocketMessage({
            type: 'change_power_mode',
            mode: mode,
            timestamp: Date.now()
        });

        this.addAlert('info', `Power mode changed to: ${mode}`);
    }

    setThermalTarget(target) {
        this.sendWebSocketMessage({
            type: 'set_thermal_target',
            target: parseInt(target),
            timestamp: Date.now()
        });
    }

    handleResize() {
        // Redraw canvas-based charts on resize
        Object.values(this.chartInstances).forEach(chart => {
            if (chart.canvas) {
                chart.draw();
            }
        });
    }

    updateCameraFeed(frameData) {
        const canvas = document.getElementById('cameraCanvas');
        if (canvas && frameData) {
            const ctx = canvas.getContext('2d');
            const img = new Image();
            img.onload = () => {
                ctx.clearRect(0, 0, canvas.width, canvas.height);
                ctx.drawImage(img, 0, 0, canvas.width, canvas.height);
            };
            img.src = `data:image/jpeg;base64,${frameData}`;
        }
    }
}

// Initialize dashboard when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.r2d2Dashboard = new R2D2Dashboard();

    // Add some initial mock alerts
    setTimeout(() => {
        window.r2d2Dashboard.addAlert('success', 'All systems initialized successfully');
        window.r2d2Dashboard.addAlert('info', 'WebSocket connection established');
    }, 1000);
});

// Handle page visibility changes to manage WebSocket connections
document.addEventListener('visibilitychange', () => {
    if (document.visibilityState === 'visible' && window.r2d2Dashboard) {
        if (!window.r2d2Dashboard.isConnected) {
            window.r2d2Dashboard.connectWebSocket();
        }
    }
});

// Export for use in other scripts
if (typeof module !== 'undefined' && module.exports) {
    module.exports = R2D2Dashboard;
}