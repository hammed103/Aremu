#!/usr/bin/env python3
"""
Script to find jobs with email contact information
"""

import psycopg2
import psycopg2.extras

# Database configuration
DATABASE_URL = "postgresql://postgres.upnvhpgaljazlsoryfgj:prAlkIpbQDqOZtOj@aws-0-us-east-1.pooler.supabase.com:6543/postgres"

def find_email_jobs():
    """Find jobs with email contact information"""
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        
        # Find jobs with email contact information
        query = """
            SELECT id, title, company, email, ai_email, whatsapp_number, ai_whatsapp_number, source, created_at
            FROM canonical_jobs 
            WHERE (email IS NOT NULL AND email != '') 
               OR (ai_email IS NOT NULL AND ai_email != '')
            ORDER BY created_at DESC
            LIMIT 10
        """
        
        cursor.execute(query)
        jobs = cursor.fetchall()
        
        print(f"📧 Found {len(jobs)} jobs with email contact:")
        print()
        
        for i, job in enumerate(jobs, 1):
            email = job['email'] or job['ai_email'] or 'None'
            whatsapp = job['whatsapp_number'] or job['ai_whatsapp_number'] or 'None'
            
            print(f"{i}. {job['title']} - {job['company']}")
            print(f"   📧 Email: {email}")
            print(f"   📱 WhatsApp: {whatsapp}")
            print(f"   🏷️  Source: {job['source']}")
            print(f"   📅 Created: {job['created_at']}")
            print()
        
        conn.close()
        return jobs
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return []

if __name__ == "__main__":
    find_email_jobs()
