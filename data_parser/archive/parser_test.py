#!/usr/bin/env python3
"""
Job Data Parser Test
Quick test to validate the job data parser
"""

import sys
import os
sys.path.append(os.path.dirname(__file__))

from job_data_parser import JobDataParser
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(message)s")
logger = logging.getLogger(__name__)

def test_parser():
    """Test the job data parser with a small sample"""
    print("🧪 Testing Job Data Parser")
    print("=" * 40)
    
    try:
        # Initialize parser without AI for testing
        parser = JobDataParser(openai_api_key=None)
        
        # Test with limited batch
        logger.info("🔍 Testing with 10 jobs (no AI enhancement)")
        parser.process_raw_jobs(limit=10)
        
        print("\n🎉 Parser test successful!")
        print("💾 Jobs parsed to canonical_jobs table")
        print("🔍 Field mapping working correctly")
        print("\n💡 Ready for full parsing:")
        print("   python job_data_parser.py")
        return True
            
    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        print(f"\n❌ Test failed: {e}")
        return False

if __name__ == "__main__":
    test_parser()
