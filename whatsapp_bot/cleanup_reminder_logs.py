#!/usr/bin/env python3
"""
Clean up old reminder logs to fix reminder issues
"""

import os
import sys
import logging
import psycopg2
from datetime import datetime

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def cleanup_reminder_logs():
    """Clean up old reminder logs that might be blocking new reminders"""
    try:
        # Connect to database
        database_url = os.getenv(
            "DATABASE_URL",
            "postgresql://postgres.upnvhpgaljazlsoryfgj:prAlkIpbQDqOZtOj@aws-0-us-east-1.pooler.supabase.com:6543/postgres",
        )
        
        conn = psycopg2.connect(database_url)
        cursor = conn.cursor()
        
        print("🧹 Cleaning up reminder logs...")
        
        # Check current reminder logs
        cursor.execute("SELECT COUNT(*) FROM reminder_log")
        total_logs = cursor.fetchone()[0]
        print(f"📊 Total reminder logs: {total_logs}")
        
        # Check logs from today
        cursor.execute("SELECT COUNT(*) FROM reminder_log WHERE DATE(sent_at) = CURRENT_DATE")
        today_logs = cursor.fetchone()[0]
        print(f"📅 Today's reminder logs: {today_logs}")
        
        # Show recent reminder types
        cursor.execute("""
            SELECT reminder_type, COUNT(*) 
            FROM reminder_log 
            WHERE DATE(sent_at) = CURRENT_DATE 
            GROUP BY reminder_type 
            ORDER BY COUNT(*) DESC
        """)
        
        reminder_types = cursor.fetchall()
        if reminder_types:
            print("📋 Today's reminder types:")
            for reminder_type, count in reminder_types:
                print(f"   - {reminder_type}: {count}")
        
        # Delete old test reminders (22h, 20h, 18h, 16h)
        test_reminder_types = ['22h_reminder', '20h_reminder', '18h_reminder', '16h_reminder']
        
        for reminder_type in test_reminder_types:
            cursor.execute("DELETE FROM reminder_log WHERE reminder_type = %s", (reminder_type,))
            deleted = cursor.rowcount
            if deleted > 0:
                print(f"🗑️  Deleted {deleted} old {reminder_type} logs")
        
        # Optionally delete all logs from today to reset (uncomment if needed)
        # cursor.execute("DELETE FROM reminder_log WHERE DATE(sent_at) = CURRENT_DATE")
        # deleted_today = cursor.rowcount
        # print(f"🗑️  Deleted {deleted_today} logs from today")
        
        conn.commit()
        
        # Check final count
        cursor.execute("SELECT COUNT(*) FROM reminder_log")
        final_logs = cursor.fetchone()[0]
        print(f"✅ Final reminder logs count: {final_logs}")
        
        cursor.close()
        conn.close()
        
        print("🎉 Cleanup completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Error during cleanup: {e}")
        return False


def check_users_needing_reminders():
    """Check which users currently need reminders"""
    try:
        # Connect to database
        database_url = os.getenv(
            "DATABASE_URL",
            "postgresql://postgres.upnvhpgaljazlsoryfgj:prAlkIpbQDqOZtOj@aws-0-us-east-1.pooler.supabase.com:6543/postgres",
        )
        
        conn = psycopg2.connect(database_url)
        cursor = conn.cursor()
        
        print("\n🔍 Checking users needing reminders...")
        
        # Use the same query as the reminder service
        query = """
        SELECT
            u.id,
            u.phone_number,
            u.name,
            u.last_active,
            EXTRACT(EPOCH FROM (NOW() - u.last_active)) / 3600 as hours_elapsed,
            24 - EXTRACT(EPOCH FROM (NOW() - u.last_active)) / 3600 as hours_remaining,
            COALESCE(js.jobs_sent_today, 0) as jobs_sent_count
        FROM users u
        LEFT JOIN (
            SELECT
                u2.id as user_id,
                COUNT(ujh.id) as jobs_sent_today
            FROM users u2
            LEFT JOIN user_job_history ujh ON u2.id = ujh.user_id 
                AND DATE(ujh.shown_at) = CURRENT_DATE
                AND ujh.message_sent = TRUE
            GROUP BY u2.id
        ) js ON u.id = js.user_id
        WHERE
            u.is_active = true
            AND u.last_active > NOW() - INTERVAL '24 hours'
            AND EXTRACT(EPOCH FROM (NOW() - u.last_active)) / 3600 >= 8  -- Start reminders at 8 hours
        ORDER BY u.last_active ASC
        """
        
        cursor.execute(query)
        users = cursor.fetchall()
        
        print(f"📊 Found {len(users)} users needing reminders:")
        
        for user in users:
            user_id, phone, name, last_active, hours_elapsed, hours_remaining, jobs_count = user
            print(f"   📱 {phone}: {hours_remaining:.1f}h remaining, {jobs_count} jobs sent")
            
            # Check if they have reminder logs today
            cursor.execute("""
                SELECT reminder_type, sent_at 
                FROM reminder_log 
                WHERE user_id = %s AND DATE(sent_at) = CURRENT_DATE 
                ORDER BY sent_at DESC
            """, (user_id,))
            
            reminders = cursor.fetchall()
            if reminders:
                print(f"      📋 Today's reminders: {[r[0] for r in reminders]}")
            else:
                print(f"      📋 No reminders sent today")
        
        cursor.close()
        conn.close()
        
        return True
        
    except Exception as e:
        print(f"❌ Error checking users: {e}")
        return False


def main():
    """Main function"""
    print("🚀 Reminder System Cleanup & Diagnostics")
    print("=" * 50)
    
    # Cleanup old logs
    if cleanup_reminder_logs():
        print("\n" + "=" * 50)
        
        # Check current status
        check_users_needing_reminders()
        
        print("\n" + "=" * 50)
        print("💡 Next steps:")
        print("   1. The reminder daemon should now send proper reminders")
        print("   2. Check Railway logs to see if daemon is running")
        print("   3. Test reminders should no longer appear")
        print("   4. Job counts should now be accurate")
    else:
        print("❌ Cleanup failed. Please check the error messages above.")


if __name__ == "__main__":
    main()
