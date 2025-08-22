#!/usr/bin/env python3
"""
Clean up old jobs from raw_jobs table
Deletes jobs that are older than 3 days
"""

import sys
import os

sys.path.append("/Users/hammedbalogun/Desktop/JOBS/whatsapp_bot")

from database_manager import DatabaseManager
from datetime import datetime, timedelta


def cleanup_old_canonical_jobs():
    """Delete jobs from canonical_jobs table that are older than 5 days"""

    db = DatabaseManager()
    conn = db.get_connection()
    cursor = conn.cursor()

    print("=== CLEANING UP OLD CANONICAL JOBS ===")

    try:
        # Calculate cutoff date (5 days ago)
        cutoff_date = datetime.now() - timedelta(days=3)
        print(f"Cutoff date: {cutoff_date}")

        # First, check how many jobs will be deleted
        cursor.execute(
            """
            SELECT COUNT(*) as old_jobs_count
            FROM canonical_jobs
            WHERE posted_date < %s::date
               OR posted_date IS NULL
        """,
            (cutoff_date,),
        )

        old_jobs_count = cursor.fetchone()[0]
        print(f"Canonical jobs older than 5 days: {old_jobs_count}")

        if old_jobs_count == 0:
            print("✅ No old canonical jobs to delete!")
            return

        # Check total jobs before deletion
        cursor.execute("SELECT COUNT(*) as total_jobs FROM canonical_jobs")
        total_jobs_before = cursor.fetchone()[0]
        print(f"Total canonical jobs before cleanup: {total_jobs_before}")

        # Show some examples of jobs that will be deleted
        cursor.execute(
            """
            SELECT id, title, company, posted_date
            FROM canonical_jobs
            WHERE posted_date < %s::date
               OR posted_date IS NULL
            ORDER BY posted_date DESC NULLS LAST
            LIMIT 5
        """,
            (cutoff_date,),
        )

        sample_jobs = cursor.fetchall()
        print(f"\nSample canonical jobs to be deleted:")
        for job in sample_jobs:
            job_id, title, company, posted_date = job
            print(f"  ID {job_id}: {title} at {company} (Posted: {posted_date})")

        # Ask for confirmation
        print(
            f"\n⚠️  About to delete {old_jobs_count} canonical jobs (older than 5 days + NULL dates)."
        )
        confirmation = input("Continue? (y/N): ").strip().lower()

        if confirmation != "y":
            print("❌ Canonical jobs cleanup cancelled.")
            return

        # Delete old jobs
        print("\n🗑️  Deleting old canonical jobs...")
        cursor.execute(
            """
            DELETE FROM canonical_jobs
            WHERE posted_date < %s::date
               OR posted_date IS NULL
        """,
            (cutoff_date,),
        )

        deleted_count = cursor.rowcount
        conn.commit()

        # Check total jobs after deletion
        cursor.execute("SELECT COUNT(*) as total_jobs FROM canonical_jobs")
        total_jobs_after = cursor.fetchone()[0]

        print(f"\n✅ CANONICAL JOBS CLEANUP COMPLETE!")
        print(f"Canonical jobs deleted: {deleted_count}")
        print(f"Canonical jobs before: {total_jobs_before}")
        print(f"Canonical jobs after: {total_jobs_after}")
        print(f"Space saved: {deleted_count} canonical job records")

        # Show date range of remaining jobs
        cursor.execute(
            """
            SELECT
                MIN(posted_date) as oldest_job,
                MAX(posted_date) as newest_job,
                COUNT(*) as remaining_jobs
            FROM canonical_jobs
            WHERE posted_date IS NOT NULL
        """
        )

        result = cursor.fetchone()
        if result and result[2] > 0:
            oldest_job, newest_job, remaining_jobs = result
            print(f"\nRemaining canonical jobs date range:")
            print(f"  Oldest: {oldest_job}")
            print(f"  Newest: {newest_job}")
            print(f"  Total: {remaining_jobs} jobs")
        else:
            print("\n📭 No canonical jobs remaining.")

    except Exception as e:
        print(f"❌ Error during canonical jobs cleanup: {e}")
        conn.rollback()
    finally:
        cursor.close()
        conn.close()


