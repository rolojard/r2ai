#!/usr/bin/env python3
"""
Session Continuity Control Center
=================================

Master control system for session continuity protocols, integrating all
components for seamless session management and agent coordination.

Created: 2025-09-19
Author: Project Manager Agent
Purpose: Central control system for comprehensive session continuity
"""

import sys
import os
import json
import time
import datetime
from pathlib import Path
import logging
from typing import Dict, List, Any, Optional

# Add the project paths to sys.path for imports
sys.path.append(str(Path(__file__).parent))
sys.path.append(str(Path(__file__).parent / "session_continuity"))
sys.path.append(str(Path(__file__).parent / "memory_persistence"))
sys.path.append(str(Path(__file__).parent / "task_resumption"))
sys.path.append(str(Path(__file__).parent / "coordination_protocols"))
sys.path.append(str(Path(__file__).parent / "monitoring"))

from session_continuity_framework import SessionContinuityFramework
from memory_persistence_manager import MemoryPersistenceManager
from task_resumption_protocols import TaskResumptionProtocols
from multi_agent_coordinator import MultiAgentCoordinator
from session_monitoring_dashboard import SessionMonitoringDashboard

class SessionContinuityController:
    """
    Master controller for all session continuity operations
    """

    def __init__(self, base_path="/home/rolo/r2ai/.claude"):
        self.base_path = Path(base_path)

        # Initialize all subsystems
        self.framework = SessionContinuityFramework(base_path)
        self.memory_manager = MemoryPersistenceManager(base_path)
        self.task_protocols = TaskResumptionProtocols(base_path)
        self.coordinator = MultiAgentCoordinator(base_path)
        self.monitor = SessionMonitoringDashboard(base_path)

        # Setup logging
        self.setup_logging()

        # Control state
        self.control_state = {
            "initialized": datetime.datetime.now().isoformat(),
            "active_protocols": [],
            "last_health_check": None,
            "handoff_prepared": False,
            "emergency_mode": False
        }

    def setup_logging(self):
        """Setup centralized logging"""
        log_dir = self.base_path / "logs"
        log_dir.mkdir(exist_ok=True)

        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_dir / "session_continuity.log"),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger("SessionContinuityController")

    def initialize_all_systems(self) -> Dict[str, Any]:
        """Initialize all session continuity systems"""
        self.logger.info("Initializing session continuity systems...")

        initialization_result = {
            "timestamp": datetime.datetime.now().isoformat(),
            "systems": {},
            "overall_success": True,
            "errors": []
        }

        # Initialize each subsystem
        systems = [
            ("framework", self.framework),
            ("memory_manager", self.memory_manager),
            ("task_protocols", self.task_protocols),
            ("coordinator", self.coordinator),
            ("monitor", self.monitor)
        ]

        for system_name, system in systems:
            try:
                # Check if system has an initialize method
                if hasattr(system, 'initialize'):
                    result = system.initialize()
                else:
                    result = {"status": "initialized", "message": f"{system_name} ready"}

                initialization_result["systems"][system_name] = {
                    "status": "success",
                    "details": result
                }
                self.control_state["active_protocols"].append(system_name)

            except Exception as e:
                self.logger.error(f"Failed to initialize {system_name}: {e}")
                initialization_result["systems"][system_name] = {
                    "status": "failed",
                    "error": str(e)
                }
                initialization_result["overall_success"] = False
                initialization_result["errors"].append(f"{system_name}: {e}")

        # Initialize agent memories if needed
        try:
            agent_names = [
                "project-manager", "super-coder", "star-wars-specialist",
                "web-dev-specialist", "ux-dev-specialist", "qa-tester",
                "nvidia-orin-nano-specialist", "video-model-trainer", "imagineer-specialist"
            ]

            for agent_name in agent_names:
                validation = self.memory_manager.validate_agent_memory(agent_name)
                if not validation["valid"]:
                    self.logger.info(f"Initializing memory for {agent_name}")
                    self.memory_manager.initialize_agent_memory(agent_name)

        except Exception as e:
            self.logger.error(f"Agent memory initialization failed: {e}")
            initialization_result["errors"].append(f"Agent memory: {e}")

        self.logger.info("Session continuity initialization completed")
        return initialization_result

    def perform_health_check(self) -> Dict[str, Any]:
        """Perform comprehensive health check"""
        self.logger.info("Performing system health check...")

        health_check = {
            "timestamp": datetime.datetime.now().isoformat(),
            "session_status": None,
            "agent_health": None,
            "resource_usage": None,
            "quality_metrics": None,
            "coordination_health": None,
            "overall_health": "unknown",
            "recommendations": []
        }

        try:
            # Check session status
            health_check["session_status"] = self.monitor.get_session_status()

            # Check agent health
            health_check["agent_health"] = self.monitor.monitor_agent_health()

            # Check resource usage
            health_check["resource_usage"] = self.monitor.monitor_resource_usage()

            # Check quality metrics
            health_check["quality_metrics"] = self.monitor.get_quality_metrics()

            # Check coordination health
            health_check["coordination_health"] = self.coordinator.monitor_coordination_health()

            # Determine overall health
            health_issues = 0

            # Session health
            if health_check["session_status"]["status"] in ["warning", "critical"]:
                health_issues += 1

            # Agent health
            if health_check["agent_health"]["critical_agents"] > 0:
                health_issues += 2  # Critical agents are serious
            if health_check["agent_health"]["offline_agents"] > 2:
                health_issues += 1

            # Resource health
            resource_status = health_check["resource_usage"]
            if "memory" in resource_status and resource_status["memory"]["status"] == "critical":
                health_issues += 2
            if "disk" in resource_status and resource_status["disk"]["status"] == "critical":
                health_issues += 1

            # Quality health
            if health_check["quality_metrics"]["overall_quality_score"] < 7.0:
                health_issues += 1

            # Determine overall health
            if health_issues == 0:
                health_check["overall_health"] = "excellent"
            elif health_issues <= 2:
                health_check["overall_health"] = "good"
            elif health_issues <= 4:
                health_check["overall_health"] = "warning"
            else:
                health_check["overall_health"] = "critical"

            # Generate recommendations
            recommendations = []

            if health_check["session_status"]["handoff_urgency"] in ["urgent", "immediate"]:
                recommendations.append("Prepare session handoff immediately")

            if health_check["agent_health"]["critical_agents"] > 0:
                recommendations.append("Investigate and restore critical agents")

            if health_check["resource_usage"].get("memory", {}).get("status") == "critical":
                recommendations.append("Clear memory or restart session")

            if health_check["quality_metrics"]["overall_quality_score"] < 8.0:
                recommendations.append("Review and improve quality processes")

            health_check["recommendations"] = recommendations

            self.control_state["last_health_check"] = datetime.datetime.now().isoformat()

        except Exception as e:
            self.logger.error(f"Health check failed: {e}")
            health_check["error"] = str(e)
            health_check["overall_health"] = "error"

        return health_check

    def prepare_session_handoff(self) -> Dict[str, Any]:
        """Prepare comprehensive session handoff"""
        self.logger.info("Preparing session handoff...")

        handoff_result = {
            "timestamp": datetime.datetime.now().isoformat(),
            "preparation_steps": [],
            "success": False,
            "files_created": [],
            "agent_backups": {},
            "handoff_package": {}
        }

        try:
            # Step 1: Create memory backups for all agents
            self.logger.info("Creating agent memory backups...")
            backup_results = {}
            agent_names = [
                "project-manager", "super-coder", "star-wars-specialist",
                "web-dev-specialist", "ux-dev-specialist", "qa-tester",
                "nvidia-orin-nano-specialist", "video-model-trainer", "imagineer-specialist"
            ]

            for agent_name in agent_names:
                try:
                    backup_path = self.memory_manager.create_memory_backup(agent_name)
                    backup_results[agent_name] = backup_path
                except Exception as e:
                    self.logger.error(f"Backup failed for {agent_name}: {e}")
                    backup_results[agent_name] = f"failed: {e}"

            handoff_result["agent_backups"] = backup_results
            handoff_result["preparation_steps"].append("Agent memory backups created")

            # Step 2: Create session snapshot
            self.logger.info("Creating session snapshot...")
            snapshot = self.framework.create_session_snapshot()
            snapshot_file = self.framework.save_session_snapshot(snapshot)
            handoff_result["files_created"].append(snapshot_file)
            handoff_result["preparation_steps"].append("Session snapshot created")

            # Step 3: Create handoff document
            self.logger.info("Creating handoff document...")
            handoff_doc = self.framework.create_handoff_document(snapshot)
            handoff_result["files_created"].append(handoff_doc)
            handoff_result["preparation_steps"].append("Handoff document created")

            # Step 4: Create task resumption plans
            self.logger.info("Creating task resumption plans...")
            global_plan = self.task_protocols.get_global_resumption_plan()
            plan_file = self.base_path / "task_management" / f"global_resumption_plan_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            plan_file.parent.mkdir(exist_ok=True)

            with open(plan_file, 'w') as f:
                json.dump(global_plan, f, indent=2)

            handoff_result["files_created"].append(str(plan_file))
            handoff_result["preparation_steps"].append("Task resumption plans created")

            # Step 5: Create coordination report
            self.logger.info("Creating coordination report...")
            coord_report = self.coordinator.create_coordination_report()
            handoff_result["files_created"].append(coord_report)
            handoff_result["preparation_steps"].append("Coordination report created")

            # Step 6: Create monitoring snapshot
            self.logger.info("Creating monitoring snapshot...")
            monitoring_snapshot = self.monitor.save_monitoring_snapshot()
            handoff_result["files_created"].append(monitoring_snapshot)
            handoff_result["preparation_steps"].append("Monitoring snapshot created")

            # Step 7: Create comprehensive handoff package
            handoff_package = {
                "timestamp": datetime.datetime.now().isoformat(),
                "session_snapshot": snapshot_file,
                "handoff_document": handoff_doc,
                "resumption_plan": str(plan_file),
                "coordination_report": coord_report,
                "monitoring_snapshot": monitoring_snapshot,
                "agent_backups": backup_results,
                "instructions": [
                    "1. Load session snapshot to restore context",
                    "2. Review handoff document for current status",
                    "3. Execute resumption plan to restore agents",
                    "4. Use coordination report to understand workflows",
                    "5. Monitor system health using monitoring data",
                    "6. Restore agent memories from backups if needed"
                ]
            }

            # Save handoff package
            package_file = self.base_path / "session_continuity" / f"handoff_package_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            package_file.parent.mkdir(exist_ok=True)

            with open(package_file, 'w') as f:
                json.dump(handoff_package, f, indent=2)

            handoff_result["handoff_package"] = handoff_package
            handoff_result["files_created"].append(str(package_file))
            handoff_result["preparation_steps"].append("Handoff package created")

            handoff_result["success"] = True
            self.control_state["handoff_prepared"] = True

            self.logger.info("Session handoff preparation completed successfully")

        except Exception as e:
            self.logger.error(f"Handoff preparation failed: {e}")
            handoff_result["error"] = str(e)

        return handoff_result

    def execute_session_restart(self, handoff_package_file: str) -> Dict[str, Any]:
        """Execute session restart using handoff package"""
        self.logger.info(f"Executing session restart from: {handoff_package_file}")

        restart_result = {
            "timestamp": datetime.datetime.now().isoformat(),
            "restart_steps": [],
            "success": False,
            "agents_restored": {},
            "validation_results": {}
        }

        try:
            # Load handoff package
            with open(handoff_package_file, 'r') as f:
                handoff_package = json.load(f)

            restart_result["restart_steps"].append("Handoff package loaded")

            # Step 1: Initialize systems
            init_result = self.initialize_all_systems()
            if not init_result["overall_success"]:
                raise Exception(f"System initialization failed: {init_result['errors']}")

            restart_result["restart_steps"].append("Systems initialized")

            # Step 2: Restore agent memories
            agent_names = [
                "project-manager", "super-coder", "star-wars-specialist",
                "web-dev-specialist", "ux-dev-specialist", "qa-tester",
                "nvidia-orin-nano-specialist", "video-model-trainer", "imagineer-specialist"
            ]

            for agent_name in agent_names:
                if agent_name in handoff_package["agent_backups"]:
                    backup_path = handoff_package["agent_backups"][agent_name]
                    if "failed:" not in backup_path:
                        try:
                            restore_success = self.memory_manager.restore_agent_memory(agent_name, backup_path)
                            restart_result["agents_restored"][agent_name] = "success" if restore_success else "failed"
                        except Exception as e:
                            restart_result["agents_restored"][agent_name] = f"failed: {e}"
                    else:
                        restart_result["agents_restored"][agent_name] = "no_backup_available"

            restart_result["restart_steps"].append("Agent memories restored")

            # Step 3: Execute task resumption
            resumption_results = {}
            for agent_name in agent_names:
                try:
                    result = self.task_protocols.execute_agent_resumption(agent_name)
                    resumption_results[agent_name] = result["success"]
                except Exception as e:
                    resumption_results[agent_name] = f"failed: {e}"

            restart_result["validation_results"]["task_resumption"] = resumption_results
            restart_result["restart_steps"].append("Task resumption executed")

            # Step 4: Validate system health
            health_check = self.perform_health_check()
            restart_result["validation_results"]["health_check"] = health_check["overall_health"]
            restart_result["restart_steps"].append("System health validated")

            # Determine overall success
            successful_restorations = len([r for r in restart_result["agents_restored"].values() if r == "success"])
            successful_resumptions = len([r for r in resumption_results.values() if r is True])

            if (successful_restorations >= 6 and  # At least 6 agents restored
                successful_resumptions >= 6 and   # At least 6 agents resumed
                health_check["overall_health"] in ["excellent", "good", "warning"]):
                restart_result["success"] = True

            self.logger.info("Session restart completed")

        except Exception as e:
            self.logger.error(f"Session restart failed: {e}")
            restart_result["error"] = str(e)

        return restart_result

    def get_control_status(self) -> Dict[str, Any]:
        """Get current control system status"""
        status = {
            "timestamp": datetime.datetime.now().isoformat(),
            "control_state": self.control_state,
            "session_time_remaining": self.framework.get_session_time_remaining() / 3600,  # in hours
            "handoff_recommended": self.framework.is_session_warning_time(),
            "systems_active": len(self.control_state["active_protocols"]),
            "last_health_check": self.control_state["last_health_check"]
        }

        return status

