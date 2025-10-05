/**
 * WCB WebSocket Client Integration Example
 *
 * This file demonstrates how to use the WCB WebSocket messaging system
 * for real-time mood control and status updates in your dashboard.
 *
 * WebSocket Server: ws://localhost:8766
 * WCB API Server: http://localhost:8770
 */

// ===== WEBSOCKET CONNECTION SETUP =====

const wcbWebSocket = new WebSocket('ws://localhost:8766');

// Connection event handlers
wcbWebSocket.onopen = () => {
    console.log('WCB WebSocket connected successfully');

    // Request initial data on connection
    wcbWebSocket.send(JSON.stringify({type: 'wcb_mood_status_request'}));
    wcbWebSocket.send(JSON.stringify({type: 'wcb_mood_list_request'}));
    wcbWebSocket.send(JSON.stringify({type: 'wcb_stats_request'}));
};

wcbWebSocket.onerror = (error) => {
    console.error('WCB WebSocket error:', error);
};

wcbWebSocket.onclose = () => {
    console.log('WCB WebSocket disconnected');
    // Implement reconnection logic here if needed
    setTimeout(() => {
        console.log('Attempting to reconnect...');
        // Reinitialize connection
    }, 5000);
};

// ===== MESSAGE HANDLER =====

wcbWebSocket.onmessage = (event) => {
    try {
        const data = JSON.parse(event.data);

        // Route messages to appropriate handlers
        switch(data.type) {
            case 'wcb_mood_status':
                handleMoodStatusUpdate(data);
                break;

            case 'wcb_mood_result':
                handleMoodExecutionResult(data);
                break;

            case 'wcb_mood_list':
                handleMoodListUpdate(data);
                break;

            case 'wcb_stats':
                handleStatsUpdate(data);
                break;

            case 'wcb_error':
                handleWCBError(data);
                break;

            default:
                // Handle other message types (existing dashboard messages)
                console.log('Other message type:', data.type);
        }
    } catch (error) {
        console.error('Error parsing WebSocket message:', error);
    }
};

// ===== MESSAGE HANDLERS =====

function handleMoodStatusUpdate(data) {
    console.log('Mood Status Update:', data);

    // Update UI elements
    const statusElement = document.getElementById('wcb-mood-status');
    if (statusElement) {
        if (data.active) {
            statusElement.innerHTML = `
                <div class="mood-active">
                    <strong>Active Mood:</strong> ${data.mood}
                    <div class="progress-bar">
                        <div class="progress-fill" style="width: ${data.progress_percent}%"></div>
                    </div>
                    <small>Commands sent: ${data.commands_sent}</small>
                    <small>Started: ${new Date(data.started_at).toLocaleTimeString()}</small>
                </div>
            `;
        } else {
            statusElement.innerHTML = `
                <div class="mood-idle">
                    <strong>Status:</strong> Idle
                    <small>No active mood sequence</small>
                </div>
            `;
        }
    }
}

function handleMoodExecutionResult(data) {
    console.log('Mood Execution Result:', data);

    // Show notification
    if (data.status === 'success') {
        showNotification(`Success: ${data.mood} executed!`, 'success');
        console.log(`- Commands sent: ${data.commands_sent}`);
        console.log(`- Execution time: ${data.execution_time_ms}ms`);
    } else {
        showNotification(`Failed: ${data.message || 'Unknown error'}`, 'error');
    }
}

function handleMoodListUpdate(data) {
    console.log('Mood List Update:', data.total, 'moods available');

    // Populate mood selector
    const moodSelector = document.getElementById('wcb-mood-selector');
    if (moodSelector) {
        moodSelector.innerHTML = '';

        data.moods.forEach(mood => {
            const option = document.createElement('option');
            option.value = mood.id;
            option.textContent = `${mood.id}. ${mood.name} (${mood.command_count} cmds)`;
            option.dataset.category = mood.category;
            moodSelector.appendChild(option);
        });
    }

    // Create mood grid
    const moodGrid = document.getElementById('wcb-mood-grid');
    if (moodGrid) {
        moodGrid.innerHTML = '';

        data.moods.forEach(mood => {
            const moodCard = document.createElement('div');
            moodCard.className = 'mood-card';
            moodCard.innerHTML = `
                <h4>${mood.name}</h4>
                <p class="category">${mood.category}</p>
                <p class="commands">${mood.command_count} commands</p>
                <button onclick="executeMoodWS(${mood.id}, '${mood.name}')">Execute</button>
            `;
            moodGrid.appendChild(moodCard);
        });
    }
}

function handleStatsUpdate(data) {
    console.log('Stats Update:', data);

    // Update statistics display
    const statsElement = document.getElementById('wcb-stats');
    if (statsElement) {
        statsElement.innerHTML = `
            <div class="stat-item">
                <span class="stat-label">Moods Executed:</span>
                <span class="stat-value">${data.moods_executed}</span>
            </div>
            <div class="stat-item">
                <span class="stat-label">Total Commands:</span>
                <span class="stat-value">${data.total_commands_sent}</span>
            </div>
            <div class="stat-item">
                <span class="stat-label">Avg Execution Time:</span>
                <span class="stat-value">${data.average_execution_time_ms}ms</span>
            </div>
            <div class="stat-item">
                <span class="stat-label">Uptime:</span>
                <span class="stat-value">${formatUptime(data.uptime_seconds)}</span>
            </div>
        `;
    }
}

