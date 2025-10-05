# WCB Dashboard API - Complete Integration Guide

## Overview

The **WCB Dashboard API** is a production-ready FastAPI service that provides unified mood-based control for the R2D2 WCB Hardware Orchestration system. It replaces direct servo/light controls with intelligent mood orchestration across all 27 R2D2 personality states.

**Version:** 1.0.0
**Port:** 8770
**Protocol:** HTTP/REST
**Documentation:** Auto-generated OpenAPI/Swagger

---

## Quick Start

### 1. Installation

```bash
# Install dependencies
pip install fastapi uvicorn pydantic pyserial

# Or with requirements file
pip install -r requirements.txt
```

### 2. Start the Server

```bash
# Using startup script (recommended)
./start_wcb_api.sh

# Or directly with Python
python3 wcb_dashboard_api.py

# Or with uvicorn
uvicorn wcb_dashboard_api:app --host 0.0.0.0 --port 8770
```

### 3. Verify Installation

```bash
# Health check
curl http://localhost:8770/

# View API documentation
open http://localhost:8770/docs
```

---

## API Endpoints Reference

### Health & Status

#### `GET /`
**Health Check**

```bash
curl http://localhost:8770/
```

**Response:**
```json
{
  "service": "WCB Dashboard API",
  "version": "1.0.0",
  "status": "running",
  "orchestrator_connected": true,
  "timestamp": "2025-10-05T12:34:56.789"
}
```

---

### Mood Control Endpoints

#### `POST /api/wcb/mood/execute`
**Execute a specific mood**

**Request Body:**
```json
{
  "mood_id": 5,
  "mood_name": "EXCITED_HAPPY",  // optional validation
  "priority": 7                   // 1-10, default 7
}
```

**Example:**
```bash
curl -X POST http://localhost:8770/api/wcb/mood/execute \
  -H "Content-Type: application/json" \
  -d '{
    "mood_id": 5,
    "priority": 8
  }'
```

**Response:**
```json
{
  "status": "success",
  "mood": "EXCITED_HAPPY",
  "mood_id": 5,
  "commands_sent": 7,
  "execution_time_ms": 850,
  "timestamp": "2025-10-05T12:34:56.789"
}
```

**Error Responses:**
- `400` - Invalid mood ID or validation failure
- `409` - Another mood is currently executing
- `500` - Execution error
- `503` - Orchestrator not connected

---

#### `POST /api/wcb/mood/stop`
**Stop currently executing mood**

**Example:**
```bash
curl -X POST http://localhost:8770/api/wcb/mood/stop
```

**Response:**
```json
{
  "status": "stopped",
  "mood": "EXCITED_HAPPY",
  "stopped_at": "2025-10-05T12:35:00.123"
}
```

**No Active Mood:**
```json
{
  "status": "no_mood_active",
  "mood": null,
  "stopped_at": "2025-10-05T12:35:00.123"
}
```

---

#### `GET /api/wcb/mood/status`
**Get current mood execution status**

**Example:**
```bash
curl http://localhost:8770/api/wcb/mood/status
```

**Response (Active):**
```json
{
  "active": true,
  "mood": "EXCITED_HAPPY",
  "mood_id": 5,
  "progress_percent": 45,
  "commands_sent": 12,
  "started_at": "2025-10-05T12:34:00.000",
  "uptime_seconds": 3600
}
```

**Response (Inactive):**
```json
{
  "active": false,
  "mood": null,
  "mood_id": null,
  "progress_percent": 100,
  "commands_sent": 47,
  "started_at": null,
  "uptime_seconds": 3600
}
```

---

#### `GET /api/wcb/mood/list`
**List all available moods**

**Example:**
```bash
curl http://localhost:8770/api/wcb/mood/list
```

