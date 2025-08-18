-- Aremu WhatsApp Bot Database Schema
-- User management and conversation history

-- Users table - store user profiles and preferences
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    phone_number VARCHAR(20) UNIQUE NOT NULL,
    name VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_active TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    message_count INTEGER DEFAULT 0,
    is_active BOOLEAN DEFAULT TRUE
);

-- JOB CATEGORIES (What field/industry they want to work in)
CREATE TYPE job_category_enum AS ENUM (
    'technology',
    'healthcare',
    'education',
    'finance',
    'marketing',
    'sales',
    'design',
    'operations',
    'human resources',
    'legal',
    'customer service',
    'hospitality',
    'construction',
    'manufacturing',
    'media',
    'consulting',
    'government',
    'non-profit'
);

-- JOB ROLES (Specific positions within categories)
CREATE TYPE job_role_enum AS ENUM (
    -- Technology
    'frontend developer', 'backend developer', 'fullstack developer',
    'mobile developer', 'data scientist', 'data analyst', 'devops engineer',
    'qa engineer', 'ui/ux designer', 'software engineer', 'cybersecurity specialist',
    'database administrator', 'system administrator', 'technical writer',

    -- Healthcare
    'registered nurse', 'doctor', 'pharmacist', 'medical technician',
    'physiotherapist', 'dentist', 'radiologist', 'lab technician',

    -- Education
    'teacher', 'lecturer', 'professor', 'tutor', 'school administrator',
    'education coordinator', 'curriculum developer',

    -- Finance
    'accountant', 'financial analyst', 'investment banker', 'auditor',
    'tax specialist', 'financial advisor', 'credit analyst', 'bookkeeper',

    -- Marketing & Sales
    'marketing manager', 'digital marketer', 'content marketer', 'seo specialist',
    'sales representative', 'account manager', 'business development',
    'brand manager', 'social media manager',

    -- Design
    'graphic designer', 'web designer', 'product designer', 'interior designer',
    'fashion designer', 'video editor', 'photographer', 'animator',

    -- Operations & Management
    'project manager', 'product manager', 'operations manager', 'supply chain manager',
    'logistics coordinator', 'quality assurance manager', 'business analyst',

    -- Human Resources
    'hr manager', 'recruiter', 'hr coordinator', 'training specialist',
    'compensation analyst', 'employee relations specialist',

    -- Customer Service
    'customer service representative', 'call center agent', 'technical support',
    'customer success manager', 'help desk specialist',

    -- Legal
    'lawyer', 'paralegal', 'legal assistant', 'compliance officer',
    'contract specialist', 'legal advisor',

    -- Others
    'chef', 'waiter', 'security guard', 'driver', 'receptionist',
    'administrative assistant', 'data entry clerk', 'translator'
);

-- WORK ARRANGEMENT (Remote, hybrid, on-site)
CREATE TYPE work_arrangement_enum AS ENUM (
    'remote',
    'hybrid',
    'on-site'
);

-- EMPLOYMENT TYPE (Full-time, part-time, etc.)
CREATE TYPE employment_type_enum AS ENUM (
    'full-time',
    'part-time',
    'contract',
    'internship',
    'freelance',
    'temporary',
    'volunteer'
);

-- EXPERIENCE LEVEL
CREATE TYPE experience_level_enum AS ENUM (
    'entry',        -- 0-2 years
    'junior',       -- 1-3 years
    'mid',          -- 3-5 years
    'senior',       -- 5-8 years
    'lead',         -- 8+ years
    'executive'     -- 10+ years, C-level
);

-- CURRENCY
CREATE TYPE currency_enum AS ENUM (
    'USD',
    'NGN',
    'EUR',
    'GBP',
    'CAD',
    'AUD'
);

-- SALARY PERIOD
CREATE TYPE salary_period_enum AS ENUM (
    'hourly',
    'daily',
    'weekly',
    'monthly',
    'yearly'
);

