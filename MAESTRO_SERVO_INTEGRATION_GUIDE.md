# R2D2 Pololu Maestro Servo Integration Guide

## 🎯 Complete Integration System Overview

This comprehensive guide covers the complete R2D2 Pololu Maestro servo integration system, featuring:

- **Enhanced Maestro Controller** with auto-detection and dynamic configuration
- **Advanced Servo Dashboard** with real-time controls and monitoring
- **WebSocket Communication** for real-time updates and control
- **Safety Systems** with emergency stops and monitoring
- **Sequence Management** for complex R2D2 behaviors
- **REST API** for external integrations

## 🚀 Quick Start

### 1. Start the Complete System

```bash
cd /home/rolo/r2ai
./start_maestro_servo_system.sh
```

### 2. Access Dashboards

- **Main Dashboard**: http://localhost:8765/
- **Advanced Servo Dashboard**: http://localhost:8765/servo
- **Enhanced Dashboard**: http://localhost:8765/enhanced
- **Vision Integration**: http://localhost:8765/vision

### 3. Test the Integration

```bash
python3 test_servo_integration.py
```

## 📋 System Requirements

### Hardware
- **NVIDIA Orin Nano** (recommended) or compatible Linux system
- **Pololu Maestro Mini 12-Channel USB Servo Controller**
- USB connection between Orin Nano and Maestro
- Servos connected to Maestro channels (optional for testing)

### Software Dependencies
- **Python 3.8+** with packages:
  - `flask`, `flask-cors`
  - `websockets`, `asyncio`
  - `pyserial`, `psutil`
- **Node.js** with packages:
  - `ws`, `axios`

## 🔧 Architecture Overview

### Core Components

```
┌─────────────────────────────────────────────────────────────┐
│                    R2D2 Servo Integration                    │
├─────────────────────────────────────────────────────────────┤
│  Dashboard Server (Node.js)                                │
│  ├── HTTP Server (Port 8765)                               │
│  ├── WebSocket Server (Port 8766)                          │
│  └── Static File Serving                                   │
├─────────────────────────────────────────────────────────────┤
│  Servo Integration Service (Python)                        │
│  ├── REST API (Port 5000)                                  │
│  ├── WebSocket Server (Port 8767)                          │
│  ├── Enhanced Maestro Controller                           │
│  ├── Safety Monitoring                                     │
│  ├── Sequence Engine                                       │
│  └── Diagnostics                                           │
├─────────────────────────────────────────────────────────────┤
│  Hardware Layer                                            │
│  ├── Pololu Maestro Controller                             │
│  ├── USB Serial Communication                              │
│  └── Servo Hardware                                        │
└─────────────────────────────────────────────────────────────┘
```

### Communication Flow

```
Web Browser ←→ Dashboard Server ←→ Servo Integration ←→ Maestro Hardware
     │              │                      │                    │
   HTTP/WS      HTTP/WS/REST          Serial/USB             Servos
```

## 🔌 API Reference

### REST API Endpoints

#### Servo Control
```
GET  /api/servo/status              - Get comprehensive system status
POST /api/servo/{channel}/move      - Move servo to position
POST /api/servo/{channel}/home      - Move servo to home position
POST /api/servo/emergency_stop      - Emergency stop all servos
POST /api/servo/emergency_stop/clear - Clear emergency stop
```

#### Board Management
```
POST /api/servo/board/detect        - Detect Maestro hardware
```

#### Sequence Control
```
POST /api/servo/sequence/{name}/execute - Execute servo sequence
POST /api/servo/sequence/stop       - Stop current sequence
```

### WebSocket Messages

#### Client → Server
```json
{
  "type": "request_data"
}

{
  "type": "servo_command",
  "channel": 0,
  "position": 1500
}

{
  "type": "emergency_stop",
  "system": "servos"
}
```

#### Server → Client
```json
{
  "type": "servo_status",
  "data": {
    "controller": {...},
    "servos": {...},
    "sequences": {...}
  }
}

{
  "type": "alert",
  "message": "Emergency stop activated",
  "level": "error"
}
```

## 🎮 Dashboard Features

### Advanced Servo Dashboard

**System Status Panel**
- Controller connection status
- Hardware detection information
- Active servo count
- Emergency stop status
- System uptime

**Individual Servo Control**
- Real-time position sliders
- Home position buttons
- Enable/disable toggles
- Position feedback
- Movement indicators

**R2D2 Controls**
- Dome rotation controls
- Panel open/close buttons
- Utility arm controls
- Emergency stop button

**Sequence Management**
- Pre-built R2D2 sequences
- Sequence execution controls
- Progress monitoring
- Custom sequence creation

