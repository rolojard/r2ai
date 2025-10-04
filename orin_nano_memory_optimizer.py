#!/usr/bin/env python3
"""
Orin Nano Memory Management Optimizer
Prevents memory-related crashes and optimizes memory usage for AI workloads
"""

import gc
import os
import sys
import psutil
import threading
import time
import logging
import subprocess
from typing import Dict, Any, Optional
import warnings

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class OrinNanoMemoryOptimizer:
    """Memory optimization and monitoring for Orin Nano"""

    def __init__(self, memory_limit_percent: float = 80.0):
        self.memory_limit_percent = memory_limit_percent
        self.monitoring_active = False
        self.monitor_thread = None
        self.memory_stats = {
            'peak_usage': 0,
            'gc_collections': 0,
            'warnings_issued': 0,
            'emergency_cleanups': 0
        }

        # Memory thresholds (percentages)
        self.warning_threshold = 75.0
        self.critical_threshold = 85.0
        self.emergency_threshold = 90.0

        # GPU memory monitoring
        self.gpu_memory_limit = None
        self._detect_gpu_memory_limit()

    def _detect_gpu_memory_limit(self):
        """Detect GPU memory limit for Orin Nano"""
        try:
            # For Orin Nano, integrated GPU shares system memory
            # Typical allocation is about 2GB for GPU from total 8GB
            total_memory = psutil.virtual_memory().total / (1024 ** 3)  # GB

            if total_memory > 7:  # 8GB Orin Nano
                self.gpu_memory_limit = 2048  # MB
            else:  # 4GB variant
                self.gpu_memory_limit = 1024  # MB

            logger.info(f"Detected GPU memory limit: {self.gpu_memory_limit}MB")

        except Exception as e:
            logger.warning(f"Could not detect GPU memory limit: {e}")
            self.gpu_memory_limit = 1024  # Conservative default

    def get_memory_status(self) -> Dict[str, Any]:
        """Get comprehensive memory status"""
        try:
            # System memory
            vm = psutil.virtual_memory()
            swap = psutil.swap_memory()

            # Process memory
            process = psutil.Process()
            process_memory = process.memory_info()

            # GPU memory (approximate for Orin Nano)
            gpu_usage = self._estimate_gpu_memory_usage()

            status = {
                'system': {
                    'total_gb': vm.total / (1024 ** 3),
                    'available_gb': vm.available / (1024 ** 3),
                    'used_percent': vm.percent,
                    'free_gb': vm.free / (1024 ** 3)
                },
                'swap': {
                    'total_gb': swap.total / (1024 ** 3),
                    'used_gb': swap.used / (1024 ** 3),
                    'used_percent': swap.percent
                },
                'process': {
                    'rss_mb': process_memory.rss / (1024 ** 2),
                    'vms_mb': process_memory.vms / (1024 ** 2)
                },
                'gpu': {
                    'estimated_usage_mb': gpu_usage,
                    'limit_mb': self.gpu_memory_limit,
                    'usage_percent': (gpu_usage / self.gpu_memory_limit * 100) if self.gpu_memory_limit else 0
                },
                'thresholds': {
                    'warning': vm.percent > self.warning_threshold,
                    'critical': vm.percent > self.critical_threshold,
                    'emergency': vm.percent > self.emergency_threshold
                }
            }

            return status

        except Exception as e:
            logger.error(f"Error getting memory status: {e}")
            return {'error': str(e)}

    def _estimate_gpu_memory_usage(self) -> float:
        """Estimate GPU memory usage for Orin Nano"""
        try:
            # Try to read from tegrastats if available
            result = subprocess.run(['tegrastats', '--once'],
                                  capture_output=True, text=True, timeout=2)

            if result.returncode == 0:
                # Parse tegrastats output for GPU memory info
                output = result.stdout
                # This is a simplified parser - actual format may vary
                if 'GPU' in output:
                    # Extract GPU usage from tegrastats output
                    # Format varies, so this is a best-effort estimation
                    pass

        except (subprocess.TimeoutExpired, FileNotFoundError, Exception):
            pass

        # Fallback: estimate based on system memory usage
        # GPU memory is shared with system on Orin Nano
        vm = psutil.virtual_memory()
        estimated_gpu_usage = min(vm.used * 0.25 / (1024 ** 2), self.gpu_memory_limit or 1024)

        return estimated_gpu_usage

    def optimize_memory_for_ai_workload(self):
        """Apply memory optimizations specific to AI/vision workloads"""
        logger.info("Applying AI workload memory optimizations...")

        try:
            # Python garbage collection tuning
            import gc
            gc.set_threshold(700, 10, 10)  # More aggressive GC for memory-constrained systems

            # Set environment variables for optimal memory usage
            memory_optimizations = {
                'MALLOC_TRIM_THRESHOLD_': '100000',  # Trim unused memory more aggressively
                'MALLOC_MMAP_THRESHOLD_': '131072',  # Use mmap for larger allocations
                'OMP_NUM_THREADS': '4',  # Limit OpenMP threads to prevent memory explosion
                'OPENCV_IO_MAX_IMAGE_PIXELS': str(640 * 480 * 10),  # Limit max image size
                'TF_CPP_MIN_LOG_LEVEL': '2',  # Reduce TensorFlow logging memory usage
                'CUDA_CACHE_DISABLE': '1',  # Disable CUDA kernel cache to save memory
            }

            for key, value in memory_optimizations.items():
                os.environ[key] = value
                logger.info(f"Set {key} = {value}")

            # Import optimizations
            import warnings
            warnings.filterwarnings('ignore', category=FutureWarning)  # Reduce warning overhead

            logger.info("Memory optimizations applied successfully")

        except Exception as e:
            logger.error(f"Error applying memory optimizations: {e}")

    def emergency_memory_cleanup(self):
        """Emergency memory cleanup to prevent crashes"""
        logger.warning("Performing emergency memory cleanup...")

        try:
            # Force garbage collection
            collected = gc.collect()
            logger.info(f"Garbage collection freed {collected} objects")

            # Clear Python caches
            sys.intern.clear() if hasattr(sys.intern, 'clear') else None

            # Try to free OpenCV memory
            try:
                import cv2
                # Force OpenCV to release unused memory
                cv2.setUseOptimized(True)
                cv2.setNumThreads(2)  # Reduce thread count to save memory
            except ImportError:
                pass

            # Try to free PyTorch cache if available
            try:
                import torch
                if torch.cuda.is_available():
                    torch.cuda.empty_cache()
                    logger.info("Cleared PyTorch CUDA cache")
            except ImportError:
                pass

            # Try to free TensorFlow memory if available
            try:
                import tensorflow as tf
                if hasattr(tf.keras.backend, 'clear_session'):
                    tf.keras.backend.clear_session()
                    logger.info("Cleared TensorFlow session")
            except ImportError:
                pass

            self.memory_stats['emergency_cleanups'] += 1
            logger.info("Emergency memory cleanup completed")

        except Exception as e:
            logger.error(f"Error during emergency memory cleanup: {e}")

    def start_memory_monitoring(self, interval: float = 5.0):
        """Start background memory monitoring"""
        if self.monitoring_active:
            logger.warning("Memory monitoring already active")
            return

        self.monitoring_active = True

        def monitor_loop():
            logger.info("Started memory monitoring")

            while self.monitoring_active:
                try:
                    status = self.get_memory_status()

                    if 'error' not in status:
                        used_percent = status['system']['used_percent']
                        self.memory_stats['peak_usage'] = max(self.memory_stats['peak_usage'], used_percent)

                        if status['thresholds']['emergency']:
                            logger.critical(f"EMERGENCY: Memory usage at {used_percent:.1f}%")
                            self.emergency_memory_cleanup()

                        elif status['thresholds']['critical']:
                            logger.error(f"CRITICAL: Memory usage at {used_percent:.1f}%")
                            gc.collect()
                            self.memory_stats['gc_collections'] += 1

                        elif status['thresholds']['warning']:
                            if self.memory_stats['warnings_issued'] % 10 == 0:  # Log every 10th warning
                                logger.warning(f"WARNING: Memory usage at {used_percent:.1f}%")
                            self.memory_stats['warnings_issued'] += 1

                    time.sleep(interval)

                except Exception as e:
                    logger.error(f"Error in memory monitoring: {e}")
                    time.sleep(interval)

        self.monitor_thread = threading.Thread(target=monitor_loop, daemon=True)
        self.monitor_thread.start()

    def stop_memory_monitoring(self):
        """Stop memory monitoring"""
        self.monitoring_active = False

        if self.monitor_thread and self.monitor_thread.is_alive():
            self.monitor_thread.join(timeout=2)

        logger.info("Memory monitoring stopped")

    def get_optimization_recommendations(self) -> Dict[str, Any]:
        """Get memory optimization recommendations"""
        status = self.get_memory_status()

        if 'error' in status:
            return {'error': status['error']}

        recommendations = {
            'system_status': 'good',
            'recommendations': [],
            'critical_actions': []
        }

        used_percent = status['system']['used_percent']

        if used_percent > 90:
            recommendations['system_status'] = 'critical'
            recommendations['critical_actions'].extend([
                'Immediately stop non-essential processes',
                'Reduce AI model complexity',
                'Lower camera resolution/framerate',
                'Enable swap if not active'
            ])

        elif used_percent > 80:
            recommendations['system_status'] = 'warning'
            recommendations['recommendations'].extend([
                'Monitor memory usage closely',
                'Consider reducing batch sizes',
                'Enable more aggressive garbage collection',
                'Optimize model inference settings'
            ])

        elif used_percent > 70:
            recommendations['recommendations'].extend([
                'Good memory usage, continue monitoring',
                'Consider memory optimizations for better headroom'
            ])

        else:
            recommendations['recommendations'].append('Memory usage is optimal')

        # GPU-specific recommendations
        gpu_percent = status['gpu']['usage_percent']
        if gpu_percent > 80:
            recommendations['recommendations'].append('Consider reducing GPU memory usage (smaller models, lower precision)')

        # Swap recommendations
        if status['swap']['used_percent'] > 50:
            recommendations['recommendations'].append('High swap usage detected - consider adding more RAM or optimizing memory usage')

        return recommendations

    def create_memory_report(self) -> Dict[str, Any]:
        """Generate comprehensive memory report"""
        status = self.get_memory_status()
        recommendations = self.get_optimization_recommendations()

        return {
            'timestamp': time.time(),
            'memory_status': status,
            'recommendations': recommendations,
            'statistics': self.memory_stats.copy(),
            'orin_nano_optimized': True
        }

