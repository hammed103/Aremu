#!/usr/bin/env python3
"""
Enhanced LinkedIn Scraper - Structured Data Extraction
Extracts detailed structured data similar to JobSpy output
"""

import csv
import json
import re
import requests
import time
import psycopg2
import hashlib
from datetime import datetime, date
from urllib.parse import quote
import logging
from bs4 import BeautifulSoup
import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
try:
    from database.config import get_database_url
    from nigeria_config import (
        NIGERIAN_LOCATIONS,
        KEYWORD_CATEGORIES,
        REMOTE_KEYWORDS,
    )
except ImportError:
    # Fallback if config files not found
    def get_database_url():
        return "postgresql://postgres.upnvhpgaljazlsoryfgj:prAlkIpbQDqOZtOj@aws-0-us-east-1.pooler.supabase.com:6543/postgres"

    NIGERIAN_LOCATIONS = {
        "Nigeria": "105365761",
        "Lagos, Nigeria": "105693087",
        "Abuja, Nigeria": "90009707",
        "Port Harcourt, Nigeria": "106808692",
        "Kano, Nigeria": "106808693",
    }

    KEYWORD_CATEGORIES = [
        "",  # ALL jobs
        "remote",
        "developer",
        "engineer",
        "manager",
        "analyst",
        "sales",
        "marketing",
        "finance",
        "operations",
    ]

    REMOTE_KEYWORDS = [
        "remote work Nigeria",
        "work from home Nigeria",
        "remote developer",
        "remote engineer",
    ]

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("enhanced_linkedin_scraper.log"),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)


