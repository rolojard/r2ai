# R2D2 AI System 🤖

A complete animatronic R2-D2 control system with advanced AI capabilities, real-time vision processing, person recognition, and web-based dashboard interface.

## 🌟 Project Overview

This is a comprehensive R2-D2 animatronic system featuring:

- **Real-time Vision Processing**: YOLO-based object and person detection
- **Person Recognition & Memory**: Face recognition with persistent memory storage
- **Web Dashboard Interface**: Real-time monitoring and control via web interface
- **Multi-Agent Architecture**: Claude-powered agent system for development and maintenance
- **Hardware Integration**: Servo control, thermal monitoring, and safety systems
- **Star Wars Canon Compliance**: Authentic R2-D2 behaviors and responses

## 🚀 Current System Status

**OPERATIONAL** - All core systems running successfully:

- ✅ Dashboard Server (Ports 8765/8766)
- ✅ Vision System with YOLO Detection (Port 8767)
- ✅ Person Recognition Pipeline
- ✅ Servo Control Systems
- ✅ Thermal & Performance Monitoring
- ✅ Safety & Security Protocols

## 🏗️ System Architecture

### Core Components

```
R2D2 AI System
├── 🌐 Web Dashboard (dashboard-server.js)
│   ├── Real-time WebSocket communication
│   ├── System monitoring interface
│   └── Vision stream integration
├── 👁️ Vision Processing Pipeline
│   ├── YOLO object detection (yolov8n.pt)
│   ├── Person recognition system
│   ├── Real-time video streaming
│   └── CUDA-optimized inference
├── 🦾 Hardware Control Layer
│   ├── Servo motor control
│   ├── Audio system integration
│   ├── Thermal monitoring
│   └── Safety protocols
├── 🧠 AI Agent System (.claude/)
│   ├── Multi-agent orchestration
│   ├── Development automation
│   ├── Quality assurance
│   └── Continuous integration
└── 🔧 Utilities & Testing
    ├── Performance monitoring
    ├── Security validation
    ├── Integration testing
    └── Backup systems
```

### Technology Stack

- **Backend**: Python 3.8+, Node.js
- **AI/ML**: YOLO v8, OpenCV, PyTorch, CUDA
- **Web**: WebSocket, HTML5, JavaScript
- **Hardware**: I2C, Serial Communication, PWM
- **Development**: Claude AI Agents, Git, Automated Testing

## 🔧 Installation & Setup

### Prerequisites

```bash
# System requirements
- NVIDIA Jetson Orin Nano (recommended) or CUDA-capable GPU
- Python 3.8+
- Node.js 16+
- Git

# Hardware (for full functionality)
- Servo motors for animatronics
- Webcam or USB camera
- Audio output system
- I2C-compatible servo controllers
```

### Quick Start

1. **Clone Repository**
   ```bash
   git clone https://github.com/YOUR_USERNAME/r2ai.git
   cd r2ai
   ```

2. **Install Python Dependencies**
   ```bash
   pip install torch torchvision opencv-python ultralytics
   pip install websocket-client flask numpy pandas
   pip install pyserial smbus2 adafruit-circuitpython-pca9685
   ```

3. **Install Node.js Dependencies**
   ```bash
   npm install
   ```

4. **Download YOLO Model**
   ```bash
   # YOLO model will be downloaded automatically on first run
   # Or manually download yolov8n.pt to project directory
   ```

5. **Start the System**
   ```bash
   # Start dashboard server
   ./start-dashboard.sh

   # Start vision system (in separate terminal)
   python3 r2d2_realtime_vision.py

   # Or use the launcher script
   ./r2ai-launcher.sh
   ```

## 🎮 Usage

### Web Dashboard Access

- **Main Dashboard**: http://localhost:8765
- **Vision Interface**: http://localhost:8766
- **Vision Stream**: http://localhost:8767

### Key Scripts

| Script | Purpose |
|--------|---------|
| `dashboard-server.js` | Main web dashboard server |
| `r2d2_realtime_vision.py` | Vision processing with YOLO |
| `r2d2_person_recognition_system.py` | Face recognition & memory |
| `r2d2_servo_controller.py` | Animatronic control |
| `start_vision_dashboard.py` | Integrated vision dashboard |
| `r2ai-launcher.sh` | System startup script |

