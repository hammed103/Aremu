#!/usr/bin/env python3
"""
Interactive Handler - Manages menu interactions and button selections
Handles WhatsApp interactive messages, buttons, and list selections
"""

import logging
from typing import Dict, Optional

logger = logging.getLogger(__name__)


class InteractiveHandler:
    """Handles interactive menu operations and button selections"""

    def __init__(
        self,
        db,
        pref_manager,
        whatsapp_service,
        preference_handler,
        field_update_handler,
        guided_setup_handler,
        job_search_handler,
    ):
        """Initialize interactive handler with required dependencies"""
        self.db = db
        self.pref_manager = pref_manager
        self.whatsapp_service = whatsapp_service
        self.preference_handler = preference_handler
        self.field_update_handler = field_update_handler
        self.guided_setup_handler = guided_setup_handler
        self.job_search_handler = job_search_handler

    def handle_interactive_message(
        self, phone_number: str, interactive_data: dict
    ) -> str:
        """Handle responses from interactive messages"""
        try:
            user_id = self.db.get_or_create_user(phone_number)

            # Handle list replies
            if interactive_data.get("type") == "list_reply":
                selection_id = interactive_data["list_reply"]["id"]
                return self.handle_list_selection(selection_id, phone_number, user_id)

            # Handle button replies
            elif interactive_data.get("type") == "button_reply":
                button_id = interactive_data["button_reply"]["id"]
                return self.handle_button_selection(button_id, phone_number, user_id)

        except Exception as e:
            logger.error(f"Error handling interactive message: {e}")
            return "Something went wrong. Please try again or type 'menu' for options."

    def handle_list_selection(
        self, selection_id: str, phone_number: str, user_id: int
    ) -> str:
        """Handle main menu selections and preference field updates"""
        try:
            # Main menu selections
            if selection_id == "change_preferences":
                return self.start_preference_setup(phone_number, user_id)

            elif selection_id == "view_jobs":
                user_prefs = self.pref_manager.get_preferences(user_id)
                if not user_prefs or not user_prefs.get("preferences_confirmed"):
                    return "Please set your preferences first. Type 'menu' and select 'Change Preferences'."
                return self.job_search_handler.handle_job_search(
                    user_prefs, user_id, phone_number
                )

            elif selection_id == "cv_analyzer":
                return self.start_cv_analysis(phone_number)

            elif selection_id == "interview_assistant":
                return self.start_interview_assistant(phone_number)

            elif selection_id == "help":
                return self.show_help_info()

            # Preference field update selections
            elif selection_id == "update_name":
                self.field_update_handler.set_updating_field(user_id, "name")
                return "👤 *Update Full Name*\n\nPlease type your full name:\n\nExample: Ahmed Ibrahim"

            elif selection_id == "update_job_title":
                self.field_update_handler.set_updating_field(user_id, "job_title")
                return "🎯 *Update Job Title*\n\nWhat type of job are you looking for?\n\nExamples:\n• Software Developer\n• Marketing Manager\n• Data Analyst\n• Frontend Developer, Backend Developer"

            elif selection_id == "update_location":
                self.field_update_handler.set_updating_field(user_id, "location")
                return "📍 *Update Location*\n\nWhere would you like to work?\n\nExamples:\n• Lagos\n• Abuja\n• Remote\n• Lagos, Abuja, Remote"

            elif selection_id == "update_salary":
                self.field_update_handler.set_updating_field(user_id, "salary")
                return "💰 *Update Minimum Salary*\n\nWhat's your minimum salary expectation?\n\nExamples:\n• ₦500,000\n• ₦1,200,000\n• ₦800,000"

            elif selection_id == "update_experience":
                return self.show_experience_options(phone_number, user_id)

            elif selection_id == "update_work_style":
                return self.show_work_style_options(phone_number, user_id)

            elif selection_id == "confirm_preferences":
                return self.preference_handler.handle_preference_confirmation(user_id)

            # Handle experience level selections
            elif selection_id.startswith("exp_"):
                return self.handle_experience_selection(selection_id, user_id)

            # Handle work style selections
            elif selection_id.startswith("work_"):
                return self.handle_work_style_selection(selection_id, user_id)

            else:
                return "Invalid selection. Type 'menu' to see options again."

        except Exception as e:
            logger.error(f"Error handling list selection {selection_id}: {e}")
            return "Something went wrong. Type 'menu' to try again."

    def handle_button_selection(
        self, button_id: str, phone_number: str, user_id: int
    ) -> str:
        """Handle button selections"""
        try:
            # Handle preference update menu buttons
            if button_id == "update_form":
                return self.show_field_update_menu(phone_number, user_id)

            elif button_id == "show_traditional_form":
                return self.preference_handler.show_traditional_preference_form(
                    phone_number, first_time=False
                )

            elif button_id == "reset_prefs":
                # Clear existing preferences
                success = self.pref_manager.clear_preferences(user_id)
                if success:
                    return self.guided_setup_handler.welcome_new_user_setup(
                        phone_number, user_id, self.whatsapp_service
                    )
                else:
                    return "Failed to reset preferences. Please try again."

            # Handle new user setup buttons
            elif button_id == "guided_setup":
                return self.guided_setup_handler.start_guided_setup(user_id)

            elif button_id == "form_setup":
                return self.preference_handler.show_preference_form(
                    phone_number, first_time=True
                )

            elif button_id == "help_setup":
                return self.show_help_info()

            # Handle post-confirmation buttons
            elif button_id == "view_jobs_now":
                user_prefs = self.pref_manager.get_preferences(user_id)
                if user_prefs and user_prefs.get("preferences_confirmed"):
                    return self.job_search_handler.handle_job_search(
                        user_prefs, user_id, phone_number
                    )
                else:
                    return "Please set up your preferences first. Type 'menu' and select 'Change Preferences'."

            elif button_id == "clear_all_prefs":
                return self.handle_clear_all_preferences(user_id, phone_number)

            elif button_id == "main_menu":
                return self.show_main_menu(phone_number)

            # Handle clear all confirmation buttons
            elif button_id == "confirm_clear_all":
                return self.execute_clear_all_preferences(user_id, phone_number)

            elif button_id == "cancel_clear":
                return "❌ Clear cancelled. Your preferences are safe!\n\nType 'menu' for options."

            # Handle incomplete setup buttons
            elif button_id == "continue_setup":
                return self.preference_handler.show_preference_form(
                    phone_number, first_time=False
                )

            elif button_id == "start_fresh":
                success = self.pref_manager.clear_preferences(user_id)
                if success:
                    return self.guided_setup_handler.welcome_new_user_setup(
                        phone_number, user_id, self.whatsapp_service
                    )
                else:
                    return "Failed to reset. Please try again."

            # Handle main menu button selections
            elif button_id == "change_preferences":
                return self.start_preference_setup(phone_number, user_id)

            elif button_id == "view_jobs":
                user_prefs = self.pref_manager.get_preferences(user_id)
                if not self._has_meaningful_preferences(user_prefs):
                    return "Please set your preferences first. Type 'menu' and select 'Change Preferences'."
                return self.job_search_handler.handle_job_search(
                    user_prefs, user_id, phone_number
                )

            elif button_id == "help":
                return self.show_help_info()

            else:
                return "Invalid selection. Type 'menu' to see options again."

        except Exception as e:
            logger.error(f"Error handling button selection {button_id}: {e}")
            return "Something went wrong. Type 'menu' to try again."

    def start_preference_setup(self, phone_number: str, user_id: int) -> str:
        """Always show current preferences first, then options"""
        existing_prefs = self.pref_manager.get_preferences(user_id)

        # Always show current preferences first (this is what user wants)
        if existing_prefs:
            # Show current preferences regardless of confirmation status
            return self.show_preference_update_menu(
                phone_number, user_id, existing_prefs
            )
        else:
            # Brand new user with no preferences at all
            return self.guided_setup_handler.welcome_new_user_setup(
                phone_number, user_id, self.whatsapp_service
            )

    def show_preference_update_menu(
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
                else "❌ Not set"
            )

            locations = existing_prefs.get("preferred_locations", [])
            locations_str = (
                ", ".join(locations)
                if locations and isinstance(locations, list)
                else "❌ Not set"
            )

            work_arrangements = existing_prefs.get("work_arrangements", [])
            work_style_str = (
                ", ".join(work_arrangements)
                if work_arrangements and isinstance(work_arrangements, list)
                else "❌ Not set"
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
                f"⏱️ **Experience:** {self._format_experience(existing_prefs.get('years_of_experience'))}\n"
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
                f"Your current job preferences:\n\n"
                f"{current_summary}\n\n"
                "What would you like to do?"
            )

            self.whatsapp_service.send_button_menu(phone_number, message, buttons)
            return "Preference update menu sent!"

        except Exception as e:
            logger.error(f"❌ Error showing preference update menu: {e}")
            return self.preference_handler.show_preference_form(
                phone_number, first_time=False
            )

    def show_main_menu(self, phone_number: str) -> str:
        """Show greeting with immediate options menu"""
        try:
            # Show options directly using list menu
            sections = [
                {
                    "title": "Options",
                    "rows": [
                        {
                            "id": "change_preferences",
                            "title": "⚙️ Change Preferences",
                            "description": "Set your job search criteria",
                        },
                        {
                            "id": "view_jobs",
                            "title": "💼 Show Jobs",
                            "description": "See jobs you may have missed",
                        },
                        {
                            "id": "cv_analyzer",
                            "title": "📋 CV Analyzer",
                            "description": "Get feedback on your resume",
                        },
                        {
                            "id": "interview_assistant",
                            "title": "🎤 Interview Assistant",
                            "description": "Get help with interview preparation",
                        },
                        {
                            "id": "help",
                            "title": "❓ Help",
                            "description": "Learn how to use the bot",
                        },
                    ],
                }
            ]

            success = self.whatsapp_service.send_list_menu(
                phone_number,
                "👨‍💼 Aremu.ai Personal Job Assistant",
                "How can I help you land your dream job?",
                sections,
            )

            return "Menu sent!" if success else "Failed to send menu"

        except Exception as e:
            logger.error(f"Error showing main menu: {e}")
            # Fallback to text menu if buttons fail
            return (
                "👨‍💼 *Aremu.ai Personal Job Assistant*\n\n"
                "How can I help you land your dream job?\n\n"
                "⚙️ *Change Preferences* - Set your job search criteria\n"
                "💼 *Show Jobs* - See jobs matching your preferences\n"
                "📋 *CV Analyzer* - Get feedback on your resume\n"
                "🎤 *Interview Assistant* - Get help with interview preparation\n"
                "❓ *Help* - Learn how to use the bot\n\n"
                "Type what you want to do!"
            )

    def show_field_update_menu(self, phone_number: str, user_id: int) -> str:
        """Show menu for updating individual preference fields"""
        try:
            # Get current preferences to show what can be updated
            current_prefs = self.pref_manager.get_preferences(user_id)

            # Get user name from users table
            cursor = self.db.connection.cursor()
            cursor.execute("SELECT name FROM users WHERE id = %s", (user_id,))
            user_name_result = cursor.fetchone()
            user_name = (
                user_name_result[0]
                if user_name_result and user_name_result[0]
                else "❌ Not set"
            )

            # Create field update options using list menu
            sections = [
                {
                    "title": "Update Preferences",
                    "rows": [
                        {
                            "id": "update_name",
                            "title": "👤 Name",
                            "description": f"Current: {user_name}",
                        },
                        {
                            "id": "update_job_title",
                            "title": "🎯 Job Title",
                            "description": f"Current: {', '.join(current_prefs.get('job_roles', [])) if current_prefs and current_prefs.get('job_roles') else '❌ Not set'}",
                        },
                        {
                            "id": "update_location",
                            "title": "📍 Location",
                            "description": f"Current: {', '.join(current_prefs.get('preferred_locations', [])) if current_prefs and current_prefs.get('preferred_locations') else '❌ Not set'}",
                        },
                        {
                            "id": "update_salary",
                            "title": "💰 Salary",
                            "description": (
                                f"Current: ₦{(current_prefs.get('salary_min') or 0):,}+ NGN"
                                if current_prefs
                                else "Current: ❌ Not set"
                            ),
                        },
                        {
                            "id": "update_experience",
                            "title": "⏱️ Experience",
                            "description": (
                                f"Current: {self._format_experience(current_prefs.get('years_of_experience'))}"
                                if current_prefs
                                else "Current: ❌ Not set"
                            ),
                        },
                        {
                            "id": "update_work_style",
                            "title": "🏢 Work Style",
                            "description": f"Current: {', '.join(current_prefs.get('work_arrangements', [])) if current_prefs and current_prefs.get('work_arrangements') else '❌ Not set'}",
                        },
                    ],
                }
            ]

            success = self.whatsapp_service.send_list_menu(
                phone_number, "⚙️ Update Preferences", "Choose what to update:", sections
            )

            return (
                "Preference menu sent!" if success else "Failed to send preference menu"
            )

        except Exception as e:
            logger.error(f"Error showing field update menu: {e}")
            # Fallback to text menu
            return (
                "⚙️ *Update Preferences*\n\n"
                "Choose what to update:\n\n"
                "👤 Type 'name' - Update your name\n"
                "🎯 Type 'job' - Update job titles\n"
                "📍 Type 'location' - Update locations\n"
                "💰 Type 'salary' - Update salary\n"
                "⏱️ Type 'experience' - Update experience\n"
                "🏢 Type 'work' - Update work style\n\n"
                "Type 'menu' to go back."
            )

    def handle_clear_all_preferences(self, user_id: int, phone_number: str) -> str:
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

    def execute_clear_all_preferences(self, user_id: int, phone_number: str) -> str:
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

    def start_cv_analysis(self, phone_number: str) -> str:
        """Start CV analysis flow"""
        return (
            "📋 *CV Analyzer*\n\n"
            "Send me your CV/Resume as:\n"
            "• PDF document 📄\n"
            "• Word document 📝\n"
            "• Or paste the text directly ✍️\n\n"
            "I'll analyze it and give you feedback to improve your chances with Nigerian employers! 🇳🇬"
        )

    def start_interview_assistant(self, phone_number: str) -> str:
        """Start interview assistant flow"""
        return (
            "🎤 *Interview Assistant*\n\n"
            "I'll help you prepare for your job interviews! Tell me:\n\n"
            "• What position are you interviewing for?\n"
            "• Which company (if you know)?\n"
            "• Any specific concerns or questions?\n\n"
            "I'll provide tailored advice for the Nigerian job market.\n\n"
            "Type 'menu' to go back to main menu."
        )

    def show_help_info(self) -> str:
        """Show help information"""
        return (
            "❓ *Help & Support*\n\n"
            "Here's how to use Aremu Job Bot:\n\n"
            "🎯 *Change Preferences* - Set your job criteria\n"
            "💼 *Show Jobs* - See jobs you may have missed\n"
            "📋 *CV Analyzer* - Get resume feedback\n\n"
            "💬 *How to use:*\n"
            "• Type `menu` - Show all options\n"
            "• Select what you want from the menu\n"
            "• Or just tell me what you need!\n\n"
            "For CV review or interview tips, just ask me directly! 😊"
        )

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

    def show_experience_options(self, phone_number: str, user_id: int) -> str:
        """Show experience level options as a list menu"""
        try:
            sections = [
                {
                    "title": "Experience Level",
                    "rows": [
                        {
                            "id": "exp_none",
                            "title": "None (Entry Level)",
                            "description": "Fresh graduate or no experience",
                        },
                        {
                            "id": "exp_1",
                            "title": "1 year",
                            "description": "1 year of experience",
                        },
                        {
                            "id": "exp_2",
                            "title": "2 years",
                            "description": "2 years of experience",
                        },
                        {
                            "id": "exp_3",
                            "title": "3 years",
                            "description": "3 years of experience",
                        },
                        {
                            "id": "exp_4",
                            "title": "4 years",
                            "description": "4 years of experience",
                        },
                        {
                            "id": "exp_5",
                            "title": "5 years",
                            "description": "5 years of experience",
                        },
                        {
                            "id": "exp_6",
                            "title": "6 years",
                            "description": "6 years of experience",
                        },
                        {
                            "id": "exp_7",
                            "title": "7 years",
                            "description": "7 years of experience",
                        },
                        {
                            "id": "exp_8",
                            "title": "8 years",
                            "description": "8 years of experience",
                        },
                        {
                            "id": "exp_9plus",
                            "title": "9+ years",
                            "description": "9 or more years of experience",
                        },
                    ],
                }
            ]

            success = self.whatsapp_service.send_list_menu(
                phone_number,
                "⏱️ Experience Level",
                "Select your experience level:",
                sections,
            )

            return (
                "Experience options sent!"
                if success
                else "Failed to send experience options"
            )

        except Exception as e:
            logger.error(f"Error showing experience options: {e}")
            return "⏱️ *Update Experience*\n\nHow many years of experience do you have?\n\nType a number (0-9+):"

    def show_work_style_options(self, phone_number: str, user_id: int) -> str:
        """Show work style options as a list menu"""
        try:
            sections = [
                {
                    "title": "Work Arrangement",
                    "rows": [
                        {
                            "id": "work_remote",
                            "title": "🏠 Remote Only",
                            "description": "Work from home/anywhere",
                        },
                        {
                            "id": "work_onsite",
                            "title": "🏢 Onsite Only",
                            "description": "Work from office location",
                        },
                        {
                            "id": "work_hybrid",
                            "title": "🔄 Hybrid",
                            "description": "Mix of remote and office work",
                        },
                        {
                            "id": "work_flexible",
                            "title": "✨ Flexible",
                            "description": "Open to any arrangement",
                        },
                    ],
                }
            ]

            success = self.whatsapp_service.send_list_menu(
                phone_number,
                "🏢 Work Style",
                "Select your preferred work arrangement:",
                sections,
            )

            return (
                "Work style options sent!"
                if success
                else "Failed to send work style options"
            )

        except Exception as e:
            logger.error(f"Error showing work style options: {e}")
            return "🏢 *Update Work Style*\n\nWhat's your preferred work arrangement?\n\nType: Remote, Onsite, Hybrid, or Flexible"

    def handle_experience_selection(self, selection_id: str, user_id: int) -> str:
        """Handle experience level selection from preset options"""
        try:
            # Map selection IDs to years
            experience_map = {
                "exp_none": 0,
                "exp_1": 1,
                "exp_2": 2,
                "exp_3": 3,
                "exp_4": 4,
                "exp_5": 5,
                "exp_6": 6,
                "exp_7": 7,
                "exp_8": 8,
                "exp_9plus": 9,
            }

            years = experience_map.get(selection_id)
            if years is None:
                return "Invalid experience selection. Please try again."

            # Save the experience
            preferences = {"years_of_experience": years}
            success = self.pref_manager.save_preferences(user_id, preferences)

            if success:
                experience_text = (
                    "Entry level"
                    if years == 0
                    else (
                        f"{years}+ years"
                        if years == 9
                        else f"{years} year{'s' if years != 1 else ''}"
                    )
                )
                return f"✅ Experience updated to: {experience_text}\n\nType 'settings' to update more fields or 'menu' for main menu."
            else:
                return "Failed to update experience. Please try again."

        except Exception as e:
            logger.error(f"Error handling experience selection: {e}")
            return "Something went wrong. Please try again."

    def handle_work_style_selection(self, selection_id: str, user_id: int) -> str:
        """Handle work style selection from preset options"""
        try:
            # Map selection IDs to work arrangements (using database enum values)
            work_style_map = {
                "work_remote": ["remote"],
                "work_onsite": ["on-site"],
                "work_hybrid": ["hybrid"],
                "work_flexible": ["remote", "on-site", "hybrid"],
            }

            work_arrangements = work_style_map.get(selection_id)
            if not work_arrangements:
                return "Invalid work style selection. Please try again."

            # Save work style directly to database (bypass validation for preset options)
            success = self._save_work_arrangements_directly(user_id, work_arrangements)

            if success:
                # Display user-friendly capitalized versions
                display_map = {
                    "remote": "Remote",
                    "on-site": "Onsite",
                    "hybrid": "Hybrid",
                }
                display_styles = [
                    display_map.get(style, style.title()) for style in work_arrangements
                ]
                style_text = ", ".join(display_styles)
                return f"✅ Work style updated to: {style_text}\n\nType 'settings' to update more fields or 'menu' for main menu."
            else:
                return "Failed to update work style. Please try again."

        except Exception as e:
            logger.error(f"Error handling work style selection: {e}")
            return "Something went wrong. Please try again."

    def _has_meaningful_preferences(self, user_prefs: dict) -> bool:
        """Check if user has meaningful preferences set (regardless of confirmation status)"""
        if not user_prefs:
            return False

        # Check for key preference fields that indicate user has set up their profile
        meaningful_fields = [
            "job_roles",
            "preferred_locations",
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

    def _save_work_arrangements_directly(
        self, user_id: int, work_arrangements: list
    ) -> bool:
        """Save work arrangements directly to database bypassing validation"""
        try:
            cursor = self.db.connection.cursor()

            # Check if user preferences exist
            cursor.execute(
                "SELECT id FROM user_preferences WHERE user_id = %s", (user_id,)
            )
            exists = cursor.fetchone()

            if exists:
                # Update existing record - cast to enum array
                cursor.execute(
                    "UPDATE user_preferences SET work_arrangements = %s::work_arrangement_enum[], updated_at = CURRENT_TIMESTAMP WHERE user_id = %s",
                    (work_arrangements, user_id),
                )
            else:
                # Insert new record - cast to enum array
                cursor.execute(
                    "INSERT INTO user_preferences (user_id, work_arrangements) VALUES (%s, %s::work_arrangement_enum[])",
                    (user_id, work_arrangements),
                )

            self.db.connection.commit()
            logger.info(
                f"✅ Saved work arrangements for user {user_id}: {work_arrangements}"
            )
            return True

        except Exception as e:
            logger.error(f"❌ Error saving work arrangements: {e}")
            self.db.connection.rollback()
            return False
