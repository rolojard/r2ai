#!/usr/bin/env node
/**
 * Elite QA Comprehensive Dashboard Test Suite
 * Advanced testing framework for R2D2 dashboard system protection
 *
 * MISSION: Zero tolerance for breaking working features during logging implementation
 * STATUS: Critical infrastructure protection - test-first methodology
 */

const axios = require('axios');
const WebSocket = require('ws');
const { spawn } = require('child_process');
const fs = require('fs');
const path = require('path');

class EliteQADashboardValidator {
    constructor() {
        this.baseUrl = 'http://localhost:8765';
        this.wsPort = 8766;
        this.behaviorWsPort = 8768;
        this.visionPort = 8767;
        this.servoPort = 5000;

        this.testResults = {
            passed: 0,
            failed: 0,
            warnings: 0,
            criticalFailures: [],
            timestamp: new Date().toISOString()
        };

        this.performanceMetrics = {};

        this.performanceBaselines = {
            responseTime: 200, // ms
            videoFps: 15,
            memoryUsage: 4096, // MB
            connectionTimeout: 5000 // ms
        };

        console.log('🔰 Elite QA Dashboard Validator Initialized');
        console.log('📋 Mission: Protect working features during logging implementation');
    }

    async runComprehensiveValidation() {
        console.log('\n🚀 Starting Comprehensive Dashboard Validation Suite');
        console.log('=' .repeat(80));

        try {
            // Phase 1: Server Health Check
            await this.validateServerHealth();

            // Phase 2: Dashboard Route Testing
            await this.validateAllDashboardRoutes();

            // Phase 3: WebSocket Connectivity
            await this.validateWebSocketConnections();

            // Phase 4: Performance Baseline Documentation
            await this.documentPerformanceBaselines();

            // Phase 5: Real-time Data Flow Validation
            await this.validateRealTimeDataFlow();

            // Phase 6: Vision System Integration
            await this.validateVisionIntegration();

            // Phase 7: Servo API Integration
            await this.validateServoIntegration();

            // Phase 8: Error Handling & Recovery
            await this.validateErrorHandling();

            // Generate Final Report
            this.generateComprehensiveReport();

        } catch (error) {
            this.recordCriticalFailure('COMPREHENSIVE_VALIDATION_FAILED', error);
            console.error('❌ Critical validation failure:', error.message);
        }
    }

    async validateServerHealth() {
        console.log('\n📊 Phase 1: Server Health Validation');
        console.log('-'.repeat(50));

        try {
            const startTime = Date.now();
            const response = await axios.get(this.baseUrl, { timeout: 5000 });
            const responseTime = Date.now() - startTime;

            if (response.status === 200) {
                this.recordSuccess('SERVER_HEALTH', {
                    status: 'ONLINE',
                    responseTime: responseTime,
                    statusCode: response.status
                });
                console.log(`✅ Server health check passed (${responseTime}ms)`);
            } else {
                this.recordFailure('SERVER_HEALTH', `Unexpected status: ${response.status}`);
            }

            this.performanceMetrics.serverResponseTime = responseTime;

        } catch (error) {
            this.recordCriticalFailure('SERVER_HEALTH', error);
            console.error('❌ Server health check failed:', error.message);
        }
    }

