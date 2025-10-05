# WCB WebSocket Integration - Testing & Usage Guide

## Overview

The WCB (Wookiee Control Board) WebSocket integration enables real-time bidirectional communication between the dashboard and the WCB mood orchestration system.

**Key Features:**
- Real-time mood execution commands
- Automatic status broadcasting (1-second interval)
- All WCB API endpoints accessible via WebSocket
- Multi-client support with concurrent connections
- Comprehensive error handling

---

## Architecture

```
Dashboard Client (Browser)
    ↕ WebSocket (ws://localhost:8766)
Dashboard Server (Node.js)
    ↕ HTTP REST API (http://localhost:8770)
WCB Dashboard API (Flask)
    ↕ Message Queue
WCB Orchestrator (Python)
    ↕ Serial Commands
Wookiee Control Board (Hardware)
```

---

## WebSocket Message Protocol

### Client → Server Messages

#### 1. Execute WCB Mood
```javascript
{
  type: 'wcb_mood_execute',
  mood_id: 5,                    // Required: 1-27
  mood_name: 'EXCITED_HAPPY',    // Optional
  priority: 7                    // Optional: default 7
}
```

#### 2. Stop Current Mood
```javascript
{
  type: 'wcb_mood_stop'
}
```

#### 3. Request Status Update
```javascript
{
  type: 'wcb_mood_status_request'
}
```

#### 4. Request Mood List
```javascript
{
  type: 'wcb_mood_list_request'
}
```

#### 5. Request Statistics
```javascript
{
  type: 'wcb_stats_request'
}
```

### Server → Client Messages

#### 1. Mood Execution Result
```javascript
{
  type: 'wcb_mood_result',
  status: 'success',              // 'success' or 'error'
  mood: 'EXCITED_HAPPY',
  commands_sent: 7,
  execution_time_ms: 850,
  message: 'Mood executed successfully',
  timestamp: 1728123456789
}
```

#### 2. Mood Status Update (Auto-broadcast every 1s)
```javascript
{
  type: 'wcb_mood_status',
  active: true,
  mood: 'EXCITED_HAPPY',
  progress_percent: 45,
  commands_sent: 12,
  started_at: '2025-10-05T12:34:56',
  timestamp: 1728123456789
}
```

#### 3. Mood List Response
```javascript
{
  type: 'wcb_mood_list',
  moods: [
    {
      id: 1,
      name: 'IDLE_RELAXED',
      category: 'Primary Emotional',
      command_count: 4
    },
    // ... all 27 moods
  ],
  total: 27,
  timestamp: 1728123456789
}
```

#### 4. Statistics Update (Auto-broadcast every 1s)
```javascript
{
  type: 'wcb_stats',
  moods_executed: 47,
  total_commands_sent: 892,
  average_execution_time_ms: 4235,
  uptime_seconds: 3600,
  timestamp: 1728123456789
}
```

#### 5. Error Message
```javascript
{
  type: 'wcb_error',
  error: 'Mood execution failed',
  details: 'Orchestrator not connected',
  timestamp: 1728123456789
}
```

---

## Testing Procedures

### Prerequisites

1. **Start WCB Dashboard API** (Port 8770)
```bash
cd /home/rolo/r2ai
python3 wcb_dashboard_api.py
```

2. **Start Dashboard Server** (Port 8766 WebSocket)
```bash
cd /home/rolo/r2ai
node dashboard-server.js
```

3. **Verify Services Are Running**
```bash
# Check WCB API
curl http://localhost:8770/api/wcb/status

# Check Dashboard Server
curl http://localhost:8765/
```

---

### Test 1: WebSocket Connection

**Objective:** Verify WebSocket connection establishment

**Steps:**
1. Open browser to http://localhost:8765/
2. Open Developer Console (F12)
3. Run:
```javascript
const ws = new WebSocket('ws://localhost:8766');
ws.onopen = () => console.log('Connected!');
ws.onerror = (e) => console.error('Error:', e);
ws.onmessage = (e) => console.log('Message:', JSON.parse(e.data));
```

**Expected Result:**
- Console shows "Connected!"
- No errors in console

**Pass Criteria:** ✅ Connection established successfully

---

### Test 2: Mood List Request

**Objective:** Verify mood list retrieval

**Steps:**
```javascript
ws.send(JSON.stringify({type: 'wcb_mood_list_request'}));
```

**Expected Result:**
```javascript
{
  type: 'wcb_mood_list',
  moods: [...],
  total: 27,
  timestamp: ...
}
```

**Pass Criteria:** ✅ Received 27 moods with correct structure

---

### Test 3: Status Request

**Objective:** Verify status information retrieval

**Steps:**
```javascript
ws.send(JSON.stringify({type: 'wcb_mood_status_request'}));
```

