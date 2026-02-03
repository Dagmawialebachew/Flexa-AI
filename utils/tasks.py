import os
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import app_context
from app_context.context import AppContext
from utils.logger import logger

ADMIN_MANUAL_GROUP_ID = int(os.getenv("ADMIN_MANUAL_GROUP_ID", "-5084517269"))

def build_manual_task_keyboard(task_id: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🧾 View Full Prompt", callback_data=f"manual_view_prompt:{task_id}"),
            InlineKeyboardButton(text="📤 Upload Result", callback_data=f"manual_upload:{task_id}"),
        ],
        [
            InlineKeyboardButton(text="❌ Cancel Task", callback_data=f"manual_cancel:{task_id}"),
            InlineKeyboardButton(text="➡️ Next Task", callback_data="manual_list:next"),
        ],
    ])

async def notify_admin_manual_queue(bot, gen, user, style, app_context: AppContext):
    queue_count = await app_context.db.get_stats() 
    manual_queue_total = queue_count['manual_queue']
    caption = (
        f"🛠️ <b>Manual Queue Alert #{manual_queue_total}</b>\n\n"
        f"👤 User: <b>{user['first_name']}</b> (@{user.get('username','—')})\n"
        f"🆔 ID: <code>{user['id']}</code>\n"
        f"🎨 Style: <b>{style['name_en']}</b>\n"
        f"💎 Credits spent: {gen['credits_spent']}\n"
        f"🧾 Prompt:\n<code>{style.get('prompt_template','—')}...</code>\n\n"
        "⚡ This task has been added to the manual queue. Admins can process it below."
    )

    kb = build_manual_task_keyboard(gen['id'])

    try:
        if gen.get('original_photo_url'):
            await bot.send_photo(
                chat_id=ADMIN_MANUAL_GROUP_ID,
                photo=gen['original_photo_url'],
                caption=caption,
                reply_markup=kb,
                parse_mode="HTML"
            )
        else:
            await bot.send_message(
                chat_id=ADMIN_MANUAL_GROUP_ID,
                text=caption,
                reply_markup=kb,
                parse_mode="HTML"
            )
    except Exception:
        logger.exception("Failed to notify admin group about manual queue")



ADMIN_DAILY_GROUP_ID = int(os.getenv("ADMIN_DAILY_GROUP_ID", "-5084517269"))

def build_payment_keyboard(payment_id: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Approve", callback_data=f"payment_approve:{payment_id}"),
            InlineKeyboardButton(text="❌ Reject", callback_data=f"payment_reject:{payment_id}"),
        ],
        [
            InlineKeyboardButton(text="🔎 View Details", callback_data=f"payment_view:{payment_id}")
        ]
    ])
    
    
async def notify_admins_new_payment(bot, payment_id: str, payment: dict, user: dict, ocr_data: dict):
    caption = (
        f"💳 <b>New Payment #{payment_id[:8]}</b>\n\n"
        f"👤 User: <b>{user['first_name']}</b> (@{user.get('username','—')})\n"
        f"🆔 ID: <code>{user['id']}</code>\n\n"
        f"📦 Package: <b>{payment['package_type']}</b>\n"
        f"💰 Amount: <b>{payment['amount_birr']} Birr</b>\n"
        f"💎 Credits: <b>{payment['credits_amount']}</b>\n\n\n"
        f"🧾 OCR Extracted:\n"
        f"• Amount: {ocr_data.get('amount') or '—'}\n"
        f"• Transaction ID: {ocr_data.get('transaction_id') or '—'}\n"
        f"• Sender: {ocr_data.get('sender') or '—'}\n"
        f"• Raw: <code>{ocr_data.get('raw_text') or '—'}</code>\n\n"
        "⚡ Admins can approve or reject below."
    )

    kb = build_payment_keyboard(payment_id)

    try:
        if payment.get('screenshot_url'):
            await bot.send_photo(
                chat_id=ADMIN_DAILY_GROUP_ID,
                photo=payment['screenshot_url'],
                caption=caption,
                parse_mode="HTML"
            )
        else:
            await bot.send_message(
                chat_id=ADMIN_DAILY_GROUP_ID,
                text=caption,
                reply_markup=kb,
                parse_mode="HTML"
            )
    except Exception:
        logger.exception("Failed to notify admin group about new payment")



ADMIN_NEWUSER_GROUP_ID = int(os.getenv("ADMIN_NEWUSER_GROUP_ID", "-5164704172"))

async def notify_admins_new_user(bot, user: dict):
    username = user.get('username', 'N/A')
    caption = (
        f"👋 <b>New User Joined</b>\n\n"
        f"👤 Name: <b>{user.get('first_name','—')} @{username}</b>\n"
        f"🆔 ID: <code>{user['id']}</code>\n"
        f"🌐 Language: {user.get('language','en')}\n"
        f"💎 Starting Credits: {user.get('credit_balance',0)}\n\n"
        "⚡ This user has completed onboarding and is now active."
    )

    try:
        await bot.send_message(
            chat_id=ADMIN_NEWUSER_GROUP_ID,
            text=caption,
            parse_mode="HTML"
        )
    except Exception:
        logger.exception("Failed to notify admin group about new user")
