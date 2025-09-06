#!/usr/bin/env python3
"""
Automated Cleanup Service for Railway Deployment
Runs database cleanup every 5 hours automatically
"""

import os
import sys
import time
import logging
import threading
from datetime import datetime, timedelta

# Add the parent directory to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database_manager import DatabaseManager
from utils.logger import setup_logger

logger = setup_logger(__name__)


class AutomatedCleanupService:
    def __init__(self):
        self.db_manager = DatabaseManager()
        self.connection = self.db_manager.get_connection()
        self.running = False
        
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
                (cutoff_date,)
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
                (cutoff_date,)
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
        self.running = True
        
        def cleanup_worker():
            while self.running:
                try:
                    logger.info(f"⏰ Starting scheduled cleanup (every {interval_hours}h)")
                    self.run_full_cleanup()
                    
                    # Sleep for the specified interval
                    sleep_seconds = interval_hours * 3600
                    logger.info(f"😴 Next cleanup in {interval_hours} hours")
                    
                    # Sleep in smaller chunks to allow for graceful shutdown
                    for _ in range(interval_hours * 60):  # Check every minute
                        if not self.running:
                            break
                        time.sleep(60)
                    
                except Exception as e:
                    logger.error(f"❌ Error in cleanup worker: {e}")
                    # Sleep for 1 hour before retrying
                    for _ in range(60):
                        if not self.running:
                            break
                        time.sleep(60)
        
        # Start the cleanup worker in a separate thread
        cleanup_thread = threading.Thread(target=cleanup_worker, daemon=True)
        cleanup_thread.start()
        logger.info(f"🚀 Automated cleanup started (every {interval_hours} hours)")
        return cleanup_thread

    def stop(self):
        """Stop the automated cleanup service"""
        self.running = False
        logger.info("🛑 Stopping automated cleanup service")


def main():
    """Main function to run the automated cleanup service"""
    logger.info("🚀 Starting Automated Cleanup Service for Railway")
    
    try:
        # Create and start the cleanup service
        cleanup_service = AutomatedCleanupService()
        
        # Run initial cleanup
        logger.info("🧹 Running initial cleanup...")
        cleanup_service.run_full_cleanup()
        
        # Start automated cleanup every 5 hours
        cleanup_service.start_automated_cleanup(interval_hours=5)
        
        # Keep the service running
        logger.info("✅ Cleanup service is running. Press Ctrl+C to stop.")
        while True:
            time.sleep(60)  # Check every minute
            
    except KeyboardInterrupt:
        logger.info("🛑 Received shutdown signal")
        cleanup_service.stop()
    except Exception as e:
        logger.error(f"❌ Fatal error in cleanup service: {e}")
    finally:
        logger.info("👋 Cleanup service stopped")


if __name__ == "__main__":
    main()
