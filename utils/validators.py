from aiogram.types import PhotoSize
from typing import List


def is_valid_photo(photos: List[PhotoSize]) -> bool:
    if not photos:
        return False
    largest = max(photos, key=lambda p: p.width * p.height)
    return largest.width >= 200 and largest.height >= 200


def is_valid_amount(amount: str) -> bool:
    try:
        value = int(amount)
        return value > 0
    except (ValueError, TypeError):
        return False
