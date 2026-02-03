import asyncio
import io
from aiogram import Router, F
from aiogram.filters import CommandStart
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from telegram import InputFile, InputMediaPhoto
from states import UserStates
from aiogram.exceptions import TelegramBadRequest
from keyboards.reply import get_main_menu_keyboard, get_cancel_keyboard
from keyboards.inline import get_styles_keyboard, get_packages_keyboard, get_language_keyboard
from utils.helpers import TEXTS, get_text, get_button
from config.settings import settings
from app_context import AppContext
from utils.logger import logger
from typing import List, Optional

from utils.tasks import notify_admin_manual_queue, notify_admins_new_user
router = Router()

CHANNEL_USERNAME = settings.CHANNEL_USERNAME  # from .env

async def check_membership(bot, user_id: int) -> bool:
    try:
        member = await bot.get_chat_member(CHANNEL_USERNAME, user_id)
        return member.status in ("member", "administrator", "creator")
    except TelegramBadRequest as e:
        # Print the error details for debugging
        print(f"TelegramBadRequest while checking membership: {e}")
        return False
    except Exception as e:
        # Catch any other unexpected errors
        print(f"Unexpected error while checking membership: {e}")
        return False
@router.message(CommandStart())
async def start_command(message: Message, state: FSMContext, app_context: AppContext):
    user = await app_context.db.get_user(message.from_user.id)

    # 1️⃣ If user is new → ask language first
    if not user:
        await message.answer(
            get_text("onboarding_choose_language", "en") + " / " +
            get_text("onboarding_choose_language", "am"),
            reply_markup=get_language_keyboard()
        )
        await state.set_state(UserStates.selecting_language)
        return

    # 2️⃣ If user exists → enforce channel membership
    lang = user["language"]
    if not await check_membership(message.bot, message.from_user.id):
        join_kb = InlineKeyboardMarkup(inline_keyboard=[[
            InlineKeyboardButton(
                text=get_button("join_channel", lang),
                url=f"https://t.me/{CHANNEL_USERNAME.strip('@')}"
            ),
            InlineKeyboardButton(
                text=get_button("joined_confirm", lang),
                callback_data="check_joined"
            )
        ]])
        await message.answer(get_text("onboarding_join_channel", lang), reply_markup=join_kb)
        return

    # 3️⃣ Continue normal flow
    await app_context.db.update_last_active(message.from_user.id)
    balance = user["credit_balance"]  # or whatever field stores credits
    await message.answer(
        get_text('main_menu', lang, balance=balance),
        reply_markup=get_main_menu_keyboard(lang),
        parse_mode="HTML"
    )
    await state.set_state(UserStates.main_menu)
@router.callback_query(F.data.startswith("lang_"))
async def language_selected(callback: CallbackQuery, state: FSMContext, app_context: AppContext):
    lang = "en" if callback.data == "lang_en" else "am"

    # Create user with chosen language
    user = await app_context.db.create_user(
        callback.from_user.id,
        callback.from_user.username,
        callback.from_user.first_name,
        lang,
        settings.BONUS_CREDITS
    )

    # 🎉 Playful animation (optional)
    # await callback.message.answer_animation("https://media.giphy.com/media/26ufdipQqU2lhNA4g/giphy.gif")

    # Edit the original language message to show localized welcome
    welcome_text = get_text('welcome', lang, credits=settings.BONUS_CREDITS)
    await callback.message.edit_text(welcome_text, parse_mode='Markdown')

    # ✅ After language is set → enforce channel membership
    if not await check_membership(callback.bot, callback.from_user.id):
        join_kb = InlineKeyboardMarkup(inline_keyboard=[[
            InlineKeyboardButton(
                text=get_button("join_channel", lang),
                url=f"https://t.me/{CHANNEL_USERNAME.strip('@')}"
            ),
            InlineKeyboardButton(
                text=get_button("joined_confirm", lang),
                callback_data="check_joined"
            )
        ]])
        await callback.message.answer(get_text("onboarding_join_channel", lang), reply_markup=join_kb)
        return

    # ✅ If already joined → show main menu with reply keyboard
    balance = settings.BONUS_CREDITS  # or whatever field stores credits
    await callback.message.answer(
            get_text('main_menu', lang, balance=balance),
            reply_markup=get_main_menu_keyboard(lang),
            parse_mode="HTML"
)

    await notify_admins_new_user(callback.bot, user)
    await state.set_state(UserStates.main_menu)