# Global memory optimizer instance
memory_optimizer = OrinNanoMemoryOptimizer()

# Convenience functions
def optimize_memory():
    """Apply memory optimizations"""
    memory_optimizer.optimize_memory_for_ai_workload()

def start_monitoring(interval: float = 5.0):
    """Start memory monitoring"""
    memory_optimizer.start_memory_monitoring(interval)

def stop_monitoring():
    """Stop memory monitoring"""
    memory_optimizer.stop_memory_monitoring()

def get_memory_status():
    """Get current memory status"""
    return memory_optimizer.get_memory_status()

def emergency_cleanup():
    """Perform emergency memory cleanup"""
    memory_optimizer.emergency_memory_cleanup()

def get_recommendations():
    """Get memory optimization recommendations"""
    return memory_optimizer.get_optimization_recommendations()

def main():
    """Test memory optimizer"""
    print("🧠 Orin Nano Memory Optimizer Test")
    print("=" * 40)

    # Apply optimizations
    optimize_memory()

    # Get status
    status = get_memory_status()
    if 'error' not in status:
        print(f"System Memory: {status['system']['used_percent']:.1f}% used")
        print(f"Available: {status['system']['available_gb']:.1f}GB")
        print(f"Process RSS: {status['process']['rss_mb']:.1f}MB")
        print(f"Est. GPU Usage: {status['gpu']['estimated_usage_mb']:.1f}MB")

        # Get recommendations
        rec = get_recommendations()
        print(f"System Status: {rec['system_status']}")

        if rec['recommendations']:
            print("Recommendations:")
            for r in rec['recommendations']:
                print(f"  • {r}")

        if rec['critical_actions']:
            print("Critical Actions Needed:")
            for a in rec['critical_actions']:
                print(f"  ⚠️ {a}")

    # Test monitoring briefly
    print("\nStarting brief monitoring test...")
    start_monitoring(1.0)
    time.sleep(5)
    stop_monitoring()

    print("Memory optimizer test completed")

if __name__ == "__main__":
    main()