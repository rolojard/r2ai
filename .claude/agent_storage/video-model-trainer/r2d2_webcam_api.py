#!/usr/bin/env python3
"""
R2D2 Webcam Interface API
Enhanced FastAPI server for webcam interface with Socket.IO support
Integrates with existing computer vision system and provides real-time monitoring
"""

from fastapi import FastAPI, HTTPException, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any
import asyncio
import json
import logging
import time
from datetime import datetime
from pathlib import Path
import base64
import cv2
import numpy as np
import socketio

# Import our webcam interface and existing systems
from r2d2_webcam_interface import R2D2WebcamInterface, DetectionResult, SystemStatus
from integration_api import app as existing_api

logger = logging.getLogger(__name__)

# Enhanced Pydantic models
class WebcamConfig(BaseModel):
    device_id: Optional[int] = 0
    resolution: Optional[List[int]] = [1920, 1080]
    fps: Optional[int] = 30
    show_interface: Optional[bool] = True
    show_agent_monitor: Optional[bool] = True

class TriggerZoneConfig(BaseModel):
    name: str
    distance: int
    priority: int
    cooldown: float
    enabled: bool = True

class VisualConfig(BaseModel):
    show_bboxes: Optional[bool] = True
    show_confidence: Optional[bool] = True
    show_zones: Optional[bool] = True
    show_status: Optional[bool] = True
    overlay_opacity: Optional[float] = 0.7

class WebcamStatus(BaseModel):
    camera_active: bool
    interface_running: bool
    monitor_clients: int
    current_detections: int
    system_status: Dict[str, Any]
    uptime_seconds: float

# Create Socket.IO server
sio = socketio.AsyncServer(
    cors_allowed_origins="*",
    logger=True,
    engineio_logger=True
)

# Create FastAPI app
app = FastAPI(
    title="R2D2 Webcam Interface API",
    description="Enhanced webcam interface with real-time monitoring and agent access",
    version="2.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount Socket.IO
app.mount("/socket.io", socketio.ASGIApp(sio))

# Global state
webcam_interface: Optional[R2D2WebcamInterface] = None
start_time = time.time()
monitor_clients = set()

# Socket.IO event handlers
@sio.event
async def connect(sid, environ):
    """Handle client connection"""
    logger.info(f"Monitor client connected: {sid}")
    monitor_clients.add(sid)

    # Send initial status if webcam interface is running
    if webcam_interface and webcam_interface.running:
        status = webcam_interface.get_system_status()
        await sio.emit('status_update', status, room=sid)

@sio.event
async def disconnect(sid):
    """Handle client disconnection"""
    logger.info(f"Monitor client disconnected: {sid}")
    monitor_clients.discard(sid)

@sio.event
async def request_screenshot(sid):
    """Handle screenshot request"""
    if webcam_interface:
        frame = await webcam_interface.capture_screenshot()
        if frame is not None:
            # Encode frame as base64
            _, buffer = cv2.imencode('.jpg', frame)
            img_base64 = base64.b64encode(buffer).decode('utf-8')

            await sio.emit('screenshot', {
                'image': img_base64,
                'timestamp': time.time()
            }, room=sid)

@sio.event
async def ping(sid):
    """Handle ping from client"""
    await sio.emit('pong', {'timestamp': time.time()}, room=sid)

# Initialize webcam interface on startup
@app.on_event("startup")
async def startup_event():
    """Initialize webcam interface system"""
    global webcam_interface

    try:
        logger.info("Initializing R2D2 Webcam Interface API...")

        # Create webcam interface
        config_path = "/home/rolo/r2ai/.claude/agent_storage/video-model-trainer/webcam_config.json"
        webcam_interface = R2D2WebcamInterface(config_path)

        # Set up callbacks for integration with motion and audio systems
        await setup_integration_callbacks()

        logger.info("✅ R2D2 Webcam Interface API ready")

    except Exception as e:
        logger.error(f"Failed to initialize webcam interface: {e}")
        raise

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    global webcam_interface

    if webcam_interface:
        await webcam_interface.stop_system()
        logger.info("R2D2 Webcam Interface stopped")

async def setup_integration_callbacks():
    """Setup callbacks for integration with motion and audio systems"""
    global webcam_interface

    async def enhanced_motion_callback(motion_data: Dict[str, Any]):
        """Enhanced motion callback with WebSocket broadcasting"""
        try:
            logger.info(f"🤖 Motion: {motion_data.get('movement_pattern', 'unknown')}")

            # Broadcast to WebSocket clients
            await sio.emit('motion_command', {
                'type': 'motion_command',
                'data': motion_data,
                'timestamp': time.time()
            })

            # Call existing motion callback if available
            # This would integrate with existing motion enhancement system
            # await existing_motion_callback(motion_data)

        except Exception as e:
            logger.error(f"Motion callback error: {e}")

    async def enhanced_audio_callback(audio_data: Dict[str, Any]):
        """Enhanced audio callback with WebSocket broadcasting"""
        try:
            logger.info(f"🔊 Audio: {audio_data.get('audio_sequence', 'unknown')}")

            # Broadcast to WebSocket clients
            await sio.emit('audio_command', {
                'type': 'audio_command',
                'data': audio_data,
                'timestamp': time.time()
            })

            # Call existing audio callback if available
            # This would integrate with existing audio integration system
            # await existing_audio_callback(audio_data)

        except Exception as e:
            logger.error(f"Audio callback error: {e}")

    async def status_update_callback(status_data: Dict[str, Any]):
        """Status update callback for real-time monitoring"""
        try:
            # Broadcast status updates to monitoring clients
            await sio.emit('status_update', status_data)

        except Exception as e:
            logger.error(f"Status callback error: {e}")

    if webcam_interface:
        webcam_interface.set_motion_callback(enhanced_motion_callback)
        webcam_interface.set_audio_callback(enhanced_audio_callback)
        webcam_interface.set_status_callback(status_update_callback)

# API Endpoints

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "R2D2 Webcam Interface API",
        "version": "2.0.0",
        "status": "operational" if webcam_interface and webcam_interface.running else "ready",
        "monitor_clients": len(monitor_clients),
        "uptime": time.time() - start_time
    }