class EnhancedLinkedInScraper:
    """Enhanced LinkedIn scraper with structured data extraction like JobSpy"""

    def __init__(self):
        # Database connection using config
        self.db_url = get_database_url()
        self.conn = None
        self.connect_to_database()

        # Initialize session and data storage
        self.session = requests.Session()
        self.jobs_data = []

        # Location mappings from config
        self.location_geo_ids = NIGERIAN_LOCATIONS

        # Nigerian locations for comprehensive scraping (from config keys + additional cities)
        self.locations = list(NIGERIAN_LOCATIONS.keys()) + [
            "Benin City, Nigeria",
            "Jos, Nigeria",
            "Warri, Nigeria",
            "Calabar, Nigeria",
            "Enugu, Nigeria",
            "Aba, Nigeria",
            "Ilorin, Nigeria",
            "Onitsha, Nigeria",
            "Abeokuta, Nigeria",
        ]

        # Search terms for comprehensive coverage (combining config categories and remote keywords)
        self.search_terms = (
            KEYWORD_CATEGORIES
            + REMOTE_KEYWORDS
            + [
                # Additional Nigeria-specific terms
                "oil and gas",
                "banking",
                "telecommunications",
                "fintech",
                "logistics",
                "agriculture",
                "healthcare",
                "education",
                "government",
                "ngo",
            ]
        )

        # Updated headers and cookies for LinkedIn
        self.headers = {
            "accept": "*/*",
            "accept-language": "en-US,en;q=0.9",
            "csrf-token": "ajax:4648340424046214088",
            "priority": "u=1, i",
            "referer": "https://ng.linkedin.com/jobs/search?keywords=&location=Nigeria&geoId=&trk=public_jobs_jobs-search-bar_search-submit",
            "sec-ch-ua": '"Not)A;Brand";v="8", "Chromium";v="138", "Google Chrome";v="138"',
            "sec-ch-ua-mobile": "?1",
            "sec-ch-ua-platform": '"Android"',
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-origin",
            "user-agent": "Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Mobile Safari/537.36",
        }

        self.cookies = {
            "lang": "v=2&lang=en-us",
            "bcookie": '"v=2&dc6d6664-563b-47c8-8e3c-468e66a1a729"',
            "lidc": '"b=VGST02:s=V:r=V:a=V:p=V:g=3610:u=1:x=1:i=1755074886:t=1755161286:v=2:sig=AQGn0tjUQSkpfVWdsjE-9oI30yZ9MiUu"',
            "JSESSIONID": "ajax:4648340424046214088",
            "bscookie": '"v=1&202508130848208695e880-f1e0-462d-8170-b40414261e1aAQGH-xQBZCKIG_GvsLAGLoPx9DpRrR-O"',
        }

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
                converted_data[key] = value.isoformat()
            elif value is None:
                converted_data[key] = None
            else:
                converted_data[key] = value

        return converted_data

    def extract_structured_job_data(self, job_card, job_url=None):
        """Extract structured job data similar to JobSpy format"""
        try:
            # Basic extraction from job card
            job_id = "N/A"
            job_link = job_card.find("a", class_="base-card__full-link")
            if job_link and job_link.get("href"):
                href = job_link.get("href")
                if "/view/" in href:
                    job_id = href.split("/view/")[-1].split("?")[0]

            # Extract core fields
            title_elem = job_card.find("h3", class_="base-search-card__title")
            title = title_elem.get_text(strip=True) if title_elem else "N/A"

            company_elem = job_card.find("h4", class_="base-search-card__subtitle")
            company = company_elem.get_text(strip=True) if company_elem else "N/A"

            location_elem = job_card.find("span", class_="job-search-card__location")
            location = location_elem.get_text(strip=True) if location_elem else "N/A"

            # Extract posting date
            date_elem = job_card.find("time", class_="job-search-card__listdate")
            date_posted = None
            if date_elem and date_elem.get("datetime"):
                try:
                    date_posted = datetime.fromisoformat(
                        date_elem.get("datetime").replace("Z", "+00:00")
                    ).date()
                except:
                    date_posted = None

            # Build job URL
            if not job_url and job_link and job_link.get("href"):
                job_url = job_link.get("href")
                if not job_url.startswith("http"):
                    job_url = "https://ng.linkedin.com" + job_url

            # Create structured data similar to JobSpy
            structured_data = {
                # Core JobSpy fields (exact match for consistency)
                "id": job_id,
                "site": "linkedin",
                "job_url": job_url,
                "job_url_direct": job_url,  # Added missing field
                "title": title,
                "company": company,
                "location": location,
                "job_type": None,  # To be filled by detail scraping
                "date_posted": date_posted,
                "job_function": None,
                "company_url": None,
                "company_logo": None,
                "company_addresses": None,  # Added missing field
                "company_industry": None,  # Added missing field
                "company_num_employees": None,  # Added missing field
                "company_revenue": None,  # Added missing field
                "company_description": None,  # Added missing field
                "ceo_name": None,  # Added missing field
                "ceo_photo_url": None,  # Added missing field
                "logo_photo_url": None,  # Added missing field
                "banner_photo_url": None,  # Added missing field
                "emails": [],
                "phones": [],
                "description": None,
                # JobSpy salary fields
                "min_amount": None,
                "max_amount": None,
                "currency": "NGN",
                # JobSpy location fields
                "city": self.extract_city(location),
                "state": self.extract_state(location),
                "country": "Nigeria",
                "is_remote": self.is_remote_job(title, location),
                # Additional LinkedIn-specific fields (for internal use)
                "work_arrangement": None,  # On-site, Remote, Hybrid
                "job_level": None,  # Entry, Mid, Senior, Executive
                "industries": None,
                "benefits": None,
                "skills": None,
                "details_fetched": False,
            }

            return structured_data

        except Exception as e:
            logger.error(f"Error extracting structured job data: {e}")
            return None

    def extract_city(self, location):
        """Extract city from location string"""
        if not location:
            return None

        location = location.strip()

        # Nigerian cities mapping
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
            "aba": "Aba",
            "ilorin": "Ilorin",
            "onitsha": "Onitsha",
            "abeokuta": "Abeokuta",
        }

        location_lower = location.lower()
        for city_key, city_name in cities.items():
            if city_key in location_lower:
                return city_name

        return None

    def extract_state(self, location):
        """Extract Nigerian state from location"""
        if not location:
            return None

        location = location.strip().lower()

        # Nigerian states mapping
        state_mapping = {
            "lagos": "Lagos",
            "abuja": "FCT",
            "port harcourt": "Rivers",
            "kano": "Kano",
            "ibadan": "Oyo",
            "kaduna": "Kaduna",
            "benin city": "Edo",
            "jos": "Plateau",
            "warri": "Delta",
            "calabar": "Cross River",
            "enugu": "Enugu",
            "aba": "Abia",
            "ilorin": "Kwara",
            "onitsha": "Anambra",
            "abeokuta": "Ogun",
        }

        for city, state in state_mapping.items():
            if city in location:
                return state

        return None

    def is_remote_job(self, title, location):
        """Check if job is remote"""
        if not title and not location:
            return False

        text = f"{title} {location}".lower()
        remote_keywords = ["remote", "work from home", "wfh", "telecommute", "virtual"]

        return any(keyword in text for keyword in remote_keywords)

    def enhance_job_with_details(self, job_data):
        """Enhance job data with detailed information from job page"""
        if not job_data.get("job_url"):
            return job_data

        try:
            logger.debug(f"Fetching details for: {job_data['title']}")

            response = self.session.get(
                job_data["job_url"],
                headers=self.headers,
                cookies=self.cookies,
                timeout=30,
            )

            if response.status_code != 200:
                logger.warning(f"Failed to fetch job details: {response.status_code}")
                return job_data

            soup = BeautifulSoup(response.text, "html.parser")

            # Extract detailed information
            details = self.extract_job_details_from_page(soup)

            # Merge details into job data
            job_data.update(details)
            job_data["details_fetched"] = True

            return job_data

        except Exception as e:
            logger.error(f"Error enhancing job details: {e}")
            job_data["details_fetched"] = False
            return job_data

    def extract_job_details_from_page(self, soup):
        """Extract detailed structured information from job page"""
        details = {}

        try:
            # Extract job description
            description = self.extract_description(soup)
            if description:
                details["description"] = description

                # Extract emails and phones from description
                details["emails"] = self.extract_emails(description)
                details["phones"] = self.extract_phones(description)

            # Extract job criteria (employment type, experience level, etc.)
            criteria = self.extract_job_criteria(soup)
            details.update(criteria)

            # Extract salary information
            salary_info = self.extract_salary_info(soup)
            if salary_info:
                details.update(salary_info)

            # Extract company information
            company_info = self.extract_company_info(soup)
            details.update(company_info)

            # Extract skills and requirements
            skills = self.extract_skills(soup)
            if skills:
                details["skills"] = skills

            # Extract benefits
            benefits = self.extract_benefits(soup)
            if benefits:
                details["benefits"] = benefits

        except Exception as e:
            logger.error(f"Error extracting job details: {e}")

        return details

    def extract_emails(self, text):
        """Extract email addresses from text"""
        if not text:
            return []

        email_pattern = r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"
        emails = re.findall(email_pattern, text)
        return list(set(emails))  # Remove duplicates

    def extract_phones(self, text):
        """Extract Nigerian phone numbers from text"""
        if not text:
            return []

        # Nigerian phone number patterns
        phone_patterns = [
            r"\+234[0-9]{10}",  # +234xxxxxxxxxx
            r"234[0-9]{10}",  # 234xxxxxxxxxx
            r"0[789][01][0-9]{8}",  # 08xxxxxxxxx, 09xxxxxxxxx, 07xxxxxxxxx
            r"[789][01][0-9]{8}",  # 8xxxxxxxxx, 9xxxxxxxxx, 7xxxxxxxxx
        ]

        phones = []
        for pattern in phone_patterns:
            phones.extend(re.findall(pattern, text))

        return list(set(phones))  # Remove duplicates

    def extract_description(self, soup):
        """Extract job description with multiple fallback selectors"""
        selectors = [
            "div.show-more-less-html__markup",
            "div.description__text",
            "section.description",
            "div.jobs-description__content",
            "div.jobs-box__html-content",
            "div.jobs-unified-top-card__job-description",
            "div.job-details-jobs-unified-top-card__job-description",
            'div[data-test-id="job-details-description"]',
            'section[data-test-id="job-details-description"]',
            "div.jobs-description-content__text",
            "div.jobs-description-content__text--stretch",
            "div.jobs-description",
            "section.jobs-description",
        ]

        for selector in selectors:
            elem = soup.select_one(selector)
            if elem:
                text = elem.get_text(separator=" ", strip=True)
                text = re.sub(r"\s+", " ", text)
                if len(text) > 50:  # Only return if substantial content
                    return text

        return None

    def extract_job_criteria(self, soup):
        """Extract job criteria (employment type, experience level, work arrangement, etc.)"""
        criteria = {}

        # Method 1: Standard job criteria items (most common)
        criteria_items = soup.find_all("li", class_="description__job-criteria-item")
        for item in criteria_items:
            subheader = item.find("h3", class_="description__job-criteria-subheader")
            text = item.find("span", class_="description__job-criteria-text")

            if subheader and text:
                key = (
                    subheader.get_text(strip=True)
                    .lower()
                    .replace(" ", "_")
                    .replace(":", "")
                )
                value = text.get_text(strip=True)

                logger.debug(f"Found criteria: {key} = {value}")

                # Map to JobSpy-like fields with comprehensive mapping
                if "employment" in key or "job_type" in key:
                    criteria["job_type"] = value
                elif "experience" in key or "seniority" in key:
                    criteria["job_level"] = value
                elif "function" in key:
                    criteria["job_function"] = value
                elif "industries" in key:
                    criteria["industries"] = value
                elif "workplace" in key or "work_arrangement" in key:
                    criteria["work_arrangement"] = value  # On-site, Remote, Hybrid
                    # Also set remote flag
                    if "remote" in value.lower():
                        criteria["is_remote"] = True
                    elif "on-site" in value.lower() or "onsite" in value.lower():
                        criteria["is_remote"] = False

        # Method 2: Alternative selectors for job criteria
        if len(criteria) < 3:  # Try alternative methods if we don't have enough data
            # Try unified top card selectors
            selectors = [
                "ul.description__job-criteria-list li",
                "div.jobs-unified-top-card__job-insight",
                "span.jobs-unified-top-card__job-insight-text",
                "div.job-details-jobs-unified-top-card__job-insight",
                "span.jobs-unified-top-card__job-insight",
                "div.jobs-unified-top-card__job-insight-text",
            ]

            for selector in selectors:
                elements = soup.select(selector)
                for elem in elements:
                    text = elem.get_text(strip=True)
                    logger.debug(f"Found insight text: {text}")

                    # Look for specific patterns
                    if (
                        any(
                            keyword in text.lower()
                            for keyword in [
                                "full-time",
                                "part-time",
                                "contract",
                                "internship",
                            ]
                        )
                        and "job_type" not in criteria
                    ):
                        criteria["job_type"] = text
                        logger.debug(f"Set job_type: {text}")
                    elif (
                        any(
                            keyword in text.lower()
                            for keyword in ["on-site", "remote", "hybrid", "onsite"]
                        )
                        and "work_arrangement" not in criteria
                    ):
                        criteria["work_arrangement"] = text
                        logger.debug(f"Set work_arrangement: {text}")
                        if "remote" in text.lower():
                            criteria["is_remote"] = True
                        elif "on-site" in text.lower():
                            criteria["is_remote"] = False
                    elif (
                        any(
                            keyword in text.lower()
                            for keyword in ["entry", "mid", "senior", "executive"]
                        )
                        and "job_level" not in criteria
                    ):
                        criteria["job_level"] = text
                        logger.debug(f"Set job_level: {text}")

        # Method 3: Look in job insights section
        insights = soup.find_all(
            "div", class_="job-details-jobs-unified-top-card__job-insight"
        )
        for insight in insights:
            text = insight.get_text(strip=True)

            # Check for employment type
            if any(
                keyword in text.lower()
                for keyword in [
                    "full-time",
                    "part-time",
                    "contract",
                    "internship",
                    "temporary",
                ]
            ):
                if "job_type" not in criteria:
                    criteria["job_type"] = text

            # Check for work arrangement
            if any(
                keyword in text.lower()
                for keyword in ["on-site", "remote", "hybrid", "onsite"]
            ):
                if "work_arrangement" not in criteria:
                    criteria["work_arrangement"] = text
                if "remote" in text.lower():
                    criteria["is_remote"] = True
                elif "on-site" in text.lower() or "onsite" in text.lower():
                    criteria["is_remote"] = False

        return criteria

    def extract_salary_info(self, soup):
        """Extract salary information with multiple methods"""
        salary_info = {}

        selectors = [
            "span.salary",
            "div.salary-main-rail__salary-info",
            "span.jobs-unified-top-card__job-insight",
            "div.job-details-jobs-unified-top-card__job-insight",
        ]

        for selector in selectors:
            elem = soup.select_one(selector)
            if elem and (
                "$" in elem.get_text()
                or "₦" in elem.get_text()
                or "salary" in elem.get_text().lower()
            ):
                salary_text = elem.get_text(strip=True)

                # Parse salary range
                salary_info["salary"] = salary_text

                # Try to extract min/max amounts
                amounts = re.findall(r"[\d,]+", salary_text)
                if len(amounts) >= 2:
                    try:
                        salary_info["min_amount"] = float(amounts[0].replace(",", ""))
                        salary_info["max_amount"] = float(amounts[1].replace(",", ""))
                    except:
                        pass
                elif len(amounts) == 1:
                    try:
                        amount = float(amounts[0].replace(",", ""))
                        salary_info["min_amount"] = amount
                        salary_info["max_amount"] = amount
                    except:
                        pass

                # Detect currency
                if "₦" in salary_text or "NGN" in salary_text:
                    salary_info["currency"] = "NGN"
                elif "$" in salary_text or "USD" in salary_text:
                    salary_info["currency"] = "USD"

                break

        return salary_info

    def extract_company_info(self, soup):
        """Extract detailed company information"""
        company_info = {}

        # Company name
        selectors = [
            "a.topcard__org-name-link",
            "span.topcard__flavor",
            "h3.topcard__title",
            "a.jobs-unified-top-card__company-name",
        ]

        for selector in selectors:
            elem = soup.select_one(selector)
            if elem:
                company_info["company_name_detailed"] = elem.get_text(strip=True)
                # Try to get company URL
                if elem.get("href"):
                    company_info["company_url"] = elem.get("href")
                break

        return company_info

    def extract_skills(self, soup):
        """Extract required skills and technologies"""
        skills = []

        # Method 1: Skills section
        skills_section = soup.find("section", {"data-test-id": "job-details-skills"})
        if skills_section:
            skill_items = skills_section.find_all(
                "span", class_="job-details-skill-match-status-list__skill-badge"
            )
            skills.extend([skill.get_text(strip=True) for skill in skill_items])

        return skills if skills else None

    def extract_benefits(self, soup):
        """Extract job benefits"""
        benefits = []

        # Look for benefits section
        benefits_keywords = ["benefits", "perks", "compensation", "package"]

        for keyword in benefits_keywords:
            elements = soup.find_all(text=re.compile(keyword, re.IGNORECASE))
            for element in elements:
                parent = element.parent
                if parent:
                    text = parent.get_text(strip=True)
                    if (
                        len(text) > 20 and len(text) < 200
                    ):  # Reasonable benefit description
                        benefits.append(text)

        return benefits if benefits else None

    def search_jobs(self, keywords="", location="Nigeria", max_results=50, delay=2.0):
        """Search for jobs using LinkedIn's public jobs page"""
        logger.info(f"Starting job search for '{keywords}' in {location}")

        # Auto-detect geo_id if location is in our mapping
        geo_id = self.location_geo_ids.get(location, "105365761")

        all_jobs = []
        start = 0

        while len(all_jobs) < max_results:
            logger.info(f"Fetching jobs starting from position {start}")

            # Use the correct API endpoint
            base_url = (
                "https://ng.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search"
            )
            params = {
                "keywords": keywords,
                "location": location,
                "geoId": geo_id,
                "start": str(start),
                "trk": "public_jobs_jobs-search-bar_search-submit",
            }

            try:
                response = self.session.get(
                    base_url,
                    headers=self.headers,
                    cookies=self.cookies,
                    params=params,
                    timeout=30,
                )

                if response.status_code != 200:
                    logger.error(
                        f"Failed to fetch jobs. Status code: {response.status_code}"
                    )
                    break

                # Parse HTML response
                soup = BeautifulSoup(response.text, "html.parser")

                # Find job cards
                job_cards = soup.find_all("div", class_="base-card")

                if not job_cards:
                    logger.info("No more jobs found")
                    break

                # Extract structured job information from HTML
                batch_jobs = []
                for card in job_cards:
                    job_info = self.extract_structured_job_data(card)
                    if job_info:
                        batch_jobs.append(job_info)

                if not batch_jobs:
                    logger.info("No valid jobs in this batch")
                    break

                all_jobs.extend(batch_jobs)
                logger.info(f"Fetched {len(batch_jobs)} jobs, total: {len(all_jobs)}")

                start += 25

                # Rate limiting
                if start < max_results:
                    time.sleep(delay)

            except Exception as e:
                logger.error(f"Error fetching jobs: {e}")
                break

        # Limit to requested number
        all_jobs = all_jobs[:max_results]
        self.jobs_data = all_jobs

        logger.info(f"Search completed. Total jobs fetched: {len(all_jobs)}")
        return all_jobs

    def save_jobs_to_database(self, jobs_data, search_context):
        """Save structured jobs to database"""
        if not jobs_data:
            return 0

        saved_count = 0

        try:
            with self.conn.cursor() as cur:
                for job in jobs_data:
                    try:
                        # Convert dates to strings for JSON serialization
                        job_data = self.convert_dates_to_strings(job)

                        # Add metadata
                        job_data["search_context"] = search_context
                        job_data["scraped_timestamp"] = datetime.now().isoformat()

                        # Generate job ID
                        job_id = self.generate_job_id(job_data)

                        # JSON serialization
                        json_data = json.dumps(job_data, ensure_ascii=False)

                        # Insert into database
                        cur.execute(
                            """
                            INSERT INTO raw_jobs (source, source_job_id, raw_data, source_url, scraped_at)
                            VALUES (%s, %s, %s, %s, NOW())
                            ON CONFLICT (source, source_job_id) DO NOTHING
                        """,
                            ("linkedin", job_id, json_data, job_data.get("job_url")),
                        )

                        if cur.rowcount > 0:
                            saved_count += 1
                            self.stats["total_saved"] += 1
                            logger.debug(
                                f"✅ Saved: {job_data.get('title', 'N/A')[:30]}"
                            )
                        else:
                            self.stats["duplicates_skipped"] += 1
                            logger.debug(
                                f"🔄 Duplicate: {job_data.get('title', 'N/A')[:30]}"
                            )

                    except Exception as e:
                        logger.error(f"Error saving job: {e}")
                        self.stats["errors"] += 1
                        continue

        except Exception as e:
            logger.error(f"Database error: {e}")
            raise

        return saved_count

    def scrape_and_save(
        self,
        search_term,
        location,
        search_context,
        max_results=100,
        enhance_details=True,  # Default to True for detailed scraping
    ):
        """Scrape jobs and save to database with detailed enhancement by default"""
        logger.info(f"🔍 Scraping: '{search_term}' in {location}")

        try:
            # Get basic job listings
            jobs = self.search_jobs(search_term, location, max_results)

            if not jobs:
                logger.info("No jobs found")
                return 0

            # Always enhance with details for structured data
            logger.info(
                f"🔍 Enhancing {len(jobs)} jobs with detailed structured data..."
            )
            enhanced_jobs = []

            for i, job in enumerate(jobs, 1):
                logger.info(
                    f"📄 Processing job {i}/{len(jobs)}: {job['title'][:50]}..."
                )

                # Always enhance job with details to get structured data
                enhanced_job = self.enhance_job_with_details(job)
                enhanced_jobs.append(enhanced_job)

                # Rate limiting for detail requests (essential for LinkedIn)
                if i < len(jobs):
                    time.sleep(4.0)  # Increased delay for stability

            jobs = enhanced_jobs

            # Save to database
            saved_count = self.save_jobs_to_database(jobs, search_context)

            self.stats["total_scraped"] += len(jobs)
            logger.info(f"✅ Scraped {len(jobs)} jobs, saved {saved_count} new jobs")

            return saved_count

        except Exception as e:
            logger.error(f"Error in scrape_and_save: {e}")
            self.stats["errors"] += 1
            return 0

    def run_test_scrape(self):
        """Run a test scrape to verify functionality"""
        logger.info("🧪 Running test scrape...")

        try:
            self.setup_database()

            # Test with a simple search - detailed scraping enabled by default
            saved_count = self.scrape_and_save(
                search_term="software engineer",
                location="Nigeria",  # Use Nigeria for broader Nigerian job results
                search_context="test_scrape_detailed",
                max_results=5,  # Reduced for testing since we're doing detailed scraping
                enhance_details=True,
            )

            if saved_count > 0:
                logger.info(f"✅ Test successful! Saved {saved_count} jobs")
                return True
            else:
                logger.warning(
                    "⚠️  Test completed but no new jobs saved (might be duplicates)"
                )
                return True

        except Exception as e:
            logger.error(f"❌ Test failed: {e}")
            return False

    def run_comprehensive_scrape(self, enhance_details=False):
        """Run comprehensive scraping across all locations and search terms"""
        logger.info("🚀 Starting comprehensive LinkedIn scraping...")
        logger.info(f"📊 Locations: {len(self.locations)}")
        logger.info(f"📊 Search terms: {len(self.search_terms)}")
        logger.info(
            f"📊 Total searches: {len(self.locations) * len(self.search_terms)}"
        )
        logger.info(
            f"📊 Detail enhancement: {'Enabled' if enhance_details else 'Disabled'}"
        )

        start_time = datetime.now()

        try:
            self.setup_database()

            total_searches = len(self.locations) * len(self.search_terms)
            current_search = 0

            for location in self.locations:
                for search_term in self.search_terms:
                    current_search += 1
                    search_context = f"comprehensive_{location}_{search_term}"

                    logger.info(f"📦 Search {current_search}/{total_searches}")
                    self.scrape_and_save(
                        search_term=search_term,
                        location=location,
                        search_context=search_context,
                        max_results=50,  # Reduced since detailed scraping takes longer
                        enhance_details=True,  # Always use detailed scraping
                    )

                    # Progress update
                    if current_search % 10 == 0:
                        logger.info(
                            f"📊 Progress: {self.stats['total_saved']} saved so far"
                        )

                    # Rate limiting between searches
                    time.sleep(3.0)

            # Final statistics
            end_time = datetime.now()
            duration = end_time - start_time

            logger.info("🎉 Comprehensive scraping completed!")
            logger.info(f"⏱️  Duration: {duration}")
            self.show_final_stats()

        except Exception as e:
            logger.error(f"❌ Comprehensive scraping failed: {e}")
            self.show_final_stats()
            raise
        finally:
            if self.conn:
                self.conn.close()
                logger.info("🔌 Database connection closed")

    def show_final_stats(self):
        """Show final scraping statistics"""
        logger.info("📊 FINAL STATISTICS:")
        logger.info(f"   Total scraped: {self.stats['total_scraped']:,}")
        logger.info(f"   Total saved: {self.stats['total_saved']:,}")
        logger.info(f"   Duplicates skipped: {self.stats['duplicates_skipped']:,}")
        logger.info(f"   Errors: {self.stats['errors']:,}")

        if self.stats["total_scraped"] > 0:
            success_rate = (
                (self.stats["total_scraped"] - self.stats["errors"])
                / self.stats["total_scraped"]
            ) * 100
            logger.info(f"   Success rate: {success_rate:.1f}%")


