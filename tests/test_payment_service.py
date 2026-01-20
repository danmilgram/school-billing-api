import pytest
from datetime import date
from decimal import Decimal
from app.services.payment_service import PaymentService
from app.schemas.payment import PaymentCreate
from app.models.invoice import InvoiceStatus


def test_create_payment(db, test_invoice):
    """Test creating a payment"""

    payment_data = PaymentCreate(
        payment_date=date(2024, 1, 25),
        amount=Decimal("500.00"),
        payment_method="cash"
    )

    payment = PaymentService.create(test_invoice, payment_data, db)

    assert payment.id is not None
    assert payment.invoice_id == test_invoice.id
    assert payment.amount == Decimal("500.00")
    assert payment.payment_method == "cash"
    assert payment.deleted_at is None


def test_full_payment_updates_invoice_status(db, test_invoice):
    """Test that a full payment updates invoice status to PAID"""

    payment_data = PaymentCreate(
        payment_date=date(2024, 1, 25),
        amount=Decimal("1000.00"),
        payment_method="cash"
    )

    PaymentService.create(test_invoice, payment_data, db)

    # Refresh invoice and check status
    db.refresh(test_invoice)
    assert test_invoice.status == InvoiceStatus.PAID


def test_partial_payment_keeps_pending_status(db, test_invoice):
    """Test that a partial payment keeps invoice status as PENDING"""
    payment_data = PaymentCreate(
        payment_date=date(2024, 1, 25),
        amount=Decimal("500.00"),
        payment_method="cash"
    )

    PaymentService.create(test_invoice, payment_data, db)

    # Refresh invoice and check status is still PENDING
    db.refresh(test_invoice)
    assert test_invoice.status == InvoiceStatus.PENDING


def test_multiple_payments_to_full_amount_updates_status(db, test_invoice):
    """Test that multiple payments totaling the full amount update status to PAID"""
    # First payment
    PaymentService.create(
        test_invoice,
        PaymentCreate(payment_date=date(2024, 1, 25), amount=Decimal("600.00"), payment_method="cash"),
        db
    )

    db.refresh(test_invoice)
    assert test_invoice.status == InvoiceStatus.PENDING

    # Second payment completing the total
    PaymentService.create(
        test_invoice,
        PaymentCreate(payment_date=date(2024, 1, 26), amount=Decimal("400.00"), payment_method="cash"),
        db
    )

    db.refresh(test_invoice)
    assert test_invoice.status == InvoiceStatus.PAID


def test_cannot_overpay_invoice(db, test_invoice):
    """Test that you cannot overpay an invoice"""

    # Try to pay more than the invoice total
    payment_data = PaymentCreate(
        payment_date=date(2024, 1, 25),
        amount=Decimal("1500.00"),
        payment_method="cash"
    )

    with pytest.raises(ValueError, match="Payment would exceed invoice total"):
        PaymentService.create(test_invoice, payment_data, db)


def test_cannot_overpay_with_multiple_payments(db, test_invoice):
    """Test that you cannot overpay with multiple payments"""
    # First payment
    PaymentService.create(
        test_invoice,
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
        PaymentService.create(test_invoice, payment_data, db)


def test_error_message_shows_remaining_amount(db, test_invoice):
    """Test that error message shows the remaining amount"""
    # Make a partial payment
    PaymentService.create(
        test_invoice,
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
        PaymentService.create(test_invoice, payment_data, db)


def test_get_payments_by_invoice(db, test_invoice):
    """Test getting all payments for an invoice"""
    # Create multiple payments
    PaymentService.create(
        test_invoice,
        PaymentCreate(payment_date=date(2024, 1, 25), amount=Decimal("300.00"), payment_method="cash"),
        db
    )
    PaymentService.create(
        test_invoice,
        PaymentCreate(payment_date=date(2024, 1, 26), amount=Decimal("400.00"), payment_method="card"),
        db
    )

    payments = PaymentService.get_by_invoice(test_invoice.id, db)

    assert len(payments) == 2
    assert payments[0].amount == Decimal("300.00")
    assert payments[1].amount == Decimal("400.00")


def test_get_payment_by_id(db, test_payment):
    """Test getting a payment by ID"""
    retrieved_payment = PaymentService.get_by_id(test_payment.id, test_payment.invoice_id, db)

    assert retrieved_payment is not None
    assert retrieved_payment.id == test_payment.id
    assert retrieved_payment.invoice_id == test_payment.invoice_id
