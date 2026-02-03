from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from states import UserStates
from keyboards.reply import get_cancel_keyboard
from utils.helpers import get_text
from app_context import AppContext
import asyncio

router = Router()


@router.callback_query(F.data.startswith('style:'))
async def style_selected(callback: CallbackQuery, state: FSMContext, app_context: AppContext):
    style_id = callback.data.split(':')[1]

    user = await app_context.db.get_user(callback.from_user.id)
    lang = user['language']

    style = await app_context.db.get_style(style_id)
    if not style:
        await callback.answer(get_text('error_general', lang), show_alert=True)
        return

    await state.update_data(selected_style=style)

    style_name = style['name_am'] if lang == 'am' else style['name_en']
    desc = style['description_am'] if lang == 'am' else style['description_en']
    cost = style['credit_cost']

    message_text = f"✅ *{style_name}*\n\n{desc}\n\n💎 Cost: {cost} credit{'s' if cost != 1 else ''}"

    await callback.message.edit_text(message_text, parse_mode='Markdown')

    upload_text = get_text('upload_photo', lang)
    await callback.message.answer(upload_text, reply_markup=get_cancel_keyboard(lang), parse_mode='Markdown')

    await state.set_state(UserStates.uploading_photo)
    await callback.answer()
