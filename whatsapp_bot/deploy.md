# Unified Deployment Guide

## Overview
This setup combines the WhatsApp bot (Flask backend) and the frontend into a single Railway deployment.

## Architecture
```
Railway Server (Single Instance)
├── Flask App (Port from $PORT env var)
│   ├── /webhook (WhatsApp webhook endpoints)
│   ├── /health (Health check)
│   ├── /api/* (API endpoints)
│   └── /* (Frontend static files)
└── Frontend Files (served by Flask)
    ├── index.html
    ├── styles.css
    ├── script.js
    └── favicon_io/
```

## Deployment Steps

### 1. Railway Setup
1. Create a new Railway project
2. Connect your GitHub repository
3. Set the root directory to `whatsapp_bot/`
4. Railway will automatically detect Python and use the railway.json config

### 2. Environment Variables
Set these in Railway dashboard:
```
OPENAI_API_KEY=your_openai_api_key
WHATSAPP_ACCESS_TOKEN=your_whatsapp_token
WHATSAPP_PHONE_NUMBER_ID=your_phone_number_id
WHATSAPP_VERIFY_TOKEN=aremu_verify_token
DATABASE_URL=your_supabase_database_url
FLASK_ENV=production
```

### 3. WhatsApp Webhook Configuration
Once deployed, configure your WhatsApp webhook URL:
```
https://your-railway-app.railway.app/webhook
```

### 4. Testing
- Frontend: `https://your-railway-app.railway.app/`
- Health check: `https://your-railway-app.railway.app/health`
- API status: `https://your-railway-app.railway.app/api/status`

## Benefits of Unified Deployment
- ✅ Single server to manage
- ✅ Reduced costs (one Railway instance)
- ✅ Simplified deployment process
- ✅ Shared environment variables
- ✅ Better resource utilization

## File Structure
```
whatsapp_bot/
├── app.py (main Flask app - serves both bot and frontend)
├── frontend/ (copied from ../FE/)
│   ├── index.html
│   ├── styles.css
│   ├── script.js
│   └── favicon_io/
├── requirements.txt
├── railway.json
├── core/
├── services/
├── webhooks/
└── utils/
```

## Local Development
```bash
cd whatsapp_bot
pip install -r requirements.txt
python app.py
```

Access:
- Frontend: http://localhost:5001/
- WhatsApp webhook: http://localhost:5001/webhook
