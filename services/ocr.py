import pytesseract
from PIL import Image
import io
import re
from typing import Dict, Optional
from utils.logger import logger

class OCRService:
    @staticmethod
    async def extract_payment_info(image_bytes: bytes) -> Dict[str, Optional[str]]:
        try:
            logger.info("OCR extraction requested (pytesseract)")

            # Convert bytes to PIL image
            image = Image.open(io.BytesIO(image_bytes))

            # Run OCR
            raw_text = pytesseract.image_to_string(image)

            # Try to parse key fields
            amount_match = re.search(r'(\d+)\s*Birr', raw_text, re.IGNORECASE)
            txn_match = re.search(r'(?:TXN|Transaction)\s*[:\-]?\s*([A-Z0-9]+)', raw_text, re.IGNORECASE)
            sender_match = re.search(r'(?:From|Sender)\s*[:\-]?\s*(\w+)', raw_text, re.IGNORECASE)

            return {
                'amount': amount_match.group(1) if amount_match else None,
                'transaction_id': txn_match.group(1) if txn_match else None,
                'sender': sender_match.group(1) if sender_match else None,
                'raw_text': raw_text
            }

        except Exception as e:
            logger.error(f"OCR extraction failed: {e}")
            return {
                'amount': None,
                'transaction_id': None,
                'sender': None,
                'raw_text': None,
                'error': str(e)
            }
