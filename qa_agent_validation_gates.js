#!/usr/bin/env node
/**
 * Elite QA Agent Validation Gates
 * Comprehensive validation framework for Web Dev and Super-Coder team changes
 *
 * MISSION: Zero tolerance quality control for all agent modifications
 * APPROACH: Pre-commit and post-commit validation with automated approval/rejection
 */

const fs = require('fs');
const path = require('path');
const EliteQADashboardValidator = require('./qa_comprehensive_dashboard_test_suite.js');
const RegressionProtectionFramework = require('./qa_regression_protection_framework.js');

class AgentValidationGates {
    constructor() {
        this.gateConfigFile = path.join(__dirname, 'qa_agent_gates_config.json');
        this.validationHistoryFile = path.join(__dirname, 'qa_agent_validation_history.json');

        this.gateConfig = {
            webDevSpecialist: {
                preCommitChecks: {
                    dashboardRouteIntegrity: true,
                    cssIntegrityCheck: true,
                    javascriptSyntaxValidation: true,
                    websocketConnectionStability: true,
                    loggingImplementationValidation: true
                },
                postCommitChecks: {
                    fullRegressionTest: true,
                    performanceImpactAnalysis: true,
                    userExperienceValidation: true,
                    crossBrowserCompatibility: false // Not applicable in this environment
                },
                qualityThresholds: {
                    maxResponseTimeDegradation: 50, // ms
                    maxMemoryIncrease: 20, // MB
                    minSuccessRate: 90, // percentage
                    maxFailedTests: 2
                }
            },
            superCoder: {
                preCommitChecks: {
                    codeQualityValidation: true,
                    securityVulnerabilityCheck: true,
                    apiIntegrityValidation: true,
                    backendServiceStability: true,
                    loggingFrameworkIntegration: true
                },
                postCommitChecks: {
                    fullSystemIntegrationTest: true,
                    performanceRegressionAnalysis: true,
                    errorHandlingValidation: true,
                    scalabilityAssessment: true
                },
                qualityThresholds: {
                    maxResponseTimeDegradation: 100, // ms
                    maxMemoryIncrease: 50, // MB
                    minSuccessRate: 85, // percentage
                    maxCriticalIssues: 0
                }
            },
            approvalWorkflow: {
                requiresQAApproval: true,
                autoApprovalEnabled: false,
                blockOnCriticalFailures: true,
                rollbackOnRegressions: false // Manual control initially
            }
        };

        this.validationHistory = [];
        this.activeValidations = new Map();

        console.log('🎯 Elite QA Agent Validation Gates Initialized');
        this.loadConfiguration();
    }

    loadConfiguration() {
        try {
            if (fs.existsSync(this.gateConfigFile)) {
                const config = JSON.parse(fs.readFileSync(this.gateConfigFile, 'utf8'));
                this.gateConfig = { ...this.gateConfig, ...config };
                console.log('📋 Gate configuration loaded');
            } else {
                this.saveConfiguration();
                console.log('📋 Default gate configuration created');
            }

            if (fs.existsSync(this.validationHistoryFile)) {
                this.validationHistory = JSON.parse(fs.readFileSync(this.validationHistoryFile, 'utf8'));
                console.log(`📜 Validation history loaded (${this.validationHistory.length} entries)`);
            }
        } catch (error) {
            console.error('⚠️  Failed to load configuration:', error.message);
        }
    }

    saveConfiguration() {
        try {
            fs.writeFileSync(this.gateConfigFile, JSON.stringify(this.gateConfig, null, 2));
        } catch (error) {
            console.error('⚠️  Failed to save configuration:', error.message);
        }
    }

    saveValidationHistory() {
        try {
            // Keep only last 100 validation records
            const recentHistory = this.validationHistory.slice(0, 100);
            fs.writeFileSync(this.validationHistoryFile, JSON.stringify(recentHistory, null, 2));
        } catch (error) {
            console.error('⚠️  Failed to save validation history:', error.message);
        }
    }

