# Railway Multi-Service Deployment Guide

## Overview
Deploy the complete Aremu job platform with multiple services on Railway:

1. **WhatsApp Bot Service** - Handles user conversations
2. **AI Parser Service** - Processes jobs with AI every 2 hours  
3. **Frontend Service** - Static website
4. **Scraper Service** - Integrated into WhatsApp Bot

## Service Architecture

```
Railway Project: Aremu Job Platform
├── WhatsApp Bot Service (whatsapp_bot/)
│   ├── Flask app for conversations
│   ├── Scraper service (JobSpy, LinkedIn, etc.)
│   └── Real-time job delivery
├── AI Parser Service (ai_parser_service/)
│   ├── Scheduled AI enhancement (every 2 hours)
│   ├── Smart delivery engine
│   └── Job processing automation
└── Frontend Service (frontend/)
    └── Static website
```

## Deployment Steps

### 1. WhatsApp Bot Service

**Directory:** `whatsapp_bot/`
**Purpose:** Main Flask app + scrapers

```bash
# Service Configuration
Service Name: whatsapp-bot
Root Directory: whatsapp_bot
Start Command: gunicorn app:app --bind 0.0.0.0:$PORT --workers 2 --timeout 120
Service Type: Web Service
```

**Environment Variables:**
```
DATABASE_URL=postgresql://...
OPENAI_API_KEY=your_key
WHATSAPP_TOKEN=your_token
WHATSAPP_PHONE_ID=your_phone_id
FLASK_ENV=production
PORT=8080
```

**Features:**
- ✅ WhatsApp conversations
- ✅ Job search and delivery
- ✅ User preference management
- ✅ Scraper service (JobSpy, LinkedIn every 6-8 hours)
- ✅ Real-time job alerts

### 2. AI Parser Service (NEW)

**Directory:** `ai_parser_service/`
**Purpose:** Scheduled AI processing

```bash
# Service Configuration
Service Name: ai-parser-scheduler
Root Directory: ai_parser_service
Start Command: python scheduler_service.py
Service Type: Worker Service
```

**Environment Variables:**
```
DATABASE_URL=postgresql://...
OPENAI_API_KEY=your_key
WHATSAPP_TOKEN=your_token
WHATSAPP_PHONE_ID=your_phone_id
SERVICE_TYPE=AI_PARSER_SCHEDULER
PYTHONPATH=/app
```

**Features:**
- ✅ Runs every 2 hours automatically
- ✅ AI enhancement with OpenAI
- ✅ Smart delivery to eligible users
- ✅ WhatsApp job alerts
- ✅ Comprehensive logging

### 3. Frontend Service

**Directory:** `frontend/`
**Purpose:** Static website

```bash
# Service Configuration
Service Name: frontend
Root Directory: frontend
Start Command: node server.js
Service Type: Web Service
```

## What Each Service Does

### WhatsApp Bot Service:
- **Primary Function:** Handle user conversations
- **Scrapers:** JobSpy (6h), LinkedIn (8h), Indeed, Prosple
- **Real-time:** Immediate job delivery when users search
- **API Endpoints:** WhatsApp webhooks, job search, preferences

### AI Parser Service:
- **Primary Function:** Batch process jobs with AI
- **Schedule:** Every 2 hours
- **Processing:** All recent jobs (14-day filter)
- **Delivery:** Smart delivery to eligible users
- **Enhancement:** AI summaries, contact extraction, matching

### Frontend Service:
- **Primary Function:** Static website
- **Features:** Job search interface, company info
- **Technology:** HTML, CSS, JavaScript, Node.js server

## Deployment Commands

### Deploy All Services:

```bash
# 1. Deploy WhatsApp Bot
cd whatsapp_bot
railway up --service whatsapp-bot

# 2. Deploy AI Parser Service  
cd ../ai_parser_service
railway up --service ai-parser-scheduler

# 3. Deploy Frontend
cd ../frontend
railway up --service frontend
```

### Alternative: Use Railway Dashboard

1. **Create New Project** in Railway
2. **Add Service** → **GitHub Repo** (3 times)
3. **Configure each service** with correct root directory
4. **Set environment variables** for each service
5. **Deploy**

## Service Communication

- **Shared Database:** All services use the same PostgreSQL database
- **Job Flow:** Scrapers → Raw Jobs → AI Parser → Enhanced Jobs → WhatsApp Delivery
- **User Data:** Shared user preferences and job tracking

## Monitoring

### WhatsApp Bot Service:
- Check `/health` endpoint
- Monitor conversation logs
- Verify scraper execution

### AI Parser Service:
- Monitor Railway logs for 2-hour cycles
- Check job processing statistics
- Verify WhatsApp alert delivery

### Frontend Service:
- Check website accessibility
- Monitor static file serving

## Benefits of Multi-Service Architecture

1. **Separation of Concerns:**
   - WhatsApp Bot: Real-time conversations
   - AI Parser: Batch processing
   - Frontend: Static content

2. **Independent Scaling:**
   - Scale conversation handling separately
   - Scale AI processing independently
   - Scale frontend based on traffic

3. **Fault Isolation:**
   - If AI parser fails, conversations still work
   - If WhatsApp bot fails, AI processing continues
   - Independent restart policies

4. **Resource Optimization:**
   - WhatsApp Bot: Always running (web service)
   - AI Parser: Scheduled execution (worker service)
   - Frontend: Lightweight static serving

## Cost Optimization

- **WhatsApp Bot:** Web service (higher cost, always running)
- **AI Parser:** Worker service (lower cost, scheduled)
- **Frontend:** Static service (lowest cost)

## Success Metrics

Monitor these across all services:
- ✅ WhatsApp conversations working
- ✅ Scrapers running every 6-8 hours
- ✅ AI parser running every 2 hours
- ✅ Job alerts being delivered
- ✅ Frontend accessible
- ✅ Database shared correctly

This multi-service architecture provides the best of both worlds: real-time conversations and automated batch processing! 🚀
