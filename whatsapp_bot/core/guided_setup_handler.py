#!/usr/bin/env python3
"""
Guided Setup Handler - Manages step-by-step preference setup
Handles guided conversation flow for setting up user preferences
"""

import logging
import re
from typing import Dict, Optional

logger = logging.getLogger(__name__)


class GuidedSetupHandler:
    """Handles guided step-by-step preference setup"""

    def __init__(self, db, pref_manager, window_manager):
        """Initialize guided setup handler with required dependencies"""
        self.db = db
        self.pref_manager = pref_manager
        self.window_manager = window_manager

    def set_guided_setup_state(self, user_id: int, step: str) -> bool:
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

    def is_in_guided_setup(self, user_id: int) -> bool:
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

    def handle_guided_setup_step(self, user_message: str, user_id: int) -> str:
        """Handle guided setup conversation flow"""
        try:
            cursor = self.db.connection.cursor()
            cursor.execute(
                "SELECT guided_setup_step FROM user_preferences WHERE user_id = %s",
                (user_id,),
            )
            result = cursor.fetchone()

            if not result or not result[0]:
                return "Setup session expired. Type 'menu' and select 'Change Preferences' to start again."

            current_step = result[0]

            if current_step == "name":
                return self._handle_name_step(user_message, user_id)
            elif current_step == "job_title":
                return self._handle_job_title_step(user_message, user_id)
            elif current_step == "location":
                return self._handle_location_step(user_message, user_id)
            elif current_step == "salary":
                return self._handle_salary_step(user_message, user_id)
            elif current_step == "experience":
                return self._handle_experience_step(user_message, user_id)
            elif current_step == "work_style":
                return self._handle_work_style_step(user_message, user_id)
            else:
                return "Something went wrong. Type 'settings' to start over."

        except Exception as e:
            logger.error(f"Error in guided setup: {e}")
            return "Something went wrong. Type 'settings' to start over."

    def _handle_name_step(self, user_message: str, user_id: int) -> str:
        """Handle name step in guided setup"""
        # Save name to users table and move to job title step
        name = user_message.strip()
        if not name or len(name) < 2:
            return "Please enter a valid name (at least 2 characters)."

        # Save name to users table
        cursor = self.db.connection.cursor()
        cursor.execute(
            "UPDATE users SET name = %s WHERE id = %s",
            (name, user_id),
        )
        self.db.connection.commit()

        # Move to job title step
        self.set_guided_setup_state(user_id, "job_title")
        return f"✅ Nice to meet you, {name.split()[0]}!\n\n🎯 What type of job are you looking for? (e.g., Software Developer, Marketing Manager, etc.)"

    def _handle_job_title_step(self, user_message: str, user_id: int) -> str:
        """Handle job title step in guided setup"""
        # Save job title and move to next step
        job_titles = [title.strip() for title in user_message.split(",")]
        preferences = {"job_roles": job_titles}
        self.pref_manager.save_preferences(user_id, preferences)

        # Move to location step
        self.set_guided_setup_state(user_id, "location")
        return f"✅ Great! I'll look for {', '.join(job_titles)} roles.\n\n📍 Where would you like to work? (e.g., Lagos, Abuja, Remote)"

    def _handle_location_step(self, user_message: str, user_id: int) -> str:
        """Handle location step in guided setup"""
        # Save location and move to salary step - use same field name as update form
        locations = [loc.strip() for loc in user_message.split(",")]
        preferences = {"location": locations}
        self.pref_manager.save_preferences(user_id, preferences)

        self.set_guided_setup_state(user_id, "salary")
        return f"✅ Perfect! I'll search in {', '.join(locations)}.\n\n💰 What's your minimum salary expectation? (e.g., ₦500,000)"

    def _handle_salary_step(self, user_message: str, user_id: int) -> str:
        """Handle salary step in guided setup"""
        # Save salary and move to experience step
        salary_match = re.search(
            r"[\d,]+", user_message.replace("₦", "").replace(",", "")
        )
        if salary_match:
            salary_amount = int(salary_match.group().replace(",", ""))
            preferences = {"salary_min": salary_amount, "salary_currency": "NGN"}
            self.pref_manager.save_preferences(user_id, preferences)

            self.set_guided_setup_state(user_id, "experience")
            return f"✅ Got it! Minimum ₦{salary_amount:,}.\n\n⏱️ How many years of experience do you have? (e.g., 3, 5, or 0 for entry level)"
        else:
            return "Please enter a valid salary amount (e.g., ₦500,000 or 500000)"

    def _handle_experience_step(self, user_message: str, user_id: int) -> str:
        """Handle experience step in guided setup - accepts only years as numbers"""
        # Save experience and move to work style step - only accept numbers
        years_match = re.search(r"(\d+)", user_message)
        if years_match:
            years = int(years_match.group(1))
            if years > 50:
                return "Please enter a realistic number of years (0-50)."
        else:
            return "Please enter your experience as a number (e.g., '3' for 3 years, '0' for entry level)."

        preferences = {"years_of_experience": years}
        self.pref_manager.save_preferences(user_id, preferences)

        self.set_guided_setup_state(user_id, "work_style")
        experience_text = (
            "Entry level" if years == 0 else f"{years} year{'s' if years != 1 else ''}"
        )
        return (
            f"✅ {experience_text} experience noted.\n\n"
            "🏢 What's your preferred work arrangement?\n\n"
            "1️⃣ Remote\n"
            "2️⃣ Onsite\n"
            "3️⃣ Hybrid\n"
            "4️⃣ Flexible\n\n"
            "Reply with a number (1-4):"
        )

    def _handle_work_style_step(self, user_message: str, user_id: int) -> str:
        """Handle work style step in guided setup - final step"""
        # Map number choices to work arrangements - use same format as update form
        user_choice = user_message.strip()

        if user_choice == "1":
            work_arrangements = ["Remote"]
            work_style_display = "Remote"
        elif user_choice == "2":
            work_arrangements = ["Onsite"]
            work_style_display = "Onsite"
        elif user_choice == "3":
            work_arrangements = ["Hybrid"]
            work_style_display = "Hybrid"
        elif user_choice == "4":
            # Flexible means all work arrangements
            work_arrangements = ["Remote", "Onsite", "Hybrid"]
            work_style_display = "Flexible (All)"
        else:
            # Default to flexible (all arrangements) for any other input
            work_arrangements = ["Remote", "Onsite", "Hybrid"]
            work_style_display = "Flexible (All)"

        preferences = {
            "work_arrangements": work_arrangements,
            "preferences_confirmed": True,
        }
        self.pref_manager.save_preferences(user_id, preferences)

        # Clear guided setup state
        cursor = self.db.connection.cursor()
        cursor.execute(
            "UPDATE user_preferences SET guided_setup_step = NULL WHERE user_id = %s",
            (user_id,),
        )
        self.db.connection.commit()

        # Start window for job monitoring
        self.window_manager.start_new_window(user_id)

        # Get all saved preferences for display
        saved_prefs = self.pref_manager.get_preferences(user_id)

        # Get user's name
        cursor = self.db.connection.cursor()
        cursor.execute("SELECT name FROM users WHERE id = %s", (user_id,))
        user_name_result = cursor.fetchone()
        user_name = (
            user_name_result[0]
            if user_name_result and user_name_result[0]
            else "Not set"
        )

        # Format all preferences
        job_roles = saved_prefs.get("job_roles", [])
        job_roles_str = ", ".join(job_roles) if job_roles else "Not set"

        locations = saved_prefs.get("preferred_locations", [])
        locations_str = ", ".join(locations) if locations else "Not set"

        salary_min = saved_prefs.get("salary_min", 0)
        salary_currency = saved_prefs.get("salary_currency", "NGN")
        salary_str = f"₦{salary_min:,}+ {salary_currency}" if salary_min else "Not set"

        experience = saved_prefs.get("years_of_experience")
        if experience == 0:
            experience_str = "Entry level"
        elif experience:
            experience_str = f"{experience} year{'s' if experience != 1 else ''}"
        else:
            experience_str = "Not set"

        # Send completion message with reply buttons
        completion_message = (
            f"🎉 Perfect! Setup complete!\n\n"
            f"✅ Your preferences:\n"
            f"👤 Name: {user_name}\n"
            f"🎯 Job: {job_roles_str}\n"
            f"📍 Location: {locations_str}\n"
            f"💰 Salary: {salary_str}\n"
            f"⏱️ Experience: {experience_str}\n"
            f"🏢 Work style: {work_style_display}\n\n"
            "I'm now actively searching for jobs that match your criteria. "
            "You'll get instant notifications when perfect opportunities appear!"
        )

        # Send message with reply buttons
        try:
            # Get user's phone number for sending buttons
            cursor = self.db.connection.cursor()
            cursor.execute("SELECT phone_number FROM users WHERE id = %s", (user_id,))
            phone_result = cursor.fetchone()

            if phone_result and phone_result[0]:
                phone_number = phone_result[0]

                # Import WhatsApp service here to avoid circular imports
                from services.whatsapp_service import WhatsAppService
                import os

                whatsapp_token = os.getenv("WHATSAPP_ACCESS_TOKEN")
                whatsapp_phone_id = os.getenv("WHATSAPP_PHONE_NUMBER_ID")
                whatsapp_service = WhatsAppService(whatsapp_token, whatsapp_phone_id)

                # Send message with reply buttons
                success = whatsapp_service.send_interactive_buttons(
                    phone_number,
                    completion_message,
                    [
                        {"id": "show_jobs", "title": "🔍 Show Jobs"},
                        {"id": "menu", "title": "📋 Main Menu"},
                    ],
                )

                if success:
                    return ""  # Don't send system message

        except Exception as e:
            logger.error(f"Error sending completion buttons: {e}")

        # Fallback to text message if buttons fail
        return (
            completion_message
            + "\n\nType 'menu' for main menu or 'show jobs' to see matches!"
        )

    def clear_guided_setup_state(self, user_id: int) -> bool:
        """Clear guided setup state"""
        try:
            cursor = self.db.connection.cursor()
            cursor.execute(
                "UPDATE user_preferences SET guided_setup_step = NULL WHERE user_id = %s",
                (user_id,),
            )
            self.db.connection.commit()
            return True
        except Exception as e:
            logger.error(f"Error clearing guided setup state: {e}")
            return False

    def start_guided_setup(self, user_id: int) -> str:
        """Start guided setup flow"""
        self.set_guided_setup_state(user_id, "name")
        return (
            "🎯 *Guided Setup*\n\n"
            "I'll ask you a few questions to set up your perfect job search.\n\n"
            "Let's start: What's your full name?"
        )

    def welcome_new_user_setup(
        self, phone_number: str, user_id: int, whatsapp_service
    ) -> str:
        """Welcome flow for brand new users"""
        buttons = [
            {
                "type": "reply",
                "reply": {"id": "guided_setup", "title": "🎯 Guided Setup"},
            },
            {"type": "reply", "reply": {"id": "form_setup", "title": "📝 Quick Form"}},
            {"type": "reply", "reply": {"id": "help_setup", "title": "❓ Need Help"}},
        ]

        welcome_message = (
            "👋 *Welcome to Aremu Job Bot!*\n\n"
            "Let's set up your job preferences to find perfect opportunities for you.\n\n"
            "Choose your preferred setup method:"
        )

        whatsapp_service.send_button_menu(phone_number, welcome_message, buttons)
        return ""  # Don't send system message

    def resume_incomplete_setup(
        self, phone_number: str, user_id: int, prefs: dict, whatsapp_service
    ) -> str:
        """Resume incomplete preference setup"""
        missing_items = []
        if not prefs.get("job_roles"):
            missing_items.append("Job titles")
        if not prefs.get("preferred_locations"):
            missing_items.append("Locations")
        if not prefs.get("salary_min"):
            missing_items.append("Salary")
        if not prefs.get("years_of_experience"):
            missing_items.append("Experience")
        if not prefs.get("work_arrangements"):
            missing_items.append("Work style")

        buttons = [
            {
                "type": "reply",
                "reply": {"id": "continue_setup", "title": "✅ Continue Setup"},
            },
            {
                "type": "reply",
                "reply": {"id": "start_fresh", "title": "🔄 Start Fresh"},
            },
        ]

        resume_message = (
            "🔄 *Resume Your Setup*\n\n"
            f"You have some preferences saved, but missing:\n"
            f"• {', '.join(missing_items)}\n\n"
            "Would you like to continue where you left off or start fresh?"
        )

        whatsapp_service.send_button_menu(phone_number, resume_message, buttons)
        return "Resume setup sent!"
