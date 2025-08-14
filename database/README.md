# Raw Jobs Database System

This system imports job data from multiple CSV sources into a PostgreSQL database with two main tables:

1. **`raw_jobs`** - Stores unprocessed job data from all sources
2. **`canonical_jobs`** - Stores normalized/standardized job data

## Setup

### 1. Install Dependencies
```bash
cd database
pip install -r requirements.txt
```

### 2. Configure Database
Edit `config.py` and replace `YOUR_ACTUAL_PASSWORD` with your Supabase password:

```python
DATABASE_CONFIG = {
    'url': 'postgresql://postgres:YOUR_ACTUAL_PASSWORD@db.upnvhpgaljazlsoryfgj.supabase.co:5432/postgres',
    # ...
}
```

### 3. Update Data Source Paths
In `config.py`, verify the file paths in `DATA_SOURCES` are correct:

```python
DATA_SOURCES = [
    {
        'name': 'linkedin_nigeria',
        'type': 'linkedin',
        'file_path': '/Users/hammedbalogun/Desktop/JOBS/scraper/linkedin/nigeria_all_jobs.csv',
        # ...
    },
    {
        'name': 'generic_jobs', 
        'type': 'generic',
        'file_path': '/Users/hammedbalogun/Desktop/JOBS/jobs.csv',
        # ...
    }
]
```

## Usage

### Import All Data Sources
```bash
python import_jobs.py
```

This will:
1. Create the database schema (tables, indexes)
2. Import LinkedIn jobs from `nigeria_all_jobs.csv`
3. Import generic jobs from `jobs.csv`
4. Show import statistics

### Manual Import
```python
from raw_jobs_importer import RawJobsImporter

importer = RawJobsImporter("postgresql://...")
importer.connect()
importer.setup_database()

# Import LinkedIn jobs
count = importer.import_linkedin_jobs("path/to/linkedin_jobs.csv")

# Import generic CSV
count = importer.import_generic_jobs("path/to/jobs.csv", "source_name")

importer.disconnect()
```

## Database Schema

### raw_jobs Table
- `id` - Primary key
- `source` - Data source name ('linkedin', 'indeed', etc.)
- `source_job_id` - Original job ID from source
- `raw_data` - Complete job data as JSONB
- `source_url` - Original job posting URL
- `scraped_at` - When job was scraped
- `processed` - Whether converted to canonical format
- `processing_errors` - Any processing errors

### canonical_jobs Table
- `id` - Primary key
- `raw_job_id` - Reference to raw_jobs
- `title` - Standardized job title
- `company` - Company name
- `location` - Job location
- `description` - Job description
- `salary_min/max` - Salary range
- `job_type` - 'full-time', 'part-time', etc.
- `remote_type` - 'remote', 'hybrid', 'onsite'
- And many more standardized fields...

## Data Sources Supported

### LinkedIn Jobs
- Expects columns: `job_id`, `title`, `company`, `location`, `all_job_details`, `job_url`, `scraped_at`
- Automatically handles LinkedIn-specific data format

### Generic CSV
- Automatically detects common column names
- Maps fields like `title`, `company`, `location`, `description`
- Creates unique IDs if none found

## Next Steps

1. **Import your data**: Run `python import_jobs.py`
2. **Review raw data**: Query `raw_jobs` table to verify imports
3. **Build canonical processor**: Create logic to convert raw_jobs → canonical_jobs
4. **Set up automation**: Schedule regular imports for new data

## Example Queries

```sql
-- Check import status
SELECT source, COUNT(*) as total, 
       COUNT(*) FILTER (WHERE processed = true) as processed
FROM raw_jobs GROUP BY source;

-- View raw LinkedIn job
SELECT raw_data->>'title' as title, 
       raw_data->>'company' as company
FROM raw_jobs WHERE source = 'linkedin' LIMIT 5;

-- Search job descriptions
SELECT raw_data->>'title', raw_data->>'company'
FROM raw_jobs 
WHERE raw_data->>'all_job_details' ILIKE '%python%';
```
