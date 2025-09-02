#!/usr/bin/env python3
"""
Final Schema Fix
Add ALL missing columns to match the parser exactly
"""

import psycopg2
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(message)s")
logger = logging.getLogger(__name__)

def final_schema_fix():
    """Add all missing columns that the parser expects"""
    db_url = "postgresql://postgres.upnvhpgaljazlsoryfgj:prAlkIpbQDqOZtOj@aws-0-us-east-1.pooler.supabase.com:6543/postgres"
    
    try:
        conn = psycopg2.connect(db_url)
        conn.autocommit = True
        
        with conn.cursor() as cur:
            # Get existing columns
            cur.execute("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'canonical_jobs'
            """)
            
            existing_columns = [row[0] for row in cur.fetchall()]
            print(f"📊 Found {len(existing_columns)} existing columns")
            
            # ALL columns the parser might try to save
            all_possible_columns = [
                # Core fields that might be missing
                ("company_url", "TEXT"),
                ("work_arrangement", "TEXT"),
                ("application_mode", "TEXT"),
                
                # AI fields that might be missing  
                ("ai_email", "TEXT"),
                ("ai_whatsapp_number", "TEXT"),
                ("ai_application_modes", "TEXT"),
                ("ai_city", "TEXT"),
                ("ai_state", "TEXT"),
                ("ai_country", "TEXT"),
                ("ai_employment_type", "TEXT"),
                ("ai_job_function", "TEXT"),
                ("ai_job_level", "TEXT"),
                ("ai_industry", "TEXT"),
                ("ai_salary_min", "DECIMAL"),
                ("ai_salary_max", "DECIMAL"),
                ("ai_salary_currency", "TEXT"),
                ("ai_compensation_summary", "TEXT"),
                ("ai_required_skills", "TEXT"),
                ("ai_preferred_skills", "TEXT"),
                ("ai_education_requirements", "TEXT"),
                ("ai_years_experience_min", "INTEGER"),
                ("ai_years_experience_max", "INTEGER"),
                ("ai_remote_allowed", "BOOLEAN"),
                ("ai_work_arrangement", "TEXT"),
                ("ai_benefits", "TEXT"),
                ("ai_application_deadline", "DATE"),
                ("ai_posted_date", "DATE"),
                ("ai_summary", "TEXT"),
                ("ai_enhanced", "BOOLEAN DEFAULT FALSE"),
                ("ai_enhancement_date", "TIMESTAMP"),
                ("ai_extraction", "TEXT"),
            ]
            
            # Add missing columns
            added_count = 0
            for column_name, column_type in all_possible_columns:
                if column_name not in existing_columns:
                    try:
                        cur.execute(f"ALTER TABLE canonical_jobs ADD COLUMN {column_name} {column_type}")
                        print(f"✅ Added column: {column_name}")
                        added_count += 1
                    except Exception as e:
                        print(f"⚠️  Could not add {column_name}: {e}")
            
            print(f"\n🎉 Final schema fix completed!")
            print(f"📊 Added {added_count} missing columns")
            print(f"💾 canonical_jobs table should now work with the parser")
            
        conn.close()
        return True
        
    except Exception as e:
        logger.error(f"❌ Final schema fix failed: {e}")
        return False

if __name__ == "__main__":
    final_schema_fix()
