# 🧪 Aremu Testing & Quality Assurance Guide

## 📋 Table of Contents

- [🎯 Testing Overview](#-testing-overview)
- [🔧 Test Setup](#-test-setup)
- [📱 WhatsApp Bot Testing](#-whatsapp-bot-testing)
- [🔄 Data Parser Testing](#-data-parser-testing)
- [🧠 AI Components Testing](#-ai-components-testing)
- [📊 Integration Testing](#-integration-testing)
- [⚡ Performance Testing](#-performance-testing)
- [🔒 Security Testing](#-security-testing)
- [📈 Quality Metrics](#-quality-metrics)

## 🎯 Testing Overview

Aremu employs a comprehensive testing strategy covering all system components:

### **Testing Pyramid**

```
                    🔺
                   /   \
                  /  E2E \
                 /       \
                /---------\
               /Integration\
              /             \
             /---------------\
            /   Unit Tests    \
           /                   \
          /---------------------\
```

### **Test Categories**

| Test Type | Coverage | Tools | Frequency |
|-----------|----------|-------|-----------|
| **Unit Tests** | Individual functions/methods | pytest, unittest | Every commit |
| **Integration Tests** | Component interactions | pytest, requests | Daily |
| **End-to-End Tests** | Complete user journeys | Selenium, API tests | Weekly |
| **Performance Tests** | Load and stress testing | locust, pytest-benchmark | Weekly |
| **Security Tests** | Vulnerability scanning | bandit, safety | Daily |

## 🔧 Test Setup

### **Environment Setup**

```bash
# Create test environment
cd whatsapp_bot
python -m venv test_env
source test_env/bin/activate

# Install test dependencies
pip install -r requirements.txt
pip install pytest pytest-cov pytest-mock pytest-asyncio

# Setup test database
createdb aremu_test
export DATABASE_URL="postgresql://user:password@localhost/aremu_test"

# Initialize test data
python tests/setup_test_data.py
```

### **Test Configuration**

```python
# tests/conftest.py
import pytest
import os
from app import WhatsAppBot
from database_manager import DatabaseManager

@pytest.fixture(scope="session")
def test_app():
    """Create test application instance"""
    os.environ['TESTING'] = 'True'
    os.environ['DATABASE_URL'] = 'postgresql://user:password@localhost/aremu_test'
    
    app = WhatsAppBot()
    return app

@pytest.fixture(scope="function")
def clean_db():
    """Clean database before each test"""
    db = DatabaseManager()
    cursor = db.connection.cursor()
    
    # Clean all tables
    cursor.execute("TRUNCATE users, user_preferences, canonical_jobs, user_job_history, conversation_windows CASCADE")
    db.connection.commit()
    
    yield db
    
    # Cleanup after test
    cursor.execute("TRUNCATE users, user_preferences, canonical_jobs, user_job_history, conversation_windows CASCADE")
    db.connection.commit()

@pytest.fixture
def sample_user_data():
    """Sample user data for testing"""
    return {
        'phone_number': '+2348123456789',
        'preferences': {
            'job_roles': ['software developer'],
            'preferred_locations': ['Lagos'],
            'technical_skills': ['Python', 'JavaScript'],
            'years_of_experience': 3,
            'salary_min': 500000,
            'salary_currency': 'NGN'
        }
    }

@pytest.fixture
def sample_job_data():
    """Sample job data for testing"""
    return {
        'title': 'Senior Python Developer',
        'company': 'TechCorp Nigeria',
        'location': 'Lagos',
        'salary_min': 600000,
        'salary_max': 800000,
        'salary_currency': 'NGN',
        'employment_type': 'Full-time',
        'ai_job_titles': ['python developer', 'software engineer', 'backend developer'],
        'ai_skills': ['Python', 'Django', 'PostgreSQL'],
        'ai_industry': 'Technology',
        'ai_summary': 'Exciting Python developer role...'
    }
```

## 📱 WhatsApp Bot Testing

### **Unit Tests**

```python
# tests/test_app.py
import pytest
from unittest.mock import Mock, patch

class TestWhatsAppBot:
    
    def test_user_creation(self, test_app, clean_db):
        """Test user creation and retrieval"""
        phone = '+2348123456789'
        user_id = test_app.db.get_or_create_user(phone)
        
        assert user_id is not None
        assert isinstance(user_id, int)
        
        # Test duplicate creation
        user_id_2 = test_app.db.get_or_create_user(phone)
        assert user_id == user_id_2
    
    def test_preference_extraction(self, test_app):
        """Test preference extraction from messages"""
        message = "I'm looking for Python developer jobs in Lagos with 500k salary"
        
        extracted = test_app.extract_user_profile(message)
        
        assert 'job_roles' in extracted
        assert 'python developer' in [role.lower() for role in extracted['job_roles']]
        assert 'preferred_locations' in extracted
        assert 'Lagos' in extracted['preferred_locations']
        assert extracted['salary_min'] == 500000
    
    @patch('app.WhatsAppBot.send_whatsapp_message')
    def test_job_search_flow(self, mock_send, test_app, clean_db, sample_user_data, sample_job_data):
        """Test complete job search flow"""
        # Create user and preferences
        user_id = test_app.db.get_or_create_user(sample_user_data['phone_number'])
        test_app.pref_manager.save_preferences(user_id, sample_user_data['preferences'])
        
        # Add sample job
        test_app.db.execute_query(
            "INSERT INTO canonical_jobs (title, company, location, ai_job_titles, ai_skills) VALUES (%s, %s, %s, %s, %s)",
            (sample_job_data['title'], sample_job_data['company'], sample_job_data['location'], 
             sample_job_data['ai_job_titles'], sample_job_data['ai_skills'])
        )
        
        # Test job search
        response = test_app.search_and_send_jobs_individually(sample_user_data['phone_number'])
        
        assert mock_send.called
        assert "job" in response.lower()
    
    def test_window_management(self, test_app, clean_db):
        """Test 24-hour window management"""
        user_id = test_app.db.get_or_create_user('+2348123456789')
        
        # Start new window
        success = test_app.window_manager.start_new_window(user_id)
        assert success
        
        # Check window status
        status = test_app.window_manager.get_window_status(user_id)
        assert status['has_active_window']
        assert status['hours_elapsed'] < 1
        assert not status['needs_battery_warning']
    
    def test_job_tracking(self, test_app, clean_db, sample_job_data):
        """Test job tracking and duplicate prevention"""
        user_id = test_app.db.get_or_create_user('+2348123456789')
        
        # Add job to database
        cursor = test_app.db.connection.cursor()
        cursor.execute(
            "INSERT INTO canonical_jobs (title, company, location) VALUES (%s, %s, %s) RETURNING id",
            (sample_job_data['title'], sample_job_data['company'], sample_job_data['location'])
        )
        job_id = cursor.fetchone()[0]
        test_app.db.connection.commit()
        
        # Mark job as shown
        success = test_app.job_tracker.mark_job_as_shown(user_id, job_id, 85.5, 'test')
        assert success
        
        # Test duplicate detection
        jobs = [{'id': job_id, 'title': sample_job_data['title']}]
        unseen = test_app.job_tracker.get_unseen_jobs(user_id, jobs)
        assert len(unseen) == 0  # Should be filtered out
```

### **Integration Tests**

```python
# tests/test_integration.py
import pytest
import requests
import json
from unittest.mock import patch

class TestWhatsAppIntegration:
    
    @patch('requests.post')
    def test_webhook_message_handling(self, mock_post, test_app):
        """Test webhook message processing"""
        mock_post.return_value.status_code = 200
        
        webhook_data = {
            "entry": [{
                "changes": [{
                    "field": "messages",
                    "value": {
                        "messages": [{
                            "from": "+2348123456789",
                            "text": {"body": "I want software developer jobs"}
                        }]
                    }
                }]
            }]
        }
        
        with test_app.app.test_client() as client:
            response = client.post('/webhook', 
                                 data=json.dumps(webhook_data),
                                 content_type='application/json')
            
            assert response.status_code == 200
    
    def test_preference_confirmation_flow(self, test_app, clean_db):
        """Test complete preference confirmation flow"""
        phone = '+2348123456789'
        
        # Step 1: Initial preference extraction
        response1 = test_app.get_ai_response("I want marketing jobs in Lagos", phone)
        assert "marketing" in response1.lower()
        
        # Step 2: Add more preferences
        response2 = test_app.get_ai_response("I have 3 years experience and want 400k salary", phone)
        
        # Step 3: Should trigger confirmation
        response3 = test_app.get_ai_response("I prefer remote work", phone)
        assert "confirm" in response3.lower()
        
        # Step 4: Confirm preferences
        response4 = test_app.get_ai_response("yes", phone)
        assert "job" in response4.lower()
```

## 🔄 Data Parser Testing

### **AI Enhancement Testing**

```python
# tests/test_ai_parser.py
import pytest
from unittest.mock import Mock, patch
from data_parser.parsers.ai_enhanced_parser import AIEnhancedJobParser

class TestAIEnhancedParser:
    
    @patch('openai.ChatCompletion.create')
    def test_job_enhancement(self, mock_openai):
        """Test AI job enhancement"""
        mock_openai.return_value = Mock(
            choices=[Mock(message=Mock(content=json.dumps({
                'ai_job_titles': ['python developer', 'software engineer'],
                'ai_skills': ['Python', 'Django', 'REST API'],
                'ai_industry': 'Technology',
                'ai_job_function': 'Software Development',
                'ai_summary': 'Exciting Python developer role...'
            })))]
        )
        
        parser = AIEnhancedJobParser()
        
        raw_job = {
            'title': 'Python Dev',
            'company': 'TechCorp',
            'description': 'Looking for Python developer with Django experience...'
        }
        
        enhanced = parser.enhance_job_with_ai(raw_job)
        
        assert 'ai_job_titles' in enhanced
        assert 'python developer' in enhanced['ai_job_titles']
        assert 'ai_skills' in enhanced
        assert 'Python' in enhanced['ai_skills']
    
    def test_smart_delivery_integration(self):
        """Test smart delivery integration"""
        parser = AIEnhancedJobParser()
        
        # Mock smart delivery
        parser.smart_delivery = Mock()
        parser.smart_delivery.is_delivery_enabled.return_value = True
        parser.smart_delivery.process_single_job_delivery.return_value = {
            'alerts_sent': 2, 'errors': 0
        }
        
        job = {'id': 1, 'title': 'Test Job'}
        
        # This should trigger smart delivery
        parser.save_canonical_job(job)
        
        assert parser.smart_delivery.process_single_job_delivery.called
```

### **Smart Delivery Testing**

```python
# tests/test_smart_delivery.py
import pytest
from unittest.mock import Mock, patch
from data_parser.smart_delivery_engine import SmartDeliveryEngine

class TestSmartDeliveryEngine:
    
    def test_eligible_users_detection(self, clean_db):
        """Test eligible users detection"""
        delivery_engine = SmartDeliveryEngine()
        
        # Create test users with different statuses
        # ... setup test data ...
        
        eligible_users = delivery_engine.get_eligible_users_for_delivery()
        
        # Should only return users with active windows and confirmed preferences
        assert len(eligible_users) > 0
        for user in eligible_users:
            assert user['preferences_confirmed'] is True
    
    @patch('requests.post')
    def test_whatsapp_delivery(self, mock_post):
        """Test WhatsApp message delivery"""
        mock_post.return_value.status_code = 200
        
        delivery_engine = SmartDeliveryEngine('test_token', 'test_phone_id')
        
        user = {'phone_number': '+2348123456789'}
        job = {'ai_summary': 'Test job alert', 'id': 1}
        
        success = delivery_engine.send_whatsapp_job_alert(user, job, 85.5)
        
        assert success
        assert mock_post.called
```

## 🧠 AI Components Testing

### **Job Matching Algorithm Testing**

```python
# tests/test_job_matcher.py
import pytest
from intelligent_job_matcher import IntelligentJobMatcher

class TestIntelligentJobMatcher:
    
    def test_title_matching_exact(self):
        """Test exact title matching"""
        matcher = IntelligentJobMatcher(None)
        
        user_prefs = {'job_roles': ['python developer']}
        job = {'ai_job_titles': ['python developer', 'software engineer']}
        
        score = matcher._score_ai_job_titles_match(user_prefs, job)
        assert score == 100.0  # Perfect match
    
    def test_title_matching_fuzzy(self):
        """Test fuzzy title matching"""
        matcher = IntelligentJobMatcher(None)
        
        user_prefs = {'job_roles': ['python dev']}
        job = {'ai_job_titles': ['python developer', 'backend engineer']}
        
        score = matcher._score_ai_job_titles_match(user_prefs, job)
        assert score > 80.0  # High fuzzy match
    
    def test_skills_matching(self):
        """Test skills matching"""
        matcher = IntelligentJobMatcher(None)
        
        user_prefs = {'technical_skills': ['Python', 'Django', 'PostgreSQL']}
        job = {'ai_skills': ['Python', 'Django', 'REST API', 'Docker']}
        
        score = matcher._score_skills_match(user_prefs, job)
        assert score > 60.0  # Good skills overlap
    
    def test_location_matching(self):
        """Test location matching"""
        matcher = IntelligentJobMatcher(None)
        
        user_prefs = {'preferred_locations': ['Lagos', 'Abuja']}
        job = {'location': 'Lagos'}
        
        score = matcher._score_location_match(user_prefs, job)
        assert score == 100.0  # Perfect location match
    
    def test_overall_score_calculation(self, clean_db):
        """Test overall match score calculation"""
        matcher = IntelligentJobMatcher(clean_db.connection)
        
        user_prefs = {
            'job_roles': ['python developer'],
            'technical_skills': ['Python', 'Django'],
            'preferred_locations': ['Lagos'],
            'salary_min': 400000,
            'years_of_experience': 3
        }
        
        job = {
            'ai_job_titles': ['python developer', 'backend developer'],
            'ai_skills': ['Python', 'Django', 'PostgreSQL'],
            'location': 'Lagos',
            'salary_min': 500000,
            'experience_level': 'Mid-level'
        }
        
        score = matcher._calculate_job_score(user_prefs, job)
        assert score >= 39.0  # Should meet minimum threshold
        assert score <= 100.0
```

## 📊 Integration Testing

### **End-to-End User Journey Testing**

```python
# tests/test_e2e.py
import pytest
import time
from selenium import webdriver
from selenium.webdriver.common.by import By

class TestEndToEndJourney:
    
    def test_complete_user_journey(self, test_app, clean_db):
        """Test complete user journey from first message to job delivery"""
        phone = '+2348123456789'
        
        # Step 1: User sends first message
        response1 = test_app.get_ai_response("Hi, I'm looking for jobs", phone)
        assert "help" in response1.lower() or "job" in response1.lower()
        
        # Step 2: User specifies preferences
        response2 = test_app.get_ai_response("I want Python developer jobs in Lagos", phone)
        
        # Step 3: User adds more details
        response3 = test_app.get_ai_response("I have 3 years experience and want 500k salary", phone)
        
        # Step 4: User adds work preference
        response4 = test_app.get_ai_response("I prefer remote work", phone)
        
        # Should trigger confirmation
        assert "confirm" in response4.lower()
        
        # Step 5: User confirms
        response5 = test_app.get_ai_response("yes", phone)
        
        # Should trigger job search
        assert "job" in response5.lower() or "found" in response5.lower()
        
        # Verify user preferences were saved
        user_id = test_app.db.get_or_create_user(phone)
        prefs = test_app.pref_manager.get_preferences(user_id)
        assert prefs['preferences_confirmed'] is True
        assert 'python developer' in [role.lower() for role in prefs['job_roles']]
    
    def test_real_time_job_delivery(self, test_app, clean_db):
        """Test real-time job delivery when new job is added"""
        # Setup user with confirmed preferences
        phone = '+2348123456789'
        user_id = test_app.db.get_or_create_user(phone)
        
        prefs = {
            'job_roles': ['python developer'],
            'preferred_locations': ['Lagos'],
            'technical_skills': ['Python'],
            'preferences_confirmed': True
        }
        test_app.pref_manager.save_preferences(user_id, prefs)
        
        # Start active window
        test_app.window_manager.start_new_window(user_id)
        
        # Simulate new job being processed
        from data_parser.parsers.ai_enhanced_parser import AIEnhancedJobParser
        parser = AIEnhancedJobParser()
        
        new_job = {
            'title': 'Senior Python Developer',
            'company': 'TechCorp',
            'location': 'Lagos',
            'ai_job_titles': ['python developer', 'software engineer'],
            'ai_skills': ['Python', 'Django'],
            'ai_summary': 'Exciting Python role...'
        }
        
        # This should trigger real-time delivery
        with patch('data_parser.smart_delivery_engine.SmartDeliveryEngine.send_whatsapp_job_alert') as mock_send:
            mock_send.return_value = True
            job_id = parser.save_canonical_job(new_job)
            
            # Verify delivery was attempted
            assert mock_send.called
```

## ⚡ Performance Testing

### **Load Testing**

```python
# tests/test_performance.py
import pytest
import time
import concurrent.futures
from locust import HttpUser, task, between

class WhatsAppBotLoadTest(HttpUser):
    wait_time = between(1, 3)
    
    @task
    def send_message(self):
        """Simulate WhatsApp message"""
        webhook_data = {
            "entry": [{
                "changes": [{
                    "field": "messages",
                    "value": {
                        "messages": [{
                            "from": f"+234812345{self.user_id:04d}",
                            "text": {"body": "I want software developer jobs"}
                        }]
                    }
                }]
            }]
        }
        
        self.client.post("/webhook", json=webhook_data)

def test_concurrent_users(test_app):
    """Test system performance with concurrent users"""
    def simulate_user(user_id):
        phone = f"+234812345{user_id:04d}"
        start_time = time.time()
        
        response = test_app.get_ai_response("I want Python jobs in Lagos", phone)
        
        end_time = time.time()
        return end_time - start_time
    
    # Test with 50 concurrent users
    with concurrent.futures.ThreadPoolExecutor(max_workers=50) as executor:
        futures = [executor.submit(simulate_user, i) for i in range(50)]
        response_times = [future.result() for future in futures]
    
    # Assert performance requirements
    avg_response_time = sum(response_times) / len(response_times)
    max_response_time = max(response_times)
    
    assert avg_response_time < 2.0  # Average response under 2 seconds
    assert max_response_time < 5.0  # Max response under 5 seconds
    assert len([t for t in response_times if t < 1.0]) / len(response_times) > 0.8  # 80% under 1 second

def test_database_performance(clean_db):
    """Test database query performance"""
    # Insert test data
    for i in range(1000):
        clean_db.execute_query(
            "INSERT INTO canonical_jobs (title, company, location) VALUES (%s, %s, %s)",
            (f"Job {i}", f"Company {i}", "Lagos")
        )
    
    # Test job search performance
    start_time = time.time()
    
    jobs = clean_db.execute_query(
        "SELECT * FROM canonical_jobs WHERE location = %s ORDER BY id DESC LIMIT 10",
        ("Lagos",)
    )
    
    end_time = time.time()
    query_time = end_time - start_time
    
    assert query_time < 0.1  # Query should complete in under 100ms
    assert len(jobs) == 10
```

## 🔒 Security Testing

### **Input Validation Testing**

```python
# tests/test_security.py
import pytest
from app import WhatsAppBot

class TestSecurity:
    
    def test_sql_injection_prevention(self, test_app, clean_db):
        """Test SQL injection prevention"""
        malicious_input = "'; DROP TABLE users; --"
        
        # This should not cause any database errors
        response = test_app.get_ai_response(malicious_input, "+2348123456789")
        
        # Verify users table still exists
        users = clean_db.execute_query("SELECT COUNT(*) FROM users")
        assert users is not None
    
    def test_xss_prevention(self, test_app):
        """Test XSS prevention in responses"""
        malicious_input = "<script>alert('xss')</script>"
        
        response = test_app.get_ai_response(malicious_input, "+2348123456789")
        
        # Response should not contain unescaped script tags
        assert "<script>" not in response
        assert "alert(" not in response
    
    def test_rate_limiting(self, test_app):
        """Test rate limiting protection"""
        phone = "+2348123456789"
        
        # Send multiple rapid requests
        responses = []
        for i in range(20):
            response = test_app.get_ai_response(f"Message {i}", phone)
            responses.append(response)
        
        # Should implement some form of rate limiting
        # (Implementation depends on your rate limiting strategy)
    
    def test_phone_number_validation(self, test_app):
        """Test phone number validation"""
        invalid_phones = [
            "invalid",
            "123",
            "+1234567890123456789",  # Too long
            "+",  # Just plus sign
            ""  # Empty
        ]
        
        for phone in invalid_phones:
            # Should handle invalid phone numbers gracefully
            response = test_app.get_ai_response("test message", phone)
            assert response is not None  # Should not crash
```

## 📈 Quality Metrics

### **Test Coverage Requirements**

```bash
# Run tests with coverage
pytest --cov=. --cov-report=html --cov-report=term

# Coverage targets
# - Overall coverage: >85%
# - Critical components: >95%
# - New code: 100%
```

### **Performance Benchmarks**

| Metric | Target | Measurement |
|--------|--------|-------------|
| Response Time | <2s average | 95th percentile |
| Throughput | 100 req/sec | Sustained load |
| Database Queries | <100ms | 95th percentile |
| Memory Usage | <512MB | Peak usage |
| CPU Usage | <70% | Average load |

### **Quality Gates**

```yaml
# .github/workflows/quality-gate.yml
quality_checks:
  - name: Unit Tests
    threshold: 100%
    
  - name: Integration Tests
    threshold: 100%
    
  - name: Code Coverage
    threshold: 85%
    
  - name: Security Scan
    threshold: 0 high/critical issues
    
  - name: Performance Tests
    threshold: <2s response time
```

---

**This comprehensive testing guide ensures Aremu maintains high quality, performance, and security standards throughout development and deployment.**
