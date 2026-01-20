import enum
from datetime import datetime, timezone

from sqlalchemy import Column, Date, DateTime, ForeignKey, Integer, String
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.orm import relationship

from app.core.database import Base


class StudentStatus(str, enum.Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    GRADUATED = "graduated"


class Student(Base):
    __tablename__ = "students"

    # TODO: Add address fields (not part of the core requirements)
    id = Column(Integer, primary_key=True, autoincrement=True)
    school_id = Column(Integer, ForeignKey("schools.id"), nullable=False)
    first_name = Column(String(255), nullable=False)
    last_name = Column(String(255), nullable=False)
    # TODO: this is like a contact email, for a real model we might want to
    # separate student and guardian(parents) contacts
    email = Column(String(255), nullable=False)
    enrollment_date = Column(Date, nullable=False)
    status = Column(SQLEnum(StudentStatus), default=StudentStatus.ACTIVE, nullable=False)
    created_at = Column(
        DateTime, default=lambda: datetime.now(timezone.utc), nullable=False
    )
    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    deleted_at = Column(DateTime, nullable=True)

    # Relationships
    school = relationship("School", back_populates="students")
    invoices = relationship(
        "Invoice", back_populates="student", cascade="all, delete-orphan"
    )
