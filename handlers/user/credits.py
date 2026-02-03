from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from states import UserStates
from keyboards.reply import get_main_menu_keyboard, get_cancel_keyboard
from utils.helpers import get_button, get_text
from app_context import AppContext
from services.payment import PaymentService
from utils.logger import logger
from config import settings
from utils.tasks import notify_admins_new_payment

router = Router()



@router.callback_query(F.data.startswith('package:'))
async def package_selected(callback: CallbackQuery, state: FSMContext, app_context: AppContext):
    package_type = callback.data.split(':', 1)[1]
    ok, err = PaymentService.validate_package(package_type)
    if not ok:
        await callback.answer("Invalid package", show_alert=True)
        return
    if not ok:
        await callback.answer("Invalid package", show_alert=True)
        return

    user = await app_context.db.get_user(callback.from_user.id)
    lang = user.get('language', 'en')

    package_info = PaymentService.get_package_info(package_type)
    instructions = PaymentService.get_payment_instructions(package_type, lang)

    try:
        await callback.message.edit_text(instructions, parse_mode='Markdown')
    except Exception:
        await callback.message.answer(instructions, parse_mode='Markdown')

    await callback.message.answer(get_text('upload_payment_prompt', lang), reply_markup=get_cancel_keyboard(lang))
    await state.update_data(selected_package=package_type, package_info=package_info)
    await state.set_state(UserStates.uploading_payment)
    await callback.answer()
    
    
@router.message(UserStates.uploading_payment, F.photo)
async def payment_screenshot_received(message: Message, state: FSMContext, app_context: AppContext):
    user = await app_context.db.get_user(message.from_user.id)
    lang = user.get('language', 'en')

    # 🔎 Check if user already has a pending payment
    pending_payments = await app_context.db.get_pending_payments(message.from_user.id)
    if pending_payments:
        await message.answer(
            get_text("payment_pending_review", lang),
            reply_markup=get_main_menu_keyboard(lang),
            parse_mode="Markdown"
        )
        await state.set_state(UserStates.main_menu)
        return


    data = await state.get_data()
    package_type = data.get('selected_package')
    package_info = data.get('package_info')
    if not package_type or not package_info:
        await message.answer(get_text('error_general', lang), parse_mode='Markdown')
        await state.clear()
        await state.set_state(UserStates.main_menu)
        return

    processing_msg = await message.answer(get_text('payment_processing', lang), parse_mode='Markdown')

    try:
        photo = message.photo[-1]
        if photo.file_size > 5 * 1024 * 1024:  # 5 MB limit
            await processing_msg.edit_text(get_text('error_general', lang), parse_mode='Markdown')
            await state.set_state(UserStates.main_menu)
            return

        file_bytes = await app_context.ai_service.download_telegram_file(message.bot, photo.file_id)
        ocr_data = await app_context.ocr_service.extract_payment_info(file_bytes)

        # Always store payment, but status depends on OCR
        status = 'pending' if not ocr_data or not ocr_data.get('amount') else 'submitted'

        payment_id = await app_context.db.create_payment(
            message.from_user.id,
            package_type,
            package_info['price'],
            package_info['credits'],
            photo.file_id,
            ocr_data,
            status=status
        )

        logger.info("Payment created: %s with status %s", payment_id, status)
        await processing_msg.edit_text(get_text('payment_submitted', lang), parse_mode='Markdown')

        # Notify admins with OCR details
        user = await app_context.db.get_user(message.from_user.id)
        payment = await app_context.db.get_payment(payment_id)
        await notify_admins_new_payment(
            bot=message.bot,
            payment_id=payment_id,
            payment=payment,
            user=user,
            ocr_data=ocr_data
        )

        balance = user["credit_balance"]  # or whatever field stores credits
        await message.answer(
                get_text('main_menu', lang, balance=balance),
                reply_markup=get_main_menu_keyboard(lang),
                parse_mode="HTML"
            )
        await state.set_state(UserStates.main_menu)

    except Exception as exc:
        logger.exception("Error processing payment screenshot: %s", exc)
        try:
            await processing_msg.edit_text(get_text('error_general', lang), parse_mode='Markdown')
        except Exception:
            await message.answer(get_text('error_general', lang), parse_mode='Markdown')
        await state.set_state(UserStates.main_menu)


# Cancel handler (specific match first)
@router.message(UserStates.uploading_payment, F.text == get_button("cancel", "en"))
@router.message(UserStates.uploading_payment, F.text == get_button("cancel", "am"))
async def cancel_payment_upload(message: Message, state: FSMContext, app_context: AppContext):
    user = await app_context.db.get_user(message.from_user.id)
    lang = user.get('language', 'en')

    await state.clear()
    await state.set_state(UserStates.main_menu)

    await message.answer(
        get_text("cancelled", lang),
        reply_markup=get_main_menu_keyboard(lang),
        parse_mode="Markdown"
    )


# Catch‑all invalid upload (only if not photo and not cancel)
@router.message(UserStates.uploading_payment, F.text)
async def invalid_payment_upload(message: Message, app_context: AppContext):
    user = await app_context.db.get_user(message.from_user.id)
    lang = user.get('language', 'en')

    # Ignore cancel button text (already handled above)
    if message.text in (get_button("cancel", "en"), get_button("cancel", "am")):
        return

    await message.answer(get_text("upload_payment_invalid", lang), parse_mode="Markdown")
