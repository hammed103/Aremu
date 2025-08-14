#!/usr/bin/env python3
"""
Import All Jobs - LinkedIn + Generic CSV
Clean and simple approach to import everything
"""

import pandas as pd
import psycopg2
import json
import time
import os

def import_csv_file(conn, file_path, source_name, batch_size=50):
    """Import a CSV file in batches"""
    print(f"\n📥 Importing {source_name} from {file_path}")
    
    if not os.path.exists(file_path):
        print(f"❌ File not found: {file_path}")
        return 0
    
    try:
        # Get total rows first
        total_rows = sum(1 for _ in open(file_path)) - 1  # -1 for header
        print(f"📊 Total rows to import: {total_rows}")
        
        imported = 0
        batch_num = 0
        
        # Read in chunks
        for chunk in pd.read_csv(file_path, chunksize=batch_size):
            batch_num += 1
            print(f"📦 Processing batch {batch_num} ({len(chunk)} rows)...")
            
            with conn.cursor() as cur:
                for _, row in chunk.iterrows():
                    try:
                        # Convert to dict and handle NaN
                        data = row.to_dict()
                        data = {k: (v if pd.notna(v) else None) for k, v in data.items()}
                        
                        # Extract job ID for deduplication
                        if source_name == 'linkedin':
                            job_id = data.get('job_id', f'linkedin_{imported}')
                        else:
                            job_id = data.get('id', f'{source_name}_{imported}')
                        
                        # Insert row with conflict handling
                        cur.execute("""
                            INSERT INTO raw_jobs (source, source_job_id, raw_data)
                            VALUES (%s, %s, %s)
                            ON CONFLICT (source, source_job_id) DO NOTHING
                        """, (source_name, str(job_id), json.dumps(data)))
                        
                        imported += 1
                        
                    except Exception as e:
                        print(f"   ⚠️  Skipped row: {str(e)[:50]}...")
            
            print(f"   ✅ Batch {batch_num}: {imported} total processed")
            
            # Small delay between batches
            time.sleep(0.5)
        
        print(f"✅ {source_name} completed: {imported} jobs processed")
        return imported
        
    except Exception as e:
        print(f"❌ Failed to import {source_name}: {e}")
        return 0

def main():
    print("🚀 Import ALL Jobs to Raw Database")
    print("=" * 40)
    
    # Connection
    db_url = "postgresql://postgres.upnvhpgaljazlsoryfgj:prAlkIpbQDqOZtOj@aws-0-us-east-1.pooler.supabase.com:6543/postgres"
    
    try:
        conn = psycopg2.connect(db_url)
        conn.autocommit = True
        print("✅ Connected to database")
        
        # Create table with proper schema
        print("🏗️  Setting up raw_jobs table...")
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS raw_jobs (
                    id SERIAL PRIMARY KEY,
                    source TEXT NOT NULL,
                    source_job_id TEXT,
                    raw_data JSONB NOT NULL,
                    created_at TIMESTAMP DEFAULT NOW(),
                    UNIQUE(source, source_job_id)
                )
            """)
            
            # Create index for better performance
            cur.execute("""
                CREATE INDEX IF NOT EXISTS idx_raw_jobs_source 
                ON raw_jobs(source)
            """)
        print("✅ Table ready")
        
        # Files to import
        files_to_import = [
            {
                'path': '../scraper/linkedin/nigeria_all_jobs.csv',
                'source': 'linkedin',
                'batch_size': 50
            },
            {
                'path': '../jobs.csv',
                'source': 'generic_jobs',
                'batch_size': 100
            }
        ]
        
        total_imported = 0
        
        # Import each file
        for file_info in files_to_import:
            imported = import_csv_file(
                conn,
                file_info['path'],
                file_info['source'],
                file_info['batch_size']
            )
            total_imported += imported
        
        # Show final statistics
        print(f"\n📊 Final Results:")
        print("=" * 30)
        
        with conn.cursor() as cur:
            # Get counts by source
            cur.execute("SELECT source, COUNT(*) FROM raw_jobs GROUP BY source ORDER BY COUNT(*) DESC")
            results = cur.fetchall()
            
            for source, count in results:
                print(f"   {source}: {count:,} jobs")
            
            # Get total
            cur.execute("SELECT COUNT(*) FROM raw_jobs")
            total = cur.fetchone()[0]
            print(f"   Total: {total:,} jobs")
            
            # Show sample data
            print(f"\n📝 Sample jobs:")
            cur.execute("""
                SELECT source, raw_data->>'title', raw_data->>'company' 
                FROM raw_jobs 
                ORDER BY created_at DESC
                LIMIT 5
            """)
            
            for source, title, company in cur.fetchall():
                title = title[:50] if title else 'No title'
                company = company[:30] if company else 'No company'
                print(f"   • [{source}] {title} at {company}")
        
        print(f"\n🎉 Import completed successfully!")
        print(f"📊 Total processed: {total_imported:,} jobs")
        print(f"\n💡 Next steps:")
        print(f"1. Check your Supabase dashboard")
        print(f"2. Query: SELECT * FROM raw_jobs LIMIT 10;")
        print(f"3. Build canonical jobs processor")
        
    except Exception as e:
        print(f"❌ Import failed: {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        if 'conn' in locals():
            conn.close()
            print("🔌 Connection closed")

if __name__ == "__main__":
    main()
