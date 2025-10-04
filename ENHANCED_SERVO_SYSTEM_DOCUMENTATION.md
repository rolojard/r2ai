# R2D2 Enhanced Servo Control System
## Production-Ready Backend Documentation

### 🎯 Overview

The R2D2 Enhanced Servo Control System is a comprehensive, production-ready backend solution for controlling Pololu Maestro servo controllers in R2D2 robotic systems. This advanced system provides:

- **Hardware Auto-Detection**: Automatic detection and configuration of Pololu Maestro boards
- **Advanced Motion Control**: Smooth interpolation with multiple easing functions
- **Sequence Management**: Create, save, and execute complex servo choreography
- **Safety Systems**: Real-time monitoring with emergency stops and violation tracking
- **Real-time APIs**: WebSocket and REST APIs for dashboard integration
- **Comprehensive Diagnostics**: System health monitoring and performance tracking
- **Configuration Management**: Dynamic servo configuration with validation

### 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Dashboard Layer                         │
├─────────────────────────────────────────────────────────────┤
│  Web Dashboard  │  REST API  │  WebSocket API  │  Mobile    │
├─────────────────────────────────────────────────────────────┤
│                    Enhanced Backend                         │
├─────────────────────────────────────────────────────────────┤
│ ServoControlBackend (Main Orchestrator)                    │
│ ├── EnhancedMaestroController (Hardware Interface)        │
│ ├── ConfigurationManager (Board Detection & Config)       │
│ ├── SequenceEngine (Advanced Motion & Choreography)       │
│ ├── SafetyMonitor (Real-time Safety & Emergency)          │
│ ├── DiagnosticsEngine (Health & Performance Monitoring)   │
│ └── WebSocketHandler (Real-time Communication)            │
├─────────────────────────────────────────────────────────────┤
│                    Hardware Layer                          │
├─────────────────────────────────────────────────────────────┤
│        Pololu Maestro Mini 12-Channel Controllers          │
└─────────────────────────────────────────────────────────────┘
```

### 🚀 Quick Start

#### 1. Install Dependencies

```bash
# Python dependencies
pip3 install fastapi uvicorn websockets pyserial psutil

# Node.js dependencies (for dashboard)
npm install ws axios
```

#### 2. Start the Complete System

```bash
# Make startup script executable
chmod +x start_enhanced_servo_system.sh

# Start all services
./start_enhanced_servo_system.sh
```

#### 3. Access the System

- **REST API**: http://localhost:5000
- **API Documentation**: http://localhost:5000/docs
- **Dashboard**: http://localhost:8765
- **Advanced Servo Dashboard**: http://localhost:8765/servo
- **WebSocket**: ws://localhost:8767

### 📋 Key Features

#### Hardware Auto-Detection
- Automatically detects connected Pololu Maestro boards
- Identifies board type, firmware version, and channel count
- Imports servo limits and configuration from hardware
- Supports hot-plugging with auto-reconnection

#### Advanced Motion Control
- **Linear**: Direct position changes
- **Ease In/Out**: Smooth acceleration and deceleration
- **Bounce**: Spring-like bouncing motion
- **Elastic**: Elastic overshoot and settle
- **Custom Duration**: Precise timing control
- **50Hz Update Rate**: Ultra-smooth motion

#### Sequence Management
- Create complex multi-servo choreography
- Save and load sequences with metadata
- Real-time sequence execution monitoring
- Loop support with configurable repeat counts
- Keyframe-based animation system

#### Safety Systems
- Real-time position monitoring
- Movement timeout detection
- Position deviation alerts
- Emergency stop with immediate response
- Violation history and tracking
- Configurable safety thresholds

#### Diagnostics & Monitoring
- Real-time system health monitoring
- Performance metrics tracking
- CPU, memory, and temperature monitoring
- Command latency measurement
- Success rate tracking
- Alert system for critical conditions

#### Communication APIs
- **WebSocket**: Real-time bidirectional communication
- **REST API**: Complete RESTful interface
- **Auto-documentation**: Interactive API docs
- **CORS Support**: Cross-origin resource sharing
- **Error Handling**: Comprehensive error responses

### 🔧 API Reference

#### REST API Endpoints

##### System Status
- `GET /health` - System health check
- `GET /api/servo/status` - Comprehensive system status
- `GET /api/servo/controller` - Controller hardware status

##### Servo Control
- `POST /api/servo/{channel}/move` - Move servo with motion type
- `POST /api/servo/{channel}/home` - Move servo to home position
- `GET /api/servo/{channel}/status` - Get individual servo status

##### Sequence Management
- `GET /api/sequences` - List all sequences
- `POST /api/sequences` - Create new sequence
- `POST /api/sequences/{id}/execute` - Execute sequence
- `POST /api/sequences/{id}/stop` - Stop sequence

##### Safety Controls
- `POST /api/emergency_stop` - Trigger emergency stop
- `POST /api/safety/clear_emergency` - Clear emergency condition
- `GET /api/safety/status` - Get safety system status
- `POST /api/safety/parameters` - Update safety parameters

##### Diagnostics
- `GET /api/diagnostics` - Get performance metrics
- `GET /api/diagnostics/hardware` - Get hardware diagnostics

#### WebSocket Messages

##### Incoming Messages
```json
{
  "type": "servo_command",
  "channel": 0,
  "command": "position",
  "value": 1500
}

