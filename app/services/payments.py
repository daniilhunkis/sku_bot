from __future__ import annotations
import uuid
from dataclasses import dataclass
from typing import Optional
from yookassa import Configuration, Payment

@dataclass
class PaymentCreateResult:
    payment_id: str
    confirmation_url: str

class YooKassaClient:
    def __init__(self, shop_id: Optional[str], secret_key: Optional[str]):
        self.enabled = bool(shop_id and secret_key)
        if self.enabled:
            Configuration.account_id = shop_id
            Configuration.secret_key = secret_key

    def create_payment(self, amount_rub: int, description: str, return_url: str) -> PaymentCreateResult:
        if not self.enabled:
            raise RuntimeError("YooKassa is not configured")
        idempotence_key = str(uuid.uuid4())
        payment = Payment.create({
            "amount": {"value": f"{amount_rub:.2f}", "currency": "RUB"},
            "confirmation": {"type": "redirect", "return_url": return_url},
            "capture": True,
            "description": description,
        }, idempotence_key)
        return PaymentCreateResult(payment.id, payment.confirmation.confirmation_url)

    def get_status(self, payment_id: str) -> str:
        if not self.enabled:
            raise RuntimeError("YooKassa is not configured")
        p = Payment.find_one(payment_id)
        return p.status
