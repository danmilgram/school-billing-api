from sqlalchemy.orm import Session
from datetime import datetime, timezone
from decimal import Decimal

from app.models.payment import Payment
from app.models.invoice import Invoice, InvoiceStatus
from app.schemas.payment import PaymentCreate


class PaymentService:

    @staticmethod
    def create(invoice: Invoice, payment_in: PaymentCreate, db: Session):
        """Create a payment for an invoice (cannot overpay)"""
        # Calculate total paid so far
        existing_payments = db.query(Payment).filter(
            Payment.invoice_id == invoice.id,
            Payment.deleted_at.is_(None)
        ).all()

        total_paid = sum(p.amount for p in existing_payments)
        new_total_paid = total_paid + payment_in.amount

        # Check for overpayment
        if new_total_paid > invoice.total_amount:
            remaining = invoice.total_amount - total_paid
            raise ValueError(f"Payment would exceed invoice total. Remaining amount: {remaining}")

        # Create payment
        payment = Payment(
            invoice_id=invoice.id,
            payment_date=payment_in.payment_date,
            amount=payment_in.amount,
            payment_method=payment_in.payment_method
        )
        db.add(payment)

        # Update invoice status
        if new_total_paid >= invoice.total_amount:
            invoice.status = InvoiceStatus.PAID
        
        db.commit()
        db.refresh(payment)
        db.refresh(invoice)
        return payment

    @staticmethod
    def get_by_invoice(invoice_id: int, db: Session):
        """Get all payments for an invoice"""
        return db.query(Payment).filter(
            Payment.invoice_id == invoice_id,
            Payment.deleted_at.is_(None)
        ).all()

    @staticmethod
    def get_by_id(payment_id: int, invoice_id: int, db: Session):
        """Get payment by ID (must belong to invoice)"""
        return db.query(Payment).filter(
            Payment.id == payment_id,
            Payment.invoice_id == invoice_id,
            Payment.deleted_at.is_(None)
        ).first()
