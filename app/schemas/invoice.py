from datetime import date, datetime
from decimal import Decimal
from typing import List, Optional

from pydantic import BaseModel, field_validator

from app.models.invoice import InvoiceStatus


class InvoiceItemBase(BaseModel):
    description: str
    quantity: int
    unit_price: Decimal


class InvoiceItemCreate(InvoiceItemBase):
    @field_validator("quantity")
    @classmethod
    def quantity_must_be_positive(cls, v):
        if v <= 0:
            raise ValueError("Quantity must be greater than 0")
        return v

    @field_validator("unit_price")
    @classmethod
    def unit_price_must_be_non_negative(cls, v):
        if v < 0:
            raise ValueError("Unit price must be non-negative")
        return v


class InvoiceItemRead(InvoiceItemBase):
    id: int
    invoice_id: int
    total_amount: Decimal
    created_at: datetime
    deleted_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class InvoiceBase(BaseModel):
    student_id: int
    issue_date: date
    due_date: date
    status: InvoiceStatus = InvoiceStatus.PENDING


class InvoiceCreate(InvoiceBase):
    items: List[InvoiceItemCreate]

    @field_validator("items")
    @classmethod
    def items_must_not_be_empty(cls, v):
        if not v or len(v) == 0:
            raise ValueError("Invoice must have at least one item")
        return v


class InvoiceUpdate(BaseModel):
    issue_date: Optional[date] = None
    due_date: Optional[date] = None
    status: Optional[InvoiceStatus] = None


class InvoiceRead(InvoiceBase):
    id: int
    total_amount: Decimal
    created_at: datetime
    updated_at: datetime
    deleted_at: Optional[datetime] = None
    items: List[InvoiceItemRead] = []

    class Config:
        from_attributes = True
