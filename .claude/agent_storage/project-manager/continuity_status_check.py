#!/usr/bin/env python3
"""
Session Continuity Status Check
==============================

Simple status checker for session continuity protocols without complex imports.
Used for quick validation and monitoring.

Created: 2025-09-19
Author: Project Manager Agent
Purpose: Quick status checking and validation
"""

import json
import os
import time
import datetime
from pathlib import Path

class ContinuityStatusChecker:
    """Simple status checker for continuity protocols"""

    def __init__(self, base_path="/home/rolo/r2ai/.claude"):
        self.base_path = Path(base_path)
        self.session_start_time = time.time()
        self.session_limit = 5 * 60 * 60  # 5 hours

    def check_directory_structure(self):
        """Check if all required directories exist"""
        required_dirs = [
            "agent_storage/project-manager/session_continuity",
            "agent_storage/project-manager/memory_persistence",
            "agent_storage/project-manager/task_resumption",
            "agent_storage/project-manager/coordination_protocols",
            "agent_storage/project-manager/monitoring",
            "agent_memory/project-manager"
        ]

        status = {
            "timestamp": datetime.datetime.now().isoformat(),
            "directories": {},
            "all_present": True
        }

        for dir_path in required_dirs:
            full_path = self.base_path / dir_path
            exists = full_path.exists()
            status["directories"][dir_path] = {
                "exists": exists,
                "path": str(full_path)
            }
            if not exists:
                status["all_present"] = False

        return status

    def check_continuity_files(self):
        """Check if continuity protocol files exist"""
        required_files = [
            "agent_storage/project-manager/session_continuity/session_continuity_framework.py",
            "agent_storage/project-manager/memory_persistence/memory_persistence_manager.py",
            "agent_storage/project-manager/task_resumption/task_resumption_protocols.py",
            "agent_storage/project-manager/coordination_protocols/multi_agent_coordinator.py",
            "agent_storage/project-manager/monitoring/session_monitoring_dashboard.py",
            "agent_storage/project-manager/session_continuity_control.py",
            "agent_storage/project-manager/test_continuity_protocols.py"
        ]

        status = {
            "timestamp": datetime.datetime.now().isoformat(),
            "files": {},
            "all_present": True,
            "total_size": 0
        }

        for file_path in required_files:
            full_path = self.base_path / file_path
            exists = full_path.exists()
            size = full_path.stat().st_size if exists else 0

            status["files"][file_path] = {
                "exists": exists,
                "size": size,
                "path": str(full_path)
            }

            if not exists:
                status["all_present"] = False
            else:
                status["total_size"] += size

        return status

    def check_agent_memory_health(self):
        """Check agent memory health"""
        agent_names = [
            "project-manager", "super-coder", "star-wars-specialist",
            "web-dev-specialist", "ux-dev-specialist", "qa-tester",
            "nvidia-orin-nano-specialist", "video-model-trainer", "imagineer-specialist"
        ]

        status = {
            "timestamp": datetime.datetime.now().isoformat(),
            "agents": {},
            "healthy_count": 0,
            "total_count": len(agent_names)
        }

        for agent_name in agent_names:
            agent_memory_path = self.base_path / "agent_memory" / agent_name
            current_work_file = agent_memory_path / "current_work.json"

            agent_status = {
                "memory_exists": agent_memory_path.exists(),
                "current_work_exists": current_work_file.exists(),
                "last_modified": None,
                "healthy": False
            }

            if current_work_file.exists():
                try:
                    mtime = current_work_file.stat().st_mtime
                    agent_status["last_modified"] = datetime.datetime.fromtimestamp(mtime).isoformat()

                    # Check if file is valid JSON
                    with open(current_work_file, 'r') as f:
                        data = json.load(f)
                        agent_status["has_valid_json"] = True
                        agent_status["healthy"] = True
                        status["healthy_count"] += 1

                except (json.JSONDecodeError, Exception) as e:
                    agent_status["error"] = str(e)
                    agent_status["has_valid_json"] = False

            status["agents"][agent_name] = agent_status

        return status

    def get_session_time_status(self):
        """Get session time status"""
        elapsed = time.time() - self.session_start_time
        remaining = max(0, self.session_limit - elapsed)
        progress = (elapsed / self.session_limit) * 100

        return {
            "timestamp": datetime.datetime.now().isoformat(),
            "elapsed_seconds": elapsed,
            "elapsed_formatted": self._format_time(elapsed),
            "remaining_seconds": remaining,
            "remaining_formatted": self._format_time(remaining),
            "progress_percentage": progress,
            "status": self._get_time_status(elapsed),
            "handoff_recommended": elapsed >= (4.5 * 60 * 60)  # 4.5 hours
        }

    def _format_time(self, seconds):
        """Format time in HH:MM:SS"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        seconds = int(seconds % 60)
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"

    def _get_time_status(self, elapsed):
        """Get time status"""
        if elapsed >= (4.8 * 60 * 60):  # 4.8 hours
            return "critical"
        elif elapsed >= (4.5 * 60 * 60):  # 4.5 hours
            return "warning"
        else:
            return "healthy"

    def generate_status_report(self):
        """Generate comprehensive status report"""
        print("Session Continuity Protocols Status Report")
        print("=" * 50)

        # Check directories
        dir_status = self.check_directory_structure()
        print(f"\nDirectory Structure: {'✓ PASS' if dir_status['all_present'] else '✗ FAIL'}")
        if not dir_status['all_present']:
            missing_dirs = [d for d, info in dir_status['directories'].items() if not info['exists']]
            print(f"Missing directories: {missing_dirs}")

        # Check files
        file_status = self.check_continuity_files()
        print(f"Continuity Files: {'✓ PASS' if file_status['all_present'] else '✗ FAIL'}")
        print(f"Total Protocol Size: {file_status['total_size'] / 1024:.1f} KB")
        if not file_status['all_present']:
            missing_files = [f for f, info in file_status['files'].items() if not info['exists']]
            print(f"Missing files: {missing_files}")

        # Check agent memory
        agent_status = self.check_agent_memory_health()
        print(f"Agent Memory Health: {agent_status['healthy_count']}/{agent_status['total_count']} agents healthy")

        # Check session time
        time_status = self.get_session_time_status()
        print(f"Session Time: {time_status['remaining_formatted']} remaining ({time_status['progress_percentage']:.1f}% elapsed)")
        print(f"Session Status: {time_status['status'].upper()}")
        if time_status['handoff_recommended']:
            print("⚠️  HANDOFF RECOMMENDED")

        # Overall assessment
        print("\n" + "=" * 50)
        all_systems_ok = (dir_status['all_present'] and
                          file_status['all_present'] and
                          agent_status['healthy_count'] >= 7)  # At least 7/9 agents

        if all_systems_ok:
            print("✅ OVERALL STATUS: READY FOR DEPLOYMENT")
        else:
            print("❌ OVERALL STATUS: NEEDS ATTENTION")

        return {
            "directories": dir_status,
            "files": file_status,
            "agents": agent_status,
            "session_time": time_status,
            "overall_ready": all_systems_ok
        }

if __name__ == "__main__":
    checker = ContinuityStatusChecker()
    report = checker.generate_status_report()