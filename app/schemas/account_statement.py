from pydantic import BaseModel
from decimal import Decimal
from typing import List
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


class SchoolAccountStatement(BaseModel):
    school_id: int
    school_name: str
    student_count: int
    total_invoiced: Decimal
    total_paid: Decimal
    total_pending: Decimal
    invoices: List[InvoiceRead]
