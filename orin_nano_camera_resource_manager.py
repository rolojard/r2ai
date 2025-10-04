#!/usr/bin/env python3
"""
Orin Nano Camera Resource Manager
Centralized camera resource management to prevent conflicts and crashes
Ensures exclusive camera access and proper resource cleanup
"""

import cv2
import threading
import time
import logging
import psutil
import os
import fcntl
import atexit
from contextlib import contextmanager
from typing import Optional, Dict, Any

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class CameraResourceManager:
    """Thread-safe camera resource manager for Orin Nano"""

    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        """Singleton pattern to ensure only one resource manager"""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super(CameraResourceManager, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        if hasattr(self, '_initialized'):
            return

        self._initialized = True
        self.camera_locks = {}  # Per-camera locks
        self.active_cameras = {}  # Track active camera instances
        self.camera_configs = {}  # Store camera configurations
        self.resource_lock = threading.RLock()
        self.lock_files = {}  # File-based locks for system-wide coordination

        # System resource monitoring
        self.memory_threshold = 85  # Percentage
        self.cpu_threshold = 90     # Percentage

        # Register cleanup on exit
        atexit.register(self.cleanup_all_resources)

        logger.info("Camera Resource Manager initialized")

    def _get_lock_file_path(self, camera_index: int) -> str:
        """Get lock file path for camera"""
        return f"/tmp/camera_{camera_index}.lock"

    def _acquire_system_lock(self, camera_index: int) -> bool:
        """Acquire system-wide lock for camera using file locking"""
        lock_path = self._get_lock_file_path(camera_index)

        try:
            lock_fd = os.open(lock_path, os.O_CREAT | os.O_WRONLY | os.O_TRUNC, 0o644)
            fcntl.flock(lock_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)

            # Write PID to lock file
            os.write(lock_fd, str(os.getpid()).encode())

            self.lock_files[camera_index] = lock_fd
            logger.info(f"Acquired system lock for camera {camera_index}")
            return True

        except (OSError, IOError) as e:
            logger.warning(f"Could not acquire system lock for camera {camera_index}: {e}")
            return False

    def _release_system_lock(self, camera_index: int):
        """Release system-wide lock for camera"""
        if camera_index in self.lock_files:
            try:
                lock_fd = self.lock_files[camera_index]
                fcntl.flock(lock_fd, fcntl.LOCK_UN)
                os.close(lock_fd)

                # Remove lock file
                lock_path = self._get_lock_file_path(camera_index)
                if os.path.exists(lock_path):
                    os.unlink(lock_path)

                del self.lock_files[camera_index]
                logger.info(f"Released system lock for camera {camera_index}")

            except Exception as e:
                logger.error(f"Error releasing system lock for camera {camera_index}: {e}")

    def check_system_resources(self) -> Dict[str, Any]:
        """Check system resource availability"""
        try:
            cpu_percent = psutil.cpu_percent(interval=0.1)
            memory = psutil.virtual_memory()

            return {
                'cpu_percent': cpu_percent,
                'memory_percent': memory.percent,
                'memory_available_mb': memory.available / 1024 / 1024,
                'cpu_ok': cpu_percent < self.cpu_threshold,
                'memory_ok': memory.percent < self.memory_threshold,
                'system_ready': cpu_percent < self.cpu_threshold and memory.percent < self.memory_threshold
            }
        except Exception as e:
            logger.error(f"Error checking system resources: {e}")
            return {'system_ready': False, 'error': str(e)}

    @contextmanager
    def acquire_camera(self, camera_index: int = 0, **config):
        """Context manager for safe camera acquisition"""
        camera = None
        acquired = False

        try:
            # Check system resources first
            resources = self.check_system_resources()
            if not resources.get('system_ready', False):
                logger.warning(f"System resources constrained: CPU {resources.get('cpu_percent', 0):.1f}%, "
                             f"Memory {resources.get('memory_percent', 0):.1f}%")
                # Continue anyway but with warnings

            with self.resource_lock:
                # Check if camera is already in use
                if camera_index in self.active_cameras:
                    existing_camera = self.active_cameras[camera_index]
                    if existing_camera is not None:
                        raise RuntimeError(f"Camera {camera_index} is already in use by another process")

                # Acquire system-wide lock
                if not self._acquire_system_lock(camera_index):
                    raise RuntimeError(f"Could not acquire exclusive access to camera {camera_index}")

                acquired = True

                # Initialize camera with optimal settings
                camera = self._initialize_camera_safe(camera_index, **config)

                if camera is None:
                    raise RuntimeError(f"Failed to initialize camera {camera_index}")

                # Register active camera (direct reference for OpenCV compatibility)
                self.active_cameras[camera_index] = camera
                self.camera_configs[camera_index] = config

                logger.info(f"Successfully acquired camera {camera_index}")

            yield camera

        except Exception as e:
            logger.error(f"Error acquiring camera {camera_index}: {e}")
            raise

        finally:
            # Always cleanup
            if camera is not None:
                try:
                    camera.release()
                    logger.info(f"Released camera {camera_index}")
                except:
                    pass

            with self.resource_lock:
                # Remove from active cameras
                if camera_index in self.active_cameras:
                    del self.active_cameras[camera_index]

                # Release system lock
                if acquired:
                    self._release_system_lock(camera_index)

    def _initialize_camera_safe(self, camera_index: int, **config) -> Optional[cv2.VideoCapture]:
        """Safely initialize camera with optimal settings for Orin Nano"""
        try:
            # Use V4L2 backend for better performance on Linux
            camera = cv2.VideoCapture(camera_index, cv2.CAP_V4L2)

            if not camera.isOpened():
                logger.error(f"Failed to open camera {camera_index}")
                return None

            # Apply Orin Nano optimized settings
            optimal_config = {
                cv2.CAP_PROP_FRAME_WIDTH: 640,
                cv2.CAP_PROP_FRAME_HEIGHT: 480,
                cv2.CAP_PROP_FPS: 30,
                cv2.CAP_PROP_BUFFERSIZE: 1,  # Minimal buffer to reduce latency
                cv2.CAP_PROP_FOURCC: cv2.VideoWriter_fourcc('M','J','P','G'),
            }

            # Apply user config overrides
            optimal_config.update(config)

            # Set camera properties
            for prop, value in optimal_config.items():
                if isinstance(prop, int):  # OpenCV property
                    try:
                        camera.set(prop, value)
                    except Exception as e:
                        logger.warning(f"Could not set camera property {prop} to {value}: {e}")

            # Test camera capture
            ret, test_frame = camera.read()
            if not ret or test_frame is None:
                logger.error(f"Camera {camera_index} failed initial capture test")
                camera.release()
                return None

            logger.info(f"Camera {camera_index} initialized successfully: {test_frame.shape}")

            # Warm up camera with a few reads
            for _ in range(3):
                camera.read()
                time.sleep(0.01)

            return camera

        except Exception as e:
            logger.error(f"Error initializing camera {camera_index}: {e}")
            return None

    def get_available_cameras(self) -> list:
        """Get list of available camera indices"""
        available = []

        for i in range(10):  # Check first 10 possible camera indices
            try:
                # Try to briefly open each camera
                cap = cv2.VideoCapture(i)
                if cap.isOpened():
                    ret, frame = cap.read()
                    if ret and frame is not None:
                        available.append(i)
                cap.release()
            except:
                continue

        logger.info(f"Available cameras: {available}")
        return available

    def cleanup_all_resources(self):
        """Clean up all camera resources"""
        logger.info("Cleaning up all camera resources...")

        with self.resource_lock:
            # Release all active cameras
            for camera_index in list(self.active_cameras.keys()):
                try:
                    camera = self.active_cameras[camera_index]
                    if camera is not None:
                        camera.release()
                except:
                    pass

                # Release system lock
                self._release_system_lock(camera_index)

            self.active_cameras.clear()
            self.camera_configs.clear()

        logger.info("Camera resource cleanup completed")

    def force_release_camera(self, camera_index: int):
        """Force release a camera (emergency use)"""
        logger.warning(f"Force releasing camera {camera_index}")

        with self.resource_lock:
            if camera_index in self.active_cameras:
                try:
                    camera = self.active_cameras[camera_index]
                    if camera is not None:
                        camera.release()
                except:
                    pass

                del self.active_cameras[camera_index]

            self._release_system_lock(camera_index)

        # Also clean up any stale lock files
        lock_path = self._get_lock_file_path(camera_index)
        if os.path.exists(lock_path):
            try:
                os.unlink(lock_path)
                logger.info(f"Removed stale lock file for camera {camera_index}")
            except:
                pass

    def get_camera_status(self) -> Dict[int, Dict[str, Any]]:
        """Get status of all managed cameras"""
        status = {}

        with self.resource_lock:
            for camera_index in list(self.active_cameras.keys()):
                camera_ref = self.active_cameras[camera_index]
                camera = camera_ref

                status[camera_index] = {
                    'active': camera is not None,
                    'config': self.camera_configs.get(camera_index, {}),
                    'lock_file': os.path.exists(self._get_lock_file_path(camera_index))
                }

        return status

# Global camera manager instance
camera_manager = CameraResourceManager()

# Convenience functions for easy use
def acquire_camera(camera_index: int = 0, **config):
    """Convenience function to acquire camera"""
    return camera_manager.acquire_camera(camera_index, **config)

def get_available_cameras():
    """Get available camera indices"""
    return camera_manager.get_available_cameras()

def cleanup_cameras():
    """Clean up all camera resources"""
    camera_manager.cleanup_all_resources()

def force_release_camera(camera_index: int):
    """Force release a specific camera"""
    camera_manager.force_release_camera(camera_index)

def get_system_status():
    """Get comprehensive system and camera status"""
    resources = camera_manager.check_system_resources()
    cameras = camera_manager.get_camera_status()

    return {
        'system_resources': resources,
        'cameras': cameras,
        'available_cameras': get_available_cameras(),
        'timestamp': time.time()
    }

def main():
    """Test the camera resource manager"""
    print("🎥 Camera Resource Manager Test")
    print("=" * 40)

    # Check system status
    status = get_system_status()
    print(f"System Resources: CPU {status['system_resources']['cpu_percent']:.1f}%, "
          f"Memory {status['system_resources']['memory_percent']:.1f}%")
    print(f"Available Cameras: {status['available_cameras']}")

    # Test camera acquisition
    try:
        with acquire_camera(0) as camera:
            print("✅ Successfully acquired camera 0")

            # Capture a few test frames
            for i in range(10):
                ret, frame = camera.read()
                if ret:
                    print(f"✅ Frame {i+1}: {frame.shape}")
                else:
                    print(f"❌ Frame {i+1}: Failed to capture")
                time.sleep(0.1)

    except Exception as e:
        print(f"❌ Camera test failed: {e}")

    print("Test completed")

if __name__ == "__main__":
    main()