**Expected Result:**
```javascript
{
  type: 'wcb_mood_status',
  active: false,
  mood: null,
  progress_percent: 0,
  commands_sent: 0,
  started_at: null,
  timestamp: ...
}
```

**Pass Criteria:** ✅ Received status with correct structure

---

### Test 4: Statistics Request

**Objective:** Verify statistics retrieval

**Steps:**
```javascript
ws.send(JSON.stringify({type: 'wcb_stats_request'}));
```

**Expected Result:**
```javascript
{
  type: 'wcb_stats',
  moods_executed: 0,
  total_commands_sent: 0,
  average_execution_time_ms: 0,
  uptime_seconds: ...,
  timestamp: ...
}
```

**Pass Criteria:** ✅ Received stats with correct structure

---

### Test 5: Mood Execution

**Objective:** Verify mood execution command

**Steps:**
```javascript
ws.send(JSON.stringify({
  type: 'wcb_mood_execute',
  mood_id: 5,
  mood_name: 'EXCITED_HAPPY',
  priority: 7
}));
```

**Expected Results:**
1. **Immediate response:**
```javascript
{
  type: 'wcb_mood_result',
  status: 'success',
  mood: 'EXCITED_HAPPY',
  commands_sent: 7,
  execution_time_ms: 850
}
```

2. **Auto-broadcast updates (every 1s during execution):**
```javascript
{
  type: 'wcb_mood_status',
  active: true,
  mood: 'EXCITED_HAPPY',
  progress_percent: 45,
  commands_sent: 12,
  started_at: '2025-10-05T12:34:56'
}
```

**Pass Criteria:**
- ✅ Received success confirmation
- ✅ Received status updates during execution
- ✅ Physical WCB executed mood sequence

---

### Test 6: Mood Stop

**Objective:** Verify mood interruption

**Steps:**
1. Execute a mood:
```javascript
ws.send(JSON.stringify({
  type: 'wcb_mood_execute',
  mood_id: 10,
  mood_name: 'FEAR_PANIC'
}));
```

2. Immediately stop it:
```javascript
ws.send(JSON.stringify({type: 'wcb_mood_stop'}));
```

**Expected Result:**
```javascript
{
  type: 'wcb_mood_result',
  status: 'success',
  message: 'Mood stopped'
}
```

**Pass Criteria:**
- ✅ Mood execution interrupted
- ✅ Status returns to idle

---

### Test 7: Auto-Broadcasting

**Objective:** Verify 1-second status broadcasts

**Steps:**
1. Connect to WebSocket
2. Monitor console for 10 seconds
3. Count status and stats messages

**Expected Result:**
- Approximately 10 `wcb_mood_status` messages
- Approximately 10 `wcb_stats` messages

**Pass Criteria:** ✅ Received regular broadcasts every ~1 second

---

### Test 8: Multiple Concurrent Clients

**Objective:** Verify multi-client support

**Steps:**
1. Open two browser tabs to http://localhost:8765/
2. In Tab 1, execute a mood:
```javascript
ws.send(JSON.stringify({
  type: 'wcb_mood_execute',
  mood_id: 3,
  mood_name: 'ALERT_FOCUSED'
}));
```

3. In Tab 2, monitor for status updates

**Expected Result:**
- Both tabs receive status broadcasts
- Both tabs show same mood execution status

**Pass Criteria:** ✅ Both clients synchronized

---

### Test 9: Error Handling - API Offline

**Objective:** Verify graceful degradation when WCB API is offline

**Steps:**
1. Stop WCB API: `Ctrl+C` on wcb_dashboard_api.py
2. Try to execute mood:
```javascript
ws.send(JSON.stringify({
  type: 'wcb_mood_execute',
  mood_id: 5
}));
```

**Expected Result:**
```javascript
{
  type: 'wcb_error',
  error: 'Mood execution failed',
  details: 'connect ECONNREFUSED ...'
}
```

**Pass Criteria:**
- ✅ Received error message
- ✅ Dashboard server didn't crash
- ✅ WebSocket connection remained active

---

### Test 10: Existing Dashboard Features

**Objective:** Verify no breaking changes to existing functionality

**Steps:**
1. Test existing servo commands
2. Test existing audio commands
3. Test existing behavioral commands

**Expected Result:**
- All existing features work normally
- No conflicts with WCB messages

**Pass Criteria:** ✅ All existing features functional

---

## Performance Benchmarks

### Expected Performance Metrics

| Metric | Target | Acceptable |
|--------|--------|------------|
| WebSocket latency | < 10ms | < 50ms |
| Message processing | < 5ms | < 20ms |
| Broadcast interval | 1000ms ± 10ms | 1000ms ± 50ms |
| Concurrent clients | 10+ | 5+ |
| Memory usage | < 100MB | < 200MB |

