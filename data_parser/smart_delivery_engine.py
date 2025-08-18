#!/usr/bin/env python3
"""
Smart Delivery Engine for Real-Time Job Distribution
Integrates with data parser to deliver jobs instantly to users within active windows
"""

import logging
import sys
import os
from typing import List, Dict, Optional

# Add WhatsApp bot path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "whatsapp_bot"))

from legacy.database_manager import DatabaseManager
from legacy.intelligent_job_matcher import IntelligentJobMatcher
from legacy.job_tracking_system import JobTrackingSystem
from legacy.window_management_system import WindowManagementSystem

logger = logging.getLogger(__name__)


class SmartDeliveryEngine:
    """Real-time job delivery engine integrated with data parser"""

    def __init__(self, whatsapp_token=None, whatsapp_phone_id=None):
        self.db = DatabaseManager()
        self.job_matcher = IntelligentJobMatcher(self.db.connection)
        self.job_tracker = JobTrackingSystem()
        self.window_manager = WindowManagementSystem()

        # WhatsApp configuration
        self.whatsapp_token = whatsapp_token
        self.whatsapp_phone_id = whatsapp_phone_id
        self.whatsapp_api_url = None

        if whatsapp_token and whatsapp_phone_id:
            self.whatsapp_api_url = (
                f"https://graph.facebook.com/v18.0/{whatsapp_phone_id}/messages"
            )

        # Delivery settings
        self.min_match_score = 39  # Minimum match score for delivery
        self.max_jobs_per_user_per_day = 10
        self.max_alerts_per_batch = 50  # Prevent spam during large scraping

        logger.info("🚀 Smart Delivery Engine initialized")

    def get_eligible_users_for_delivery(self) -> List[Dict]:
        """Get users eligible for job delivery (active window + confirmed preferences)"""
        try:
            cursor = self.db.connection.cursor()

            cursor.execute(
                """
                SELECT DISTINCT 
                    u.id,
                    u.phone_number,
                    u.name,
                    up.job_roles,
                    up.preferred_locations,
                    up.technical_skills,
                    up.years_of_experience,
                    up.salary_min,
                    up.salary_currency,
                    up.work_arrangements,
                    up.experience_level,
                    cw.messages_in_window,
                    cw.last_activity
                FROM users u
                JOIN user_preferences up ON u.id = up.user_id
                JOIN conversation_windows cw ON u.id = cw.user_id
                WHERE up.preferences_confirmed = TRUE
                AND cw.window_status = 'active'
                AND cw.last_activity >= CURRENT_TIMESTAMP - INTERVAL '24 hours'
                AND EXTRACT(EPOCH FROM (CURRENT_TIMESTAMP - cw.window_start))/3600 < 24
            """
            )

            eligible_users = []
            for row in cursor.fetchall():
                eligible_users.append(
                    {
                        "user_id": row[0],
                        "phone_number": row[1],
                        "name": row[2],
                        "job_roles": row[3],
                        "preferred_locations": row[4],
                        "technical_skills": row[5],
                        "years_experience": row[6],
                        "salary_min": row[7],
                        "salary_currency": row[8],
                        "work_arrangements": row[9],
                        "experience_level": row[10],
                        "messages_in_window": row[11],
                        "last_activity": row[12],
                    }
                )

            logger.info(f"👥 Found {len(eligible_users)} eligible users for delivery")
            return eligible_users

        except Exception as e:
            logger.error(f"❌ Error getting eligible users: {e}")
            return []

    def calculate_job_matches_for_users(
        self, job: Dict, eligible_users: List[Dict]
    ) -> List[Dict]:
        """Calculate match scores for a job against eligible users"""
        matches = []

        for user in eligible_users:
            try:
                # Check daily limit first
                user_id = user["user_id"]
                if not self.job_tracker.should_send_more_jobs(
                    user_id, self.max_jobs_per_user_per_day
                ):
                    continue

                # Check if job already shown
                if self.job_tracker.get_unseen_jobs(user_id, [job]):
                    # Calculate match score
                    match_score = self.job_matcher._calculate_job_score(user, job)

                    if match_score >= self.min_match_score:
                        matches.append(
                            {"user": user, "job": job, "match_score": match_score}
                        )

            except Exception as e:
                logger.error(
                    f"❌ Error calculating match for user {user.get('user_id')}: {e}"
                )
                continue

        # Sort by match score (highest first)
        matches.sort(key=lambda x: x["match_score"], reverse=True)
        return matches

    def send_whatsapp_job_alert(
        self, user: Dict, job: Dict, match_score: float
    ) -> bool:
        """Send WhatsApp job alert to user"""
        try:
            if not self.whatsapp_api_url or not self.whatsapp_token:
                logger.warning("⚠️ WhatsApp credentials not configured")
                return False

            import requests

            phone_number = user["phone_number"]

            # Format alert message
            alert_msg = f"🚨 *NEW JOB ALERT!* ({match_score:.0f}% match)\n\n"

            # Use AI summary if available
            if job.get("ai_summary"):
                alert_msg += job["ai_summary"]
            else:
                # Fallback formatting
                alert_msg += f"🚀 **{job.get('title', 'Job Opportunity')}** at **{job.get('company', 'Company')}**\n"
                alert_msg += f"📍 {job.get('location', 'Location not specified')}\n"
                if job.get("salary_min"):
                    currency = job.get("salary_currency", "NGN")
                    alert_msg += f"💰 {job['salary_min']:,} {currency}+\n"
                alert_msg += f"\n🔗 **Apply:** {job.get('job_url', 'Contact employer')}"

            # Send WhatsApp message
            headers = {
                "Authorization": f"Bearer {self.whatsapp_token}",
                "Content-Type": "application/json",
            }

            payload = {
                "messaging_product": "whatsapp",
                "to": phone_number,
                "type": "text",
                "text": {"body": alert_msg},
            }

            response = requests.post(
                self.whatsapp_api_url, headers=headers, json=payload
            )

            if response.status_code == 200:
                logger.info(
                    f"🚨 Sent real-time alert to {phone_number} for job {job.get('id')}"
                )
                return True
            else:
                logger.error(f"❌ Failed to send alert: {response.text}")
                return False

        except Exception as e:
            logger.error(f"❌ Error sending WhatsApp alert: {e}")
            return False

    def process_single_job_delivery(self, job: Dict) -> Dict:
        """Process delivery for a single new job"""
        stats = {
            "job_id": job.get("id"),
            "job_title": job.get("title"),
            "eligible_users": 0,
            "matches_found": 0,
            "alerts_sent": 0,
            "errors": 0,
        }

        try:
            # Get eligible users
            eligible_users = self.get_eligible_users_for_delivery()
            stats["eligible_users"] = len(eligible_users)

            if not eligible_users:
                logger.info(f"👥 No eligible users for job {job.get('id')}")
                return stats

            # Calculate matches
            matches = self.calculate_job_matches_for_users(job, eligible_users)
            stats["matches_found"] = len(matches)

            if not matches:
                logger.info(f"🎯 No matches found for job {job.get('id')}")
                return stats

            # Send alerts to matching users
            for match in matches:
                try:
                    user = match["user"]
                    match_score = match["match_score"]

                    # Send alert
                    if self.send_whatsapp_job_alert(user, job, match_score):
                        # Mark job as shown (with error handling for timing issues)
                        try:
                            self.job_tracker.mark_job_as_shown(
                                user["user_id"],
                                job["id"],
                                match_score,
                                "real_time_parser",
                            )
                        except Exception as e:
                            logger.warning(
                                f"⚠️ Could not mark job {job['id']} as shown: {e}"
                            )
                        stats["alerts_sent"] += 1
                    else:
                        stats["errors"] += 1

                except Exception as e:
                    logger.error(f"❌ Error processing match: {e}")
                    stats["errors"] += 1

            logger.info(
                f"✅ Job {job.get('id')} delivery: {stats['alerts_sent']} alerts sent"
            )
            return stats

        except Exception as e:
            logger.error(f"❌ Error in single job delivery: {e}")
            stats["errors"] += 1
            return stats

    def process_batch_job_delivery(self, jobs: List[Dict]) -> Dict:
        """Process delivery for a batch of new jobs"""
        batch_stats = {
            "total_jobs": len(jobs),
            "jobs_processed": 0,
            "total_alerts_sent": 0,
            "total_errors": 0,
            "job_details": [],
        }

        try:
            logger.info(f"🚀 Starting batch delivery for {len(jobs)} jobs")

            # Get eligible users once for the batch
            eligible_users = self.get_eligible_users_for_delivery()

            if not eligible_users:
                logger.info("👥 No eligible users for batch delivery")
                return batch_stats

            alerts_sent_in_batch = 0

            for job in jobs:
                try:
                    # Check batch limit to prevent spam
                    if alerts_sent_in_batch >= self.max_alerts_per_batch:
                        logger.warning(
                            f"⚠️ Batch alert limit reached ({self.max_alerts_per_batch})"
                        )
                        break

                    # Process single job
                    job_stats = self.process_single_job_delivery(job)

                    batch_stats["jobs_processed"] += 1
                    batch_stats["total_alerts_sent"] += job_stats["alerts_sent"]
                    batch_stats["total_errors"] += job_stats["errors"]
                    batch_stats["job_details"].append(job_stats)

                    alerts_sent_in_batch += job_stats["alerts_sent"]

                except Exception as e:
                    logger.error(f"❌ Error processing job {job.get('id')}: {e}")
                    batch_stats["total_errors"] += 1

            logger.info(
                f"✅ Batch delivery complete: {batch_stats['total_alerts_sent']} total alerts sent"
            )
            return batch_stats

        except Exception as e:
            logger.error(f"❌ Error in batch delivery: {e}")
            batch_stats["total_errors"] += 1
            return batch_stats

    def is_delivery_enabled(self) -> bool:
        """Check if delivery is properly configured"""
        return bool(self.whatsapp_token and self.whatsapp_phone_id)
