#!/usr/bin/env python3
"""
New Bot Controller - Simplified main orchestrator using modular handlers
Handles message routing and coordinates specialized handlers
"""

import logging
from typing import Dict, Optional

# Legacy imports (keeping existing structure)
from legacy.database_manager import DatabaseManager
from legacy.flexible_preference_manager import FlexiblePreferenceManager
from legacy.intelligent_job_matcher import IntelligentJobMatcher
from legacy.job_tracking_system import JobTrackingSystem
from legacy.window_management_system import WindowManagementSystem
from agents.conversation_agent import ConversationAgent, PreferenceParsingAgent
from services.job_service import JobService
from services.whatsapp_service import WhatsAppService

# New modular handlers
from .preference_handler import PreferenceHandler
from .field_update_handler import FieldUpdateHandler
from .guided_setup_handler import GuidedSetupHandler
from .interactive_handler import InteractiveHandler
from .job_search_handler import JobSearchHandler

logger = logging.getLogger(__name__)


class BotController:
    """Simplified main controller using modular handlers"""

    def __init__(
        self, openai_api_key: str, whatsapp_token: str, whatsapp_phone_id: str
    ):
        """Initialize the bot controller with all components"""
        # Initialize database and core managers (keeping existing structure)
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

        # Initialize specialized handlers
        self.preference_handler = PreferenceHandler(
            self.db,
            self.pref_manager,
            self.preference_parser,
            self.whatsapp_service,
            self.window_manager,
        )

        self.field_update_handler = FieldUpdateHandler(self.db, self.pref_manager)

        self.guided_setup_handler = GuidedSetupHandler(
            self.db, self.pref_manager, self.window_manager
        )

        self.job_search_handler = JobSearchHandler(
            self.db,
            self.pref_manager,
            self.job_matcher,
            self.job_service,
            self.whatsapp_service,
            self.conversation_agent,
        )

        self.interactive_handler = InteractiveHandler(
            self.db,
            self.pref_manager,
            self.whatsapp_service,
            self.preference_handler,
            self.field_update_handler,
            self.guided_setup_handler,
            self.job_search_handler,
        )

        logger.info("🤖 New Bot Controller initialized with modular handlers")

    def handle_message(self, phone_number: str, user_message: str) -> str:
        """Simplified message handling using specialized handlers"""
        try:
            user_id = self.db.get_or_create_user(phone_number)
            user_message_lower = user_message.lower().strip()

            # Update conversation window activity
            self.window_manager.update_window_activity(user_id)

            # Show menu for explicit menu commands only
            if user_message_lower in [
                "menu",
                "main",
                "start",
                "/start",
                "/menu",
            ]:
                return self.interactive_handler.show_main_menu(phone_number)

            # Quick commands
            if user_message_lower in ["help", "/help"]:
                return self.interactive_handler.show_help_info()

            # Handle settings command
            if user_message_lower in ["settings", "preferences", "setup"]:
                return self.interactive_handler.start_preference_setup(
                    phone_number, user_id
                )

            # Handle clear command
            if user_message_lower in ["clear", "reset", "clear all"]:
                return self.interactive_handler.execute_clear_all_preferences(
                    user_id, phone_number
                )

            # Check if it's a preference form submission
            if self.preference_handler.is_preference_form(user_message):
                return self.preference_handler.process_preference_form(
                    user_message, phone_number
                )

            # Handle confirmation responses
            if user_message_lower in ["yes", "confirm", "correct", "ok"]:
                user_prefs = self.pref_manager.get_preferences(user_id)
                if user_prefs and not user_prefs.get("preferences_confirmed"):
                    return self.preference_handler.confirm_user_preferences(user_id)

            # Check if user is in guided setup mode
            if self.guided_setup_handler.is_in_guided_setup(user_id):
                response = self.guided_setup_handler.handle_guided_setup_step(
                    user_message, user_id
                )

                # Handle completion with buttons
                if (
                    isinstance(response, dict)
                    and response.get("type") == "completion_with_buttons"
                ):
                    # Send completion message with buttons
                    # Convert button format for send_button_menu
                    formatted_buttons = [
                        {
                            "type": "reply",
                            "reply": {"id": btn["id"], "title": btn["title"]},
                        }
                        for btn in response["buttons"]
                    ]
                    success = self.whatsapp_service.send_button_menu(
                        phone_number, response["message"], formatted_buttons
                    )
                    return (
                        ""
                        if success
                        else response["message"]
                        + "\n\nType 'menu' for main menu or 'show jobs' to see matches!"
                    )

                return response

            # Check if user is updating a specific preference field
            if self.field_update_handler.is_updating_preference_field(user_id):
                return self.field_update_handler.handle_preference_field_update(
                    user_message, phone_number, user_id
                )

            # Handle normal conversation using AI agent
            user_prefs = self.pref_manager.get_preferences(user_id)
            return self.job_search_handler.handle_normal_conversation(
                user_message, user_prefs, user_id
            )

        except Exception as e:
            logger.error(f"❌ Error handling message: {e}")
            return "Something went wrong. Type 'menu' to see options."

    def handle_interactive_message(
        self, phone_number: str, interactive_data: dict
    ) -> str:
        """Handle interactive messages using the interactive handler"""
        return self.interactive_handler.handle_interactive_message(
            phone_number, interactive_data
        )

    def handle_document_message(self, phone_number: str, document_data: dict) -> str:
        """Handle document uploads (CV analysis)"""
        try:
            # For now, return a simple response
            # This can be enhanced with actual CV analysis later
            return (
                "📋 *CV Received!*\n\n"
                "Thanks for sharing your CV. I'm analyzing it now...\n\n"
                "💡 *Quick Tips:*\n"
                "• Make sure your contact info is clear\n"
                "• Highlight your key achievements\n"
                "• Tailor it for Nigerian job market\n\n"
                "I'll send you detailed feedback shortly!"
            )
        except Exception as e:
            logger.error(f"❌ Error handling document: {e}")
            return "Sorry, I couldn't process your document. Please try again."

    def send_job_alerts(self) -> None:
        """Send job alerts to all users with confirmed preferences"""
        try:
            # Get all users with confirmed preferences
            cursor = self.db.connection.cursor()
            cursor.execute(
                """
                SELECT DISTINCT u.id, u.phone_number 
                FROM users u 
                JOIN user_preferences up ON u.id = up.user_id 
                WHERE up.preferences_confirmed = TRUE
                """
            )
            users = cursor.fetchall()

            for user_id, phone_number in users:
                try:
                    self.job_search_handler.send_job_alerts(user_id, phone_number)
                except Exception as e:
                    logger.error(f"Error sending alert to user {user_id}: {e}")

        except Exception as e:
            logger.error(f"❌ Error sending job alerts: {e}")

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

    def get_user_statistics(self) -> Dict:
        """Get statistics about bot usage"""
        try:
            cursor = self.db.connection.cursor()

            # Total users
            cursor.execute("SELECT COUNT(*) FROM users")
            total_users = cursor.fetchone()[0]

            # Users with confirmed preferences
            cursor.execute(
                "SELECT COUNT(*) FROM user_preferences WHERE preferences_confirmed = TRUE"
            )
            active_users = cursor.fetchone()[0]

            # Recent activity (last 7 days)
            cursor.execute(
                """
                SELECT COUNT(DISTINCT user_id) 
                FROM conversation_history 
                WHERE created_at >= NOW() - INTERVAL '7 days'
                """
            )
            recent_active = cursor.fetchone()[0] if cursor.fetchone() else 0

            return {
                "total_users": total_users,
                "active_users": active_users,
                "recent_active": recent_active,
                "engagement_rate": (
                    (recent_active / total_users * 100) if total_users > 0 else 0
                ),
            }

        except Exception as e:
            logger.error(f"Error getting user statistics: {e}")
            return {
                "total_users": 0,
                "active_users": 0,
                "recent_active": 0,
                "engagement_rate": 0,
            }

    def cleanup_old_data(self, days: int = 30) -> bool:
        """Clean up old conversation history and temporary data"""
        try:
            cursor = self.db.connection.cursor()

            # Clean old conversation history
            cursor.execute(
                "DELETE FROM conversation_history WHERE created_at < NOW() - INTERVAL %s",
                (f"{days} days",),
            )

            # Clean old job feedback
            cursor.execute(
                "DELETE FROM job_feedback WHERE created_at < NOW() - INTERVAL %s",
                (f"{days} days",),
            )

            self.db.connection.commit()
            logger.info(f"Cleaned up data older than {days} days")
            return True

        except Exception as e:
            logger.error(f"Error cleaning up old data: {e}")
            return False

    def health_check(self) -> Dict:
        """Perform health check on all components"""
        health = {
            "database": False,
            "whatsapp_service": False,
            "ai_agents": False,
            "handlers": False,
        }

        try:
            # Check database
            cursor = self.db.connection.cursor()
            cursor.execute("SELECT 1")
            health["database"] = True
        except Exception as e:
            logger.error(f"Database health check failed: {e}")

        try:
            # Check WhatsApp service (basic check)
            health["whatsapp_service"] = self.whatsapp_service is not None
        except Exception as e:
            logger.error(f"WhatsApp service health check failed: {e}")

        try:
            # Check AI agents
            health["ai_agents"] = (
                self.conversation_agent is not None
                and self.preference_parser is not None
            )
        except Exception as e:
            logger.error(f"AI agents health check failed: {e}")

        try:
            # Check handlers
            health["handlers"] = (
                self.preference_handler is not None
                and self.interactive_handler is not None
                and self.job_search_handler is not None
            )
        except Exception as e:
            logger.error(f"Handlers health check failed: {e}")

        health["overall"] = all(health.values())
        return health
