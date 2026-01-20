import pytest
from datetime import date
from decimal import Decimal
from app.services.student_statement_service import StudentStatementService
from app.services.invoice_service import InvoiceService
from app.schemas.invoice import InvoiceItemCreate


def test_student_statement_basic(db, test_school, test_student, invoice_factory, payment_factory):
    """Test basic student account statement"""
    # Create an invoice and payment
    invoice = invoice_factory(test_student.id)
    payment_factory(invoice, amount=Decimal("600.00"))

    service = StudentStatementService(
        student_id=test_student.id,
        db=db,
        start_date=date(2024, 1, 1),
        end_date=date(2024, 12, 31),
        include_invoices=True
    )
    statement = service.get_statement()

    assert statement is not None
    assert statement["student_id"] == test_student.id
    assert statement["student_name"] == "John Doe"
    assert statement["school_id"] == test_school.id
    assert statement["school_name"] == "Test School"
    assert statement["period"]["start_date"] == date(2024, 1, 1)
    assert statement["period"]["end_date"] == date(2024, 12, 31)
    assert statement["summary"]["total_invoiced"] == Decimal("1000.00")
    assert statement["summary"]["total_paid"] == Decimal("600.00")
    assert statement["summary"]["total_pending"] == Decimal("400.00")
    assert len(statement["invoices"]) == 1
    assert statement["invoices"][0]["invoice_id"] == invoice.id
    assert statement["invoices"][0]["paid_amount"] == Decimal("600.00")
    assert statement["invoices"][0]["pending_amount"] == Decimal("400.00")


def test_student_statement_multiple_invoices(db, test_student, invoice_factory, payment_factory):
    """Test student statement with multiple invoices"""
    # Create two invoices with different amounts
    invoice1 = invoice_factory(test_student.id)
    invoice2 = invoice_factory(
        test_student.id,
        issue_date=date(2024, 2, 1),
        due_date=date(2024, 3, 1),
        items=[InvoiceItemCreate(description="Books", quantity=1, unit_price=Decimal("500.00"))]
    )

    # Make payments
    payment_factory(invoice1, amount=Decimal("1000.00"))
    payment_factory(invoice2, amount=Decimal("200.00"), payment_date=date(2024, 2, 5))

    service = StudentStatementService(
        student_id=test_student.id,
        db=db,
        start_date=date(2024, 1, 1),
        end_date=date(2024, 12, 31),
        include_invoices=True
    )
    statement = service.get_statement()

    assert statement["summary"]["total_invoiced"] == Decimal("1500.00")
    assert statement["summary"]["total_paid"] == Decimal("1200.00")
    assert statement["summary"]["total_pending"] == Decimal("300.00")
    assert len(statement["invoices"]) == 2


def test_student_statement_excludes_cancelled_invoices(db, test_student, invoice_factory):
    """Test that cancelled invoices are excluded from student statement"""
    # Create two invoices
    invoice1 = invoice_factory(test_student.id)
    invoice2 = invoice_factory(
        test_student.id,
        issue_date=date(2024, 2, 1),
        due_date=date(2024, 3, 1),
        items=[InvoiceItemCreate(description="Invoice 2", quantity=1, unit_price=Decimal("500.00"))]
    )

    # Cancel the first invoice
    InvoiceService.cancel(invoice1, db)

    service = StudentStatementService(
        student_id=test_student.id,
        db=db,
        start_date=date(2024, 1, 1),
        end_date=date(2024, 12, 31),
        include_invoices=True
    )
    statement = service.get_statement()

    # Should only include invoice2
    assert statement["summary"]["total_invoiced"] == Decimal("500.00")
    assert statement["summary"]["total_paid"] == Decimal("0.00")
    assert statement["summary"]["total_pending"] == Decimal("500.00")
    assert len(statement["invoices"]) == 1


def test_student_statement_nonexistent_student(db):
    """Test student statement for non-existent student"""
    service = StudentStatementService(
        student_id=999,
        db=db,
        start_date=date(2024, 1, 1),
        end_date=date(2024, 12, 31)
    )
    statement = service.get_statement()

    assert statement is None