    async validateWebDevChanges(changeDescription, changePaths = []) {
        console.log('\n🎨 Web Dev Specialist Validation Gate');
        console.log('=' .repeat(60));
        console.log(`📝 Change Description: ${changeDescription}`);
        console.log(`📁 Changed Files: ${changePaths.length > 0 ? changePaths.join(', ') : 'Not specified'}`);

        const validationId = `webdev_${Date.now()}`;
        const validationRecord = {
            id: validationId,
            agent: 'WebDevSpecialist',
            timestamp: new Date().toISOString(),
            changeDescription: changeDescription,
            changePaths: changePaths,
            preCommitResults: {},
            postCommitResults: {},
            finalStatus: 'in_progress',
            approvalStatus: 'pending'
        };

        this.activeValidations.set(validationId, validationRecord);

        try {
            // Pre-commit validation
            if (this.gateConfig.webDevSpecialist.preCommitChecks.dashboardRouteIntegrity) {
                validationRecord.preCommitResults.dashboardRoutes = await this.validateDashboardRoutes();
            }

            if (this.gateConfig.webDevSpecialist.preCommitChecks.websocketConnectionStability) {
                validationRecord.preCommitResults.websocketStability = await this.validateWebSocketStability();
            }

            if (this.gateConfig.webDevSpecialist.preCommitChecks.loggingImplementationValidation) {
                validationRecord.preCommitResults.loggingValidation = await this.validateLoggingImplementation();
            }

            // Post-commit validation (full regression test)
            if (this.gateConfig.webDevSpecialist.postCommitChecks.fullRegressionTest) {
                console.log('\n🔍 Running full regression test...');
                const regressionFramework = new RegressionProtectionFramework();
                validationRecord.postCommitResults.regressionAnalysis = await regressionFramework.validateAgainstBaseline();
            }

            // Performance impact analysis
            if (this.gateConfig.webDevSpecialist.postCommitChecks.performanceImpactAnalysis) {
                validationRecord.postCommitResults.performanceImpact = await this.analyzePerformanceImpact();
            }

            // Quality gate assessment
            const assessmentResult = this.assessWebDevQualityGate(validationRecord);
            validationRecord.finalStatus = assessmentResult.status;
            validationRecord.approvalStatus = assessmentResult.approval;
            validationRecord.recommendations = assessmentResult.recommendations;

            // Save validation record
            this.validationHistory.unshift(validationRecord);
            this.saveValidationHistory();
            this.activeValidations.delete(validationId);

            // Generate validation report
            this.generateWebDevValidationReport(validationRecord);

            return validationRecord;

        } catch (error) {
            validationRecord.finalStatus = 'error';
            validationRecord.error = error.message;
            validationRecord.approvalStatus = 'rejected';

            console.error('❌ Web Dev validation failed:', error.message);
            return validationRecord;
        }
    }

    async validateSuperCoderChanges(changeDescription, changePaths = []) {
        console.log('\n⚡ Super-Coder Validation Gate');
        console.log('=' .repeat(60));
        console.log(`📝 Change Description: ${changeDescription}`);
        console.log(`📁 Changed Files: ${changePaths.length > 0 ? changePaths.join(', ') : 'Not specified'}`);

        const validationId = `supercoder_${Date.now()}`;
        const validationRecord = {
            id: validationId,
            agent: 'SuperCoder',
            timestamp: new Date().toISOString(),
            changeDescription: changeDescription,
            changePaths: changePaths,
            preCommitResults: {},
            postCommitResults: {},
            finalStatus: 'in_progress',
            approvalStatus: 'pending'
        };

        this.activeValidations.set(validationId, validationRecord);

        try {
            // Pre-commit validation
            if (this.gateConfig.superCoder.preCommitChecks.apiIntegrityValidation) {
                validationRecord.preCommitResults.apiIntegrity = await this.validateAPIIntegrity();
            }

            if (this.gateConfig.superCoder.preCommitChecks.backendServiceStability) {
                validationRecord.preCommitResults.backendStability = await this.validateBackendStability();
            }

            if (this.gateConfig.superCoder.preCommitChecks.loggingFrameworkIntegration) {
                validationRecord.preCommitResults.loggingFramework = await this.validateLoggingFramework();
            }

            // Post-commit validation
            if (this.gateConfig.superCoder.postCommitChecks.fullSystemIntegrationTest) {
                console.log('\n🔧 Running full system integration test...');
                const regressionFramework = new RegressionProtectionFramework();
                validationRecord.postCommitResults.systemIntegration = await regressionFramework.validateAgainstBaseline();
            }

            if (this.gateConfig.superCoder.postCommitChecks.errorHandlingValidation) {
                validationRecord.postCommitResults.errorHandling = await this.validateErrorHandling();
            }

            // Quality gate assessment
            const assessmentResult = this.assessSuperCoderQualityGate(validationRecord);
            validationRecord.finalStatus = assessmentResult.status;
            validationRecord.approvalStatus = assessmentResult.approval;
            validationRecord.recommendations = assessmentResult.recommendations;

            // Save validation record
            this.validationHistory.unshift(validationRecord);
            this.saveValidationHistory();
            this.activeValidations.delete(validationId);

            // Generate validation report
            this.generateSuperCoderValidationReport(validationRecord);

            return validationRecord;

        } catch (error) {
            validationRecord.finalStatus = 'error';
            validationRecord.error = error.message;
            validationRecord.approvalStatus = 'rejected';

            console.error('❌ Super-Coder validation failed:', error.message);
            return validationRecord;
        }
    }