@app.get("/monitor", response_class=HTMLResponse)
async def get_monitor_interface():
    """Serve the monitoring interface HTML page"""
    try:
        monitor_path = Path(__file__).parent / "r2d2_monitor_interface.html"
        if monitor_path.exists():
            with open(monitor_path, 'r') as f:
                return HTMLResponse(content=f.read())
        else:
            raise HTTPException(status_code=404, detail="Monitor interface not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load monitor interface: {e}")

@app.post("/webcam/start")
async def start_webcam_interface():
    """Start the webcam interface system"""
    global webcam_interface

    if not webcam_interface:
        raise HTTPException(status_code=500, detail="Webcam interface not initialized")

    try:
        if webcam_interface.running:
            return {"status": "already_running", "message": "Webcam interface is already running"}

        success = await webcam_interface.start_system()

        if success:
            # Start broadcasting updates to monitoring clients
            asyncio.create_task(broadcast_updates_loop())

            return {"status": "started", "message": "Webcam interface started successfully"}
        else:
            raise HTTPException(status_code=500, detail="Failed to start webcam interface")

    except Exception as e:
        logger.error(f"Failed to start webcam interface: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/webcam/stop")
async def stop_webcam_interface():
    """Stop the webcam interface system"""
    global webcam_interface

    if not webcam_interface:
        raise HTTPException(status_code=500, detail="Webcam interface not initialized")

    try:
        await webcam_interface.stop_system()
        return {"status": "stopped", "message": "Webcam interface stopped successfully"}

    except Exception as e:
        logger.error(f"Failed to stop webcam interface: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/webcam/status", response_model=WebcamStatus)
