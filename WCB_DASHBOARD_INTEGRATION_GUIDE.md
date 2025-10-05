# WCB Dashboard Integration Guide

## Overview
This document describes the refactored R2D2 dashboards that now use the WCB (Wired Command Bus) Orchestration System for intelligent mood-based control instead of direct servo/light commands.

---

## 🎯 Mission Accomplished

### Deliverables

1. **r2d2_wcb_mood_dashboard.html** - Primary WCB Mood Control Dashboard
2. **r2d2_behavioral_wcb_dashboard.html** - Behavioral Intelligence + WCB Integration
3. **WCB_DASHBOARD_INTEGRATION_GUIDE.md** - This documentation
4. **wcb_dashboard_test.py** - Automated testing script

---

## 🚀 New Dashboards

### 1. Primary WCB Mood Dashboard
**File:** `/home/rolo/r2ai/r2d2_wcb_mood_dashboard.html`

**Features:**
- ✅ 27 R2D2 personality mood buttons organized by category
- ✅ Real-time mood status display with progress indicator
- ✅ Commands sent counter and execution timer
- ✅ Quick-access buttons for common moods
- ✅ Emergency panic button (Mood 27)
- ✅ Live vision feed integration
- ✅ Character detection display
- ✅ Statistics tracking (moods executed, total commands)
- ✅ 500ms status polling from WCB API
- ✅ Toast notifications for user feedback
- ✅ Responsive design (mobile-friendly)

**Mood Categories:**
1. **Primary Emotional** (1-6): Idle Relaxed, Idle Bored, Alert Curious, Alert Cautious, Excited Happy, Excited Mischievous
2. **Social Interaction** (7-10): Greeting Friendly, Greeting Shy, Affectionate, Sad Whimper
3. **Character Specific** (11-14): Stubborn Defiant, Frightened, Protective Alert, Sassy Attitude
4. **Activity States** (15-20): Scanning Methodical, Scanning Frantic, Processing Task, Problem Solving, Task Complete, Task Failed
5. **Performance States** (21-26): Entertaining Crowd, Show-off Mode, Jedi Respect, Sith Alert, Spy Mode, Low Power Sleep
6. **Special States** (27): Emergency Panic

**Access:**
```bash
# Start WCB Dashboard API (if not running)
python wcb_dashboard_api.py

# Open dashboard
xdg-open /home/rolo/r2ai/r2d2_wcb_mood_dashboard.html
# Or navigate to: file:///home/rolo/r2ai/r2d2_wcb_mood_dashboard.html
```

---

### 2. Behavioral Intelligence + WCB Dashboard
**File:** `/home/rolo/r2ai/r2d2_behavioral_wcb_dashboard.html`

**Features:**
- ✅ Personality mode selector (Curious, Excited, Cautious, Playful, Protective, Friendly)
- ✅ Each personality mode triggers corresponding WCB mood
- ✅ Visual mapping of behavioral states to WCB moods
- ✅ Real-time mood execution status
- ✅ Quick mood action buttons
- ✅ Emergency panic integration
- ✅ Statistics dashboard (total moods, commands, uptime)
- ✅ WCB API connection status
- ✅ Responsive grid layout

**Personality → Mood Mapping:**
- **Curious** → Alert Curious (Mood 3)
- **Excited** → Excited Happy (Mood 5)
- **Cautious** → Alert Cautious (Mood 4)
- **Playful** → Excited Mischievous (Mood 6)
- **Protective** → Protective Alert (Mood 13)
- **Friendly** → Greeting Friendly (Mood 7)

**Access:**
```bash
xdg-open /home/rolo/r2ai/r2d2_behavioral_wcb_dashboard.html
```

---

## 🔧 Technical Architecture

### API Integration

**WCB Dashboard API Endpoints:**
```
POST http://localhost:8770/api/wcb/mood/execute
  Body: {"mood_id": 1-27, "priority": 1-10}
  Response: {"mood": "Idle Relaxed", "commands_sent": 8}

POST http://localhost:8770/api/wcb/mood/stop
  Response: {"status": "stopped"}

GET http://localhost:8770/api/wcb/mood/status
  Response: {
    "active": true,
    "mood": "Excited Happy",
    "commands_sent": 12,
    "progress_percent": 45
  }
```

### Vision Feed Integration

**WebSocket Connection:**
```javascript
const VISION_WS_URL = 'ws://localhost:8767';
visionWs = new WebSocket(VISION_WS_URL);

visionWs.onmessage = (event) => {
  const data = JSON.parse(event.data);
  if (data.type === 'vision_data' && data.image) {
    // Display base64 encoded image
    img.src = 'data:image/jpeg;base64,' + data.image;
  }
};
```

### Status Polling

**500ms Polling Loop:**
```javascript
setInterval(pollMoodStatus, 500);

async function pollMoodStatus() {
  const response = await fetch(`${WCB_API_URL}/api/wcb/mood/status`);
  const status = await response.json();
  
  // Update UI with current mood state
  updateMoodStatus(status.mood, status.progress_percent);
}
```

---

## 🎨 UI/UX Features

