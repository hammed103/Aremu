#!/usr/bin/env python3
"""
Script to check what contact information is available in jobs
"""

import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), "whatsapp_bot"))

from database_manager import DatabaseManager


def check_contact_info():
    """Check what contact information is available in jobs"""
    try:
        db = DatabaseManager()
        conn = db.get_connection()
        cursor = conn.cursor()

        print("=== JOB CONTACT INFORMATION ANALYSIS ===\n")

        # Total jobs
        cursor.execute("SELECT COUNT(*) FROM canonical_jobs")
        total_jobs = cursor.fetchone()[0]
        print(f"📊 Total jobs in database: {total_jobs}")

        # Jobs with job_url
        cursor.execute(
            "SELECT COUNT(*) FROM canonical_jobs WHERE job_url IS NOT NULL AND job_url != ''"
        )
        jobs_with_url = cursor.fetchone()[0]
        print(
            f"🔗 Jobs with job_url: {jobs_with_url} ({jobs_with_url/total_jobs*100:.1f}%)"
        )

        # Jobs with email
        cursor.execute(
            "SELECT COUNT(*) FROM canonical_jobs WHERE email IS NOT NULL AND email != ''"
        )
        jobs_with_email = cursor.fetchone()[0]
        print(
            f"📧 Jobs with email: {jobs_with_email} ({jobs_with_email/total_jobs*100:.1f}%)"
        )

        # Jobs with ai_email
        cursor.execute(
            "SELECT COUNT(*) FROM canonical_jobs WHERE ai_email IS NOT NULL AND ai_email != ''"
        )
        jobs_with_ai_email = cursor.fetchone()[0]
        print(
            f"🤖 Jobs with ai_email: {jobs_with_ai_email} ({jobs_with_ai_email/total_jobs*100:.1f}%)"
        )

        # Jobs with whatsapp_number
        cursor.execute(
            "SELECT COUNT(*) FROM canonical_jobs WHERE whatsapp_number IS NOT NULL AND whatsapp_number != ''"
        )
        jobs_with_whatsapp = cursor.fetchone()[0]
        print(
            f"📱 Jobs with whatsapp_number: {jobs_with_whatsapp} ({jobs_with_whatsapp/total_jobs*100:.1f}%)"
        )

        # Jobs with ai_whatsapp_number
        cursor.execute(
            "SELECT COUNT(*) FROM canonical_jobs WHERE ai_whatsapp_number IS NOT NULL AND ai_whatsapp_number != ''"
        )
        jobs_with_ai_whatsapp = cursor.fetchone()[0]
        print(
            f"🤖 Jobs with ai_whatsapp_number: {jobs_with_ai_whatsapp} ({jobs_with_ai_whatsapp/total_jobs*100:.1f}%)"
        )

        # Jobs with ANY contact info
        cursor.execute(
            """
            SELECT COUNT(*) FROM canonical_jobs 
            WHERE (job_url IS NOT NULL AND job_url != '') 
               OR (email IS NOT NULL AND email != '')
               OR (ai_email IS NOT NULL AND ai_email != '')
               OR (whatsapp_number IS NOT NULL AND whatsapp_number != '')
               OR (ai_whatsapp_number IS NOT NULL AND ai_whatsapp_number != '')
        """
        )
        jobs_with_any_contact = cursor.fetchone()[0]
        print(
            f"✅ Jobs with ANY contact info: {jobs_with_any_contact} ({jobs_with_any_contact/total_jobs*100:.1f}%)"
        )

        # Jobs with NO contact info
        jobs_without_contact = total_jobs - jobs_with_any_contact
        print(
            f"❌ Jobs with NO contact info: {jobs_without_contact} ({jobs_without_contact/total_jobs*100:.1f}%)"
        )

        print("\n=== SAMPLE JOBS WITH CONTACT INFO ===")

        # Show sample jobs with contact info
        cursor.execute(
            """
            SELECT id, title, company, job_url, email, ai_email, whatsapp_number, ai_whatsapp_number, source
            FROM canonical_jobs 
            WHERE (job_url IS NOT NULL AND job_url != '') 
               OR (email IS NOT NULL AND email != '')
               OR (ai_email IS NOT NULL AND ai_email != '')
               OR (whatsapp_number IS NOT NULL AND whatsapp_number != '')
               OR (ai_whatsapp_number IS NOT NULL AND ai_whatsapp_number != '')
            ORDER BY created_at DESC
            LIMIT 5
        """
        )

        jobs_with_contact = cursor.fetchall()

        for i, job in enumerate(jobs_with_contact, 1):
            print(f"\n{i}. {job['title']} - {job['company']}")
            print(f"   🔗 URL: {job['job_url'] or 'None'}")
            print(f"   📧 Email: {job['email'] or 'None'}")
            print(f"   🤖 AI Email: {job['ai_email'] or 'None'}")
            print(f"   📱 WhatsApp: {job['whatsapp_number'] or 'None'}")
            print(f"   🤖 AI WhatsApp: {job['ai_whatsapp_number'] or 'None'}")
            print(f"   🏷️  Source: {job['source']}")

        print("\n=== SAMPLE JOBS WITHOUT CONTACT INFO ===")

        # Show sample jobs without contact info
        cursor.execute(
            """
            SELECT id, title, company, source, created_at
            FROM canonical_jobs 
            WHERE (job_url IS NULL OR job_url = '') 
              AND (email IS NULL OR email = '')
              AND (ai_email IS NULL OR ai_email = '')
              AND (whatsapp_number IS NULL OR whatsapp_number = '')
              AND (ai_whatsapp_number IS NULL OR ai_whatsapp_number = '')
            ORDER BY created_at DESC
            LIMIT 5
        """
        )

        jobs_without_contact = cursor.fetchall()

        for i, job in enumerate(jobs_without_contact, 1):
            print(f"\n{i}. {job['title']} - {job['company']}")
            print(f"   🏷️  Source: {job['source']}")
            print(f"   📅 Created: {job['created_at']}")

        conn.close()

    except Exception as e:
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    check_contact_info()
