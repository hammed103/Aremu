#!/usr/bin/env python3
"""
Database manager for Aremu WhatsApp Bot
Handles user management, preferences, and conversation history
"""

import os
import psycopg2
import psycopg2.extras
from psycopg2 import pool
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import logging
import time
import json
import re

logger = logging.getLogger(__name__)


class DatabaseManager:
    def __init__(self):
        """Initialize database connection pool"""
        self.connection_pool = None
        self.user_cache = {}  # Cache user info to avoid repeated queries
        self.database_url = "postgresql://postgres.upnvhpgaljazlsoryfgj:prAlkIpbQDqOZtOj@aws-0-us-east-1.pooler.supabase.com:6543/postgres"
        self.connect()

    def connect(self):
        """Create connection pool for PostgreSQL database"""
        try:
            self.connection_pool = psycopg2.pool.ThreadedConnectionPool(
                minconn=1,
                maxconn=10,
                dsn=self.database_url,
                keepalives=1,
                keepalives_idle=30,
                keepalives_interval=10,
                keepalives_count=5,
            )
            logger.info("✅ Database connection pool created successfully")
        except Exception as e:
            logger.error(f"❌ Database connection pool creation failed: {e}")
            raise

    def get_connection(self):
        """Get a connection from the pool with retry logic"""
        max_retries = 3
        for attempt in range(max_retries):
            try:
                if not self.connection_pool:
                    self.connect()

                conn = self.connection_pool.getconn()
                if conn:
                    conn.autocommit = True
                    return conn
                else:
                    raise Exception("Failed to get connection from pool")

            except Exception as e:
                logger.warning(f"⚠️ Connection attempt {attempt + 1} failed: {e}")
                if attempt < max_retries - 1:
                    time.sleep(1)  # Wait before retry
                    try:
                        # Try to recreate the pool
                        if self.connection_pool:
                            self.connection_pool.closeall()
                        self.connect()
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
                    logger.error(
                        f"❌ Query failed after {max_retries} attempts: {query}"
                    )
                    raise

    def ensure_tables_exist(self):
        """Create tables if they don't exist"""
        try:
            # Try different possible paths for the schema file
            schema_paths = [
                "config/database_schema.sql",
                "database_schema.sql",
                "../database/raw_jobs_schema.sql",
            ]

            schema_sql = None
            for path in schema_paths:
                try:
                    with open(path, "r") as f:
                        schema_sql = f.read()
                    break
                except FileNotFoundError:
                    continue

            if not schema_sql:
                logger.warning(
                    "⚠️ Database schema file not found, skipping table creation"
                )
                return

            self.execute_with_retry(schema_sql)
            logger.info("✅ Database tables ensured")
        except Exception as e:
            logger.error(f"❌ Failed to create tables: {e}")

    def get_or_create_user(self, phone_number: str, name: str = None) -> int:
        """Get existing user or create new one"""
        try:
            # Try to get existing user
            result = self.execute_with_retry(
                "SELECT id, name FROM users WHERE phone_number = %s",
                (phone_number,),
                fetch_one=True,
            )

            if result:
                user_id = result[0]
                # Update last active and increment message count
                self.execute_with_retry(
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
                result = self.execute_with_retry(
                    """INSERT INTO users (phone_number, name)
                       VALUES (%s, %s) RETURNING id""",
                    (phone_number, name),
                    fetch_one=True,
                )
                user_id = result[0]
                logger.info(f"👤 Created new user {phone_number}")
                return user_id

        except Exception as e:
            logger.error(f"❌ Error managing user {phone_number}: {e}")
            return None

    def update_user_activity(self, user_id: int) -> bool:
        """Update user's last_active timestamp (critical for 24-hour window tracking)"""
        try:
            self.execute_with_retry(
                "UPDATE users SET last_active = CURRENT_TIMESTAMP WHERE id = %s",
                (user_id,),
            )
            return True
        except Exception as e:
            logger.error(f"❌ Error updating user activity: {e}")
            return False

    def save_conversation_message(
        self, user_id: int, message_type: str, content: str, session_id: str = None
    ) -> bool:
        """Save a conversation message"""
        try:
            if not session_id:
                session_id = str(uuid.uuid4())

            # Get message order for this session
            message_order = self.execute_with_retry(
                "SELECT COALESCE(MAX(message_order), 0) + 1 FROM conversations WHERE session_id = %s",
                (session_id,),
                fetch_one=True,
            )[0]

            # Insert message
            self.execute_with_retry(
                """INSERT INTO conversations
                   (user_id, message_type, message_content, session_id, message_order)
                   VALUES (%s, %s, %s, %s, %s)""",
                (user_id, message_type, content, session_id, message_order),
            )

            # Update session
            self.execute_with_retry(
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
            messages = self.execute_with_retry(
                """SELECT message_type, message_content, timestamp
                   FROM conversations
                   WHERE user_id = %s
                   ORDER BY timestamp DESC
                   LIMIT %s""",
                (user_id, limit),
                fetch_all=True,
                cursor_factory=psycopg2.extras.RealDictCursor,
            )

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

    def search_jobs_for_user(self, user_id: int, limit: int = 5) -> List[Dict]:
        """Get recent jobs matching user preferences"""
        try:
            # Get user preferences
            preferences = self.get_user_preferences(user_id)

            if not preferences:
                logger.info(f"No preferences found for user {user_id}")
                return []

            logger.info(f"User {user_id} preferences: {preferences}")

            # Build dynamic query based on available preferences
            where_conditions = []
            params = []

            # Job type matching (most important)
            if preferences.get("job_type"):
                where_conditions.append(
                    """
                    (LOWER(title) LIKE %s
                     OR LOWER(ai_job_function) LIKE %s
                     OR LOWER(description) LIKE %s)
                """
                )
                job_type_pattern = f"%{preferences['job_type'].lower()}%"
                params.extend([job_type_pattern, job_type_pattern, job_type_pattern])

            # Location preference
            if preferences.get("location_preference"):
                location = preferences["location_preference"].lower()
                if location == "remote":
                    where_conditions.append(
                        "(ai_remote_allowed = true OR remote_allowed = true OR LOWER(location) LIKE %s)"
                    )
                    params.append("%remote%")
                else:
                    where_conditions.append("LOWER(location) LIKE %s")
                    params.append(f"%{location}%")

            # Employment type
            if preferences.get("employment_type"):
                where_conditions.append(
                    "(LOWER(employment_type) LIKE %s OR LOWER(ai_employment_type) LIKE %s)"
                )
                emp_type_pattern = f"%{preferences['employment_type'].lower()}%"
                params.extend([emp_type_pattern, emp_type_pattern])

            # Salary preferences
            if preferences.get("salary_min"):
                where_conditions.append("(salary_max >= %s OR ai_salary_max >= %s)")
                params.extend([preferences["salary_min"], preferences["salary_min"]])

            # Currency preference
            if preferences.get("salary_currency"):
                where_conditions.append(
                    "(salary_currency = %s OR ai_salary_currency = %s)"
                )
                currency = preferences["salary_currency"]
                params.extend([currency, currency])

            # Build final query
            where_clause = " AND ".join(where_conditions) if where_conditions else "1=1"

            query = f"""
                SELECT
                    c.id,
                    c.title,
                    c.company,
                    c.location,
                    c.description,
                    c.salary_min,
                    c.salary_max,
                    c.salary_currency,
                    c.employment_type,
                    c.job_url,
                    c.posted_date,
                    c.created_at as scraped_at,
                    -- AI fields
                    c.ai_salary_min,
                    c.ai_salary_max,
                    c.ai_salary_currency,
                    c.ai_employment_type,
                    c.ai_job_level,
                    c.ai_remote_allowed,
                    c.ai_required_skills,
                    c.ai_summary,
                    c.ai_compensation_summary,
                    c.email,
                    c.whatsapp_number,
                    c.ai_email,
                    c.ai_whatsapp_number
                FROM canonical_jobs c
                WHERE {where_clause}
                ORDER BY
                    COALESCE(c.posted_date, c.date_posted, c.created_at) DESC,
                    c.created_at DESC
                LIMIT %s
            """

            params.append(limit)

            cursor = self.connection.cursor(
                cursor_factory=psycopg2.extras.RealDictCursor
            )
            cursor.execute(query, params)
            jobs = cursor.fetchall()

            logger.info(
                f"Found {len(jobs)} jobs for user {user_id} with preferences: {preferences}"
            )
            return [dict(job) for job in jobs]

        except Exception as e:
            logger.error(f"❌ Error searching jobs for user {user_id}: {e}")
            import traceback

            logger.error(traceback.format_exc())
            return []

    def search_jobs_simple(self, user_id: int, limit: int = 5) -> List[Dict]:
        """COMPREHENSIVE multi-field, multi-level job search using ALL available data"""
        try:
            # Get user preferences
            preferences = self.get_user_preferences(user_id)

            if not preferences:
                logger.info(f"No preferences found for user {user_id}")
                return []

            # Extract all possible search criteria (safely handle None values)
            job_type = (preferences.get("job_type") or "").lower()
            employment_type = (preferences.get("employment_type") or "").lower()
            location_pref = (preferences.get("location_preference") or "").lower()
            salary_min = preferences.get("salary_min")
            salary_max = preferences.get("salary_max")
            remote_pref = (preferences.get("remote_preference") or "").lower()
            experience_years = preferences.get("experience_years")

            if not job_type:
                logger.info("No job type specified")
                return []

            # Expand job_type to include related terms for better matching
            job_search_terms = [job_type]

            # Add comprehensive related terms for intelligent fuzzy matching
            job_type_lower = job_type.lower()
            if "software" in job_type_lower or "developer" in job_type_lower:
                job_search_terms.extend(
                    [
                        "developer",
                        "engineer",
                        "programmer",
                        "software",
                        "frontend",
                        "backend",
                        "fullstack",
                        "full-stack",
                        "web developer",
                        "mobile developer",
                        "ui",
                        "ux",
                        "react",
                        "javascript",
                        "python",
                        "java",
                        "coding",
                        "programming",
                    ]
                )
            elif "sales" in job_type_lower or "business development" in job_type_lower:
                job_search_terms.extend(
                    [
                        "sales",
                        "business",
                        "manager",
                        "representative",
                        "account",
                        "client",
                        "customer",
                        "revenue",
                        "growth",
                        "bd",
                        "business development",
                    ]
                )
            elif "product" in job_type_lower and "manager" in job_type_lower:
                job_search_terms.extend(
                    [
                        "product manager",
                        "product",
                        "manager",
                        "coordinator",
                        "lead",
                        "strategy",
                        "roadmap",
                        "feature",
                        "user experience",
                        "pm",
                    ]
                )
            elif "analyst" in job_type_lower:
                job_search_terms.extend(
                    [
                        "analyst",
                        "analysis",
                        "data",
                        "business",
                        "research",
                        "insights",
                        "reporting",
                        "analytics",
                        "intelligence",
                    ]
                )
            elif "marketing" in job_type_lower:
                job_search_terms.extend(
                    [
                        "marketing",
                        "digital",
                        "social",
                        "content",
                        "campaign",
                        "brand",
                        "advertising",
                        "promotion",
                        "seo",
                        "sem",
                    ]
                )

            # Remove duplicates and empty strings
            job_search_terms = list(
                set(term.strip() for term in job_search_terms if term.strip())
            )

            # ULTIMATE COMPREHENSIVE multi-field, multi-level, multi-criteria matching query
            conditions = []
            params = []

            # Build dynamic WHERE conditions based on user preferences
            base_conditions = []

            # 1. JOB TYPE/TITLE MATCHING (most important) - Use expanded search terms
            if job_search_terms:
                all_job_conditions = []
                for search_term in job_search_terms:
                    job_conditions = [
                        "LOWER(c.title) LIKE %s",
                        "LOWER(c.description) LIKE %s",
                        "LOWER(c.ai_job_function) LIKE %s",
                        "EXISTS (SELECT 1 FROM unnest(c.ai_job_titles) AS job_title WHERE LOWER(job_title) LIKE %s)",
                        "EXISTS (SELECT 1 FROM unnest(c.ai_required_skills) AS skill WHERE LOWER(skill) LIKE %s)",
                        "EXISTS (SELECT 1 FROM unnest(c.ai_preferred_skills) AS skill WHERE LOWER(skill) LIKE %s)",
                        "EXISTS (SELECT 1 FROM unnest(c.ai_industry) AS industry WHERE LOWER(industry) LIKE %s)",
                        "EXISTS (SELECT 1 FROM unnest(c.ai_job_level) AS level WHERE LOWER(level) LIKE %s)",
                    ]
                    all_job_conditions.append(f"({' OR '.join(job_conditions)})")
                    search_pattern = f"%{search_term}%"
                    params.extend([search_pattern] * 8)

                # Combine all search terms with OR
                base_conditions.append(f"({' OR '.join(all_job_conditions)})")

            # 2. EMPLOYMENT TYPE MATCHING (only if specified)
            if employment_type and employment_type.strip():
                emp_conditions = [
                    "LOWER(c.employment_type) LIKE %s",
                    "LOWER(c.ai_employment_type) LIKE %s",
                ]
                conditions.append(f"({' OR '.join(emp_conditions)})")
                emp_pattern = f"%{employment_type}%"
                params.extend([emp_pattern, emp_pattern])

            # 3. LOCATION MATCHING (only if specified)
            if location_pref and location_pref.strip():
                if location_pref == "remote":
                    loc_conditions = [
                        "LOWER(c.location) LIKE '%remote%'",
                        "LOWER(c.ai_work_arrangement) LIKE '%remote%'",
                        "c.ai_remote_allowed = true",
                        "c.is_remote = true",
                    ]
                    conditions.append(f"({' OR '.join(loc_conditions)})")
                else:
                    loc_conditions = [
                        "LOWER(c.location) LIKE %s",
                        "LOWER(c.ai_city) LIKE %s",
                        "LOWER(c.ai_state) LIKE %s",
                        "LOWER(c.ai_country) LIKE %s",
                    ]
                    conditions.append(f"({' OR '.join(loc_conditions)})")
                    loc_pattern = f"%{location_pref}%"
                    params.extend([loc_pattern] * 4)

            # 4. SALARY RANGE MATCHING
            if salary_min or salary_max:
                salary_conditions = []
                if salary_min:
                    salary_conditions.extend(
                        ["c.salary_max >= %s", "c.ai_salary_max >= %s"]
                    )
                    params.extend([salary_min, salary_min])
                if salary_max:
                    salary_conditions.extend(
                        ["c.salary_min <= %s", "c.ai_salary_min <= %s"]
                    )
                    params.extend([salary_max, salary_max])
                if salary_conditions:
                    conditions.append(f"({' OR '.join(salary_conditions)})")

            # 5. REMOTE PREFERENCE MATCHING (only if specified)
            if (
                remote_pref
                and remote_pref.strip()
                and remote_pref in ["remote", "hybrid", "on-site"]
            ):
                remote_conditions = [
                    "LOWER(c.ai_work_arrangement) LIKE %s",
                    "LOWER(c.work_arrangement) LIKE %s",
                ]
                if remote_pref == "remote":
                    remote_conditions.extend(
                        ["c.ai_remote_allowed = true", "c.is_remote = true"]
                    )
                conditions.append(f"({' OR '.join(remote_conditions)})")
                remote_pattern = f"%{remote_pref}%"
                params.extend([remote_pattern, remote_pattern])

            # 6. EXPERIENCE LEVEL MATCHING (only if specified)
            if experience_years and experience_years > 0:
                exp_conditions = [
                    "c.ai_years_experience_min <= %s",
                    "c.years_experience_min <= %s",
                    "c.years_experience <= %s",
                ]
                conditions.append(f"({' OR '.join(exp_conditions)})")
                params.extend([experience_years] * 3)

            # Combine all conditions
            where_clause = ""
            if base_conditions:
                where_clause = f"WHERE {' AND '.join(base_conditions)}"
                if conditions:
                    where_clause += f" AND {' AND '.join(conditions)}"
            elif conditions:
                where_clause = f"WHERE {' AND '.join(conditions)}"
            else:
                where_clause = "WHERE 1=1"  # Fallback

            query = f"""
                SELECT
                    c.id, c.title, c.company, c.location, c.description,
                    c.salary_min, c.salary_max, c.salary_currency, c.employment_type,
                    c.job_url, c.posted_date, c.created_at as scraped_at,
                    c.ai_salary_min, c.ai_salary_max, c.ai_salary_currency,
                    c.ai_employment_type, c.ai_required_skills, c.ai_summary,
                    c.ai_compensation_summary, c.email, c.whatsapp_number,
                    c.ai_email, c.ai_whatsapp_number, c.ai_job_titles,
                    c.ai_job_function, c.ai_job_level, c.ai_industry,
                    c.ai_work_arrangement, c.ai_remote_allowed, c.is_remote
                FROM canonical_jobs c
                {where_clause}
                ORDER BY
                    -- Prioritize AI-enhanced jobs first
                    CASE WHEN c.ai_enhanced = true THEN 1 ELSE 2 END,
                    -- Prioritize jobs with comprehensive AI data
                    CASE WHEN c.ai_job_titles IS NOT NULL THEN 1 ELSE 2 END,
                    -- Prioritize recent jobs
                    COALESCE(c.posted_date, c.date_posted, c.created_at) DESC
                LIMIT %s
            """

            # Add limit parameter
            params.append(limit)

            # Execute the comprehensive search
            logger.debug(f"Query: {query}")
            logger.debug(f"Params: {params}")
            logger.debug(f"Param count: {len(params)}")
            logger.debug(f"Query placeholder count: {query.count('%s')}")

            cursor = self.connection.cursor(
                cursor_factory=psycopg2.extras.RealDictCursor
            )
            cursor.execute(query, params)
            jobs = cursor.fetchall()

            logger.info(
                f"Found {len(jobs)} jobs for '{job_type}' with {len(params)} params"
            )
            return [dict(job) for job in jobs]

        except Exception as e:
            logger.error(f"❌ Error in simple search: {e}")
            return []

    def format_job_for_whatsapp(self, job: Dict, index: int = 1) -> str:
        """Format a job for WhatsApp message"""
        try:
            # Check if we have a complete AI summary (new enhanced format)
            if job.get("ai_summary") and len(job.get("ai_summary", "")) > 100:
                # Use the complete AI-generated WhatsApp post (includes contact info)
                ai_summary = job["ai_summary"]

                # Format with job number - AI summary already includes contact info
                return f"**{index}️⃣ JOB ALERT**\n\n{ai_summary}"

            else:
                # Simple fallback for jobs without enhanced AI summary
                title = job.get("title", "Job Opening")
                company = job.get("company", "Company")
                location = job.get("location", "Location not specified")
                job_url = job.get("job_url", "")

                # Simple format for fallback
                contact = f", Apply: {job_url}" if job_url else ""
                job_text = f"{index}️⃣ *{title}* - {company}, {location}{contact}"
                return job_text

        except Exception as e:
            logger.error(f"❌ Error formatting job: {e}")
            return f"{index}️⃣ Job formatting error"

    @property
    def connection(self):
        """Get a connection from the pool for legacy compatibility"""
        return self.get_connection()

    def close(self):
        """Close database connection"""
        if self.connection_pool:
            self.connection_pool.closeall()
            logger.info("🔌 Database connection pool closed")
