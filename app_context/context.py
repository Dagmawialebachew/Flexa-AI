from dataclasses import dataclass
from database import Database
from services import AIImageService, OCRService, PaymentService


@dataclass
class AppContext:
    db: Database
    ai_service: AIImageService
    ocr_service: OCRService
    payment_service: PaymentService
