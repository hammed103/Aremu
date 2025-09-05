#!/usr/bin/env python3
"""
Intelligent Fuzzy Job Matching System for Aremu WhatsApp Bot
Matches users to jobs using multiple intelligent strategies
"""

import logging
import re
from typing import Dict, List, Optional, Tuple
import psycopg2.extras
from difflib import SequenceMatcher
from collections import defaultdict

logger = logging.getLogger(__name__)


class IntelligentJobMatcher:
    """Advanced job matching using fuzzy logic, semantic similarity, and skill matching"""

    def __init__(self, db_connection):
        self.connection = db_connection

        # Semantic job title clusters for intelligent matching
        self.JOB_CLUSTERS = {
            "software_development": [
                "developer",
                "engineer",
                "programmer",
                "coder",
                "architect",
                "frontend",
                "backend",
                "fullstack",
                "web developer",
                "software engineer",
                "react developer",
                "vue developer",
                "angular developer",
                "node developer",
                "python developer",
                "java developer",
                "javascript developer",
            ],
            "data_science": [
                "data scientist",
                "data analyst",
                "machine learning",
                "ai engineer",
                "data engineer",
                "analytics",
                "statistician",
                "ml engineer",
                "ai researcher",
                "data specialist",
            ],
            "design": [
                "designer",
                "ui designer",
                "ux designer",
                "graphic designer",
                "web designer",
                "product designer",
                "visual designer",
                "creative",
                "artist",
                "illustrator",
            ],
            "management": [
                "manager",
                "director",
                "lead",
                "supervisor",
                "coordinator",
                "project manager",
                "product manager",
                "team lead",
                "head of",
                "chief",
                "executive",
            ],
            "marketing": [
                "marketer",
                "marketing",
                "digital marketing",
                "content marketing",
                "social media",
                "seo specialist",
                "brand manager",
                "campaign manager",
                "growth hacker",
                "content creator",
            ],
            "sales": [
                "sales",
                "account manager",
                "business development",
                "sales representative",
                "account executive",
                "sales manager",
                "relationship manager",
            ],
            "healthcare": [
                "nurse",
                "doctor",
                "physician",
                "therapist",
                "medical",
                "healthcare",
                "pharmacist",
                "dentist",
                "surgeon",
                "technician",
            ],
            "education": [
                "teacher",
                "instructor",
                "professor",
                "educator",
                "tutor",
                "lecturer",
                "trainer",
                "coordinator",
                "administrator",
            ],
        }

        # Common skill synonyms for better matching
        self.SKILL_SYNONYMS = {
            "javascript": ["js", "javascript", "ecmascript"],
            "typescript": ["ts", "typescript"],
            "react": ["react", "reactjs", "react.js"],
            "vue": ["vue", "vuejs", "vue.js"],
            "angular": ["angular", "angularjs"],
            "node": ["node", "nodejs", "node.js"],
            "python": ["python", "py"],
            "machine learning": [
                "ml",
                "machine learning",
                "ai",
                "artificial intelligence",
            ],
            "data science": ["data science", "data analytics", "analytics"],
            "project management": ["pm", "project management", "agile", "scrum"],
        }

    def search_jobs_for_user(self, user_id: int, limit: int = 100) -> List[Dict]:
        """Advanced job search using multiple intelligent matching strategies"""
        try:
            # Get user preferences
            cursor = self.connection.cursor(
                cursor_factory=psycopg2.extras.RealDictCursor
            )
            cursor.execute(
                "SELECT * FROM user_preferences WHERE user_id = %s", (user_id,)
            )
            prefs = cursor.fetchone()

            if not prefs:
                logger.info(f"No preferences found for user {user_id}")
                return []

            prefs = dict(prefs)
            logger.info(f"🔍 Intelligent job search for user {user_id}")

            # Get all recent jobs for matching (from canonical_jobs table)
            cursor.execute(
                """
                SELECT
                    id, title, company, location, description, job_url, source,
                    ai_salary_min as salary_min, ai_salary_max as salary_max,
                    ai_salary_currency as salary_currency,
                    ai_employment_type as employment_type,
                    ai_remote_allowed as is_remote,
                    posted_date,

                    -- Contact Information (CRITICAL for CTA buttons)
                    email, ai_email, whatsapp_number, ai_whatsapp_number,

                    -- AI Enhanced Fields for Better Matching
                    ai_job_titles,  -- Full array of job title variations
                    ai_job_function,  -- Sales, Engineering, Marketing, etc.
                    ai_job_level,  -- Entry-level, Mid-level, Senior, etc.
                    ai_industry,  -- Technology, Healthcare, Finance, etc.
                    ai_skills_required,  -- Required skills array
                    ai_years_experience_min,
                    ai_years_experience_max,
                    ai_work_arrangement,  -- Remote, On-site, Hybrid
                    ai_remote_allowed,

                    -- Fallback fields
                    CASE WHEN ai_job_titles IS NOT NULL AND array_length(ai_job_titles, 1) > 0
                         THEN ai_job_titles[1]
                         ELSE title
                    END as ai_job_title,
                    job_url as ai_application_url,
                    ai_summary as whatsapp_summary
                FROM canonical_jobs
                WHERE posted_date >= CURRENT_DATE - INTERVAL '60 days'
                   OR posted_date IS NULL
                ORDER BY
                    CASE WHEN ai_summary IS NOT NULL THEN 0 ELSE 1 END,
                    -- Balanced sorting to ensure WhatsApp jobs aren't pushed out by more frequent JobSpy scraping
                    CASE
                        WHEN source = 'whatsapp' THEN scraped_at + INTERVAL '1 day'  -- Boost WhatsApp jobs
                        ELSE scraped_at
                    END DESC NULLS FIRST,
                    id DESC  -- Add deterministic secondary sort
                LIMIT 2000  -- Increased limit to ensure WhatsApp jobs are included
            """
            )
            all_jobs = cursor.fetchall()

            if not all_jobs:
                logger.info("No recent jobs found in database")
                return []

            # Score each job using multiple strategies
            scored_jobs = []
            for job in all_jobs:
                job_dict = dict(job)
                score = self._calculate_job_score(prefs, job_dict)
                if score >= 50.0:  # Only include jobs with 50%+ match
                    job_dict["match_score"] = score
                    job_dict["match_reasons"] = self._get_match_reasons(prefs, job_dict)
                    scored_jobs.append(job_dict)

            # Sort by score and return top matches
            scored_jobs.sort(key=lambda x: x["match_score"], reverse=True)
            top_jobs = scored_jobs[:limit]

            logger.info(
                f"🎯 Found {len(top_jobs)} intelligent matches for user {user_id}"
            )
            return top_jobs

        except Exception as e:
            logger.error(f"❌ Error in intelligent job search: {e}")
            import traceback

            logger.error(traceback.format_exc())
            return []

    def _calculate_job_score(self, user_prefs: Dict, job: Dict) -> float:
        """
        Calculate AI-enhanced job match score using multiple intelligent strategies

        ENHANCED SCORING SYSTEM (Total: 162 points, capped at 100):
        ================================================================
        1. AI Job Titles (35 pts)     - Fuzzy matching with 15+ AI variations
        2. AI Job Function (25 pts)    - Semantic function classification
        3. AI Industry (20 pts)        - Industry category matching
        4. Skills Matching (20 pts)    - Required/preferred skills with synonyms
        5. Work Arrangement (15 pts)   - Remote/hybrid/onsite with AI detection
        6. Semantic Clusters (15 pts)  - Reduced weight clustering
        7. Salary Matching (12 pts)    - Currency conversion & range flexibility
        8. Experience Level (10 pts)   - AI years + level hierarchy matching
        9. Contact Info Bonus (10 pts) - Prioritize jobs with apply methods

        LOCATION FILTERING (Not Scored):
        - Location works as a FILTER, not scoring
        - Jobs that don't match user's preferred_locations are excluded
        - Intelligent abbreviation handling (Lagos/LOS, Abuja/FCT, PH, etc.)
        - Geographic proximity for Nigerian cities and states

        Key Enhancements:
        - Uses AI-enhanced fields (ai_city, ai_remote_allowed, ai_salary_*, etc.)
        - Location filtering with abbreviation intelligence
        - Currency conversion with flexible salary ranges
        - Required vs preferred skills distinction
        - Experience level hierarchy with flexibility
        - Work arrangement intelligent detection
        """

        # LOCATION FILTERING - Apply before scoring
        if not self._is_location_compatible(user_prefs, job):
            return 0.0  # Exclude jobs that don't match location preferences

        total_score = 0.0

        # 1. AI JOB TITLES MATCHING (35 points) - Enhanced with 15+ AI variations
        ai_title_score = self._score_ai_job_titles_match(user_prefs, job)
        total_score += ai_title_score

        # 2. AI JOB FUNCTION MATCHING (25 points) - New AI-powered matching
        function_score = self._score_ai_job_function_match(user_prefs, job)
        total_score += function_score

        # 3. AI INDUSTRY MATCHING (20 points) - New AI industry classification
        industry_score = self._score_ai_industry_match(user_prefs, job)
        total_score += industry_score

        # 4. SEMANTIC CLUSTER MATCHING (15 points) - Reduced weight
        cluster_score = self._score_semantic_clusters(user_prefs, job)
        total_score += cluster_score * 0.6  # Reduce from 25 to 15 points

        # 5. SKILLS MATCHING (20 points) - Enhanced with AI required/preferred skills
        skills_score = self._score_skills_match(user_prefs, job)
        total_score += skills_score

        # 6. WORK ARRANGEMENT MATCHING (15 points) - RE-ENABLED with AI enhancement
        work_score = self._score_work_arrangement(user_prefs, job)
        total_score += work_score

        # 7. SALARY MATCHING (12 points) - Enhanced with currency conversion
        salary_score = self._score_salary_match(user_prefs, job)
        total_score += salary_score

        # 9. EXPERIENCE LEVEL MATCHING (10 points) - Enhanced with AI fields
        exp_score = self._score_experience_match(user_prefs, job)
        total_score += exp_score

        # 10. CONTACT INFORMATION BONUS (10 points) - NEW: Prioritize jobs with contact info
        contact_score = self._score_contact_availability(job)
        total_score += contact_score

        return min(total_score, 100.0)  # Cap at 100%

    def _is_location_compatible(self, user_prefs: Dict, job: Dict) -> bool:
        """
        LOCATION FILTERING - Determine if job location matches user preferences

        This is a FILTER, not scoring. Jobs that don't match are excluded entirely.

        Compares:
        - user_prefs['preferred_locations'] vs job['location'], job['ai_city'], job['ai_state']
        - Handles abbreviations: Lagos/LOS, Abuja/FCT, Port Harcourt/PH, etc.
        - Geographic proximity for Nigerian locations
        - Remote work exceptions
        """
        user_locations = user_prefs.get("preferred_locations", []) or []
        willing_to_relocate = user_prefs.get("willing_to_relocate", False)
        user_work_arrangements = user_prefs.get("work_arrangements", []) or []

        # If no location preferences set, allow all jobs
        if not user_locations:
            return True

        # If user wants remote work, check if job allows remote
        if "remote" in [arr.lower() for arr in user_work_arrangements]:
            if self._job_allows_remote_work(job):
                return True  # Remote jobs bypass location filtering

        # If user is willing to relocate, allow all jobs with valid locations
        if willing_to_relocate:
            job_location = job.get("location", "").strip()
            ai_city = job.get("ai_city", "").strip()
            ai_country = job.get("ai_country", "").strip()
            if job_location or ai_city or ai_country:
                return True

        # Get job location data
        job_location = (job.get("location", "") or "").lower().strip()
        ai_city = (job.get("ai_city", "") or "").lower().strip()
        ai_state = (job.get("ai_state", "") or "").lower().strip()
        ai_country = (job.get("ai_country", "") or "").lower().strip()

        # Check each user preferred location
        for user_location in user_locations:
            user_loc_lower = user_location.lower().strip()

            if self._locations_match(
                user_loc_lower, job_location, ai_city, ai_state, ai_country
            ):
                return True

        return False

    def _job_allows_remote_work(self, job: Dict) -> bool:
        """Check if job allows remote work - prioritize AI fields over text"""
        # AI-enhanced remote detection (highest priority)
        ai_remote_allowed = job.get("ai_remote_allowed")
        ai_work_arrangement = (job.get("ai_work_arrangement", "") or "").lower()

        # If AI fields are available, use them exclusively
        if ai_remote_allowed is not None or ai_work_arrangement:
            if ai_remote_allowed or "remote" in ai_work_arrangement:
                return True
            else:
                return False  # AI says not remote, don't check text

        # Legacy remote detection (fallback)
        is_remote = job.get("is_remote", False)
        if is_remote:
            return True

        # Text-based remote detection (only if no AI data available)
        job_title = (job.get("title", "") or "").lower()
        job_description = (job.get("description", "") or "").lower()
        location = (job.get("location", "") or "").lower()

        remote_keywords = [
            "remote",
            "work from home",
            "wfh",
            "telecommute",
            "distributed",
        ]
        all_text = f"{job_title} {job_description} {location}"

        return any(keyword in all_text for keyword in remote_keywords)

    def _locations_match(
        self,
        user_location: str,
        job_location: str,
        ai_city: str,
        ai_state: str,
        ai_country: str,
    ) -> bool:
        """
        Intelligent location matching with abbreviation handling

        Handles:
        - Direct matches
        - Nigerian abbreviations (Lagos/LOS, Abuja/FCT, PH, etc.)
        - State-level matching
        - City variations and proximity
        - International locations
        """
        # Direct exact matches
        if (
            user_location in job_location
            or user_location in ai_city
            or user_location in ai_state
        ):
            return True

        # Nigerian location abbreviations and variations
        if self._nigerian_location_match(
            user_location, job_location, ai_city, ai_state
        ):
            return True

        # International location matching
        if self._international_location_match(
            user_location, job_location, ai_city, ai_country
        ):
            return True

        # Geographic proximity for Nigerian cities
        if self._nigerian_proximity_match(user_location, ai_city, ai_state):
            return True

        return False

    def _nigerian_location_match(
        self, user_location: str, job_location: str, ai_city: str, ai_state: str
    ) -> bool:
        """Handle Nigerian location abbreviations and variations"""

        # Nigerian location mappings with abbreviations
        nigerian_locations = {
            # Lagos variations
            "lagos": [
                "lagos",
                "los",
                "lagos state",
                "lagos island",
                "lagos mainland",
                "ikeja",
                "victoria island",
                "vi",
                "ikoyi",
                "lekki",
                "surulere",
                "yaba",
            ],
            "los": ["lagos", "los", "lagos state"],
            # Abuja variations
            "abuja": [
                "abuja",
                "fct",
                "federal capital territory",
                "garki",
                "wuse",
                "maitama",
                "asokoro",
                "gwarinpa",
            ],
            "fct": ["abuja", "fct", "federal capital territory"],
            # Port Harcourt variations
            "port harcourt": [
                "port harcourt",
                "ph",
                "portharcourt",
                "rivers",
                "rivers state",
            ],
            "ph": ["port harcourt", "ph", "portharcourt", "rivers"],
            # Other major cities
            "kano": ["kano", "kano state"],
            "ibadan": ["ibadan", "oyo", "oyo state"],
            "kaduna": ["kaduna", "kaduna state"],
            "jos": ["jos", "plateau", "plateau state"],
            "enugu": ["enugu", "enugu state"],
            "calabar": ["calabar", "cross river", "cross river state"],
            "warri": ["warri", "delta", "delta state"],
            "benin": ["benin", "benin city", "edo", "edo state"],
            "aba": ["aba", "abia", "abia state"],
            "onitsha": ["onitsha", "anambra", "anambra state"],
        }

        # Check if user location matches any variation
        user_variations = []
        for main_location, variations in nigerian_locations.items():
            if user_location in variations:
                user_variations = variations
                break

        if not user_variations:
            user_variations = [user_location]  # Use as-is if no mapping found

        # Check against job location fields
        all_job_text = f"{job_location} {ai_city} {ai_state}".lower()

        return any(variation in all_job_text for variation in user_variations)

    def _international_location_match(
        self, user_location: str, job_location: str, ai_city: str, ai_country: str
    ) -> bool:
        """Handle international location matching"""

        # Country-level matching
        country_mappings = {
            "nigeria": ["nigeria", "ng", "nigerian", "naija"],
            "ghana": ["ghana", "gh", "ghanaian"],
            "kenya": ["kenya", "ke", "kenyan", "nairobi"],
            "south africa": ["south africa", "za", "sa", "cape town", "johannesburg"],
            "united states": ["usa", "us", "united states", "america", "american"],
            "united kingdom": [
                "uk",
                "united kingdom",
                "britain",
                "british",
                "england",
                "london",
            ],
            "canada": ["canada", "ca", "canadian", "toronto", "vancouver"],
            "germany": ["germany", "de", "german", "berlin", "munich"],
            "france": ["france", "fr", "french", "paris"],
        }

        # Find user's country group
        user_country_variations = []
        for country, variations in country_mappings.items():
            if user_location in variations:
                user_country_variations = variations
                break

        if user_country_variations:
            all_job_text = f"{job_location} {ai_city} {ai_country}".lower()
            return any(
                variation in all_job_text for variation in user_country_variations
            )

        return False

    def _nigerian_proximity_match(
        self, user_location: str, ai_city: str, ai_state: str
    ) -> bool:
        """Check for geographic proximity within Nigerian regions - STRICT matching only"""

        # Regional clusters for proximity matching - ONLY same region allowed
        regional_clusters = {
            "southwest": [
                "lagos",
                "ibadan",
                "abeokuta",
                "ilorin",
                "oshogbo",
                "akure",
                "ado ekiti",
            ],
            "southeast": [
                "enugu",
                "onitsha",
                "aba",
                "owerri",
                "umuahia",
                "awka",
                "abakaliki",
            ],
            "southsouth": [
                "port harcourt",
                "warri",
                "benin",
                "calabar",
                "uyo",
                "yenagoa",
            ],
            "northcentral": ["abuja", "jos", "makurdi", "minna", "lokoja", "lafia"],
            "northwest": ["kano", "kaduna", "zaria", "sokoto", "katsina"],
            "northeast": ["maiduguri", "yola", "bauchi", "gombe", "jalingo"],
        }

        # Find user's region
        user_region = None
        for region, cities in regional_clusters.items():
            if any(city in user_location for city in cities):
                user_region = region
                break

        if not user_region:
            return False

        # Find job's region
        job_region = None
        ai_city_lower = ai_city.lower()
        for region, cities in regional_clusters.items():
            if any(city in ai_city_lower for city in cities):
                job_region = region
                break

        # Only allow matches within the SAME region (strict proximity)
        return user_region == job_region and job_region is not None

    def _score_ai_job_titles_match(self, user_prefs: dict, job: dict) -> float:
        """Enhanced job title matching using AI job titles array"""
        user_roles = user_prefs.get("job_roles", [])
        if not user_roles:
            return 0.0

        # Get AI job titles array (15+ variations per job)
        ai_job_titles = job.get("ai_job_titles", []) or []
        job_title = job.get("title", "").lower()

        max_score = 0.0

        for user_role in user_roles:
            user_role_lower = user_role.lower()

            # Check exact matches in AI job titles array
            for ai_title in ai_job_titles:
                if ai_title and user_role_lower in ai_title.lower():
                    max_score = max(max_score, 35.0)  # Full points for AI match
                    break

            # Check fuzzy matches in AI job titles
            if max_score < 35.0:
                for ai_title in ai_job_titles:
                    if ai_title:
                        similarity = SequenceMatcher(
                            None, user_role_lower, ai_title.lower()
                        ).ratio()
                        if similarity > 0.8:
                            max_score = max(max_score, 30.0)
                        elif similarity > 0.6:
                            max_score = max(max_score, 20.0)

            # Fallback to original title
            if max_score < 20.0 and user_role_lower in job_title:
                max_score = max(max_score, 15.0)

        return max_score

    def _score_ai_job_function_match(self, user_prefs: dict, job: dict) -> float:
        """Match based on AI job function (Sales, Engineering, etc.)"""
        user_categories = user_prefs.get("job_categories", [])
        user_roles = user_prefs.get("job_roles", [])

        if not user_categories and not user_roles:
            return 0.0

        ai_job_function = job.get("ai_job_function", "") or ""
        if not ai_job_function:
            return 0.0

        # Handle case where ai_job_function might be a list
        if isinstance(ai_job_function, list):
            ai_job_function = ai_job_function[0] if ai_job_function else ""

        if not ai_job_function:
            return 0.0

        ai_function_lower = ai_job_function.lower()

        # Check user categories first (highest priority)
        for category in user_categories:
            if category and category.lower() in ai_function_lower:
                return 25.0

        # Enhanced direct matching for data roles (second priority - 25 points)
        if any(
            "data" in role.lower() or "analyst" in role.lower() for role in user_roles
        ):
            if any(
                keyword in ai_function_lower
                for keyword in ["data", "analytics", "analyst", "intelligence"]
            ):
                return 25.0  # Full points for direct data match

        # Check user roles for function keywords (third priority - 20 points)
        function_keywords = {
            "sales": ["sales", "business development", "account management"],
            "engineering": ["engineer", "developer", "technical", "software"],
            "marketing": ["marketing", "digital marketing", "content"],
            "customer service": ["customer", "support", "service"],
            "finance": ["finance", "accounting", "financial"],
            "hr": ["hr", "human resources", "recruitment"],
            "operations": ["operations", "logistics", "supply chain"],
        }

        for user_role in user_roles:
            user_role_lower = user_role.lower()
            for func, keywords in function_keywords.items():
                if any(keyword in user_role_lower for keyword in keywords):
                    if func in ai_function_lower:
                        return 20.0

        return 0.0

    def _score_ai_industry_match(self, user_prefs: dict, job: dict) -> float:
        """Match based on AI industry classification"""
        user_industries = user_prefs.get("industry_preferences", [])
        user_roles = user_prefs.get("job_roles", [])

        ai_industries = job.get("ai_industry", []) or []
        if not ai_industries:
            return 0.0

        # Direct industry preference match
        if user_industries:
            for user_industry in user_industries:
                for ai_industry in ai_industries:
                    if (
                        user_industry
                        and ai_industry
                        and user_industry.lower() in ai_industry.lower()
                    ):
                        return 20.0

        # Infer industry from user roles
        role_industry_map = {
            "tech": ["technology", "software", "information technology"],
            "finance": ["finance", "financial services", "banking"],
            "healthcare": ["healthcare", "medical", "pharmaceutical"],
            "education": ["education", "academic", "training"],
            "retail": ["retail", "e-commerce", "consumer goods"],
            "media": ["media", "entertainment", "advertising"],
        }

        for user_role in user_roles:
            user_role_lower = user_role.lower()
            for role_key, industries in role_industry_map.items():
                if role_key in user_role_lower:
                    for ai_industry in ai_industries:
                        if any(ind in ai_industry.lower() for ind in industries):
                            return 15.0

        return 0.0

    def _score_job_titles(self, user_prefs: Dict, job: Dict) -> float:
        """Score exact job title matches"""
        user_roles = user_prefs.get("job_roles", [])
        if not user_roles:
            return 0.0

        # Get job title fields
        job_title = (job.get("title", "") or "").lower()

        # Handle ai_job_title which might be a list
        ai_job_title_raw = job.get("ai_job_title", "") or ""
        if isinstance(ai_job_title_raw, list):
            ai_job_title = ai_job_title_raw[0].lower() if ai_job_title_raw else ""
        else:
            ai_job_title = ai_job_title_raw.lower()

        max_score = 0.0
        for user_role in user_roles:
            user_role_lower = user_role.lower()

            # Exact matches
            if user_role_lower in job_title or user_role_lower in ai_job_title:
                max_score = max(max_score, 40.0)
            # Partial matches
            elif any(word in job_title for word in user_role_lower.split()):
                max_score = max(max_score, 25.0)
            elif any(word in ai_job_title for word in user_role_lower.split()):
                max_score = max(max_score, 20.0)

        return max_score

    def _score_fuzzy_titles(self, user_prefs: Dict, job: Dict) -> float:
        """Score fuzzy job title matches using string similarity"""
        user_roles = user_prefs.get("job_roles", [])
        if not user_roles:
            return 0.0

        job_title = (job.get("title", "") or "").lower()

        # Handle ai_job_title which might be a list
        ai_job_title_raw = job.get("ai_job_title", "") or ""
        if isinstance(ai_job_title_raw, list):
            ai_job_title = ai_job_title_raw[0].lower() if ai_job_title_raw else ""
        else:
            ai_job_title = ai_job_title_raw.lower()

        max_score = 0.0
        for user_role in user_roles:
            user_role_lower = user_role.lower()

            # Calculate similarity ratios
            title_similarity = SequenceMatcher(None, user_role_lower, job_title).ratio()
            ai_title_similarity = SequenceMatcher(
                None, user_role_lower, ai_job_title
            ).ratio()

            # Convert similarity to score (threshold of 0.6 for relevance)
            best_similarity = max(title_similarity, ai_title_similarity)
            if best_similarity >= 0.6:
                fuzzy_score = (
                    (best_similarity - 0.6) / 0.4 * 30.0
                )  # Scale to 0-30 points
                max_score = max(max_score, fuzzy_score)

        return max_score

    def _score_semantic_clusters(self, user_prefs: Dict, job: Dict) -> float:
        """Score semantic cluster matches"""
        user_roles = user_prefs.get("job_roles", [])
        if not user_roles:
            return 0.0

        job_title = (job.get("title", "") or "").lower()

        # Handle ai_job_title which might be a list
        ai_job_title_raw = job.get("ai_job_title", "") or ""
        if isinstance(ai_job_title_raw, list):
            ai_job_title = ai_job_title_raw[0].lower() if ai_job_title_raw else ""
        else:
            ai_job_title = ai_job_title_raw.lower()

        job_description = (job.get("description", "") or "").lower()

        # Find user's clusters
        user_clusters = set()
        for user_role in user_roles:
            user_role_lower = user_role.lower()
            for cluster_name, cluster_terms in self.JOB_CLUSTERS.items():
                if any(term in user_role_lower for term in cluster_terms):
                    user_clusters.add(cluster_name)

        if not user_clusters:
            return 0.0

        # Check if job matches any user clusters
        max_score = 0.0
        for cluster_name in user_clusters:
            cluster_terms = self.JOB_CLUSTERS[cluster_name]

            # Check title matches
            title_matches = sum(
                1 for term in cluster_terms if term in job_title or term in ai_job_title
            )

            # Check description matches (lower weight)
            desc_matches = sum(1 for term in cluster_terms if term in job_description)

            if title_matches > 0:
                cluster_score = min(title_matches * 15.0, 25.0)  # Up to 25 points
                max_score = max(max_score, cluster_score)
            elif desc_matches > 0:
                cluster_score = min(desc_matches * 5.0, 15.0)  # Up to 15 points
                max_score = max(max_score, cluster_score)

        return max_score

    def _score_skills_match(self, user_prefs: Dict, job: Dict) -> float:
        """Enhanced AI-powered skills matching with required/preferred distinction"""
        user_technical_skills = user_prefs.get("technical_skills", []) or []
        user_soft_skills = user_prefs.get("soft_skills", []) or []

        if not user_technical_skills and not user_soft_skills:
            return 0.0

        # Get AI-enhanced skills data
        ai_required_skills = job.get("ai_required_skills", []) or []
        ai_preferred_skills = job.get("ai_preferred_skills", []) or []

        # Legacy fields for backward compatibility
        job_description = (job.get("description", "") or "").lower()
        ai_skills_raw = job.get("ai_skills_required", "") or ""
        if isinstance(ai_skills_raw, list):
            ai_skills_legacy = ai_skills_raw
        else:
            ai_skills_legacy = [ai_skills_raw] if ai_skills_raw else []

        total_score = 0.0

        # Score technical skills matching
        if user_technical_skills:
            tech_score = self._score_technical_skills_match(
                user_technical_skills,
                ai_required_skills,
                ai_preferred_skills,
                ai_skills_legacy,
                job_description,
            )
            total_score += tech_score

        # Score soft skills matching (lower weight)
        if user_soft_skills:
            soft_score = self._score_soft_skills_match(
                user_soft_skills, job_description
            )
            total_score += soft_score

        return min(total_score, 20.0)  # Cap at 20 points

    def _score_technical_skills_match(
        self,
        user_skills: list,
        ai_required: list,
        ai_preferred: list,
        ai_legacy: list,
        job_description: str,
    ) -> float:
        """Score technical skills with required/preferred distinction"""
        if not user_skills:
            return 0.0

        required_matches = 0
        preferred_matches = 0
        legacy_matches = 0
        description_matches = 0

        total_user_skills = len(user_skills)

        for user_skill in user_skills:
            user_skill_lower = user_skill.lower().strip()

            # Check required skills (highest priority)
            if self._skill_matches_list(user_skill_lower, ai_required):
                required_matches += 1
                continue

            # Check preferred skills
            if self._skill_matches_list(user_skill_lower, ai_preferred):
                preferred_matches += 1
                continue

            # Check legacy AI skills
            if self._skill_matches_list(user_skill_lower, ai_legacy):
                legacy_matches += 1
                continue

            # Check job description with synonyms
            if self._skill_matches_description(user_skill_lower, job_description):
                description_matches += 1

        # Calculate weighted score
        score = 0.0

        # Required skills: 3 points each (critical)
        if ai_required:
            required_ratio = required_matches / len(ai_required)
            score += required_ratio * 12.0  # Up to 12 points

        # Preferred skills: 1.5 points each (nice to have)
        if ai_preferred:
            preferred_ratio = preferred_matches / len(ai_preferred)
            score += preferred_ratio * 6.0  # Up to 6 points

        # Legacy and description matches: 1 point each
        if total_user_skills > 0:
            other_ratio = (legacy_matches + description_matches) / total_user_skills
            score += other_ratio * 4.0  # Up to 4 points

        return score

    def _score_soft_skills_match(
        self, user_soft_skills: list, job_description: str
    ) -> float:
        """Score soft skills matching (lower weight than technical)"""
        if not user_soft_skills:
            return 0.0

        soft_skill_keywords = {
            "communication": [
                "communication",
                "communicate",
                "verbal",
                "written",
                "presentation",
            ],
            "leadership": [
                "leadership",
                "lead",
                "manage",
                "mentor",
                "guide",
                "supervise",
            ],
            "teamwork": ["teamwork", "collaboration", "team player", "cooperative"],
            "problem solving": [
                "problem solving",
                "analytical",
                "critical thinking",
                "troubleshoot",
            ],
            "creativity": ["creative", "innovation", "design thinking", "artistic"],
            "adaptability": ["adaptable", "flexible", "agile", "change management"],
            "time management": [
                "time management",
                "organization",
                "prioritization",
                "deadline",
            ],
        }

        matched_soft_skills = 0

        for user_skill in user_soft_skills:
            user_skill_lower = user_skill.lower().strip()

            # Direct match
            if user_skill_lower in job_description:
                matched_soft_skills += 1
                continue

            # Keyword matching
            for skill_category, keywords in soft_skill_keywords.items():
                if user_skill_lower in keywords or any(
                    keyword in user_skill_lower for keyword in keywords
                ):
                    if any(keyword in job_description for keyword in keywords):
                        matched_soft_skills += 1
                        break

        if len(user_soft_skills) > 0:
            soft_ratio = matched_soft_skills / len(user_soft_skills)
            return soft_ratio * 3.0  # Up to 3 points for soft skills

        return 0.0

    def _skill_matches_list(self, user_skill: str, skill_list: list) -> bool:
        """Check if user skill matches any skill in the list with synonyms"""
        if not skill_list:
            return False

        for job_skill in skill_list:
            job_skill_lower = job_skill.lower().strip()

            # Direct match
            if user_skill == job_skill_lower or user_skill in job_skill_lower:
                return True

            # Synonym matching
            if self._are_skills_synonymous(user_skill, job_skill_lower):
                return True

        return False

    def _skill_matches_description(self, user_skill: str, job_description: str) -> bool:
        """Check if user skill matches job description with synonyms"""
        # Direct match
        if user_skill in job_description:
            return True

        # Synonym matching with existing SKILL_SYNONYMS
        for skill_group, synonyms in self.SKILL_SYNONYMS.items():
            if user_skill in synonyms:
                if any(syn in job_description for syn in synonyms):
                    return True

        return False

    def _are_skills_synonymous(self, skill1: str, skill2: str) -> bool:
        """Check if two skills are synonymous"""
        # Enhanced skill synonyms for better matching
        enhanced_synonyms = {
            "javascript": ["js", "javascript", "ecmascript", "node.js", "nodejs"],
            "python": ["python", "py", "python3", "django", "flask"],
            "react": ["react", "reactjs", "react.js", "react native"],
            "angular": ["angular", "angularjs", "angular.js"],
            "vue": ["vue", "vuejs", "vue.js"],
            "css": ["css", "css3", "stylesheets", "styling"],
            "html": ["html", "html5", "markup"],
            "sql": ["sql", "mysql", "postgresql", "database"],
            "aws": ["aws", "amazon web services", "cloud"],
            "docker": ["docker", "containerization", "containers"],
            "kubernetes": ["kubernetes", "k8s", "orchestration"],
            "git": ["git", "version control", "github", "gitlab"],
        }

        # Check if skills are in the same synonym group
        for synonyms in enhanced_synonyms.values():
            if skill1 in synonyms and skill2 in synonyms:
                return True

        # Check existing SKILL_SYNONYMS
        for synonyms in self.SKILL_SYNONYMS.values():
            if skill1 in synonyms and skill2 in synonyms:
                return True

        return False

    def _score_work_arrangement(self, user_prefs: Dict, job: Dict) -> float:
        """Enhanced AI-powered work arrangement matching"""
        user_arrangements = user_prefs.get("work_arrangements", []) or []
        if not user_arrangements:
            return 0.0

        # Get AI-enhanced work arrangement data
        ai_work_arrangement = (job.get("ai_work_arrangement", "") or "").lower()
        ai_remote_allowed = job.get("ai_remote_allowed", False)

        # Legacy fields for backward compatibility
        job_title = (job.get("title", "") or "").lower()
        job_description = (job.get("description", "") or "").lower()
        location = (job.get("location", "") or "").lower()
        is_remote = job.get("is_remote", False)

        max_score = 0.0

        for arrangement in user_arrangements:
            arrangement_lower = arrangement.lower()

            if arrangement_lower == "remote":
                score = self._score_remote_arrangement(
                    ai_work_arrangement,
                    ai_remote_allowed,
                    is_remote,
                    job_title,
                    job_description,
                    location,
                )
                max_score = max(max_score, score)

            elif arrangement_lower == "hybrid":
                score = self._score_hybrid_arrangement(
                    ai_work_arrangement, job_title, job_description, location
                )
                max_score = max(max_score, score)

            elif arrangement_lower in ["on-site", "onsite", "office"]:
                score = self._score_onsite_arrangement(
                    ai_work_arrangement,
                    ai_remote_allowed,
                    is_remote,
                    job_title,
                    job_description,
                    location,
                )
                max_score = max(max_score, score)

        return max_score

    def _score_remote_arrangement(
        self,
        ai_work_arrangement: str,
        ai_remote_allowed: bool,
        is_remote: bool,
        job_title: str,
        job_description: str,
        location: str,
    ) -> float:
        """Score remote work arrangement matching"""
        # Perfect AI match
        if "remote" in ai_work_arrangement:
            return 15.0

        # AI explicitly allows remote
        if ai_remote_allowed:
            return 15.0

        # Legacy remote indicators
        if is_remote:
            return 14.0

        # Text-based remote indicators (weighted by reliability)
        remote_indicators = {
            "100% remote": 13.0,
            "fully remote": 13.0,
            "work from home": 12.0,
            "remote work": 12.0,
            "remote position": 12.0,
            "remote job": 12.0,
            "work remotely": 11.0,
            "remote": 10.0,
        }

        all_text = f"{job_title} {job_description} {location}"
        for indicator, score in remote_indicators.items():
            if indicator in all_text:
                return score

        return 0.0

    def _score_hybrid_arrangement(
        self,
        ai_work_arrangement: str,
        job_title: str,
        job_description: str,
        location: str,
    ) -> float:
        """Score hybrid work arrangement matching"""
        # Perfect AI match
        if "hybrid" in ai_work_arrangement:
            return 15.0

        # Text-based hybrid indicators
        hybrid_indicators = {
            "hybrid work": 14.0,
            "hybrid model": 14.0,
            "hybrid arrangement": 14.0,
            "flexible work": 13.0,
            "work from home some days": 13.0,
            "part remote": 12.0,
            "flexible schedule": 11.0,
            "hybrid": 10.0,
            "flexible": 8.0,
        }

        all_text = f"{job_title} {job_description} {location}"
        for indicator, score in hybrid_indicators.items():
            if indicator in all_text:
                return score

        return 0.0

    def _score_onsite_arrangement(
        self,
        ai_work_arrangement: str,
        ai_remote_allowed: bool,
        is_remote: bool,
        job_title: str,
        job_description: str,
        location: str,
    ) -> float:
        """Score on-site work arrangement matching"""
        # Perfect AI match
        if "on-site" in ai_work_arrangement or "onsite" in ai_work_arrangement:
            return 15.0

        # Explicit on-site indicators
        onsite_indicators = [
            "on-site",
            "onsite",
            "office based",
            "in-office",
            "office work",
            "office environment",
            "physical presence required",
        ]

        all_text = f"{job_title} {job_description} {location}"
        for indicator in onsite_indicators:
            if indicator in all_text:
                return 13.0

        # Default assumption: if no remote indicators, likely on-site
        if not (
            ai_remote_allowed
            or is_remote
            or "remote" in all_text
            or "hybrid" in all_text
        ):
            return 10.0  # Lower score as on-site is often default

        return 0.0

    def _score_salary_match(self, user_prefs: Dict, job: Dict) -> float:
        """Enhanced intelligent salary matching with currency conversion"""
        user_currency = user_prefs.get("salary_currency")
        user_min = user_prefs.get("salary_min")
        user_max = user_prefs.get("salary_max")
        salary_negotiable = user_prefs.get("salary_negotiable", True)

        if not any([user_currency, user_min, user_max]):
            return 0.0

        # Get job salary data (prefer AI-enhanced fields)
        job_currency = job.get("ai_salary_currency") or job.get("salary_currency")
        job_min = job.get("ai_salary_min") or job.get("salary_min")
        job_max = job.get("ai_salary_max") or job.get("salary_max")

        # Convert to numbers if they're strings
        try:
            if job_min and isinstance(job_min, str):
                job_min = float(job_min.replace(",", ""))
            if job_max and isinstance(job_max, str):
                job_max = float(job_max.replace(",", ""))
            if user_min and isinstance(user_min, str):
                user_min = float(str(user_min).replace(",", ""))
            if user_max and isinstance(user_max, str):
                user_max = float(str(user_max).replace(",", ""))
        except (ValueError, AttributeError):
            pass

        score = 0.0

        # Currency matching with intelligent conversion
        if user_currency and job_currency:
            currency_score = self._score_currency_match(user_currency, job_currency)
            score += currency_score

            # Apply currency conversion if needed
            if currency_score > 0 and currency_score < 4.0:  # Partial currency match
                conversion_factor = self._get_currency_conversion_factor(
                    job_currency, user_currency
                )
                if conversion_factor and job_min:
                    job_min = job_min * conversion_factor
                if conversion_factor and job_max:
                    job_max = job_max * conversion_factor

        # Salary range matching with flexibility
        if user_min or user_max:
            range_score = self._score_salary_range_match(
                user_min, user_max, job_min, job_max, salary_negotiable
            )
            score += range_score

        return min(score, 12.0)  # Cap at 12 points

    def _score_currency_match(self, user_currency: str, job_currency: str) -> float:
        """Score currency matching with intelligent equivalents"""
        if not user_currency or not job_currency:
            return 0.0

        user_curr = user_currency.upper().strip()
        job_curr = job_currency.upper().strip()

        # Perfect match
        if user_curr == job_curr:
            return 4.0

        # Currency equivalents and common variations
        currency_groups = {
            "NGN": ["NGN", "NAIRA", "₦", "NIGERIAN NAIRA"],
            "USD": ["USD", "DOLLAR", "$", "US DOLLAR", "AMERICAN DOLLAR"],
            "EUR": ["EUR", "EURO", "€", "EUROPEAN EURO"],
            "GBP": ["GBP", "POUND", "£", "BRITISH POUND", "STERLING"],
            "CAD": ["CAD", "CANADIAN DOLLAR", "C$"],
            "AUD": ["AUD", "AUSTRALIAN DOLLAR", "A$"],
        }

        user_group = None
        job_group = None

        for currency, variations in currency_groups.items():
            if user_curr in variations:
                user_group = currency
            if job_curr in variations:
                job_group = currency

        if user_group and job_group:
            if user_group == job_group:
                return 4.0

            # Related currencies (easier conversion)
            related_pairs = [
                ("USD", "CAD"),
                ("USD", "AUD"),
                ("GBP", "EUR"),
                ("NGN", "USD"),
                ("NGN", "GBP"),
                ("NGN", "EUR"),
            ]

            for curr1, curr2 in related_pairs:
                if (user_group == curr1 and job_group == curr2) or (
                    user_group == curr2 and job_group == curr1
                ):
                    return 2.0

        return 0.0

    def _get_currency_conversion_factor(
        self, from_currency: str, to_currency: str
    ) -> float:
        """Get approximate currency conversion factor (simplified)"""
        # Simplified conversion rates (should be updated with real-time rates in production)
        conversion_rates = {
            ("USD", "NGN"): 750.0,
            ("EUR", "NGN"): 820.0,
            ("GBP", "NGN"): 950.0,
            ("USD", "EUR"): 0.92,
            ("USD", "GBP"): 0.79,
            ("EUR", "GBP"): 0.86,
        }

        from_curr = from_currency.upper().strip()
        to_curr = to_currency.upper().strip()

        # Direct conversion
        if (from_curr, to_curr) in conversion_rates:
            return conversion_rates[(from_curr, to_curr)]

        # Reverse conversion
        if (to_curr, from_curr) in conversion_rates:
            return 1.0 / conversion_rates[(to_curr, from_curr)]

        return None

    def _score_salary_range_match(
        self,
        user_min: float,
        user_max: float,
        job_min: float,
        job_max: float,
        salary_negotiable: bool,
    ) -> float:
        """Score salary range matching with flexibility"""
        if not any([user_min, user_max, job_min, job_max]):
            return 0.0

        score = 0.0

        # Perfect range overlap
        if user_min and user_max and job_min and job_max:
            if user_min <= job_max and user_max >= job_min:
                overlap_ratio = self._calculate_range_overlap(
                    user_min, user_max, job_min, job_max
                )
                score += overlap_ratio * 6.0  # Up to 6 points for perfect overlap

        # Minimum salary requirements
        if user_min and job_max:
            if job_max >= user_min:
                score += 3.0
            elif salary_negotiable and job_max >= (
                user_min * 0.8
            ):  # 20% flexibility if negotiable
                score += 2.0

        # Maximum budget constraints
        if user_max and job_min:
            if job_min <= user_max:
                score += 2.0
            elif salary_negotiable and job_min <= (
                user_max * 1.2
            ):  # 20% flexibility if negotiable
                score += 1.0

        # Single-sided matches
        if user_min and job_min and not (user_max and job_max):
            if abs(user_min - job_min) / max(user_min, job_min) <= 0.2:  # Within 20%
                score += 2.0

        if user_max and job_max and not (user_min and job_min):
            if abs(user_max - job_max) / max(user_max, job_max) <= 0.2:  # Within 20%
                score += 2.0

        return score

    def _calculate_range_overlap(
        self, user_min: float, user_max: float, job_min: float, job_max: float
    ) -> float:
        """Calculate the overlap ratio between two salary ranges"""
        overlap_start = max(user_min, job_min)
        overlap_end = min(user_max, job_max)

        if overlap_start >= overlap_end:
            return 0.0

        overlap_size = overlap_end - overlap_start
        user_range_size = user_max - user_min
        job_range_size = job_max - job_min

        # Calculate overlap as percentage of the smaller range
        smaller_range = min(user_range_size, job_range_size)
        if smaller_range <= 0:
            return 0.0

        return min(overlap_size / smaller_range, 1.0)

    def _score_contact_availability(self, job: Dict) -> float:
        """Score jobs based on availability of contact information for CTA buttons"""
        score = 0.0

        # Check for job URL (highest priority for apply buttons)
        job_url = job.get("job_url")
        if job_url and job_url.strip():
            score += 6.0  # 6 points for job URL

        # Check for email contact
        email = job.get("email") or job.get("ai_email")
        if email and email.strip():
            score += 3.0  # 3 points for email

        # Check for WhatsApp contact (highest value for user engagement)
        whatsapp = job.get("whatsapp_number") or job.get("ai_whatsapp_number")
        if whatsapp and whatsapp.strip():
            score += 4.0  # 4 points for WhatsApp

        # Bonus for multiple contact methods
        contact_methods = sum(
            [
                1 if job_url and job_url.strip() else 0,
                1 if email and email.strip() else 0,
                1 if whatsapp and whatsapp.strip() else 0,
            ]
        )

        if contact_methods >= 2:
            score += 2.0  # 2 bonus points for multiple contact methods

        return min(score, 10.0)  # Cap at 10 points

    def _score_experience_match(self, user_prefs: Dict, job: Dict) -> float:
        """Enhanced AI-powered experience level matching"""
        user_exp_level = user_prefs.get("experience_level")
        user_years = user_prefs.get("years_of_experience")

        if not user_exp_level and not user_years:
            return 0.0

        # Get AI-enhanced experience data
        ai_job_level = job.get("ai_job_level", []) or []
        ai_years_min = job.get("ai_years_experience_min")
        ai_years_max = job.get("ai_years_experience_max")

        # Legacy fields
        job_description = (job.get("description", "") or "").lower()
        ai_exp_raw = job.get("ai_experience_required", "") or ""
        if isinstance(ai_exp_raw, list):
            ai_exp_required = " ".join(ai_exp_raw).lower() if ai_exp_raw else ""
        else:
            ai_exp_required = ai_exp_raw.lower()

        max_score = 0.0

        # Experience level matching with AI enhancement
        if user_exp_level:
            level_score = self._score_experience_level_match(
                user_exp_level, ai_job_level, job_description, ai_exp_required
            )
            max_score = max(max_score, level_score)

        # Years of experience matching with AI enhancement
        if user_years:
            years_score = self._score_years_experience_match(
                user_years, ai_years_min, ai_years_max, job_description, ai_exp_required
            )
            max_score = max(max_score, years_score)

        return max_score

    def _score_experience_level_match(
        self,
        user_level: str,
        ai_job_level: list,
        job_description: str,
        ai_exp_required: str,
    ) -> float:
        """Score experience level matching with intelligent mapping"""
        if not user_level:
            return 0.0

        user_level_lower = user_level.lower().strip()

        # Experience level hierarchy and mappings
        level_mappings = {
            "entry": [
                "entry",
                "junior",
                "graduate",
                "trainee",
                "intern",
                "beginner",
                "fresh",
            ],
            "junior": ["junior", "entry", "associate", "level 1", "i", "1"],
            "mid": [
                "mid",
                "intermediate",
                "senior",
                "level 2",
                "ii",
                "2",
                "experienced",
            ],
            "senior": ["senior", "lead", "principal", "level 3", "iii", "3", "expert"],
            "lead": ["lead", "senior", "principal", "manager", "head", "chief"],
            "principal": ["principal", "staff", "architect", "expert", "specialist"],
            "executive": ["executive", "director", "vp", "vice president", "c-level"],
        }

        # Find user's level category
        user_category = None
        for category, variations in level_mappings.items():
            if user_level_lower in variations:
                user_category = category
                break

        if not user_category:
            user_category = user_level_lower

        # Check AI job levels first (highest priority)
        if ai_job_level:
            for job_level in ai_job_level:
                job_level_lower = job_level.lower().strip()

                # Direct match
                if user_level_lower == job_level_lower:
                    return 10.0

                # Category match
                job_category = None
                for category, variations in level_mappings.items():
                    if job_level_lower in variations:
                        job_category = category
                        break

                if job_category and user_category:
                    compatibility_score = self._calculate_level_compatibility(
                        user_category, job_category
                    )
                    if compatibility_score > 0:
                        return compatibility_score

        # Fallback to text-based matching
        all_text = f"{job_description} {ai_exp_required}"

        # Direct text matches
        if user_level_lower in all_text:
            return 8.0

        # Category-based text matching
        if user_category in level_mappings:
            for variation in level_mappings[user_category]:
                if variation in all_text:
                    return 6.0

        return 0.0

    def _calculate_level_compatibility(self, user_level: str, job_level: str) -> float:
        """Calculate compatibility score between experience levels"""
        # Experience level progression
        level_hierarchy = [
            "entry",
            "junior",
            "mid",
            "senior",
            "lead",
            "principal",
            "executive",
        ]

        try:
            user_index = level_hierarchy.index(user_level)
            job_index = level_hierarchy.index(job_level)
        except ValueError:
            return 0.0

        # Perfect match
        if user_index == job_index:
            return 10.0

        # Adjacent levels (good compatibility)
        if abs(user_index - job_index) == 1:
            return 8.0

        # Two levels apart (acceptable)
        if abs(user_index - job_index) == 2:
            return 5.0

        # User is overqualified (still acceptable for some roles)
        if user_index > job_index and (user_index - job_index) <= 3:
            return 3.0

        # User is underqualified (less desirable)
        if job_index > user_index and (job_index - user_index) <= 2:
            return 2.0

        return 0.0

    def _score_years_experience_match(
        self,
        user_years: int,
        ai_years_min: int,
        ai_years_max: int,
        job_description: str,
        ai_exp_required: str,
    ) -> float:
        """Score years of experience matching with flexibility"""
        if not user_years:
            return 0.0

        score = 0.0

        # AI-enhanced years matching (highest priority)
        if ai_years_min is not None or ai_years_max is not None:
            if ai_years_min is not None and ai_years_max is not None:
                # Range specified
                if ai_years_min <= user_years <= ai_years_max:
                    return 10.0
                elif user_years >= ai_years_min:
                    # Overqualified but acceptable
                    excess_years = user_years - ai_years_max
                    if excess_years <= 2:
                        return 8.0
                    elif excess_years <= 5:
                        return 6.0
                    else:
                        return 4.0
                elif user_years >= (ai_years_min * 0.8):
                    # Slightly underqualified but close
                    return 5.0
            elif ai_years_min is not None:
                # Only minimum specified
                if user_years >= ai_years_min:
                    return 9.0
                elif user_years >= (ai_years_min * 0.8):
                    return 6.0
            elif ai_years_max is not None:
                # Only maximum specified (rare case)
                if user_years <= ai_years_max:
                    return 8.0

        # Fallback to text-based years extraction
        import re

        all_text = f"{job_description} {ai_exp_required}"

        # Look for year patterns
        year_patterns = re.findall(r"(\d+)\+?\s*(?:years?|yrs?)", all_text)
        if year_patterns:
            required_years = []
            for pattern in year_patterns:
                try:
                    required_years.append(int(pattern))
                except ValueError:
                    continue

            if required_years:
                min_required = min(required_years)
                max_required = max(required_years) if len(required_years) > 1 else None

                if user_years >= min_required:
                    if max_required and user_years <= max_required:
                        return 7.0  # Within range
                    else:
                        return 6.0  # Meets minimum
                elif user_years >= (min_required * 0.8):
                    return 4.0  # Close to minimum

        return score

    def _get_match_reasons(self, user_prefs: Dict, job: Dict) -> List[str]:
        """Get human-readable reasons for the match"""
        reasons = []

        # Job title matches
        user_roles = user_prefs.get("job_roles", [])
        job_title = (job.get("title", "") or "").lower()
        for role in user_roles:
            if role.lower() in job_title:
                reasons.append(f"Job title matches '{role}'")

        # Skills matches
        user_skills = user_prefs.get("technical_skills", []) or []
        job_description = (job.get("description", "") or "").lower()
        for skill in user_skills:
            if skill and skill.lower() in job_description:
                reasons.append(f"Requires '{skill}' skill")

        # Work arrangement matches
        user_arrangements = user_prefs.get("work_arrangements", []) or []
        if "remote" in user_arrangements:
            if job.get("ai_remote_allowed") or "remote" in job_title:
                reasons.append("Remote work available")

        # Location matches - DISABLED
        # user_locations = user_prefs.get("preferred_locations", []) or []
        # job_location = (job.get("location", "") or "").lower()
        # for location in user_locations:
        #     if location.lower() in job_location:
        #         reasons.append(f"Located in {location}")

        return reasons[:3]  # Limit to top 3 reasons

    def format_job_for_whatsapp(self, job: Dict, index: int) -> str:
        """Format job for WhatsApp with intelligent match information"""
        try:
            # Extract key information
            title = job.get("title", "Job Opportunity")
            company = job.get("company", "Company")
            location = job.get("location", "Location not specified")

            # Match information
            match_score = job.get("match_score", 0)
            match_reasons = job.get("match_reasons", [])

            # Build message
            message = f"""*{index}. {title}*
🏢 {company}
📍 {location}"""

            # Add match score and reasons
            if match_score > 0:
                message += f"\n⭐ {match_score:.0f}% match"
                if match_reasons:
                    message += f"\n🎯 {', '.join(match_reasons)}"

            # Add application link
            if job.get("job_url"):
                message += f"\n🔗 Apply: {job['job_url']}"
            elif job.get("ai_application_url"):
                message += f"\n🔗 Apply: {job['ai_application_url']}"

            return message

        except Exception as e:
            logger.error(f"❌ Error formatting job: {e}")
            return f"{index}. Job opportunity available (formatting error)"