### Person Recognition Features

- **Face Detection**: Real-time face detection and tracking
- **Person Memory**: Persistent storage of recognized individuals
- **Guest Management**: New person registration and greeting
- **Costume Recognition**: Star Wars character costume detection
- **Interaction History**: Maintains interaction logs and preferences

## 🔧 Configuration

### Hardware Configuration

Edit servo and hardware settings in:
- `r2d2_servo_controller.py` - Servo motor configuration
- `r2d2_thermal_power_manager.py` - Thermal management
- Hardware-specific configuration files in `/config/` (if applicable)

### Vision System Configuration

Adjust vision parameters in:
- `r2d2_realtime_vision.py` - YOLO detection settings
- `r2d2_person_recognition_system.py` - Face recognition parameters
- Camera settings and resolution configuration

### Web Dashboard Configuration

Modify dashboard settings in:
- `dashboard-server.js` - Server configuration and ports
- `dashboard_with_vision.html` - UI customization
- WebSocket communication parameters

## 🧪 Testing & Validation

### Run System Tests

```bash
# Hardware component testing
python3 test_r2d2_servos.py
python3 test_vision_setup.py

# Integration testing
python3 r2d2_component_tester.py
python3 r2d2_integrated_performance.py

# Performance validation
python3 r2d2_convention_load_test.py
./r2d2_system_performance.sh
```

### Quality Assurance

The system includes comprehensive QA automation:
- Security validation (`r2d2_security_validator.py`)
- Performance monitoring (`r2d2_enhanced_scenario_tester.py`)
- Star Wars authenticity validation
- Multi-modal testing frameworks

## 🔒 Security & Safety

### Built-in Safety Features

- **Thermal Protection**: Automatic shutdown on overheating
- **Performance Monitoring**: Real-time system health checks
- **Security Validation**: Input sanitization and access control
- **Emergency Protocols**: Safe shutdown procedures
- **Hardware Limits**: Servo position and speed constraints

### Security Measures

- Input validation for all user interfaces
- WebSocket connection security
- File system access restrictions
- Hardware command validation
- Audit logging for all operations

## 🤖 Agent-Based Development

This project uses Claude AI agents for development automation:

### Active Agents

- **Super Coder**: Core system development and optimization
- **Web Dev Specialist**: Dashboard and UI development
- **Video Model Trainer**: Vision system and ML pipeline
- **QA Tester**: Quality assurance and validation
- **Project Manager**: Coordination and task management
- **Imagineer Specialist**: Creative and interaction design
- **Star Wars Specialist**: Canon compliance and authenticity

### Agent Storage

Agent work and memory is stored in `.claude/agent_storage/` with:
- Development history and context
- Specialized knowledge bases
- Task completion reports
- Coordination protocols

## 📊 Performance & Monitoring

### System Monitoring

The dashboard provides real-time monitoring of:
- CPU/GPU utilization and temperatures
- Memory usage and system load
- Vision processing frame rates
- Person recognition accuracy
- Hardware component status
- Network and communication status

### Performance Optimization

- CUDA acceleration for vision processing
- Multi-threaded processing pipelines
- Efficient memory management
- Hardware-specific optimizations for Jetson Orin Nano
- Automatic performance tuning

## 🔄 Backup & Version Control

### Automated Backup System

```bash
# Manual backup
python3 scripts/git_auto_backup.py --backup

# Agent commit (for development)
python3 scripts/git_auto_backup.py --agent-commit "AgentName" "Description"

# Push to remote
python3 scripts/git_auto_backup.py --push

# Show status
python3 scripts/git_auto_backup.py --status
```

### Repository Structure

```
/home/rolo/r2ai/
├── 📁 .claude/          # Agent system and memory
├── 📁 scripts/          # Utility and backup scripts
├── 📁 logs/             # System and operation logs
├── 📁 docs/             # Project documentation
├── 📁 database/         # Person recognition database
├── 🐍 Core Python Scripts (77+ files)
├── 🌐 Web Interface Files
├── ⚙️ Configuration Files
└── 📋 Documentation & Reports
```

