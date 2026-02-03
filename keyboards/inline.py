from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from typing import List, Dict, Any
from config.settings import settings


def get_styles_keyboard(styles: List[Dict[str, Any]], lang: str = 'en') -> InlineKeyboardMarkup:
    buttons = []
    for style in styles:
        name = style['name_am'] if lang == 'am' else style['name_en']
        cost = style['credit_cost']
        buttons.append([InlineKeyboardButton(text=f"{name} ({cost} 💎)", callback_data=f"style:{style['id']}")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_packages_keyboard(lang: str = 'en') -> InlineKeyboardMarkup:
    buttons = []
    for package_key, package_info in settings.CREDIT_PACKAGES.items():
        name = package_info['name_am'] if lang == 'am' else package_info['name_en']
        price = package_info['price']
        buttons.append([InlineKeyboardButton(text=f"{name} - {price} Birr", callback_data=f"package:{package_key}")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)



def get_language_keyboard() -> InlineKeyboardMarkup:
    keyboard = [
        [
            InlineKeyboardButton(text='🇬🇧 English', callback_data='lang_en'),
            InlineKeyboardButton(text='🇪🇹 አማርኛ', callback_data='lang_am')
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

async def get_admin_reply_keyboard(db):
    stats = await db.get_stats()
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text=f"📊 Stats"),
                KeyboardButton(text=f"💳 Payments")
            ],
            [
                KeyboardButton(text=f"🎨 Manual Queue"),
                KeyboardButton(text="👥 Users")
            ],
            [
                KeyboardButton(text="✨ Prompts")
            ]
        ],
        resize_keyboard=True
    )






# keyboards/inline.py
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def get_style_upload_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="⬅️ Back", callback_data="style_upload:back"),
                InlineKeyboardButton(text="➡️ Next", callback_data="style_upload:next"),
                InlineKeyboardButton(text="❌ Cancel", callback_data="style_upload:cancel"),
            ]
        ]
    )

def get_style_confirm_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✅ Confirm & Save",
                    callback_data="style_upload:confirm"
                ),
                InlineKeyboardButton(
                    text="✏️ Edit",
                    callback_data="style_upload:edit"
                ),
            ],
            [
                InlineKeyboardButton(
                    text="❌ Cancel",
                    callback_data="style_upload:cancel"
                )
            ]
        ]
    )

def get_style_field_keyboard(field_name: str = "") -> InlineKeyboardMarkup:
    """
    Keyboard to jump to a specific field during edit.
    callback_data: style_edit:<field_name>
    """
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✏️ Edit Name (EN)", callback_data="style_edit:name_en"),
                InlineKeyboardButton(text="🇪🇹 Edit Name (AM)", callback_data="style_edit:name_am"),
            ],
            [
                InlineKeyboardButton(text="📖 Edit Desc (EN)", callback_data="style_edit:desc_en"),
                InlineKeyboardButton(text="📖 Edit Desc (AM)", callback_data="style_edit:desc_am"),
            ],
            [
                InlineKeyboardButton(text="🧠 Edit Prompt", callback_data="style_edit:prompt"),
                InlineKeyboardButton(text="💎 Edit Cost", callback_data="style_edit:cost"),
            ],
            [
                InlineKeyboardButton(text="🔁 Edit Active", callback_data="style_edit:is_active"),
                InlineKeyboardButton(text="🔢 Edit Order", callback_data="style_edit:display_order"),
            ],
            [
                InlineKeyboardButton(text="📸 Edit Preview Image", callback_data="style_edit:preview_image"),
            ],
            [
                InlineKeyboardButton(text="🗑️ Delete", callback_data="edit_style:delete"),
                InlineKeyboardButton(text="⬅️ Back to Review", callback_data="style_edit:back"),
            ]
        ]
    )




#For payment verification
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def get_payment_review_keyboard(payment_id: str) -> InlineKeyboardMarkup:
    """
    Inline keyboard for reviewing a payment.
    Provides Approve, Reject, and Back buttons.
    """
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="✅ Approve",
                callback_data=f"payment:approve:{payment_id}"
            ),
            InlineKeyboardButton(
                text="❌ Reject",
                callback_data=f"payment:reject:{payment_id}"
            ),
        ],
        [
            InlineKeyboardButton(
                text="⬅️ Back",
                callback_data="admin:payments"
            )
        ]
    ])






# --- Additional imports (add near top of file) ---
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

# --- Reply keyboards for Prompts menu ---
def get_prompts_reply_keyboard():
    """
    Reply keyboard shown when admin opens Prompts.
    Contains: Add New Style, View Styles, Back
    """
    kb = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="➕ Add New Style"), KeyboardButton(text="📚 View Styles")],
            [KeyboardButton(text="⬅️ Back")]
        ],
        resize_keyboard=True,
        one_time_keyboard=False
    )
    return kb

# --- Inline keyboard for paginated style list ---
def build_styles_list_keyboard(styles: list, page: int = 0, page_size: int = 5) -> InlineKeyboardMarkup:
    """
    Build inline keyboard listing styles with View buttons and Prev/Next pagination.
    Each style row: [View #N: <name>]
    """
    start = page * page_size
    end = start + page_size
    rows = []
    for idx, s in enumerate(styles[start:end], start=1 + start):
        label = f"🔎 View #{idx} {s.get('name_en') or 'Untitled'}"
        rows.append([InlineKeyboardButton(text=label, callback_data=f"view_style:{s['id']}")])

    # pagination controls
    nav_row = []
    if page > 0:
        nav_row.append(InlineKeyboardButton(text="⬅️ Prev", callback_data=f"list_style:page:{page-1}"))
    if end < len(styles):
        nav_row.append(InlineKeyboardButton(text="➡️ Next", callback_data=f"list_style:page:{page+1}"))
    if nav_row:
        rows.append(nav_row)

    # back to prompts
    rows.append([InlineKeyboardButton(text="⬅️ Back to Prompts", callback_data="list_style:back")])
    return InlineKeyboardMarkup(inline_keyboard=rows)
