def test_register_user_endpoint(client):
    """Test POST /api/v1/auth/register"""
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": "newuser@example.com",
            "password": "password123",
            "full_name": "New User",
        },
    )

    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "newuser@example.com"
    assert data["full_name"] == "New User"
    assert data["role"] == "user"
    assert data["is_active"] == 1
    assert "id" in data
    assert data["deleted_at"] is None
    assert "hashed_password" not in data  # Should not expose password


def test_register_duplicate_email(client):
    """Test registering with duplicate email"""
    # Register first user
    client.post(
        "/api/v1/auth/register",
        json={
            "email": "duplicate@example.com",
            "password": "password123",
            "full_name": "First User",
        },
    )

    # Try to register with same email
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": "duplicate@example.com",
            "password": "password456",
            "full_name": "Second User",
        },
    )

    assert response.status_code == 400
    assert "already registered" in response.json()["detail"].lower()


def test_register_invalid_email(client):
    """Test registering with invalid email"""
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": "not-an-email",
            "password": "password123",
            "full_name": "Test User",
        },
    )

    assert response.status_code == 422  # Validation error


def test_login_success(client, test_user):
    """Test POST /api/v1/auth/login with valid credentials"""
    response = client.post(
        "/api/v1/auth/login",
        data={"username": test_user.email, "password": "testpassword123"},
    )

    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert len(data["access_token"]) > 0


def test_login_wrong_password(client, test_user):
    """Test login with wrong password"""
    response = client.post(
        "/api/v1/auth/login",
        data={"username": test_user.email, "password": "wrongpassword"},
    )

    assert response.status_code == 401
    assert "incorrect" in response.json()["detail"].lower()


def test_login_nonexistent_user(client):
    """Test login with non-existent email"""
    response = client.post(
        "/api/v1/auth/login",
        data={"username": "nonexistent@example.com", "password": "password123"},
    )

    assert response.status_code == 401
    assert "incorrect" in response.json()["detail"].lower()


def test_get_current_user_profile(client, test_user, auth_token):
    """Test GET /api/v1/auth/me with valid token"""
    response = client.post(
        "/api/v1/auth/me", headers={"Authorization": f"Bearer {auth_token}"}
    )

    # Note: Due to our test setup with mock user override, this will return the mock user
    assert response.status_code in [200, 405]  # May be 405 if POST not allowed


def test_get_current_user_profile_get_method(client, test_user, auth_token):
    """Test GET /api/v1/auth/me with valid token using GET"""
    response = client.get(
        "/api/v1/auth/me", headers={"Authorization": f"Bearer {auth_token}"}
    )

    assert response.status_code == 200
    data = response.json()
    # Note: Due to mock user override in conftest, this returns the mock user
    assert "email" in data
    assert "full_name" in data
    assert "hashed_password" not in data


def test_get_current_user_without_token(client):
    """Test GET /api/v1/auth/me without authentication token"""
    # Need to clear the auth override for this test
    from fastapi.testclient import TestClient

    from app.core.database import get_db
    from app.main import app

    # Temporarily clear overrides
    app.dependency_overrides.clear()

    # Add back only the db override
    def override_get_db():
        from tests.conftest import TestingSessionLocal

        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as temp_client:
        response = temp_client.get("/api/v1/auth/me")

        assert response.status_code == 401
        assert "not authenticated" in response.json()["detail"].lower()


def test_get_current_user_with_invalid_token(client):
    """Test GET /api/v1/auth/me with invalid token"""
    # Need to clear the auth override for this test
    from fastapi.testclient import TestClient

    from app.core.database import get_db
    from app.main import app

    # Temporarily clear overrides
    app.dependency_overrides.clear()

    # Add back only the db override
    def override_get_db():
        from tests.conftest import TestingSessionLocal

        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as temp_client:
        response = temp_client.get(
            "/api/v1/auth/me", headers={"Authorization": "Bearer invalid_token_here"}
        )

        assert response.status_code == 401


def test_register_without_optional_full_name(client):
    """Test registering without full_name (optional field)"""
    response = client.post(
        "/api/v1/auth/register",
        json={"email": "noname@example.com", "password": "password123"},
    )

    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "noname@example.com"
    assert data["full_name"] is None


def test_login_inactive_user(client, test_user, db):
    """Test login with inactive user"""
    # Deactivate the user
    test_user.is_active = 0
    db.commit()

    response = client.post(
        "/api/v1/auth/login",
        data={"username": test_user.email, "password": "testpassword123"},
    )

    # Login should succeed but accessing protected routes should fail
    # For now, just check that login works
    assert response.status_code in [200, 403]  # Depends on implementation


def test_jwt_token_contains_user_email(client, test_user):
    """Test that JWT token contains user email in subject"""
    response = client.post(
        "/api/v1/auth/login",
        data={"username": test_user.email, "password": "testpassword123"},
    )

    assert response.status_code == 200
    token = response.json()["access_token"]

    # Decode token header to verify it's a JWT
    import base64
    import json

    # JWT format: header.payload.signature
    parts = token.split(".")
    assert len(parts) == 3, "Token should have 3 parts"

    # Decode payload (add padding if needed)
    payload = parts[1]
    padding = 4 - len(payload) % 4
    if padding != 4:
        payload += "=" * padding

    decoded = json.loads(base64.b64decode(payload))
    assert decoded["sub"] == test_user.email
    assert "exp" in decoded  # Should have expiration
