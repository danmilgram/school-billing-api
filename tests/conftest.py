import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient

from app.core.database import Base, get_db
from app.core.auth import get_current_user
from app.main import app
from app.models.user import User, UserRole
from app.services.user_service import UserService
from app.schemas.user import UserCreate

# Test database URL (use in-memory SQLite for fast tests)
TEST_DATABASE_URL = "sqlite:///./test.db"

# Create test engine
engine = create_engine(
    TEST_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db():
    """Create a fresh database for each test"""
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db):
    """Create a test client with database override and auth bypass"""
    def override_get_db():
        try:
            yield db
        finally:
            pass

    # Create a mock user for authenticated requests
    from datetime import datetime, timezone
    mock_user = User(
        id=999,
        email="test@example.com",
        hashed_password="fake_hash",
        full_name="Test User",
        role=UserRole.USER,
        is_active=1,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )

    def override_get_current_user():
        return mock_user

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = override_get_current_user

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
def test_user(db):
    """Create a test user in the database"""
    user_data = UserCreate(
        email="testuser@example.com",
        password="testpassword123",
        full_name="Test User"
    )
    user = UserService.create(user_data, db)
    return user


@pytest.fixture(scope="function")
def auth_token(client, test_user):
    """Get an authentication token for the test user"""
    response = client.post(
        "/api/v1/auth/login",
        data={
            "username": test_user.email,
            "password": "testpassword123"
        }
    )
    return response.json()["access_token"]


@pytest.fixture(scope="function")
def auth_headers(auth_token):
    """Get authorization headers with token"""
    return {"Authorization": f"Bearer {auth_token}"}