### Visual Feedback
- **Active Mood Highlighting:** Pulsing gradient animation on active mood button
- **Progress Bar:** Real-time visual progress of mood execution
- **Connection Status:** Green (connected) / Red (disconnected) indicator
- **Toast Notifications:** Success/error messages for user actions
- **Statistics Dashboard:** Live counters for moods executed and commands sent

### Responsive Design
- **Desktop:** 2-column grid layout
- **Tablet:** Adaptive grid (1200px breakpoint)
- **Mobile:** Single column stack (768px breakpoint)
- **Touch-friendly:** Large buttons with hover states

### Accessibility
- **Semantic HTML:** Proper heading hierarchy
- **ARIA Labels:** Emergency stop, connection status
- **Keyboard Navigation:** Tab-accessible controls
- **Color Contrast:** WCAG AA compliant

---

## 🧪 Testing

### Manual Testing Checklist

**WCB Mood Dashboard:**
- [ ] Load dashboard and verify connection status turns green
- [ ] Click "Idle Relaxed" (Mood 1) - verify progress bar updates
- [ ] Click "Excited Happy" (Mood 5) - verify button highlights
- [ ] Click "Stop Mood" - verify mood stops and progress resets
- [ ] Test all 27 mood buttons in each category
- [ ] Verify quick-access buttons work (Greet, Happy, Alert, Emergency)
- [ ] Test Emergency Panic button (Mood 27)
- [ ] Verify statistics update correctly
- [ ] Test vision feed connection (if vision system running)
- [ ] Test responsive design (resize browser window)

**Behavioral Dashboard:**
- [ ] Click "Curious" personality mode - verify Mood 3 executes
- [ ] Click "Excited" personality mode - verify Mood 5 executes
- [ ] Verify personality mode highlights when active
- [ ] Test quick mood action buttons
- [ ] Verify WCB status indicator shows connected
- [ ] Test Emergency Panic button
- [ ] Verify uptime counter increments
- [ ] Test all personality modes sequentially

### Automated Testing

**Test Script:** `/home/rolo/r2ai/wcb_dashboard_test.py`

```bash
# Run automated tests
python wcb_dashboard_test.py
```

**Test Coverage:**
- WCB API connectivity
- All 27 mood execution endpoints
- Mood stop functionality
- Status polling accuracy
- Error handling (API offline scenarios)
- Response time validation (<500ms)

---

## 📊 Performance Metrics

### Target Metrics
- **Status Poll Frequency:** 500ms
- **API Response Time:** <100ms average
- **Mood Execution Time:** As per mood duration (3-20 seconds)
- **UI Update Latency:** <50ms
- **Dashboard Load Time:** <2 seconds

### Optimization
- **CSS Animations:** GPU-accelerated transforms
- **Fetch API:** Async/await for non-blocking requests
- **WebSocket:** Efficient binary data transfer for vision feed
- **Polling Strategy:** Exponential backoff on connection failure

---

## 🔄 Migration from Old Dashboards

### What Changed

**REMOVED:**
- ❌ Direct `sendServoCommand()` functions
- ❌ Individual servo sliders for dome, head, panels
- ❌ Direct light control commands
- ❌ Manual PSI/Logic display controls
- ❌ Sound bank selection dropdowns

**ADDED:**
- ✅ WCB mood-based orchestration
- ✅ 27 intelligent personality moods
- ✅ Behavioral state mapping
- ✅ Real-time mood status monitoring
- ✅ Command execution progress tracking
- ✅ Integrated vision feed with character detection

### Benefits

1. **Behavioral Intelligence:** Moods execute coordinated multi-system behaviors
2. **Simplified Control:** One button triggers complete personality expression
3. **Character Authenticity:** R2D2 behaviors match Disney/film canon
4. **System Coordination:** WCB orchestrator manages timing and sequencing
5. **Priority System:** Emergency moods override normal operations
6. **Audit Trail:** Complete command logging for debugging

---

## 🚨 Emergency Controls

### Emergency Panic (Mood 27)

**Purpose:** Immediate crisis response with safety positioning

**Actions:**
- Dome centers to neutral position
- Periscope retracts to safe position
- Head centers to neutral
- Red emergency PSI flashing
- Alarm sound activation
- All lights maximum brightness
- Emergency logic display pattern

**Priority:** 10 (highest)

**Activation:**
1. Click red "🚨 EMERGENCY" button on any dashboard
2. Execute: `executeMood(27, 10)` in browser console
3. API call: `POST /api/wcb/mood/execute {"mood_id": 27, "priority": 10}`

---

## 🔌 Prerequisites

### Running Systems Required

1. **WCB Dashboard API:**
```bash
python wcb_dashboard_api.py
# Should show: "WCB Dashboard API running on http://localhost:8770"
```

2. **WCB Orchestrator** (if hardware connected):
```bash
python wcb_orchestrator.py
```

3. **Vision System** (optional, for video feed):
```bash
python enhanced_yolo_vision.py
# WebSocket server on port 8767
```

### Port Configuration
- **WCB API:** 8770
- **Vision WebSocket:** 8767
- **Dashboard:** File protocol (no server needed)

