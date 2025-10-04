#!/usr/bin/env node
/**
 * Elite QA Real-time Monitoring System
 * Continuous health tracking and automated alerting during logging implementation
 *
 * MISSION: Proactive detection of system degradation with instant alerts
 * APPROACH: Multi-layer monitoring with automated response capabilities
 */

const fs = require('fs');
const path = require('path');
const WebSocket = require('ws');
const EventEmitter = require('events');
const axios = require('axios');

class RealTimeMonitoringSystem extends EventEmitter {
    constructor() {
        super();

        this.configFile = path.join(__dirname, 'qa_monitoring_config.json');
        this.alertsFile = path.join(__dirname, 'qa_monitoring_alerts.json');
        this.metricsFile = path.join(__dirname, 'qa_monitoring_metrics.json');

        this.config = {
            monitoring: {
                dashboardHealthCheck: {
                    enabled: true,
                    interval: 10000, // 10 seconds
                    timeout: 5000,
                    maxResponseTime: 1000 // ms
                },
                websocketMonitoring: {
                    enabled: true,
                    interval: 15000, // 15 seconds
                    connectionTimeout: 3000,
                    maxReconnectAttempts: 3
                },
                memoryMonitoring: {
                    enabled: true,
                    interval: 30000, // 30 seconds
                    maxMemoryUsage: 1024, // MB
                    maxHeapUsage: 512 // MB
                },
                performanceMonitoring: {
                    enabled: true,
                    interval: 60000, // 1 minute
                    baselineDeviationThreshold: 50 // percentage
                }
            },
            alerting: {
                immediateAlerts: true,
                alertCooldown: 30000, // 30 seconds
                escalationThreshold: 3, // consecutive failures
                autoRecoveryEnabled: false
            },
            persistence: {
                maxAlerts: 1000,
                maxMetrics: 10000,
                retentionPeriod: 86400000 // 24 hours
            }
        };

        this.isMonitoring = false;
        this.intervals = {};
        this.connections = new Map();
        this.metrics = [];
        this.alerts = [];
        this.consecutiveFailures = new Map();
        this.lastAlerts = new Map();

        console.log('🔄 Elite QA Real-time Monitoring System Initialized');
        this.loadConfiguration();
        this.setupEventHandlers();
    }

    loadConfiguration() {
        try {
            if (fs.existsSync(this.configFile)) {
                const config = JSON.parse(fs.readFileSync(this.configFile, 'utf8'));
                this.config = { ...this.config, ...config };
                console.log('📋 Monitoring configuration loaded');
            } else {
                this.saveConfiguration();
                console.log('📋 Default monitoring configuration created');
            }

            if (fs.existsSync(this.alertsFile)) {
                this.alerts = JSON.parse(fs.readFileSync(this.alertsFile, 'utf8'));
                console.log(`🚨 Loaded ${this.alerts.length} historical alerts`);
            }

            if (fs.existsSync(this.metricsFile)) {
                this.metrics = JSON.parse(fs.readFileSync(this.metricsFile, 'utf8'));
                console.log(`📊 Loaded ${this.metrics.length} historical metrics`);
            }

        } catch (error) {
            console.error('⚠️  Failed to load configuration:', error.message);
        }
    }

    saveConfiguration() {
        try {
            fs.writeFileSync(this.configFile, JSON.stringify(this.config, null, 2));
        } catch (error) {
            console.error('⚠️  Failed to save configuration:', error.message);
        }
    }

    setupEventHandlers() {
        this.on('alert', (alert) => {
            this.handleAlert(alert);
        });

        this.on('metric', (metric) => {
            this.handleMetric(metric);
        });

        this.on('recovery', (recovery) => {
            this.handleRecovery(recovery);
        });
    }

