#!/usr/bin/env python3
"""
Debug the comprehensive search function
"""

import sys
import os

sys.path.append("whatsapp_bot")

from database_manager import DatabaseManager
import logging

# Enable debug logging
logging.basicConfig(level=logging.DEBUG)


def debug_search():
    """Debug the search function step by step"""
    print("🔍 Debugging Comprehensive Search Function")
    print("=" * 50)

    try:
        # Initialize database manager
        db = DatabaseManager()

        # Check if we have jobs
        import psycopg2

        db_url = "postgresql://postgres.upnvhpgaljazlsoryfgj:prAlkIpbQDqOZtOj@aws-0-us-east-1.pooler.supabase.com:6543/postgres"
        conn = psycopg2.connect(db_url)
        cur = conn.cursor()

        cur.execute("SELECT COUNT(*) FROM canonical_jobs")
        total_jobs = cur.fetchone()[0]
        print(f"Total jobs in database: {total_jobs}")

        if total_jobs == 0:
            print("❌ No jobs in database! Need to run AI parser first.")
            return

        # Test simple search with fresh user
        test_phone = "+2348999999999"  # New phone number
        user_id = db.get_or_create_user(test_phone, "Fresh Debug User")

        # Clear any existing preferences first
        cur.execute("DELETE FROM user_preferences WHERE user_id = %s", (user_id,))
        conn.commit()

        # Set ONLY job_type preference
        preferences = {"job_type": "software"}
        db.save_user_preferences(user_id, preferences)

        # Check what was actually saved
        saved_prefs = db.get_user_preferences(user_id)
        print(f"Saved preferences: {saved_prefs}")

        print(f"\nTesting search with preferences: {preferences}")

        # Try the search
        jobs = db.search_jobs_simple(user_id, limit=2)

        print(f"Search result: {len(jobs)} jobs found")

        if jobs:
            for i, job in enumerate(jobs, 1):
                print(f"{i}. {job.get('title')} at {job.get('company')}")

        conn.close()
        db.close()

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    debug_search()