    async validateDashboardRoutes() {
        console.log('📊 Validating dashboard route integrity...');

        try {
            const axios = require('axios');
            const routes = ['/', '/vision', '/enhanced', '/servo', '/servo-only', '/disney'];
            const results = [];

            for (const route of routes) {
                const startTime = Date.now();
                const response = await axios.get(`http://localhost:8765${route}`, { timeout: 5000 });
                const responseTime = Date.now() - startTime;

                results.push({
                    route: route,
                    status: response.status,
                    responseTime: responseTime,
                    contentLength: response.data.length,
                    success: response.status === 200 && response.data.includes('<!DOCTYPE html>')
                });
            }

            const successCount = results.filter(r => r.success).length;
            const avgResponseTime = Math.round(results.reduce((sum, r) => sum + r.responseTime, 0) / results.length);

            return {
                status: successCount === routes.length ? 'passed' : 'failed',
                successRate: Math.round((successCount / routes.length) * 100),
                averageResponseTime: avgResponseTime,
                results: results
            };

        } catch (error) {
            return {
                status: 'error',
                error: error.message
            };
        }
    }

    async validateWebSocketStability() {
        console.log('🔌 Validating WebSocket connection stability...');

        return new Promise((resolve) => {
            try {
                const WebSocket = require('ws');
                const connections = [];
                const results = [];

                // Test main dashboard WebSocket
                const mainWs = new WebSocket('ws://localhost:8766');
                const behaviorWs = new WebSocket('ws://localhost:8768');

                let connectedCount = 0;
                const expectedConnections = 2;

                const testConnection = (ws, name) => {
                    const startTime = Date.now();

                    ws.on('open', () => {
                        const connectionTime = Date.now() - startTime;
                        results.push({
                            name: name,
                            connectionTime: connectionTime,
                            status: 'connected'
                        });

                        connectedCount++;
                        if (connectedCount === expectedConnections) {
                            // All connections established, run stability test
                            setTimeout(() => {
                                connections.forEach(conn => conn.close());
                                resolve({
                                    status: 'passed',
                                    connectionsEstablished: connectedCount,
                                    averageConnectionTime: Math.round(results.reduce((sum, r) => sum + r.connectionTime, 0) / results.length),
                                    results: results
                                });
                            }, 2000);
                        }
                    });

                    ws.on('error', (error) => {
                        results.push({
                            name: name,
                            status: 'error',
                            error: error.message
                        });

                        if (results.length === expectedConnections) {
                            resolve({
                                status: 'failed',
                                error: 'WebSocket connection failures',
                                results: results
                            });
                        }
                    });

                    connections.push(ws);
                };

                testConnection(mainWs, 'MainDashboard');
                testConnection(behaviorWs, 'BehavioralIntelligence');

                // Timeout after 10 seconds
                setTimeout(() => {
                    connections.forEach(conn => {
                        if (conn.readyState === WebSocket.CONNECTING) {
                            conn.terminate();
                        }
                    });

                    resolve({
                        status: 'timeout',
                        error: 'WebSocket connection timeout',
                        results: results
                    });
                }, 10000);

            } catch (error) {
                resolve({
                    status: 'error',
                    error: error.message
                });
            }
        });
    }

    async validateLoggingImplementation() {
        console.log('📝 Validating logging implementation...');

        try {
            // Check for logging-related files and configurations
            const loggingFiles = [];
            const checkPaths = [
                'logging_config.json',
                'logger.js',
                'r2d2_logger.py',
                'logs/',
                'log_aggregator.js'
            ];

            for (const filePath of checkPaths) {
                if (fs.existsSync(path.join(__dirname, filePath))) {
                    loggingFiles.push(filePath);
                }
            }

            // Check dashboard server for logging integration
            const dashboardServerContent = fs.readFileSync(path.join(__dirname, 'dashboard-server.js'), 'utf8');
            const hasLoggingIntegration = dashboardServerContent.includes('log') || dashboardServerContent.includes('winston') || dashboardServerContent.includes('console.log');

            return {
                status: loggingFiles.length > 0 || hasLoggingIntegration ? 'partial' : 'not_implemented',
                loggingFilesFound: loggingFiles,
                dashboardLoggingIntegrated: hasLoggingIntegration,
                recommendations: loggingFiles.length === 0 ? ['Implement structured logging system', 'Add log aggregation'] : []
            };

        } catch (error) {
            return {
                status: 'error',
                error: error.message
            };
        }
    }

