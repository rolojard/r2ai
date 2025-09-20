#!/usr/bin/env python3
"""
R2D2 Computer Vision Integration API
FastAPI-based API for coordinating computer vision with motion and audio systems
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any, Callable
import asyncio
import json
import logging
import time
from datetime import datetime
from pathlib import Path
import numpy as np
import cv2
import base64
from concurrent.futures import ThreadPoolExecutor
import uuid

# Import our computer vision components
from real_time_inference_engine import R2D2VisionSystem, R2D2VisionAPI
from cv_system_architecture import R2D2Response, GuestProfile
from face_recognition_system import R2D2GuestMemorySystem

logger = logging.getLogger(__name__)

# Pydantic models for API
class VisionSystemStatus(BaseModel):
    running: bool
    performance: Dict[str, float]
    camera_active: bool
    queue_size: int
    config: Dict[str, Any]

class GuestDetectionResult(BaseModel):
    guest_id: str
    confidence: float
    bbox: List[int]  # [x, y, w, h]
    costume: str
    costume_confidence: float
    relationship_level: int
    visit_count: int
    timestamp: float

class R2D2ResponseModel(BaseModel):
    audio_sequence: str
    movement_pattern: str
    light_pattern: str
    priority: int = Field(ge=1, le=10)
    duration: float
    context: Dict[str, Any]

class MotionCommand(BaseModel):
    movement_pattern: str
    light_pattern: str
    priority: int
    duration: float
    context: Dict[str, Any]

class AudioCommand(BaseModel):
    audio_sequence: str
    priority: int
    context: Dict[str, Any]

class ConfigUpdate(BaseModel):
    detection_threshold: Optional[float] = None
    recognition_threshold: Optional[float] = None
    max_inference_time: Optional[float] = None

class SystemAlert(BaseModel):
    level: str  # info, warning, error, critical
    message: str
    timestamp: float
    component: str
    data: Optional[Dict[str, Any]] = None

# Initialize FastAPI app
app = FastAPI(
    title="R2D2 Computer Vision Integration API",
    description="Real-time computer vision API for R2D2 interactive behaviors",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global state
vision_system: Optional[R2D2VisionSystem] = None
vision_api: Optional[R2D2VisionAPI] = None
motion_callback: Optional[Callable] = None
audio_callback: Optional[Callable] = None
websocket_connections: List[WebSocket] = []
system_alerts: List[SystemAlert] = []

# Background task executor
executor = ThreadPoolExecutor(max_workers=4)

@app.on_event("startup")
async def startup_event():
    """Initialize computer vision system on startup"""
    global vision_system, vision_api

    try:
        logger.info("Initializing R2D2 Computer Vision System...")

        # Initialize vision system
        config_path = "/home/rolo/r2ai/.claude/agent_storage/video-model-trainer/config.json"
        vision_system = R2D2VisionSystem(config_path)
        vision_api = R2D2VisionAPI(vision_system)

        # Register default callbacks
        await register_default_callbacks()

        logger.info("R2D2 Computer Vision API ready")

    except Exception as e:
        logger.error(f"Failed to initialize vision system: {e}")
        raise

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    global vision_system

    if vision_system:
        await vision_system.stop_system()
        logger.info("R2D2 Computer Vision System stopped")

async def register_default_callbacks():
    """Register default motion and audio callbacks"""
    global vision_system

    async def default_motion_callback(motion_data: Dict[str, Any]):
        """Default motion callback - logs commands"""
        logger.info(f"Motion command: {motion_data.get('movement_pattern', 'unknown')}")

        # Broadcast to WebSocket clients
        await broadcast_to_websockets({
            "type": "motion_command",
            "data": motion_data,
            "timestamp": time.time()
        })

    async def default_audio_callback(audio_data: Dict[str, Any]):
        """Default audio callback - logs commands"""
        logger.info(f"Audio command: {audio_data.get('audio_sequence', 'unknown')}")

        # Broadcast to WebSocket clients
        await broadcast_to_websockets({
            "type": "audio_command",
            "data": audio_data,
            "timestamp": time.time()
        })

    if vision_system:
        vision_system.set_motion_api_callback(default_motion_callback)
        vision_system.set_audio_api_callback(default_audio_callback)

async def broadcast_to_websockets(message: Dict[str, Any]):
    """Broadcast message to all connected WebSocket clients"""
    if websocket_connections:
        disconnected = []
        for websocket in websocket_connections:
            try:
                await websocket.send_text(json.dumps(message))
            except:
                disconnected.append(websocket)

        # Remove disconnected clients
        for ws in disconnected:
            websocket_connections.remove(ws)

async def add_system_alert(level: str, message: str, component: str, data: Dict[str, Any] = None):
    """Add system alert and broadcast to clients"""
    alert = SystemAlert(
        level=level,
        message=message,
        timestamp=time.time(),
        component=component,
        data=data
    )

    system_alerts.append(alert)

    # Keep only recent alerts
    if len(system_alerts) > 100:
        system_alerts.pop(0)

    # Broadcast alert
    await broadcast_to_websockets({
        "type": "system_alert",
        "data": alert.dict(),
        "timestamp": time.time()
    })

# API Endpoints

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "R2D2 Computer Vision Integration API",
        "version": "1.0.0",
        "status": "operational" if vision_system else "initializing"
    }

@app.post("/vision/start")
async def start_vision_system():
    """Start the computer vision system"""
    global vision_api

    if not vision_api:
        raise HTTPException(status_code=500, detail="Vision system not initialized")

    try:
        result = await vision_api.start()

        if result["success"]:
            await add_system_alert("info", "Vision system started", "vision_api")
            return {"status": "started", "message": "Computer vision system is now running"}
        else:
            await add_system_alert("error", "Failed to start vision system", "vision_api")
            raise HTTPException(status_code=500, detail=result["message"])

    except Exception as e:
        await add_system_alert("error", f"Vision system startup error: {e}", "vision_api")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/vision/stop")
async def stop_vision_system():
    """Stop the computer vision system"""
    global vision_api

    if not vision_api:
        raise HTTPException(status_code=500, detail="Vision system not initialized")

    try:
        result = await vision_api.stop()
        await add_system_alert("info", "Vision system stopped", "vision_api")
        return {"status": "stopped", "message": "Computer vision system has been stopped"}

    except Exception as e:
        await add_system_alert("error", f"Vision system stop error: {e}", "vision_api")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/vision/status", response_model=VisionSystemStatus)
async def get_vision_status():
    """Get current vision system status"""
    global vision_api

    if not vision_api:
        raise HTTPException(status_code=500, detail="Vision system not initialized")

    try:
        status = await vision_api.get_status()
        return VisionSystemStatus(**status)

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/vision/configure")
async def configure_vision_system(config: ConfigUpdate):
    """Update vision system configuration"""
    global vision_api

    if not vision_api:
        raise HTTPException(status_code=500, detail="Vision system not initialized")

    try:
        config_dict = config.dict(exclude_unset=True)
        result = await vision_api.configure(config_dict)

        if result["success"]:
            await add_system_alert("info", f"Configuration updated: {list(config_dict.keys())}", "vision_api")
            return {"status": "configured", "message": "Configuration updated successfully"}
        else:
            await add_system_alert("warning", f"Configuration update failed: {result['message']}", "vision_api")
            raise HTTPException(status_code=400, detail=result["message"])

    except Exception as e:
        await add_system_alert("error", f"Configuration error: {e}", "vision_api")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/motion/register_callback")
async def register_motion_callback():
    """Register motion system callback"""
    global vision_api, motion_callback

    if not vision_api:
        raise HTTPException(status_code=500, detail="Vision system not initialized")

    try:
        # Create motion callback that can be customized by external systems
        async def motion_system_callback(motion_data: Dict[str, Any]):
            # Call external motion callback if registered
            if motion_callback:
                await motion_callback(motion_data)
            else:
                # Default behavior - log and broadcast
                logger.info(f"Motion command: {motion_data}")
                await broadcast_to_websockets({
                    "type": "motion_command",
                    "data": motion_data,
                    "timestamp": time.time()
                })

        result = await vision_api.register_motion_callback(motion_system_callback)

        if result["success"]:
            await add_system_alert("info", "Motion callback registered", "motion_api")
            return {"status": "registered", "message": "Motion callback registered successfully"}
        else:
            raise HTTPException(status_code=500, detail=result["message"])

    except Exception as e:
        await add_system_alert("error", f"Motion callback registration error: {e}", "motion_api")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/audio/register_callback")
async def register_audio_callback():
    """Register audio system callback"""
    global vision_api, audio_callback

    if not vision_api:
        raise HTTPException(status_code=500, detail="Vision system not initialized")

    try:
        # Create audio callback that can be customized by external systems
        async def audio_system_callback(audio_data: Dict[str, Any]):
            # Call external audio callback if registered
            if audio_callback:
                await audio_callback(audio_data)
            else:
                # Default behavior - log and broadcast
                logger.info(f"Audio command: {audio_data}")
                await broadcast_to_websockets({
                    "type": "audio_command",
                    "data": audio_data,
                    "timestamp": time.time()
                })

        result = await vision_api.register_audio_callback(audio_system_callback)

        if result["success"]:
            await add_system_alert("info", "Audio callback registered", "audio_api")
            return {"status": "registered", "message": "Audio callback registered successfully"}
        else:
            raise HTTPException(status_code=500, detail=result["message"])

    except Exception as e:
        await add_system_alert("error", f"Audio callback registration error: {e}", "audio_api")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/guests/current")
async def get_current_guests():
    """Get currently detected guests"""
    global vision_system

    if not vision_system or not vision_system.running:
        raise HTTPException(status_code=503, detail="Vision system not running")

    try:
        # This would get current guest detections from the vision system
        # For now, return placeholder data
        current_guests = []

        return {
            "guest_count": len(current_guests),
            "guests": current_guests,
            "timestamp": time.time()
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/guests/{guest_id}/history")
async def get_guest_history(guest_id: str):
    """Get interaction history for specific guest"""
    global vision_system

    if not vision_system:
        raise HTTPException(status_code=500, detail="Vision system not initialized")

    try:
        # Get guest history from memory system
        memory_system = vision_system.memory_manager
        history = memory_system.get_guest_interaction_history(guest_id)

        if not history:
            raise HTTPException(status_code=404, detail="Guest not found")

        return {
            "guest_id": guest_id,
            "history": history,
            "timestamp": time.time()
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/guests/{guest_id}/feedback")
async def log_interaction_feedback(guest_id: str, effectiveness_score: float, response_type: str):
    """Log feedback for guest interaction"""
    global vision_system

    if not vision_system:
        raise HTTPException(status_code=500, detail="Vision system not initialized")

    try:
        # Log interaction outcome
        memory_system = vision_system.memory_manager
        memory_system.log_interaction_outcome(
            guest_id, response_type, effectiveness_score
        )

        await add_system_alert("info", f"Interaction feedback logged for {guest_id}", "guest_memory")

        return {
            "status": "logged",
            "guest_id": guest_id,
            "effectiveness_score": effectiveness_score,
            "timestamp": time.time()
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/system/alerts")
async def get_system_alerts(limit: int = 50):
    """Get recent system alerts"""
    global system_alerts

    recent_alerts = system_alerts[-limit:] if len(system_alerts) > limit else system_alerts

    return {
        "alerts": [alert.dict() for alert in recent_alerts],
        "total_alerts": len(system_alerts),
        "timestamp": time.time()
    }

@app.get("/system/performance")
async def get_performance_metrics():
    """Get system performance metrics"""
    global vision_system

    if not vision_system:
        raise HTTPException(status_code=500, detail="Vision system not initialized")

    try:
        status = vision_system.get_system_status()

        return {
            "performance": status.get("performance", {}),
            "camera_active": status.get("camera_active", False),
            "queue_size": status.get("queue_size", 0),
            "timestamp": time.time()
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# WebSocket endpoint for real-time updates
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time system updates"""
    await websocket.accept()
    websocket_connections.append(websocket)

    try:
        # Send initial status
        if vision_system:
            status = vision_system.get_system_status()
            await websocket.send_text(json.dumps({
                "type": "status_update",
                "data": status,
                "timestamp": time.time()
            }))

        # Keep connection alive and handle incoming messages
        while True:
            try:
                data = await websocket.receive_text()
                message = json.loads(data)

                # Handle incoming WebSocket messages
                if message.get("type") == "ping":
                    await websocket.send_text(json.dumps({
                        "type": "pong",
                        "timestamp": time.time()
                    }))

            except WebSocketDisconnect:
                break
            except Exception as e:
                logger.error(f"WebSocket error: {e}")
                break

    except WebSocketDisconnect:
        pass
    finally:
        if websocket in websocket_connections:
            websocket_connections.remove(websocket)