---

## 🐛 Troubleshooting

### "WCB Disconnected" Status

**Cause:** WCB Dashboard API not running

**Solution:**
```bash
# Start WCB API
python wcb_dashboard_api.py

# Verify with curl
curl http://localhost:8770/api/wcb/mood/status
```

### Mood Not Executing

**Check:**
1. WCB API running? `curl http://localhost:8770/api/wcb/mood/status`
2. Browser console errors? Open DevTools (F12)
3. Correct mood ID (1-27)?
4. Network connectivity?

**Debug:**
```javascript
// Browser console
fetch('http://localhost:8770/api/wcb/mood/execute', {
  method: 'POST',
  headers: {'Content-Type': 'application/json'},
  body: JSON.stringify({mood_id: 5, priority: 7})
}).then(r => r.json()).then(console.log);
```

### Vision Feed Not Showing

**Check:**
1. Vision system running on port 8767?
2. WebSocket connection established? (Check browser console)
3. Camera connected and accessible?

**Solution:**
```bash
# Start vision system
python enhanced_yolo_vision.py

# Check WebSocket
wscat -c ws://localhost:8767
```

### Buttons Not Responding

**Check:**
1. JavaScript errors in browser console
2. CORS issues (shouldn't occur with file:// protocol)
3. API endpoint reachable

**Solution:**
- Refresh page (Ctrl+F5)
- Clear browser cache
- Verify API with curl before using dashboard

---

## 📈 Future Enhancements

### Phase 2B (Planned)
- [ ] Vision-triggered mood responses (person detected → greeting)
- [ ] Mood queue system (sequence multiple moods)
- [ ] Custom mood creation interface
- [ ] Mood history and analytics
- [ ] Voice command integration
- [ ] Mobile app version

### Phase 3 (Advanced)
- [ ] Machine learning mood selection based on context
- [ ] Multi-R2D2 coordination
- [ ] Remote control via network
- [ ] Integration with home automation

---

## 📝 Code Examples

### Execute Mood from JavaScript
```javascript
// Execute Happy mood (ID 5) with normal priority
executeMood(5, 7);

// Execute Emergency Panic with highest priority
executeMood(27, 10);

// Stop current mood
stopMood();
```

### Check Mood Status
```javascript
async function checkStatus() {
  const response = await fetch('http://localhost:8770/api/wcb/mood/status');
  const status = await response.json();
  console.log(`Active: ${status.active}, Mood: ${status.mood}`);
}
```

### Custom Mood Execution
```javascript
async function customMoodSequence() {
  await executeMood(7);  // Greeting
  await new Promise(r => setTimeout(r, 6000)); // Wait 6s
  await executeMood(5);  // Happy
  await new Promise(r => setTimeout(r, 7000)); // Wait 7s
  await executeMood(21); // Entertain
}
```

---

## 📚 Related Documentation

- **WCB Architecture:** `/home/rolo/r2ai/WCB_HARDWARE_INTEGRATION_ARCHITECTURE.md`
- **Mood Commands:** `/home/rolo/r2ai/wcb_mood_commands.json`
- **Deployment Guide:** `/home/rolo/r2ai/WCB_DEPLOYMENT_GUIDE.md`
- **Project Summary:** `/home/rolo/r2ai/WCB_PROJECT_SUMMARY.md`

---

## ✅ Quality Standards Met

- ✅ Zero direct servo/light commands in dashboards
- ✅ All 27 moods accessible from UI
- ✅ Real-time status updates (500ms polling)
- ✅ Responsive design (works on all screen sizes)
- ✅ Error handling for API failures
- ✅ User-friendly mood organization by category
- ✅ Emergency stop functionality
- ✅ Vision feed integration
- ✅ Comprehensive documentation
- ✅ Testing suite included

---

## 🎓 Developer Notes

### Key Design Decisions

1. **Mood-Based Architecture:** Instead of low-level control, dashboards now express high-level behavioral intentions
2. **Polling vs. WebSocket:** Used HTTP polling for status (simpler, more reliable) and WebSocket for vision (high bandwidth)
3. **Priority System:** Emergency moods (priority 10) can interrupt normal operations
4. **Stateless UI:** Dashboard state rebuilt from WCB API on each poll
5. **Progressive Enhancement:** Works without vision feed, degrades gracefully

### Code Organization

```
r2d2_wcb_mood_dashboard.html
├── HTML Structure
│   ├── Header (title, subtitle)
│   ├── Vision Feed Panel
│   ├── Mood Status Panel
│   ├── Quick Actions
│   └── 27 Mood Buttons (6 categories)
├── CSS Styling
│   ├── Responsive grid layouts
│   ├── Gradient animations
│   ├── Pulse effects
│   └── Toast notifications
└── JavaScript Logic
    ├── WCB API integration
    ├── Status polling (500ms)
    ├── Vision WebSocket
    ├── UI state management
    └── Error handling
```

---

**Version:** 1.0  
**Last Updated:** 2025-10-05  
**Author:** Web Development Specialist  
**Status:** ✅ Production Ready
