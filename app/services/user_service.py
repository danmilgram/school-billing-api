from sqlalchemy.orm import Session
from datetime import datetime, timezone

from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate
from app.core.security import hash_password, verify_password


class UserService:

    @staticmethod
    def get_by_email(email: str, db: Session):
        """Get user by email excluding soft-deleted"""
        return db.query(User).filter(
            User.email == email,
            User.deleted_at.is_(None)
        ).first()

    @staticmethod
    def get_by_id(user_id: int, db: Session):
        """Get user by ID excluding soft-deleted"""
        return db.query(User).filter(
            User.id == user_id,
            User.deleted_at.is_(None)
        ).first()

    @staticmethod
    def create(user_in: UserCreate, db: Session):
        """Create a new user with hashed password"""
        hashed_pwd = hash_password(user_in.password)
        user = User(
            email=user_in.email,
            hashed_password=hashed_pwd,
            full_name=user_in.full_name
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return user

    @staticmethod
    def update(user: User, user_in: UserUpdate, db: Session):
        """Update user information"""
        update_data = user_in.model_dump(exclude_unset=True)

        # Hash password if provided
        if "password" in update_data:
            update_data["hashed_password"] = hash_password(update_data.pop("password"))

        for field, value in update_data.items():
            setattr(user, field, value)

        db.commit()
        db.refresh(user)
        return user

    @staticmethod
    def authenticate(email: str, password: str, db: Session):
        """Authenticate user with email and password"""
        user = UserService.get_by_email(email, db)
        if not user:
            return None
        if not verify_password(password, user.hashed_password):
            return None
        return user

    @staticmethod
    def delete(user: User, db: Session):
        """Soft delete a user"""
        user.deleted_at = datetime.now(timezone.utc)
        db.commit()
        return True
