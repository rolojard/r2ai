#!/usr/bin/env node
/**
 * Dashboard WebSocket Connectivity Test
 */

const WebSocket = require('ws');

console.log('🔍 Testing Dashboard WebSocket Connections...\n');

function testWebSocketConnection(port, name) {
    return new Promise((resolve) => {
        console.log(`Testing ${name} on port ${port}...`);

        const ws = new WebSocket(`ws://localhost:${port}`);
        let connected = false;

        const timeout = setTimeout(() => {
            if (!connected) {
                console.log(`❌ ${name} - Connection timeout\n`);
                resolve({ port, name, status: 'timeout' });
            }
        }, 5000);

        ws.on('open', () => {
            connected = true;
            clearTimeout(timeout);
            console.log(`✅ ${name} - Connected successfully`);

            // Send test message
            ws.send(JSON.stringify({ type: 'test_connection' }));

            setTimeout(() => {
                ws.close();
                console.log(`🔌 ${name} - Connection closed\n`);
                resolve({ port, name, status: 'success' });
            }, 1000);
        });

        ws.on('message', (data) => {
            console.log(`📨 ${name} - Received message:`, data.toString());
        });

        ws.on('error', (error) => {
            clearTimeout(timeout);
            console.log(`❌ ${name} - Error: ${error.message}\n`);
            resolve({ port, name, status: 'error', error: error.message });
        });

        ws.on('close', () => {
            if (!connected) {
                clearTimeout(timeout);
                console.log(`❌ ${name} - Connection closed before opening\n`);
                resolve({ port, name, status: 'closed' });
            }
        });
    });
}

async function runTests() {
    const tests = [
        { port: 8766, name: 'Main Dashboard WebSocket' },
        { port: 8768, name: 'Behavioral Intelligence WebSocket' }
    ];

    const results = [];

    for (const test of tests) {
        const result = await testWebSocketConnection(test.port, test.name);
        results.push(result);
    }

    console.log('📊 Test Results Summary:');
    console.log('========================');
    results.forEach(result => {
        const status = result.status === 'success' ? '✅' : '❌';
        console.log(`${status} ${result.name} (port ${result.port}): ${result.status}`);
        if (result.error) {
            console.log(`   Error: ${result.error}`);
        }
    });

    const successCount = results.filter(r => r.status === 'success').length;
    console.log(`\n🎯 ${successCount}/${results.length} connections successful`);

    process.exit(0);
}

runTests().catch(console.error);