{
  "type": "sequence_command",
  "action": "execute",
  "sequence_id": "greeting_sequence"
}

{
  "type": "emergency_stop"
}
```

##### Outgoing Messages
```json
{
  "type": "servo_status",
  "timestamp": 1234567890,
  "controller": {...},
  "servos": {...}
}

{
  "type": "alert",
  "message": "Emergency stop activated",
  "level": "error"
}
```

### 🔒 Safety Features

#### Emergency Stop System
- Immediate servo movement halt
- Automatic violation tracking
- Recovery procedures
- System-wide emergency broadcasts

#### Real-time Monitoring
- Position accuracy verification
- Movement timeout detection
- Communication health checks
- Hardware error monitoring

#### Violation Management
- Categorized violation types
- Severity-based responses
- Historical violation tracking
- Automatic resolution marking

### 📊 Diagnostics & Monitoring

#### Performance Metrics
- Command latency tracking
- Position accuracy measurement
- Movement smoothness analysis
- Success rate monitoring

#### System Health
- CPU usage monitoring
- Memory consumption tracking
- Temperature monitoring (Orin Nano)
- Service status verification

#### Alert Thresholds
- Configurable warning levels
- Automatic alert generation
- Real-time dashboard notifications
- Log file integration

### ⚙️ Configuration

#### Servo Configuration
```python
# Dynamic servo configuration
controller.create_dynamic_servo_config(
    channel=0,
    name="dome_rotation",
    display_name="Dome Rotation",
    min_position=1000,   # 250µs
    max_position=8000,   # 2000µs
    home_position=6000,  # 1500µs
    max_speed=50,
    acceleration=20
)
```

#### Safety Parameters
```python
# Configure safety monitoring
safety_monitor.set_safety_parameters(
    position_deviation_threshold=500,  # Quarter-microseconds
    movement_timeout=10.0,             # Seconds
    connection_timeout=5.0,            # Seconds
    max_violations=3                   # Count
)
```

#### Motion Types
```python
# Available motion types
motion_types = [
    "linear",      # Direct movement
    "ease_in",     # Slow start, fast end
    "ease_out",    # Fast start, slow end
    "ease_in_out", # Slow start/end, fast middle
    "bounce",      # Bouncing motion
    "elastic"      # Elastic overshoot
]
```

### 🗂️ File Structure

```
r2ai/
├── r2d2_servo_backend.py           # Enhanced servo backend
├── r2d2_servo_api_server.py        # REST API server
├── maestro_enhanced_controller.py   # Enhanced hardware controller
├── pololu_maestro_controller.py     # Base hardware controller
├── dashboard-server.js              # Dashboard web server
├── r2d2_advanced_servo_dashboard.html # Advanced web dashboard
├── start_enhanced_servo_system.sh   # System startup script
├── demo_enhanced_servo_system.py    # Comprehensive demo
├── config/                          # Configuration files
│   ├── servo_config.json           # Servo configurations
│   └── servo_sequences.json        # Saved sequences
└── logs/                           # System logs
    ├── servo_api.log               # API server logs
    └── dashboard.log               # Dashboard logs
