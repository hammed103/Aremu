# Nigeria JobSpy Scraper

Clean, focused JobSpy scraper for Nigerian jobs with direct database integration.

## Files

- `jobspy_scraper.py` - Main scraper (saves directly to raw_jobs table)
- `jobspy_test.py` - Test the scraper
- `run_jobspy.py` - Simple runner script
- `requirements.txt` - Dependencies

## Features

✅ **Direct Database Integration** - Saves to raw_jobs table
✅ **Proxy Support** - Uses HydraProxy for reliable scraping
✅ **Duplicate Prevention** - Automatic deduplication
✅ **Nigerian Focus** - Optimized for Nigeria job market
✅ **Multiple Sources** - Indeed, LinkedIn, Google Jobs

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Test scraper
python jobspy_test.py

# Run full scraping
python jobspy_scraper.py

# Or use the runner
python run_jobspy.py
```

## Configuration

The scraper includes:
- **Proxy**: HydraProxy US servers for reliable access
- **Rate limiting**: 3-second delays between searches
- **Locations**: Major Nigerian cities (Lagos, Abuja, etc.)
- **Search terms**: Comprehensive job categories
- **Results**: 100 jobs per search, last 7 days

## Output

Jobs are saved directly to the `raw_jobs` table with:
- Automatic duplicate prevention
- Full job data in JSONB format
- Source tracking and timestamps
- Real-time progress logging

Expected results: 5,000-15,000 unique Nigerian jobs.
