#!/usr/bin/env python3
"""
Embedding Service - Handles all embedding generation and caching
"""

import openai
import numpy as np
import hashlib
import json
import logging
from typing import List, Dict, Optional, Tuple
import psycopg2.extras
from utils.logger import setup_logger

logger = setup_logger(__name__)


class EmbeddingService:
    def __init__(self, openai_api_key: str, db_connection):
        self.openai_client = openai.OpenAI(api_key=openai_api_key)
        self.connection = db_connection
        self.embedding_cache = {}
        self.batch_queue = []
        self.batch_size = 20  # Process 20 embeddings at once

    def get_embedding(self, text: str, use_cache: bool = True) -> np.ndarray:
        """Get embedding for text with caching"""
        if not text or not text.strip():
            return np.zeros(1536)

        # Create cache key
        cache_key = hashlib.md5(text.encode()).hexdigest()

        # Check cache
        if use_cache and cache_key in self.embedding_cache:
            return self.embedding_cache[cache_key]

        try:
            response = self.openai_client.embeddings.create(
                model="text-embedding-3-small", input=text
            )

            embedding = np.array(response.data[0].embedding)

            # Cache result
            if use_cache:
                self.embedding_cache[cache_key] = embedding

            return embedding

        except Exception as e:
            logger.error(f"Error generating embedding: {e}")
            return np.zeros(1536)

    def get_embeddings_batch(self, texts: List[str]) -> List[np.ndarray]:
        """Get embeddings for multiple texts in batch (faster)"""
        if not texts:
            return []

        try:
            response = self.openai_client.embeddings.create(
                model="text-embedding-3-small", input=texts
            )

            embeddings = []
            for data in response.data:
                embeddings.append(np.array(data.embedding))

            return embeddings

        except Exception as e:
            logger.error(f"Error generating batch embeddings: {e}")
            return [np.zeros(1536) for _ in texts]

    def create_user_profile_text(self, prefs: dict) -> str:
        """Create comprehensive user profile text for embedding"""

        profile_parts = []

        # Job identity
        job_roles = prefs.get("job_roles", []) or []
        job_categories = prefs.get("job_categories", []) or []
        user_job_input = prefs.get("user_job_input", "") or ""

        if job_roles:
            profile_parts.append(f"Seeking roles: {', '.join(job_roles)}")
        if job_categories:
            profile_parts.append(f"Job categories: {', '.join(job_categories)}")
        if user_job_input:
            profile_parts.append(f"Job interests: {user_job_input}")

        # Experience profile
        experience_level = prefs.get("experience_level", "") or ""
        years_of_experience = prefs.get("years_of_experience", 0) or 0

        if experience_level:
            profile_parts.append(f"Experience level: {experience_level}")
        if years_of_experience:
            profile_parts.append(f"Years of experience: {years_of_experience}")

        # Skills profile
        technical_skills = prefs.get("technical_skills", []) or []
        soft_skills = prefs.get("soft_skills", []) or []

        if technical_skills:
            profile_parts.append(f"Technical skills: {', '.join(technical_skills)}")
        if soft_skills:
            profile_parts.append(f"Soft skills: {', '.join(soft_skills)}")

        # Location profile
        preferred_locations = prefs.get("preferred_locations", []) or []
        user_location_input = prefs.get("user_location_input", "") or ""
        willing_to_relocate = prefs.get("willing_to_relocate", False)

        if preferred_locations:
            profile_parts.append(
                f"Preferred locations: {', '.join(preferred_locations)}"
            )
        if user_location_input:
            profile_parts.append(f"Location preferences: {user_location_input}")
        if willing_to_relocate:
            profile_parts.append("Open to relocation")

        # Work preferences
        work_arrangements = prefs.get("work_arrangements", []) or []
        employment_types = prefs.get("employment_types", []) or []

        if work_arrangements:
            profile_parts.append(f"Work arrangements: {', '.join(work_arrangements)}")
        if employment_types:
            profile_parts.append(f"Employment types: {', '.join(employment_types)}")

        # Compensation
        salary_min = prefs.get("salary_min", 0) or 0
        salary_max = prefs.get("salary_max", 0) or 0
        salary_currency = prefs.get("salary_currency", "NGN") or "NGN"

        if salary_min and salary_max:
            profile_parts.append(
                f"Salary expectation: {salary_currency} {salary_min:,} - {salary_max:,}"
            )
        elif salary_min:
            profile_parts.append(f"Minimum salary: {salary_currency} {salary_min:,}")

        # Company preferences
        company_size_preference = prefs.get("company_size_preference", []) or []
        industry_preferences = prefs.get("industry_preferences", []) or []

        if company_size_preference:
            profile_parts.append(
                f"Company size preference: {', '.join(company_size_preference)}"
            )
        if industry_preferences:
            profile_parts.append(
                f"Industry interests: {', '.join(industry_preferences)}"
            )

        return ". ".join(profile_parts) if profile_parts else "Job seeker"

    def create_job_profile_text(self, job: dict) -> str:
        """Create comprehensive job profile text for embedding"""

        profile_parts = []

        # Basic job info
        title = job.get("title", "") or ""
        company = job.get("company", "") or ""

        if title:
            profile_parts.append(f"Job title: {title}")
        if company:
            profile_parts.append(f"Company: {company}")

        # AI enhanced job info
        ai_job_titles = job.get("ai_job_titles", []) or []
        ai_job_function = job.get("ai_job_function", "") or ""
        ai_job_level = job.get("ai_job_level", []) or []

        if ai_job_titles:
            profile_parts.append(f"Job variations: {', '.join(ai_job_titles)}")
        if ai_job_function:
            profile_parts.append(f"Job function: {ai_job_function}")
        if ai_job_level:
            profile_parts.append(f"Job level: {', '.join(ai_job_level)}")

        # Industry and location
        ai_industry = job.get("ai_industry", []) or []
        ai_city = job.get("ai_city", "") or ""
        ai_state = job.get("ai_state", "") or ""
        ai_country = job.get("ai_country", "") or ""
        location = job.get("location", "") or ""

        if ai_industry:
            profile_parts.append(f"Industry: {', '.join(ai_industry)}")
        if ai_city and ai_state:
            profile_parts.append(f"Location: {ai_city}, {ai_state}")
        elif location:
            profile_parts.append(f"Location: {location}")
        if ai_country:
            profile_parts.append(f"Country: {ai_country}")

        # Work arrangement
        ai_work_arrangement = job.get("ai_work_arrangement", "") or ""
        ai_remote_allowed = job.get("ai_remote_allowed", False)

        if ai_work_arrangement:
            profile_parts.append(f"Work arrangement: {ai_work_arrangement}")
        if ai_remote_allowed:
            profile_parts.append("Remote work allowed")

        # Skills and experience
        ai_required_skills = job.get("ai_required_skills", []) or []
        ai_preferred_skills = job.get("ai_preferred_skills", []) or []
        ai_years_experience_min = job.get("ai_years_experience_min", 0) or 0
        ai_years_experience_max = job.get("ai_years_experience_max", 0) or 0

        if ai_required_skills:
            profile_parts.append(f"Required skills: {', '.join(ai_required_skills)}")
        if ai_preferred_skills:
            profile_parts.append(f"Preferred skills: {', '.join(ai_preferred_skills)}")
        if ai_years_experience_min and ai_years_experience_max:
            profile_parts.append(
                f"Experience required: {ai_years_experience_min}-{ai_years_experience_max} years"
            )
        elif ai_years_experience_min:
            profile_parts.append(f"Minimum experience: {ai_years_experience_min} years")

        # Compensation
        ai_salary_min = job.get("ai_salary_min", 0) or 0
        ai_salary_max = job.get("ai_salary_max", 0) or 0
        ai_salary_currency = job.get("ai_salary_currency", "") or ""

        if ai_salary_min and ai_salary_max:
            profile_parts.append(
                f"Salary: {ai_salary_currency} {ai_salary_min:,} - {ai_salary_max:,}"
            )
        elif ai_salary_min:
            profile_parts.append(
                f"Minimum salary: {ai_salary_currency} {ai_salary_min:,}"
            )

        # Description snippet
        description = job.get("description", "") or ""
        ai_summary = job.get("ai_summary", "") or ""

        if ai_summary:
            profile_parts.append(f"Summary: {ai_summary}")
        elif description:
            desc_snippet = (
                description[:300] + "..." if len(description) > 300 else description
            )
            profile_parts.append(f"Description: {desc_snippet}")

        return ". ".join(profile_parts) if profile_parts else "Job posting"
