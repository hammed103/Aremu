#!/usr/bin/env python3
"""
JobSpy Runner - Simple interface to run the Nigeria job scraper
"""

import sys
import os
sys.path.append(os.path.dirname(__file__))

from jobspy_scraper import FixedDatabaseJobScraper

def main():
    """Main runner function"""
    print("🇳🇬 Nigeria JobSpy Scraper")
    print("=" * 30)
    print("Choose your option:")
    print("1. Test scraper (recommended first)")
    print("2. Run comprehensive scraping")
    print("3. Exit")
    
    while True:
        choice = input("\nEnter your choice (1-3): ").strip()
        
        if choice == "1":
            print("\n🧪 Running test scraper...")
            try:
                scraper = FixedDatabaseJobScraper()
                success = scraper.run_test_scrape()
                
                if success:
                    print("\n🎉 Test successful!")
                    print("💾 Jobs saved to raw_jobs database")
                    print("💡 Ready for comprehensive scraping")
                else:
                    print("\n❌ Test failed")
                    
            except Exception as e:
                print(f"❌ Test error: {e}")
            break
            
        elif choice == "2":
            print("\n🚀 Running comprehensive scraping...")
            print("⚠️  This will:")
            print("   - Scrape thousands of Nigerian jobs")
            print("   - Take 1-2 hours to complete")
            print("   - Save directly to raw_jobs database")
            
            confirm = input("\nProceed? (y/N): ").strip().lower()
            
            if confirm in ['y', 'yes']:
                try:
                    scraper = FixedDatabaseJobScraper()
                    scraper.run_comprehensive_scrape()
                    print("\n🎉 Comprehensive scraping completed!")
                    
                except Exception as e:
                    print(f"❌ Scraping error: {e}")
            else:
                print("Cancelled.")
            break
            
        elif choice == "3":
            print("👋 Goodbye!")
            break
            
        else:
            print("❌ Invalid choice. Please enter 1, 2, or 3.")

if __name__ == "__main__":
    main()
