# handlers/admin/payments.py
from typing import Optional
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.filters import StateFilter

from config.settings import settings
from app_context import AppContext
from utils.helpers import escape_markdown, get_text
from utils.logger import logger

router = Router()

# Admin FSM states for payment rejection flow
class AdminPaymentStates:
    waiting_reject_reason = "admin:waiting_reject_reason"

# Helper: render a single payment caption (photo sent separately)
def render_payment_caption(payment: dict, index: int, total: int) -> str:
    user_name = payment.get('first_name') or payment.get('username') or f"User {payment.get('user_id')}"
    created_at = payment.get('created_at')
    created_str = created_at.strftime("%Y-%m-%d %H:%M") if created_at else "—"
    status = payment.get('status', '—').capitalize()
    amount_expected = payment.get('package_price') or payment.get('amount_birr') or "—"
    ocr = payment.get('ocr_data') or {}
    ocr_amount = ocr.get('amount') or "—"
    ocr_txn = ocr.get('transaction_id') or "—"
    ocr_sender = ocr.get('sender') or "—"
    ocr_raw = escape_markdown((ocr.get('raw_text') or "—")[:400])  # teaser
    confidence = ocr.get('confidence')
    conf_str = f"{confidence:.0%}" if isinstance(confidence, float) else (str(confidence) if confidence else "—")

    caption = (
        f"🔢 <b>Payment #{index} / {total}</b>\n\n"
        f"👤 <b>User:</b> {user_name} (ID: <code>{payment.get('user_id')}</code>)\n"
        f"📦 <b>Package:</b> {payment.get('package_type') or '—'}\n"
        f"💰 <b>Expected:</b> {amount_expected} Birr\n"
        f"🕒 <b>Submitted:</b> {created_str}\n"
        f"⚠️ <b>Status:</b> {status}\n\n"
        f"🧾 <b>OCR Summary</b>\n"
        f"• Amount: {ocr_amount}  • Confidence: {conf_str}\n"
        f"• Transaction ID: {ocr_txn}\n"
        f"• Sender: {ocr_sender}\n\n"
        f"🔎 <b>OCR Raw (teaser)</b>\n<code>{ocr_raw}</code>\n\n"
        "Use the buttons below to approve, reject (with reason), or skip to the next payment."
    )
    return caption

# Build inline keyboard for a single payment (admin actions)
def build_payment_keyboard(payment_id: str) -> InlineKeyboardMarkup:
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Approve", callback_data=f"approve_payment:{payment_id}"),
            InlineKeyboardButton(text="❌ Reject", callback_data=f"reject_payment:{payment_id}"),
        ],
        [
            InlineKeyboardButton(text="🔁 Refresh", callback_data=f"payments_list:refresh"),
        ],
    ])
    return kb

# Entry: show pending payments (first page)
@router.message(F.text == "💳 Payments")
async def cmd_payments(message: Message, app_context: AppContext, state: FSMContext):
    if message.from_user.id not in settings.ADMIN_IDS:
        await message.answer("❌ Not authorized")
        return

    page = 0
    page_size = 5
    queue, total = await app_context.db.get_pending_payments_paginated(page=page, page_size=page_size)
    if not queue:
        await message.answer("✅ No pending payments right now. Enjoy the calm.")
        return

    total_pages = ((total - 1) // page_size) + 1
    header = f"💳 <b>Pending Payments</b>\n\nTotal: <b>{total}</b>\nShowing page {page+1} / {total_pages}"
    await message.answer(header, parse_mode="HTML")

    base_index = page * page_size
    for idx, payment in enumerate(queue):
        overall_index = base_index + idx + 1
        caption = render_payment_caption(payment, overall_index, total)
        kb = build_payment_keyboard(payment['id'])
        try:
            if payment.get('screenshot_url'):
                await message.answer_photo(payment['screenshot_url'], caption=caption, reply_markup=kb, parse_mode="HTML")
            else:
                await message.answer(caption, reply_markup=kb, parse_mode="HTML")
        except Exception:
            await message.answer(caption, reply_markup=kb, parse_mode="HTML")

        if idx < len(queue) - 1:
            await message.answer("────────")

    # navigation
    nav_kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔁 Refresh", callback_data=f"payments_list:page:{page}")],
    ])
    await message.answer("Navigation", reply_markup=nav_kb)

