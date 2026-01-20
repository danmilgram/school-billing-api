from app.core.security import verify_password
from app.models.user import User, UserRole
from app.schemas.user import UserCreate, UserUpdate
from app.services.user_service import UserService


def test_create_user(db):
    """Test creating a new user"""
    user_data = UserCreate(
        email="test@example.com", password="password123", full_name="Test User"
    )

    user = UserService.create(user_data, db)

    assert user.id is not None
    assert user.email == "test@example.com"
    assert user.full_name == "Test User"
    assert user.role == UserRole.USER
    assert user.is_active == 1
    assert user.deleted_at is None
    assert user.hashed_password != "password123"  # Should be hashed
    assert verify_password("password123", user.hashed_password)  # Verify password works


def test_get_user_by_email(db):
    """Test getting a user by email"""
    user = UserService.create(
        UserCreate(
            email="test@example.com", password="password123", full_name="Test User"
        ),
        db,
    )

    retrieved_user = UserService.get_by_email("test@example.com", db)

    assert retrieved_user is not None
    assert retrieved_user.id == user.id
    assert retrieved_user.email == "test@example.com"


def test_get_nonexistent_user_by_email(db):
    """Test getting a user that doesn't exist"""
    user = UserService.get_by_email("nonexistent@example.com", db)

    assert user is None


def test_get_user_by_id(db):
    """Test getting a user by ID"""
    user = UserService.create(
        UserCreate(
            email="test@example.com", password="password123", full_name="Test User"
        ),
        db,
    )

    retrieved_user = UserService.get_by_id(user.id, db)

    assert retrieved_user is not None
    assert retrieved_user.id == user.id
    assert retrieved_user.email == "test@example.com"


def test_get_nonexistent_user_by_id(db):
    """Test getting a user by ID that doesn't exist"""
    user = UserService.get_by_id(999, db)

    assert user is None


def test_update_user(db):
    """Test updating a user"""
    user = UserService.create(
        UserCreate(
            email="original@example.com",
            password="password123",
            full_name="Original Name",
        ),
        db,
    )

    update_data = UserUpdate(full_name="Updated Name")
    updated_user = UserService.update(user, update_data, db)

    assert updated_user.full_name == "Updated Name"
    assert updated_user.email == "original@example.com"  # Email should not change


def test_update_user_password(db):
    """Test updating a user's password"""
    user = UserService.create(
        UserCreate(
            email="test@example.com", password="oldpassword", full_name="Test User"
        ),
        db,
    )

    old_hashed_password = user.hashed_password

    update_data = UserUpdate(password="newpassword")
    updated_user = UserService.update(user, update_data, db)

    # Password should be hashed and different from old one
    assert updated_user.hashed_password != old_hashed_password
    assert verify_password("newpassword", updated_user.hashed_password)
    assert not verify_password("oldpassword", updated_user.hashed_password)


def test_authenticate_user_success(db):
    """Test successful user authentication"""
    UserService.create(
        UserCreate(
            email="test@example.com", password="password123", full_name="Test User"
        ),
        db,
    )

    authenticated_user = UserService.authenticate("test@example.com", "password123", db)

    assert authenticated_user is not None
    assert authenticated_user.email == "test@example.com"


def test_authenticate_user_wrong_password(db):
    """Test authentication with wrong password"""
    UserService.create(
        UserCreate(
            email="test@example.com", password="password123", full_name="Test User"
        ),
        db,
    )

    authenticated_user = UserService.authenticate("test@example.com", "wrongpassword", db)

    assert authenticated_user is None


def test_authenticate_nonexistent_user(db):
    """Test authentication with non-existent email"""
    authenticated_user = UserService.authenticate(
        "nonexistent@example.com", "password123", db
    )

    assert authenticated_user is None


def test_soft_delete_user(db):
    """Test soft deleting a user"""
    user = UserService.create(
        UserCreate(
            email="delete@example.com", password="password123", full_name="To Delete"
        ),
        db,
    )

    UserService.delete(user, db)

    # Should not be returned by get_by_email
    retrieved_user = UserService.get_by_email("delete@example.com", db)
    assert retrieved_user is None

    # Should not be returned by get_by_id
    retrieved_user_by_id = UserService.get_by_id(user.id, db)
    assert retrieved_user_by_id is None

    # But should still exist in database with deleted_at set
    deleted_user = db.query(User).filter(User.id == user.id).first()
    assert deleted_user is not None
    assert deleted_user.deleted_at is not None


def test_get_by_email_excludes_soft_deleted(db):
    """Test that get_by_email excludes soft-deleted users"""
    user = UserService.create(
        UserCreate(
            email="test@example.com", password="password123", full_name="Test User"
        ),
        db,
    )

    # Soft delete user
    UserService.delete(user, db)

    # get_by_email should return None
    retrieved_user = UserService.get_by_email("test@example.com", db)
    assert retrieved_user is None


def test_authenticate_soft_deleted_user(db):
    """Test that authentication fails for soft-deleted users"""
    user = UserService.create(
        UserCreate(
            email="test@example.com", password="password123", full_name="Test User"
        ),
        db,
    )

    # Soft delete user
    UserService.delete(user, db)

    # Authentication should fail
    authenticated_user = UserService.authenticate("test@example.com", "password123", db)
    assert authenticated_user is None
