from aiogram import Router
from .handlers import router as handlers_router
from .dashboard import router as dashboard_router
from .prompts import router as prompts_router
from .manual_queue import router as manual_queue_router
from .payments import router as payments_router
from .users import router as users_router

admin_router = Router()
admin_router.include_router(handlers_router)
admin_router.include_router(dashboard_router)
admin_router.include_router(prompts_router)
admin_router.include_router(manual_queue_router)
admin_router.include_router(payments_router)
admin_router.include_router(users_router)

__all__ = ["admin_router"]
