#!/usr/bin/env node

const WebSocket = require('ws');

console.log('Testing dashboard command functionality...');

const ws = new WebSocket('ws://localhost:8766');

let testIndex = 0;
const commands = [
    {type: 'command', command: 'test_servos'},
    {type: 'command', command: 'test_audio'},
    {type: 'command', command: 'test_vision'},
    {type: 'servo_command', channel: 1, position: 1500},
    {type: 'audio_command', sound: 'beep'},
    {type: 'emergency_stop', system: 'all'}
];

ws.on('open', function open() {
    console.log('✅ Connected to dashboard for command testing');

    // Run each test command with delay
    function runNextTest() {
        if (testIndex < commands.length) {
            const cmd = commands[testIndex];
            console.log(`\n🧪 Testing command ${testIndex + 1}/${commands.length}:`, cmd.type);
            ws.send(JSON.stringify(cmd));
            testIndex++;

            setTimeout(runNextTest, 2000);
        } else {
            console.log('\n✅ All command tests completed');
            setTimeout(() => {
                ws.close();
                process.exit(0);
            }, 2000);
        }
    }

    runNextTest();
});

ws.on('message', function message(data) {
    try {
        const parsed = JSON.parse(data);

        if (parsed.type === 'alert') {
            const emoji = parsed.level === 'error' ? '❌' :
                         parsed.level === 'success' ? '✅' : '📋';
            console.log(`${emoji} Alert: ${parsed.message}`);
        }
    } catch (error) {
        console.log('📨 Response:', data.toString());
    }
});

ws.on('error', function error(err) {
    console.error('❌ WebSocket error:', err.message);
    process.exit(1);
});

// Timeout after 30 seconds
setTimeout(() => {
    console.error('❌ Command test timed out');
    process.exit(1);
}, 30000);