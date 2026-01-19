from sqlalchemy import Column, Integer, String, Date, DateTime, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
import enum

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
    email = Column(String(255))
    enrollment_date = Column(Date)
    status = Column(SQLEnum(StudentStatus), default=StudentStatus.ACTIVE, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)
    deleted_at = Column(DateTime, nullable=True)

    # Relationships
    school = relationship("School", back_populates="students")
    invoices = relationship("Invoice", back_populates="student", cascade="all, delete-orphan")
