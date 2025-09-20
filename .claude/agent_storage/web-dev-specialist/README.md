# R2D2 Multi-Agent Monitoring Dashboard

A comprehensive web-based monitoring and control system for the R2D2 multi-agent architecture, providing real-time visibility and control across all agent specialties.

## Features

### Multi-Agent Monitoring
- **Project Manager**: System health, agent status, performance overview
- **QA Tester**: Test results, quality metrics, validation status
- **Imagineer**: Servo controls, motion visualization, animation sequences
- **Video Model Trainer**: Camera feeds, detection accuracy, model performance
- **Star Wars Expert**: Character authenticity, interaction quality, canon compliance
- **Super Coder**: System performance, optimization metrics, error logs
- **UX Designer**: User interaction analysis, accessibility metrics, UI responsiveness
- **NVIDIA Specialist**: GPU monitoring, thermal management, power optimization

### Real-Time Communication
- WebSocket-based real-time updates
- Live system metrics and performance data
- Interactive controls and command execution
- Alert system for critical events

### Responsive Design
- Mobile-optimized interface for convention monitoring
- Tablet and desktop layouts
- Touch-friendly controls
- Dark theme optimized for low-light environments

### System Integration
- Direct integration with existing R2D2 hardware systems
- Camera feed integration with computer vision
- Screenshot capabilities for documentation
- System optimization and control interfaces

## Quick Start

### Prerequisites
```bash
# Install Python dependencies
pip install websockets psutil opencv-python numpy

# Install system dependencies (Ubuntu/Debian)
sudo apt-get install scrot i2c-tools
```

### Launch Dashboard
```bash
# Navigate to dashboard directory
cd /home/rolo/r2ai/.claude/agent_storage/web-dev-specialist/

# Launch the complete dashboard system
python3 launch_dashboard.py

# Or with custom configuration
python3 launch_dashboard.py --config dashboard_config.json
```

### Access Dashboard
- **Web Interface**: http://localhost:8080/r2d2_agent_dashboard.html
- **WebSocket**: ws://localhost:8765
- **Mobile Access**: Use your device's IP address instead of localhost

## Architecture

### Components

#### Frontend (Web Dashboard)
- **HTML**: Semantic, accessible dashboard structure
- **CSS**: Responsive design with CSS Grid and Flexbox
- **JavaScript**: Real-time WebSocket communication and interactive controls

#### Backend Services
- **WebSocket Server**: Real-time communication hub (`websocket_server.py`)
- **System Monitor**: Hardware integration and monitoring (`r2d2_system_monitor.py`)
- **HTTP Server**: Static file serving for dashboard assets

#### Integration Layer
- **R2D2 Component Integration**: Direct interface with existing hardware systems
- **Camera System**: Live video feeds with computer vision integration
- **Performance Monitoring**: Real-time system metrics and optimization

### File Structure
```
web-dev-specialist/
├── r2d2_agent_dashboard.html    # Main dashboard interface
├── dashboard_styles.css         # Responsive styling
├── dashboard_script.js          # Real-time communication logic
├── websocket_server.py          # WebSocket communication server
├── r2d2_system_monitor.py       # Hardware integration and monitoring
├── launch_dashboard.py          # System launcher and orchestrator
├── dashboard_architecture.json  # System architecture documentation
└── README.md                    # This file
```

## Agent Panel Details

### Project Manager Dashboard
- System health indicators with color-coded status
- Real-time performance charts (CPU, Memory, GPU)
- Alert center with categorized notifications
- Overall agent status grid

### QA Tester Dashboard
- Test execution controls and results display
- Quality score visualization with progress indicators
- Validation status checklist for different system components
- Real-time test logs with filterable entries

### Imagineer Motion Control
- 16-channel servo status grid with individual indicators
- Motion visualization canvas showing real-time servo positions
- Animation queue management with priority controls
- Preset motion triggers (Happy, Sad, Excited, Curious)

### Video Model Trainer
- Live camera feed with detection overlays
- Real-time accuracy and performance metrics
- Object detection log with confidence scores
- Frame rate monitoring and optimization controls

### Star Wars Expert
- Character authenticity scoring with detailed breakdown
- Interaction quality metrics (voice, movement, timing)
- Canon compliance checklist with validation status
- Guest interaction log with sentiment analysis

### Super Coder Performance
- Real-time system performance bars (CPU, Memory, GPU)
- Optimization status with component-specific indicators
- System log viewer with syntax highlighting
- Performance optimization controls

### UX Designer Interface
- User interaction heatmap visualization
- Accessibility scoring with WCAG compliance metrics
- UI responsiveness metrics (load time, first paint, interactive)
- Design system status and component library health

### NVIDIA Specialist Hardware
- GPU utilization with circular progress indicators
- Thermal monitoring with temperature charts
- Power consumption metrics and efficiency tracking
- Hardware optimization controls (power mode, thermal targets)

## Configuration

