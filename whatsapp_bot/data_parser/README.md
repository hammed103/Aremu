# Job Data Parser

Transforms raw job data from different sources (LinkedIn, JobSpy) into a canonical normalized format with optional AI enhancement.

## Files

- `job_data_parser.py` - Main parser with AI enhancement
- `parser_test.py` - Test the parser
- `README.md` - Documentation

## Features

✅ **Multi-Source Parsing** - Handles LinkedIn and JobSpy data formats  
✅ **Canonical Schema** - Normalizes all jobs into consistent format  
✅ **AI Enhancement** - Uses OpenAI to extract missing fields  
✅ **Smart Field Mapping** - Intelligent parsing of locations, salaries, etc.  
✅ **Duplicate Prevention** - Automatic deduplication  
✅ **Comprehensive Schema** - 25+ fields for complete job information  

## Canonical Schema

The parser creates a `canonical_jobs` table with these fields:

### Core Information
- `title` - Job title
- `company` - Company name
- `location` - Job location
- `job_url` - Direct link to job posting
- `description` - Full job description

### Job Details
- `employment_type` - Full-time, Part-time, Contract, etc.
- `experience_level` - Entry, Mid, Senior, Executive
- `salary_min/max` - Salary range
- `salary_currency` - Currency (defaults to NGN)

### Skills & Requirements
- `required_skills` - Array of required skills
- `preferred_skills` - Array of preferred skills
- `education_requirements` - Education level needed
- `years_experience_min/max` - Experience range

### Company Information
- `company_size` - Startup, Small, Medium, Large, Enterprise
- `industry` - Industry sector
- `company_description` - About the company

### Location Details
- `city` - Extracted city
- `state` - Nigerian state
- `country` - Defaults to Nigeria
- `remote_allowed` - Boolean for remote work

### Metadata
- `posted_date` - When job was posted
- `source` - linkedin, jobspy, etc.
- `ai_enhanced` - Whether AI was used
- `created_at/updated_at` - Timestamps

## Usage

### Quick Test (No AI)
```bash
python parser_test.py
```

### Full Parsing with AI
```bash
python job_data_parser.py
# Enter your OpenAI API key when prompted
# Choose processing option
```

### Processing Options
1. **Process all sources** - Parse all LinkedIn and JobSpy jobs
2. **Process LinkedIn only** - Parse only LinkedIn jobs
3. **Process JobSpy only** - Parse only JobSpy jobs
4. **Limited batch** - Process 100 jobs for testing

## AI Enhancement

When you provide an OpenAI API key, the parser will:

✅ **Extract Skills** - Identify required and preferred skills  
✅ **Determine Experience** - Infer years of experience needed  
✅ **Classify Company** - Determine company size and industry  
✅ **Education Requirements** - Extract education needs  

**AI Prompt Example:**
```
Analyze this Nigerian job posting and extract/infer:
- required_skills: Array of key technical skills
- preferred_skills: Array of nice-to-have skills
- education_requirements: Education level needed
- years_experience_min/max: Experience range
- company_size: Startup/Small/Medium/Large/Enterprise
- industry: Industry sector
```

## Field Mapping

### LinkedIn Jobs
- `title` → `title`
- `company` → `company`
- `location` → `location` + parsed `city`/`state`
- `job_url` → `job_url`
- `description` → `description`
- `job_id` → `source_job_id`

### JobSpy Jobs
- `title` → `title`
- `company` → `company`
- `location` → `location` + parsed `city`/`state`
- `job_url` → `job_url`
- `description` → `description`
- `job_type` → `employment_type`
- `min_amount/max_amount` → `salary_min/max`
- `currency` → `salary_currency`

## Smart Parsing

### Location Extraction
- **Cities:** Lagos, Abuja, Port Harcourt, Kano, etc.
- **States:** Maps cities to Nigerian states
- **Remote Detection:** Identifies remote work opportunities

### Experience Level Detection
- **Entry:** intern, internship, graduate, entry, junior
- **Senior:** senior, lead, principal, staff
- **Executive:** manager, director, head, chief
- **Mid:** Everything else

### Salary Parsing
- Handles multiple currencies (NGN, USD, etc.)
- Removes symbols and formatting
- Converts to decimal format

## Expected Results

**Processing 1,000 raw jobs:**
- ✅ 950+ successfully parsed
- ✅ All fields properly mapped
- ✅ Smart location/salary extraction
- ✅ AI enhancement (if enabled)
- ✅ Duplicate prevention working

**Database Impact:**
- Creates `canonical_jobs` table
- Indexes for performance
- Unique constraints prevent duplicates
- Links back to original raw data

Perfect for creating a clean, searchable job database! 🎯