def cleanup_old_raw_jobs():
    """Delete jobs from raw_jobs table that are older than 3 days"""

    db = DatabaseManager()
    conn = db.get_connection()
    cursor = conn.cursor()

    print("=== CLEANING UP OLD RAW JOBS ===")

    try:
        # Calculate cutoff date (5 days ago)
        cutoff_date = datetime.now() - timedelta(days=3)
        print(f"Cutoff date: {cutoff_date}")

        # First, check how many jobs will be deleted
        cursor.execute(
            """
            SELECT COUNT(*) as old_jobs_count
            FROM raw_jobs
            WHERE (raw_data->>'date_posted')::date < %s::date
               OR raw_data->>'date_posted' IS NULL
        """,
            (cutoff_date,),
        )

        old_jobs_count = cursor.fetchone()[0]
        print(f"Jobs older than 5 days: {old_jobs_count}")

        if old_jobs_count == 0:
            print("✅ No old jobs to delete!")
            return

        # Check total jobs before deletion
        cursor.execute("SELECT COUNT(*) as total_jobs FROM raw_jobs")
        total_jobs_before = cursor.fetchone()[0]
        print(f"Total jobs before cleanup: {total_jobs_before}")

        # Show some examples of jobs that will be deleted
        cursor.execute(
            """
            SELECT id, raw_data->>'title' as title, raw_data->>'company' as company, raw_data->>'date_posted' as date_posted
            FROM raw_jobs
            WHERE (raw_data->>'date_posted')::date < %s::date
               OR raw_data->>'date_posted' IS NULL
            ORDER BY (raw_data->>'date_posted')::date DESC NULLS LAST
            LIMIT 5
        """,
            (cutoff_date,),
        )

        sample_jobs = cursor.fetchall()
        print(f"\nSample jobs to be deleted:")
        for job in sample_jobs:
            job_id, title, company, date_posted = job
            print(f"  ID {job_id}: {title} at {company} (Posted: {date_posted})")

        # Ask for confirmation
        print(
            f"\n⚠️  About to delete {old_jobs_count} jobs (older than 5 days + NULL dates)."
        )
        confirmation = input("Continue? (y/N): ").strip().lower()

        if confirmation != "y":
            print("❌ Cleanup cancelled.")
            return

        # Delete old jobs
        print("\n🗑️  Deleting old jobs...")
        cursor.execute(
            """
            DELETE FROM raw_jobs
            WHERE (raw_data->>'date_posted')::date < %s::date
               OR raw_data->>'date_posted' IS NULL
        """,
            (cutoff_date,),
        )

        deleted_count = cursor.rowcount
        conn.commit()

        # Check total jobs after deletion
        cursor.execute("SELECT COUNT(*) as total_jobs FROM raw_jobs")
        total_jobs_after = cursor.fetchone()[0]

        print(f"\n✅ CLEANUP COMPLETE!")
        print(f"Jobs deleted: {deleted_count}")
        print(f"Jobs before: {total_jobs_before}")
        print(f"Jobs after: {total_jobs_after}")
        print(f"Space saved: {deleted_count} job records")

        # Show date range of remaining jobs
        cursor.execute(
            """
            SELECT 
                MIN(scraped_at) as oldest_job,
                MAX(scraped_at) as newest_job,
                COUNT(*) as remaining_jobs
            FROM raw_jobs
        """
        )

        result = cursor.fetchone()
        if result and result[2] > 0:
            oldest_job, newest_job, remaining_jobs = result
            print(f"\nRemaining jobs date range:")
            print(f"  Oldest: {oldest_job}")
            print(f"  Newest: {newest_job}")
            print(f"  Total: {remaining_jobs} jobs")
        else:
            print("\n📭 No jobs remaining in raw_jobs table.")

    except Exception as e:
        print(f"❌ Error during cleanup: {e}")
        conn.rollback()
    finally:
        cursor.close()
        conn.close()