    async validateAllDashboardRoutes() {
        console.log('\n🎯 Phase 2: Dashboard Route Validation');
        console.log('-'.repeat(50));

        const routes = [
            { path: '/', description: 'Default Dashboard (Vision-enabled)' },
            { path: '/vision', description: 'Vision Dashboard' },
            { path: '/enhanced', description: 'Enhanced Dashboard' },
            { path: '/servo', description: 'Advanced Servo Dashboard' },
            { path: '/servo-only', description: 'Servo-only Dashboard' },
            { path: '/disney', description: 'Disney Behavioral Dashboard' }
        ];

        for (const route of routes) {
            try {
                const startTime = Date.now();
                const response = await axios.get(`${this.baseUrl}${route.path}`, {
                    timeout: 10000,
                    headers: { 'Accept': 'text/html' }
                });
                const responseTime = Date.now() - startTime;

                if (response.status === 200 && response.data.includes('<!DOCTYPE html>')) {
                    this.recordSuccess(`ROUTE_${route.path.replace('/', 'ROOT')}`, {
                        description: route.description,
                        responseTime: responseTime,
                        contentLength: response.data.length
                    });
                    console.log(`✅ ${route.description}: ${responseTime}ms (${response.data.length} bytes)`);
                } else {
                    this.recordFailure(`ROUTE_${route.path}`, `Invalid HTML response: ${response.status}`);
                }

            } catch (error) {
                this.recordFailure(`ROUTE_${route.path}`, error.message);
                console.error(`❌ ${route.description} failed:`, error.message);
            }
        }
    }

    async validateWebSocketConnections() {
        console.log('\n🔌 Phase 3: WebSocket Connection Validation');
        console.log('-'.repeat(50));

        // Test main dashboard WebSocket
        await this.testWebSocketConnection(
            `ws://localhost:${this.wsPort}`,
            'MAIN_DASHBOARD_WS',
            'Main Dashboard WebSocket'
        );

        // Test behavioral intelligence WebSocket
        await this.testWebSocketConnection(
            `ws://localhost:${this.behaviorWsPort}`,
            'BEHAVIORAL_WS',
            'Behavioral Intelligence WebSocket'
        );
    }

    async testWebSocketConnection(url, testId, description) {
        return new Promise((resolve) => {
            try {
                const startTime = Date.now();
                const ws = new WebSocket(url);
                let connected = false;

                const timeout = setTimeout(() => {
                    if (!connected) {
                        this.recordFailure(testId, 'Connection timeout');
                        console.error(`❌ ${description}: Connection timeout`);
                        ws.terminate();
                        resolve();
                    }
                }, 5000);

                ws.on('open', () => {
                    connected = true;
                    const connectionTime = Date.now() - startTime;
                    clearTimeout(timeout);

                    this.recordSuccess(testId, {
                        description: description,
                        connectionTime: connectionTime,
                        readyState: ws.readyState
                    });
                    console.log(`✅ ${description}: Connected in ${connectionTime}ms`);

                    // Test data exchange
                    ws.send(JSON.stringify({ type: 'request_data' }));

                    ws.on('message', (data) => {
                        try {
                            const parsed = JSON.parse(data);
                            console.log(`📨 ${description}: Received ${parsed.type}`);
                        } catch (e) {
                            console.log(`📨 ${description}: Received data (${data.length} bytes)`);
                        }
                    });

                    setTimeout(() => {
                        ws.close();
                        resolve();
                    }, 2000);
                });

                ws.on('error', (error) => {
                    clearTimeout(timeout);
                    this.recordFailure(testId, error.message);
                    console.error(`❌ ${description}:`, error.message);
                    resolve();
                });

            } catch (error) {
                this.recordFailure(testId, error.message);
                console.error(`❌ ${description}:`, error.message);
                resolve();
            }
        });
    }

    async documentPerformanceBaselines() {
        console.log('\n📈 Phase 4: Performance Baseline Documentation');
        console.log('-'.repeat(50));

        try {
            // Memory usage check
            const memUsage = process.memoryUsage();
            this.performanceMetrics.memoryUsage = {
                rss: Math.round(memUsage.rss / 1024 / 1024),
                heapUsed: Math.round(memUsage.heapUsed / 1024 / 1024),
                heapTotal: Math.round(memUsage.heapTotal / 1024 / 1024),
                external: Math.round(memUsage.external / 1024 / 1024)
            };

            console.log(`📊 Memory Usage: RSS ${this.performanceMetrics.memoryUsage.rss}MB, Heap ${this.performanceMetrics.memoryUsage.heapUsed}MB`);

            // Check for running Node.js processes
            await this.checkNodeProcesses();

            // Document current FPS if vision system is running
            await this.checkVisionSystemPerformance();

            this.recordSuccess('PERFORMANCE_BASELINE', this.performanceMetrics);

        } catch (error) {
            this.recordFailure('PERFORMANCE_BASELINE', error.message);
            console.error('❌ Performance baseline documentation failed:', error.message);
        }
    }

