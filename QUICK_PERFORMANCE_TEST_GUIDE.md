# Quick Performance Testing Guide

## 🚀 Quick Start Testing

### 1. Start the Dashboard
```bash
cd /home/rolo/r2ai
node dashboard-server.js
```

Open browser: `http://localhost:8765/`

### 2. Check Performance Monitor

Look for the new **Performance Monitor** section below the video feed:

**6 Metrics to Watch:**
- ✅ **Actual FPS**: Should show ~15 FPS (green)
- ✅ **Frame Variance**: Should be <10% (green)
- ✅ **WS Latency**: Should be <50ms (green)
- ✅ **Message Queue**: Should be 0-2 (green)
- ✅ **Dropped Frames**: Should be minimal
- ✅ **Target FPS**: Shows current adaptive target

**Health Indicator:** Green pulse = healthy, Yellow = degraded, Red = disconnected

---

## ⚡ 5-Minute Quick Test

### Test 1: Baseline (2 minutes)
1. Open dashboard
2. Wait for "Vision Connected"
3. Observe metrics for 60 seconds
4. **Expected**: All green, variance <10%

### Test 2: Connection Recovery (2 minutes)
1. Stop server (Ctrl+C)
2. Watch reconnection attempts in console
3. Restart server
4. **Expected**: Automatic reconnection with exponential backoff

### Test 3: Performance Under Load (1 minute)
```bash
# Open multiple tabs with the dashboard
```
**Expected**: Each tab shows independent metrics, all remain green

---

## 🎯 Success Criteria

### ✅ Passing Tests
- Frame variance consistently <10%
- WebSocket health indicator is green
- No JavaScript errors in console
- Automatic reconnection works
- Adaptive FPS adjusts under load

### ❌ Failing Tests
- Frame variance >15% for extended periods
- Frequent disconnections
- Message queue consistently >7
- Browser freezing or stuttering
- JavaScript errors in console

---

## 🔍 Browser Console Commands

### Check Current Performance
```javascript
// View all metrics at once
{
    fps: document.getElementById('actualFps').textContent,
    variance: document.getElementById('frameVariance').textContent,
    latency: document.getElementById('wsLatency').textContent,
    queue: document.getElementById('msgQueue').textContent,
    dropped: document.getElementById('droppedFrames').textContent
}
```

### Check WebSocket Status
```javascript
// Vision WebSocket (1 = connected)
DashboardState.visionWs.readyState

// Current adaptive FPS
DashboardState.adaptiveFrameRate.currentFPS
```

### Reset Performance Metrics
```javascript
PerformanceMonitor.reset();
```

---

## 🐛 Quick Troubleshooting

### Problem: High Frame Variance (>15%)
**Quick Fix:**
1. Close other browser tabs
2. Check system load: `top`
3. Let adaptive FPS reduce target
4. Wait 30 seconds for stabilization

### Problem: Can't Connect
**Quick Fix:**
1. Verify server is running: `ps aux | grep node`
2. Check port 8766: `netstat -an | grep 8766`
3. Check browser console for errors
4. Try hard refresh: Ctrl+Shift+R

### Problem: Red Health Indicator
**Quick Fix:**
1. Check connection status at top-right
2. Wait for automatic reconnection
3. Verify server is running
4. Check network connectivity

---

## 📊 Expected Performance

### Normal Operation
```
Actual FPS:      14.5-15.5 (green)
Frame Variance:  5-8%      (green)
WS Latency:      10-40ms   (green)
Message Queue:   0-2       (green)
Dropped Frames:  <10/min   (green)
Target FPS:      15.0      (stable)
```

### Under Load
```
Actual FPS:      8-12      (yellow/green)
Frame Variance:  10-14%    (yellow)
WS Latency:      40-80ms   (yellow)
Message Queue:   2-5       (yellow)
Dropped Frames:  10-30/min (yellow)
Target FPS:      8-12      (adapting)
```

### Degraded/Recovering
```
Actual FPS:      5-8       (yellow/red)
Frame Variance:  15-20%    (red)
WS Latency:      80-150ms  (red)
Message Queue:   5-10      (red)
Dropped Frames:  30+/min   (red)
Target FPS:      5-8       (adapting down)
```

---

## ✅ Test Checklist

- [ ] Dashboard loads without errors
- [ ] Performance Monitor section is visible
- [ ] All 6 metrics display values (not "--")
- [ ] WebSocket health indicator shows green pulse
- [ ] Frame variance is <10% during normal operation
- [ ] Actual FPS matches target FPS (±10%)
- [ ] Reconnection works after server restart
- [ ] Metrics update in real-time
- [ ] No JavaScript errors in console
- [ ] Browser doesn't freeze or stutter

---

## 🎓 Understanding the Metrics

### Actual FPS
- **What**: Frames displayed per second
- **Good**: Close to target FPS
- **Bad**: Significantly below target

### Frame Variance
- **What**: Consistency of frame timing (lower = better)
- **Good**: <10% (smooth, consistent)
- **Bad**: >15% (jittery, inconsistent)

### WS Latency
- **What**: Time from message receipt to processing
- **Good**: <50ms (imperceptible)
- **Bad**: >100ms (noticeable lag)

### Message Queue
- **What**: Backlog of unprocessed messages
- **Good**: 0-2 (real-time processing)
- **Bad**: >7 (system struggling)

### Dropped Frames
- **What**: Frames skipped to maintain performance
- **Good**: Minimal (<10 in first minute)
- **Bad**: Rapidly increasing

### Target FPS
- **What**: Current adaptive frame rate goal
- **Good**: Stable at 15 FPS
- **Note**: Will decrease under load (this is normal!)

---

## 📞 Quick Reference

**Dashboard URL**: http://localhost:8765/
**WebSocket Port**: 8766
**Performance Section**: Below video feed
**Browser Console**: F12 → Console tab

**Key Performance Indicators:**
- Green metrics = healthy
- Yellow metrics = warning
- Red metrics = critical
- Pulse indicator = WebSocket health

**Test Duration**: 2-5 minutes for quick validation
**Full Test**: 30-60 minutes for comprehensive testing

---

**Ready to Test!** 🚀

Open the dashboard and look for the new Performance Monitor section.
All metrics should be green under normal conditions.
