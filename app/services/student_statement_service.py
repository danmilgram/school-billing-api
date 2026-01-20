from sqlalchemy.orm import Session
from sqlalchemy import func
from decimal import Decimal
from datetime import date

from app.models.school import School
from app.models.student import Student
from app.models.invoice import Invoice
from app.models.payment import Payment


class StudentStatementService:
    """Service for generating student account statements"""

    @staticmethod
    def _get_student_and_school(
        db: Session, student_id: int
    ) -> tuple[Student | None, School | None]:
        """Fetch student and their school (validation + existence check)"""
        student = db.query(Student).filter(
            Student.id == student_id,
            Student.deleted_at.is_(None)
        ).first()

        if not student:
            return None, None

        school = db.query(School).filter(School.id == student.school_id).first()
        return student, school

    @staticmethod
    def _get_student_totals(
        db: Session,
        student_id: int,
        start_date: date,
        end_date: date,
    ) -> tuple[Decimal, Decimal, Decimal]:
        """Aggregate totals for student invoices (pure aggregation logic)

        Returns:
            (total_invoiced, total_paid, total_pending)
        """
        # SUM(invoice.total_amount) for total_invoiced
        total_invoiced_result = db.query(
            func.coalesce(func.sum(Invoice.total_amount), 0)
        ).filter(
            Invoice.student_id == student_id,
            Invoice.deleted_at.is_(None),
            Invoice.status != 'cancelled',
            Invoice.issue_date >= start_date,
            Invoice.issue_date <= end_date
        ).scalar()

        total_invoiced = Decimal(str(total_invoiced_result))

        # SUM(payment.amount) for total_paid with date filters on invoice issue_date
        total_paid_result = db.query(
            func.coalesce(func.sum(Payment.amount), 0)
        ).join(
            Invoice, Payment.invoice_id == Invoice.id
        ).filter(
            Invoice.student_id == student_id,
            Invoice.deleted_at.is_(None),
            Invoice.status != 'cancelled',
            Payment.deleted_at.is_(None),
            Invoice.issue_date >= start_date,
            Invoice.issue_date <= end_date
        ).scalar()

        total_paid = Decimal(str(total_paid_result))
        total_pending = total_invoiced - total_paid

        return total_invoiced, total_paid, total_pending

    @staticmethod
    def _get_student_invoice_rows(
        db: Session,
        student_id: int,
        start_date: date,
        end_date: date,
    ) -> list[dict]:
        """Get invoice breakdown for student (expensive, optional, reusable)

        Handles:
        - Invoice query
        - Payment aggregation per invoice (no N+1)
        - Row shaping
        """
        # Query for invoices with date filters
        invoices = db.query(Invoice).filter(
            Invoice.student_id == student_id,
            Invoice.deleted_at.is_(None),
            Invoice.status != 'cancelled',
            Invoice.issue_date >= start_date,
            Invoice.issue_date <= end_date
        ).all()

        if not invoices:
            return []

        # Single grouped query to get paid amounts for all invoices (no N+1)
        invoice_ids = [invoice.id for invoice in invoices]

        payment_results = db.query(
            Payment.invoice_id,
            func.coalesce(func.sum(Payment.amount), 0).label('paid_amount')
        ).filter(
            Payment.invoice_id.in_(invoice_ids),
            Payment.deleted_at.is_(None)
        ).group_by(Payment.invoice_id).all()

        # Build a dictionary for O(1) lookup
        payment_totals = {invoice_id: Decimal(str(paid)) for invoice_id, paid in payment_results}

        # Now build invoice items with O(1) lookup per invoice
        invoice_items = []
        for invoice in invoices:
            paid_amount = payment_totals.get(invoice.id, Decimal("0"))
            pending_amount = invoice.total_amount - paid_amount

            invoice_items.append({
                "invoice_id": invoice.id,
                "issue_date": invoice.issue_date,
                "due_date": invoice.due_date,
                "status": invoice.status.upper(),
                "total_amount": invoice.total_amount,
                "paid_amount": paid_amount,
                "pending_amount": pending_amount
            })

        return invoice_items

    @staticmethod
    def get_statement(
        student_id: int,
        db: Session,
        start_date: date,
        end_date: date,
        include_invoices: bool = False
    ):
        """Get account statement for a student (application-level use case)

        Orchestrates the statement generation by delegating to helper methods.

        Args:
            student_id: The student ID
            db: Database session
            start_date: Filter for invoices issued on or after this date (required)
            end_date: Filter for invoices issued on or before this date (required)
            include_invoices: Whether to include the list of invoices (default: False)
        """
        # Validation / existence check
        student, school = StudentStatementService._get_student_and_school(db, student_id)
        if not student:
            return None

        # Aggregation queries
        total_invoiced, total_paid, total_pending = StudentStatementService._get_student_totals(
            db, student_id, start_date, end_date
        )

        # Optional detail expansion
        invoice_items = None
        if include_invoices:
            invoice_items = StudentStatementService._get_student_invoice_rows(
                db, student_id, start_date, end_date
            )

        # Build and return statement
        return {
            "student_id": student.id,
            "student_name": f"{student.first_name} {student.last_name}",
            "school_id": school.id,
            "school_name": school.name,
            "period": {
                "start_date": start_date,
                "end_date": end_date
            },
            "summary": {
                "total_invoiced": total_invoiced,
                "total_paid": total_paid,
                "total_pending": total_pending
            },
            "invoices": invoice_items
        }
