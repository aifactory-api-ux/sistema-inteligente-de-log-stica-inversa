# backend/src/services/qr_generator.py

import io
import base64
import json
import logging
from datetime import datetime, timedelta
from typing import Optional
from uuid import uuid4

import qrcode
from qrcode.constants import ERROR_CORRECT_L

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from config import settings

logger = logging.getLogger(__name__)


class QRTokenData:
    def __init__(
        self,
        return_id: str,
        trace_id: str,
        channel: str,
        expires_at: Optional[datetime] = None
    ):
        self.return_id = return_id
        self.trace_id = trace_id
        self.channel = channel
        self.token = f"RET:{return_id}:{trace_id}"
        self.expires_at = expires_at or (datetime.utcnow() + timedelta(hours=24))

    def to_json(self) -> str:
        return json.dumps({
            "return_id": self.return_id,
            "trace_id": self.trace_id,
            "channel": self.channel,
            "token": self.token,
            "expires_at": self.expires_at.isoformat(),
        })

    @classmethod
    def from_token(cls, token: str) -> Optional["QRTokenData"]:
        try:
            parts = token.split(":")
            if len(parts) != 3 or parts[0] != "RET":
                return None
            return cls(
                return_id=parts[1],
                trace_id=parts[2],
                channel="B2C",
            )
        except Exception:
            return None


class QRGenerator:
    def __init__(self):
        self.box_size = 10
        self.border = 4
        self.error_correction = ERROR_CORRECT_L

    def generate_token(self, return_id: str, trace_id: str, channel: str) -> str:
        token_data = QRTokenData(
            return_id=return_id,
            trace_id=trace_id,
            channel=channel,
        )
        return token_data.to_json()

    def generate_qr_code_base64(self, data: str) -> str:
        qr = qrcode.QRCode(
            version=1,
            error_correction=self.error_correction,
            box_size=self.box_size,
            border=self.border,
        )
        qr.add_data(data)
        qr.make(fit=True)

        img = qr.make_image(fill_color="black", back_color="white")
        buffer = io.BytesIO()
        img.save(buffer, format="PNG")
        qr_base64 = base64.b64encode(buffer.getvalue()).decode()
        return qr_base64

    def generate_return_qr(
        self,
        return_id: str,
        trace_id: str,
        channel: str = "B2C"
    ) -> dict:
        token = self.generate_token(return_id, trace_id, channel)
        qr_base64 = self.generate_qr_code_base64(token)

        token_data = QRTokenData.from_token(token)

        return {
            "qr_code": qr_base64,
            "token": token,
            "return_id": return_id,
            "trace_id": trace_id,
            "channel": channel,
            "expires_at": token_data.expires_at.isoformat() if token_data else None,
        }

    def validate_token(self, token: str) -> bool:
        token_data = QRTokenData.from_token(token)
        if not token_data:
            return False

        if datetime.utcnow() > token_data.expires_at:
            logger.warning(f"QR token expired: {token}")
            return False

        return True

    def generate_batch_qr(
        self,
        batch_id: str,
        items: list[dict],
        customer_id: str,
        channel: str = "B2B"
    ) -> dict:
        trace_id = str(uuid4())
        token_data = QRTokenData(
            return_id=f"BATCH:{batch_id}",
            trace_id=trace_id,
            channel=channel,
        )

        batch_token = json.dumps({
            "type": "BATCH",
            "batch_id": batch_id,
            "trace_id": trace_id,
            "customer_id": customer_id,
            "item_count": len(items),
            "token": token_data.to_json(),
            "expires_at": token_data.expires_at.isoformat(),
        })

        qr_base64 = self.generate_qr_code_base64(batch_token)

        return {
            "qr_code": qr_base64,
            "batch_id": batch_id,
            "trace_id": trace_id,
            "token": batch_token,
            "item_count": len(items),
            "expires_at": token_data.expires_at.isoformat(),
        }


qr_generator = QRGenerator()
