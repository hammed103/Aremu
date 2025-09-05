-- Migration 002: Add Job Embeddings to canonical_jobs
-- This migration adds embedding columns to canonical_jobs table for semantic job matching

-- Add embedding columns to canonical_jobs
ALTER TABLE canonical_jobs
ADD COLUMN IF NOT EXISTS job_embedding vector(1536),
ADD COLUMN IF NOT EXISTS job_embedding_text TEXT,
ADD COLUMN IF NOT EXISTS job_embedding_updated_at TIMESTAMP DEFAULT NOW(),
ADD COLUMN IF NOT EXISTS embedding_version INTEGER DEFAULT 1;

-- Create vector index for fast similarity search
-- Using ivfflat index with cosine distance for optimal performance
-- Lists = 1000 for larger job dataset
CREATE INDEX IF NOT EXISTS idx_canonical_jobs_embedding 
    ON canonical_jobs USING ivfflat (job_embedding vector_cosine_ops)
    WITH (lists = 1000);

-- Add index for recent jobs with embeddings (for performance)
CREATE INDEX IF NOT EXISTS idx_canonical_jobs_recent_with_embedding
    ON canonical_jobs (posted_date DESC) 
    WHERE job_embedding IS NOT NULL;

-- Add index for jobs without embeddings (for batch processing)
CREATE INDEX IF NOT EXISTS idx_canonical_jobs_no_embedding
    ON canonical_jobs (id)
    WHERE job_embedding IS NULL
    AND title IS NOT NULL;

-- Add index for embedding metadata
CREATE INDEX IF NOT EXISTS idx_canonical_jobs_embedding_updated 
    ON canonical_jobs (job_embedding_updated_at DESC) 
    WHERE job_embedding IS NOT NULL;
