#!/usr/bin/env python3
"""
Job Data Parser
Transforms raw job data from different sources into canonical normalized format
"""

import json
import psycopg2
import logging
from datetime import datetime
from typing import Dict, Any, Optional
import os

# Try to import OpenAI, handle gracefully if not available
try:
    import openai

    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    openai = None

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("job_data_parser.log"), logging.StreamHandler()],
)
logger = logging.getLogger(__name__)


class JobDataParser:
    """Parse raw job data into canonical normalized format"""

    def __init__(self, openai_api_key: str = None):
        # Database connection
        self.db_url = "postgresql://postgres.upnvhpgaljazlsoryfgj:prAlkIpbQDqOZtOj@aws-0-us-east-1.pooler.supabase.com:6543/postgres"
        self.conn = None
        self.connect_to_database()

        # OpenAI setup
        if openai_api_key and OPENAI_AVAILABLE:
            openai.api_key = openai_api_key
            self.use_ai = True
            logger.info("✅ OpenAI API key configured")
        elif openai_api_key and not OPENAI_AVAILABLE:
            self.use_ai = False
            logger.warning("⚠️  OpenAI package not installed - AI enhancement disabled")
            logger.info("   Install with: pip install openai")
        else:
            self.use_ai = False
            logger.info("⚠️  No OpenAI API key - AI enhancement disabled")

        # Statistics
        self.stats = {
            "total_processed": 0,
            "linkedin_processed": 0,
            "jobspy_processed": 0,
            "ai_enhanced": 0,
            "errors": 0,
        }

    def connect_to_database(self):
        """Connect to PostgreSQL database"""
        try:
            self.conn = psycopg2.connect(self.db_url)
            self.conn.autocommit = True
            logger.info("✅ Connected to database")
            self.setup_canonical_table()
        except Exception as e:
            logger.error(f"❌ Database connection failed: {e}")
            raise

    def setup_canonical_table(self):
        """Create canonical jobs table if it doesn't exist"""
        try:
            with self.conn.cursor() as cur:
                cur.execute(
                    """
                    CREATE TABLE IF NOT EXISTS canonical_jobs (
                        id SERIAL PRIMARY KEY,
                        
                        -- Core job information
                        title TEXT,
                        company TEXT,
                        location TEXT,
                        job_url TEXT,
                        description TEXT,
                        
                        -- Job details (direct mapping only)
                        employment_type TEXT,
                        salary_min DECIMAL,
                        salary_max DECIMAL,
                        salary_currency TEXT DEFAULT 'NGN',

                        -- Contact information
                        email TEXT,
                        whatsapp_number TEXT,
                        application_mode TEXT[], -- Array: linkedin, indeed, jobberman, email, whatsapp

                        -- Location (direct mapping)
                        country TEXT DEFAULT 'Nigeria',
                        
                        -- Dates and metadata
                        posted_date DATE,
                        application_deadline DATE,
                        
                        -- Source tracking
                        source TEXT NOT NULL, -- 'linkedin', 'jobspy', etc.
                        source_job_id TEXT,
                        raw_job_id INTEGER, -- Reference to raw_jobs table
                        
                        -- AI enhancement
                        ai_enhanced BOOLEAN DEFAULT FALSE,
                        ai_enhancement_date TIMESTAMP,
                        
                        -- Timestamps
                        created_at TIMESTAMP DEFAULT NOW(),
                        updated_at TIMESTAMP DEFAULT NOW(),
                        
                        -- Constraints
                        UNIQUE(source, source_job_id)
                    )
                """
                )

                # Create indexes for performance (after table creation)
                try:
                    cur.execute(
                        "CREATE INDEX IF NOT EXISTS idx_canonical_jobs_source ON canonical_jobs(source)"
                    )
                    cur.execute(
                        "CREATE INDEX IF NOT EXISTS idx_canonical_jobs_location ON canonical_jobs(location)"
                    )
                    cur.execute(
                        "CREATE INDEX IF NOT EXISTS idx_canonical_jobs_company ON canonical_jobs(company)"
                    )
                    cur.execute(
                        "CREATE INDEX IF NOT EXISTS idx_canonical_jobs_posted_date ON canonical_jobs(posted_date)"
                    )
                except Exception as e:
                    logger.warning(f"⚠️  Could not create indexes: {e}")

            logger.info("✅ Canonical jobs table ready")
        except Exception as e:
            logger.error(f"❌ Failed to setup canonical table: {e}")
            raise

    def parse_linkedin_job(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """Parse LinkedIn job data into canonical format"""
        try:
            canonical = {
                # Core information
                "title": raw_data.get("title", "").strip(),
                "company": raw_data.get("company", "").strip(),
                "location": raw_data.get("location", "").strip(),
                "job_url": raw_data.get("job_url") or raw_data.get("url", ""),
                "description": raw_data.get("description", "").strip(),
                # Job details
                "employment_type": raw_data.get("employment_type"),
                "experience_level": self.extract_experience_level(raw_data),
                # Company info
                "company_size": raw_data.get("company_size"),
                "industry": raw_data.get("industry"),
                # Location parsing
                "city": self.extract_city(raw_data.get("location", "")),
                "state": self.extract_state(raw_data.get("location", "")),
                "country": "Nigeria",
                "remote_allowed": self.is_remote_job(raw_data),
                # Dates
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
        """Parse JobSpy job data into canonical format"""
        try:
            canonical = {
                # Core information
                "title": raw_data.get("title", "").strip(),
                "company": raw_data.get("company", "").strip(),
                "location": raw_data.get("location", "").strip(),
                "job_url": raw_data.get("job_url", "").strip(),
                "description": raw_data.get("description", "").strip(),
                # Job details
                "employment_type": raw_data.get("job_type"),
                "experience_level": self.extract_experience_level(raw_data),
                # Salary information
                "salary_min": self.parse_salary(raw_data.get("min_amount")),
                "salary_max": self.parse_salary(raw_data.get("max_amount")),
                "salary_currency": raw_data.get("currency", "NGN"),
                # Location parsing
                "city": self.extract_city(raw_data.get("location", "")),
                "state": self.extract_state(raw_data.get("location", "")),
                "country": "Nigeria",
                "remote_allowed": self.is_remote_job(raw_data),
                # Dates
                "posted_date": self.parse_date(raw_data.get("date_posted")),
                # Source tracking
                "source": "jobspy",
                "source_job_id": raw_data.get("id"),
            }

            return canonical

        except Exception as e:
            logger.error(f"❌ Failed to parse JobSpy job: {e}")
            return None

    def extract_experience_level(self, raw_data: Dict[str, Any]) -> Optional[str]:
        """Extract experience level from job data"""
        title = (
            raw_data.get("title", "") + " " + raw_data.get("description", "")
        ).lower()

        if any(
            word in title
            for word in ["intern", "internship", "graduate", "entry", "junior"]
        ):
            return "Entry"
        elif any(word in title for word in ["senior", "lead", "principal", "staff"]):
            return "Senior"
        elif any(word in title for word in ["manager", "director", "head", "chief"]):
            return "Executive"
        else:
            return "Mid"

    def extract_city(self, location: str) -> Optional[str]:
        """Extract city from location string"""
        if not location:
            return None

        # Common Nigerian cities
        cities = [
            "Lagos",
            "Abuja",
            "Port Harcourt",
            "Kano",
            "Ibadan",
            "Kaduna",
            "Benin City",
            "Jos",
            "Warri",
            "Calabar",
            "Enugu",
            "Onitsha",
        ]

        location_lower = location.lower()
        for city in cities:
            if city.lower() in location_lower:
                return city

        # Extract first part before comma
        parts = location.split(",")
        if parts:
            return parts[0].strip()

        return None

    def extract_state(self, location: str) -> Optional[str]:
        """Extract state from location string"""
        if not location:
            return None

        # Nigerian states mapping
        state_mapping = {
            "lagos": "Lagos",
            "abuja": "FCT",
            "port harcourt": "Rivers",
            "kano": "Kano",
            "ibadan": "Oyo",
            "kaduna": "Kaduna",
            "benin": "Edo",
            "jos": "Plateau",
            "warri": "Delta",
            "calabar": "Cross River",
            "enugu": "Enugu",
            "onitsha": "Anambra",
        }

        location_lower = location.lower()
        for key, state in state_mapping.items():
            if key in location_lower:
                return state

        return None

    def is_remote_job(self, raw_data: Dict[str, Any]) -> bool:
        """Determine if job allows remote work"""
        text = (
            raw_data.get("title", "")
            + " "
            + raw_data.get("description", "")
            + " "
            + raw_data.get("location", "")
        ).lower()

        remote_keywords = [
            "remote",
            "work from home",
            "wfh",
            "telecommute",
            "distributed",
        ]
        return any(keyword in text for keyword in remote_keywords)

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

    def enhance_with_ai(self, canonical_job: Dict[str, Any]) -> Dict[str, Any]:
        """Use OpenAI to enhance job data with missing fields"""
        if not self.use_ai:
            return canonical_job

        try:
            # Prepare prompt for AI enhancement
            prompt = f"""
            Analyze this Nigerian job posting and extract/infer the missing information:
            
            Title: {canonical_job.get('title', 'N/A')}
            Company: {canonical_job.get('company', 'N/A')}
            Description: {canonical_job.get('description', 'N/A')[:500]}...
            
            Please provide a JSON response with these fields (only include if you can reasonably infer):
            - required_skills: Array of key technical skills required
            - preferred_skills: Array of nice-to-have skills
            - education_requirements: Education level needed
            - years_experience_min: Minimum years of experience
            - years_experience_max: Maximum years of experience
            - company_size: Startup/Small/Medium/Large/Enterprise
            - industry: Industry sector
            
            Only include fields you're confident about. Return valid JSON only.
            """

            response = openai.ChatCompletion.create(
                model="gpt-4.1-nano",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=500,
                temperature=0.3,
            )

            ai_data = json.loads(response.choices[0].message.content)

            # Merge AI data with canonical job
            for key, value in ai_data.items():
                if key in ["required_skills", "preferred_skills"] and isinstance(
                    value, list
                ):
                    canonical_job[key] = value
                elif value and key not in canonical_job:
                    canonical_job[key] = value

            canonical_job["ai_enhanced"] = True
            canonical_job["ai_enhancement_date"] = datetime.now().isoformat()
            self.stats["ai_enhanced"] += 1

            logger.debug(
                f"✅ AI enhanced job: {canonical_job.get('title', 'N/A')[:30]}"
            )

        except Exception as e:
            logger.debug(f"⚠️  AI enhancement failed: {e}")

        return canonical_job

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
                    logger.debug(
                        f"✅ Saved canonical job: {canonical_job.get('title', 'N/A')[:30]}"
                    )
                    return True
                else:
                    logger.debug(
                        f"🔄 Updated canonical job: {canonical_job.get('title', 'N/A')[:30]}"
                    )
                    return True

        except Exception as e:
            logger.error(f"❌ Failed to save canonical job: {e}")
            logger.error(f"   Title: {canonical_job.get('title', 'N/A')[:50]}")
            return False

    def process_raw_jobs(self, source: str = None, limit: int = None):
        """Process raw jobs into canonical format"""
        logger.info("🚀 Starting Job Data Parsing")
        logger.info("=" * 50)

        try:
            # Build query
            where_clause = ""
            params = []

            if source:
                where_clause = "WHERE source = %s"
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

                    # Enhance with AI if available
                    if self.use_ai:
                        canonical_job = self.enhance_with_ai(canonical_job)

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
            logger.info("🎉 Job data parsing completed!")
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
        logger.info(f"   AI enhanced: {self.stats['ai_enhanced']:,}")
        logger.info(f"   Errors: {self.stats['errors']:,}")

        if self.stats["total_processed"] > 0:
            success_rate = (
                (self.stats["total_processed"] - self.stats["errors"])
                / self.stats["total_processed"]
            ) * 100
            logger.info(f"   Success rate: {success_rate:.1f}%")


def main():
    """Main function"""
    print("🔄 Job Data Parser")
    print("=" * 30)

    # Get OpenAI API key
    openai_key = input(
        "Enter OpenAI API key (or press Enter to skip AI enhancement): "
    ).strip()
    if not openai_key:
        openai_key = None
        print("⚠️  Proceeding without AI enhancement")

    print("\nChoose processing option:")
    print("1. Process all sources")
    print("2. Process LinkedIn jobs only")
    print("3. Process JobSpy jobs only")
    print("4. Process limited batch (100 jobs)")

    choice = input("Enter choice (1-4): ").strip()

    try:
        parser = JobDataParser(openai_api_key=openai_key)

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

        print("\n🎉 Job data parsing completed!")
        print("💾 Canonical jobs saved to canonical_jobs table")

    except Exception as e:
        logger.error(f"❌ Parsing failed: {e}")


if __name__ == "__main__":
    main()
