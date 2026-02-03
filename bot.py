import asyncio
import logging
import os
import sys
from aiohttp import web
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import BotCommand, BotCommandScopeDefault, BotCommandScopeChat
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application

from config.settings import settings
from database import Database
from services import AIImageService, OCRService, PaymentService
from app_context import AppContext
from handlers import user_router, admin_router
from middlewares.error_handling_middleware import ErrorHandlingMiddleware
from middlewares.throttling_middleware import ThrottlingMiddleware
from utils.logger import logger

logging.basicConfig(level=logging.INFO)

# --- Global objects ---
bot = Bot(token=settings.BOT_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)
db = Database(settings.DATABASE_URL)

# --- Middleware setup ---
def setup_middlewares(app_context: AppContext):
    from aiogram import BaseMiddleware
    class AppContextMiddleware(BaseMiddleware):
        def __init__(self, app_context: AppContext):
            self.app_context = app_context
        async def __call__(self, handler, event, data):
            data['app_context'] = self.app_context
            return await handler(event, data)

    dp.message.middleware(AppContextMiddleware(app_context))
    dp.callback_query.middleware(AppContextMiddleware(app_context))
    dp.message.middleware(ThrottlingMiddleware(message_interval=1.5, callback_interval=0.5))
    dp.callback_query.middleware(ThrottlingMiddleware(message_interval=1.5, callback_interval=0.5))
    dp.message.middleware(ErrorHandlingMiddleware())
    dp.callback_query.middleware(ErrorHandlingMiddleware())

# --- Routers ---
dp.include_router(user_router)
dp.include_router(admin_router)

# --- Bot commands ---
async def set_commands(bot, admin_ids: list[int]):
    user_commands = [
        BotCommand(command="start", description="🚀 Start Flexa AI"),
        BotCommand(command="help", description="❓ Help & Contact"),
    ]
    await bot.set_my_commands(user_commands, scope=BotCommandScopeDefault(), request_timeout=30)

    admin_commands = user_commands + [
        BotCommand(command="admin", description="🔐 Admin Command Center"),
    ]
    for admin_id in admin_ids:
        await bot.set_my_commands(admin_commands, scope=BotCommandScopeChat(chat_id=admin_id), request_timeout=30)

# --- Startup / Shutdown ---
async def on_startup(bot: Bot):
    logger.info("🚀 Starting Flexa AI bot...")
    await db.connect()
    ai_service = AIImageService()
    ocr_service = OCRService()
    payment_service = PaymentService()
    app_context = AppContext(db=db, ai_service=ai_service, ocr_service=ocr_service, payment_service=payment_service)
    setup_middlewares(app_context)
    await set_commands(bot, settings.ADMIN_IDS)
    webhook_url = f"{os.getenv('WEBHOOK_BASE_URL')}/webhook"
    await bot.set_webhook(webhook_url, drop_pending_updates=True)
    logger.info(f"Webhook set to: {webhook_url}")

async def on_shutdown(bot: Bot):
    logger.info("🛑 Shutting down Flexa AI bot...")
    await db.close()
    await bot.session.close()

# --- Health check ---
async def health_check(request):
    return web.Response(text="OK")

# --- Webhook app factory ---
async def create_app() -> web.Application:
    app = web.Application()
    app.router.add_get("/health", health_check)
    webhook_handler = SimpleRequestHandler(dispatcher=dp, bot=bot)
    webhook_handler.register(app, path="/webhook")
    setup_application(app, dp, bot=bot)
    app.on_startup.append(lambda app: asyncio.create_task(on_startup(bot)))
    app.on_cleanup.append(lambda app: asyncio.create_task(on_shutdown(bot)))
    return app

# --- Polling mode ---
async def start_polling():
    await db.connect()
    ai_service = AIImageService()
    ocr_service = OCRService()
    payment_service = PaymentService()
    app_context = AppContext(db=db, ai_service=ai_service, ocr_service=ocr_service, payment_service=payment_service)
    setup_middlewares(app_context)
    await set_commands(bot, settings.ADMIN_IDS)
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

# --- Entrypoint ---
if __name__ == "__main__":
    if "--polling" in sys.argv:
        asyncio.run(start_polling())
    else:
        port = int(os.getenv("PORT", "8080"))
        logger.info(f"Starting webhook server on http://0.0.0.0:{port}")
        web.run_app(create_app(), host="0.0.0.0", port=port)