    startMonitoring() {
        if (this.isMonitoring) {
            console.log('⚠️  Monitoring is already running');
            return;
        }

        console.log('\n🚀 Starting Real-time Monitoring System');
        console.log('=' .repeat(60));

        this.isMonitoring = true;

        // Dashboard health monitoring
        if (this.config.monitoring.dashboardHealthCheck.enabled) {
            this.intervals.dashboardHealth = setInterval(() => {
                this.checkDashboardHealth();
            }, this.config.monitoring.dashboardHealthCheck.interval);
            console.log(`✅ Dashboard health monitoring: ${this.config.monitoring.dashboardHealthCheck.interval / 1000}s intervals`);
        }

        // WebSocket connection monitoring
        if (this.config.monitoring.websocketMonitoring.enabled) {
            this.intervals.websocketHealth = setInterval(() => {
                this.checkWebSocketHealth();
            }, this.config.monitoring.websocketMonitoring.interval);
            console.log(`✅ WebSocket monitoring: ${this.config.monitoring.websocketMonitoring.interval / 1000}s intervals`);
        }

        // Memory usage monitoring
        if (this.config.monitoring.memoryMonitoring.enabled) {
            this.intervals.memoryMonitoring = setInterval(() => {
                this.checkMemoryUsage();
            }, this.config.monitoring.memoryMonitoring.interval);
            console.log(`✅ Memory monitoring: ${this.config.monitoring.memoryMonitoring.interval / 1000}s intervals`);
        }

        // Performance monitoring
        if (this.config.monitoring.performanceMonitoring.enabled) {
            this.intervals.performanceMonitoring = setInterval(() => {
                this.checkPerformanceMetrics();
            }, this.config.monitoring.performanceMonitoring.interval);
            console.log(`✅ Performance monitoring: ${this.config.monitoring.performanceMonitoring.interval / 1000}s intervals`);
        }

        console.log('\n🔄 Monitoring system active - watching for issues...');
    }

    stopMonitoring() {
        if (!this.isMonitoring) {
            console.log('⚠️  Monitoring is not running');
            return;
        }

        console.log('\n🛑 Stopping Real-time Monitoring System');

        // Clear all intervals
        Object.keys(this.intervals).forEach(key => {
            clearInterval(this.intervals[key]);
        });
        this.intervals = {};

        // Close all connections
        this.connections.forEach(connection => {
            if (connection.readyState === WebSocket.OPEN) {
                connection.close();
            }
        });
        this.connections.clear();

        this.isMonitoring = false;
        console.log('✅ Monitoring system stopped');
    }

    async checkDashboardHealth() {
        const checkId = 'dashboard_health';
        try {
            const startTime = Date.now();
            const response = await axios.get('http://localhost:8765', {
                timeout: this.config.monitoring.dashboardHealthCheck.timeout
            });
            const responseTime = Date.now() - startTime;

            const metric = {
                type: 'dashboard_health',
                timestamp: new Date().toISOString(),
                responseTime: responseTime,
                statusCode: response.status,
                status: response.status === 200 ? 'healthy' : 'degraded'
            };

            this.emit('metric', metric);

            if (responseTime > this.config.monitoring.dashboardHealthCheck.maxResponseTime) {
                this.emit('alert', {
                    type: 'performance_degradation',
                    severity: 'warning',
                    message: `Dashboard response time ${responseTime}ms exceeds threshold ${this.config.monitoring.dashboardHealthCheck.maxResponseTime}ms`,
                    metric: metric
                });
            }

            // Reset consecutive failures on success
            this.consecutiveFailures.set(checkId, 0);

        } catch (error) {
            this.incrementFailureCount(checkId);

            this.emit('alert', {
                type: 'dashboard_failure',
                severity: 'critical',
                message: `Dashboard health check failed: ${error.message}`,
                consecutiveFailures: this.consecutiveFailures.get(checkId),
                error: error.message
            });
        }
    }

    async checkWebSocketHealth() {
        const checkId = 'websocket_health';
        const endpoints = [
            { url: 'ws://localhost:8766', name: 'MainDashboard' },
            { url: 'ws://localhost:8768', name: 'BehavioralIntelligence' }
        ];

        for (const endpoint of endpoints) {
            try {
                await this.testWebSocketConnection(endpoint.url, endpoint.name);
            } catch (error) {
                this.incrementFailureCount(`${checkId}_${endpoint.name}`);

                this.emit('alert', {
                    type: 'websocket_failure',
                    severity: 'high',
                    message: `WebSocket ${endpoint.name} connection failed: ${error.message}`,
                    endpoint: endpoint.url,
                    consecutiveFailures: this.consecutiveFailures.get(`${checkId}_${endpoint.name}`)
                });
            }
        }
    }