@router.callback_query(F.data == "check_joined")
async def check_joined(callback: CallbackQuery, state: FSMContext, app_context: AppContext):
    user = await app_context.db.get_user(callback.from_user.id)
    lang = user["language"] if user else "en"

    if await check_membership(callback.bot, callback.from_user.id):
        # ✅ Edit the original inline message to show success
        await callback.message.edit_text(
            get_text("onboarding_thanks_joined", lang)
        )
        # Then send the main menu with reply keyboard
        balance = user["credit_balance"]  # or whatever field stores credits
        await callback.message.answer(
            get_text('main_menu', lang, balance=balance),
            reply_markup=get_main_menu_keyboard(lang),
            parse_mode="HTML"
)
        await notify_admins_new_user(callback.bot, user)
        await state.set_state(UserStates.main_menu)
    else:
        # ❌ Show alert if still not joined
        await callback.answer(get_text("onboarding_still_required", lang), show_alert=True)

#--------------
# Small helpers
# -------------------------
def prompt_teaser(prompt: Optional[str], words: int = 12) -> str:
    if not prompt:
        return "—"
    parts = prompt.strip().split()
    if len(parts) <= words:
        return " ".join(parts)
    return " ".join(parts[:words]) + " ..."

def short_description(desc: Optional[str], max_chars: int = 100) -> str:
    if not desc:
        return "—"
    if len(desc) <= max_chars:
        return desc
    return desc[:max_chars].rstrip() + " …"

