import psycopg2
import sys

def check_raw_jobs_table():
    """Check the current structure of raw_jobs table"""
    try:
        conn = psycopg2.connect(
            "postgresql://postgres.upnvhpgaljazlsoryfgj:prAlkIpbQDqOZtOj@aws-0-us-east-1.pooler.supabase.com:6543/postgres"
        )
        
        with conn.cursor() as cur:
            # Check table structure
            print("=== RAW_JOBS TABLE STRUCTURE ===")
            cur.execute("""
                SELECT column_name, data_type, is_nullable, column_default
                FROM information_schema.columns 
                WHERE table_name = 'raw_jobs'
                ORDER BY ordinal_position;
            """)
            
            columns = cur.fetchall()
            if not columns:
                print("❌ raw_jobs table does not exist!")
                return
                
            for col in columns:
                print(f"  {col[0]}: {col[1]} (nullable: {col[2]}, default: {col[3]})")
            
            print("\n=== CONSTRAINTS AND INDEXES ===")
            # Check constraints
            cur.execute("""
                SELECT conname, contype, pg_get_constraintdef(oid)
                FROM pg_constraint 
                WHERE conrelid = 'raw_jobs'::regclass;
            """)
            
            constraints = cur.fetchall()
            if constraints:
                for constraint in constraints:
                    print(f"  {constraint[0]} ({constraint[1]}): {constraint[2]}")
            else:
                print("  No constraints found!")
            
            # Check indexes
            cur.execute("""
                SELECT indexname, indexdef
                FROM pg_indexes 
                WHERE tablename = 'raw_jobs';
            """)
            
            indexes = cur.fetchall()
            if indexes:
                print("\n=== INDEXES ===")
                for index in indexes:
                    print(f"  {index[0]}: {index[1]}")
            else:
                print("  No indexes found!")
                
        conn.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    check_raw_jobs_table()
