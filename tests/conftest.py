from datetime import date
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.auth import get_current_user
from app.core.database import Base, get_db
from app.main import app
from app.models.user import User, UserRole
from app.schemas.invoice import InvoiceCreate, InvoiceItemCreate
from app.schemas.payment import PaymentCreate
from app.schemas.school import SchoolCreate
from app.schemas.student import StudentCreate
from app.schemas.user import UserCreate
from app.services.invoice_service import InvoiceService
from app.services.payment_service import PaymentService
from app.services.school_service import SchoolService
from app.services.student_service import StudentService
from app.services.user_service import UserService

# Test database URL (use in-memory SQLite for fast tests)
TEST_DATABASE_URL = "sqlite:///./test.db"

# Create test engine
engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
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

    # Create a mock admin user for authenticated requests
    # Using ADMIN role so existing tests can access admin-only endpoints
    from datetime import datetime, timezone

    mock_user = User(
        id=999,
        email="admin@example.com",
        hashed_password="fake_hash",
        full_name="Test Admin",
        role=UserRole.ADMIN,
        is_active=1,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
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
        email="testuser@example.com", password="testpassword123", full_name="Test User"
    )
    user = UserService.create(user_data, db)
    return user


@pytest.fixture(scope="function")
def auth_token(client, test_user):
    """Get an authentication token for the test user"""
    response = client.post(
        "/api/v1/auth/login",
        data={"username": test_user.email, "password": "testpassword123"},
    )
    return response.json()["access_token"]


@pytest.fixture(scope="function")
def auth_headers(auth_token):
    """Get authorization headers with token"""
    return {"Authorization": f"Bearer {auth_token}"}


@pytest.fixture(scope="function")
def regular_user_client(db):
    """Create a test client with regular (non-admin) user authentication"""

    def override_get_db():
        try:
            yield db
        finally:
            pass

    # Create a mock regular user (non-admin)
    from datetime import datetime, timezone

    mock_user = User(
        id=888,
        email="user@example.com",
        hashed_password="fake_hash",
        full_name="Regular User",
        role=UserRole.USER,
        is_active=1,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )

    def override_get_current_user():
        return mock_user

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = override_get_current_user

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


# Domain object fixtures for service-level tests


@pytest.fixture(scope="function")
def test_school(db):
    """Create a test school"""
    school_data = SchoolCreate(
        name="Test School", contact_email="test@school.com", contact_phone="+1234567890"
    )
    return SchoolService.create(school_data, db)


@pytest.fixture(scope="function")
def test_student(db, test_school):
    """Create a test student"""
    student_data = StudentCreate(
        school_id=test_school.id,
        first_name="John",
        last_name="Doe",
        email="john@student.com",
        enrollment_date=date(2024, 1, 15),
    )
    return StudentService.create(student_data, db)


@pytest.fixture(scope="function")
def test_invoice(db, test_student):
    """Create a test invoice"""
    invoice_data = InvoiceCreate(
        student_id=test_student.id,
        issue_date=date(2024, 1, 20),
        due_date=date(2024, 2, 20),
        items=[
            InvoiceItemCreate(
                description="Tuition", quantity=1, unit_price=Decimal("1000.00")
            )
        ],
    )
    return InvoiceService.create(invoice_data, db)


@pytest.fixture(scope="function")
def test_payment(db, test_invoice):
    """Create a test payment"""
    payment_data = PaymentCreate(
        payment_date=date(2024, 1, 25), amount=Decimal("500.00"), payment_method="cash"
    )
    return PaymentService.create(test_invoice, payment_data, db)


# Factory fixtures for creating variations


@pytest.fixture(scope="function")
def school_factory(db):
    """Factory for creating schools with custom data"""

    def _create_school(**kwargs):
        defaults = {
            "name": "Test School",
            "contact_email": "test@school.com",
            "contact_phone": "+1234567890",
        }
        defaults.update(kwargs)
        return SchoolService.create(SchoolCreate(**defaults), db)

    return _create_school


@pytest.fixture(scope="function")
def student_factory(db):
    """Factory for creating students with custom data"""

    def _create_student(school_id, **kwargs):
        defaults = {
            "school_id": school_id,
            "first_name": "John",
            "last_name": "Doe",
            "email": "john@student.com",
            "enrollment_date": date(2024, 1, 15),
        }
        defaults.update(kwargs)
        return StudentService.create(StudentCreate(**defaults), db)

    return _create_student


@pytest.fixture(scope="function")
def invoice_factory(db):
    """Factory for creating invoices with custom data"""

    def _create_invoice(student_id, **kwargs):
        defaults = {
            "student_id": student_id,
            "issue_date": date(2024, 1, 20),
            "due_date": date(2024, 2, 20),
            "items": [
                InvoiceItemCreate(
                    description="Tuition", quantity=1, unit_price=Decimal("1000.00")
                )
            ],
        }
        defaults.update(kwargs)
        return InvoiceService.create(InvoiceCreate(**defaults), db)

    return _create_invoice


@pytest.fixture(scope="function")
def payment_factory(db):
    """Factory for creating payments with custom data"""

    def _create_payment(invoice, **kwargs):
        defaults = {
            "payment_date": date(2024, 1, 25),
            "amount": Decimal("500.00"),
            "payment_method": "cash",
        }
        defaults.update(kwargs)
        return PaymentService.create(invoice, PaymentCreate(**defaults), db)

    return _create_payment
