# 🎮 R2D2 Advanced Servo Control Dashboard - User Guide

## Overview
The R2D2 Advanced Servo Control Dashboard is a professional-grade interface designed for controlling and monitoring the R2D2 animatronics system. It features a Star Wars-themed design with comprehensive servo management capabilities.

## Dashboard Access URLs

### Main Advanced Servo Dashboard
- **URL**: `http://localhost:8765/` or `http://localhost:8765/servo`
- **Features**: Professional servo control with sequence management, board detection, and Maestro script execution

### Alternative Dashboard Views
- **Enhanced Dashboard**: `http://localhost:8765/enhanced`
- **Vision Dashboard**: `http://localhost:8765/vision`

## Key Features

### 🔍 Servo Board Detection
- **Auto-Detection**: Automatically scans for connected Pololu Maestro boards
- **Board Information**: Displays board type, port, channels, and firmware version
- **Connection Status**: Real-time connection status with visual indicators
- **Manual Controls**: Scan and connect buttons for manual board management

### ⚙️ Dynamic Servo Configuration
- **Servo Count**: Configurable number of servos (1-24)
- **Custom Naming**: Click on servo names to rename them
- **Limit Configuration**: Visual servo limit displays with min/max values
- **Update Rate**: Configurable refresh rate (50Hz, 100Hz, 200Hz)
- **Safety Modes**: Strict, Normal, and Permissive safety modes

### 🎛️ Advanced Control Interface
- **Real-time Sliders**: Smooth servo position control with visual feedback
- **Precise Input**: Direct microsecond value input for exact positioning
- **Live Feedback**: Real-time position display with color-coded status
- **Touch Support**: Optimized for tablet and mobile control
- **Visual Animations**: Servo movement animations and active state indicators

### 🎪 Sequence Management System
- **Sequence Library**: Pre-built sequences (Excited Greeting, Scanning Pattern, Panel Demonstration)
- **Playback Controls**: Play, Pause, Stop, and Loop functionality
- **Sequence Editor**: Record keyframes and create custom sequences
- **Import/Export**: Save and load sequence libraries
- **Real-time Progress**: Visual progress tracking during playback

### 📜 Maestro Script Execution
- **Script Selection**: Built-in scripts (Initialization, Home Position, Demo, Calibration)
- **Execution Controls**: Execute and stop script functions
- **Progress Tracking**: Visual progress bar and status updates
- **Error Handling**: Comprehensive error reporting and recovery

### 🛡️ Safety & Emergency Features
- **Emergency Stop**: Immediate halt of all servo movement
- **System Monitoring**: Real-time system load and response time tracking
- **Safety Modes**: Configurable safety levels for different use cases
- **Visual Feedback**: Color-coded status indicators and alerts

### 🎨 Professional UI/UX
- **Star Wars Theme**: Authentic Star Wars-inspired visual design
- **Hologram Effects**: Animated scanning lines and glow effects
- **Responsive Design**: Optimized for desktop, tablet, and mobile devices
- **Touch Controls**: Large, touch-friendly controls for tablet use
- **Professional Animations**: Smooth transitions and visual feedback

## Controls Guide

### Servo Control
1. **Position Control**: Use sliders or direct input to set servo positions
2. **Home All**: Move all servos to their home positions
3. **Enable/Disable**: Toggle servo power states
4. **Save/Load**: Save and restore servo configurations

### Sequence Management
1. **Select Sequence**: Click on sequences in the library
2. **Play Controls**: Use playback buttons to control sequence execution
3. **Record Keyframes**: Capture current servo positions as keyframes
4. **Edit Sequences**: Create custom sequences with the built-in editor

### Emergency Procedures
1. **Emergency Stop**: Use the red emergency button (top-right) for immediate stop
2. **System Shutdown**: Graceful shutdown through safety controls
3. **Error Recovery**: System diagnostics and recovery procedures

## System Requirements

### Server Setup
- Node.js with WebSocket support
- Python 3.x for servo control scripts
- Pololu Maestro servo controller (compatible with Mini 12, 18, 24)

### Browser Compatibility
- Modern browsers with WebSocket support
- Recommended: Chrome, Firefox, Safari, Edge
- Mobile/Tablet: iOS Safari, Android Chrome

### Hardware Requirements
- USB connection to Pololu Maestro board
- Adequate power supply for servo loads
- Optional: Touch screen for optimal control experience

## WebSocket Communication

The dashboard communicates with the backend through WebSocket connections:

### Connection Endpoints
- **Main Dashboard**: `ws://localhost:8766`
- **Vision System**: `ws://localhost:8767` (if using vision integration)

### Message Types
- `servo_command`: Individual servo position commands
- `sequence_command`: Sequence playback commands
- `emergency_stop`: Emergency stop commands
- `config_update`: Configuration change notifications

## Troubleshooting

### Connection Issues
1. Verify server is running on port 8765
2. Check WebSocket connection status indicators
3. Ensure servo board is properly connected
4. Verify USB permissions for board access

### Performance Issues
1. Reduce update rate if experiencing lag
2. Close unnecessary browser tabs
3. Check system load indicators
4. Verify adequate power supply for servos

### Servo Issues
1. Check servo board detection status
2. Verify servo connections and power
3. Test individual servos before sequences
4. Use emergency stop if servos behave unexpectedly

## Support & Development

This dashboard is part of the R2AI (R2D2 AI) project and provides professional-grade animatronics control capabilities. For technical support or development questions, refer to the project documentation.

---

**Safety Note**: Always ensure proper power supply and safety precautions when operating servo systems. The emergency stop function should be immediately accessible during all operations.