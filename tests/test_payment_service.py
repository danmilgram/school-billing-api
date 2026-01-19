import pytest
from datetime import date
from decimal import Decimal
from app.services.payment_service import PaymentService
from app.services.invoice_service import InvoiceService
from app.services.school_service import SchoolService
from app.services.student_service import StudentService
from app.schemas.payment import PaymentCreate
from app.schemas.invoice import InvoiceCreate, InvoiceItemCreate
from app.schemas.school import SchoolCreate
from app.schemas.student import StudentCreate
from app.models.invoice import InvoiceStatus


def create_test_invoice(db, total_amount=Decimal("1000.00")):
    """Helper to create a test invoice"""
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
    invoice = InvoiceService.create(
        InvoiceCreate(
            student_id=student.id,
            issue_date=date(2024, 1, 20),
            due_date=date(2024, 2, 20),
            items=[InvoiceItemCreate(description="Item", quantity=1, unit_price=total_amount)]
        ),
        db
    )
    return invoice


def test_create_payment(db):
    """Test creating a payment"""
    invoice = create_test_invoice(db, Decimal("1000.00"))

    payment_data = PaymentCreate(
        payment_date=date(2024, 1, 25),
        amount=Decimal("500.00"),
        payment_method="cash"
    )

    payment = PaymentService.create(invoice, payment_data, db)

    assert payment.id is not None
    assert payment.invoice_id == invoice.id
    assert payment.amount == Decimal("500.00")
    assert payment.payment_method == "cash"
    assert payment.deleted_at is None


def test_full_payment_updates_invoice_status(db):
    """Test that a full payment updates invoice status to PAID"""
    invoice = create_test_invoice(db, Decimal("1000.00"))

    payment_data = PaymentCreate(
        payment_date=date(2024, 1, 25),
        amount=Decimal("1000.00"),
        payment_method="cash"
    )

    PaymentService.create(invoice, payment_data, db)

    # Refresh invoice and check status
    db.refresh(invoice)
    assert invoice.status == InvoiceStatus.PAID


def test_partial_payment_keeps_pending_status(db):
    """Test that a partial payment keeps invoice status as PENDING"""
    invoice = create_test_invoice(db, Decimal("1000.00"))

    payment_data = PaymentCreate(
        payment_date=date(2024, 1, 25),
        amount=Decimal("500.00"),
        payment_method="cash"
    )

    PaymentService.create(invoice, payment_data, db)

    # Refresh invoice and check status is still PENDING
    db.refresh(invoice)
    assert invoice.status == InvoiceStatus.PENDING


def test_multiple_payments_to_full_amount_updates_status(db):
    """Test that multiple payments totaling the full amount update status to PAID"""
    invoice = create_test_invoice(db, Decimal("1000.00"))

    # First payment
    PaymentService.create(
        invoice,
        PaymentCreate(payment_date=date(2024, 1, 25), amount=Decimal("600.00"), payment_method="cash"),
        db
    )

    db.refresh(invoice)
    assert invoice.status == InvoiceStatus.PENDING

    # Second payment completing the total
    PaymentService.create(
        invoice,
        PaymentCreate(payment_date=date(2024, 1, 26), amount=Decimal("400.00"), payment_method="cash"),
        db
    )

    db.refresh(invoice)
    assert invoice.status == InvoiceStatus.PAID


def test_cannot_overpay_invoice(db):
    """Test that you cannot overpay an invoice"""
    invoice = create_test_invoice(db, Decimal("1000.00"))

    # Try to pay more than the invoice total
    payment_data = PaymentCreate(
        payment_date=date(2024, 1, 25),
        amount=Decimal("1500.00"),
        payment_method="cash"
    )

    with pytest.raises(ValueError, match="Payment would exceed invoice total"):
        PaymentService.create(invoice, payment_data, db)


def test_cannot_overpay_with_multiple_payments(db):
    """Test that you cannot overpay with multiple payments"""
    invoice = create_test_invoice(db, Decimal("1000.00"))

    # First payment
    PaymentService.create(
        invoice,
        PaymentCreate(payment_date=date(2024, 1, 25), amount=Decimal("800.00"), payment_method="cash"),
        db
    )

    # Try to pay more than the remaining amount
    payment_data = PaymentCreate(
        payment_date=date(2024, 1, 26),
        amount=Decimal("300.00"),  # Total would be 1100
        payment_method="cash"
    )

    with pytest.raises(ValueError, match="Payment would exceed invoice total"):
        PaymentService.create(invoice, payment_data, db)


def test_error_message_shows_remaining_amount(db):
    """Test that error message shows the remaining amount"""
    invoice = create_test_invoice(db, Decimal("1000.00"))

    # Make a partial payment
    PaymentService.create(
        invoice,
        PaymentCreate(payment_date=date(2024, 1, 25), amount=Decimal("700.00"), payment_method="cash"),
        db
    )

    # Try to overpay
    payment_data = PaymentCreate(
        payment_date=date(2024, 1, 26),
        amount=Decimal("500.00"),
        payment_method="cash"
    )

    with pytest.raises(ValueError, match="Remaining amount: 300"):
        PaymentService.create(invoice, payment_data, db)


def test_get_payments_by_invoice(db):
    """Test getting all payments for an invoice"""
    invoice = create_test_invoice(db, Decimal("1000.00"))

    # Create multiple payments
    PaymentService.create(
        invoice,
        PaymentCreate(payment_date=date(2024, 1, 25), amount=Decimal("300.00"), payment_method="cash"),
        db
    )
    PaymentService.create(
        invoice,
        PaymentCreate(payment_date=date(2024, 1, 26), amount=Decimal("400.00"), payment_method="card"),
        db
    )

    payments = PaymentService.get_by_invoice(invoice.id, db)

    assert len(payments) == 2
    assert payments[0].amount == Decimal("300.00")
    assert payments[1].amount == Decimal("400.00")


def test_get_payment_by_id(db):
    """Test getting a payment by ID"""
    invoice = create_test_invoice(db, Decimal("1000.00"))

    payment = PaymentService.create(
        invoice,
        PaymentCreate(payment_date=date(2024, 1, 25), amount=Decimal("500.00"), payment_method="cash"),
        db
    )

    retrieved_payment = PaymentService.get_by_id(payment.id, invoice.id, db)

    assert retrieved_payment is not None
    assert retrieved_payment.id == payment.id
    assert retrieved_payment.invoice_id == invoice.id
