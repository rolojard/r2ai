#!/usr/bin/env node
/**
 * Comprehensive Dashboard System Test Suite
 * Tests all dashboard components, connections, and functionality
 */

const http = require('http');
const WebSocket = require('ws');

console.log('🔍 R2D2 Dashboard System Comprehensive Test Suite');
console.log('================================================\n');

const tests = [];
let totalTests = 0;
let passedTests = 0;

function addTest(name, testFunc) {
    tests.push({ name, testFunc });
    totalTests++;
}

function testPassed(testName) {
    console.log(`✅ ${testName}`);
    passedTests++;
}

function testFailed(testName, error) {
    console.log(`❌ ${testName}: ${error}`);
}

// Test HTTP Server Endpoints
addTest('Dashboard Server HTTP Endpoint', async () => {
    return new Promise((resolve) => {
        const req = http.get('http://localhost:8765/', (res) => {
            if (res.statusCode === 200) {
                testPassed('Dashboard Server HTTP Endpoint');
                resolve();
            } else {
                testFailed('Dashboard Server HTTP Endpoint', `Status: ${res.statusCode}`);
                resolve();
            }
        });
        req.on('error', (err) => {
            testFailed('Dashboard Server HTTP Endpoint', err.message);
            resolve();
        });
        req.setTimeout(5000, () => {
            testFailed('Dashboard Server HTTP Endpoint', 'Timeout');
            resolve();
        });
    });
});

// Test Enhanced Dashboard Route
addTest('Enhanced Dashboard Route', async () => {
    return new Promise((resolve) => {
        const req = http.get('http://localhost:8765/enhanced', (res) => {
            if (res.statusCode === 200) {
                testPassed('Enhanced Dashboard Route');
            } else {
                testFailed('Enhanced Dashboard Route', `Status: ${res.statusCode}`);
            }
            resolve();
        });
        req.on('error', (err) => {
            testFailed('Enhanced Dashboard Route', err.message);
            resolve();
        });
        req.setTimeout(5000, () => {
            testFailed('Enhanced Dashboard Route', 'Timeout');
            resolve();
        });
    });
});

// Test Vision Dashboard Route
addTest('Vision Dashboard Route', async () => {
    return new Promise((resolve) => {
        const req = http.get('http://localhost:8765/vision', (res) => {
            if (res.statusCode === 200) {
                testPassed('Vision Dashboard Route');
            } else {
                testFailed('Vision Dashboard Route', `Status: ${res.statusCode}`);
            }
            resolve();
        });
        req.on('error', (err) => {
            testFailed('Vision Dashboard Route', err.message);
            resolve();
        });
        req.setTimeout(5000, () => {
            testFailed('Vision Dashboard Route', 'Timeout');
            resolve();
        });
    });
});

// Test Servo Dashboard Route
addTest('Servo Dashboard Route', async () => {
    return new Promise((resolve) => {
        const req = http.get('http://localhost:8765/servo', (res) => {
            if (res.statusCode === 200) {
                testPassed('Servo Dashboard Route');
            } else {
                testFailed('Servo Dashboard Route', `Status: ${res.statusCode}`);
            }
            resolve();
        });
        req.on('error', (err) => {
            testFailed('Servo Dashboard Route', err.message);
            resolve();
        });
        req.setTimeout(5000, () => {
            testFailed('Servo Dashboard Route', 'Timeout');
            resolve();
        });
    });
});

// Test Disney Behavioral Dashboard Route
addTest('Disney Behavioral Dashboard Route', async () => {
    return new Promise((resolve) => {
        const req = http.get('http://localhost:8765/disney', (res) => {
            if (res.statusCode === 200) {
                testPassed('Disney Behavioral Dashboard Route');
            } else {
                testFailed('Disney Behavioral Dashboard Route', `Status: ${res.statusCode}`);
            }
            resolve();
        });
        req.on('error', (err) => {
            testFailed('Disney Behavioral Dashboard Route', err.message);
            resolve();
        });
        req.setTimeout(5000, () => {
            testFailed('Disney Behavioral Dashboard Route', 'Timeout');
            resolve();
        });
    });
});

// Test Main WebSocket Connection (Port 8766)
addTest('Main Dashboard WebSocket (8766)', async () => {
    return new Promise((resolve) => {
        const ws = new WebSocket('ws://localhost:8766');
        let connected = false;

        const timeout = setTimeout(() => {
            if (!connected) {
                testFailed('Main Dashboard WebSocket (8766)', 'Connection timeout');
                resolve();
            }
        }, 5000);

        ws.on('open', () => {
            connected = true;
            clearTimeout(timeout);
            testPassed('Main Dashboard WebSocket (8766)');
            ws.close();
            resolve();
        });

        ws.on('error', (error) => {
            clearTimeout(timeout);
            testFailed('Main Dashboard WebSocket (8766)', error.message);
            resolve();
        });
    });
});