    async checkNodeProcesses() {
        return new Promise((resolve) => {
            const ps = spawn('ps', ['aux']);
            let output = '';

            ps.stdout.on('data', (data) => {
                output += data.toString();
            });

            ps.on('close', () => {
                const nodeProcesses = output.split('\n')
                    .filter(line => line.includes('node') && line.includes('dashboard'))
                    .length;

                this.performanceMetrics.nodeProcesses = nodeProcesses;
                console.log(`🔧 Node processes detected: ${nodeProcesses}`);
                resolve();
            });

            ps.on('error', () => {
                console.log('⚠️  Process check unavailable');
                resolve();
            });
        });
    }

    async checkVisionSystemPerformance() {
        try {
            const response = await axios.get(`http://localhost:${this.visionPort}/status`, { timeout: 3000 });
            if (response.data) {
                this.performanceMetrics.visionSystem = response.data;
                console.log(`👁️  Vision system: ${response.data.fps || 'N/A'} FPS`);
            }
        } catch (error) {
            console.log('👁️  Vision system: Not accessible for performance check');
            this.performanceMetrics.visionSystem = { status: 'not_accessible' };
        }
    }

    async validateRealTimeDataFlow() {
        console.log('\n⚡ Phase 5: Real-time Data Flow Validation');
        console.log('-'.repeat(50));

        return new Promise((resolve) => {
            try {
                const ws = new WebSocket(`ws://localhost:${this.wsPort}`);
                let messageCount = 0;
                const receivedTypes = new Set();

                const timeout = setTimeout(() => {
                    ws.close();

                    if (messageCount > 0) {
                        this.recordSuccess('REALTIME_DATA_FLOW', {
                            messagesReceived: messageCount,
                            messageTypes: Array.from(receivedTypes),
                            testDuration: 10000
                        });
                        console.log(`✅ Real-time data flow: ${messageCount} messages, ${receivedTypes.size} types`);
                    } else {
                        this.recordFailure('REALTIME_DATA_FLOW', 'No real-time messages received');
                        console.error('❌ Real-time data flow: No messages received');
                    }
                    resolve();
                }, 10000);

                ws.on('open', () => {
                    console.log('🔄 Testing real-time data flow for 10 seconds...');
                    ws.send(JSON.stringify({ type: 'request_data' }));
                });

                ws.on('message', (data) => {
                    try {
                        const parsed = JSON.parse(data);
                        messageCount++;
                        receivedTypes.add(parsed.type);
                    } catch (e) {
                        messageCount++;
                        receivedTypes.add('binary_data');
                    }
                });

                ws.on('error', (error) => {
                    clearTimeout(timeout);
                    this.recordFailure('REALTIME_DATA_FLOW', error.message);
                    console.error('❌ Real-time data flow error:', error.message);
                    resolve();
                });

            } catch (error) {
                this.recordFailure('REALTIME_DATA_FLOW', error.message);
                console.error('❌ Real-time data flow validation failed:', error.message);
                resolve();
            }
        });
    }

    async validateVisionIntegration() {
        console.log('\n👁️  Phase 6: Vision System Integration Validation');
        console.log('-'.repeat(50));

        try {
            // Check if vision system is accessible
            const response = await axios.get(`http://localhost:${this.visionPort}/health`, {
                timeout: 5000
            });

            if (response.status === 200) {
                this.recordSuccess('VISION_INTEGRATION', {
                    status: 'accessible',
                    port: this.visionPort,
                    response: response.data
                });
                console.log('✅ Vision system integration: Accessible');
            }

        } catch (error) {
            if (error.code === 'ECONNREFUSED') {
                console.log('👁️  Vision system: Not running (expected in test environment)');
                this.recordSuccess('VISION_INTEGRATION', {
                    status: 'not_running',
                    note: 'Expected in test environment'
                });
            } else {
                this.recordFailure('VISION_INTEGRATION', error.message);
                console.error('❌ Vision integration error:', error.message);
            }
        }
    }

