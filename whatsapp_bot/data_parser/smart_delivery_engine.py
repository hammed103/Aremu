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
whatsapp_bot_path = os.path.join(os.path.dirname(__file__), "..")
sys.path.insert(0, whatsapp_bot_path)  # Use insert(0, ...) for higher priority

from legacy.database_manager import DatabaseManager
from legacy.intelligent_job_matcher import IntelligentJobMatcher
from legacy.job_tracking_system import JobTrackingSystem
from legacy.window_management_system import WindowManagementSystem

# Import apply button designer with robust error handling
apply_button_designer = None

try:
    # Try local copy first
    from apply_button_designer import apply_button_designer

    print("✅ Smart Delivery Engine: Using local apply button designer")
except ImportError:
    try:
        # Try WhatsApp bot utils import
        from utils.apply_button_designer import apply_button_designer

        print("✅ Smart Delivery Engine: Using WhatsApp bot apply button designer")
    except ImportError as e:
        try:
            # Try with explicit importlib approach
            import importlib.util

            apply_button_path = os.path.join(
                whatsapp_bot_path, "utils", "apply_button_designer.py"
            )
            spec = importlib.util.spec_from_file_location(
                "apply_button_designer", apply_button_path
            )
            apply_button_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(apply_button_module)
            apply_button_designer = apply_button_module.apply_button_designer
            print("✅ Smart Delivery Engine: Using importlib apply button designer")
        except Exception as e2:
            # Final fallback if all imports fail
            class FallbackApplyButtonDesigner:
                def get_apply_button_text(self, job_url, company=None, job_title=None):
                    return "🚀 Apply Now"

            apply_button_designer = FallbackApplyButtonDesigner()
            print(f"⚠️ Smart Delivery Engine: Using fallback ({e}, {e2})")

logger = logging.getLogger(__name__)