async def get_webcam_status():
    """Get current webcam interface status"""
    global webcam_interface

    if not webcam_interface:
        raise HTTPException(status_code=500, detail="Webcam interface not initialized")

    try:
        system_status = webcam_interface.get_system_status()
        current_detections = len(webcam_interface.get_current_detections())

        return WebcamStatus(
            camera_active=webcam_interface.camera_active,
            interface_running=webcam_interface.running,
            monitor_clients=len(monitor_clients),
            current_detections=current_detections,
            system_status=system_status,
            uptime_seconds=time.time() - start_time
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/webcam/configure")
async def configure_webcam(config: WebcamConfig):
    """Update webcam configuration"""
    global webcam_interface

    if not webcam_interface:
        raise HTTPException(status_code=500, detail="Webcam interface not initialized")

    try:
        config_dict = config.dict(exclude_unset=True)
        webcam_interface.update_config({"camera": config_dict})

        return {"status": "configured", "message": "Webcam configuration updated"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/webcam/configure/visual")
async def configure_visual_settings(config: VisualConfig):
    """Update visual interface settings"""
    global webcam_interface

    if not webcam_interface:
        raise HTTPException(status_code=500, detail="Webcam interface not initialized")

    try:
        config_dict = config.dict(exclude_unset=True)
        webcam_interface.update_config({"visual": config_dict})

        return {"status": "configured", "message": "Visual settings updated"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/webcam/detections")
async def get_current_detections():
    """Get current detection results"""
    global webcam_interface

    if not webcam_interface:
        raise HTTPException(status_code=500, detail="Webcam interface not initialized")

    try:
        detections = webcam_interface.get_current_detections()
        return {
            "detections": detections,
            "count": len(detections),
            "timestamp": time.time()
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/webcam/screenshot")
async def capture_screenshot():
    """Capture current screenshot"""
    global webcam_interface

    if not webcam_interface:
        raise HTTPException(status_code=500, detail="Webcam interface not initialized")

    try:
        frame = await webcam_interface.capture_screenshot()
        if frame is not None:
            # Encode frame as base64
            _, buffer = cv2.imencode('.jpg', frame)
            img_base64 = base64.b64encode(buffer).decode('utf-8')

            return {
                "screenshot": img_base64,
                "timestamp": time.time(),
                "format": "jpeg"
            }
        else:
            raise HTTPException(status_code=503, detail="No frame available")

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/webcam/triggers")
async def get_trigger_zones():
    """Get current trigger zone configuration"""
    global webcam_interface

    if not webcam_interface:
        raise HTTPException(status_code=500, detail="Webcam interface not initialized")

    try:
        zones = []
        for zone in webcam_interface.trigger_zones:
            zones.append({
                "name": zone.name,
                "bbox": zone.bbox,
                "color": zone.color,
                "interaction_type": zone.interaction_type,
                "priority": zone.priority,
                "cooldown_seconds": zone.cooldown_seconds
            })

        return {"trigger_zones": zones}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/webcam/triggers/test")
async def test_trigger_zone(zone_name: str, guest_costume: str = "jedi"):
    """Test a trigger zone with simulated detection"""
    global webcam_interface

    if not webcam_interface:
        raise HTTPException(status_code=500, detail="Webcam interface not initialized")

    try:
        # Find the trigger zone
        zone = None
        for z in webcam_interface.trigger_zones:
            if z.name == zone_name:
                zone = z
                break

        if not zone:
            raise HTTPException(status_code=404, detail=f"Trigger zone '{zone_name}' not found")

        # Create simulated detection
        center_x, center_y = zone.bbox[0] + zone.bbox[2]//2, zone.bbox[1] + zone.bbox[3]//2
        simulated_detection = DetectionResult(
            guest_id=f"test_guest_{int(time.time())}",
            bbox=(center_x-50, center_y-50, 100, 100),
            confidence=0.95,
            costume=guest_costume,
            costume_confidence=0.9,
            face_recognition=None,
            face_confidence=0.0,
            distance_zone=zone_name,
            timestamp=time.time(),
            interaction_count=0,
            relationship_level=1
        )

        # Trigger the interaction
        await webcam_interface._trigger_r2d2_interaction(simulated_detection, zone)

        return {
            "status": "triggered",
            "zone": zone_name,
            "costume": guest_costume,
            "message": f"Test trigger executed for {zone_name} zone with {guest_costume} costume"
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/integration/motion/status")
async def get_motion_integration_status():
    """Get motion system integration status"""
    return {
        "motion_callback_registered": webcam_interface.motion_callback is not None if webcam_interface else False,
        "integration_active": webcam_interface.running if webcam_interface else False,
        "timestamp": time.time()
    }

@app.get("/integration/audio/status")
async def get_audio_integration_status():
    """Get audio system integration status"""
    return {
        "audio_callback_registered": webcam_interface.audio_callback is not None if webcam_interface else False,
        "integration_active": webcam_interface.running if webcam_interface else False,
        "timestamp": time.time()
    }

@app.get("/monitoring/clients")
async def get_monitoring_clients():
    """Get information about connected monitoring clients"""
    return {
        "client_count": len(monitor_clients),
        "clients": list(monitor_clients),
        "timestamp": time.time()
    }

async def broadcast_updates_loop():
    """Background task to broadcast updates to monitoring clients"""
    logger.info("Starting monitoring broadcast loop...")

    while webcam_interface and webcam_interface.running:
        try:
            if monitor_clients:
                # Get current status and detections
                status = webcam_interface.get_system_status()
                detections = webcam_interface.get_current_detections()

                # Capture current frame for monitoring
                frame = await webcam_interface.capture_screenshot()
                frame_base64 = None

                if frame is not None:
                    # Create display frame with overlays
                    display_frame = webcam_interface._create_visual_overlay(
                        frame, webcam_interface.current_detections,
                        status.get('inference_time_ms', 0)
                    )

                    # Encode for transmission
                    _, buffer = cv2.imencode('.jpg', display_frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
                    frame_base64 = base64.b64encode(buffer).decode('utf-8')

                # Broadcast update
                await sio.emit('detection_update', {
                    'frame': frame_base64,
                    'detections': detections,
                    'system_status': status,
                    'timestamp': time.time()
                })

            # Update interval (10 FPS for monitoring)
            await asyncio.sleep(0.1)

        except Exception as e:
            logger.error(f"Broadcast loop error: {e}")
            await asyncio.sleep(1.0)

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    global webcam_interface

    health_status = {
        "status": "healthy",
        "timestamp": time.time(),
        "components": {
            "webcam_interface": "operational" if webcam_interface and webcam_interface.running else "inactive",
            "api": "operational",
            "socket_connections": len(monitor_clients),
            "uptime": time.time() - start_time
        }
    }

    # Check for issues
    if webcam_interface:
        if not webcam_interface.camera_active:
            health_status["status"] = "degraded"
            health_status["issues"] = health_status.get("issues", [])
            health_status["issues"].append("Camera not active")

        if not webcam_interface.running:
            health_status["status"] = "degraded"
            health_status["issues"] = health_status.get("issues", [])
            health_status["issues"].append("Interface not running")
    else:
        health_status["status"] = "degraded"
        health_status["issues"] = ["Webcam interface not initialized"]

    return health_status

if __name__ == "__main__":
    import uvicorn

    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Run the API server
    uvicorn.run(
        "r2d2_webcam_api:app",
        host="0.0.0.0",
        port=8000,
        reload=False,
        log_level="info"
    )