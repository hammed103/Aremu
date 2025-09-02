#!/usr/bin/env python3
"""
Scraper Service - Unified scraper runner for all job scrapers
Runs JobSpy, LinkedIn, Indeed, and Prosple scrapers in a continuous loop
"""

import os
import sys
import time
import threading
import logging
from datetime import datetime
from typing import Dict, Any

# Add scraper paths to system path
current_dir = os.path.dirname(os.path.abspath(__file__))
scraper_dir = os.path.join(os.path.dirname(current_dir), "scraper")
sys.path.append(scraper_dir)
sys.path.append(os.path.join(scraper_dir, "jobspy"))
sys.path.append(os.path.join(scraper_dir, "linkedin"))

from utils.logger import setup_logger

logger = setup_logger(__name__)


class ScraperService:
    """Unified service to run all job scrapers in a continuous loop"""

    def __init__(self):
        """Initialize the scraper service"""
        self.is_running = False
        self.scraper_thread = None
        self.cycle_count = 0
        self.last_run_times = {}

        # Scraper configurations
        self.scrapers = {
            "jobspy": {
                "enabled": True,
                "interval_hours": 6,  # Run every 6 hours
                "module": None,
                "last_run": None,
            },
            "linkedin": {
                "enabled": False,
                "interval_hours": 8,  # Run every 8 hours
                "module": None,
                "last_run": None,
            },
            "indeed": {
                "enabled": False,  # Disabled until implemented
                "interval_hours": 12,
                "module": None,
                "last_run": None,
            },
            "prosple": {
                "enabled": False,  # Disabled until implemented
                "interval_hours": 24,
                "module": None,
                "last_run": None,
            },
        }

        logger.info("🔧 ScraperService initialized")

    def _import_scrapers(self):
        """Dynamically import scraper modules"""
        try:
            # Import JobSpy scraper
            from jobspy_scraper import FixedDatabaseJobScraper

            self.scrapers["jobspy"]["module"] = FixedDatabaseJobScraper
            logger.info("✅ JobSpy scraper imported successfully")
        except ImportError as e:
            logger.error(f"❌ Failed to import JobSpy scraper: {e}")
            self.scrapers["jobspy"]["enabled"] = False
            self.scrapers["jobspy"]["module"] = None

        try:
            # Import LinkedIn scraper - need to import the class properly
            import sys
            import os

            linkedin_path = os.path.join(
                os.path.dirname(os.path.dirname(__file__)), "scraper", "linkedin"
            )
            sys.path.append(linkedin_path)
            from enhanced_linkedin_scraper import EnhancedLinkedInScraper

            self.scrapers["linkedin"]["module"] = EnhancedLinkedInScraper
            logger.info("✅ LinkedIn scraper imported successfully")
        except ImportError as e:
            logger.error(f"❌ Failed to import LinkedIn scraper: {e}")
            self.scrapers["linkedin"]["enabled"] = False
            self.scrapers["linkedin"]["module"] = None

        try:
            # Import Indeed scraper
            indeed_path = os.path.join(
                os.path.dirname(os.path.dirname(__file__)), "scraper", "indeed"
            )
            sys.path.append(indeed_path)
            from indeed_scraper import IndeedScraper

            self.scrapers["indeed"]["module"] = IndeedScraper
            logger.info("✅ Indeed scraper imported successfully")
        except ImportError as e:
            logger.error(f"❌ Failed to import Indeed scraper: {e}")
            self.scrapers["indeed"]["enabled"] = False
            self.scrapers["indeed"]["module"] = None

        try:
            # Import Prosple scraper
            prosple_path = os.path.join(
                os.path.dirname(os.path.dirname(__file__)), "scraper", "prosple"
            )
            sys.path.append(prosple_path)
            from prosple_scraper import ProspleScraper

            self.scrapers["prosple"]["module"] = ProspleScraper
            logger.info("✅ Prosple scraper imported successfully")
        except ImportError as e:
            logger.error(f"❌ Failed to import Prosple scraper: {e}")
            self.scrapers["prosple"]["enabled"] = False
            self.scrapers["prosple"]["module"] = None

    def _should_run_scraper(self, scraper_name: str) -> bool:
        """Check if a scraper should run based on its interval"""
        scraper_config = self.scrapers[scraper_name]

        if not scraper_config["enabled"]:
            return False

        last_run = scraper_config["last_run"]
        if last_run is None:
            return True

        hours_since_last_run = (datetime.now() - last_run).total_seconds() / 3600
        return hours_since_last_run >= scraper_config["interval_hours"]

    def _run_jobspy_scraper(self) -> bool:
        """Run the JobSpy scraper"""
        try:
            logger.info("🚀 Starting JobSpy scraper...")
            scraper_class = self.scrapers["jobspy"]["module"]
            scraper = scraper_class()

            # Run comprehensive scrape
            success = scraper.run_comprehensive_scrape()

            if success:
                logger.info("✅ JobSpy scraper completed successfully")
                self.scrapers["jobspy"]["last_run"] = datetime.now()
                return True
            else:
                logger.error("❌ JobSpy scraper failed")
                return False

        except Exception as e:
            logger.error(f"❌ JobSpy scraper error: {e}")
            return False

    def _run_linkedin_scraper(self) -> bool:
        """Run the LinkedIn scraper"""
        try:
            logger.info("🚀 Starting LinkedIn scraper...")
            scraper_class = self.scrapers["linkedin"]["module"]
            scraper = scraper_class()

            # Run comprehensive scrape
            success = scraper.run_comprehensive_scrape()

            if success:
                logger.info("✅ LinkedIn scraper completed successfully")
                self.scrapers["linkedin"]["last_run"] = datetime.now()
                return True
            else:
                logger.error("❌ LinkedIn scraper failed")
                return False

        except Exception as e:
            logger.error(f"❌ LinkedIn scraper error: {e}")
            return False

    def _run_indeed_scraper(self) -> bool:
        """Run the Indeed scraper"""
        try:
            logger.info("🚀 Starting Indeed scraper...")
            scraper_class = self.scrapers["indeed"]["module"]
            scraper = scraper_class()

            # Run comprehensive scrape
            success = scraper.run_comprehensive_scrape()

            if success:
                logger.info("✅ Indeed scraper completed successfully")
                self.scrapers["indeed"]["last_run"] = datetime.now()
                return True
            else:
                logger.error("❌ Indeed scraper failed")
                return False

        except Exception as e:
            logger.error(f"❌ Indeed scraper error: {e}")
            return False

    def _run_prosple_scraper(self) -> bool:
        """Run the Prosple scraper"""
        try:
            logger.info("🚀 Starting Prosple scraper...")
            scraper_class = self.scrapers["prosple"]["module"]
            scraper = scraper_class()

            # Run comprehensive scrape
            success = scraper.run_comprehensive_scrape()

            if success:
                logger.info("✅ Prosple scraper completed successfully")
                self.scrapers["prosple"]["last_run"] = datetime.now()
                return True
            else:
                logger.error("❌ Prosple scraper failed")
                return False

        except Exception as e:
            logger.error(f"❌ Prosple scraper error: {e}")
            return False

    def _run_scraper_cycle(self):
        """Run one cycle of all enabled scrapers"""
        self.cycle_count += 1
        logger.info(f"🔄 Scraper cycle #{self.cycle_count} starting")

        scrapers_run = 0

        # Check and run each scraper if needed
        for scraper_name, config in self.scrapers.items():
            if self._should_run_scraper(scraper_name):
                logger.info(f"⏰ Running {scraper_name} scraper (due for run)")

                if scraper_name == "jobspy":
                    success = self._run_jobspy_scraper()
                elif scraper_name == "linkedin":
                    success = self._run_linkedin_scraper()
                elif scraper_name == "indeed":
                    success = self._run_indeed_scraper()
                elif scraper_name == "prosple":
                    success = self._run_prosple_scraper()
                else:
                    logger.info(f"⚠️ {scraper_name} scraper not implemented yet")
                    continue

                if success:
                    scrapers_run += 1
            else:
                next_run_hours = config["interval_hours"] - (
                    (datetime.now() - config["last_run"]).total_seconds() / 3600
                    if config["last_run"]
                    else 0
                )
                logger.info(
                    f"⏳ {scraper_name} scraper not due (next run in {next_run_hours:.1f} hours)"
                )

        if scrapers_run > 0:
            logger.info(
                f"✅ Cycle #{self.cycle_count}: {scrapers_run} scrapers completed"
            )
        else:
            logger.info(f"✅ Cycle #{self.cycle_count}: No scrapers needed to run")

    def _scraper_daemon(self):
        """Main scraper daemon loop"""
        logger.info("🤖 Scraper daemon started")

        # Import scrapers on first run
        self._import_scrapers()

        while self.is_running:
            try:
                self._run_scraper_cycle()

                # Sleep for 1 hour between cycles
                logger.info("😴 Sleeping for 1 hour until next cycle...")
                time.sleep(3600)  # 1 hour

            except Exception as e:
                logger.error(f"❌ Scraper daemon cycle #{self.cycle_count} error: {e}")
                logger.info("⏳ Waiting 10 minutes before retry...")
                time.sleep(600)  # Wait 10 minutes on error

        logger.info("🛑 Scraper daemon stopped")

    def start_daemon(self):
        """Start the scraper daemon in a background thread"""
        if self.is_running:
            logger.warning("⚠️ Scraper daemon is already running")
            return

        self.is_running = True
        self.scraper_thread = threading.Thread(target=self._scraper_daemon, daemon=True)
        self.scraper_thread.start()
        logger.info("🚀 Scraper daemon started in background thread")

    def stop_daemon(self):
        """Stop the scraper daemon"""
        if not self.is_running:
            logger.warning("⚠️ Scraper daemon is not running")
            return

        self.is_running = False
        logger.info("🛑 Scraper daemon stop requested")

    def get_status(self) -> Dict[str, Any]:
        """Get current status of all scrapers"""
        status = {
            "daemon_running": self.is_running,
            "cycle_count": self.cycle_count,
            "scrapers": {},
        }

        for name, config in self.scrapers.items():
            status["scrapers"][name] = {
                "enabled": config["enabled"],
                "interval_hours": config["interval_hours"],
                "last_run": (
                    config["last_run"].isoformat() if config["last_run"] else None
                ),
                "next_run_due": self._should_run_scraper(name),
            }

        return status

    def run_manual_scrape(self, scraper_name: str = "all") -> Dict[str, Any]:
        """Manually trigger a scraper run"""
        if scraper_name == "all":
            logger.info("🔧 Manual scrape requested for all scrapers")
            self._run_scraper_cycle()
            return {"status": "success", "message": "All scrapers triggered"}

        elif scraper_name in self.scrapers:
            if not self.scrapers[scraper_name]["enabled"]:
                return {
                    "status": "error",
                    "message": f"{scraper_name} scraper is disabled",
                }

            logger.info(f"🔧 Manual scrape requested for {scraper_name}")

            if scraper_name == "jobspy":
                success = self._run_jobspy_scraper()
            elif scraper_name == "linkedin":
                success = self._run_linkedin_scraper()

            elif scraper_name == "indeed":
                success = self._run_indeed_scraper()
            elif scraper_name == "prosple":
                success = self._run_prosple_scraper()
            else:
                return {
                    "status": "error",
                    "message": f"{scraper_name} scraper not implemented",
                }

            if success:
                return {
                    "status": "success",
                    "message": f"{scraper_name} scraper completed",
                }
            else:
                return {"status": "error", "message": f"{scraper_name} scraper failed"}

        else:
            return {"status": "error", "message": f"Unknown scraper: {scraper_name}"}
