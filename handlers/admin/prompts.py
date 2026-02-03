# handlers/admin/style_upload.py
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from config.settings import settings
from app_context import AppContext
from utils.logger import logger
from states.admin_states import AdminStyleStates
from keyboards.inline import (
    build_styles_list_keyboard,
    get_prompts_reply_keyboard,
    get_style_upload_keyboard,
    get_style_confirm_keyboard,
    get_style_field_keyboard,
)

router = Router()


def is_admin(user_id: int) -> bool:
    return user_id in settings.ADMIN_IDS


# Helper to render the current collected data as a single review caption
def render_style_review_caption(data: dict) -> str:
    """
    Returns a polished caption used for the final preview.
    This is designed to be sent as a photo caption (template-like).
    """
    name_en = data.get("name_en", "—")
    name_am = data.get("name_am", "—")
    desc_en = data.get("description_en", "—")
    desc_am = data.get("description_am", "—")
    prompt = data.get("prompt_template", "—")
    credit_cost = data.get("credit_cost", "—")
    is_active = data.get("is_active", True)
    display_order = data.get("display_order", 0)

    caption = (
        "🎨 <b>Style Template Preview</b>\n\n"
        f"🆔 <b>Name (EN):</b> {name_en}\n"
        f"🇪🇹 <b>Name (AM):</b> {name_am}\n\n"
        f"📘 <b>Description (EN):</b>\n{desc_en}\n\n"
        f"📗 <b>Description (AM):</b>\n{desc_am}\n\n"
        f"🧠 <b>Prompt Template:</b>\n<code>{prompt}</code>\n\n"
        f"💎 <b>Credit Cost:</b> {credit_cost}  •  "
        f"🔁 <b>Active:</b> {'Yes' if is_active else 'No'}  •  "
        f"🔢 <b>Order:</b> {display_order}\n\n"
        "⚡ Tap Confirm to save, Edit to change fields, or Cancel to abort."
    )
    return caption


# Fallback textual review (used when no preview image is provided)
def render_style_review_text(data: dict) -> str:
    name_en = data.get("name_en", "—")
    name_am = data.get("name_am", "—")
    desc_en = data.get("description_en", "—")
    desc_am = data.get("description_am", "—")
    prompt = data.get("prompt_template", "—")
    credit_cost = data.get("credit_cost", "—")
    is_active = data.get("is_active", True)
    display_order = data.get("display_order", 0)

    text = (
        "<b>🎨 Style Review</b>\n\n"
        f"📝 <b>Name (EN):</b> {name_en}\n"
        f"🇪🇹 <b>Name (AM):</b> {name_am}\n\n"
        f"📖 <b>Description (EN):</b>\n{desc_en}\n\n"
        f"📖 <b>Description (AM):</b>\n{desc_am}\n\n"
        f"✨ <b>Prompt Template:</b>\n{prompt}\n\n"
        f"💎 <b>Credit Cost:</b> {credit_cost}\n"
        f"🔁 <b>Active:</b> {'Yes' if is_active else 'No'}\n"
        f"🔢 <b>Display Order:</b> {display_order}\n\n"
        "Use the buttons below to confirm, edit, or cancel."
    )
    return text


# ---------- Flow start ----------
@router.message(F.text == "➕ Add New Style")
async def cmd_add_style(message: Message, app_context: AppContext, state: FSMContext):
    if not is_admin(message.from_user.id):
        await message.answer("❌ You are not authorized to use this command.")
        return

    # initialize state data
    await state.set_state(AdminStyleStates.waiting_name_en)
    await state.update_data({
        "name_en": None,
        "name_am": None,
        "description_en": None,
        "description_am": None,
        "prompt_template": None,
        "credit_cost": None,
        "is_active": True,
        "display_order": 0,
        "preview_image": None,
    })

    # send a single progress message that will be edited as admin fills fields
    progress_text = (
        "🚀 <b>New Style Creator — 2030 Edition</b>\n\n"
        "Step 1️⃣ • <b>Name (EN)</b>\n\n"
        "✍️ Send the English name for the style."
    )
    sent = await message.answer(progress_text, reply_markup=get_style_upload_keyboard(), parse_mode="HTML")
    await state.update_data(progress_message_id=sent.message_id, progress_chat_id=sent.chat.id)


