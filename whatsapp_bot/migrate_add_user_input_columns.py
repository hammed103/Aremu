#!/usr/bin/env python3
"""
Database migration: Add user input preservation columns
Adds user_job_input and user_location_input columns to preserve original user input
"""

import os
import sys

# Add the current directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from legacy.database_manager import DatabaseManager

def migrate_add_user_input_columns():
    """Add columns to preserve original user input"""
    
    print("🔄 Database Migration: Adding User Input Preservation Columns")
    print("=" * 70)
    
    db = DatabaseManager()
    cursor = db.connection.cursor()
    
    try:
        # Add user_job_input column
        print("\n1. Adding user_job_input column...")
        cursor.execute("""
            ALTER TABLE user_preferences 
            ADD COLUMN IF NOT EXISTS user_job_input TEXT
        """)
        print("   ✅ user_job_input column added")
        
        # Add user_location_input column
        print("\n2. Adding user_location_input column...")
        cursor.execute("""
            ALTER TABLE user_preferences 
            ADD COLUMN IF NOT EXISTS user_location_input TEXT
        """)
        print("   ✅ user_location_input column added")
        
        # Commit changes
        db.connection.commit()
        print("\n✅ Migration completed successfully!")
        
        # Verify columns exist
        print("\n3. Verifying new columns...")
        cursor.execute("""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = 'user_preferences' 
            AND column_name IN ('user_job_input', 'user_location_input')
            ORDER BY column_name
        """)
        
        columns = cursor.fetchall()
        for column_name, data_type in columns:
            print(f"   ✅ {column_name}: {data_type}")
        
        if len(columns) == 2:
            print("\n🎉 All columns successfully added!")
        else:
            print(f"\n⚠️ Expected 2 columns, found {len(columns)}")
            
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        db.connection.rollback()
        return False
    
    return True

if __name__ == "__main__":
    success = migrate_add_user_input_columns()
    if success:
        print("\n🚀 Ready to preserve user input!")
    else:
        print("\n💥 Migration failed - check errors above")
