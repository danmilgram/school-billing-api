from datetime import date
from decimal import Decimal

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.invoice import Invoice
from app.models.payment import Payment
from app.models.school import School
from app.models.student import Student


class SchoolStatementService:
    """Service for generating school account statements"""

    def __init__(
        self,
        school_id: int,
        db: Session,
        start_date: date,
        end_date: date,
        include_invoices: bool = False,
    ):
        """Initialize the service with request parameters

        Args:
            school_id: The school ID
            db: Database session
            start_date: Filter for invoices issued on or after this date
            end_date: Filter for invoices issued on or before this date
            include_invoices: Whether to include the list of invoices (default: False)
        """
        self.school_id = school_id
        self.db = db
        self.start_date = start_date
        self.end_date = end_date
        self.include_invoices = include_invoices

    def _get_school_and_student_count(self) -> tuple[School, int] | None:
        """Fetch school and count active students (validation + existence check)

        Returns:
            Tuple of (school, student_count) if school exists, None otherwise
        """
        school = (
            self.db.query(School)
            .filter(School.id == self.school_id, School.deleted_at.is_(None))
            .first()
        )

        if not school:
            return None

        student_count = (
            self.db.query(Student)
            .filter(Student.school_id == self.school_id, Student.deleted_at.is_(None))
            .count()
        )

        return school, student_count

    def _calculate_totals(self) -> tuple[Decimal, Decimal, Decimal]:
        """Aggregate totals for school invoices (pure aggregation logic)

        Returns:
            Tuple of (total_invoiced, total_paid, total_pending)
        """
        # Query for total_invoiced with date filters
        total_invoiced_result = (
            self.db.query(func.coalesce(func.sum(Invoice.total_amount), 0))
            .join(Student, Invoice.student_id == Student.id)
            .filter(
                Student.school_id == self.school_id,
                Student.deleted_at.is_(None),
                Invoice.deleted_at.is_(None),
                Invoice.status != "cancelled",
                Invoice.issue_date >= self.start_date,
                Invoice.issue_date <= self.end_date,
            )
            .scalar()
        )

        total_invoiced = Decimal(str(total_invoiced_result))

        # Query for total_paid with date filters on invoice issue_date
        total_paid_result = (
            self.db.query(func.coalesce(func.sum(Payment.amount), 0))
            .join(Invoice, Payment.invoice_id == Invoice.id)
            .join(Student, Invoice.student_id == Student.id)
            .filter(
                Student.school_id == self.school_id,
                Student.deleted_at.is_(None),
                Invoice.deleted_at.is_(None),
                Invoice.status != "cancelled",
                Payment.deleted_at.is_(None),
                Invoice.issue_date >= self.start_date,
                Invoice.issue_date <= self.end_date,
            )
            .scalar()
        )

        total_paid = Decimal(str(total_paid_result))
        total_pending = total_invoiced - total_paid

        return total_invoiced, total_paid, total_pending

    def _build_invoice_rows(self) -> list[dict]:
        """Get invoice breakdown for school (expensive, optional, reusable)

        Returns:
            List of invoice dictionaries with paid/pending amounts

        Handles:
        - Invoice query (joined with students)
        - Payment aggregation per invoice (no N+1)
        - Row shaping
        """
        # Query for invoices with date filters
        invoices = (
            self.db.query(Invoice)
            .join(Student, Invoice.student_id == Student.id)
            .filter(
                Student.school_id == self.school_id,
                Student.deleted_at.is_(None),
                Invoice.deleted_at.is_(None),
                Invoice.status != "cancelled",
                Invoice.issue_date >= self.start_date,
                Invoice.issue_date <= self.end_date,
            )
            .all()
        )

        if not invoices:
            return []

        # Single grouped query to get paid amounts for all invoices (no N+1)
        invoice_ids = [invoice.id for invoice in invoices]

        payment_results = (
            self.db.query(
                Payment.invoice_id,
                func.coalesce(func.sum(Payment.amount), 0).label("paid_amount"),
            )
            .filter(Payment.invoice_id.in_(invoice_ids), Payment.deleted_at.is_(None))
            .group_by(Payment.invoice_id)
            .all()
        )

        # Build a dictionary for O(1) lookup
        payment_totals = {
            invoice_id: Decimal(str(paid)) for invoice_id, paid in payment_results
        }

        # Now build invoice items with O(1) lookup per invoice
        invoice_items = []
        for invoice in invoices:
            paid_amount = payment_totals.get(invoice.id, Decimal("0"))
            pending_amount = invoice.total_amount - paid_amount

            invoice_items.append(
                {
                    "invoice_id": invoice.id,
                    "student_id": invoice.student_id,
                    "issue_date": invoice.issue_date,
                    "due_date": invoice.due_date,
                    "status": invoice.status.upper(),
                    "total_amount": invoice.total_amount,
                    "paid_amount": paid_amount,
                    "pending_amount": pending_amount,
                }
            )

        return invoice_items

    def get_statement(self):
        """Get account statement for a school (application-level use case)

        Orchestrates the statement generation by delegating to helper methods.

        Returns:
            Statement dict or None if school not found
        """
        # Validation / existence check
        result = self._get_school_and_student_count()
        if not result:
            return None

        school, student_count = result

        # Aggregation queries
        total_invoiced, total_paid, total_pending = self._calculate_totals()

        # Optional detail expansion
        invoice_items = None
        if self.include_invoices:
            invoice_items = self._build_invoice_rows()

        # Build and return statement
        return {
            "school_id": school.id,
            "school_name": school.name,
            "period": {"start_date": self.start_date, "end_date": self.end_date},
            "student_count": student_count,
            "summary": {
                "total_invoiced": total_invoiced,
                "total_paid": total_paid,
                "total_pending": total_pending,
            },
            "invoices": invoice_items,
        }
