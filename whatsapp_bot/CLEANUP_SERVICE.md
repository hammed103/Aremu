# Automated Cleanup Service

The automated cleanup service automatically maintains the `canonical_jobs` table by removing old jobs and duplicates every 5 hours.

## Features

### 🧹 Old Job Cleanup
- Removes jobs older than 5 days from `canonical_jobs` table
- Handles jobs with NULL `scraped_at` timestamps
- Configurable age threshold

### 🔍 Duplicate Removal
- Identifies duplicates based on:
  - Job title (case-insensitive, trimmed)
  - Company name (case-insensitive, trimmed)
  - Location (case-insensitive, trimmed, handles NULL)
- Keeps the most recent job when duplicates are found
- Uses PostgreSQL window functions for efficient processing

### ⏰ Automated Scheduling
- Runs every 5 hours automatically on Railway
- Background thread with graceful shutdown
- Error handling and retry logic

## Usage

### Manual Cleanup
```bash
# Run manual cleanup with stats
python run_cleanup.py

# Show stats only
python run_cleanup.py stats

# Run cleanup without prompts
python run_cleanup.py cleanup
```

### Test the Service
```bash
python test_cleanup.py
```

### API Endpoints
```bash
# Get cleanup statistics
GET /api/cleanup/stats

# Run manual cleanup
POST /api/cleanup/run
```

## Railway Deployment

The cleanup service is automatically started in production mode:

1. **Integrated with main app**: The service starts when `app.py` runs in production
2. **Railway startup script**: Use `railway_start.py` for explicit control
3. **Environment detection**: Only runs in production (`FLASK_ENV=production`)

## Configuration

### Environment Variables
- `DATABASE_URL`: PostgreSQL connection string
- `FLASK_ENV`: Set to "production" to enable automated cleanup

### Cleanup Settings
- **Old job threshold**: 5 days (configurable in code)
- **Cleanup interval**: 5 hours (configurable in code)
- **Duplicate detection**: Title + Company + Location

## Database Impact

### Performance
- Uses efficient PostgreSQL window functions
- Minimal impact on database performance
- Runs during low-traffic periods

### Safety
- Transaction-based operations
- Rollback on errors
- Detailed logging for monitoring

## Monitoring

### Logs
The service provides detailed logging:
```
🧹 Starting full database cleanup...
🔍 Found 150 duplicate jobs
✅ Removed 150 duplicate jobs
🧹 Cleaning jobs older than 2024-01-01 12:00:00
✅ Cleaned up 500 old jobs
✅ Full cleanup completed successfully
😴 Next cleanup in 5 hours
```

### API Monitoring
```bash
# Check cleanup stats
curl http://localhost:5001/api/cleanup/stats

# Response
{
  "status": "success",
  "stats": {
    "total_jobs": 1000,
    "old_jobs": 200,
    "duplicate_jobs": 50,
    "jobs_after_cleanup": 750
  }
}
```

## Integration

### With Existing Services
The cleanup service integrates seamlessly with:
- **Scraper Service**: Cleans up after scraping operations
- **Job Matcher**: Maintains clean data for matching
- **WhatsApp Bot**: Ensures users get fresh, relevant jobs

### Database Schema
Works with the existing `canonical_jobs` table:
- `id`: Primary key
- `title`: Job title
- `company`: Company name
- `location`: Job location
- `scraped_at`: Timestamp for age-based cleanup

## Troubleshooting

### Common Issues

1. **Service not starting**
   - Check `FLASK_ENV=production`
   - Verify database connection
   - Check logs for initialization errors

2. **Cleanup not running**
   - Verify service is in production mode
   - Check background thread status
   - Review error logs

3. **Database connection issues**
   - Verify `DATABASE_URL` environment variable
   - Check database permissions
   - Test connection manually

### Manual Recovery
If automated cleanup fails:
```bash
# Run manual cleanup
python run_cleanup.py cleanup

# Check database status
python run_cleanup.py stats
```

## Development

### Adding New Cleanup Rules
1. Extend `AutomatedCleanupService` class
2. Add new cleanup methods
3. Update `run_full_cleanup()` method
4. Test with `test_cleanup.py`

### Modifying Schedule
Change the interval in `app.py`:
```python
cleanup_service.start_automated_cleanup(interval_hours=3)  # Every 3 hours
```

### Custom Cleanup Logic
```python
# Example: Custom cleanup for specific conditions
def cleanup_specific_jobs(self):
    cursor = self.connection.cursor()
    cursor.execute("""
        DELETE FROM canonical_jobs 
        WHERE title ILIKE '%test%' 
        AND scraped_at < NOW() - INTERVAL '1 day'
    """)
    self.connection.commit()
```
