import pytest
from datetime import date
from decimal import Decimal
from app.services.student_statement_service import StudentStatementService
from app.services.school_statement_service import SchoolStatementService
from app.services.school_service import SchoolService
from app.services.student_service import StudentService
from app.services.invoice_service import InvoiceService
from app.services.payment_service import PaymentService
from app.schemas.school import SchoolCreate
from app.schemas.student import StudentCreate
from app.schemas.invoice import InvoiceCreate, InvoiceItemCreate
from app.schemas.payment import PaymentCreate


def create_test_data(db):
    """Helper to create test data"""
    school = SchoolService.create(
        SchoolCreate(name="Test School", contact_email="test@school.com", contact_phone="+1234567890"),
        db
    )
    student = StudentService.create(
        StudentCreate(
            school_id=school.id,
            first_name="John",
            last_name="Doe",
            email="john@student.com",
            enrollment_date=date(2024, 1, 15)
        ),
        db
    )
    return school, student


def test_student_statement_basic(db):
    """Test basic student account statement"""
    school, student = create_test_data(db)

    # Create an invoice
    invoice = InvoiceService.create(
        InvoiceCreate(
            student_id=student.id,
            issue_date=date(2024, 1, 20),
            due_date=date(2024, 2, 20),
            items=[InvoiceItemCreate(description="Tuition", quantity=1, unit_price=Decimal("1000.00"))]
        ),
        db
    )

    # Create a payment
    PaymentService.create(
        invoice,
        PaymentCreate(payment_date=date(2024, 1, 25), amount=Decimal("600.00"), payment_method="cash"),
        db
    )

    statement = StudentStatementService.get_statement(
        student.id, db,
        start_date=date(2024, 1, 1),
        end_date=date(2024, 12, 31),
        include_invoices=True
    )

    assert statement is not None
    assert statement["student_id"] == student.id
    assert statement["student_name"] == "John Doe"
    assert statement["school_id"] == school.id
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


def test_student_statement_multiple_invoices(db):
    """Test student statement with multiple invoices"""
    school, student = create_test_data(db)

    # Create two invoices
    invoice1 = InvoiceService.create(
        InvoiceCreate(
            student_id=student.id,
            issue_date=date(2024, 1, 20),
            due_date=date(2024, 2, 20),
            items=[InvoiceItemCreate(description="Tuition", quantity=1, unit_price=Decimal("1000.00"))]
        ),
        db
    )
    invoice2 = InvoiceService.create(
        InvoiceCreate(
            student_id=student.id,
            issue_date=date(2024, 2, 1),
            due_date=date(2024, 3, 1),
            items=[InvoiceItemCreate(description="Books", quantity=1, unit_price=Decimal("500.00"))]
        ),
        db
    )

    # Make payments
    PaymentService.create(invoice1, PaymentCreate(payment_date=date(2024, 1, 25), amount=Decimal("1000.00"), payment_method="cash"), db)
    PaymentService.create(invoice2, PaymentCreate(payment_date=date(2024, 2, 5), amount=Decimal("200.00"), payment_method="cash"), db)

    statement = StudentStatementService.get_statement(
        student.id, db,
        start_date=date(2024, 1, 1),
        end_date=date(2024, 12, 31),
        include_invoices=True
    )

    assert statement["summary"]["total_invoiced"] == Decimal("1500.00")
    assert statement["summary"]["total_paid"] == Decimal("1200.00")
    assert statement["summary"]["total_pending"] == Decimal("300.00")
    assert len(statement["invoices"]) == 2


def test_student_statement_excludes_cancelled_invoices(db):
    """Test that cancelled invoices are excluded from student statement"""
    school, student = create_test_data(db)

    # Create two invoices
    invoice1 = InvoiceService.create(
        InvoiceCreate(
            student_id=student.id,
            issue_date=date(2024, 1, 20),
            due_date=date(2024, 2, 20),
            items=[InvoiceItemCreate(description="Invoice 1", quantity=1, unit_price=Decimal("1000.00"))]
        ),
        db
    )
    invoice2 = InvoiceService.create(
        InvoiceCreate(
            student_id=student.id,
            issue_date=date(2024, 2, 1),
            due_date=date(2024, 3, 1),
            items=[InvoiceItemCreate(description="Invoice 2", quantity=1, unit_price=Decimal("500.00"))]
        ),
        db
    )

    # Cancel the first invoice
    InvoiceService.cancel(invoice1, db)

    statement = StudentStatementService.get_statement(
        student.id, db,
        start_date=date(2024, 1, 1),
        end_date=date(2024, 12, 31),
        include_invoices=True
    )

    # Should only include invoice2
    assert statement["summary"]["total_invoiced"] == Decimal("500.00")
    assert statement["summary"]["total_paid"] == Decimal("0.00")
    assert statement["summary"]["total_pending"] == Decimal("500.00")
    assert len(statement["invoices"]) == 1


