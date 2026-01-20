from sqlalchemy.orm import Session
from sqlalchemy import func
from decimal import Decimal
from datetime import date
from typing import Optional

from app.models.school import School
from app.models.student import Student
from app.models.invoice import Invoice
from app.models.payment import Payment


class AccountStatementService:

    @staticmethod
    def get_student_statement(student_id: int, db: Session):
        """Get account statement for a student

        Optimized with SQL aggregation to avoid N+1 queries.
        Uses SUM() with JOIN to calculate totals in a single query.
        """
        student = db.query(Student).filter(
            Student.id == student_id,
            Student.deleted_at.is_(None)
        ).first()

        if not student:
            return None

        school = db.query(School).filter(School.id == student.school_id).first()

        # Get all invoices for student (excluding cancelled and deleted)
        invoices = db.query(Invoice).filter(
            Invoice.student_id == student_id,
            Invoice.deleted_at.is_(None),
            Invoice.status != 'cancelled'
        ).all()

        # Use SQL aggregation to calculate totals efficiently
        # SUM(invoice.total_amount) for total_invoiced
        total_invoiced_result = db.query(
            func.coalesce(func.sum(Invoice.total_amount), 0)
        ).filter(
            Invoice.student_id == student_id,
            Invoice.deleted_at.is_(None),
            Invoice.status != 'cancelled'
        ).scalar()

        total_invoiced = Decimal(str(total_invoiced_result))

        # SUM(payment.amount) for total_paid
        # Join payments with invoices to ensure we only sum payments for non-cancelled invoices
        total_paid_result = db.query(
            func.coalesce(func.sum(Payment.amount), 0)
        ).join(
            Invoice, Payment.invoice_id == Invoice.id
        ).filter(
            Invoice.student_id == student_id,
            Invoice.deleted_at.is_(None),
            Invoice.status != 'cancelled',
            Payment.deleted_at.is_(None)
        ).scalar()

        total_paid = Decimal(str(total_paid_result))
        total_pending = total_invoiced - total_paid

        return {
            "student_id": student.id,
            "student_name": f"{student.first_name} {student.last_name}",
            "school_id": school.id,
            "school_name": school.name,
            "total_invoiced": total_invoiced,
            "total_paid": total_paid,
            "total_pending": total_pending,
            "invoices": invoices
        }

    @staticmethod
    def get_school_statement(
        school_id: int,
        db: Session,
        start_date: date,
        end_date: date,
        include_invoices: bool = False
    ):
        """Get account statement for a school

        Optimized with SQL aggregation to avoid N+1 queries.
        Uses SUM() with JOIN to calculate totals in a single query across all students.

        Args:
            school_id: The school ID
            db: Database session
            start_date: Filter for invoices issued on or after this date (required)
            end_date: Filter for invoices issued on or before this date (required)
            include_invoices: Whether to include the list of invoices (default: False)
        """
        school = db.query(School).filter(
            School.id == school_id,
            School.deleted_at.is_(None)
        ).first()

        if not school:
            return None

        # Count active students
        student_count = db.query(Student).filter(
            Student.school_id == school_id,
            Student.deleted_at.is_(None)
        ).count()

        # Query for invoices with date filters (only if needed)
        invoices = []
        if include_invoices:
            invoices = db.query(Invoice).join(
                Student, Invoice.student_id == Student.id
            ).filter(
                Student.school_id == school_id,
                Student.deleted_at.is_(None),
                Invoice.deleted_at.is_(None),
                Invoice.status != 'cancelled',
                Invoice.issue_date >= start_date,
                Invoice.issue_date <= end_date
            ).all()

        # Query for total_invoiced with date filters
        total_invoiced_result = db.query(
            func.coalesce(func.sum(Invoice.total_amount), 0)
        ).join(
            Student, Invoice.student_id == Student.id
        ).filter(
            Student.school_id == school_id,
            Student.deleted_at.is_(None),
            Invoice.deleted_at.is_(None),
            Invoice.status != 'cancelled',
            Invoice.issue_date >= start_date,
            Invoice.issue_date <= end_date
        ).scalar()

        total_invoiced = Decimal(str(total_invoiced_result))

        # Query for total_paid with date filters on invoice issue_date
        total_paid_result = db.query(
            func.coalesce(func.sum(Payment.amount), 0)
        ).join(
            Invoice, Payment.invoice_id == Invoice.id
        ).join(
            Student, Invoice.student_id == Student.id
        ).filter(
            Student.school_id == school_id,
            Student.deleted_at.is_(None),
            Invoice.deleted_at.is_(None),
            Invoice.status != 'cancelled',
            Payment.deleted_at.is_(None),
            Invoice.issue_date >= start_date,
            Invoice.issue_date <= end_date
        ).scalar()
        total_paid = Decimal(str(total_paid_result))
        total_pending = total_invoiced - total_paid

        # Build invoice statement items with paid/pending amounts (only if requested)
        invoice_items = None
        if include_invoices:
            invoice_items = []
            for invoice in invoices:
                # Calculate paid amount for this invoice
                paid_for_invoice = db.query(
                    func.coalesce(func.sum(Payment.amount), 0)
                ).filter(
                    Payment.invoice_id == invoice.id,
                    Payment.deleted_at.is_(None)
                ).scalar()

                paid_amount = Decimal(str(paid_for_invoice))
                pending_amount = invoice.total_amount - paid_amount

                invoice_items.append({
                    "invoice_id": invoice.id,
                    "student_id": invoice.student_id,
                    "issue_date": invoice.issue_date,
                    "due_date": invoice.due_date,
                    "status": invoice.status.upper(),
                    "total_amount": invoice.total_amount,
                    "paid_amount": paid_amount,
                    "pending_amount": pending_amount
                })

        return {
            "school_id": school.id,
            "school_name": school.name,
            "period": {
                "start_date": start_date,
                "end_date": end_date
            },
            "student_count": student_count,
            "summary": {
                "total_invoiced": total_invoiced,
                "total_paid": total_paid,
                "total_pending": total_pending
            },
            "invoices": invoice_items
        }
