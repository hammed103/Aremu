#!/usr/bin/env python3
"""
Bot Controller - Main business logic controller
Orchestrates all components and handles conversation flow
"""

import logging
from typing import Dict, Optional
from legacy.database_manager import DatabaseManager
from legacy.flexible_preference_manager import FlexiblePreferenceManager
from legacy.intelligent_job_matcher import IntelligentJobMatcher
from legacy.job_tracking_system import JobTrackingSystem
from legacy.window_management_system import WindowManagementSystem
from agents.conversation_agent import ConversationAgent, PreferenceParsingAgent
from services.job_service import JobService
from services.whatsapp_service import WhatsAppService

logger = logging.getLogger(__name__)


class BotController:
    """Main controller that orchestrates all bot functionality"""

    def __init__(
        self, openai_api_key: str, whatsapp_token: str, whatsapp_phone_id: str
    ):
        """Initialize the bot controller with all components"""
        # Initialize database and core managers
        self.db = DatabaseManager()
        self.db.ensure_tables_exist()

        # Initialize preference and job managers
        self.pref_manager = FlexiblePreferenceManager(self.db.connection)
        self.job_matcher = IntelligentJobMatcher(self.db.connection)
        self.job_tracker = JobTrackingSystem()
        self.window_manager = WindowManagementSystem()

        # Initialize AI agents
        self.conversation_agent = ConversationAgent(openai_api_key)
        self.preference_parser = PreferenceParsingAgent(openai_api_key)

        # Initialize services
        self.job_service = JobService()
        self.whatsapp_service = WhatsAppService(whatsapp_token, whatsapp_phone_id)

        logger.info("🤖 Bot Controller initialized with all components")

    def handle_message(self, phone_number: str, user_message: str) -> str:
        """Main message handling logic - orchestrates the entire conversation flow"""
        try:
            user_id = self.db.get_or_create_user(phone_number)
            user_message_lower = user_message.lower().strip()

            # STEP 1: Handle commands first
            if user_message_lower in ["help", "/help"]:
                return self._show_help_menu()

            if user_message_lower in ["settings", "/settings"]:
                return self._show_preference_form(phone_number)

            # STEP 2: Check if this is a preference form submission
            if self._is_preference_form(user_message):
                return self._process_preference_form(user_message, phone_number)

            # STEP 3: Check for new user flow (welcome + form)
            conversation_history = self.db.get_conversation_history(user_id, limit=1)
            user_prefs = self.pref_manager.get_preferences(user_id)

            if not conversation_history and (
                not user_prefs or not user_prefs.get("preferences_confirmed")
            ):
                # Send welcome message + form for brand new users
                welcome_msg = self._send_welcome_message()
                form_msg = self._show_preference_form(phone_number, first_time=True)
                return f"{welcome_msg}\n\n{form_msg}"

            # STEP 4: Handle preference confirmation
            if (
                user_prefs
                and not user_prefs.get("preferences_confirmed")
                and user_message_lower in ["yes", "y", "confirm", "correct"]
            ):
                return self._confirm_user_preferences(user_id)

            # STEP 5: Handle job search requests
            if user_message_lower in ["jobs", "show jobs", "find jobs"]:
                return self._handle_job_search(user_prefs, user_id, phone_number)

            # STEP 6: Handle job detail requests (numbers 1, 2, 3)
            if user_message_lower in ["1", "2", "3"]:
                job_number = int(user_message_lower)
                return self.job_service.get_detailed_job_info(
                    job_number, user_prefs or {}
                )

            # STEP 7: Normal conversation using AI agent
            return self._handle_normal_conversation(user_message, user_prefs, user_id)

        except Exception as e:
            logger.error(f"❌ Error handling message: {e}")
            return "I'm having trouble processing your message. Please try again."

    def _show_help_menu(self) -> str:
        """Show help menu"""
        return (
            "👋 *Welcome to Aremu Job Bot!*\n\n"
            "🎯 *How it works:*\n"
            "1. Fill out your job preferences form\n"
            "2. I'll find matching jobs for you\n"
            "3. Get instant alerts when new jobs appear!\n\n"
            "⚡ *Commands:*\n"
            "• Type `settings` - Set your job preferences\n"
            "• Type `jobs` - See available jobs\n\n"
            "Start by typing `settings` to set up your preferences! 😊"
        )

    def _send_welcome_message(self) -> str:
        """Send preset welcome message for new users"""
        return (
            "👋 Hello! I'm Aremu, your AI job search assistant.\n\n"
            "I help Nigerians find their perfect jobs quickly and easily.\n\n"
            "Let me get your job preferences to start finding opportunities for you:"
        )

    def _show_preference_form(self, phone_number: str, first_time: bool = False) -> str:
        """Show preference form to user"""
        try:
            user_id = self.db.get_or_create_user(phone_number)
            current_prefs = self.pref_manager.get_preferences(user_id)

            if first_time:
                intro = "🎯 *Welcome! Let's set up your job preferences.*\n\n"
            else:
                intro = "⚙️ *Update your job preferences:*\n\n"

            # Get current values or use examples
            cursor = self.db.connection.cursor()
            cursor.execute("SELECT name FROM users WHERE id = %s", (user_id,))
            user_name_result = cursor.fetchone()
            current_name = (
                user_name_result[0]
                if user_name_result and user_name_result[0]
                else "John Doe"
            )

            job_title = (
                ", ".join(current_prefs.get("job_roles", []))
                if current_prefs and current_prefs.get("job_roles")
                else "Software Developer, Frontend Developer"
            )
            location = (
                ", ".join(current_prefs.get("preferred_locations", []))
                if current_prefs and current_prefs.get("preferred_locations")
                else "Lagos, Abuja, Remote"
            )
            salary = (
                f"₦{current_prefs.get('salary_min', 500000):,}"
                if current_prefs and current_prefs.get("salary_min")
                else "₦500,000"
            )
            experience = (
                f"{current_prefs.get('years_of_experience', 3)} years"
                if current_prefs and current_prefs.get("years_of_experience")
                else "3 years"
            )
            work_style = (
                ", ".join(current_prefs.get("work_arrangements", []))
                if current_prefs and current_prefs.get("work_arrangements")
                else "Remote, Hybrid, Onsite"
            )

            form = (
                f"{intro}"
                "📝 *Copy and edit this form:*\n\n"
                f"**Full Name:** {current_name}\n"
                f"**Job Title:** {job_title}\n"
                f"**Location:** {location}\n"
                f"**Minimum Salary:** {salary}\n"
                f"**Experience:** {experience}\n"
                f"**Work Style:** {work_style}\n\n"
                "📱 *Just copy, edit and send back!*\n\n"
            )

            if not first_time:
                form += (
                    "Note: You can always change your preferences by sending `settings`"
                )

            return form

        except Exception as e:
            logger.error(f"❌ Error showing preference form: {e}")
            return "I'm having trouble showing the form. Please try typing 'settings' again."

    def _is_preference_form(self, message: str) -> bool:
        """Check if message is a filled preference form"""
        form_keywords = [
            "full name:",
            "job title:",
            "location:",
            "minimum salary:",
            "experience:",
            "work style:",
            "salary:",
        ]
        message_lower = message.lower()
        matches = sum(1 for keyword in form_keywords if keyword in message_lower)
        return matches >= 3  # Must contain at least 3 form fields

    def _process_preference_form(self, message: str, phone_number: str) -> str:
        """Process filled preference form using LLM parser"""
        try:
            user_id = self.db.get_or_create_user(phone_number)

            # Use AI agent to parse preferences
            preferences = self.preference_parser.parse_preferences_from_form(message)

            if not preferences:
                return (
                    "❌ I couldn't understand the form. Please use this format:\n\n"
                    "**Full Name:** Ahmed Ibrahim\n"
                    "**Job Title:** Software Developer\n"
                    "**Location:** Lagos\n"
                    "**Minimum Salary:** ₦500,000\n"
                    "**Experience:** 3 years\n"
                    "**Work Style:** Remote\n\n"
                    "Type `settings` to see the form again."
                )

            # Save preferences
            success = self.pref_manager.save_preferences(user_id, preferences)

            if success:
                # Save full name to users table if provided
                if preferences.get("full_name"):
                    cursor = self.db.connection.cursor()
                    cursor.execute(
                        "UPDATE users SET name = %s WHERE id = %s",
                        (preferences["full_name"], user_id),
                    )
                    self.db.connection.commit()

                # Show confirmation instead of immediately confirming
                return self._show_preference_confirmation(user_id, preferences)
            else:
                return "❌ Failed to save preferences. Please try again."

        except Exception as e:
            logger.error(f"❌ Error processing preference form: {e}")
            return "Something went wrong. Type `settings` to try again."

    def _show_preference_confirmation(self, user_id: int, preferences: dict) -> str:
        """Show user their preferences and ask for confirmation"""
        try:
            # Get user's name
            cursor = self.db.connection.cursor()
            cursor.execute("SELECT name FROM users WHERE id = %s", (user_id,))
            user_name_result = cursor.fetchone()
            user_name = (
                user_name_result[0]
                if user_name_result and user_name_result[0]
                else "there"
            )

            # Format the confirmation message
            name_part = f"Hi {user_name}! " if user_name != "there" else "Hi! "

            confirmation_msg = (
                f"{name_part}I've saved your job preferences:\n\n"
                f"👤 **Name:** {preferences.get('full_name', 'Not provided')}\n"
                f"🎯 **Looking for:** {', '.join(preferences.get('job_roles', []))}\n"
                f"📍 **Location:** {', '.join(preferences.get('preferred_locations', []))}\n"
                f"💰 **Salary:** ₦{preferences.get('salary_min', 0):,}+ {preferences.get('salary_currency', 'NGN')}\n"
                f"⏱️ **Experience:** {preferences.get('years_of_experience', 'Not specified')} years\n"
                f"🏢 **Work Style:** {', '.join(preferences.get('work_arrangements', []))}\n\n"
                "✅ **Please confirm:** Are these details correct?\n\n"
                "Reply 'Yes' to confirm and start job search, or type 'settings' to make changes."
            )

            return confirmation_msg

        except Exception as e:
            logger.error(f"❌ Error showing confirmation: {e}")
            return "Please confirm your preferences by replying 'Yes' or type 'settings' to make changes."

    def _confirm_user_preferences(self, user_id: int) -> str:
        """Confirm user preferences and start job search"""
        try:
            # Mark preferences as confirmed
            cursor = self.db.connection.cursor()
            cursor.execute(
                "UPDATE user_preferences SET preferences_confirmed = TRUE WHERE user_id = %s",
                (user_id,),
            )
            self.db.connection.commit()

            # Start window for job monitoring
            self.window_manager.start_new_window(user_id)

            # Get user's name for personalized response
            cursor.execute("SELECT name FROM users WHERE id = %s", (user_id,))
            user_name_result = cursor.fetchone()
            user_name = (
                user_name_result[0].split()[0]
                if user_name_result and user_name_result[0]
                else "there"
            )

            return (
                f"🎉 Perfect, {user_name}! Your preferences are confirmed.\n\n"
                "🔍 I'm now actively searching for jobs that match your criteria.\n"
                "You'll get instant notifications when perfect opportunities appear!\n\n"
                "💬 Feel free to chat with me about:\n"
                "• Job market insights\n"
                "• Career advice\n"
                "• Interview tips\n"
                "• Or just say 'jobs' to see current matches\n\n"
                "I'm here to help with your job search journey! 😊"
            )

        except Exception as e:
            logger.error(f"❌ Error confirming preferences: {e}")
            return "✅ Preferences confirmed! I'm now searching for jobs for you."

    def _handle_job_search(
        self, user_prefs: dict, user_id: int, phone_number: str
    ) -> str:
        """Handle job search requests"""
        # Refresh user preferences to get latest confirmation status
        fresh_prefs = self.pref_manager.get_preferences(user_id)

        if not fresh_prefs or not fresh_prefs.get("preferences_confirmed"):
            return "Please set up your job preferences first by typing 'settings'."

        # Get user's name
        cursor = self.db.connection.cursor()
        cursor.execute("SELECT name FROM users WHERE id = %s", (user_id,))
        user_name_result = cursor.fetchone()
        user_name = (
            user_name_result[0].split()[0]
            if user_name_result and user_name_result[0]
            else None
        )

        # Generate realistic job listings using fresh preferences
        job_messages = self.job_service.generate_realistic_job_listings(
            fresh_prefs, user_name, user_id
        )

        # Send all job messages sequentially
        if job_messages:
            # Send first message (introduction)
            first_message = job_messages[0]

            # Send remaining messages (individual jobs) with small delays AFTER the first message
            if len(job_messages) > 1:
                import time
                import threading

                def send_delayed_messages():
                    time.sleep(2)  # Wait for first message to be sent
                    for message in job_messages[1:]:
                        time.sleep(1)  # Small delay between messages
                        self.whatsapp_service.send_message(phone_number, message)

                # Send additional messages in background thread
                thread = threading.Thread(target=send_delayed_messages)
                thread.daemon = True
                thread.start()

            return first_message
        else:
            return "No jobs available at the moment."

    def _handle_normal_conversation(
        self, user_message: str, user_prefs: dict, user_id: int
    ) -> str:
        """Handle normal conversation using AI agent"""
        # Get user's name
        cursor = self.db.connection.cursor()
        cursor.execute("SELECT name FROM users WHERE id = %s", (user_id,))
        user_name_result = cursor.fetchone()
        user_name = (
            user_name_result[0] if user_name_result and user_name_result[0] else None
        )

        # Get conversation history
        conversation_history = self.db.get_conversation_history(user_id, limit=10)

        # Generate AI response
        return self.conversation_agent.generate_response(
            user_message, user_prefs or {}, user_name, conversation_history
        )
