import pytest


def create_test_data(client):
    """Helper to create test data"""
    school_response = client.post("/api/v1/schools/", json={
        "name": "Test School",
        "contact_email": "test@school.com",
        "contact_phone": "+1234567890"
    })
    school = school_response.json()

    student_response = client.post("/api/v1/students/", json={
        "school_id": school["id"],
        "first_name": "John",
        "last_name": "Doe",
        "email": "john@student.com",
        "enrollment_date": "2024-01-15"
    })
    student = student_response.json()

    return school, student


def test_student_statement_endpoint(client):
    """Test GET /api/v1/students/{student_id}/account-statement"""
    school, student = create_test_data(client)

    # Create invoice with payment
    invoice_response = client.post("/api/v1/invoices/", json={
        "student_id": student["id"],
        "issue_date": "2024-01-20",
        "due_date": "2024-02-20",
        "items": [{"description": "Tuition", "quantity": 1, "unit_price": "1000.00"}]
    })
    invoice = invoice_response.json()

    client.post(f"/api/v1/invoices/{invoice['id']}/payments", json={
        "payment_date": "2024-01-25",
        "amount": "600.00",
        "payment_method": "cash"
    })

    response = client.get(f"/api/v1/students/{student['id']}/account-statement")

    assert response.status_code == 200
    data = response.json()
    assert data["student_id"] == student["id"]
    assert data["student_name"] == "John Doe"
    assert data["school_id"] == school["id"]
    assert data["school_name"] == "Test School"
    assert data["total_invoiced"] == "1000.00"
    assert data["total_paid"] == "600.00"
    assert data["total_pending"] == "400.00"
    assert len(data["invoices"]) == 1


def test_student_statement_multiple_invoices_endpoint(client):
    """Test student statement with multiple invoices"""
    school, student = create_test_data(client)

    # Create two invoices
    invoice1_response = client.post("/api/v1/invoices/", json={
        "student_id": student["id"],
        "issue_date": "2024-01-20",
        "due_date": "2024-02-20",
        "items": [{"description": "Tuition", "quantity": 1, "unit_price": "1000.00"}]
    })
    invoice1 = invoice1_response.json()

    invoice2_response = client.post("/api/v1/invoices/", json={
        "student_id": student["id"],
        "issue_date": "2024-02-01",
        "due_date": "2024-03-01",
        "items": [{"description": "Books", "quantity": 1, "unit_price": "500.00"}]
    })
    invoice2 = invoice2_response.json()

    # Make payments
    client.post(f"/api/v1/invoices/{invoice1['id']}/payments", json={
        "payment_date": "2024-01-25",
        "amount": "1000.00",
        "payment_method": "cash"
    })
    client.post(f"/api/v1/invoices/{invoice2['id']}/payments", json={
        "payment_date": "2024-02-05",
        "amount": "200.00",
        "payment_method": "cash"
    })

    response = client.get(f"/api/v1/students/{student['id']}/account-statement")

    assert response.status_code == 200
    data = response.json()
    assert data["total_invoiced"] == "1500.00"
    assert data["total_paid"] == "1200.00"
    assert data["total_pending"] == "300.00"
    assert len(data["invoices"]) == 2


def test_student_statement_excludes_cancelled_endpoint(client):
    """Test that student statement excludes cancelled invoices"""
    school, student = create_test_data(client)

    # Create two invoices
    invoice1_response = client.post("/api/v1/invoices/", json={
        "student_id": student["id"],
        "issue_date": "2024-01-20",
        "due_date": "2024-02-20",
        "items": [{"description": "Invoice 1", "quantity": 1, "unit_price": "5000.00"}]
    })
    invoice1 = invoice1_response.json()

    invoice2_response = client.post("/api/v1/invoices/", json={
        "student_id": student["id"],
        "issue_date": "2024-02-01",
        "due_date": "2024-03-01",
        "items": [{"description": "Invoice 2", "quantity": 1, "unit_price": "1000.00"}]
    })

    # Cancel the first invoice
    client.post(f"/api/v1/invoices/{invoice1['id']}/cancel")

    response = client.get(f"/api/v1/students/{student['id']}/account-statement")

    # Should only include invoice2
    assert response.status_code == 200
    data = response.json()
    assert data["total_invoiced"] == "1000.00"
    assert len(data["invoices"]) == 1


