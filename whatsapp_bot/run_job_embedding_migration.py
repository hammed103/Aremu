#!/usr/bin/env python3
"""
Run only the job embedding migration (002)
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

def run_job_embedding_migration():
    """Run the job embedding migration"""
    
    print("🚀 JOB EMBEDDING MIGRATION")
    print("=" * 40)
    
    try:
        # Connect to database
        db = DatabaseManager()
        cursor = db.connection.cursor()
        
        # Read and execute the migration
        migration_file = Path(__file__).parent / "database" / "migrations" / "002_add_job_embeddings.sql"
        
        with open(migration_file, 'r') as f:
            migration_sql = f.read()
        
        logger.info("Running job embedding migration...")
        cursor.execute(migration_sql)
        db.connection.commit()
        
        logger.info("✅ Job embedding migration completed successfully")
        
        # Verify columns exist
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
        
        print("\n🎉 JOB EMBEDDING MIGRATION COMPLETED!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Migration failed: {e}")
        return False

if __name__ == "__main__":
    success = run_job_embedding_migration()
    if not success:
        sys.exit(1)
