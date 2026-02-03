from email import message
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
import app_context
from config.settings import settings
from app_context import AppContext
from keyboards.inline import get_admin_reply_keyboard
from utils.logger import logger

router = Router()


def is_admin(user_id: int) -> bool:
    return user_id in settings.ADMIN_IDS




@router.message(Command('admin'))
async def admin_command(message: Message, app_context: AppContext):
    if not is_admin(message.from_user.id):
        await message.answer("❌ You are not authorized to use this command.")
        return
    stats = await app_context.db.get_stats()
    stats_text = f"""
    📊 <b>Flexa AI Admin Dashboard</b>

    👥 Total Users: {stats['total_users']}
    📸 Total Generations: {stats['total_generations']}
    💳 Pending Payments: {stats['pending_payments']}
    🎨 Manual Queue: {stats['manual_queue']}

    <b>Commands:</b>
    /user &lt;user_id&gt; - View user details
    /add_credits &lt;user_id&gt; &lt;amount&gt; - Add credits
    /deduct_credits &lt;user_id&gt; &lt;amount&gt; - Remove credits
    /approve_payment &lt;payment_id&gt; - Approve payment
    /reject_payment &lt;payment_id&gt; - Reject payment
    """

    await message.answer( stats_text, reply_markup=await get_admin_reply_keyboard(app_context.db), parse_mode="HTML" )

@router.message(Command('user'))
async def user_command(message: Message, app_context: AppContext):
    if not is_admin(message.from_user.id):
        await message.answer("Not authorized")
        return
    args = message.text.split()
    if len(args) < 2:
        await message.answer("Usage: /user <user_id>")
        return
    try:
        user_id = int(args[1])
    except ValueError:
        await message.answer("Invalid user ID")
        return
    user = await app_context.db.get_user(user_id)
    if not user:
        await message.answer("User not found")
        return
    user_info = f"""
👤 *User Details*

ID: {user['id']}
Name: {user['first_name']}
Username: {user['username'] or 'N/A'}
Language: {user['language']}
Credits: {user['credit_balance']}
Generations: {user['total_generations']}
Status: {'Active' if user['is_active'] else 'Inactive'}
Joined: {user['joined_at'][:10]}
"""
    await message.answer(user_info, parse_mode='Markdown')


@router.message(Command('add_credits'))
async def add_credits_command(message: Message, app_context: AppContext):
    if not is_admin(message.from_user.id):
        await message.answer("Not authorized")
        return
    args = message.text.split()
    if len(args) < 3:
        await message.answer("Usage: /add_credits <user_id> <amount>")
        return
    try:
        user_id = int(args[1])
        amount = int(args[2])
    except ValueError:
        await message.answer("Invalid user ID or amount")
        return
    user = await app_context.db.get_user(user_id)
    if not user:
        await message.answer("User not found")
        return
    new_balance = await app_context.db.add_credits(user_id, amount, 'admin_adjustment')
    await message.answer(f"✅ Added {amount} credits to {user['first_name']}\nNew balance: {new_balance}", parse_mode='Markdown')
    try:
        await message.bot.send_message(user_id, f"💎 Admin added {amount} credits to your account!\nNew balance: {new_balance}", parse_mode='Markdown')
    except:
        pass


@router.message(Command('deduct_credits'))
async def deduct_credits_command(message: Message, app_context: AppContext):
    if not is_admin(message.from_user.id):
        await message.answer("Not authorized")
        return
    args = message.text.split()
    if len(args) < 3:
        await message.answer("Usage: /deduct_credits <user_id> <amount>")
        return
    try:
        user_id = int(args[1])
        amount = int(args[2])
    except ValueError:
        await message.answer("Invalid user ID or amount")
        return
    user = await app_context.db.get_user(user_id)
    if not user:
        await message.answer("User not found")
        return
    new_balance = await app_context.db.add_credits(user_id, -amount, 'admin_adjustment')
    await message.answer(f"✅ Deducted {amount} credits from {user['first_name']}\nNew balance: {new_balance}", parse_mode='Markdown')


@router.message(Command('approve_payment'))
async def approve_payment_command(message: Message, app_context: AppContext):
    if not is_admin(message.from_user.id):
        await message.answer("Not authorized")
        return
    args = message.text.split()
    if len(args) < 2:
        await message.answer("Usage: /approve_payment <payment_id>")
        return
    payment_id = args[1]
    payment = await app_context.db.get_payment(payment_id)
    if not payment:
        await message.answer("Payment not found")
        return
    success = await app_context.db.approve_payment(payment_id, message.from_user.id)
    if success:
        user = await app_context.db.get_user(payment['user_id'])
        await message.answer(f"✅ Payment {payment_id} approved!\n💎 {payment['credits_amount']} credits added.", parse_mode='Markdown')
        try:
            await message.bot.send_message(payment['user_id'], f"🎉 *Your payment has been approved!*\n\n💎 {payment['credits_amount']} credits have been added to your account.\n\nNew balance: {user['credit_balance']} credits", parse_mode='Markdown')
        except:
            pass
    else:
        await message.answer("Failed to approve payment")


@router.message(Command('reject_payment'))
async def reject_payment_command(message: Message, app_context: AppContext):
    if not is_admin(message.from_user.id):
        await message.answer("Not authorized")
        return
    args = message.text.split()
    if len(args) < 2:
        await message.answer("Usage: /reject_payment <payment_id>")
        return
    payment_id = args[1]
    payment = await app_context.db.get_payment(payment_id)
    if not payment:
        await message.answer("Payment not found")
        return
    await app_context.db.reject_payment(payment_id, message.from_user.id, "Rejected by admin")
    await message.answer(f"❌ Payment {payment_id} rejected.")
    try:
        await message.bot.send_message(payment['user_id'], f"❌ *Your payment was rejected*\n\nPlease contact support for more information.", parse_mode='Markdown')
    except:
        pass


@router.message(Command('payments'))
async def view_payments_command(message: Message, app_context: AppContext):
    if not is_admin(message.from_user.id):
        await message.answer("Not authorized")
        return
    payments = await app_context.db.get_pending_payments(limit=5)
    if not payments:
        await message.answer("No pending payments")
        return
    payments_text = "*Pending Payments*\n\n"
    for p in payments:
        user_name = p['first_name'] or p['username'] or f"User {p['user_id']}"
        payments_text += f"ID: `{str(p['id'])[:8]}`\n👤 {user_name}\n💰 {p['amount_birr']} Birr\n\n"
    await message.answer(payments_text, parse_mode='Markdown')
