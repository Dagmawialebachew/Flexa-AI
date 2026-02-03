import asyncio
import logging
from typing import Any, Callable, Dict, Awaitable
from aiogram import BaseMiddleware, Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import TelegramObject, BotCommand, BotCommandScopeDefault, BotCommandScopeChat
from config.settings import settings
from database import Database
from middlewares.error_handling_middleware import ErrorHandlingMiddleware
from services import AIImageService, OCRService, PaymentService
from app_context import AppContext
from handlers import user_router, admin_router
from utils.logger import logger
from middlewares.throttling_middleware import ThrottlingMiddleware
logging.basicConfig(level=logging.INFO)


class AppContextMiddleware(BaseMiddleware):
    def __init__(self, app_context: AppContext):
        self.app_context = app_context

    async def __call__(self, handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]], event: TelegramObject, data: Dict[str, Any]) -> Any:
        data['app_context'] = self.app_context
        return await handler(event, data)


async def setup_database() -> Database:
    db = Database(settings.DATABASE_URL)
    await db.connect()
    return db


async def set_commands(bot, admin_ids: list[int]):
    # convert BotCommand objects to dicts
    user_commands = [
        BotCommand(command="start", description="🚀 Start Flexa AI").model_dump(),
        BotCommand(command="help", description="❓ Help & Contact").model_dump(),
    ]
    # scope also needs to be a dict
    await bot.set_my_commands(
        user_commands,
        scope=BotCommandScopeDefault().model_dump(),
        request_timeout=30
    )

    admin_commands = user_commands + [
        BotCommand(command="admin", description="🔐 Admin Command Center").model_dump(),
    ]
    for admin_id in admin_ids:
        await bot.set_my_commands(
            admin_commands,
            scope=BotCommandScopeChat(chat_id=admin_id).model_dump(),
            request_timeout=30
        )


async def main():
    logger.info("Starting Flexa AI bot...")

    db = await setup_database()

    bot = Bot(token=settings.BOT_TOKEN)
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)

    ai_service = AIImageService()
    ocr_service = OCRService()
    payment_service = PaymentService()
    await set_commands(bot, settings.ADMIN_IDS)


    app_context = AppContext(
        db=db,
        ai_service=ai_service,
        ocr_service=ocr_service,
        payment_service=payment_service
    )

    dp.message.middleware(AppContextMiddleware(app_context))
    dp.callback_query.middleware(AppContextMiddleware(app_context))
    
    # ✅ Add throttling middleware
    dp.message.middleware(ThrottlingMiddleware(message_interval=1.5, callback_interval=0.5)) 
    dp.callback_query.middleware(ThrottlingMiddleware(message_interval=1.5, callback_interval=0.5))
    
    # Erro handling
    dp.message.middleware(ErrorHandlingMiddleware())
    dp.callback_query.middleware(ErrorHandlingMiddleware())

    dp.include_router(user_router)
    dp.include_router(admin_router)

    logger.info("Bot handlers registered")
    logger.info("Bot started and listening for updates...")
   
    try:
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    finally:
        await bot.session.close()
        await db.close()


if __name__ == '__main__':
    asyncio.run(main())
