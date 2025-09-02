#!/usr/bin/env python3
"""
Check the specific jobs that were sent to verify they have no contact info
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'whatsapp_bot'))

from database_manager import DatabaseManager

def check_specific_jobs():
    """Check the specific jobs that were sent via WhatsApp"""
    try:
        db = DatabaseManager()
        conn = db.get_connection()
        cursor = conn.cursor()
        
        print("=== CHECKING SPECIFIC JOBS FROM WHATSAPP MESSAGES ===\n")
        
        # The jobs from the WhatsApp messages
        job_titles = [
            "Sales Representative",
            "Relationship Manager", 
            "B2B Cold Caller",
            "Client Services Associate"
        ]
        
        for i, title in enumerate(job_titles, 1):
            print(f"Job #{i}: {title}")
            
            # Find jobs with this title
            cursor.execute("""
                SELECT id, title, company, job_url, email, ai_email, 
                       whatsapp_number, ai_whatsapp_number, source
                FROM canonical_jobs 
                WHERE title ILIKE %s
                ORDER BY created_at DESC
                LIMIT 3
            """, (f"%{title}%",))
            
            jobs = cursor.fetchall()
            
            if jobs:
                for job in jobs:
                    job_id, job_title, company, job_url, email, ai_email, whatsapp, ai_whatsapp, source = job
                    
                    print(f"  📋 ID: {job_id} | Company: {company}")
                    print(f"  🔗 job_url: {job_url or 'None'}")
                    print(f"  📧 email: {email or 'None'}")
                    print(f"  🤖 ai_email: {ai_email or 'None'}")
                    print(f"  📱 whatsapp_number: {whatsapp or 'None'}")
                    print(f"  🤖 ai_whatsapp_number: {ai_whatsapp or 'None'}")
                    print(f"  🏷️  source: {source}")
                    
                    # Check if this job has ANY contact info
                    has_contact = any([
                        job_url and job_url.strip(),
                        email and email.strip(),
                        ai_email and ai_email.strip(),
                        whatsapp and whatsapp.strip(),
                        ai_whatsapp and ai_whatsapp.strip()
                    ])
                    
                    if has_contact:
                        print("  ✅ HAS CONTACT INFO - Should have CTA buttons")
                    else:
                        print("  ❌ NO CONTACT INFO - Will be sent as plain text")
                    
                    print()
            else:
                print(f"  ⚠️  No jobs found with title containing '{title}'")
                print()
        
        print("\n=== SUMMARY ===")
        print("If all 4 jobs show '❌ NO CONTACT INFO', that explains why no CTA buttons appeared.")
        print("The intelligent matcher is selecting jobs without contact information.")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    check_specific_jobs()
