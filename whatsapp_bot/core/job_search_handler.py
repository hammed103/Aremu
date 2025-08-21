#!/usr/bin/env python3
"""
Job Search Handler - Manages job search and matching functionality
Handles job retrieval, matching, and delivery to users
"""

import logging
import threading
import time
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


class JobSearchHandler:
    """Handles job search and matching operations"""

    def __init__(
        self,
        db,
        pref_manager,
        job_matcher,
        job_service,
        whatsapp_service,
        conversation_agent,
    ):
        """Initialize job search handler with required dependencies"""
        self.db = db
        self.pref_manager = pref_manager
        self.job_matcher = job_matcher
        self.job_service = job_service
        self.whatsapp_service = whatsapp_service
        self.conversation_agent = conversation_agent

    def handle_job_search(
        self, user_prefs: dict, user_id: int, phone_number: str
    ) -> str:
        """Handle job search requests"""
        # Refresh user preferences to get latest status
        fresh_prefs = self.pref_manager.get_preferences(user_id)

        # Debug: Log what preferences we actually have
        logger.info(f"🔍 DEBUG - User {user_id} preferences: {fresh_prefs}")
        has_meaningful = self._has_meaningful_preferences(fresh_prefs)
        logger.info(f"🔍 DEBUG - Has meaningful preferences: {has_meaningful}")

        if not has_meaningful:
            return "Please set your preferences first. Type 'menu' and select 'Change Preferences'."

        # Get user's name for personalized response
        cursor = self.db.connection.cursor()
        cursor.execute("SELECT name FROM users WHERE id = %s", (user_id,))
        user_name_result = cursor.fetchone()
        user_name = (
            user_name_result[0].split()[0]
            if user_name_result and user_name_result[0]
            else None
        )

        # Get job messages using the job service
        job_messages = self.job_service.generate_realistic_job_listings(
            fresh_prefs, user_name, user_id
        )

        # Send all job messages sequentially
        if job_messages:
            # Send first message (introduction)
            first_message = job_messages[0]

            # Send remaining messages (individual jobs) with small delays AFTER the first message
            if len(job_messages) > 1:

                def send_delayed_messages():
                    time.sleep(2)  # Wait for first message to be sent
                    for message in job_messages[1:]:
                        time.sleep(1)  # Small delay between messages

                        # Handle different message types
                        if (
                            isinstance(message, dict)
                            and message.get("type") == "job_with_button"
                        ):
                            # Send job with apply button including company and title
                            self.whatsapp_service.send_job_with_apply_button(
                                phone_number,
                                message["summary"],
                                message.get("job_url"),
                                message.get("company"),
                                message.get("job_title"),
                            )
                        elif (
                            isinstance(message, dict)
                            and message.get("type") == "follow_up_buttons"
                        ):
                            # Send follow-up message with interactive buttons
                            # Convert button format for send_button_menu
                            formatted_buttons = [
                                {
                                    "type": "reply",
                                    "reply": {"id": btn["id"], "title": btn["title"]},
                                }
                                for btn in message["buttons"]
                            ]
                            self.whatsapp_service.send_button_menu(
                                phone_number, message["message"], formatted_buttons
                            )
                        else:
                            # Send regular text message
                            self.whatsapp_service.send_message(phone_number, message)

                # Send additional messages in background thread
                thread = threading.Thread(target=send_delayed_messages)
                thread.daemon = True
                thread.start()

            return first_message
        else:
            return "No jobs available at the moment."

    def handle_normal_conversation(
        self, user_message: str, user_prefs: dict, user_id: int
    ) -> str:
        """Handle normal conversation using AI agent"""
        # Always use AI conversation agent - no automatic job search
        # The AI agent will handle job requests intelligently based on user preferences

        # Get user's name for conversation
        cursor = self.db.connection.cursor()
        cursor.execute("SELECT name FROM users WHERE id = %s", (user_id,))
        user_name_result = cursor.fetchone()
        user_name = (
            user_name_result[0] if user_name_result and user_name_result[0] else None
        )

        # For now, use empty conversation history - can be enhanced later
        conversation_history = []

        # Generate AI response using conversation agent
        return self.conversation_agent.generate_response(
            user_message, user_prefs or {}, user_name, conversation_history
        )

    def get_matching_jobs(self, user_prefs: dict, limit: int = 10) -> List[Dict]:
        """Get jobs matching user preferences"""
        try:
            # Use the job matcher to find relevant jobs
            matching_jobs = self.job_matcher.find_matching_jobs(user_prefs, limit=limit)
            return matching_jobs
        except Exception as e:
            logger.error(f"Error getting matching jobs: {e}")
            return []

    def format_job_message(self, job: Dict, user_name: str = None) -> str:
        """Format a single job into a WhatsApp message"""
        try:
            # Extract job details
            title = job.get("title", "Job Opportunity")
            company = job.get("company", "Company")
            location = job.get("location", "Location not specified")
            salary = job.get("salary", "Salary not specified")
            description = job.get("description", "")

            # Format the message
            message = f"💼 *{title}*\n"
            message += f"🏢 {company}\n"
            message += f"📍 {location}\n"

            if salary and salary != "Salary not specified":
                message += f"💰 {salary}\n"

            message += "\n"

            # Add description if available (truncated)
            if description:
                # Truncate description to reasonable length
                if len(description) > 200:
                    description = description[:200] + "..."
                message += f"📝 {description}\n\n"

            # Add application instructions
            apply_url = job.get("apply_url", "")
            apply_email = job.get("apply_email", "")

            if apply_url:
                message += f"🔗 Apply: {apply_url}"
            elif apply_email:
                message += f"📧 Apply: {apply_email}"
            else:
                message += "Contact the company to apply"

            return message

        except Exception as e:
            logger.error(f"Error formatting job message: {e}")
            return "Error formatting job details"

    def format_job_summary_message(
        self, jobs: List[Dict], user_name: str = None
    ) -> str:
        """Format a summary message for multiple jobs"""
        try:
            if not jobs:
                return "No jobs found matching your preferences at the moment."

            greeting = f"Hi {user_name}! " if user_name else "Hi! "

            if len(jobs) == 1:
                summary = f"{greeting}I found 1 job matching your preferences:"
            else:
                summary = (
                    f"{greeting}I found {len(jobs)} jobs matching your preferences:"
                )

            return summary

        except Exception as e:
            logger.error(f"Error formatting job summary: {e}")
            return "Here are your job matches:"

    def check_job_availability(self, user_prefs: dict) -> bool:
        """Check if there are any jobs available for user preferences"""
        try:
            jobs = self.get_matching_jobs(user_prefs, limit=1)
            return len(jobs) > 0
        except Exception as e:
            logger.error(f"Error checking job availability: {e}")
            return False

    def get_job_statistics(self, user_prefs: dict) -> Dict:
        """Get statistics about available jobs for user preferences"""
        try:
            # Get all matching jobs
            all_jobs = self.get_matching_jobs(user_prefs, limit=100)

            # Calculate statistics
            stats = {
                "total_jobs": len(all_jobs),
                "companies": len(set(job.get("company", "") for job in all_jobs)),
                "locations": len(set(job.get("location", "") for job in all_jobs)),
                "job_types": len(set(job.get("job_type", "") for job in all_jobs)),
            }

            return stats

        except Exception as e:
            logger.error(f"Error getting job statistics: {e}")
            return {"total_jobs": 0, "companies": 0, "locations": 0, "job_types": 0}

    def send_job_alerts(self, user_id: int, phone_number: str) -> bool:
        """Send job alerts to user if new jobs are available"""
        try:
            # Get user preferences
            user_prefs = self.pref_manager.get_preferences(user_id)
            if not user_prefs or not user_prefs.get("preferences_confirmed"):
                return False

            # Check for new jobs
            if self.check_job_availability(user_prefs):
                # Get user's name
                cursor = self.db.connection.cursor()
                cursor.execute("SELECT name FROM users WHERE id = %s", (user_id,))
                user_name_result = cursor.fetchone()
                user_name = (
                    user_name_result[0].split()[0]
                    if user_name_result and user_name_result[0]
                    else None
                )

                # Send job alert
                alert_message = (
                    f"🚨 *New Job Alert!*\n\n"
                    f"Hi {user_name or 'there'}! I found new jobs matching your preferences.\n\n"
                    "Type 'menu' and select 'Show Jobs' to see them now!"
                )

                return self.whatsapp_service.send_message(phone_number, alert_message)

            return True

        except Exception as e:
            logger.error(f"Error sending job alerts: {e}")
            return False

    def handle_job_feedback(self, user_id: int, job_id: str, feedback: str) -> str:
        """Handle user feedback on job recommendations"""
        try:
            # Store feedback for improving recommendations
            cursor = self.db.connection.cursor()
            cursor.execute(
                """
                INSERT INTO job_feedback (user_id, job_id, feedback, created_at)
                VALUES (%s, %s, %s, NOW())
                ON CONFLICT (user_id, job_id) 
                DO UPDATE SET feedback = EXCLUDED.feedback, created_at = NOW()
                """,
                (user_id, job_id, feedback),
            )
            self.db.connection.commit()

            if feedback.lower() in ["like", "interested", "good"]:
                return "✅ Thanks for the feedback! I'll find more jobs like this one."
            elif feedback.lower() in ["dislike", "not interested", "bad"]:
                return "👍 Got it! I'll avoid recommending similar jobs in the future."
            else:
                return "📝 Thanks for your feedback! This helps me improve your job recommendations."

        except Exception as e:
            logger.error(f"Error handling job feedback: {e}")
            return "Thanks for your feedback!"

    def _has_meaningful_preferences(self, user_prefs: dict) -> bool:
        """Check if user has meaningful preferences set (regardless of confirmation status)"""
        if not user_prefs:
            return False

        # Check for key preference fields that indicate user has set up their profile
        # Include backward compatibility for existing users with old field names
        meaningful_fields = [
            "job_roles",
            "preferred_locations",  # Standard field name
            "location",  # Backward compatibility for existing users
            "work_arrangements",
            "years_of_experience",
            "salary_min",
        ]

        for field in meaningful_fields:
            value = user_prefs.get(field)
            if value is not None:
                # For lists, check if not empty
                if isinstance(value, list) and len(value) > 0:
                    return True
                # For non-lists, check if not empty/zero
                elif not isinstance(value, list) and value:
                    return True

        return False

    def _is_job_request(self, user_message: str) -> bool:
        """Check if user message is asking about jobs"""
        job_keywords = [
            "job",
            "jobs",
            "work",
            "employment",
            "position",
            "role",
            "opportunity",
            "opportunities",
            "vacancy",
            "vacancies",
            "hiring",
            "career",
            "opening",
            "openings",
        ]

        message_lower = user_message.lower()

        # Check for job-related keywords
        for keyword in job_keywords:
            if keyword in message_lower:
                return True

        return False

    def get_personalized_job_tips(self, user_prefs: dict, user_name: str = None) -> str:
        """Get personalized job search tips based on user preferences"""
        try:
            tips = []

            # Add tips based on experience level
            experience = user_prefs.get("years_of_experience", 0)
            if experience == 0:
                tips.append(
                    "💡 As an entry-level candidate, focus on showcasing your skills and eagerness to learn"
                )
            elif experience < 3:
                tips.append(
                    "💡 Highlight your achievements and growth in your current/previous roles"
                )
            else:
                tips.append(
                    "💡 Emphasize your leadership experience and impact on previous projects"
                )

            # Add tips based on work arrangements
            work_arrangements = user_prefs.get("work_arrangements", [])
            if "Remote" in work_arrangements:
                tips.append(
                    "🏠 For remote roles, highlight your self-management and communication skills"
                )

            # Add tips based on job roles
            job_roles = user_prefs.get("job_roles", [])
            if any("developer" in role.lower() for role in job_roles):
                tips.append(
                    "💻 Keep your GitHub profile updated and showcase your best projects"
                )

            if tips:
                greeting = f"Hi {user_name}! " if user_name else "Hi! "
                return (
                    f"{greeting}Here are some personalized job search tips:\n\n"
                    + "\n\n".join(tips)
                )
            else:
                return "Keep applying and stay positive! The right opportunity is out there."

        except Exception as e:
            logger.error(f"Error getting personalized tips: {e}")
            return "Keep up the great work with your job search!"
