#!/usr/bin/env python3
"""
Configuration for Nigeria Job Scraper
Customize locations, keywords, and scraping parameters
"""

# Nigerian cities and their LinkedIn geo IDs
NIGERIAN_LOCATIONS = {
    "Nigeria": "105365761",  # General Nigeria - gets nationwide jobs
    "Lagos, Nigeria": "105693087",  # Updated correct geo ID for Lagos
    "Abuja, Nigeria": "90009707",
    "Port Harcourt, Nigeria": "106808692",
    "Kano, Nigeria": "106808693",
    # Add more cities as needed - you may need to find their geo IDs
    # "Ibadan, Nigeria": "XXXXX",
    # "Benin City, Nigeria": "XXXXX",
}

# Broad keyword categories to capture different job types
# Empty string "" captures ALL jobs in a location
KEYWORD_CATEGORIES = [
    "",  # ALL jobs (most important)
    "remote",
    "developer",
    "engineer",
    "manager",
    "analyst",
    "sales",
    "marketing",
    "finance",
    "operations",
    "customer service",
    "admin",
    "consultant",
    "specialist",
    "coordinator",
    "assistant",
    "intern",
    "graduate",
]

# Remote-specific keywords to catch remote opportunities
REMOTE_KEYWORDS = [
    "remote work Nigeria",
    "work from home Nigeria",
    "remote developer",
    "remote engineer",
    "remote analyst",
    "remote manager",
    "remote sales",
    "remote marketing",
    "remote customer service",
    "freelance Nigeria",
    "contract Nigeria",
]

# Scraping parameters
SCRAPING_CONFIG = {
    "scrape_interval_minutes": 10,  # How often to scrape
    "max_results_per_search": 10,  # REDUCED: Jobs per keyword/location combo
    "delay_between_requests": 1.5,  # Seconds between search requests
    "detail_delay": 2.0,  # Seconds between detail requests
    "time_filter": "r86400",  # Last 24 hours (r86400), week (r604800), month (r2592000)
    "save_logs": True,  # Save logs to file
    "log_filename": "nigeria_jobs.log",
}

# File naming
OUTPUT_CONFIG = {
    "filename_prefix": "nigeria_all_jobs",
    "include_timestamp": True,
    "save_csv": True,
    "save_json": True,
    "save_summary": True,
}

# Advanced settings
ADVANCED_CONFIG = {
    "remove_duplicates": True,  # Filter out duplicate job IDs
    "max_total_jobs_in_memory": 10000,  # Prevent memory issues
    "cleanup_old_jobs_days": 30,  # Remove jobs older than X days
}
