#!/usr/bin/env python3
"""
Standalone AI Enhanced Parser for Railway
Runs without interactive menu - processes all recent jobs
"""

import os
import sys
import logging
from datetime import datetime

# Add the current directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from data_parser.parsers.ai_enhanced_parser import AIEnhancedJobParser

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('ai_parser_standalone.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def main():
    """Main function for standalone AI parser"""
    logger.info("🤖 Starting Standalone AI Enhanced Job Parser")
    logger.info("💡 Processing all recent jobs (14-day filter)")
    logger.info("=" * 60)
    
    start_time = datetime.now()
    
    try:
        # Initialize parser
        parser = AIEnhancedJobParser()
        
        # Process all recent jobs (equivalent to option 1 in the menu)
        parser.process_raw_jobs()
        
        # Calculate duration
        end_time = datetime.now()
        duration = end_time - start_time
        
        # Print final stats
        logger.info(f"\n📊 Final Statistics:")
        logger.info(f"   Total processed: {parser.stats['total_processed']}")
        logger.info(f"   AI enhanced: {parser.stats['ai_enhanced']}")
        logger.info(f"   Errors: {parser.stats['errors']}")
        logger.info(f"   Duration: {duration}")
        
        logger.info("✅ AI Enhanced Parser completed successfully")
        
    except Exception as e:
        logger.error(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
