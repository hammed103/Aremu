#!/usr/bin/env python3
"""
Background Embedding Generator - Processes users and jobs in batches
"""

import logging
import time
from typing import List, Tuple
import psycopg2.extras
from services.embedding_job_matcher import EmbeddingJobMatcher
from utils.logger import setup_logger

logger = setup_logger(__name__)

class EmbeddingGenerator:
    def __init__(self, db_connection, openai_api_key: str):
        self.connection = db_connection
        self.matcher = EmbeddingJobMatcher(db_connection, openai_api_key)
        
    def generate_missing_user_embeddings(self, batch_size: int = 50) -> int:
        """Generate embeddings for users without them"""
        try:
            cursor = self.connection.cursor()
            
            # Find users without embeddings
            cursor.execute("""
                SELECT user_id FROM user_preferences 
                WHERE user_embedding IS NULL 
                AND (job_roles IS NOT NULL OR job_categories IS NOT NULL)
                LIMIT %s
            """, (batch_size,))
            
            user_ids = [row[0] for row in cursor.fetchall()]
            
            if not user_ids:
                logger.info("✅ All users have embeddings")
                return 0
            
            # Generate embeddings
            success_count = 0
            for user_id in user_ids:
                if self.matcher.generate_user_embedding(user_id):
                    success_count += 1
                time.sleep(0.1)  # Rate limiting
            
            logger.info(f"✅ Generated {success_count}/{len(user_ids)} user embeddings")
            return success_count
            
        except Exception as e:
            logger.error(f"❌ Error generating user embeddings: {e}")
            return 0
    
    def generate_missing_job_embeddings(self, batch_size: int = 100) -> int:
        """Generate embeddings for jobs without them"""
        try:
            cursor = self.connection.cursor()
            
            # Find recent jobs without embeddings
            cursor.execute("""
                SELECT id FROM canonical_jobs 
                WHERE job_embedding IS NULL 
                AND posted_date >= CURRENT_DATE - INTERVAL '60 days'
                AND title IS NOT NULL
                LIMIT %s
            """, (batch_size,))
            
            job_ids = [row[0] for row in cursor.fetchall()]
            
            if not job_ids:
                logger.info("✅ All recent jobs have embeddings")
                return 0
            
            # Generate embeddings
            success_count = 0
            for job_id in job_ids:
                if self.matcher.generate_job_embedding(job_id):
                    success_count += 1
                time.sleep(0.1)  # Rate limiting
            
            logger.info(f"✅ Generated {success_count}/{len(job_ids)} job embeddings")
            return success_count
            
        except Exception as e:
            logger.error(f"❌ Error generating job embeddings: {e}")
            return 0
    
    def update_stale_embeddings(self, days_old: int = 30) -> int:
        """Update embeddings older than specified days"""
        try:
            cursor = self.connection.cursor()
            
            # Find stale user embeddings
            cursor.execute("""
                SELECT user_id FROM user_preferences 
                WHERE embedding_updated_at < CURRENT_DATE - INTERVAL '%s days'
                AND user_embedding IS NOT NULL
                LIMIT 20
            """, (days_old,))
            
            user_ids = [row[0] for row in cursor.fetchall()]
            
            # Update user embeddings
            success_count = 0
            for user_id in user_ids:
                if self.matcher.generate_user_embedding(user_id):
                    success_count += 1
                time.sleep(0.1)
            
            logger.info(f"✅ Updated {success_count} stale user embeddings")
            return success_count
            
        except Exception as e:
            logger.error(f"❌ Error updating stale embeddings: {e}")
            return 0
    
    def get_embedding_stats(self) -> dict:
        """Get statistics about embedding coverage"""
        try:
            cursor = self.connection.cursor()
            
            # User embedding stats
            cursor.execute("""
                SELECT 
                    COUNT(*) as total_users,
                    COUNT(user_embedding) as users_with_embeddings,
                    ROUND(COUNT(user_embedding) * 100.0 / COUNT(*), 1) as coverage_percent
                FROM user_preferences 
                WHERE job_roles IS NOT NULL OR job_categories IS NOT NULL
            """)
            
            user_stats = cursor.fetchone()
            
            # Job embedding stats
            cursor.execute("""
                SELECT 
                    COUNT(*) as total_jobs,
                    COUNT(job_embedding) as jobs_with_embeddings,
                    ROUND(COUNT(job_embedding) * 100.0 / COUNT(*), 1) as coverage_percent
                FROM canonical_jobs 
                WHERE posted_date >= CURRENT_DATE - INTERVAL '60 days'
            """)
            
            job_stats = cursor.fetchone()
            
            return {
                'user_total': user_stats[0],
                'user_with_embeddings': user_stats[1],
                'user_coverage_percent': user_stats[2],
                'job_total': job_stats[0],
                'job_with_embeddings': job_stats[1],
                'job_coverage_percent': job_stats[2]
            }
            
        except Exception as e:
            logger.error(f"❌ Error getting embedding stats: {e}")
            return {}
    
    def run_full_embedding_generation(self) -> dict:
        """Run a complete embedding generation cycle"""
        logger.info("🧠 Starting full embedding generation cycle...")
        
        results = {
            'user_embeddings_generated': 0,
            'job_embeddings_generated': 0,
            'stale_embeddings_updated': 0,
            'stats': {}
        }
        
        # Generate missing user embeddings
        results['user_embeddings_generated'] = self.generate_missing_user_embeddings(50)
        
        # Generate missing job embeddings
        results['job_embeddings_generated'] = self.generate_missing_job_embeddings(100)
        
        # Update stale embeddings
        results['stale_embeddings_updated'] = self.update_stale_embeddings(30)
        
        # Get final stats
        results['stats'] = self.get_embedding_stats()
        
        logger.info(f"🎉 Embedding generation cycle complete: {results}")
        return results
