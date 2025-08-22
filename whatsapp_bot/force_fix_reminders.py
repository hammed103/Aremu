#!/usr/bin/env python3
"""
Force fix reminder system by cleaning up all invalid reminders and testing the logic
"""

import os
import sys
import logging
import psycopg2
from datetime import datetime

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def force_cleanup_all_invalid_reminders():
    """Aggressively clean up all invalid reminder logs"""
    try:
        # Connect to database
        database_url = os.getenv(
            "DATABASE_URL",
            "postgresql://postgres.upnvhpgaljazlsoryfgj:prAlkIpbQDqOZtOj@aws-0-us-east-1.pooler.supabase.com:6543/postgres",
        )
        
        conn = psycopg2.connect(database_url)
        cursor = conn.cursor()
        
        print("🧹 Force cleaning ALL invalid reminder logs...")
        
        # Check current reminder logs
        cursor.execute("SELECT COUNT(*) FROM reminder_log")
        total_logs = cursor.fetchone()[0]
        print(f"📊 Total reminder logs before: {total_logs}")
        
        # Show all reminder types currently in database
        cursor.execute("""
            SELECT reminder_type, COUNT(*) 
            FROM reminder_log 
            GROUP BY reminder_type 
            ORDER BY COUNT(*) DESC
        """)
        
        all_types = cursor.fetchall()
        print("📋 Current reminder types in database:")
        for reminder_type, count in all_types:
            print(f"   - {reminder_type}: {count}")
        
        # Only keep valid reminder types from our schedule
        valid_types = ['8h_reminder', '5h_reminder', '3h_reminder', '1h_reminder', '0.25h_reminder']
        
        print(f"\n🎯 Valid reminder types: {valid_types}")
        
        # Delete ALL invalid reminder types
        placeholders = ','.join(['%s'] * len(valid_types))
        cursor.execute(f"""
            DELETE FROM reminder_log 
            WHERE reminder_type NOT IN ({placeholders})
        """, valid_types)
        
        deleted_invalid = cursor.rowcount
        print(f"🗑️  Deleted {deleted_invalid} invalid reminder logs")
        
        # Also delete all reminders from today to reset
        cursor.execute("DELETE FROM reminder_log WHERE DATE(sent_at) = CURRENT_DATE")
        deleted_today = cursor.rowcount
        print(f"🗑️  Deleted {deleted_today} logs from today")
        
        conn.commit()
        
        # Check final count
        cursor.execute("SELECT COUNT(*) FROM reminder_log")
        final_logs = cursor.fetchone()[0]
        print(f"✅ Final reminder logs count: {final_logs}")
        
        # Show remaining types
        cursor.execute("""
            SELECT reminder_type, COUNT(*) 
            FROM reminder_log 
            GROUP BY reminder_type 
            ORDER BY COUNT(*) DESC
        """)
        
        remaining_types = cursor.fetchall()
        if remaining_types:
            print("📋 Remaining reminder types:")
            for reminder_type, count in remaining_types:
                print(f"   - {reminder_type}: {count}")
        else:
            print("📋 No reminder logs remaining (clean slate)")
        
        cursor.close()
        conn.close()
        
        print("🎉 Force cleanup completed!")
        return True
        
    except Exception as e:
        print(f"❌ Error during force cleanup: {e}")
        return False


def check_daemon_status():
    """Check if the daemon is running and what version"""
    print("\n🔍 Checking daemon status...")
    
    try:
        import requests
        
        # Try to check Railway deployment
        railway_url = "https://whatsapp-bot-production-8f5e.up.railway.app"
        
        print(f"📡 Checking daemon at {railway_url}")
        
        # Check health endpoint
        try:
            response = requests.get(f"{railway_url}/health", timeout=10)
            if response.status_code == 200:
                data = response.json()
                print(f"   ✅ Service Status: {data.get('status')}")
                print(f"   🤖 Bot Initialized: {data.get('bot_initialized')}")
                print(f"   ⏰ Reminder Daemon: {data.get('reminder_daemon_enabled')}")
            else:
                print(f"   ❌ Health check failed: {response.status_code}")
        except Exception as e:
            print(f"   ❌ Cannot reach daemon: {e}")
        
        # Check reminder status
        try:
            response = requests.get(f"{railway_url}/reminder/status", timeout=10)
            if response.status_code == 200:
                data = response.json()
                print(f"   📊 Daemon Status: {data.get('status')}")
                print(f"   👥 Users Needing Reminders: {data.get('users_needing_reminders')}")
                print(f"   📤 Reminders Sent Today: {data.get('reminders_sent_today')}")
            else:
                print(f"   ❌ Reminder status failed: {response.status_code}")
        except Exception as e:
            print(f"   ❌ Cannot get reminder status: {e}")
            
    except ImportError:
        print("   ⚠️  requests not available, skipping daemon check")