**System Logs**
- Real-time event logging
- Error notifications
- Performance alerts
- Safety violations

## ⚙️ Configuration

### Servo Configuration

The system automatically detects and configures servos. You can customize:

```json
{
  "channel": 0,
  "name": "dome_rotation",
  "display_name": "Dome Rotation",
  "min_position": 2000,
  "max_position": 8000,
  "home_position": 6000,
  "max_speed": 30,
  "acceleration": 15,
  "enabled": true,
  "r2d2_function": "dome_rotation"
}
```

### Safety Parameters

```json
{
  "position_deviation_threshold": 500,
  "movement_timeout": 10.0,
  "connection_timeout": 5.0,
  "max_violations": 3
}
```

## 🔒 Safety Features

### Emergency Stop System
- **Hardware Emergency Stop**: Immediately halts all servo movement
- **Software Emergency Stop**: API and dashboard controls
- **Automatic Recovery**: Clear emergency stop and resume operation

### Safety Monitoring
- **Position Limits**: Prevents servos from exceeding safe ranges
- **Movement Timeouts**: Detects stuck or unresponsive servos
- **Communication Health**: Monitors connection status
- **Violation Tracking**: Logs and responds to safety violations

### Real-time Alerts
- **WebSocket Notifications**: Instant alerts to all connected clients
- **Severity Levels**: Info, warning, error, critical
- **Automatic Actions**: Emergency stops for critical violations

## 🎬 Sequence System

### Built-in Sequences

**Dome Scan**
- Smooth dome rotation pattern
- Search behavior simulation
- Configurable speed and range

**Panel Wave**
- Sequential panel opening
- Coordinated movement timing
- Smooth transitions

**Excited Behavior**
- Quick dome movements
- Head tilt coordination
- Periscope animations

### Custom Sequences

Create sequences with keyframes:

```python
sequence = {
    "name": "custom_greeting",
    "description": "Custom R2D2 greeting",
    "keyframes": [
        {
            "channel": 0,
            "position": 1800,
            "duration": 1.0,
            "motion_type": "ease_in_out",
            "delay": 0.0
        },
        {
            "channel": 1,
            "position": 1600,
            "duration": 0.8,
            "motion_type": "smooth",
            "delay": 0.5
        }
    ]
}
```

## 📊 Monitoring and Diagnostics

### Performance Metrics
- **Command Latency**: Response time for servo commands
- **Position Accuracy**: Actual vs. target position tracking
- **Movement Smoothness**: Quality of motion transitions
- **Success Rate**: Percentage of successful operations

### System Health
- **CPU Usage**: System resource utilization
- **Memory Usage**: RAM consumption monitoring
- **Temperature**: Thermal monitoring (Orin Nano)
- **Connection Quality**: Communication reliability

### Logging
- **System Events**: All operations and status changes
- **Error Tracking**: Detailed error information
- **Performance Data**: Metrics and diagnostics
- **Safety Violations**: Security and safety events

## 🔧 Troubleshooting

### Common Issues

**Maestro Not Detected**
```bash
# Check USB connection
lsusb | grep -i pololu

# Check device permissions
ls -la /dev/ttyACM*

# Run hardware detection
python3 -c "from maestro_enhanced_controller import EnhancedMaestroController; c = EnhancedMaestroController()"
```

**Permission Errors**
```bash
# Add user to dialout group
sudo usermod -a -G dialout $USER

# Set device permissions
sudo chmod 666 /dev/ttyACM0
```

**Port Conflicts**
```bash
# Check port usage
netstat -tuln | grep -E ":(5000|8765|8766|8767) "

# Kill conflicting processes
sudo lsof -ti:5000 | xargs sudo kill -9
```

**Service Startup Issues**
```bash
# Check logs
tail -f /home/rolo/r2ai/logs/servo_integration.log
tail -f /home/rolo/r2ai/logs/dashboard_server.log

# Test components individually
python3 servo_dashboard_integration.py
node dashboard-server.js
```

### Performance Optimization

**Low Latency Mode**
- Increase monitoring frequency
- Reduce WebSocket broadcast interval
- Optimize servo update rates

**Resource Conservation**
- Reduce log verbosity
- Lower monitoring frequencies
- Disable unused features

## 🧪 Testing

### Integration Test Suite

Run comprehensive tests:
```bash
python3 test_servo_integration.py
```

Test categories:
- **API Connectivity**: REST endpoint responsiveness
- **Hardware Detection**: Maestro board discovery
- **Servo Control**: Individual servo movement
- **Emergency Systems**: Safety mechanism validation
- **WebSocket Communication**: Real-time messaging
- **Dashboard Access**: Web interface availability
- **Performance**: Response time and reliability