// Test Behavioral WebSocket Connection (Port 8768)
addTest('Behavioral Intelligence WebSocket (8768)', async () => {
    return new Promise((resolve) => {
        const ws = new WebSocket('ws://localhost:8768');
        let connected = false;

        const timeout = setTimeout(() => {
            if (!connected) {
                testFailed('Behavioral Intelligence WebSocket (8768)', 'Connection timeout');
                resolve();
            }
        }, 5000);

        ws.on('open', () => {
            connected = true;
            clearTimeout(timeout);
            testPassed('Behavioral Intelligence WebSocket (8768)');
            ws.close();
            resolve();
        });

        ws.on('error', (error) => {
            clearTimeout(timeout);
            testFailed('Behavioral Intelligence WebSocket (8768)', error.message);
            resolve();
        });
    });
});

// Test Servo WebSocket Connection (Port 8767)
addTest('Servo Backend WebSocket (8767)', async () => {
    return new Promise((resolve) => {
        const ws = new WebSocket('ws://localhost:8767');
        let connected = false;

        const timeout = setTimeout(() => {
            if (!connected) {
                testFailed('Servo Backend WebSocket (8767)', 'Connection timeout');
                resolve();
            }
        }, 5000);

        ws.on('open', () => {
            connected = true;
            clearTimeout(timeout);
            testPassed('Servo Backend WebSocket (8767)');
            ws.close();
            resolve();
        });

        ws.on('error', (error) => {
            clearTimeout(timeout);
            testFailed('Servo Backend WebSocket (8767)', error.message);
            resolve();
        });
    });
});

// Test Servo API Health Endpoint
addTest('Servo API Health Endpoint', async () => {
    return new Promise((resolve) => {
        const req = http.get('http://localhost:5000/health', (res) => {
            let data = '';
            res.on('data', (chunk) => data += chunk);
            res.on('end', () => {
                try {
                    const health = JSON.parse(data);
                    if (health.status === 'healthy') {
                        testPassed('Servo API Health Endpoint');
                    } else {
                        testFailed('Servo API Health Endpoint', `Status: ${health.status}`);
                    }
                } catch (e) {
                    testFailed('Servo API Health Endpoint', 'Invalid JSON response');
                }
                resolve();
            });
        });
        req.on('error', (err) => {
            testFailed('Servo API Health Endpoint', err.message);
            resolve();
        });
        req.setTimeout(5000, () => {
            testFailed('Servo API Health Endpoint', 'Timeout');
            resolve();
        });
    });
});

// Test WebSocket Data Flow
addTest('WebSocket Data Flow Test', async () => {
    return new Promise((resolve) => {
        const ws = new WebSocket('ws://localhost:8766');
        let dataReceived = false;

        const timeout = setTimeout(() => {
            if (!dataReceived) {
                testFailed('WebSocket Data Flow Test', 'No data received');
            }
            ws.close();
            resolve();
        }, 8000);

        ws.on('open', () => {
            // Request data
            ws.send(JSON.stringify({ type: 'request_data' }));
        });

        ws.on('message', (data) => {
            try {
                const message = JSON.parse(data);
                if (message.type === 'system_stats' || message.type === 'r2d2_status') {
                    dataReceived = true;
                    clearTimeout(timeout);
                    testPassed('WebSocket Data Flow Test');
                    ws.close();
                    resolve();
                }
            } catch (e) {
                // Ignore parsing errors, wait for valid data
            }
        });

        ws.on('error', (error) => {
            clearTimeout(timeout);
            testFailed('WebSocket Data Flow Test', error.message);
            resolve();
        });
    });
});

async function runAllTests() {
    console.log('🚀 Starting comprehensive dashboard test suite...\n');

    for (let i = 0; i < tests.length; i++) {
        const test = tests[i];
        console.log(`Running test ${i + 1}/${tests.length}: ${test.name}`);
        await test.testFunc();
    }

    console.log('\n📊 Test Results Summary');
    console.log('========================');
    console.log(`✅ Passed: ${passedTests}/${totalTests}`);
    console.log(`❌ Failed: ${totalTests - passedTests}/${totalTests}`);

    const successRate = ((passedTests / totalTests) * 100).toFixed(1);
    console.log(`📈 Success Rate: ${successRate}%`);

    if (successRate >= 80) {
        console.log('\n🎉 Dashboard system is FUNCTIONAL!');
    } else if (successRate >= 60) {
        console.log('\n⚠️  Dashboard system has issues but is partially functional');
    } else {
        console.log('\n🚨 Dashboard system has significant issues');
    }

    console.log('\n🔧 Recommendations:');
    if (passedTests < totalTests) {
        console.log('- Review failed tests above');
        console.log('- Check server logs for detailed error information');
        console.log('- Ensure all required services are running');
    } else {
        console.log('- All tests passed! Dashboard system is fully operational');
        console.log('- Monitor performance and error logs periodically');
    }

    process.exit(0);
}

runAllTests().catch((error) => {
    console.error('Test suite error:', error);
    process.exit(1);
});