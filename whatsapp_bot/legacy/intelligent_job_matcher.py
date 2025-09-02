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

    def search_jobs_for_user(self, user_id: int, limit: int = 10) -> List[Dict]:
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
                    id, title, company, location, description, job_url,
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
                    scraped_at DESC NULLS FIRST,  -- Sort by scraped_at (more reliable than posted_date)
                    id DESC  -- Add deterministic secondary sort
                LIMIT 900  -- Balanced limit for performance vs coverage
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
        """Calculate AI-enhanced job match score using multiple strategies"""

        # LOCATION FILTERING DISABLED - Allow all jobs regardless of location
        # We'll handle location preferences in the UI/scoring instead of hard filtering
        # if not self._is_location_compatible(user_prefs, job):
        #     return 0.0  # Disqualify jobs with incompatible locations

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

        # 5. SKILLS MATCHING (15 points) - Keep existing logic
        skills_score = self._score_skills_match(user_prefs, job)
        total_score += skills_score * 0.75  # Reduce from 20 to 15 points

        # 6. WORK ARRANGEMENT MATCHING (10 points) - DISABLED (uses location)
        # work_score = self._score_work_arrangement(user_prefs, job)
        # total_score += work_score * 0.67  # Reduce from 15 to 10 points

        # 7. LOCATION MATCHING (10 points) - DISABLED FOR NOW
        # location_score = self._score_location_match(user_prefs, job)
        # total_score += location_score

        # 8. SALARY MATCHING (5 points) - Reduced weight
        salary_score = self._score_salary_match(user_prefs, job)
        total_score += salary_score * 0.5  # Reduce from 10 to 5 points

        # 9. EXPERIENCE LEVEL MATCHING (5 points) - Keep existing
        exp_score = self._score_experience_match(user_prefs, job)
        total_score += exp_score

        # 10. CONTACT INFORMATION BONUS (10 points) - NEW: Prioritize jobs with contact info
        contact_score = self._score_contact_availability(job)
        total_score += contact_score

        return min(total_score, 100.0)  # Cap at 100%

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
        """Score skills matching with synonyms"""
        user_skills = user_prefs.get("technical_skills", []) or []
        if not user_skills:
            return 0.0

        # Get job skills from various fields
        job_description = (job.get("description", "") or "").lower()

        # Handle ai_skills_required which might be a list
        ai_skills_raw = job.get("ai_skills_required", "") or ""
        if isinstance(ai_skills_raw, list):
            ai_skills = " ".join(ai_skills_raw).lower() if ai_skills_raw else ""
        else:
            ai_skills = ai_skills_raw.lower()

        matched_skills = 0
        total_user_skills = len(user_skills)

        for user_skill in user_skills:
            user_skill_lower = user_skill.lower()

            # Check direct matches
            if user_skill_lower in job_description or user_skill_lower in ai_skills:
                matched_skills += 1
                continue

            # Check synonym matches
            for skill_group, synonyms in self.SKILL_SYNONYMS.items():
                if user_skill_lower in synonyms:
                    if any(
                        syn in job_description or syn in ai_skills for syn in synonyms
                    ):
                        matched_skills += 1
                        break

        if total_user_skills > 0:
            skill_ratio = matched_skills / total_user_skills
            return skill_ratio * 20.0  # Up to 20 points

        return 0.0

    def _score_work_arrangement(self, user_prefs: Dict, job: Dict) -> float:
        """Score work arrangement matching"""
        user_arrangements = user_prefs.get("work_arrangements", []) or []
        if not user_arrangements:
            return 0.0

        # Check job work arrangement indicators
        job_title = (job.get("title", "") or "").lower()
        job_description = (job.get("description", "") or "").lower()
        location = (job.get("location", "") or "").lower()
        ai_remote = job.get("ai_remote_allowed", False)
        is_remote = job.get("is_remote", False)

        for arrangement in user_arrangements:
            if arrangement == "remote":
                if (
                    ai_remote
                    or is_remote
                    or "remote" in job_title
                    or "remote" in job_description
                    or "remote" in location
                ):
                    return 15.0
            elif arrangement == "hybrid":
                if (
                    "hybrid" in job_title
                    or "hybrid" in job_description
                    or "flexible" in job_description
                ):
                    return 15.0
            elif arrangement == "on-site":
                if not (ai_remote or is_remote or "remote" in location):
                    return 10.0  # Lower score as on-site is default

        return 0.0

    def _score_location_match(self, user_prefs: Dict, job: Dict) -> float:
        """Score location matching"""
        user_locations = user_prefs.get("preferred_locations", []) or []
        willing_to_relocate = user_prefs.get("willing_to_relocate", False)

        if not user_locations:
            return 0.0

        job_location = (job.get("location", "") or "").lower()

        # Exact location matches
        for user_location in user_locations:
            user_loc_lower = user_location.lower()
            if user_loc_lower in job_location:
                return 10.0

        # If willing to relocate, give partial score for any location
        if willing_to_relocate and job_location:
            return 5.0

        return 0.0

    def _score_salary_match(self, user_prefs: Dict, job: Dict) -> float:
        """Score salary matching"""
        user_currency = user_prefs.get("salary_currency")
        user_min = user_prefs.get("salary_min")
        user_max = user_prefs.get("salary_max")

        if not any([user_currency, user_min, user_max]):
            return 0.0

        job_currency = job.get("salary_currency") or job.get("ai_salary_currency")
        job_min = job.get("salary_min") or job.get("ai_salary_min")
        job_max = job.get("salary_max") or job.get("ai_salary_max")

        score = 0.0

        # Currency match
        if user_currency and job_currency and user_currency == job_currency:
            score += 5.0

        # Salary range overlap
        if user_min and job_max and user_min <= job_max:
            score += 3.0
        if user_max and job_min and user_max >= job_min:
            score += 2.0

        return score

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
        """Score experience level matching"""
        user_exp_level = user_prefs.get("experience_level")
        user_years = user_prefs.get("years_of_experience")

        if not user_exp_level and not user_years:
            return 0.0

        job_description = (job.get("description", "") or "").lower()

        # Handle ai_experience_required which might be a list
        ai_exp_raw = job.get("ai_experience_required", "") or ""
        if isinstance(ai_exp_raw, list):
            ai_exp_required = " ".join(ai_exp_raw).lower() if ai_exp_raw else ""
        else:
            ai_exp_required = ai_exp_raw.lower()

        # Simple experience level matching
        if user_exp_level:
            if user_exp_level in job_description or user_exp_level in ai_exp_required:
                return 5.0

        # Years of experience matching (basic)
        if user_years:
            # Look for year patterns in job description
            import re

            year_patterns = re.findall(
                r"(\d+)\+?\s*years?", job_description + " " + ai_exp_required
            )
            if year_patterns:
                required_years = min(int(y) for y in year_patterns)
                if user_years >= required_years:
                    return 3.0

        return 0.0

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
