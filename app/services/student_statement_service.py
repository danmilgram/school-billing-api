import logging
from datetime import date
from decimal import Decimal

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.invoice import Invoice
from app.models.payment import Payment
from app.models.school import School
from app.models.student import Student

logger = logging.getLogger(__name__)


class StudentStatementService:
    """Service for generating student account statements"""

    def __init__(
        self,
        student_id: int,
        db: Session,
        start_date: date,
        end_date: date,
        include_invoices: bool = False,
    ):
        """Initialize the service with request parameters

        Args:
            student_id: The student ID
            db: Database session
            start_date: Filter for invoices issued on or after this date
            end_date: Filter for invoices issued on or before this date
            include_invoices: Whether to include the list of invoices (default: False)
        """
        self.student_id = student_id
        self.db = db
        self.start_date = start_date
        self.end_date = end_date
        self.include_invoices = include_invoices

    def _get_student_and_school(self) -> tuple[Student, School] | None:
        """Fetch student and their school (validation + existence check)

        Returns:
            Tuple of (student, school) if student exists, None otherwise
        """
        student = (
            self.db.query(Student)
            .filter(Student.id == self.student_id, Student.deleted_at.is_(None))
            .first()
        )

        if not student:
            return None

        school = self.db.query(School).filter(School.id == student.school_id).first()

        return student, school

    def _student_invoice_base_filters(self):
        """
        Return common filter conditions for student invoice queries

        Returns:
            List of filter conditions that can be unpacked into .filter()
        """
        return [
            Invoice.student_id == self.student_id,
            Invoice.deleted_at.is_(None),
            Invoice.status != "cancelled",
            Invoice.issue_date >= self.start_date,
            Invoice.issue_date <= self.end_date,
        ]

    def _calculate_totals(self) -> tuple[Decimal, Decimal, Decimal]:
        """Aggregate totals for student invoices (pure aggregation logic)

        Returns:
            Tuple of (total_invoiced, total_paid, total_pending)
        """
        # SUM(invoice.total_amount) for total_invoiced
        total_invoiced_result = (
            self.db.query(func.coalesce(func.sum(Invoice.total_amount), 0))
            .filter(*self._student_invoice_base_filters())
            .scalar()
        )

        total_invoiced: Decimal = total_invoiced_result or Decimal("0")

        # SUM(payment.amount) for total_paid with date filters on invoice issue_date
        total_paid_result = (
            self.db.query(func.coalesce(func.sum(Payment.amount), 0))
            .join(Invoice, Payment.invoice_id == Invoice.id)
            .filter(*self._student_invoice_base_filters(), Payment.deleted_at.is_(None))
            .scalar()
        )

        total_paid: Decimal = total_paid_result or Decimal("0")
        total_pending: Decimal = total_invoiced - total_paid

        return total_invoiced, total_paid, total_pending

    def _build_invoice_rows(self) -> list[dict]:
        """Get invoice breakdown for student (expensive, optional, reusable)

        Returns:
            List of invoice dictionaries with paid/pending amounts

        Handles:
        - Invoice query
        - Payment aggregation per invoice (no N+1)
        - Row shaping
        """
        # Query for invoices with date filters
        invoices = (
            self.db.query(Invoice)
            .filter(*self._student_invoice_base_filters())
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
            invoice_id: paid or Decimal("0") for invoice_id, paid in payment_results
        }

        # Now build invoice items with O(1) lookup per invoice
        invoice_items = []
        for invoice in invoices:
            paid_amount = payment_totals.get(invoice.id, Decimal("0"))
            pending_amount = invoice.total_amount - paid_amount

            invoice_items.append(
                {
                    "invoice_id": invoice.id,
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
        """Get account statement for a student (application-level use case)

        Orchestrates the statement generation by delegating to helper methods.

        Returns:
            Statement dict or None if student not found
        """
        logger.info(
            f"Generating student statement: student_id={self.student_id}, "
            f"period={self.start_date} to {self.end_date}, "
            f"include_invoices={self.include_invoices}"
        )

        # Validation / existence check
        result = self._get_student_and_school()
        if not result:
            logger.warning(f"Student not found: student_id={self.student_id}")
            return None

        student, school = result

        # Aggregation queries
        total_invoiced, total_paid, total_pending = self._calculate_totals()

        # Optional detail expansion
        invoice_items = None
        if self.include_invoices:
            invoice_items = self._build_invoice_rows()

        logger.info(
            f"Student statement generated: student_id={student.id}, "
            f"school_id={school.id}, "
            f"total_invoiced={total_invoiced}, "
            f"total_paid={total_paid}, total_pending={total_pending}"
        )

        # Build and return statement
        return {
            "student_id": student.id,
            "student_name": f"{student.first_name} {student.last_name}",
            "school_id": school.id,
            "school_name": school.name,
            "period": {"start_date": self.start_date, "end_date": self.end_date},
            "summary": {
                "total_invoiced": total_invoiced,
                "total_paid": total_paid,
                "total_pending": total_pending,
            },
            "invoices": invoice_items,
        }