function handleWCBError(data) {
    console.error('WCB Error:', data.error, data.details);
    showNotification(`Error: ${data.error}`, 'error');

    // Show detailed error message
    const errorElement = document.getElementById('wcb-error-display');
    if (errorElement) {
        errorElement.innerHTML = `
            <div class="error-message">
                <strong>${data.error}</strong>
                <p>${data.details || 'No additional details'}</p>
                <small>${new Date(data.timestamp).toLocaleTimeString()}</small>
            </div>
        `;
        errorElement.style.display = 'block';

        // Auto-hide after 5 seconds
        setTimeout(() => {
            errorElement.style.display = 'none';
        }, 5000);
    }
}

// ===== CLIENT-TO-SERVER MESSAGE FUNCTIONS =====

/**
 * Execute a WCB mood via WebSocket
 * @param {number} moodId - Mood ID (1-27)
 * @param {string} moodName - Optional mood name
 * @param {number} priority - Optional priority (default 7)
 */
function executeMoodWS(moodId, moodName = null, priority = 7) {
    console.log(`Sending mood execute command: ${moodId} (${moodName})`);

    wcbWebSocket.send(JSON.stringify({
        type: 'wcb_mood_execute',
        mood_id: moodId,
        mood_name: moodName,
        priority: priority
    }));
}

/**
 * Stop the currently executing mood
 */
function stopMoodWS() {
    console.log('Sending mood stop command');

    wcbWebSocket.send(JSON.stringify({
        type: 'wcb_mood_stop'
    }));
}

/**
 * Request current mood status
 */
function requestMoodStatusWS() {
    wcbWebSocket.send(JSON.stringify({
        type: 'wcb_mood_status_request'
    }));
}

/**
 * Request list of available moods
 */
function requestMoodListWS() {
    wcbWebSocket.send(JSON.stringify({
        type: 'wcb_mood_list_request'
    }));
}

/**
 * Request WCB statistics
 */
function requestStatsWS() {
    wcbWebSocket.send(JSON.stringify({
        type: 'wcb_stats_request'
    }));
}

// ===== UTILITY FUNCTIONS =====

function showNotification(message, type = 'info') {
    console.log(`[${type.toUpperCase()}] ${message}`);

    // Create toast notification
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    notification.textContent = message;

    document.body.appendChild(notification);

    // Animate in
    setTimeout(() => notification.classList.add('show'), 10);

    // Remove after 3 seconds
    setTimeout(() => {
        notification.classList.remove('show');
        setTimeout(() => notification.remove(), 300);
    }, 3000);
}

function formatUptime(seconds) {
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const secs = seconds % 60;

    return `${hours}h ${minutes}m ${secs}s`;
}

// ===== EXAMPLE UI INTEGRATION =====

/**
 * Example HTML structure for WCB dashboard integration:
 *
 * <div id="wcb-control-panel">
 *   <div id="wcb-mood-status"></div>
 *
 *   <div id="wcb-mood-selector-container">
 *     <select id="wcb-mood-selector">
 *       <option>Loading moods...</option>
 *     </select>
 *     <button onclick="executeMoodFromSelector()">Execute</button>
 *     <button onclick="stopMoodWS()">Stop</button>
 *   </div>
 *
 *   <div id="wcb-mood-grid"></div>
 *
 *   <div id="wcb-stats"></div>
 *
 *   <div id="wcb-error-display" style="display: none;"></div>
 * </div>
 */

function executeMoodFromSelector() {
    const selector = document.getElementById('wcb-mood-selector');
    if (selector && selector.value) {
        const selectedOption = selector.options[selector.selectedIndex];
        const moodId = parseInt(selector.value);
        const moodName = selectedOption.textContent.split('.')[1].split('(')[0].trim();

        executeMoodWS(moodId, moodName);
    }
}

// ===== INITIALIZATION =====

document.addEventListener('DOMContentLoaded', () => {
    console.log('WCB WebSocket Client initialized');

    // Set up periodic status refresh (backup to WebSocket broadcasts)
    setInterval(() => {
        if (wcbWebSocket.readyState === WebSocket.OPEN) {
            requestMoodStatusWS();
        }
    }, 5000); // Every 5 seconds as backup
});

// ===== TESTING EXAMPLES =====

/**
 * Console Testing Commands:
 *
 * // Execute a specific mood
 * executeMoodWS(5, 'EXCITED_HAPPY', 7);
 *
 * // Stop current mood
 * stopMoodWS();
 *
 * // Request status updates
 * requestMoodStatusWS();
 * requestMoodListWS();
 * requestStatsWS();
 *
 * // Check connection status
 * console.log('WebSocket state:', wcbWebSocket.readyState);
 * // 0 = CONNECTING, 1 = OPEN, 2 = CLOSING, 3 = CLOSED
 */