**Response:**
```json
{
  "moods": [
    {
      "id": 1,
      "name": "IDLE_RELAXED",
      "category": "Primary Emotional",
      "command_count": 4
    },
    {
      "id": 5,
      "name": "EXCITED_HAPPY",
      "category": "Primary Emotional",
      "command_count": 7
    },
    ...
  ],
  "total": 27,
  "categories": {
    "Primary Emotional": [1, 2, 3, 4, 5, 6],
    "Social Interaction": [7, 8, 9, 10],
    "Character-Specific": [11, 12, 13, 14],
    "Activity States": [15, 16, 17, 18, 19, 20],
    "Performance": [21, 22, 23, 24],
    "Special": [25, 26, 27]
  }
}
```

---

### Statistics & Hardware

#### `GET /api/wcb/stats`
**Get API usage statistics**

**Example:**
```bash
curl http://localhost:8770/api/wcb/stats
```

**Response:**
```json
{
  "moods_executed": 47,
  "total_commands_sent": 892,
  "total_commands_failed": 3,
  "average_execution_time_ms": 4235,
  "uptime_seconds": 3600,
  "current_mode": "simulation",
  "api_version": "1.0.0"
}
```

---

#### `GET /api/wcb/boards/status`
**Get WCB boards connection status**

**Example:**
```bash
curl http://localhost:8770/api/wcb/boards/status
```

**Response:**
```json
{
  "wcb1": {
    "connected": true,
    "last_command": "EXCITED_HAPPY",
    "last_update": "2025-10-05T12:34:56.789"
  },
  "wcb2": {
    "connected": true,
    "last_command": "EXCITED_HAPPY",
    "last_update": "2025-10-05T12:34:56.789"
  },
  "wcb3": {
    "connected": true,
    "last_command": "EXCITED_HAPPY",
    "last_update": "2025-10-05T12:34:56.789"
  },
  "overall_status": "connected"
}
```

---

## Complete Mood Reference (27 Moods)

### Primary Emotional (1-6)
| ID | Name | Description | Commands |
|----|------|-------------|----------|
| 1 | IDLE_RELAXED | Calm, content waiting state | 4 |
| 2 | IDLE_BORED | Restless, seeking stimulation | 5 |
| 3 | ALERT_CURIOUS | Interested investigation | 5 |
| 4 | ALERT_CAUTIOUS | Wary defensive stance | 5 |
| 5 | EXCITED_HAPPY | Joyful enthusiasm | 7 |
| 6 | EXCITED_MISCHIEVOUS | Playful troublemaking | 5 |

### Social Interaction (7-10)
| ID | Name | Description | Commands |
|----|------|-------------|----------|
| 7 | GREETING_FRIENDLY | Warm welcoming | 7 |
| 8 | GREETING_SHY | Reserved introduction | 5 |
| 9 | FAREWELL_SAD | Sad goodbye | 6 |
| 10 | FAREWELL_HOPEFUL | Hopeful farewell | 6 |

### Character-Specific (11-14)
| ID | Name | Description | Commands |
|----|------|-------------|----------|
| 11 | STUBBORN_DEFIANT | Sharp refusal | 6 |
| 12 | STUBBORN_POUTY | Sulking resistance | 6 |
| 13 | PROTECTIVE_ALERT | Scanning ready stance | 7 |
| 14 | PROTECTIVE_AGGRESSIVE | Aggressive defense | 7 |

### Activity States (15-20)
| ID | Name | Description | Commands |
|----|------|-------------|----------|
| 15 | SCANNING_METHODICAL | Systematic scanning | 5 |
| 16 | SCANNING_FRANTIC | Urgent searching | 6 |
| 17 | TRACKING_FOCUSED | Concentrated tracking | 5 |
| 18 | TRACKING_PLAYFUL | Playful following | 5 |
| 19 | DEMONSTRATING_CONFIDENT | Assured presentation | 6 |
| 20 | DEMONSTRATING_NERVOUS | Anxious demonstration | 5 |

