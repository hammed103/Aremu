import psycopg2
import sys

def fix_raw_jobs_constraint():
    """Add the missing unique constraint to raw_jobs table"""
    try:
        conn = psycopg2.connect(
            "postgresql://postgres.upnvhpgaljazlsoryfgj:prAlkIpbQDqOZtOj@aws-0-us-east-1.pooler.supabase.com:6543/postgres"
        )
        
        with conn.cursor() as cur:
            print("🔧 Adding unique constraint to raw_jobs table...")
            
            # Add the unique constraint that the ON CONFLICT clause expects
            cur.execute("""
                ALTER TABLE raw_jobs 
                ADD CONSTRAINT raw_jobs_source_job_id_unique 
                UNIQUE (source, source_job_id);
            """)
            
            conn.commit()
            print("✅ Successfully added unique constraint: (source, source_job_id)")
            
            # Verify the constraint was added
            cur.execute("""
                SELECT conname, contype, pg_get_constraintdef(oid)
                FROM pg_constraint 
                WHERE conrelid = 'raw_jobs'::regclass
                AND contype = 'u';
            """)
            
            constraints = cur.fetchall()
            print("\n=== UNIQUE CONSTRAINTS ===")
            for constraint in constraints:
                print(f"  {constraint[0]}: {constraint[2]}")
                
        conn.close()
        print("\n🎉 Fix complete! Your scrapers should now work without the ON CONFLICT error.")
        
    except psycopg2.errors.DuplicateTable as e:
        print("⚠️  Constraint already exists - this is fine!")
    except Exception as e:
        print(f"❌ Error: {e}")
        if "duplicate key value violates unique constraint" in str(e):
            print("\n🚨 There are duplicate records in your table!")
            print("You'll need to clean up duplicates first. Would you like me to help with that?")

if __name__ == "__main__":
    fix_raw_jobs_constraint()