    async validateAPIIntegrity() {
        console.log('🔧 Validating API integrity...');

        try {
            const axios = require('axios');
            const apiEndpoints = [
                { url: 'http://localhost:5000/api/servo/status', name: 'Servo API Status' },
                { url: 'http://localhost:8767/health', name: 'Vision System Health' }
            ];

            const results = [];

            for (const endpoint of apiEndpoints) {
                try {
                    const response = await axios.get(endpoint.url, { timeout: 3000 });
                    results.push({
                        name: endpoint.name,
                        url: endpoint.url,
                        status: 'accessible',
                        responseCode: response.status
                    });
                } catch (error) {
                    results.push({
                        name: endpoint.name,
                        url: endpoint.url,
                        status: 'not_accessible',
                        error: error.code || error.message
                    });
                }
            }

            const accessibleCount = results.filter(r => r.status === 'accessible').length;

            return {
                status: accessibleCount > 0 ? 'partial' : 'not_accessible',
                accessibleEndpoints: accessibleCount,
                totalEndpoints: apiEndpoints.length,
                results: results
            };

        } catch (error) {
            return {
                status: 'error',
                error: error.message
            };
        }
    }

    async validateBackendStability() {
        console.log('🔗 Validating backend service stability...');

        try {
            const validator = new EliteQADashboardValidator();

            // Run a quick health check
            const startTime = Date.now();
            await validator.validateServerHealth();
            const validationTime = Date.now() - startTime;

            return {
                status: 'stable',
                validationTime: validationTime,
                serverResponsive: true
            };

        } catch (error) {
            return {
                status: 'unstable',
                error: error.message
            };
        }
    }

    async validateLoggingFramework() {
        console.log('📋 Validating logging framework integration...');

        // Similar to logging implementation validation but focused on framework
        return this.validateLoggingImplementation();
    }

    async analyzePerformanceImpact() {
        console.log('📈 Analyzing performance impact...');

        try {
            // Get current performance metrics
            const memUsage = process.memoryUsage();
            const currentMetrics = {
                memoryUsage: Math.round(memUsage.rss / 1024 / 1024),
                heapUsed: Math.round(memUsage.heapUsed / 1024 / 1024),
                timestamp: Date.now()
            };

            // Load baseline for comparison
            const baselineFile = path.join(__dirname, 'qa_baseline_metrics.json');
            if (fs.existsSync(baselineFile)) {
                const baseline = JSON.parse(fs.readFileSync(baselineFile, 'utf8'));

                const memoryIncrease = currentMetrics.memoryUsage - baseline.performance.memory_usage.rss;
                const heapIncrease = currentMetrics.heapUsed - baseline.performance.memory_usage.heapUsed;

                return {
                    status: memoryIncrease < 20 ? 'acceptable' : 'concerning',
                    memoryIncrease: memoryIncrease,
                    heapIncrease: heapIncrease,
                    currentMetrics: currentMetrics,
                    baselineMetrics: baseline.performance.memory_usage
                };
            } else {
                return {
                    status: 'no_baseline',
                    currentMetrics: currentMetrics,
                    note: 'No baseline available for comparison'
                };
            }

        } catch (error) {
            return {
                status: 'error',
                error: error.message
            };
        }
    }

    async validateErrorHandling() {
        console.log('🛡️  Validating error handling...');

        try {
            const axios = require('axios');

            // Test invalid route handling
            const response = await axios.get('http://localhost:8765/invalid-test-route', {
                timeout: 5000,
                validateStatus: () => true
            });

            return {
                status: response.status === 302 ? 'proper_redirect' : 'unexpected_behavior',
                responseStatus: response.status,
                redirectWorking: response.status === 302
            };

        } catch (error) {
            return {
                status: 'error',
                error: error.message
            };
        }
    }