class SmartDeliveryEngine:
    """Real-time job delivery engine integrated with data parser"""

    def __init__(self, whatsapp_token=None, whatsapp_phone_id=None):
        self.db = DatabaseManager()
        self.job_matcher = IntelligentJobMatcher(self.db.connection)
        self.job_tracker = JobTrackingSystem()
        self.window_manager = WindowManagementSystem()

        # WhatsApp configuration - load from environment if not provided
        self.whatsapp_token = whatsapp_token or self._load_whatsapp_token()
        self.whatsapp_phone_id = whatsapp_phone_id or self._load_whatsapp_phone_id()
        self.whatsapp_api_url = None

        if self.whatsapp_token and self.whatsapp_phone_id:
            self.whatsapp_api_url = (
                f"https://graph.facebook.com/v18.0/{self.whatsapp_phone_id}/messages"
            )

        # Delivery settings
        self.min_match_score = 50  # Minimum match score for delivery
        self.max_jobs_per_user_per_day = None  # No daily limits
        self.max_alerts_per_batch = 50  # Prevent spam during large scraping

        logger.info("🚀 Smart Delivery Engine initialized")

    def _load_whatsapp_token(self):
        """Load WhatsApp access token from environment"""
        try:
            env_path = os.path.join(os.path.dirname(__file__), "..", ".env")
            if os.path.exists(env_path):
                with open(env_path, "r") as f:
                    for line in f:
                        if line.startswith("WHATSAPP_ACCESS_TOKEN="):
                            return line.split("=", 1)[1].strip()
            return os.getenv("WHATSAPP_ACCESS_TOKEN")
        except Exception as e:
            logger.error(f"Error loading WhatsApp token: {e}")
            return None

    def _load_whatsapp_phone_id(self):
        """Load WhatsApp phone number ID from environment"""
        try:
            env_path = os.path.join(os.path.dirname(__file__), "..", ".env")
            if os.path.exists(env_path):
                with open(env_path, "r") as f:
                    for line in f:
                        if line.startswith("WHATSAPP_PHONE_NUMBER_ID="):
                            return line.split("=", 1)[1].strip()
            return os.getenv("WHATSAPP_PHONE_NUMBER_ID")
        except Exception as e:
            logger.error(f"Error loading WhatsApp phone ID: {e}")
            return None

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
                AND cw.last_activity >= CURRENT_TIMESTAMP - INTERVAL '7 days'
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
                # Check daily limit first (if enabled)
                user_id = user["user_id"]
                user_name = user.get("name", "Unknown")

                print(f"🔍 Processing User {user_id} ({user_name})...")

                # Skip daily limit check if max_jobs_per_user_per_day is None
                if self.max_jobs_per_user_per_day is not None:
                    if not self.job_tracker.should_send_more_jobs(
                        user_id, self.max_jobs_per_user_per_day
                    ):
                        print(f"   ⏸️ User {user_id} hit daily limit, skipping")
                        continue
                else:
                    print(
                        f"   ♾️ No daily limits - processing all jobs for User {user_id}"
                    )

                # Check if job already shown
                unseen_jobs = self.job_tracker.get_unseen_jobs(user_id, [job])
                if unseen_jobs:
                    print(f"   ✅ User {user_id} has unseen jobs, calculating match...")

                    # Convert user row to preferences format for intelligent matcher
                    user_prefs = self._convert_user_to_preferences_format(user)

                    # Debug logging - UPDATED VERSION
                    print(f"🔧 DEBUG: User {user_id} preferences: {user_prefs}")

                    # Calculate match score
                    match_score = self.job_matcher._calculate_job_score(user_prefs, job)

                    if match_score >= self.min_match_score:
                        matches.append(
                            {"user": user, "job": job, "match_score": match_score}
                        )
                else:
                    print(f"   ⏭️ User {user_id} has already seen this job, skipping")

            except Exception as e:
                logger.error(
                    f"❌ Error calculating match for user {user.get('user_id')}: {e}"
                )
                logger.error(f"🔧 User data: {user}")
                logger.error(f"🔧 Job data: {job.get('id', 'unknown')}")
                import traceback

                logger.error(f"🔧 Full traceback: {traceback.format_exc()}")
                continue

        # Sort by match score (highest first)
        matches.sort(key=lambda x: x["match_score"], reverse=True)
        return matches

    def _convert_user_to_preferences_format(self, user: Dict) -> Dict:
        """Convert user database row to preferences format for intelligent matcher"""

        def ensure_list_of_strings(value):
            """Ensure value is a list of strings"""
            if value is None:
                return []
            if isinstance(value, str):
                return [value]  # Convert single string to list
            if isinstance(value, list):
                # Ensure all items are strings
                return [str(item) for item in value if item is not None]
            return []

        return {
            "job_roles": ensure_list_of_strings(user.get("job_roles")),
            "technical_skills": ensure_list_of_strings(user.get("technical_skills")),
            "preferred_locations": ensure_list_of_strings(
                user.get("preferred_locations")
            ),
            "salary_min": user.get("salary_min"),
            "salary_currency": user.get("salary_currency"),
            "willing_to_relocate": user.get("willing_to_relocate", False),
            "work_arrangements": ensure_list_of_strings(user.get("work_arrangements")),
            "years_of_experience": user.get("years_of_experience"),
            "experience_level": user.get("experience_level"),
            "job_categories": ensure_list_of_strings(user.get("job_categories")),
            "industry_preferences": ensure_list_of_strings(
                user.get("industry_preferences")
            ),
        }

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

            # Format alert message with clean AI summary (no apply section)
            alert_msg = f"🚨 *NEW JOB ALERT!* ({match_score:.0f}% match)\n\n"

            # Use AI summary if available (now clean without apply section)
            if job.get("ai_summary"):
                alert_msg += job["ai_summary"]
            else:
                # Fallback formatting
                alert_msg += f"🚀 **{job.get('title', 'Job Opportunity')}** at **{job.get('company', 'Company')}**\n"
                alert_msg += f"📍 {job.get('location', 'Location not specified')}\n"
                if job.get("salary_min"):
                    currency = job.get("salary_currency", "NGN")
                    alert_msg += f"💰 {job['salary_min']:,} {currency}+\n"

            # Use WhatsApp service for smart CTA button handling
            try:
                # Import WhatsApp service for advanced button functionality
                whatsapp_service_path = os.path.join(
                    os.path.dirname(__file__), "..", "services"
                )
                sys.path.append(whatsapp_service_path)
                from whatsapp_service import WhatsAppService

                # Create WhatsApp service instance
                whatsapp_service = WhatsAppService()

                # Send job with smart CTA buttons (dual buttons if both URL and WhatsApp available)
                success = whatsapp_service.send_job_with_apply_button(
                    phone_number,
                    alert_msg,
                    job.get("job_url"),
                    job.get("company"),
                    job.get("title"),
                    job.get("whatsapp_number") or job.get("ai_whatsapp_number"),
                    job.get("email") or job.get("ai_email"),
                )

                if success:
                    logger.info(
                        f"🚨 Sent smart CTA alert to {phone_number} for job {job.get('id')}"
                    )
                    return True
                else:
                    logger.error(f"❌ Failed to send smart CTA alert")
                    return False

            except Exception as import_error:
                logger.warning(
                    f"⚠️ WhatsApp service not available, using fallback: {import_error}"
                )

                # Fallback to basic implementation
                headers = {
                    "Authorization": f"Bearer {self.whatsapp_token}",
                    "Content-Type": "application/json",
                }

                job_url = job.get("job_url")
                if job_url:
                    # Get smart apply button text based on context
                    button_text = apply_button_designer.get_apply_button_text(
                        job_url, job.get("company"), job.get("title")
                    )
                    # Send with CTA URL button that opens website directly
                    payload = {
                        "messaging_product": "whatsapp",
                        "to": phone_number,
                        "type": "interactive",
                        "interactive": {
                            "type": "cta_url",
                            "body": {"text": alert_msg},
                            "action": {
                                "name": "cta_url",
                                "parameters": {
                                    "display_text": button_text,
                                    "url": job_url,
                                },
                            },
                        },
                    }
                else:
                    # Send as regular text message if no job URL
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
                        f"🚨 Sent fallback alert to {phone_number} for job {job.get('id')}"
                    )
                    return True
                else:
                    logger.error(f"❌ Failed to send fallback alert: {response.text}")
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
                            import time

                            time.sleep(0.1)  # Small delay to ensure commit is processed
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
