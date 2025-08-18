# Aremu Frontend 🌐

**AI-Powered Job Search Platform - Frontend**

This is the frontend for Aremu, an AI-powered job search platform focused on the Nigerian job market.

## 🚀 Quick Deploy to Railway

### Option 1: Deploy from GitHub (Recommended)

1. **Push to GitHub** (if not already done):
   ```bash
   git add .
   git commit -m "Organize frontend in FE folder"
   git push origin main
   ```

2. **Deploy on Railway**:
   - Go to [railway.app](https://railway.app)
   - Click "Start a New Project"
   - Select "Deploy from GitHub repo"
   - Choose your `Aremu` repository
   - Set **Root Directory** to `FE`
   - Railway will auto-detect Node.js and deploy

### Option 2: Deploy from Local

1. **Install Railway CLI**:
   ```bash
   npm install -g @railway/cli
   ```

2. **Login and Deploy**:
   ```bash
   cd FE
   railway login
   railway init
   railway up
   ```

## 🛠️ Local Development

### Prerequisites
- Node.js 16+ 
- npm or yarn

### Setup
```bash
cd FE
npm install
npm start
```

The app will be available at `http://localhost:3000`

## 📁 File Structure

```
FE/
├── index.html              # Main landing page
├── styles.css              # Styling
├── script.js               # Frontend JavaScript
├── privacy.html            # Privacy policy page
├── server.js               # Express server for deployment
├── package.json            # Node.js dependencies
├── railway.json            # Railway deployment config
├── .railwayignore          # Files to ignore during deployment
└── zeoob.com_c2gdhjhska_photo.png  # Logo/assets
```

## 🎯 Features

- **Responsive Design**: Works on desktop and mobile
- **Nigerian Focus**: Tailored for Nigerian job seekers
- **WhatsApp Integration**: Direct connection to WhatsApp bot
- **Clean UI**: Modern, professional interface
- **Fast Loading**: Optimized static assets

## 🔧 Configuration

### Environment Variables (Optional)
Create a `.env` file in the FE folder if needed:
```
PORT=3000
NODE_ENV=production
```

### Railway Configuration
The `railway.json` file configures:
- Build process (Nixpacks)
- Start command (`npm start`)
- Restart policy

## 🌐 Deployment URLs

After deployment, your Aremu frontend will be available at:
- Railway: `https://your-app-name.railway.app`
- Custom domain: Configure in Railway dashboard

## 🔗 Backend Integration

This frontend is designed to work with the Aremu backend:
- **Data Parser**: Located in `../data_parser/`
- **Scrapers**: Located in `../scraper/`
- **Database**: PostgreSQL (Supabase)

## 📱 WhatsApp Integration

The frontend includes direct links to WhatsApp for job search:
- Users can start conversations with the AI bot
- Seamless transition from web to WhatsApp
- Nigerian phone number format support

---

**Ready to deploy?** Just push to GitHub and connect to Railway! 🚀