# -------------------------
# Page sender: send N style cards per page
# -------------------------
async def send_styles_cards_page(message_or_callback, styles: List[dict], page: int, lang: str, page_size: int = 4):
    """
    Send compact style cards per page.
    Each card shows photo (if available), emoji+name, short description teaser, cost,
    and inline buttons (View / Choose).
    After the cards, send a navigation keyboard (Prev / Next / Back).
    """
    start = page * page_size
    end = start + page_size
    subset = styles[start:end]

    for s in subset:
        name = s.get("name_am") if lang == 'am' else s.get("name_en") or s.get("name_am") or "Untitled"
        emoji = s.get("emoji_tag") or "🎨"
        desc = s.get("description_am") if lang == 'am' else s.get("description_en") or ""
        desc_short = short_description(desc, max_chars=90)  # keep it concise
        cost = s.get("credit_cost", 1)

        caption = (
            f"{emoji} <b>{name}</b>\n\n"
            f"{desc_short}\n\n"
            f"💎 <b>Cost:</b> {cost} credit{'s' if cost != 1 else ''}"
        )

        card_kb = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text=get_button('view', lang), callback_data=f"style_view:{s['id']}"),
                InlineKeyboardButton(text=get_button('choose_style', lang), callback_data=f"style_choose:{s['id']}")
            ]
        ])

        if s.get('preview_image_url'):
            try:
                await message_or_callback.answer_photo(
                    s['preview_image_url'],
                    caption=caption,
                    reply_markup=card_kb,
                    parse_mode="HTML"
                )
            except Exception:
                await message_or_callback.answer(caption, reply_markup=card_kb, parse_mode="HTML")
        else:
            await message_or_callback.answer(caption, reply_markup=card_kb, parse_mode="HTML")

    # Navigation keyboard
    total_pages = ((len(styles) - 1) // page_size) + 1 if styles else 1
    nav_buttons = []
    if page > 0:
        nav_buttons.append(InlineKeyboardButton(text=get_button('prev', lang), callback_data=f"style_list:page:{page-1}"))
    if end < len(styles):
        nav_buttons.append(InlineKeyboardButton(text=get_button('next', lang), callback_data=f"style_list:page:{page+1}"))

    nav_rows = []
    if nav_buttons:
        nav_rows.append(nav_buttons)
    nav_rows.append([InlineKeyboardButton(text=get_button('back', lang), callback_data="style_list:back")])

    nav_kb = InlineKeyboardMarkup(inline_keyboard=nav_rows)

    page_text = get_text('browse_styles_page', lang, page=page+1, total_pages=total_pages)
    try:
        await message_or_callback.answer(page_text, reply_markup=nav_kb, parse_mode="HTML")
    except Exception:
        try:
            await message_or_callback.message.answer(page_text, reply_markup=nav_kb, parse_mode="HTML")
        except Exception:
            pass

# -------------------------
# Handlers: entry, pagination, view, choose
# -------------------------
@router.message(F.text.in_([get_button('generate_photo', 'en'), get_button('generate_photo', 'am')]))
async def start_generation_preview(message: Message, state: FSMContext, app_context: AppContext):
    user = await app_context.db.get_user(message.from_user.id)
    if not user:
        await message.answer(get_text('error_general', 'en'))
        return
    lang = user.get('language', 'en')

    # Prevent spam: check if user already has an active/pending/manual generation
    try:
        has_active = await app_context.db.user_has_active_generation(message.from_user.id)
    except Exception:
        logger.warning("user_has_active_generation missing or failed; allowing flow")
        has_active = False

    if has_active:
        await message.answer(get_text('already_pending', lang), parse_mode="HTML")
        return

    styles = await app_context.db.get_active_styles()
    if not styles:
        await message.answer(get_text('error_general', lang))
        return

    # Send first page (cards + navigation)
    await send_styles_cards_page(message, styles, page=0, lang=lang, page_size=4)
    await state.set_state(UserStates.selecting_style)

@router.callback_query(F.data.startswith("style_list:"))
async def style_list_navigation(callback: CallbackQuery, state: FSMContext, app_context: AppContext):
    user = await app_context.db.get_user(callback.from_user.id)
    if not user:
        await callback.answer(get_text('error_general', 'en'), show_alert=True)
        return
    lang = user.get('language', 'en')

    parts = callback.data.split(":")
    action = parts[1]
    if action == "page":
        page = int(parts[2])
        styles = await app_context.db.get_active_styles()
        # Try to edit the current message to show page header, then send cards
        try:
            await callback.message.edit_text(get_text('browse_styles_page', lang, page=page+1), reply_markup=None, parse_mode="HTML")
        except Exception:
            pass
        await send_styles_cards_page(callback.message, styles, page=page, lang=lang, page_size=4)
        await callback.answer()
        return

    if action == "back":
        try:
            balance = user["credit_balance"]  # or whatever field stores credits
            await callback.message.answer(
                get_text('main_menu', lang, balance=balance),
                reply_markup=get_main_menu_keyboard(lang),
                parse_mode="HTML"
            )

        except Exception:
            pass
        # balance = user["credit_balance"]  # or whatever field stores credits
        # await callback.message.answer(
        #         get_text('main_menu', lang, balance=balance),
        #         reply_markup=get_main_menu_keyboard(lang),
        #         parse_mode="HTML"
        #     )
        await callback.answer()
        return

@router.callback_query(F.data.startswith("style_view:"))
async def style_view(callback: CallbackQuery, state: FSMContext, app_context: AppContext):
    style_id = callback.data.split(":", 1)[1]
    user = await app_context.db.get_user(callback.from_user.id)
    if not user:
        await callback.answer(get_text('error_general', 'en'), show_alert=True)
        return
    lang = user.get('language', 'en')

    style = await app_context.db.get_style(style_id)
    if not style:
        await callback.answer(get_text('error_general', lang), show_alert=True)
        return

    teaser = prompt_teaser(style.get('prompt_template', ''), words=12)
    style_name = style['name_am'] if lang == 'am' else style['name_en']
    desc = style['description_am'] if lang == 'am' else style['description_en']
    cost = style['credit_cost']
    emoji = style.get('emoji_tag') or "🎨"
    plural = '' if cost == 1 else 's'

    caption = get_text(
        'style_view_caption',
        lang,
        style_name=style_name,
        emoji=emoji,
        desc=desc or "—",
        cost=cost,
        teaser=teaser,
        plural=plural
    )

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=get_button('choose_style', lang), callback_data=f"style_choose:{style_id}")],
        # [InlineKeyboardButton(text=get_button('back_to_previews', lang), callback_data="style_list:page:0")]
    ])

    if style.get('preview_image_url'):
        try:
            await callback.message.answer_photo(style['preview_image_url'], caption=caption, reply_markup=kb, parse_mode="HTML")
        except Exception:
            await callback.message.answer(caption, reply_markup=kb, parse_mode="HTML")
    else:
        await callback.message.answer(caption, reply_markup=kb, parse_mode="HTML")

    await callback.answer()

