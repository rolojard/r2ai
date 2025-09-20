#!/usr/bin/env python3
"""
R2D2 AI Project - Automated Git Backup System
===============================================

This script provides automated backup functionality for the R2D2 AI project,
ensuring regular commits and GitHub synchronization.

Author: R2D2 AI Development Team
License: MIT
"""

import subprocess
import json
import os
import sys
import datetime
from pathlib import Path
from typing import List, Dict, Optional

class R2D2GitBackup:
    """Automated backup system for R2D2 AI project."""

    def __init__(self, repo_path: str = "/home/rolo/r2ai"):
        """Initialize backup system."""
        self.repo_path = Path(repo_path)
        self.config_file = self.repo_path / "scripts" / "backup_config.json"
        self.log_file = self.repo_path / "logs" / "backup.log"

        # Ensure directories exist
        (self.repo_path / "scripts").mkdir(exist_ok=True)
        (self.repo_path / "logs").mkdir(exist_ok=True)

        # Load or create configuration
        self.config = self._load_config()

    def _load_config(self) -> Dict:
        """Load backup configuration."""
        default_config = {
            "auto_commit_interval": 3600,  # 1 hour
            "commit_message_template": "Auto-backup: {timestamp}",
            "include_patterns": ["*.py", "*.js", "*.json", "*.md", "*.txt", "*.sh"],
            "exclude_patterns": ["*.log", "*.pyc", "__pycache__", "node_modules"],
            "max_file_size_mb": 50,
            "agent_commit_prefix": "🤖 Agent commit:",
            "backup_branches": ["main", "development", "feature/*"],
            "remote_name": "origin"
        }

        if self.config_file.exists():
            try:
                with open(self.config_file, 'r') as f:
                    config = json.load(f)
                # Merge with defaults for any missing keys
                return {**default_config, **config}
            except (json.JSONDecodeError, IOError) as e:
                self._log(f"Error loading config: {e}. Using defaults.")

        # Save default config
        with open(self.config_file, 'w') as f:
            json.dump(default_config, f, indent=2)

        return default_config

    def _log(self, message: str, level: str = "INFO"):
        """Log message with timestamp."""
        timestamp = datetime.datetime.now().isoformat()
        log_entry = f"[{timestamp}] {level}: {message}"

        # Print to console
        print(log_entry)

        # Write to log file
        try:
            with open(self.log_file, 'a') as f:
                f.write(log_entry + "\\n")
        except IOError as e:
            print(f"Warning: Could not write to log file: {e}")

    def _run_command(self, command: List[str], cwd: Optional[str] = None) -> tuple:
        """Run git command and return output."""
        try:
            result = subprocess.run(
                command,
                cwd=cwd or self.repo_path,
                capture_output=True,
                text=True,
                check=False
            )
            return result.returncode, result.stdout.strip(), result.stderr.strip()
        except Exception as e:
            self._log(f"Command execution error: {e}", "ERROR")
            return 1, "", str(e)

    def check_git_status(self) -> Dict:
        """Check current git repository status."""
        self._log("Checking git status...")

        # Check if we're in a git repo
        returncode, stdout, stderr = self._run_command(["git", "rev-parse", "--git-dir"])
        if returncode != 0:
            raise RuntimeError(f"Not a git repository: {stderr}")

        # Get status
        returncode, stdout, stderr = self._run_command(["git", "status", "--porcelain"])
        if returncode != 0:
            raise RuntimeError(f"Git status failed: {stderr}")

        # Parse status
        status = {
            "modified": [],
            "added": [],
            "deleted": [],
            "untracked": [],
            "staged": []
        }

        for line in stdout.split("\\n"):
            if line.strip():
                status_code = line[:2]
                filename = line[3:]

                if status_code[0] in "AM":
                    status["staged"].append(filename)
                if status_code[1] == "M":
                    status["modified"].append(filename)
                elif status_code[1] == "D":
                    status["deleted"].append(filename)
                elif status_code == "??":
                    status["untracked"].append(filename)

        return status

    def should_include_file(self, filepath: str) -> bool:
        """Check if file should be included in backup."""
        file_path = Path(filepath)

        # Check file size
        try:
            if file_path.exists():
                size_mb = file_path.stat().st_size / (1024 * 1024)
                if size_mb > self.config["max_file_size_mb"]:
                    self._log(f"Skipping large file: {filepath} ({size_mb:.1f}MB)")
                    return False
        except OSError:
            pass

        # Check include patterns
        for pattern in self.config["include_patterns"]:
            if file_path.match(pattern):
                # Check exclude patterns
                for exclude_pattern in self.config["exclude_patterns"]:
                    if file_path.match(exclude_pattern):
                        return False
                return True

        return False

    def stage_files(self, files: List[str]) -> int:
        """Stage files for commit."""
        if not files:
            return 0

        staged_count = 0
        for file in files:
            if self.should_include_file(file):
                returncode, stdout, stderr = self._run_command(["git", "add", file])
                if returncode == 0:
                    staged_count += 1
                    self._log(f"Staged: {file}")
                else:
                    self._log(f"Failed to stage {file}: {stderr}", "WARNING")

        return staged_count

    def create_commit(self, message: str, author: str = "R2D2-AI-System") -> bool:
        """Create a git commit."""
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        full_message = f"""{message}

🤖 Generated with Claude Code
Timestamp: {timestamp}
Author: {author}

Co-Authored-By: Claude <noreply@anthropic.com>"""

        returncode, stdout, stderr = self._run_command([
            "git", "commit", "-m", full_message
        ])

        if returncode == 0:
            self._log(f"Commit created successfully: {message}")
            return True
        else:
            self._log(f"Commit failed: {stderr}", "ERROR")
            return False

    def auto_backup(self, commit_message: Optional[str] = None) -> bool:
        """Perform automatic backup of current changes."""
        try:
            self._log("Starting automatic backup...")

            # Check git status
            status = self.check_git_status()

            # Collect files to stage
            files_to_stage = (
                status["modified"] +
                status["deleted"] +
                status["untracked"]
            )

            if not files_to_stage:
                self._log("No changes to backup.")
                return True

            # Stage appropriate files
            staged_count = self.stage_files(files_to_stage)

            if staged_count == 0:
                self._log("No files staged for commit.")
                return True

            # Create commit message
            if not commit_message:
                timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                commit_message = f"Auto-backup: {staged_count} files updated - {timestamp}"

            # Create commit
            success = self.create_commit(commit_message)

            if success:
                self._log(f"Backup completed successfully. Files staged: {staged_count}")

            return success

        except Exception as e:
            self._log(f"Backup failed: {e}", "ERROR")
            return False

    def push_to_remote(self, branch: str = "main", remote: str = "origin") -> bool:
        """Push commits to remote repository."""
        try:
            self._log(f"Pushing to {remote}/{branch}...")

            returncode, stdout, stderr = self._run_command([
                "git", "push", remote, branch
            ])

            if returncode == 0:
                self._log(f"Push to {remote}/{branch} successful")
                return True
            else:
                self._log(f"Push failed: {stderr}", "ERROR")
                return False

        except Exception as e:
            self._log(f"Push error: {e}", "ERROR")
            return False

    def agent_commit(self, agent_name: str, changes_description: str) -> bool:
        """Create a commit specifically for agent changes."""
        commit_message = f"{self.config['agent_commit_prefix']} {agent_name} - {changes_description}"
        return self.auto_backup(commit_message)

    def setup_branches(self) -> bool:
        """Set up development branch structure."""
        try:
            self._log("Setting up branch structure...")

            # Create development branch
            returncode, stdout, stderr = self._run_command([
                "git", "checkout", "-b", "development"
            ])

            if returncode == 0:
                self._log("Development branch created")
            else:
                self._log(f"Development branch creation failed: {stderr}", "WARNING")

            # Switch back to main
            self._run_command(["git", "checkout", "main"])

            return True

        except Exception as e:
            self._log(f"Branch setup error: {e}", "ERROR")
            return False

    def backup_status_report(self) -> Dict:
        """Generate backup status report."""
        try:
            status = self.check_git_status()

            # Get recent commits
            returncode, stdout, stderr = self._run_command([
                "git", "log", "--oneline", "-10"
            ])
            recent_commits = stdout.split("\\n") if returncode == 0 else []

            # Get branch info
            returncode, stdout, stderr = self._run_command([
                "git", "branch", "-v"
            ])
            branches = stdout.split("\\n") if returncode == 0 else []

            report = {
                "timestamp": datetime.datetime.now().isoformat(),
                "status": status,
                "recent_commits": recent_commits,
                "branches": branches,
                "total_files": len(status["modified"]) + len(status["untracked"]) + len(status["deleted"])
            }

            return report

        except Exception as e:
            self._log(f"Status report error: {e}", "ERROR")
            return {"error": str(e)}

