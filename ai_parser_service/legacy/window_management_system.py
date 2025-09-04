#!/usr/bin/env python3
"""
24-Hour Window Management System for WhatsApp Bot
Manages WhatsApp conversation windows to optimize costs
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple
from .database_manager import DatabaseManager

logger = logging.getLogger(__name__)


class WindowManagementSystem:
    """Manages 24-hour WhatsApp conversation windows"""

    def __init__(self):
        self.db = DatabaseManager()
        self._create_window_tracking_table()

    def _create_window_tracking_table(self):
        """Create conversation_windows table if it doesn't exist"""
        try:
            cursor = self.db.connection.cursor()

            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS conversation_windows (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
                    window_start TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    window_status VARCHAR(20) DEFAULT 'active',
                    battery_warning_sent BOOLEAN DEFAULT FALSE,
                    four_hour_reminder_sent BOOLEAN DEFAULT FALSE,
                    messages_in_window INTEGER DEFAULT 0,
                    UNIQUE(user_id, window_start)
                );
            """
            )

            # Create index for performance
            cursor.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_conversation_windows_user_id 
                ON conversation_windows(user_id);
            """
            )

            cursor.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_conversation_windows_status 
                ON conversation_windows(window_status);
            """
            )

            self.db.connection.commit()
            logger.info("✅ Window management table ready")

        except Exception as e:
            logger.error(f"❌ Error creating window management table: {e}")

    def start_new_window(self, user_id: int) -> bool:
        """Start a new 24-hour conversation window for user"""
        try:
            cursor = self.db.connection.cursor()

            # Close any existing active windows first
            cursor.execute(
                """
                UPDATE conversation_windows 
                SET window_status = 'expired'
                WHERE user_id = %s AND window_status = 'active'
            """,
                (user_id,),
            )

            # Start new window
            cursor.execute(
                """
                INSERT INTO conversation_windows 
                (user_id, window_start, last_activity, window_status, messages_in_window)
                VALUES (%s, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 'active', 1)
            """,
                (user_id,),
            )

            self.db.connection.commit()
            logger.info(f"🔋 Started new 24h window for user {user_id}")
            return True

        except Exception as e:
            logger.error(f"❌ Error starting new window: {e}")
            return False

    def update_window_activity(self, user_id: int) -> bool:
        """Update last activity in current window"""
        try:
            cursor = self.db.connection.cursor()

            cursor.execute(
                """
                UPDATE conversation_windows 
                SET last_activity = CURRENT_TIMESTAMP,
                    messages_in_window = messages_in_window + 1
                WHERE user_id = %s AND window_status = 'active'
            """,
                (user_id,),
            )

            if cursor.rowcount == 0:
                # No active window, start a new one
                return self.start_new_window(user_id)

            self.db.connection.commit()
            return True

        except Exception as e:
            logger.error(f"❌ Error updating window activity: {e}")
            return False

    def get_window_status(self, user_id: int) -> Dict:
        """Get current window status for user"""
        try:
            cursor = self.db.connection.cursor()

            cursor.execute(
                """
                SELECT
                    window_start,
                    last_activity,
                    window_status,
                    battery_warning_sent,
                    four_hour_reminder_sent,
                    messages_in_window,
                    EXTRACT(EPOCH FROM (CURRENT_TIMESTAMP - window_start))/3600 as hours_elapsed
                FROM conversation_windows 
                WHERE user_id = %s AND window_status = 'active'
                ORDER BY window_start DESC
                LIMIT 1
            """,
                (user_id,),
            )

            result = cursor.fetchone()

            if not result:
                return {
                    "has_active_window": False,
                    "needs_new_window": True,
                    "hours_elapsed": 0,
                    "status": "no_window",
                }

            hours_elapsed = float(result[6])

            return {
                "has_active_window": True,
                "window_start": result[0],
                "last_activity": result[1],
                "window_status": result[2],
                "battery_warning_sent": result[3],
                "four_hour_reminder_sent": result[4],
                "messages_in_window": result[5],
                "hours_elapsed": hours_elapsed,
                "needs_four_hour_reminder": hours_elapsed >= 20 and not result[4],
                "needs_battery_warning": hours_elapsed >= 23 and not result[3],
                "window_expired": hours_elapsed >= 24,
                "status": "active" if hours_elapsed < 24 else "expired",
            }

        except Exception as e:
            logger.error(f"❌ Error getting window status: {e}")
            return {"has_active_window": False, "status": "error"}

    def send_four_hour_reminder(self, user_id: int) -> bool:
        """Mark that 4-hour reminder has been sent"""
        try:
            cursor = self.db.connection.cursor()

            cursor.execute(
                """
                UPDATE conversation_windows
                SET four_hour_reminder_sent = TRUE
                WHERE user_id = %s AND window_status = 'active'
            """,
                (user_id,),
            )

            self.db.connection.commit()
            logger.info(f"⏰ 4-hour reminder marked as sent for user {user_id}")
            return True

        except Exception as e:
            logger.error(f"❌ Error marking 4-hour reminder: {e}")
            return False

    def send_battery_warning(self, user_id: int) -> bool:
        """Mark that battery warning has been sent"""
        try:
            cursor = self.db.connection.cursor()

            cursor.execute(
                """
                UPDATE conversation_windows
                SET battery_warning_sent = TRUE
                WHERE user_id = %s AND window_status = 'active'
            """,
                (user_id,),
            )

            self.db.connection.commit()
            logger.info(f"🔋 Battery warning marked as sent for user {user_id}")
            return True

        except Exception as e:
            logger.error(f"❌ Error marking battery warning: {e}")
            return False

    def expire_window(self, user_id: int) -> bool:
        """Mark current window as expired"""
        try:
            cursor = self.db.connection.cursor()

            cursor.execute(
                """
                UPDATE conversation_windows 
                SET window_status = 'expired'
                WHERE user_id = %s AND window_status = 'active'
            """,
                (user_id,),
            )

            self.db.connection.commit()
            logger.info(f"😴 Expired window for user {user_id}")
            return True

        except Exception as e:
            logger.error(f"❌ Error expiring window: {e}")
            return False

    def get_four_hour_reminder_message(self) -> str:
        """Get the 4-hour reminder message"""
        return (
            "⏰ *Friendly reminder!*\n\n"
            "I have about 4 hours left in my current session. "
            "I'll keep sending you job alerts until then!\n\n"
            "💡 Send me a message anytime to reset my 24-hour window."
        )

    def get_battery_warning_message(self) -> str:
        """Get the battery warning message"""
        return (
            "🔋 *My battery is running low!*\n\n"
            "Send me any message in the next hour to keep getting job updates, "
            "or I'll go to sleep mode 😴\n\n"
            "💡 Just say 'hi' or 'keep going' to boost my energy!"
        )

    def get_window_expired_message(self, missed_jobs_count: int = 0) -> str:
        """Get message for when user returns after window expired"""
        if missed_jobs_count > 0:
            return (
                f"😴 *I was sleeping, but I'm back!*\n\n"
                f"While I was away, {missed_jobs_count} new jobs matched your profile. "
                f"Let me catch you up...\n\n"
                f"💡 I'll start monitoring for new jobs again!"
            )
        else:
            return (
                "😴 *I was sleeping, but I'm back!*\n\n"
                "No new jobs while I was away, but I'm now monitoring "
                "for fresh opportunities!\n\n"
                "💡 Send me a message anytime to keep the conversation active."
            )

    def cleanup_old_windows(self, days_old: int = 7) -> int:
        """Clean up old window records"""
        try:
            cursor = self.db.connection.cursor()

            cursor.execute(
                """
                DELETE FROM conversation_windows 
                WHERE window_start < CURRENT_DATE - INTERVAL '%s days'
            """,
                (days_old,),
            )

            deleted_count = cursor.rowcount
            self.db.connection.commit()

            logger.info(f"🧹 Cleaned up {deleted_count} old window records")
            return deleted_count

        except Exception as e:
            logger.error(f"❌ Error cleaning up old windows: {e}")
            return 0