@router.callback_query(F.data.startswith("style_choose:"))
async def style_choose(callback: CallbackQuery, state: FSMContext, app_context: AppContext):
    style_id = callback.data.split(":", 1)[1]
    user = await app_context.db.get_user(callback.from_user.id)
    if not user:
        await callback.answer(get_text('error_general', 'en'), show_alert=True)
        return
    lang = user.get('language', 'en')

    try:
        has_active = await app_context.db.user_has_active_generation(callback.from_user.id)
    except Exception:
        logger.warning("user_has_active_generation missing or failed; allowing choose")
        has_active = False

    if has_active:
        await callback.answer(get_text('already_pending', lang), show_alert=True)
        return

    style = await app_context.db.get_style(style_id)
    if not style:
        await callback.answer(get_text('error_general', lang), show_alert=True)
        return

    await state.update_data(selected_style=style)
    await state.set_state(UserStates.uploading_photo)

    await callback.message.answer(
        get_text('choose_style_prompt', lang, name=(style['name_am'] if lang == 'am' else style['name_en'])),
        reply_markup=get_cancel_keyboard(lang),
        parse_mode="HTML"
    )
    await callback.answer(get_text('ready_receive', lang))

from aiogram.filters import StateFilter

@router.message(StateFilter(UserStates.uploading_photo), F.text.in_(['❌ Cancel', '❌ ሰርዝ']))
async def cancel_upload(message: Message, state: FSMContext, app_context: AppContext):
    user = await app_context.db.get_user(message.from_user.id)
    lang = user.get('language', 'en') if user else 'en'

    await state.clear()
    await message.answer(
        get_text('cancelled', lang),
        reply_markup=get_main_menu_keyboard(lang),
        parse_mode="Markdown"
    )

# Helper: small retry wrapper for generation
async def _generate_with_retry(ai_service, image_bytes: bytes, prompt: str, retries: int = 1, delay_s: float = 1.0):
    """
    Try to generate image. On failure, retry `retries` times with delay.
    Returns (result_bytes, error, provider, processing_time_ms)
    """
    last_error = None
    for attempt in range(retries + 1):
        try:
            result_bytes, error, provider, processing_time = await ai_service.generate_image(image_bytes, prompt)
            # If API returned an error string but also bytes, treat as success if bytes present
            if result_bytes:
                return result_bytes, None, provider, processing_time
            # If no bytes, capture error and possibly retry
            last_error = error or "No image returned"
            logger.warning(f"[_generate_with_retry] attempt={attempt} provider={provider} error={last_error}")
        except Exception as exc:
            last_error = str(exc)
            logger.exception(f"[_generate_with_retry] exception on attempt={attempt}: {last_error}")
        if attempt < retries:
            await asyncio.sleep(delay_s)
    # final return: no bytes
    return None, last_error, "manual", 0

