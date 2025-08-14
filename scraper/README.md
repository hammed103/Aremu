# Nigeria Comprehensive Job Scraper

A Python-based scraper that continuously monitors ALL jobs in Nigerian cities + remote positions every 10 minutes.

## 🚀 Key Features

- **🇳🇬 Comprehensive Nigeria Coverage**: Scrapes ALL jobs in Lagos, Abuja, Port Harcourt, Kano, and more
- **🌐 Remote Job Detection**: Specifically searches for remote opportunities for Nigerians
- **⏰ Continuous Monitoring**: Runs every 10 minutes automatically
- **🧹 Clean Job Content**: Extracts only relevant job information without LinkedIn UI clutter
- **🔄 Duplicate Prevention**: Automatically filters out duplicate job postings
- **📊 Multiple Export Formats**: CSV, JSON, and summary reports
- **⚙️ Fully Configurable**: Easy to customize locations, keywords, and timing
- **📝 Comprehensive Logging**: Track all scraping activity

## 🛠️ Quick Setup

1. **Install dependencies:**
```bash
pip install -r requirements.txt
```

2. **Test the scraper:**
```bash
python3 test_nigeria_scraper.py
```

3. **Run continuous scraping:**
```bash
python3 continuous_nigeria_scraper.py
```

## 📋 Usage Options

### Option 1: Continuous Scraping (Recommended)
Automatically scrapes ALL jobs every 10 minutes:

```bash
python3 continuous_nigeria_scraper.py
# Choose 'c' for continuous mode
```

### Option 2: One-Time Scraping
Run once for testing or manual collection:

```bash
python3 continuous_nigeria_scraper.py
# Choose 'o' for one-time mode
```

### Option 3: Custom Configuration
Edit `nigeria_config.py` to customize:
- Cities to scrape
- Keywords to search
- Scraping frequency
- Output settings

```python
# Example: Add more cities
NIGERIAN_LOCATIONS = {
    "Nigeria": "105365761",
    "Lagos, Nigeria": "90009706",
    "Abuja, Nigeria": "90009707",
    "Your City, Nigeria": "FIND_GEO_ID",  # Add your city
}

# Example: Change scraping frequency
SCRAPING_CONFIG = {
    "scrape_interval_minutes": 5,  # Every 5 minutes instead of 10
    "max_results_per_search": 200,  # More jobs per search
}
```

## Configuration

### Search Parameters

- **keywords**: Job search keywords (e.g., "Python Developer", "Data Scientist")
- **location**: Location to search in (e.g., "Nigeria", "Lagos, Nigeria")
- **geo_id**: Geographic ID for the location (auto-detected for common locations)
- **time_filter**: Filter by posting date
  - `past_24_hours`: Jobs posted in the last 24 hours
  - `past_week`: Jobs posted in the last week
  - `past_month`: Jobs posted in the last month (default)
  - `any_time`: All jobs regardless of posting date
- **max_results**: Maximum number of jobs to scrape (default: 100)
- **delay**: Delay between requests in seconds (default: 2.0)

### Available Locations

The scraper includes geo IDs for common locations:

- Nigeria: 105365761
- Lagos, Nigeria: 90009706
- Abuja, Nigeria: 90009707
- Port Harcourt, Nigeria: 106808692
- Kano, Nigeria: 106808693
- United States: 103644278
- United Kingdom: 101165590
- Canada: 101174742
- Germany: 101282230
- France: 105015875

## Output Format

### CSV Output
The CSV file contains the following columns:
- `job_id`: Unique job identifier
- `title`: Job title
- `company`: Company name
- `location`: Job location
- `posted_date`: Date when the job was posted
- `job_url`: Direct link to the job posting
- `scraped_at`: Timestamp when the job was scraped

### JSON Output
The JSON file contains the same information in a structured format suitable for further processing.

### Detailed Scraping Output
When using detailed scraping (`--fetch-details` or `DetailedLinkedInScraper`), additional fields are included:

**Enhanced Fields:**
- `all_job_details`: Clean job content without LinkedIn UI elements or meta information
- `details_fetched`: Boolean indicating if detailed info was successfully retrieved
- `detail_fetch_timestamp`: When the detailed content was fetched
- `page_url`: URL of the job detail page
- `content_length`: Length of the extracted content

**Note:** The detailed scraper now returns only clean job content, removing all LinkedIn UI elements, navigation, meta tags, and other clutter. This provides focused, AI-ready job information perfect for analysis.

## Rate Limiting

The scraper includes built-in rate limiting to avoid being blocked by LinkedIn:
- Default delay of 2 seconds between requests
- Configurable delay parameter
- Proper headers and user agent to mimic browser behavior

## Important Notes

1. **Respect LinkedIn's Terms of Service**: This scraper is for educational and research purposes. Make sure to comply with LinkedIn's terms of service and robots.txt.

2. **Rate Limiting**: Always use appropriate delays between requests to avoid being blocked.

3. **Cookie Updates**: The cookies and headers in the configuration may need to be updated periodically. If you encounter authentication errors, you may need to update these values.

4. **Legal Compliance**: Ensure your use of this scraper complies with applicable laws and regulations regarding web scraping and data collection.

## Troubleshooting

### Common Issues

1. **403 Forbidden Errors**: Update the cookies and headers in `config.py`
2. **No Jobs Found**: Check if the location geo ID is correct
3. **Timeout Errors**: Increase the delay between requests
4. **Parsing Errors**: LinkedIn may have changed their HTML structure

### Getting Fresh Cookies

If you encounter authentication issues:

1. Open LinkedIn in your browser
2. Go to the jobs search page
3. Open browser developer tools (F12)
4. Go to Network tab and refresh the page
5. Find a request to the jobs API
6. Copy the cookies and headers from the request
7. Update the values in `config.py`

## License

This project is for educational purposes only. Please respect LinkedIn's terms of service and use responsibly.