# Callback: approve payment
@router.callback_query(F.data.startswith('approve_payment:'))
async def approve_payment(callback: CallbackQuery, app_context: AppContext):
    if callback.from_user.id not in settings.ADMIN_IDS:
        await callback.answer("Not authorized", show_alert=True)
        return

    payment_id = callback.data.split(':', 1)[1]
    payment = await app_context.db.get_payment(payment_id)
    if not payment:
        await callback.answer("Payment not found", show_alert=True)
        return

    success = await app_context.db.approve_payment(payment_id, callback.from_user.id)
    if not success:
        await callback.answer("Failed to approve payment", show_alert=True)
        return

    # Fetch updated user info after approval
    user = await app_context.db.get_user(payment['user_id'])
    approval_text = get_text(
        'admin_payment_approved',
        'en',  # admin UI language; you can detect admin language if needed
        user_name=user.get('first_name'),
        credits=payment.get('credits_amount'),
        balance=user.get('credit_balance')
    )

    try:
        await callback.message.edit_text(approval_text, parse_mode='Markdown')
    except Exception:
        await callback.answer("Approved", show_alert=False)

    # Notify user
    try:
        user_msg = get_text(
            'user_payment_approved',
            user.get('language', 'en'),
            credits=payment.get('credits_amount'),
            balance=user.get('credit_balance')
        )
        await callback.bot.send_message(payment['user_id'], user_msg, parse_mode='Markdown')
    except Exception as e:
        logger.error(f"Failed to notify user {payment['user_id']}: {e}")

    logger.info(f"Payment {payment_id} approved by admin {callback.from_user.id}")
    await callback.answer("Payment approved")

# Callback: start rejection flow (ask for reason)
@router.callback_query(F.data.startswith('reject_payment:'))
async def reject_payment(callback: CallbackQuery, state: FSMContext, app_context: AppContext):
    if callback.from_user.id not in settings.ADMIN_IDS:
        await callback.answer("Not authorized", show_alert=True)
        return

    payment_id = callback.data.split(':', 1)[1]
    payment = await app_context.db.get_payment(payment_id)
    if not payment:
        await callback.answer("Payment not found", show_alert=True)
        return

    # Ask admin for rejection reason
    await state.update_data(rejecting_payment_id=payment_id)
    await state.set_state(AdminPaymentStates.waiting_reject_reason)
    try:
        await callback.message.edit_text(
            "❌ Please type the reason for rejection (this will be sent to the user):",
            parse_mode="Markdown"
        )
    except Exception:
        # Fallback: send a new message if editing fails
        await callback.message.answer(
            "❌ Please type the reason for rejection (this will be sent to the user):",
            parse_mode="Markdown"
        )
        await callback.answer()

# Handler: admin provides rejection reason
@router.message(StateFilter(AdminPaymentStates.waiting_reject_reason))
async def handle_rejection_reason(message: Message, state: FSMContext, app_context: AppContext):
    if message.from_user.id not in settings.ADMIN_IDS:
        await message.answer("Not authorized")
        await state.clear()
        return

    data = await state.get_data()
    payment_id = data.get('rejecting_payment_id')
    if not payment_id:
        await message.answer("No payment selected for rejection.")
        await state.clear()
        return

    reason = message.text.strip()
    try:
        await app_context.db.reject_payment(payment_id, message.from_user.id, reason)
    except Exception:
        logger.exception("Failed to reject payment in DB")
        await message.answer("❌ Failed to reject payment. Check logs.")
        await state.clear()
        return

    payment = await app_context.db.get_payment(payment_id)
    user = await app_context.db.get_user(payment['user_id'])

    # Admin confirmation (playful)
    admin_confirm = get_text('admin_payment_rejected_confirm', 'en', payment_id=payment_id, reason=reason)
    await message.answer(admin_confirm, parse_mode='Markdown')

    # Notify user (localized)
    try:
        user_msg = get_text('user_payment_rejected', user.get('language', 'en'), reason=reason)
        await message.bot.send_message(payment['user_id'], user_msg, parse_mode='Markdown')
    except Exception as e:
        logger.error(f"Failed to notify user {payment['user_id']}: {e}")

    logger.info(f"Payment {payment_id} rejected by admin {message.from_user.id}: {reason}")
    await state.clear()

@router.callback_query(F.data.startswith("payments_list:"))
async def payments_list_navigation(callback: CallbackQuery, app_context: AppContext):
    if callback.from_user.id not in settings.ADMIN_IDS:
        await callback.answer("Not authorized", show_alert=True)
        return

    page = 0
    page_size = 5
    queue, total = await app_context.db.get_pending_payments_paginated(page=page, page_size=page_size)
    if not queue:
        await callback.answer("No pending payments", show_alert=True)
        return

    total_pages = ((total - 1) // page_size) + 1
    header = f"💳 <b>Pending Payments</b>\n\nTotal: <b>{total}</b>\nShowing page {page+1} / {total_pages}"

    # Instead of edit_text (which fails if the message is a photo), send a fresh header
    await callback.message.answer(header, parse_mode="HTML")

    # Re‑send the list of payments with keyboards
    base_index = page * page_size
    for idx, payment in enumerate(queue):
        overall_index = base_index + idx + 1
        caption = render_payment_caption(payment, overall_index, total)
        kb = build_payment_keyboard(payment['id'])
        if payment.get('screenshot_url'):
            await callback.message.answer_photo(payment['screenshot_url'], caption=caption, reply_markup=kb, parse_mode="HTML")
        else:
            await callback.message.answer(caption, reply_markup=kb, parse_mode="HTML")

    await callback.answer("Refreshed")
