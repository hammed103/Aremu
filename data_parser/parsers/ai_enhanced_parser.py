#!/usr/bin/env python3
"""
AI Enhanced Job Data Parser
Direct field mapping with AI enhancement using OpenAI
"""

import json
import psycopg2
import logging
import re
import os
from datetime import datetime
from typing import Dict, Any, Optional, List
from dotenv import load_dotenv

# Try to import OpenAI
try:
    from openai import OpenAI

    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    OpenAI = None

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("ai_enhanced_parser.log"), logging.StreamHandler()],
)
logger = logging.getLogger(__name__)


class AIEnhancedJobParser:
    """AI Enhanced parser with direct field mapping and OpenAI enhancement"""

    def __init__(self):
        # Database connection
        self.db_url = "postgresql://postgres.upnvhpgaljazlsoryfgj:prAlkIpbQDqOZtOj@aws-0-us-east-1.pooler.supabase.com:6543/postgres"
        self.conn = None
        self.connect_to_database()

        # OpenAI setup
        self.setup_openai()

        # Statistics
        self.stats = {
            "total_processed": 0,
            "linkedin_processed": 0,
            "jobspy_processed": 0,
            "ai_enhanced": 0,
            "errors": 0,
        }

    def setup_openai(self):
        """Setup OpenAI client"""
        openai_key = os.getenv("OPENAI_API_KEY")

        if openai_key and OPENAI_AVAILABLE:
            try:
                self.openai_client = OpenAI(api_key=openai_key)
                self.use_ai = True
                logger.info("✅ OpenAI API key loaded from .env file")
            except Exception as e:
                self.use_ai = False
                logger.warning(f"⚠️  OpenAI setup failed: {e}")
        elif openai_key and not OPENAI_AVAILABLE:
            self.use_ai = False
            logger.warning("⚠️  OpenAI package not installed")
        else:
            self.use_ai = False
            logger.info("⚠️  No OpenAI API key found in .env file")

    def connect_to_database(self):
        """Connect to PostgreSQL database"""
        try:
            self.conn = psycopg2.connect(self.db_url)
            self.conn.autocommit = True
            logger.info("✅ Connected to database")
            self.setup_enhanced_canonical_table()
        except Exception as e:
            logger.error(f"❌ Database connection failed: {e}")
            raise

    def setup_enhanced_canonical_table(self):
        """Create enhanced canonical jobs table with all AI fields"""
        try:
            with self.conn.cursor() as cur:
                cur.execute(
                    """
                    CREATE TABLE IF NOT EXISTS canonical_jobs (
                        id SERIAL PRIMARY KEY,

                        -- Core job information (direct from scraped data)
                        title TEXT,
                        company TEXT,
                        location TEXT,
                        job_url TEXT,
                        job_url_direct TEXT,
                        description TEXT,
                        site TEXT, -- linkedin, indeed, etc.

                        -- Job classification (direct from scraped data)
                        employment_type TEXT,
                        job_type TEXT, -- alias for employment_type
                        job_function TEXT,
                        job_level TEXT,
                        experience_level TEXT, -- alias for job_level
                        seniority_level TEXT,
                        industry TEXT,
                        industries TEXT,

                        -- Salary information (direct from scraped data)
                        salary_min DECIMAL,
                        salary_max DECIMAL,
                        min_amount DECIMAL, -- alias for salary_min
                        max_amount DECIMAL, -- alias for salary_max
                        salary_currency TEXT DEFAULT 'NGN',
                        currency TEXT, -- alias for salary_currency

                        -- Location details (direct from scraped data)
                        city TEXT,
                        state TEXT,
                        country TEXT DEFAULT 'Nigeria',
                        is_remote BOOLEAN DEFAULT FALSE,
                        remote_allowed BOOLEAN DEFAULT FALSE,
                        work_arrangement TEXT,

                        -- Company information (direct from scraped data)
                        company_url TEXT,
                        company_logo TEXT,
                        company_addresses TEXT,
                        company_industry TEXT,
                        company_num_employees TEXT,
                        company_revenue TEXT,
                        company_description TEXT,
                        company_size TEXT,
                        ceo_name TEXT,
                        ceo_photo_url TEXT,
                        logo_photo_url TEXT,
                        banner_photo_url TEXT,

                        -- Contact and application (direct from scraped data)
                        emails TEXT, -- JSON array as text
                        phones TEXT, -- JSON array as text
                        application_mode TEXT, -- JSON array as text

                        -- Skills and requirements (direct from scraped data)
                        skills TEXT, -- JSON array as text
                        required_skills TEXT, -- JSON array as text
                        preferred_skills TEXT, -- JSON array as text
                        education_requirements TEXT,
                        years_experience_min INTEGER,
                        years_experience_max INTEGER,

                        -- Benefits and additional info (direct from scraped data)
                        benefits TEXT, -- JSON array as text

                        -- Dates (direct from scraped data)
                        date_posted DATE,
                        posted_date DATE, -- alias for date_posted
                        application_deadline DATE,

                        -- Source tracking
                        source TEXT NOT NULL,
                        source_job_id TEXT,
                        raw_job_id INTEGER,

                        -- AI-INFERRED FIELDS (clearly separated with ai_ prefix)
                        ai_email TEXT,
                        ai_whatsapp_number TEXT,
                        ai_application_modes TEXT, -- JSON array as text
                        ai_city TEXT,
                        ai_state TEXT,
                        ai_country TEXT,
                        ai_employment_type TEXT,
                        ai_job_function TEXT,
                        ai_job_level TEXT,
                        ai_industry TEXT,
                        ai_salary_min DECIMAL,
                        ai_salary_max DECIMAL,
                        ai_salary_currency TEXT,
                        ai_compensation_summary TEXT,
                        ai_required_skills TEXT, -- JSON array as text
                        ai_preferred_skills TEXT, -- JSON array as text
                        ai_education_requirements TEXT,
                        ai_years_experience_min INTEGER,
                        ai_years_experience_max INTEGER,
                        ai_remote_allowed BOOLEAN,
                        ai_work_arrangement TEXT,
                        ai_benefits TEXT, -- JSON array as text
                        ai_application_deadline DATE,
                        ai_posted_date DATE,
                        ai_summary TEXT, -- Short job summary

                        -- AI enhancement tracking
                        ai_enhanced BOOLEAN DEFAULT FALSE,
                        ai_enhancement_date TIMESTAMP,
                        ai_extraction TEXT, -- Raw AI response for debugging

                        -- Timestamps
                        created_at TIMESTAMP DEFAULT NOW(),
                        updated_at TIMESTAMP DEFAULT NOW(),

                        -- Constraints
                        UNIQUE(source, source_job_id)
                    )
                """
                )

                # Create indexes for performance
                indexes = [
                    "CREATE INDEX IF NOT EXISTS idx_canonical_jobs_source ON canonical_jobs(source)",
                    "CREATE INDEX IF NOT EXISTS idx_canonical_jobs_location ON canonical_jobs(location)",
                    "CREATE INDEX IF NOT EXISTS idx_canonical_jobs_company ON canonical_jobs(company)",
                    "CREATE INDEX IF NOT EXISTS idx_canonical_jobs_posted_date ON canonical_jobs(posted_date)",
                    "CREATE INDEX IF NOT EXISTS idx_canonical_jobs_city ON canonical_jobs(city)",
                    "CREATE INDEX IF NOT EXISTS idx_canonical_jobs_industry ON canonical_jobs(industry)",
                    "CREATE INDEX IF NOT EXISTS idx_canonical_jobs_job_level ON canonical_jobs(job_level)",
                ]

                for index_sql in indexes:
                    try:
                        cur.execute(index_sql)
                    except Exception as e:
                        logger.debug(f"Index creation note: {e}")

            logger.info("✅ Enhanced canonical jobs table ready")
        except Exception as e:
            logger.error(f"❌ Failed to setup enhanced canonical table: {e}")
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

    def enhance_with_ai(self, canonical_job: Dict[str, Any]) -> Dict[str, Any]:
        """Use OpenAI to enhance job data with missing fields"""
        if not self.use_ai:
            return canonical_job

        try:
            # Prepare prompt for AI enhancement
            title = canonical_job.get("title", "N/A")
            company = canonical_job.get("company", "N/A")
            description = canonical_job.get("description", "N/A")[
                :1200
            ]  # Increased limit
            location = canonical_job.get("location", "N/A")
            job_url = canonical_job.get("job_url", "N/A")

            prompt = f"""
            You are an expert Nigerian job market analyst. Analyze this job posting and extract ALL missing information for a comprehensive job database.

            CURRENT DATA:
            Title: {title}
            Company: {company}
            Job URL: {job_url}
            Location: {location}
            Description: {description}...

            TASK: Extract and infer missing fields. Use "ai_" prefix for ALL inferred fields to distinguish from direct scraped data.

            AI-INFERRED CONTACT & APPLICATION:
            "ai_email": Extract email address from description (null if none found)
            "ai_whatsapp_number": Extract  phone number from description (null if none found)
            "ai_application_modes": Array like ["linkedin", "email", "whatsapp"] based on available contact methods , 

            AI-INFERRED LOCATION DETAILS (Nigerian context):
            "ai_city": Extract specific Nigerian city (e.g., "Lagos", "Abuja", "Port Harcourt", "Kano", "Ibadan")
            "ai_state": Extract Nigerian state (e.g., "Lagos", "FCT", "Rivers", "Kano", "Oyo")
            "ai_country": Always "Nigeria"

            AI-INFERRED JOB CLASSIFICATION:
            "ai_employment_type": "Full-time", "Part-time", "Contract", "Internship", "Freelance", "Remote"
            "ai_job_function": Main function (e.g., "Engineering", "Sales", "Marketing", "Finance", "Operations")
            "ai_job_level": "Entry", "Mid", "Senior", "Executive", "Internship"
            "ai_industry": Nigerian industry (e.g., "Technology", "Banking", "Oil & Gas", "Telecommunications", "Healthcare")

            AI-INFERRED COMPENSATION:
            "ai_salary_min": Minimum salary in NGN (extract from description, null if not mentioned)
            "ai_salary_max": Maximum salary in NGN (extract from description, null if not mentioned)
            "ai_salary_currency": "NGN", "USD", "EUR" (default "NGN" for Nigerian jobs)
            "ai_compensation_summary": Brief summary of compensation package mentioned

            AI-INFERRED SKILLS & REQUIREMENTS:
            "ai_required_skills": Array of 5-10 key technical/professional skills required
            "ai_preferred_skills": Array of 3-5 nice-to-have skills
            "ai_education_requirements": Education level needed (e.g., "Bachelor's Degree", "Master's Degree", "Diploma")
            "ai_years_experience_min": Minimum years of experience required (number or null)
            "ai_years_experience_max": Maximum years of experience (number or null)

            AI-INFERRED WORK ARRANGEMENT:
            "ai_remote_allowed": true/false based on remote work mentions
            "ai_work_arrangement": "On-site", "Remote", "Hybrid"
            "ai_benefits": Array of benefits mentioned (e.g., ["Health Insurance", "Pension", "Training"])

            AI-INFERRED DATES:
            "ai_application_deadline": Extract deadline if mentioned (YYYY-MM-DD format, null if none)
            "ai_posted_date": Job posting date if mentioned (YYYY-MM-DD format, null if none)

            "ai_summary": A very short Summary of the Job 

            IMPORTANT:
            - Return ONLY valid JSON with flat structure (no nested objects)
            - Include ALL fields even if null
            - Extract as much as possible from the description
            - Use Nigerian context for locations and industries
            - Be specific with skills and requirements
            """

            response = self.openai_client.chat.completions.create(
                model="gpt-4.1-nano",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=2000,
                temperature=0.3,
            )

            ai_response = response.choices[0].message.content.strip()

            # Save raw AI response for debugging
            canonical_job["ai_extraction"] = ai_response

            # Clean up the response to ensure it's valid JSON
            if ai_response.startswith("```json"):
                ai_response = (
                    ai_response.replace("```json", "").replace("```", "").strip()
                )

            try:
                ai_data = json.loads(ai_response)

                # Handle flat JSON structure from AI
                if isinstance(ai_data, dict):
                    for field_key, field_value in ai_data.items():
                        # Only add if field has meaningful value and doesn't already exist
                        if (
                            field_value is not None
                            and field_value != ""
                            and field_value != []
                            and field_key not in canonical_job
                        ):
                            canonical_job[field_key] = field_value
                        # Override existing fields if AI provides better data
                        elif (
                            field_value is not None
                            and field_value != ""
                            and field_value != []
                            and field_key in canonical_job
                            and not canonical_job[
                                field_key
                            ]  # Only if current value is empty/null
                        ):
                            canonical_job[field_key] = field_value

                canonical_job["ai_enhanced"] = True
                canonical_job["ai_enhancement_date"] = datetime.now().isoformat()
                self.stats["ai_enhanced"] += 1

                logger.debug(f"✅ AI enhanced: {title[:30]}")

            except json.JSONDecodeError as json_error:
                logger.debug(f"⚠️  JSON decode error for {title[:30]}: {json_error}")
                logger.debug(f"Raw AI response: {ai_response[:200]}...")
                # Still mark as AI enhanced since we have the raw response
                canonical_job["ai_enhanced"] = True
                canonical_job["ai_enhancement_date"] = datetime.now().isoformat()
                self.stats["ai_enhanced"] += 1

        except Exception as e:
            logger.debug(
                f"⚠️  AI enhancement failed for {canonical_job.get('title', 'N/A')[:30]}: {e}"
            )

        return canonical_job

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

    def parse_unified_job(
        self, raw_data: Dict[str, Any], source: str
    ) -> Dict[str, Any]:
        """Parse job data from either JobSpy or LinkedIn into comprehensive canonical format"""
        try:
            # Start with basic canonical structure
            canonical = {
                # Core information (direct mapping)
                "title": self.clean_text(raw_data.get("title", "")),
                "company": self.clean_text(raw_data.get("company", "")),
                "location": self.clean_text(raw_data.get("location", "")),
                "job_url": raw_data.get("job_url") or raw_data.get("url", ""),
                "description": self.clean_text(raw_data.get("description", "")),
                # Source tracking
                "source": source,
                "source_job_id": raw_data.get("id") or raw_data.get("job_id"),
                # Default values
                "country": "Nigeria",
                "salary_currency": "NGN",
            }

            # Comprehensive field mappings for JobSpy and LinkedIn data
            field_mappings = {
                # Core job information
                "site": ["site"],
                "job_url_direct": ["job_url_direct"],
                # Employment and job details
                "employment_type": ["job_type", "employment_type"],
                "job_type": ["job_type", "employment_type"],
                "job_function": ["job_function", "function"],
                "job_level": ["job_level", "experience_level"],
                "experience_level": ["experience_level", "job_level"],
                "seniority_level": ["seniority_level"],
                "industry": ["industry", "company_industry"],
                "industries": ["industries"],
                # Salary information
                "salary_min": ["min_amount", "salary_min"],
                "salary_max": ["max_amount", "salary_max"],
                "min_amount": ["min_amount", "salary_min"],
                "max_amount": ["max_amount", "salary_max"],
                "salary_currency": ["currency", "salary_currency"],
                "currency": ["currency", "salary_currency"],
                # Location details
                "city": ["city"],
                "state": ["state"],
                "is_remote": ["is_remote", "remote_allowed"],
                "remote_allowed": ["remote_allowed", "is_remote"],
                "work_arrangement": ["work_arrangement"],
                # Company information
                "company_url": ["company_url"],
                "company_logo": ["company_logo"],
                "company_addresses": ["company_addresses"],
                "company_industry": ["company_industry", "industry"],
                "company_num_employees": ["company_num_employees"],
                "company_revenue": ["company_revenue"],
                "company_description": ["company_description"],
                "company_size": ["company_size"],
                "ceo_name": ["ceo_name"],
                "ceo_photo_url": ["ceo_photo_url"],
                "logo_photo_url": ["logo_photo_url"],
                "banner_photo_url": ["banner_photo_url"],
                # Contact information
                "emails": ["emails"],
                "phones": ["phones"],
                # Skills and requirements
                "skills": ["skills"],
                "required_skills": ["required_skills"],
                "preferred_skills": ["preferred_skills"],
                "education_requirements": ["education_requirements"],
                "years_experience_min": ["years_experience_min"],
                "years_experience_max": ["years_experience_max"],
                # Benefits and dates
                "benefits": ["benefits"],
                "date_posted": ["date_posted", "posted_date"],
                "posted_date": ["posted_date", "date_posted"],
                "application_deadline": ["application_deadline"],
            }

            # Apply field mappings
            for canonical_field, source_fields in field_mappings.items():
                for source_field in source_fields:
                    if source_field in raw_data and raw_data[source_field]:
                        value = raw_data[source_field]

                        # Special handling for different field types
                        if canonical_field in ["salary_min", "salary_max"]:
                            canonical[canonical_field] = self.parse_salary(value)
                        elif canonical_field == "posted_date":
                            canonical[canonical_field] = self.parse_date(value)
                        elif canonical_field in [
                            "emails",
                            "phones",
                            "skills",
                            "benefits",
                        ]:
                            # Handle arrays
                            if isinstance(value, list):
                                canonical[canonical_field] = value
                            elif isinstance(value, str) and value.strip():
                                canonical[canonical_field] = [value.strip()]
                        elif canonical_field == "remote_allowed":
                            canonical[canonical_field] = bool(value)
                        else:
                            canonical[canonical_field] = self.clean_text(str(value))
                        break  # Use first matching field

            # Extract contact information from description if not already present
            if canonical.get("description"):
                if not canonical.get("emails"):
                    email = self.extract_email(canonical["description"])
                    if email:
                        canonical["emails"] = [email]

                if not canonical.get("phones"):
                    phone = self.extract_whatsapp(canonical["description"])
                    if phone:
                        canonical["phones"] = [phone]

            # Determine application modes
            canonical["application_mode"] = self.determine_application_modes(
                canonical.get("job_url", ""),
                canonical.get("emails", []),
                canonical.get("phones", []),
            )

            # Parse location details if not already present
            if not canonical.get("city") or not canonical.get("state"):
                location = canonical.get("location", "")
                if not canonical.get("city"):
                    canonical["city"] = self.extract_city_enhanced(location)
                if not canonical.get("state"):
                    canonical["state"] = self.extract_state_enhanced(location)

            return canonical

        except Exception as e:
            logger.error(f"❌ Failed to parse {source} job: {e}")
            return None

    def clean_text(self, text: str) -> str:
        """Clean and normalize text"""
        if not text:
            return ""
        return text.strip().replace("\n", " ").replace("\r", " ")

    def extract_city_enhanced(self, location: str) -> Optional[str]:
        """Enhanced city extraction with more Nigerian cities"""
        if not location:
            return None

        # Comprehensive Nigerian cities
        cities = {
            "lagos": "Lagos",
            "abuja": "Abuja",
            "port harcourt": "Port Harcourt",
            "kano": "Kano",
            "ibadan": "Ibadan",
            "kaduna": "Kaduna",
            "benin city": "Benin City",
            "jos": "Jos",
            "warri": "Warri",
            "calabar": "Calabar",
            "enugu": "Enugu",
            "onitsha": "Onitsha",
            "aba": "Aba",
            "ilorin": "Ilorin",
            "abeokuta": "Abeokuta",
            "maiduguri": "Maiduguri",
            "zaria": "Zaria",
            "owerri": "Owerri",
            "uyo": "Uyo",
            "akure": "Akure",
        }

        location_lower = location.lower()
        for city_key, city_name in cities.items():
            if city_key in location_lower:
                return city_name

        # Extract first part before comma as fallback
        parts = location.split(",")
        if parts:
            return parts[0].strip()

        return None

    def extract_state_enhanced(self, location: str) -> Optional[str]:
        """Enhanced state extraction for Nigerian states"""
        if not location:
            return None

        # Comprehensive Nigerian states mapping
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
            "aba": "Abia",
            "ilorin": "Kwara",
            "abeokuta": "Ogun",
            "maiduguri": "Borno",
            "zaria": "Kaduna",
            "owerri": "Imo",
            "uyo": "Akwa Ibom",
            "akure": "Ondo",
        }

        location_lower = location.lower()
        for key, state in state_mapping.items():
            if key in location_lower:
                return state

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
        """Parse LinkedIn job - only map fields that actually exist, let AI handle the rest"""
        try:
            canonical = {
                # Only map what actually exists in LinkedIn data
                "title": raw_data.get("title", "").strip(),
                "company": raw_data.get("company", "").strip(),
                "location": raw_data.get("location", "").strip(),
                "job_url": raw_data.get("job_url") or raw_data.get("url", ""),
                "posted_date": self.parse_date(
                    raw_data.get("posted_date") or raw_data.get("date_posted")
                ),
                # Description for AI processing
                "description": raw_data.get("description", "").strip(),
                # Source tracking
                "source": "linkedin",
                "source_job_id": raw_data.get("job_id") or raw_data.get("id"),
                "country": "Nigeria",
            }

            # Let AI handle everything else: email, whatsapp, application_mode,
            # salary, employment_type, experience_level, industry, city, state, etc.
            if self.use_ai:
                canonical = self.enhance_with_ai(canonical)

            return canonical

        except Exception as e:
            logger.error(f"❌ Failed to parse LinkedIn job: {e}")
            return None

    def parse_jobspy_job(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """Parse JobSpy job - direct mapping + AI enhancement"""
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

            # Enhance with AI if available
            if self.use_ai:
                canonical = self.enhance_with_ai(canonical)

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
                if value is not None and value != "" and value != []:
                    columns.append(key)
                    # Handle array/dict fields properly for PostgreSQL
                    if isinstance(value, list):
                        # Convert list to PostgreSQL array format
                        if all(isinstance(item, str) for item in value):
                            # String array: convert to PostgreSQL array
                            values.append(value)  # psycopg2 handles list conversion
                        else:
                            # Mixed types: convert to JSON string
                            values.append(json.dumps(value))
                    elif isinstance(value, dict):
                        # Convert dict to JSON string
                        values.append(json.dumps(value))
                    else:
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
        """Process raw jobs into canonical format with AI enhancement"""
        logger.info("🚀 Starting AI Enhanced Job Data Parsing")
        logger.info("💡 Direct mapping + AI enhancement + application modes")
        logger.info("=" * 60)

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

                    # Parse using unified parser (handles both JobSpy and LinkedIn)
                    canonical_job = self.parse_unified_job(raw_data, source)

                    if source == "linkedin":
                        self.stats["linkedin_processed"] += 1
                    elif source == "jobspy":
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
                    if self.stats["total_processed"] % 25 == 0:
                        logger.info(
                            f"📊 Progress: {self.stats['total_processed']} processed, {self.stats['ai_enhanced']} AI enhanced"
                        )

                except Exception as e:
                    logger.error(f"❌ Failed to process job {raw_job_id}: {e}")
                    self.stats["errors"] += 1
                    continue

            # Final statistics
            logger.info("🎉 AI Enhanced parsing completed!")
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
            ai_rate = (self.stats["ai_enhanced"] / self.stats["total_processed"]) * 100
            logger.info(f"   Success rate: {success_rate:.1f}%")
            logger.info(f"   AI enhancement rate: {ai_rate:.1f}%")


def main():
    """Main function"""
    print("🤖 AI Enhanced Job Data Parser")
    print("💡 Direct mapping + AI enhancement + application modes")
    print("=" * 50)

    print("Choose processing option:")
    print("1. Process all sources (with AI enhancement)")
    print("2. Process LinkedIn jobs only")
    print("3. Process JobSpy jobs only")
    print("4. Process limited batch (50 jobs)")

    choice = input("Enter choice (1-4): ").strip()

    try:
        parser = AIEnhancedJobParser()

        if choice == "1":
            parser.process_raw_jobs()
        elif choice == "2":
            parser.process_raw_jobs(source="linkedin")
        elif choice == "3":
            parser.process_raw_jobs(source="jobspy")
        elif choice == "4":
            parser.process_raw_jobs(limit=50)
        else:
            print("Invalid choice")
            return

        print("\n🎉 AI Enhanced parsing completed!")
        print("💾 Jobs saved to canonical_jobs table")
        print("🤖 AI enhancement applied")
        print("📱 Application modes detected")

    except Exception as e:
        logger.error(f"❌ Parsing failed: {e}")


if __name__ == "__main__":
    main()
