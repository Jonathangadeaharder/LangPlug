# LangPlug Backend - Deployment Guide

**Version**: 1.0
**Last Updated**: 2025-10-03

Complete guide for deploying LangPlug Backend to production environments.

---

## Table of Contents

1. [Deployment Overview](#deployment-overview)
2. [Prerequisites](#prerequisites)
3. [Production Configuration](#production-configuration)
4. [Deployment Methods](#deployment-methods)
5. [Database Setup](#database-setup)
6. [Reverse Proxy Configuration](#reverse-proxy-configuration)
7. [SSL/TLS Setup](#ssl-tls-setup)
8. [Process Management](#process-management)
9. [Health Checks](#health-checks)
10. [Rollback Procedures](#rollback-procedures)

---

## Deployment Overview

### Deployment Architecture

```
                                 ┌─────────────┐
                                 │   Internet  │
                                 └──────┬──────┘
                                        │
                              ┌─────────▼────────────┐
                              │   Load Balancer      │
                              │   (Optional)         │
                              └─────────┬────────────┘
                                        │
                              ┌─────────▼────────────┐
                              │   Reverse Proxy      │
                              │   (Nginx/Traefik)    │
                              │   - SSL Termination  │
                              │   - Static Files     │
                              └─────────┬────────────┘
                                        │
                      ┌─────────────────┼────────────────────┐
                      │                 │                    │
            ┌─────────▼───────┐  ┌─────▼──────┐  ┌─────────▼──────┐
            │   Uvicorn #1    │  │ Uvicorn #2 │  │   Uvicorn #N   │
            │   (Worker)      │  │  (Worker)  │  │    (Worker)    │
            └─────────┬───────┘  └─────┬──────┘  └────────┬───────┘
                      │                 │                   │
                      └─────────────────┼───────────────────┘
                                        │
                              ┌─────────▼────────────┐
                              │    PostgreSQL        │
                              │    (Database)        │
                              └──────────────────────┘
```

### Recommended Stack

- **OS**: Ubuntu 22.04 LTS
- **Python**: 3.11+
- **Web Server**: Nginx (reverse proxy)
- **App Server**: Uvicorn with multiple workers
- **Process Manager**: Systemd or Supervisor
- **Database**: PostgreSQL 14+
- **SSL**: Let's Encrypt (Certbot)

---

## Prerequisites

### Server Requirements

**Minimum** (Small deployment, <100 users):

- 2 CPU cores
- 4GB RAM
- 50GB SSD
- Ubuntu 22.04 LTS

**Recommended** (Production, 1000+ users):

- 4-8 CPU cores
- 16GB RAM
- 200GB SSD (AI models + videos require space)
- Ubuntu 22.04 LTS

**GPU** (Optional, for faster AI processing):

- NVIDIA GPU with 8GB+ VRAM
- CUDA 11.8+
- cuDNN 8.x

### Domain & DNS

- Domain name registered
- DNS A record pointing to server IP
- Optional: CDN for static assets

---

## Production Configuration

### Environment Variables

Create `/etc/langplug/.env.production`:

```bash
# Application
LANGPLUG_HOST=127.0.0.1  # Bind to localhost (Nginx proxies)
LANGPLUG_PORT=8000
LANGPLUG_DEBUG=False  # CRITICAL: Must be False
LANGPLUG_ENVIRONMENT=production

# Paths
LANGPLUG_VIDEOS_PATH=/var/lib/langplug/videos
LANGPLUG_DATA_PATH=/var/lib/langplug/data
LANGPLUG_LOGS_PATH=/var/log/langplug

# Security (USE SECRETS MANAGER)
LANGPLUG_SECRET_KEY=${SECRET_KEY_FROM_VAULT}
LANGPLUG_SESSION_TIMEOUT_HOURS=8
LANGPLUG_CORS_ORIGINS=https://app.langplug.com

# Database (PostgreSQL)
DATABASE_URL=postgresql+asyncpg://langplug_user:${DB_PASSWORD}@localhost:5432/langplug

# AI Services (Production models)
LANGPLUG_TRANSCRIPTION_SERVICE=whisper
LANGPLUG_TRANSCRIPTION_MODEL=medium  # Or small for lower resource usage
LANGPLUG_TRANSLATION_SERVICE=opus

# Logging
LANGPLUG_LOG_LEVEL=WARNING  # Only warnings and errors in production
LANGPLUG_LOG_FORMAT=json  # For log aggregation (ELK, etc.)

# Optional: Redis for caching
REDIS_URL=redis://:${REDIS_PASSWORD}@localhost:6379/0

# Optional: Rate limiting
LANGPLUG_RATE_LIMIT_ENABLED=True
```

### Security Hardening

```bash
# Set proper file permissions
sudo chown -R langplug:langplug /var/lib/langplug
sudo chmod 700 /etc/langplug
sudo chmod 600 /etc/langplug/.env.production

# Restrict log access
sudo chown -R langplug:adm /var/log/langplug
sudo chmod 750 /var/log/langplug
```

---

## Deployment Methods

### Method 1: Manual Deployment (Simple)

**Step 1**: Prepare server

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install dependencies
sudo apt install -y python3.11 python3.11-venv python3-pip \
  postgresql postgresql-contrib nginx git ffmpeg

# Create application user
sudo useradd -m -s /bin/bash langplug
sudo usermod -aG sudo langplug
```

**Step 2**: Clone and setup application

```bash
# Switch to langplug user
sudo su - langplug

# Clone repository
git clone https://github.com/your-org/LangPlug.git /home/langplug/app
cd /home/langplug/app/Backend

# Create virtual environment
python3.11 -m venv venv
source venv/bin/activate

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Install AI models
python install_spacy_models.py
```

**Step 3**: Configure application

```bash
# Create config directory
sudo mkdir -p /etc/langplug
sudo cp .env.example /etc/langplug/.env.production

# Edit configuration
sudo nano /etc/langplug/.env.production
# (Update with production values)

# Create data directories
sudo mkdir -p /var/lib/langplug/{data,videos}
sudo chown -R langplug:langplug /var/lib/langplug

# Create log directory
sudo mkdir -p /var/log/langplug
sudo chown -R langplug:adm /var/log/langplug
```

**Step 4**: Setup database

```bash
# See "Database Setup" section below
```

**Step 5**: Setup systemd service

```bash
# See "Process Management" section below
```

### Method 2: Docker Deployment (Recommended)

**Dockerfile** (create in `Backend/`):

```dockerfile
FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    ffmpeg \
    git \
    && rm -rf /var/lib/apt/lists/*

# Create app user
RUN useradd -m -s /bin/bash langplug

# Set working directory
WORKDIR /app

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Install AI models
RUN python install_spacy_models.py

# Switch to non-root user
USER langplug

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD python -c "import requests; requests.get('http://localhost:8000/health')"

# Start application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
```

**docker-compose.yml** (create in project root):

```yaml
version: "3.8"

services:
  backend:
    build: ./Backend
    container_name: langplug-backend
    restart: always
    ports:
      - "8000:8000"
    environment:
      - LANGPLUG_DEBUG=False
      - LANGPLUG_ENVIRONMENT=production
      - DATABASE_URL=postgresql+asyncpg://langplug:${DB_PASSWORD}@db:5432/langplug
      - LANGPLUG_SECRET_KEY=${SECRET_KEY}
    volumes:
      - ./data:/var/lib/langplug/data
      - ./videos:/var/lib/langplug/videos
      - ./logs:/var/log/langplug
    depends_on:
      - db
    networks:
      - langplug

  db:
    image: postgres:14-alpine
    container_name: langplug-db
    restart: always
    environment:
      - POSTGRES_USER=langplug
      - POSTGRES_PASSWORD=${DB_PASSWORD}
      - POSTGRES_DB=langplug
    volumes:
      - postgres_data:/var/lib/postgresql/data
    networks:
      - langplug

  nginx:
    image: nginx:alpine
    container_name: langplug-nginx
    restart: always
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
      - ./ssl:/etc/nginx/ssl:ro
    depends_on:
      - backend
    networks:
      - langplug

volumes:
  postgres_data:

networks:
  langplug:
    driver: bridge
```

**Deploy with Docker**:

```bash
# Build and start
docker-compose up -d

# View logs
docker-compose logs -f backend

# Apply migrations
docker-compose exec backend alembic upgrade head

# Restart services
docker-compose restart

# Stop services
docker-compose down
```

---

## Database Setup

### PostgreSQL Installation

```bash
# Install PostgreSQL
sudo apt install -y postgresql postgresql-contrib

# Start and enable PostgreSQL
sudo systemctl start postgresql
sudo systemctl enable postgresql

# Switch to postgres user
sudo -i -u postgres
```

### Database Creation

```sql
-- Create database and user
CREATE DATABASE langplug;
CREATE USER langplug_user WITH PASSWORD 'your_secure_password';

-- Grant privileges
GRANT ALL PRIVILEGES ON DATABASE langplug TO langplug_user;

-- Connect to database
\c langplug

-- Grant schema privileges
GRANT ALL ON SCHEMA public TO langplug_user;

-- Exit
\q
```

### Apply Migrations

```bash
# Switch to langplug user
sudo su - langplug
cd /home/langplug/app/Backend
source venv/bin/activate

# Run migrations
alembic upgrade head

# Verify
psql -U langplug_user -d langplug -c "\dt"
```

### Database Backup

```bash
# Create backup script: /home/langplug/backup.sh
#!/bin/bash
BACKUP_DIR="/var/backups/langplug"
DATE=$(date +%Y%m%d_%H%M%S)

mkdir -p $BACKUP_DIR

pg_dump -U langplug_user langplug | gzip > \
  $BACKUP_DIR/langplug_$DATE.sql.gz

# Keep only last 7 days
find $BACKUP_DIR -name "*.sql.gz" -mtime +7 -delete

# Make executable
chmod +x /home/langplug/backup.sh

# Add to crontab
crontab -e
# Add: 0 2 * * * /home/langplug/backup.sh
```

---

## Reverse Proxy Configuration

### Nginx Configuration

Create `/etc/nginx/sites-available/langplug`:

```nginx
# Upstream backend servers
upstream langplug_backend {
    server 127.0.0.1:8000;
    # Add more for load balancing:
    # server 127.0.0.1:8001;
    # server 127.0.0.1:8002;
}

# HTTP → HTTPS redirect
server {
    listen 80;
    listen [::]:80;
    server_name app.langplug.com;

    location /.well-known/acme-challenge/ {
        root /var/www/certbot;
    }

    location / {
        return 301 https://$server_name$request_uri;
    }
}

# HTTPS server
server {
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    server_name app.langplug.com;

    # SSL configuration
    ssl_certificate /etc/letsencrypt/live/app.langplug.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/app.langplug.com/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;

    # Security headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;

    # Max upload size (for videos)
    client_max_body_size 500M;

    # Proxy settings
    location / {
        proxy_pass http://langplug_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # Timeouts (for long video processing)
        proxy_connect_timeout 600s;
        proxy_send_timeout 600s;
        proxy_read_timeout 600s;
    }

    # WebSocket support
    location /ws {
        proxy_pass http://langplug_backend;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
    }

    # Static files (if serving directly)
    location /static {
        alias /var/lib/langplug/static;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    # Access and error logs
    access_log /var/log/nginx/langplug_access.log;
    error_log /var/log/nginx/langplug_error.log;
}
```

**Enable site**:

```bash
# Create symlink
sudo ln -s /etc/nginx/sites-available/langplug /etc/nginx/sites-enabled/

# Test configuration
sudo nginx -t

# Reload Nginx
sudo systemctl reload nginx
```

---

## SSL/TLS Setup

### Let's Encrypt (Free SSL)

```bash
# Install Certbot
sudo apt install -y certbot python3-certbot-nginx

# Obtain certificate
sudo certbot --nginx -d app.langplug.com

# Certbot will:
# 1. Validate domain ownership
# 2. Obtain certificate
# 3. Configure Nginx automatically

# Test auto-renewal
sudo certbot renew --dry-run

# Auto-renewal is configured via systemd timer
sudo systemctl status certbot.timer
```

---

## Process Management

### Systemd Service

Create `/etc/systemd/system/langplug.service`:

```ini
[Unit]
Description=LangPlug Backend API
After=network.target postgresql.service

[Service]
Type=notify
User=langplug
Group=langplug
WorkingDirectory=/home/langplug/app/Backend
Environment="PATH=/home/langplug/app/Backend/venv/bin"
EnvironmentFile=/etc/langplug/.env.production

# Multiple workers for production
ExecStart=/home/langplug/app/Backend/venv/bin/uvicorn main:app \
  --host 127.0.0.1 \
  --port 8000 \
  --workers 4 \
  --log-config logging.conf

# Restart on failure
Restart=always
RestartSec=10

# Resource limits
LimitNOFILE=65536
MemoryMax=8G

# Logging
StandardOutput=journal
StandardError=journal
SyslogIdentifier=langplug

[Install]
WantedBy=multi-user.target
```

**Manage service**:

```bash
# Reload systemd
sudo systemctl daemon-reload

# Start service
sudo systemctl start langplug

# Enable on boot
sudo systemctl enable langplug

# Check status
sudo systemctl status langplug

# View logs
sudo journalctl -u langplug -f

# Restart service
sudo systemctl restart langplug
```

---

## Health Checks

### Application Health Endpoint

Add to `main.py`:

```python
@app.get("/health")
async def health_check():
    """Health check endpoint for monitoring"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0"
    }
```

### Monitoring Script

Create `/home/langplug/health_check.sh`:

```bash
#!/bin/bash
HEALTH_URL="http://localhost:8000/health"
RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" $HEALTH_URL)

if [ $RESPONSE -eq 200 ]; then
    echo "Health check passed"
    exit 0
else
    echo "Health check failed: HTTP $RESPONSE"
    # Send alert (email, Slack, etc.)
    exit 1
fi

# Add to crontab
crontab -e
# Add: */5 * * * * /home/langplug/health_check.sh
```

---

## Rollback Procedures

### Quick Rollback Steps

```bash
# 1. Stop current service
sudo systemctl stop langplug

# 2. Switch to previous version
cd /home/langplug/app
git checkout <previous-commit-hash>

# 3. Rollback database (if needed)
cd Backend
source venv/bin/activate
alembic downgrade -1

# 4. Restart service
sudo systemctl start langplug

# 5. Verify
curl http://localhost:8000/health
```

### Zero-Downtime Deployment

**Blue-Green Deployment**:

```bash
# Keep two versions: blue (current) and green (new)

# Deploy to green
sudo systemctl stop langplug-green
cd /home/langplug/app-green
git pull
source venv/bin/activate
pip install -r requirements.txt
alembic upgrade head

# Test green
sudo systemctl start langplug-green
curl http://localhost:8001/health  # Green on port 8001

# If tests pass, switch Nginx upstream
sudo nano /etc/nginx/sites-available/langplug
# Change upstream from :8000 to :8001
sudo nginx -t && sudo systemctl reload nginx

# Stop blue
sudo systemctl stop langplug-blue
```

---

## Deployment Checklist

Before deploying to production:

### Pre-deployment

- [ ] All tests pass in staging
- [ ] Database migrations tested
- [ ] Environment variables configured
- [ ] Secrets stored securely (not in code)
- [ ] SSL certificate obtained
- [ ] Backup created
- [ ] Rollback plan documented

### Deployment

- [ ] Code deployed to server
- [ ] Dependencies installed
- [ ] Database migrations applied
- [ ] Static files collected (if applicable)
- [ ] Service restarted
- [ ] Nginx configuration updated

### Post-deployment

- [ ] Health check passes
- [ ] Application accessible via HTTPS
- [ ] Logs show no errors
- [ ] Monitoring alerts configured
- [ ] Performance acceptable (response times)
- [ ] Database connections stable
- [ ] AI models loading correctly

---

## Related Documentation

- **[CONFIGURATION.md](CONFIGURATION.md)** - Environment variables
- **[MIGRATIONS.md](MIGRATIONS.md)** - Database migrations
- **[MONITORING.md](MONITORING.md)** - Monitoring and logging
- **[DEVELOPER_SETUP.md](DEVELOPER_SETUP.md)** - Local development

---

**Document Version**: 1.0
**Last Updated**: 2025-10-03
**Maintained By**: DevOps Team
