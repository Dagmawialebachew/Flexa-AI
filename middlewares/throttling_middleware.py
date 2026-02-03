# middlewares/throttling_middleware.py
import asyncio
import time
from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery
from typing import Callable, Dict, Any, Awaitable

from utils.helpers import get_text

class ThrottlingMiddleware(BaseMiddleware):
    def __init__(self, message_interval: float = 1.5, callback_interval: float = 0.5) -> None:
        super().__init__()
        self.message_interval = message_interval
        self.callback_interval = callback_interval
        self._last_seen_msg: dict[int, float] = {}
        self._last_seen_cb: dict[int, float] = {}

    async def __call__(self, handler, event, data):
        user_id = getattr(getattr(event, "from_user", None), "id", None)
        now = time.time()

        # Try to fetch user language from DB via app_context
        lang = "en"
        app_context = data.get("app_context")
        if user_id and app_context:
            try:
                db_user = await app_context.db.get_user(user_id)
                if db_user and db_user.get("language"):
                    lang = db_user["language"]
            except Exception:
                pass

        if isinstance(event, Message):
            last = self._last_seen_msg.get(user_id, 0.0)
            if (now - last) < self.message_interval:
                try:
                    msg = await event.answer(get_text("error_throttle_message", lang))
                    await asyncio.sleep(1)
                    await msg.delete()
                except Exception:
                    pass
                return None
            self._last_seen_msg[user_id] = now

        elif isinstance(event, CallbackQuery):
            last = self._last_seen_cb.get(user_id, 0.0)
            if (now - last) < self.callback_interval:
                try:
                    await event.answer(get_text("error_throttle_callback", lang), show_alert=False)
                except Exception:
                    pass
                return None
            self._last_seen_cb[user_id] = now

        return await handler(event, data)
