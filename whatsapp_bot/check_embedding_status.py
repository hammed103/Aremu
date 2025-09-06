#!/usr/bin/env python3
"""
Check embedding generation status
"""

import sys
import os
from pathlib import Path

# Add current directory to path
sys.path.insert(0, '.')

# Load .env file
env_file = Path('.env')
if env_file.exists():
    with open(env_file, 'r') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                os.environ[key.strip()] = value.strip()

from legacy.database_manager import DatabaseManager

def main():
    print('📊 Checking embedding generation status...')

    # Initialize database
    db = DatabaseManager()
    cursor = db.connection.cursor()

    # Check job embedding status
    cursor.execute('''
        SELECT 
            COUNT(*) as total_jobs,
            COUNT(job_embedding) as jobs_with_embeddings,
            COUNT(*) - COUNT(job_embedding) as jobs_without_embeddings
        FROM canonical_jobs
        WHERE scraped_at >= CURRENT_DATE - INTERVAL '60 days'
    ''')

    total, with_embeddings, without_embeddings = cursor.fetchone()
    coverage = (with_embeddings/total*100) if total > 0 else 0

    print(f'\n🧠 Job Embeddings Status:')
    print(f'  Total jobs (last 60 days): {total}')
    print(f'  Jobs with embeddings: {with_embeddings}')
    print(f'  Jobs without embeddings: {without_embeddings}')
    print(f'  Coverage: {coverage:.1f}%')

    # Check user embedding status
    cursor.execute('''
        SELECT 
            COUNT(*) as total_users,
            COUNT(user_embedding) as users_with_embeddings,
            COUNT(*) - COUNT(user_embedding) as users_without_embeddings
        FROM user_preferences
        WHERE job_roles IS NOT NULL
    ''')

    total_users, with_user_embeddings, without_user_embeddings = cursor.fetchone()
    user_coverage = (with_user_embeddings/total_users*100) if total_users > 0 else 0

    print(f'\n👥 User Embeddings Status:')
    print(f'  Total users with preferences: {total_users}')
    print(f'  Users with embeddings: {with_user_embeddings}')
    print(f'  Users without embeddings: {without_user_embeddings}')
    print(f'  Coverage: {user_coverage:.1f}%')

    # Show recent embedding generation activity
    cursor.execute('''
        SELECT 
            DATE(scraped_at) as date,
            COUNT(*) as total_jobs,
            COUNT(job_embedding) as jobs_with_embeddings
        FROM canonical_jobs
        WHERE scraped_at >= CURRENT_DATE - INTERVAL '7 days'
        GROUP BY DATE(scraped_at)
        ORDER BY date DESC
    ''')

    daily_stats = cursor.fetchall()
    print(f'\n📅 Daily Embedding Coverage (Last 7 days):')
    for date, total_jobs, jobs_with_embeddings in daily_stats:
        daily_coverage = (jobs_with_embeddings/total_jobs*100) if total_jobs > 0 else 0
        print(f'  {date}: {jobs_with_embeddings}/{total_jobs} jobs ({daily_coverage:.1f}%)')

    print(f'\n✅ Status check complete!')

if __name__ == "__main__":
    main()
