from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from states import UserStates
from keyboards.reply import get_main_menu_keyboard
from utils.helpers import get_text
from app_context import AppContext
from utils.logger import logger
import asyncio

router = Router()


@router.message(UserStates.uploading_photo, F.photo)
async def photo_received(message: Message, state: FSMContext, app_context: AppContext):
    user = await app_context.db.get_user(message.from_user.id)
    lang = user['language']

    state_data = await state.get_data()
    style = state_data.get('selected_style')

    if not style:
        await message.answer(get_text('error_general', lang), parse_mode='Markdown')
        await state.set_state(UserStates.main_menu)
        return

    credit_cost = style['credit_cost']

    if user['credit_balance'] < credit_cost:
        required = credit_cost
        balance = user['credit_balance']
        await message.answer(
            get_text('insufficient_credits', lang, required=required, balance=balance),
            parse_mode='Markdown'
        )
        await state.set_state(UserStates.main_menu)
        return

    processing_msg = await message.answer(get_text('processing', lang), parse_mode='Markdown')

    try:
        photo = message.photo[-1]
        file_bytes = await app_context.ai_service.download_telegram_file(message.bot, photo.file_id)

        deducted = await app_context.db.deduct_credits(message.from_user.id, credit_cost)
        if not deducted:
            await processing_msg.edit_text(get_text('error_general', lang), parse_mode='Markdown')
            await state.set_state(UserStates.main_menu)
            return

        generation_id = await app_context.db.create_generation(
            message.from_user.id,
            style['id'],
            photo.file_id,
            credit_cost
        )

        prompt = style['prompt_template']

        result_bytes, error, provider, processing_time = await app_context.ai_service.generate_image(
            file_bytes,
            prompt
        )

        if result_bytes:
            await app_context.db.update_generation(
                generation_id,
                'completed',
                generated_photo_url=photo.file_id,
                api_provider=provider,
                processing_time_ms=processing_time
            )

            new_user = await app_context.db.get_user(message.from_user.id)

            await processing_msg.delete()

            success_text = get_text('success', lang, credits=credit_cost, balance=new_user['credit_balance'])
            await message.answer(success_text, parse_mode='Markdown')

            await message.answer_photo(
                photo.file_id,
                caption="✨ Your transformed photo!"
            )

        else:
            await app_context.db.update_generation(
                generation_id,
                'manual_queue',
                error_message=error,
                api_provider=provider,
                processing_time_ms=processing_time
            )

            logger.info(f"Generation {generation_id} sent to manual queue: {error}")

            new_user = await app_context.db.get_user(message.from_user.id)

            await processing_msg.edit_text(
                "⏳ Our AI is having trouble right now.\n\nNo worries! We've added your request to our priority queue and will complete it manually soon.\n\nYour credits have already been deducted.",
                parse_mode='Markdown'
            )

        await state.set_state(UserStates.main_menu)
        balance = user["credit_balance"]  # or whatever field stores credits
        await message.answer(
                get_text('main_menu', lang, balance=balance),
                reply_markup=get_main_menu_keyboard(lang),
                parse_mode="HTML"
            )

    except Exception as e:
        logger.error(f"Error processing photo: {e}")
        await processing_msg.edit_text(get_text('error_general', lang), parse_mode='Markdown')
        await state.set_state(UserStates.main_menu)


@router.message(UserStates.uploading_photo)
async def invalid_upload(message: Message, app_context: AppContext):
    user = await app_context.db.get_user(message.from_user.id)
    lang = user['language']

    await message.answer(
        "📸 Please upload a photo!",
        parse_mode='Markdown'
    )
