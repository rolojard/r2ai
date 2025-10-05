# R2D2 WCB Dashboard - Quick Start Guide

## 🚀 Get Started in 3 Minutes

### Step 1: Start WCB API (30 seconds)

```bash
# Terminal 1 - Start WCB Dashboard API
cd /home/rolo/r2ai
python wcb_dashboard_api.py

# You should see:
# "WCB Dashboard API running on http://localhost:8770"
# "API Documentation: http://localhost:8770/docs"
```

### Step 2: Run Tests (1 minute)

```bash
# Terminal 2 - Run automated tests
cd /home/rolo/r2ai
python wcb_dashboard_test.py

# Expected result:
# "✓ All critical tests passed! Dashboard ready for use."
# "Success Rate: 100.0%"
```

### Step 3: Open Dashboard (30 seconds)

```bash
# Open primary WCB mood dashboard
xdg-open /home/rolo/r2ai/r2d2_wcb_mood_dashboard.html

# Or open behavioral intelligence dashboard
xdg-open /home/rolo/r2ai/r2d2_behavioral_wcb_dashboard.html
```

### Step 4: Test Functionality (1 minute)

1. **Check connection:** Top-right corner should show "WCB Connected" (green)
2. **Execute a mood:** Click "😄 Excited Happy" button
3. **Watch feedback:** Progress bar animates, status updates in real-time
4. **Stop execution:** Click "⏹️ Stop Current Mood" button

**You're done! Dashboard is ready to use.**

---

## 🎯 Quick Mood Reference

### Most Common Moods

| Button | Mood | What It Does |
|--------|------|--------------|
| 👋 Greet | Greeting Friendly (7) | Warm welcoming wave motion |
| 😄 Happy | Excited Happy (5) | Joyful bouncing movements |
| 🛡️ Alert | Protective Alert (13) | Scanning sweep ready stance |
| 🚨 Emergency | Emergency Panic (27) | Crisis response, safe positioning |

### Mood Categories

1. **Primary Emotional (1-6):** Relaxed, Bored, Curious, Cautious, Happy, Mischievous
2. **Social (7-10):** Friendly, Shy, Affectionate, Sad
3. **Character (11-14):** Defiant, Frightened, Protective, Sassy
4. **Activity (15-20):** Scanning, Processing, Problem Solving, Success/Failed
5. **Performance (21-26):** Entertaining, Show-off, Jedi, Sith, Spy, Sleep
6. **Special (27):** Emergency Panic

---

## 🐛 Quick Troubleshooting

### "WCB Disconnected" Status

**Problem:** Dashboard shows red "WCB Disconnected"

**Solution:**
```bash
# Check if WCB API is running
curl http://localhost:8770/api/wcb/mood/status

# If not running, start it
python wcb_dashboard_api.py
```

### Mood Not Executing

**Problem:** Clicking mood button does nothing

**Solution:**
1. Open browser console (F12)
2. Look for error messages
3. Verify API is running: `curl http://localhost:8770/api/wcb/mood/status`
4. Refresh dashboard (Ctrl+F5)

### Vision Feed Not Showing

**Problem:** "Connecting to vision system..." never changes

**Solution:**
```bash
# Vision system is optional. If you want it:
python enhanced_yolo_vision.py

# Refresh dashboard to reconnect
```

---

## 📱 Browser Console Testing

Open browser DevTools (F12), then try these commands:

### Execute a Mood
```javascript
executeMood(5);  // Execute "Excited Happy"
```

### Stop Current Mood
```javascript
stopMood();
```

### Check API Status
```javascript
fetch('http://localhost:8770/api/wcb/mood/status')
  .then(r => r.json())
  .then(console.log);
```

---

## 📚 Full Documentation

- **Integration Guide:** [WCB_DASHBOARD_INTEGRATION_GUIDE.md](WCB_DASHBOARD_INTEGRATION_GUIDE.md)
- **Testing Notes:** [WCB_DASHBOARD_TESTING_NOTES.md](WCB_DASHBOARD_TESTING_NOTES.md)
- **Implementation Summary:** [WCB_DASHBOARD_IMPLEMENTATION_SUMMARY.md](WCB_DASHBOARD_IMPLEMENTATION_SUMMARY.md)

---

## ✅ Success Checklist

After starting, verify these:

- [ ] WCB API running (port 8770)
- [ ] Dashboard connection shows green
- [ ] WCB API status shows ✓
- [ ] Clicking mood button updates progress bar
- [ ] Statistics increment correctly
- [ ] Stop button halts execution

**All checked? You're ready to go!**

---

## 🎓 Next Steps

1. **Explore All Moods:** Try each of the 27 mood buttons
2. **Test Quick Actions:** Use the 4 quick-access buttons
3. **Try Behavioral Dashboard:** Open the behavioral intelligence version
4. **Read Full Guide:** Review comprehensive documentation

---

**Need Help?** Check the troubleshooting sections in the full integration guide.

**Ready for Advanced Features?** See the implementation summary for Phase 2B/3 roadmap.

---

*Quick Start Guide - Version 1.0 - 2025-10-05*
