import enum
from datetime import datetime, timezone

from sqlalchemy import Column, Date, DateTime, ForeignKey, Integer, Numeric
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.orm import relationship

from app.core.database import Base


class InvoiceStatus(str, enum.Enum):
    PENDING = "pending"
    PAID = "paid"
    OVERDUE = "overdue"
    CANCELLED = "cancelled"


class Invoice(Base):
    __tablename__ = "invoices"

    id = Column(Integer, primary_key=True, autoincrement=True)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False)
    issue_date = Column(Date, nullable=False)
    due_date = Column(Date, nullable=False)
    total_amount = Column(Numeric(10, 2), nullable=False)
    status = Column(SQLEnum(InvoiceStatus), default=InvoiceStatus.PENDING, nullable=False)
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
    student = relationship("Student", back_populates="invoices")
    items = relationship(
        "InvoiceItem", back_populates="invoice", cascade="all, delete-orphan"
    )
    payments = relationship(
        "Payment", back_populates="invoice", cascade="all, delete-orphan"
    )
