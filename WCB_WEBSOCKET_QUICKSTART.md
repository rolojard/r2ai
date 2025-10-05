# WCB WebSocket Integration - Quick Start Guide

## 🚀 Get Started in 3 Minutes

### Prerequisites
- WCB Dashboard API running
- Dashboard Server ready
- Browser (Chrome/Firefox recommended)

---

## Step 1: Start the Servers

### Terminal 1 - WCB Dashboard API
```bash
cd /home/rolo/r2ai
python3 wcb_dashboard_api.py
```

**Expected Output:**
```
🎮 WCB Dashboard API Server
📡 Starting on port 8770...
✅ Server running at http://localhost:8770
🔗 Available endpoints:
   • GET  /api/wcb/status
   • GET  /api/wcb/mood/list
   • GET  /api/wcb/mood/status
   • POST /api/wcb/mood/execute
   • POST /api/wcb/mood/stop
   • GET  /api/wcb/stats
```

### Terminal 2 - Dashboard Server
```bash
cd /home/rolo/r2ai
node dashboard-server.js
```

**Expected Output:**
```
🎯 R2D2 Dashboard Server running at http://localhost:8765
🔌 WebSocket server running on port 8766
🧠 Behavioral Intelligence WebSocket server running on port 8768
📊 Dashboard ready for R2AI system monitoring!
```

---

## Step 2: Open Test Interface

Open your browser to:
```
http://localhost:8765/wcb_websocket_test.html
```

**You should see:**
- 🤖 WCB WebSocket Test Interface
- Connection status indicator (should turn GREEN automatically)
- Message log showing "Connected to WebSocket"

---

## Step 3: Test Basic Functions

### Test 1: Get Mood List
Click **"Get Mood List"** button

**Expected Result:**
- Log shows: "Loaded 27 moods"
- Mood selector dropdown populated
- Mood grid shows all available moods

### Test 2: Execute a Mood
Click any mood card OR select from dropdown and click **"Execute Selected Mood"**

**Expected Result:**
- Log shows: "✓ Mood executed: [MOOD_NAME]"
- Green notification appears
- Progress bar shows execution
- Physical WCB hardware responds

### Test 3: Stop Mood
During mood execution, click **"Stop Current Mood"**

**Expected Result:**
- Log shows: "Mood stopped"
- Progress bar resets
- Status returns to "Idle"

---

## Quick Testing Commands

### Browser Console Method

Press **F12** to open Developer Console, then paste:

```javascript
// Test 1: Connect to WebSocket
const ws = new WebSocket('ws://localhost:8766');
ws.onopen = () => console.log('✅ Connected!');
ws.onmessage = (e) => console.log('📨', JSON.parse(e.data));

// Test 2: Get mood list
ws.send(JSON.stringify({type: 'wcb_mood_list_request'}));

// Test 3: Get status
ws.send(JSON.stringify({type: 'wcb_mood_status_request'}));

// Test 4: Execute mood #5 (EXCITED_HAPPY)
ws.send(JSON.stringify({
  type: 'wcb_mood_execute',
  mood_id: 5,
  mood_name: 'EXCITED_HAPPY',
  priority: 7
}));

// Test 5: Stop mood
ws.send(JSON.stringify({type: 'wcb_mood_stop'}));
```

---

## Verify Auto-Broadcasting

**Watch the console for 10 seconds**

You should see messages appearing automatically every ~1 second:
```javascript
{type: "wcb_mood_status", active: false, mood: null, ...}
{type: "wcb_stats", moods_executed: 0, total_commands_sent: 0, ...}
```

This confirms the 1-second auto-broadcast is working!

---

## Common Issues & Solutions

### ❌ "WebSocket error" in log

**Problem:** Dashboard server not running

**Solution:**
```bash
node /home/rolo/r2ai/dashboard-server.js
```

### ❌ "WCB API Error: connect ECONNREFUSED"

**Problem:** WCB API server not running

**Solution:**
```bash
python3 /home/rolo/r2ai/wcb_dashboard_api.py
```

### ❌ No moods in list

**Problem:** WCB orchestrator not connected

**Solution:**
1. Check WCB API terminal for errors
2. Verify `wcb_mood_commands.json` exists
3. Restart WCB API

### ❌ Mood executes but nothing happens

**Problem:** Physical hardware not connected

**Solution:**
1. Check WCB orchestrator logs
2. Verify serial connection to Maestro board
3. Check hardware power

---

## Success Checklist

- [ ] Both servers running (WCB API + Dashboard)
- [ ] Test page loads successfully
- [ ] WebSocket connects (green indicator)
- [ ] Mood list loads (27 moods)
- [ ] Can execute a mood
- [ ] Can stop a mood
- [ ] Status updates appear in log
- [ ] Statistics display updates
- [ ] Auto-broadcasting working (1s interval)

---

## Next Steps After Quick Start

### 1. Run Full Test Suite
See: `WCB_WEBSOCKET_TESTING_GUIDE.md`
- 10 comprehensive tests
- Performance benchmarks
- Multi-client testing

### 2. Integrate into Your Dashboard
See: `WCB_WEBSOCKET_CLIENT_EXAMPLE.js`
- Copy-paste ready code
- UI integration examples
- Production patterns

### 3. Read Full Documentation
See: `WCB_WEBSOCKET_IMPLEMENTATION_SUMMARY.md`
- Complete architecture
- Message protocol details
- Troubleshooting guide

---

## 30-Second Verification Test

Run this in browser console:

```javascript
fetch('http://localhost:8770/api/wcb/mood/list')
  .then(r => r.json())
  .then(d => console.log('✅ WCB API:', d.total, 'moods'))
  .catch(e => console.log('❌ WCB API offline'));

const ws = new WebSocket('ws://localhost:8766');
ws.onopen = () => {
  console.log('✅ WebSocket connected');
  ws.send(JSON.stringify({type: 'wcb_mood_status_request'}));
};
ws.onmessage = (e) => {
  const d = JSON.parse(e.data);
  if (d.type === 'wcb_mood_status') {
    console.log('✅ Status:', d.active ? 'Active' : 'Idle');
  }
};
```

**Expected Output:**
```
✅ WCB API: 27 moods
✅ WebSocket connected
✅ Status: Idle
```

---

## Congratulations! 🎉

If you see all green checkmarks, your WCB WebSocket integration is working perfectly!

You can now:
- Execute moods via WebSocket
- Monitor real-time status
- Track statistics
- Build custom dashboards
- Integrate into existing systems

**Ready for production use!**

---

## Quick Reference Card

| Action | Command |
|--------|---------|
| **Start WCB API** | `python3 wcb_dashboard_api.py` |
| **Start Dashboard** | `node dashboard-server.js` |
| **Test Page** | `http://localhost:8765/wcb_websocket_test.html` |
| **WebSocket URL** | `ws://localhost:8766` |
| **API URL** | `http://localhost:8770` |
| **Execute Mood** | `{type:'wcb_mood_execute', mood_id:5}` |
| **Stop Mood** | `{type:'wcb_mood_stop'}` |
| **Get Status** | `{type:'wcb_mood_status_request'}` |

---

**Need Help?**
- Full Testing Guide: `WCB_WEBSOCKET_TESTING_GUIDE.md`
- Client Examples: `WCB_WEBSOCKET_CLIENT_EXAMPLE.js`
- Complete Docs: `WCB_WEBSOCKET_IMPLEMENTATION_SUMMARY.md`
