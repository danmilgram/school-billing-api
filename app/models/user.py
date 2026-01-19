from sqlalchemy import Column, Integer, String, DateTime, Enum as SQLEnum
from datetime import datetime, timezone
from enum import Enum

from app.core.database import Base


class UserRole(str, Enum):
    """User role enumeration"""
    ADMIN = "admin"
    USER = "user"


class User(Base):
    """User model for authentication"""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String(255), nullable=True)
    role = Column(
        SQLEnum(UserRole, name="user_role"),
        default=UserRole.USER,
        nullable=False
    )
    is_active = Column(Integer, default=1, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False
    )
    deleted_at = Column(DateTime, nullable=True)
