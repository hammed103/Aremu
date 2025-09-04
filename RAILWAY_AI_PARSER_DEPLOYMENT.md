# Railway AI Enhanced Parser Deployment Guide

## Overview
Deploy the AI Enhanced Parser to Railway to run automatically every 2 hours, processing job data and enhancing it with AI.

## Deployment Options

### Option 1: Scheduled Service (Recommended)
Runs continuously with 2-hour intervals.

### Option 2: Standalone Service
Runs once and exits (for manual triggering or external cron).

## Railway Deployment Steps

### 1. Create New Railway Service

1. Go to [Railway Dashboard](https://railway.app/dashboard)
2. Click "New Project" → "Deploy from GitHub repo"
3. Select your repository
4. Choose "Add Service" → "GitHub Repo"

### 2. Configure Service for AI Parser

#### For Scheduled Service (Option 1):
```bash
# Service Name: ai-parser-scheduler
# Root Directory: whatsapp_bot
# Build Command: (leave empty - uses Nixpacks)
# Start Command: python scheduler_service.py
```

#### For Standalone Service (Option 2):
```bash
# Service Name: ai-parser-standalone  
# Root Directory: whatsapp_bot
# Build Command: (leave empty - uses Nixpacks)
# Start Command: python ai_parser_standalone.py
```

### 3. Environment Variables

Add these environment variables to your Railway service:

```bash
# Database
DATABASE_URL=postgresql://username:password@host:port/database

# OpenAI
OPENAI_API_KEY=your_openai_api_key

# WhatsApp (for smart delivery)
WHATSAPP_TOKEN=your_whatsapp_token
WHATSAPP_PHONE_ID=your_phone_id

# Service Type
SERVICE_TYPE=AI_PARSER_SCHEDULER
PYTHONPATH=/app
```

### 4. Railway Configuration Files

Use the appropriate railway configuration:

#### For Scheduled Service:
Copy `railway-parser.json` to `railway.json` in the whatsapp_bot directory.

#### For Standalone Service:
```json
{
  "$schema": "https://railway.app/railway.schema.json",
  "build": {
    "builder": "NIXPACKS"
  },
  "deploy": {
    "startCommand": "python ai_parser_standalone.py",
    "restartPolicyType": "NEVER"
  }
}
```

## Service Features

### Scheduled Service (`scheduler_service.py`)
- ✅ Runs every 2 hours automatically
- ✅ Processes all recent jobs (14-day filter)
- ✅ Includes smart delivery engine
- ✅ Comprehensive logging
- ✅ Error recovery and retries
- ✅ Runs immediately on startup

### Standalone Service (`ai_parser_standalone.py`)
- ✅ Runs once and exits
- ✅ Processes all recent jobs (14-day filter)
- ✅ Perfect for manual triggering
- ✅ Lightweight and fast

## Monitoring

### Logs
Both services provide detailed logging:
- Processing statistics
- AI enhancement results
- Error tracking
- Performance metrics

### Railway Dashboard
Monitor your service through Railway dashboard:
- Service health
- Resource usage
- Deployment logs
- Environment variables

## Scaling Considerations

### Resource Requirements
- **Memory**: 512MB - 1GB recommended
- **CPU**: 0.5 vCPU sufficient
- **Storage**: Minimal (logs only)

### Cost Optimization
- Scheduled service runs continuously (higher cost)
- Standalone service runs on-demand (lower cost)
- Consider using Railway's cron jobs for cost-effective scheduling

## Troubleshooting

### Common Issues

1. **Database Connection Errors**
   - Verify DATABASE_URL is correct
   - Check database accessibility from Railway

2. **OpenAI API Errors**
   - Verify OPENAI_API_KEY is valid
   - Check API quota and billing

3. **Import Errors**
   - Ensure PYTHONPATH=/app is set
   - Verify all dependencies in requirements.txt

### Debug Commands

```bash
# Check service logs
railway logs

# Connect to service shell
railway shell

# Test database connection
python -c "from data_parser.parsers.ai_enhanced_parser import AIEnhancedJobParser; parser = AIEnhancedJobParser()"
```

## Manual Deployment Commands

```bash
# Deploy scheduled service
railway up --service ai-parser-scheduler

# Deploy standalone service  
railway up --service ai-parser-standalone

# Update environment variables
railway variables set OPENAI_API_KEY=your_key
```

## Success Metrics

Monitor these metrics to ensure successful deployment:
- ✅ Service starts without errors
- ✅ Database connection established
- ✅ Jobs are being processed every 2 hours
- ✅ AI enhancement working
- ✅ Smart delivery sending alerts
- ✅ No memory/CPU issues

## Next Steps

After successful deployment:
1. Monitor logs for first few runs
2. Verify job processing statistics
3. Check smart delivery alerts are being sent
4. Set up alerting for service failures
5. Consider adding health check endpoints
