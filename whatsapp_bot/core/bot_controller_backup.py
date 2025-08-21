#!/usr/bin/env python3
"""
Bot Controller - Main business logic controller
Orchestrates all components and handles conversation flow
"""

import logging
import re
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
        """Enhanced message handling with menu navigation"""
        try:
            user_id = self.db.get_or_create_user(phone_number)
            user_message_lower = user_message.lower().strip()

            # Show menu for menu commands
            if user_message_lower in [
                "menu",
                "main",
                "start",
                "/start",
                "/menu",
                "hi",
                "hello",
            ]:
                return self._show_main_menu(phone_number)

            # Quick commands
            if user_message_lower in ["help", "/help"]:
                return self._show_help_info()

            if user_message_lower in ["jobs", "view jobs", "find jobs"]:
                user_prefs = self.pref_manager.get_preferences(user_id)
                if not user_prefs or not user_prefs.get("preferences_confirmed"):
                    return "Please set your preferences first. Type 'menu' and select 'Change Preferences'."
                return self._handle_job_search(user_prefs, user_id, phone_number)

            # Handle settings command
            if user_message_lower in ["settings", "preferences", "setup"]:
                return self._start_preference_setup(phone_number, user_id)

            # Check if it's a preference form submission
            if self._is_preference_form(user_message):
                return self._process_preference_form(user_message, phone_number)

            # Handle confirmation responses
            if user_message_lower in ["yes", "confirm", "correct", "ok"]:
                user_prefs = self.pref_manager.get_preferences(user_id)
                if user_prefs and not user_prefs.get("preferences_confirmed"):
                    return self._confirm_user_preferences(user_id)

            # Check if user is in guided setup mode
            if self._is_in_guided_setup(user_id):
                return self._handle_guided_setup_step(user_message, user_id)

            # Check if user is updating a specific preference field
            if self._is_updating_preference_field(user_id):
                return self._handle_preference_field_update(
                    user_message, phone_number, user_id
                )

            # Handle normal conversation using AI agent
            user_prefs = self.pref_manager.get_preferences(user_id)
            return self._handle_normal_conversation(user_message, user_prefs, user_id)

        except Exception as e:
            logger.error(f"Error handling message: {e}")
            return "Something went wrong. Type 'menu' for options."

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
        """Show interactive preference form with menu options"""
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
            # Try to get name from users table first, then preferences, then default
            current_name = "Not set"
            if user_name_result and user_name_result[0]:
                current_name = user_name_result[0]
            elif current_prefs and current_prefs.get("full_name"):
                current_name = current_prefs.get("full_name")
            else:
                current_name = "Not set"

            job_title = (
                ", ".join(current_prefs.get("job_roles", []))
                if current_prefs and current_prefs.get("job_roles")
                else "Not set"
            )
            location = (
                ", ".join(current_prefs.get("preferred_locations", []))
                if current_prefs and current_prefs.get("preferred_locations")
                else "Not set"
            )
            salary = (
                f"₦{current_prefs.get('salary_min'):,}"
                if current_prefs and current_prefs.get("salary_min")
                else "Not set"
            )
            experience = (
                f"{current_prefs.get('years_of_experience')} years"
                if current_prefs
                and current_prefs.get("years_of_experience") is not None
                else "Not set"
            )
            work_style = (
                ", ".join(current_prefs.get("work_arrangements", []))
                if current_prefs and current_prefs.get("work_arrangements")
                else "Not set"
            )

            # Create the preference display
            preference_display = (
                f"{intro}"
                "� *Your current preferences:*\n\n"
                f"*Full Name:* {current_name}\n"
                f"*Job Title:* {job_title}\n"
                f"*Location:* {location}\n"
                f"*Minimum Salary:* {salary}\n"
                f"*Experience:* {experience}\n"
                f"*Work Style:* {work_style}\n\n"
                "� *Select a field to update:*"
            )

            # Create interactive menu for field selection
            sections = [
                {
                    "title": "Update Preferences",
                    "rows": [
                        {
                            "id": "update_name",
                            "title": "👤 Full Name",
                            "description": f"Current: {current_name}",
                        },
                        {
                            "id": "update_job_title",
                            "title": "🎯 Job Title",
                            "description": f"Current: {job_title}",
                        },
                        {
                            "id": "update_location",
                            "title": "📍 Location",
                            "description": f"Current: {location}",
                        },
                        {
                            "id": "update_salary",
                            "title": "💰 Minimum Salary",
                            "description": f"Current: {salary}",
                        },
                        {
                            "id": "update_experience",
                            "title": "⏱️ Experience",
                            "description": f"Current: {experience}",
                        },
                        {
                            "id": "update_work_style",
                            "title": "🏢 Work Style",
                            "description": f"Current: {work_style}",
                        },
                        {
                            "id": "confirm_preferences",
                            "title": "✅ Confirm & Save",
                            "description": "Save these preferences",
                        },
                    ],
                }
            ]

            # Try interactive menu first, fallback to buttons if it fails
            success = self.whatsapp_service.send_list_menu(
                phone_number, "Update Preferences", "Choose what to update:", sections
            )

            if success:
                return "Preference menu sent!"
            else:
                # Fallback to button menu if list menu fails
                logger.warning("List menu failed, trying button menu")
                return self._show_preference_buttons(phone_number, preference_display)

        except Exception as e:
            logger.error(f"❌ Error showing preference form: {e}")
            return "I'm having trouble showing the form. Please try typing 'settings' again."

    def _show_preference_buttons(
        self, phone_number: str, preference_display: str
    ) -> str:
        """Show preference options using button menu as fallback"""
        try:
            buttons = [
                {
                    "type": "reply",
                    "reply": {"id": "update_form", "title": "📝 Update Form"},
                },
                {
                    "type": "reply",
                    "reply": {"id": "reset_prefs", "title": "🔄 Start Fresh"},
                },
            ]

            # Send the preference display first
            self.whatsapp_service.send_message(phone_number, preference_display)

            # Then send the button menu
            success = self.whatsapp_service.send_button_menu(
                phone_number, "What would you like to do?", buttons
            )

            return (
                "Preference update menu sent!"
                if success
                else "Failed to send preference menu"
            )

        except Exception as e:
            logger.error(f"❌ Error showing preference buttons: {e}")
            return self._show_traditional_preference_form(
                phone_number, first_time=False
            )

    def _show_traditional_preference_form(
        self, phone_number: str, first_time: bool = False
    ) -> str:
        """Show traditional copy-paste preference form as fallback"""
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
                f"*Full Name:* {current_name}\n"
                f"*Job Title:* {job_title}\n"
                f"*Location:* {location}\n"
                f"*Minimum Salary:* {salary}\n"
                f"*Experience:* {experience}\n"
                f"*Work Style:* {work_style}\n\n"
                "📱 *Just copy, edit and send back!*\n\n"
            )

            if not first_time:
                form += (
                    "Note: You can always change your preferences by sending `settings`"
                )

            return form

        except Exception as e:
            logger.error(f"❌ Error showing traditional preference form: {e}")
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

            # Safe array handling for confirmation
            job_roles = preferences.get("job_roles", [])
            job_roles_str = (
                ", ".join(job_roles)
                if job_roles and isinstance(job_roles, list)
                else "Not set"
            )

            locations = preferences.get("preferred_locations", [])
            locations_str = (
                ", ".join(locations)
                if locations and isinstance(locations, list)
                else "Not set"
            )

            work_arrangements = preferences.get("work_arrangements", [])
            work_style_str = (
                ", ".join(work_arrangements)
                if work_arrangements and isinstance(work_arrangements, list)
                else "Not set"
            )

            confirmation_msg = (
                f"{name_part}I've saved your job preferences:\n\n"
                f"👤 **Name:** {preferences.get('full_name', 'Not provided')}\n"
                f"🎯 **Looking for:** {job_roles_str}\n"
                f"📍 **Location:** {locations_str}\n"
                f"💰 **Salary:** ₦{(preferences.get('salary_min') or 0):,}+ {preferences.get('salary_currency') or 'NGN'}\n"
                f"⏱️ **Experience:** {preferences.get('years_of_experience', 'Not specified')} years\n"
                f"🏢 **Work Style:** {work_style_str}\n\n"
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

            # Send confirmation message with Clear All option
            confirmation_message = (
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

            # Add Clear All button option
            buttons = [
                {
                    "type": "reply",
                    "reply": {"id": "view_jobs_now", "title": "🔍 View Jobs"},
                },
                {
                    "type": "reply",
                    "reply": {"id": "clear_all_prefs", "title": "🗑️ Clear All"},
                },
                {
                    "type": "reply",
                    "reply": {"id": "main_menu", "title": "📋 Main Menu"},
                },
            ]

            # Get phone number for this user
            cursor.execute("SELECT phone_number FROM users WHERE id = %s", (user_id,))
            phone_result = cursor.fetchone()
            if phone_result:
                phone_number = phone_result[0]
                self.whatsapp_service.send_button_menu(
                    phone_number, confirmation_message, buttons
                )

            return "Preferences confirmed with options sent!"

        except Exception as e:
            logger.error(f"❌ Error confirming preferences: {e}")
            return "✅ Preferences confirmed! I'm now searching for jobs for you."

    def _is_updating_preference_field(self, user_id: int) -> bool:
        """Check if user is in the middle of updating a preference field"""
        try:
            cursor = self.db.connection.cursor()

            # First ensure the updating_field column exists
            try:
                cursor.execute(
                    "ALTER TABLE user_preferences ADD COLUMN IF NOT EXISTS updating_field VARCHAR(50)"
                )
                self.db.connection.commit()
            except Exception as e:
                logger.debug(f"Column might already exist: {e}")

            cursor.execute(
                "SELECT updating_field FROM user_preferences WHERE user_id = %s",
                (user_id,),
            )
            result = cursor.fetchone()
            return result and result[0] is not None
        except Exception as e:
            logger.error(f"Error checking updating field: {e}")
            return False

    def _handle_preference_field_update(
        self, user_message: str, phone_number: str, user_id: int
    ) -> str:
        """Handle updates to specific preference fields"""
        try:
            # Get which field is being updated
            cursor = self.db.connection.cursor()
            cursor.execute(
                "SELECT updating_field FROM user_preferences WHERE user_id = %s",
                (user_id,),
            )
            result = cursor.fetchone()

            if not result or not result[0]:
                return "No field being updated. Type 'settings' to update preferences."

            updating_field = result[0]

            # Process the update based on field type
            if updating_field == "name":
                return self._update_name_field(user_message, user_id)
            elif updating_field == "job_title":
                return self._update_job_title_field(user_message, user_id)
            elif updating_field == "location":
                return self._update_location_field(user_message, user_id)
            elif updating_field == "salary":
                return self._update_salary_field(user_message, user_id)
            elif updating_field == "experience":
                return self._update_experience_field(user_message, user_id)
            elif updating_field == "work_style":
                return self._update_work_style_field(user_message, user_id)
            else:
                return "Unknown field being updated. Type 'settings' to start over."

        except Exception as e:
            logger.error(f"Error handling field update: {e}")
            return "Something went wrong. Type 'settings' to try again."

    def _handle_preference_confirmation(self, user_id: int) -> str:
        """Handle preference confirmation from the menu"""
        try:
            current_prefs = self.pref_manager.get_preferences(user_id)
            if not current_prefs:
                return "No preferences found. Please set them up first."

            return self._show_preference_confirmation(user_id, current_prefs)

        except Exception as e:
            logger.error(f"Error handling preference confirmation: {e}")
            return "Something went wrong. Type 'settings' to try again."

    def _handle_clear_all_preferences(self, user_id: int, phone_number: str) -> str:
        """Handle clearing all user preferences with confirmation"""
        try:
            # Send confirmation message
            buttons = [
                {
                    "type": "reply",
                    "reply": {"id": "confirm_clear_all", "title": "✅ Yes, Clear All"},
                },
                {
                    "type": "reply",
                    "reply": {"id": "cancel_clear", "title": "❌ Cancel"},
                },
            ]

            confirmation_message = (
                "🗑️ *Clear All Preferences*\n\n"
                "⚠️ This will permanently delete all your job preferences:\n"
                "• Job titles\n"
                "• Locations\n"
                "• Salary expectations\n"
                "• Experience level\n"
                "• Work arrangements\n\n"
                "Are you sure you want to continue?"
            )

            success = self.whatsapp_service.send_button_menu(
                phone_number, confirmation_message, buttons
            )

            return (
                "Clear confirmation sent!" if success else "Failed to send confirmation"
            )

        except Exception as e:
            logger.error(f"Error handling clear all preferences: {e}")
            return "Something went wrong. Type 'menu' to try again."

    def _execute_clear_all_preferences(self, user_id: int, phone_number: str) -> str:
        """Actually clear all user preferences"""
        try:
            # Clear preferences from database
            success = self.pref_manager.clear_preferences(user_id)

            if success:
                # Also clear any updating states
                cursor = self.db.connection.cursor()
                cursor.execute(
                    """
                    UPDATE user_preferences
                    SET updating_field = NULL, guided_setup_step = NULL
                    WHERE user_id = %s
                    """,
                    (user_id,),
                )
                self.db.connection.commit()

                return (
                    "🗑️ *All Preferences Cleared*\n\n"
                    "✅ Your job preferences have been completely removed.\n\n"
                    "To start fresh, type 'settings' to set up new preferences.\n\n"
                    "Type 'menu' to see all available options."
                )
            else:
                return "❌ Failed to clear preferences. Please try again."

        except Exception as e:
            logger.error(f"Error executing clear all preferences: {e}")
            return (
                "Something went wrong clearing preferences. Type 'menu' to try again."
            )

    def _set_guided_setup_state(self, user_id: int, step: str) -> bool:
        """Set guided setup state for user"""
        try:
            cursor = self.db.connection.cursor()

            # First ensure the guided_setup_step column exists
            try:
                cursor.execute(
                    "ALTER TABLE user_preferences ADD COLUMN IF NOT EXISTS guided_setup_step VARCHAR(50)"
                )
                self.db.connection.commit()
            except Exception as e:
                logger.debug(f"Column might already exist: {e}")

            cursor.execute(
                """
                INSERT INTO user_preferences (user_id, guided_setup_step)
                VALUES (%s, %s)
                ON CONFLICT (user_id)
                DO UPDATE SET guided_setup_step = EXCLUDED.guided_setup_step
                """,
                (user_id, step),
            )
            self.db.connection.commit()
            return True
        except Exception as e:
            logger.error(f"Error setting guided setup state: {e}")
            return False

    def _is_in_guided_setup(self, user_id: int) -> bool:
        """Check if user is in guided setup mode"""
        try:
            cursor = self.db.connection.cursor()
            cursor.execute(
                "SELECT guided_setup_step FROM user_preferences WHERE user_id = %s",
                (user_id,),
            )
            result = cursor.fetchone()
            return result and result[0] is not None
        except Exception as e:
            logger.error(f"Error checking guided setup: {e}")
            return False

    def _handle_guided_setup_step(self, user_message: str, user_id: int) -> str:
        """Handle guided setup conversation flow"""
        try:
            cursor = self.db.connection.cursor()
            cursor.execute(
                "SELECT guided_setup_step FROM user_preferences WHERE user_id = %s",
                (user_id,),
            )
            result = cursor.fetchone()

            if not result or not result[0]:
                return "Setup session expired. Type 'settings' to start again."

            current_step = result[0]

            if current_step == "job_title":
                # Save job title and move to next step
                job_titles = [title.strip() for title in user_message.split(",")]
                preferences = {"job_roles": job_titles}
                self.pref_manager.save_preferences(user_id, preferences)

                # Move to location step
                self._set_guided_setup_state(user_id, "location")
                return f"✅ Great! I'll look for {', '.join(job_titles)} roles.\n\n📍 Where would you like to work? (e.g., Lagos, Abuja, Remote)"

            elif current_step == "location":
                # Save location and move to salary step
                locations = [loc.strip() for loc in user_message.split(",")]
                preferences = {"preferred_locations": locations}
                self.pref_manager.save_preferences(user_id, preferences)

                self._set_guided_setup_state(user_id, "salary")
                return f"✅ Perfect! I'll search in {', '.join(locations)}.\n\n💰 What's your minimum salary expectation? (e.g., ₦500,000)"

            elif current_step == "salary":
                # Save salary and move to experience step
                salary_match = re.search(
                    r"[\d,]+", user_message.replace("₦", "").replace(",", "")
                )
                if salary_match:
                    salary_amount = int(salary_match.group().replace(",", ""))
                    preferences = {
                        "salary_min": salary_amount,
                        "salary_currency": "NGN",
                    }
                    self.pref_manager.save_preferences(user_id, preferences)

                    self._set_guided_setup_state(user_id, "experience")
                    return f"✅ Got it! Minimum ₦{salary_amount:,}.\n\n⏱️ How many years of experience do you have? (e.g., 3 years or Entry level)"
                else:
                    return (
                        "Please enter a valid salary amount (e.g., ₦500,000 or 500000)"
                    )

            elif current_step == "experience":
                # Save experience and move to work style step
                message_lower = user_message.lower()
                if "entry" in message_lower or "fresh" in message_lower:
                    years = 0
                else:
                    years_match = re.search(r"(\d+)", user_message)
                    years = int(years_match.group(1)) if years_match else 1

                preferences = {"years_of_experience": years}
                self.pref_manager.save_preferences(user_id, preferences)

                self._set_guided_setup_state(user_id, "work_style")
                experience_text = "Entry level" if years == 0 else f"{years} years"
                return f"✅ {experience_text} experience noted.\n\n🏢 What's your preferred work arrangement? (e.g., Remote, Onsite, Hybrid)"

            elif current_step == "work_style":
                # Save work style and finish setup
                work_styles = [
                    style.strip().title() for style in user_message.split(",")
                ]
                preferences = {
                    "work_arrangements": work_styles,
                    "preferences_confirmed": True,
                }
                self.pref_manager.save_preferences(user_id, preferences)

                # Clear guided setup state
                cursor.execute(
                    "UPDATE user_preferences SET guided_setup_step = NULL WHERE user_id = %s",
                    (user_id,),
                )
                self.db.connection.commit()

                # Start window for job monitoring
                self.window_manager.start_new_window(user_id)

                return f"🎉 Perfect! Setup complete!\n\n✅ Your preferences:\n• Job: {', '.join(work_styles)}\n• Work style: {', '.join(work_styles)}\n\nI'm now actively searching for jobs that match your criteria. You'll get instant notifications when perfect opportunities appear!\n\nType 'jobs' to see current matches or 'menu' for more options."

            else:
                return "Unknown setup step. Type 'settings' to start over."

        except Exception as e:
            logger.error(f"Error in guided setup: {e}")
            return "Something went wrong. Type 'settings' to start over."

    def _set_updating_field(self, user_id: int, field_name: str) -> bool:
        """Set which field the user is currently updating"""
        try:
            cursor = self.db.connection.cursor()

            # First ensure the updating_field column exists
            try:
                cursor.execute(
                    "ALTER TABLE user_preferences ADD COLUMN IF NOT EXISTS updating_field VARCHAR(50)"
                )
                self.db.connection.commit()
            except Exception as e:
                logger.debug(f"Column might already exist: {e}")

            # Now set the updating field
            cursor.execute(
                """
                INSERT INTO user_preferences (user_id, updating_field)
                VALUES (%s, %s)
                ON CONFLICT (user_id)
                DO UPDATE SET updating_field = EXCLUDED.updating_field
                """,
                (user_id, field_name),
            )
            self.db.connection.commit()
            return True
        except Exception as e:
            logger.error(f"Error setting updating field: {e}")
            return False

    def _clear_updating_field(self, user_id: int) -> bool:
        """Clear the updating field after update is complete"""
        try:
            cursor = self.db.connection.cursor()
            cursor.execute(
                "UPDATE user_preferences SET updating_field = NULL WHERE user_id = %s",
                (user_id,),
            )
            self.db.connection.commit()
            return True
        except Exception as e:
            logger.error(f"Error clearing updating field: {e}")
            return False

    def _update_name_field(self, user_message: str, user_id: int) -> str:
        """Update the user's name"""
        try:
            name = user_message.strip()
            if len(name) < 2:
                return "Please enter a valid name (at least 2 characters)."

            # Update in users table
            cursor = self.db.connection.cursor()
            cursor.execute("UPDATE users SET name = %s WHERE id = %s", (name, user_id))

            # Update in preferences
            preferences = {"full_name": name}
            self.pref_manager.save_preferences(user_id, preferences)

            self._clear_updating_field(user_id)
            self.db.connection.commit()

            return f"✅ Name updated to: {name}\n\nType 'settings' to update more fields or 'menu' for main menu."

        except Exception as e:
            logger.error(f"Error updating name: {e}")
            return "Failed to update name. Please try again."

    def _update_job_title_field(self, user_message: str, user_id: int) -> str:
        """Update the user's job title preferences"""
        try:
            # Parse job titles from message
            job_titles = [title.strip() for title in user_message.split(",")]
            job_titles = [title for title in job_titles if title]  # Remove empty

            if not job_titles:
                return "Please enter at least one job title."

            preferences = {"job_roles": job_titles}
            success = self.pref_manager.save_preferences(user_id, preferences)

            if success:
                self._clear_updating_field(user_id)
                return f"✅ Job titles updated to: {', '.join(job_titles)}\n\nType 'settings' to update more fields or 'menu' for main menu."
            else:
                return "Failed to update job titles. Please try again."

        except Exception as e:
            logger.error(f"Error updating job titles: {e}")
            return "Failed to update job titles. Please try again."

    def _update_location_field(self, user_message: str, user_id: int) -> str:
        """Update the user's location preferences"""
        try:
            locations = [loc.strip() for loc in user_message.split(",")]
            locations = [loc for loc in locations if loc]  # Remove empty

            if not locations:
                return "Please enter at least one location."

            preferences = {"preferred_locations": locations}
            success = self.pref_manager.save_preferences(user_id, preferences)

            if success:
                self._clear_updating_field(user_id)
                return f"✅ Locations updated to: {', '.join(locations)}\n\nType 'settings' to update more fields or 'menu' for main menu."
            else:
                return "Failed to update locations. Please try again."

        except Exception as e:
            logger.error(f"Error updating locations: {e}")
            return "Failed to update locations. Please try again."

    def _update_salary_field(self, user_message: str, user_id: int) -> str:
        """Update the user's salary preferences"""
        try:
            # Extract salary amount from message
            import re

            salary_match = re.search(
                r"[\d,]+", user_message.replace("₦", "").replace(",", "")
            )

            if not salary_match:
                return "Please enter a valid salary amount (e.g., ₦500,000 or 500000)."

            salary_amount = int(salary_match.group().replace(",", ""))

            if salary_amount < 50000:
                return "Please enter a realistic salary amount (minimum ₦50,000)."

            preferences = {"salary_min": salary_amount, "salary_currency": "NGN"}
            success = self.pref_manager.save_preferences(user_id, preferences)

            if success:
                self._clear_updating_field(user_id)
                return f"✅ Minimum salary updated to: ₦{salary_amount:,}\n\nType 'settings' to update more fields or 'menu' for main menu."
            else:
                return "Failed to update salary. Please try again."

        except Exception as e:
            logger.error(f"Error updating salary: {e}")
            return (
                "Failed to update salary. Please enter a valid amount (e.g., ₦500,000)."
            )

    def _update_experience_field(self, user_message: str, user_id: int) -> str:
        """Update the user's experience level"""
        try:
            # Extract years from message
            import re

            message_lower = user_message.lower()
            if (
                "entry" in message_lower
                or "fresh" in message_lower
                or "graduate" in message_lower
            ):
                years = 0
            else:
                years_match = re.search(r"(\d+)", user_message)
                if years_match:
                    years = int(years_match.group(1))
                else:
                    return "Please enter your experience in years (e.g., '3 years' or 'Entry level')."

            if years > 50:
                return "Please enter a realistic number of years (0-50)."

            preferences = {"years_of_experience": years}
            success = self.pref_manager.save_preferences(user_id, preferences)

            if success:
                self._clear_updating_field(user_id)
                experience_text = "Entry level" if years == 0 else f"{years} years"
                return f"✅ Experience updated to: {experience_text}\n\nType 'settings' to update more fields or 'menu' for main menu."
            else:
                return "Failed to update experience. Please try again."

        except Exception as e:
            logger.error(f"Error updating experience: {e}")
            return "Failed to update experience. Please try again."

    def _update_work_style_field(self, user_message: str, user_id: int) -> str:
        """Update the user's work style preferences"""
        try:
            work_styles = [style.strip() for style in user_message.split(",")]
            work_styles = [style for style in work_styles if style]  # Remove empty

            if not work_styles:
                return "Please enter at least one work style (Remote, Onsite, Hybrid)."

            # Validate work styles
            valid_styles = [
                "remote",
                "onsite",
                "hybrid",
                "on-site",
                "work from home",
                "wfh",
            ]
            normalized_styles = []

            for style in work_styles:
                style_lower = style.lower().strip()
                if any(valid in style_lower for valid in valid_styles):
                    if (
                        "remote" in style_lower
                        or "wfh" in style_lower
                        or "work from home" in style_lower
                    ):
                        normalized_styles.append("Remote")
                    elif "onsite" in style_lower or "on-site" in style_lower:
                        normalized_styles.append("Onsite")
                    elif "hybrid" in style_lower:
                        normalized_styles.append("Hybrid")
                else:
                    normalized_styles.append(style.title())

            preferences = {"work_arrangements": normalized_styles}
            success = self.pref_manager.save_preferences(user_id, preferences)

            if success:
                self._clear_updating_field(user_id)
                return f"✅ Work style updated to: {', '.join(normalized_styles)}\n\nType 'settings' to update more fields or 'menu' for main menu."
            else:
                return "Failed to update work style. Please try again."

        except Exception as e:
            logger.error(f"Error updating work style: {e}")
            return "Failed to update work style. Please try again."

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

    def _show_main_menu(self, phone_number: str) -> str:
        """Show main menu with core features"""
        sections = [
            {
                "title": "Aremu Job Bot",
                "rows": [
                    {
                        "id": "change_preferences",
                        "title": "Change Preferences",
                        "description": "Update your job search criteria",
                    },
                    {
                        "id": "view_jobs",
                        "title": "View Jobs",
                        "description": "See available job opportunities",
                    },
                    {
                        "id": "cv_analyzer",
                        "title": "CV Analyzer",
                        "description": "Get feedback on your resume",
                    },
                    {
                        "id": "help",
                        "title": "Help",
                        "description": "Get assistance and support",
                    },
                ],
            }
        ]

        success = self.whatsapp_service.send_list_menu(
            phone_number, "🎯 Aremu Job Bot", "What would you like to do?", sections
        )

        return "Menu sent!" if success else "Failed to send menu"

    def handle_interactive_message(
        self, phone_number: str, interactive_data: dict
    ) -> str:
        """Handle responses from interactive messages"""
        try:
            user_id = self.db.get_or_create_user(phone_number)

            # Handle list replies
            if interactive_data.get("type") == "list_reply":
                selection_id = interactive_data["list_reply"]["id"]
                return self._handle_list_selection(selection_id, phone_number, user_id)

            # Handle button replies
            elif interactive_data.get("type") == "button_reply":
                button_id = interactive_data["button_reply"]["id"]
                return self._handle_button_selection(button_id, phone_number, user_id)

        except Exception as e:
            logger.error(f"Error handling interactive message: {e}")
            return "Something went wrong. Please try again or type 'menu' for options."

    def _handle_list_selection(
        self, selection_id: str, phone_number: str, user_id: int
    ) -> str:
        """Handle main menu selections and preference field updates"""
        try:
            # Main menu selections
            if selection_id == "change_preferences":
                return self._start_preference_setup(phone_number, user_id)

            elif selection_id == "view_jobs":
                user_prefs = self.pref_manager.get_preferences(user_id)
                if not user_prefs or not user_prefs.get("preferences_confirmed"):
                    return "Please set your preferences first. Type 'menu' and select 'Change Preferences'."
                return self._handle_job_search(user_prefs, user_id, phone_number)

            elif selection_id == "cv_analyzer":
                return self._start_cv_analysis(phone_number)

            elif selection_id == "help":
                return self._show_help_info()

            # Preference field update selections
            elif selection_id == "update_name":
                self._set_updating_field(user_id, "name")
                return "👤 *Update Full Name*\n\nPlease type your full name:\n\nExample: Ahmed Ibrahim"

            elif selection_id == "update_job_title":
                self._set_updating_field(user_id, "job_title")
                return "🎯 *Update Job Title*\n\nWhat type of job are you looking for?\n\nExamples:\n• Software Developer\n• Marketing Manager\n• Data Analyst\n• Frontend Developer, Backend Developer"

            elif selection_id == "update_location":
                self._set_updating_field(user_id, "location")
                return "📍 *Update Location*\n\nWhere would you like to work?\n\nExamples:\n• Lagos\n• Abuja\n• Remote\n• Lagos, Abuja, Remote"

            elif selection_id == "update_salary":
                self._set_updating_field(user_id, "salary")
                return "💰 *Update Minimum Salary*\n\nWhat's your minimum salary expectation?\n\nExamples:\n• ₦500,000\n• ₦1,200,000\n• ₦800,000"

            elif selection_id == "update_experience":
                self._set_updating_field(user_id, "experience")
                return "⏱️ *Update Experience*\n\nHow many years of experience do you have?\n\nExamples:\n• 2 years\n• 5 years\n• Entry level"

            elif selection_id == "update_work_style":
                self._set_updating_field(user_id, "work_style")
                return "🏢 *Update Work Style*\n\nWhat's your preferred work arrangement?\n\nExamples:\n• Remote\n• Onsite\n• Hybrid\n• Remote, Hybrid"

            elif selection_id == "confirm_preferences":
                return self._handle_preference_confirmation(user_id)

            else:
                return "Invalid selection. Type 'menu' to see options again."

        except Exception as e:
            logger.error(f"Error handling list selection {selection_id}: {e}")
            return "Something went wrong. Type 'menu' to try again."

    def _handle_button_selection(
        self, button_id: str, phone_number: str, user_id: int
    ) -> str:
        """Handle button selections"""
        try:
            # Handle preference update menu buttons
            if button_id == "update_form":
                return self._show_preference_form(phone_number, first_time=False)

            elif button_id == "show_traditional_form":
                return self._show_traditional_preference_form(
                    phone_number, first_time=False
                )

            elif button_id == "reset_prefs":
                # Clear existing preferences
                success = self.pref_manager.clear_preferences(user_id)
                if success:
                    return self._welcome_new_user_setup(phone_number, user_id)
                else:
                    return "Failed to reset preferences. Please try again."

            # Handle new user setup buttons
            elif button_id == "guided_setup":
                # Set guided setup state
                self._set_guided_setup_state(user_id, "job_title")
                return "🎯 *Guided Setup*\n\nI'll ask you a few questions to set up your perfect job search.\n\nLet's start: What type of job are you looking for? (e.g., Software Developer, Marketing Manager, etc.)"

            elif button_id == "form_setup":
                return self._show_traditional_preference_form(
                    phone_number, first_time=True
                )

            elif button_id == "help_setup":
                return self._show_help_info()

            # Handle post-confirmation buttons
            elif button_id == "view_jobs_now":
                user_prefs = self.pref_manager.get_preferences(user_id)
                if user_prefs and user_prefs.get("preferences_confirmed"):
                    return self._handle_job_search(user_prefs, user_id, phone_number)
                else:
                    return "Please set up your preferences first. Type 'settings'."

            elif button_id == "clear_all_prefs":
                return self._handle_clear_all_preferences(user_id, phone_number)

            elif button_id == "main_menu":
                return self._show_main_menu(phone_number)

            # Handle clear all confirmation buttons
            elif button_id == "confirm_clear_all":
                return self._execute_clear_all_preferences(user_id, phone_number)

            elif button_id == "cancel_clear":
                return "❌ Clear cancelled. Your preferences are safe!\n\nType 'menu' for options."

            # Handle incomplete setup buttons
            elif button_id == "continue_setup":
                return self._show_preference_form(phone_number, first_time=False)

            elif button_id == "start_fresh":
                success = self.pref_manager.clear_preferences(user_id)
                if success:
                    return self._welcome_new_user_setup(phone_number, user_id)
                else:
                    return "Failed to reset. Please try again."

            else:
                return "Invalid selection. Type 'menu' to see options again."

        except Exception as e:
            logger.error(f"Error handling button selection {button_id}: {e}")
            return "Something went wrong. Type 'menu' to try again."

    def _start_preference_setup(self, phone_number: str, user_id: int) -> str:
        """Always show current preferences first, then options"""
        existing_prefs = self.pref_manager.get_preferences(user_id)

        # Always show current preferences first (this is what user wants)
        if existing_prefs:
            # Show current preferences regardless of confirmation status
            return self._show_preference_update_menu(
                phone_number, user_id, existing_prefs
            )
        else:
            # Brand new user with no preferences at all
            return self._welcome_new_user_setup(phone_number, user_id)

    def _show_preference_update_menu(
        self, phone_number: str, user_id: int, existing_prefs: dict
    ) -> str:
        """Show update menu for users with existing confirmed preferences"""
        try:
            # Get user's name for personalization
            cursor = self.db.connection.cursor()
            cursor.execute("SELECT name FROM users WHERE id = %s", (user_id,))
            user_name_result = cursor.fetchone()
            user_name = (
                user_name_result[0].split()[0]
                if user_name_result and user_name_result[0]
                else "there"
            )

            # Create current preferences summary with safe array handling
            job_roles = existing_prefs.get("job_roles", [])
            job_roles_str = (
                ", ".join(job_roles)
                if job_roles and isinstance(job_roles, list)
                else "Not set"
            )

            locations = existing_prefs.get("preferred_locations", [])
            locations_str = (
                ", ".join(locations)
                if locations and isinstance(locations, list)
                else "Not set"
            )

            work_arrangements = existing_prefs.get("work_arrangements", [])
            work_style_str = (
                ", ".join(work_arrangements)
                if work_arrangements and isinstance(work_arrangements, list)
                else "Not set"
            )

            # Use name from users table if available, otherwise from preferences
            display_name = "Not set"
            if user_name_result and user_name_result[0]:
                display_name = user_name_result[0]
            elif existing_prefs and existing_prefs.get("full_name"):
                display_name = existing_prefs.get("full_name")

            current_summary = (
                f"👤 **Name:** {display_name}\n"
                f"🎯 **Looking for:** {job_roles_str}\n"
                f"📍 **Location:** {locations_str}\n"
                f"💰 **Salary:** ₦{(existing_prefs.get('salary_min') or 0):,}+ {existing_prefs.get('salary_currency') or 'NGN'}\n"
                f"⏱️ **Experience:** {existing_prefs.get('years_of_experience', 'Not specified')} years\n"
                f"🏢 **Work Style:** {work_style_str}"
            )

            buttons = [
                {
                    "type": "reply",
                    "reply": {"id": "update_form", "title": "📝 Update Form"},
                },
                {
                    "type": "reply",
                    "reply": {"id": "reset_prefs", "title": "🔄 Start Fresh"},
                },
            ]

            message = (
                f"⚙️ *Hi {user_name}! Update Your Preferences*\n\n"
                f"Your current job preferences:\n\n{current_summary}\n\n"
                "What would you like to do?"
            )

            self.whatsapp_service.send_button_menu(phone_number, message, buttons)
            return "Preference update menu sent!"

        except Exception as e:
            logger.error(f"❌ Error showing preference update menu: {e}")
            return self._show_preference_form(phone_number, first_time=False)

    def _welcome_new_user_setup(self, phone_number: str, user_id: int) -> str:
        """Welcome flow for brand new users"""
        buttons = [
            {
                "type": "reply",
                "reply": {"id": "guided_setup", "title": "🎯 Guided Setup"},
            },
            {
                "type": "reply",
                "reply": {"id": "form_setup", "title": "📋 Copy Paste Form"},
            },
            {"type": "reply", "reply": {"id": "help_setup", "title": "❓ Need Help"}},
        ]

        self.whatsapp_service.send_button_menu(
            phone_number,
            "👋 *Welcome to Aremu Job Bot!*\n\nLet's set up your job preferences so I can find perfect opportunities for you.\n\nHow would you like to start?",
            buttons,
        )

        return "Welcome setup sent!"

    def _resume_incomplete_setup(
        self, phone_number: str, user_id: int, prefs: dict
    ) -> str:
        """Resume incomplete preference setup"""
        missing_items = []
        if not prefs.get("job_roles"):
            missing_items.append("Job Type")
        if not prefs.get("preferred_locations"):
            missing_items.append("Location")
        if not prefs.get("salary_min"):
            missing_items.append("Salary")

        buttons = [
            {
                "type": "reply",
                "reply": {"id": "continue_setup", "title": "▶️ Continue Setup"},
            },
            {"type": "reply", "reply": {"id": "start_fresh", "title": "🔄 Start Over"}},
            {
                "type": "reply",
                "reply": {"id": "view_current", "title": "� View Current"},
            },
        ]

        missing_text = ", ".join(missing_items)

        self.whatsapp_service.send_button_menu(
            phone_number,
            f"🔄 *Resume Setup*\n\nYou started setting up preferences but didn't finish.\n\nStill missing: {missing_text}\n\nWhat would you like to do?",
            buttons,
        )

        return "Resume setup sent!"

    def _start_cv_analysis(self, phone_number: str) -> str:
        """Start CV analysis flow"""
        return (
            "📋 *CV Analyzer*\n\n"
            "Send me your CV/Resume as:\n"
            "• PDF document 📄\n"
            "• Word document 📝\n"
            "• Or paste the text directly ✍️\n\n"
            "I'll analyze it and give you feedback to improve your chances with Nigerian employers! 🇳🇬"
        )

    def _show_help_info(self) -> str:
        """Show help information"""
        return (
            "❓ *Help & Support*\n\n"
            "Here's how to use Aremu Job Bot:\n\n"
            "🎯 *Change Preferences* - Set your job criteria\n"
            "👀 *View Jobs* - Get matching job opportunities\n"
            "📋 *CV Analyzer* - Get resume feedback\n\n"
            "💬 *Commands:*\n"
            "• Type 'menu' - Show main menu\n"
            "• Type 'help' - Show this help\n"
            "• Type 'jobs' - Quick job search\n\n"
            "Need human help? Contact support at support@aremu.com"
        )