# Main control functions
def initialize_session_continuity():
    """Initialize session continuity system"""
    controller = SessionContinuityController()
    return controller.initialize_all_systems()

def check_system_health():
    """Check overall system health"""
    controller = SessionContinuityController()
    return controller.perform_health_check()

def prepare_handoff():
    """Prepare session handoff"""
    controller = SessionContinuityController()
    return controller.prepare_session_handoff()

def restart_session(handoff_package_file: str):
    """Restart session from handoff package"""
    controller = SessionContinuityController()
    return controller.execute_session_restart(handoff_package_file)

if __name__ == "__main__":
    # Command line interface
    if len(sys.argv) < 2:
        print("Usage: python session_continuity_control.py <command>")
        print("Commands: init, health, prepare, restart <package_file>, status")
        sys.exit(1)

    command = sys.argv[1].lower()
    controller = SessionContinuityController()

    if command == "init":
        result = controller.initialize_all_systems()
        print(f"Initialization: {'SUCCESS' if result['overall_success'] else 'FAILED'}")
        if result["errors"]:
            print(f"Errors: {result['errors']}")

    elif command == "health":
        result = controller.perform_health_check()
        print(f"System Health: {result['overall_health'].upper()}")
        if result["recommendations"]:
            print("Recommendations:")
            for rec in result["recommendations"]:
                print(f"  - {rec}")

    elif command == "prepare":
        result = controller.prepare_session_handoff()
        print(f"Handoff Preparation: {'SUCCESS' if result['success'] else 'FAILED'}")
        print(f"Files Created: {len(result['files_created'])}")

    elif command == "restart":
        if len(sys.argv) < 3:
            print("Usage: python session_continuity_control.py restart <package_file>")
            sys.exit(1)
        package_file = sys.argv[2]
        result = controller.execute_session_restart(package_file)
        print(f"Session Restart: {'SUCCESS' if result['success'] else 'FAILED'}")

    elif command == "status":
        status = controller.get_control_status()
        print(f"Session Time Remaining: {status['session_time_remaining']:.2f} hours")
        print(f"Handoff Recommended: {status['handoff_recommended']}")
        print(f"Active Systems: {status['systems_active']}")

    else:
        print(f"Unknown command: {command}")
        sys.exit(1)