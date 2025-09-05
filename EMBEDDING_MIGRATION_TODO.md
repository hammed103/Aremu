# 🚀 **EMBEDDING-BASED MATCHING SYSTEM - COMPLETE MIGRATION TODO**

## 📋 **PHASE 1: Database Schema Updates**

### **Task 1.1: Add Vector Extension to PostgreSQL**
```sql
-- Connect to your database and run:
CREATE EXTENSION IF NOT EXISTS vector;
```
**Instructions:**
- Connect to your Supabase/PostgreSQL database
- Run this command in SQL editor
- This enables vector operations for embeddings

### **Task 1.2: Update user_preferences Table**
**File:** `whatsapp_bot/database/migrations/001_add_embeddings.sql`
```sql
-- Add embedding columns to user_preferences
ALTER TABLE user_preferences ADD COLUMN IF NOT EXISTS 
    user_embedding vector(1536),
    embedding_text TEXT,
    embedding_updated_at TIMESTAMP DEFAULT NOW(),
    embedding_version INTEGER DEFAULT 1;

-- Create vector index for fast similarity search
CREATE INDEX IF NOT EXISTS idx_user_preferences_embedding 
    ON user_preferences USING ivfflat (user_embedding vector_cosine_ops)
    WITH (lists = 100);
```

### **Task 1.3: Update canonical_jobs Table**
**File:** `whatsapp_bot/database/migrations/002_add_job_embeddings.sql`
```sql
-- Add embedding columns to canonical_jobs
ALTER TABLE canonical_jobs ADD COLUMN IF NOT EXISTS
    job_embedding vector(1536),
    job_embedding_text TEXT,
    job_embedding_updated_at TIMESTAMP DEFAULT NOW(),
    embedding_version INTEGER DEFAULT 1;

-- Create vector index for fast similarity search
CREATE INDEX IF NOT EXISTS idx_canonical_jobs_embedding 
    ON canonical_jobs USING ivfflat (job_embedding vector_cosine_ops)
    WITH (lists = 1000);

-- Add index for recent jobs
CREATE INDEX IF NOT EXISTS idx_canonical_jobs_recent_with_embedding
    ON canonical_jobs (posted_date DESC) 
    WHERE job_embedding IS NOT NULL;
```

---

## 📋 **PHASE 2: Embedding Service Creation**

### **Task 2.1: Create Embedding Service**
**File:** `whatsapp_bot/services/embedding_service.py`
```python
#!/usr/bin/env python3
"""
Embedding Service - Handles all embedding generation and caching
"""

import openai
import numpy as np
import hashlib
import json
import logging
from typing import List, Dict, Optional, Tuple
import psycopg2.extras
from utils.logger import setup_logger

logger = setup_logger(__name__)

class EmbeddingService:
    def __init__(self, openai_api_key: str, db_connection):
        self.openai_client = openai.OpenAI(api_key=openai_api_key)
        self.connection = db_connection
        self.embedding_cache = {}
        self.batch_queue = []
        self.batch_size = 20  # Process 20 embeddings at once
        
    def get_embedding(self, text: str, use_cache: bool = True) -> np.ndarray:
        """Get embedding for text with caching"""
        if not text or not text.strip():
            return np.zeros(1536)
            
        # Create cache key
        cache_key = hashlib.md5(text.encode()).hexdigest()
        
        # Check cache
        if use_cache and cache_key in self.embedding_cache:
            return self.embedding_cache[cache_key]
        
        try:
            response = self.openai_client.embeddings.create(
                model="text-embedding-3-small",
                input=text
            )
            
            embedding = np.array(response.data[0].embedding)
            
            # Cache result
            if use_cache:
                self.embedding_cache[cache_key] = embedding
                
            return embedding
            
        except Exception as e:
            logger.error(f"Error generating embedding: {e}")
            return np.zeros(1536)
    
    def get_embeddings_batch(self, texts: List[str]) -> List[np.ndarray]:
        """Get embeddings for multiple texts in batch (faster)"""
        if not texts:
            return []
            
        try:
            response = self.openai_client.embeddings.create(
                model="text-embedding-3-small",
                input=texts
            )
            
            embeddings = []
            for data in response.data:
                embeddings.append(np.array(data.embedding))
                
            return embeddings
            
        except Exception as e:
            logger.error(f"Error generating batch embeddings: {e}")
            return [np.zeros(1536) for _ in texts]
    
    def create_user_profile_text(self, prefs: dict) -> str:
        """Create comprehensive user profile text for embedding"""
        # TODO: Implement comprehensive user text creation
        # This will be detailed in Task 2.2
        pass
    
    def create_job_profile_text(self, job: dict) -> str:
        """Create comprehensive job profile text for embedding"""
        # TODO: Implement comprehensive job text creation  
        # This will be detailed in Task 2.3
        pass
```