def test_student_statement_nonexistent_student(db):
    """Test student statement for non-existent student"""
    statement = StudentStatementService.get_statement(
        999, db,
        start_date=date(2024, 1, 1),
        end_date=date(2024, 12, 31)
    )

    assert statement is None


def test_school_statement_basic(db):
    """Test basic school account statement"""
    school, student = create_test_data(db)

    # Create an invoice with payment
    invoice = InvoiceService.create(
        InvoiceCreate(
            student_id=student.id,
            issue_date=date(2024, 1, 20),
            due_date=date(2024, 2, 20),
            items=[InvoiceItemCreate(description="Tuition", quantity=1, unit_price=Decimal("1000.00"))]
        ),
        db
    )
    PaymentService.create(invoice, PaymentCreate(payment_date=date(2024, 1, 25), amount=Decimal("400.00"), payment_method="cash"), db)

    statement = SchoolStatementService.get_statement(
        school.id, db,
        start_date=date(2024, 1, 1),
        end_date=date(2024, 12, 31),
        include_invoices=True
    )

    assert statement is not None
    assert statement["school_id"] == school.id
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


def test_school_statement_multiple_students(db):
    """Test school statement aggregates across multiple students"""
    school, student1 = create_test_data(db)

    # Create another student
    student2 = StudentService.create(
        StudentCreate(
            school_id=school.id,
            first_name="Jane",
            last_name="Smith",
            email="jane@student.com",
            enrollment_date=date(2024, 1, 15)
        ),
        db
    )

    # Create invoices for both students
    invoice1 = InvoiceService.create(
        InvoiceCreate(
            student_id=student1.id,
            issue_date=date(2024, 1, 20),
            due_date=date(2024, 2, 20),
            items=[InvoiceItemCreate(description="Tuition", quantity=1, unit_price=Decimal("1000.00"))]
        ),
        db
    )
    invoice2 = InvoiceService.create(
        InvoiceCreate(
            student_id=student2.id,
            issue_date=date(2024, 1, 20),
            due_date=date(2024, 2, 20),
            items=[InvoiceItemCreate(description="Tuition", quantity=1, unit_price=Decimal("1200.00"))]
        ),
        db
    )

    # Make payments
    PaymentService.create(invoice1, PaymentCreate(payment_date=date(2024, 1, 25), amount=Decimal("500.00"), payment_method="cash"), db)
    PaymentService.create(invoice2, PaymentCreate(payment_date=date(2024, 1, 25), amount=Decimal("1200.00"), payment_method="cash"), db)

    statement = SchoolStatementService.get_statement(
        school.id, db,
        start_date=date(2024, 1, 1),
        end_date=date(2024, 12, 31),
        include_invoices=True
    )

    assert statement["student_count"] == 2
    assert statement["summary"]["total_invoiced"] == Decimal("2200.00")
    assert statement["summary"]["total_paid"] == Decimal("1700.00")
    assert statement["summary"]["total_pending"] == Decimal("500.00")


def test_school_statement_excludes_cancelled_invoices(db):
    """Test that cancelled invoices are excluded from school statement"""
    school, student = create_test_data(db)

    # Create two invoices
    invoice1 = InvoiceService.create(
        InvoiceCreate(
            student_id=student.id,
            issue_date=date(2024, 1, 20),
            due_date=date(2024, 2, 20),
            items=[InvoiceItemCreate(description="Invoice 1", quantity=1, unit_price=Decimal("5000.00"))]
        ),
        db
    )
    invoice2 = InvoiceService.create(
        InvoiceCreate(
            student_id=student.id,
            issue_date=date(2024, 2, 1),
            due_date=date(2024, 3, 1),
            items=[InvoiceItemCreate(description="Invoice 2", quantity=1, unit_price=Decimal("1000.00"))]
        ),
        db
    )

    # Cancel the first invoice
    InvoiceService.cancel(invoice1, db)

    statement = SchoolStatementService.get_statement(
        school.id, db,
        start_date=date(2024, 1, 1),
        end_date=date(2024, 12, 31),
        include_invoices=True
    )

    # Should only include invoice2
    assert statement["summary"]["total_invoiced"] == Decimal("1000.00")
    assert len(statement["invoices"]) == 1


def test_school_statement_nonexistent_school(db):
    """Test school statement for non-existent school"""
    statement = SchoolStatementService.get_statement(
        999, db,
        start_date=date(2024, 1, 1),
        end_date=date(2024, 12, 31)
    )

    assert statement is None
