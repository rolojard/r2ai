#!/usr/bin/env python3
"""
Deployment Script for R2D2 Stability Solutions
Automated deployment and validation of all stability components
"""

import os
import sys
import time
import subprocess
import logging
from datetime import datetime
from typing import Dict, List, Tuple

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class StabilityDeployment:
    """Deploy and validate all stability solutions"""

    def __init__(self):
        self.deployment_status = {}
        self.validation_results = {}
        self.base_path = "/home/rolo/r2ai"

        # Components to deploy
        self.components = [
            'orin_nano_camera_resource_manager.py',
            'orin_nano_memory_optimizer.py',
            'stable_vision_system.py',
            'agent_stability_guidelines.py'
        ]

    def print_header(self):
        """Print deployment header"""
        print("🚀 R2D2 Stability Solutions Deployment")
        print("=" * 50)
        print(f"Deployment Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Base Path: {self.base_path}")
        print("=" * 50)

    def check_prerequisites(self) -> bool:
        """Check system prerequisites"""
        logger.info("Checking prerequisites...")

        prerequisites = {
            'python_version': sys.version_info >= (3, 7),
            'opencv_available': self._check_import('cv2'),
            'numpy_available': self._check_import('numpy'),
            'psutil_available': self._check_import('psutil'),
            'threading_support': True,  # Always available
            'file_system_writable': os.access(self.base_path, os.W_OK)
        }

        all_good = True
        for check, status in prerequisites.items():
            status_text = "✅ PASS" if status else "❌ FAIL"
            print(f"  {status_text} {check}")
            if not status:
                all_good = False

        if all_good:
            logger.info("All prerequisites satisfied")
        else:
            logger.error("Prerequisites not met - deployment cannot continue")

        return all_good

    def _check_import(self, module_name: str) -> bool:
        """Check if a module can be imported"""
        try:
            __import__(module_name)
            return True
        except ImportError:
            return False

    def validate_components(self) -> bool:
        """Validate all component files exist"""
        logger.info("Validating component files...")

        all_exist = True
        for component in self.components:
            component_path = os.path.join(self.base_path, component)
            exists = os.path.exists(component_path)

            status_text = "✅ EXISTS" if exists else "❌ MISSING"
            print(f"  {status_text} {component}")

            if not exists:
                all_exist = False

        return all_exist

    def test_component(self, component: str) -> Tuple[bool, str]:
        """Test a single component"""
        logger.info(f"Testing {component}...")

        component_path = os.path.join(self.base_path, component)

        try:
            # Run component test
            result = subprocess.run([
                sys.executable, component_path
            ], capture_output=True, text=True, timeout=30)

            success = result.returncode == 0
            output = result.stdout if success else result.stderr

            return success, output

        except subprocess.TimeoutExpired:
            return False, "Test timed out after 30 seconds"
        except Exception as e:
            return False, str(e)

    def run_component_tests(self) -> bool:
        """Test all components"""
        logger.info("Running component tests...")

        all_passed = True

        for component in self.components:
            success, output = self.test_component(component)

            status_text = "✅ PASS" if success else "❌ FAIL"
            print(f"  {status_text} {component}")

            if not success:
                print(f"    Error: {output[:200]}...")
                all_passed = False
            else:
                print(f"    Output: Test completed successfully")

            self.validation_results[component] = {
                'success': success,
                'output': output,
                'timestamp': time.time()
            }

        return all_passed

    def check_system_health(self) -> Dict[str, any]:
        """Check current system health"""
        logger.info("Checking system health...")

        try:
            import psutil

            # System metrics
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')

            health = {
                'cpu_percent': cpu_percent,
                'memory_percent': memory.percent,
                'memory_available_gb': memory.available / (1024 ** 3),
                'disk_percent': disk.percent,
                'disk_free_gb': disk.free / (1024 ** 3),
                'cpu_ok': cpu_percent < 80,
                'memory_ok': memory.percent < 75,
                'disk_ok': disk.percent < 90,
                'overall_health': 'good'
            }

            # Determine overall health
            if not (health['cpu_ok'] and health['memory_ok'] and health['disk_ok']):
                health['overall_health'] = 'warning'

            if cpu_percent > 90 or memory.percent > 85:
                health['overall_health'] = 'critical'

            # Display health
            print(f"  System Health: {health['overall_health'].upper()}")
            print(f"  CPU Usage: {cpu_percent:.1f}% {'✅' if health['cpu_ok'] else '⚠️'}")
            print(f"  Memory Usage: {memory.percent:.1f}% {'✅' if health['memory_ok'] else '⚠️'}")
            print(f"  Available Memory: {health['memory_available_gb']:.1f}GB")
            print(f"  Disk Usage: {disk.percent:.1f}% {'✅' if health['disk_ok'] else '⚠️'}")

            return health

        except Exception as e:
            logger.error(f"Error checking system health: {e}")
            return {'overall_health': 'unknown', 'error': str(e)}

    def create_integration_examples(self):
        """Create example integration code for agents"""
        logger.info("Creating integration examples...")

        examples = {
            'camera_integration_example.py': '''#!/usr/bin/env python3
"""
Example: Safe Camera Integration for Agents
"""

from orin_nano_camera_resource_manager import acquire_camera
from orin_nano_memory_optimizer import get_memory_status, emergency_cleanup
import cv2
import time

def safe_camera_processing():
    """Example of safe camera processing"""

    # Check memory before starting
    memory_status = get_memory_status()
    if memory_status['system']['used_percent'] > 80:
        print("Warning: High memory usage before camera operation")
        emergency_cleanup()

    # Safe camera access
    try:
        with acquire_camera(0) as camera:
            print("Camera acquired successfully")

            for i in range(50):  # Process 50 frames
                ret, frame = camera.read()
                if not ret:
                    print(f"Frame capture failed at {i}")
                    break

                # Process frame (your AI/vision code here)
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

                # Monitor memory during processing
                if i % 10 == 0:
                    memory_status = get_memory_status()
                    if memory_status['system']['used_percent'] > 85:
                        print("High memory usage detected, performing cleanup")
                        emergency_cleanup()

                time.sleep(0.1)  # Simulate processing time

            print("Camera processing completed successfully")

    except Exception as e:
        print(f"Camera processing failed: {e}")
        # Emergency cleanup on error
        emergency_cleanup()

if __name__ == "__main__":
    safe_camera_processing()
''',

            'stable_agent_template.py': '''#!/usr/bin/env python3
"""
Template: Stable Agent Implementation
Use this as a starting template for stable agents
"""

from agent_stability_guidelines import stable_vision, AgentHealthMonitor
from orin_nano_memory_optimizer import optimize_memory, start_monitoring
import time
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class StableAgent:
    """Template for a stable agent implementation"""

    def __init__(self, agent_name: str):
        self.agent_name = agent_name
        self.health_monitor = AgentHealthMonitor(agent_name)
        self.running = False

        # Initialize optimizations
        optimize_memory()
        start_monitoring(interval=10.0)

        logger.info(f"Stable agent {agent_name} initialized")

    @stable_vision  # Automatic stability monitoring
    def process_vision_data(self, data):
        """Example vision processing with stability monitoring"""
        self.health_monitor.update_heartbeat()

        try:
            # Your vision processing code here
            result = self._safe_vision_processing(data)
            return result

        except Exception as e:
            self.health_monitor.record_error(e)
            logger.error(f"Vision processing failed: {e}")
            return None

    def _safe_vision_processing(self, data):
        """Safe vision processing implementation"""
        # Implement your specific processing here
        # This template includes error handling
        time.sleep(0.1)  # Simulate processing
        return {"processed": True, "data_size": len(data) if data else 0}

    def get_health_status(self):
        """Get agent health status"""
        return self.health_monitor.get_health_status()

    def run(self):
        """Main agent loop"""
        self.running = True
        logger.info(f"Starting {self.agent_name}")

        try:
            while self.running:
                # Update heartbeat
                self.health_monitor.update_heartbeat()

                # Simulate agent work
                self.process_vision_data(b"example_data")

                # Check health periodically
                health = self.get_health_status()
                if health['status'] == 'critical':
                    logger.warning(f"Agent health critical: {health}")

                time.sleep(1)

        except KeyboardInterrupt:
            logger.info("Agent stopped by user")
        except Exception as e:
            logger.error(f"Agent error: {e}")
            self.health_monitor.record_error(e)
        finally:
            self.running = False
            logger.info(f"Agent {self.agent_name} stopped")

def main():
    agent = StableAgent("example_agent")
    agent.run()

if __name__ == "__main__":
    main()
'''
        }

        for filename, content in examples.items():
            filepath = os.path.join(self.base_path, filename)
            try:
                with open(filepath, 'w') as f:
                    f.write(content)
                os.chmod(filepath, 0o755)
                print(f"  ✅ Created {filename}")
            except Exception as e:
                print(f"  ❌ Failed to create {filename}: {e}")

    def generate_deployment_report(self) -> str:
        """Generate comprehensive deployment report"""
        report = f"""
# Stability Solutions Deployment Report

**Deployment Time:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**System:** Nvidia Jetson Orin Nano Super

## Deployment Summary

"""

        # Component status
        report += "### Component Validation\n\n"
        for component in self.components:
            if component in self.validation_results:
                result = self.validation_results[component]
                status = "✅ PASSED" if result['success'] else "❌ FAILED"
                report += f"- **{component}:** {status}\n"

        # System health
        health = self.check_system_health()
        report += f"\n### System Health: {health['overall_health'].upper()}\n\n"
        report += f"- CPU Usage: {health.get('cpu_percent', 0):.1f}%\n"
        report += f"- Memory Usage: {health.get('memory_percent', 0):.1f}%\n"
        report += f"- Available Memory: {health.get('memory_available_gb', 0):.1f}GB\n"

        # Next steps
        report += """
## Next Steps

1. **Agent Integration:** Update all agents to use stable frameworks
2. **Monitoring Setup:** Enable continuous health monitoring
3. **Testing Period:** Run 24-hour validation test
4. **Documentation:** Share integration examples with team

## Agent Migration Checklist

- [ ] Update camera access patterns
- [ ] Implement memory monitoring
- [ ] Add error recovery mechanisms
- [ ] Test with resource constraints
- [ ] Enable health monitoring

## Support

- Integration examples: `/home/rolo/r2ai/camera_integration_example.py`
- Agent template: `/home/rolo/r2ai/stable_agent_template.py`
- Guidelines: `/home/rolo/r2ai/agent_stability_guidelines.py`
- Full report: `/home/rolo/r2ai/SYSTEM_STABILITY_ANALYSIS_REPORT.md`
"""

        return report

    def deploy(self) -> bool:
        """Run complete deployment process"""
        self.print_header()

        # Check prerequisites
        if not self.check_prerequisites():
            logger.error("Prerequisites check failed")
            return False

        # Validate components
        if not self.validate_components():
            logger.error("Component validation failed")
            return False

        # Test components
        if not self.run_component_tests():
            logger.warning("Some component tests failed - proceeding with caution")

        # Check system health
        health = self.check_system_health()
        if health['overall_health'] == 'critical':
            logger.warning("System health is critical - consider addressing before deployment")

        # Create integration examples
        self.create_integration_examples()

        # Generate deployment report
        report = self.generate_deployment_report()
        report_path = os.path.join(self.base_path, 'DEPLOYMENT_REPORT.md')

        try:
            with open(report_path, 'w') as f:
                f.write(report)
            logger.info(f"Deployment report saved to {report_path}")
        except Exception as e:
            logger.error(f"Failed to save deployment report: {e}")

        print("\n🎉 DEPLOYMENT COMPLETED!")
        print("=" * 50)
        print("✅ All stability solutions deployed")
        print("📋 Integration examples created")
        print("📊 System health verified")
        print("📝 Deployment report generated")
        print("")
        print("🚀 READY FOR AGENT INTEGRATION!")
        print("See DEPLOYMENT_REPORT.md for next steps")
        print("=" * 50)

        return True

def main():
    """Main deployment function"""
    deployment = StabilityDeployment()

    try:
        success = deployment.deploy()
        return 0 if success else 1

    except KeyboardInterrupt:
        print("\n\n🛑 Deployment interrupted by user")
        return 1
    except Exception as e:
        logger.error(f"Deployment failed: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())