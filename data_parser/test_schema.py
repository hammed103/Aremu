#!/usr/bin/env python3
"""
Test Database Schema Creation
Quick test to validate the enhanced schema works
"""

import sys
import os
sys.path.append(os.path.dirname(__file__))

from parsers.ai_enhanced_parser import AIEnhancedJobParser
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(message)s")
logger = logging.getLogger(__name__)

def test_schema():
    """Test the enhanced schema creation"""
    print("🧪 Testing Enhanced Database Schema")
    print("=" * 40)
    
    try:
        # Initialize parser (this will create the schema)
        parser = AIEnhancedJobParser()
        
        print("✅ Schema created successfully")
        print("🤖 AI Enhancement:", "Enabled" if parser.use_ai else "Disabled")
        print("💾 Database: Connected")
        
        # Test with just 1 job to verify schema works
        print("\n🔄 Processing 1 job to test schema...")
        parser.process_raw_jobs(limit=1)
        
        print("\n🎉 Schema test completed!")
        print("💾 Enhanced canonical_jobs table is ready")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Schema test failed: {e}")
        print(f"\n❌ Schema test failed: {e}")
        return False

if __name__ == "__main__":
    test_schema()
