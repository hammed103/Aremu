#!/usr/bin/env python3
"""
Fixed Nigeria JobSpy Scraper - Handles Date Serialization
Fixes the JSON encoding error for date objects
"""

import pandas as pd
import time
import logging
import psycopg2
import json
import hashlib
from datetime import datetime, date
from jobspy import scrape_jobs

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("fixed_jobspy.log"), logging.StreamHandler()],
)
logger = logging.getLogger(__name__)


class FixedDatabaseJobScraper:
    def __init__(self):
        """Initialize scraper with date handling fix"""

        # Database connection
        self.db_url = "postgresql://postgres.upnvhpgaljazlsoryfgj:prAlkIpbQDqOZtOj@aws-0-us-east-1.pooler.supabase.com:6543/postgres"
        self.conn = None
        self.connect_to_database()

        # Scraping configuration
        self.config = {
            "results_wanted": 100,
            "hours_old": 168,
            "delay_between_searches": 3,
            "linkedin_fetch_description": True,
            "use_proxy": False,
        }

        # Nigerian locations
        self.locations = [
            "Lagos, Nigeria",
            "Abuja, Nigeria",
            "Port Harcourt, Nigeria",
            "Kano, Nigeria",
            "Ibadan, Nigeria",
            "Kaduna, Nigeria",
            "Benin City, Nigeria",
            "Jos, Nigeria",
            "Warri, Nigeria",
            "Calabar, Nigeria",
            "Nigeria",
        ]

        # Search terms
        self.search_terms = [
            "",
            "software engineer",
            "data analyst",
            "project manager",
            "sales manager",
            "marketing manager",
            "accountant",
            "human resources",
            "customer service",
            "business analyst",
            "operations manager",
            "finance manager",
            "engineer",
            "developer",
            "analyst",
            "manager",
            "remote",
            "oil and gas",
            "banking",
            "telecommunications",
        ]

        self.job_sites = ["indeed", "linkedin", "google"]

        # Statistics
        self.stats = {
            "total_scraped": 0,
            "total_saved": 0,
            "duplicates_skipped": 0,
            "errors": 0,
        }

    def connect_to_database(self):
        """Connect to PostgreSQL database"""
        try:
            self.conn = psycopg2.connect(self.db_url)
            self.conn.autocommit = True
            logger.info("✅ Connected to database")
            self.setup_database()
        except Exception as e:
            logger.error(f"❌ Database connection failed: {e}")
            raise

    def setup_database(self):
        """Ensure raw_jobs table exists"""
        try:
            with self.conn.cursor() as cur:
                cur.execute(
                    """
                    CREATE TABLE IF NOT EXISTS raw_jobs (
                        id SERIAL PRIMARY KEY,
                        source TEXT NOT NULL,
                        source_job_id TEXT,
                        raw_data JSONB NOT NULL,
                        source_url TEXT,
                        scraped_at TIMESTAMP DEFAULT NOW(),
                        created_at TIMESTAMP DEFAULT NOW(),
                        UNIQUE(source, source_job_id)
                    )
                """
                )
            logger.info("✅ Database schema ready")
        except Exception as e:
            logger.error(f"❌ Database setup failed: {e}")
            raise

    def generate_job_id(self, job_data):
        """Generate unique job ID"""
        title = str(job_data.get("title", "")).lower().strip()
        company = str(job_data.get("company", "")).lower().strip()
        job_url = str(job_data.get("job_url", "")).strip()

        if job_url:
            return hashlib.md5(job_url.encode()).hexdigest()
        else:
            unique_string = f"{title}_{company}"
            return hashlib.md5(unique_string.encode()).hexdigest()

    def convert_dates_to_strings(self, job_data):
        """Convert date objects to ISO format strings for JSON serialization"""
        converted_data = {}

        for key, value in job_data.items():
            if isinstance(value, (date, datetime)):
                # Convert date/datetime to ISO format string
                converted_data[key] = value.isoformat()
            elif pd.isna(value) or value is None:
                # Keep None values as None
                converted_data[key] = None
            else:
                # Keep other values as-is
                converted_data[key] = value

        return converted_data

    def save_jobs_to_database(self, jobs_df, search_context):
        """Save jobs with proper date handling"""
        if jobs_df is None or len(jobs_df) == 0:
            return 0

        saved_count = 0

        try:
            with self.conn.cursor() as cur:
                for job_index, job in jobs_df.iterrows():
                    try:
                        # Convert to dict and handle NaN values
                        job_data = job.to_dict()
                        job_data = {
                            k: (v if pd.notna(v) else None) for k, v in job_data.items()
                        }

                        # Convert date objects to strings
                        job_data = self.convert_dates_to_strings(job_data)

                        # Validate essential fields
                        title = (
                            str(job_data.get("title", "")).strip()
                            if job_data.get("title")
                            else ""
                        )
                        company = (
                            str(job_data.get("company", "")).strip()
                            if job_data.get("company")
                            else ""
                        )

                        if not title and not company:
                            logger.debug(
                                f"⚠️  Job {job_index}: Missing both title and company"
                            )
                            self.stats["errors"] += 1
                            continue

                        # Generate job ID
                        job_id = self.generate_job_id(job_data)

                        # Add metadata
                        job_data["search_context"] = search_context
                        job_data["scraped_timestamp"] = datetime.now().isoformat()

                        # JSON serialization should work now
                        json_data = json.dumps(job_data, ensure_ascii=False)

                        # Insert into database
                        cur.execute(
                            """
                            INSERT INTO raw_jobs (source, source_job_id, raw_data, source_url, scraped_at)
                            VALUES (%s, %s, %s, %s, NOW())
                            ON CONFLICT (source, source_job_id) DO NOTHING
                        """,
                            ("jobspy", job_id, json_data, job_data.get("job_url")),
                        )

                        if cur.rowcount > 0:
                            saved_count += 1
                            self.stats["total_saved"] += 1
                            logger.debug(f"✅ Saved: {title[:30]} at {company[:20]}")
                        else:
                            self.stats["duplicates_skipped"] += 1
                            logger.debug(
                                f"🔄 Duplicate: {title[:30]} at {company[:20]}"
                            )

                    except Exception as e:
                        logger.error(f"❌ Job {job_index}: {e}")
                        logger.error(f"   Title: {job_data.get('title', 'N/A')[:50]}")
                        logger.error(
                            f"   Company: {job_data.get('company', 'N/A')[:30]}"
                        )
                        self.stats["errors"] += 1
                        continue

        except Exception as e:
            logger.error(f"❌ Database save failed: {e}")
            self.stats["errors"] += 1

        return saved_count

    def show_database_status(self):
        """Show current database status after each query"""
        try:
            with self.conn.cursor() as cur:
                cur.execute("SELECT COUNT(*) FROM raw_jobs WHERE source = 'jobspy'")
                total_jobspy = cur.fetchone()[0]
                logger.info(f"   💾 Database: {total_jobspy} total JobSpy jobs stored")
        except Exception as e:
            logger.debug(f"Failed to get database status: {e}")

    def scrape_and_save(self, search_term, location, search_context):
        """Scrape jobs and save to database"""
        logger.info(f"🔍 Scraping: '{search_term}' in {location}")

        try:
            jobs = scrape_jobs(
                site_name=self.job_sites,
                search_term=search_term,
                location=location,
                results_wanted=self.config["results_wanted"],
                hours_old=self.config["hours_old"],
                country_indeed="Nigeria",
                linkedin_fetch_description=self.config["linkedin_fetch_description"],
            )

            if jobs is not None and len(jobs) > 0:
                self.stats["total_scraped"] += len(jobs)

                # Save to database IMMEDIATELY after scraping this query
                saved = self.save_jobs_to_database(jobs, search_context)

                logger.info(
                    f"   ✅ Query complete: {len(jobs)} scraped, {saved} saved to database"
                )
                logger.info(
                    f"   📊 Running totals: {self.stats['total_scraped']} scraped, {self.stats['total_saved']} saved"
                )

                # Show database status
                self.show_database_status()

                return saved
            else:
                logger.info(f"   ⚠️  No jobs found for this query")
                return 0

        except Exception as e:
            logger.error(f"   ❌ Scraping failed: {e}")
            self.stats["errors"] += 1
            return 0

    def run_test_scrape(self):
        """Run a test scrape to validate the fix"""
        logger.info("🧪 Testing Fixed JobSpy Scraper")
        logger.info("=" * 40)

        # Test with one search
        saved = self.scrape_and_save("software engineer", "Lagos, Nigeria", "test_fix")

        # Show results
        logger.info(f"\n📊 Test Results:")
        logger.info(f"   Total scraped: {self.stats['total_scraped']}")
        logger.info(f"   Total saved: {self.stats['total_saved']}")
        logger.info(f"   Duplicates skipped: {self.stats['duplicates_skipped']}")
        logger.info(f"   Errors: {self.stats['errors']}")

        if self.stats["total_scraped"] > 0:
            success_rate = (
                self.stats["total_saved"] / self.stats["total_scraped"]
            ) * 100
            logger.info(f"   Success rate: {success_rate:.1f}%")

        return saved > 0

    def run_comprehensive_scrape(self):
        """Run comprehensive scraping with IMMEDIATE batch saving"""
        logger.info("🚀 Starting Comprehensive Nigeria Job Scraping (FIXED)")
        logger.info("💾 BATCH SAVING: Jobs saved immediately after each query")
        logger.info("=" * 60)

        start_time = datetime.now()
        total_searches = len(self.locations) * len(self.search_terms)
        current_search = 0

        try:
            for location in self.locations:
                for search_term in self.search_terms:
                    current_search += 1
                    search_context = f"location_term_{location}_{search_term}"

                    logger.info(f"📦 Search {current_search}/{total_searches}")
                    self.scrape_and_save(search_term, location, search_context)

                    # Progress update
                    if current_search % 10 == 0:
                        logger.info(
                            f"📊 Progress: {self.stats['total_saved']} saved so far"
                        )

                    # Rate limiting
                    time.sleep(self.config["delay_between_searches"])

            # Final statistics
            end_time = datetime.now()
            duration = end_time - start_time

            logger.info("🎉 Comprehensive scraping completed!")
            logger.info(f"⏱️  Duration: {duration}")
            self.show_final_stats()

        except KeyboardInterrupt:
            logger.info("🛑 Scraping interrupted by user")
            self.show_final_stats()
        except Exception as e:
            logger.error(f"❌ Scraping failed: {e}")
            self.show_final_stats()
            raise
        finally:
            if self.conn:
                self.conn.close()
                logger.info("🔌 Database connection closed")

    def show_final_stats(self):
        """Show final statistics"""
        logger.info("📊 FINAL STATISTICS:")
        logger.info(f"   Total scraped: {self.stats['total_scraped']:,}")
        logger.info(f"   Total saved: {self.stats['total_saved']:,}")
        logger.info(f"   Duplicates skipped: {self.stats['duplicates_skipped']:,}")
        logger.info(f"   Errors: {self.stats['errors']:,}")

        if self.stats["total_scraped"] > 0:
            success_rate = (
                self.stats["total_saved"] / self.stats["total_scraped"]
            ) * 100
            logger.info(f"   Success rate: {success_rate:.1f}%")


def main():
    """Main function"""
    scraper = FixedDatabaseJobScraper()

    print("🔧 Fixed JobSpy Scraper")
    print("Choose option:")
    print("1. Test fix (recommended)")
    print("2. Run comprehensive scraping")

    choice = input("Enter choice (1-2): ").strip()

    if choice == "1":
        try:
            success = scraper.run_test_scrape()
            if success:
                print("\n🎉 Fix successful! Date serialization working!")
                print("💡 Ready to run comprehensive scraping")
            else:
                print("\n❌ Fix test failed")
        except Exception as e:
            logger.error(f"❌ Test failed: {e}")

    elif choice == "2":
        try:
            scraper.run_comprehensive_scrape()
            print("\n🎉 Comprehensive scraping completed!")
        except Exception as e:
            logger.error(f"❌ Comprehensive scraping failed: {e}")

    else:
        print("Invalid choice")


if __name__ == "__main__":
    main()
