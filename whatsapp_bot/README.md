# 🤖 Aremu - Intelligent WhatsApp Job Search Bot

An AI-powered WhatsApp bot that helps Nigerians find their perfect jobs through natural conversation and intelligent preference learning.

## ✨ Features

### 🧠 **Intelligent AI Agent**
- **Natural conversation** - No rigid forms or preset responses
- **Context-aware responses** - Adapts based on user's profile completeness
- **Smart questioning** - Only asks for missing information
- **Flexible interaction** - Handles any language patterns naturally

### 🎯 **Advanced Preference Learning**
- **AI-powered extraction** - Detects preferences from natural language
- **Progressive profiling** - Builds user profile over time
- **Smart mapping** - "Naira" → "NGN", "part-time" → proper format
- **Real-time updates** - Saves preferences as conversation flows

### 💾 **Enterprise Database Integration**
- **User management** - Names, phone numbers, activity tracking
- **Preference storage** - Job type, employment type, salary, location
- **Conversation history** - Persistent memory across sessions
- **Multi-user support** - Individual contexts for each user

### 📱 **WhatsApp Integration**
- **Real-time messaging** - Instant responses via WhatsApp API
- **Message status tracking** - Delivery confirmations
- **Multi-format support** - Text messages with future media support

## 🚀 Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Environment Setup
Create `.env` file:
```env
OPENAI_API_KEY=your_openai_api_key
WHATSAPP_ACCESS_TOKEN=your_whatsapp_access_token
WHATSAPP_PHONE_NUMBER_ID=your_phone_number_id
```

### 3. Run the Bot
```bash
python app.py
```

The bot will start on `http://localhost:5001`

## 🗄️ Database Schema

### Users Table
- `id` - Primary key
- `phone_number` - WhatsApp phone number
- `name` - User's name (extracted from conversation)
- `message_count` - Total messages sent
- `last_active` - Last activity timestamp

### User Preferences Table
- `job_type` - Software developer, marketing, etc.
- `employment_type` - Full-time, part-time, contract
- `salary_currency` - NGN, USD
- `location_preference` - Lagos, remote, etc.
- `experience_level` - Entry, mid, senior

### Conversations Table
- Complete message history with timestamps
- Session tracking for context

## 🔧 API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/webhook` | POST | WhatsApp message webhook |
| `/webhook` | GET | Webhook verification |

## 🌟 How It Works

1. **User sends message** → WhatsApp webhook
2. **AI analyzes message** → Extracts preferences + generates response
3. **Database updates** → Saves preferences and conversation
4. **Response sent** → Natural, contextual reply via WhatsApp

## 🎭 Example Conversations

### New User
**User**: *"Hi, I'm looking for a job"*  
**Aremu**: *"Hello! I'd love to help you find the perfect job. What type of work interests you most?"*

### Experienced User
**User**: *"Any new marketing jobs?"*  
**Aremu**: *"Hi Sarah! I can definitely help with marketing roles. Would you prefer full-time or part-time?"*

### Complete Profile
**User**: *"Show me jobs"*  
**Aremu**: *"Hi Mike! Here are 3 fresh customer service jobs in Lagos..."* (Shows actual listings)

## 🚀 Deployment

### Railway (Recommended)
```bash
railway login
railway init
railway up
```

### Environment Variables Required
- `OPENAI_API_KEY`
- `WHATSAPP_ACCESS_TOKEN`
- `WHATSAPP_PHONE_NUMBER_ID`
- `DATABASE_URL` (auto-provided by hosting platforms)

## 📁 Project Structure

```
whatsapp_bot/
├── app.py                 # Main Flask application
├── database_manager.py    # Database operations
├── requirements.txt       # Python dependencies
├── Procfile              # Deployment configuration
├── railway.json          # Railway deployment config
├── config/
│   └── database_schema.sql # Database schema
└── README.md             # This documentation
```

## 🔮 Future Enhancements

- [ ] Job scraping integration
- [ ] Resume upload and parsing
- [ ] Interview scheduling
- [ ] Salary negotiation tips
- [ ] Company reviews and insights
- [ ] Multi-language support

---

**Built with ❤️ for Nigerian job seekers**
