#!/usr/bin/env python3
"""
Reorganize canonical_jobs table columns for better structure
"""

import psycopg2


def reorganize_canonical_jobs():
    """Reorganize canonical_jobs table columns logically"""
    print("🔧 Reorganizing canonical_jobs table columns")
    print("=" * 60)

    try:
        db_url = "postgresql://postgres.upnvhpgaljazlsoryfgj:prAlkIpbQDqOZtOj@aws-0-us-east-1.pooler.supabase.com:6543/postgres"
        conn = psycopg2.connect(db_url)
        cur = conn.cursor()

        # Define the logical column order
        new_column_order = [
            # 1. CORE IDENTITY
            "id",
            "source",
            "source_job_id",
            "raw_job_id",
            # 2. BASIC JOB INFO
            "title",
            "company",
            "description",
            "job_url",
            "job_url_direct",
            # 3. LOCATION & WORK ARRANGEMENT
            "location",
            "city",
            "state",
            "country",
            "is_remote",
            "remote_allowed",
            "work_arrangement",
            # 4. EMPLOYMENT & LEVEL
            "employment_type",
            "job_type",
            "job_function",
            "job_level",
            "seniority_level",
            "experience_level",
            "years_experience",
            "years_experience_min",
            "years_experience_max",
            # 5. COMPENSATION
            "salary_min",
            "salary_max",
            "salary_currency",
            "min_amount",
            "max_amount",
            "currency",
            "benefits",
            # 6. SKILLS & REQUIREMENTS
            "required_skills",
            "preferred_skills",
            "skills",
            "education_requirements",
            "industry",
            "industries",
            # 7. CONTACT & APPLICATION
            "email",
            "emails",
            "whatsapp_number",
            "phones",
            "application_mode",
            "application_deadline",
            # 8. COMPANY DETAILS
            "company_size",
            "company_industry",
            "company_description",
            "company_url",
            "company_logo",
            "company_addresses",
            "company_num_employees",
            "company_revenue",
            "ceo_name",
            "ceo_photo_url",
            "logo_photo_url",
            "banner_photo_url",
            # 9. AI ENHANCED FIELDS
            "ai_enhanced",
            "ai_enhancement_date",
            "ai_extraction",
            "ai_summary",
            # AI Job Classification
            "ai_job_titles",
            "ai_employment_type",
            "ai_job_function",
            "ai_job_level",
            "ai_industry",
            # AI Location
            "ai_city",
            "ai_state",
            "ai_country",
            "ai_work_arrangement",
            "ai_remote_allowed",
            # AI Compensation
            "ai_salary_min",
            "ai_salary_max",
            "ai_salary_currency",
            "ai_compensation_summary",
            "ai_benefits",
            # AI Skills & Requirements
            "ai_required_skills",
            "ai_preferred_skills",
            "ai_education_requirements",
            "ai_years_experience_min",
            "ai_years_experience_max",
            # AI Contact & Application
            "ai_email",
            "ai_whatsapp_number",
            "ai_application_modes",
            "ai_application_deadline",
            "ai_posted_date",
            # 10. METADATA & DATES
            "posted_date",
            "date_posted",
            "created_at",
            "updated_at",
            "site",
        ]

        print(f"📊 Reorganizing {len(new_column_order)} columns into logical groups...")

        # Create new table with reorganized columns
        print("\n1️⃣ Creating new table with logical column order...")

        # Get current table definition
        cur.execute(
            """
            SELECT column_name, data_type, is_nullable, column_default
            FROM information_schema.columns 
            WHERE table_name = 'canonical_jobs' 
            ORDER BY ordinal_position
        """
        )

        current_columns = {row[0]: row for row in cur.fetchall()}

        # Build CREATE TABLE statement with new order
        create_columns = []
        for col_name in new_column_order:
            if col_name in current_columns:
                col_name_db, data_type, is_nullable, default = current_columns[col_name]

                # Handle array types
                if data_type == "ARRAY":
                    data_type = "TEXT[]"
                elif data_type == "timestamp without time zone":
                    data_type = "TIMESTAMP"
                elif data_type == "character varying":
                    data_type = "TEXT"

                nullable = "NULL" if is_nullable == "YES" else "NOT NULL"
                default_clause = f" DEFAULT {default}" if default else ""

                create_columns.append(
                    f"    {col_name} {data_type} {nullable}{default_clause}"
                )

        create_table_sql = f"""
        CREATE TABLE canonical_jobs_new (
{','.join(create_columns)}
        )
        """

        cur.execute(create_table_sql)
        print("   ✅ New table structure created")

        # Copy data to new table
        print("\n2️⃣ Copying data to reorganized table...")

        existing_columns = [col for col in new_column_order if col in current_columns]
        columns_list = ", ".join(existing_columns)

        copy_sql = f"""
        INSERT INTO canonical_jobs_new ({columns_list})
        SELECT {columns_list}
        FROM canonical_jobs
        """

        cur.execute(copy_sql)

        # Get count to verify
        cur.execute("SELECT COUNT(*) FROM canonical_jobs_new")
        new_count = cur.fetchone()[0]

        cur.execute("SELECT COUNT(*) FROM canonical_jobs")
        old_count = cur.fetchone()[0]

        print(f"   ✅ Copied {new_count} rows (original: {old_count})")

        if new_count == old_count:
            # Replace old table
            print("\n3️⃣ Replacing old table with reorganized version...")

            cur.execute("ALTER TABLE canonical_jobs RENAME TO canonical_jobs_old")
            cur.execute("ALTER TABLE canonical_jobs_new RENAME TO canonical_jobs")

            # Recreate primary key and indexes
            cur.execute("ALTER TABLE canonical_jobs ADD PRIMARY KEY (id)")
            cur.execute(
                "CREATE INDEX IF NOT EXISTS idx_canonical_jobs_source ON canonical_jobs(source, source_job_id)"
            )
            cur.execute(
                "CREATE INDEX IF NOT EXISTS idx_canonical_jobs_ai_enhanced ON canonical_jobs(ai_enhanced)"
            )
            cur.execute(
                "CREATE INDEX IF NOT EXISTS idx_canonical_jobs_created_at ON canonical_jobs(created_at)"
            )

            print("   ✅ Table replacement completed")

            conn.commit()

            # Show new organization
            print("\n4️⃣ New column organization:")
            print("=" * 50)

            groups = [
                ("CORE IDENTITY", new_column_order[0:4]),
                ("BASIC JOB INFO", new_column_order[4:9]),
                ("LOCATION & WORK", new_column_order[9:16]),
                ("EMPLOYMENT & LEVEL", new_column_order[16:25]),
                ("COMPENSATION", new_column_order[25:31]),
                ("SKILLS & REQUIREMENTS", new_column_order[31:37]),
                ("CONTACT & APPLICATION", new_column_order[37:43]),
                ("COMPANY DETAILS", new_column_order[43:55]),
                ("AI ENHANCED", new_column_order[55:85]),
                ("METADATA", new_column_order[85:]),
            ]

            for group_name, columns in groups:
                print(f"\n📋 {group_name}:")
                for col in columns:
                    if col in current_columns:
                        print(f"   ✅ {col}")
                    else:
                        print(f"   ❌ {col} (missing)")

            print(f"\n🎉 Reorganization completed successfully!")
            print(
                f"   📊 Total columns: {len([col for col in new_column_order if col in current_columns])}"
            )
            print(f"   🔄 Logical grouping applied")
            print(f"   📈 Much better organization for development!")

        else:
            print("❌ Row count mismatch - rolling back")
            conn.rollback()

        conn.close()

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    reorganize_canonical_jobs()
