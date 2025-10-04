#!/usr/bin/env python3
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
