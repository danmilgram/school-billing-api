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
        """Get account statement for a student"""
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

        total_invoiced = Decimal('0')
        total_paid = Decimal('0')

        for invoice in invoices:
            total_invoiced += invoice.total_amount

            # Calculate paid amount for this invoice
            payments = db.query(Payment).filter(
                Payment.invoice_id == invoice.id,
                Payment.deleted_at.is_(None)
            ).all()
            total_paid += sum(p.amount for p in payments)

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
        """Get account statement for a school"""
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

        # Get all student IDs for this school
        student_ids = db.query(Student.id).filter(
            Student.school_id == school_id,
            Student.deleted_at.is_(None)
        ).all()
        student_ids = [s[0] for s in student_ids]

        # Get all invoices for school's students (excluding cancelled and deleted)
        invoices = db.query(Invoice).filter(
            Invoice.student_id.in_(student_ids),
            Invoice.deleted_at.is_(None),
            Invoice.status != 'cancelled'
        ).all()

        total_invoiced = Decimal('0')
        total_paid = Decimal('0')

        for invoice in invoices:
            total_invoiced += invoice.total_amount

            # Calculate paid amount for this invoice
            payments = db.query(Payment).filter(
                Payment.invoice_id == invoice.id,
                Payment.deleted_at.is_(None)
            ).all()
            total_paid += sum(p.amount for p in payments)

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