def main():
    """Main function for command-line usage."""
    import argparse

    parser = argparse.ArgumentParser(description="R2D2 AI Project Git Backup System")
    parser.add_argument("--backup", action="store_true", help="Perform automatic backup")
    parser.add_argument("--push", action="store_true", help="Push to remote repository")
    parser.add_argument("--setup-branches", action="store_true", help="Setup branch structure")
    parser.add_argument("--status", action="store_true", help="Show backup status")
    parser.add_argument("--agent-commit", nargs=2, metavar=("AGENT_NAME", "DESCRIPTION"),
                       help="Create agent commit")
    parser.add_argument("--message", "-m", help="Custom commit message")

    args = parser.parse_args()

    backup_system = R2D2GitBackup()

    if args.setup_branches:
        backup_system.setup_branches()

    if args.agent_commit:
        agent_name, description = args.agent_commit
        backup_system.agent_commit(agent_name, description)

    if args.backup:
        backup_system.auto_backup(args.message)

    if args.push:
        backup_system.push_to_remote()

    if args.status:
        report = backup_system.backup_status_report()
        print(json.dumps(report, indent=2))

    if not any([args.backup, args.push, args.setup_branches, args.status, args.agent_commit]):
        # Default action - show status
        report = backup_system.backup_status_report()
        print("R2D2 AI Project Backup Status:")
        print(f"Modified files: {len(report.get('status', {}).get('modified', []))}")
        print(f"Untracked files: {len(report.get('status', {}).get('untracked', []))}")
        print(f"Recent commits: {len(report.get('recent_commits', []))}")

if __name__ == "__main__":
    main()