def test_student_statement_nonexistent_endpoint(client):
    """Test student statement for non-existent student"""
    response = client.get("/api/v1/students/999/account-statement")

    assert response.status_code == 404
    assert response.json()["detail"] == "Student not found"


def test_school_statement_endpoint(client):
    """Test GET /api/v1/schools/{school_id}/account-statement"""
    school, student = create_test_data(client)

    # Create invoice with payment
    invoice_response = client.post("/api/v1/invoices/", json={
        "student_id": student["id"],
        "issue_date": "2024-01-20",
        "due_date": "2024-02-20",
        "items": [{"description": "Tuition", "quantity": 1, "unit_price": "1000.00"}]
    })
    invoice = invoice_response.json()

    client.post(f"/api/v1/invoices/{invoice['id']}/payments", json={
        "payment_date": "2024-01-25",
        "amount": "400.00",
        "payment_method": "cash"
    })

    response = client.get(f"/api/v1/schools/{school['id']}/account-statement")

    assert response.status_code == 200
    data = response.json()
    assert data["school_id"] == school["id"]
    assert data["school_name"] == "Test School"
    assert data["student_count"] == 1
    assert data["total_invoiced"] == "1000.00"
    assert data["total_paid"] == "400.00"
    assert data["total_pending"] == "600.00"


def test_school_statement_multiple_students_endpoint(client):
    """Test school statement aggregates across multiple students"""
    school, student1 = create_test_data(client)

    # Create another student
    student2_response = client.post("/api/v1/students/", json={
        "school_id": school["id"],
        "first_name": "Jane",
        "last_name": "Smith",
        "email": "jane@student.com",
        "enrollment_date": "2024-01-15"
    })
    student2 = student2_response.json()

    # Create invoices for both students
    invoice1_response = client.post("/api/v1/invoices/", json={
        "student_id": student1["id"],
        "issue_date": "2024-01-20",
        "due_date": "2024-02-20",
        "items": [{"description": "Tuition", "quantity": 1, "unit_price": "1000.00"}]
    })
    invoice1 = invoice1_response.json()

    invoice2_response = client.post("/api/v1/invoices/", json={
        "student_id": student2["id"],
        "issue_date": "2024-01-20",
        "due_date": "2024-02-20",
        "items": [{"description": "Tuition", "quantity": 1, "unit_price": "1200.00"}]
    })
    invoice2 = invoice2_response.json()

    # Make payments
    client.post(f"/api/v1/invoices/{invoice1['id']}/payments", json={
        "payment_date": "2024-01-25",
        "amount": "500.00",
        "payment_method": "cash"
    })
    client.post(f"/api/v1/invoices/{invoice2['id']}/payments", json={
        "payment_date": "2024-01-25",
        "amount": "1200.00",
        "payment_method": "cash"
    })

    response = client.get(f"/api/v1/schools/{school['id']}/account-statement")

    assert response.status_code == 200
    data = response.json()
    assert data["student_count"] == 2
    assert data["total_invoiced"] == "2200.00"
    assert data["total_paid"] == "1700.00"
    assert data["total_pending"] == "500.00"


def test_school_statement_excludes_cancelled_endpoint(client):
    """Test that school statement excludes cancelled invoices"""
    school, student = create_test_data(client)

    # Create two invoices
    invoice1_response = client.post("/api/v1/invoices/", json={
        "student_id": student["id"],
        "issue_date": "2024-01-20",
        "due_date": "2024-02-20",
        "items": [{"description": "Invoice 1", "quantity": 1, "unit_price": "5000.00"}]
    })
    invoice1 = invoice1_response.json()

    invoice2_response = client.post("/api/v1/invoices/", json={
        "student_id": student["id"],
        "issue_date": "2024-02-01",
        "due_date": "2024-03-01",
        "items": [{"description": "Invoice 2", "quantity": 1, "unit_price": "1000.00"}]
    })

    # Cancel the first invoice
    client.post(f"/api/v1/invoices/{invoice1['id']}/cancel")

    response = client.get(f"/api/v1/schools/{school['id']}/account-statement")

    # Should only include invoice2
    assert response.status_code == 200
    data = response.json()
    assert data["total_invoiced"] == "1000.00"
    assert len(data["invoices"]) == 1


def test_school_statement_nonexistent_endpoint(client):
    """Test school statement for non-existent school"""
    response = client.get("/api/v1/schools/999/account-statement")

    assert response.status_code == 404
    assert response.json()["detail"] == "School not found"
