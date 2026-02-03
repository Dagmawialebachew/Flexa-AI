from typing import Dict, Optional
from utils.helpers import get_text
from config.settings import settings

class PaymentService:
    @staticmethod
    def get_package_info(package_type: str) -> Optional[Dict]:
        return settings.CREDIT_PACKAGES.get(package_type)

    @staticmethod
    def validate_package(package_type: str) -> tuple[bool, Optional[str]]:
        if package_type not in settings.CREDIT_PACKAGES:
            return False, "unknown_package"
        return True, None


    @staticmethod
    def get_payment_instructions(package_type: str, lang: str = "en") -> str:
        pkg = PaymentService.get_package_info(package_type)
        if not pkg:
            return get_text("error_general", lang)

        # Centralize account info in TEXTS for easy updates
        telebirr_account = get_text("payment_account", lang)

        # Build only the dynamic details (no header/footer)
        details = (
            f"📦 Package: {pkg['name_en'] if lang == 'en' else pkg['name_am']}\n"
            f"💰 Amount: {pkg['price']} Birr\n"
            f"💎 Credits: {pkg['credits']}\n\n"
            f"➡️ {telebirr_account}"
        )

        # Template adds header + footer
        return get_text("payment_instructions", lang, instructions=details)
