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

            if current_step == "job_title":
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
        # Save location and move to salary step
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
        return f"✅ {experience_text} experience noted.\n\n🏢 What's your preferred work arrangement? (e.g., Remote, Onsite, Hybrid)"

    def _handle_work_style_step(self, user_message: str, user_id: int) -> str:
        """Handle work style step in guided setup - final step"""
        # Save work style and finish setup
        work_styles = [style.strip().title() for style in user_message.split(",")]
        preferences = {"work_arrangements": work_styles, "preferences_confirmed": True}
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

        return (
            f"🎉 Perfect! Setup complete!\n\n"
            f"✅ Your preferences:\n"
            f"• Job: {', '.join(work_styles)}\n"
            f"• Work style: {', '.join(work_styles)}\n\n"
            "I'm now actively searching for jobs that match your criteria. "
            "You'll get instant notifications when perfect opportunities appear!\n\n"
            "Type 'menu' and select 'Show Jobs' to see current matches!"
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
        self.set_guided_setup_state(user_id, "job_title")
        return (
            "🎯 *Guided Setup*\n\n"
            "I'll ask you a few questions to set up your perfect job search.\n\n"
            "Let's start: What type of job are you looking for? (e.g., Software Developer, Marketing Manager, etc.)"
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
        return "Welcome setup sent!"

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
