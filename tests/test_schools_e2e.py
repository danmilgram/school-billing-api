import pytest


def test_create_school_endpoint(client):
    """Test POST /api/v1/schools/"""
    response = client.post(
        "/api/v1/schools/",
        json={
            "name": "Test School",
            "contact_email": "test@school.com",
            "contact_phone": "+1234567890"
        }
    )

    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Test School"
    assert data["contact_email"] == "test@school.com"
    assert data["contact_phone"] == "+1234567890"
    assert "id" in data
    assert data["deleted_at"] is None


def test_list_schools_endpoint(client):
    """Test GET /api/v1/schools/"""
    # Create two schools
    client.post("/api/v1/schools/", json={
        "name": "School 1",
        "contact_email": "school1@test.com",
        "contact_phone": "+1111111111"
    })
    client.post("/api/v1/schools/", json={
        "name": "School 2",
        "contact_email": "school2@test.com",
        "contact_phone": "+2222222222"
    })

    response = client.get("/api/v1/schools/")

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert data[0]["name"] == "School 1"
    assert data[1]["name"] == "School 2"


def test_get_school_by_id_endpoint(client):
    """Test GET /api/v1/schools/{school_id}"""
    # Create a school
    create_response = client.post("/api/v1/schools/", json={
        "name": "Test School",
        "contact_email": "test@school.com",
        "contact_phone": "+1234567890"
    })
    school_id = create_response.json()["id"]

    # Get the school
    response = client.get(f"/api/v1/schools/{school_id}")

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == school_id
    assert data["name"] == "Test School"


def test_get_nonexistent_school_endpoint(client):
    """Test GET /api/v1/schools/{school_id} with invalid ID"""
    response = client.get("/api/v1/schools/999")

    assert response.status_code == 404
    assert response.json()["detail"] == "School not found"


def test_update_school_endpoint(client):
    """Test PUT /api/v1/schools/{school_id}"""
    # Create a school
    create_response = client.post("/api/v1/schools/", json={
        "name": "Original Name",
        "contact_email": "original@test.com",
        "contact_phone": "+1111111111"
    })
    school_id = create_response.json()["id"]

    # Update the school
    response = client.put(f"/api/v1/schools/{school_id}", json={
        "name": "Updated Name",
        "contact_email": "updated@test.com"
    })

    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Updated Name"
    assert data["contact_email"] == "updated@test.com"
    assert data["contact_phone"] == "+1111111111"  # Unchanged


def test_delete_school_endpoint(client):
    """Test DELETE /api/v1/schools/{school_id}"""
    # Create a school
    create_response = client.post("/api/v1/schools/", json={
        "name": "To Delete",
        "contact_email": "delete@test.com",
        "contact_phone": "+1234567890"
    })
    school_id = create_response.json()["id"]

    # Delete the school
    response = client.delete(f"/api/v1/schools/{school_id}")

    assert response.status_code == 204

    # Verify it's not returned by GET
    get_response = client.get(f"/api/v1/schools/{school_id}")
    assert get_response.status_code == 404


def test_list_excludes_deleted_schools(client):
    """Test that GET /api/v1/schools/ excludes soft-deleted schools"""
    # Create two schools
    create1 = client.post("/api/v1/schools/", json={
        "name": "Active School",
        "contact_email": "active@test.com",
        "contact_phone": "+1111111111"
    })
    create2 = client.post("/api/v1/schools/", json={
        "name": "Deleted School",
        "contact_email": "deleted@test.com",
        "contact_phone": "+2222222222"
    })
    school2_id = create2.json()["id"]

    # Delete the second school
    client.delete(f"/api/v1/schools/{school2_id}")

    # List should only return the first school
    response = client.get("/api/v1/schools/")
    data = response.json()

    assert response.status_code == 200
    assert len(data) == 1
    assert data[0]["name"] == "Active School"


def test_create_school_missing_fields(client):
    """Test POST /api/v1/schools/ with missing required fields"""
    response = client.post("/api/v1/schools/", json={
        "name": "Incomplete School"
        # Missing contact_email and contact_phone
    })

    assert response.status_code == 422  # Validation error


def test_update_nonexistent_school(client):
    """Test PUT /api/v1/schools/{school_id} with invalid ID"""
    response = client.put("/api/v1/schools/999", json={
        "name": "Updated Name"
    })

    assert response.status_code == 404
    assert response.json()["detail"] == "School not found"


def test_delete_nonexistent_school(client):
    """Test DELETE /api/v1/schools/{school_id} with invalid ID"""
    response = client.delete("/api/v1/schools/999")

    assert response.status_code == 404
    assert response.json()["detail"] == "School not found"