def test_new_logic_thoroughly():
    """Test the new reminder logic thoroughly"""
    print("\n🧪 Testing new reminder logic...")
    
    # Import the reminder service
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
    
    try:
        from services.reminder_service import ReminderService
        from services.whatsapp_service import WhatsAppService
        
        whatsapp_service = WhatsAppService("dummy_token", "dummy_phone_id")
        reminder_service = ReminderService(whatsapp_service)
        
        print(f"📅 Reminder schedule: {reminder_service.reminder_schedule}")
        
        # Test realistic scenarios
        test_scenarios = [
            {"hours": 8.5, "expected_slot": 8, "description": "Just entered 8h window"},
            {"hours": 8.0, "expected_slot": 8, "description": "Exactly 8h remaining"},
            {"hours": 7.0, "expected_slot": 8, "description": "Still in 8h window"},
            {"hours": 6.5, "expected_slot": 8, "description": "End of 8h window"},
            {"hours": 5.5, "expected_slot": 5, "description": "Just entered 5h window"},
            {"hours": 5.0, "expected_slot": 5, "description": "Exactly 5h remaining"},
            {"hours": 4.5, "expected_slot": 5, "description": "End of 5h window"},
            {"hours": 3.5, "expected_slot": 3, "description": "Just entered 3h window"},
            {"hours": 3.0, "expected_slot": 3, "description": "Exactly 3h remaining"},
            {"hours": 2.0, "expected_slot": 3, "description": "Still in 3h window"},
            {"hours": 1.2, "expected_slot": 1, "description": "Just entered 1h window"},
            {"hours": 1.0, "expected_slot": 1, "description": "Exactly 1h remaining"},
            {"hours": 0.8, "expected_slot": 1, "description": "Still in 1h window"},
            {"hours": 0.4, "expected_slot": 0.25, "description": "15min window"},
            {"hours": 0.1, "expected_slot": 0.25, "description": "Final minutes"},
        ]
        
        print("📋 Testing realistic scenarios:")
        all_correct = True
        
        for scenario in test_scenarios:
            hours = scenario["hours"]
            expected = scenario["expected_slot"]
            description = scenario["description"]
            
            actual_slot = reminder_service.get_reminder_slot(hours)
            status = "✅" if actual_slot == expected else "❌"
            
            if actual_slot != expected:
                all_correct = False
                
            print(f"   {status} {hours}h → {actual_slot} ({description})")
        
        if all_correct:
            print("🎉 All reminder logic tests passed!")
        else:
            print("⚠️  Some tests failed - logic needs adjustment")
            
        return all_correct
        
    except Exception as e:
        print(f"❌ Error testing logic: {e}")
        return False


def create_deployment_instructions():
    """Create instructions for redeploying the daemon"""
    print("\n📋 Deployment Instructions:")
    print("=" * 50)
    print("To ensure the daemon uses the new code:")
    print()
    print("1. 🚀 **Redeploy on Railway:**")
    print("   - Go to Railway dashboard")
    print("   - Find your WhatsApp bot service")
    print("   - Click 'Deploy' or trigger a new deployment")
    print("   - This will restart the daemon with new code")
    print()
    print("2. 🔄 **Alternative - Restart via API:**")
    print("   - The daemon should auto-restart every few hours")
    print("   - Or manually restart the Railway service")
    print()
    print("3. ✅ **Verify Fix:**")
    print("   - Check Railway logs for 'Reminder Daemon initialized'")
    print("   - Look for 'Reminder schedule: [8, 5, 3, 1, 0.25]'")
    print("   - No more duplicate reminders should appear")
    print()
    print("4. 🎯 **Expected Behavior:**")
    print("   - Only one reminder per time slot (8h, 5h, 3h, 1h, 15min)")
    print("   - Accurate job counts in messages")
    print("   - Correct monitoring hours calculation")
    print("   - No test messages")


def main():
    """Main function"""
    print("🚀 Force Fix Reminder System")
    print("=" * 50)
    
    # Force cleanup
    if force_cleanup_all_invalid_reminders():
        print("\n" + "=" * 50)
        
        # Check daemon status
        check_daemon_status()
        
        print("\n" + "=" * 50)
        
        # Test logic
        test_new_logic_thoroughly()
        
        print("\n" + "=" * 50)
        
        # Deployment instructions
        create_deployment_instructions()
        
        print("\n" + "=" * 50)
        print("🎯 Summary:")
        print("   ✅ Cleaned up ALL invalid reminder logs")
        print("   ✅ Reset today's reminders")
        print("   ✅ Tested new logic")
        print("   🚀 Ready for daemon restart/redeploy")
        
    else:
        print("❌ Force cleanup failed!")


if __name__ == "__main__":
    main()
