#!/usr/bin/env python3
"""
Fix user 249's eligibility issues
"""

import os
import sys

# Add the current directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from legacy.database_manager import DatabaseManager
from legacy.window_management_system import WindowManagementSystem


def fix_user_249():
    """Fix user 249's eligibility issues"""

    print("🔧 Fixing User 249's Eligibility Issues")
    print("=" * 50)

    db = DatabaseManager()
    window_manager = WindowManagementSystem()
    cursor = db.connection.cursor()

    try:
        # Fix 1: Confirm preferences
        print("\n1. Confirming user preferences...")
        cursor.execute(
            """
            UPDATE user_preferences
            SET preferences_confirmed = TRUE,
                updated_at = CURRENT_TIMESTAMP
            WHERE user_id = 249
        """
        )

        if cursor.rowcount > 0:
            print("   ✅ Preferences confirmed!")
        else:
            print("   ❌ Failed to confirm preferences")

        # Fix 2: Start new active conversation window (proper way)
        print("\n2. Starting new active conversation window...")
        success = window_manager.start_new_window(249)

        if success:
            print("   ✅ New conversation window started!")
        else:
            print("   ❌ Failed to start new conversation window")

        # Commit changes
        db.connection.commit()
        print("\n✅ All fixes applied successfully!")

        # Verify fixes
        print("\n3. Verifying fixes...")

        # Check preferences
        cursor.execute(
            "SELECT preferences_confirmed FROM user_preferences WHERE user_id = 249"
        )
        confirmed = cursor.fetchone()[0]
        print(f"   Preferences confirmed: {confirmed}")

        # Check window status
        cursor.execute(
            "SELECT window_status, last_activity FROM conversation_windows WHERE user_id = 249 ORDER BY window_start DESC LIMIT 1"
        )
        window_result = cursor.fetchone()
        if window_result:
            status, last_activity = window_result
            print(f"   Window status: {status}")
            print(f"   Last activity: {last_activity}")
        else:
            print("   ❌ No conversation window found")

        # Test eligibility
        print("\n4. Testing eligibility...")
        from data_parser.smart_delivery_engine import SmartDeliveryEngine

        smart_delivery = SmartDeliveryEngine()
        eligible_users = smart_delivery.get_eligible_users_for_delivery()

        user_249_eligible = any(user["user_id"] == 249 for user in eligible_users)

        if user_249_eligible:
            print("   🎉 User 249 is now ELIGIBLE for job delivery!")
        else:
            print("   ❌ User 249 is still NOT eligible")
            print(f"   📊 Total eligible users: {len(eligible_users)}")

    except Exception as e:
        print(f"❌ Error fixing user 249: {e}")
        import traceback

        traceback.print_exc()
        db.connection.rollback()


if __name__ == "__main__":
    fix_user_249()
