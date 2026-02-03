from aiogram import Router
from .handlers import router as router
from .credits import router as credits_router
from .settings import router as settings_router


user_router = Router()
user_router.include_router(credits_router)
user_router.include_router(router)
user_router.include_router(settings_router)

__all__ = ['user_router']