### Manual Testing

**Basic Servo Control**
1. Access servo dashboard: http://localhost:8765/servo
2. Move individual servos using sliders
3. Test home position buttons
4. Verify position feedback

**Emergency Stop Testing**
1. Trigger emergency stop
2. Verify all movement halts
3. Clear emergency stop
4. Resume normal operation

**Sequence Testing**
1. Execute built-in sequences
2. Monitor progress and completion
3. Test sequence interruption
4. Verify servo coordination

## 📈 Advanced Features

### Custom R2D2 Functions

**Dome Control**
```javascript
// Rotate dome to specific angle
fetch('/api/servo/0/move', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({position: 1800})
});
```

**Panel Management**
```javascript
// Open/close specific panels
const panelPositions = {
    closed: 1200,
    open: 1800
};
```

**Utility Arms**
```javascript
// Coordinate dual arm movement
Promise.all([
    moveServo(4, leftPosition),
    moveServo(5, rightPosition)
]);
```

### External Integration

**Python API Client**
```python
import requests

# Control servos from external applications
response = requests.post('http://localhost:5000/api/servo/0/move',
                        json={'position': 1500})
```

**WebSocket Client**
```javascript
const ws = new WebSocket('ws://localhost:8767');
ws.onopen = () => {
    ws.send(JSON.stringify({
        type: 'servo_command',
        channel: 0,
        position: 1500
    }));
};
```

## 🔄 System Maintenance

### Regular Tasks

**Configuration Backup**
```bash
# Backup servo configurations
cp -r /home/rolo/r2ai/servo_configs /backup/location/

# Backup sequences
cp -r /home/rolo/r2ai/servo_sequences /backup/location/
```

**Log Rotation**
```bash
# Clean old logs
find /home/rolo/r2ai/logs -name "*.log" -mtime +7 -delete

# Archive important logs
tar -czf servo_logs_$(date +%Y%m%d).tar.gz /home/rolo/r2ai/logs/
```

**Performance Monitoring**
```bash
# Check system health
python3 -c "
from servo_dashboard_integration import ServoDashboardIntegration
integration = ServoDashboardIntegration()
print('System health check completed')
"
```

### Updates and Upgrades

**Update Dependencies**
```bash
# Python packages
pip3 install --upgrade flask flask-cors websockets pyserial psutil

# Node.js packages
npm update
```

**Configuration Migration**
- Backup existing configurations
- Test new features in simulation mode
- Gradually migrate settings
- Validate functionality

## 🎯 Best Practices

### Safety Guidelines
1. **Always test in simulation mode first**
2. **Use emergency stop during development**
3. **Validate position limits before deployment**
4. **Monitor servo temperatures during operation**
5. **Implement gradual movement for heavy loads**

### Performance Optimization
1. **Batch servo commands when possible**
2. **Use appropriate motion types for smooth movement**
3. **Monitor system resources during operation**
4. **Optimize WebSocket message frequency**
5. **Cache frequently accessed configurations**

### Development Workflow
1. **Test individual components before integration**
2. **Use version control for configuration changes**
3. **Document custom sequences and behaviors**
4. **Implement comprehensive error handling**
5. **Monitor logs for performance insights**

## 📞 Support and Resources

### Documentation
- **Pololu Maestro Manual**: [Pololu Website](https://www.pololu.com/docs/0J40)
- **R2D2 Build Guides**: Community resources
- **Python asyncio**: [Official Documentation](https://docs.python.org/3/library/asyncio.html)

### Community
- **R2 Builders Club**: [astromech.net](https://astromech.net)
- **GitHub Issues**: Report bugs and feature requests
- **Discord/Forums**: Real-time community support

### Debugging Resources
- **System Logs**: `/home/rolo/r2ai/logs/`
- **Configuration Files**: `/home/rolo/r2ai/servo_configs/`
- **Sequence Files**: `/home/rolo/r2ai/servo_sequences/`
- **Test Reports**: `/home/rolo/r2ai/logs/integration_test_report.json`

---

## 🎉 Conclusion

This comprehensive R2D2 Pololu Maestro servo integration system provides:

✅ **Complete Hardware Integration** with auto-detection and configuration
✅ **Professional Web Dashboard** with real-time controls
✅ **Advanced Safety Systems** with emergency stops and monitoring
✅ **Flexible Sequence Engine** for complex R2D2 behaviors
✅ **REST API and WebSocket Support** for external integrations
✅ **Comprehensive Testing Suite** for validation and debugging
✅ **Production-Ready Architecture** with monitoring and diagnostics

The system is ready for deployment and provides a solid foundation for advanced R2D2 animatronics control.

**🤖 May the Force be with your R2D2 project!**