### Performance (21-24)
| ID | Name | Description | Commands |
|----|------|-------------|----------|
| 21 | ENTERTAINING_CROWD | Big performance | 7 |
| 22 | ENTERTAINING_INTIMATE | Gentle show | 6 |
| 23 | JEDI_RESPECT | Reverent bow | 6 |
| 24 | SITH_ALERT | Defensive warning | 7 |

### Special (25-27)
| ID | Name | Description | Commands |
|----|------|-------------|----------|
| 25 | MAINTENANCE_COOPERATIVE | Service mode | 6 |
| 26 | EMERGENCY_CALM | Controlled crisis | 6 |
| 27 | EMERGENCY_PANIC | Panic response | 7 |

---

## Dashboard Integration Examples

### JavaScript/TypeScript Integration

```javascript
class WCBDashboardClient {
  constructor(apiUrl = 'http://localhost:8770') {
    this.apiUrl = apiUrl;
  }

  async executeMood(moodId, priority = 7) {
    const response = await fetch(`${this.apiUrl}/api/wcb/mood/execute`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ mood_id: moodId, priority })
    });
    return response.json();
  }

  async getMoodStatus() {
    const response = await fetch(`${this.apiUrl}/api/wcb/mood/status`);
    return response.json();
  }

  async listMoods() {
    const response = await fetch(`${this.apiUrl}/api/wcb/mood/list`);
    return response.json();
  }

  async stopMood() {
    const response = await fetch(`${this.apiUrl}/api/wcb/mood/stop`, {
      method: 'POST'
    });
    return response.json();
  }
}

// Usage
const wcb = new WCBDashboardClient();

// Execute excited happy mood
await wcb.executeMood(5, 8);

// Get current status
const status = await wcb.getMoodStatus();
console.log('Active:', status.active);
```

### Python Integration

```python
import requests

class WCBDashboardClient:
    def __init__(self, api_url='http://localhost:8770'):
        self.api_url = api_url

    def execute_mood(self, mood_id, priority=7):
        response = requests.post(
            f'{self.api_url}/api/wcb/mood/execute',
            json={'mood_id': mood_id, 'priority': priority}
        )
        return response.json()

    def get_mood_status(self):
        response = requests.get(f'{self.api_url}/api/wcb/mood/status')
        return response.json()

    def list_moods(self):
        response = requests.get(f'{self.api_url}/api/wcb/mood/list')
        return response.json()

    def stop_mood(self):
        response = requests.post(f'{self.api_url}/api/wcb/mood/stop')
        return response.json()

# Usage
wcb = WCBDashboardClient()

# Execute mood
result = wcb.execute_mood(5, priority=8)
print(f"Executed: {result['mood']}")

# Get status
status = wcb.get_mood_status()
print(f"Active: {status['active']}")
```

---

## Configuration

### Environment Variables

```bash
# API server configuration
export WCB_API_HOST=0.0.0.0
export WCB_API_PORT=8770
export WCB_MODE=simulation  # or 'hardware'
export WCB_RELOAD=false     # true for development

# Hardware configuration
export WCB_SERIAL_PORT=/dev/ttyUSB0
export WCB_SERIAL_BAUD=9600
```

### Switching to Hardware Mode

Edit `/home/rolo/r2ai/wcb_dashboard_api.py`:

```python
# In lifespan function, change:
await manager.initialize(
    port='/dev/ttyUSB0',
    baud=9600,
    simulation=False  # Changed from True to False
)
```

Or set environment variable:
```bash
export WCB_MODE=hardware
```

---

## Testing

### Run Complete Test Suite

```bash
# Make executable
chmod +x wcb_api_test_commands.sh

# Run all tests
./wcb_api_test_commands.sh
```

### Individual Tests

```bash
# Test mood execution
curl -X POST http://localhost:8770/api/wcb/mood/execute \
  -H "Content-Type: application/json" \
  -d '{"mood_id": 5, "priority": 7}'

# Test mood list
curl http://localhost:8770/api/wcb/mood/list | jq '.total'

# Test statistics
curl http://localhost:8770/api/wcb/stats | jq '.moods_executed'
```

