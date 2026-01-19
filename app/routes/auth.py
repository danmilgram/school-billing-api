from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.user import UserCreate, UserRead, Token
from app.services.user_service import UserService
from app.core.security import create_access_token
from app.core.auth import get_current_user
from app.models.user import User

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=UserRead, status_code=status.HTTP_201_CREATED)
def register(user_in: UserCreate, db: Session = Depends(get_db)):
    """
    Register a new user

    - **email**: Valid email address (must be unique)
    - **password**: User password (will be hashed)
    - **full_name**: Optional full name
    """
    # Check if user already exists
    existing_user = UserService.get_by_email(user_in.email, db)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    # Create new user
    user = UserService.create(user_in, db)
    return user


@router.post("/login", response_model=Token)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """
    Login with email and password to get access token

    - **username**: User email (OAuth2 spec uses 'username' field)
    - **password**: User password

    Returns JWT access token for authenticated requests
    """
    # Authenticate user
    user = UserService.authenticate(
        email=form_data.username,  # OAuth2PasswordRequestForm uses 'username' field
        password=form_data.password,
        db=db
    )

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Create access token
    access_token = create_access_token(data={"sub": user.email})

    return {
        "access_token": access_token,
        "token_type": "bearer"
    }


@router.get("/me", response_model=UserRead)
def get_current_user_profile(current_user: User = Depends(get_current_user)):
    """
    Get current user profile

    Requires authentication token
    """
    return current_user
