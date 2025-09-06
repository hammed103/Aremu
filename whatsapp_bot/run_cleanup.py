#!/usr/bin/env python3
"""
Manual cleanup runner for testing and one-time cleanup
"""

import sys
import os

# Add the current directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.automated_cleanup_service import AutomatedCleanupService
from utils.logger import setup_logger

logger = setup_logger(__name__)


def run_manual_cleanup():
    """Run a manual cleanup operation"""
    logger.info("🧹 Starting manual cleanup operation...")
    
    try:
        # Create cleanup service
        cleanup_service = AutomatedCleanupService()
        
        # Run full cleanup
        success = cleanup_service.run_full_cleanup()
        
        if success:
            logger.info("✅ Manual cleanup completed successfully!")
        else:
            logger.error("❌ Manual cleanup completed with errors")
            
        return success
        
    except Exception as e:
        logger.error(f"❌ Error during manual cleanup: {e}")
        return False


def show_cleanup_stats():
    """Show statistics about jobs that would be cleaned"""
    logger.info("📊 Showing cleanup statistics...")
    
    try:
        cleanup_service = AutomatedCleanupService()
        cursor = cleanup_service.connection.cursor()
        
        # Count total jobs
        cursor.execute("SELECT COUNT(*) FROM canonical_jobs")
        total_jobs = cursor.fetchone()[0]
        
        # Count old jobs (5 days)
        cursor.execute(
            """
            SELECT COUNT(*) 
            FROM canonical_jobs 
            WHERE scraped_at < NOW() - INTERVAL '5 days' 
            OR scraped_at IS NULL
            """
        )
        old_jobs = cursor.fetchone()[0]
        
        # Count potential duplicates
        cursor.execute(
            """
            WITH duplicates AS (
                SELECT 
                    id,
                    ROW_NUMBER() OVER (
                        PARTITION BY 
                            LOWER(TRIM(title)), 
                            LOWER(TRIM(company)), 
                            LOWER(TRIM(COALESCE(location, '')))
                        ORDER BY scraped_at DESC, id DESC
                    ) as row_num
                FROM canonical_jobs
                WHERE title IS NOT NULL 
                AND company IS NOT NULL
            )
            SELECT COUNT(*) 
            FROM duplicates 
            WHERE row_num > 1
            """
        )
        duplicate_jobs = cursor.fetchone()[0]
        
        # Show stats
        logger.info(f"📊 Cleanup Statistics:")
        logger.info(f"   Total jobs: {total_jobs}")
        logger.info(f"   Old jobs (>5 days): {old_jobs}")
        logger.info(f"   Duplicate jobs: {duplicate_jobs}")
        logger.info(f"   Jobs after cleanup: {total_jobs - old_jobs - duplicate_jobs}")
        
        return {
            'total': total_jobs,
            'old': old_jobs,
            'duplicates': duplicate_jobs,
            'remaining': total_jobs - old_jobs - duplicate_jobs
        }
        
    except Exception as e:
        logger.error(f"❌ Error getting cleanup stats: {e}")
        return None


def main():
    """Main function"""
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command == "stats":
            show_cleanup_stats()
        elif command == "cleanup":
            run_manual_cleanup()
        elif command == "help":
            print("Usage:")
            print("  python run_cleanup.py stats    - Show cleanup statistics")
            print("  python run_cleanup.py cleanup  - Run manual cleanup")
            print("  python run_cleanup.py help     - Show this help")
        else:
            print(f"Unknown command: {command}")
            print("Use 'python run_cleanup.py help' for usage information")
    else:
        # Default: show stats then ask if user wants to run cleanup
        stats = show_cleanup_stats()
        
        if stats and (stats['old'] > 0 or stats['duplicates'] > 0):
            print(f"\n⚠️  Found {stats['old']} old jobs and {stats['duplicates']} duplicates")
            response = input("Do you want to run cleanup? (y/N): ").strip().lower()
            
            if response == 'y':
                run_manual_cleanup()
            else:
                print("Cleanup cancelled.")
        else:
            print("✅ No cleanup needed!")


if __name__ == "__main__":
    main()