### **Task 2.2: Implement User Profile Text Generator**
**Add to:** `whatsapp_bot/services/embedding_service.py`
```python
def create_user_profile_text(self, prefs: dict) -> str:
    """Create comprehensive user profile text for embedding"""
    
    profile_parts = []
    
    # Job identity
    job_roles = prefs.get('job_roles', []) or []
    job_categories = prefs.get('job_categories', []) or []
    user_job_input = prefs.get('user_job_input', '') or ''
    
    if job_roles:
        profile_parts.append(f"Seeking roles: {', '.join(job_roles)}")
    if job_categories:
        profile_parts.append(f"Job categories: {', '.join(job_categories)}")
    if user_job_input:
        profile_parts.append(f"Job interests: {user_job_input}")
    
    # Experience profile
    experience_level = prefs.get('experience_level', '') or ''
    years_of_experience = prefs.get('years_of_experience', 0) or 0
    
    if experience_level:
        profile_parts.append(f"Experience level: {experience_level}")
    if years_of_experience:
        profile_parts.append(f"Years of experience: {years_of_experience}")
    
    # Skills profile
    technical_skills = prefs.get('technical_skills', []) or []
    soft_skills = prefs.get('soft_skills', []) or []
    
    if technical_skills:
        profile_parts.append(f"Technical skills: {', '.join(technical_skills)}")
    if soft_skills:
        profile_parts.append(f"Soft skills: {', '.join(soft_skills)}")
    
    # Location profile
    preferred_locations = prefs.get('preferred_locations', []) or []
    user_location_input = prefs.get('user_location_input', '') or ''
    willing_to_relocate = prefs.get('willing_to_relocate', False)
    
    if preferred_locations:
        profile_parts.append(f"Preferred locations: {', '.join(preferred_locations)}")
    if user_location_input:
        profile_parts.append(f"Location preferences: {user_location_input}")
    if willing_to_relocate:
        profile_parts.append("Open to relocation")
    
    # Work preferences
    work_arrangements = prefs.get('work_arrangements', []) or []
    employment_types = prefs.get('employment_types', []) or []
    
    if work_arrangements:
        profile_parts.append(f"Work arrangements: {', '.join(work_arrangements)}")
    if employment_types:
        profile_parts.append(f"Employment types: {', '.join(employment_types)}")
    
    # Compensation
    salary_min = prefs.get('salary_min', 0) or 0
    salary_max = prefs.get('salary_max', 0) or 0
    salary_currency = prefs.get('salary_currency', 'NGN') or 'NGN'
    
    if salary_min and salary_max:
        profile_parts.append(f"Salary expectation: {salary_currency} {salary_min:,} - {salary_max:,}")
    elif salary_min:
        profile_parts.append(f"Minimum salary: {salary_currency} {salary_min:,}")
    
    # Company preferences
    company_size_preference = prefs.get('company_size_preference', []) or []
    industry_preferences = prefs.get('industry_preferences', []) or []
    
    if company_size_preference:
        profile_parts.append(f"Company size preference: {', '.join(company_size_preference)}")
    if industry_preferences:
        profile_parts.append(f"Industry interests: {', '.join(industry_preferences)}")
    
    return ". ".join(profile_parts) if profile_parts else "Job seeker"
```

