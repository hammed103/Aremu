#!/usr/bin/env python3
"""
Simple Job Data Parser
Direct field mapping with application mode detection
"""

import json
import psycopg2
import logging
import re
from datetime import datetime
from typing import Dict, Any, Optional, List

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("simple_parser.log"), logging.StreamHandler()],
)
logger = logging.getLogger(__name__)


class SimpleJobParser:
    """Simple parser focusing on direct field mapping and application modes"""

    def __init__(self):
        # Database connection
        self.db_url = "postgresql://postgres.upnvhpgaljazlsoryfgj:prAlkIpbQDqOZtOj@aws-0-us-east-1.pooler.supabase.com:6543/postgres"
        self.conn = None
        self.connect_to_database()

        # Statistics
        self.stats = {
            "total_processed": 0,
            "linkedin_processed": 0,
            "jobspy_processed": 0,
            "errors": 0,
        }

    def connect_to_database(self):
        """Connect to PostgreSQL database"""
        try:
            self.conn = psycopg2.connect(self.db_url)
            self.conn.autocommit = True
            logger.info("✅ Connected to database")
        except Exception as e:
            logger.error(f"❌ Database connection failed: {e}")
            raise

    def extract_email(self, text: str) -> Optional[str]:
        """Extract email from text"""
        if not text:
            return None

        email_pattern = r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"
        emails = re.findall(email_pattern, text)
        return emails[0] if emails else None

    def extract_whatsapp(self, text: str) -> Optional[str]:
        """Extract WhatsApp number from text"""
        if not text:
            return None

        # Nigerian phone number patterns
        phone_patterns = [
            r"\+234[0-9]{10}",  # +234xxxxxxxxxx
            r"234[0-9]{10}",  # 234xxxxxxxxxx
            r"0[789][01][0-9]{8}",  # 08xxxxxxxxx, 09xxxxxxxxx, 07xxxxxxxxx
            r"[789][01][0-9]{8}",  # 8xxxxxxxxx, 9xxxxxxxxx, 7xxxxxxxxx
        ]

        for pattern in phone_patterns:
            phones = re.findall(pattern, text)
            if phones:
                return phones[0]

        return None

    def determine_application_modes(
        self, job_url: str, email: str, whatsapp: str
    ) -> List[str]:
        """Determine application modes based on URL and contact info"""
        modes = []

        # Check job URL for platform
        if job_url:
            url_lower = job_url.lower()
            if "linkedin.com" in url_lower:
                modes.append("linkedin")
            elif "indeed.com" in url_lower:
                modes.append("indeed")
            elif "jobberman.com" in url_lower:
                modes.append("jobberman")

        # Add contact methods
        if email:
            modes.append("email")
        if whatsapp:
            modes.append("whatsapp")

        return modes

    def parse_salary(self, salary_value) -> Optional[float]:
        """Parse salary value"""
        if not salary_value:
            return None

        try:
            if isinstance(salary_value, (int, float)):
                return float(salary_value)
            elif isinstance(salary_value, str):
                # Remove currency symbols and commas
                cleaned = (
                    salary_value.replace(",", "")
                    .replace("₦", "")
                    .replace("NGN", "")
                    .strip()
                )
                return float(cleaned) if cleaned else None
        except:
            return None

    def parse_date(self, date_value) -> Optional[str]:
        """Parse date from various formats"""
        if not date_value:
            return None

        try:
            if isinstance(date_value, str):
                # Try to parse ISO format
                if "T" in date_value:
                    return (
                        datetime.fromisoformat(date_value.replace("Z", "+00:00"))
                        .date()
                        .isoformat()
                    )
                else:
                    return datetime.fromisoformat(date_value).date().isoformat()
            elif hasattr(date_value, "isoformat"):
                return date_value.isoformat()
            else:
                return str(date_value)
        except:
            return None

    def parse_linkedin_job(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """Parse LinkedIn job - direct mapping only"""
        try:
            # Get job URL and description for contact extraction
            job_url = raw_data.get("job_url") or raw_data.get("url", "")
            description = raw_data.get("description", "").strip()

            # Extract contact information and application modes
            email = self.extract_email(description)
            whatsapp = self.extract_whatsapp(description)
            application_modes = self.determine_application_modes(
                job_url, email, whatsapp
            )

            canonical = {
                # Core information (direct mapping)
                "title": raw_data.get("title", "").strip(),
                "company": raw_data.get("company", "").strip(),
                "location": raw_data.get("location", "").strip(),
                "job_url": job_url,
                "description": description,
                # Job details (direct mapping only)
                "employment_type": raw_data.get("employment_type"),
                "salary_min": self.parse_salary(raw_data.get("salary_min")),
                "salary_max": self.parse_salary(raw_data.get("salary_max")),
                "salary_currency": raw_data.get("salary_currency", "NGN"),
                # Contact information
                "email": email,
                "whatsapp_number": whatsapp,
                "application_mode": application_modes,
                # Location (direct mapping)
                "country": "Nigeria",
                # Dates (direct mapping)
                "posted_date": self.parse_date(
                    raw_data.get("posted_date") or raw_data.get("date_posted")
                ),
                # Source tracking
                "source": "linkedin",
                "source_job_id": raw_data.get("job_id") or raw_data.get("id"),
            }

            return canonical

        except Exception as e:
            logger.error(f"❌ Failed to parse LinkedIn job: {e}")
            return None

    def parse_jobspy_job(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """Parse JobSpy job - direct mapping only"""
        try:
            # Get job URL and description for contact extraction
            job_url = raw_data.get("job_url", "").strip()
            description = raw_data.get("description", "").strip()

            # Extract contact information and application modes
            email = self.extract_email(description)
            whatsapp = self.extract_whatsapp(description)
            application_modes = self.determine_application_modes(
                job_url, email, whatsapp
            )

            canonical = {
                # Core information (direct mapping)
                "title": raw_data.get("title", "").strip(),
                "company": raw_data.get("company", "").strip(),
                "location": raw_data.get("location", "").strip(),
                "job_url": job_url,
                "description": description,
                # Job details (direct mapping only)
                "employment_type": raw_data.get("job_type"),
                "salary_min": self.parse_salary(raw_data.get("min_amount")),
                "salary_max": self.parse_salary(raw_data.get("max_amount")),
                "salary_currency": raw_data.get("currency", "NGN"),
                # Contact information
                "email": email,
                "whatsapp_number": whatsapp,
                "application_mode": application_modes,
                # Location (direct mapping)
                "country": "Nigeria",
                # Dates (direct mapping)
                "posted_date": self.parse_date(raw_data.get("date_posted")),
                # Source tracking
                "source": "jobspy",
                "source_job_id": raw_data.get("id"),
            }

            return canonical

        except Exception as e:
            logger.error(f"❌ Failed to parse JobSpy job: {e}")
            return None

    def save_canonical_job(
        self, canonical_job: Dict[str, Any], raw_job_id: int
    ) -> bool:
        """Save canonical job to database"""
        try:
            canonical_job["raw_job_id"] = raw_job_id

            # Prepare SQL
            columns = []
            values = []
            placeholders = []

            for key, value in canonical_job.items():
                if value is not None:
                    columns.append(key)
                    values.append(value)
                    placeholders.append("%s")

            sql = f"""
                INSERT INTO canonical_jobs ({', '.join(columns)})
                VALUES ({', '.join(placeholders)})
                ON CONFLICT (source, source_job_id) 
                DO UPDATE SET 
                    {', '.join([f"{col} = EXCLUDED.{col}" for col in columns if col not in ['source', 'source_job_id']])},
                    updated_at = NOW()
            """

            with self.conn.cursor() as cur:
                cur.execute(sql, values)

                if cur.rowcount > 0:
                    logger.debug(f"✅ Saved: {canonical_job.get('title', 'N/A')[:30]}")
                    return True
                else:
                    logger.debug(
                        f"🔄 Updated: {canonical_job.get('title', 'N/A')[:30]}"
                    )
                    return True

        except Exception as e:
            logger.error(f"❌ Failed to save job: {e}")
            return False

    def process_raw_jobs(self, source: str = None, limit: int = None):
        """Process raw jobs into canonical format"""
        logger.info("🚀 Starting Simple Job Data Parsing")
        logger.info("💡 Direct field mapping + application mode detection")
        logger.info("=" * 50)

        try:
            # Build query
            where_clause = ""
            params = []

            if source:
                where_clause = "WHERE r.source = %s"
                params.append(source)

            limit_clause = ""
            if limit:
                limit_clause = f"LIMIT {limit}"

            # Get raw jobs that haven't been processed
            with self.conn.cursor() as cur:
                # Check if canonical_jobs table exists
                cur.execute(
                    """
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables
                        WHERE table_name = 'canonical_jobs'
                    )
                """
                )
                table_exists = cur.fetchone()[0]

                if table_exists:
                    # Query with LEFT JOIN to exclude already processed jobs
                    cur.execute(
                        f"""
                        SELECT r.id, r.source, r.raw_data, r.source_job_id
                        FROM raw_jobs r
                        LEFT JOIN canonical_jobs c ON r.source = c.source AND r.source_job_id = c.source_job_id
                        WHERE c.id IS NULL
                        {f"AND r.source = %s" if source else ""}
                        ORDER BY r.created_at DESC
                        {limit_clause}
                    """,
                        params,
                    )
                else:
                    # Table doesn't exist yet, get all raw jobs
                    cur.execute(
                        f"""
                        SELECT id, source, raw_data, source_job_id
                        FROM raw_jobs
                        {where_clause}
                        ORDER BY created_at DESC
                        {limit_clause}
                    """,
                        params,
                    )

                raw_jobs = cur.fetchall()

            logger.info(f"📦 Found {len(raw_jobs)} raw jobs to process")

            if not raw_jobs:
                logger.info("✅ No new jobs to process")
                return

            # Process each job
            for raw_job_id, source, raw_data_json, source_job_id in raw_jobs:
                try:
                    self.stats["total_processed"] += 1

                    # Parse JSON data
                    if isinstance(raw_data_json, str):
                        raw_data = json.loads(raw_data_json)
                    else:
                        raw_data = raw_data_json

                    # Parse based on source
                    if source == "linkedin":
                        canonical_job = self.parse_linkedin_job(raw_data)
                        self.stats["linkedin_processed"] += 1
                    elif source == "jobspy":
                        canonical_job = self.parse_jobspy_job(raw_data)
                        self.stats["jobspy_processed"] += 1
                    else:
                        logger.warning(f"⚠️  Unknown source: {source}")
                        continue

                    if not canonical_job:
                        logger.warning(f"⚠️  Failed to parse job from {source}")
                        self.stats["errors"] += 1
                        continue

                    # Save to canonical table
                    success = self.save_canonical_job(canonical_job, raw_job_id)

                    if not success:
                        self.stats["errors"] += 1

                    # Progress update
                    if self.stats["total_processed"] % 50 == 0:
                        logger.info(
                            f"📊 Progress: {self.stats['total_processed']} processed"
                        )

                except Exception as e:
                    logger.error(f"❌ Failed to process job {raw_job_id}: {e}")
                    self.stats["errors"] += 1
                    continue

            # Final statistics
            logger.info("🎉 Simple parsing completed!")
            self.show_final_stats()

        except Exception as e:
            logger.error(f"❌ Processing failed: {e}")
            self.show_final_stats()
            raise
        finally:
            if self.conn:
                self.conn.close()
                logger.info("🔌 Database connection closed")

    def show_final_stats(self):
        """Show final processing statistics"""
        logger.info("📊 FINAL STATISTICS:")
        logger.info(f"   Total processed: {self.stats['total_processed']:,}")
        logger.info(f"   LinkedIn jobs: {self.stats['linkedin_processed']:,}")
        logger.info(f"   JobSpy jobs: {self.stats['jobspy_processed']:,}")
        logger.info(f"   Errors: {self.stats['errors']:,}")

        if self.stats["total_processed"] > 0:
            success_rate = (
                (self.stats["total_processed"] - self.stats["errors"])
                / self.stats["total_processed"]
            ) * 100
            logger.info(f"   Success rate: {success_rate:.1f}%")


def main():
    """Main function"""
    print("🔄 Simple Job Data Parser")
    print("💡 Direct mapping + application modes")
    print("=" * 40)

    print("Choose processing option:")
    print("1. Process all sources")
    print("2. Process LinkedIn jobs only")
    print("3. Process JobSpy jobs only")
    print("4. Process limited batch (100 jobs)")

    choice = input("Enter choice (1-4): ").strip()

    try:
        parser = SimpleJobParser()

        if choice == "1":
            parser.process_raw_jobs()
        elif choice == "2":
            parser.process_raw_jobs(source="linkedin")
        elif choice == "3":
            parser.process_raw_jobs(source="jobspy")
        elif choice == "4":
            parser.process_raw_jobs(limit=100)
        else:
            print("Invalid choice")
            return

        print("\n🎉 Simple parsing completed!")
        print("💾 Jobs saved to canonical_jobs table")
        print("📱 Application modes detected")

    except Exception as e:
        logger.error(f"❌ Parsing failed: {e}")


if __name__ == "__main__":
    main()
