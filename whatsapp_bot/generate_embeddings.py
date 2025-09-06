#!/usr/bin/env python3
"""
Generate embeddings for existing jobs in batches
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

from services.embedding_generator import EmbeddingGenerator
from legacy.database_manager import DatabaseManager
import time

def main():
    print('🧠 Starting embedding generation for existing jobs...')

    # Initialize services
    db = DatabaseManager()
    openai_key = os.getenv('OPENAI_API_KEY')
    if not openai_key:
        print('❌ OPENAI_API_KEY not found')
        return

    generator = EmbeddingGenerator(db.connection, openai_key)

    # Check current status
    cursor = db.connection.cursor()
    cursor.execute('''
        SELECT 
            COUNT(*) as total_jobs,
            COUNT(job_embedding) as jobs_with_embeddings,
            COUNT(*) - COUNT(job_embedding) as jobs_without_embeddings
        FROM canonical_jobs
        WHERE scraped_at >= CURRENT_DATE - INTERVAL '60 days'
    ''')

    total, with_embeddings, without_embeddings = cursor.fetchone()
    print(f'📊 Current status:')
    print(f'  Total jobs (last 60 days): {total}')
    print(f'  Jobs with embeddings: {with_embeddings}')
    print(f'  Jobs without embeddings: {without_embeddings}')

    if without_embeddings == 0:
        print('✅ All jobs already have embeddings!')
        return

    # Run multiple batches
    batch_size = 100
    max_batches = 20  # Process up to 2000 jobs
    total_processed = 0

    for batch_num in range(1, max_batches + 1):
        print(f'\n🚀 Running batch {batch_num}/{max_batches}...')
        
        try:
            processed_count = generator.generate_missing_job_embeddings(batch_size=batch_size)
            total_processed += processed_count
            
            print(f'✅ Batch {batch_num}: Processed {processed_count} jobs')
            
            if processed_count == 0:
                print('🎉 No more jobs to process!')
                break
                
            # Check current status
            cursor.execute('''
                SELECT 
                    COUNT(*) as total_jobs,
                    COUNT(job_embedding) as jobs_with_embeddings
                FROM canonical_jobs
                WHERE scraped_at >= CURRENT_DATE - INTERVAL '60 days'
            ''')
            
            total, with_embeddings = cursor.fetchone()
            coverage = (with_embeddings/total*100) if total > 0 else 0
            print(f'📊 Progress: {with_embeddings}/{total} jobs ({coverage:.1f}% coverage)')
            
            # Small delay to avoid rate limiting
            time.sleep(2)
            
        except Exception as e:
            print(f'❌ Error in batch {batch_num}: {e}')
            import traceback
            traceback.print_exc()
            break

    print(f'\n🎉 Embedding generation complete!')
    print(f'Total jobs processed: {total_processed}')

    # Final status
    cursor.execute('''
        SELECT 
            COUNT(*) as total_jobs,
            COUNT(job_embedding) as jobs_with_embeddings,
            COUNT(*) - COUNT(job_embedding) as jobs_without_embeddings
        FROM canonical_jobs
        WHERE scraped_at >= CURRENT_DATE - INTERVAL '60 days'
    ''')

    final_total, final_with_embeddings, final_without = cursor.fetchone()
    print(f'\n📊 Final status:')
    print(f'  Total jobs: {final_total}')
    print(f'  Jobs with embeddings: {final_with_embeddings}')
    print(f'  Jobs without embeddings: {final_without}')
    print(f'  Coverage: {(final_with_embeddings/final_total*100):.1f}%')

if __name__ == "__main__":
    main()
