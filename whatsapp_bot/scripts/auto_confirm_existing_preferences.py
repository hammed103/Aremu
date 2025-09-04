#!/usr/bin/env python3
"""
Auto-confirm existing user preferences based on completeness
This script will retroactively apply the auto-confirmation logic to existing users
"""

import sys
import os
import logging

# Add parent directory to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from legacy.database_manager import DatabaseManager

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def auto_confirm_existing_preferences():
    """Auto-confirm preferences for existing users based on completeness"""
    try:
        # Connect to database
        db = DatabaseManager()
        cursor = db.connection.cursor()
        
        print("🔍 Checking existing user preferences for auto-confirmation...")
        
        # Get all users with preferences that are not confirmed
        cursor.execute("""
            SELECT 
                up.user_id,
                u.name,
                u.phone_number,
                up.job_roles,
                up.preferred_locations,
                up.salary_min,
                up.work_arrangements,
                up.preferences_confirmed
            FROM user_preferences up
            JOIN users u ON up.user_id = u.id
            WHERE up.preferences_confirmed = FALSE OR up.preferences_confirmed IS NULL
            ORDER BY up.updated_at DESC
        """)
        
        unconfirmed_users = cursor.fetchall()
        print(f"Found {len(unconfirmed_users)} users with unconfirmed preferences")
        
        auto_confirmed_count = 0
        incomplete_count = 0
        
        for user in unconfirmed_users:
            user_id = user[0]
            name = user[1] or "Unknown"
            phone = user[2]
            job_roles = user[3] or []
            locations = user[4] or []
            salary_min = user[5]
            work_arrangements = user[6] or []
            current_confirmed = user[7]
            
            # Check if user has essential preferences
            has_job_roles = job_roles and len(job_roles) > 0
            has_locations = locations and len(locations) > 0
            
            print(f"\nUser {user_id} ({name}): {phone}")
            print(f"  Job roles: {job_roles}")
            print(f"  Locations: {locations}")
            print(f"  Currently confirmed: {current_confirmed}")
            
            if has_job_roles and has_locations:
                # Auto-confirm this user
                cursor.execute(
                    "UPDATE user_preferences SET preferences_confirmed = TRUE WHERE user_id = %s",
                    (user_id,)
                )
                auto_confirmed_count += 1
                print(f"  ✅ AUTO-CONFIRMED (has job roles and locations)")
            else:
                # Keep as not confirmed
                cursor.execute(
                    "UPDATE user_preferences SET preferences_confirmed = FALSE WHERE user_id = %s",
                    (user_id,)
                )
                incomplete_count += 1
                missing = []
                if not has_job_roles:
                    missing.append("job roles")
                if not has_locations:
                    missing.append("locations")
                print(f"  ❌ INCOMPLETE (missing: {', '.join(missing)})")
        
        # Commit all changes
        db.connection.commit()
        
        print(f"\n📊 SUMMARY:")
        print(f"  ✅ Auto-confirmed: {auto_confirmed_count} users")
        print(f"  ❌ Still incomplete: {incomplete_count} users")
        print(f"  📝 Total processed: {len(unconfirmed_users)} users")
        
        # Show new eligible user count
        cursor.execute("""
            SELECT COUNT(*) FROM users u
            JOIN user_preferences up ON u.id = up.user_id
            JOIN conversation_windows cw ON u.id = cw.user_id
            WHERE up.preferences_confirmed = TRUE
            AND cw.window_status = 'active'
            AND cw.last_activity >= CURRENT_TIMESTAMP - INTERVAL '23 hours 30 minutes'
        """)
        
        eligible_count = cursor.fetchone()[0]
        print(f"\n🎯 RESULT: {eligible_count} users now eligible for job delivery")
        
    except Exception as e:
        logger.error(f"❌ Error auto-confirming preferences: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    auto_confirm_existing_preferences()
