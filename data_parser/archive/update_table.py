#!/usr/bin/env python3
"""
Update canonical_jobs table with new fields
"""

import psycopg2
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(message)s")
logger = logging.getLogger(__name__)


def update_canonical_table():
    """Update canonical_jobs table with new fields"""
    print("🔧 Updating Canonical Jobs Table")
    print("=" * 40)

    try:
        # Database connection
        db_url = "postgresql://postgres.upnvhpgaljazlsoryfgj:prAlkIpbQDqOZtOj@aws-0-us-east-1.pooler.supabase.com:6543/postgres"
        conn = psycopg2.connect(db_url)
        conn.autocommit = True
        logger.info("✅ Connected to database")

        with conn.cursor() as cur:
            # Drop existing table and recreate with new schema
            cur.execute("DROP TABLE IF EXISTS canonical_jobs CASCADE")
            logger.info("🗑️  Dropped existing canonical_jobs table")

            # Create new table with simplified schema
            cur.execute(
                """
                CREATE TABLE canonical_jobs (
                    id SERIAL PRIMARY KEY,
                    
                    -- Core information (direct mapping)
                    title TEXT,
                    company TEXT,
                    location TEXT,
                    job_url TEXT,
                    description TEXT,
                    
                    -- Job details (direct mapping only)
                    employment_type TEXT,
                    salary_min DECIMAL,
                    salary_max DECIMAL,
                    salary_currency TEXT DEFAULT 'NGN',
                    
                    -- Contact information
                    email TEXT,
                    whatsapp_number TEXT,
                    application_mode TEXT[], -- Array: linkedin, indeed, jobberman, email, whatsapp

                    -- AI Enhanced fields (AI does most of the work)
                    city TEXT,
                    state TEXT,
                    required_skills TEXT[],
                    experience_level TEXT,
                    industry TEXT,
                    company_size TEXT,
                    remote_allowed BOOLEAN,
                    years_experience INTEGER,
                    ai_enhanced BOOLEAN DEFAULT FALSE,
                    ai_enhancement_date TIMESTAMP,
                    ai_extraction TEXT, -- Store raw AI response for debugging

                    -- Location (direct mapping)
                    country TEXT DEFAULT 'Nigeria',
                    
                    -- Dates and metadata
                    posted_date DATE,
                    application_deadline DATE,
                    
                    -- Source tracking
                    source TEXT NOT NULL, -- 'linkedin', 'jobspy', etc.
                    source_job_id TEXT,
                    raw_job_id INTEGER, -- Reference to raw_jobs table
                    
                    -- Timestamps
                    created_at TIMESTAMP DEFAULT NOW(),
                    updated_at TIMESTAMP DEFAULT NOW(),
                    
                    -- Constraints
                    UNIQUE(source, source_job_id)
                )
            """
            )
            logger.info("✅ Created new canonical_jobs table with simplified schema")

            # Create indexes
            cur.execute(
                "CREATE INDEX idx_canonical_jobs_source ON canonical_jobs(source)"
            )
            cur.execute(
                "CREATE INDEX idx_canonical_jobs_location ON canonical_jobs(location)"
            )
            cur.execute(
                "CREATE INDEX idx_canonical_jobs_company ON canonical_jobs(company)"
            )
            cur.execute(
                "CREATE INDEX idx_canonical_jobs_posted_date ON canonical_jobs(posted_date)"
            )
            logger.info("✅ Created indexes")

            # Verify table structure
            cur.execute(
                """
                SELECT column_name, data_type 
                FROM information_schema.columns 
                WHERE table_name = 'canonical_jobs' 
                ORDER BY ordinal_position
            """
            )
            columns = cur.fetchall()

            logger.info("📋 New table structure:")
            for col_name, col_type in columns:
                logger.info(f"   {col_name}: {col_type}")

        conn.close()
        print("\n🎉 Table updated successfully!")
        print("💾 canonical_jobs table ready with:")
        print("   ✅ Direct field mapping")
        print("   ✅ Contact information (email, whatsapp)")
        print("   ✅ Application modes array")
        print("   ✅ Simplified schema")
        return True

    except Exception as e:
        logger.error(f"❌ Update failed: {e}")
        print(f"\n❌ Update failed: {e}")
        return False


if __name__ == "__main__":
    update_canonical_table()