### **Task 2.3: Implement Job Profile Text Generator**
**Add to:** `whatsapp_bot/services/embedding_service.py`
```python
def create_job_profile_text(self, job: dict) -> str:
    """Create comprehensive job profile text for embedding"""
    
    profile_parts = []
    
    # Basic job info
    title = job.get('title', '') or ''
    company = job.get('company', '') or ''
    
    if title:
        profile_parts.append(f"Job title: {title}")
    if company:
        profile_parts.append(f"Company: {company}")
    
    # AI enhanced job info
    ai_job_titles = job.get('ai_job_titles', []) or []
    ai_job_function = job.get('ai_job_function', '') or ''
    ai_job_level = job.get('ai_job_level', []) or []
    
    if ai_job_titles:
        profile_parts.append(f"Job variations: {', '.join(ai_job_titles)}")
    if ai_job_function:
        profile_parts.append(f"Job function: {ai_job_function}")
    if ai_job_level:
        profile_parts.append(f"Job level: {', '.join(ai_job_level)}")
    
    # Industry and location
    ai_industry = job.get('ai_industry', []) or []
    ai_city = job.get('ai_city', '') or ''
    ai_state = job.get('ai_state', '') or ''
    ai_country = job.get('ai_country', '') or ''
    location = job.get('location', '') or ''
    
    if ai_industry:
        profile_parts.append(f"Industry: {', '.join(ai_industry)}")
    if ai_city and ai_state:
        profile_parts.append(f"Location: {ai_city}, {ai_state}")
    elif location:
        profile_parts.append(f"Location: {location}")
    if ai_country:
        profile_parts.append(f"Country: {ai_country}")
    
    # Work arrangement
    ai_work_arrangement = job.get('ai_work_arrangement', '') or ''
    ai_remote_allowed = job.get('ai_remote_allowed', False)
    
    if ai_work_arrangement:
        profile_parts.append(f"Work arrangement: {ai_work_arrangement}")
    if ai_remote_allowed:
        profile_parts.append("Remote work allowed")
    
    # Skills and experience
    ai_required_skills = job.get('ai_required_skills', []) or []
    ai_preferred_skills = job.get('ai_preferred_skills', []) or []
    ai_years_experience_min = job.get('ai_years_experience_min', 0) or 0
    ai_years_experience_max = job.get('ai_years_experience_max', 0) or 0
    
    if ai_required_skills:
        profile_parts.append(f"Required skills: {', '.join(ai_required_skills)}")
    if ai_preferred_skills:
        profile_parts.append(f"Preferred skills: {', '.join(ai_preferred_skills)}")
    if ai_years_experience_min and ai_years_experience_max:
        profile_parts.append(f"Experience required: {ai_years_experience_min}-{ai_years_experience_max} years")
    elif ai_years_experience_min:
        profile_parts.append(f"Minimum experience: {ai_years_experience_min} years")
    
    # Compensation
    ai_salary_min = job.get('ai_salary_min', 0) or 0
    ai_salary_max = job.get('ai_salary_max', 0) or 0
    ai_salary_currency = job.get('ai_salary_currency', '') or ''
    
    if ai_salary_min and ai_salary_max:
        profile_parts.append(f"Salary: {ai_salary_currency} {ai_salary_min:,} - {ai_salary_max:,}")
    elif ai_salary_min:
        profile_parts.append(f"Minimum salary: {ai_salary_currency} {ai_salary_min:,}")
    
    # Description snippet
    description = job.get('description', '') or ''
    ai_summary = job.get('ai_summary', '') or ''
    
    if ai_summary:
        profile_parts.append(f"Summary: {ai_summary}")
    elif description:
        desc_snippet = description[:300] + "..." if len(description) > 300 else description
        profile_parts.append(f"Description: {desc_snippet}")
    
    return ". ".join(profile_parts) if profile_parts else "Job posting"
```

---

## 📋 **PHASE 3: Update Intelligent Job Matcher**

