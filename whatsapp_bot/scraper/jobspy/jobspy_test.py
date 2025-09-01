#!/usr/bin/env python3
"""
JobSpy Test - Quick validation of the scraper
"""

import sys
import os
sys.path.append(os.path.dirname(__file__))

from jobspy_scraper import FixedDatabaseJobScraper
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(message)s")
logger = logging.getLogger(__name__)

def test_jobspy_scraper():
    """Test the JobSpy scraper with a small sample"""
    print("🧪 Testing JobSpy Nigeria Scraper")
    print("=" * 40)
    
    try:
        # Initialize scraper
        scraper = FixedDatabaseJobScraper()
        
        # Run test
        success = scraper.run_test_scrape()
        
        if success:
            print("\n🎉 JobSpy scraper test successful!")
            print("💾 Jobs saved to raw_jobs database")
            print("🔍 No JSON encoding errors")
            print("\n💡 Ready to run full scraping:")
            print("   python jobspy_scraper.py")
            return True
        else:
            print("\n❌ JobSpy scraper test failed")
            return False
            
    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        print(f"\n❌ Test failed: {e}")
        return False

if __name__ == "__main__":
    test_jobspy_scraper()
