from datetime import date
from decimal import Decimal
from typing import List

from pydantic import BaseModel, ConfigDict


class PeriodSchema(BaseModel):
    start_date: date
    end_date: date


class SummarySchema(BaseModel):
    total_invoiced: Decimal
    total_paid: Decimal
    total_pending: Decimal


class StatementInvoice(BaseModel):
    """Simplified invoice for statement views - no items, no nested details"""

    invoice_id: int
    issue_date: date
    due_date: date
    status: str
    total_amount: Decimal
    paid_amount: Decimal
    pending_amount: Decimal


class StudentAccountStatement(BaseModel):
    model_config = ConfigDict(exclude_none=True)

    student_id: int
    student_name: str
    school_id: int
    school_name: str
    period: PeriodSchema
    summary: SummarySchema
    invoices: List[StatementInvoice] | None = None


class InvoiceStatementItem(BaseModel):
    """Invoice item for school statements - includes student_id"""

    invoice_id: int
    student_id: int
    issue_date: date
    due_date: date
    status: str
    total_amount: Decimal
    paid_amount: Decimal
    pending_amount: Decimal


class SchoolAccountStatement(BaseModel):
    model_config = ConfigDict(exclude_none=True)

    school_id: int
    school_name: str
    period: PeriodSchema
    student_count: int
    summary: SummarySchema
    invoices: List[InvoiceStatementItem] | None = None
