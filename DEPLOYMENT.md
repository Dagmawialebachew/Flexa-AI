# Flexa AI - Deployment Guide

Production-ready deployment instructions for Flexa AI Telegram bot.

## Prerequisites

- Python 3.10+
- PostgreSQL database (Supabase recommended)
- Telegram Bot Token (from @BotFather)
- (Optional) Gemini API key, Banana API key

## Quick Start (Local Development)

### 1. Clone & Setup

```bash
git clone <repo>
cd flexa-ai-bot
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
cp .env.example .env
```

Edit `.env`:
```
BOT_TOKEN=your_token_from_botfather
ADMIN_IDS=your_telegram_user_id
DATABASE_URL=postgresql://user:pass@db.supabase.co:5432/postgres
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your_anon_key
BONUS_CREDITS=3
```

### 3. Verify Database Connection

```bash
python3 -c "
import asyncio
from database import Database
from config import settings

async def test():
    db = Database(settings.DATABASE_URL)
    await db.connect()
    stats = await db.get_stats()
    print(f'✅ Connected! Stats: {stats}')
    await db.close()

asyncio.run(test())
"
```

### 4. Run Bot Locally

```bash
python3 bot.py
```

Bot will start polling for updates. Send `/start` to your bot to test.

## Production Deployment

### Option A: Ubuntu Server with Systemd

#### 1. Server Setup

```bash
sudo apt update && sudo apt upgrade
sudo apt install python3.10 python3.10-venv git postgresql-client-14
```

#### 2. Application Setup

```bash
cd /opt/flexa-ai-bot
git clone <repo> .
python3.10 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

#### 3. Create Systemd Service

```bash
sudo tee /etc/systemd/system/flexa-ai-bot.service > /dev/null << EOF
[Unit]
Description=Flexa AI Telegram Bot
After=network.target

[Service]
Type=simple
User=appuser
WorkingDirectory=/opt/flexa-ai-bot
Environment="PATH=/opt/flexa-ai-bot/venv/bin"
ExecStart=/opt/flexa-ai-bot/venv/bin/python3 /opt/flexa-ai-bot/bot.py
Restart=always
RestartSec=10
StandardOutput=append:/var/log/flexa-ai-bot/bot.log
StandardError=append:/var/log/flexa-ai-bot/bot.error.log

[Install]
WantedBy=multi-user.target
EOF
```

#### 4. Start Service

```bash
sudo mkdir -p /var/log/flexa-ai-bot
sudo chown appuser:appuser /var/log/flexa-ai-bot
sudo systemctl daemon-reload
sudo systemctl enable flexa-ai-bot
sudo systemctl start flexa-ai-bot
```

#### 5. Monitor

```bash
sudo systemctl status flexa-ai-bot
sudo tail -f /var/log/flexa-ai-bot/bot.log
```

### Option B: Docker

Create `Dockerfile`:

```dockerfile
FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

CMD ["python3", "bot.py"]
```

Build & Run:

```bash
docker build -t flexa-ai-bot .
docker run -d --name flexa-ai-bot --restart always -e BOT_TOKEN=$BOT_TOKEN -e DATABASE_URL=$DATABASE_URL flexa-ai-bot
```

### Option C: Cloud Platforms

#### Render.com
1. Connect GitHub repo
2. Create new Web Service
3. Set environment variables
4. Deploy

#### Railway.app
1. New project → GitHub repo
2. Add PostgreSQL plugin
3. Set environment variables
4. Deploy

#### Heroku (Legacy)
```bash
heroku login
heroku create flexa-ai-bot
git push heroku main
```

## Scaling Considerations

### Single Instance (Current)
- Works for ~1000 concurrent users
- Memory-based FSM (sufficient for this scale)
- Direct database connections

### Multi-Instance Setup

#### 1. Replace MemoryStorage with Redis

In `bot.py`:
```python
from aiogram.fsm.storage.redis import RedisStorage

redis_storage = RedisStorage.from_url('redis://localhost:6379')
dp = Dispatcher(storage=redis_storage)
```

#### 2. Use Message Queue (Optional)

Add to `requirements.txt`:
```
celery==5.3.0
redis==5.0.0
```

For long-running tasks:
```python
from celery import Celery

celery_app = Celery('flexa_ai')

@celery_app.task
async def generate_image_async(user_id, style_id, photo_url):
    # Long-running AI generation
    pass
```

#### 3. Load Balancing

Use Nginx as reverse proxy (for webhook mode):
```nginx
upstream flexa_bot {
    server bot1:8080;
    server bot2:8080;
    server bot3:8080;
}

server {
    listen 80;
    location /webhook {
        proxy_pass http://flexa_bot;
    }
}
```

## Database Maintenance

### Backup

```bash
pg_dump $DATABASE_URL > backup.sql
```

### Monitor

```sql
-- View user growth
SELECT DATE_TRUNC('day', joined_at) as day, COUNT(*) as users
FROM users
GROUP BY day
ORDER BY day DESC;

-- View generation stats
SELECT status, COUNT(*) FROM generations GROUP BY status;

-- Check pending payments
SELECT COUNT(*) FROM payments WHERE status = 'pending';
```

## Monitoring & Logging

### Real-time Logs

```bash
tail -f /var/log/flexa-ai-bot/bot.log
```

### Log Levels

Set in `.env`:
```
LOG_LEVEL=INFO  # INFO, DEBUG, WARNING, ERROR
```

### Error Alerts

Forward logs to monitoring service:
```bash
# With Sentry
pip install sentry-sdk
```

In logger.py:
```python
import sentry_sdk
sentry_sdk.init("your_sentry_dsn")
```

## Security Checklist

- [ ] Bot token stored in environment variables (not in code)
- [ ] Database password in environment (not in code)
- [ ] Admin IDs configured correctly
- [ ] RLS policies enabled on all tables
- [ ] HTTPS enabled for webhooks (if using)
- [ ] Regular database backups
- [ ] Dependency updates (`pip check` for vulnerabilities)
- [ ] Rate limiting enabled
- [ ] Sensitive data not logged

## Admin Commands Reference

```
/admin - Show dashboard
/user <id> - View user details
/add_credits <id> <amount> - Add credits
/deduct_credits <id> <amount> - Remove credits
/approve_payment <id> - Approve payment
/reject_payment <id> - Reject payment
/payments - View pending payments
```

## Troubleshooting

### Bot Not Responding

```bash
# Check if running
systemctl status flexa-ai-bot

# Verify token
curl https://api.telegram.org/bot$BOT_TOKEN/getMe

# Check logs
tail -50 /var/log/flexa-ai-bot/bot.log
```

### Database Connection Error

```bash
# Test connection
psql $DATABASE_URL -c "SELECT 1;"

# Check pool
python3 -c "from database import Database; import asyncio; asyncio.run(Database('$DATABASE_URL').connect())"
```

### High Memory Usage

Restart bot service:
```bash
systemctl restart flexa-ai-bot
```

Monitor with:
```bash
watch -n 1 'ps aux | grep bot.py'
```

## Updates & Maintenance

### Code Updates

```bash
cd /opt/flexa-ai-bot
git pull origin main
source venv/bin/activate
pip install -r requirements.txt
systemctl restart flexa-ai-bot
```

### Dependency Updates

```bash
pip list --outdated
pip install -U aiogram aiohttp asyncpg
```

## Support & Contacts

- Issues: GitHub Issues
- Email: support@flexaai.com
- Telegram: @FlexaAISupport

---

**Last Updated**: 2025-01-31
**Status**: Production Ready
**Version**: 1.0.0
