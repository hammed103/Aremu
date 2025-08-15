#!/usr/bin/env python3
"""
Database manager for Aremu WhatsApp Bot
Handles user management, preferences, and conversation history
"""

import os
import psycopg2
import psycopg2.extras
import json
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import logging

logger = logging.getLogger(__name__)


class DatabaseManager:
    def __init__(self):
        """Initialize database connection"""
        self.connection = None
        self.user_cache = {}  # Cache user info to avoid repeated queries
        self.connect()

    def connect(self):
        """Connect to PostgreSQL database"""
        try:
            # Use the same database config as your data parser
            database_url = "postgresql://postgres.upnvhpgaljazlsoryfgj:prAlkIpbQDqOZtOj@aws-0-us-east-1.pooler.supabase.com:6543/postgres"
            self.connection = psycopg2.connect(database_url)
            self.connection.autocommit = True
            logger.info("✅ Database connected successfully")
        except Exception as e:
            logger.error(f"❌ Database connection failed: {e}")
            raise

    def ensure_tables_exist(self):
        """Create tables if they don't exist"""
        try:
            with open("database_schema.sql", "r") as f:
                schema_sql = f.read()

            cursor = self.connection.cursor()
            cursor.execute(schema_sql)
            logger.info("✅ Database tables ensured")
        except Exception as e:
            logger.error(f"❌ Failed to create tables: {e}")

    def get_or_create_user(self, phone_number: str, name: str = None) -> int:
        """Get existing user or create new one"""
        try:
            cursor = self.connection.cursor()

            # Try to get existing user
            cursor.execute(
                "SELECT id, name FROM users WHERE phone_number = %s", (phone_number,)
            )
            result = cursor.fetchone()

            if result:
                user_id = result[0]
                # Update last active and increment message count
                cursor.execute(
                    """UPDATE users 
                       SET last_active = CURRENT_TIMESTAMP, 
                           message_count = message_count + 1,
                           name = COALESCE(%s, name)
                       WHERE id = %s""",
                    (name, user_id),
                )
                logger.info(f"📱 Updated existing user {phone_number}")
                return user_id
            else:
                # Create new user
                cursor.execute(
                    """INSERT INTO users (phone_number, name) 
                       VALUES (%s, %s) RETURNING id""",
                    (phone_number, name),
                )
                user_id = cursor.fetchone()[0]
                logger.info(f"👤 Created new user {phone_number}")
                return user_id

        except Exception as e:
            logger.error(f"❌ Error managing user {phone_number}: {e}")
            return None

    def save_conversation_message(
        self, user_id: int, message_type: str, content: str, session_id: str = None
    ) -> bool:
        """Save a conversation message"""
        try:
            if not session_id:
                session_id = str(uuid.uuid4())

            cursor = self.connection.cursor()

            # Get message order for this session
            cursor.execute(
                "SELECT COALESCE(MAX(message_order), 0) + 1 FROM conversations WHERE session_id = %s",
                (session_id,),
            )
            message_order = cursor.fetchone()[0]

            # Insert message
            cursor.execute(
                """INSERT INTO conversations 
                   (user_id, message_type, message_content, session_id, message_order)
                   VALUES (%s, %s, %s, %s, %s)""",
                (user_id, message_type, content, session_id, message_order),
            )

            # Update session
            cursor.execute(
                """INSERT INTO user_sessions (user_id, session_id, last_message_at, message_count)
                   VALUES (%s, %s, CURRENT_TIMESTAMP, 1)
                   ON CONFLICT (session_id) 
                   DO UPDATE SET 
                       last_message_at = CURRENT_TIMESTAMP,
                       message_count = user_sessions.message_count + 1""",
                (user_id, session_id),
            )

            return True

        except Exception as e:
            logger.error(f"❌ Error saving conversation: {e}")
            return False

    def get_conversation_history(self, user_id: int, limit: int = 20) -> List[Dict]:
        """Get recent conversation history for a user"""
        try:
            cursor = self.connection.cursor(
                cursor_factory=psycopg2.extras.RealDictCursor
            )

            cursor.execute(
                """SELECT message_type, message_content, timestamp
                   FROM conversations 
                   WHERE user_id = %s 
                   ORDER BY timestamp DESC 
                   LIMIT %s""",
                (user_id, limit),
            )

            messages = cursor.fetchall()
            # Reverse to get chronological order
            return [
                {"role": msg["message_type"], "content": msg["message_content"]}
                for msg in reversed(messages)
            ]

        except Exception as e:
            logger.error(f"❌ Error getting conversation history: {e}")
            return []

    def extract_and_save_preferences(
        self, user_id: int, message: str, ai_response: str = None
    ):
        """Extract job preferences and name from user message and save them (optimized)"""
        try:
            # Only extract if message contains potential preference keywords
            if self.should_extract_preferences(message):
                preferences = self.extract_preferences_from_text(message)
                if preferences:
                    self.save_user_preferences(user_id, preferences)
                    logger.info(
                        f"💾 Saved preferences for user {user_id}: {preferences}"
                    )

            # Only extract name if user doesn't have one and message might contain a name
            if self.should_extract_name(user_id, message):
                name = self.extract_name_from_text(message)
                if name:
                    self.update_user_name(user_id, name)
                    logger.info(f"👤 Saved name for user {user_id}: {name}")

        except Exception as e:
            logger.error(f"❌ Error extracting preferences/name: {e}")

    def should_extract_preferences(self, message: str) -> bool:
        """Check if message likely contains preferences to avoid unnecessary processing"""
        preference_keywords = [
            "job",
            "work",
            "role",
            "position",
            "full-time",
            "part-time",
            "remote",
            "dollar",
            "naira",
            "usd",
            "ngn",
            "software",
            "customer",
            "marketing",
            "sales",
            "design",
            "data",
            "lagos",
            "abuja",
            "hybrid",
            "contract",
        ]
        message_lower = message.lower()
        return any(keyword in message_lower for keyword in preference_keywords)

    def should_extract_name(self, user_id: int, message: str) -> bool:
        """Check if we should try to extract name (only if user doesn't have one)"""
        try:
            # Check cache first
            if user_id in self.user_cache and self.user_cache[user_id].get("name"):
                return False

            # Check database if not in cache
            cursor = self.connection.cursor()
            cursor.execute("SELECT name FROM users WHERE id = %s", (user_id,))
            result = cursor.fetchone()

            # Update cache
            if user_id not in self.user_cache:
                self.user_cache[user_id] = {}
            self.user_cache[user_id]["name"] = (
                result[0] if result and result[0] else None
            )

            # Only extract if no name exists and message might contain name patterns
            if not result or not result[0]:
                name_keywords = [
                    "name",
                    "i'm",
                    "i am",
                    "call me",
                    "this is",
                    "hi,",
                    "hello,",
                ]
                message_lower = message.lower()
                return any(keyword in message_lower for keyword in name_keywords)

            return False
        except Exception as e:
            logger.error(f"❌ Error checking if should extract name: {e}")
            return False

    def extract_preferences_from_text(self, text: str) -> Dict:
        """Extract preferences from user message using keywords"""
        text_lower = text.lower()
        preferences = {}

        # Job types
        job_types = {
            "software developer": ["software", "developer", "programming", "coding"],
            "customer service": ["customer service", "support", "help desk"],
            "data analyst": ["data analyst", "data science", "analytics"],
            "marketing": ["marketing", "digital marketing", "social media"],
            "sales": ["sales", "business development"],
            "designer": ["designer", "graphic design", "ui/ux"],
        }

        for job_type, keywords in job_types.items():
            if any(keyword in text_lower for keyword in keywords):
                preferences["job_type"] = job_type
                break

        # Employment type
        if any(word in text_lower for word in ["full-time", "fulltime", "full time"]):
            preferences["employment_type"] = "Full-time"
        elif any(word in text_lower for word in ["part-time", "parttime", "part time"]):
            preferences["employment_type"] = "Part-time"
        elif "contract" in text_lower:
            preferences["employment_type"] = "Contract"

        # Currency
        if any(word in text_lower for word in ["dollar", "usd", "$"]):
            preferences["salary_currency"] = "USD"
        elif any(word in text_lower for word in ["naira", "ngn", "₦"]):
            preferences["salary_currency"] = "NGN"

        # Location
        if "remote" in text_lower:
            preferences["location_preference"] = "Remote"
        elif "hybrid" in text_lower:
            preferences["location_preference"] = "Hybrid"
        elif any(
            city in text_lower for city in ["lagos", "abuja", "port harcourt", "kano"]
        ):
            for city in ["lagos", "abuja", "port harcourt", "kano"]:
                if city in text_lower:
                    preferences["location_preference"] = city.title()
                    break

        return preferences

    def extract_name_from_text(self, text: str) -> str:
        """Extract user name from message using common patterns"""
        import re

        text = text.strip()

        # Common name introduction patterns
        name_patterns = [
            r"my name is ([A-Za-z\s]+)",
            r"name is ([A-Za-z\s]+)",
            r"i'm ([A-Za-z\s]+)",
            r"i am ([A-Za-z\s]+)",
            r"call me ([A-Za-z\s]+)",
            r"this is ([A-Za-z\s]+)",
            r"^([A-Za-z\s]+) here",
            r"hi,?\s*i'?m\s+([A-Za-z\s]+)",
            r"hello,?\s*i'?m\s+([A-Za-z\s]+)",
            r"hi,?\s*my name is ([A-Za-z\s]+)",
            r"hello,?\s*my name is ([A-Za-z\s]+)",
        ]

        for pattern in name_patterns:
            match = re.search(pattern, text.lower())
            if match:
                name = match.group(1).strip().title()
                # Validate name (2-50 chars, only letters and spaces)
                if 2 <= len(name) <= 50 and re.match(r"^[A-Za-z\s]+$", name):
                    # Remove common non-name words
                    non_names = [
                        "looking",
                        "searching",
                        "interested",
                        "want",
                        "need",
                        "here",
                        "good",
                    ]
                    if not any(word in name.lower() for word in non_names):
                        return name

        return None

    def update_user_name(self, user_id: int, name: str):
        """Update user name in database"""
        try:
            cursor = self.connection.cursor()
            # Check current name first
            cursor.execute("SELECT name FROM users WHERE id = %s", (user_id,))
            current_name = cursor.fetchone()

            # Only update if name is different (avoid unnecessary updates)
            if not current_name or current_name[0] != name:
                cursor.execute(
                    "UPDATE users SET name = %s WHERE id = %s",
                    (name, user_id),
                )
                if cursor.rowcount > 0:
                    logger.info(
                        f"👤 Updated name for user {user_id}: {current_name[0] if current_name else 'NULL'} → {name}"
                    )
            else:
                logger.info(f"👤 Name already correct for user {user_id}: {name}")
        except Exception as e:
            logger.error(f"❌ Error updating user name: {e}")

    def save_user_preferences(self, user_id: int, preferences: Dict):
        """Save or update user preferences"""
        try:
            cursor = self.connection.cursor()

            # Check if preferences exist
            cursor.execute(
                "SELECT id FROM user_preferences WHERE user_id = %s", (user_id,)
            )
            existing = cursor.fetchone()

            if existing:
                # Update existing preferences
                update_fields = []
                values = []
                for key, value in preferences.items():
                    update_fields.append(f"{key} = %s")
                    values.append(value)

                if update_fields:
                    values.append(user_id)
                    cursor.execute(
                        f"UPDATE user_preferences SET {', '.join(update_fields)} WHERE user_id = %s",
                        values,
                    )
            else:
                # Insert new preferences
                fields = list(preferences.keys()) + ["user_id"]
                values = list(preferences.values()) + [user_id]
                placeholders = ", ".join(["%s"] * len(values))

                cursor.execute(
                    f"INSERT INTO user_preferences ({', '.join(fields)}) VALUES ({placeholders})",
                    values,
                )

        except Exception as e:
            logger.error(f"❌ Error saving preferences: {e}")

    def get_user_preferences(self, user_id: int) -> Dict:
        """Get user preferences"""
        try:
            cursor = self.connection.cursor(
                cursor_factory=psycopg2.extras.RealDictCursor
            )
            cursor.execute(
                "SELECT * FROM user_preferences WHERE user_id = %s", (user_id,)
            )
            result = cursor.fetchone()
            return dict(result) if result else {}
        except Exception as e:
            logger.error(f"❌ Error getting preferences: {e}")
            return {}

    def close(self):
        """Close database connection"""
        if self.connection:
            self.connection.close()
            logger.info("🔌 Database connection closed")
