from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from config.settings import settings
from app_context import AppContext
from utils.logger import logger

router = Router()


def is_admin(user_id: int) -> bool:
    return user_id in settings.ADMIN_IDS


@router.message(Command('manual_generate'))
async def manual_generate_command(message: Message, app_context: AppContext):
    if not is_admin(message.from_user.id):
        await message.answer("Not authorized")
        return

    args = message.text.split()
    if len(args) < 2:
        await message.answer("Usage: /manual_generate <generation_id>")
        return

    generation_id = args[1]

    generation = await app_context.db.get_generation(generation_id)
    if not generation:
        await message.answer("Generation not found")
        return

    await message.answer(f"Please upload the completed image for generation {generation_id}")


@router.message(F.photo, F.caption.contains('manual_complete'))
async def manual_image_upload(message: Message, app_context: AppContext):
    if not is_admin(message.from_user.id):
        return

    caption = message.caption or ""
    parts = caption.split()

    generation_id = None
    for i, part in enumerate(parts):
        if part == 'manual_complete' and i + 1 < len(parts):
            generation_id = parts[i + 1]
            break

    if not generation_id:
        await message.answer("Could not extract generation ID from caption. Use: 'manual_complete <id>'")
        return

    generation = await app_context.db.get_generation(generation_id)
    if not generation:
        await message.answer("Generation not found")
        return

    photo = message.photo[-1]

    await app_context.db.update_generation(
        generation_id,
        'completed',
        generated_photo_url=photo.file_id,
        api_provider='manual',
        admin_id=message.from_user.id
    )

    await message.answer(f"✅ Generation {generation_id} completed and sent to user")

    try:
        success_msg = f"""
✨ *Your Photo is Ready!*

Our team manually completed your request.

Thank you for your patience!
"""
        await message.bot.send_photo(
            generation['user_id'],
            photo.file_id,
            caption=success_msg,
            parse_mode='Markdown'
        )
    except Exception as e:
        logger.error(f"Failed to send completed photo to user {generation['user_id']}: {e}")

    logger.info(f"Manual generation {generation_id} completed by admin {message.from_user.id}")


@router.callback_query(F.data.startswith('complete_manual:'))
async def complete_manual_prompt(callback: CallbackQuery, app_context: AppContext):
    if not is_admin(callback.from_user.id):
        await callback.answer("Not authorized", show_alert=True)
        return

    generation_id = callback.data.split(':')[1]

    generation = await app_context.db.get_generation(generation_id)
    if not generation:
        await callback.answer("Generation not found", show_alert=True)
        return

    await callback.message.answer(
        f"📸 Upload the completed image for generation {generation_id}\n\nCaption format: manual_complete {generation_id}"
    )
    await callback.answer()


@router.callback_query(F.data.startswith('skip_manual:'))
async def skip_manual(callback: CallbackQuery, app_context: AppContext):
    if not is_admin(callback.from_user.id):
        await callback.answer("Not authorized", show_alert=True)
        return

    generation_id = callback.data.split(':')[1]

    generation = await app_context.db.get_generation(generation_id)
    if not generation:
        await callback.answer("Generation not found", show_alert=True)
        return

    await app_context.db.update_generation(
        generation_id,
        'failed',
        error_message='Skipped by admin'
    )

    await callback.message.edit_text(f"⏭️ Skipped generation {generation_id}")
    await callback.answer()



