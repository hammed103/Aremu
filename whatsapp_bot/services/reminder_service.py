#!/usr/bin/env python3
"""
24-Hour Window Reminder Service
Tracks user activity and sends progressive reminders before the WhatsApp 24-hour window expires
"""

import os
import time
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import psycopg2
import psycopg2.extras
from psycopg2 import pool
from services.whatsapp_service import WhatsAppService

logger = logging.getLogger(__name__)


class ReminderService:
    def __init__(self, whatsapp_service: WhatsAppService):
        """Initialize reminder service"""
        self.whatsapp_service = whatsapp_service
        self.connection_pool = None
        self.connect_db()

        # Reminder schedule (hours remaining when to send reminder)
        # For testing: start reminders much earlier
        self.reminder_schedule = [
            22,
            20,
            18,
            16,
            8,
            5,
            3,
            1,
            0.25,
        ]  # More frequent for testing

    def connect_db(self):
        """Create database connection pool"""
        try:
            database_url = os.getenv(
                "DATABASE_URL",
                "postgresql://postgres.upnvhpgaljazlsoryfgj:prAlkIpbQDqOZtOj@aws-0-us-east-1.pooler.supabase.com:6543/postgres",
            )
            self.connection_pool = psycopg2.pool.ThreadedConnectionPool(
                minconn=1,
                maxconn=5,
                dsn=database_url,
                keepalives=1,
                keepalives_idle=30,
                keepalives_interval=10,
                keepalives_count=5,
            )
            logger.info("✅ Reminder service database pool created")
        except Exception as e:
            logger.error(f"❌ Database connection pool creation failed: {e}")
            raise

    def get_connection(self):
        """Get a connection from the pool with retry logic"""
        max_retries = 3
        for attempt in range(max_retries):
            try:
                if not self.connection_pool:
                    self.connect_db()

                conn = self.connection_pool.getconn()
                if conn:
                    conn.autocommit = True
                    return conn
                else:
                    raise Exception("Failed to get connection from pool")

            except Exception as e:
                logger.warning(f"⚠️ Connection attempt {attempt + 1} failed: {e}")
                if attempt < max_retries - 1:
                    time.sleep(1)
                    try:
                        if self.connection_pool:
                            self.connection_pool.closeall()
                        self.connect_db()
                    except:
                        pass
                else:
                    logger.error(
                        f"❌ Failed to get database connection after {max_retries} attempts"
                    )
                    raise

    def return_connection(self, conn):
        """Return a connection to the pool"""
        try:
            if self.connection_pool and conn:
                self.connection_pool.putconn(conn)
        except Exception as e:
            logger.error(f"❌ Error returning connection to pool: {e}")

    def execute_with_retry(
        self, query, params=None, fetch_one=False, fetch_all=False, cursor_factory=None
    ):
        """Execute query with automatic retry and connection management"""
        max_retries = 3
        for attempt in range(max_retries):
            conn = None
            try:
                conn = self.get_connection()
                cursor = (
                    conn.cursor(cursor_factory=cursor_factory)
                    if cursor_factory
                    else conn.cursor()
                )

                cursor.execute(query, params)

                if fetch_one:
                    result = cursor.fetchone()
                elif fetch_all:
                    result = cursor.fetchall()
                else:
                    result = cursor.rowcount

                cursor.close()
                self.return_connection(conn)
                return result

            except Exception as e:
                if conn:
                    try:
                        conn.rollback()
                        self.return_connection(conn)
                    except:
                        pass

                logger.warning(f"⚠️ Query attempt {attempt + 1} failed: {e}")
                if attempt < max_retries - 1:
                    time.sleep(1)
                else:
                    logger.error(f"❌ Query failed after {max_retries} attempts")
                    raise

    def get_users_needing_reminders(self) -> List[Dict]:
        """Get users who need reminders based on their last activity"""
        try:
            # Get users whose last activity is approaching 24 hours
            query = """
            SELECT
                u.id,
                u.phone_number,
                u.name,
                u.last_active,
                EXTRACT(EPOCH FROM (NOW() - u.last_active)) / 3600 as hours_elapsed,
                24 - EXTRACT(EPOCH FROM (NOW() - u.last_active)) / 3600 as hours_remaining,
                COALESCE(js.jobs_sent_today, 0) as jobs_sent_count
            FROM users u
            LEFT JOIN (
                SELECT
                    u2.phone_number as user_phone,
                    0 as jobs_sent_today
                FROM users u2
                WHERE 1=0  -- Always return 0 for now, will implement job tracking later
            ) js ON u.phone_number = js.user_phone
            WHERE
                u.is_active = true
                AND u.last_active > NOW() - INTERVAL '24 hours'
                AND EXTRACT(EPOCH FROM (NOW() - u.last_active)) / 3600 >= 2  -- Start reminders at 2 hours (for testing)
            ORDER BY u.last_active ASC
            """

            users = self.execute_with_retry(
                query, fetch_all=True, cursor_factory=psycopg2.extras.RealDictCursor
            )

            logger.info(f"📊 Found {len(users)} users needing reminders")
            return users

        except Exception as e:
            logger.error(f"❌ Error getting users for reminders: {e}")
            return []

    def should_send_reminder(self, hours_remaining: float, user_id: int) -> bool:
        """Check if we should send a reminder at this time"""
        try:
            # Check if we already sent a reminder for this time slot

            # Determine which reminder slot this falls into
            # Find the appropriate slot based on hours remaining
            reminder_slot = None

            # Sort schedule from smallest to largest
            sorted_schedule = sorted(self.reminder_schedule)

            for slot in sorted_schedule:
                if hours_remaining <= slot + 0.75:  # Within 45 minutes of slot
                    reminder_slot = slot
                    break

            if not reminder_slot:
                return False

            # Check if we already sent this reminder today
            query = """
            SELECT COUNT(*) FROM reminder_log
            WHERE user_id = %s
            AND reminder_type = %s
            AND DATE(sent_at) = CURRENT_DATE
            """

            result = self.execute_with_retry(
                query, (user_id, f"{reminder_slot}h_reminder"), fetch_one=True
            )
            count = result[0]

            return count == 0

        except Exception as e:
            logger.error(f"❌ Error checking reminder status: {e}")
            return False

    def get_progressive_reminder_message(
        self, hours_remaining: float, jobs_sent_count: int = 0
    ) -> str:
        """Get escalating reminder messages based on time remaining"""

        if hours_remaining >= 21.5 and hours_remaining <= 22.5:  # 22h reminder
            return (
                f"🧪 *TEST REMINDER - 22 Hours Remaining*\n\n"
                f"This is a test of the reminder system!\n"
                f"I've been monitoring for 2 hours.\n"
                f"Jobs sent so far: {jobs_sent_count} 📊\n\n"
                f"In production, this would be sent at 8 hours remaining.\n"
                f"Send any message to reset the 24-hour cycle! ⚡"
            )

        elif hours_remaining >= 19.5 and hours_remaining <= 20.5:  # 20h reminder
            return (
                f"🧪 *TEST REMINDER - 20 Hours Remaining*\n\n"
                f"I've been monitoring for 4 hours.\n"
                f"Jobs sent so far: {jobs_sent_count} 📊\n\n"
                f"Testing the reminder system at 20h remaining.\n"
                f"Send any message to reset the 24-hour cycle! ⚡"
            )

        elif hours_remaining >= 17.5 and hours_remaining <= 18.5:  # 18h reminder
            return (
                f"🧪 *TEST REMINDER - 18 Hours Remaining*\n\n"
                f"I've been monitoring for 6 hours.\n"
                f"Jobs sent so far: {jobs_sent_count} 📊\n\n"
                f"Testing the reminder system at 18h remaining.\n"
                f"Send any message to reset the 24-hour cycle! ⚡"
            )

        elif hours_remaining >= 15.5 and hours_remaining <= 16.5:  # 16h reminder
            return (
                f"🧪 *TEST REMINDER - 16 Hours Remaining*\n\n"
                f"I've been monitoring for 8 hours.\n"
                f"Jobs sent so far: {jobs_sent_count} 📊\n\n"
                f"Testing the reminder system at 16h remaining.\n"
                f"Send any message to reset the 24-hour cycle! ⚡"
            )

        elif hours_remaining >= 7.5 and hours_remaining <= 8.5:  # 8 hour reminder
            if jobs_sent_count > 0:
                return (
                    f"📊 *Market Update for you!*\n\n"
                    f"I've been actively monitoring job boards for 16 hours.\n"
                    f"Sent you {jobs_sent_count} quality matches so far! 🎯\n\n"
                    f"I've got 8 more hours of **real-time alerts** left.\n"
                    f"Drop me a message anytime to reset my 24-hour cycle! ⚡"
                )
            else:
                return (
                    f"📊 *Market Update for you!*\n\n"
                    f"I've been actively monitoring for 16 hours.\n"
                    f"No perfect matches yet, but I'm still hunting! 🔍\n\n"
                    f"I've got 8 more hours of **real-time alerts** left.\n"
                    f"Send me a message anytime to reset my 24-hour cycle! ⚡"
                )

        elif hours_remaining >= 4.5 and hours_remaining <= 5.5:  # 5 hour reminder
            return (
                f"🤖 *Your job-hunting buddy checking in!*\n\n"
                f"I've been working for 19 hours straight!\n"
                f"Delivered {jobs_sent_count} matches to your WhatsApp 📱\n\n"
                f"I've got 5 hours left of **instant notifications**\n"
                f"(You can still see jobs when I sleep, but no real-time alerts! 😴)"
            )

        elif hours_remaining >= 2.5 and hours_remaining <= 3.5:  # 3 hour reminder
            return (
                f"⚠️ *Don't miss out!*\n\n"
                f"Only 3 hours left of **instant job alerts**! ⏰\n\n"
                f"When I sleep:\n"
                f"✅ You can still request jobs ('show me jobs')\n"
                f"❌ But no automatic real-time notifications\n"
                f"❌ Other candidates get alerts first\n\n"
                f"Send ANY message to keep instant alerts active! 🚀"
            )

        elif hours_remaining >= 0.5 and hours_remaining <= 1.5:  # 1 hour reminder
            return (
                f"🔋 *FINAL HOUR ALERT!*\n\n"
                f"Just 1 hour left of **instant notifications**! 😰\n\n"
                f"After I sleep:\n"
                f"📱 No automatic job alerts\n"
                f"🏃‍♂️ You'll need to manually ask for jobs\n"
                f"⚡ Others get the speed advantage\n\n"
                f"**Quick!** Send 'stay awake' or any message!"
            )

        else:  # 15 minutes remaining
            return (
                f"🚨 *LAST CALL - 15 MINUTES!*\n\n"
                f"This is it! **Instant alerts** shutting down! 😱\n\n"
                f"⏰ 15 minutes to save automatic notifications\n"
                f"⏰ 15 minutes to stay ahead of competition\n\n"
                f"**SEND ANY MESSAGE NOW!**\n"
                f"(You can still get jobs when I sleep, but no auto-alerts!) 🆘"
            )

    def log_reminder_sent(
        self, user_id: int, reminder_type: str, hours_remaining: float
    ):
        """Log that a reminder was sent"""
        try:
            query = """
            INSERT INTO reminder_log (user_id, reminder_type, hours_remaining, sent_at)
            VALUES (%s, %s, %s, NOW())
            """

            self.execute_with_retry(query, (user_id, reminder_type, hours_remaining))

        except Exception as e:
            logger.error(f"❌ Error logging reminder: {e}")

    def send_reminder(self, user: Dict) -> bool:
        """Send reminder to a specific user"""
        try:
            hours_remaining = user["hours_remaining"]

            if not self.should_send_reminder(hours_remaining, user["id"]):
                return False

            message = self.get_progressive_reminder_message(
                hours_remaining, user["jobs_sent_count"]
            )

            # Send the reminder
            success = self.whatsapp_service.send_message(user["phone_number"], message)

            if success:
                # Log the reminder
                reminder_type = f"{int(hours_remaining)}h_reminder"
                self.log_reminder_sent(user["id"], reminder_type, hours_remaining)

                logger.info(f"✅ Sent {reminder_type} to {user['phone_number']}")
                return True
            else:
                logger.error(f"❌ Failed to send reminder to {user['phone_number']}")
                return False

        except Exception as e:
            logger.error(f"❌ Error sending reminder: {e}")
            return False

    def run_reminder_cycle(self):
        """Run one cycle of reminder checking and sending"""
        logger.info("🔄 Starting reminder cycle...")

        users = self.get_users_needing_reminders()
        sent_count = 0

        for user in users:
            if self.send_reminder(user):
                sent_count += 1
                time.sleep(1)  # Rate limiting

        logger.info(f"📤 Sent {sent_count} reminders in this cycle")
        return sent_count

    def create_reminder_log_table(self):
        """Create reminder log table if it doesn't exist"""
        try:
            # Create table with IF NOT EXISTS to avoid conflicts
            query = """
            CREATE TABLE IF NOT EXISTS reminder_log (
                id SERIAL PRIMARY KEY,
                user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
                reminder_type VARCHAR(50) NOT NULL,
                hours_remaining DECIMAL(4,2),
                sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """

            self.execute_with_retry(query)

            # Create index separately to handle existing indexes gracefully
            index_query = """
            CREATE INDEX IF NOT EXISTS idx_reminder_log_user_date
            ON reminder_log(user_id, DATE(sent_at));
            """

            self.execute_with_retry(index_query)
            logger.info("✅ Reminder log table ready")

        except Exception as e:
            # Log the error but don't crash - table might already exist
            logger.warning(f"⚠️ Reminder log table setup: {e}")
            logger.info("📋 Continuing - table likely already exists")

    def check_table_status(self):
        """Check if reminder_log table exists and is accessible"""
        try:
            # Check if table exists
            result = self.execute_with_retry(
                """
                SELECT EXISTS (
                    SELECT FROM information_schema.tables
                    WHERE table_name = 'reminder_log'
                );
                """,
                fetch_one=True,
            )

            table_exists = result[0]

            if table_exists:
                # Check table structure
                count_result = self.execute_with_retry(
                    "SELECT COUNT(*) FROM reminder_log;", fetch_one=True
                )
                count = count_result[0]
                logger.info(f"✅ reminder_log table exists with {count} records")
            else:
                logger.warning("⚠️ reminder_log table does not exist")

            return table_exists

        except Exception as e:
            logger.error(f"❌ Error checking table status: {e}")
            return False
