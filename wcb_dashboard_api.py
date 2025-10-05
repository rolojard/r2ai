"""
WCB Dashboard API Service
FastAPI service providing unified dashboard control for WCB hardware orchestration
Production-ready API for mood-based R2D2 personality control
"""

import asyncio
import time
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from enum import Enum
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, validator

from wcb_hardware_orchestrator import HardwareOrchestrator, R2D2Mood

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# ============================================================================
# PYDANTIC MODELS (Request/Response Schemas)
# ============================================================================

class MoodExecuteRequest(BaseModel):
    """Request model for mood execution"""
    mood_id: int = Field(..., ge=1, le=27, description="Mood ID (1-27)")
    mood_name: Optional[str] = Field(None, description="Optional mood name for validation")
    priority: int = Field(7, ge=1, le=10, description="Execution priority (1-10)")

    @validator('mood_id')
    def validate_mood_id(cls, v):
        """Validate mood ID is within valid range"""
        try:
            R2D2Mood(v)
            return v
        except ValueError:
            raise ValueError(f"Invalid mood_id: {v}. Must be 1-27.")


class MoodExecuteResponse(BaseModel):
    """Response model for mood execution"""
    status: str
    mood: str
    mood_id: int
    commands_sent: int
    execution_time_ms: int
    timestamp: str


class MoodStopResponse(BaseModel):
    """Response model for stopping mood"""
    status: str
    mood: Optional[str]
    stopped_at: str


class MoodStatusResponse(BaseModel):
    """Response model for mood status"""
    active: bool
    mood: Optional[str]
    mood_id: Optional[int]
    progress_percent: int
    commands_sent: int
    started_at: Optional[str]
    uptime_seconds: int


class MoodInfo(BaseModel):
    """Model for individual mood information"""
    id: int
    name: str
    category: str
    command_count: int


class MoodListResponse(BaseModel):
    """Response model for mood list"""
    moods: List[MoodInfo]
    total: int
    categories: Dict[str, List[int]]


class WCBBoardStatus(BaseModel):
    """Status of individual WCB board"""
    connected: bool
    last_command: Optional[str]
    last_update: Optional[str]


class WCBBoardsStatusResponse(BaseModel):
    """Response model for WCB boards status"""
    wcb1: WCBBoardStatus
    wcb2: WCBBoardStatus
    wcb3: WCBBoardStatus
    overall_status: str


class StatsResponse(BaseModel):
    """Response model for API statistics"""
    moods_executed: int
    total_commands_sent: int
    total_commands_failed: int
    average_execution_time_ms: int
    uptime_seconds: int
    current_mode: str
    api_version: str


# ============================================================================
# ORCHESTRATOR MANAGER (Singleton State Management)
# ============================================================================

