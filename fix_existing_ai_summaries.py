#!/usr/bin/env python3
"""
Re-run AI enhancement on existing jobs to fix bad summaries
"""

import sys
import os
sys.path.append('data_parser/parsers')

from ai_enhanced_parser import AIEnhancedJobParser
import psycopg2

def fix_existing_ai_summaries():
    """Re-enhance existing jobs with fixed AI prompt"""
    print("🔧 Fixing Existing AI Summaries with Corrected Prompt")
    print("=" * 60)
    
    try:
        db_url = "postgresql://postgres.upnvhpgaljazlsoryfgj:prAlkIpbQDqOZtOj@aws-0-us-east-1.pooler.supabase.com:6543/postgres"
        conn = psycopg2.connect(db_url)
        cur = conn.cursor()
        
        # Find jobs with problematic AI summaries
        print("1️⃣ Finding jobs with problematic AI summaries...")
        
        cur.execute("""
            SELECT id, title, company, description, location, job_url,
                   ai_summary, ai_enhancement_date
            FROM canonical_jobs 
            WHERE ai_enhanced = true 
            AND (
                ai_summary LIKE '%[job_url]%' 
                OR ai_summary LIKE '%Not specified%'
                OR ai_summary LIKE '%{%'
                OR ai_summary LIKE '%globalhotline%'
            )
            ORDER BY ai_enhancement_date DESC
        """)
        
        problematic_jobs = cur.fetchall()
        print(f"   Found {len(problematic_jobs)} jobs with issues")
        
        if len(problematic_jobs) == 0:
            print("✅ No problematic summaries found!")
            return
        
        # Show issues found
        print("\n📋 Issues found:")
        for job_id, title, company, desc, location, job_url, summary, enhanced_date in problematic_jobs:
            issues = []
            if '[job_url]' in summary:
                issues.append("Contains [job_url] placeholder")
            if 'Not specified' in summary:
                issues.append("Says 'Not specified' instead of 'Competitive salary'")
            if 'globalhotline' in summary:
                issues.append("Contains support email")
            if '{' in summary:
                issues.append("Contains template placeholders")
            
            print(f"   ❌ {title[:40]}... - {', '.join(issues)}")
        
        # Ask for confirmation
        print(f"\n🤖 Re-enhance {len(problematic_jobs)} jobs with fixed AI prompt?")
        choice = input("Continue? (y/n): ").strip().lower()
        
        if choice != 'y':
            print("❌ Cancelled")
            return
        
        # Initialize AI parser
        print("\n2️⃣ Initializing AI parser with fixed prompt...")
        parser = AIEnhancedJobParser()
        
        if not parser.use_ai:
            print("❌ AI enhancement not available (no OpenAI key)")
            return
        
        print("   ✅ AI parser ready with fixed prompt")
        
        # Re-enhance each problematic job
        print(f"\n3️⃣ Re-enhancing {len(problematic_jobs)} jobs...")
        
        fixed_count = 0
        for i, (job_id, title, company, description, location, job_url, old_summary, enhanced_date) in enumerate(problematic_jobs, 1):
            print(f"\n   {i}/{len(problematic_jobs)} Processing: {title[:40]}...")
            
            try:
                # Create canonical job data
                canonical_job = {
                    "id": job_id,
                    "title": title,
                    "company": company,
                    "description": description,
                    "location": location,
                    "job_url": job_url
                }
                
                # Re-enhance with fixed AI prompt
                enhanced_job = parser.enhance_with_ai(canonical_job)
                
                # Update the database with new AI data
                new_summary = enhanced_job.get('ai_summary', '')
                new_email = enhanced_job.get('ai_email')
                new_whatsapp = enhanced_job.get('ai_whatsapp_number')
                
                # Check if the new summary is better
                issues_fixed = []
                if '[job_url]' not in new_summary and '[job_url]' in old_summary:
                    issues_fixed.append("Fixed [job_url] placeholder")
                if 'Not specified' not in new_summary and 'Not specified' in old_summary:
                    issues_fixed.append("Fixed 'Not specified' text")
                if 'globalhotline' not in new_summary and 'globalhotline' in old_summary:
                    issues_fixed.append("Removed support email")
                
                if issues_fixed or len(new_summary) > len(old_summary):
                    # Update the job with new AI data
                    update_fields = []
                    update_values = []
                    
                    for field, value in enhanced_job.items():
                        if field.startswith('ai_') and value is not None:
                            update_fields.append(f"{field} = %s")
                            update_values.append(value)
                    
                    if update_fields:
                        update_values.append(job_id)
                        cur.execute(f"""
                            UPDATE canonical_jobs 
                            SET {', '.join(update_fields)}, 
                                ai_enhancement_date = NOW()
                            WHERE id = %s
                        """, update_values)
                        
                        fixed_count += 1
                        print(f"      ✅ Fixed: {', '.join(issues_fixed) if issues_fixed else 'Improved summary'}")
                    else:
                        print(f"      ⚠️ No improvements generated")
                else:
                    print(f"      ⚠️ New summary not better than old one")
                
            except Exception as e:
                print(f"      ❌ Error: {e}")
        
        # Commit changes
        conn.commit()
        
        print(f"\n4️⃣ Results:")
        print(f"   ✅ Successfully fixed: {fixed_count} jobs")
        print(f"   📊 Total processed: {len(problematic_jobs)} jobs")
        print(f"   🎯 Success rate: {fixed_count/len(problematic_jobs)*100:.1f}%")
        
        # Show sample of fixed summaries
        if fixed_count > 0:
            print(f"\n📱 Sample of fixed summaries:")
            cur.execute("""
                SELECT title, ai_summary 
                FROM canonical_jobs 
                WHERE ai_enhancement_date >= NOW() - INTERVAL '5 minutes'
                AND ai_summary NOT LIKE '%[job_url]%'
                LIMIT 2
            """)
            
            fixed_samples = cur.fetchall()
            for title, summary in fixed_samples:
                print(f"\n✅ {title}:")
                contact_section = summary[summary.find('Ready to apply?'):] if 'Ready to apply?' in summary else summary[-100:]
                print(f"   Contact: {contact_section[:100]}...")
        
        conn.close()
        
        print(f"\n🎉 AI summary fixing completed!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    fix_existing_ai_summaries()