def main():
    """Main function for testing"""
    print("🔗 Enhanced LinkedIn Scraper - Structured Data Extraction")
    print("=" * 60)
    print("Choose your option:")
    print("1. Test scraper (recommended first)")
    print("2. Run basic comprehensive scraping")
    print("3. Run enhanced comprehensive scraping (with details)")
    print("4. Exit")

    while True:
        choice = input("\nEnter your choice (1-4): ").strip()

        if choice == "1":
            print("\n🧪 Running test scraper...")
            try:
                scraper = EnhancedLinkedInScraper()
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
            print("\n🚀 Running basic comprehensive scraping...")
            print("⚠️  This will:")
            print("   - Scrape thousands of Nigerian LinkedIn jobs")
            print("   - Extract structured data (JobSpy-like format)")
            print("   - Take 1-2 hours to complete")
            print("   - Save directly to raw_jobs database")

            confirm = input("\nProceed? (y/N): ").strip().lower()

            if confirm in ["y", "yes"]:
                try:
                    scraper = EnhancedLinkedInScraper()
                    scraper.run_comprehensive_scrape(enhance_details=False)
                    print("\n🎉 Basic comprehensive scraping completed!")

                except Exception as e:
                    print(f"❌ Scraping error: {e}")
            else:
                print("Cancelled.")
            break

        elif choice == "3":
            print("\n🚀 Running enhanced comprehensive scraping...")
            print("⚠️  This will:")
            print("   - Scrape thousands of Nigerian LinkedIn jobs")
            print("   - Extract detailed structured data with job descriptions")
            print("   - Take 3-4 hours to complete (slower due to detail fetching)")
            print("   - Save directly to raw_jobs database")

            confirm = input("\nProceed? (y/N): ").strip().lower()

            if confirm in ["y", "yes"]:
                try:
                    scraper = EnhancedLinkedInScraper()
                    scraper.run_comprehensive_scrape(enhance_details=True)
                    print("\n🎉 Enhanced comprehensive scraping completed!")

                except Exception as e:
                    print(f"❌ Scraping error: {e}")
            else:
                print("Cancelled.")
            break

        elif choice == "4":
            print("👋 Goodbye!")
            break

        else:
            print("Invalid choice. Please enter 1-4.")


if __name__ == "__main__":
    main()
