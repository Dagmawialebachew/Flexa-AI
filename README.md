# Flexa AI - Premium AI Photo Transformation Bot

Production-ready Telegram bot for Ethiopia's first premium AI photo transformation service.

## Features

- 🎨 AI-powered photo transformation with predefined styles
- 💎 Credit-based system with flexible packages
- 💳 Payment verification with OCR extraction
- 🇪🇹 Full bilingual support (English + Amharic)
- 🧑‍💼 Admin dashboard with full control
- 🚨 Failure-safe manual generation fallback
- ⚡ Lightning-fast async architecture

## Architecture

```
bot.py                          # Main entrypoint
├── config/
│   └── settings.py             # Configuration management
├── database/
│   └── db.py                   # Supabase database service
├── handlers/
│   ├── user/
│   │   ├── onboarding.py       # Language selection, first-time setup
│   │   ├── main_menu.py        # Main menu router
│   │   ├── styles.py           # Style selection flow
│   │   ├── upload.py           # Photo upload & generation
│   │   └── credits.py          # Credit purchase flow
│   └── admin/
│       ├── dashboard.py        # Admin stats & menu
│       ├── payments.py         # Payment approval/rejection
│       ├── manual_generate.py  # Manual generation from queue
│       └── users.py            # User management
├── services/
│   ├── ai_image.py             # Gemini/Banana API abstraction
│   ├── ocr.py                  # Payment screenshot OCR
│   └── payment.py              # Payment utilities
├── states/
│   ├── user_states.py          # User FSM states
│   └── admin_states.py         # Admin FSM states
├── keyboards/
│   ├── reply.py                # Reply keyboard layouts
│   └── inline.py               # Inline keyboard layouts
├── app_context/
│   └── context.py              # Application context
└── utils/
    ├── logger.py               # Logging setup
    ├── helpers.py              # Bilingual text & formatting
    └── validators.py           # Input validation
```

## Setup

### 1. Environment Variables

Create `.env` file:

```bash
# Telegram Bot
BOT_TOKEN=your_telegram_bot_token
ADMIN_IDS=123456789,987654321

# Supabase Database
DATABASE_URL=postgresql://user:password@db.supabase.co:5432/postgres
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your_anon_key

# AI APIs
GEMINI_API_KEY=your_gemini_api_key
BANANA_API_KEY=your_banana_api_key

# Configuration
BONUS_CREDITS=3
DEFAULT_LANGUAGE=en
LOG_LEVEL=INFO
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Database Setup

Schema is automatically created in Supabase. Default styles are pre-inserted.

### 4. Run Bot

```bash
python bot.py
```

## Credit System

### Packages
- 5 images: 100 Birr
- 10 images: 150 Birr
- 25 images: 300 Birr

### Bonus
- 3 free credits on registration

### Usage
- 1 credit per standard transformation
- 2 credits for restoration/enhancement

## Admin Commands

```bash
/admin                          # Show dashboard
/user <user_id>                 # View user details
/add_credits <user_id> <amount> # Add credits
/deduct_credits <user_id> <amount>  # Remove credits
/manual_generate <gen_id>       # Complete manual task
```

## Payment Flow

1. User selects package
2. Receives payment instructions (bank details)
3. Uploads payment screenshot
4. OCR extracts: amount, transaction ID, sender (assistive only)
5. Admin reviews and approves/rejects
6. Credits automatically added on approval

## Failure Handling

If AI API fails:
1. User is notified politely
2. Generation marked as "manual_queue"
3. Admin sees in dashboard
4. Admin generates manually when ready
5. Photo delivered to user

## Styles (Database)

Pre-configured styles:
- Professional Portrait (1 credit)
- Artistic Oil Painting (1 credit)
- Cinematic Movie Poster (2 credits)
- Vintage 1950s Photo (1 credit)
- Restore Old Photo (2 credits)

Add custom styles via database insert:
```sql
INSERT INTO styles (name_en, name_am, description_en, description_am, prompt_template, credit_cost, display_order)
VALUES (...)
```

## Database Schema

### users
- Telegram user ID, profile info, language, credit balance, generation count

### styles
- Style definitions with bilingual names, prompts, costs

### generations
- Generation history with status tracking, API provider, processing time

### payments
- Payment submissions with OCR data, approval workflow

### credit_transactions
- Full credit transaction log for auditing

### admin_logs
- Admin action audit trail

## Performance Notes

- Async-first with asyncpg connection pooling
- Memory-based FSM (can switch to Redis for scaling)
- Middleware-based context injection
- Direct Supabase queries (no ORM overhead)

## Scaling (Future)

1. Replace MemoryStorage with Redis for multi-instance
2. Add message queue (Celery) for async generation
3. Implement webhook for async Telegram updates
4. Add caching layer (Redis) for styles and user data
5. Switch to production Gunicorn deployment

## Testing

```bash
# Test database connection
python -c "from database import Database; import asyncio; from config import settings; asyncio.run(Database(settings.DATABASE_URL).connect())"

# Test bot connection
python -c "from aiogram import Bot; from config import settings; import asyncio; asyncio.run(Bot(settings.BOT_TOKEN).get_me())"
```

## Support

Contact: @FlexaAISupport

---

**Status**: Production-ready, 48-hour development cycle complete
**Version**: 1.0.0
**Built**: 2025-01-31
