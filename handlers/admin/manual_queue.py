# handlers/admin/manual_queue.py
from typing import List, Optional
from aiogram import Router, F
from aiogram.types import (
    Message,
    CallbackQuery,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)
from aiogram.fsm.context import FSMContext

from app_context import AppContext
from utils.helpers import escape_markdown, get_text
from utils.logger import logger

router = Router()
# Small admin-only FSM state (string constant)
class AdminManualStates:
    waiting_manual_photo = "admin:waiting_manual_photo"
    waiting_cancel_reason = "admin:waiting_cancel_reason"
    waiting_cancel_reason_text = "admin:waiting_cancel_reason_text"


# Helper: render a single task caption (photo will be sent separately)
def render_manual_task_caption(task: dict, index: int, total: int) -> str:
    """
    index: 1-based position of this task in the full queue
    total: total number of tasks in the queue
    """
    user_name = task.get('first_name') or task.get('username') or f"User {task.get('user_id')}"
    style_name = task.get('style_name') or "—"
    status = task.get('status') or "—"
    created_at = task.get('created_at')
    created_str = created_at.strftime("%Y-%m-%d %H:%M") if created_at else "—"
    credits = task.get('credits_spent') or 0
    prompt = task.get('prompt_template') or task.get('prompt') or "—"
    # teaser for quick glance
    teaser = " ".join(prompt.split()[:12]) + (" ..." if len(prompt.split()) > 12 else "")

    caption = (
        f"🔢 <b>Task #{index} / {total}</b>\n\n"
        "🎨 <b>Manual Generation Task</b>\n\n"
        f"👤 <b>User:</b> {user_name} (ID: <code>{task.get('user_id')}</code>)\n"
        f"🖼️ <b>Style:</b> {style_name}\n"
        f"💎 <b>Credits spent:</b> {credits}\n"
        f"📅 <b>Created:</b> {created_str}\n"
        f"⚠️ <b>Status:</b> {status}\n\n"
        f"🧾 <b>Prompt teaser:</b>\n<code>{teaser}</code>\n\n"
        "Use the buttons below to view full prompt, upload result, cancel, or move to next task."
    )
    return caption


# Build inline keyboard for a single task (admin actions)
def build_manual_task_keyboard(task_id: str) -> InlineKeyboardMarkup:
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🧾 View Full Prompt", callback_data=f"manual_view_prompt:{task_id}"),
            InlineKeyboardButton(text="📤 Upload Result", callback_data=f"manual_upload:{task_id}"),
        ],
        [
            InlineKeyboardButton(text="❌ Cancel Task", callback_data=f"manual_cancel:{task_id}"),
            InlineKeyboardButton(text="➡️ Next Task", callback_data="manual_list:next"),
        ],
    ])
    return kb


