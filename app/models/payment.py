import enum
from datetime import datetime, timezone

from sqlalchemy import Column, Date, DateTime, ForeignKey, Integer, Numeric
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.orm import relationship

from app.core.database import Base


class PaymentMethod(str, enum.Enum):
    CASH = "cash"
    CARD = "card"
    TRANSFER = "transfer"
    CHECK = "check"


class Payment(Base):
    __tablename__ = "payments"

    id = Column(Integer, primary_key=True, autoincrement=True)
    invoice_id = Column(Integer, ForeignKey("invoices.id"), nullable=False)
    payment_date = Column(Date, nullable=False)
    amount = Column(Numeric(10, 2), nullable=False)
    payment_method = Column(SQLEnum(PaymentMethod), nullable=False)
    created_at = Column(
        DateTime, default=lambda: datetime.now(timezone.utc), nullable=False
    )
    deleted_at = Column(DateTime, nullable=True)

    # Relationships
    invoice = relationship("Invoice", back_populates="payments")
