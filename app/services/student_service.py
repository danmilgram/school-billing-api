from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models.student import Student
from app.schemas.student import StudentCreate, StudentUpdate


class StudentService:
    @staticmethod
    def get_all(db: Session, skip: int = 0, limit: int = 100):
        """Get all students excluding soft-deleted with pagination"""
        return (
            db.query(Student)
            .filter(Student.deleted_at.is_(None))
            .offset(skip)
            .limit(limit)
            .all()
        )

    @staticmethod
    def get_by_id(student_id: int, db: Session):
        """Get student by ID excluding soft-deleted"""
        return (
            db.query(Student)
            .filter(Student.id == student_id, Student.deleted_at.is_(None))
            .first()
        )

    @staticmethod
    def create(student_in: StudentCreate, db: Session):
        """Create a new student"""
        student = Student(**student_in.model_dump())
        db.add(student)
        db.commit()
        db.refresh(student)
        return student

    @staticmethod
    def update(student: Student, student_in: StudentUpdate, db: Session):
        """Update an existing student"""
        for field, value in student_in.model_dump(exclude_unset=True).items():
            setattr(student, field, value)
        db.commit()
        db.refresh(student)
        return student

    @staticmethod
    def delete(student: Student, db: Session):
        """Soft delete a student"""
        student.deleted_at = datetime.now(timezone.utc)
        db.commit()
        return True
