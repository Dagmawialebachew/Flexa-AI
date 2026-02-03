# Flexa AI - Quick Start Guide

Get the bot running in 5 minutes.

## Prerequisites

- Python 3.10+
- Telegram Bot Token (from @BotFather)
- Supabase PostgreSQL database (https://supabase.com)

## 1. Clone & Setup (2 min)

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

## 2. Configure Environment (2 min)

Create `.env` file:

```bash
cp .env.example .env
```

Edit `.env` with your values:
```
BOT_TOKEN=your_bot_token_here
ADMIN_IDS=your_telegram_user_id
DATABASE_URL=postgresql://user:pass@db.supabase.co:5432/postgres
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your_anon_key
```

**Where to find:**
- BOT_TOKEN: Message @BotFather on Telegram
- Your ID: Message @userinfobot on Telegram
- Supabase: https://supabase.com → New project → Settings → Database

## 3. Test Database Connection (1 min)

```bash
python3 << 'EOF'
import asyncio
from database import Database
from config import settings

async def test():
    db = Database(settings.DATABASE_URL)
    await db.connect()
    stats = await db.get_stats()
    print(f'✅ Connected! Users: {stats["total_users"]}')
    await db.close()

asyncio.run(test())
EOF
```

If you see `✅ Connected!`, you're good to go.

## 4. Run Bot (1 min)

```bash
python3 bot.py
```

You should see:
```
2025-01-31 10:00:00 - flexa_ai - INFO - Starting Flexa AI bot...
2025-01-31 10:00:01 - flexa_ai - INFO - Database connection pool established
2025-01-31 10:00:02 - flexa_ai - INFO - Bot handlers registered
2025-01-31 10:00:02 - flexa_ai - INFO - Bot started and listening for updates...
```

## 5. Test the Bot

1. Open Telegram
2. Search for your bot (username set in @BotFather)
3. Send `/start`
4. You should see language selection

**Test User Flow:**
- Select language
- Click "🎨 Generate Photo"
- Select a style
- Send any image
- Bot will generate (placeholder for now)

**Test Admin Commands:**
```
/admin - Show stats
/user 123456789 - View user details
/add_credits 123456789 50 - Give 50 credits to user
```

## Environment Variables Explained

| Variable | Purpose | Example |
|----------|---------|---------|
| `BOT_TOKEN` | Telegram bot authentication | `5123456:ABCDEFGHIJKLMNOPqrstuvwxyz` |
| `ADMIN_IDS` | Who can run admin commands | `123456789,987654321` |
| `DATABASE_URL` | PostgreSQL connection | `postgresql://user:pass@host:5432/db` |
| `SUPABASE_URL` | API endpoint | `https://abc.supabase.co` |
| `SUPABASE_KEY` | API key | `eyJhbGc...` |
| `BONUS_CREDITS` | Free credits on signup | `3` |

## Common Issues & Solutions

### Bot doesn't respond to `/start`

```bash
# Check token is correct
curl https://api.telegram.org/bot$BOT_TOKEN/getMe

# Check bot is running
ps aux | grep bot.py

# Check logs
tail -50 logs.txt
```

### Database connection failed

```bash
# Verify connection string
psql $DATABASE_URL -c "SELECT 1;"

# Check .env file is loaded
python3 -c "from config import settings; print(settings.DATABASE_URL)"
```

### Module not found errors

```bash
# Reinstall dependencies
pip install --force-reinstall -r requirements.txt

# Verify virtual environment is activated
which python3  # Should show venv/bin/python3
```

## Next Steps

1. **Integrate AI API**: See `services/ai_image.py` for Gemini integration
2. **Deploy**: Follow `DEPLOYMENT.md`
3. **Understand architecture**: Read `ARCHITECTURE.md`
4. **Add features**: See `DEVELOPMENT.md` (patterns for new handlers)

## Project Structure

```
flexa-ai-bot/
├── bot.py                 # Main entry point
├── config/                # Settings management
├── database/              # Database service
├── handlers/
│   ├── user/             # User flows
│   └── admin/            # Admin commands
├── services/             # AI, OCR, Payments
├── keyboards/            # Telegram keyboards
├── states/               # FSM states
└── utils/                # Helpers, logger, validators
```

## Useful Commands

```bash
# Run bot with debug output
LOG_LEVEL=DEBUG python3 bot.py

# Connect to database directly
psql $DATABASE_URL

# View recent users
psql $DATABASE_URL -c "SELECT first_name, language, joined_at FROM users ORDER BY joined_at DESC LIMIT 5;"

# View pending payments
psql $DATABASE_URL -c "SELECT * FROM payments WHERE status = 'pending';"

# Deactivate virtual environment
deactivate
```

## Support

- **Issues**: Check error logs
- **Questions**: See README.md, ARCHITECTURE.md
- **Telegram**: @FlexaAISupport

---

**Time to first message**: ~5 minutes ⚡
**Status**: Ready for production 🚀
