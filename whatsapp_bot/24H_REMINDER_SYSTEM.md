# 🕐 24-Hour Window Reminder System

## 🎯 **Problem Solved**

WhatsApp Business API has a **24-hour messaging window** - you can only send messages to users for 24 hours after their last message. This system ensures users stay engaged and don't lose instant job alerts.

## 🧠 **Smart Reminder Strategy**

### **Progressive Urgency Messages:**

1. **16 hours elapsed (8h remaining)** - Friendly check-in
   - "📊 Market Update for you! I've been monitoring for 16 hours..."
   - Shows jobs sent count if any

2. **19 hours elapsed (5h remaining)** - Personalized summary  
   - "🤖 Your job-hunting buddy checking in! Delivered X matches..."

3. **21 hours elapsed (3h remaining)** - Building urgency
   - "⚠️ Don't miss out! Only 3 hours left of instant alerts..."
   - Explains what happens when bot "sleeps"

4. **23 hours elapsed (1h remaining)** - High urgency
   - "🔋 FINAL HOUR ALERT! Others get the speed advantage..."

5. **23h 45min elapsed (15min remaining)** - MAXIMUM urgency
   - "🚨 LAST CALL - 15 MINUTES! SEND ANY MESSAGE NOW!"

## 🏗️ **System Architecture**

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Main Bot      │    │  Reminder        │    │   Database      │
│   (app.py)      │    │  Daemon          │    │                 │
│                 │    │                  │    │                 │
│ • Handles msgs  │    │ • Monitors users │    │ • users table   │
│ • Updates       │◄──►│ • Sends reminders│◄──►│ • last_active   │
│   last_active   │    │ • Logs reminders │    │ • reminder_log  │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

## 📁 **Files Created**

### **Core System:**
- `services/reminder_service.py` - Main reminder logic
- `reminder_daemon.py` - Background service that runs 24/7
- `aremu-reminder.service` - Systemd service file

### **Database Updates:**
- Added `update_user_activity()` method to track user interactions
- Creates `reminder_log` table to prevent duplicate reminders

## 🚀 **Deployment Options**

### **Option 1: Railway (Recommended)**
```bash
# Add to your existing Railway deployment
# Railway will run both the main app AND the reminder daemon
```

### **Option 2: Separate Server**
```bash
# Install on Ubuntu/Debian server
sudo cp aremu-reminder.service /etc/systemd/system/
sudo systemctl enable aremu-reminder
sudo systemctl start aremu-reminder
```

### **Option 3: Docker**
```dockerfile
# Add to your Dockerfile
CMD ["python", "reminder_daemon.py"]
```

## 🧪 **Testing**

```bash
# Test single cycle
python reminder_daemon.py test

# Check health
python reminder_daemon.py health

# View logs
tail -f /var/log/aremu-reminder.log
```

## ⚙️ **Configuration**

### **Environment Variables:**
```bash
WHATSAPP_ACCESS_TOKEN=your_token
WHATSAPP_PHONE_NUMBER_ID=your_phone_id  
DATABASE_URL=your_database_url
OPENAI_API_KEY=your_openai_key
```

### **Reminder Schedule:**
- Check every **5 minutes** for users needing reminders
- Send reminders at: 8h, 5h, 3h, 1h, 15min remaining
- Prevents duplicate reminders using `reminder_log` table

## 📊 **Monitoring**

### **Key Metrics to Track:**
- Users receiving reminders per day
- Response rate after reminders
- 24-hour window "saves" (users who respond)
- Jobs sent vs. reminder effectiveness

### **Logs to Monitor:**
```bash
# Reminder daemon logs
grep "Sent.*reminders" /var/log/aremu-reminder.log

# User activity updates
grep "Update user activity" /var/log/aremu-bot.log
```

## 🎯 **Expected Results**

### **User Behavior:**
- **Higher engagement** - Users reminded to stay active
- **Reduced churn** - Don't lose users to 24h window
- **Better job delivery** - More users get instant alerts
- **Competitive advantage** - Users stay ahead of others

### **Business Impact:**
- **Increased retention** - Users stay engaged longer
- **More job applications** - Users see more opportunities  
- **Better user experience** - Clear communication about limitations
- **Reduced support** - Users understand the system

## 🔧 **Maintenance**

### **Daily Tasks:**
- Monitor reminder logs for errors
- Check database for reminder_log growth
- Verify daemon is running

### **Weekly Tasks:**
- Analyze reminder effectiveness
- Adjust reminder timing if needed
- Clean old reminder logs

## 🚨 **Troubleshooting**

### **Common Issues:**
1. **Daemon not running** - Check systemd status
2. **Database connection** - Verify DATABASE_URL
3. **WhatsApp API errors** - Check token validity
4. **Duplicate reminders** - Check reminder_log table

### **Quick Fixes:**
```bash
# Restart daemon
sudo systemctl restart aremu-reminder

# Check status
sudo systemctl status aremu-reminder

# View recent logs
journalctl -u aremu-reminder -f
```

## ✅ **Success Metrics**

- **90%+ users** respond within 24 hours after first reminder
- **50%+ reduction** in users lost to 24h window
- **25%+ increase** in job application rates
- **Zero duplicate** reminders sent

Your 24-hour window reminder system is ready! 🎉