@router.message(UserStates.uploading_photo, F.photo)
async def photo_received(message: Message, state: FSMContext, app_context: AppContext):
    """
    Handles user photo upload after they selected a style.
    - Downloads photo bytes
    - Deducts credits and creates generation record
    - Calls AI service (Gemini) to transform image using style prompt
    - Sends result or queues for manual processing
    - Updates DB and logs every step
    """
    user = await app_context.db.get_user(message.from_user.id)
    lang = user.get('language', 'en') if user else 'en'

    state_data = await state.get_data()
    style = state_data.get('selected_style')
    if not style:
        await message.answer(get_text('error_general', lang), parse_mode='Markdown')
        await state.set_state(UserStates.main_menu)
        return

    credit_cost = style.get('credit_cost', 1)
    if user['credit_balance'] < credit_cost:
        await message.answer(
            get_text('insufficient_credits', lang, required=credit_cost, balance=user['credit_balance']),
            parse_mode='Markdown'
        )
        await state.set_state(UserStates.main_menu)
        return

    processing_msg = await message.answer(get_text('processing', lang), parse_mode='Markdown', reply_markup=get_main_menu_keyboard(lang) )

    try:
        # 1) Download original photo bytes
        photo = message.photo[-1]
        logger.info(f"[photo_received] user={message.from_user.id} style={style['id']} file_id={photo.file_id}")
        original_bytes = await app_context.ai_service.download_telegram_file(message.bot, photo.file_id)
        logger.info(f"[photo_received] downloaded {len(original_bytes)} bytes")

        # 2) Deduct credits
        deducted = await app_context.db.deduct_credits(message.from_user.id, credit_cost)
        if not deducted:
            logger.error(f"[photo_received] failed to deduct credits for user={message.from_user.id}")
            await processing_msg.edit_text(get_text('error_general', lang), parse_mode='Markdown')
            await state.set_state(UserStates.main_menu)
            return

        # 3) Create generation record (store original file_id so admins can preview)
        generation_id = await app_context.db.create_generation(
            user_id=message.from_user.id,
            style_id=style['id'],
            original_photo_url=photo.file_id,
            credits_spent=credit_cost
        )
        logger.info(f"[photo_received] created generation id={generation_id}")

        # 4) Build prompt and call AI (with one retry)
        prompt = style.get('prompt_template') or style.get('prompt') or ""
        logger.debug(f"[photo_received] prompt head: {prompt[:200]}")

        result_bytes, error, provider, processing_time = await _generate_with_retry(
            app_context.ai_service,
            original_bytes,
            prompt,
            retries=1,
            delay_s=1.0
        )

        # 5) Success path: send generated image and update DB
        if result_bytes:
            buf = io.BytesIO(result_bytes)
            buf.seek(0)
            input_file = InputFile(buf, filename="result.jpg")

            # Send success message + image (include localized success text)
            new_user = await app_context.db.get_user(message.from_user.id)
            success_text = get_text('success', lang, credits=credit_cost, balance=new_user['credit_balance'])
            await processing_msg.delete()
            sent = await message.answer_photo(input_file, caption="✨ " + success_text, parse_mode='Markdown')

            # Extract Telegram file_id of the sent photo (highest-res)
            sent_file_id: Optional[str] = None
            if sent and getattr(sent, "photo", None):
                sent_file_id = sent.photo[-1].file_id

            # Update generation record as completed
            await app_context.db.update_generation(
                generation_id=generation_id,
                status='completed',
                generated_photo_url=sent_file_id,
                error_message=None,
                api_provider=provider,
                processing_time_ms=processing_time
            )
            logger.info(f"[photo_received] generation {generation_id} completed provider={provider} time={processing_time}ms")

        # 6) Failure path: queue for manual processing and update DB
        else:
            await app_context.db.update_generation(
                generation_id=generation_id,
                status='manual_queue',
                generated_photo_url=None,
                error_message=error or "Unknown error",
                api_provider=provider,
                processing_time_ms=processing_time
            )
            gen = await app_context.db.get_generation(generation_id)
            logger.info(f"[photo_received] generation {generation_id} queued for manual processing: {error}")
            await notify_admin_manual_queue(message.bot, gen, user, style, app_context)

            # Inform user and keep processing message visible (edit)
            try:
                await processing_msg.edit_text(get_text('manual_queue', lang), parse_mode='Markdown')
            except Exception:
                # If editing fails, just send a new message
                await message.answer(get_text('manual_queue', lang), parse_mode='Markdown')


        # 7) Return user to main menu
        await state.set_state(UserStates.main_menu)
        balance = user["credit_balance"]  # or whatever field stores credits
        await message.answer(
                get_text('main_menu', lang, balance=balance),
                reply_markup=get_main_menu_keyboard(lang),
                parse_mode="HTML"
            )

    except Exception as exc:
        logger.exception(f"[photo_received] unexpected error: {exc}")
        try:
            await processing_msg.edit_text(get_text('error_general', lang), parse_mode='Markdown')
        except Exception:
            pass
        await state.set_state(UserStates.main_menu)

@router.message(F.text.in_(['🧾 My Credits', '🧾 የእኔ ክሬዲቶች']))
async def show_credits(message: Message, app_context: AppContext):
    user = await app_context.db.get_user(message.from_user.id)
    lang = user['language']
    await message.answer(get_text('my_credits', lang, balance=user['credit_balance'], total=user['total_generations']), parse_mode='Markdown')


@router.message(F.text.in_(['💳 Buy Credits', '💳 ክሬዲት ለመግዛት']))
async def buy_credits_menu(message: Message, state: FSMContext, app_context: AppContext):
    user = await app_context.db.get_user(message.from_user.id)
    lang = user['language']
    await message.answer(get_text('buy_credits', lang), reply_markup=get_packages_keyboard(lang), parse_mode='Markdown')
    await state.set_state(UserStates.selecting_package)


from aiogram.filters import Command

@router.message(F.text.in_(['📞 Help', '📞 እገዛ/አስተያየት']))
@router.message(Command("help"))
async def show_help(message: Message, app_context: AppContext):
    user = await app_context.db.get_user(message.from_user.id)
    lang = user['language'] if user else "en"

    await message.answer(
        get_text('help', lang),
        parse_mode="Markdown"
    )



@router.message(F.text.in_(['🔙 Back', '🔙 ተመለስ']))
async def back_to_menu(message: Message, state: FSMContext, app_context: AppContext):
    user = await app_context.db.get_user(message.from_user.id)
    lang = user['language']
    balance = user["credit_balance"]  # or whatever field stores credits
    await message.answer(
                get_text('main_menu', lang, balance=balance),
                reply_markup=get_main_menu_keyboard(lang),
                parse_mode="HTML"
            )
    await state.set_state(UserStates.main_menu)