### Dashboard Configuration
```json
{
  "websocket_server": {
    "host": "0.0.0.0",
    "port": 8765,
    "auto_start": true
  },
  "web_server": {
    "host": "0.0.0.0",
    "port": 8080,
    "auto_start": true,
    "open_browser": true
  },
  "system_monitor": {
    "auto_start": true,
    "monitoring_interval": 5
  },
  "dashboard": {
    "title": "R2D2 Multi-Agent Dashboard",
    "theme": "dark",
    "auto_refresh": true,
    "refresh_interval": 5000
  }
}
```

### Responsive Breakpoints
- **Mobile**: 320px - 767px (Single column, touch-optimized)
- **Tablet**: 768px - 1023px (Dual column, gesture-friendly)
- **Desktop**: 1024px+ (Multi-column, mouse-optimized)

## WebSocket API

### Message Types

#### Client to Server
```javascript
// Request agent data
{
  "type": "request_data",
  "agent": "project_manager"
}

// Trigger motion
{
  "type": "trigger_motion",
  "motion": "happy"
}

// Take screenshot
{
  "type": "take_screenshot"
}

// Run tests
{
  "type": "run_tests"
}
```

#### Server to Client
```javascript
// System metrics update
{
  "type": "system_update",
  "metrics": {
    "cpu": 65.2,
    "memory": 42.1,
    "temperature": 58.3,
    "systemHealth": 98
  }
}

// Agent-specific data
{
  "type": "agent_data",
  "agent": "qa_tester",
  "data": {
    "testResults": {"passed": 127, "failed": 3},
    "qualityScore": 96.2
  }
}

// Alert notification
{
  "type": "alert",
  "level": "success",
  "message": "All systems operational"
}
```

## Hardware Integration

### Supported Systems
- **Servo Controllers**: 16-channel PCA9685-based servo control
- **Camera Systems**: USB cameras with OpenCV integration
- **I2C Devices**: Automatic detection and status monitoring
- **Audio Systems**: ALSA-based audio device monitoring
- **NVIDIA Hardware**: GPU monitoring and optimization

### R2D2 Component Integration
The dashboard automatically detects and integrates with existing R2D2 components:
- `r2d2_component_tester.py` - Comprehensive hardware testing
- `orin_nano_r2d2_optimizer.py` - NVIDIA Orin Nano optimization
- `servo_functionality_test.py` - Servo system validation
- `r2d2_basic_tester.py` - Basic system functionality tests
- `r2d2_security_validator.py` - Security and safety validation

## Performance Optimization

### Frontend Optimization
- CSS variables for efficient theming
- Hardware-accelerated animations
- Lazy loading for non-critical components
- Efficient WebSocket message handling

### Backend Optimization
- Asynchronous WebSocket handling
- Efficient system monitoring with configurable intervals
- Memory-optimized data structures
- Connection pooling and management

### Mobile Optimization
- Touch-optimized interface controls
- Reduced data transfer for mobile connections
- Adaptive refresh rates based on device capabilities
- Offline-capable design patterns

## Security Considerations

### Network Security
- WebSocket origin validation
- Configurable host restrictions
- Optional authentication layer
- Secure communication protocols

### System Security
- Sandboxed command execution
- Input validation and sanitization
- Rate limiting for control commands
- Audit logging for all interactions

## Troubleshooting

### Common Issues

#### Dashboard Not Loading
```bash
# Check if servers are running
ps aux | grep -E "(websocket_server|web_server)"

# Check port availability
netstat -tulpn | grep -E "(8080|8765)"

# Restart dashboard
python3 launch_dashboard.py
```

#### WebSocket Connection Failed
```bash
# Check WebSocket server logs
python3 websocket_server.py

# Test WebSocket connection
curl -i -N -H "Connection: Upgrade" -H "Upgrade: websocket" -H "Sec-WebSocket-Key: test" -H "Sec-WebSocket-Version: 13" http://localhost:8765/
```

#### Camera Feed Not Working
```bash
# Check camera devices
ls /dev/video*

# Test camera with OpenCV
python3 -c "import cv2; cap = cv2.VideoCapture(0); print('Camera working' if cap.isOpened() else 'Camera not available')"
```

### Performance Issues
- Reduce monitoring intervals in configuration
- Disable non-essential agent panels
- Check system resource usage with `htop`
- Optimize WebSocket message frequency

## Development

### Adding New Agent Panels
1. Add agent configuration to `dashboard_architecture.json`
2. Create HTML panel structure in `r2d2_agent_dashboard.html`
3. Add CSS styling in `dashboard_styles.css`
4. Implement JavaScript handlers in `dashboard_script.js`
5. Add WebSocket message handling in `websocket_server.py`

### Customizing Visualizations
- Modify CSS variables for theming
- Add new chart types in JavaScript
- Extend WebSocket message types
- Create custom monitoring widgets

### Integration with External Systems
- Extend `r2d2_system_monitor.py` for new hardware
- Add new WebSocket message types
- Create custom data collection modules
- Implement additional security measures

## License

This dashboard is part of the R2D2 multi-agent system and is designed for educational and development purposes. All Star Wars references are used under fair use for educational demonstration.

## Support

For technical support or feature requests, consult with the Super Coder agent or review the system logs for detailed error information.

---

**Generated with Claude Code** - R2D2 Multi-Agent Dashboard v2.1.0