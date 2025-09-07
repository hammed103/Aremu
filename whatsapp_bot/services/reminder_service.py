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
        self.reminder_schedule = [
            8,  # 8 hours remaining - main market update
            5,  # 5 hours remaining - buddy check-in
            3,  # 3 hours remaining - don't miss out
            1,  # 1 hour remaining - final hour alert
            0.25,  # 15 minutes remaining - last call
        ]

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
                    u2.id as user_id,
                    COUNT(ujh.id) as jobs_sent_today
                FROM users u2
                LEFT JOIN user_job_history ujh ON u2.id = ujh.user_id
                    AND DATE(ujh.shown_at) = CURRENT_DATE
                    AND ujh.message_sent = TRUE
                GROUP BY u2.id
            ) js ON u.id = js.user_id
            WHERE
                u.is_active = true
                AND u.last_active > NOW() - INTERVAL '24 hours'
                AND EXTRACT(EPOCH FROM (NOW() - u.last_active)) / 3600 >= 8  -- Start reminders at 8 hours
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

    def get_reminder_slot(self, hours_remaining: float) -> float:
        """Get the appropriate reminder slot for the given hours remaining"""
        # Use clear ranges that don't overlap and cover all cases
        if hours_remaining <= 0.5:  # 0-30 minutes
            return 0.25
        elif 0.5 < hours_remaining <= 1.5:  # 30 minutes - 1.5 hours
            return 1
        elif 1.5 < hours_remaining <= 4:  # 1.5 - 4 hours
            return 3
        elif 4 < hours_remaining <= 6.5:  # 4 - 6.5 hours
            return 5
        elif 6.5 < hours_remaining <= 24:  # 6.5 - 24 hours
            return 8
        else:
            return None

    def should_send_reminder(self, hours_remaining: float, user_id: int) -> bool:
        """Check if we should send a reminder at this time"""
        try:
            # Get the appropriate reminder slot
            reminder_slot = self.get_reminder_slot(hours_remaining)

            if not reminder_slot:
                return False

            # Check if we already sent this reminder recently (within last 2 hours)
            query = """
            SELECT COUNT(*) FROM reminder_log
            WHERE user_id = %s
            AND reminder_type = %s
            AND sent_at > NOW() - INTERVAL '2 hours'
            """

            result = self.execute_with_retry(
                query, (user_id, f"{reminder_slot}h_reminder"), fetch_one=True
            )
            count = result[0]

            if count > 0:
                logger.info(
                    f"⏭️ Skipping {reminder_slot}h reminder for user {user_id} - already sent recently"
                )
                return False

            return True

        except Exception as e:
            logger.error(f"❌ Error checking reminder status: {e}")
            return False

    def get_progressive_reminder_message(
        self, hours_remaining: float, jobs_sent_count: int = 0, hours_elapsed: float = 0
    ) -> str:
        """Get escalating reminder messages based on time remaining"""

        # Calculate monitoring hours (24 - hours_remaining)
        monitoring_hours = int(24 - hours_remaining)

        if hours_remaining > 6.5:  # 8 hour reminder (6.5-24 hours)
            if jobs_sent_count > 0:
                return (
                    f"📊 *Market Update for you!*\n\n"
                    f"I've been actively monitoring job boards for {monitoring_hours} hours.\n"
                    f"Sent you {jobs_sent_count} quality matches so far! 🎯\n\n"
                    f"I've got 8 more hours of *real-time alerts* left.\n"
                    f"Click 'Stay Active' below to keep me hunting! ⚡"
                )
            else:
                return (
                    f"📊 *Market Update for you!*\n\n"
                    f"I've been actively monitoring for {monitoring_hours} hours.\n"
                    f"No perfect matches yet, but I'm still hunting! 🔍\n\n"
                    f"I've got 8 more hours of *real-time alerts* left.\n"
                    f"Click 'Stay Active' below to keep me hunting! ⚡"
                )

        elif 4 < hours_remaining <= 6.5:  # 5 hour reminder (4-6.5 hours)
            return (
                f"👋 *Quick check-in!*\n\n"
                f"I've been monitoring for {monitoring_hours} hours now.\n"
                f"Found {jobs_sent_count} matches for you! 🎯\n\n"
                f"I have 5 more hours of instant alerts remaining.\n"
                f"Click 'Stay Active' to continue getting real-time job alerts! ⚡"
            )

        elif 1.5 < hours_remaining <= 4:  # 3 hour reminder (1.5-4 hours)
            return (
                f"⏰ *3 hours remaining*\n\n"
                f"I have 3 hours left of instant job alerts.\n\n"
                f"After this period:\n"
                f"✅ You can still request jobs anytime\n"
                f"📱 Just ask me 'show me jobs' whenever you want\n"
                f"⚡ But automatic alerts will pause\n\n"
                f"Click 'Stay Active' to continue instant notifications! 🚀"
            )

        elif 0.5 < hours_remaining <= 1.5:  # 1 hour reminder (0.5-1.5 hours)
            return (
                f"🔔 *1 hour remaining*\n\n"
                f"I have 1 hour left of instant notifications.\n\n"
                f"After this:\n"
                f"📱 You can still get jobs by asking me\n"
                f"💬 Just say 'show me jobs' anytime\n"
                f"⏸️ Automatic alerts will pause\n\n"
                f"Click 'Stay Active' to continue! ⚡"
            )

        else:  # 15 minutes remaining
            # Calculate actual minutes remaining
            minutes_remaining = int(hours_remaining * 60)

            return (
                f"🚨 *FINAL ALERT - {minutes_remaining} MINUTES LEFT!*\n\n"
                f"Your 24-hour window is almost up! ⏰\n\n"
                f"⚡ {minutes_remaining} minutes to extend instant notifications\n"
                f"📱 After this, you'll need to manually request jobs\n\n"
                f"**Click 'Stay Active' to continue!** 👆\n"
                f"(Don't worry - you can always ask me for jobs later! 😊)"
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
        """Send reminder to a specific user with database-level duplicate prevention"""
        user_id = user["id"]
        hours_remaining = user["hours_remaining"]

        # Create a unique lock ID for this user and reminder type
        reminder_slot = self.get_reminder_slot(hours_remaining)
        if not reminder_slot:
            logger.warning(f"⚠️ No reminder slot found for {hours_remaining}h remaining")
            return False

        lock_id = (
            hash(f"{user_id}_{reminder_slot}") % 2147483647
        )  # PostgreSQL int limit

        try:
            # Use PostgreSQL advisory lock to prevent concurrent reminders
            lock_query = "SELECT pg_try_advisory_lock(%s)"
            lock_result = self.execute_with_retry(
                lock_query, (lock_id,), fetch_one=True
            )

            if not lock_result[0]:  # Failed to acquire lock
                logger.info(
                    f"🔒 Lock failed: Another reminder process active for user {user_id}"
                )
                return False

            try:
                hours_elapsed = user.get("hours_elapsed", 0)

                if not self.should_send_reminder(hours_remaining, user_id):
                    return False

                # Final duplicate check with lock held
                reminder_type = f"{reminder_slot}h_reminder"

                check_query = """
                SELECT COUNT(*) FROM reminder_log
                WHERE user_id = %s
                AND reminder_type = %s
                AND sent_at > NOW() - INTERVAL '15 minutes'
                """

                check_result = self.execute_with_retry(
                    check_query, (user_id, reminder_type), fetch_one=True
                )

                if check_result[0] > 0:
                    logger.info(
                        f"⏭️ Final duplicate check: Skipping {reminder_type} for user {user_id}"
                    )
                    return False

                message = self.get_progressive_reminder_message(
                    hours_remaining, user["jobs_sent_count"], hours_elapsed
                )

                # Send the reminder with Stay Active button
                success = self.whatsapp_service.send_reminder_with_stay_active_button(
                    user["phone_number"], message
                )

                if success:
                    # Log the reminder immediately
                    self.log_reminder_sent(user_id, reminder_type, hours_remaining)
                    logger.info(f"✅ Sent {reminder_type} to {user['phone_number']}")
                    return True
                else:
                    logger.error(
                        f"❌ Failed to send reminder to {user['phone_number']}"
                    )
                    return False

            finally:
                # Always release the lock
                unlock_query = "SELECT pg_advisory_unlock(%s)"
                self.execute_with_retry(unlock_query, (lock_id,))

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