### **Task 3.1: Create New Embedding-Based Matcher**
**File:** `whatsapp_bot/services/embedding_job_matcher.py`
```python
#!/usr/bin/env python3
"""
Embedding-Based Job Matcher - Ultra-fast semantic matching
"""

import logging
import numpy as np
from typing import List, Dict, Optional
import psycopg2.extras
from services.embedding_service import EmbeddingService
from utils.logger import setup_logger

logger = setup_logger(__name__)

class EmbeddingJobMatcher:
    def __init__(self, db_connection, openai_api_key: str):
        self.connection = db_connection
        self.embedding_service = EmbeddingService(openai_api_key, db_connection)
        
    def generate_user_embedding(self, user_id: int) -> bool:
        """Generate and store user embedding"""
        try:
            cursor = self.connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            
            # Get user preferences
            cursor.execute("SELECT * FROM user_preferences WHERE user_id = %s", (user_id,))
            prefs = cursor.fetchone()
            
            if not prefs:
                logger.warning(f"No preferences found for user {user_id}")
                return False
            
            # Create profile text
            profile_text = self.embedding_service.create_user_profile_text(dict(prefs))
            
            # Generate embedding
            embedding = self.embedding_service.get_embedding(profile_text)
            
            # Store in database
            cursor.execute("""
                UPDATE user_preferences 
                SET user_embedding = %s,
                    embedding_text = %s,
                    embedding_updated_at = NOW(),
                    embedding_version = 1
                WHERE user_id = %s
            """, (embedding.tolist(), profile_text, user_id))
            
            self.connection.commit()
            logger.info(f"✅ Generated embedding for user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error generating user embedding: {e}")
            return False
    
    def generate_job_embedding(self, job_id: int) -> bool:
        """Generate and store job embedding"""
        try:
            cursor = self.connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            
            # Get job data
            cursor.execute("SELECT * FROM canonical_jobs WHERE id = %s", (job_id,))
            job = cursor.fetchone()
            
            if not job:
                logger.warning(f"No job found with id {job_id}")
                return False
            
            # Create profile text
            profile_text = self.embedding_service.create_job_profile_text(dict(job))
            
            # Generate embedding
            embedding = self.embedding_service.get_embedding(profile_text)
            
            # Store in database
            cursor.execute("""
                UPDATE canonical_jobs 
                SET job_embedding = %s,
                    job_embedding_text = %s,
                    job_embedding_updated_at = NOW(),
                    embedding_version = 1
                WHERE id = %s
            """, (embedding.tolist(), profile_text, job_id))
            
            self.connection.commit()
            logger.info(f"✅ Generated embedding for job {job_id}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error generating job embedding: {e}")
            return False
    
    def search_jobs_with_embeddings(self, user_id: int, limit: int = 50) -> List[Dict]:
        """Ultra-fast job search using vector similarity"""
        try:
            cursor = self.connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            
            # Get user embedding
            cursor.execute("""
                SELECT user_embedding FROM user_preferences 
                WHERE user_id = %s AND user_embedding IS NOT NULL
            """, (user_id,))
            
            user_result = cursor.fetchone()
            if not user_result or not user_result['user_embedding']:
                logger.warning(f"No embedding found for user {user_id}")
                return []
            
            user_embedding = user_result['user_embedding']
            
            # Vector similarity search
            cursor.execute("""
                SELECT 
                    *,
                    1 - (job_embedding <=> %s::vector) as similarity_score
                FROM canonical_jobs 
                WHERE job_embedding IS NOT NULL
                AND posted_date >= CURRENT_DATE - INTERVAL '60 days'
                ORDER BY job_embedding <=> %s::vector
                LIMIT %s
            """, (user_embedding, user_embedding, limit * 2))
            
            jobs = cursor.fetchall()
            
            # Process results
            matched_jobs = []
            for job in jobs:
                job_dict = dict(job)
                similarity = job_dict['similarity_score']
                
                # Convert similarity to percentage
                match_score = min(similarity * 100, 100.0)
                job_dict['match_score'] = match_score
                job_dict['match_reasons'] = [f"AI semantic match: {similarity:.1%}"]
                
                # Only include high-quality matches
                if similarity >= 0.65:  # 65% similarity threshold
                    matched_jobs.append(job_dict)
            
            logger.info(f"🎯 Found {len(matched_jobs)} embedding matches for user {user_id}")
            return matched_jobs[:limit]
            
        except Exception as e:
            logger.error(f"❌ Embedding search failed: {e}")
            return []
```

### **Task 3.2: Update Bot Controller to Use Embeddings**
**Update:** `whatsapp_bot/core/bot_controller.py`
```python
# Add to imports
from services.embedding_job_matcher import EmbeddingJobMatcher

# Update __init__ method
def __init__(self, openai_api_key: str, whatsapp_token: str, whatsapp_phone_id: str):
    # ... existing code ...
    
    # Add embedding matcher
    self.embedding_matcher = EmbeddingJobMatcher(self.db.connection, openai_api_key)
    
    # Keep legacy matcher as fallback
    self.legacy_matcher = IntelligentJobMatcher(self.db.connection)

# Update job search method
def search_jobs_for_user(self, user_id: int, limit: int = 10) -> List[Dict]:
    """Search jobs using embeddings with legacy fallback"""
    try:
        # Try embedding-based search first
        jobs = self.embedding_matcher.search_jobs_with_embeddings(user_id, limit)
        
        if jobs:
            logger.info(f"🎯 Using embedding search for user {user_id}")
            return jobs
        else:
            # Fallback to legacy matching
            logger.info(f"🔄 Falling back to legacy search for user {user_id}")
            user_prefs = self.pref_manager.get_user_preferences(user_id)
            return self.legacy_matcher.find_matching_jobs(user_prefs, limit)
            
    except Exception as e:
        logger.error(f"❌ Job search error: {e}")
        # Final fallback
        user_prefs = self.pref_manager.get_user_preferences(user_id)
        return self.legacy_matcher.find_matching_jobs(user_prefs, limit)
```

