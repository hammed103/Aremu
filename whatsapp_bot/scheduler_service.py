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

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('scheduler.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class SchedulerService:
    """Railway scheduler service for automated job processing"""
    
    def __init__(self):
        """Initialize the scheduler service"""
        self.parser = None
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
    
    def start_scheduler(self):
        """Start the scheduler with 2-hour intervals"""
        logger.info("⏰ Starting scheduler - AI Parser will run every 2 hours")
        
        # Schedule the job every 2 hours
        schedule.every(2).hours.do(self.run_ai_parser)
        
        # Run immediately on startup
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
    if os.getenv('RAILWAY_ENVIRONMENT'):
        logger.info("🚂 Running in Railway environment")
    else:
        logger.info("💻 Running in local environment")
    
    # Start the scheduler service
    scheduler = SchedulerService()
    scheduler.start_scheduler()

if __name__ == "__main__":
    main()
