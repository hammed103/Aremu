#!/usr/bin/env python3
"""
Add Missing Column
Quick fix for company_industry column
"""

import psycopg2
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(message)s")
logger = logging.getLogger(__name__)


def add_missing_column():
    """Add the missing company_industry column"""
    db_url = "postgresql://postgres.upnvhpgaljazlsoryfgj:prAlkIpbQDqOZtOj@aws-0-us-east-1.pooler.supabase.com:6543/postgres"

    try:
        conn = psycopg2.connect(db_url)
        conn.autocommit = True

        with conn.cursor() as cur:
            # Add the missing column
            try:
                cur.execute(
                    "ALTER TABLE canonical_jobs ADD COLUMN company_industry TEXT"
                )
                print("✅ Added company_industry column")
            except Exception as e:
                if "already exists" in str(e):
                    print("ℹ️  company_industry column already exists")
                else:
                    print(f"⚠️  Error adding company_industry: {e}")

            # Add other missing columns
            missing_columns = [
                ("company_description", "TEXT"),
                ("benefits", "TEXT"),
                ("application_mode", "TEXT"),
                ("emails", "TEXT"),
                ("phones", "TEXT"),
            ]

            for column_name, column_type in missing_columns:
                try:
                    cur.execute(
                        f"ALTER TABLE canonical_jobs ADD COLUMN {column_name} {column_type}"
                    )
                    print(f"✅ Added {column_name} column")
                except Exception as e:
                    if "already exists" in str(e):
                        print(f"ℹ️  {column_name} column already exists")
                    else:
                        print(f"⚠️  Error adding {column_name}: {e}")

        conn.close()
        print("🎉 Missing columns added successfully!")
        return True

    except Exception as e:
        logger.error(f"❌ Failed to add missing columns: {e}")
        return False


if __name__ == "__main__":
    add_missing_column()