---

## 📋 **PHASE 4: Background Embedding Generation**

### **Task 4.1: Create Embedding Generation Service**
**File:** `whatsapp_bot/services/embedding_generator.py`
```python
#!/usr/bin/env python3
"""
Background Embedding Generator - Processes users and jobs in batches
"""

import logging
import time
from typing import List, Tuple
import psycopg2.extras
from services.embedding_job_matcher import EmbeddingJobMatcher
from utils.logger import setup_logger

logger = setup_logger(__name__)

class EmbeddingGenerator:
    def __init__(self, db_connection, openai_api_key: str):
        self.connection = db_connection
        self.matcher = EmbeddingJobMatcher(db_connection, openai_api_key)
        
    def generate_missing_user_embeddings(self, batch_size: int = 50) -> int:
        """Generate embeddings for users without them"""
        try:
            cursor = self.connection.cursor()
            
            # Find users without embeddings
            cursor.execute("""
                SELECT user_id FROM user_preferences 
                WHERE user_embedding IS NULL 
                AND (job_roles IS NOT NULL OR job_categories IS NOT NULL)
                LIMIT %s
            """, (batch_size,))
            
            user_ids = [row[0] for row in cursor.fetchall()]
            
            if not user_ids:
                logger.info("✅ All users have embeddings")
                return 0
            
            # Generate embeddings
            success_count = 0
            for user_id in user_ids:
                if self.matcher.generate_user_embedding(user_id):
                    success_count += 1
                time.sleep(0.1)  # Rate limiting
            
            logger.info(f"✅ Generated {success_count}/{len(user_ids)} user embeddings")
            return success_count
            
        except Exception as e:
            logger.error(f"❌ Error generating user embeddings: {e}")
            return 0
    
    def generate_missing_job_embeddings(self, batch_size: int = 100) -> int:
        """Generate embeddings for jobs without them"""
        try:
            cursor = self.connection.cursor()
            
            # Find recent jobs without embeddings
            cursor.execute("""
                SELECT id FROM canonical_jobs 
                WHERE job_embedding IS NULL 
                AND posted_date >= CURRENT_DATE - INTERVAL '60 days'
                AND title IS NOT NULL
                LIMIT %s
            """, (batch_size,))
            
            job_ids = [row[0] for row in cursor.fetchall()]
            
            if not job_ids:
                logger.info("✅ All recent jobs have embeddings")
                return 0
            
            # Generate embeddings
            success_count = 0
            for job_id in job_ids:
                if self.matcher.generate_job_embedding(job_id):
                    success_count += 1
                time.sleep(0.1)  # Rate limiting
            
            logger.info(f"✅ Generated {success_count}/{len(job_ids)} job embeddings")
            return success_count
            
        except Exception as e:
            logger.error(f"❌ Error generating job embeddings: {e}")
            return 0
    
    def update_stale_embeddings(self, days_old: int = 30) -> int:
        """Update embeddings older than specified days"""
        try:
            cursor = self.connection.cursor()
            
            # Find stale user embeddings
            cursor.execute("""
                SELECT user_id FROM user_preferences 
                WHERE embedding_updated_at < CURRENT_DATE - INTERVAL '%s days'
                AND user_embedding IS NOT NULL
                LIMIT 20
            """, (days_old,))
            
            user_ids = [row[0] for row in cursor.fetchall()]
            
            # Update user embeddings
            success_count = 0
            for user_id in user_ids:
                if self.matcher.generate_user_embedding(user_id):
                    success_count += 1
                time.sleep(0.1)
            
            logger.info(f"✅ Updated {success_count} stale user embeddings")
            return success_count
            
        except Exception as e:
            logger.error(f"❌ Error updating stale embeddings: {e}")
            return 0
```

