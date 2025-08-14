#!/usr/bin/env python3
"""
Fix canonical_jobs table
"""

import psycopg2
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(message)s")
logger = logging.getLogger(__name__)

def fix_canonical_table():
    """Drop and recreate canonical_jobs table properly"""
    print("🔧 Fixing Canonical Jobs Table")
    print("=" * 40)
    
    try:
        # Database connection
        db_url = "postgresql://postgres.upnvhpgaljazlsoryfgj:prAlkIpbQDqOZtOj@aws-0-us-east-1.pooler.supabase.com:6543/postgres"
        conn = psycopg2.connect(db_url)
        conn.autocommit = True
        logger.info("✅ Connected to database")
        
        with conn.cursor() as cur:
            # Drop existing table
            cur.execute("DROP TABLE IF EXISTS canonical_jobs CASCADE")
            logger.info("🗑️  Dropped existing canonical_jobs table")
            
            # Create new table with all columns
            cur.execute("""
                CREATE TABLE canonical_jobs (
                    id SERIAL PRIMARY KEY,
                    title TEXT,
                    company TEXT,
                    location TEXT,
                    job_url TEXT,
                    description TEXT,
                    employment_type TEXT,
                    experience_level TEXT,
                    salary_min DECIMAL,
                    salary_max DECIMAL,
                    salary_currency TEXT DEFAULT 'NGN',
                    required_skills TEXT[],
                    preferred_skills TEXT[],
                    education_requirements TEXT,
                    years_experience_min INTEGER,
                    years_experience_max INTEGER,
                    company_size TEXT,
                    industry TEXT,
                    company_description TEXT,
                    city TEXT,
                    state TEXT,
                    country TEXT DEFAULT 'Nigeria',
                    remote_allowed BOOLEAN DEFAULT FALSE,
                    posted_date DATE,
                    application_deadline DATE,
                    source TEXT NOT NULL,
                    source_job_id TEXT,
                    raw_job_id INTEGER,
                    ai_enhanced BOOLEAN DEFAULT FALSE,
                    ai_enhancement_date TIMESTAMP,
                    created_at TIMESTAMP DEFAULT NOW(),
                    updated_at TIMESTAMP DEFAULT NOW(),
                    UNIQUE(source, source_job_id)
                )
            """)
            logger.info("✅ Created new canonical_jobs table")
            
            # Create indexes
            cur.execute("CREATE INDEX idx_canonical_jobs_source ON canonical_jobs(source)")
            cur.execute("CREATE INDEX idx_canonical_jobs_location ON canonical_jobs(location)")
            cur.execute("CREATE INDEX idx_canonical_jobs_company ON canonical_jobs(company)")
            cur.execute("CREATE INDEX idx_canonical_jobs_posted_date ON canonical_jobs(posted_date)")
            logger.info("✅ Created indexes")
            
            # Verify table structure
            cur.execute("""
                SELECT column_name, data_type 
                FROM information_schema.columns 
                WHERE table_name = 'canonical_jobs' 
                ORDER BY ordinal_position
            """)
            columns = cur.fetchall()
            
            logger.info("📋 Table structure:")
            for col_name, col_type in columns:
                logger.info(f"   {col_name}: {col_type}")
        
        conn.close()
        print("\n🎉 Table fixed successfully!")
        print("💾 canonical_jobs table ready with all columns")
        return True
        
    except Exception as e:
        logger.error(f"❌ Fix failed: {e}")
        print(f"\n❌ Fix failed: {e}")
        return False

if __name__ == "__main__":
    fix_canonical_table()
