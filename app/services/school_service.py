from sqlalchemy.orm import Session
from datetime import datetime, timezone

from app.models.school import School
from app.schemas.school import SchoolCreate, SchoolUpdate


class SchoolService:

    @staticmethod
    def get_all(db: Session):
        """Get all schools excluding soft-deleted"""
        return db.query(School).filter(School.deleted_at.is_(None)).all()

    @staticmethod
    def get_by_id(school_id: int, db: Session):
        """Get school by ID excluding soft-deleted"""
        return db.query(School).filter(
            School.id == school_id,
            School.deleted_at.is_(None)
        ).first()

    @staticmethod
    def create(school_in: SchoolCreate, db: Session):
        """Create a new school"""
        school = School(**school_in.model_dump())
        db.add(school)
        db.commit()
        db.refresh(school)
        return school

    @staticmethod
    def update(school: School, school_in: SchoolUpdate, db: Session):
        """Update an existing school"""
        for field, value in school_in.model_dump(exclude_unset=True).items():
            setattr(school, field, value)
        db.commit()
        db.refresh(school)
        return school

    @staticmethod
    def delete(school: School, db: Session):
        """Soft delete a school"""
        school.deleted_at = datetime.now(timezone.utc)
        db.commit()
        return True
