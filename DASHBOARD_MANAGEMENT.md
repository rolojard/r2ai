# R2D2 Dashboard Management Scripts

## Overview

This suite of scripts provides safe, automated management of the R2D2 Dashboard Server, preventing common issues like port conflicts and orphaned processes.

## Available Scripts

### 1. `stop_dashboard.sh`
**Purpose:** Safely stop all running dashboard instances and free ports

**Features:**
- Gracefully terminates Node.js dashboard processes
- Frees ports 8765, 8766, 8768
- Attempts graceful shutdown (SIGTERM) before force kill (SIGKILL)
- Verifies all ports are released
- Color-coded status output

**Usage:**
```bash
./stop_dashboard.sh
```

**Exit Codes:**
- `0` - Success, all processes stopped and ports freed
- `1` - Warning, some ports still in use (manual intervention needed)

---

### 2. `start_dashboard.sh`
**Purpose:** Start dashboard server with pre-flight checks

**Features:**
- Checks for existing dashboard processes
- Verifies port availability before starting
- Validates dashboard script exists
- Checks Node.js dependencies
- Starts server in background with logging
- Provides access URLs and status

**Usage:**
```bash
./start_dashboard.sh
```

**Exit Codes:**
- `0` - Success, dashboard started
- `1` - Failure, see error message for details

**Output Log:** `/home/rolo/r2ai/dashboard.log`

---

### 3. `restart_dashboard.sh`
**Purpose:** One-command stop and restart

**Features:**
- Combines stop and start operations
- Handles cleanup between phases
- Provides consolidated status

**Usage:**
```bash
./restart_dashboard.sh
```

**Exit Codes:**
- `0` - Success, dashboard restarted
- `1` - Failure, check logs

---

### 4. `dashboard_status.sh`
**Purpose:** Comprehensive status report

**Features:**
- Shows running dashboard processes (PID, runtime, CPU, memory)
- Port status for all dashboard ports
- Log file information
- Network connectivity test
- System resource usage
- Helpful command suggestions

**Usage:**
```bash
./dashboard_status.sh
```

---

## Common Scenarios

### Scenario 1: Port Conflict (EADDRINUSE Error)

**Problem:** You try to start dashboard and get:
```
Error: listen EADDRINUSE: address already in use :::8766
```

**Solution:**
```bash
# Option 1: Stop and start separately
./stop_dashboard.sh
./start_dashboard.sh

# Option 2: One command restart
./restart_dashboard.sh
```

---

### Scenario 2: Check if Dashboard is Running

**Command:**
```bash
./dashboard_status.sh
```

**Interpretation:**
- **Green "RUNNING"** = Dashboard is active
- **Red "NOT RUNNING"** = Dashboard is stopped
- **Port IN USE** = Port is occupied (normal when running)
- **Port FREE** = Port is available

---

### Scenario 3: Dashboard Won't Stop

**Problem:** `stop_dashboard.sh` reports ports still in use

**Solution:**
```bash
# Find processes manually
lsof -i :8765 -i :8766 -i :8768

# Kill specific PID (replace XXXX with actual PID)
kill -9 XXXX

# Verify ports are free
./dashboard_status.sh
```

---

### Scenario 4: View Dashboard Logs

**Real-time monitoring:**
```bash
tail -f /home/rolo/r2ai/dashboard.log
```

**Last 50 lines:**
```bash
tail -50 /home/rolo/r2ai/dashboard.log
```

**Search for errors:**
```bash
grep -i error /home/rolo/r2ai/dashboard.log
```

---

## Port Reference

| Port | Service | Description |
|------|---------|-------------|
| 8765 | HTTP Server | Main dashboard web interface |
| 8766 | WebSocket | Real-time data updates |
| 8768 | WebSocket | Behavioral intelligence system |

---

## Dashboard URLs

After successful start, access dashboards at:

- **Default (Vision):** http://localhost:8765/
- **Enhanced Dashboard:** http://localhost:8765/enhanced
- **Servo Control:** http://localhost:8765/servo
- **Disney Behavioral:** http://localhost:8765/disney

---

## Troubleshooting

### Issue: Scripts not executable

**Error:** `Permission denied`

**Fix:**
```bash
chmod +x *.sh
```

---

### Issue: Node modules missing

**Error:** Dashboard won't start, dependency errors

**Fix:**
```bash
cd /home/rolo/r2ai
npm install
./start_dashboard.sh
```

---

### Issue: Multiple dashboard instances

**Symptom:** Multiple PIDs shown in status

**Fix:**
```bash
# Stop all instances
./stop_dashboard.sh

# Verify clean state
./dashboard_status.sh

# Start single instance
./start_dashboard.sh
```

---

### Issue: Dashboard crashes immediately

**Diagnosis:**
```bash
# Check recent logs
tail -50 /home/rolo/r2ai/dashboard.log

# Try starting manually to see errors
node /home/rolo/r2ai/dashboard-server.js
```

**Common Causes:**
- Missing dependencies (run `npm install`)
- Port conflicts (run `./stop_dashboard.sh`)
- Syntax errors in dashboard-server.js
- Missing required files

---

## Best Practices

1. **Always use scripts instead of manual `node dashboard-server.js`**
   - Scripts handle cleanup and validation
   - Logging is automatic
   - Port conflicts are detected early

2. **Check status before starting**
   ```bash
   ./dashboard_status.sh
   ./start_dashboard.sh
   ```

3. **Use restart for updates**
   ```bash
   # After editing dashboard-server.js
   ./restart_dashboard.sh
   ```

4. **Monitor logs during development**
   ```bash
   tail -f /home/rolo/r2ai/dashboard.log
   ```

5. **Clean shutdown when done**
   ```bash
   ./stop_dashboard.sh
   ```

---

## Quick Reference Card

```bash
# Start dashboard
./start_dashboard.sh

# Stop dashboard
./stop_dashboard.sh

# Restart dashboard
./restart_dashboard.sh

# Check status
./dashboard_status.sh

# View live logs
tail -f /home/rolo/r2ai/dashboard.log

# Fix port conflicts
./stop_dashboard.sh && ./start_dashboard.sh
```

---

## Script Locations

All scripts are located in: `/home/rolo/r2ai/`

- `stop_dashboard.sh`
- `start_dashboard.sh`
- `restart_dashboard.sh`
- `dashboard_status.sh`
- `dashboard.log` (created automatically)

---

## Dependencies

- **lsof** - Port checking (standard on most Linux systems)
- **Node.js** - JavaScript runtime
- **bash** - Shell interpreter (standard)
- **ps**, **pgrep**, **pkill** - Process management (standard)

---

## Safety Features

All scripts include:
- ✅ Pre-flight validation
- ✅ Graceful shutdown attempts before force kill
- ✅ Port availability verification
- ✅ Color-coded status output
- ✅ Helpful error messages
- ✅ Exit codes for scripting
- ✅ No data loss

---

## Support

For issues or questions:
1. Check logs: `tail -f /home/rolo/r2ai/dashboard.log`
2. Run status check: `./dashboard_status.sh`
3. Review this documentation
4. Check process list: `ps aux | grep dashboard`
5. Check ports: `lsof -i :8765 -i :8766 -i :8768`

---

**Last Updated:** 2025-10-05
**Version:** 1.0.0
**Author:** R2AI Project Management