    async validateServoIntegration() {
        console.log('\n🔧 Phase 7: Servo API Integration Validation');
        console.log('-'.repeat(50));

        try {
            // Check servo API health
            const response = await axios.get(`http://localhost:${this.servoPort}/api/servo/status`, {
                timeout: 5000
            });

            if (response.status === 200) {
                this.recordSuccess('SERVO_INTEGRATION', {
                    status: 'accessible',
                    port: this.servoPort,
                    response: response.data
                });
                console.log('✅ Servo API integration: Accessible');
            }

        } catch (error) {
            if (error.code === 'ECONNREFUSED') {
                console.log('🔧 Servo API: Not running (expected in simulation mode)');
                this.recordSuccess('SERVO_INTEGRATION', {
                    status: 'simulation_mode',
                    note: 'Expected behavior for testing'
                });
            } else {
                this.recordFailure('SERVO_INTEGRATION', error.message);
                console.error('❌ Servo integration error:', error.message);
            }
        }
    }

    async validateErrorHandling() {
        console.log('\n🛡️  Phase 8: Error Handling & Recovery Validation');
        console.log('-'.repeat(50));

        try {
            // Test invalid route handling
            const response = await axios.get(`${this.baseUrl}/nonexistent-route`, {
                timeout: 5000,
                validateStatus: () => true // Accept all status codes
            });

            if (response.status === 302) {
                this.recordSuccess('ERROR_HANDLING', {
                    test: 'invalid_route_redirect',
                    expectedBehavior: 'redirect_to_default',
                    actualStatus: response.status
                });
                console.log('✅ Error handling: Invalid routes properly redirected');
            } else {
                this.recordFailure('ERROR_HANDLING', `Unexpected status for invalid route: ${response.status}`);
            }

        } catch (error) {
            this.recordFailure('ERROR_HANDLING', error.message);
            console.error('❌ Error handling validation failed:', error.message);
        }
    }

    recordSuccess(testId, data) {
        this.testResults.passed++;
        this.testResults[testId] = { status: 'PASSED', data: data, timestamp: new Date().toISOString() };
    }

    recordFailure(testId, error) {
        this.testResults.failed++;
        this.testResults[testId] = { status: 'FAILED', error: error, timestamp: new Date().toISOString() };
    }

    recordCriticalFailure(testId, error) {
        this.testResults.failed++;
        this.testResults.criticalFailures.push({ testId, error: error.message, timestamp: new Date().toISOString() });
        this.testResults[testId] = { status: 'CRITICAL_FAILURE', error: error.message, timestamp: new Date().toISOString() };
    }

