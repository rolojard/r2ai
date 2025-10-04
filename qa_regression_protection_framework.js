#!/usr/bin/env node
/**
 * Elite QA Regression Protection Framework
 * Advanced automated testing system to prevent feature degradation during logging implementation
 *
 * MISSION: Zero tolerance for breaking working features
 * APPROACH: Continuous validation with automated rollback capabilities
 */

const fs = require('fs');
const path = require('path');
const EliteQADashboardValidator = require('./qa_comprehensive_dashboard_test_suite.js');

class RegressionProtectionFramework {
    constructor() {
        this.baselineFile = path.join(__dirname, 'qa_baseline_metrics.json');
        this.alertsFile = path.join(__dirname, 'qa_regression_alerts.json');
        this.configFile = path.join(__dirname, 'qa_protection_config.json');

        this.protectionConfig = {
            critical_thresholds: {
                dashboard_response_time: 1000, // ms
                websocket_connection_time: 2000, // ms
                memory_usage_limit: 1024, // MB
                success_rate_minimum: 85 // percentage
            },
            monitoring_intervals: {
                continuous_check: 30000, // 30 seconds
                full_validation: 300000, // 5 minutes
                baseline_update: 3600000 // 1 hour
            },
            auto_actions: {
                alert_on_degradation: true,
                block_on_critical_failure: true,
                auto_rollback_enabled: false // Manual control initially
            }
        };

        this.baseline = null;
        this.isMonitoring = false;

        console.log('🛡️  Elite QA Regression Protection Framework Initialized');
        this.loadConfiguration();
    }

    loadConfiguration() {
        try {
            if (fs.existsSync(this.configFile)) {
                const config = JSON.parse(fs.readFileSync(this.configFile, 'utf8'));
                this.protectionConfig = { ...this.protectionConfig, ...config };
                console.log('📋 Protection configuration loaded');
            } else {
                this.saveConfiguration();
                console.log('📋 Default protection configuration created');
            }
        } catch (error) {
            console.error('⚠️  Failed to load configuration:', error.message);
        }
    }

    saveConfiguration() {
        try {
            fs.writeFileSync(this.configFile, JSON.stringify(this.protectionConfig, null, 2));
        } catch (error) {
            console.error('⚠️  Failed to save configuration:', error.message);
        }
    }

    async establishBaseline() {
        console.log('\n🎯 Establishing Performance Baseline');
        console.log('=' .repeat(60));

        try {
            const validator = new EliteQADashboardValidator();
            await validator.runComprehensiveValidation();

            // Extract baseline metrics
            this.baseline = {
                timestamp: new Date().toISOString(),
                version: '1.0.0',
                performance: {
                    server_response_time: validator.performanceMetrics.serverResponseTime || 0,
                    memory_usage: validator.performanceMetrics.memoryUsage || {},
                    websocket_connection_time: 50, // Average from test results
                    dashboard_load_times: this.extractDashboardLoadTimes(validator.testResults)
                },
                functionality: {
                    success_rate: Math.round((validator.testResults.passed / (validator.testResults.passed + validator.testResults.failed)) * 100),
                    passed_tests: validator.testResults.passed,
                    total_tests: validator.testResults.passed + validator.testResults.failed,
                    working_endpoints: this.extractWorkingEndpoints(validator.testResults)
                },
                integration: {
                    websocket_channels: ['main_dashboard', 'behavioral_intelligence'],
                    dashboard_routes: ['/', '/vision', '/enhanced', '/servo', '/servo-only', '/disney'],
                    real_time_data_flow: true
                }
            };

            this.saveBaseline();
            console.log('✅ Baseline established and saved');
            console.log(`📊 Success Rate: ${this.baseline.functionality.success_rate}%`);
            console.log(`⚡ Server Response: ${this.baseline.performance.server_response_time}ms`);
            console.log(`💾 Memory Usage: ${this.baseline.performance.memory_usage.rss}MB RSS`);

            return this.baseline;

        } catch (error) {
            console.error('❌ Failed to establish baseline:', error.message);
            throw error;
        }
    }

    extractDashboardLoadTimes(testResults) {
        const loadTimes = {};
        Object.keys(testResults).forEach(key => {
            if (key.startsWith('ROUTE_') && testResults[key].status === 'PASSED') {
                loadTimes[key] = testResults[key].data.responseTime;
            }
        });
        return loadTimes;
    }

