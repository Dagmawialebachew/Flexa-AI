import os
from typing import List
from dotenv import load_dotenv

load_dotenv()


class Settings:
    BOT_TOKEN: str = os.getenv('BOT_TOKEN', '')
    ADMIN_IDS: List[int] = [int(id.strip()) for id in os.getenv('ADMIN_IDS', '').split(',') if id.strip()]

    DATABASE_URL: str = os.getenv('DATABASE_URL', '')
    SUPABASE_URL: str = os.getenv('SUPABASE_URL', '')
    SUPABASE_KEY: str = os.getenv('SUPABASE_KEY', '')

    GEMINI_API_KEY: str = os.getenv('GEMINI_API_KEY', '')
    BANANA_API_KEY: str = os.getenv('BANANA_API_KEY', '')
    HF_API_KEY: str = os.getenv('HF_API_KEY', '')
    REPLICATE_API_TOKEN: str = os.getenv('REPLICATE_API_TOKEN', '')
    ADMIN_MANUAL_GROUP_ID: int = int(os.getenv('ADMIN_MANUAL_GROUP_ID', '-5084517269'))
    ADMIN_DAILY_GROUP_ID: int = int(os.getenv('ADMIN_DAILY_GROUP_ID', '-5164478198'))
    ADMIN_ERROR_GROUP_ID: int = int(os.getenv('ADMIN_ERROR_GROUP_ID', '-5271996630'))
    CHANNEL_USERNAME: str = os.getenv('CHANNEL_USERNAME', '@FlexaAI')

    BONUS_CREDITS: int = int(os.getenv('BONUS_CREDITS', '3'))
    DEFAULT_LANGUAGE: str = os.getenv('DEFAULT_LANGUAGE', 'en')
    LOG_LEVEL: str = os.getenv('LOG_LEVEL', 'INFO')

    CREDIT_PACKAGES = {
        '5_images': {'credits': 5, 'price': 100, 'name_en': '5 Images', 'name_am': '5 ፎቶዎች'},
        '10_images': {'credits': 10, 'price': 150, 'name_en': '10 Images', 'name_am': '10 ፎቶዎች'},
        '25_images': {'credits': 25, 'price': 300, 'name_en': '25 Images', 'name_am': '25 ፎቶዎች'},
    }

    def is_admin(self, user_id: int) -> bool:
        return user_id in self.ADMIN_IDS


settings = Settings()
