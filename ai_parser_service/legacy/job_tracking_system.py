#!/usr/bin/env python3
"""
Job Tracking System for WhatsApp Bot
Tracks which jobs have been shown to users to avoid duplicates
"""

import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from .database_manager import DatabaseManager

logger = logging.getLogger(__name__)


class JobTrackingSystem:
    """Manages job delivery tracking and prevents duplicate job sends"""

    def __init__(self):
        self.db = DatabaseManager()
        self._create_job_history_table()

    def _create_job_history_table(self):
        """Create user_job_history table if it doesn't exist"""
        try:
            cursor = self.db.connection.cursor()

            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS user_job_history (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
                    job_id INTEGER REFERENCES canonical_jobs(id) ON DELETE CASCADE,
                    shown_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    match_score FLOAT,
                    delivery_type VARCHAR(20) DEFAULT 'initial_batch',
                    message_sent BOOLEAN DEFAULT TRUE,
                    UNIQUE(user_id, job_id)
                );
            """
            )

            # Create indexes for performance
            cursor.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_user_job_history_user_id 
                ON user_job_history(user_id);
            """
            )

            cursor.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_user_job_history_shown_at 
                ON user_job_history(shown_at);
            """
            )

            self.db.connection.commit()
            logger.info("✅ Job tracking table ready")

        except Exception as e:
            logger.error(f"❌ Error creating job history table: {e}")

    def mark_job_as_shown(
        self,
        user_id: int,
        job_id: int,
        match_score: float,
        delivery_type: str = "initial_batch",
    ) -> bool:
        """Mark a job as shown to a user"""
        try:
            cursor = self.db.connection.cursor()

            cursor.execute(
                """
                INSERT INTO user_job_history 
                (user_id, job_id, match_score, delivery_type)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (user_id, job_id) 
                DO UPDATE SET 
                    shown_at = CURRENT_TIMESTAMP,
                    match_score = EXCLUDED.match_score,
                    delivery_type = EXCLUDED.delivery_type
            """,
                (user_id, job_id, match_score, delivery_type),
            )

            self.db.connection.commit()
            logger.info(f"📝 Marked job {job_id} as shown to user {user_id}")
            return True

        except Exception as e:
            logger.error(f"❌ Error marking job as shown: {e}")
            return False

    def get_unseen_jobs(self, user_id: int, all_jobs: List[Dict]) -> List[Dict]:
        """Filter out jobs that have already been shown to the user"""
        try:
            if not all_jobs:
                return []

            cursor = self.db.connection.cursor()

            # Get list of job IDs already shown to this user
            cursor.execute(
                """
                SELECT job_id FROM user_job_history 
                WHERE user_id = %s
            """,
                (user_id,),
            )

            shown_job_ids = {row[0] for row in cursor.fetchall()}

            # Filter out already shown jobs
            unseen_jobs = [
                job for job in all_jobs if job.get("id") not in shown_job_ids
            ]

            logger.info(
                f"🔍 User {user_id}: {len(all_jobs)} total jobs, "
                f"{len(shown_job_ids)} already shown, "
                f"{len(unseen_jobs)} unseen"
            )

            return unseen_jobs

        except Exception as e:
            logger.error(f"❌ Error filtering unseen jobs: {e}")
            return all_jobs  # Return all jobs if error

    def get_user_job_history(self, user_id: int, days: int = 30) -> List[Dict]:
        """Get user's job viewing history"""
        try:
            cursor = self.db.connection.cursor()

            cursor.execute(
                """
                SELECT 
                    ujh.job_id,
                    ujh.shown_at,
                    ujh.match_score,
                    ujh.delivery_type,
                    cj.title,
                    cj.company
                FROM user_job_history ujh
                JOIN canonical_jobs cj ON ujh.job_id = cj.id
                WHERE ujh.user_id = %s 
                AND ujh.shown_at >= CURRENT_DATE - INTERVAL '%s days'
                ORDER BY ujh.shown_at DESC
            """,
                (user_id, days),
            )

            history = []
            for row in cursor.fetchall():
                history.append(
                    {
                        "job_id": row[0],
                        "shown_at": row[1],
                        "match_score": row[2],
                        "delivery_type": row[3],
                        "title": row[4],
                        "company": row[5],
                    }
                )

            return history

        except Exception as e:
            logger.error(f"❌ Error getting job history: {e}")
            return []

    def get_jobs_shown_count(self, user_id: int, days: int = 1) -> int:
        """Get count of jobs shown to user in last N days"""
        try:
            cursor = self.db.connection.cursor()

            cursor.execute(
                """
                SELECT COUNT(*) FROM user_job_history 
                WHERE user_id = %s 
                AND shown_at >= CURRENT_DATE - INTERVAL '%s days'
            """,
                (user_id, days),
            )

            count = cursor.fetchone()[0]
            return count

        except Exception as e:
            logger.error(f"❌ Error getting jobs shown count: {e}")
            return 0

    def should_send_more_jobs(self, user_id: int, max_per_day: int = 10) -> bool:
        """Check if we should send more jobs to user today"""
        today_count = self.get_jobs_shown_count(user_id, days=1)
        return today_count < max_per_day

    def mark_multiple_jobs_as_shown(
        self, user_id: int, jobs: List[Dict], delivery_type: str = "initial_batch"
    ) -> int:
        """Mark multiple jobs as shown in batch"""
        success_count = 0

        for job in jobs:
            job_id = job.get("id")
            match_score = job.get("match_score", 0)

            if job_id and self.mark_job_as_shown(
                user_id, job_id, match_score, delivery_type
            ):
                success_count += 1

        logger.info(
            f"📝 Marked {success_count}/{len(jobs)} jobs as shown to user {user_id}"
        )
        return success_count