---

## Error Handling

### Common Errors

**409 Conflict - Mood Already Running**
```json
{
  "detail": "Another mood is currently executing. Stop it first."
}
```
**Solution:** Call `/api/wcb/mood/stop` first

**400 Bad Request - Invalid Mood ID**
```json
{
  "detail": "Invalid mood_id: 99. Must be 1-27."
}
```
**Solution:** Use mood ID 1-27

**503 Service Unavailable - Orchestrator Not Connected**
```json
{
  "detail": "WCB orchestrator not connected"
}
```
**Solution:** Check hardware connection or simulation mode

---

## Performance & Optimization

### Expected Performance
- **Mood Execution:** 500-5000ms (depending on mood complexity)
- **Status Queries:** <10ms
- **Mood List:** <50ms
- **Statistics:** <10ms

### Concurrent Requests
- Only one mood can execute at a time (thread-safe)
- Status/list queries can run concurrently
- Proper locking prevents race conditions

---

## Logging

### View Logs

```bash
# Server logs show:
# - Mood executions
# - Command transmission
# - Errors and warnings
# - Performance metrics

# Example output:
# 2025-10-05 12:34:56 - INFO - Starting mood execution: EXCITED_HAPPY (ID: 5, Priority: 8)
# 2025-10-05 12:34:56 - INFO - [Maestro] ';M12\r' - Arms wave
# 2025-10-05 12:34:56 - INFO - Mood EXCITED_HAPPY executed successfully in 850ms
```

---

## Production Deployment

### SystemD Service (Recommended)

Create `/etc/systemd/system/wcb-api.service`:

```ini
[Unit]
Description=WCB Dashboard API Service
After=network.target

[Service]
Type=simple
User=rolo
WorkingDirectory=/home/rolo/r2ai
ExecStart=/usr/bin/python3 /home/rolo/r2ai/wcb_dashboard_api.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl enable wcb-api
sudo systemctl start wcb-api
sudo systemctl status wcb-api
```

### Docker Deployment

```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY wcb_*.py .
EXPOSE 8770

CMD ["python3", "wcb_dashboard_api.py"]
```

---

## Security Considerations

### Production Checklist
- [ ] Configure CORS allowed origins (not `*`)
- [ ] Add authentication/authorization
- [ ] Use HTTPS/TLS
- [ ] Rate limiting
- [ ] Input validation
- [ ] Logging sanitization
- [ ] Network isolation

---

## Troubleshooting

### Server Won't Start
```bash
# Check if port is in use
lsof -i :8770

# Check dependencies
python3 -c "import fastapi, uvicorn, pydantic"
```

### Moods Not Executing
```bash
# Check orchestrator connection
curl http://localhost:8770/api/wcb/boards/status

# Check logs for errors
# Review serial port permissions (hardware mode)
```

### Slow Performance
```bash
# Check system resources
# Review mood execution times in stats
curl http://localhost:8770/api/wcb/stats | jq '.average_execution_time_ms'
```

---

## API Documentation

**Interactive API Docs:** http://localhost:8770/docs
**ReDoc:** http://localhost:8770/redoc
**OpenAPI Schema:** http://localhost:8770/openapi.json

---

## Support & Development

**Repository:** /home/rolo/r2ai
**Main Files:**
- `wcb_dashboard_api.py` - FastAPI service
- `wcb_hardware_orchestrator.py` - Orchestration engine
- `wcb_hardware_commands.py` - Command library
- `wcb_mood_commands.json` - Mood definitions

**Testing:**
- `wcb_api_test_commands.sh` - Complete test suite
- `start_wcb_api.sh` - Startup script

---

## Changelog

### Version 1.0.0 (2025-10-05)
- Initial production release
- 27 R2D2 moods fully integrated
- Complete REST API
- Async mood execution
- Statistics tracking
- Thread-safe operations
- Comprehensive error handling
- Auto-generated documentation

---

**Ready for Production Use** ✓
