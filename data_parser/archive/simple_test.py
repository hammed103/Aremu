#!/usr/bin/env python3
"""
Simple test to create canonical table and test basic parsing
"""

import psycopg2
import json
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(message)s")
logger = logging.getLogger(__name__)

def test_table_creation():
    """Test creating the canonical jobs table"""
    print("🧪 Testing Canonical Table Creation")
    print("=" * 40)
    
    try:
        # Database connection
        db_url = "postgresql://postgres.upnvhpgaljazlsoryfgj:prAlkIpbQDqOZtOj@aws-0-us-east-1.pooler.supabase.com:6543/postgres"
        conn = psycopg2.connect(db_url)
        conn.autocommit = True
        logger.info("✅ Connected to database")
        
        # Create canonical table
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS canonical_jobs (
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
            logger.info("✅ Canonical jobs table created")
            
            # Test a simple query
            cur.execute("SELECT COUNT(*) FROM raw_jobs WHERE source = 'linkedin' LIMIT 5")
            linkedin_count = cur.fetchone()[0]
            logger.info(f"📊 Found {linkedin_count} LinkedIn jobs in raw_jobs")
            
            cur.execute("SELECT COUNT(*) FROM raw_jobs WHERE source = 'jobspy' LIMIT 5")
            jobspy_count = cur.fetchone()[0]
            logger.info(f"📊 Found {jobspy_count} JobSpy jobs in raw_jobs")
            
            # Test parsing one job
            cur.execute("SELECT id, source, raw_data FROM raw_jobs LIMIT 1")
            result = cur.fetchone()
            
            if result:
                raw_id, source, raw_data_json = result
                raw_data = json.loads(raw_data_json)
                logger.info(f"📦 Sample job from {source}:")
                logger.info(f"   Title: {raw_data.get('title', 'N/A')}")
                logger.info(f"   Company: {raw_data.get('company', 'N/A')}")
                logger.info(f"   Location: {raw_data.get('location', 'N/A')}")
        
        conn.close()
        print("\n🎉 Table creation test successful!")
        print("💾 canonical_jobs table ready")
        print("📊 Raw jobs data accessible")
        return True
        
    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        print(f"\n❌ Test failed: {e}")
        return False

if __name__ == "__main__":
    test_table_creation()
