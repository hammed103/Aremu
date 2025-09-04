#!/usr/bin/env python3
"""
Enhanced AI Job Data Parser with Intelligent Matching Fields
"""

import os
import sys
import json
import logging
import psycopg2
import psycopg2.extras
from datetime import datetime
from typing import Dict, Any, List, Optional
from openai import OpenAI

# Add smart delivery engine (optional for standalone testing)
try:
    sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
    from smart_delivery_engine import SmartDeliveryEngine
except ImportError:
    print("⚠️ Smart delivery engine not available - running in parser-only mode")
    SmartDeliveryEngine = None

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("ai_enhanced_parser.log"), logging.StreamHandler()],
)
logger = logging.getLogger(__name__)


class AIEnhancedJobParser:
    def __init__(self):
        """Initialize the AI Enhanced Job Parser"""
        self.connection = None
        self.openai_client = None
        self.use_ai = True
        self.stats = {
            "total_processed": 0,
            "linkedin_jobs": 0,
            "jobspy_jobs": 0,
            "ai_enhanced": 0,
            "errors": 0,
        }

        # Connect to database
        self.connect_to_database()

        # Setup OpenAI
        self.setup_openai()

        # Setup Smart Delivery Engine
        self.setup_smart_delivery()

        # Ensure canonical jobs table exists
        self.ensure_canonical_jobs_table()

    def connect_to_database(self):
        """Connect to PostgreSQL database"""
        try:
            db_url = "postgresql://postgres.upnvhpgaljazlsoryfgj:prAlkIpbQDqOZtOj@aws-0-us-east-1.pooler.supabase.com:6543/postgres"
            self.connection = psycopg2.connect(db_url)
            logger.info("✅ Connected to database")
        except Exception as e:
            logger.error(f"❌ Database connection failed: {e}")
            raise

    def setup_openai(self):
        """Setup OpenAI client"""
        try:
            # Load from .env file
            env_path = os.path.join(os.path.dirname(__file__), "..", "..", ".env")
            if os.path.exists(env_path):
                with open(env_path, "r") as f:
                    for line in f:
                        if line.startswith("OPENAI_API_KEY="):
                            api_key = line.split("=", 1)[1].strip()
                            self.openai_client = OpenAI(api_key=api_key)
                            logger.info("✅ OpenAI API key loaded from .env file")
                            return

            # Fallback to environment variable
            api_key = os.getenv("OPENAI_API_KEY")
            if api_key:
                self.openai_client = OpenAI(api_key=api_key)
                logger.info("✅ OpenAI API key loaded from environment")
            else:
                logger.warning("⚠️ No OpenAI API key found - AI enhancement disabled")
                self.use_ai = False

        except Exception as e:
            logger.error(f"❌ OpenAI setup failed: {e}")
            self.use_ai = False

    def setup_smart_delivery(self):
        """Setup Smart Delivery Engine with WhatsApp credentials"""
        if SmartDeliveryEngine is None:
            logger.info("⚠️ Smart delivery engine not available - skipping setup")
            self.smart_delivery = None
            return

        try:
            # Load WhatsApp credentials from WhatsApp bot .env file
            whatsapp_env_path = os.path.join(
                os.path.dirname(__file__), "..", "..", ".env"
            )
            whatsapp_token = None
            whatsapp_phone_id = None

            if os.path.exists(whatsapp_env_path):
                with open(whatsapp_env_path, "r") as f:
                    for line in f:
                        if line.startswith("WHATSAPP_ACCESS_TOKEN="):
                            whatsapp_token = line.split("=", 1)[1].strip()
                        elif line.startswith("WHATSAPP_PHONE_NUMBER_ID="):
                            whatsapp_phone_id = line.split("=", 1)[1].strip()

            # Fallback to environment variables
            if not whatsapp_token:
                whatsapp_token = os.getenv("WHATSAPP_ACCESS_TOKEN")
            if not whatsapp_phone_id:
                whatsapp_phone_id = os.getenv("WHATSAPP_PHONE_NUMBER_ID")

            # Initialize smart delivery engine
            self.smart_delivery = SmartDeliveryEngine(whatsapp_token, whatsapp_phone_id)

            if self.smart_delivery.is_delivery_enabled():
                logger.info("✅ Smart Delivery Engine enabled")
            else:
                logger.warning(
                    "⚠️ Smart Delivery Engine disabled - WhatsApp credentials missing"
                )

        except Exception as e:
            logger.error(f"❌ Error setting up Smart Delivery: {e}")
            self.smart_delivery = None

    def ensure_canonical_jobs_table(self):
        """Ensure canonical jobs table exists with all required columns"""
        try:
            cursor = self.connection.cursor()

            # Create table if it doesn't exist
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS canonical_jobs (
                    id SERIAL PRIMARY KEY,
                    title TEXT,
                    company TEXT,
                    location TEXT,
                    job_url TEXT,
                    description TEXT,
                    employment_type TEXT,
                    salary_min NUMERIC,
                    salary_max NUMERIC,
                    salary_currency TEXT,
                    email TEXT,
                    whatsapp_number TEXT,
                    source TEXT NOT NULL,
                    source_job_id TEXT,
                    raw_job_id INTEGER,
                    created_at TIMESTAMP DEFAULT NOW(),
                    updated_at TIMESTAMP DEFAULT NOW(),
                    
                    -- AI Enhanced Fields for Intelligent Matching
                    ai_enhanced BOOLEAN DEFAULT FALSE,
                    ai_enhancement_date TIMESTAMP,
                    ai_extraction TEXT,
                    
                    -- AI Job Titles for Intelligent Matching
                    ai_job_titles TEXT[], -- List of all relevant job titles
                    
                    -- AI Location Fields
                    ai_city TEXT,
                    ai_state TEXT,
                    ai_country TEXT,
                    
                    -- AI Job Classification
                    ai_employment_type TEXT,
                    ai_job_function TEXT,
                    ai_job_level TEXT[], -- List since job can be Senior AND Mid
                    ai_industry TEXT[], -- List since job can fit multiple industries
                    
                    -- AI Compensation
                    ai_salary_min NUMERIC,
                    ai_salary_max NUMERIC,
                    ai_salary_currency TEXT,
                    ai_compensation_summary TEXT,
                    
                    -- AI Skills & Requirements (Arrays for intelligent matching)
                    ai_required_skills TEXT[], -- Array of required skills
                    ai_preferred_skills TEXT[], -- Array of preferred skills
                    ai_education_requirements TEXT,
                    ai_years_experience_min INTEGER,
                    ai_years_experience_max INTEGER,
                    
                    -- AI Work Arrangement
                    ai_remote_allowed BOOLEAN,
                    ai_work_arrangement TEXT,
                    ai_benefits TEXT[],
                    
                    -- AI Contact & Application
                    ai_email TEXT,
                    ai_whatsapp_number TEXT,
                    ai_application_modes TEXT[],
                    ai_application_deadline DATE,
                    ai_posted_date DATE,
                    
                    -- AI Generated WhatsApp Summary
                    ai_summary TEXT
                )
            """
            )

            self.connection.commit()
            logger.info("✅ Enhanced canonical jobs table ready")

        except Exception as e:
            logger.error(f"❌ Error creating canonical jobs table: {e}")
            raise

    def enhance_with_ai(self, canonical_job: Dict[str, Any]) -> Dict[str, Any]:
        """Enhance job data with AI for intelligent matching"""
        if not self.use_ai or not self.openai_client:
            return canonical_job

        title = canonical_job.get("title", "")
        company = canonical_job.get("company", "")
        description = canonical_job.get("description", "")
        location = canonical_job.get("location", "")

        try:
            # Enhanced AI prompt for intelligent matching
            prompt = f"""
            You are an expert Nigerian job market analyst. Analyze this job posting and extract ALL information for intelligent job matching.

            CURRENT DATA:
            Title: {title}
            Company: {company}
            Location: {location}
            Description: {description[:1000]}...

            TASK: Extract comprehensive data for intelligent job matching. Return ONLY valid JSON with these fields:

            {{
                "ai_job_titles": ["COMPREHENSIVE list of ALL job titles this role matches - include exact title, variations, synonyms, related roles. Examples: 'Software Engineer', 'Backend Developer', 'Python Developer', 'Full Stack Developer', 'Software Developer', 'Application Developer', 'Systems Engineer', etc. BE VERY COMPREHENSIVE!"],

                "ai_employment_type": "Full-time, Part-time, Contract, Internship, or Freelance",
                "ai_job_function": "Engineering, Product, Design, Marketing, Sales, Data & Analytics, Operations, Finance, HR, etc.",
                "ai_job_level": ["MULTIPLE levels this job fits - be inclusive! Examples: ['Entry-level', 'Mid-level'] for roles open to both, ['Mid-level', 'Senior'] for experienced roles, ['Senior', 'Lead'] for leadership roles, ['Entry-level'] for junior only. Consider experience requirements and responsibilities."],
                "ai_industry": ["MULTIPLE industries this job fits - be comprehensive! Examples: ['Technology', 'Software', 'Fintech', 'Financial Services'] for fintech roles, ['Technology', 'E-commerce', 'Retail'] for e-commerce roles, ['Technology', 'Healthcare', 'Digital Health'] for healthtech. Include primary industry + related sectors."],

                "ai_city": "Extract city from location",
                "ai_state": "Extract state/region from location",
                "ai_country": "Extract country from location (default: Nigeria)",

                "ai_required_skills": ["Array of required technical skills"],
                "ai_preferred_skills": ["Array of preferred/nice-to-have skills"],
                "ai_years_experience_min": 0,
                "ai_years_experience_max": 10,

                "ai_salary_min": 0,
                "ai_salary_max": 0,
                "ai_salary_currency": "NGN, USD, or EUR",
                "ai_compensation_summary": "Brief salary description",

                "ai_remote_allowed": true or false,
                "ai_work_arrangement": "Remote, Hybrid, or On-site",
                "ai_benefits": ["Array of benefits mentioned"],

                "ai_email": "Extract APPLICATION email ONLY. IGNORE emails that are for: reporting, support, suspicious activity, globalhotline, complaints, or any email that says 'do not send applications'. Return null if no application email found.",
                "ai_whatsapp_number": "Extract phone/WhatsApp for applications (ignore support numbers)",
                "ai_application_modes": ["Email", "WhatsApp", "Online", "LinkedIn"],

                "ai_summary": "Create a clean WhatsApp job post using this EXACT format:\n\n🚀 **[Job Title]** at **[Company]**\n📍 [Location] | 💰 [Salary OR 'Competitive salary' if none] | ⏰ [Employment Type]\n\n[1-2 compelling sentences about the role]\n\n**What you'll do:**\n• [Key responsibility 1]\n• [Key responsibility 2]\n• [Key responsibility 3]\n\n**What we need:**\n• [Key requirement 1]\n• [Key requirement 2]\n• [Key requirement 3]\n\n**Why join us:**\n[Benefits/company culture from description]\n\n**Skills:** [Top 5 relevant skills]\n\nIMPORTANT:\n- Use REAL data from the job description\n- Replace ALL placeholders with actual content\n- Use 'Competitive salary' if no salary mentioned\n- Keep it concise and engaging for WhatsApp",
            }}

            CRITICAL FOR INTELLIGENT MATCHING:
            - ai_job_titles: Include 8-15 relevant job titles (exact + variations + synonyms)
            - ai_job_level: Include ALL applicable levels (be inclusive for better matching)
            - ai_industry: Include 3-6 industries this role could fit into
            - ai_required_skills: Extract 5-10 key technical skills
            - ai_preferred_skills: Extract 3-8 nice-to-have skills

            Focus on Nigerian job market context. BE COMPREHENSIVE for maximum matching potential!
            """

            response = self.openai_client.chat.completions.create(
                model="gpt-4o-mini",  # Use valid OpenAI model
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
            )

            # Check if response has choices
            if (
                not hasattr(response, "choices")
                or not response.choices
                or len(response.choices) == 0
            ):
                logger.error(f"❌ No AI response choices for {title[:30]}")
                return canonical_job

            ai_response = response.choices[0].message.content
            if not ai_response:
                logger.error(f"❌ Empty AI response for {title[:30]}")
                return canonical_job

            ai_response = ai_response.strip()

            # Clean up JSON response
            if ai_response.startswith("```json"):
                ai_response = (
                    ai_response.replace("```json", "").replace("```", "").strip()
                )

            # Fix common JSON escape issues
            ai_response = (
                ai_response.replace("\\+", "+")
                .replace("\\-", "-")
                .replace("\\&", "&")
                .replace("\\:", ":")
                .replace("\\=", "=")
                .replace("\\#", "#")
                .replace("\\*", "*")
                .replace("\\(", "(")
                .replace("\\)", ")")
                .replace("\\[", "[")
                .replace("\\]", "]")
                .replace("\\{", "{")
                .replace("\\}", "}")
                .replace("\\|", "|")
                .replace("\\<", "<")
                .replace("\\>", ">")
                .replace("\\@", "@")
                .replace("\\%", "%")
                .replace("\\$", "$")
                .replace("\\^", "^")
                .replace("\\~", "~")
                .replace("\\`", "`")
            )

            try:
                ai_data = json.loads(ai_response)

                # Add AI fields to canonical job
                if isinstance(ai_data, dict):
                    for field_key, field_value in ai_data.items():
                        if (
                            field_value is not None
                            and field_value != ""
                            and field_value != []
                        ):
                            # Always add AI fields (they start with ai_)
                            if field_key.startswith("ai_"):
                                canonical_job[field_key] = field_value
                            # For non-AI fields, only add if missing or empty
                            elif (
                                field_key not in canonical_job
                                or not canonical_job.get(field_key)
                            ):
                                canonical_job[field_key] = field_value

                # Mark as AI enhanced
                canonical_job["ai_enhanced"] = True
                canonical_job["ai_enhancement_date"] = datetime.now().isoformat()
                self.stats["ai_enhanced"] += 1

                title_display = title[:30] if title else "Unknown"
                logger.debug(f"✅ AI enhanced: {title_display}...")

            except json.JSONDecodeError as json_error:
                logger.warning(f"⚠️ JSON decode error for {title[:30]}: {json_error}")
                logger.warning(f"Raw AI response: {ai_response[:500]}...")
                # Store the raw response for debugging
                canonical_job["ai_extraction"] = ai_response[:1000]
                canonical_job["ai_enhanced"] = True
                canonical_job["ai_enhancement_date"] = datetime.now().isoformat()
                self.stats["ai_enhanced"] += 1

        except Exception as e:
            title_display = title[:30] if title else "Unknown"
            logger.error(f"❌ AI enhancement failed for {title_display}: {e}")
            logger.error(f"❌ Error type: {type(e)}")
            logger.error(f"❌ Error details: {str(e)}")
            import traceback

            logger.error(f"❌ Traceback: {traceback.format_exc()}")
            self.stats["errors"] += 1

        return canonical_job

    def process_raw_jobs(self, limit: Optional[int] = None):
        """Process raw jobs with AI enhancement and 14-day filter"""
        try:
            cursor = self.connection.cursor(
                cursor_factory=psycopg2.extras.RealDictCursor
            )

            # Get recent jobs (14-day filter) - using JSONB structure
            query = """
                SELECT
                    id, source, source_job_id, raw_data, scraped_at,
                    (raw_data->>'date_posted')::date as posted_date
                FROM raw_jobs
                WHERE (
                    (raw_data->>'date_posted')::date >= CURRENT_DATE - INTERVAL '14 days' OR
                    ((raw_data->>'date_posted') IS NULL AND scraped_at >= CURRENT_DATE - INTERVAL '14 days')
                )
                AND (processed = false OR processed IS NULL)
                ORDER BY
                    COALESCE((raw_data->>'date_posted')::date, scraped_at::date) DESC,
                    scraped_at DESC
            """

            if limit:
                query += f" LIMIT {limit}"

            cursor.execute(query)
            raw_jobs = cursor.fetchall()

            logger.info(f"📊 Processing {len(raw_jobs)} recent jobs (14-day filter)")

            processed_count = 0
            for raw_job in raw_jobs:
                try:
                    # Convert to canonical format
                    canonical_job = self.convert_to_canonical(dict(raw_job))

                    # Enhance with AI for intelligent matching
                    enhanced_job = self.enhance_with_ai(canonical_job)

                    # Save to database
                    job_id = self.save_canonical_job(enhanced_job)

                    # Commit immediately so delivery engine can access the job
                    self.connection.commit()

                    # SMART DELIVERY: Trigger real-time job delivery
                    if (
                        job_id
                        and self.smart_delivery
                        and self.smart_delivery.is_delivery_enabled()
                    ):
                        try:
                            # Add job ID to enhanced job for delivery
                            enhanced_job["id"] = job_id
                            delivery_stats = (
                                self.smart_delivery.process_single_job_delivery(
                                    enhanced_job
                                )
                            )

                            if delivery_stats["alerts_sent"] > 0:
                                logger.info(
                                    f"🚨 Delivered job {job_id} to {delivery_stats['alerts_sent']} users"
                                )
                        except Exception as e:
                            logger.error(
                                f"❌ Smart delivery failed for job {job_id}: {e}"
                            )

                    processed_count += 1
                    if processed_count % 10 == 0:
                        logger.info(
                            f"✅ Processed {processed_count}/{len(raw_jobs)} jobs"
                        )

                except Exception as e:
                    logger.error(
                        f"❌ Error processing job {raw_job.get('id', 'unknown')}: {e}"
                    )
                    logger.error(f"❌ Error type: {type(e)}")
                    logger.error(f"❌ Error details: {str(e)}")
                    import traceback

                    logger.error(f"❌ Traceback: {traceback.format_exc()}")
                    logger.error(f"❌ Raw job data: {raw_job}")
                    self.stats["errors"] += 1

            self.connection.commit()
            logger.info(f"🎉 Processing complete! {processed_count} jobs processed")

        except Exception as e:
            logger.error(f"❌ Error in process_raw_jobs: {e}")
            raise

    def convert_to_canonical(self, raw_job: Dict[str, Any]) -> Dict[str, Any]:
        """Convert raw job to canonical format from JSONB structure"""
        raw_data = raw_job.get("raw_data", {})

        # Handle case where raw_data is None or not a dict
        if not isinstance(raw_data, dict):
            logger.warning(
                f"⚠️ Invalid raw_data for job {raw_job.get('id')}: {type(raw_data)}"
            )
            raw_data = {}

        # Handle different data structures based on source
        source = raw_job.get("source", "unknown")

        if source == "whatsapp":
            # WhatsApp jobs have text field with full job posting
            text = raw_data.get("text", "")
            email = self.extract_email_from_text(text)
            whatsapp = self.extract_whatsapp_from_text(text)
            job_url = self.extract_url_from_text(
                text
            )  # NEW: Extract URLs for CTA buttons

            return {
                "title": self.extract_title_from_whatsapp_text(text),
                "company": None,  # Will be extracted by AI
                "location": None,  # Will be extracted by AI
                "job_url": job_url,  # Now extracts URLs from WhatsApp text
                "description": text,
                "employment_type": None,  # Will be extracted by AI
                "salary_min": None,
                "salary_max": None,
                "salary_currency": None,
                "email": email,
                "whatsapp_number": whatsapp,
                "source": source,
                "source_job_id": raw_job.get("source_job_id"),
                "raw_job_id": raw_job.get("id"),
                "posted_date": raw_data.get("date_posted"),
            }
        else:
            # Web scraped jobs have structured fields
            description = raw_data.get("description", "") or ""
            email = raw_data.get("emails") or self.extract_email_from_text(description)
            whatsapp = self.extract_whatsapp_from_text(description)

            return {
                "title": raw_data.get("title"),
                "company": raw_data.get("company"),
                "location": raw_data.get("location"),
                "job_url": raw_data.get("job_url"),
                "description": description,
                "employment_type": raw_data.get("job_type"),
                "salary_min": raw_data.get("min_amount"),
                "salary_max": raw_data.get("max_amount"),
                "salary_currency": raw_data.get("currency"),
                "email": email,
                "whatsapp_number": whatsapp,
                "source": source,
                "source_job_id": raw_job.get("source_job_id"),
                "raw_job_id": raw_job.get("id"),
                "posted_date": raw_data.get("date_posted"),
            }

    def extract_email_from_text(self, text: str) -> Optional[str]:
        """Extract email from text"""
        import re

        if not text:
            return None
        email_pattern = r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"
        matches = re.findall(email_pattern, text)
        return matches[0] if matches else None

    def extract_title_from_whatsapp_text(self, text: str) -> Optional[str]:
        """Extract job title from WhatsApp text"""
        if not text or not isinstance(text, str):
            return "Job Opportunity"  # Default title

        import re

        # Look for common patterns like "Position Title:", "*Position:", etc.
        title_patterns = [
            r"Position Title:\s*([^\n*]+)",
            r"\*Position[^:]*:\s*([^\n*]+)",
            r"Job Title:\s*([^\n*]+)",
            r"Role:\s*([^\n*]+)",
            r"We are hiring[^:]*:\s*([^\n*]+)",
            r"Looking for[^:]*:\s*([^\n*]+)",
        ]

        for pattern in title_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                title = match.group(1).strip()
                # Clean up the title
                title = re.sub(r"[*_]+", "", title)  # Remove markdown
                return title[:100] if title else "Job Opportunity"

        # If no pattern found, try to extract from first line
        lines = text.split("\n")
        for line in lines[:3]:  # Check first 3 lines
            line = line.strip()
            if len(line) > 10 and len(line) < 100:  # Reasonable title length
                # Clean up the line
                line = re.sub(r"[*_]+", "", line)
                if any(
                    word in line.lower()
                    for word in ["position", "job", "role", "hiring", "vacancy"]
                ):
                    return line

        return "Job Opportunity"  # Default fallback

    def extract_whatsapp_from_text(self, text: str) -> Optional[str]:
        """Extract WhatsApp/phone number from text"""
        import re

        if not text:
            return None
        # Look for Nigerian phone patterns
        phone_patterns = [
            r"\b(?:\+234|234|0)[789]\d{9}\b",  # Nigerian mobile
            r"\b[789]\d{9}\b",  # Short Nigerian mobile
            r"\b\d{11}\b",  # 11-digit numbers
        ]
        for pattern in phone_patterns:
            matches = re.findall(pattern, text)
            if matches:
                return matches[0]
        return None

    def extract_url_from_text(self, text: str) -> Optional[str]:
        """Extract URLs from WhatsApp job text for CTA buttons"""
        import re

        if not text:
            return None

        # URL patterns to match various formats
        url_patterns = [
            # Standard HTTP/HTTPS URLs
            r'https?://[^\s<>"{}|\\^`\[\]]+',
            # URLs without protocol
            r'www\.[^\s<>"{}|\\^`\[\]]+',
            # Common job board domains without www
            r'\b(?:linkedin\.com|indeed\.com|glassdoor\.com|jobberman\.com|myjobmag\.com|careers\.[\w-]+\.com)[^\s<>"{}|\\^`\[\]]*',
            # Application links
            r'\b[\w-]+\.com/(?:jobs|careers|apply)[^\s<>"{}|\\^`\[\]]*',
        ]

        for pattern in url_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                url = matches[0]
                # Clean up the URL
                url = url.rstrip(".,!?;)")  # Remove trailing punctuation

                # Add protocol if missing
                if not url.startswith(("http://", "https://")):
                    url = "https://" + url

                # Validate URL format
                if self._is_valid_url(url):
                    return url

        return None

    def _is_valid_url(self, url: str) -> bool:
        """Validate if extracted URL is properly formatted"""
        import re

        # Basic URL validation
        url_regex = re.compile(
            r"^https?://"  # http:// or https://
            r"(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|"  # domain...
            r"localhost|"  # localhost...
            r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})"  # ...or ip
            r"(?::\d+)?"  # optional port
            r"(?:/?|[/?]\S+)$",
            re.IGNORECASE,
        )

        return url_regex.match(url) is not None

    def save_canonical_job(self, job: Dict[str, Any]):
        """Save canonical job to database and return job ID"""
        try:
            cursor = self.connection.cursor()

            # Check if job already exists
            cursor.execute(
                """
                SELECT id FROM canonical_jobs
                WHERE source = %s AND source_job_id = %s
            """,
                (job.get("source"), job.get("source_job_id")),
            )

            existing = cursor.fetchone()

            if existing:
                # Update existing job
                job_id = existing[0]
                update_fields = []
                update_values = []

                for key, value in job.items():
                    if key != "id" and value is not None:
                        update_fields.append(f"{key} = %s")
                        update_values.append(value)

                if update_fields:
                    update_values.append(job_id)
                    cursor.execute(
                        f"""
                        UPDATE canonical_jobs
                        SET {', '.join(update_fields)}, updated_at = NOW()
                        WHERE id = %s
                    """,
                        update_values,
                    )
            else:
                # Insert new job
                columns = list(job.keys())
                values = list(job.values())
                placeholders = ", ".join(["%s"] * len(values))

                cursor.execute(
                    f"""
                    INSERT INTO canonical_jobs ({', '.join(columns)})
                    VALUES ({placeholders})
                    RETURNING id
                """,
                    values,
                )
                job_id = cursor.fetchone()[0]

            # Mark raw job as processed
            if job.get("raw_job_id"):
                cursor.execute(
                    """
                    UPDATE raw_jobs
                    SET processed = true, updated_at = NOW()
                    WHERE id = %s
                """,
                    (job["raw_job_id"],),
                )

            self.stats["total_processed"] += 1
            return job_id

        except Exception as e:
            logger.error(f"❌ Error saving job: {e}")
            raise


def main():
    """Main function"""
    print("🤖 Enhanced AI Job Data Parser")
    print("💡 Intelligent matching + AI enhancement + WhatsApp summaries")
    print("=" * 60)
    print("Choose processing option:")
    print("1. Process all recent jobs (14-day filter)")
    print("2. Process limited batch (10 jobs)")

    choice = input("Enter choice (1-2): ").strip()

    try:
        parser = AIEnhancedJobParser()

        if choice == "1":
            parser.process_raw_jobs()
        elif choice == "2":
            parser.process_raw_jobs(limit=10)
        else:
            print("❌ Invalid choice")
            return

        # Print final stats
        print(f"\n📊 Final Statistics:")
        print(f"   Total processed: {parser.stats['total_processed']}")
        print(f"   AI enhanced: {parser.stats['ai_enhanced']}")
        print(f"   Errors: {parser.stats['errors']}")

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()
