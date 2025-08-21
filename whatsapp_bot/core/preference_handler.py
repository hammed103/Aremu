#!/usr/bin/env python3
"""
Preference Handler - Manages all preference-related functionality
Handles preference forms, updates, confirmations, and field-specific operations
"""

import logging
import re
from typing import Dict, Optional

logger = logging.getLogger(__name__)


class PreferenceHandler:
    """Handles all preference-related operations"""

    def __init__(
        self, db, pref_manager, preference_parser, whatsapp_service, window_manager
    ):
        """Initialize preference handler with required dependencies"""
        self.db = db
        self.pref_manager = pref_manager
        self.preference_parser = preference_parser
        self.whatsapp_service = whatsapp_service
        self.window_manager = window_manager

    def show_preference_form(self, phone_number: str, first_time: bool = False) -> str:
        """Show interactive preference form with menu options"""
        try:
            user_id = self.db.get_or_create_user(phone_number)
            current_prefs = self.pref_manager.get_preferences(user_id)

            # Get user's name for personalization
            cursor = self.db.connection.cursor()
            cursor.execute("SELECT name FROM users WHERE id = %s", (user_id,))
            user_name_result = cursor.fetchone()
            user_name = (
                user_name_result[0].split()[0]
                if user_name_result and user_name_result[0]
                else "there"
            )

            # Create preference display
            if current_prefs:
                # Safe array handling for existing preferences
                job_roles = current_prefs.get("job_roles", [])
                job_roles_str = (
                    ", ".join(job_roles)
                    if job_roles and isinstance(job_roles, list)
                    else "Not set"
                )

                locations = current_prefs.get("preferred_locations", [])
                locations_str = (
                    ", ".join(locations)
                    if locations and isinstance(locations, list)
                    else "Not set"
                )

                work_arrangements = current_prefs.get("work_arrangements", [])
                work_style_str = (
                    ", ".join(work_arrangements)
                    if work_arrangements and isinstance(work_arrangements, list)
                    else "❌ Not set"
                )

                # Get user name from users table
                cursor = self.db.connection.cursor()
                cursor.execute("SELECT name FROM users WHERE id = %s", (user_id,))
                user_name_result = cursor.fetchone()
                display_name = (
                    user_name_result[0]
                    if user_name_result and user_name_result[0]
                    else "❌ Not set"
                )

                preference_display = (
                    f"⚙️ *Hi {user_name}! Update Your Preferences*\n\n"
                    f"Your current job preferences:\n\n"
                    f"👤 *Name:* {display_name}\n"
                    f"🎯 *Looking for:* {job_roles_str}\n"
                    f"📍 *Location:* {locations_str}\n"
                    f"💰 *Salary:* ₦{(current_prefs.get('salary_min') or 0):,}+ {current_prefs.get('salary_currency') or 'NGN'}\n"
                    f"⏱️ *Experience:* {self._format_experience(current_prefs.get('years_of_experience'))}\n"
                    f"🏢 *Work Style:* {work_style_str}\n\n"
                    "What would you like to do?"
                )
            else:
                preference_display = (
                    f"⚙️ *Hi {user_name}! Set Your Job Preferences*\n\n"
                    "Let's set up your job search preferences to find the perfect opportunities for you!\n\n"
                    "What would you like to do?"
                )

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
                    "reply": {
                        "id": "show_traditional_form",
                        "title": "📋 Copy-Paste Form",
                    },
                },
                {
                    "type": "reply",
                    "reply": {"id": "help_setup", "title": "❓ Need Help"},
                },
            ]

            success = self.whatsapp_service.send_button_menu(
                phone_number, preference_display, buttons
            )

            return (
                "Preference menu sent!" if success else "Failed to send preference menu"
            )

        except Exception as e:
            logger.error(f"❌ Error showing preference buttons: {e}")
            return self.show_traditional_preference_form(phone_number, first_time=False)

    def show_traditional_preference_form(
        self, phone_number: str, first_time: bool = False
    ) -> str:
        """Show traditional copy-paste preference form as fallback"""
        try:
            user_id = self.db.get_or_create_user(phone_number)
            current_prefs = self.pref_manager.get_preferences(user_id)

            # Get user's name for personalization
            cursor = self.db.connection.cursor()
            cursor.execute("SELECT name FROM users WHERE id = %s", (user_id,))
            user_name_result = cursor.fetchone()
            user_name = (
                user_name_result[0].split()[0]
                if user_name_result and user_name_result[0]
                else "there"
            )

            # Show current values or defaults
            job_roles = (
                ", ".join(current_prefs.get("job_roles", []))
                if current_prefs and current_prefs.get("job_roles")
                else "Not set"
            )
            locations = (
                ", ".join(current_prefs.get("preferred_locations", []))
                if current_prefs and current_prefs.get("preferred_locations")
                else "❌ Not set"
            )
            salary = (
                f"₦{current_prefs.get('salary_min'):,}"
                if current_prefs and current_prefs.get("salary_min")
                else "❌ Not set"
            )
            experience = (
                self._format_experience(current_prefs.get("years_of_experience"))
                if current_prefs
                and current_prefs.get("years_of_experience") is not None
                else "❌ Not set"
            )
            work_style = (
                ", ".join(current_prefs.get("work_arrangements", []))
                if current_prefs and current_prefs.get("work_arrangements")
                else "❌ Not set"
            )

            # Get user name from users table for the form
            cursor = self.db.connection.cursor()
            cursor.execute("SELECT name FROM users WHERE id = %s", (user_id,))
            user_name_result = cursor.fetchone()
            form_name = (
                user_name_result[0]
                if user_name_result and user_name_result[0]
                else "Your Full Name"
            )

            form_message = (
                f"📝 *Hi {user_name}! Fill Your Job Preferences*\n\n"
                "Copy, edit and send this form back:\n\n"
                f"**Full Name:** {form_name}\n"
                f"**Job Title:** {job_roles}\n"
                f"**Location:** {locations}\n"
                f"**Minimum Salary:** {salary}\n"
                f"**Experience:** {experience}\n"
                f"**Work Style:** {work_style}\n\n"
                "📱 Just copy the form above, edit your details, and send it back!\n\n"
                "Type 'menu' to go back to main menu."
            )

            return form_message

        except Exception as e:
            logger.error(f"❌ Error showing traditional preference form: {e}")
            return "I'm having trouble showing the form. Please try typing 'settings' again."

    def is_preference_form(self, message: str) -> bool:
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

    def process_preference_form(self, message: str, phone_number: str) -> str:
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
                return self.show_preference_confirmation(user_id, preferences)
            else:
                return "❌ Failed to save preferences. Please try again."

        except Exception as e:
            logger.error(f"❌ Error processing preference form: {e}")
            return "Something went wrong. Type `settings` to try again."

    def show_preference_confirmation(self, user_id: int, preferences: dict) -> str:
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
                else "❌ Not set"
            )

            locations = preferences.get("preferred_locations", [])
            locations_str = (
                ", ".join(locations)
                if locations and isinstance(locations, list)
                else "❌ Not set"
            )

            work_arrangements = preferences.get("work_arrangements", [])
            work_style_str = (
                ", ".join(work_arrangements)
                if work_arrangements and isinstance(work_arrangements, list)
                else "❌ Not set"
            )

            confirmation_msg = (
                f"{name_part}I've saved your job preferences:\n\n"
                f"👤 **Name:** {preferences.get('full_name', 'Not provided')}\n"
                f"🎯 **Looking for:** {job_roles_str}\n"
                f"📍 **Location:** {locations_str}\n"
                f"💰 **Salary:** ₦{(preferences.get('salary_min') or 0):,}+ {preferences.get('salary_currency') or 'NGN'}\n"
                f"⏱️ **Experience:** {self._format_experience(preferences.get('years_of_experience'))}\n"
                f"🏢 **Work Style:** {work_style_str}\n\n"
                "✅ **Please confirm:** Are these details correct?\n\n"
                "Reply 'Yes' to confirm and start job search, or type 'settings' to make changes."
            )

            return confirmation_msg

        except Exception as e:
            logger.error(f"❌ Error showing confirmation: {e}")
            return "Please confirm your preferences by replying 'Yes' or type 'settings' to make changes."

    def confirm_user_preferences(self, user_id: int) -> str:
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

    def _format_experience(self, years_of_experience) -> str:
        """Format experience with proper singular/plural grammar"""
        if years_of_experience is None:
            return "❌ Not specified"

        years = int(years_of_experience)
        if years == 0:
            return "Entry level"
        elif years == 1:
            return "1 year"
        else:
            return f"{years} years"