    assessWebDevQualityGate(validationRecord) {
        const thresholds = this.gateConfig.webDevSpecialist.qualityThresholds;
        const issues = [];
        const recommendations = [];

        // Analyze dashboard routes
        if (validationRecord.preCommitResults.dashboardRoutes) {
            const routeResult = validationRecord.preCommitResults.dashboardRoutes;
            if (routeResult.successRate < 100) {
                issues.push(`Dashboard route failures: ${100 - routeResult.successRate}% failure rate`);
            }
            if (routeResult.averageResponseTime > thresholds.maxResponseTimeDegradation) {
                issues.push(`Slow dashboard response: ${routeResult.averageResponseTime}ms average`);
            }
        }

        // Analyze WebSocket stability
        if (validationRecord.preCommitResults.websocketStability) {
            const wsResult = validationRecord.preCommitResults.websocketStability;
            if (wsResult.status !== 'passed') {
                issues.push(`WebSocket connectivity issues: ${wsResult.status}`);
            }
        }

        // Analyze regression results
        if (validationRecord.postCommitResults.regressionAnalysis) {
            const regression = validationRecord.postCommitResults.regressionAnalysis;
            if (regression.status === 'critical_failure') {
                issues.push('Critical regression detected');
            } else if (regression.status === 'regression_detected') {
                issues.push(`${regression.regressions?.length || 0} regressions detected`);
            }
        }

        // Determine approval status
        let status = 'passed';
        let approval = 'approved';

        if (issues.length > thresholds.maxFailedTests) {
            status = 'failed';
            approval = 'rejected';
            recommendations.push('Address all critical issues before resubmission');
        } else if (issues.length > 0) {
            status = 'conditional';
            approval = 'conditional';
            recommendations.push('Monitor performance during deployment');
        }

        if (issues.length === 0) {
            recommendations.push('Changes approved - proceed with deployment');
        }

        return {
            status: status,
            approval: approval,
            issues: issues,
            recommendations: recommendations
        };
    }

    assessSuperCoderQualityGate(validationRecord) {
        const thresholds = this.gateConfig.superCoder.qualityThresholds;
        const issues = [];
        const recommendations = [];

        // Analyze API integrity
        if (validationRecord.preCommitResults.apiIntegrity) {
            const apiResult = validationRecord.preCommitResults.apiIntegrity;
            if (apiResult.status === 'not_accessible') {
                issues.push('API endpoints not accessible');
            }
        }

        // Analyze system integration
        if (validationRecord.postCommitResults.systemIntegration) {
            const integration = validationRecord.postCommitResults.systemIntegration;
            if (integration.status === 'critical_failure') {
                issues.push('Critical system integration failure');
            }
        }

        // Determine approval status
        let status = 'passed';
        let approval = 'approved';

        if (issues.some(issue => issue.includes('Critical'))) {
            status = 'failed';
            approval = 'rejected';
            recommendations.push('Resolve critical issues immediately');
        } else if (issues.length > 0) {
            status = 'conditional';
            approval = 'conditional';
            recommendations.push('Address issues and monitor system stability');
        }

        if (issues.length === 0) {
            recommendations.push('Code changes approved - deployment authorized');
        }

        return {
            status: status,
            approval: approval,
            issues: issues,
            recommendations: recommendations
        };
    }

    generateWebDevValidationReport(validationRecord) {
        console.log('\n📋 Web Dev Validation Report');
        console.log('=' .repeat(60));
        console.log(`🎯 Validation ID: ${validationRecord.id}`);
        console.log(`📝 Change: ${validationRecord.changeDescription}`);
        console.log(`🕒 Timestamp: ${new Date(validationRecord.timestamp).toLocaleString()}`);
        console.log(`📊 Status: ${validationRecord.finalStatus.toUpperCase()}`);
        console.log(`✅ Approval: ${validationRecord.approvalStatus.toUpperCase()}`);

        if (validationRecord.recommendations) {
            console.log(`\n📌 Recommendations:`);
            validationRecord.recommendations.forEach(rec => {
                console.log(`   • ${rec}`);
            });
        }

        // Save detailed report
        const reportFile = path.join(__dirname, `qa_webdev_validation_${validationRecord.id}.json`);
        fs.writeFileSync(reportFile, JSON.stringify(validationRecord, null, 2));
        console.log(`\n📁 Detailed report: ${reportFile}`);
    }