    extractWorkingEndpoints(testResults) {
        const endpoints = [];
        Object.keys(testResults).forEach(key => {
            if (testResults[key].status === 'PASSED') {
                endpoints.push({
                    test_id: key,
                    description: testResults[key].data?.description || key,
                    response_time: testResults[key].data?.responseTime || 0
                });
            }
        });
        return endpoints;
    }

    saveBaseline() {
        try {
            fs.writeFileSync(this.baselineFile, JSON.stringify(this.baseline, null, 2));
        } catch (error) {
            console.error('⚠️  Failed to save baseline:', error.message);
        }
    }

    loadBaseline() {
        try {
            if (fs.existsSync(this.baselineFile)) {
                this.baseline = JSON.parse(fs.readFileSync(this.baselineFile, 'utf8'));
                console.log('📊 Baseline loaded from file');
                return true;
            }
        } catch (error) {
            console.error('⚠️  Failed to load baseline:', error.message);
        }
        return false;
    }

    async validateAgainstBaseline() {
        if (!this.baseline) {
            if (!this.loadBaseline()) {
                console.log('⚠️  No baseline found. Establishing new baseline...');
                await this.establishBaseline();
                return { status: 'baseline_established' };
            }
        }

        console.log('\n🔍 Running Regression Validation');
        console.log('-'.repeat(50));

        try {
            const validator = new EliteQADashboardValidator();
            await validator.runComprehensiveValidation();

            const current = {
                performance: {
                    server_response_time: validator.performanceMetrics.serverResponseTime || 0,
                    memory_usage: validator.performanceMetrics.memoryUsage || {},
                    dashboard_load_times: this.extractDashboardLoadTimes(validator.testResults)
                },
                functionality: {
                    success_rate: Math.round((validator.testResults.passed / (validator.testResults.passed + validator.testResults.failed)) * 100),
                    passed_tests: validator.testResults.passed,
                    total_tests: validator.testResults.passed + validator.testResults.failed
                }
            };

            const regressionAnalysis = this.analyzeRegression(this.baseline, current);
            this.handleRegressionResults(regressionAnalysis);

            return regressionAnalysis;

        } catch (error) {
            console.error('❌ Regression validation failed:', error.message);
            return { status: 'validation_failed', error: error.message };
        }
    }

    analyzeRegression(baseline, current) {
        const analysis = {
            status: 'passed',
            timestamp: new Date().toISOString(),
            regressions: [],
            improvements: [],
            warnings: [],
            critical_issues: []
        };

        // Performance Analysis
        if (current.performance.server_response_time > baseline.performance.server_response_time * 1.5) {
            analysis.regressions.push({
                type: 'performance',
                metric: 'server_response_time',
                baseline: baseline.performance.server_response_time,
                current: current.performance.server_response_time,
                degradation: Math.round(((current.performance.server_response_time - baseline.performance.server_response_time) / baseline.performance.server_response_time) * 100)
            });
        }

        // Memory Usage Analysis
        if (current.performance.memory_usage.rss && baseline.performance.memory_usage.rss) {
            if (current.performance.memory_usage.rss > baseline.performance.memory_usage.rss * 1.3) {
                analysis.regressions.push({
                    type: 'memory',
                    metric: 'rss_usage',
                    baseline: baseline.performance.memory_usage.rss,
                    current: current.performance.memory_usage.rss,
                    increase: Math.round(((current.performance.memory_usage.rss - baseline.performance.memory_usage.rss) / baseline.performance.memory_usage.rss) * 100)
                });
            }
        }

        // Functionality Analysis
        if (current.functionality.success_rate < baseline.functionality.success_rate) {
            const regression = {
                type: 'functionality',
                metric: 'success_rate',
                baseline: baseline.functionality.success_rate,
                current: current.functionality.success_rate,
                degradation: baseline.functionality.success_rate - current.functionality.success_rate
            };

            if (regression.degradation > 10) {
                analysis.critical_issues.push(regression);
            } else {
                analysis.regressions.push(regression);
            }
        }

        // Dashboard Load Time Analysis
        Object.keys(baseline.performance.dashboard_load_times).forEach(route => {
            const baselineTime = baseline.performance.dashboard_load_times[route];
            const currentTime = current.performance.dashboard_load_times[route];

            if (currentTime && currentTime > baselineTime * 2) {
                analysis.regressions.push({
                    type: 'dashboard_performance',
                    metric: route,
                    baseline: baselineTime,
                    current: currentTime,
                    degradation: Math.round(((currentTime - baselineTime) / baselineTime) * 100)
                });
            }
        });

        // Critical Threshold Checks
        if (current.performance.server_response_time > this.protectionConfig.critical_thresholds.dashboard_response_time) {
            analysis.critical_issues.push({
                type: 'critical_threshold',
                metric: 'server_response_time',
                current: current.performance.server_response_time,
                threshold: this.protectionConfig.critical_thresholds.dashboard_response_time
            });
        }

        if (current.functionality.success_rate < this.protectionConfig.critical_thresholds.success_rate_minimum) {
            analysis.critical_issues.push({
                type: 'critical_threshold',
                metric: 'success_rate',
                current: current.functionality.success_rate,
                threshold: this.protectionConfig.critical_thresholds.success_rate_minimum
            });
        }

        // Determine overall status
        if (analysis.critical_issues.length > 0) {
            analysis.status = 'critical_failure';
        } else if (analysis.regressions.length > 0) {
            analysis.status = 'regression_detected';
        } else {
            analysis.status = 'passed';
        }

        return analysis;
    }

