#!/usr/bin/env python3
"""
Database Configuration
"""

import os
from typing import Dict, List

# Database Configuration
DATABASE_CONFIG = {
    "url": "postgresql://postgres.upnvhpgaljazlsoryfgj:prAlkIpbQDqOZtOj@aws-0-us-east-1.pooler.supabase.com:6543/postgres",
    "pool_size": 5,
    "max_overflow": 10,
    "pool_timeout": 30,
    "pool_recycle": 3600,
}

# Data Sources Configuration
DATA_SOURCES = [
    {
        "name": "linkedin_nigeria",
        "type": "linkedin",
        "file_path": "/Users/hammedbalogun/Desktop/JOBS/scraper/linkedin/nigeria_all_jobs.csv",
        "description": "LinkedIn Nigeria jobs scraped data",
        "active": True,
    },
    {
        "name": "generic_jobs",
        "type": "generic",
        "file_path": "/Users/hammedbalogun/Desktop/JOBS/jobs.csv",
        "description": "Generic jobs CSV data",
        "active": True,
    },
]

# Field Mapping for Canonical Jobs
# Maps raw field names to canonical field names
FIELD_MAPPINGS = {
    "linkedin": {
        "title": ["title", "job_title", "position"],
        "company": ["company", "company_name", "employer"],
        "location": ["location", "job_location", "city"],
        "description": ["all_job_details", "description", "job_description"],
        "posted_date": ["posted_date", "date_posted", "post_date"],
        "job_url": ["job_url", "url", "link"],
        "job_id": ["job_id", "id", "jobId"],
        "scraped_at": ["scraped_at", "created_at", "timestamp"],
    },
    "generic": {
        "title": ["title", "job_title", "position", "role", "job_name"],
        "company": ["company", "company_name", "employer", "organization"],
        "location": ["location", "job_location", "city", "address"],
        "description": ["description", "job_description", "details", "summary"],
        "posted_date": ["posted_date", "date_posted", "post_date", "created_date"],
        "job_url": ["job_url", "url", "link", "apply_url"],
        "job_id": ["job_id", "id", "jobId", "ID"],
        "salary": ["salary", "pay", "compensation", "wage"],
        "job_type": ["job_type", "employment_type", "type", "category"],
    },
}

# Normalization Rules
NORMALIZATION_RULES = {
    "job_type": {
        "full-time": ["full time", "fulltime", "permanent", "full-time"],
        "part-time": ["part time", "parttime", "part-time"],
        "contract": ["contract", "contractor", "freelance", "temporary"],
        "internship": ["intern", "internship", "trainee", "graduate"],
    },
    "remote_type": {
        "remote": ["remote", "work from home", "wfh", "telecommute"],
        "hybrid": ["hybrid", "flexible", "mixed"],
        "onsite": ["onsite", "on-site", "office", "in-person"],
    },
    "experience_level": {
        "entry": ["entry", "junior", "graduate", "fresh", "beginner", "0-2 years"],
        "mid": ["mid", "intermediate", "experienced", "2-5 years", "3-7 years"],
        "senior": ["senior", "lead", "principal", "5+ years", "7+ years"],
        "executive": ["executive", "director", "manager", "head", "chief"],
    },
}

# Location Normalization
LOCATION_MAPPINGS = {
    "nigeria_cities": {
        "Lagos": ["lagos", "lagos state", "lagos, nigeria", "lagos nigeria"],
        "Abuja": ["abuja", "fct", "federal capital territory", "abuja, nigeria"],
        "Port Harcourt": [
            "port harcourt",
            "ph",
            "rivers state",
            "port harcourt, nigeria",
        ],
        "Kano": ["kano", "kano state", "kano, nigeria"],
        "Ibadan": ["ibadan", "oyo state", "ibadan, nigeria"],
        "Kaduna": ["kaduna", "kaduna state", "kaduna, nigeria"],
    }
}


def get_database_url() -> str:
    """Get database URL from environment or config"""
    return os.getenv("DATABASE_URL", DATABASE_CONFIG["url"])


def get_active_sources() -> List[Dict]:
    """Get list of active data sources"""
    return [source for source in DATA_SOURCES if source.get("active", True)]


def get_field_mapping(source_type: str) -> Dict:
    """Get field mapping for a specific source type"""
    return FIELD_MAPPINGS.get(source_type, FIELD_MAPPINGS["generic"])


def normalize_value(field: str, value: str) -> str:
    """Normalize a field value using predefined rules"""
    if not value or field not in NORMALIZATION_RULES:
        return value

    value_lower = str(value).lower().strip()

    for normalized, variants in NORMALIZATION_RULES[field].items():
        if any(variant in value_lower for variant in variants):
            return normalized

    return value
