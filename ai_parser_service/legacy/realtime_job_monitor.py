#!/usr/bin/env python3
"""
Real-Time Job Monitoring System for WhatsApp Bot
Monitors for new jobs and sends instant alerts to matching users
"""

import logging
import time
from datetime import datetime, timedelta
from typing import List, Dict, Set
from database_manager import DatabaseManager
from intelligent_job_matcher import IntelligentJobMatcher
from job_tracking_system import JobTrackingSystem
from window_management_system import WindowManagementSystem

logger = logging.getLogger(__name__)


class RealTimeJobMonitor:
    """Monitors for new jobs and sends real-time alerts to users"""

    def __init__(self, whatsapp_bot=None):
        self.db = DatabaseManager()
        self.job_matcher = IntelligentJobMatcher(self.db.connection)
        self.job_tracker = JobTrackingSystem()
        self.window_manager = WindowManagementSystem()
        self.whatsapp_bot = whatsapp_bot

        # Monitoring settings
        self.min_match_score = 50  # Minimum match score to send
        self.check_interval = 300  # Check every 5 minutes
        self.max_jobs_per_user_per_day = 10

        self._create_monitoring_table()

    def _create_monitoring_table(self):
        """Create real-time monitoring tracking table"""
        try:
            cursor = self.db.connection.cursor()

            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS realtime_monitoring (
                    id SERIAL PRIMARY KEY,
                    last_check_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    jobs_processed INTEGER DEFAULT 0,
                    alerts_sent INTEGER DEFAULT 0,
                    check_duration_seconds FLOAT DEFAULT 0
                );
            """
            )

            # Initialize with first record if empty
            cursor.execute("SELECT COUNT(*) FROM realtime_monitoring")
            if cursor.fetchone()[0] == 0:
                cursor.execute(
                    """
                    INSERT INTO realtime_monitoring 
                    (last_check_time, jobs_processed, alerts_sent) 
                    VALUES (CURRENT_TIMESTAMP, 0, 0)
                """
                )

            self.db.connection.commit()
            logger.info("✅ Real-time monitoring table ready")

        except Exception as e:
            logger.error(f"❌ Error creating monitoring table: {e}")

    def get_new_jobs_since_last_check(self) -> List[Dict]:
        """Get jobs added since last monitoring check"""
        try:
            cursor = self.db.connection.cursor()

            # Get last check time
            cursor.execute(
                """
                SELECT last_check_time FROM realtime_monitoring 
                ORDER BY id DESC LIMIT 1
            """
            )
            result = cursor.fetchone()
            last_check = result[0] if result else datetime.now() - timedelta(hours=1)

            # Get new jobs since last check
            cursor.execute(
                """
                SELECT id, title, company, location, salary_min, salary_max, 
                       salary_currency, employment_type, posted_date, ai_summary
                FROM canonical_jobs 
                WHERE scraped_at > %s 
                AND ai_summary IS NOT NULL
                ORDER BY scraped_at DESC
            """,
                (last_check,),
            )

            new_jobs = []
            for row in cursor.fetchall():
                new_jobs.append(
                    {
                        "id": row[0],
                        "title": row[1],
                        "company": row[2],
                        "location": row[3],
                        "salary_min": row[4],
                        "salary_max": row[5],
                        "salary_currency": row[6],
                        "employment_type": row[7],
                        "posted_date": row[8],
                        "ai_summary": row[9],
                    }
                )

            logger.info(f"🔍 Found {len(new_jobs)} new jobs since {last_check}")
            return new_jobs

        except Exception as e:
            logger.error(f"❌ Error getting new jobs: {e}")
            return []

    def get_active_users_with_preferences(self) -> List[Dict]:
        """Get users with active windows and confirmed preferences"""
        try:
            cursor = self.db.connection.cursor()

            cursor.execute(
                """
                SELECT DISTINCT 
                    u.id,
                    u.phone_number,
                    up.job_roles,
                    up.preferred_locations,
                    up.technical_skills,
                    up.years_experience,
                    up.salary_min,
                    up.salary_currency
                FROM users u
                JOIN user_preferences up ON u.id = up.user_id
                JOIN conversation_windows cw ON u.id = cw.user_id
                WHERE up.preferences_confirmed = TRUE
                AND cw.window_status = 'active'
                AND cw.last_activity >= CURRENT_TIMESTAMP - INTERVAL '24 hours'
            """
            )

            active_users = []
            for row in cursor.fetchall():
                active_users.append(
                    {
                        "user_id": row[0],
                        "phone_number": row[1],
                        "job_roles": row[2],
                        "preferred_locations": row[3],
                        "technical_skills": row[4],
                        "years_experience": row[5],
                        "salary_min": row[6],
                        "salary_currency": row[7],
                    }
                )

            logger.info(f"👥 Found {len(active_users)} active users with preferences")
            return active_users

        except Exception as e:
            logger.error(f"❌ Error getting active users: {e}")
            return []

    def check_job_matches_for_user(
        self, user: Dict, new_jobs: List[Dict]
    ) -> List[Dict]:
        """Check which new jobs match a specific user"""
        try:
            user_id = user["user_id"]

            # Get unseen jobs for this user
            unseen_jobs = self.job_tracker.get_unseen_jobs(user_id, new_jobs)

            if not unseen_jobs:
                return []

            # Calculate match scores for unseen jobs
            matching_jobs = []
            for job in unseen_jobs:
                # Use intelligent matcher to calculate score
                match_score = self.job_matcher._calculate_match_score(user, job)

                if match_score >= self.min_match_score:
                    job["match_score"] = match_score
                    matching_jobs.append(job)

            # Sort by match score (highest first)
            matching_jobs.sort(key=lambda x: x["match_score"], reverse=True)

            return matching_jobs

        except Exception as e:
            logger.error(
                f"❌ Error checking matches for user {user.get('user_id')}: {e}"
            )
            return []

    def send_real_time_job_alert(self, user: Dict, job: Dict) -> bool:
        """Send real-time job alert to user"""
        try:
            if not self.whatsapp_bot:
                logger.warning("⚠️ WhatsApp bot not available for sending alerts")
                return False

            phone_number = user["phone_number"]
            match_score = job.get("match_score", 0)

            # Format job alert message
            alert_msg = f"🚨 *NEW JOB ALERT!* ({match_score:.0f}% match)\n\n"
            alert_msg += job.get("ai_summary", "Job details not available")

            # Send the alert
            success = self.whatsapp_bot.send_whatsapp_message(phone_number, alert_msg)

            if success:
                # Mark job as shown
                self.job_tracker.mark_job_as_shown(
                    user["user_id"], job["id"], match_score, "real_time_alert"
                )
                logger.info(
                    f"🚨 Sent real-time alert to {phone_number} for job {job['id']}"
                )

            return success

        except Exception as e:
            logger.error(f"❌ Error sending real-time alert: {e}")
            return False

    def run_monitoring_cycle(self) -> Dict:
        """Run one complete monitoring cycle"""
        start_time = time.time()
        stats = {"new_jobs_found": 0, "active_users": 0, "alerts_sent": 0, "errors": 0}

        try:
            logger.info("🔍 Starting real-time monitoring cycle...")

            # Get new jobs
            new_jobs = self.get_new_jobs_since_last_check()
            stats["new_jobs_found"] = len(new_jobs)

            if not new_jobs:
                logger.info("📭 No new jobs found")
                self._update_monitoring_stats(stats, time.time() - start_time)
                return stats

            # Get active users
            active_users = self.get_active_users_with_preferences()
            stats["active_users"] = len(active_users)

            if not active_users:
                logger.info("👥 No active users found")
                self._update_monitoring_stats(stats, time.time() - start_time)
                return stats

            # Check matches for each user
            for user in active_users:
                try:
                    user_id = user["user_id"]

                    # Check daily limit
                    if not self.job_tracker.should_send_more_jobs(
                        user_id, self.max_jobs_per_user_per_day
                    ):
                        continue

                    # Check window status
                    window_status = self.window_manager.get_window_status(user_id)
                    if not window_status.get("has_active_window"):
                        continue

                    # Find matching jobs
                    matching_jobs = self.check_job_matches_for_user(user, new_jobs)

                    # Send alerts for top matches (limit to 1 per cycle to avoid spam)
                    for job in matching_jobs[:1]:
                        if self.send_real_time_job_alert(user, job):
                            stats["alerts_sent"] += 1
                        else:
                            stats["errors"] += 1

                except Exception as e:
                    logger.error(f"❌ Error processing user {user.get('user_id')}: {e}")
                    stats["errors"] += 1

            duration = time.time() - start_time
            self._update_monitoring_stats(stats, duration)

            logger.info(f"✅ Monitoring cycle complete: {stats}")
            return stats

        except Exception as e:
            logger.error(f"❌ Error in monitoring cycle: {e}")
            stats["errors"] += 1
            return stats

    def _update_monitoring_stats(self, stats: Dict, duration: float):
        """Update monitoring statistics in database"""
        try:
            cursor = self.db.connection.cursor()

            cursor.execute(
                """
                INSERT INTO realtime_monitoring 
                (last_check_time, jobs_processed, alerts_sent, check_duration_seconds)
                VALUES (CURRENT_TIMESTAMP, %s, %s, %s)
            """,
                (stats["new_jobs_found"], stats["alerts_sent"], duration),
            )

            self.db.connection.commit()

        except Exception as e:
            logger.error(f"❌ Error updating monitoring stats: {e}")

    def start_continuous_monitoring(self):
        """Start continuous monitoring loop"""
        logger.info(
            f"🚀 Starting continuous job monitoring (every {self.check_interval}s)"
        )

        while True:
            try:
                self.run_monitoring_cycle()
                time.sleep(self.check_interval)

            except KeyboardInterrupt:
                logger.info("⏹️ Monitoring stopped by user")
                break
            except Exception as e:
                logger.error(f"❌ Unexpected error in monitoring loop: {e}")
                time.sleep(60)  # Wait 1 minute before retrying