# Custom motion and audio callback setters (for external integration)
def set_motion_callback(callback: Callable):
    """Set custom motion callback function"""
    global motion_callback
    motion_callback = callback

def set_audio_callback(callback: Callable):
    """Set custom audio callback function"""
    global audio_callback
    audio_callback = callback

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    global vision_system

    health_status = {
        "status": "healthy",
        "timestamp": time.time(),
        "components": {
            "vision_system": "operational" if vision_system and vision_system.running else "inactive",
            "api": "operational",
            "websocket_connections": len(websocket_connections)
        }
    }

    # Check for critical issues
    if vision_system and not vision_system.running:
        health_status["status"] = "degraded"

    return health_status

# Background task for periodic system monitoring
async def system_monitor():
    """Background task for system monitoring"""
    while True:
        try:
            if vision_system and vision_system.running:
                status = vision_system.get_system_status()
                performance = status.get("performance", {})

                # Check performance thresholds
                fps = performance.get("fps", 0)
                if fps < 20:  # Below 20 FPS is concerning
                    await add_system_alert(
                        "warning",
                        f"Low FPS detected: {fps:.1f}",
                        "performance_monitor",
                        {"fps": fps}
                    )

                # Check memory usage
                # (Additional monitoring logic would go here)

            await asyncio.sleep(30)  # Monitor every 30 seconds

        except Exception as e:
            logger.error(f"System monitor error: {e}")
            await asyncio.sleep(60)