class OrchestratorManager:
    """
    Singleton manager for hardware orchestrator with statistics tracking
    Thread-safe mood execution and status management
    """

    def __init__(self):
        self.orchestrator: Optional[HardwareOrchestrator] = None
        self.is_connected: bool = False
        self.current_mood: Optional[R2D2Mood] = None
        self.current_mood_task: Optional[asyncio.Task] = None
        self.is_executing: bool = False

        # Statistics
        self.stats = {
            "moods_executed": 0,
            "total_commands_sent": 0,
            "total_commands_failed": 0,
            "execution_times_ms": [],
            "start_time": time.time()
        }

        # Lock for thread safety
        self._lock = asyncio.Lock()

        # Mood category mapping
        self.mood_categories = {
            "Primary Emotional": list(range(1, 7)),
            "Social Interaction": list(range(7, 11)),
            "Character-Specific": list(range(11, 15)),
            "Activity States": list(range(15, 21)),
            "Performance": list(range(21, 25)),
            "Special": list(range(25, 28))
        }

    async def initialize(self, port: str = '/dev/ttyUSB0', baud: int = 9600, simulation: bool = True):
        """Initialize hardware orchestrator"""
        try:
            self.orchestrator = HardwareOrchestrator(port=port, baud=baud, simulation=simulation)
            self.is_connected = self.orchestrator.connect()

            if self.is_connected:
                logger.info(f"WCB Orchestrator initialized - Mode: {'SIMULATION' if simulation else 'HARDWARE'}")
            else:
                logger.error("Failed to connect to WCB hardware")

            return self.is_connected
        except Exception as e:
            logger.error(f"Orchestrator initialization failed: {e}")
            return False

    async def execute_mood(self, mood_id: int, priority: int = 7) -> Dict[str, Any]:
        """
        Execute mood asynchronously with statistics tracking
        Thread-safe execution with proper error handling
        """
        async with self._lock:
            if self.is_executing:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Another mood is currently executing. Stop it first."
                )

            if not self.is_connected or not self.orchestrator:
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail="WCB orchestrator not connected"
                )

            try:
                # Get mood enum
                mood = R2D2Mood(mood_id)
                self.current_mood = mood
                self.is_executing = True

                # Execute mood and track timing
                start_time = time.time()
                logger.info(f"Starting mood execution: {mood.name} (ID: {mood_id}, Priority: {priority})")

                # Run mood execution in executor to avoid blocking
                loop = asyncio.get_event_loop()
                success = await loop.run_in_executor(
                    None,
                    self.orchestrator.execute_mood,
                    mood,
                    priority
                )

                execution_time_ms = int((time.time() - start_time) * 1000)

                # Update statistics
                self.stats["moods_executed"] += 1
                self.stats["execution_times_ms"].append(execution_time_ms)

                # Count commands from mood
                commands = self.orchestrator.mood_commands.get(mood, [])
                commands_sent = len(commands)

                if success:
                    self.stats["total_commands_sent"] += commands_sent
                    logger.info(f"Mood {mood.name} executed successfully in {execution_time_ms}ms")
                else:
                    self.stats["total_commands_failed"] += commands_sent
                    logger.warning(f"Mood {mood.name} completed with errors")

                return {
                    "status": "success" if success else "completed_with_errors",
                    "mood": mood.name,
                    "mood_id": mood_id,
                    "commands_sent": commands_sent,
                    "execution_time_ms": execution_time_ms,
                    "timestamp": datetime.now().isoformat()
                }

            except ValueError as e:
                logger.error(f"Invalid mood ID: {mood_id}")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid mood ID: {mood_id}"
                )
            except Exception as e:
                logger.error(f"Mood execution failed: {e}")
                self.stats["total_commands_failed"] += 1
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Mood execution failed: {str(e)}"
                )
            finally:
                self.is_executing = False

    async def stop_mood(self) -> Dict[str, Any]:
        """Stop current mood execution"""
        async with self._lock:
            if not self.is_executing:
                return {
                    "status": "no_mood_active",
                    "mood": None,
                    "stopped_at": datetime.now().isoformat()
                }

            mood_name = self.current_mood.name if self.current_mood else "Unknown"

            # Cancel current task if exists
            if self.current_mood_task and not self.current_mood_task.done():
                self.current_mood_task.cancel()

            self.is_executing = False
            logger.info(f"Stopped mood: {mood_name}")

            return {
                "status": "stopped",
                "mood": mood_name,
                "stopped_at": datetime.now().isoformat()
            }

    def get_status(self) -> Dict[str, Any]:
        """Get current mood execution status"""
        uptime = int(time.time() - self.stats["start_time"])

        return {
            "active": self.is_executing,
            "mood": self.current_mood.name if self.current_mood else None,
            "mood_id": self.current_mood.value if self.current_mood else None,
            "progress_percent": 100 if not self.is_executing else 50,  # Simplified
            "commands_sent": self.stats["total_commands_sent"],
            "started_at": None,  # Could track per-mood start time
            "uptime_seconds": uptime
        }

    def get_mood_list(self) -> Dict[str, Any]:
        """Get list of all available moods"""
        moods = []

        for mood_id in range(1, 28):
            try:
                mood = R2D2Mood(mood_id)

                # Determine category
                category = "Unknown"
                for cat_name, ids in self.mood_categories.items():
                    if mood_id in ids:
                        category = cat_name
                        break

                # Get command count
                commands = self.orchestrator.mood_commands.get(mood, []) if self.orchestrator else []

                moods.append({
                    "id": mood_id,
                    "name": mood.name,
                    "category": category,
                    "command_count": len(commands)
                })
            except ValueError:
                continue

        return {
            "moods": moods,
            "total": len(moods),
            "categories": self.mood_categories
        }

    def get_stats(self) -> Dict[str, Any]:
        """Get API statistics"""
        uptime = int(time.time() - self.stats["start_time"])

        avg_exec_time = 0
        if self.stats["execution_times_ms"]:
            avg_exec_time = int(sum(self.stats["execution_times_ms"]) / len(self.stats["execution_times_ms"]))

        mode = "simulation" if (self.orchestrator and self.orchestrator.simulation) else "hardware"

        return {
            "moods_executed": self.stats["moods_executed"],
            "total_commands_sent": self.stats["total_commands_sent"],
            "total_commands_failed": self.stats["total_commands_failed"],
            "average_execution_time_ms": avg_exec_time,
            "uptime_seconds": uptime,
            "current_mode": mode,
            "api_version": "1.0.0"
        }

    def get_boards_status(self) -> Dict[str, Any]:
        """Get WCB boards connection status"""
        # Simplified - in real implementation, track per-board status
        connected = self.is_connected
        timestamp = datetime.now().isoformat()

        board_status = WCBBoardStatus(
            connected=connected,
            last_command=self.current_mood.name if self.current_mood else None,
            last_update=timestamp if connected else None
        )

        return {
            "wcb1": board_status,
            "wcb2": board_status,
            "wcb3": board_status,
            "overall_status": "connected" if connected else "disconnected"
        }

    async def shutdown(self):
        """Cleanup on shutdown"""
        if self.orchestrator:
            self.orchestrator.disconnect()
            logger.info("Orchestrator disconnected")