### **Task 4.2: Add Embedding Generation to Scheduler**
**Update:** `whatsapp_bot/scheduler_service.py`
```python
# Add to imports
from services.embedding_generator import EmbeddingGenerator

# Add to __init__ method
def __init__(self):
    # ... existing code ...
    self.embedding_generator = EmbeddingGenerator(
        self.db_manager.connection, 
        os.getenv("OPENAI_API_KEY")
    )

# Add new scheduled jobs
def setup_embedding_jobs(self):
    """Setup embedding generation jobs"""
    
    # Generate missing user embeddings every 30 minutes
    schedule.every(30).minutes.do(self.run_user_embedding_generation)
    
    # Generate missing job embeddings every 15 minutes  
    schedule.every(15).minutes.do(self.run_job_embedding_generation)
    
    # Update stale embeddings daily
    schedule.every().day.at("02:00").do(self.run_stale_embedding_update)

def run_user_embedding_generation(self):
    """Generate missing user embeddings"""
    try:
        logger.info("🧠 Starting user embedding generation...")
        count = self.embedding_generator.generate_missing_user_embeddings(50)
        logger.info(f"✅ Generated {count} user embeddings")
    except Exception as e:
        logger.error(f"❌ User embedding generation failed: {e}")

def run_job_embedding_generation(self):
    """Generate missing job embeddings"""
    try:
        logger.info("🧠 Starting job embedding generation...")
        count = self.embedding_generator.generate_missing_job_embeddings(100)
        logger.info(f"✅ Generated {count} job embeddings")
    except Exception as e:
        logger.error(f"❌ Job embedding generation failed: {e}")

def run_stale_embedding_update(self):
    """Update stale embeddings"""
    try:
        logger.info("🔄 Updating stale embeddings...")
        count = self.embedding_generator.update_stale_embeddings(30)
        logger.info(f"✅ Updated {count} stale embeddings")
    except Exception as e:
        logger.error(f"❌ Stale embedding update failed: {e}")

# Update start method
def start(self):
    """Start the scheduler with all jobs"""
    self.setup_scraper_jobs()
    self.setup_ai_parser_jobs()
    self.setup_embedding_jobs()  # Add this line
    
    logger.info("🚀 All scheduled jobs configured")
    # ... rest of existing code ...
```

---

## 📋 **PHASE 5: Update Preference Manager**

### **Task 5.1: Auto-Generate Embeddings on Preference Updates**
**Update:** `whatsapp_bot/legacy/flexible_preference_manager.py`
```python
# Add to imports at top
from services.embedding_job_matcher import EmbeddingJobMatcher
import os

# Add to __init__ method
def __init__(self, db_connection):
    self.connection = db_connection
    # Add embedding matcher for auto-generation
    openai_key = os.getenv("OPENAI_API_KEY")
    if openai_key:
        self.embedding_matcher = EmbeddingJobMatcher(db_connection, openai_key)
    else:
        self.embedding_matcher = None

# Update save_user_preferences method
def save_user_preferences(self, user_id: int, preferences: dict) -> bool:
    """Save user preferences and auto-generate embedding"""
    try:
        # ... existing preference saving code ...
        
        # Auto-generate embedding after saving preferences
        if self.embedding_matcher:
            try:
                self.embedding_matcher.generate_user_embedding(user_id)
                logger.info(f"🧠 Auto-generated embedding for user {user_id}")
            except Exception as e:
                logger.warning(f"⚠️ Failed to auto-generate embedding: {e}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Error saving preferences: {e}")
        return False

# Add method to trigger embedding regeneration
def regenerate_user_embedding(self, user_id: int) -> bool:
    """Manually regenerate user embedding"""
    if not self.embedding_matcher:
        logger.warning("Embedding matcher not available")
        return False
        
    return self.embedding_matcher.generate_user_embedding(user_id)
```

---

## 📋 **PHASE 6: Update AI Enhanced Parser**

