#!/usr/bin/env python3
"""
Check AI extraction results
"""

import psycopg2
import json

def check_ai_results():
    """Check what the AI extracted"""
    print("🔍 Checking AI Extraction Results")
    print("=" * 40)
    
    try:
        # Database connection
        db_url = "postgresql://postgres.upnvhpgaljazlsoryfgj:prAlkIpbQDqOZtOj@aws-0-us-east-1.pooler.supabase.com:6543/postgres"
        conn = psycopg2.connect(db_url)
        
        with conn.cursor() as cur:
            # Get a few AI enhanced jobs
            cur.execute("""
                SELECT 
                    title, 
                    company, 
                    location,
                    city,
                    state,
                    email,
                    whatsapp_number,
                    application_mode,
                    employment_type,
                    salary_min,
                    salary_max,
                    required_skills,
                    experience_level,
                    industry,
                    ai_extraction
                FROM canonical_jobs 
                WHERE ai_enhanced = true 
                LIMIT 3
            """)
            
            jobs = cur.fetchall()
            
            if not jobs:
                print("❌ No AI enhanced jobs found")
                return
            
            for i, job in enumerate(jobs, 1):
                print(f"\n📋 JOB {i}:")
                print(f"   Title: {job[0]}")
                print(f"   Company: {job[1]}")
                print(f"   Location: {job[2]}")
                print(f"   City: {job[3]}")
                print(f"   State: {job[4]}")
                print(f"   Email: {job[5]}")
                print(f"   WhatsApp: {job[6]}")
                print(f"   Application Mode: {job[7]}")
                print(f"   Employment Type: {job[8]}")
                print(f"   Salary Min: {job[9]}")
                print(f"   Salary Max: {job[10]}")
                print(f"   Required Skills: {job[11]}")
                print(f"   Experience Level: {job[12]}")
                print(f"   Industry: {job[13]}")
                print(f"   AI Extraction (first 500 chars): {job[14][:500] if job[14] else 'None'}...")
                print("-" * 60)
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    check_ai_results()
