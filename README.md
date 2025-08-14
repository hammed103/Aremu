# Aremu 🇳🇬

**Stop Searching for Jobs... Let AI do that for You**

Aremu is an AI-powered job search platform that searches the internet 24/7 for Nigerian job opportunities, so you don't have to. Built specifically for the Nigerian job market with comprehensive data extraction and AI enhancement.

## 🚀 Features

### 🤖 AI-Powered Job Discovery
- **24/7 Automated Scraping**: Continuously monitors LinkedIn, JobSpy, and other job boards
- **AI Enhancement**: Uses OpenAI to extract missing job details like skills, compensation, and requirements
- **Smart Categorization**: Automatically classifies jobs by industry, level, and location

### 🇳🇬 Nigerian-Focused
- **Comprehensive Location Coverage**: All major Nigerian cities and states
- **Local Industry Knowledge**: Optimized for Nigerian job market (Banking, Oil & Gas, Tech, etc.)
- **Currency & Compensation**: Handles NGN, USD, and other currencies common in Nigeria

### 📊 Rich Data Processing
- **89+ Job Fields**: Comprehensive job data including direct scraped + AI-inferred fields
- **Data Integrity**: Clear separation between direct data and AI predictions
- **Batch Processing**: Efficient handling of thousands of jobs

## 🏗️ Architecture

```
Aremu/
├── FE/                     # Frontend - AI Job Search Interface
│   ├── index.html         # Main landing page
│   ├── server.js          # Express server for deployment
│   └── railway.json       # Railway deployment config
├── scraper/               # Job data collection
│   ├── linkedin/          # LinkedIn scraper with Nigerian optimization
│   ├── jobspy/           # JobSpy integration
│   └── database/         # Database configuration
├── data_parser/          # Data processing and AI enhancement
│   └── parsers/         # Enhanced job data parsers
└── database/            # Database schemas and migrations
```

## 🛠️ Technology Stack

- **Backend**: Python 3.8+
- **Database**: PostgreSQL (Supabase)
- **AI**: OpenAI GPT-4 for data enhancement
- **Scraping**: Custom scrapers for LinkedIn, JobSpy integration
- **Data Processing**: Pandas, psycopg2

## 📋 Prerequisites

- Python 3.8 or higher
- PostgreSQL database
- OpenAI API key
- Virtual environment (recommended)

## 🚀 Quick Start

### 1. Clone the Repository
```bash
git clone https://github.com/hammed103/Aremu.git
cd Aremu
```

### 2. Set Up Virtual Environment
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Configure Environment
```bash
# Create .env file in data_parser/
echo "OPENAI_API_KEY=your_openai_api_key_here" > data_parser/.env
```

### 4. Run the Enhanced Data Parser
```bash
cd data_parser
python parsers/ai_enhanced_parser.py
```

### 5. Run LinkedIn Scraper
```bash
cd scraper/linkedin
python enhanced_linkedin_scraper.py
```

## 🌐 Frontend Deployment

### Deploy to Railway
```bash
# Navigate to frontend
cd FE

# Deploy to Railway (requires Railway CLI)
railway login
railway init
railway up
```

Or deploy directly from GitHub:
1. Go to [railway.app](https://railway.app)
2. Connect your GitHub repository
3. Set root directory to `FE`
4. Deploy automatically

## 📊 Data Schema

### Raw Jobs Table
Stores original scraped data from various sources.

### Canonical Jobs Table (89+ Fields)
Enhanced job data with both direct and AI-inferred fields:

**Direct Fields**: `title`, `company`, `location`, `salary_min`, `salary_max`, `description`
**AI Fields**: `ai_skills`, `ai_compensation_summary`, `ai_job_level`, `ai_industry`

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Built for the Nigerian job market
- Powered by OpenAI for intelligent data enhancement
- Optimized for comprehensive job discovery

---

**Aremu** - *Because your next opportunity shouldn't wait for you to find it.*
