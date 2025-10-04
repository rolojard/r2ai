#!/usr/bin/env python3
"""
Agent Stability Guidelines for R2D2 Project
Comprehensive guidelines and utilities for preventing crashes and ensuring stable operation
"""

import logging
import threading
import time
import psutil
import os
from typing import Dict, List, Any, Callable
from functools import wraps
from contextlib import contextmanager

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class AgentStabilityManager:
    """Central stability manager for all agents"""

    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super(AgentStabilityManager, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        if hasattr(self, '_initialized'):
            return

        self._initialized = True
        self.active_operations = {}
        self.resource_locks = {}
        self.error_counts = {}
        self.stability_metrics = {
            'total_operations': 0,
            'successful_operations': 0,
            'failed_operations': 0,
            'resource_conflicts': 0,
            'memory_warnings': 0,
            'recovery_actions': 0
        }

    def register_operation(self, operation_id: str, agent_name: str, resource_type: str):
        """Register an operation with the stability manager"""
        with self._lock:
            self.active_operations[operation_id] = {
                'agent': agent_name,
                'resource_type': resource_type,
                'start_time': time.time(),
                'status': 'active'
            }
            self.stability_metrics['total_operations'] += 1

    def complete_operation(self, operation_id: str, success: bool = True):
        """Complete an operation"""
        with self._lock:
            if operation_id in self.active_operations:
                operation = self.active_operations[operation_id]
                operation['status'] = 'completed' if success else 'failed'
                operation['end_time'] = time.time()

                if success:
                    self.stability_metrics['successful_operations'] += 1
                else:
                    self.stability_metrics['failed_operations'] += 1

                del self.active_operations[operation_id]

    @contextmanager
    def managed_operation(self, operation_id: str, agent_name: str, resource_type: str):
        """Context manager for managed operations"""
        self.register_operation(operation_id, agent_name, resource_type)
        success = False

        try:
            yield
            success = True
        finally:
            self.complete_operation(operation_id, success)

# Global stability manager
stability_manager = AgentStabilityManager()

class AgentStabilityGuidelines:
    """Comprehensive stability guidelines for agents"""

    @staticmethod
    def get_camera_access_guidelines() -> Dict[str, Any]:
        """Guidelines for safe camera access"""
        return {
            'title': 'Camera Access Safety Guidelines',
            'critical_rules': [
                'ALWAYS use the camera resource manager for exclusive access',
                'NEVER open multiple camera instances simultaneously',
                'ALWAYS release cameras in finally blocks or context managers',
                'CHECK system resources before initializing cameras',
                'IMPLEMENT timeout mechanisms for camera operations'
            ],
            'recommended_patterns': {
                'safe_camera_access': '''
# CORRECT: Use resource manager
from orin_nano_camera_resource_manager import acquire_camera

with acquire_camera(0) as camera:
    ret, frame = camera.read()
    # Process frame
# Camera automatically released
''',
                'unsafe_camera_access': '''
# WRONG: Direct camera access without coordination
camera = cv2.VideoCapture(0)  # Risk of conflicts
ret, frame = camera.read()
# Might forget to release!
''',
                'error_handling': '''
# CORRECT: Proper error handling
try:
    with acquire_camera(0) as camera:
        for i in range(100):
            ret, frame = camera.read()
            if not ret:
                logger.warning(f"Frame capture failed at {i}")
                break
            # Process frame
except Exception as e:
    logger.error(f"Camera operation failed: {e}")
    # Handle gracefully
'''
            },
            'system_checks': [
                'Check memory usage before camera operations',
                'Verify camera availability with get_available_cameras()',
                'Monitor system health during long operations',
                'Implement graceful degradation for resource constraints'
            ],
            'error_recovery': [
                'Implement retry logic with exponential backoff',
                'Use emergency cleanup for memory issues',
                'Log errors with context for debugging',
                'Fail gracefully without crashing the system'
            ]
        }

    @staticmethod
    def get_memory_management_guidelines() -> Dict[str, Any]:
        """Guidelines for memory management"""
        return {
            'title': 'Memory Management Guidelines',
            'critical_rules': [
                'ALWAYS monitor memory usage in long-running processes',
                'IMPLEMENT memory limits and cleanup mechanisms',
                'USE garbage collection strategically',
                'LIMIT batch sizes and model complexity based on available memory',
                'DETECT and respond to memory pressure'
            ],
            'recommended_patterns': {
                'memory_monitoring': '''
# CORRECT: Monitor memory usage
from orin_nano_memory_optimizer import get_memory_status, emergency_cleanup

def process_with_memory_check():
    memory_status = get_memory_status()
    if memory_status['system']['used_percent'] > 80:
        logger.warning("High memory usage, performing cleanup")
        emergency_cleanup()

    # Proceed with processing
''',
                'batch_processing': '''
# CORRECT: Adaptive batch processing
def process_frames_adaptively(frames):
    memory_status = get_memory_status()

    if memory_status['system']['used_percent'] > 75:
        batch_size = 1  # Process one at a time
    elif memory_status['system']['used_percent'] > 60:
        batch_size = 5
    else:
        batch_size = 10

    for i in range(0, len(frames), batch_size):
        batch = frames[i:i+batch_size]
        process_batch(batch)

        # Check memory after each batch
        if get_memory_status()['system']['used_percent'] > 85:
            emergency_cleanup()
'''
            },
            'optimization_techniques': [
                'Use memory-mapped files for large datasets',
                'Implement lazy loading for models and data',
                'Use lower precision (float16) when possible',
                'Clear unused variables and intermediate results',
                'Limit model complexity based on available memory'
            ]
        }

    @staticmethod
    def get_error_handling_guidelines() -> Dict[str, Any]:
        """Guidelines for robust error handling"""
        return {
            'title': 'Error Handling and Recovery Guidelines',
            'critical_rules': [
                'NEVER let exceptions crash the entire system',
                'IMPLEMENT graceful degradation for all components',
                'LOG errors with sufficient context for debugging',
                'USE circuit breaker patterns for unstable components',
                'IMPLEMENT automatic recovery mechanisms'
            ],
            'recommended_patterns': {
                'robust_operation': '''
# CORRECT: Robust operation with retry logic
def robust_ai_inference(model, input_data, max_retries=3):
    for attempt in range(max_retries):
        try:
            # Check system health
            memory_status = get_memory_status()
            if memory_status['system']['used_percent'] > 90:
                emergency_cleanup()

            # Perform inference
            result = model(input_data)
            return result

        except torch.cuda.OutOfMemoryError:
            logger.error(f"GPU memory error on attempt {attempt + 1}")
            torch.cuda.empty_cache()
            emergency_cleanup()

        except Exception as e:
            logger.error(f"Inference failed on attempt {attempt + 1}: {e}")
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)  # Exponential backoff

    logger.error("All inference attempts failed")
    return None  # Graceful failure
''',
                'circuit_breaker': '''
# CORRECT: Circuit breaker for unstable components
class CircuitBreaker:
    def __init__(self, failure_threshold=5, timeout=30):
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.failure_count = 0
        self.last_failure_time = 0
        self.state = 'closed'  # closed, open, half-open

    def call(self, func, *args, **kwargs):
        if self.state == 'open':
            if time.time() - self.last_failure_time > self.timeout:
                self.state = 'half-open'
            else:
                raise Exception("Circuit breaker is open")

        try:
            result = func(*args, **kwargs)
            if self.state == 'half-open':
                self.state = 'closed'
                self.failure_count = 0
            return result

        except Exception as e:
            self.failure_count += 1
            self.last_failure_time = time.time()

            if self.failure_count >= self.failure_threshold:
                self.state = 'open'

            raise
'''
            }
        }

    @staticmethod
    def get_threading_guidelines() -> Dict[str, Any]:
        """Guidelines for safe threading"""
        return {
            'title': 'Threading and Concurrency Guidelines',
            'critical_rules': [
                'AVOID race conditions with proper locking',
                'USE thread-safe queues for inter-thread communication',
                'IMPLEMENT proper thread shutdown mechanisms',
                'LIMIT the number of concurrent threads',
                'AVOID deadlocks with consistent lock ordering'
            ],
            'recommended_patterns': {
                'safe_threading': '''
# CORRECT: Thread-safe producer-consumer
import queue
import threading

class SafeVideoProcessor:
    def __init__(self):
        self.frame_queue = queue.Queue(maxsize=10)
        self.result_queue = queue.Queue(maxsize=5)
        self.running = False
        self.threads = []

    def start(self):
        self.running = True

        # Producer thread
        producer = threading.Thread(target=self._capture_frames, daemon=True)
        producer.start()
        self.threads.append(producer)

        # Consumer thread
        consumer = threading.Thread(target=self._process_frames, daemon=True)
        consumer.start()
        self.threads.append(consumer)

    def stop(self):
        self.running = False

        # Wait for threads to finish
        for thread in self.threads:
            thread.join(timeout=2)

    def _capture_frames(self):
        with acquire_camera(0) as camera:
            while self.running:
                ret, frame = camera.read()
                if ret:
                    try:
                        self.frame_queue.put_nowait(frame)
                    except queue.Full:
                        # Drop oldest frame
                        try:
                            self.frame_queue.get_nowait()
                            self.frame_queue.put_nowait(frame)
                        except queue.Empty:
                            pass

    def _process_frames(self):
        while self.running:
            try:
                frame = self.frame_queue.get(timeout=0.1)
                # Process frame
                result = self._process_single_frame(frame)

                try:
                    self.result_queue.put_nowait(result)
                except queue.Full:
                    try:
                        self.result_queue.get_nowait()
                        self.result_queue.put_nowait(result)
                    except queue.Empty:
                        pass

            except queue.Empty:
                continue
'''
            }
        }

    @staticmethod
    def get_resource_management_guidelines() -> Dict[str, Any]:
        """Guidelines for resource management"""
        return {
            'title': 'System Resource Management Guidelines',
            'critical_rules': [
                'MONITOR system resources continuously',
                'IMPLEMENT resource quotas and limits',
                'USE context managers for resource cleanup',
                'DETECT resource exhaustion early',
                'IMPLEMENT graceful degradation under resource pressure'
            ],
            'system_monitoring': [
                'Monitor CPU usage and implement throttling',
                'Track memory usage and perform cleanup when needed',
                'Monitor GPU utilization and memory',
                'Watch thermal status and implement cooling delays',
                'Track disk space and implement cleanup'
            ],
            'resource_limits': {
                'memory_usage': '< 80% for normal operation, < 85% warning, > 90% emergency',
                'cpu_usage': '< 90% sustained, implement throttling if exceeded',
                'gpu_memory': '< 80% for stable operation',
                'thread_count': '< 20 threads per agent process',
                'file_descriptors': 'Monitor and cleanup unused FDs'
            }
        }

def create_stability_decorator(resource_type: str = 'generic'):
    """Decorator for adding stability monitoring to functions"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            operation_id = f"{func.__name__}_{int(time.time() * 1000)}"

            with stability_manager.managed_operation(operation_id, 'unknown', resource_type):
                # Pre-execution checks
                memory_status = None
                try:
                    from orin_nano_memory_optimizer import get_memory_status
                    memory_status = get_memory_status()

                    if 'error' not in memory_status:
                        if memory_status['system']['used_percent'] > 85:
                            logger.warning(f"High memory usage ({memory_status['system']['used_percent']:.1f}%) before {func.__name__}")

                except ImportError:
                    pass

                # Execute function
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    logger.error(f"Function {func.__name__} failed: {e}")

                    # Emergency cleanup if memory-related
                    if 'memory' in str(e).lower() or 'allocation' in str(e).lower():
                        try:
                            from orin_nano_memory_optimizer import emergency_cleanup
                            emergency_cleanup()
                            stability_manager.stability_metrics['recovery_actions'] += 1
                        except ImportError:
                            pass

                    raise

        return wrapper
    return decorator

# Convenience decorators
stable_vision = create_stability_decorator('vision')
stable_ai = create_stability_decorator('ai')
stable_servo = create_stability_decorator('servo')
stable_network = create_stability_decorator('network')

class AgentHealthMonitor:
    """Health monitoring for agent processes"""

    def __init__(self, agent_name: str):
        self.agent_name = agent_name
        self.start_time = time.time()
        self.health_metrics = {
            'cpu_usage': [],
            'memory_usage': [],
            'error_count': 0,
            'last_heartbeat': time.time()
        }

    def update_heartbeat(self):
        """Update agent heartbeat"""
        self.health_metrics['last_heartbeat'] = time.time()

    def record_error(self, error: Exception):
        """Record an error"""
        self.health_metrics['error_count'] += 1
        logger.error(f"Agent {self.agent_name} error: {error}")

    def get_health_status(self) -> Dict[str, Any]:
        """Get current health status"""
        try:
            process = psutil.Process()
            cpu_percent = process.cpu_percent()
            memory_mb = process.memory_info().rss / (1024 ** 2)

            self.health_metrics['cpu_usage'].append(cpu_percent)
            self.health_metrics['memory_usage'].append(memory_mb)

            # Keep only last 100 measurements
            if len(self.health_metrics['cpu_usage']) > 100:
                self.health_metrics['cpu_usage'] = self.health_metrics['cpu_usage'][-100:]
                self.health_metrics['memory_usage'] = self.health_metrics['memory_usage'][-100:]

            uptime = time.time() - self.start_time
            avg_cpu = sum(self.health_metrics['cpu_usage']) / len(self.health_metrics['cpu_usage'])
            avg_memory = sum(self.health_metrics['memory_usage']) / len(self.health_metrics['memory_usage'])

            return {
                'agent_name': self.agent_name,
                'uptime_seconds': uptime,
                'cpu_percent': cpu_percent,
                'memory_mb': memory_mb,
                'avg_cpu_percent': avg_cpu,
                'avg_memory_mb': avg_memory,
                'error_count': self.health_metrics['error_count'],
                'last_heartbeat': self.health_metrics['last_heartbeat'],
                'status': self._calculate_status(cpu_percent, memory_mb, uptime)
            }

        except Exception as e:
            logger.error(f"Error getting health status: {e}")
            return {'agent_name': self.agent_name, 'status': 'unknown', 'error': str(e)}

    def _calculate_status(self, cpu_percent: float, memory_mb: float, uptime: float) -> str:
        """Calculate overall agent status"""
        if cpu_percent > 90 or memory_mb > 2000:  # High resource usage
            return 'critical'
        elif cpu_percent > 70 or memory_mb > 1500:
            return 'warning'
        elif uptime > 3600:  # Running for over an hour
            return 'needs_restart'
        else:
            return 'healthy'

def get_agent_stability_report() -> Dict[str, Any]:
    """Generate comprehensive stability report for all agents"""
    return {
        'timestamp': time.time(),
        'system_status': {
            'cpu_percent': psutil.cpu_percent(),
            'memory_percent': psutil.virtual_memory().percent,
            'available_memory_gb': psutil.virtual_memory().available / (1024 ** 3)
        },
        'stability_metrics': stability_manager.stability_metrics.copy(),
        'active_operations': len(stability_manager.active_operations),
        'guidelines_version': '1.0',
        'recommendations': _generate_recommendations()
    }

def _generate_recommendations() -> List[str]:
    """Generate stability recommendations based on current state"""
    recommendations = []

    try:
        # System resource recommendations
        memory_percent = psutil.virtual_memory().percent
        cpu_percent = psutil.cpu_percent()

        if memory_percent > 85:
            recommendations.append("CRITICAL: Memory usage high - implement immediate cleanup")
        elif memory_percent > 75:
            recommendations.append("WARNING: Memory usage elevated - monitor closely")

        if cpu_percent > 90:
            recommendations.append("CRITICAL: CPU usage very high - reduce workload")
        elif cpu_percent > 75:
            recommendations.append("INFO: CPU usage elevated - consider optimization")

        # Stability metrics recommendations
        metrics = stability_manager.stability_metrics
        if metrics['total_operations'] > 0:
            failure_rate = metrics['failed_operations'] / metrics['total_operations']
            if failure_rate > 0.1:
                recommendations.append(f"WARNING: High failure rate ({failure_rate:.1%}) - investigate error patterns")
            elif failure_rate > 0.05:
                recommendations.append(f"INFO: Moderate failure rate ({failure_rate:.1%}) - monitor trends")

        if not recommendations:
            recommendations.append("System operating within normal parameters")

    except Exception as e:
        recommendations.append(f"Error generating recommendations: {e}")

    return recommendations

def main():
    """Test the stability guidelines system"""
    print("🛡️ Agent Stability Guidelines System")
    print("=" * 50)

    # Display all guidelines
    guidelines = AgentStabilityGuidelines()

    sections = [
        guidelines.get_camera_access_guidelines(),
        guidelines.get_memory_management_guidelines(),
        guidelines.get_error_handling_guidelines(),
        guidelines.get_threading_guidelines(),
        guidelines.get_resource_management_guidelines()
    ]

    for section in sections:
        print(f"\n📋 {section['title']}")
        print("-" * len(section['title']))

        if 'critical_rules' in section:
            print("\nCRITICAL RULES:")
            for rule in section['critical_rules']:
                print(f"  ⚠️ {rule}")

    # Generate stability report
    report = get_agent_stability_report()
    print(f"\n📊 CURRENT SYSTEM STATUS:")
    print(f"  CPU: {report['system_status']['cpu_percent']:.1f}%")
    print(f"  Memory: {report['system_status']['memory_percent']:.1f}%")
    print(f"  Available Memory: {report['system_status']['available_memory_gb']:.1f}GB")

    print(f"\n🔍 RECOMMENDATIONS:")
    for rec in report['recommendations']:
        print(f"  • {rec}")

if __name__ == "__main__":
    main()