import pytest


def test_create_student_endpoint(client):
    """Test POST /api/v1/students/"""
    # Create a school first
    school_response = client.post("/api/v1/schools/", json={
        "name": "Test School",
        "contact_email": "test@school.com",
        "contact_phone": "+1234567890"
    })
    school_id = school_response.json()["id"]

    response = client.post("/api/v1/students/", json={
        "school_id": school_id,
        "first_name": "John",
        "last_name": "Doe",
        "email": "john.doe@student.com",
        "enrollment_date": "2024-01-15",
        "status": "active"
    })

    assert response.status_code == 201
    data = response.json()
    assert data["school_id"] == school_id
    assert data["first_name"] == "John"
    assert data["last_name"] == "Doe"
    assert data["email"] == "john.doe@student.com"
    assert data["enrollment_date"] == "2024-01-15"
    assert data["status"] == "active"
    assert "id" in data
    assert data["deleted_at"] is None


def test_list_students_endpoint(client):
    """Test GET /api/v1/students/"""
    # Create a school
    school_response = client.post("/api/v1/schools/", json={
        "name": "Test School",
        "contact_email": "test@school.com",
        "contact_phone": "+1234567890"
    })
    school_id = school_response.json()["id"]

    # Create two students
    client.post("/api/v1/students/", json={
        "school_id": school_id,
        "first_name": "John",
        "last_name": "Doe",
        "email": "john@student.com",
        "enrollment_date": "2024-01-15"
    })
    client.post("/api/v1/students/", json={
        "school_id": school_id,
        "first_name": "Jane",
        "last_name": "Smith",
        "email": "jane@student.com",
        "enrollment_date": "2024-02-01"
    })

    response = client.get("/api/v1/students/")

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert data[0]["first_name"] == "John"
    assert data[1]["first_name"] == "Jane"


def test_get_student_by_id_endpoint(client):
    """Test GET /api/v1/students/{student_id}"""
    # Create a school
    school_response = client.post("/api/v1/schools/", json={
        "name": "Test School",
        "contact_email": "test@school.com",
        "contact_phone": "+1234567890"
    })
    school_id = school_response.json()["id"]

    # Create a student
    create_response = client.post("/api/v1/students/", json={
        "school_id": school_id,
        "first_name": "John",
        "last_name": "Doe",
        "email": "john@student.com",
        "enrollment_date": "2024-01-15"
    })
    student_id = create_response.json()["id"]

    # Get the student
    response = client.get(f"/api/v1/students/{student_id}")

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == student_id
    assert data["first_name"] == "John"


def test_get_nonexistent_student_endpoint(client):
    """Test GET /api/v1/students/{student_id} with invalid ID"""
    response = client.get("/api/v1/students/999")

    assert response.status_code == 404
    assert response.json()["detail"] == "Student not found"


def test_update_student_endpoint(client):
    """Test PUT /api/v1/students/{student_id}"""
    # Create a school
    school_response = client.post("/api/v1/schools/", json={
        "name": "Test School",
        "contact_email": "test@school.com",
        "contact_phone": "+1234567890"
    })
    school_id = school_response.json()["id"]

    # Create a student
    create_response = client.post("/api/v1/students/", json={
        "school_id": school_id,
        "first_name": "John",
        "last_name": "Doe",
        "email": "john@student.com",
        "enrollment_date": "2024-01-15"
    })
    student_id = create_response.json()["id"]

    # Update the student
    response = client.put(f"/api/v1/students/{student_id}", json={
        "first_name": "Jane",
        "email": "jane@student.com"
    })

    assert response.status_code == 200
    data = response.json()
    assert data["first_name"] == "Jane"
    assert data["email"] == "jane@student.com"
    assert data["last_name"] == "Doe"  # Unchanged


def test_update_student_status_endpoint(client):
    """Test updating student status"""
    # Create a school
    school_response = client.post("/api/v1/schools/", json={
        "name": "Test School",
        "contact_email": "test@school.com",
        "contact_phone": "+1234567890"
    })
    school_id = school_response.json()["id"]

    # Create a student
    create_response = client.post("/api/v1/students/", json={
        "school_id": school_id,
        "first_name": "John",
        "last_name": "Doe",
        "email": "john@student.com",
        "enrollment_date": "2024-01-15",
        "status": "active"
    })
    student_id = create_response.json()["id"]

    # Update status to graduated
    response = client.put(f"/api/v1/students/{student_id}", json={
        "status": "graduated"
    })

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "graduated"


def test_delete_student_endpoint(client):
    """Test DELETE /api/v1/students/{student_id}"""
    # Create a school
    school_response = client.post("/api/v1/schools/", json={
        "name": "Test School",
        "contact_email": "test@school.com",
        "contact_phone": "+1234567890"
    })
    school_id = school_response.json()["id"]

    # Create a student
    create_response = client.post("/api/v1/students/", json={
        "school_id": school_id,
        "first_name": "John",
        "last_name": "Doe",
        "email": "john@student.com",
        "enrollment_date": "2024-01-15"
    })
    student_id = create_response.json()["id"]

    # Delete the student
    response = client.delete(f"/api/v1/students/{student_id}")

    assert response.status_code == 204

    # Verify it's not returned by GET
    get_response = client.get(f"/api/v1/students/{student_id}")
    assert get_response.status_code == 404


def test_list_excludes_deleted_students(client):
    """Test that GET /api/v1/students/ excludes soft-deleted students"""
    # Create a school
    school_response = client.post("/api/v1/schools/", json={
        "name": "Test School",
        "contact_email": "test@school.com",
        "contact_phone": "+1234567890"
    })
    school_id = school_response.json()["id"]

    # Create two students
    create1 = client.post("/api/v1/students/", json={
        "school_id": school_id,
        "first_name": "John",
        "last_name": "Doe",
        "email": "john@student.com",
        "enrollment_date": "2024-01-15"
    })
    create2 = client.post("/api/v1/students/", json={
        "school_id": school_id,
        "first_name": "Jane",
        "last_name": "Smith",
        "email": "jane@student.com",
        "enrollment_date": "2024-02-01"
    })
    student2_id = create2.json()["id"]

    # Delete the second student
    client.delete(f"/api/v1/students/{student2_id}")

    # List should only return the first student
    response = client.get("/api/v1/students/")
    data = response.json()

    assert response.status_code == 200
    assert len(data) == 1
    assert data[0]["first_name"] == "John"


def test_create_student_missing_fields(client):
    """Test POST /api/v1/students/ with missing required fields"""
    response = client.post("/api/v1/students/", json={
        "first_name": "John",
        "last_name": "Doe"
        # Missing school_id, email, enrollment_date
    })

    assert response.status_code == 422  # Validation error


def test_update_nonexistent_student(client):
    """Test PUT /api/v1/students/{student_id} with invalid ID"""
    response = client.put("/api/v1/students/999", json={
        "first_name": "Updated Name"
    })

    assert response.status_code == 404
    assert response.json()["detail"] == "Student not found"


def test_delete_nonexistent_student(client):
    """Test DELETE /api/v1/students/{student_id} with invalid ID"""
    response = client.delete("/api/v1/students/999")

    assert response.status_code == 404
    assert response.json()["detail"] == "Student not found"
