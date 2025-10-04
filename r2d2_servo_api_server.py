#!/usr/bin/env python3
"""
R2D2 Enhanced Servo API Server
High-Performance REST API for Servo Control Integration

This module provides a production-ready REST API server that integrates with
the enhanced servo control backend, offering:
- FastAPI-based high-performance REST endpoints
- Real-time servo control with motion types
- Sequence management and execution
- Comprehensive diagnostics and monitoring
- Safety system integration
- Dashboard communication
- Auto-documentation with OpenAPI

Target: NVIDIA Orin Nano R2D2 Systems
Hardware: Pololu Maestro Mini 12-Channel USB Servo Controller
"""

import asyncio
import uvicorn
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any
import logging
import time
from pathlib import Path

# Import the enhanced servo backend
from r2d2_servo_backend import (
    ServoControlBackend,
    MotionType,
    ServoCommandType,
    SystemHealthStatus,
    ConnectionStatus
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Pydantic models for API requests/responses
class ServoMoveRequest(BaseModel):
    position: float = Field(..., ge=500, le=2500, description="Servo position in microseconds")
    duration: Optional[float] = Field(0.0, ge=0, le=10, description="Movement duration in seconds")
    motion_type: Optional[str] = Field("linear", description="Motion easing type")

class SequenceKeyframe(BaseModel):
    channel: int = Field(..., ge=0, le=11, description="Servo channel")
    position: float = Field(..., ge=500, le=2500, description="Target position in microseconds")
    duration: float = Field(1.0, ge=0.1, le=10, description="Movement duration in seconds")
    delay: Optional[float] = Field(0.0, ge=0, le=10, description="Delay before movement")
    motion_type: Optional[str] = Field("linear", description="Motion easing type")

class SequenceCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=50, description="Sequence name")
    description: Optional[str] = Field("", max_length=200, description="Sequence description")
    keyframes: List[SequenceKeyframe] = Field(..., min_items=1, description="Sequence keyframes")

class SafetyParametersRequest(BaseModel):
    position_deviation_threshold: Optional[int] = Field(None, ge=100, le=2000)
    movement_timeout: Optional[float] = Field(None, ge=1.0, le=60.0)
    connection_timeout: Optional[float] = Field(None, ge=1.0, le=30.0)
    max_violations: Optional[int] = Field(None, ge=1, le=10)

class ServoConfigRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=30)
    display_name: Optional[str] = Field(None, max_length=50)
    min_position: Optional[int] = Field(None, ge=500, le=2500)
    max_position: Optional[int] = Field(None, ge=500, le=2500)
    home_position: Optional[int] = Field(None, ge=500, le=2500)
    max_speed: Optional[int] = Field(None, ge=0, le=255)
    acceleration: Optional[int] = Field(None, ge=0, le=255)
    enabled: Optional[bool] = Field(None)

