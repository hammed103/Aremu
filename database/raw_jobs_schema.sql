-- Raw Jobs Table Schema
-- This table stores unprocessed job data from multiple sources

CREATE TABLE IF NOT EXISTS raw_jobs (
    id SERIAL PRIMARY KEY,
    source VARCHAR(100) NOT NULL,  -- 'linkedin', 'indeed', 'glassdoor', etc.
    source_job_id VARCHAR(255),    -- Original job ID from source
    raw_data JSONB NOT NULL,       -- Complete raw job data as JSON
    source_url VARCHAR(500),       -- Original job posting URL
    scraped_at TIMESTAMP,          -- When the job was scraped
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    processed BOOLEAN DEFAULT FALSE,  -- Whether this has been processed to canonical
    processing_errors TEXT,        -- Any errors during processing
    
    -- Indexes for performance
    UNIQUE(source, source_job_id)  -- Prevent duplicates from same source
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_raw_jobs_source ON raw_jobs(source);
CREATE INDEX IF NOT EXISTS idx_raw_jobs_processed ON raw_jobs(processed);
CREATE INDEX IF NOT EXISTS idx_raw_jobs_created_at ON raw_jobs(created_at);
CREATE INDEX IF NOT EXISTS idx_raw_jobs_source_job_id ON raw_jobs(source_job_id);

-- Add GIN index for JSONB queries
CREATE INDEX IF NOT EXISTS idx_raw_jobs_raw_data ON raw_jobs USING GIN(raw_data);

-- Canonical Jobs Table Schema (normalized/standardized)
CREATE TABLE IF NOT EXISTS canonical_jobs (
    id SERIAL PRIMARY KEY,
    raw_job_id INTEGER REFERENCES raw_jobs(id),
    
    -- Standard job fields
    title VARCHAR(500) NOT NULL,
    company VARCHAR(300),
    location VARCHAR(300),
    country VARCHAR(100),
    city VARCHAR(100),
    state_province VARCHAR(100),
    remote_type VARCHAR(50),  -- 'remote', 'hybrid', 'onsite', 'flexible'
    
    -- Job details
    job_type VARCHAR(50),     -- 'full-time', 'part-time', 'contract', 'internship'
    experience_level VARCHAR(50), -- 'entry', 'mid', 'senior', 'executive'
    salary_min DECIMAL(12,2),
    salary_max DECIMAL(12,2),
    salary_currency VARCHAR(10),
    salary_period VARCHAR(20), -- 'hourly', 'monthly', 'yearly'
    
    -- Content
    description TEXT,
    requirements TEXT,
    benefits TEXT,
    
    -- Metadata
    posted_date DATE,
    expires_date DATE,
    application_url VARCHAR(500),
    company_size VARCHAR(50),
    industry VARCHAR(100),
    
    -- Processing metadata
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    confidence_score DECIMAL(3,2), -- How confident we are in the normalization
    
    -- Prevent duplicates
    UNIQUE(raw_job_id)
);

-- Create indexes for canonical jobs
CREATE INDEX IF NOT EXISTS idx_canonical_jobs_title ON canonical_jobs(title);
CREATE INDEX IF NOT EXISTS idx_canonical_jobs_company ON canonical_jobs(company);
CREATE INDEX IF NOT EXISTS idx_canonical_jobs_location ON canonical_jobs(location);
CREATE INDEX IF NOT EXISTS idx_canonical_jobs_posted_date ON canonical_jobs(posted_date);
CREATE INDEX IF NOT EXISTS idx_canonical_jobs_job_type ON canonical_jobs(job_type);
CREATE INDEX IF NOT EXISTS idx_canonical_jobs_remote_type ON canonical_jobs(remote_type);

-- Add full-text search
CREATE INDEX IF NOT EXISTS idx_canonical_jobs_description_fts 
ON canonical_jobs USING GIN(to_tsvector('english', description));

-- Source tracking table
CREATE TABLE IF NOT EXISTS data_sources (
    id SERIAL PRIMARY KEY,
    source_name VARCHAR(100) UNIQUE NOT NULL,
    source_type VARCHAR(50), -- 'scraper', 'api', 'manual', 'import'
    last_sync TIMESTAMP,
    total_records INTEGER DEFAULT 0,
    active BOOLEAN DEFAULT TRUE,
    config JSONB, -- Source-specific configuration
    created_at TIMESTAMP DEFAULT NOW()
);

-- Insert default sources
INSERT INTO data_sources (source_name, source_type) VALUES 
('linkedin', 'scraper'),
('indeed', 'scraper'),
('glassdoor', 'scraper'),
('manual_import', 'manual')
ON CONFLICT (source_name) DO NOTHING;
