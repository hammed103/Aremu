# 📡 Aremu API Documentation

## 📋 Table of Contents

- [🎯 Overview](#-overview)
- [🔐 Authentication](#-authentication)
- [📱 WhatsApp Webhook](#-whatsapp-webhook)
- [🧠 Core Classes](#-core-classes)
- [📊 Database Operations](#-database-operations)
- [⚡ Real-Time Components](#-real-time-components)
- [🔧 Configuration](#-configuration)
- [📈 Monitoring](#-monitoring)

## 🎯 Overview

Aremu exposes several APIs and interfaces for job distribution, user management, and system monitoring.

### **API Endpoints**

| Endpoint | Method | Purpose | Authentication |
|----------|--------|---------|----------------|
| `/webhook` | POST | WhatsApp message handling | Webhook verification |
| `/health` | GET | System health check | None |
| `/metrics` | GET | Performance metrics | API Key |
| `/admin/users` | GET | User management | Admin token |
| `/admin/jobs` | GET | Job analytics | Admin token |

## 🔐 Authentication

### **WhatsApp Webhook Verification**
```python
def verify_webhook(request):
    """Verify WhatsApp webhook signature"""
    signature = request.headers.get('X-Hub-Signature-256')
    payload = request.get_data()
    
    expected_signature = hmac.new(
        WEBHOOK_VERIFY_TOKEN.encode(),
        payload,
        hashlib.sha256
    ).hexdigest()
    
    return hmac.compare_digest(signature, f"sha256={expected_signature}")
```

### **API Key Authentication**
```python
def require_api_key(f):
    """Decorator for API key authentication"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        api_key = request.headers.get('X-API-Key')
        if not api_key or api_key != ADMIN_API_KEY:
            return jsonify({'error': 'Invalid API key'}), 401
        return f(*args, **kwargs)
    return decorated_function
```

## 📱 WhatsApp Webhook

### **Message Handling Flow**

```python
@app.route('/webhook', methods=['POST'])
def webhook():
    """Handle incoming WhatsApp messages"""
    try:
        # Verify webhook signature
        if not verify_webhook(request):
            return jsonify({'error': 'Invalid signature'}), 401
        
        # Parse webhook data
        data = request.get_json()
        
        # Extract message details
        for entry in data.get('entry', []):
            for change in entry.get('changes', []):
                if change.get('field') == 'messages':
                    messages = change.get('value', {}).get('messages', [])
                    
                    for message in messages:
                        phone_number = message.get('from')
                        message_text = message.get('text', {}).get('body', '')
                        
                        # Process message
                        response = bot.get_ai_response(message_text, phone_number)
                        
                        # Send response (if any)
                        if response:
                            bot.send_whatsapp_message(phone_number, response)
        
        return jsonify({'status': 'success'}), 200
        
    except Exception as e:
        logger.error(f"Webhook error: {e}")
        return jsonify({'error': 'Internal server error'}), 500
```

### **Message Types Supported**

#### **Text Messages**
```json
{
  "messaging_product": "whatsapp",
  "to": "+2348123456789",
  "type": "text",
  "text": {
    "body": "🚨 NEW JOB ALERT! (85% match)\n\n🚀 **Marketing Manager** at **TechCorp**..."
  }
}
```

#### **Interactive Messages** (Future)
```json
{
  "messaging_product": "whatsapp",
  "to": "+2348123456789",
  "type": "interactive",
  "interactive": {
    "type": "button",
    "body": {
      "text": "Found 3 matching jobs. What would you like to do?"
    },
    "action": {
      "buttons": [
        {"id": "view_jobs", "title": "View Jobs"},
        {"id": "update_prefs", "title": "Update Preferences"},
        {"id": "pause_alerts", "title": "Pause Alerts"}
      ]
    }
  }
}
```

## 🧠 Core Classes

### **1. WhatsAppBot** (`app.py`)

```python
class WhatsAppBot:
    """Main WhatsApp bot application"""
    
    def __init__(self):
        """Initialize bot with all components"""
        self.db = DatabaseManager()
        self.pref_manager = FlexiblePreferenceManager(self.db.connection)
        self.job_matcher = IntelligentJobMatcher(self.db.connection)
        self.job_tracker = JobTrackingSystem()
        self.window_manager = WindowManagementSystem()
    
    def get_ai_response(self, user_message: str, phone_number: str) -> str:
        """Process user message and generate response"""
        # Window management
        # Preference extraction
        # Job search handling
        # Response generation
    
    def send_whatsapp_message(self, phone_number: str, message: str) -> bool:
        """Send message via WhatsApp Business API"""
        # API call to WhatsApp
        # Error handling
        # Logging
```

### **2. IntelligentJobMatcher** (`intelligent_job_matcher.py`)

```python
class IntelligentJobMatcher:
    """Advanced job matching with AI-enhanced scoring"""
    
    def search_jobs_for_user(self, user_id: int, limit: int = 10) -> List[Dict]:
        """Find and score jobs for a specific user"""
        user_prefs = self.get_user_preferences(user_id)
        jobs = self.get_candidate_jobs()
        
        scored_jobs = []
        for job in jobs:
            score = self._calculate_job_score(user_prefs, job)
            if score >= self.min_score_threshold:
                job['match_score'] = score
                job['match_reasons'] = self._get_match_reasons(user_prefs, job)
                scored_jobs.append(job)
        
        return sorted(scored_jobs, key=lambda x: x['match_score'], reverse=True)[:limit]
    
    def _calculate_job_score(self, user_prefs: Dict, job: Dict) -> float:
        """Calculate comprehensive match score"""
        total_score = 0.0
        
        # AI Job Titles Matching (35%)
        title_score = self._score_ai_job_titles_match(user_prefs, job)
        total_score += title_score * 0.35
        
        # Skills Matching (25%)
        skills_score = self._score_skills_match(user_prefs, job)
        total_score += skills_score * 0.25
        
        # Location Matching (20%)
        location_score = self._score_location_match(user_prefs, job)
        total_score += location_score * 0.20
        
        # Salary Matching (10%)
        salary_score = self._score_salary_match(user_prefs, job)
        total_score += salary_score * 0.10
        
        # Experience Matching (10%)
        experience_score = self._score_experience_match(user_prefs, job)
        total_score += experience_score * 0.10
        
        return min(total_score, 100.0)
```

### **3. SmartDeliveryEngine** (`smart_delivery_engine.py`)

```python
class SmartDeliveryEngine:
    """Real-time job delivery with intelligent targeting"""
    
    def process_single_job_delivery(self, job: Dict) -> Dict:
        """Process delivery for a single new job"""
        stats = {
            'job_id': job.get('id'),
            'eligible_users': 0,
            'matches_found': 0,
            'alerts_sent': 0,
            'errors': 0
        }
        
        # Get eligible users (active windows + confirmed preferences)
        eligible_users = self.get_eligible_users_for_delivery()
        stats['eligible_users'] = len(eligible_users)
        
        # Calculate matches
        matches = self.calculate_job_matches_for_users(job, eligible_users)
        stats['matches_found'] = len(matches)
        
        # Send alerts
        for match in matches:
            if self.send_whatsapp_job_alert(match['user'], job, match['match_score']):
                self.job_tracker.mark_job_as_shown(
                    match['user']['user_id'], 
                    job['id'], 
                    match['match_score'], 
                    'real_time_parser'
                )
                stats['alerts_sent'] += 1
        
        return stats
```

### **4. WindowManagementSystem** (`window_management_system.py`)

```python
class WindowManagementSystem:
    """24-hour WhatsApp window cost optimization"""
    
    def get_window_status(self, user_id: int) -> Dict:
        """Get current window status with smart triggers"""
        # Query database for window info
        # Calculate hours elapsed
        # Determine reminder needs
        
        return {
            'has_active_window': bool,
            'hours_elapsed': float,
            'needs_four_hour_reminder': bool,  # 20h mark
            'needs_battery_warning': bool,     # 23h mark
            'window_expired': bool,            # 24h mark
            'status': str
        }
    
    def start_new_window(self, user_id: int) -> bool:
        """Start fresh 24-hour window"""
        # Close existing windows
        # Create new window record
        # Reset all flags
    
    def update_window_activity(self, user_id: int) -> bool:
        """Update last activity timestamp"""
        # Update last_activity
        # Increment message count
        # Create window if none exists
```

## 📊 Database Operations

### **Core Database Manager**

```python
class DatabaseManager:
    """Centralized database operations"""
    
    def __init__(self):
        """Initialize database connection"""
        self.connection = psycopg2.connect(DATABASE_URL)
        self.ensure_tables_exist()
    
    def get_or_create_user(self, phone_number: str) -> int:
        """Get existing user or create new one"""
        cursor = self.connection.cursor()
        
        # Try to get existing user
        cursor.execute(
            "SELECT id FROM users WHERE phone_number = %s",
            (phone_number,)
        )
        result = cursor.fetchone()
        
        if result:
            return result[0]
        
        # Create new user
        cursor.execute(
            "INSERT INTO users (phone_number) VALUES (%s) RETURNING id",
            (phone_number,)
        )
        user_id = cursor.fetchone()[0]
        self.connection.commit()
        
        return user_id
    
    def execute_query(self, query: str, params: tuple = None) -> List[tuple]:
        """Execute query with error handling"""
        try:
            cursor = self.connection.cursor()
            cursor.execute(query, params)
            
            if query.strip().upper().startswith('SELECT'):
                return cursor.fetchall()
            else:
                self.connection.commit()
                return []
                
        except Exception as e:
            self.connection.rollback()
            logger.error(f"Database error: {e}")
            raise
```

### **Performance Optimizations**

#### **Indexing Strategy**
```sql
-- User lookup optimization
CREATE INDEX idx_users_phone ON users(phone_number);

-- Job matching optimization
CREATE INDEX idx_canonical_jobs_location ON canonical_jobs(location);
CREATE INDEX idx_canonical_jobs_posted_date ON canonical_jobs(posted_date DESC);

-- Array field optimization (GIN indexes)
CREATE INDEX idx_canonical_jobs_ai_skills ON canonical_jobs USING GIN(ai_skills);
CREATE INDEX idx_user_preferences_job_roles ON user_preferences USING GIN(job_roles);

-- Window management optimization
CREATE INDEX idx_conversation_windows_active ON conversation_windows(user_id, window_status) 
WHERE window_status = 'active';
```

#### **Query Optimization**
```python
def get_matching_jobs_optimized(self, user_prefs: Dict, limit: int = 10) -> List[Dict]:
    """Optimized job matching query"""
    
    # Build dynamic WHERE clause based on user preferences
    where_conditions = ["ai_enhanced = TRUE"]
    params = []
    
    # Location filtering
    if user_prefs.get('preferred_locations'):
        where_conditions.append("location = ANY(%s)")
        params.append(user_prefs['preferred_locations'])
    
    # Date filtering (recent jobs only)
    where_conditions.append("posted_date >= CURRENT_DATE - INTERVAL '30 days'")
    
    query = f"""
        SELECT id, title, company, location, ai_job_titles, ai_skills, ai_summary
        FROM canonical_jobs 
        WHERE {' AND '.join(where_conditions)}
        ORDER BY posted_date DESC, id DESC
        LIMIT %s
    """
    params.append(limit * 3)  # Get more candidates for scoring
    
    return self.db.execute_query(query, tuple(params))
```

## ⚡ Real-Time Components

### **Event-Driven Job Processing**

```python
# In AI Enhanced Parser
def save_canonical_job(self, job: Dict) -> int:
    """Save job and trigger real-time delivery"""
    
    # Save to database
    job_id = self._insert_job_to_db(job)
    
    # REAL-TIME TRIGGER: Immediate delivery check
    if self.smart_delivery and self.smart_delivery.is_delivery_enabled():
        job['id'] = job_id
        delivery_stats = self.smart_delivery.process_single_job_delivery(job)
        
        if delivery_stats['alerts_sent'] > 0:
            logger.info(f"🚨 Delivered job {job_id} to {delivery_stats['alerts_sent']} users")
    
    return job_id
```

### **Background Monitoring** (Optional)

```python
class RealTimeJobMonitor:
    """Background job monitoring for missed opportunities"""
    
    def run_monitoring_cycle(self) -> Dict:
        """Check for new jobs and send alerts"""
        
        # Get jobs added since last check
        new_jobs = self.get_new_jobs_since_last_check()
        
        # Get active users
        active_users = self.get_active_users_with_preferences()
        
        # Process matches and send alerts
        stats = {'alerts_sent': 0, 'errors': 0}
        
        for job in new_jobs:
            for user in active_users:
                if self.should_send_job_to_user(user, job):
                    if self.send_real_time_job_alert(user, job):
                        stats['alerts_sent'] += 1
        
        return stats
```

## 🔧 Configuration

### **Environment Variables**

```bash
# Database Configuration
DATABASE_URL=postgresql://user:password@localhost/aremu_jobs

# WhatsApp Business API
WHATSAPP_ACCESS_TOKEN=EAAZAxxxxx...
WHATSAPP_PHONE_NUMBER_ID=123456789
WEBHOOK_VERIFY_TOKEN=your_webhook_secret

# OpenAI Configuration
OPENAI_API_KEY=sk-proj-xxxxx...

# System Configuration
MIN_MATCH_SCORE=39
MAX_JOBS_PER_USER_PER_DAY=10
WINDOW_DURATION_HOURS=24

# Monitoring
LOG_LEVEL=INFO
SENTRY_DSN=https://xxxxx@sentry.io/xxxxx
```

### **Application Settings**

```python
class Config:
    """Application configuration"""
    
    # Database
    DATABASE_URL = os.getenv('DATABASE_URL')
    
    # WhatsApp
    WHATSAPP_ACCESS_TOKEN = os.getenv('WHATSAPP_ACCESS_TOKEN')
    WHATSAPP_PHONE_NUMBER_ID = os.getenv('WHATSAPP_PHONE_NUMBER_ID')
    WEBHOOK_VERIFY_TOKEN = os.getenv('WEBHOOK_VERIFY_TOKEN')
    
    # AI
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
    
    # Business Logic
    MIN_MATCH_SCORE = float(os.getenv('MIN_MATCH_SCORE', 39))
    MAX_JOBS_PER_USER_PER_DAY = int(os.getenv('MAX_JOBS_PER_USER_PER_DAY', 10))
    WINDOW_DURATION_HOURS = int(os.getenv('WINDOW_DURATION_HOURS', 24))
    
    # Performance
    JOB_BATCH_SIZE = int(os.getenv('JOB_BATCH_SIZE', 50))
    CACHE_TTL_SECONDS = int(os.getenv('CACHE_TTL_SECONDS', 300))
```

## 📈 Monitoring

### **Health Check Endpoint**

```python
@app.route('/health')
def health_check():
    """System health check"""
    try:
        # Database connectivity
        db_status = check_database_connection()
        
        # WhatsApp API connectivity
        whatsapp_status = check_whatsapp_api()
        
        # OpenAI API connectivity
        openai_status = check_openai_api()
        
        return jsonify({
            'status': 'healthy',
            'timestamp': datetime.utcnow().isoformat(),
            'services': {
                'database': db_status,
                'whatsapp': whatsapp_status,
                'openai': openai_status
            }
        }), 200
        
    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'error': str(e)
        }), 500
```

### **Metrics Collection**

```python
@app.route('/metrics')
@require_api_key
def get_metrics():
    """System performance metrics"""
    
    metrics = {
        'users': {
            'total': get_total_users(),
            'active_24h': get_active_users(hours=24),
            'new_today': get_new_users_today()
        },
        'jobs': {
            'total': get_total_jobs(),
            'processed_today': get_jobs_processed_today(),
            'alerts_sent_today': get_alerts_sent_today()
        },
        'performance': {
            'avg_response_time_ms': get_avg_response_time(),
            'error_rate_percent': get_error_rate(),
            'match_accuracy_percent': get_match_accuracy()
        }
    }
    
    return jsonify(metrics)
```

---

**This API documentation provides comprehensive coverage of Aremu's interfaces and internal architecture for developers and system administrators.**
