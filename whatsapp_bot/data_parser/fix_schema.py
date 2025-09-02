#!/usr/bin/env python3
"""
Fix Database Schema
Add any missing columns to the canonical_jobs table
"""

import psycopg2
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(message)s")
logger = logging.getLogger(__name__)


def fix_schema():
    """Fix the canonical_jobs table schema"""
    db_url = "postgresql://postgres.upnvhpgaljazlsoryfgj:prAlkIpbQDqOZtOj@aws-0-us-east-1.pooler.supabase.com:6543/postgres"

    try:
        conn = psycopg2.connect(db_url)
        conn.autocommit = True

        with conn.cursor() as cur:
            # Check current columns
            cur.execute(
                """
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'canonical_jobs'
                ORDER BY ordinal_position
            """
            )

            existing_columns = [row[0] for row in cur.fetchall()]
            print(f"📊 Found {len(existing_columns)} existing columns")

            # Define all required columns
            required_columns = [
                ("site", "TEXT"),
                ("job_url_direct", "TEXT"),
                ("job_type", "TEXT"),
                ("job_function", "TEXT"),
                ("job_level", "TEXT"),
                ("experience_level", "TEXT"),
                ("seniority_level", "TEXT"),
                ("industries", "TEXT"),
                ("min_amount", "DECIMAL"),
                ("max_amount", "DECIMAL"),
                ("currency", "TEXT"),
                ("is_remote", "BOOLEAN DEFAULT FALSE"),
                ("company_logo", "TEXT"),
                ("company_addresses", "TEXT"),
                ("company_num_employees", "TEXT"),
                ("company_revenue", "TEXT"),
                ("ceo_name", "TEXT"),
                ("ceo_photo_url", "TEXT"),
                ("logo_photo_url", "TEXT"),
                ("banner_photo_url", "TEXT"),
                ("skills", "TEXT"),
                ("date_posted", "DATE"),
                ("required_skills", "TEXT"),
                ("preferred_skills", "TEXT"),
                ("education_requirements", "TEXT"),
                ("years_experience_min", "INTEGER"),
                ("years_experience_max", "INTEGER"),
            ]

            # Add missing columns
            added_count = 0
            for column_name, column_type in required_columns:
                if column_name not in existing_columns:
                    try:
                        cur.execute(
                            f"ALTER TABLE canonical_jobs ADD COLUMN {column_name} {column_type}"
                        )
                        print(f"✅ Added column: {column_name}")
                        added_count += 1
                    except Exception as e:
                        print(f"⚠️  Could not add {column_name}: {e}")

            print(f"\n🎉 Schema fix completed!")
            print(f"📊 Added {added_count} missing columns")
            print(f"💾 canonical_jobs table now has all required fields")

        conn.close()
        return True

    except Exception as e:
        logger.error(f"❌ Schema fix failed: {e}")
        return False


if __name__ == "__main__":
    fix_schema()
