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
                AND posted_date >= CURRENT_DATE - INTERVAL '60 days'
                ORDER BY job_embedding <=> %s::vector
                LIMIT %s
            """,
                (user_embedding_for_query, user_embedding_for_query, limit * 2),
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

                # Include matches above 10% threshold
                if similarity >= 0.10:  # 10% similarity threshold
                    matched_jobs.append(job_dict)

            logger.info(
                f"🎯 Found {len(matched_jobs)} embedding matches for user {user_id}"
            )
            return matched_jobs[:limit]

        except Exception as e:
            logger.error(f"❌ Embedding search failed: {e}")
            return []