# Build pagination keyboard for the queue (5 per page)
def build_manual_list_keyboard(page: int, total_pages: int) -> InlineKeyboardMarkup:
    nav = []
    if page > 0:
        nav.append(InlineKeyboardButton(text="⬅️ Prev", callback_data=f"manual_list:page:{page-1}"))
    if page + 1 < total_pages:
        nav.append(InlineKeyboardButton(text="➡️ Next", callback_data=f"manual_list:page:{page+1}"))
    rows = []
    if nav:
        rows.append(nav)
    rows.append([InlineKeyboardButton(text="🔁 Refresh", callback_data=f"manual_list:page:{page}")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


# Entry: show manual queue summary (first page)
@router.message(F.text == "🛠️ Manual Queue")
async def cmd_manual_queue(message: Message, app_context: AppContext, state: FSMContext):
    from config.settings import settings
    if message.from_user.id not in settings.ADMIN_IDS:
        await message.answer("❌ Not authorized")
        return

    page = 0
    page_size = 5
    queue, total = await app_context.db.get_manual_queue_paginated(page=page, page_size=page_size)
    if not queue:
        await message.answer("✅ Manual queue is empty. No tasks to process.")
        return

    total_pages = ((total - 1) // page_size) + 1
    header = f"🛠️ <b>Manual Queue</b>\n\nTotal tasks: <b>{total}</b>\nShowing page {page+1} / {total_pages}"
    await message.answer(header, parse_mode="HTML")

    # Send all tasks on this page with gaps and numbering
    base_index = page * page_size  # zero-based offset
    for idx, task in enumerate(queue):
        overall_index = base_index + idx + 1  # 1-based
        caption = render_manual_task_caption(task, overall_index, total)
        kb = build_manual_task_keyboard(task['id'])
        try:
            if task.get('original_photo_url'):
                await message.answer_photo(task['original_photo_url'], caption=caption, reply_markup=kb, parse_mode="HTML")
            else:
                await message.answer(caption, reply_markup=kb, parse_mode="HTML")
        except Exception:
            # fallback to plain text if sending photo with caption fails
            await message.answer(caption, reply_markup=kb, parse_mode="HTML")

        # gap between tasks for readability (except after last)
        if idx < len(queue) - 1:
            try:
                await message.answer("────────", parse_mode="HTML")
            except Exception:
                pass

    # pagination controls at the end
    try:
        await message.answer("Navigation", reply_markup=build_manual_list_keyboard(page, total_pages))
    except Exception:
        pass


# Callback: paginate / next / prev / refresh
@router.callback_query(F.data.startswith("manual_list:"))
async def manual_list_navigation(callback: CallbackQuery, app_context: AppContext):
    from config.settings import settings
    if callback.from_user.id not in settings.ADMIN_IDS:
        await callback.answer("Not authorized", show_alert=True)
        return

    parts = callback.data.split(":")
    action = parts[1]
    page_size = 5

    # compute page
    if action == "page":
        page = int(parts[2])
    elif action == "next":
        # If message text contains page info, try to parse it; otherwise default to 0
        page = 0
    else:
        page = 0

    queue, total = await app_context.db.get_manual_queue_paginated(page=page, page_size=page_size)
    if not queue:
        await callback.answer("No tasks on this page", show_alert=True)
        return

    total_pages = ((total - 1) // page_size) + 1
    header = f"🛠️ <b>Manual Queue</b>\n\nTotal tasks: <b>{total}</b>\nShowing page {page+1} / {total_pages}"

    # Try to edit the invoking message header; if not possible, send a new header
    try:
        await callback.message.edit_text(header, parse_mode="HTML")
    except Exception:
        try:
            await callback.message.answer(header, parse_mode="HTML")
        except Exception:
            pass

    # Send all tasks on this page with gaps and numbering
    base_index = page * page_size
    for idx, task in enumerate(queue):
        overall_index = base_index + idx + 1
        caption = render_manual_task_caption(task, overall_index, total)
        kb = build_manual_task_keyboard(task['id'])
        try:
            if task.get('original_photo_url'):
                await callback.message.answer_photo(task['original_photo_url'], caption=caption, reply_markup=kb, parse_mode="HTML")
            else:
                await callback.message.answer(caption, reply_markup=kb, parse_mode="HTML")
        except Exception:
            await callback.message.answer(caption, reply_markup=kb, parse_mode="HTML")

        # gap between tasks
        if idx < len(queue) - 1:
            try:
                await callback.message.answer("────────", parse_mode="HTML")
            except Exception:
                pass

    # pagination controls
    try:
        await callback.message.answer("Navigation", reply_markup=build_manual_list_keyboard(page, total_pages))
    except Exception:
        pass

    await callback.answer()

# Callback: view a specific task (by id) — show full card
@router.callback_query(F.data.startswith("manual_view:"))
async def manual_view(callback: CallbackQuery, app_context: AppContext):
    from config.settings import settings
    if callback.from_user.id not in settings.ADMIN_IDS:
        await callback.answer("Not authorized", show_alert=True)
        return

    task_id = callback.data.split(":", 1)[1]
    task = await app_context.db.get_manual_task(task_id)
    if not task:
        await callback.answer("Task not found", show_alert=True)
        return

    caption = render_manual_task_caption(task)
    kb = build_manual_task_keyboard(task['id'])
    if task.get('original_photo_url'):
        try:
            await callback.message.answer_photo(task['original_photo_url'], caption=caption, reply_markup=kb, parse_mode="HTML")
        except Exception:
            await callback.message.answer(caption, reply_markup=kb, parse_mode="HTML")
    else:
        await callback.message.answer(caption, reply_markup=kb, parse_mode="HTML")

    await callback.answer()

# Callback: view full prompt and copy it into a code block (one click)
@router.callback_query(F.data.startswith("manual_view_prompt:"))
async def manual_view_prompt(callback: CallbackQuery, app_context: AppContext):
    from config.settings import settings
    if callback.from_user.id not in settings.ADMIN_IDS:
        await callback.answer("Not authorized", show_alert=True)
        return

    task_id = callback.data.split(":", 1)[1]
    task = await app_context.db.get_manual_task(task_id)
    if not task:
        await callback.answer("Task not found", show_alert=True)
        return

    full_prompt = task.get('prompt_template') or task.get('prompt') or "—"
    # send the full prompt inside a code block so admin can copy easily
    prompt_msg = f"🧾 <b>Full Prompt (copy-ready)</b>\n\n<code>{full_prompt}</code>"
    try:
        await callback.message.answer(prompt_msg, parse_mode="HTML")
    except Exception:
        await callback.message.answer("Failed to show prompt.")
    await callback.answer("Full prompt shown")

# Callback: admin chooses to upload a manual result for a task
@router.callback_query(F.data.startswith("manual_upload:"))
async def manual_upload(callback: CallbackQuery, state: FSMContext, app_context: AppContext):
    from config.settings import settings
    if callback.from_user.id not in settings.ADMIN_IDS:
        await callback.answer("Not authorized", show_alert=True)
        return

    task_id = callback.data.split(":", 1)[1]
    task = await app_context.db.get_manual_task(task_id)
    if not task:
        await callback.answer("Task not found", show_alert=True)
        return

    # store the task id in state and ask admin to send the generated photo
    await state.update_data(manual_task_id=task_id)
    await state.set_state(AdminManualStates.waiting_manual_photo)

    await callback.message.answer(
        "📤 Please upload the manually generated photo for this task. The file you send will be attached to the task and marked as completed.",
    )
    await callback.answer("Waiting for uploaded photo")
from aiogram.filters import StateFilter
# Handler: admin uploads the manual photo while in waiting_manual_photo state

@router.message(StateFilter(AdminManualStates.waiting_manual_photo), F.photo)
async def admin_manual_photo_received(message: Message, state: FSMContext, app_context: AppContext):
    from config.settings import settings
    if message.from_user.id not in settings.ADMIN_IDS:
        await message.answer("Not authorized")
        await state.clear()
        return

    data = await state.get_data()
    task_id = data.get('manual_task_id')
    if not task_id:
        await message.answer("No task in progress. Use the manual queue to pick a task.")
        await state.clear()
        return

    file_id = message.photo[-1].file_id

    try:
        # Mark generation as completed
        await app_context.db.update_generation(
            task_id,
            status='completed',
            generated_photo_url=file_id,
            error_message=None,
            api_provider='manual',
            processing_time_ms=None
        )

        # Fetch generation + user info
        gen = await app_context.db.get_generation(task_id)
        user_id = gen['user_id']
        user = await app_context.db.get_user(user_id)
        lang = user.get('language', 'en')

        # Localized success text
        from utils.helpers import get_text
        success_text = get_text(
            'success',
            lang,
            credits=gen['credits_spent'],
            balance=user['credit_balance']
        )

        # Send result to user
        await message.bot.send_photo(
            chat_id=user_id,
            photo=file_id,
            caption=success_text,
            parse_mode="Markdown"
        )

        await message.answer("✅ Task completed. Result sent to user.")
        logger.info(f"Admin {message.from_user.id} completed manual generation {task_id}")

    except Exception as e:
        logger.exception("Failed to mark manual generation completed")
        await message.answer("❌ Failed to attach result. Check logs.")
    finally:
        await state.clear()


# Step 1: Admin clicks "Cancel Task" — show reason buttons
@router.callback_query(F.data.startswith("manual_cancel:"))
async def manual_cancel(callback: CallbackQuery, state: FSMContext, app_context: AppContext):
    from config.settings import settings
    if callback.from_user.id not in settings.ADMIN_IDS:
        await callback.answer("Not authorized", show_alert=True)
        return

    task_id = callback.data.split(":", 1)[1]
    task = await app_context.db.get_manual_task(task_id)
    if not task:
        await callback.answer("Task not found", show_alert=True)
        return

    # Save task_id in state for follow-up
    await state.update_data(cancel_task_id=task_id)

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📷 Photo too blurry", callback_data="cancel_reason:blurry")],
        [InlineKeyboardButton(text="🎨 Style not supported", callback_data="cancel_reason:unsupported")],
        [InlineKeyboardButton(text="⚡ Quota exceeded", callback_data="cancel_reason:quota")],
        [InlineKeyboardButton(text="✏️ Other (type reason)", callback_data="cancel_reason:other")]
    ])

    await callback.message.answer("❌ Choose a reason for cancelling this task:", reply_markup=kb)
    await state.set_state(AdminManualStates.waiting_cancel_reason)
    await callback.answer()


# Step 2: Admin selects a prefilled reason (or "other")
@router.callback_query(StateFilter(AdminManualStates.waiting_cancel_reason), F.data.startswith("cancel_reason:"))
async def cancel_reason_selected(callback: CallbackQuery, state: FSMContext, app_context: AppContext):
    reason_key = callback.data.split(":", 1)[1]
    data = await state.get_data()
    task_id = data.get("cancel_task_id")

    if reason_key == "other":
        await callback.message.answer("✏️ Please type your custom reason:")
        await state.set_state(AdminManualStates.waiting_cancel_reason_text)
        await callback.answer()
        return

    # Map prefilled reasons to text (admin-facing labels; stored reason_text is plain)
    reasons = {
        "blurry": "Photo too blurry",
        "unsupported": "Style not supported",
        "quota": "Quota exceeded"
    }
    reason_text = reasons.get(reason_key, "Cancelled by admin")

    await finalize_cancellation(callback, app_context, state, task_id, reason_text)


# Step 3: Admin types a custom reason
@router.message(StateFilter(AdminManualStates.waiting_cancel_reason_text))
async def cancel_reason_text(message: Message, state: FSMContext, app_context: AppContext):
    data = await state.get_data()
    task_id = data.get("cancel_task_id")
    reason_text = message.text.strip()
    await finalize_cancellation(message, app_context, state, task_id, reason_text)


# Finalize: update DB, notify admin, notify user (localized)
async def finalize_cancellation(message_or_callback, app_context: AppContext, state: FSMContext, task_id: str, reason_text: str):
    try:
        # Mark as failed in DB
        await app_context.db.update_generation(
            task_id,
            'failed',
            generated_photo_url=None,
            error_message=reason_text,
            api_provider='manual',
            processing_time_ms=None
        )

        # Fetch task + user info
        task = await app_context.db.get_manual_task(task_id)
        user = await app_context.db.get_user(task['user_id'])
        lang = user.get('language', 'en')

        # Refund credits
        refunded_amount = task.get('credits_spent', 0)
        if refunded_amount > 0:
            new_balance = await app_context.db.add_credits(
                user['id'],
                refunded_amount,
                transaction_type='admin_adjustment'
            )
        else:
            new_balance = user['credit_balance']

        # Notify admin
        await message_or_callback.answer(f"❌ Task {task_id} cancelled.\nReason: {reason_text}\n💳 Refunded: {refunded_amount}")

        # Notify user (localized)
        user_msg = get_text(
            'manual_cancelled_user',
            lang,
            reason=escape_markdown(reason_text),
            credits=refunded_amount,
            balance=new_balance
        )

        await message_or_callback.bot.send_message(
            chat_id=user['id'],
            text=user_msg,
            parse_mode="Markdown"
        )

        logger.info(f"Admin cancelled task {task_id}, refunded {refunded_amount} credits, reason: {reason_text}")

    except Exception:
        logger.exception("Failed to cancel manual generation")
        try:
            await message_or_callback.answer("❌ Failed to cancel task. Check logs.")
        except Exception:
            pass
    finally:
        await state.clear()