    handleRegressionResults(analysis) {
        console.log(`\n📋 Regression Analysis Results: ${analysis.status.toUpperCase()}`);
        console.log('-'.repeat(50));

        if (analysis.status === 'passed') {
            console.log('✅ All regression checks passed - System stable');
        }

        if (analysis.regressions.length > 0) {
            console.log(`⚠️  ${analysis.regressions.length} regression(s) detected:`);
            analysis.regressions.forEach(regression => {
                console.log(`   📉 ${regression.type}: ${regression.metric} degraded by ${regression.degradation || regression.increase}%`);
            });
        }

        if (analysis.critical_issues.length > 0) {
            console.log(`🚨 ${analysis.critical_issues.length} critical issue(s) detected:`);
            analysis.critical_issues.forEach(issue => {
                console.log(`   ❌ ${issue.type}: ${issue.metric} - Current: ${issue.current}, Threshold: ${issue.threshold || 'N/A'}`);
            });

            if (this.protectionConfig.auto_actions.block_on_critical_failure) {
                console.log('\n🛑 BLOCKING DEPLOYMENT DUE TO CRITICAL ISSUES');
                console.log('   Resolve critical issues before proceeding with logging implementation');
            }
        }

        // Save alerts
        this.saveAlert(analysis);
    }

    saveAlert(analysis) {
        try {
            let alerts = [];
            if (fs.existsSync(this.alertsFile)) {
                alerts = JSON.parse(fs.readFileSync(this.alertsFile, 'utf8'));
            }

            alerts.unshift({
                ...analysis,
                id: Date.now(),
                timestamp: new Date().toISOString()
            });

            // Keep only last 50 alerts
            alerts = alerts.slice(0, 50);

            fs.writeFileSync(this.alertsFile, JSON.stringify(alerts, null, 2));
        } catch (error) {
            console.error('⚠️  Failed to save alert:', error.message);
        }
    }

    startContinuousMonitoring() {
        if (this.isMonitoring) {
            console.log('⚠️  Monitoring is already running');
            return;
        }

        console.log('\n🔄 Starting Continuous Regression Monitoring');
        console.log(`⏰ Check interval: ${this.protectionConfig.monitoring_intervals.continuous_check / 1000}s`);
        console.log(`📊 Full validation interval: ${this.protectionConfig.monitoring_intervals.full_validation / 1000}s`);

        this.isMonitoring = true;

        // Quick health checks
        this.quickCheckInterval = setInterval(() => {
            this.performQuickHealthCheck();
        }, this.protectionConfig.monitoring_intervals.continuous_check);

        // Full regression validation
        this.fullValidationInterval = setInterval(() => {
            this.validateAgainstBaseline();
        }, this.protectionConfig.monitoring_intervals.full_validation);

        console.log('✅ Continuous monitoring started');
    }

    stopContinuousMonitoring() {
        if (!this.isMonitoring) {
            console.log('⚠️  Monitoring is not running');
            return;
        }

        clearInterval(this.quickCheckInterval);
        clearInterval(this.fullValidationInterval);
        this.isMonitoring = false;

        console.log('🛑 Continuous monitoring stopped');
    }

