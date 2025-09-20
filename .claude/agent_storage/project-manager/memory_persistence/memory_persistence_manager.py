#!/usr/bin/env python3
"""
Memory Persistence Manager for Multi-Agent System
================================================

Manages memory persistence and restoration for all agent types
with specialized handling for each agent's unique memory requirements.

Created: 2025-09-19
Author: Project Manager Agent
Purpose: Ensure seamless memory continuity across session boundaries
"""

import json
import os
import shutil
import time
import datetime
from typing import Dict, List, Any, Optional
from pathlib import Path
import logging

class MemoryPersistenceManager:
    """
    Manages memory persistence and restoration for all agents
    """

    def __init__(self, base_path="/home/rolo/r2ai/.claude"):
        self.base_path = Path(base_path)
        self.agent_memory = self.base_path / "agent_memory"
        self.agent_storage = self.base_path / "agent_storage"
        self.backup_dir = self.base_path / "memory_backups"
        self.backup_dir.mkdir(exist_ok=True)

        self.logger = logging.getLogger("MemoryPersistence")

        # Agent-specific memory schemas
        self.agent_schemas = {
            "project-manager": {
                "required_files": ["current_work.json"],
                "memory_structure": {
                    "session_state": ["active_sessions", "coordination_state", "resource_tracking"],
                    "agent_contexts": ["agent_status", "task_assignments", "communication_logs"],
                    "task_tracking": ["current_tasks", "completed_tasks", "pending_tasks"],
                    "quality_metrics": ["quality_scores", "compliance_status", "improvement_tracking"],
                    "resource_usage": ["token_usage", "time_tracking", "efficiency_metrics"]
                }
            },
            "super-coder": {
                "required_files": ["current_work.json", "code_context.json"],
                "memory_structure": {
                    "code_context": ["active_projects", "code_state", "technical_decisions"],
                    "optimization_tracking": ["performance_metrics", "optimization_history"],
                    "development_state": ["current_implementations", "testing_status"],
                    "technical_debt": ["identified_issues", "refactoring_plans"]
                }
            },
            "star-wars-specialist": {
                "required_files": ["current_work.json", "canon_state.json"],
                "memory_structure": {
                    "canon_compliance": ["character_states", "universe_consistency", "timeline_tracking"],
                    "character_development": ["personality_traits", "behavioral_patterns", "dialogue_style"],
                    "story_continuity": ["narrative_threads", "plot_consistency", "character_arcs"]
                }
            },
            "web-dev-specialist": {
                "required_files": ["current_work.json", "frontend_state.json"],
                "memory_structure": {
                    "frontend_state": ["component_status", "ui_development", "styling_decisions"],
                    "framework_context": ["technology_stack", "dependencies", "build_state"],
                    "user_interface": ["design_implementations", "responsive_design", "accessibility"]
                }
            },
            "ux-dev-specialist": {
                "required_files": ["current_work.json", "design_state.json"],
                "memory_structure": {
                    "design_decisions": ["interface_design", "user_research", "usability_testing"],
                    "user_experience": ["interaction_design", "user_flows", "accessibility_compliance"],
                    "design_system": ["component_library", "design_tokens", "style_guidelines"]
                }
            },
            "qa-tester": {
                "required_files": ["current_work.json", "test_state.json"],
                "memory_structure": {
                    "test_execution": ["test_results", "test_coverage", "automation_status"],
                    "quality_validation": ["quality_metrics", "compliance_checks", "regression_tracking"],
                    "bug_tracking": ["identified_bugs", "bug_status", "resolution_tracking"]
                }
            },
            "nvidia-orin-nano-specialist": {
                "required_files": ["current_work.json", "hardware_state.json"],
                "memory_structure": {
                    "hardware_optimization": ["performance_metrics", "optimization_results", "configuration_state"],
                    "system_monitoring": ["resource_usage", "thermal_management", "power_efficiency"],
                    "embedded_development": ["driver_status", "firmware_state", "hardware_integration"]
                }
            },
            "video-model-trainer": {
                "required_files": ["current_work.json", "training_state.json"],
                "memory_structure": {
                    "model_training": ["training_progress", "model_performance", "hyperparameters"],
                    "dataset_management": ["dataset_status", "preprocessing_state", "augmentation_config"],
                    "model_evaluation": ["validation_metrics", "testing_results", "deployment_status"]
                }
            },
            "imagineer-specialist": {
                "required_files": ["current_work.json", "creative_state.json"],
                "memory_structure": {
                    "creative_development": ["concept_iterations", "design_evolution", "innovation_tracking"],
                    "project_vision": ["creative_direction", "aesthetic_decisions", "conceptual_framework"],
                    "design_validation": ["concept_testing", "stakeholder_feedback", "iteration_planning"]
                }
            }
        }

    def create_memory_backup(self, agent_name: str) -> str:
        """Create comprehensive backup of agent memory"""
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = self.backup_dir / f"{agent_name}_backup_{timestamp}"
        backup_path.mkdir(exist_ok=True)

        agent_memory_path = self.agent_memory / agent_name
        agent_storage_path = self.agent_storage / agent_name

        backup_info = {
            "agent": agent_name,
            "timestamp": timestamp,
            "backup_path": str(backup_path),
            "files_backed_up": []
        }

        # Backup memory files
        if agent_memory_path.exists():
            memory_backup = backup_path / "memory"
            memory_backup.mkdir(exist_ok=True)

            for file_path in agent_memory_path.rglob("*"):
                if file_path.is_file():
                    relative_path = file_path.relative_to(agent_memory_path)
                    backup_file = memory_backup / relative_path
                    backup_file.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(file_path, backup_file)
                    backup_info["files_backed_up"].append(f"memory/{relative_path}")

        # Backup storage files (critical files only)
        if agent_storage_path.exists():
            storage_backup = backup_path / "storage"
            storage_backup.mkdir(exist_ok=True)

            # Get recent and critical files
            critical_files = []
            for file_path in agent_storage_path.rglob("*"):
                if file_path.is_file():
                    # Include files modified in last 24 hours or with critical extensions
                    if (time.time() - file_path.stat().st_mtime < 86400 or
                        file_path.suffix in ['.json', '.md', '.py', '.txt']):
                        critical_files.append(file_path)

            for file_path in critical_files:
                relative_path = file_path.relative_to(agent_storage_path)
                backup_file = storage_backup / relative_path
                backup_file.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(file_path, backup_file)
                backup_info["files_backed_up"].append(f"storage/{relative_path}")

        # Save backup metadata
        backup_metadata = backup_path / "backup_metadata.json"
        with open(backup_metadata, 'w') as f:
            json.dump(backup_info, f, indent=2)

        self.logger.info(f"Memory backup created for {agent_name}: {backup_path}")
        return str(backup_path)

    def validate_agent_memory(self, agent_name: str) -> Dict[str, Any]:
        """Validate agent memory structure and completeness"""
        validation_result = {
            "agent": agent_name,
            "timestamp": datetime.datetime.now().isoformat(),
            "valid": True,
            "missing_files": [],
            "corrupted_files": [],
            "memory_structure_valid": True,
            "recommendations": []
        }

        if agent_name not in self.agent_schemas:
            validation_result["valid"] = False
            validation_result["recommendations"].append(f"Unknown agent type: {agent_name}")
            return validation_result

        schema = self.agent_schemas[agent_name]
        agent_memory_path = self.agent_memory / agent_name

        # Check required files
        for required_file in schema["required_files"]:
            file_path = agent_memory_path / required_file
            if not file_path.exists():
                validation_result["missing_files"].append(required_file)
                validation_result["valid"] = False

        # Validate file integrity
        for required_file in schema["required_files"]:
            file_path = agent_memory_path / required_file
            if file_path.exists():
                try:
                    with open(file_path, 'r') as f:
                        json.load(f)
                except json.JSONDecodeError:
                    validation_result["corrupted_files"].append(required_file)
                    validation_result["valid"] = False

        # Check memory structure directories
        for structure_dir in schema["memory_structure"].keys():
            dir_path = agent_memory_path / structure_dir
            if not dir_path.exists():
                validation_result["recommendations"].append(f"Create memory structure directory: {structure_dir}")

        return validation_result

    def restore_agent_memory(self, agent_name: str, backup_path: str) -> bool:
        """Restore agent memory from backup"""
        try:
            backup_dir = Path(backup_path)
            if not backup_dir.exists():
                self.logger.error(f"Backup path does not exist: {backup_path}")
                return False

            agent_memory_path = self.agent_memory / agent_name
            agent_storage_path = self.agent_storage / agent_name

            # Restore memory files
            memory_backup = backup_dir / "memory"
            if memory_backup.exists():
                if agent_memory_path.exists():
                    shutil.rmtree(agent_memory_path)

                shutil.copytree(memory_backup, agent_memory_path)

            # Restore critical storage files
            storage_backup = backup_dir / "storage"
            if storage_backup.exists():
                agent_storage_path.mkdir(parents=True, exist_ok=True)

                for file_path in storage_backup.rglob("*"):
                    if file_path.is_file():
                        relative_path = file_path.relative_to(storage_backup)
                        target_file = agent_storage_path / relative_path
                        target_file.parent.mkdir(parents=True, exist_ok=True)
                        shutil.copy2(file_path, target_file)

            self.logger.info(f"Memory restored for {agent_name} from {backup_path}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to restore memory for {agent_name}: {e}")
            return False

    def initialize_agent_memory(self, agent_name: str) -> bool:
        """Initialize clean memory structure for agent"""
        if agent_name not in self.agent_schemas:
            self.logger.error(f"Unknown agent type: {agent_name}")
            return False

        schema = self.agent_schemas[agent_name]
        agent_memory_path = self.agent_memory / agent_name

        # Create memory directory structure
        agent_memory_path.mkdir(parents=True, exist_ok=True)

        for structure_dir, subdirs in schema["memory_structure"].items():
            dir_path = agent_memory_path / structure_dir
            dir_path.mkdir(exist_ok=True)

            for subdir in subdirs:
                subdir_path = dir_path / subdir
                subdir_path.mkdir(exist_ok=True)

        # Create initial required files
        for required_file in schema["required_files"]:
            file_path = agent_memory_path / required_file
            if not file_path.exists():
                initial_data = {
                    "agent": agent_name,
                    "timestamp": datetime.datetime.now().isoformat(),
                    "initialized": True,
                    "version": "1.0"
                }

                with open(file_path, 'w') as f:
                    json.dump(initial_data, f, indent=2)

        self.logger.info(f"Memory initialized for {agent_name}")
        return True

    def sync_agent_memory(self, agent_name: str, memory_data: Dict[str, Any]) -> bool:
        """Synchronize agent memory with provided data"""
        try:
            agent_memory_path = self.agent_memory / agent_name
            agent_memory_path.mkdir(parents=True, exist_ok=True)

            # Update current work file
            current_work_file = agent_memory_path / "current_work.json"
            current_data = {}

            if current_work_file.exists():
                with open(current_work_file, 'r') as f:
                    current_data = json.load(f)

            # Merge with new data
            current_data.update(memory_data)
            current_data["last_sync"] = datetime.datetime.now().isoformat()

            with open(current_work_file, 'w') as f:
                json.dump(current_data, f, indent=2)

            self.logger.info(f"Memory synchronized for {agent_name}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to sync memory for {agent_name}: {e}")
            return False

    def get_memory_status(self) -> Dict[str, Any]:
        """Get comprehensive memory status for all agents"""
        status = {
            "timestamp": datetime.datetime.now().isoformat(),
            "agents": {},
            "backup_count": len(list(self.backup_dir.glob("*_backup_*"))),
            "total_memory_size": 0
        }

        for agent_name in self.agent_schemas.keys():
            agent_memory_path = self.agent_memory / agent_name
            agent_status = {
                "memory_exists": agent_memory_path.exists(),
                "last_modified": None,
                "file_count": 0,
                "size_bytes": 0,
                "validation": None
            }

            if agent_memory_path.exists():
                # Get modification time and file count
                files = list(agent_memory_path.rglob("*"))
                agent_status["file_count"] = len([f for f in files if f.is_file()])

                if files:
                    mod_times = [f.stat().st_mtime for f in files if f.is_file()]
                    if mod_times:
                        agent_status["last_modified"] = datetime.datetime.fromtimestamp(max(mod_times)).isoformat()

                # Calculate size
                total_size = sum(f.stat().st_size for f in files if f.is_file())
                agent_status["size_bytes"] = total_size
                status["total_memory_size"] += total_size

                # Validate memory
                agent_status["validation"] = self.validate_agent_memory(agent_name)

            status["agents"][agent_name] = agent_status

        return status

    def cleanup_old_backups(self, keep_last_n: int = 10) -> int:
        """Clean up old backups, keeping only the most recent ones"""
        backups = list(self.backup_dir.glob("*_backup_*"))
        backups.sort(key=lambda x: x.stat().st_mtime, reverse=True)

        deleted_count = 0
        for backup_dir in backups[keep_last_n:]:
            try:
                shutil.rmtree(backup_dir)
                deleted_count += 1
                self.logger.info(f"Deleted old backup: {backup_dir.name}")
            except Exception as e:
                self.logger.error(f"Failed to delete backup {backup_dir}: {e}")

        return deleted_count

# Utility functions
def backup_all_agents():
    """Backup memory for all agents"""
    manager = MemoryPersistenceManager()
    results = {}

    for agent_name in manager.agent_schemas.keys():
        backup_path = manager.create_memory_backup(agent_name)
        results[agent_name] = backup_path

    return results

def validate_all_agents():
    """Validate memory for all agents"""
    manager = MemoryPersistenceManager()
    results = {}

    for agent_name in manager.agent_schemas.keys():
        validation = manager.validate_agent_memory(agent_name)
        results[agent_name] = validation

    return results

if __name__ == "__main__":
    # Test the memory persistence system
    manager = MemoryPersistenceManager()
    status = manager.get_memory_status()
    print(f"Memory status for {len(status['agents'])} agents")
    print(f"Total memory size: {status['total_memory_size']} bytes")
    print(f"Available backups: {status['backup_count']}")