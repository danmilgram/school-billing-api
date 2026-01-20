from pydantic import BaseModel, ConfigDict
from decimal import Decimal
from typing import List
from datetime import date
from app.schemas.invoice import InvoiceRead


class StudentAccountStatement(BaseModel):
    student_id: int
    student_name: str
    school_id: int
    school_name: str
    total_invoiced: Decimal
    total_paid: Decimal
    total_pending: Decimal
    invoices: List[InvoiceRead]


class PeriodSchema(BaseModel):
    start_date: date
    end_date: date


class SummarySchema(BaseModel):
    total_invoiced: Decimal
    total_paid: Decimal
    total_pending: Decimal


class InvoiceStatementItem(BaseModel):
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