### Performance Test Commands

```javascript
// Latency test
const start = Date.now();
ws.send(JSON.stringify({type: 'wcb_mood_status_request'}));
ws.onmessage = (e) => {
  const data = JSON.parse(e.data);
  if (data.type === 'wcb_mood_status') {
    console.log('Latency:', Date.now() - start, 'ms');
  }
};

// Broadcast interval test
let lastTimestamp = 0;
let intervals = [];
ws.onmessage = (e) => {
  const data = JSON.parse(e.data);
  if (data.type === 'wcb_mood_status') {
    if (lastTimestamp) {
      intervals.push(data.timestamp - lastTimestamp);
      console.log('Interval:', data.timestamp - lastTimestamp, 'ms');
      console.log('Average:', intervals.reduce((a,b)=>a+b)/intervals.length, 'ms');
    }
    lastTimestamp = data.timestamp;
  }
};
```

---

## Troubleshooting

### Issue: WebSocket won't connect

**Solutions:**
1. Verify dashboard-server.js is running
2. Check port 8766 is not in use: `lsof -i :8766`
3. Check firewall settings

### Issue: No WCB status updates

**Solutions:**
1. Verify WCB API is running on port 8770
2. Check logs: `curl http://localhost:8770/api/wcb/status`
3. Restart both services

### Issue: Commands not executing

**Solutions:**
1. Check WCB orchestrator is connected
2. Verify message format is correct
3. Check browser console for errors

### Issue: High memory usage

**Solutions:**
1. Check for WebSocket connection leaks
2. Monitor with: `node --expose-gc dashboard-server.js`
3. Reduce broadcast frequency if needed

---

## Integration Checklist

- [ ] WCB API running on port 8770
- [ ] Dashboard server running on port 8766
- [ ] WebSocket connection established
- [ ] Mood list retrieval working
- [ ] Status requests working
- [ ] Statistics requests working
- [ ] Mood execution working
- [ ] Mood stop working
- [ ] Auto-broadcasting active (1s interval)
- [ ] Multiple clients supported
- [ ] Error handling tested
- [ ] Existing features unaffected
- [ ] Performance benchmarks met

---

## API Endpoint Reference

### WCB Dashboard API (Flask)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/wcb/status` | GET | System status |
| `/api/wcb/mood/list` | GET | List all moods |
| `/api/wcb/mood/status` | GET | Current mood status |
| `/api/wcb/mood/execute` | POST | Execute mood |
| `/api/wcb/mood/stop` | POST | Stop current mood |
| `/api/wcb/stats` | GET | Usage statistics |

### Dashboard WebSocket (Node.js)

| Port | Protocol | Purpose |
|------|----------|---------|
| 8765 | HTTP | Dashboard web server |
| 8766 | WebSocket | Main dashboard WebSocket |
| 8768 | WebSocket | Behavioral intelligence |
| 8770 | HTTP | WCB Dashboard API |

---

## Success Criteria Summary

**Integration is successful when:**

1. ✅ All 10 test cases pass
2. ✅ Performance metrics meet targets
3. ✅ No breaking changes to existing features
4. ✅ Error handling works gracefully
5. ✅ Multi-client support confirmed
6. ✅ Auto-broadcasting functioning at 1s interval
7. ✅ Physical WCB hardware responds to commands

---

## Next Steps

After successful testing:

1. **Create WCB-specific dashboard page**
   - Dedicated mood control interface
   - Real-time status visualization
   - Statistics dashboard

2. **Add to existing dashboards**
   - Integrate WCB controls into main dashboard
   - Add mood selector to behavioral dashboard
   - Create quick-access mood buttons

3. **Implement advanced features**
   - Mood scheduling
   - Mood sequencing
   - Custom mood creation
   - Mood history tracking

4. **Documentation**
   - User guide for dashboard operators
   - Video tutorials
   - API documentation

---

## Contact & Support

**Files Modified:**
- `/home/rolo/r2ai/dashboard-server.js` - WebSocket message handlers added

**Files Created:**
- `/home/rolo/r2ai/WCB_WEBSOCKET_CLIENT_EXAMPLE.js` - Client integration example
- `/home/rolo/r2ai/WCB_WEBSOCKET_TESTING_GUIDE.md` - This testing guide

**Related Systems:**
- WCB Dashboard API: `/home/rolo/r2ai/wcb_dashboard_api.py`
- WCB Orchestrator: `/home/rolo/r2ai/wcb_orchestrator.py`
- WCB Controller: `/home/rolo/r2ai/wcb_controller.py`

---

## Version History

- **v1.0.0** (2025-10-05) - Initial WebSocket integration
  - 5 client→server message types
  - 5 server→client message types
  - 1-second auto-broadcasting
  - Multi-client support
  - Comprehensive error handling