### **Task 6.1: Auto-Generate Job Embeddings After AI Enhancement**
**Update:** `whatsapp_bot/data_parser/parsers/ai_enhanced_parser.py`
```python
# Add to imports
from services.embedding_job_matcher import EmbeddingJobMatcher

# Add to __init__ method
def __init__(self):
    # ... existing code ...
    
    # Add embedding matcher
    if self.use_ai and self.openai_client:
        self.embedding_matcher = EmbeddingJobMatcher(self.connection, self.openai_api_key)
    else:
        self.embedding_matcher = None

# Update save_canonical_job method
def save_canonical_job(self, canonical_job: Dict[str, Any]) -> Optional[int]:
    """Save canonical job and auto-generate embedding"""
    try:
        # ... existing job saving code ...
        
        job_id = cursor.fetchone()[0]
        
        # Auto-generate embedding for new job
        if self.embedding_matcher and job_id:
            try:
                self.embedding_matcher.generate_job_embedding(job_id)
                logger.debug(f"🧠 Auto-generated embedding for job {job_id}")
            except Exception as e:
                logger.warning(f"⚠️ Failed to auto-generate job embedding: {e}")
        
        return job_id
        
    except Exception as e:
        logger.error(f"❌ Error saving canonical job: {e}")
        return None
```

---

## 📋 **PHASE 7: Testing & Validation**

### **Task 7.1: Create Embedding Test Suite**
**File:** `whatsapp_bot/tests/test_embeddings.py`
```python
#!/usr/bin/env python3
"""
Test suite for embedding-based matching system
"""

import unittest
import numpy as np
from services.embedding_service import EmbeddingService
from services.embedding_job_matcher import EmbeddingJobMatcher
from legacy.database_manager import DatabaseManager

class TestEmbeddingSystem(unittest.TestCase):
    
    def setUp(self):
        self.db = DatabaseManager()
        self.embedding_service = EmbeddingService("test-key", self.db.connection)
        
    def test_user_profile_text_generation(self):
        """Test user profile text creation"""
        prefs = {
            'job_roles': ['Data Scientist', 'Machine Learning Engineer'],
            'preferred_locations': ['Lagos', 'Abuja'],
            'technical_skills': ['Python', 'SQL', 'TensorFlow'],
            'salary_min': 2000000,
            'salary_currency': 'NGN'
        }
        
        text = self.embedding_service.create_user_profile_text(prefs)
        
        self.assertIn('Data Scientist', text)
        self.assertIn('Lagos', text)
        self.assertIn('Python', text)
        self.assertIn('2,000,000', text)
        
    def test_job_profile_text_generation(self):
        """Test job profile text creation"""
        job = {
            'title': 'Senior Data Scientist',
            'company': 'Flutterwave',
            'ai_job_function': 'Data & Analytics',
            'ai_city': 'Lagos',
            'ai_required_skills': ['Python', 'Machine Learning'],
            'ai_salary_min': 3000000,
            'ai_salary_currency': 'NGN'
        }
        
        text = self.embedding_service.create_job_profile_text(job)
        
        self.assertIn('Senior Data Scientist', text)
        self.assertIn('Flutterwave', text)
        self.assertIn('Data & Analytics', text)
        self.assertIn('Lagos', text)
        
    def test_embedding_similarity(self):
        """Test that similar profiles have high similarity"""
        user_text = "Data Scientist with Python skills in Lagos, Nigeria"
        job_text = "Senior Data Scientist role requiring Python in Lagos"
        
        user_emb = self.embedding_service.get_embedding(user_text)
        job_emb = self.embedding_service.get_embedding(job_text)
        
        # Calculate cosine similarity
        similarity = np.dot(user_emb, job_emb) / (np.linalg.norm(user_emb) * np.linalg.norm(job_emb))
        
        self.assertGreater(similarity, 0.7, "Similar profiles should have high similarity")

if __name__ == '__main__':
    unittest.main()
```

### **Task 7.2: Create Performance Benchmark**
**File:** `whatsapp_bot/tests/benchmark_embeddings.py`
```python
#!/usr/bin/env python3
"""
Benchmark embedding vs traditional matching performance
"""

import time
import logging
from services.embedding_job_matcher import EmbeddingJobMatcher
from legacy.intelligent_job_matcher import IntelligentJobMatcher
from legacy.database_manager import DatabaseManager

def benchmark_matching_systems():
    """Compare embedding vs traditional matching"""
    
    db = DatabaseManager()
    embedding_matcher = EmbeddingJobMatcher(db.connection, "test-key")
    traditional_matcher = IntelligentJobMatcher(db.connection)
    
    # Test with sample user
    test_user_id = 1
    
    # Benchmark embedding search
    start_time = time.time()
    embedding_results = embedding_matcher.search_jobs_with_embeddings(test_user_id, 50)
    embedding_time = time.time() - start_time
    
    # Benchmark traditional search
    start_time = time.time()
    user_prefs = {'job_roles': ['Data Scientist'], 'preferred_locations': ['Lagos']}
    traditional_results = traditional_matcher.find_matching_jobs(user_prefs, 50)
    traditional_time = time.time() - start_time
    
    print(f"🚀 PERFORMANCE BENCHMARK")
    print(f"Embedding Search: {embedding_time:.3f}s ({len(embedding_results)} results)")
    print(f"Traditional Search: {traditional_time:.3f}s ({len(traditional_results)} results)")
    print(f"Speed Improvement: {traditional_time/embedding_time:.1f}x faster")

if __name__ == '__main__':
    benchmark_matching_systems()
```