## 🚀 Development Workflow

### Adding New Features

1. **Create Feature Branch**
   ```bash
   git checkout -b feature/new-feature-name
   ```

2. **Develop with Agent Support**
   - Use Claude agents for specialized development
   - Follow existing code patterns and standards
   - Include comprehensive testing

3. **Test & Validate**
   ```bash
   python3 test_integration.py
   ./validate_system.sh
   ```

4. **Commit & Push**
   ```bash
   python3 scripts/git_auto_backup.py --backup
   git push origin feature/new-feature-name
   ```

### Code Quality Standards

- **Python**: PEP 8 compliance, type hints, comprehensive docstrings
- **JavaScript**: ESLint standards, modular design
- **Testing**: >90% code coverage, integration tests
- **Documentation**: Inline comments, API documentation
- **Security**: Input validation, secure coding practices

## 🌟 Features in Development

### Upcoming Enhancements

- [ ] Advanced natural language interaction
- [ ] Expanded gesture recognition
- [ ] Multi-room navigation
- [ ] Enhanced emotion detection
- [ ] Voice command processing
- [ ] Mobile app integration
- [ ] Cloud connectivity for updates
- [ ] Advanced character personality modes

### Contributing

This project is designed for collaborative development:

1. **Fork the repository**
2. **Create your feature branch**
3. **Make your changes with comprehensive testing**
4. **Ensure all QA checks pass**
5. **Submit a pull request with detailed description**

## 📚 Documentation

### Additional Documentation

- `DEPLOYMENT_SUMMARY.md` - Deployment and setup guide
- `R2AI_PROJECT_MANAGEMENT_DASHBOARD.md` - Project management overview
- `STAR_WARS_CANON_COMPLIANCE_ANALYSIS.md` - Authenticity standards
- `GUEST_RECOGNITION_SYSTEM.md` - Person recognition architecture
- `SAFETY_CROWD_MANAGEMENT.md` - Safety protocols and guidelines

### Technical Reports

- Hardware assessment and optimization reports
- Performance benchmarking results
- Security audit documentation
- QA testing comprehensive reports
- Integration testing summaries

## 🆘 Troubleshooting

### Common Issues

**Dashboard not accessible**
```bash
# Check if server is running
ps aux | grep dashboard-server.js
# Restart dashboard
./start-dashboard.sh
```

**Vision system not detecting**
```bash
# Test camera connection
python3 test_vision_setup.py
# Check CUDA availability
python3 cuda_performance_test.py
```

**Servo motors not responding**
```bash
# Test servo connections
python3 test_r2d2_servos.py
# Check I2C bus
python3 r2d2_component_tester.py
```

### Getting Help

- Check log files in `/logs/` directory
- Run system diagnostics: `python3 r2d2_integrated_performance.py`
- Review security reports: `r2d2_security_summary.txt`
- Use backup system status: `python3 scripts/git_auto_backup.py --status`

## 📄 License

This project is developed for educational and hobbyist purposes. Please respect Star Wars intellectual property and use responsibly.

## 🙏 Acknowledgments

- **Ultralytics YOLO** - Object detection framework
- **OpenCV** - Computer vision library
- **PyTorch** - Machine learning framework
- **Claude AI** - Development assistance and automation
- **Star Wars Universe** - Inspiration and character reference
- **Maker Community** - Hardware integration guidance

---

**May the Force be with you!** 🌟

*This R2-D2 system brings the beloved droid to life with modern AI and robotics technology while honoring the original Star Wars vision.*

---

## 🔗 Quick Links

- [System Status Dashboard](http://localhost:8765)
- [Vision Interface](http://localhost:8766)
- [Live Camera Feed](http://localhost:8767)
- [Project Documentation](/docs/)
- [Agent Management](/.claude/)
- [Backup System](/scripts/git_auto_backup.py)

**Repository**: https://github.com/YOUR_USERNAME/r2ai
**Last Updated**: September 2025
**Version**: 1.0.0 (Operational)