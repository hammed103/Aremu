#!/usr/bin/env python3
"""
Railway Scheduler Service for AI Enhanced Parser
Runs the AI enhanced parser automatically every 2 hours
"""

import os
import sys
import time
import logging
import schedule
from datetime import datetime

# Add the current directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from data_parser.parsers.ai_enhanced_parser import AIEnhancedJobParser
from services.embedding_generator import EmbeddingGenerator
from legacy.database_manager import DatabaseManager

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("scheduler.log"), logging.StreamHandler()],
)
logger = logging.getLogger(__name__)


class SchedulerService:
    """Railway scheduler service for automated job processing"""

    def __init__(self):
        """Initialize the scheduler service"""
        self.parser = None

        # Initialize database and embedding generator
        self.db_manager = DatabaseManager()
        self.embedding_generator = EmbeddingGenerator(
            self.db_manager.connection, os.getenv("OPENAI_API_KEY")
        )

        logger.info("🚀 Scheduler Service initialized")

    def run_ai_parser(self):
        """Run the AI enhanced parser"""
        try:
            logger.info("🤖 Starting AI Enhanced Parser job...")
            start_time = datetime.now()

            # Initialize parser
            self.parser = AIEnhancedJobParser()

            # Process all recent jobs (14-day filter)
            self.parser.process_raw_jobs()

            # Log completion stats
            end_time = datetime.now()
            duration = end_time - start_time

            logger.info(f"✅ AI Parser job completed in {duration}")
            logger.info(f"📊 Statistics:")
            logger.info(f"   Total processed: {self.parser.stats['total_processed']}")
            logger.info(f"   AI enhanced: {self.parser.stats['ai_enhanced']}")
            logger.info(f"   Errors: {self.parser.stats['errors']}")

        except Exception as e:
            logger.error(f"❌ Error running AI parser: {e}")
            import traceback

            traceback.print_exc()

    def run_user_embedding_generation(self):
        """Generate missing user embeddings"""
        try:
            logger.info("🧠 Starting user embedding generation...")
            count = self.embedding_generator.generate_missing_user_embeddings(50)
            logger.info(f"✅ Generated {count} user embeddings")
        except Exception as e:
            logger.error(f"❌ User embedding generation failed: {e}")

    def run_job_embedding_generation(self):
        """Generate missing job embeddings"""
        try:
            logger.info("🧠 Starting job embedding generation...")
            count = self.embedding_generator.generate_missing_job_embeddings(100)
            logger.info(f"✅ Generated {count} job embeddings")
        except Exception as e:
            logger.error(f"❌ Job embedding generation failed: {e}")

    def run_stale_embedding_update(self):
        """Update stale embeddings"""
        try:
            logger.info("🔄 Updating stale embeddings...")
            count = self.embedding_generator.update_stale_embeddings(30)
            logger.info(f"✅ Updated {count} stale embeddings")
        except Exception as e:
            logger.error(f"❌ Stale embedding update failed: {e}")

    def setup_embedding_jobs(self):
        """Setup embedding generation jobs"""

        # Generate missing user embeddings every 30 minutes
        schedule.every(30).minutes.do(self.run_user_embedding_generation)

        # Generate missing job embeddings every 15 minutes
        schedule.every(15).minutes.do(self.run_job_embedding_generation)

        # Update stale embeddings daily
        schedule.every().day.at("02:00").do(self.run_stale_embedding_update)

    def start_scheduler(self):
        """Start the scheduler with all jobs"""
        logger.info("⏰ Starting scheduler with all jobs...")

        # Schedule AI parser every 2 hours
        schedule.every(2).hours.do(self.run_ai_parser)

        # Setup embedding generation jobs
        self.setup_embedding_jobs()

        logger.info("🚀 Scheduler configured:")
        logger.info("   - AI Parser: every 2 hours")
        logger.info("   - User embeddings: every 30 minutes")
        logger.info("   - Job embeddings: every 15 minutes")
        logger.info("   - Stale embedding updates: daily at 2:00 AM")

        # Run initial AI Parser job
        logger.info("🚀 Running initial AI Parser job...")
        self.run_ai_parser()

        # Keep the scheduler running
        while True:
            try:
                schedule.run_pending()
                time.sleep(60)  # Check every minute
            except KeyboardInterrupt:
                logger.info("🛑 Scheduler stopped by user")
                break
            except Exception as e:
                logger.error(f"❌ Scheduler error: {e}")
                time.sleep(300)  # Wait 5 minutes before retrying


def main():
    """Main function for Railway deployment"""
    logger.info("🚀 Starting Railway AI Enhanced Parser Scheduler")

    # Check if running in Railway environment
    if os.getenv("RAILWAY_ENVIRONMENT"):
        logger.info("🚂 Running in Railway environment")
    else:
        logger.info("💻 Running in local environment")

    # Start the scheduler service
    scheduler = SchedulerService()
    scheduler.start_scheduler()


if __name__ == "__main__":
    main()