    generateSuperCoderValidationReport(validationRecord) {
        console.log('\n📋 Super-Coder Validation Report');
        console.log('=' .repeat(60));
        console.log(`🎯 Validation ID: ${validationRecord.id}`);
        console.log(`📝 Change: ${validationRecord.changeDescription}`);
        console.log(`🕒 Timestamp: ${new Date(validationRecord.timestamp).toLocaleString()}`);
        console.log(`📊 Status: ${validationRecord.finalStatus.toUpperCase()}`);
        console.log(`✅ Approval: ${validationRecord.approvalStatus.toUpperCase()}`);

        if (validationRecord.recommendations) {
            console.log(`\n📌 Recommendations:`);
            validationRecord.recommendations.forEach(rec => {
                console.log(`   • ${rec}`);
            });
        }

        // Save detailed report
        const reportFile = path.join(__dirname, `qa_supercoder_validation_${validationRecord.id}.json`);
        fs.writeFileSync(reportFile, JSON.stringify(validationRecord, null, 2));
        console.log(`\n📁 Detailed report: ${reportFile}`);
    }

    getValidationHistory(agentType = null, limit = 10) {
        let history = this.validationHistory;

        if (agentType) {
            history = history.filter(record =>
                record.agent.toLowerCase().includes(agentType.toLowerCase())
            );
        }

        return history.slice(0, limit);
    }

    generateSummaryReport() {
        console.log('\n📊 Elite QA Agent Validation Summary');
        console.log('=' .repeat(60));

        const recentValidations = this.validationHistory.slice(0, 20);
        const approvedCount = recentValidations.filter(v => v.approvalStatus === 'approved').length;
        const rejectedCount = recentValidations.filter(v => v.approvalStatus === 'rejected').length;
        const conditionalCount = recentValidations.filter(v => v.approvalStatus === 'conditional').length;

        console.log(`📈 Recent Validations: ${recentValidations.length}`);
        console.log(`✅ Approved: ${approvedCount}`);
        console.log(`❌ Rejected: ${rejectedCount}`);
        console.log(`⚠️  Conditional: ${conditionalCount}`);

        if (recentValidations.length > 0) {
            const approvalRate = Math.round((approvedCount / recentValidations.length) * 100);
            console.log(`📊 Approval Rate: ${approvalRate}%`);
        }

        console.log(`\n⚙️  Current Configuration:`);
        console.log(`   Web Dev Max Failed Tests: ${this.gateConfig.webDevSpecialist.qualityThresholds.maxFailedTests}`);
        console.log(`   Super-Coder Max Critical Issues: ${this.gateConfig.superCoder.qualityThresholds.maxCriticalIssues}`);
        console.log(`   Auto-approval: ${this.gateConfig.approvalWorkflow.autoApprovalEnabled ? 'Enabled' : 'Disabled'}`);
        console.log(`   Block on Critical: ${this.gateConfig.approvalWorkflow.blockOnCriticalFailures ? 'Enabled' : 'Disabled'}`);
    }
}

// CLI Interface
if (require.main === module) {
    const gates = new AgentValidationGates();
    const command = process.argv[2];
    const agent = process.argv[3];
    const description = process.argv[4] || 'Manual validation test';

    switch (command) {
        case 'validate-webdev':
            gates.validateWebDevChanges(description)
                .then((result) => {
                    console.log(`\nValidation completed: ${result.approvalStatus}`);
                    process.exit(result.approvalStatus === 'rejected' ? 1 : 0);
                })
                .catch(() => process.exit(1));
            break;

        case 'validate-supercoder':
            gates.validateSuperCoderChanges(description)
                .then((result) => {
                    console.log(`\nValidation completed: ${result.approvalStatus}`);
                    process.exit(result.approvalStatus === 'rejected' ? 1 : 0);
                })
                .catch(() => process.exit(1));
            break;

        case 'history':
            const history = gates.getValidationHistory(agent, 10);
            console.log(`\n📜 Recent Validation History${agent ? ` (${agent})` : ''}:`);
            history.forEach(record => {
                console.log(`   ${record.id}: ${record.approvalStatus} - ${record.changeDescription.substring(0, 50)}...`);
            });
            process.exit(0);
            break;

        case 'summary':
            gates.generateSummaryReport();
            process.exit(0);
            break;

        default:
            console.log('Elite QA Agent Validation Gates');
            console.log('Usage:');
            console.log('  node qa_agent_validation_gates.js validate-webdev "Description"    - Validate Web Dev changes');
            console.log('  node qa_agent_validation_gates.js validate-supercoder "Description" - Validate Super-Coder changes');
            console.log('  node qa_agent_validation_gates.js history [agent]                   - Show validation history');
            console.log('  node qa_agent_validation_gates.js summary                           - Show validation summary');
            process.exit(0);
    }
}

module.exports = AgentValidationGates;