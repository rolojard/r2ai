#!/usr/bin/env python3
"""
R2D2 Memory Manager - Handles 7-day temporary storage and persistent character memory
Automatic cleanup service for privacy compliance and memory optimization
"""

import sqlite3
import json
import time
import logging
import threading
import schedule
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import asyncio

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class R2D2MemoryManager:
    """Memory management system for R2D2 person recognition with privacy compliance"""

    def __init__(self, config: Dict = None):
        self.config = config or self._get_default_config()
        self.db_path = "/home/rolo/r2ai/r2d2_person_memory.db"
        self.persistent_db_path = "/home/rolo/r2ai/r2d2_persistent_memory.db"

        # Memory management settings
        self.temp_retention_days = self.config.get('temp_retention_days', 7)
        self.cleanup_interval_hours = self.config.get('cleanup_interval_hours', 6)
        self.max_temp_identities = self.config.get('max_temp_identities', 1000)

        # Service control
        self.running = False
        self.cleanup_thread = None

        # Initialize databases
        self._setup_persistent_database()
        self._setup_star_wars_characters()

        # Start cleanup scheduler
        self._schedule_cleanup()

        logger.info("R2D2 Memory Manager initialized")

    def _get_default_config(self) -> Dict:
        """Get default configuration for memory management"""
        return {
            "temp_retention_days": 7,
            "cleanup_interval_hours": 6,
            "max_temp_identities": 1000,
            "privacy_compliance": True,
            "auto_cleanup": True,
            "persistent_star_wars_chars": True,
            "backup_enabled": True,
            "performance_tracking": True
        }

    def _setup_persistent_database(self):
        """Setup persistent database for Star Wars characters and designated persons"""
        try:
            Path(self.persistent_db_path).parent.mkdir(parents=True, exist_ok=True)

            with sqlite3.connect(self.persistent_db_path) as conn:
                # Persistent Star Wars characters
                conn.execute('''
                    CREATE TABLE IF NOT EXISTS star_wars_characters (
                        character_id TEXT PRIMARY KEY,
                        character_name TEXT NOT NULL,
                        character_type TEXT,
                        costume_description TEXT,
                        recognition_features TEXT,
                        canon_background TEXT,
                        r2d2_relationship_type TEXT,
                        preferred_responses TEXT,
                        interaction_count INTEGER DEFAULT 0,
                        last_interaction TIMESTAMP,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')

                # Designated known persons (convention staff, special guests)
                conn.execute('''
                    CREATE TABLE IF NOT EXISTS designated_persons (
                        person_id TEXT PRIMARY KEY,
                        designation_type TEXT NOT NULL,
                        person_name TEXT,
                        role_description TEXT,
                        embedding_hash TEXT UNIQUE,
                        special_permissions TEXT,
                        r2d2_relationship_level INTEGER DEFAULT 5,
                        preferred_responses TEXT,
                        interaction_count INTEGER DEFAULT 0,
                        last_interaction TIMESTAMP,
                        designation_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        active BOOLEAN DEFAULT TRUE
                    )
                ''')

                # Memory statistics tracking
                conn.execute('''
                    CREATE TABLE IF NOT EXISTS memory_statistics (
                        stat_id INTEGER PRIMARY KEY AUTOINCREMENT,
                        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        temp_identities_count INTEGER,
                        persistent_characters_count INTEGER,
                        designated_persons_count INTEGER,
                        total_interactions_today INTEGER,
                        cleanup_operations_count INTEGER,
                        memory_usage_mb REAL
                    )
                ''')

                conn.commit()
                logger.info("Persistent memory database initialized")

        except Exception as e:
            logger.error(f"Error setting up persistent database: {e}")
            raise

    def _setup_star_wars_characters(self):
        """Initialize canonical Star Wars characters in persistent memory"""
        star_wars_characters = [
            {
                "character_id": "luke_skywalker",
                "character_name": "Luke Skywalker",
                "character_type": "jedi_hero",
                "costume_description": "Jedi robes, lightsaber, brown or black outfit",
                "recognition_features": "lightsaber, jedi_robe, belt, boots",
                "canon_background": "Rebellion hero, Jedi Knight, R2D2's close companion",
                "r2d2_relationship_type": "best_friend",
                "preferred_responses": '["excited_recognition", "loyal_beeps", "mission_ready"]'
            },
            {
                "character_id": "princess_leia",
                "character_name": "Princess Leia",
                "character_type": "rebellion_leader",
                "costume_description": "White dress, side buns hairstyle, belt",
                "recognition_features": "white_dress, distinctive_hairstyle, royal_bearing",
                "canon_background": "Princess of Alderaan, Rebellion leader, R2D2's trusted ally",
                "r2d2_relationship_type": "royal_respect",
                "preferred_responses": '["princess_acknowledgment", "urgent_mission_beeps", "protective_stance"]'
            },
            {
                "character_id": "obi_wan_kenobi",
                "character_name": "Obi-Wan Kenobi",
                "character_type": "jedi_master",
                "costume_description": "Brown jedi robes, hood, beard, lightsaber",
                "recognition_features": "brown_robes, beard, wise_appearance, lightsaber",
                "canon_background": "Jedi Master, former owner of R2D2 during Clone Wars",
                "r2d2_relationship_type": "respectful_familiarity",
                "preferred_responses": '["respectful_acknowledgment", "old_friend_beeps", "wise_counsel_chirps"]'
            },
            {
                "character_id": "darth_vader",
                "character_name": "Darth Vader",
                "character_type": "sith_lord",
                "costume_description": "Black armor, cape, helmet, breathing apparatus",
                "recognition_features": "black_armor, distinctive_helmet, cape, imposing_presence",
                "canon_background": "Sith Lord, former Anakin Skywalker, complex history with R2D2",
                "r2d2_relationship_type": "complex_fear_respect",
                "preferred_responses": '["cautious_warbles", "nervous_beeps", "conflicted_sounds"]'
            },
            {
                "character_id": "han_solo",
                "character_name": "Han Solo",
                "character_type": "smuggler_hero",
                "costume_description": "Brown jacket, vest, white shirt, holster",
                "recognition_features": "leather_jacket, vest, blaster_holster, confident_stance",
                "canon_background": "Smuggler turned hero, close friend of Luke and Leia",
                "r2d2_relationship_type": "friendly_banter",
                "preferred_responses": '["sarcastic_beeps", "friendly_chirps", "adventurous_sounds"]'
            },
            {
                "character_id": "stormtrooper",
                "character_name": "Imperial Stormtrooper",
                "character_type": "imperial_soldier",
                "costume_description": "White plastoid armor, distinctive helmet, blaster",
                "recognition_features": "white_armor, helmet_design, military_posture",
                "canon_background": "Imperial soldier, typically viewed with suspicion",
                "r2d2_relationship_type": "cautious_neutral",
                "preferred_responses": '["neutral_beeps", "watchful_sounds", "compliance_chirps"]'
            },
            {
                "character_id": "jedi_knight",
                "character_name": "Jedi Knight",
                "character_type": "jedi_general",
                "costume_description": "Various colored robes, lightsaber, peaceful demeanor",
                "recognition_features": "jedi_robes, lightsaber, serene_presence",
                "canon_background": "Jedi Order member, protector of peace",
                "r2d2_relationship_type": "respectful_assistance",
                "preferred_responses": '["respectful_beeps", "helpful_chirps", "service_ready_sounds"]'
            },
            {
                "character_id": "rebel_pilot",
                "character_name": "Rebel Alliance Pilot",
                "character_type": "rebellion_fighter",
                "costume_description": "Orange flight suit, helmet, rebel insignia",
                "recognition_features": "flight_suit, helmet, rebel_patches, pilot_gear",
                "canon_background": "Rebellion fighter pilot, ally in the cause",
                "r2d2_relationship_type": "comrade_support",
                "preferred_responses": '["solidarity_beeps", "mission_support_chirps", "alliance_pride_sounds"]'
            }
        ]

        try:
            with sqlite3.connect(self.persistent_db_path) as conn:
                for character in star_wars_characters:
                    # Check if character already exists
                    cursor = conn.cursor()
                    cursor.execute('SELECT character_id FROM star_wars_characters WHERE character_id = ?',
                                 (character['character_id'],))

                    if cursor.fetchone() is None:
                        # Insert new character
                        conn.execute('''
                            INSERT INTO star_wars_characters (
                                character_id, character_name, character_type, costume_description,
                                recognition_features, canon_background, r2d2_relationship_type, preferred_responses
                            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                        ''', (
                            character['character_id'], character['character_name'], character['character_type'],
                            character['costume_description'], character['recognition_features'],
                            character['canon_background'], character['r2d2_relationship_type'],
                            character['preferred_responses']
                        ))

                conn.commit()
                logger.info("Star Wars characters initialized in persistent memory")

        except Exception as e:
            logger.error(f"Error setting up Star Wars characters: {e}")

    def _schedule_cleanup(self):
        """Schedule automatic cleanup operations"""
        try:
            # Schedule cleanup every N hours
            schedule.every(self.cleanup_interval_hours).hours.do(self.perform_scheduled_cleanup)

            # Schedule daily statistics update
            schedule.every().day.at("03:00").do(self.update_daily_statistics)

            # Schedule weekly deep cleanup
            schedule.every().sunday.at("04:00").do(self.perform_deep_cleanup)

            logger.info(f"Cleanup scheduled every {self.cleanup_interval_hours} hours")

        except Exception as e:
            logger.error(f"Error scheduling cleanup: {e}")

    def start_memory_service(self):
        """Start the memory management service"""
        try:
            self.running = True

            # Start cleanup scheduler thread
            self.cleanup_thread = threading.Thread(target=self._run_scheduler, daemon=True)
            self.cleanup_thread.start()

            logger.info("R2D2 Memory Management Service started")

        except Exception as e:
            logger.error(f"Error starting memory service: {e}")
            raise

    def stop_memory_service(self):
        """Stop the memory management service"""
        try:
            self.running = False

            if self.cleanup_thread and self.cleanup_thread.is_alive():
                self.cleanup_thread.join(timeout=5)

            logger.info("R2D2 Memory Management Service stopped")

        except Exception as e:
            logger.error(f"Error stopping memory service: {e}")

    def _run_scheduler(self):
        """Run the cleanup scheduler"""
        logger.info("Memory management scheduler started")

        while self.running:
            try:
                schedule.run_pending()
                time.sleep(60)  # Check every minute

            except Exception as e:
                logger.error(f"Error in scheduler: {e}")
                time.sleep(300)  # Wait 5 minutes on error

    def perform_scheduled_cleanup(self):
        """Perform scheduled cleanup of temporary identities"""
        try:
            logger.info("Starting scheduled memory cleanup")

            # Clean up expired temporary identities
            deleted_count = self.cleanup_expired_temporary_identities()

            # Clean up orphaned interactions
            orphan_count = self.cleanup_orphaned_interactions()

            # Enforce memory limits
            limit_count = self.enforce_memory_limits()

            # Update statistics
            self.update_memory_statistics()

            logger.info(f"Cleanup completed: {deleted_count} expired, {orphan_count} orphaned, {limit_count} limit-enforced")

        except Exception as e:
            logger.error(f"Error in scheduled cleanup: {e}")

    def cleanup_expired_temporary_identities(self) -> int:
        """Clean up temporary identities older than retention period"""
        try:
            cutoff_time = datetime.now() - timedelta(days=self.temp_retention_days)

            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                # Delete expired temporary identities
                cursor.execute('''
                    DELETE FROM person_identities
                    WHERE identity_type = 'temporary' AND last_seen < ?
                ''', (cutoff_time,))

                deleted_count = cursor.rowcount
                conn.commit()

                if deleted_count > 0:
                    logger.info(f"Cleaned up {deleted_count} expired temporary identities")

                return deleted_count

        except Exception as e:
            logger.error(f"Error cleaning up expired identities: {e}")
            return 0

    def cleanup_orphaned_interactions(self) -> int:
        """Clean up interaction records for deleted identities"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                # Delete orphaned interactions
                cursor.execute('''
                    DELETE FROM interaction_history
                    WHERE person_id NOT IN (SELECT person_id FROM person_identities)
                ''')

                orphan_count = cursor.rowcount
                conn.commit()

                if orphan_count > 0:
                    logger.info(f"Cleaned up {orphan_count} orphaned interactions")

                return orphan_count

        except Exception as e:
            logger.error(f"Error cleaning up orphaned interactions: {e}")
            return 0

    def enforce_memory_limits(self) -> int:
        """Enforce maximum number of temporary identities"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                # Count current temporary identities
                cursor.execute('SELECT COUNT(*) FROM person_identities WHERE identity_type = "temporary"')
                current_count = cursor.fetchone()[0]

                if current_count > self.max_temp_identities:
                    # Delete oldest identities to stay under limit
                    excess_count = current_count - self.max_temp_identities

                    cursor.execute('''
                        DELETE FROM person_identities
                        WHERE identity_type = 'temporary'
                        AND person_id IN (
                            SELECT person_id FROM person_identities
                            WHERE identity_type = 'temporary'
                            ORDER BY last_seen ASC
                            LIMIT ?
                        )
                    ''', (excess_count,))

                    deleted_count = cursor.rowcount
                    conn.commit()

                    logger.info(f"Enforced memory limit: removed {deleted_count} oldest identities")
                    return deleted_count

                return 0

        except Exception as e:
            logger.error(f"Error enforcing memory limits: {e}")
            return 0

    def perform_deep_cleanup(self):
        """Perform comprehensive weekly cleanup"""
        try:
            logger.info("Starting deep cleanup operation")

            # Vacuum databases
            self._vacuum_databases()

            # Clean up performance metrics older than 30 days
            self._cleanup_old_metrics()

            # Backup persistent data
            self._backup_persistent_data()

            # Reset statistics
            self._reset_weekly_statistics()

            logger.info("Deep cleanup completed")

        except Exception as e:
            logger.error(f"Error in deep cleanup: {e}")

    def _vacuum_databases(self):
        """Vacuum databases to reclaim space"""
        try:
            for db_path in [self.db_path, self.persistent_db_path]:
                if Path(db_path).exists():
                    with sqlite3.connect(db_path) as conn:
                        conn.execute('VACUUM')
                        conn.commit()

            logger.info("Database vacuum completed")

        except Exception as e:
            logger.error(f"Error vacuuming databases: {e}")

    def _cleanup_old_metrics(self):
        """Clean up old performance metrics"""
        try:
            cutoff_time = datetime.now() - timedelta(days=30)

            with sqlite3.connect(self.persistent_db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('DELETE FROM memory_statistics WHERE timestamp < ?', (cutoff_time,))
                deleted_count = cursor.rowcount
                conn.commit()

                if deleted_count > 0:
                    logger.info(f"Cleaned up {deleted_count} old metric records")

        except Exception as e:
            logger.error(f"Error cleaning up old metrics: {e}")

    def _backup_persistent_data(self):
        """Backup persistent data"""
        try:
            backup_dir = Path("/home/rolo/r2ai/backups")
            backup_dir.mkdir(exist_ok=True)

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_file = backup_dir / f"r2d2_persistent_memory_backup_{timestamp}.db"

            # Copy persistent database
            import shutil
            shutil.copy2(self.persistent_db_path, backup_file)

            # Keep only last 7 backups
            backup_files = sorted(backup_dir.glob("r2d2_persistent_memory_backup_*.db"))
            for old_backup in backup_files[:-7]:
                old_backup.unlink()

            logger.info(f"Persistent data backed up to {backup_file}")

        except Exception as e:
            logger.error(f"Error backing up persistent data: {e}")

    def _reset_weekly_statistics(self):
        """Reset weekly statistics counters"""
        try:
            # This could reset weekly counters if implemented
            logger.info("Weekly statistics reset")

        except Exception as e:
            logger.error(f"Error resetting weekly statistics: {e}")

    def update_memory_statistics(self):
        """Update memory usage statistics"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                # Count temporary identities
                cursor.execute('SELECT COUNT(*) FROM person_identities WHERE identity_type = "temporary"')
                temp_count = cursor.fetchone()[0]

                # Count today's interactions
                today = datetime.now().date()
                cursor.execute('SELECT COUNT(*) FROM interaction_history WHERE DATE(timestamp) = ?', (today,))
                today_interactions = cursor.fetchone()[0]

            with sqlite3.connect(self.persistent_db_path) as conn:
                cursor = conn.cursor()

                # Count persistent characters
                cursor.execute('SELECT COUNT(*) FROM star_wars_characters')
                characters_count = cursor.fetchone()[0]

                # Count designated persons
                cursor.execute('SELECT COUNT(*) FROM designated_persons WHERE active = 1')
                designated_count = cursor.fetchone()[0]

                # Calculate memory usage (simplified)
                memory_usage = (temp_count * 0.5) + (characters_count * 0.1) + (designated_count * 0.2)  # MB estimate

                # Insert statistics
                conn.execute('''
                    INSERT INTO memory_statistics (
                        temp_identities_count, persistent_characters_count, designated_persons_count,
                        total_interactions_today, memory_usage_mb
                    ) VALUES (?, ?, ?, ?, ?)
                ''', (temp_count, characters_count, designated_count, today_interactions, memory_usage))

                conn.commit()

        except Exception as e:
            logger.error(f"Error updating memory statistics: {e}")

    def update_daily_statistics(self):
        """Update daily statistics and perform maintenance"""
        try:
            logger.info("Updating daily statistics")

            # Update memory statistics
            self.update_memory_statistics()

            # Update character interaction counts
            self._update_character_interaction_counts()

            logger.info("Daily statistics updated")

        except Exception as e:
            logger.error(f"Error updating daily statistics: {e}")

    def _update_character_interaction_counts(self):
        """Update interaction counts for Star Wars characters"""
        try:
            with sqlite3.connect(self.persistent_db_path) as conn:
                # This would be connected to actual interaction tracking
                # For now, just update timestamp
                conn.execute('UPDATE star_wars_characters SET updated_at = ?', (datetime.now(),))
                conn.commit()

        except Exception as e:
            logger.error(f"Error updating character interaction counts: {e}")

    def add_designated_person(self, person_name: str, role: str, embedding_hash: str,
                           designation_type: str = "staff") -> bool:
        """Add a designated person to persistent memory"""
        try:
            person_id = f"{designation_type}_{int(time.time())}"

            with sqlite3.connect(self.persistent_db_path) as conn:
                conn.execute('''
                    INSERT INTO designated_persons (
                        person_id, designation_type, person_name, role_description,
                        embedding_hash, r2d2_relationship_level
                    ) VALUES (?, ?, ?, ?, ?, ?)
                ''', (person_id, designation_type, person_name, role, embedding_hash, 5))

                conn.commit()

                logger.info(f"Added designated person: {person_name} ({role})")
                return True

        except Exception as e:
            logger.error(f"Error adding designated person: {e}")
            return False

    def get_memory_status(self) -> Dict[str, Any]:
        """Get current memory system status"""
        try:
            # Get temporary memory stats
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                cursor.execute('SELECT COUNT(*) FROM person_identities WHERE identity_type = "temporary"')
                temp_count = cursor.fetchone()[0]

                cursor.execute('SELECT COUNT(*) FROM interaction_history')
                interaction_count = cursor.fetchone()[0]

            # Get persistent memory stats
            with sqlite3.connect(self.persistent_db_path) as conn:
                cursor = conn.cursor()

                cursor.execute('SELECT COUNT(*) FROM star_wars_characters')
                characters_count = cursor.fetchone()[0]

                cursor.execute('SELECT COUNT(*) FROM designated_persons WHERE active = 1')
                designated_count = cursor.fetchone()[0]

            # Calculate retention info
            oldest_allowed = datetime.now() - timedelta(days=self.temp_retention_days)

            status = {
                "service_running": self.running,
                "memory_counts": {
                    "temporary_identities": temp_count,
                    "star_wars_characters": characters_count,
                    "designated_persons": designated_count,
                    "total_interactions": interaction_count
                },
                "retention_policy": {
                    "temp_retention_days": self.temp_retention_days,
                    "max_temp_identities": self.max_temp_identities,
                    "oldest_allowed_date": oldest_allowed.isoformat(),
                    "cleanup_interval_hours": self.cleanup_interval_hours
                },
                "next_cleanup": schedule.next_run().isoformat() if schedule.jobs else None,
                "memory_usage_estimate_mb": (temp_count * 0.5) + (characters_count * 0.1),
                "privacy_compliance": {
                    "auto_cleanup_enabled": self.config.get('auto_cleanup', True),
                    "privacy_mode": self.config.get('privacy_compliance', True)
                }
            }

            return status

        except Exception as e:
            logger.error(f"Error getting memory status: {e}")
            return {"error": str(e)}

def main():
    """Main function for testing memory manager"""
    print("R2D2 Memory Manager")
    print("=" * 30)

    # Initialize memory manager
    memory_manager = R2D2MemoryManager()

    # Start service
    memory_manager.start_memory_service()

    print("Memory Manager started. Press Ctrl+C to stop")

    try:
        # Keep service running
        while True:
            time.sleep(10)

            # Print status every 60 seconds
            status = memory_manager.get_memory_status()
            print(f"\nMemory Status: {json.dumps(status, indent=2, default=str)}")
            time.sleep(50)

    except KeyboardInterrupt:
        print("\nStopping Memory Manager...")
        memory_manager.stop_memory_service()
        print("Memory Manager stopped")

if __name__ == "__main__":
    main()