-- Migration 001: Add Vector Extension and User Embeddings
-- This migration adds the PostgreSQL vector extension and embedding columns to user_preferences

-- Enable vector extension for embeddings
CREATE EXTENSION IF NOT EXISTS vector;

-- Add embedding columns to user_preferences
ALTER TABLE user_preferences
ADD COLUMN IF NOT EXISTS user_embedding vector(1536),
ADD COLUMN IF NOT EXISTS embedding_text TEXT,
ADD COLUMN IF NOT EXISTS embedding_updated_at TIMESTAMP DEFAULT NOW(),
ADD COLUMN IF NOT EXISTS embedding_version INTEGER DEFAULT 1;

-- Create vector index for fast similarity search
-- Using ivfflat index with cosine distance for optimal performance
CREATE INDEX IF NOT EXISTS idx_user_preferences_embedding 
    ON user_preferences USING ivfflat (user_embedding vector_cosine_ops)
    WITH (lists = 100);

-- Add index for embedding metadata
CREATE INDEX IF NOT EXISTS idx_user_preferences_embedding_updated 
    ON user_preferences (embedding_updated_at DESC) 
    WHERE user_embedding IS NOT NULL;

-- Add index for users without embeddings (for batch processing)
CREATE INDEX IF NOT EXISTS idx_user_preferences_no_embedding 
    ON user_preferences (user_id) 
    WHERE user_embedding IS NULL 
    AND (job_roles IS NOT NULL OR job_categories IS NOT NULL);