    testWebSocketConnection(url, name) {
        return new Promise((resolve, reject) => {
            const startTime = Date.now();
            const ws = new WebSocket(url);

            const timeout = setTimeout(() => {
                ws.terminate();
                reject(new Error('Connection timeout'));
            }, this.config.monitoring.websocketMonitoring.connectionTimeout);

            ws.on('open', () => {
                clearTimeout(timeout);
                const connectionTime = Date.now() - startTime;

                this.emit('metric', {
                    type: 'websocket_health',
                    name: name,
                    timestamp: new Date().toISOString(),
                    connectionTime: connectionTime,
                    status: 'connected'
                });

                ws.close();
                resolve();
            });

            ws.on('error', (error) => {
                clearTimeout(timeout);
                reject(error);
            });
        });
    }

    checkMemoryUsage() {
        const memUsage = process.memoryUsage();
        const metric = {
            type: 'memory_usage',
            timestamp: new Date().toISOString(),
            rss: Math.round(memUsage.rss / 1024 / 1024),
            heapUsed: Math.round(memUsage.heapUsed / 1024 / 1024),
            heapTotal: Math.round(memUsage.heapTotal / 1024 / 1024),
            external: Math.round(memUsage.external / 1024 / 1024)
        };

        this.emit('metric', metric);

        // Check for memory alerts
        if (metric.rss > this.config.monitoring.memoryMonitoring.maxMemoryUsage) {
            this.emit('alert', {
                type: 'memory_high',
                severity: 'warning',
                message: `Memory usage ${metric.rss}MB exceeds threshold ${this.config.monitoring.memoryMonitoring.maxMemoryUsage}MB`,
                metric: metric
            });
        }

        if (metric.heapUsed > this.config.monitoring.memoryMonitoring.maxHeapUsage) {
            this.emit('alert', {
                type: 'heap_high',
                severity: 'warning',
                message: `Heap usage ${metric.heapUsed}MB exceeds threshold ${this.config.monitoring.memoryMonitoring.maxHeapUsage}MB`,
                metric: metric
            });
        }
    }

    async checkPerformanceMetrics() {
        try {
            // Load baseline for comparison
            const baselineFile = path.join(__dirname, 'qa_baseline_metrics.json');
            if (!fs.existsSync(baselineFile)) {
                return; // No baseline to compare against
            }

            const baseline = JSON.parse(fs.readFileSync(baselineFile, 'utf8'));

            // Check current dashboard response time
            const startTime = Date.now();
            await axios.get('http://localhost:8765', { timeout: 5000 });
            const currentResponseTime = Date.now() - startTime;

            const baselineResponseTime = baseline.performance.server_response_time;
            const deviation = ((currentResponseTime - baselineResponseTime) / baselineResponseTime) * 100;

            const metric = {
                type: 'performance_comparison',
                timestamp: new Date().toISOString(),
                currentResponseTime: currentResponseTime,
                baselineResponseTime: baselineResponseTime,
                deviation: Math.round(deviation)
            };

            this.emit('metric', metric);

            if (Math.abs(deviation) > this.config.monitoring.performanceMonitoring.baselineDeviationThreshold) {
                this.emit('alert', {
                    type: 'performance_deviation',
                    severity: deviation > 0 ? 'warning' : 'info',
                    message: `Performance deviation ${Math.round(deviation)}% from baseline`,
                    metric: metric
                });
            }

        } catch (error) {
            this.emit('alert', {
                type: 'performance_check_error',
                severity: 'low',
                message: `Performance check failed: ${error.message}`
            });
        }
    }

    incrementFailureCount(checkId) {
        const current = this.consecutiveFailures.get(checkId) || 0;
        this.consecutiveFailures.set(checkId, current + 1);

        if (current + 1 >= this.config.alerting.escalationThreshold) {
            this.emit('alert', {
                type: 'escalation',
                severity: 'critical',
                message: `${checkId} has failed ${current + 1} consecutive times - escalating alert`,
                checkId: checkId,
                consecutiveFailures: current + 1
            });
        }
    }

