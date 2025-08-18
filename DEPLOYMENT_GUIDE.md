# 🚀 Aremu Deployment Guide

## 📋 Table of Contents

- [🎯 Deployment Overview](#-deployment-overview)
- [🏗️ Infrastructure Requirements](#️-infrastructure-requirements)
- [🔧 Production Setup](#-production-setup)
- [📊 Database Configuration](#-database-configuration)
- [🔐 Security Configuration](#-security-configuration)
- [📈 Monitoring & Logging](#-monitoring--logging)
- [🔄 CI/CD Pipeline](#-cicd-pipeline)
- [🛠️ Maintenance](#️-maintenance)

## 🎯 Deployment Overview

Aremu can be deployed in multiple configurations:

### **Deployment Options**

| Option | Use Case | Complexity | Cost | Scalability |
|--------|----------|------------|------|-------------|
| **Single Server** | Development/Testing | Low | Low | Limited |
| **Docker Compose** | Small Production | Medium | Medium | Moderate |
| **Kubernetes** | Large Production | High | High | Excellent |
| **Cloud Native** | Enterprise | High | Variable | Excellent |

### **Recommended Production Architecture**

```
┌─────────────────────────────────────────────────────────────────┐
│                        Load Balancer                            │
│                     (nginx/CloudFlare)                         │
└─────────────────────────────────────────────────────────────────┘
                                │
┌─────────────────────────────────────────────────────────────────┐
│                    Application Layer                            │
│                                                                 │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐ │
│  │  WhatsApp Bot   │  │  Data Parser    │  │  Admin Panel    │ │
│  │   (Flask)       │  │   (Python)      │  │   (Optional)    │ │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
                                │
┌─────────────────────────────────────────────────────────────────┐
│                      Data Layer                                 │
│                                                                 │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐ │
│  │   PostgreSQL    │  │   Redis Cache   │  │  File Storage   │ │
│  │   (Primary DB)  │  │   (Sessions)    │  │   (Logs/Backup) │ │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

## 🏗️ Infrastructure Requirements

### **Minimum Requirements**

#### **Single Server Deployment**
- **CPU**: 2 vCPUs
- **RAM**: 4GB
- **Storage**: 50GB SSD
- **Network**: 100 Mbps
- **OS**: Ubuntu 20.04+ / CentOS 8+

#### **Production Deployment**
- **Application Servers**: 2x (4 vCPUs, 8GB RAM each)
- **Database Server**: 1x (4 vCPUs, 16GB RAM, 200GB SSD)
- **Cache Server**: 1x (2 vCPUs, 4GB RAM)
- **Load Balancer**: 1x (2 vCPUs, 2GB RAM)

### **Cloud Provider Recommendations**

#### **AWS Configuration**
```yaml
# Application Servers
EC2 Instance Type: t3.large (2x)
- vCPUs: 2
- RAM: 8GB
- Network: Up to 5 Gbps

# Database
RDS PostgreSQL: db.t3.large
- vCPUs: 2
- RAM: 8GB
- Storage: 200GB gp3

# Cache
ElastiCache Redis: cache.t3.micro
- vCPUs: 2
- RAM: 1GB

# Load Balancer
Application Load Balancer (ALB)
```

#### **DigitalOcean Configuration**
```yaml
# Application Servers
Droplet: s-2vcpu-4gb (2x)
- vCPUs: 2
- RAM: 4GB
- Storage: 80GB SSD

# Database
Managed PostgreSQL: db-s-2vcpu-4gb
- vCPUs: 2
- RAM: 4GB
- Storage: 100GB

# Load Balancer
DigitalOcean Load Balancer
```

## 🔧 Production Setup

### **1. Server Preparation**

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install required packages
sudo apt install -y python3.9 python3.9-venv python3-pip postgresql-client redis-tools nginx git

# Create application user
sudo useradd -m -s /bin/bash aremu
sudo usermod -aG sudo aremu

# Create application directory
sudo mkdir -p /opt/aremu
sudo chown aremu:aremu /opt/aremu
```

### **2. Application Deployment**

```bash
# Switch to application user
sudo su - aremu

# Clone repository
cd /opt/aremu
git clone <repository-url> .

# Create virtual environment
python3.9 -m venv venv
source venv/bin/activate

# Install dependencies
cd whatsapp_bot
pip install -r requirements.txt

cd ../data_parser
pip install -r requirements.txt
```

### **3. Environment Configuration**

```bash
# Create production environment file
cat > /opt/aremu/whatsapp_bot/.env << EOF
# Database
DATABASE_URL=postgresql://aremu_user:secure_password@localhost/aremu_production

# WhatsApp Business API
WHATSAPP_ACCESS_TOKEN=your_production_token
WHATSAPP_PHONE_NUMBER_ID=your_phone_id
WEBHOOK_VERIFY_TOKEN=your_webhook_secret

# OpenAI
OPENAI_API_KEY=your_openai_key

# Production Settings
FLASK_ENV=production
LOG_LEVEL=INFO
MIN_MATCH_SCORE=39
MAX_JOBS_PER_USER_PER_DAY=10

# Security
SECRET_KEY=your_very_secure_secret_key
ADMIN_API_KEY=your_admin_api_key
EOF

# Secure environment file
chmod 600 /opt/aremu/whatsapp_bot/.env
```

### **4. Systemd Service Configuration**

```bash
# WhatsApp Bot Service
sudo cat > /etc/systemd/system/aremu-bot.service << EOF
[Unit]
Description=Aremu WhatsApp Bot
After=network.target postgresql.service

[Service]
Type=simple
User=aremu
Group=aremu
WorkingDirectory=/opt/aremu/whatsapp_bot
Environment=PATH=/opt/aremu/venv/bin
ExecStart=/opt/aremu/venv/bin/python app.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Data Parser Service (for scheduled runs)
sudo cat > /etc/systemd/system/aremu-parser.service << EOF
[Unit]
Description=Aremu Data Parser
After=network.target postgresql.service

[Service]
Type=oneshot
User=aremu
Group=aremu
WorkingDirectory=/opt/aremu/data_parser
Environment=PATH=/opt/aremu/venv/bin
ExecStart=/opt/aremu/venv/bin/python parsers/ai_enhanced_parser.py
EOF

# Timer for regular parsing
sudo cat > /etc/systemd/system/aremu-parser.timer << EOF
[Unit]
Description=Run Aremu Parser every hour
Requires=aremu-parser.service

[Timer]
OnCalendar=hourly
Persistent=true

[Install]
WantedBy=timers.target
EOF

# Enable and start services
sudo systemctl daemon-reload
sudo systemctl enable aremu-bot.service
sudo systemctl enable aremu-parser.timer
sudo systemctl start aremu-bot.service
sudo systemctl start aremu-parser.timer
```

## 📊 Database Configuration

### **PostgreSQL Setup**

```bash
# Install PostgreSQL
sudo apt install -y postgresql postgresql-contrib

# Create database and user
sudo -u postgres psql << EOF
CREATE DATABASE aremu_production;
CREATE USER aremu_user WITH ENCRYPTED PASSWORD 'secure_password';
GRANT ALL PRIVILEGES ON DATABASE aremu_production TO aremu_user;
ALTER USER aremu_user CREATEDB;
\q
EOF

# Configure PostgreSQL for production
sudo nano /etc/postgresql/13/main/postgresql.conf
```

#### **PostgreSQL Production Settings**
```ini
# Memory Settings
shared_buffers = 256MB
effective_cache_size = 1GB
work_mem = 4MB
maintenance_work_mem = 64MB

# Connection Settings
max_connections = 100
listen_addresses = 'localhost'

# Performance Settings
random_page_cost = 1.1
effective_io_concurrency = 200

# Logging
log_min_duration_statement = 1000
log_checkpoints = on
log_connections = on
log_disconnections = on
```

### **Database Initialization**

```bash
# Run database setup
cd /opt/aremu/whatsapp_bot
source ../venv/bin/activate
python -c "
from database_manager import DatabaseManager
db = DatabaseManager()
print('Database initialized successfully!')
"
```

### **Database Backup Strategy**

```bash
# Create backup script
cat > /opt/aremu/scripts/backup_db.sh << EOF
#!/bin/bash
BACKUP_DIR="/opt/aremu/backups"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="aremu_backup_\$DATE.sql"

mkdir -p \$BACKUP_DIR

pg_dump -h localhost -U aremu_user -d aremu_production > \$BACKUP_DIR/\$BACKUP_FILE

# Compress backup
gzip \$BACKUP_DIR/\$BACKUP_FILE

# Keep only last 7 days of backups
find \$BACKUP_DIR -name "*.sql.gz" -mtime +7 -delete

echo "Backup completed: \$BACKUP_FILE.gz"
EOF

chmod +x /opt/aremu/scripts/backup_db.sh

# Schedule daily backups
echo "0 2 * * * /opt/aremu/scripts/backup_db.sh" | sudo crontab -u aremu -
```

## 🔐 Security Configuration

### **Firewall Setup**

```bash
# Configure UFW firewall
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow ssh
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable
```

### **SSL/TLS Configuration**

```bash
# Install Certbot
sudo apt install -y certbot python3-certbot-nginx

# Obtain SSL certificate
sudo certbot --nginx -d your-domain.com

# Auto-renewal
echo "0 12 * * * /usr/bin/certbot renew --quiet" | sudo crontab -
```

### **Nginx Configuration**

```nginx
# /etc/nginx/sites-available/aremu
server {
    listen 80;
    server_name your-domain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your-domain.com;

    ssl_certificate /etc/letsencrypt/live/your-domain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/your-domain.com/privkey.pem;

    # Security headers
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains";

    # Rate limiting
    limit_req_zone $binary_remote_addr zone=webhook:10m rate=10r/s;

    location /webhook {
        limit_req zone=webhook burst=20 nodelay;
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /health {
        proxy_pass http://127.0.0.1:5000;
        access_log off;
    }

    location / {
        return 404;
    }
}
```

### **Application Security**

```python
# Security middleware
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

limiter = Limiter(
    app,
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"]
)

@app.route('/webhook', methods=['POST'])
@limiter.limit("10 per minute")
def webhook():
    # Webhook handling with rate limiting
    pass
```

## 📈 Monitoring & Logging

### **Logging Configuration**

```python
# logging_config.py
import logging
import logging.handlers
import os

def setup_logging():
    """Configure production logging"""
    
    # Create logs directory
    log_dir = '/opt/aremu/logs'
    os.makedirs(log_dir, exist_ok=True)
    
    # Configure root logger
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            # Rotating file handler
            logging.handlers.RotatingFileHandler(
                f'{log_dir}/aremu.log',
                maxBytes=10*1024*1024,  # 10MB
                backupCount=5
            ),
            # Console handler
            logging.StreamHandler()
        ]
    )
    
    # Configure specific loggers
    logging.getLogger('werkzeug').setLevel(logging.WARNING)
    logging.getLogger('urllib3').setLevel(logging.WARNING)
```

### **Health Monitoring**

```bash
# Create monitoring script
cat > /opt/aremu/scripts/health_check.sh << EOF
#!/bin/bash

# Check if services are running
systemctl is-active --quiet aremu-bot.service
BOT_STATUS=\$?

# Check database connectivity
sudo -u aremu psql -h localhost -U aremu_user -d aremu_production -c "SELECT 1;" > /dev/null 2>&1
DB_STATUS=\$?

# Check disk space
DISK_USAGE=\$(df /opt/aremu | awk 'NR==2 {print \$5}' | sed 's/%//')

# Send alerts if needed
if [ \$BOT_STATUS -ne 0 ]; then
    echo "ALERT: WhatsApp Bot service is down" | mail -s "Aremu Alert" admin@yourcompany.com
fi

if [ \$DB_STATUS -ne 0 ]; then
    echo "ALERT: Database connection failed" | mail -s "Aremu Alert" admin@yourcompany.com
fi

if [ \$DISK_USAGE -gt 80 ]; then
    echo "ALERT: Disk usage is \${DISK_USAGE}%" | mail -s "Aremu Alert" admin@yourcompany.com
fi
EOF

chmod +x /opt/aremu/scripts/health_check.sh

# Schedule health checks every 5 minutes
echo "*/5 * * * * /opt/aremu/scripts/health_check.sh" | sudo crontab -u aremu -
```

### **Performance Monitoring**

```python
# metrics.py
import psutil
import time
from datetime import datetime

class SystemMetrics:
    """Collect system performance metrics"""
    
    @staticmethod
    def get_system_metrics():
        """Get current system metrics"""
        return {
            'timestamp': datetime.utcnow().isoformat(),
            'cpu_percent': psutil.cpu_percent(interval=1),
            'memory_percent': psutil.virtual_memory().percent,
            'disk_percent': psutil.disk_usage('/').percent,
            'load_average': psutil.getloadavg()[0],
            'process_count': len(psutil.pids())
        }
    
    @staticmethod
    def get_application_metrics():
        """Get application-specific metrics"""
        # Database connection count
        # Active user sessions
        # Job processing rate
        # Error rates
        pass
```

## 🔄 CI/CD Pipeline

### **GitHub Actions Workflow**

```yaml
# .github/workflows/deploy.yml
name: Deploy to Production

on:
  push:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v3
        with:
          python-version: '3.9'
      - name: Install dependencies
        run: |
          cd whatsapp_bot
          pip install -r requirements.txt
      - name: Run tests
        run: |
          cd whatsapp_bot
          python -m pytest tests/

  deploy:
    needs: test
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    steps:
      - name: Deploy to server
        uses: appleboy/ssh-action@v0.1.5
        with:
          host: ${{ secrets.HOST }}
          username: ${{ secrets.USERNAME }}
          key: ${{ secrets.SSH_KEY }}
          script: |
            cd /opt/aremu
            git pull origin main
            source venv/bin/activate
            pip install -r whatsapp_bot/requirements.txt
            sudo systemctl restart aremu-bot.service
```

### **Deployment Script**

```bash
# deploy.sh
#!/bin/bash
set -e

echo "Starting deployment..."

# Backup current version
cp -r /opt/aremu /opt/aremu.backup.$(date +%Y%m%d_%H%M%S)

# Pull latest code
cd /opt/aremu
git pull origin main

# Update dependencies
source venv/bin/activate
pip install -r whatsapp_bot/requirements.txt
pip install -r data_parser/requirements.txt

# Run database migrations (if any)
cd whatsapp_bot
python database_manager.py

# Restart services
sudo systemctl restart aremu-bot.service

# Verify deployment
sleep 5
if systemctl is-active --quiet aremu-bot.service; then
    echo "Deployment successful!"
else
    echo "Deployment failed! Rolling back..."
    sudo systemctl stop aremu-bot.service
    # Restore backup and restart
    exit 1
fi
```

## 🛠️ Maintenance

### **Regular Maintenance Tasks**

```bash
# Weekly maintenance script
cat > /opt/aremu/scripts/weekly_maintenance.sh << EOF
#!/bin/bash

echo "Starting weekly maintenance..."

# Clean old logs
find /opt/aremu/logs -name "*.log.*" -mtime +30 -delete

# Vacuum database
sudo -u aremu psql -h localhost -U aremu_user -d aremu_production -c "VACUUM ANALYZE;"

# Update system packages
sudo apt update && sudo apt upgrade -y

# Restart services
sudo systemctl restart aremu-bot.service

echo "Weekly maintenance completed."
EOF

# Schedule weekly maintenance
echo "0 3 * * 0 /opt/aremu/scripts/weekly_maintenance.sh" | sudo crontab -u root -
```

### **Troubleshooting Commands**

```bash
# Check service status
sudo systemctl status aremu-bot.service

# View logs
sudo journalctl -u aremu-bot.service -f

# Check application logs
tail -f /opt/aremu/logs/aremu.log

# Database connection test
sudo -u aremu psql -h localhost -U aremu_user -d aremu_production -c "SELECT COUNT(*) FROM users;"

# Check disk space
df -h /opt/aremu

# Check memory usage
free -h

# Check process status
ps aux | grep python
```

---

**This deployment guide provides a comprehensive production setup for Aremu with security, monitoring, and maintenance best practices.**