```

### 🧪 Testing

#### Run Comprehensive Demo
```bash
python3 demo_enhanced_servo_system.py
```

#### Manual Testing
```bash
# Test API endpoints
curl http://localhost:5000/health
curl http://localhost:5000/api/servo/status

# Test servo movement
curl -X POST http://localhost:5000/api/servo/0/move \
  -H "Content-Type: application/json" \
  -d '{"position": 1500, "duration": 2.0, "motion_type": "ease_in_out"}'

# Test emergency stop
curl -X POST http://localhost:5000/api/emergency_stop
```

#### WebSocket Testing
```javascript
const ws = new WebSocket('ws://localhost:8767');
ws.onopen = () => {
  ws.send(JSON.stringify({type: 'status_request'}));
};
ws.onmessage = (event) => {
  console.log('Status:', JSON.parse(event.data));
};
```

### 🔧 Troubleshooting

#### Common Issues

1. **Hardware Not Detected**
   - Check USB connection
   - Verify Maestro device permissions
   - Run `lsusb` to confirm device recognition
   - Check `/dev/ttyACM*` device files

2. **Port Already in Use**
   - Kill existing processes: `pkill -f servo_api`
   - Check port usage: `netstat -tulpn | grep :5000`
   - Use different ports in configuration

3. **Permission Denied**
   - Add user to dialout group: `sudo usermod -a -G dialout $USER`
   - Set device permissions: `sudo chmod 666 /dev/ttyACM0`
   - Logout and login again

4. **WebSocket Connection Failed**
   - Verify backend is running
   - Check firewall settings
   - Confirm WebSocket port (8767) is available

#### Debug Mode
```bash
# Enable debug logging
export SERVO_DEBUG=1
python3 r2d2_servo_api_server.py
```

#### Log Analysis
```bash
# Monitor real-time logs
tail -f logs/servo_api.log
tail -f logs/dashboard.log

# Check for errors
grep "ERROR" logs/*.log
```

### 📈 Performance Optimization

#### System Configuration
- Use dedicated USB ports for Maestro boards
- Enable real-time kernel for better timing
- Configure CPU governor for performance
- Optimize system swappiness

#### Code Optimization
- Adjust motion update rates based on requirements
- Configure appropriate safety monitoring intervals
- Optimize sequence execution timing
- Use connection pooling for high-frequency operations

### 🛡️ Security Considerations

#### API Security
- Implement authentication for production use
- Configure CORS origins appropriately
- Use HTTPS in production environments
- Implement rate limiting

#### System Security
- Run services with minimal privileges
- Secure configuration files
- Monitor system access logs
- Implement emergency stop accessibility

### 📝 Development

#### Adding New Features
1. Extend the appropriate backend class
2. Add corresponding API endpoints
3. Update WebSocket message handlers
4. Add dashboard integration
5. Update documentation

#### Custom Motion Types
```python
def custom_easing_function(t: float) -> float:
    """Custom easing function"""
    # Implement your easing curve
    return your_custom_curve(t)

# Register in SequenceEngine._apply_motion_easing()
```

#### Custom Safety Checks
```python
def custom_safety_check(self):
    """Custom safety monitoring"""
    # Implement your safety logic
    if violation_detected:
        self._handle_safety_violation(
            violation_type="custom_check",
            channel=channel,
            severity="high",
            description="Custom violation detected"
        )
```

### 📞 Support

For issues, feature requests, or contributions:

1. Check the troubleshooting section
2. Review system logs in `logs/` directory
3. Test with the comprehensive demo script
4. Verify hardware connections and permissions

### 🎉 Conclusion

The R2D2 Enhanced Servo Control System provides a complete, production-ready solution for advanced servo control in robotic applications. With comprehensive safety systems, real-time monitoring, and flexible APIs, it's designed to support both hobbyist and professional R2D2 builds.

The system is ready for immediate deployment and can be extended for custom requirements while maintaining safety and reliability standards.