import pytest
from datetime import date
from decimal import Decimal
from app.services.school_statement_service import SchoolStatementService
from app.services.invoice_service import InvoiceService
from app.schemas.invoice import InvoiceItemCreate


def test_school_statement_basic(db, test_school, test_student, invoice_factory, payment_factory):
    """Test basic school account statement"""
    # Create an invoice with payment
    invoice = invoice_factory(test_student.id)
    payment_factory(invoice, amount=Decimal("400.00"))

    service = SchoolStatementService(
        school_id=test_school.id,
        db=db,
        start_date=date(2024, 1, 1),
        end_date=date(2024, 12, 31),
        include_invoices=True
    )
    statement = service.get_statement()

    assert statement is not None
    assert statement["school_id"] == test_school.id
    assert statement["school_name"] == "Test School"
    assert statement["period"]["start_date"] == date(2024, 1, 1)
    assert statement["period"]["end_date"] == date(2024, 12, 31)
    assert statement["student_count"] == 1
    assert statement["summary"]["total_invoiced"] == Decimal("1000.00")
    assert statement["summary"]["total_paid"] == Decimal("400.00")
    assert statement["summary"]["total_pending"] == Decimal("600.00")
    assert len(statement["invoices"]) == 1
    assert statement["invoices"][0]["invoice_id"] == invoice.id
    assert statement["invoices"][0]["paid_amount"] == Decimal("400.00")
    assert statement["invoices"][0]["pending_amount"] == Decimal("600.00")


def test_school_statement_multiple_students(db, test_school, test_student, student_factory, invoice_factory, payment_factory):
    """Test school statement aggregates across multiple students"""
    # Create another student
    student2 = student_factory(
        test_school.id,
        first_name="Jane",
        last_name="Smith",
        email="jane@student.com"
    )

    # Create invoices for both students
    invoice1 = invoice_factory(test_student.id)
    invoice2 = invoice_factory(
        student2.id,
        items=[InvoiceItemCreate(description="Tuition", quantity=1, unit_price=Decimal("1200.00"))]
    )

    # Make payments
    payment_factory(invoice1, amount=Decimal("500.00"))
    payment_factory(invoice2, amount=Decimal("1200.00"))

    service = SchoolStatementService(
        school_id=test_school.id,
        db=db,
        start_date=date(2024, 1, 1),
        end_date=date(2024, 12, 31),
        include_invoices=True
    )
    statement = service.get_statement()

    assert statement["student_count"] == 2
    assert statement["summary"]["total_invoiced"] == Decimal("2200.00")
    assert statement["summary"]["total_paid"] == Decimal("1700.00")
    assert statement["summary"]["total_pending"] == Decimal("500.00")


def test_school_statement_excludes_cancelled_invoices(db, test_school, test_student, invoice_factory):
    """Test that cancelled invoices are excluded from school statement"""
    # Create two invoices
    invoice1 = invoice_factory(
        test_student.id,
        items=[InvoiceItemCreate(description="Invoice 1", quantity=1, unit_price=Decimal("5000.00"))]
    )
    invoice2 = invoice_factory(
        test_student.id,
        issue_date=date(2024, 2, 1),
        due_date=date(2024, 3, 1),
        items=[InvoiceItemCreate(description="Invoice 2", quantity=1, unit_price=Decimal("1000.00"))]
    )

    # Cancel the first invoice
    InvoiceService.cancel(invoice1, db)

    service = SchoolStatementService(
        school_id=test_school.id,
        db=db,
        start_date=date(2024, 1, 1),
        end_date=date(2024, 12, 31),
        include_invoices=True
    )
    statement = service.get_statement()

    # Should only include invoice2
    assert statement["summary"]["total_invoiced"] == Decimal("1000.00")
    assert len(statement["invoices"]) == 1


def test_school_statement_nonexistent_school(db):
    """Test school statement for non-existent school"""
    service = SchoolStatementService(
        school_id=999,
        db=db,
        start_date=date(2024, 1, 1),
        end_date=date(2024, 12, 31)
    )
    statement = service.get_statement()

    assert statement is None
