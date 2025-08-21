#!/usr/bin/env python3
"""
Field Update Handler - Manages individual preference field updates
Handles field-specific update operations and state management
"""

import logging
import re
from typing import Dict, Optional

logger = logging.getLogger(__name__)


class FieldUpdateHandler:
    """Handles individual preference field updates"""

    def __init__(self, db, pref_manager):
        """Initialize field update handler with required dependencies"""
        self.db = db
        self.pref_manager = pref_manager

    def is_updating_preference_field(self, user_id: int) -> bool:
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

    def handle_preference_field_update(
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
                return "No field update in progress. Type 'settings' to update preferences."

            field_name = result[0]

            # Route to appropriate field update handler
            if field_name == "name":
                return self.update_name_field(user_message, user_id)
            elif field_name == "job_title":
                return self.update_job_title_field(user_message, user_id)
            elif field_name == "location":
                return self.update_location_field(user_message, user_id)
            elif field_name == "salary":
                return self.update_salary_field(user_message, user_id)
            elif field_name == "experience":
                return self.update_experience_field(user_message, user_id)
            elif field_name == "work_style":
                return self.update_work_style_field(user_message, user_id)
            else:
                return "Unknown field update. Type 'settings' to try again."

        except Exception as e:
            logger.error(f"Error handling field update: {e}")
            return "Something went wrong. Type 'settings' to try again."

    def set_updating_field(self, user_id: int, field_name: str) -> bool:
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

    def clear_updating_field(self, user_id: int) -> bool:
        """Clear the updating field after update is complete"""
        try:
            conn = self.db.get_connection()
            try:
                cursor = conn.cursor()
                # First ensure user_preferences record exists
                cursor.execute(
                    """
                    INSERT INTO user_preferences (user_id, updating_field)
                    VALUES (%s, NULL)
                    ON CONFLICT (user_id)
                    DO UPDATE SET updating_field = NULL
                    """,
                    (user_id,),
                )
                return True
            finally:
                self.db.return_connection(conn)
        except Exception as e:
            logger.error(f"Error clearing updating field: {e}")
            return False

    def update_name_field(self, user_message: str, user_id: int) -> str:
        """Update the user's name"""
        try:
            name = user_message.strip()
            if len(name) < 2:
                return "Please enter a valid name (at least 2 characters)."

            # Update only the users table (name doesn't go in user_preferences)
            conn = self.db.get_connection()
            try:
                cursor = conn.cursor()
                cursor.execute(
                    "UPDATE users SET name = %s WHERE id = %s", (name, user_id)
                )

                # Clear the updating field state
                self.clear_updating_field(user_id)

                return f"✅ Name updated to: {name}\n\nType 'settings' to update more fields or 'menu' for main menu."
            finally:
                self.db.return_connection(conn)

        except Exception as e:
            logger.error(f"Error updating name: {e}")
            return "Failed to update name. Please try again."

    def update_job_title_field(self, user_message: str, user_id: int) -> str:
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
                self.clear_updating_field(user_id)
                return f"✅ Job titles updated to: {', '.join(job_titles)}\n\nType 'settings' to update more fields or 'menu' for main menu."
            else:
                return "Failed to update job titles. Please try again."

        except Exception as e:
            logger.error(f"Error updating job titles: {e}")
            return "Failed to update job titles. Please try again."

    def update_location_field(self, user_message: str, user_id: int) -> str:
        """Update the user's location preferences"""
        try:
            locations = [loc.strip() for loc in user_message.split(",")]
            locations = [loc for loc in locations if loc]  # Remove empty

            if not locations:
                return "Please enter at least one location."

            preferences = {"location": locations}
            success = self.pref_manager.save_preferences(user_id, preferences)

            if success:
                self.clear_updating_field(user_id)
                return f"✅ Locations updated to: {', '.join(locations)}\n\nType 'settings' to update more fields or 'menu' for main menu."
            else:
                return "Failed to update locations. Please try again."

        except Exception as e:
            logger.error(f"Error updating locations: {e}")
            return "Failed to update locations. Please try again."

    def update_salary_field(self, user_message: str, user_id: int) -> str:
        """Update the user's salary preferences"""
        try:
            # Extract salary amount from message
            salary_match = re.search(
                r"[\d,]+", user_message.replace("₦", "").replace(",", "")
            )

            if salary_match:
                salary_amount = int(salary_match.group().replace(",", ""))

                # Validate reasonable salary range
                if salary_amount < 50000:
                    return "Please enter a realistic salary amount (minimum ₦50,000)."

                preferences = {"salary_min": salary_amount, "salary_currency": "NGN"}
                success = self.pref_manager.save_preferences(user_id, preferences)

                if success:
                    self.clear_updating_field(user_id)
                    return f"✅ Minimum salary updated to: ₦{salary_amount:,}\n\nType 'settings' to update more fields or 'menu' for main menu."
                else:
                    return "Failed to update salary. Please try again."
            else:
                return "Please enter a valid salary amount (e.g., ₦500,000 or 500000)."

        except Exception as e:
            logger.error(f"Error updating salary: {e}")
            return (
                "Failed to update salary. Please enter a valid amount (e.g., ₦500,000)."
            )

    def update_experience_field(self, user_message: str, user_id: int) -> str:
        """Update the user's experience level - accepts only years as numbers"""
        try:
            # Extract years from message - only accept numbers
            years_match = re.search(r"(\d+)", user_message)
            if years_match:
                years = int(years_match.group(1))
                # Validate reasonable experience range
                if years > 50:
                    return "Please enter a realistic number of years (0-50)."
            else:
                return "Please enter your experience as a number (e.g., '3' for 3 years, '0' for entry level)."

            preferences = {"years_of_experience": years}
            success = self.pref_manager.save_preferences(user_id, preferences)

            if success:
                self.clear_updating_field(user_id)
                experience_text = (
                    "Entry level"
                    if years == 0
                    else f"{years} year{'s' if years != 1 else ''}"
                )
                return f"✅ Experience updated to: {experience_text}\n\nType 'settings' to update more fields or 'menu' for main menu."
            else:
                return "Failed to update experience. Please try again."

        except Exception as e:
            logger.error(f"Error updating experience: {e}")
            return "Failed to update experience. Please try again."

    def update_work_style_field(self, user_message: str, user_id: int) -> str:
        """Update the user's work style preferences"""
        try:
            work_styles = [style.strip() for style in user_message.split(",")]
            work_styles = [style for style in work_styles if style]  # Remove empty

            if not work_styles:
                return "Please enter at least one work style (Remote, Hybrid, Onsite)."

            # Standardize work style names
            standardized_styles = []
            for style in work_styles:
                style_lower = style.lower()
                if "remote" in style_lower:
                    standardized_styles.append("Remote")
                elif "hybrid" in style_lower:
                    standardized_styles.append("Hybrid")
                elif "onsite" in style_lower or "office" in style_lower:
                    standardized_styles.append("Onsite")
                else:
                    standardized_styles.append(style.title())

            preferences = {"work_arrangements": standardized_styles}
            success = self.pref_manager.save_preferences(user_id, preferences)

            if success:
                self.clear_updating_field(user_id)
                return f"✅ Work style updated to: {', '.join(standardized_styles)}\n\nType 'settings' to update more fields or 'menu' for main menu."
            else:
                return "Failed to update work style. Please try again."

        except Exception as e:
            logger.error(f"Error updating work style: {e}")
            return "Failed to update work style. Please try again."
