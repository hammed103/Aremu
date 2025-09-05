#!/usr/bin/env python3
"""
Check why User 249 is only seeing one job - eligibility and delivery analysis
"""

import sys
import os
import psycopg2
import psycopg2.extras

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

def check_user_249_eligibility():
    """Check User 249's eligibility for smart delivery"""
    
    print("🔍 Checking User 249 Smart Delivery Eligibility")
    print("=" * 55)
    
    connection = get_database_connection()
    if not connection:
        return
    
    try:
        cursor = connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        
        # 1. Check if User 249 exists and has confirmed preferences
        print("\n1. 👤 User 249 Basic Check")
        cursor.execute("SELECT * FROM users WHERE id = 249")
        user = cursor.fetchone()
        
        if user:
            print(f"✅ User 249 exists: {user.get('name')} ({user.get('phone_number')})")
        else:
            print("❌ User 249 not found!")
            return
        
        cursor.execute("SELECT * FROM user_preferences WHERE user_id = 249")
        prefs = cursor.fetchone()
        
        if prefs:
            print(f"✅ Preferences exist, confirmed: {prefs.get('preferences_confirmed')}")
        else:
            print("❌ No preferences found!")
            return
        
        # 2. Check conversation window status (CRITICAL for delivery)
        print("\n2. 💬 Conversation Window Status")
        cursor.execute("SELECT * FROM conversation_windows WHERE user_id = 249")
        window = cursor.fetchone()
        
        if window:
            print(f"✅ Conversation window exists:")
            print(f"   • Status: {window.get('window_status')}")
            print(f"   • Last activity: {window.get('last_activity')}")
            print(f"   • Messages in window: {window.get('messages_in_window')}")
            
            # Check if window is active and recent
            cursor.execute("""
                SELECT 
                    CASE WHEN last_activity >= CURRENT_TIMESTAMP - INTERVAL '23 hours 30 minutes' 
                    THEN 'RECENT' ELSE 'OLD' END as activity_status
                FROM conversation_windows 
                WHERE user_id = 249
            """)
            activity_status = cursor.fetchone()
            print(f"   • Activity status: {activity_status.get('activity_status')}")
            
        else:
            print("❌ No conversation window found! This is why no jobs are delivered.")
            print("   Smart delivery requires an active conversation window.")
            return
        
        # 3. Check if User 249 would be eligible for delivery
        print("\n3. 🎯 Smart Delivery Eligibility Query")
        cursor.execute("""
            SELECT DISTINCT
                u.id,
                u.phone_number,
                u.name,
                up.job_roles,
                up.preferred_locations,
                up.work_arrangements,
                cw.window_status,
                cw.last_activity,
                CASE WHEN cw.last_activity >= CURRENT_TIMESTAMP - INTERVAL '23 hours 30 minutes' 
                THEN 'ELIGIBLE' ELSE 'NOT_ELIGIBLE' END as delivery_status
            FROM users u
            JOIN user_preferences up ON u.id = up.user_id
            JOIN conversation_windows cw ON u.id = cw.user_id
            WHERE u.id = 249
            AND up.preferences_confirmed = TRUE
            AND cw.window_status = 'active'
            AND cw.last_activity >= CURRENT_TIMESTAMP - INTERVAL '23 hours 30 minutes'
        """)
        
        eligible = cursor.fetchone()
        
        if eligible:
            print("✅ User 249 IS ELIGIBLE for smart delivery!")
            print(f"   • Delivery status: {eligible.get('delivery_status')}")
        else:
            print("❌ User 249 IS NOT ELIGIBLE for smart delivery!")
            print("   Checking individual requirements...")
            
            # Check each requirement individually
            cursor.execute("SELECT preferences_confirmed FROM user_preferences WHERE user_id = 249")
            confirmed = cursor.fetchone()
            print(f"   • Preferences confirmed: {confirmed.get('preferences_confirmed') if confirmed else 'NO PREFS'}")
            
            cursor.execute("SELECT window_status FROM conversation_windows WHERE user_id = 249")
            status = cursor.fetchone()
            print(f"   • Window status: {status.get('window_status') if status else 'NO WINDOW'}")
            
            cursor.execute("""
                SELECT 
                    last_activity,
                    CASE WHEN last_activity >= CURRENT_TIMESTAMP - INTERVAL '23 hours 30 minutes' 
                    THEN 'RECENT' ELSE 'OLD' END as recent_activity
                FROM conversation_windows WHERE user_id = 249
            """)
            activity = cursor.fetchone()
            if activity:
                print(f"   • Last activity: {activity.get('last_activity')} ({activity.get('recent_activity')})")
            else:
                print("   • Last activity: NO WINDOW")
        
        # 4. Check job history
        print("\n4. 📋 Job History Check")
        cursor.execute("SELECT COUNT(*) as count FROM user_job_history WHERE user_id = 249")
        history_count = cursor.fetchone()
        print(f"   • Jobs shown to User 249: {history_count.get('count')}")
        
        if history_count.get('count') > 0:
            cursor.execute("""
                SELECT job_id, match_score, shown_at, delivery_type 
                FROM user_job_history 
                WHERE user_id = 249 
                ORDER BY shown_at DESC 
                LIMIT 5
            """)
            recent_jobs = cursor.fetchall()
            print("   • Recent job deliveries:")
            for job in recent_jobs:
                print(f"     - Job {job['job_id']}: {job['match_score']:.1f} pts at {job['shown_at']}")
        
        # 5. Manual job matching test
        print("\n5. 🧪 Manual Job Matching Test")
        
        # Get a sample sales job in Lagos
        cursor.execute("""
            SELECT id, title, company, location, ai_job_titles, ai_work_arrangement
            FROM canonical_jobs 
            WHERE (title ILIKE '%sales%' OR ai_job_titles::text ILIKE '%sales%')
            AND (location ILIKE '%lagos%' OR ai_city ILIKE '%lagos%')
            LIMIT 3
        """)
        
        sample_jobs = cursor.fetchall()
        print(f"   • Found {len(sample_jobs)} sample sales jobs in Lagos:")
        
        for job in sample_jobs:
            print(f"     - Job {job['id']}: {job['title']} at {job.get('company', 'Unknown')}")
            print(f"       Location: {job['location']}")
            print(f"       AI titles: {job.get('ai_job_titles', [])}")
        
        # 6. Check if smart delivery is running
        print("\n6. ⚙️ System Status Check")
        
        # Check for recent job processing
        cursor.execute("""
            SELECT COUNT(*) as recent_jobs 
            FROM canonical_jobs 
            WHERE created_at >= NOW() - INTERVAL '24 hours'
        """)
        recent_jobs = cursor.fetchone()
        print(f"   • Jobs added in last 24h: {recent_jobs.get('recent_jobs')}")
        
        # Check for any delivery logs (if table exists)
        try:
            cursor.execute("""
                SELECT COUNT(*) as deliveries 
                FROM job_delivery_log 
                WHERE created_at >= NOW() - INTERVAL '24 hours'
            """)
            deliveries = cursor.fetchone()
            print(f"   • Deliveries in last 24h: {deliveries.get('deliveries')}")
        except:
            print("   • No delivery log table found")
        
        print("\n7. 💡 Summary & Recommendations")
        
        if not eligible:
            print("🚨 ISSUE FOUND: User 249 is not eligible for smart delivery!")
            print("   Most likely causes:")
            print("   1. Conversation window is not active")
            print("   2. Last activity is older than 23.5 hours")
            print("   3. Preferences not confirmed")
            print("\n   🔧 Solutions:")
            print("   1. User needs to send a message to activate window")
            print("   2. Check conversation window management")
            print("   3. Verify preferences confirmation process")
        else:
            print("✅ User 249 is eligible for smart delivery")
            print("   Other possible issues:")
            print("   1. No new jobs matching criteria")
            print("   2. All matching jobs already shown")
            print("   3. Smart delivery service not running")
            print("   4. Location matching too strict")
        
    except Exception as e:
        print(f"❌ Error during check: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        if connection:
            connection.close()

if __name__ == "__main__":
    check_user_249_eligibility()
