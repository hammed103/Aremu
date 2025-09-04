#!/usr/bin/env python3
"""
Simple test script for Railway deployment
Tests environment and basic functionality
"""

import os
import sys
import logging
from datetime import datetime

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_railway_environment():
    """Test Railway environment and dependencies"""
    
    print("🚂 Railway Environment Test")
    print("=" * 50)
    
    # Test 1: Environment Variables
    print("\n1. Environment Variables:")
    required_vars = [
        'DATABASE_URL',
        'OPENAI_API_KEY', 
        'WHATSAPP_TOKEN',
        'WHATSAPP_PHONE_ID'
    ]
    
    for var in required_vars:
        value = os.getenv(var)
        if value:
            print(f"   ✅ {var}: {'*' * 10}...{value[-4:] if len(value) > 4 else '****'}")
        else:
            print(f"   ❌ {var}: Missing")
    
    # Test 2: Python Path
    print(f"\n2. Python Path:")
    print(f"   Current directory: {os.getcwd()}")
    print(f"   Python path: {sys.path[:3]}...")
    
    # Test 3: Import Tests
    print(f"\n3. Import Tests:")
    try:
        import openai
        print(f"   ✅ OpenAI: {openai.__version__}")
    except Exception as e:
        print(f"   ❌ OpenAI: {e}")
    
    try:
        import psycopg2
        print(f"   ✅ PostgreSQL: Available")
    except Exception as e:
        print(f"   ❌ PostgreSQL: {e}")
    
    try:
        import schedule
        print(f"   ✅ Schedule: Available")
    except Exception as e:
        print(f"   ❌ Schedule: {e}")
    
    # Test 4: Database Connection
    print(f"\n4. Database Connection:")
    try:
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        from legacy.database_manager import DatabaseManager
        
        db = DatabaseManager()
        print(f"   ✅ Database connected successfully")
        
        # Test query
        cursor = db.connection.cursor()
        cursor.execute("SELECT COUNT(*) FROM raw_jobs LIMIT 1")
        count = cursor.fetchone()[0]
        print(f"   ✅ Raw jobs count: {count}")
        cursor.close()
        
    except Exception as e:
        print(f"   ❌ Database error: {e}")
    
    # Test 5: AI Enhanced Parser Import
    print(f"\n5. AI Enhanced Parser:")
    try:
        from data_parser.parsers.ai_enhanced_parser import AIEnhancedJobParser
        print(f"   ✅ AI Enhanced Parser imported successfully")
    except Exception as e:
        print(f"   ❌ AI Enhanced Parser error: {e}")
    
    print(f"\n🎯 Test completed at {datetime.now()}")
    print("=" * 50)

if __name__ == "__main__":
    test_railway_environment()