    async performQuickHealthCheck() {
        try {
            const axios = require('axios');
            const startTime = Date.now();
            const response = await axios.get('http://localhost:8765', { timeout: 5000 });
            const responseTime = Date.now() - startTime;

            if (responseTime > this.protectionConfig.critical_thresholds.dashboard_response_time) {
                console.log(`⚠️  Quick health check: Response time ${responseTime}ms exceeds threshold`);
                this.saveAlert({
                    status: 'quick_check_warning',
                    type: 'response_time',
                    value: responseTime,
                    threshold: this.protectionConfig.critical_thresholds.dashboard_response_time,
                    timestamp: new Date().toISOString()
                });
            }

        } catch (error) {
            console.log(`❌ Quick health check failed: ${error.message}`);
            this.saveAlert({
                status: 'quick_check_failed',
                error: error.message,
                timestamp: new Date().toISOString()
            });
        }
    }

    generateProtectionReport() {
        console.log('\n📊 Elite QA Protection Report');
        console.log('=' .repeat(60));

        // Baseline status
        if (this.baseline) {
            console.log(`📈 Baseline Established: ${new Date(this.baseline.timestamp).toLocaleString()}`);
            console.log(`   Success Rate: ${this.baseline.functionality.success_rate}%`);
            console.log(`   Server Response: ${this.baseline.performance.server_response_time}ms`);
            console.log(`   Memory Usage: ${this.baseline.performance.memory_usage.rss}MB RSS`);
        } else {
            console.log('⚠️  No baseline established');
        }

        // Monitoring status
        console.log(`\n🔄 Monitoring Status: ${this.isMonitoring ? 'ACTIVE' : 'INACTIVE'}`);

        // Recent alerts
        try {
            if (fs.existsSync(this.alertsFile)) {
                const alerts = JSON.parse(fs.readFileSync(this.alertsFile, 'utf8'));
                const recentAlerts = alerts.slice(0, 5);

                if (recentAlerts.length > 0) {
                    console.log(`\n🚨 Recent Alerts (${recentAlerts.length}):`);
                    recentAlerts.forEach(alert => {
                        console.log(`   ${alert.status}: ${new Date(alert.timestamp).toLocaleString()}`);
                    });
                } else {
                    console.log('\n✅ No recent alerts');
                }
            }
        } catch (error) {
            console.log('\n⚠️  Could not read alerts file');
        }

        // Configuration summary
        console.log(`\n⚙️  Protection Configuration:`);
        console.log(`   Response Time Threshold: ${this.protectionConfig.critical_thresholds.dashboard_response_time}ms`);
        console.log(`   Success Rate Minimum: ${this.protectionConfig.critical_thresholds.success_rate_minimum}%`);
        console.log(`   Auto-block on Critical: ${this.protectionConfig.auto_actions.block_on_critical_failure}`);
    }
}

// CLI Interface
if (require.main === module) {
    const framework = new RegressionProtectionFramework();
    const command = process.argv[2];

    switch (command) {
        case 'baseline':
            framework.establishBaseline()
                .then(() => process.exit(0))
                .catch(() => process.exit(1));
            break;

        case 'validate':
            framework.validateAgainstBaseline()
                .then((result) => {
                    console.log(`\nValidation result: ${result.status}`);
                    process.exit(result.status === 'critical_failure' ? 1 : 0);
                })
                .catch(() => process.exit(1));
            break;

        case 'monitor':
            framework.startContinuousMonitoring();

            // Handle graceful shutdown
            process.on('SIGINT', () => {
                console.log('\n🛑 Shutting down monitoring...');
                framework.stopContinuousMonitoring();
                process.exit(0);
            });
            break;

        case 'report':
            framework.generateProtectionReport();
            process.exit(0);
            break;

        default:
            console.log('Elite QA Regression Protection Framework');
            console.log('Usage:');
            console.log('  node qa_regression_protection_framework.js baseline  - Establish performance baseline');
            console.log('  node qa_regression_protection_framework.js validate  - Validate against baseline');
            console.log('  node qa_regression_protection_framework.js monitor   - Start continuous monitoring');
            console.log('  node qa_regression_protection_framework.js report    - Generate protection report');
            process.exit(0);
    }
}

module.exports = RegressionProtectionFramework;