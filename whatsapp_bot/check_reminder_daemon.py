#!/usr/bin/env python3
"""
Quick script to check reminder daemon status on Railway
"""

import requests
import json
import sys
import os
from datetime import datetime

def check_daemon_status(base_url):
    """Check if reminder daemon is working"""
    print(f"🔍 Checking reminder daemon status at {base_url}")
    print("=" * 50)
    
    try:
        # Check health endpoint
        print("1. Checking health endpoint...")
        health_response = requests.get(f"{base_url}/health", timeout=10)
        health_data = health_response.json()
        
        print(f"   ✅ Service Status: {health_data.get('status')}")
        print(f"   🤖 Bot Initialized: {health_data.get('bot_initialized')}")
        print(f"   ⏰ Reminder Daemon Enabled: {health_data.get('reminder_daemon_enabled')}")
        
        if not health_data.get('bot_initialized'):
            print("   ❌ Bot not initialized - daemon won't work")
            return False
            
        if not health_data.get('reminder_daemon_enabled'):
            print("   ❌ Reminder daemon not enabled")
            return False
            
        print()
        
        # Check reminder status
        print("2. Checking reminder daemon activity...")
        reminder_response = requests.get(f"{base_url}/reminder/status", timeout=10)
        
        if reminder_response.status_code == 200:
            reminder_data = reminder_response.json()
            
            print(f"   ✅ Daemon Status: {reminder_data.get('status')}")
            print(f"   👥 Users Needing Reminders: {reminder_data.get('users_needing_reminders')}")
            print(f"   📤 Reminders Sent Today: {reminder_data.get('reminders_sent_today')}")
            print(f"   ⏱️  Check Interval: {reminder_data.get('check_interval_seconds')}s")
            
            recent_reminders = reminder_data.get('recent_reminders', [])
            if recent_reminders:
                print(f"   📋 Recent Reminders ({len(recent_reminders)}):")
                for reminder in recent_reminders[:3]:  # Show last 3
                    sent_at = reminder.get('sent_at', 'Unknown')
                    reminder_type = reminder.get('reminder_type', 'Unknown')
                    phone = reminder.get('phone_number', 'Unknown')
                    print(f"      - {sent_at}: {reminder_type} to {phone}")
            else:
                print("   📋 No recent reminders found")
                
            return True
        else:
            print(f"   ❌ Failed to get reminder status: {reminder_response.status_code}")
            print(f"   Error: {reminder_response.text}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Connection error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def test_reminder_cycle(base_url):
    """Manually trigger a reminder cycle"""
    print("\n3. Testing reminder cycle...")
    try:
        response = requests.post(f"{base_url}/reminder/test", timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Test Status: {data.get('status')}")
            print(f"   📤 Reminders Sent: {data.get('reminders_sent')}")
            print(f"   💬 Message: {data.get('message')}")
            return True
        else:
            print(f"   ❌ Test failed: {response.status_code}")
            print(f"   Error: {response.text}")
            return False
            
    except Exception as e:
        print(f"   ❌ Test error: {e}")
        return False

def main():
    """Main function"""
    # Get Railway URL from environment or command line
    railway_url = os.getenv('RAILWAY_URL')
    
    if len(sys.argv) > 1:
        railway_url = sys.argv[1]
    
    if not railway_url:
        print("❌ Please provide Railway URL:")
        print("   python check_reminder_daemon.py https://your-app.railway.app")
        print("   or set RAILWAY_URL environment variable")
        sys.exit(1)
    
    # Remove trailing slash
    railway_url = railway_url.rstrip('/')
    
    print(f"🚀 Reminder Daemon Health Check")
    print(f"📅 Time: {datetime.now()}")
    print(f"🌐 URL: {railway_url}")
    print()
    
    # Check daemon status
    daemon_ok = check_daemon_status(railway_url)
    
    if daemon_ok:
        # Test reminder cycle
        test_ok = test_reminder_cycle(railway_url)
        
        if test_ok:
            print("\n🎉 Reminder daemon is working correctly!")
        else:
            print("\n⚠️  Daemon is running but test cycle failed")
    else:
        print("\n❌ Reminder daemon is not working properly")
        
    print("\n" + "=" * 50)
    print("💡 Tips:")
    print("   - Check Railway logs for detailed error messages")
    print("   - Ensure FLASK_ENV=production is set in Railway")
    print("   - Verify database connection and WhatsApp credentials")
    print("   - Check that users exist in database with recent activity")

if __name__ == "__main__":
    main()
