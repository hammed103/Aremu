#!/usr/bin/env python3
"""
Diagnostic script to understand why User 249 is only seeing one job
"""

import sys
import os
import psycopg2
import psycopg2.extras
from typing import Dict, List

# Add paths for imports
sys.path.append(os.path.join(os.path.dirname(__file__), 'whatsapp_bot'))

from whatsapp_bot.legacy.intelligent_job_matcher import IntelligentJobMatcher

def get_database_connection():
    """Get database connection"""
    try:
        connection = psycopg2.connect(
            host="aws-0-us-east-1.pooler.supabase.com",
            database="postgres",
            user="postgres.upnvhpgaljazlsoryfgj",
            password="prAlkIpbQDqOZtOj",
            port="6543"
        )
        return connection
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return None

def diagnose_user_249():
    """Comprehensive diagnosis of User 249's job delivery issues"""
    
    print("🔍 Diagnosing User 249 Job Delivery Issues")
    print("=" * 50)
    
    connection = get_database_connection()
    if not connection:
        print("❌ Cannot connect to database for diagnosis")
        return
    
    try:
        cursor = connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        
        # 1. Check User 249 preferences
        print("\n1. 👤 User 249 Preferences Check")
        cursor.execute("SELECT * FROM user_preferences WHERE user_id = 249")
        user_prefs = cursor.fetchone()
        
        if user_prefs:
            print("✅ User preferences found:")
            print(f"   • Job roles: {user_prefs.get('job_roles')}")
            print(f"   • Work arrangements: {user_prefs.get('work_arrangements')}")
            print(f"   • Preferred locations: {user_prefs.get('preferred_locations')}")
            print(f"   • Salary range: {user_prefs.get('salary_min')} - {user_prefs.get('salary_max')} {user_prefs.get('salary_currency')}")
        else:
            print("❌ No user preferences found!")
            return
        
        # 2. Check total jobs in database
        print("\n2. 📊 Database Job Statistics")
        cursor.execute("SELECT COUNT(*) as total FROM canonical_jobs")
        total_jobs = cursor.fetchone()['total']
        print(f"   • Total jobs in database: {total_jobs}")
        
        cursor.execute("SELECT COUNT(*) as enhanced FROM canonical_jobs WHERE ai_enhanced = true")
        enhanced_jobs = cursor.fetchone()['enhanced']
        print(f"   • AI-enhanced jobs: {enhanced_jobs}")
        
        cursor.execute("SELECT COUNT(*) as recent FROM canonical_jobs WHERE created_at >= NOW() - INTERVAL '7 days'")
        recent_jobs = cursor.fetchone()['recent']
        print(f"   • Jobs from last 7 days: {recent_jobs}")
        
        # 3. Check location matching
        print("\n3. 📍 Location Analysis")
        user_locations = user_prefs.get('preferred_locations', [])
        print(f"   • User preferred locations: {user_locations}")
        
        # Check jobs with different location formats
        location_queries = [
            ("Lagos exact", "location ILIKE '%Lagos%'"),
            ("Lagos State", "location ILIKE '%Lagos State%'"),
            ("LOS abbreviation", "location ILIKE '%LOS%'"),
            ("Nigeria general", "location ILIKE '%Nigeria%'"),
            ("AI city Lagos", "ai_city ILIKE '%Lagos%'"),
            ("AI state Lagos", "ai_state ILIKE '%Lagos%'")
        ]
        
        for desc, query in location_queries:
            cursor.execute(f"SELECT COUNT(*) as count FROM canonical_jobs WHERE {query}")
            count = cursor.fetchone()['count']
            print(f"   • {desc}: {count} jobs")
        
        # 4. Check seen jobs for User 249
        print("\n4. 👁️ Seen Jobs Analysis")
        cursor.execute("SELECT COUNT(*) as seen FROM user_seen_jobs WHERE user_id = 249")
        seen_count = cursor.fetchone()['seen']
        print(f"   • Jobs already seen by User 249: {seen_count}")
        
        if seen_count > 0:
            cursor.execute("""
                SELECT job_id, seen_at 
                FROM user_seen_jobs 
                WHERE user_id = 249 
                ORDER BY seen_at DESC 
                LIMIT 5
            """)
            recent_seen = cursor.fetchall()
            print("   • Recent seen jobs:")
            for job in recent_seen:
                print(f"     - Job {job['job_id']} seen at {job['seen_at']}")
        
        # 5. Check job delivery logs
        print("\n5. 📤 Job Delivery Analysis")
        cursor.execute("""
            SELECT COUNT(*) as delivered 
            FROM job_delivery_log 
            WHERE user_id = 249 AND delivered_at >= NOW() - INTERVAL '24 hours'
        """)
        delivered_today = cursor.fetchone()['delivered']
        print(f"   • Jobs delivered to User 249 in last 24h: {delivered_today}")
        
        # 6. Test job matching with sample jobs
        print("\n6. 🎯 Job Matching Test")
        matcher = IntelligentJobMatcher(connection)
        
        # Get some sample jobs that should match
        cursor.execute("""
            SELECT id, title, company, location, ai_job_titles, ai_work_arrangement,
                   ai_salary_min, ai_salary_max, ai_salary_currency
            FROM canonical_jobs 
            WHERE (
                title ILIKE '%sales%' OR 
                ai_job_titles::text ILIKE '%sales%' OR
                title ILIKE '%account%' OR
                ai_job_titles::text ILIKE '%account%'
            )
            AND (location ILIKE '%lagos%' OR ai_city ILIKE '%lagos%')
            AND ai_enhanced = true
            LIMIT 5
        """)
        
        sample_jobs = cursor.fetchall()
        print(f"   • Found {len(sample_jobs)} potential matching jobs:")
        
        for job in sample_jobs:
            job_dict = dict(job)
            score = matcher._calculate_job_score(dict(user_prefs), job_dict)
            print(f"     - Job {job['id']}: {job['title']} → {score:.1f}/100 points")
            
            # Check if this job would pass location filtering
            location_compatible = matcher._is_location_compatible(dict(user_prefs), job_dict)
            print(f"       Location compatible: {location_compatible}")
        
        # 7. Check delivery thresholds and limits
        print("\n7. ⚙️ System Configuration Check")
        
        # Check if there are any system limits
        cursor.execute("""
            SELECT setting_name, setting_value 
            FROM system_settings 
            WHERE setting_name IN ('min_match_score', 'max_jobs_per_day', 'delivery_enabled')
        """)
        settings = cursor.fetchall()
        
        if settings:
            print("   • System settings:")
            for setting in settings:
                print(f"     - {setting['setting_name']}: {setting['setting_value']}")
        else:
            print("   • No system settings table found (using defaults)")
        
        # 8. Recommendations
        print("\n8. 💡 Diagnosis Summary & Recommendations")
        
        issues_found = []
        
        if seen_count > 50:
            issues_found.append("User has seen many jobs - might need fresh content")
        
        if delivered_today >= 10:
            issues_found.append("Daily delivery limit might be reached")
        
        if enhanced_jobs < 100:
            issues_found.append("Low number of AI-enhanced jobs in database")
        
        if len(sample_jobs) == 0:
            issues_found.append("No sales jobs found in Lagos - data issue")
        
        if issues_found:
            print("   🚨 Issues identified:")
            for issue in issues_found:
                print(f"     • {issue}")
        else:
            print("   ✅ No obvious issues found - need deeper investigation")
        
        print("\n   🔧 Recommended actions:")
        print("     1. Check smart delivery engine logs")
        print("     2. Verify location filtering logic")
        print("     3. Review job delivery scheduling")
        print("     4. Check if User 249 has delivery paused")
        print("     5. Verify minimum score thresholds")
        
    except Exception as e:
        print(f"❌ Error during diagnosis: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        if connection:
            connection.close()

if __name__ == "__main__":
    diagnose_user_249()