def show_canonical_jobs_stats():
    """Show statistics about canonical_jobs table"""

    db = DatabaseManager()
    conn = db.get_connection()
    cursor = conn.cursor()

    print("=== CANONICAL JOBS STATISTICS ===")

    try:
        # Total jobs
        cursor.execute("SELECT COUNT(*) as total_jobs FROM canonical_jobs")
        total_jobs = cursor.fetchone()[0]
        print(f"Total jobs in canonical_jobs: {total_jobs}")

        if total_jobs == 0:
            print("📭 No jobs in canonical_jobs table.")
            return

        # Date range
        cursor.execute(
            """
            SELECT
                MIN(posted_date) as oldest_job,
                MAX(posted_date) as newest_job
            FROM canonical_jobs
            WHERE posted_date IS NOT NULL
        """
        )

        result = cursor.fetchone()
        if result and result[0]:
            oldest_job, newest_job = result
            print(f"Date range: {oldest_job} to {newest_job}")
        else:
            print("No jobs with valid posted_date")

        # Jobs by age
        cutoff_date = datetime.now() - timedelta(days=3)

        cursor.execute(
            """
            SELECT
                COUNT(CASE WHEN posted_date >= %s::date THEN 1 END) as recent_jobs,
                COUNT(CASE WHEN posted_date < %s::date OR posted_date IS NULL THEN 1 END) as old_jobs
            FROM canonical_jobs
        """,
            (cutoff_date, cutoff_date),
        )

        recent_jobs, old_jobs = cursor.fetchone()
        print(f"Recent canonical jobs (≤5 days): {recent_jobs}")
        print(f"Old canonical jobs (>5 days + NULL): {old_jobs}")

    except Exception as e:
        print(f"❌ Error getting canonical jobs stats: {e}")
    finally:
        cursor.close()
        conn.close()


def show_raw_jobs_stats():
    """Show statistics about raw_jobs table"""

    db = DatabaseManager()
    conn = db.get_connection()
    cursor = conn.cursor()

    print("=== RAW JOBS STATISTICS ===")

    try:
        # Total jobs
        cursor.execute("SELECT COUNT(*) as total_jobs FROM raw_jobs")
        total_jobs = cursor.fetchone()[0]
        print(f"Total jobs in raw_jobs: {total_jobs}")

        if total_jobs == 0:
            print("📭 No jobs in raw_jobs table.")
            return

        # Date range
        cursor.execute(
            """
            SELECT
                MIN((raw_data->>'date_posted')::date) as oldest_job,
                MAX((raw_data->>'date_posted')::date) as newest_job
            FROM raw_jobs
            WHERE raw_data->>'date_posted' IS NOT NULL
        """
        )

        oldest_job, newest_job = cursor.fetchone()
        print(f"Date range: {oldest_job} to {newest_job}")

        # Jobs by age
        cutoff_date = datetime.now() - timedelta(days=3)

        cursor.execute(
            """
            SELECT
                COUNT(CASE WHEN (raw_data->>'date_posted')::date >= %s::date THEN 1 END) as recent_jobs,
                COUNT(CASE WHEN (raw_data->>'date_posted')::date < %s::date THEN 1 END) as old_jobs
            FROM raw_jobs
            WHERE raw_data->>'date_posted' IS NOT NULL
        """,
            (cutoff_date, cutoff_date),
        )

        recent_jobs, old_jobs = cursor.fetchone()
        print(f"Recent jobs (≤5 days): {recent_jobs}")
        print(f"Old jobs (>5 days): {old_jobs}")

        # Jobs by source
        cursor.execute(
            """
            SELECT source, COUNT(*) as job_count
            FROM raw_jobs
            GROUP BY source
            ORDER BY job_count DESC
        """
        )

        sources = cursor.fetchall()
        print(f"\nJobs by source:")
        for source, count in sources:
            print(f"  {source}: {count} jobs")

    except Exception as e:
        print(f"❌ Error getting stats: {e}")
    finally:
        cursor.close()
        conn.close()


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "stats":
        show_canonical_jobs_stats()
        print("\n" + "=" * 50)
        show_raw_jobs_stats()
    else:
        # Show stats for both tables
        show_canonical_jobs_stats()
        print("\n" + "=" * 50)
        show_raw_jobs_stats()
        print("\n" + "=" * 50)

        # Run cleanup for both tables
        cleanup_old_canonical_jobs()
        print("\n" + "=" * 50)
        cleanup_old_raw_jobs()
