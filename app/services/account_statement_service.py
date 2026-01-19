from sqlalchemy.orm import Session
from sqlalchemy import func
from decimal import Decimal

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
    def get_school_statement(school_id: int, db: Session):
        """Get account statement for a school

        Optimized with SQL aggregation to avoid N+1 queries.
        Uses SUM() with JOIN to calculate totals in a single query across all students.
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

        # Get all invoices for school's students (excluding cancelled and deleted)
        # Join with Student to filter by school_id
        invoices = db.query(Invoice).join(
            Student, Invoice.student_id == Student.id
        ).filter(
            Student.school_id == school_id,
            Student.deleted_at.is_(None),
            Invoice.deleted_at.is_(None),
            Invoice.status != 'cancelled'
        ).all()

        # Use SQL aggregation to calculate totals efficiently
        # SUM(invoice.total_amount) for total_invoiced
        total_invoiced_result = db.query(
            func.coalesce(func.sum(Invoice.total_amount), 0)
        ).join(
            Student, Invoice.student_id == Student.id
        ).filter(
            Student.school_id == school_id,
            Student.deleted_at.is_(None),
            Invoice.deleted_at.is_(None),
            Invoice.status != 'cancelled'
        ).scalar()

        total_invoiced = Decimal(str(total_invoiced_result))

        # SUM(payment.amount) for total_paid
        # Join payments -> invoices -> students to filter by school
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
            Payment.deleted_at.is_(None)
        ).scalar()

        total_paid = Decimal(str(total_paid_result))
        total_pending = total_invoiced - total_paid

        return {
            "school_id": school.id,
            "school_name": school.name,
            "student_count": student_count,
            "total_invoiced": total_invoiced,
            "total_paid": total_paid,
            "total_pending": total_pending,
            "invoices": invoices
        }