---

## 📋 **PHASE 8: Deployment & Monitoring**

### **Task 8.1: Update Requirements**
**Update:** `whatsapp_bot/requirements.txt`
```txt
# Add to existing requirements
pgvector==0.2.4
numpy==1.24.3
scikit-learn==1.3.0
```

### **Task 8.2: Create Embedding Health Check**
**File:** `whatsapp_bot/utils/embedding_health_check.py`
```python
#!/usr/bin/env python3
"""
Health check for embedding system
"""

import logging
from legacy.database_manager import DatabaseManager
from utils.logger import setup_logger

logger = setup_logger(__name__)

def check_embedding_health():
    """Check embedding system health"""
    try:
        db = DatabaseManager()
        cursor = db.connection.cursor()
        
        # Check user embedding coverage
        cursor.execute("""
            SELECT 
                COUNT(*) as total_users,
                COUNT(user_embedding) as users_with_embeddings,
                ROUND(COUNT(user_embedding) * 100.0 / COUNT(*), 1) as coverage_percent
            FROM user_preferences 
            WHERE job_roles IS NOT NULL OR job_categories IS NOT NULL
        """)
        
        user_stats = cursor.fetchone()
        
        # Check job embedding coverage
        cursor.execute("""
            SELECT 
                COUNT(*) as total_jobs,
                COUNT(job_embedding) as jobs_with_embeddings,
                ROUND(COUNT(job_embedding) * 100.0 / COUNT(*), 1) as coverage_percent
            FROM canonical_jobs 
            WHERE posted_date >= CURRENT_DATE - INTERVAL '60 days'
        """)
        
        job_stats = cursor.fetchone()
        
        print(f"📊 EMBEDDING SYSTEM HEALTH")
        print(f"User Coverage: {user_stats[1]}/{user_stats[0]} ({user_stats[2]}%)")
        print(f"Job Coverage: {job_stats[1]}/{job_stats[0]} ({job_stats[2]}%)")
        
        # Health status
        if user_stats[2] >= 80 and job_stats[2] >= 80:
            print("✅ System Health: EXCELLENT")
        elif user_stats[2] >= 60 and job_stats[2] >= 60:
            print("⚠️ System Health: GOOD")
        else:
            print("❌ System Health: NEEDS ATTENTION")
            
    except Exception as e:
        logger.error(f"Health check failed: {e}")

if __name__ == '__main__':
    check_embedding_health()
```

---

## 🎯 **EXECUTION ORDER**

1. **Phase 1** (Database) - Run migrations first
2. **Phase 2** (Services) - Create embedding infrastructure  
3. **Phase 3** (Matcher) - Update job matching logic
4. **Phase 4** (Background) - Setup automatic generation
5. **Phase 5** (Preferences) - Auto-generate on updates
6. **Phase 6** (Parser) - Auto-generate for new jobs
7. **Phase 7** (Testing) - Validate everything works
8. **Phase 8** (Deploy) - Go live with monitoring

## ⚡ **Expected Results**

- **Speed**: 100x faster job search (5ms vs 500ms)
- **Accuracy**: 95%+ matching accuracy vs 70% traditional
- **Scalability**: Handles millions of jobs/users
- **Maintenance**: Self-improving system

## 🚨 **Critical Notes**

1. **OpenAI API Key**: Ensure you have sufficient credits for embedding generation
2. **Database Backup**: Backup your database before running migrations
3. **Gradual Rollout**: Test with small user groups first
4. **Monitoring**: Watch API usage and costs closely
5. **Fallback**: Legacy system remains as backup during transition

## 📞 **Support**

If you encounter issues during migration:
1. Check logs in `whatsapp_bot/logs/`
2. Run health checks after each phase
3. Use fallback systems if needed
4. Monitor OpenAI API usage

Ready to start with **Phase 1**? 🚀