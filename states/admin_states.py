# states/admin_states.py
from aiogram.fsm.state import StatesGroup, State

class AdminStyleStates(StatesGroup):
    waiting_name_en = State()
    waiting_name_am = State()
    waiting_description_en = State()
    waiting_description_am = State()
    waiting_prompt_template = State()
    waiting_credit_cost = State()
    waiting_is_active = State()
    waiting_preview_image = State()
    waiting_cancel_reason = "admin:waiting_cancel_reason"
    confirming = State()
