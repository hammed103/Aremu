# Aremu WhatsApp AI Bot 🤖📱

**Intelligent Job Search Conversations via WhatsApp**

This Flask application provides an AI-powered WhatsApp bot that helps Nigerians find jobs through natural conversations.

## 🚀 Features

- **Two-way AI Conversations**: Intelligent responses using OpenAI GPT-4
- **WhatsApp Integration**: Native WhatsApp Business API support
- **Nigerian Job Focus**: Specialized knowledge of Nigerian job market
- **Conversation Memory**: Maintains context across messages
- **Real-time Processing**: Instant responses to user queries

## 🛠️ Setup Instructions

### 1. WhatsApp Business API Setup

1. **Create Meta Developer Account**:
   - Go to [developers.facebook.com](https://developers.facebook.com)
   - Create a new app with WhatsApp Business API

2. **Get Required Credentials**:
   - `WHATSAPP_ACCESS_TOKEN`: From your Meta app dashboard
   - `WHATSAPP_PHONE_NUMBER_ID`: Your WhatsApp Business phone number ID
   - `WHATSAPP_VERIFY_TOKEN`: Create a custom verification token

### 2. Environment Setup

1. **Copy environment file**:
   ```bash
   cp .env.example .env
   ```

2. **Fill in your credentials**:
   ```bash
   # Edit .env file with your actual values
   OPENAI_API_KEY=sk-your-openai-key
   WHATSAPP_ACCESS_TOKEN=your-whatsapp-token
   WHATSAPP_PHONE_NUMBER_ID=your-phone-id
   WHATSAPP_VERIFY_TOKEN=your-custom-verify-token
   ```

### 3. Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Run the Flask app
python app.py
```

The bot will be available at `http://localhost:5000`

### 4. Webhook Configuration

1. **Deploy to a public URL** (Railway, Heroku, etc.)
2. **Set webhook URL** in Meta Developer Console:
   - Webhook URL: `https://your-app-url.com/webhook`
   - Verify Token: Your `WHATSAPP_VERIFY_TOKEN`

## 📡 API Endpoints

### `GET /`
Health check endpoint
```json
{
  "status": "active",
  "service": "Aremu WhatsApp AI Bot",
  "timestamp": "2024-08-14T18:00:00"
}
```

### `GET /webhook`
WhatsApp webhook verification

### `POST /webhook`
Handles incoming WhatsApp messages

### `POST /send`
Manual message sending (for testing)
```json
{
  "phone_number": "2348123456789",
  "message": "Hello from Aremu!"
}
```

## 🤖 AI Capabilities

The bot can help with:
- **Job Search**: Finding relevant opportunities in Nigeria
- **Career Advice**: Professional guidance and tips
- **CV/Resume Help**: Writing and improvement suggestions
- **Interview Prep**: Practice questions and tips
- **Company Information**: Details about Nigerian employers
- **Industry Insights**: Market trends and opportunities

## 📱 WhatsApp Message Flow

1. **User sends message** → WhatsApp → Webhook
2. **Bot processes message** → OpenAI API → AI Response
3. **Bot sends reply** → WhatsApp API → User receives response

## 🔧 Configuration

### Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `OPENAI_API_KEY` | OpenAI API key for AI responses | Yes |
| `WHATSAPP_ACCESS_TOKEN` | WhatsApp Business API token | Yes |
| `WHATSAPP_PHONE_NUMBER_ID` | WhatsApp phone number ID | Yes |
| `WHATSAPP_VERIFY_TOKEN` | Custom webhook verification token | Yes |
| `PORT` | Server port (default: 5000) | No |

### Conversation Storage

Currently stores conversations in memory. For production:
- Add database integration (PostgreSQL recommended)
- Implement conversation persistence
- Add user session management

## 🚀 Deployment

### Railway Deployment
```bash
# Connect to Railway
railway login
railway init
railway up

# Set environment variables in Railway dashboard
```

### Heroku Deployment
```bash
# Create Heroku app
heroku create aremu-whatsapp-bot

# Set environment variables
heroku config:set OPENAI_API_KEY=your-key
heroku config:set WHATSAPP_ACCESS_TOKEN=your-token

# Deploy
git push heroku main
```

## 🔍 Testing

### Test Webhook Verification
```bash
curl "https://your-app-url.com/webhook?hub.mode=subscribe&hub.verify_token=your-verify-token&hub.challenge=test"
```

### Test Manual Message Sending
```bash
curl -X POST https://your-app-url.com/send \
  -H "Content-Type: application/json" \
  -d '{"phone_number": "2348123456789", "message": "Test message"}'
```

## 📊 Monitoring

- **Logs**: Check `whatsapp_bot.log` for detailed activity
- **Health Check**: Monitor `/` endpoint for uptime
- **WhatsApp Status**: Monitor webhook delivery in Meta dashboard

## 🔮 Future Enhancements

- [ ] Job search integration with database
- [ ] User profile management
- [ ] Job alerts and notifications
- [ ] Multi-language support
- [ ] Analytics and usage tracking
- [ ] Rich media support (images, documents)

---

**Ready to help Nigerians find their dream jobs through WhatsApp!** 🇳🇬🚀
