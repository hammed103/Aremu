#!/usr/bin/env python3
"""
Embedding-Based Job Matcher - Ultra-fast semantic matching
"""

import logging
import numpy as np
from typing import List, Dict, Optional
import psycopg2.extras
from services.embedding_service import EmbeddingService
from utils.logger import setup_logger
from datetime import datetime, timedelta
import threading
import time

logger = setup_logger(__name__)


class EmbeddingJobMatcher:
    def __init__(self, db_connection, openai_api_key: str):
        self.connection = db_connection
        self.embedding_service = EmbeddingService(openai_api_key, db_connection)

    def generate_user_embedding(self, user_id: int) -> bool:
        """Generate and store user embedding"""
        try:
            cursor = self.connection.cursor(
                cursor_factory=psycopg2.extras.RealDictCursor
            )

            # Get user preferences
            cursor.execute(
                "SELECT * FROM user_preferences WHERE user_id = %s", (user_id,)
            )
            prefs = cursor.fetchone()

            if not prefs:
                logger.warning(f"No preferences found for user {user_id}")
                return False

            # Create profile text
            profile_text = self.embedding_service.create_user_profile_text(dict(prefs))

            # Generate embedding
            embedding = self.embedding_service.get_embedding(profile_text)

            # Store in database
            cursor.execute(
                """
                UPDATE user_preferences 
                SET user_embedding = %s,
                    embedding_text = %s,
                    embedding_updated_at = NOW(),
                    embedding_version = 1
                WHERE user_id = %s
            """,
                (embedding.tolist(), profile_text, user_id),
            )

            self.connection.commit()
            logger.info(f"✅ Generated embedding for user {user_id}")
            return True

        except Exception as e:
            logger.error(f"❌ Error generating user embedding: {e}")
            return False

    def generate_job_embedding(self, job_id: int) -> bool:
        """Generate and store job embedding"""
        try:
            cursor = self.connection.cursor(
                cursor_factory=psycopg2.extras.RealDictCursor
            )

            # Get job data
            cursor.execute("SELECT * FROM canonical_jobs WHERE id = %s", (job_id,))
            job = cursor.fetchone()

            if not job:
                logger.warning(f"No job found with id {job_id}")
                return False

            # Create profile text
            profile_text = self.embedding_service.create_job_profile_text(dict(job))

            # Generate embedding
            embedding = self.embedding_service.get_embedding(profile_text)

            # Store in database
            cursor.execute(
                """
                UPDATE canonical_jobs 
                SET job_embedding = %s,
                    job_embedding_text = %s,
                    job_embedding_updated_at = NOW(),
                    embedding_version = 1
                WHERE id = %s
            """,
                (embedding.tolist(), profile_text, job_id),
            )

            self.connection.commit()
            logger.info(f"✅ Generated embedding for job {job_id}")
            return True

        except Exception as e:
            logger.error(f"❌ Error generating job embedding: {e}")
            return False

    def search_jobs_with_embeddings(self, user_id: int, limit: int = 50) -> List[Dict]:
        """Ultra-fast job search using vector similarity"""
        try:
            cursor = self.connection.cursor(
                cursor_factory=psycopg2.extras.RealDictCursor
            )

            # Get user embedding
            cursor.execute(
                """
                SELECT user_embedding FROM user_preferences 
                WHERE user_id = %s AND user_embedding IS NOT NULL
            """,
                (user_id,),
            )

            user_result = cursor.fetchone()
            if not user_result or not user_result["user_embedding"]:
                logger.warning(f"No embedding found for user {user_id}")
                return []

            user_embedding = user_result["user_embedding"]

            # Ensure embedding is in correct format for PostgreSQL
            if isinstance(user_embedding, str):
                # Already a JSON string - perfect for PostgreSQL
                user_embedding_for_query = user_embedding
                import json

                user_embedding_list = json.loads(user_embedding)
                embedding_length = len(user_embedding_list)
            else:
                # Convert list to JSON string for PostgreSQL
                import json

                user_embedding_for_query = json.dumps(user_embedding)
                embedding_length = len(user_embedding)

            logger.info(
                f"🔍 Found user embedding for user {user_id}, length: {embedding_length}"
            )

            # Vector similarity search
            cursor.execute(
                """
                SELECT 
                    *,
                    1 - (job_embedding <=> %s::vector) as similarity_score
                FROM canonical_jobs 
                WHERE job_embedding IS NOT NULL
                AND scraped_at >= CURRENT_DATE - INTERVAL '60 days'
                ORDER BY job_embedding <=> %s::vector
                LIMIT %s
            """,
                (
                    user_embedding_for_query,
                    user_embedding_for_query,
                    500,
                ),  # Get more jobs to filter
            )

            jobs = cursor.fetchall()

            # Process results
            matched_jobs = []
            for job in jobs:
                job_dict = dict(job)
                similarity = job_dict["similarity_score"]

                # Convert similarity to percentage
                match_score = min(similarity * 100, 100.0)
                job_dict["match_score"] = match_score
                job_dict["match_reasons"] = [f"AI semantic match: {similarity:.1%}"]

                # Include matches above 58% threshold
                if similarity >= 0.58:  # 58% similarity threshold
                    matched_jobs.append(job_dict)

            logger.info(
                f"🎯 Found {len(matched_jobs)} embedding matches for user {user_id}"
            )
            return matched_jobs[:limit]

        except Exception as e:
            logger.error(f"❌ Embedding search failed: {e}")
            return []

    def cleanup_old_jobs(self, days: int = 5) -> bool:
        """Clean up old jobs from canonical_jobs table"""
        try:
            cursor = self.connection.cursor()

            # Calculate cutoff date
            cutoff_date = datetime.now() - timedelta(days=days)
            logger.info(f"🧹 Cleaning jobs older than {cutoff_date}")

            # Count jobs to be deleted
            cursor.execute(
                """
                SELECT COUNT(*)
                FROM canonical_jobs
                WHERE scraped_at < %s OR scraped_at IS NULL
                """,
                (cutoff_date,),
            )

            old_jobs_count = cursor.fetchone()[0]

            if old_jobs_count == 0:
                logger.info("✅ No old jobs to clean up")
                return True

            # Delete old jobs
            cursor.execute(
                """
                DELETE FROM canonical_jobs
                WHERE scraped_at < %s OR scraped_at IS NULL
                """,
                (cutoff_date,),
            )

            deleted_count = cursor.rowcount
            self.connection.commit()

            logger.info(f"✅ Cleaned up {deleted_count} old jobs")
            return True

        except Exception as e:
            logger.error(f"❌ Error cleaning up old jobs: {e}")
            self.connection.rollback()
            return False

    def remove_duplicate_jobs(self) -> bool:
        """Remove duplicate jobs from canonical_jobs table"""
        try:
            cursor = self.connection.cursor()

            logger.info("🔍 Finding duplicate jobs...")

            # Find duplicates based on title, company, and location
            cursor.execute(
                """
                WITH duplicates AS (
                    SELECT
                        id,
                        ROW_NUMBER() OVER (
                            PARTITION BY
                                LOWER(TRIM(title)),
                                LOWER(TRIM(company)),
                                LOWER(TRIM(COALESCE(location, '')))
                            ORDER BY scraped_at DESC, id DESC
                        ) as row_num
                    FROM canonical_jobs
                    WHERE title IS NOT NULL
                    AND company IS NOT NULL
                )
                SELECT COUNT(*)
                FROM duplicates
                WHERE row_num > 1
                """
            )

            duplicate_count = cursor.fetchone()[0]

            if duplicate_count == 0:
                logger.info("✅ No duplicate jobs found")
                return True

            logger.info(f"🔍 Found {duplicate_count} duplicate jobs")

            # Delete duplicates (keep the most recent one)
            cursor.execute(
                """
                WITH duplicates AS (
                    SELECT
                        id,
                        ROW_NUMBER() OVER (
                            PARTITION BY
                                LOWER(TRIM(title)),
                                LOWER(TRIM(company)),
                                LOWER(TRIM(COALESCE(location, '')))
                            ORDER BY scraped_at DESC, id DESC
                        ) as row_num
                    FROM canonical_jobs
                    WHERE title IS NOT NULL
                    AND company IS NOT NULL
                )
                DELETE FROM canonical_jobs
                WHERE id IN (
                    SELECT id FROM duplicates WHERE row_num > 1
                )
                """
            )

            deleted_count = cursor.rowcount
            self.connection.commit()

            logger.info(f"✅ Removed {deleted_count} duplicate jobs")
            return True

        except Exception as e:
            logger.error(f"❌ Error removing duplicate jobs: {e}")
            self.connection.rollback()
            return False

    def run_full_cleanup(self) -> bool:
        """Run both old job cleanup and duplicate removal"""
        try:
            logger.info("🧹 Starting full database cleanup...")

            # Remove duplicates first
            duplicate_success = self.remove_duplicate_jobs()

            # Then clean old jobs
            cleanup_success = self.cleanup_old_jobs()

            if duplicate_success and cleanup_success:
                logger.info("✅ Full cleanup completed successfully")
                return True
            else:
                logger.warning("⚠️ Cleanup completed with some issues")
                return False

        except Exception as e:
            logger.error(f"❌ Error during full cleanup: {e}")
            return False

    def start_automated_cleanup(self, interval_hours: int = 5):
        """Start automated cleanup that runs every X hours"""

        def cleanup_worker():
            while True:
                try:
                    logger.info(
                        f"⏰ Starting scheduled cleanup (every {interval_hours}h)"
                    )
                    self.run_full_cleanup()

                    # Sleep for the specified interval
                    sleep_seconds = interval_hours * 3600
                    logger.info(f"😴 Next cleanup in {interval_hours} hours")
                    time.sleep(sleep_seconds)

                except Exception as e:
                    logger.error(f"❌ Error in cleanup worker: {e}")
                    # Sleep for 1 hour before retrying
                    time.sleep(3600)

        # Start the cleanup worker in a separate thread
        cleanup_thread = threading.Thread(target=cleanup_worker, daemon=True)
        cleanup_thread.start()
        logger.info(f"🚀 Automated cleanup started (every {interval_hours} hours)")
        return cleanup_thread
