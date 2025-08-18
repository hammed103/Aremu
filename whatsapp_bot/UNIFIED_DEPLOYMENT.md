# 🚀 Unified WhatsApp Bot + Frontend Deployment

## ✅ Setup Complete!

Your WhatsApp bot and frontend are now configured to run on a single Railway server.

## 📁 What Was Done

### 1. **Modified Flask App** (`app.py`)
- Added frontend static file serving
- Added routes for serving the website
- Configured to serve both WhatsApp webhook and frontend

### 2. **Copied Frontend Files**
- Copied all files from `../FE/` to `whatsapp_bot/frontend/`
- Includes: HTML, CSS, JS, favicon, and all assets

### 3. **Updated Configuration**
- Enhanced `railway.json` for production deployment
- Flask app now serves both backend API and frontend

## 🌐 URL Structure

When deployed, your single Railway app will serve:

```
https://your-app.railway.app/
├── /                    → Frontend (index.html)
├── /styles.css          → Frontend CSS
├── /script.js           → Frontend JavaScript  
├── /favicon_io/         → Favicon files
├── /webhook             → WhatsApp webhook (GET/POST)
├── /health              → Health check endpoint
└── /api/status          → API status for frontend
```

## 🚀 Deployment Instructions

### Railway Deployment:
1. **Create Railway Project**
   - Connect your GitHub repo
   - Set root directory to: `whatsapp_bot/`

2. **Environment Variables** (Set in Railway dashboard):
   ```
   OPENAI_API_KEY=your_openai_key
   WHATSAPP_ACCESS_TOKEN=your_whatsapp_token
   WHATSAPP_PHONE_NUMBER_ID=your_phone_id
   WHATSAPP_VERIFY_TOKEN=aremu_verify_token
   DATABASE_URL=your_supabase_url
   FLASK_ENV=production
   ```

3. **Deploy**
   - Railway will automatically build and deploy
   - Uses `gunicorn` for production serving

### WhatsApp Configuration:
- Set webhook URL to: `https://your-app.railway.app/webhook`
- Verify token: `aremu_verify_token`

## 🧪 Local Testing

```bash
cd whatsapp_bot
pip install -r requirements.txt
python app.py
```

Then visit:
- Frontend: http://localhost:5001/
- Health: http://localhost:5001/health

## 💰 Benefits

- **Cost Effective**: Single Railway instance instead of two
- **Simplified**: One deployment, one domain, one set of environment variables
- **Efficient**: Shared resources between frontend and backend
- **Maintainable**: All code in one place

## 📊 Resource Usage

- **Memory**: ~512MB (Flask + static files)
- **CPU**: Minimal (serves static files efficiently)
- **Storage**: ~50MB (app + frontend assets)

## 🔧 Technical Details

- **Framework**: Flask (Python)
- **Server**: Gunicorn (production)
- **Static Files**: Served directly by Flask
- **Routing**: SPA-friendly (fallback to index.html)
- **Port**: Dynamic (from Railway's $PORT env var)

Your unified deployment is ready! 🎉