    handleAlert(alert) {
        const now = Date.now();
        const alertKey = `${alert.type}_${alert.severity}`;

        // Check alert cooldown
        const lastAlert = this.lastAlerts.get(alertKey);
        if (lastAlert && (now - lastAlert) < this.config.alerting.alertCooldown) {
            return; // Skip duplicate alert within cooldown period
        }

        this.lastAlerts.set(alertKey, now);

        // Add alert to history
        const alertRecord = {
            id: now,
            timestamp: new Date().toISOString(),
            ...alert
        };

        this.alerts.unshift(alertRecord);

        // Trim alerts to max limit
        if (this.alerts.length > this.config.persistence.maxAlerts) {
            this.alerts = this.alerts.slice(0, this.config.persistence.maxAlerts);
        }

        // Save alerts immediately
        this.saveAlerts();

        // Display alert
        this.displayAlert(alertRecord);

        // Trigger auto-recovery if enabled
        if (this.config.alerting.autoRecoveryEnabled && alert.severity === 'critical') {
            this.attemptAutoRecovery(alert);
        }
    }

    handleMetric(metric) {
        this.metrics.unshift({
            id: Date.now(),
            ...metric
        });

        // Trim metrics to max limit
        if (this.metrics.length > this.config.persistence.maxMetrics) {
            this.metrics = this.metrics.slice(0, this.config.persistence.maxMetrics);
        }

        // Save metrics periodically (every 100 metrics)
        if (this.metrics.length % 100 === 0) {
            this.saveMetrics();
        }
    }

    handleRecovery(recovery) {
        console.log(`🔄 Recovery event: ${recovery.message}`);

        // Reset failure counts
        if (recovery.checkId) {
            this.consecutiveFailures.set(recovery.checkId, 0);
        }
    }

    displayAlert(alert) {
        const severityEmojis = {
            critical: '🚨',
            high: '⚠️ ',
            warning: '⚠️ ',
            info: 'ℹ️ ',
            low: '📝'
        };

        const emoji = severityEmojis[alert.severity] || '📢';
        const timestamp = new Date(alert.timestamp).toLocaleTimeString();

        console.log(`\n${emoji} ALERT [${alert.severity.toUpperCase()}] ${timestamp}`);
        console.log(`   Type: ${alert.type}`);
        console.log(`   Message: ${alert.message}`);

        if (alert.consecutiveFailures > 1) {
            console.log(`   Consecutive Failures: ${alert.consecutiveFailures}`);
        }

        if (alert.metric) {
            console.log(`   Metric: ${JSON.stringify(alert.metric, null, 2)}`);
        }
    }

    attemptAutoRecovery(alert) {
        console.log(`🔧 Attempting auto-recovery for: ${alert.type}`);

        // Placeholder for auto-recovery logic
        // Could include:
        // - Restarting failed services
        // - Clearing memory leaks
        // - Reconnecting WebSocket connections
        // - Triggering backup systems

        this.emit('recovery', {
            type: 'auto_recovery_attempted',
            originalAlert: alert.type,
            message: `Auto-recovery attempted for ${alert.type}`
        });
    }

    saveAlerts() {
        try {
            fs.writeFileSync(this.alertsFile, JSON.stringify(this.alerts, null, 2));
        } catch (error) {
            console.error('⚠️  Failed to save alerts:', error.message);
        }
    }

    saveMetrics() {
        try {
            fs.writeFileSync(this.metricsFile, JSON.stringify(this.metrics, null, 2));
        } catch (error) {
            console.error('⚠️  Failed to save metrics:', error.message);
        }
    }

    getRecentAlerts(count = 10) {
        return this.alerts.slice(0, count);
    }

    getRecentMetrics(type = null, count = 100) {
        let metrics = this.metrics;

        if (type) {
            metrics = metrics.filter(m => m.type === type);
        }

        return metrics.slice(0, count);
    }

    getSystemHealth() {
        const recentAlerts = this.alerts.slice(0, 10);
        const criticalAlerts = recentAlerts.filter(a => a.severity === 'critical').length;
        const highAlerts = recentAlerts.filter(a => a.severity === 'high').length;
        const warningAlerts = recentAlerts.filter(a => a.severity === 'warning').length;

        let healthStatus = 'healthy';
        if (criticalAlerts > 0) {
            healthStatus = 'critical';
        } else if (highAlerts > 2) {
            healthStatus = 'degraded';
        } else if (warningAlerts > 5) {
            healthStatus = 'warning';
        }

        return {
            status: healthStatus,
            recentAlerts: {
                critical: criticalAlerts,
                high: highAlerts,
                warning: warningAlerts,
                total: recentAlerts.length
            },
            monitoring: this.isMonitoring,
            activeChecks: Object.keys(this.intervals).length
        };
    }

