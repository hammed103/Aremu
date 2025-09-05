#!/usr/bin/env python3
"""
Embedding Migration Runner
Executes database migrations for embedding-based matching system
"""

import os
import sys
import psycopg2
import logging
from pathlib import Path

# Add the current directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from legacy.database_manager import DatabaseManager

# Set up logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

def run_migration_file(cursor, migration_file: Path) -> bool:
    """Run a single migration file"""
    try:
        logger.info(f"Running migration: {migration_file.name}")
        
        with open(migration_file, 'r') as f:
            migration_sql = f.read()
        
        # Execute the migration
        cursor.execute(migration_sql)
        logger.info(f"✅ Migration {migration_file.name} completed successfully")
        return True
        
    except Exception as e:
        logger.error(f"❌ Migration {migration_file.name} failed: {e}")
        return False

def check_vector_extension(cursor) -> bool:
    """Check if vector extension is available"""
    try:
        cursor.execute("SELECT 1 FROM pg_extension WHERE extname = 'vector'")
        result = cursor.fetchone()
        return result is not None
    except Exception as e:
        logger.error(f"Error checking vector extension: {e}")
        return False

def run_embedding_migrations():
    """Run all embedding-related migrations"""
    
    print("🚀 EMBEDDING SYSTEM MIGRATION")
    print("=" * 50)
    
    try:
        # Connect to database
        db = DatabaseManager()
        cursor = db.connection.cursor()
        
        # Get migrations directory
        migrations_dir = Path(__file__).parent / "database" / "migrations"
        
        if not migrations_dir.exists():
            logger.error(f"Migrations directory not found: {migrations_dir}")
            return False
        
        # Get migration files in order
        migration_files = sorted([
            f for f in migrations_dir.glob("*.sql") 
            if f.name.startswith(("001_", "002_"))
        ])
        
        if not migration_files:
            logger.error("No migration files found")
            return False
        
        logger.info(f"Found {len(migration_files)} migration files")
        
        # Run migrations
        success_count = 0
        for migration_file in migration_files:
            if run_migration_file(cursor, migration_file):
                success_count += 1
            else:
                logger.error(f"Migration failed, stopping at {migration_file.name}")
                break
        
        # Commit all changes
        db.connection.commit()
        
        # Check if vector extension is now available
        if check_vector_extension(cursor):
            logger.info("✅ Vector extension is available")
        else:
            logger.warning("⚠️ Vector extension not found - some features may not work")
        
        # Verify new columns exist
        logger.info("Verifying new columns...")
        
        # Check user_preferences columns
        cursor.execute("""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = 'user_preferences' 
            AND column_name IN ('user_embedding', 'embedding_text', 'embedding_updated_at', 'embedding_version')
            ORDER BY column_name
        """)
        
        user_columns = cursor.fetchall()
        logger.info(f"User preferences embedding columns: {len(user_columns)}/4")
        for column_name, data_type in user_columns:
            logger.info(f"  ✅ {column_name}: {data_type}")
        
        # Check canonical_jobs columns
        cursor.execute("""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = 'canonical_jobs' 
            AND column_name IN ('job_embedding', 'job_embedding_text', 'job_embedding_updated_at', 'embedding_version')
            ORDER BY column_name
        """)
        
        job_columns = cursor.fetchall()
        logger.info(f"Canonical jobs embedding columns: {len(job_columns)}/4")
        for column_name, data_type in job_columns:
            logger.info(f"  ✅ {column_name}: {data_type}")
        
        # Check indexes
        cursor.execute("""
            SELECT indexname 
            FROM pg_indexes 
            WHERE tablename IN ('user_preferences', 'canonical_jobs')
            AND indexname LIKE '%embedding%'
            ORDER BY indexname
        """)
        
        indexes = cursor.fetchall()
        logger.info(f"Embedding indexes created: {len(indexes)}")
        for (index_name,) in indexes:
            logger.info(f"  ✅ {index_name}")
        
        if success_count == len(migration_files):
            print("\n🎉 ALL MIGRATIONS COMPLETED SUCCESSFULLY!")
            print(f"✅ Executed {success_count}/{len(migration_files)} migrations")
            print("✅ Vector extension enabled")
            print("✅ Embedding columns added to user_preferences")
            print("✅ Embedding columns added to canonical_jobs")
            print("✅ Vector indexes created for fast similarity search")
            print("\n🚀 Ready for Phase 2: Embedding Service Creation!")
            return True
        else:
            print(f"\n❌ Migration incomplete: {success_count}/{len(migration_files)} succeeded")
            return False
            
    except Exception as e:
        logger.error(f"❌ Migration failed: {e}")
        return False

if __name__ == "__main__":
    success = run_embedding_migrations()
    if not success:
        sys.exit(1)