# Initialize FastAPI app
app = FastAPI(
    title="R2D2 Enhanced Servo Control API",
    description="Production-ready REST API for R2D2 servo control system",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global backend instance
servo_backend: Optional[ServoControlBackend] = None

@app.on_event("startup")
async def startup_event():
    """Initialize servo backend on startup"""
    global servo_backend

    logger.info("🚀 Starting R2D2 Enhanced Servo API Server...")

    try:
        # Initialize backend with auto-detection
        servo_backend = ServoControlBackend(auto_detect=True)

        # Start all backend services
        await servo_backend.start_services(websocket_port=8767)

        logger.info("✅ R2D2 Servo API Server ready!")

    except Exception as e:
        logger.error(f"Failed to start servo backend: {e}")
        raise

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    global servo_backend

    if servo_backend:
        await servo_backend.shutdown()
        logger.info("✅ R2D2 Servo API Server shutdown complete")

# Health and status endpoints
@app.get("/", tags=["System"])
async def root():
    """API root endpoint"""
    return {
        "service": "R2D2 Enhanced Servo Control API",
        "version": "2.0.0",
        "status": "operational",
        "timestamp": time.time()
    }

@app.get("/health", tags=["System"])
async def health_check():
    """System health check"""
    if not servo_backend:
        raise HTTPException(status_code=503, detail="Servo backend not initialized")

    status = servo_backend.get_controller_status()

    return {
        "status": "healthy" if status.get("health_status") != "critical" else "degraded",
        "connection_status": status.get("connection_status"),
        "health_status": status.get("health_status"),
        "uptime": status.get("uptime"),
        "services": status.get("services_running"),
        "timestamp": time.time()
    }

@app.get("/api/servo/status", tags=["Servo Control"])
async def get_servo_status():
    """Get comprehensive servo system status"""
    if not servo_backend:
        raise HTTPException(status_code=503, detail="Servo backend not initialized")

    return servo_backend.get_comprehensive_status()

@app.get("/api/servo/controller", tags=["Servo Control"])
async def get_controller_status():
    """Get controller hardware status"""
    if not servo_backend:
        raise HTTPException(status_code=503, detail="Servo backend not initialized")

    return servo_backend.get_controller_status()

@app.get("/api/servo/servos", tags=["Servo Control"])
async def get_all_servos():
    """Get status of all configured servos"""
    if not servo_backend:
        raise HTTPException(status_code=503, detail="Servo backend not initialized")

    return {"servos": servo_backend.get_servo_status()}

# Individual servo control
@app.post("/api/servo/{channel}/move", tags=["Servo Control"])
async def move_servo(channel: int, request: ServoMoveRequest):
    """Move individual servo with enhanced motion control"""
    if not servo_backend:
        raise HTTPException(status_code=503, detail="Servo backend not initialized")

    if not 0 <= channel <= 11:
        raise HTTPException(status_code=400, detail="Channel must be between 0 and 11")

    # Validate motion type
    try:
        MotionType(request.motion_type)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid motion type: {request.motion_type}")

    result = servo_backend.move_servo_enhanced(
        channel=channel,
        position=request.position,
        duration=request.duration,
        motion_type=request.motion_type
    )

    if not result["success"]:
        raise HTTPException(status_code=500, detail=result.get("error", "Servo movement failed"))

    return result

@app.post("/api/servo/{channel}/home", tags=["Servo Control"])
async def home_servo(channel: int):
    """Move servo to home position"""
    if not servo_backend:
        raise HTTPException(status_code=503, detail="Servo backend not initialized")

    if not 0 <= channel <= 11:
        raise HTTPException(status_code=400, detail="Channel must be between 0 and 11")

    try:
        # Get servo config
        servo_configs = servo_backend.get_servo_status()
        if channel not in servo_configs:
            raise HTTPException(status_code=404, detail=f"Servo {channel} not configured")

        home_position = servo_configs[channel]["home_us"]

        result = servo_backend.move_servo_enhanced(
            channel=channel,
            position=home_position,
            duration=1.0,
            motion_type="ease_in_out"
        )

        if not result["success"]:
            raise HTTPException(status_code=500, detail=result.get("error", "Home movement failed"))

        return {"success": True, "channel": channel, "home_position": home_position}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/servo/{channel}/status", tags=["Servo Control"])
async def get_servo_status_by_channel(channel: int):
    """Get status of specific servo"""
    if not servo_backend:
        raise HTTPException(status_code=503, detail="Servo backend not initialized")

    if not 0 <= channel <= 11:
        raise HTTPException(status_code=400, detail="Channel must be between 0 and 11")

    servo_status = servo_backend.get_servo_status()

    if channel not in servo_status:
        raise HTTPException(status_code=404, detail=f"Servo {channel} not found")

    return {"channel": channel, "status": servo_status[channel]}

# Sequence management
@app.get("/api/sequences", tags=["Sequences"])
async def get_sequences():
    """Get all available sequences"""
    if not servo_backend:
        raise HTTPException(status_code=503, detail="Servo backend not initialized")

    return {"sequences": servo_backend.sequence_engine.list_sequences()}

@app.post("/api/sequences", tags=["Sequences"])
async def create_sequence(request: SequenceCreateRequest):
    """Create new servo sequence"""
    if not servo_backend:
        raise HTTPException(status_code=503, detail="Servo backend not initialized")

    # Convert keyframes to dict format
    keyframes = [keyframe.dict() for keyframe in request.keyframes]

    result = servo_backend.create_sequence_from_keyframes(
        name=request.name,
        keyframes=keyframes,
        description=request.description
    )

    if not result["success"]:
        raise HTTPException(status_code=500, detail=result.get("error", "Sequence creation failed"))

    return result

@app.post("/api/sequences/{sequence_id}/execute", tags=["Sequences"])
async def execute_sequence(sequence_id: str, loop: bool = False):
    """Execute servo sequence"""
    if not servo_backend:
        raise HTTPException(status_code=503, detail="Servo backend not initialized")

    try:
        success = await servo_backend.sequence_engine.execute_sequence(sequence_id, loop)

        if not success:
            raise HTTPException(status_code=404, detail=f"Sequence {sequence_id} not found")

        return {
            "success": True,
            "sequence_id": sequence_id,
            "loop": loop,
            "status": "executing"
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/sequences/{sequence_id}/stop", tags=["Sequences"])
async def stop_sequence(sequence_id: str):
    """Stop executing sequence"""
    if not servo_backend:
        raise HTTPException(status_code=503, detail="Servo backend not initialized")

    success = servo_backend.sequence_engine.stop_sequence(sequence_id)

    return {
        "success": success,
        "sequence_id": sequence_id,
        "status": "stopped" if success else "not_running"
    }

@app.post("/api/sequences/stop_all", tags=["Sequences"])
async def stop_all_sequences():
    """Stop all executing sequences"""
    if not servo_backend:
        raise HTTPException(status_code=503, detail="Servo backend not initialized")

    servo_backend.sequence_engine.stop_all_sequences()

    return {"success": True, "message": "All sequences stopped"}

# Safety and emergency controls
@app.post("/api/emergency_stop", tags=["Safety"])
async def emergency_stop():
    """Trigger emergency stop"""
    if not servo_backend:
        raise HTTPException(status_code=503, detail="Servo backend not initialized")

    servo_backend.emergency_stop()

    return {
        "success": True,
        "message": "Emergency stop activated",
        "timestamp": time.time()
    }

@app.post("/api/safety/clear_emergency", tags=["Safety"])
async def clear_emergency_stop():
    """Clear emergency stop condition"""
    if not servo_backend:
        raise HTTPException(status_code=503, detail="Servo backend not initialized")

    servo_backend.safety_monitor.clear_emergency_stop()

    return {
        "success": True,
        "message": "Emergency stop cleared",
        "timestamp": time.time()
    }

@app.get("/api/safety/status", tags=["Safety"])
async def get_safety_status():
    """Get safety system status"""
    if not servo_backend:
        raise HTTPException(status_code=503, detail="Servo backend not initialized")

    return servo_backend.safety_monitor.get_safety_status()

@app.post("/api/safety/parameters", tags=["Safety"])
async def update_safety_parameters(request: SafetyParametersRequest):
    """Update safety monitoring parameters"""
    if not servo_backend:
        raise HTTPException(status_code=503, detail="Servo backend not initialized")

    # Convert request to dict, filtering None values
    parameters = {k: v for k, v in request.dict().items() if v is not None}

    servo_backend.safety_monitor.set_safety_parameters(**parameters)

    return {
        "success": True,
        "updated_parameters": parameters,
        "timestamp": time.time()
    }

# Diagnostics and monitoring
@app.get("/api/diagnostics", tags=["Diagnostics"])
async def get_diagnostics():
    """Get system diagnostics and performance metrics"""
    if not servo_backend:
        raise HTTPException(status_code=503, detail="Servo backend not initialized")

    return servo_backend.diagnostics_engine.get_performance_report()

@app.get("/api/diagnostics/hardware", tags=["Diagnostics"])
async def get_hardware_diagnostics():
    """Get hardware detection and status"""
    if not servo_backend:
        raise HTTPException(status_code=503, detail="Servo backend not initialized")

    detected_boards = servo_backend.config_manager.detect_maestro_boards()

    return {
        "detected_boards": [
            {
                "port": board.port,
                "device_name": board.device_name,
                "serial_number": board.serial_number,
                "firmware_version": board.firmware_version,
                "channel_count": board.channel_count,
                "connection_status": board.connection_status,
                "last_detected": board.last_detected
            }
            for board in detected_boards
        ],
        "board_detection_enabled": servo_backend.config_manager.board_detection_enabled,
        "last_detection_time": servo_backend.config_manager.last_detection_time
    }

# Configuration management
@app.post("/api/config/servo_count", tags=["Configuration"])
async def set_servo_count(count: int):
    """Set number of active servos"""
    if not servo_backend:
        raise HTTPException(status_code=503, detail="Servo backend not initialized")

    if not 1 <= count <= 12:
        raise HTTPException(status_code=400, detail="Servo count must be between 1 and 12")

    if hasattr(servo_backend.controller, 'set_servo_count'):
        success = servo_backend.controller.set_servo_count(count)

        if not success:
            raise HTTPException(status_code=500, detail="Failed to set servo count")

        return {"success": True, "servo_count": count}
    else:
        raise HTTPException(status_code=501, detail="Servo count configuration not supported")

@app.post("/api/config/servo/{channel}", tags=["Configuration"])
async def configure_servo(channel: int, request: ServoConfigRequest):
    """Configure individual servo parameters"""
    if not servo_backend:
        raise HTTPException(status_code=503, detail="Servo backend not initialized")

    if not 0 <= channel <= 11:
        raise HTTPException(status_code=400, detail="Channel must be between 0 and 11")

    if hasattr(servo_backend.controller, 'rename_servo'):
        success = servo_backend.controller.rename_servo(
            channel=channel,
            name=request.name,
            display_name=request.display_name
        )

        if not success:
            raise HTTPException(status_code=500, detail="Failed to configure servo")

        return {
            "success": True,
            "channel": channel,
            "configuration": request.dict(exclude_none=True)
        }
    else:
        raise HTTPException(status_code=501, detail="Servo configuration not supported")

if __name__ == "__main__":
    # Run the API server
    uvicorn.run(
        "r2d2_servo_api_server:app",
        host="0.0.0.0",
        port=5000,
        reload=False,
        access_log=True
    )