-- COMPREHENSIVE USER PREFERENCES - Optimized for intelligent job matching
CREATE TABLE IF NOT EXISTS user_preferences (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,

    -- JOB PREFERENCES
    job_categories job_category_enum[],     -- Industries/fields of interest
    job_roles job_role_enum[],              -- Specific positions wanted

    -- WORK ARRANGEMENT & EMPLOYMENT
    work_arrangements work_arrangement_enum[], -- Remote, hybrid, on-site
    employment_types employment_type_enum[],   -- Full-time, part-time, contract

    -- EXPERIENCE & CAREER LEVEL
    experience_level experience_level_enum,
    years_of_experience INTEGER,            -- Actual years of experience

    -- SALARY EXPECTATIONS
    salary_currency currency_enum,
    salary_period salary_period_enum DEFAULT 'monthly',
    salary_min INTEGER,                     -- Minimum expected salary
    salary_max INTEGER,                     -- Maximum expected salary
    salary_negotiable BOOLEAN DEFAULT true,

    -- LOCATION PREFERENCES
    preferred_locations TEXT[],             -- Array of cities/countries
    willing_to_relocate BOOLEAN DEFAULT false,
    max_commute_distance INTEGER,          -- In kilometers

    -- SKILLS & QUALIFICATIONS
    technical_skills TEXT[],               -- Programming languages, tools, etc.
    soft_skills TEXT[],                    -- Communication, leadership, etc.
    certifications TEXT[],                 -- Professional certifications
    education_level TEXT,                  -- Degree level
    languages_spoken TEXT[],               -- English, French, Yoruba, etc.

    -- WORK PREFERENCES
    company_size_preference TEXT[],        -- startup, small, medium, large, enterprise
    industry_preferences TEXT[],           -- fintech, healthtech, e-commerce, etc.
    benefits_priorities TEXT[],            -- health insurance, pension, flexible hours

    -- AVAILABILITY
    available_start_date DATE,
    notice_period_weeks INTEGER DEFAULT 2,

    -- METADATA
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_job_search_date TIMESTAMP,

    -- Ensure one preference record per user
    UNIQUE(user_id)
);

-- Conversation history table - store chat messages
CREATE TABLE IF NOT EXISTS conversations (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    message_type VARCHAR(20) NOT NULL, -- 'user' or 'assistant'
    message_content TEXT NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    session_id VARCHAR(100),         -- Group related messages
    message_order INTEGER DEFAULT 0  -- Order within session
);

-- User sessions table - track conversation sessions
CREATE TABLE IF NOT EXISTS user_sessions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    session_id VARCHAR(100) UNIQUE NOT NULL,
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_message_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    message_count INTEGER DEFAULT 0,
    is_active BOOLEAN DEFAULT TRUE
);

-- Indexes for better performance
CREATE INDEX IF NOT EXISTS idx_users_phone ON users(phone_number);
CREATE INDEX IF NOT EXISTS idx_conversations_user_id ON conversations(user_id);
CREATE INDEX IF NOT EXISTS idx_conversations_timestamp ON conversations(timestamp);
CREATE INDEX IF NOT EXISTS idx_user_sessions_user_id ON user_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_user_sessions_active ON user_sessions(is_active);

-- COMPREHENSIVE INDEXES for lightning-fast job matching
CREATE INDEX IF NOT EXISTS idx_user_preferences_user_id ON user_preferences(user_id);

-- Job preference indexes
CREATE INDEX IF NOT EXISTS idx_user_preferences_job_categories ON user_preferences USING GIN(job_categories);
CREATE INDEX IF NOT EXISTS idx_user_preferences_job_roles ON user_preferences USING GIN(job_roles);
CREATE INDEX IF NOT EXISTS idx_user_preferences_work_arrangements ON user_preferences USING GIN(work_arrangements);
CREATE INDEX IF NOT EXISTS idx_user_preferences_employment_types ON user_preferences USING GIN(employment_types);

-- Experience and salary indexes
CREATE INDEX IF NOT EXISTS idx_user_preferences_experience_level ON user_preferences(experience_level);
CREATE INDEX IF NOT EXISTS idx_user_preferences_years_experience ON user_preferences(years_of_experience);
CREATE INDEX IF NOT EXISTS idx_user_preferences_salary_range ON user_preferences(salary_min, salary_max);
CREATE INDEX IF NOT EXISTS idx_user_preferences_salary_currency ON user_preferences(salary_currency);

-- Location indexes
CREATE INDEX IF NOT EXISTS idx_user_preferences_locations ON user_preferences USING GIN(preferred_locations);
CREATE INDEX IF NOT EXISTS idx_user_preferences_relocate ON user_preferences(willing_to_relocate);

-- Skills indexes
CREATE INDEX IF NOT EXISTS idx_user_preferences_technical_skills ON user_preferences USING GIN(technical_skills);
CREATE INDEX IF NOT EXISTS idx_user_preferences_soft_skills ON user_preferences USING GIN(soft_skills);
CREATE INDEX IF NOT EXISTS idx_user_preferences_certifications ON user_preferences USING GIN(certifications);
CREATE INDEX IF NOT EXISTS idx_user_preferences_languages ON user_preferences USING GIN(languages_spoken);

-- Company and industry preferences
CREATE INDEX IF NOT EXISTS idx_user_preferences_company_size ON user_preferences USING GIN(company_size_preference);
CREATE INDEX IF NOT EXISTS idx_user_preferences_industries ON user_preferences USING GIN(industry_preferences);

-- Availability indexes
CREATE INDEX IF NOT EXISTS idx_user_preferences_start_date ON user_preferences(available_start_date);
CREATE INDEX IF NOT EXISTS idx_user_preferences_last_search ON user_preferences(last_job_search_date);

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Triggers to auto-update timestamps
CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_user_preferences_updated_at BEFORE UPDATE ON user_preferences
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
