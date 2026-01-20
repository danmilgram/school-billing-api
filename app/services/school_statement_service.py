from sqlalchemy.orm import Session
from sqlalchemy import func
from decimal import Decimal
from datetime import date

from app.models.school import School
from app.models.student import Student
from app.models.invoice import Invoice
from app.models.payment import Payment


class SchoolStatementService:
    """Service for generating school account statements"""

    @staticmethod
    def _get_school_and_student_count(
        db: Session, school_id: int
    ) -> tuple[School | None, int]:
        """Fetch school and count active students (validation + existence check)"""
        school = db.query(School).filter(
            School.id == school_id,
            School.deleted_at.is_(None)
        ).first()

        if not school:
            return None, 0

        student_count = db.query(Student).filter(
            Student.school_id == school_id,
            Student.deleted_at.is_(None)
        ).count()

        return school, student_count

    @staticmethod
    def _get_school_totals(
        db: Session,
        school_id: int,
        start_date: date,
        end_date: date,
    ) -> tuple[Decimal, Decimal, Decimal]:
        """Aggregate totals for school invoices (pure aggregation logic)

        Returns:
            (total_invoiced, total_paid, total_pending)
        """
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

        return total_invoiced, total_paid, total_pending

    @staticmethod
    def _get_school_invoice_rows(
        db: Session,
        school_id: int,
        start_date: date,
        end_date: date,
    ) -> list[dict]:
        """Get invoice breakdown for school (expensive, optional, reusable)

        Handles:
        - Invoice query (joined with students)
        - Payment aggregation per invoice (no N+1)
        - Row shaping
        """
        # Query for invoices with date filters
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
                "student_id": invoice.student_id,
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
        school_id: int,
        db: Session,
        start_date: date,
        end_date: date,
        include_invoices: bool = False
    ):
        """Get account statement for a school (application-level use case)

        Orchestrates the statement generation by delegating to helper methods.

        Args:
            school_id: The school ID
            db: Database session
            start_date: Filter for invoices issued on or after this date (required)
            end_date: Filter for invoices issued on or before this date (required)
            include_invoices: Whether to include the list of invoices (default: False)
        """
        # Validation / existence check
        school, student_count = SchoolStatementService._get_school_and_student_count(db, school_id)
        if not school:
            return None

        # Aggregation queries
        total_invoiced, total_paid, total_pending = SchoolStatementService._get_school_totals(
            db, school_id, start_date, end_date
        )

        # Optional detail expansion
        invoice_items = None
        if include_invoices:
            invoice_items = SchoolStatementService._get_school_invoice_rows(
                db, school_id, start_date, end_date
            )

        # Build and return statement
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
