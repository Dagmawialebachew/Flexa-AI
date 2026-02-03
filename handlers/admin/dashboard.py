from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import Command
from telegram import CallbackQuery
from config.settings import settings
from handlers.admin.users import render_users
from keyboards.inline import get_admin_reply_keyboard, get_payment_review_keyboard
from app_context import AppContext
from utils.helpers import get_text
from .manual_queue import build_manual_task_keyboard, render_manual_task_caption
from aiogram.fsm.context import FSMContext
from .payments import cmd_payments
router = Router()

def is_admin(user_id: int) -> bool:
    return user_id in settings.ADMIN_IDS


# ---------- LOGIC FUNCTIONS ----------

async def render_stats(message: Message, app_context: AppContext):
    stats = await app_context.db.get_stats()
    stats_text = (
        "📊 *Current Stats*\n\n"
        f"👥 Total Users: {stats['total_users']}\n"
        f"📸 Total Generations: {stats['total_generations']}\n"
        f"💳 Pending Payments: {stats['pending_payments']}\n"
        f"🎨 Manual Queue: {stats['manual_queue']}\n"
    )
    await message.answer(stats_text, parse_mode="Markdown")



def format_ocr_data(ocr_data) -> str:
    if not ocr_data:
        return "No OCR data extracted"
    import json
    if isinstance(ocr_data, str):
        ocr_data = json.loads(ocr_data)
    lines = []
    if ocr_data.get('amount'):
        lines.append(f"Amount: {ocr_data['amount']} Birr")
    if ocr_data.get('transaction_id'):
        lines.append(f"TXN ID: {ocr_data['transaction_id']}")
    if ocr_data.get('sender'):
        lines.append(f"Sender: {ocr_data['sender']}")
    return "\n".join(lines) if lines else "Could not extract payment details"


# ---------- HANDLERS ----------

@router.message(Command("admin"))
async def admin_command(message: Message, app_context: AppContext):
    if not is_admin(message.from_user.id):
        await message.answer("❌ You are not authorized to use this command.")
        return

    stats = await app_context.db.get_stats()
    stats_text = (
        "📊 *Flexa AI Admin Dashboard*\n\n"
        f"👥 Total Users: {stats['total_users']}\n"
        f"📸 Total Generations: {stats['total_generations']}\n"
        f"💳 Pending Payments: {stats['pending_payments']}\n"
        f"🎨 Manual Queue: {stats['manual_queue']}\n\n"
        "What would you like to do?"
    )
    await message.answer(stats_text, reply_markup=get_admin_reply_keyboard(), parse_mode="HTML")


@router.message(F.text.in_(["📊 Stats", "💳 Payments", "🎨 Manual Queue", "👥 Users"]))
async def admin_menu_handler(message: Message, app_context: AppContext, state: FSMContext):
    if not is_admin(message.from_user.id):
        await message.answer(get_text("not_authorized", "en"))
        return

    if message.text == "📊 Stats":
        await render_stats(message, app_context)

    elif message.text == "💳 Payments":
        # Call your updated playful payments flow
        await cmd_payments(message, app_context, state)

    elif message.text == "🎨 Manual Queue":
        page = 0
        page_size = 5
        queue, total = await app_context.db.get_manual_queue_paginated(page=page, page_size=page_size)
        if not queue:
            await message.answer(get_text("manual_queue_empty", "en"), parse_mode="HTML")
            return

        total_pages = ((total - 1) // page_size) + 1
        header = (
            f"🛠️ <b>{get_text('manual_queue_header', 'en')}</b>\n\n"
            f"Total tasks: <b>{total}</b>\nShowing page {page+1} / {total_pages}"
        )
        await message.answer(header, parse_mode="HTML")

        base_index = page * page_size
        for idx, task in enumerate(queue):
            overall_index = base_index + idx + 1
            caption = render_manual_task_caption(task, overall_index, total)
            kb = build_manual_task_keyboard(task['id'])

            try:
                if task.get('original_photo_url'):
                    await message.answer_photo(
                        task['original_photo_url'],
                        caption=caption,
                        reply_markup=kb,
                        parse_mode="HTML"
                    )
                else:
                    await message.answer(caption, reply_markup=kb, parse_mode="HTML")
            except Exception:
                await message.answer(caption, reply_markup=kb, parse_mode="HTML")

            if idx < len(queue) - 1:
                await message.answer("────────", parse_mode="HTML")
    elif message.text == "👥 Users":
        # Start at page 0 with default page_size
        await render_users(message, app_context, page=0, page_size=5)

@router.callback_query(F.data.startswith("payment:approve:"))
async def approve_payment_callback(callback: CallbackQuery, app_context: AppContext):
    payment_id = callback.data.split(":")[2]
    success = await app_context.db.approve_payment(payment_id, callback.from_user.id)
    if success:
        await callback.answer("Payment approved!", show_alert=True)
    else:
        await callback.answer("Failed to approve payment", show_alert=True)

@router.callback_query(F.data.startswith("payment:reject:"))
async def reject_payment_callback(callback: CallbackQuery, app_context: AppContext):
    payment_id = callback.data.split(":")[2]
    await app_context.db.reject_payment(payment_id, callback.from_user.id, "Rejected by admin")
    await callback.answer("Payment rejected", show_alert=True)


@router.callback_query(F.data == "admin:payments")
async def back_to_payments(callback: CallbackQuery, app_context: AppContext):
    if not is_admin(callback.from_user.id):
        await callback.answer("Not authorized", show_alert=True)
        return

    payments = await app_context.db.get_pending_payments(limit=5)
    if not payments:
        await callback.message.edit_text("No pending payments", parse_mode="Markdown")
        await callback.answer()
        return

    payments_text = "*Pending Payments*\n\n"
    for p in payments:
        user_name = p['first_name'] or p['username'] or f"User {p['user_id']}"
        payments_text += f"ID: `{str(p['id'])[:8]}`\n👤 {user_name}\n💰 {p['amount_birr']} Birr\n\n"

    # Replace the current message with the list again
    await callback.message.edit_text(payments_text, parse_mode="Markdown")
    await callback.answer()