    generateMonitoringReport() {
        console.log('\n📊 Elite QA Real-time Monitoring Report');
        console.log('=' .repeat(60));

        const health = this.getSystemHealth();
        const statusEmojis = {
            healthy: '✅',
            warning: '⚠️ ',
            degraded: '🔴',
            critical: '🚨'
        };

        console.log(`${statusEmojis[health.status]} System Health: ${health.status.toUpperCase()}`);
        console.log(`🔄 Monitoring Active: ${health.monitoring ? 'YES' : 'NO'}`);
        console.log(`⚙️  Active Checks: ${health.activeChecks}`);

        console.log(`\n🚨 Recent Alert Summary:`);
        console.log(`   Critical: ${health.recentAlerts.critical}`);
        console.log(`   High: ${health.recentAlerts.high}`);
        console.log(`   Warning: ${health.recentAlerts.warning}`);
        console.log(`   Total: ${health.recentAlerts.total}`);

        // Recent alerts detail
        const recentAlerts = this.getRecentAlerts(5);
        if (recentAlerts.length > 0) {
            console.log(`\n📋 Last 5 Alerts:`);
            recentAlerts.forEach(alert => {
                const time = new Date(alert.timestamp).toLocaleTimeString();
                console.log(`   ${time} [${alert.severity}] ${alert.type}: ${alert.message}`);
            });
        }

        // Performance metrics
        const perfMetrics = this.getRecentMetrics('dashboard_health', 5);
        if (perfMetrics.length > 0) {
            const avgResponseTime = Math.round(
                perfMetrics.reduce((sum, m) => sum + (m.responseTime || 0), 0) / perfMetrics.length
            );
            console.log(`\n📈 Recent Performance:`);
            console.log(`   Average Response Time: ${avgResponseTime}ms`);
        }

        console.log(`\n⚙️  Configuration:`);
        console.log(`   Dashboard Check Interval: ${this.config.monitoring.dashboardHealthCheck.interval / 1000}s`);
        console.log(`   WebSocket Check Interval: ${this.config.monitoring.websocketMonitoring.interval / 1000}s`);
        console.log(`   Memory Check Interval: ${this.config.monitoring.memoryMonitoring.interval / 1000}s`);
        console.log(`   Auto-recovery: ${this.config.alerting.autoRecoveryEnabled ? 'Enabled' : 'Disabled'}`);
    }
}

// CLI Interface
if (require.main === module) {
    const monitor = new RealTimeMonitoringSystem();
    const command = process.argv[2];

    switch (command) {
        case 'start':
            monitor.startMonitoring();

            // Handle graceful shutdown
            process.on('SIGINT', () => {
                console.log('\n🛑 Shutting down monitoring system...');
                monitor.stopMonitoring();
                monitor.saveMetrics();
                monitor.saveAlerts();
                process.exit(0);
            });
            break;

        case 'health':
            const health = monitor.getSystemHealth();
            console.log('\n🏥 System Health Status');
            console.log(`Status: ${health.status}`);
            console.log(`Monitoring: ${health.monitoring ? 'Active' : 'Inactive'}`);
            console.log(`Recent Alerts: ${health.recentAlerts.total}`);
            process.exit(0);
            break;

        case 'alerts':
            const alerts = monitor.getRecentAlerts(10);
            console.log('\n🚨 Recent Alerts:');
            alerts.forEach(alert => {
                console.log(`${alert.timestamp} [${alert.severity}] ${alert.type}: ${alert.message}`);
            });
            process.exit(0);
            break;

        case 'report':
            monitor.generateMonitoringReport();
            process.exit(0);
            break;

        default:
            console.log('Elite QA Real-time Monitoring System');
            console.log('Usage:');
            console.log('  node qa_realtime_monitoring_system.js start   - Start monitoring');
            console.log('  node qa_realtime_monitoring_system.js health  - Check system health');
            console.log('  node qa_realtime_monitoring_system.js alerts  - Show recent alerts');
            console.log('  node qa_realtime_monitoring_system.js report  - Generate monitoring report');
            process.exit(0);
    }
}

module.exports = RealTimeMonitoringSystem;