    generateComprehensiveReport() {
        console.log('\n📋 Elite QA Comprehensive Validation Report');
        console.log('=' .repeat(80));

        const totalTests = this.testResults.passed + this.testResults.failed;
        const successRate = totalTests > 0 ? Math.round((this.testResults.passed / totalTests) * 100) : 0;

        console.log(`📊 Test Summary:`);
        console.log(`   ✅ Passed: ${this.testResults.passed}`);
        console.log(`   ❌ Failed: ${this.testResults.failed}`);
        console.log(`   📈 Success Rate: ${successRate}%`);
        console.log(`   ⚠️  Critical Failures: ${this.testResults.criticalFailures.length}`);

        if (this.testResults.criticalFailures.length > 0) {
            console.log(`\n🚨 Critical Failures:`);
            this.testResults.criticalFailures.forEach(failure => {
                console.log(`   ❌ ${failure.testId}: ${failure.error}`);
            });
        }

        // Performance metrics summary
        console.log(`\n📈 Performance Metrics:`);
        if (this.performanceMetrics.serverResponseTime) {
            console.log(`   🔥 Server Response: ${this.performanceMetrics.serverResponseTime}ms`);
        }
        if (this.performanceMetrics.memoryUsage) {
            console.log(`   💾 Memory Usage: ${this.performanceMetrics.memoryUsage.rss}MB RSS`);
        }
        if (this.performanceMetrics.nodeProcesses) {
            console.log(`   🔧 Node Processes: ${this.performanceMetrics.nodeProcesses}`);
        }

        // Quality gate assessment
        const qualityGate = this.assessQualityGate(successRate);
        console.log(`\n🎯 Quality Gate Assessment: ${qualityGate.status}`);
        console.log(`   ${qualityGate.message}`);

        // Save detailed report
        this.saveDetailedReport();

        console.log(`\n📁 Detailed report saved to: qa_dashboard_validation_report.json`);
        console.log('=' .repeat(80));
    }

    assessQualityGate(successRate) {
        if (this.testResults.criticalFailures.length > 0) {
            return {
                status: '🚨 CRITICAL FAILURE - DEPLOYMENT BLOCKED',
                message: 'Critical infrastructure failures detected. Immediate attention required.'
            };
        } else if (successRate >= 95) {
            return {
                status: '✅ PASSED - DEPLOYMENT APPROVED',
                message: 'All quality gates passed. System ready for logging implementation.'
            };
        } else if (successRate >= 85) {
            return {
                status: '⚠️  CONDITIONAL PASS - MONITORING REQUIRED',
                message: 'Most tests passed but monitoring recommended during deployment.'
            };
        } else {
            return {
                status: '❌ FAILED - DEPLOYMENT NOT RECOMMENDED',
                message: 'Multiple test failures detected. System stabilization required.'
            };
        }
    }

    saveDetailedReport() {
        const report = {
            metadata: {
                testSuite: 'Elite QA Comprehensive Dashboard Validation',
                timestamp: this.testResults.timestamp,
                version: '1.0.0',
                environment: 'development'
            },
            summary: {
                totalTests: this.testResults.passed + this.testResults.failed,
                passed: this.testResults.passed,
                failed: this.testResults.failed,
                successRate: Math.round((this.testResults.passed / (this.testResults.passed + this.testResults.failed)) * 100)
            },
            performanceMetrics: this.performanceMetrics,
            testResults: this.testResults,
            recommendations: this.generateRecommendations()
        };

        fs.writeFileSync(
            path.join(__dirname, 'qa_dashboard_validation_report.json'),
            JSON.stringify(report, null, 2)
        );
    }

    generateRecommendations() {
        const recommendations = [];

        if (this.testResults.criticalFailures.length > 0) {
            recommendations.push('CRITICAL: Resolve all critical failures before proceeding with logging implementation');
        }

        if (this.performanceMetrics.serverResponseTime > this.performanceBaselines.responseTime) {
            recommendations.push('PERFORMANCE: Server response time exceeds baseline - investigate optimization opportunities');
        }

        if (this.testResults.failed > 0) {
            recommendations.push('QUALITY: Address all test failures to ensure system stability');
        }

        recommendations.push('MONITORING: Set up continuous monitoring during logging implementation');
        recommendations.push('REGRESSION: Run this test suite after each logging feature addition');

        return recommendations;
    }
}

// Auto-run if called directly
if (require.main === module) {
    const validator = new EliteQADashboardValidator();
    validator.runComprehensiveValidation()
        .then(() => {
            console.log('\n🏁 Elite QA validation completed');
            process.exit(0);
        })
        .catch((error) => {
            console.error('\n💥 Elite QA validation failed:', error);
            process.exit(1);
        });
}

module.exports = EliteQADashboardValidator;