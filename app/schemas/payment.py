from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, field_validator

from app.models.payment import PaymentMethod


class PaymentBase(BaseModel):
    payment_date: date
    amount: Decimal
    payment_method: PaymentMethod


class PaymentCreate(PaymentBase):
    @field_validator("amount")
    @classmethod
    def amount_must_be_positive(cls, v):
        if v <= 0:
            raise ValueError("Payment amount must be greater than 0")
        return v


class PaymentRead(PaymentBase):
    id: int
    invoice_id: int
    created_at: datetime
    deleted_at: Optional[datetime] = None

    class Config:
        from_attributes = True
