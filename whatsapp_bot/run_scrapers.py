#!/usr/bin/env python3
"""
Standalone Scraper Runner - Run scrapers independently or in daemon mode
"""

import os
import sys
import argparse
import time

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.scraper_service import ScraperService
from utils.logger import setup_logger

logger = setup_logger(__name__)


def run_single_scraper(scraper_name: str):
    """Run a single scraper"""
    logger.info(f"🚀 Running {scraper_name} scraper")
    
    scraper_service = ScraperService()
    result = scraper_service.run_manual_scrape(scraper_name)
    
    if result['status'] == 'success':
        logger.info(f"✅ {result['message']}")
        return True
    else:
        logger.error(f"❌ {result['message']}")
        return False


def run_all_scrapers():
    """Run all enabled scrapers once"""
    logger.info("🚀 Running all enabled scrapers")
    
    scraper_service = ScraperService()
    result = scraper_service.run_manual_scrape("all")
    
    if result['status'] == 'success':
        logger.info(f"✅ {result['message']}")
        return True
    else:
        logger.error(f"❌ {result['message']}")
        return False


def run_daemon_mode():
    """Run scrapers in continuous daemon mode"""
    logger.info("🤖 Starting scraper daemon mode")
    logger.info("Press Ctrl+C to stop")
    
    scraper_service = ScraperService()
    
    try:
        scraper_service.start_daemon()
        
        # Keep the main thread alive
        while True:
            time.sleep(60)
            
    except KeyboardInterrupt:
        logger.info("\n🛑 Stopping scraper daemon...")
        scraper_service.stop_daemon()
        logger.info("✅ Scraper daemon stopped")


def show_status():
    """Show status of all scrapers"""
    logger.info("📊 Scraper Status")
    logger.info("=" * 40)
    
    scraper_service = ScraperService()
    status = scraper_service.get_status()
    
    logger.info(f"Daemon Running: {'✅ Yes' if status['daemon_running'] else '❌ No'}")
    logger.info(f"Cycle Count: {status['cycle_count']}")
    logger.info("\nScraper Details:")
    
    for name, config in status['scrapers'].items():
        enabled_status = "✅ Enabled" if config['enabled'] else "❌ Disabled"
        last_run = config['last_run'] if config['last_run'] else "Never"
        next_due = "✅ Yes" if config['next_run_due'] else "❌ No"
        
        logger.info(f"\n{name.upper()}:")
        logger.info(f"  Status: {enabled_status}")
        logger.info(f"  Interval: {config['interval_hours']} hours")
        logger.info(f"  Last Run: {last_run}")
        logger.info(f"  Next Run Due: {next_due}")


def main():
    """Main function with command line interface"""
    parser = argparse.ArgumentParser(description="Aremu Job Scraper Runner")
    parser.add_argument(
        "action",
        choices=["run", "daemon", "status", "test"],
        help="Action to perform"
    )
    parser.add_argument(
        "--scraper",
        choices=["all", "jobspy", "linkedin", "indeed", "prosple"],
        default="all",
        help="Which scraper to run (default: all)"
    )
    
    args = parser.parse_args()
    
    logger.info("🔧 Aremu Job Scraper Runner")
    logger.info("=" * 30)
    
    try:
        if args.action == "run":
            if args.scraper == "all":
                success = run_all_scrapers()
            else:
                success = run_single_scraper(args.scraper)
            
            if success:
                logger.info("🎉 Scraping completed successfully!")
            else:
                logger.error("❌ Scraping failed!")
                sys.exit(1)
        
        elif args.action == "daemon":
            run_daemon_mode()
        
        elif args.action == "status":
            show_status()
        
        elif args.action == "test":
            logger.info("🧪 Running scraper integration test...")
            from test_scraper_integration import test_scraper_service
            success = test_scraper_service()
            
            if success:
                logger.info("✅ All tests passed!")
            else:
                logger.error("❌ Some tests failed!")
                sys.exit(1)
    
    except KeyboardInterrupt:
        logger.info("\n👋 Goodbye!")
    except Exception as e:
        logger.error(f"❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
