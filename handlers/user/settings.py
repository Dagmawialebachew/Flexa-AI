from aiogram import Router, F
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from app_context.context import AppContext
from keyboards.reply import get_main_menu_keyboard
from utils.helpers import get_text, get_button

router = Router()

# -------------------------
# Settings Menu
# -------------------------
@router.message(F.text.in_(['⚙️ Settings', '⚙️ ሴቲንግ']))
async def show_settings(message: Message, app_context: AppContext):
    user = await app_context.db.get_user(message.from_user.id)
    lang = user["language"] if user else "en"

    settings_kb = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text=get_button("change_language", lang), callback_data="settings_change_language")
    ]])

    await message.answer(get_text("settings_menu", lang), reply_markup=settings_kb, parse_mode="Markdown")


# -------------------------
# Change Language Flow
# -------------------------
@router.callback_query(F.data == "settings_change_language")
async def settings_change_language(callback: CallbackQuery, state: FSMContext, app_context: AppContext):
    user = await app_context.db.get_user(callback.from_user.id)
    lang = user["language"] if user else "en"

    lang_kb = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="🇬🇧 English", callback_data="ch_lang_en"),
        InlineKeyboardButton(text="🇪🇹 አማርኛ", callback_data="ch_lang_am")
    ]])

    await callback.message.edit_text(
        get_text("onboarding_choose_language", lang),
        reply_markup=lang_kb
    )


@router.callback_query(F.data.startswith("ch_lang"))
async def language_selected(callback: CallbackQuery, state: FSMContext, app_context: AppContext):
    lang = "en" if callback.data == "ch_lang_en" else "am"

    # Update user language in DB
    print('here is the lang to be updated', lang)
    await app_context.db.update_user_language(callback.from_user.id, lang)

    # Confirm change
    await callback.message.edit_text(
        get_text("language_changed", lang),
        parse_mode="Markdown",
    )
    await callback.message.answer(
        get_text('main_menu', lang, balance=(await app_context.db.get_user(callback.from_user.id))["credit_balance"]),
        reply_markup=get_main_menu_keyboard(lang),
        parse_mode="HTML"
        
    )