# ---------- Field handlers (emoji-rich UX copy) ----------
@router.message(AdminStyleStates.waiting_name_en)
async def handle_name_en(message: Message, state: FSMContext, app_context: AppContext):
    await state.update_data(name_en=message.text)
    await state.set_state(AdminStyleStates.waiting_name_am)
    data = await state.get_data()

    new_text = (
        "✨ <b>Adding New Style</b>\n\n"
        "Step 2️⃣ • <b>Name (AM)</b>\n\n"
        f"✅ <b>Name (EN):</b> {data['name_en']}\n\n"
        "🇪🇹 Send the Amharic name (or /skip to leave empty)."
    )
    try:
        await message.bot.edit_message_text(new_text, data["progress_chat_id"], data["progress_message_id"],
                                            reply_markup=get_style_upload_keyboard(), parse_mode="HTML")
    except Exception:
        await message.answer(new_text, reply_markup=get_style_upload_keyboard(), parse_mode="HTML")


@router.message(AdminStyleStates.waiting_name_am)
async def handle_name_am(message: Message, state: FSMContext):
    if message.text.strip() == "/skip":
        await state.update_data(name_am=None)
    else:
        await state.update_data(name_am=message.text)

    await state.set_state(AdminStyleStates.waiting_description_en)
    data = await state.get_data()

    new_text = (
        "✨ <b>Adding New Style</b>\n\n"
        "Step 3️⃣ • <b>Description (EN)</b>\n\n"
        f"📝 <b>Name (EN):</b> {data.get('name_en','—')}\n"
        f"🇪🇹 <b>Name (AM):</b> {data.get('name_am','—')}\n\n"
        "📎 Send a short English description."
    )
    try:
        await message.bot.edit_message_text(new_text, data["progress_chat_id"], data["progress_message_id"],
                                            reply_markup=get_style_upload_keyboard(), parse_mode="HTML")
    except Exception:
        await message.answer(new_text, reply_markup=get_style_upload_keyboard(), parse_mode="HTML")


@router.message(AdminStyleStates.waiting_description_en)
async def handle_desc_en(message: Message, state: FSMContext):
    await state.update_data(description_en=message.text)
    await state.set_state(AdminStyleStates.waiting_description_am)
    data = await state.get_data()

    new_text = (
        "✨ <b>Adding New Style</b>\n\n"
        "Step 4️⃣ • <b>Description (AM)</b>\n\n"
        f"📘 <b>Description (EN):</b>\n{data.get('description_en','—')}\n\n"
        "🇪🇹 Send the Amharic description (or /skip)."
    )
    try:
        await message.bot.edit_message_text(new_text, data["progress_chat_id"], data["progress_message_id"],
                                            reply_markup=get_style_upload_keyboard(), parse_mode="HTML")
    except Exception:
        await message.answer(new_text, reply_markup=get_style_upload_keyboard(), parse_mode="HTML")


@router.message(AdminStyleStates.waiting_description_am)
async def handle_desc_am(message: Message, state: FSMContext):
    if message.text.strip() == "/skip":
        await state.update_data(description_am=None)
    else:
        await state.update_data(description_am=message.text)

    await state.set_state(AdminStyleStates.waiting_prompt_template)
    data = await state.get_data()

    new_text = (
        "✨ <b>Adding New Style</b>\n\n"
        "Step 5️⃣ • <b>Prompt Template</b>\n\n"
        f"📘 <b>Description (EN):</b>\n{data.get('description_en','—')}\n\n"
        "🧾 Send the prompt template that the AI will use."
    )
    try:
        await message.bot.edit_message_text(new_text, data["progress_chat_id"], data["progress_message_id"],
                                            reply_markup=get_style_upload_keyboard(), parse_mode="HTML")
    except Exception:
        await message.answer(new_text, reply_markup=get_style_upload_keyboard(), parse_mode="HTML")


@router.message(AdminStyleStates.waiting_prompt_template)
async def handle_prompt(message: Message, state: FSMContext):
    await state.update_data(prompt_template=message.text)
    await state.set_state(AdminStyleStates.waiting_credit_cost)
    data = await state.get_data()

    new_text = (
        "✨ <b>Adding New Style</b>\n\n"
        "Step 6️⃣ • <b>Credit Cost</b>\n\n"
        f"🧠 <b>Prompt:</b>\n{data.get('prompt_template','—')}\n\n"
        "💎 Send the integer credit cost (e.g., 1)."
    )
    try:
        await message.bot.edit_message_text(new_text, data["progress_chat_id"], data["progress_message_id"],
                                            reply_markup=get_style_upload_keyboard(), parse_mode="HTML")
    except Exception:
        await message.answer(new_text, reply_markup=get_style_upload_keyboard(), parse_mode="HTML")


@router.message(AdminStyleStates.waiting_credit_cost)
async def handle_credit_cost(message: Message, state: FSMContext):
    try:
        cost = int(message.text.strip())
    except ValueError:
        await message.answer("⚠️ Please send a valid integer for credit cost.")
        return

    await state.update_data(credit_cost=cost)
    await state.set_state(AdminStyleStates.waiting_preview_image)
    data = await state.get_data()

    new_text = (
        "✨ <b>Adding New Style</b>\n\n"
        "Step 7️⃣ • <b>Preview Image</b>\n\n"
        f"💎 <b>Credit Cost:</b> {cost}\n\n"
        "📸 Send a photo to use as preview, or send /skip to leave empty."
    )
    try:
        await message.bot.edit_message_text(new_text, data["progress_chat_id"], data["progress_message_id"],
                                            reply_markup=get_style_upload_keyboard(), parse_mode="HTML")
    except Exception:
        await message.answer(new_text, reply_markup=get_style_upload_keyboard(), parse_mode="HTML")


# ---------- Preview handlers ----------
@router.message(AdminStyleStates.waiting_preview_image, F.photo)
async def handle_preview_photo(message: Message, state: FSMContext):
    # take highest resolution
    file_id = message.photo[-1].file_id
    await state.update_data(preview_image=file_id)
    await state.set_state(AdminStyleStates.confirming)
    data = await state.get_data()

    # Build a template-like caption and send the actual image with caption
    caption = render_style_review_caption(data)
    try:
        await message.bot.send_photo(
            chat_id=data["progress_chat_id"],
            photo=file_id,
            caption=caption,
            reply_markup=get_style_confirm_keyboard(),
            parse_mode="HTML"
        )
    except Exception:
        # fallback to text review if sending photo fails
        review_text = render_style_review_text(data)
        await message.answer(review_text, reply_markup=get_style_confirm_keyboard(), parse_mode="HTML")


@router.message(AdminStyleStates.waiting_preview_image)
async def handle_preview_skip(message: Message, state: FSMContext):
    if message.text.strip() == "/skip":
        await state.update_data(preview_image=None)
        await state.set_state(AdminStyleStates.confirming)
        data = await state.get_data()

        # No image: send a polished textual template preview
        review_text = render_style_review_text(data)
        try:
            await message.bot.send_message(
                chat_id=data["progress_chat_id"],
                text=review_text,
                reply_markup=get_style_confirm_keyboard(),
                parse_mode="HTML"
            )
        except Exception:
            await message.answer(review_text, reply_markup=get_style_confirm_keyboard(), parse_mode="HTML")
    else:
        await message.answer("📸 Please send a photo or /skip.")


# ---------- Callback navigation & confirmation ----------
# Exclude the explicit confirm callback so it can be handled separately
@router.callback_query(F.data.startswith("style_upload:") & (F.data != "style_upload:confirm")) & (F.data != "style_upload:edit")
async def style_upload_navigation(callback: CallbackQuery, state: FSMContext, app_context: AppContext):
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Not authorized", show_alert=True)
        return

    action = callback.data.split(":", 1)[1]
    data = await state.get_data()

    order = [
        AdminStyleStates.waiting_name_en,
        AdminStyleStates.waiting_name_am,
        AdminStyleStates.waiting_description_en,
        AdminStyleStates.waiting_description_am,
        AdminStyleStates.waiting_prompt_template,
        AdminStyleStates.waiting_credit_cost,
        AdminStyleStates.waiting_preview_image,
        AdminStyleStates.confirming,
    ]

    current = await state.get_state()
    try:
        idx = order.index(current)
    except ValueError:
        idx = 0

    # Back navigation
    if action == "back":
        new_idx = max(0, idx - 1)
        await state.set_state(order[new_idx])
        step_name = order[new_idx].state
        new_text = (
            "↩️ <b>Step Back</b>\n\n"
            f"Now editing: <b>{step_name}</b>\n\n"
            "Send the requested value or use the buttons."
        )
        try:
            await callback.message.edit_text(new_text, reply_markup=get_style_upload_keyboard(), parse_mode="HTML")
        except Exception:
            await callback.message.answer(new_text, reply_markup=get_style_upload_keyboard(), parse_mode="HTML")
        await callback.answer()
        return

    # Next navigation
    if action == "next":
        new_idx = min(len(order) - 1, idx + 1)
        await state.set_state(order[new_idx])
        step_name = order[new_idx].state
        new_text = (
            "➡️ <b>Step Forward</b>\n\n"
            f"Now editing: <b>{step_name}</b>\n\n"
            "Send the requested value or use the buttons."
        )
        try:
            await callback.message.edit_text(new_text, reply_markup=get_style_upload_keyboard(), parse_mode="HTML")
        except Exception:
            await callback.message.answer(new_text, reply_markup=get_style_upload_keyboard(), parse_mode="HTML")
        await callback.answer()
        return

    # Cancel flow
    if action == "cancel":
        await state.clear()
        try:
            await callback.message.edit_text("❌ <b>Style creation cancelled.</b>", parse_mode="HTML")
        except Exception:
            await callback.message.answer("❌ Style creation cancelled.")
        await callback.answer()
        return

    # Confirm is intentionally not handled here
@router.callback_query(F.data == "style_upload:confirm")
async def style_upload_confirm(callback: CallbackQuery, state: FSMContext, app_context: AppContext):
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Not authorized", show_alert=True)
        return

    data = await state.get_data()
    required = ["name_en", "prompt_template", "credit_cost"]
    missing = [f for f in required if not data.get(f)]
    if missing:
        await callback.answer(f"⚠️ Missing required fields: {', '.join(missing)}", show_alert=True)
        return

    style_id = data.get("style_id")
    try:
        if style_id:
            # ✅ Update existing style
            await app_context.db.update_style(
                style_id,
                name_en=data.get("name_en"),
                name_am=data.get("name_am"),
                description_en=data.get("description_en"),
                description_am=data.get("description_am"),
                prompt_template=data.get("prompt_template"),
                credit_cost=data.get("credit_cost"),
                is_active=data.get("is_active", True),
                display_order=data.get("display_order", 0),
                preview_image_url=data.get("preview_image"),
            )
            success_text = f"✅ <b>Style Updated</b>\n\n🆔 ID: <code>{style_id}</code>"
        else:
            # ➕ Create new style
            style_id = await app_context.db.create_style(
                name_en=data.get("name_en"),
                name_am=data.get("name_am"),
                description_en=data.get("description_en"),
                description_am=data.get("description_am"),
                prompt_template=data.get("prompt_template"),
                credit_cost=data.get("credit_cost"),
                is_active=data.get("is_active", True),
                display_order=data.get("display_order", 0),
                preview_image_url=data.get("preview_image"),
            )
            success_text = f"🎉 <b>Style Created</b>\n\n🆔 ID: <code>{style_id}</code>"

        await callback.message.edit_text(success_text, parse_mode="HTML")
    except Exception:
        await callback.message.answer("❌ Failed to save style. Check logs.", parse_mode="HTML")

    await state.clear()
    await callback.answer("Saved")


