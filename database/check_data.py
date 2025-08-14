#!/usr/bin/env python3
"""
Check what data we have in the database
"""

import psycopg2

def main():
    print("📊 Checking Raw Jobs Database")
    print("=" * 30)
    
    # Connection
    db_url = "postgresql://postgres.upnvhpgaljazlsoryfgj:prAlkIpbQDqOZtOj@aws-0-us-east-1.pooler.supabase.com:6543/postgres"
    
    try:
        conn = psycopg2.connect(db_url)
        
        with conn.cursor() as cur:
            # Get counts by source
            cur.execute("SELECT source, COUNT(*) FROM raw_jobs GROUP BY source ORDER BY COUNT(*) DESC")
            results = cur.fetchall()
            
            print("📈 Jobs by source:")
            total = 0
            for source, count in results:
                print(f"   {source}: {count:,} jobs")
                total += count
            
            print(f"   Total: {total:,} jobs")
            
            # Show sample LinkedIn jobs
            print(f"\n📝 Sample LinkedIn jobs:")
            cur.execute("""
                SELECT raw_data->>'title', raw_data->>'company', raw_data->>'location'
                FROM raw_jobs 
                WHERE source = 'linkedin'
                LIMIT 5
            """)
            
            for title, company, location in cur.fetchall():
                print(f"   • {title} at {company} ({location})")
            
            # Show sample generic jobs if any
            cur.execute("SELECT COUNT(*) FROM raw_jobs WHERE source = 'generic_jobs'")
            generic_count = cur.fetchone()[0]
            
            if generic_count > 0:
                print(f"\n📝 Sample generic jobs:")
                cur.execute("""
                    SELECT raw_data->>'title', raw_data->>'company'
                    FROM raw_jobs 
                    WHERE source = 'generic_jobs'
                    LIMIT 5
                """)
                
                for title, company in cur.fetchall():
                    print(f"   • {title} at {company}")
            
            print(f"\n✅ Database check completed!")
        
    except Exception as e:
        print(f"❌ Check failed: {e}")
        
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    main()