# Start background monitoring when the app starts
@app.on_event("startup")
async def start_background_tasks():
    """Start background monitoring tasks"""
    asyncio.create_task(system_monitor())

# Development and testing endpoints
@app.post("/dev/simulate_guest")
async def simulate_guest_detection(
    costume: str = "jedi",
    confidence: float = 0.9,
    is_returning: bool = False
):
    """Simulate guest detection for testing (development only)"""
    try:
        # Create simulated guest detection
        guest_id = f"sim_guest_{int(time.time())}"

        # Simulate R2D2 response
        if costume == "jedi":
            response = R2D2ResponseModel(
                audio_sequence="curious_beeps_sequence",
                movement_pattern="head_tilt_inspection",
                light_pattern="blue_pulse_pattern",
                priority=8,
                duration=3.0,
                context={"emotion": "curious", "costume": costume}
            )
        else:
            response = R2D2ResponseModel(
                audio_sequence="friendly_greeting_beeps",
                movement_pattern="gentle_acknowledgment",
                light_pattern="soft_blue_pulse",
                priority=6,
                duration=3.0,
                context={"emotion": "friendly", "costume": costume}
            )

        # Broadcast simulated detection
        await broadcast_to_websockets({
            "type": "guest_detection",
            "data": {
                "guest_id": guest_id,
                "costume": costume,
                "confidence": confidence,
                "is_returning": is_returning,
                "response": response.dict()
            },
            "timestamp": time.time()
        })

        return {
            "status": "simulated",
            "guest_id": guest_id,
            "response": response.dict()
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn

    # Configure logging
    logging.basicConfig(level=logging.INFO)

    # Run the API server
    uvicorn.run(
        "integration_api:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )