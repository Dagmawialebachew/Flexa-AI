# handlers/admin/users.py
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.filters import StateFilter

from config.settings import settings
from app_context import AppContext
from utils.helpers import get_text, escape_markdown
from utils.logger import logger

router = Router()

class AdminUserStates:
    waiting_add_credits_amount = "admin:user:waiting_add_credits_amount"

def is_admin(user_id: int) -> bool:
    return user_id in settings.ADMIN_IDS

# Helper: user caption
def render_user_caption(user: dict, index: int, total: int) -> str:
    name = user.get("first_name") or user.get("username") or f"User {user.get('id')}"
    username = f"@{user['username']}" if user.get("username") else "—"
    balance = user.get("credit_balance", 0)
    generations = user.get("total_generations", 0)
    created_at = user.get("created_at")
    created_str = created_at.strftime("%Y-%m-%d %H:%M") if created_at else "—"
    banned = "🚫 BANNED" if user.get("is_banned") else "✅ Active"

    caption = (
        f"👤 <b>User #{index}/{total}</b>\n\n"
        f"🪪 <b>Name:</b> {name}\n"
        f"🔗 <b>Username:</b> {username}\n"
        f"💎 <b>Credits:</b> {balance}\n"
        f"📸 <b>Generations:</b> {generations}\n"
        f"📅 <b>Joined:</b> {created_str}\n"
        f"⚠️ <b>Status:</b> {banned}\n"
    )
    return caption

# Helper: user action keyboard
def build_user_keyboard(user_id: int) -> InlineKeyboardMarkup:
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="👀 View Details", callback_data=f"user_view:{user_id}"),
            InlineKeyboardButton(text="➕ Add Credits", callback_data=f"user_add_credits:{user_id}"),
        ],
        [
            InlineKeyboardButton(text="🚫 Ban", callback_data=f"user_ban:{user_id}"),
            InlineKeyboardButton(text="✅ Unban", callback_data=f"user_unban:{user_id}"),
        ],
    ])
    return kb

# Entry: show users page (called from admin menu)
async def render_users(message: Message, app_context: AppContext, page: int = 0, page_size: int = 5):
    if message.from_user.id not in settings.ADMIN_IDS:
        await message.answer("❌ Not authorized")
        return

    users, total = await app_context.db.get_users_paginated(page=page, page_size=page_size)
    if not users:
        await message.answer("❌ No users found")
        return

    total_pages = ((total - 1) // page_size) + 1
    header = f"👥 <b>Users</b>\n\nTotal: <b>{total}</b>\nShowing page {page+1}/{total_pages}"
    await message.answer(header, parse_mode="HTML")

    base_index = page * page_size
    for idx, user in enumerate(users):
        overall_index = base_index + idx + 1
        caption = render_user_caption(user, overall_index, total)
        kb = build_user_keyboard(user["id"])
        await message.answer(caption, reply_markup=kb, parse_mode="HTML")
        if idx < len(users) - 1:
            await message.answer("────────", parse_mode="HTML")

    # Pagination controls
    nav = []
    if page > 0:
        nav.append(InlineKeyboardButton(text="⬅️ Prev", callback_data=f"users_page:{page-1}"))
    if page + 1 < total_pages:
        nav.append(InlineKeyboardButton(text="➡️ Next", callback_data=f"users_page:{page+1}"))
    nav.append(InlineKeyboardButton(text="🔁 Refresh", callback_data=f"users_page:{page}"))

    await message.answer("Navigation", reply_markup=InlineKeyboardMarkup(inline_keyboard=[nav]))

# Callback: pagination / refresh
@router.callback_query(F.data.startswith("users_page:"))
async def users_page_navigation(callback: CallbackQuery, app_context: AppContext):
    if not is_admin(callback.from_user.id):
        await callback.answer("Not authorized", show_alert=True)
        return

    parts = callback.data.split(":")
    page = int(parts[1])
    page_size = 5
    users, total = await app_context.db.get_users_paginated(page=page, page_size=page_size)
    if not users:
        await callback.answer("No users on this page", show_alert=True)
        return

    total_pages = ((total - 1) // page_size) + 1
    header = f"👥 <b>Users</b>\n\nTotal: <b>{total}</b>\nShowing page {page+1}/{total_pages}"

    # Send a fresh header and page content (avoid edit_text on photo messages)
    await callback.message.answer(header, parse_mode="HTML")

    base_index = page * page_size
    for idx, user in enumerate(users):
        overall_index = base_index + idx + 1
        caption = render_user_caption(user, overall_index, total)
        kb = build_user_keyboard(user["id"])
        await callback.message.answer(caption, reply_markup=kb, parse_mode="HTML")
        if idx < len(users) - 1:
            await callback.message.answer("────────", parse_mode="HTML")

    await callback.answer("Refreshed")

# Callback: view user details (admin only)
@router.callback_query(F.data.startswith("user_view:"))
async def user_view(callback: CallbackQuery, app_context: AppContext):
    if not is_admin(callback.from_user.id):
        await callback.answer("Not authorized", show_alert=True)
        return

    user_id = int(callback.data.split(":", 1)[1])
    user = await app_context.db.get_user(user_id)
    if not user:
        await callback.answer("User not found", show_alert=True)
        return

    # Render a more detailed admin-only card
    details = (
        f"👤 <b>User Details</b>\n\n"
        f"🪪 Name: {user.get('first_name') or '—'}\n"
        f"🔗 Username: @{user.get('username') or '—'}\n"
        f"💎 Credits: {user.get('credit_balance', 0)}\n"
        f"📸 Generations: {user.get('total_generations', 0)}\n"
        f"📅 Joined: {user.get('created_at').strftime('%Y-%m-%d %H:%M') if user.get('created_at') else '—'}\n"
        f"⚠️ Banned: {'Yes' if user.get('is_banned') else 'No'}\n"
        f"🆔 ID: <code>{user.get('id')}</code>\n"
    )
    await callback.message.answer(details, parse_mode="HTML")
    await callback.answer()

# Callback: start add credits flow (ask admin for amount)
@router.callback_query(F.data.startswith("user_add_credits:"))
async def user_add_credits(callback: CallbackQuery, state: FSMContext, app_context: AppContext):
    if not is_admin(callback.from_user.id):
        await callback.answer("Not authorized", show_alert=True)
        return

    user_id = int(callback.data.split(":", 1)[1])
    await state.update_data(target_user_id=user_id)
    await state.set_state(AdminUserStates.waiting_add_credits_amount)
    # Ask admin to type amount
    try:
        await callback.message.answer("➕ Type the number of credits to add (e.g. 10):", parse_mode="Markdown")
    except Exception:
        await callback.message.answer("➕ Type the number of credits to add (e.g. 10):")
    await callback.answer()

# Handler: admin types credits amount
@router.message(StateFilter(AdminUserStates.waiting_add_credits_amount))
async def handle_add_credits(message: Message, state: FSMContext, app_context: AppContext):
    if not is_admin(message.from_user.id):
        await message.answer("Not authorized")
        await state.clear()
        return

    data = await state.get_data()
    target_user_id = data.get("target_user_id")
    if not target_user_id:
        await message.answer("No user selected.")
        await state.clear()
        return

    try:
        amount = int(message.text.strip())
        if amount <= 0:
            raise ValueError()
    except Exception:
        await message.answer("Please enter a valid positive integer amount.")
        return

    try:
        new_balance = await app_context.db.add_credits(target_user_id, amount, transaction_type='admin_adjustment')
    except Exception:
        logger.exception("Failed to add credits in DB")
        await message.answer("❌ Failed to add credits. Check logs.")
        await state.clear()
        return

    # Notify admin
    await message.answer(f"✅ Added {amount} credits to user {target_user_id}. New balance: {new_balance}")

    # Notify user (localized)
    try:
        user = await app_context.db.get_user(target_user_id)
        user_msg = get_text('user_credits_added', user.get('language', 'en'), credits=amount, balance=new_balance)
        await message.bot.send_message(target_user_id, user_msg, parse_mode='Markdown')
    except Exception as e:
        logger.error(f"Failed to notify user {target_user_id}: {e}")

    logger.info(f"Admin {message.from_user.id} added {amount} credits to user {target_user_id}")
    await state.clear()

# Callback: ban user
@router.callback_query(F.data.startswith("user_ban:"))
async def user_ban(callback: CallbackQuery, app_context: AppContext):
    if not is_admin(callback.from_user.id):
        await callback.answer("Not authorized", show_alert=True)
        return

    user_id = int(callback.data.split(":", 1)[1])
    try:
        await app_context.db.set_user_banned(user_id, True)
    except Exception:
        logger.exception("Failed to ban user in DB")
        await callback.answer("Failed to ban user", show_alert=True)
        return

    await callback.message.answer(f"🚫 User {user_id} banned.")
    # Notify user (localized)
    try:
        user = await app_context.db.get_user(user_id)
        user_msg = get_text('user_banned', user.get('language', 'en'))
        await callback.bot.send_message(user_id, user_msg, parse_mode='Markdown')
    except Exception as e:
        logger.error(f"Failed to notify user {user_id}: {e}")

    logger.info(f"Admin {callback.from_user.id} banned user {user_id}")
    await callback.answer()

# Callback: unban user
@router.callback_query(F.data.startswith("user_unban:"))
async def user_unban(callback: CallbackQuery, app_context: AppContext):
    if not is_admin(callback.from_user.id):
        await callback.answer("Not authorized", show_alert=True)
        return

    user_id = int(callback.data.split(":", 1)[1])
    try:
        await app_context.db.set_user_banned(user_id, False)
    except Exception:
        logger.exception("Failed to unban user in DB")
        await callback.answer("Failed to unban user", show_alert=True)
        return

    await callback.message.answer(f"✅ User {user_id} unbanned.")
    # Notify user (localized)
    try:
        user = await app_context.db.get_user(user_id)
        user_msg = get_text('user_unbanned', user.get('language', 'en'))
        await callback.bot.send_message(user_id, user_msg, parse_mode='Markdown')
    except Exception as e:
        logger.error(f"Failed to notify user {user_id}: {e}")

    logger.info(f"Admin {callback.from_user.id} unbanned user {user_id}")
    await callback.answer()
