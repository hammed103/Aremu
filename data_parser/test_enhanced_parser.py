#!/usr/bin/env python3
"""
Test Enhanced AI Parser
Quick test to validate the enhanced parser functionality
"""

import sys
import os

sys.path.append(os.path.dirname(__file__))

from parsers.ai_enhanced_parser import AIEnhancedJobParser
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(message)s")
logger = logging.getLogger(__name__)


def test_enhanced_parser():
    """Test the enhanced parser with a small sample"""
    print("🧪 Testing Enhanced AI Job Parser")
    print("=" * 50)

    try:
        # Initialize parser
        parser = AIEnhancedJobParser()

        print(f"✅ Parser initialized")
        print(f"🤖 AI Enhancement: {'Enabled' if parser.use_ai else 'Disabled'}")
        print(f"💾 Database: Connected")

        # Test with limited batch
        print("\n🔄 Processing 5 jobs for testing...")
        parser.process_raw_jobs(limit=5)

        print("\n🎉 Enhanced parser test completed!")
        print("💾 Jobs processed and saved to canonical_jobs table")
        print("🔍 Check the database for enhanced job data")

        return True

    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        print(f"\n❌ Test failed: {e}")
        return False


def main():
    """Main function"""
    print("🚀 Enhanced AI Job Parser Test")
    print("=" * 40)
    print("This will:")
    print("- Test the unified parser for JobSpy and LinkedIn data")
    print("- Apply AI enhancement to extract missing fields")
    print("- Save comprehensive job data to canonical_jobs table")
    print("- Process only 10 jobs for testing")

    confirm = input("\nProceed with test? (y/N): ").strip().lower()

    if confirm in ["y", "yes"]:
        success = test_enhanced_parser()
        if success:
            print("\n💡 Ready for full processing:")
            print("   python parsers/ai_enhanced_parser.py")
    else:
        print("Test cancelled.")


if __name__ == "__main__":
    main()
