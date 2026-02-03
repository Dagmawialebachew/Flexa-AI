from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from utils.helpers import get_button


def get_main_menu_keyboard(lang: str = 'en') -> ReplyKeyboardMarkup:
    keyboard = [
        [KeyboardButton(text=get_button('generate_photo', lang))],
        [KeyboardButton(text=get_button('my_credits', lang)), KeyboardButton(text=get_button('buy_credits', lang))],
        [KeyboardButton(text=get_button('help', lang)), KeyboardButton(text=get_button('settings', lang))]
    ]
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)



def get_cancel_keyboard(lang: str = 'en') -> ReplyKeyboardMarkup:
    keyboard = [[KeyboardButton(text=get_button('cancel', lang))]]
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)