@router.callback_query(F.data == "style_upload:edit")
async def style_upload_edit(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Not authorized", show_alert=True)
        return

    data = await state.get_data()
    review_text = render_style_review_text(data)
    try:
        await callback.message.edit_text(review_text, reply_markup=get_style_field_keyboard(""), parse_mode="HTML")
    except Exception:
        await callback.message.answer(review_text, reply_markup=get_style_field_keyboard(""), parse_mode="HTML")
    await callback.answer()


# Individual edit callbacks (jump to a specific field)
@router.callback_query(F.data.startswith("style_edit:"))
async def style_edit_field(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Not authorized", show_alert=True)
        return

    action = callback.data.split(":", 1)[1]
    mapping = {
        "name_en": AdminStyleStates.waiting_name_en,
        "name_am": AdminStyleStates.waiting_name_am,
        "desc_en": AdminStyleStates.waiting_description_en,
        "desc_am": AdminStyleStates.waiting_description_am,
        "prompt": AdminStyleStates.waiting_prompt_template,
        "cost": AdminStyleStates.waiting_credit_cost,
        "preview_image": AdminStyleStates.waiting_preview_image,
        "back": AdminStyleStates.confirming,
    }
    if action not in mapping:
        await callback.answer()
        return

    await state.set_state(mapping[action])
    try:
        await callback.message.edit_text(f"✏️ Editing <b>{action}</b>\n\nPlease send the new value.", parse_mode="HTML")
    except Exception:
        await callback.message.answer(f"✏️ Editing <b>{action}</b>\n\nPlease send the new value.", parse_mode="HTML")
    await callback.answer()



# --- Handler: open Prompts menu (reply keyboard) ---
@router.message(F.text == "✨ Prompts")
async def open_prompts_menu(message: Message):
    if not is_admin(message.from_user.id):
        await message.answer("❌ Not authorized")
        return
    text = (
        "🧭 <b>Prompts Hub</b>\n\n"
        "Choose an action below to manage style prompts and templates.\n\n"
        "➕ Create a new style\n"
        "📚 Browse existing styles"
    )
    await message.answer(text, reply_markup=get_prompts_reply_keyboard(), parse_mode="HTML")

# --- Handler: View Styles (reply button) ---
@router.message(F.text == "📚 View Styles")
async def list_styles(message: Message, app_context: AppContext):
    if not is_admin(message.from_user.id):
        await message.answer("❌ Not authorized")
        return

    # fetch all styles (you can adjust to fetch paginated from DB if available)
    styles = await app_context.db.get_all_styles()  # implement or adapt to your DB method
    if not styles:
        await message.answer("📭 No styles found.", reply_markup=get_prompts_reply_keyboard())
        return

    kb = build_styles_list_keyboard(styles, page=0, page_size=5)
    await message.answer("📚 <b>Available Styles</b>\n\nSelect a style to view details.", reply_markup=kb, parse_mode="HTML")

# --- Callback: paginate style list or go back ---
@router.callback_query(F.data.startswith("list_style:"))
async def style_list_navigation(callback: CallbackQuery, app_context: AppContext):
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Not authorized", show_alert=True)
        return

    parts = callback.data.split(":")
    if parts[1] == "page":
        page = int(parts[2])
        styles = await app_context.db.get_all_styles()
        kb = build_styles_list_keyboard(styles, page=page, page_size=5)
        try:
            await callback.message.edit_text("📚 <b>Available Styles</b>\n\nSelect a style to view details.", reply_markup=kb, parse_mode="HTML")
        except Exception:
            await callback.message.answer("📚 <b>Available Styles</b>\n\nSelect a style to view details.", reply_markup=kb, parse_mode="HTML")
        await callback.answer()
        return

    if parts[1] == "back":
        # return to prompts reply keyboard
        try:
            await callback.message.edit_text("🧭 <b>Prompts Hub</b>\n\nChoose an action below.", reply_markup=None, parse_mode="HTML")
        except Exception:
            pass
        await callback.message.answer(
            "🧭 Back to Prompts",
            reply_markup=get_prompts_reply_keyboard(),
            parse_mode="HTML"
        )
        await callback.answer()
        return

@router.callback_query(F.data.startswith("view_style:"))
async def style_view(callback: CallbackQuery, app_context: AppContext, state: FSMContext):
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Not authorized", show_alert=True)
        return

    style_id = callback.data.split(":", 1)[1]
    style = await app_context.db.get_style(style_id)
    if not style:
        await callback.answer("❌ Style not found", show_alert=True)
        return

    # prepare data dict compatible with render functions
    data = {
        "name_en": style.get("name_en"),
        "name_am": style.get("name_am"),
        "description_en": style.get("description_en"),
        "description_am": style.get("description_am"),
        "prompt_template": style.get("prompt_template"),
        "credit_cost": style.get("credit_cost"),
        "is_active": style.get("is_active", True),
        "display_order": style.get("display_order", 0),
        "preview_image": style.get("preview_image_url") or style.get("preview_image"),
    }

    # ✅ Hydrate FSM state with full style data
    await state.update_data(style_id=style_id, **data)

    caption = render_style_review_caption(data)
    preview = data.get("preview_image")
    edit_kb = get_style_field_keyboard("")  

    try:
        if preview:
            await callback.message.answer_photo(photo=preview, caption=caption, reply_markup=edit_kb, parse_mode="HTML")
        else:
            text = render_style_review_text(data)
            await callback.message.answer(text, reply_markup=edit_kb, parse_mode="HTML")
    except Exception:
        text = render_style_review_text(data)
        await callback.message.answer(text, reply_markup=edit_kb, parse_mode="HTML")

    await callback.answer()

@router.callback_query(F.data == "edit_style:delete")
async def style_upload_delete(callback: CallbackQuery, app_context: AppContext, state: FSMContext):
    print('here it is ')
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Not authorized", show_alert=True)
        return

    data = await state.get_data()
    style_id = data.get("style_id")

    if not style_id:
        await callback.answer("⚠️ No style loaded", show_alert=True)
        return

    try:
        await app_context.db.delete_style(style_id)  # UUID string is fine
        if callback.message.text:
            await callback.message.edit_text("🗑️ <b>Style deleted successfully.</b>", parse_mode="HTML")
        elif callback.message.caption:
            await callback.message.edit_caption("🗑️ <b>Style deleted successfully.</b>", parse_mode="HTML")
        else:
            # fallback: send a new message
            await callback.message.answer("🗑️ <b>Style deleted successfully.</b>", parse_mode="HTML")
    except Exception as e:
        print("Delete error:", e)
        await callback.message.answer("❌ Failed to delete style.", parse_mode="HTML")

    await state.clear()
    await callback.answer("Deleted")
