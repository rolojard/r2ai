# WCB Dashboard API - Quick Reference Card

## Server Control

```bash
# Start server
./start_wcb_api.sh

# Or direct
python3 wcb_dashboard_api.py

# With custom port
WCB_API_PORT=8771 ./start_wcb_api.sh
```

**API Base URL:** `http://localhost:8770`
**Documentation:** `http://localhost:8770/docs`

---

## Essential API Calls

### Execute Mood
```bash
curl -X POST http://localhost:8770/api/wcb/mood/execute \
  -H "Content-Type: application/json" \
  -d '{"mood_id": 5, "priority": 7}'
```

### Stop Mood
```bash
curl -X POST http://localhost:8770/api/wcb/mood/stop
```

### Get Status
```bash
curl http://localhost:8770/api/wcb/mood/status
```

### List Moods
```bash
curl http://localhost:8770/api/wcb/mood/list
```

### Get Statistics
```bash
curl http://localhost:8770/api/wcb/stats
```

---

## Common Moods Quick Access

| Mood | ID | Command |
|------|----|----|
| Idle Relaxed | 1 | `{"mood_id": 1}` |
| Alert Curious | 3 | `{"mood_id": 3}` |
| Excited Happy | 5 | `{"mood_id": 5}` |
| Greeting Friendly | 7 | `{"mood_id": 7}` |
| Stubborn Defiant | 11 | `{"mood_id": 11}` |
| Protective Alert | 13 | `{"mood_id": 13}` |
| Scanning Methodical | 15 | `{"mood_id": 15}` |
| Jedi Respect | 23 | `{"mood_id": 23}` |
| Emergency Panic | 27 | `{"mood_id": 27}` |

---

## JavaScript One-Liner

```javascript
// Execute mood
fetch('http://localhost:8770/api/wcb/mood/execute', {
  method: 'POST',
  headers: {'Content-Type': 'application/json'},
  body: JSON.stringify({mood_id: 5, priority: 7})
}).then(r => r.json()).then(console.log);

// Get status
fetch('http://localhost:8770/api/wcb/mood/status')
  .then(r => r.json()).then(console.log);
```

---

## Python One-Liner

```python
import requests

# Execute mood
requests.post('http://localhost:8770/api/wcb/mood/execute',
  json={'mood_id': 5, 'priority': 7}).json()

# Get status
requests.get('http://localhost:8770/api/wcb/mood/status').json()
```

---

## Testing

```bash
# Run full test suite
./wcb_api_test_commands.sh

# Quick health check
curl http://localhost:8770/
```

---

## Mode Switching

### Simulation (Default)
Already configured - no changes needed

### Hardware Mode
Edit `wcb_dashboard_api.py` line ~469:
```python
simulation=False  # Change from True
```

---

## All Endpoints

| Method | Endpoint | Purpose |
|--------|----------|---------|
| GET | `/` | Health check |
| POST | `/api/wcb/mood/execute` | Execute mood |
| POST | `/api/wcb/mood/stop` | Stop mood |
| GET | `/api/wcb/mood/status` | Mood status |
| GET | `/api/wcb/mood/list` | List all moods |
| GET | `/api/wcb/stats` | Statistics |
| GET | `/api/wcb/boards/status` | Board status |

---

## Error Codes

- **200** - Success
- **400** - Invalid request
- **409** - Mood already running
- **500** - Server error
- **503** - Orchestrator unavailable

---

## Priority Levels

- **10** - Emergency (highest)
- **9** - RC Override
- **7** - Mood Control (default)
- **5** - Normal Operations
- **1** - Background Tasks (lowest)

---

**Complete Guide:** `WCB_DASHBOARD_API_GUIDE.md`