# ============================================================================
# FASTAPI APPLICATION
# ============================================================================

# Global orchestrator manager
manager = OrchestratorManager()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    # Startup
    logger.info("Starting WCB Dashboard API...")

    # Initialize orchestrator (simulation mode by default)
    # Change simulation=False when ready for hardware
    await manager.initialize(
        port='/dev/ttyUSB0',
        baud=9600,
        simulation=True  # Set to False for hardware mode
    )

    yield

    # Shutdown
    logger.info("Shutting down WCB Dashboard API...")
    await manager.shutdown()


# Create FastAPI app
app = FastAPI(
    title="WCB Dashboard API",
    description="Unified API for R2D2 WCB Hardware Orchestration - Mood-Based Control",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware for dashboard access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================================
# API ENDPOINTS
# ============================================================================

@app.get("/", tags=["Health"])
async def root():
    """API health check"""
    return {
        "service": "WCB Dashboard API",
        "version": "1.0.0",
        "status": "running",
        "orchestrator_connected": manager.is_connected,
        "timestamp": datetime.now().isoformat()
    }


@app.post("/api/wcb/mood/execute", response_model=MoodExecuteResponse, tags=["Mood Control"])
async def execute_mood(request: MoodExecuteRequest):
    """
    Execute a specific R2D2 mood

    - **mood_id**: Mood ID from 1-27
    - **mood_name**: Optional mood name for validation
    - **priority**: Execution priority (1-10, default 7)

    Returns execution status, timing, and command count
    """
    logger.info(f"API Request: Execute mood {request.mood_id} with priority {request.priority}")

    # Validate mood name if provided
    if request.mood_name:
        try:
            mood = R2D2Mood(request.mood_id)
            if mood.name != request.mood_name:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Mood name mismatch: ID {request.mood_id} is '{mood.name}', not '{request.mood_name}'"
                )
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid mood_id: {request.mood_id}"
            )

    result = await manager.execute_mood(request.mood_id, request.priority)
    return MoodExecuteResponse(**result)


@app.post("/api/wcb/mood/stop", response_model=MoodStopResponse, tags=["Mood Control"])
async def stop_mood():
    """
    Stop currently executing mood

    Returns stop status and timestamp
    """
    logger.info("API Request: Stop current mood")
    result = await manager.stop_mood()
    return MoodStopResponse(**result)


@app.get("/api/wcb/mood/status", response_model=MoodStatusResponse, tags=["Mood Control"])
async def get_mood_status():
    """
    Get current mood execution status

    Returns active status, current mood, progress, and statistics
    """
    status_data = manager.get_status()
    return MoodStatusResponse(**status_data)


@app.get("/api/wcb/mood/list", response_model=MoodListResponse, tags=["Mood Control"])
async def list_moods():
    """
    List all available R2D2 moods

    Returns complete list of 27 moods with categories and command counts
    """
    mood_list = manager.get_mood_list()
    return MoodListResponse(**mood_list)


@app.get("/api/wcb/stats", response_model=StatsResponse, tags=["Statistics"])
async def get_stats():
    """
    Get API usage statistics

    Returns execution counts, timing statistics, and uptime
    """
    stats = manager.get_stats()
    return StatsResponse(**stats)


@app.get("/api/wcb/boards/status", response_model=WCBBoardsStatusResponse, tags=["Hardware"])
async def get_boards_status():
    """
    Get WCB boards connection status

    Returns status for WCB1, WCB2, and WCB3 boards
    """
    boards_status = manager.get_boards_status()
    return WCBBoardsStatusResponse(**boards_status)


# ============================================================================
# MAIN ENTRY POINT
# ============================================================================

if __name__ == "__main__":
    import uvicorn

    logger.info("="*80)
    logger.info("WCB Dashboard API - Production Server")
    logger.info("="*80)
    logger.info("Starting server on http://0.0.0.0:8770")
    logger.info("API Documentation: http://0.0.0.0:8770/docs")
    logger.info("="*80)

    uvicorn.run(
        "wcb_dashboard_api:app",
        host="0.0.0.0",
        port=8770,
        log_level="info",
        reload=False  # Set to True for development
    )
