import pytest


def create_test_student(client):
    """Helper to create a test student"""
    school_response = client.post("/api/v1/schools/", json={
        "name": "Test School",
        "contact_email": "test@school.com",
        "contact_phone": "+1234567890"
    })
    school_id = school_response.json()["id"]

    student_response = client.post("/api/v1/students/", json={
        "school_id": school_id,
        "first_name": "John",
        "last_name": "Doe",
        "email": "john@student.com",
        "enrollment_date": "2024-01-15"
    })
    return student_response.json()


def test_create_invoice_endpoint(client):
    """Test POST /api/v1/invoices/"""
    student = create_test_student(client)

    response = client.post("/api/v1/invoices/", json={
        "student_id": student["id"],
        "issue_date": "2024-01-20",
        "due_date": "2024-02-20",
        "items": [
            {"description": "Tuition", "quantity": 1, "unit_price": "10000.00"},
            {"description": "Books", "quantity": 3, "unit_price": "500.00"}
        ]
    })

    assert response.status_code == 201
    data = response.json()
    assert data["student_id"] == student["id"]
    assert data["total_amount"] == "11500.00"  # 10000 + (3 * 500)
    assert data["status"] == "pending"
    assert len(data["items"]) == 2


def test_list_invoices_endpoint(client):
    """Test GET /api/v1/invoices/"""
    student = create_test_student(client)

    # Create two invoices
    client.post("/api/v1/invoices/", json={
        "student_id": student["id"],
        "issue_date": "2024-01-20",
        "due_date": "2024-02-20",
        "items": [{"description": "Item", "quantity": 1, "unit_price": "100.00"}]
    })
    client.post("/api/v1/invoices/", json={
        "student_id": student["id"],
        "issue_date": "2024-02-01",
        "due_date": "2024-03-01",
        "items": [{"description": "Item", "quantity": 1, "unit_price": "200.00"}]
    })

    response = client.get("/api/v1/invoices/")

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2


def test_get_invoice_by_id_endpoint(client):
    """Test GET /api/v1/invoices/{invoice_id}"""
    student = create_test_student(client)

    create_response = client.post("/api/v1/invoices/", json={
        "student_id": student["id"],
        "issue_date": "2024-01-20",
        "due_date": "2024-02-20",
        "items": [{"description": "Item", "quantity": 1, "unit_price": "100.00"}]
    })
    invoice_id = create_response.json()["id"]

    response = client.get(f"/api/v1/invoices/{invoice_id}")

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == invoice_id


def test_update_invoice_endpoint(client):
    """Test PUT /api/v1/invoices/{invoice_id}"""
    student = create_test_student(client)

    create_response = client.post("/api/v1/invoices/", json={
        "student_id": student["id"],
        "issue_date": "2024-01-20",
        "due_date": "2024-02-20",
        "items": [{"description": "Item", "quantity": 1, "unit_price": "100.00"}]
    })
    invoice_id = create_response.json()["id"]

    response = client.put(f"/api/v1/invoices/{invoice_id}", json={
        "due_date": "2024-03-15"
    })

    assert response.status_code == 200
    data = response.json()
    assert data["due_date"] == "2024-03-15"


def test_cancel_invoice_endpoint(client):
    """Test POST /api/v1/invoices/{invoice_id}/cancel"""
    student = create_test_student(client)

    create_response = client.post("/api/v1/invoices/", json={
        "student_id": student["id"],
        "issue_date": "2024-01-20",
        "due_date": "2024-02-20",
        "items": [{"description": "Item", "quantity": 1, "unit_price": "100.00"}]
    })
    invoice_id = create_response.json()["id"]

    response = client.post(f"/api/v1/invoices/{invoice_id}/cancel")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "cancelled"


def test_add_item_to_invoice_endpoint(client):
    """Test POST /api/v1/invoices/{invoice_id}/items"""
    student = create_test_student(client)

    create_response = client.post("/api/v1/invoices/", json={
        "student_id": student["id"],
        "issue_date": "2024-01-20",
        "due_date": "2024-02-20",
        "items": [{"description": "Original Item", "quantity": 1, "unit_price": "100.00"}]
    })
    invoice_id = create_response.json()["id"]

    # Add a new item
    response = client.post(f"/api/v1/invoices/{invoice_id}/items", json={
        "description": "New Item",
        "quantity": 2,
        "unit_price": "50.00"
    })

    assert response.status_code == 201
    data = response.json()
    assert data["description"] == "New Item"
    assert data["total_amount"] == "100.00"  # 2 * 50

    # Verify invoice total was recalculated
    invoice_response = client.get(f"/api/v1/invoices/{invoice_id}")
    assert invoice_response.json()["total_amount"] == "200.00"  # 100 + 100


def test_update_item_in_invoice_endpoint(client):
    """Test PATCH /api/v1/invoices/{invoice_id}/items/{item_id}"""
    student = create_test_student(client)

    create_response = client.post("/api/v1/invoices/", json={
        "student_id": student["id"],
        "issue_date": "2024-01-20",
        "due_date": "2024-02-20",
        "items": [
            {"description": "Item 1", "quantity": 1, "unit_price": "100.00"},
            {"description": "Item 2", "quantity": 1, "unit_price": "50.00"}
        ]
    })
    invoice = create_response.json()
    invoice_id = invoice["id"]
    item_id = invoice["items"][0]["id"]

    # Update the first item
    response = client.patch(f"/api/v1/invoices/{invoice_id}/items/{item_id}", json={
        "description": "Updated Item",
        "quantity": 3,
        "unit_price": "200.00"
    })

    assert response.status_code == 200
    data = response.json()
    assert data["description"] == "Updated Item"
    assert data["total_amount"] == "600.00"  # 3 * 200

    # Verify invoice total was recalculated
    invoice_response = client.get(f"/api/v1/invoices/{invoice_id}")
    assert invoice_response.json()["total_amount"] == "650.00"  # 600 + 50


def test_delete_item_from_invoice_endpoint(client):
    """Test DELETE /api/v1/invoices/{invoice_id}/items/{item_id}"""
    student = create_test_student(client)

    create_response = client.post("/api/v1/invoices/", json={
        "student_id": student["id"],
        "issue_date": "2024-01-20",
        "due_date": "2024-02-20",
        "items": [
            {"description": "Item 1", "quantity": 1, "unit_price": "100.00"},
            {"description": "Item 2", "quantity": 1, "unit_price": "50.00"}
        ]
    })
    invoice = create_response.json()
    invoice_id = invoice["id"]
    item_id = invoice["items"][0]["id"]

    # Delete the first item
    response = client.delete(f"/api/v1/invoices/{invoice_id}/items/{item_id}")

    assert response.status_code == 204

    # Verify invoice total was recalculated
    invoice_response = client.get(f"/api/v1/invoices/{invoice_id}")
    assert invoice_response.json()["total_amount"] == "50.00"  # Only item 2 remains


def test_cannot_delete_last_item_endpoint(client):
    """Test that you cannot delete the last item from an invoice"""
    student = create_test_student(client)

    create_response = client.post("/api/v1/invoices/", json={
        "student_id": student["id"],
        "issue_date": "2024-01-20",
        "due_date": "2024-02-20",
        "items": [{"description": "Only Item", "quantity": 1, "unit_price": "100.00"}]
    })
    invoice = create_response.json()
    invoice_id = invoice["id"]
    item_id = invoice["items"][0]["id"]

    # Try to delete the only item
    response = client.delete(f"/api/v1/invoices/{invoice_id}/items/{item_id}")

    assert response.status_code == 400
    assert "Cannot delete last invoice item" in response.json()["detail"]


def test_get_nonexistent_invoice_endpoint(client):
    """Test GET /api/v1/invoices/{invoice_id} with invalid ID"""
    response = client.get("/api/v1/invoices/999")

    assert response.status_code == 404
    assert response.json()["detail"] == "Invoice not found"


def test_update_nonexistent_invoice(client):
    """Test PUT /api/v1/invoices/{invoice_id} with invalid ID"""
    response = client.put("/api/v1/invoices/999", json={
        "due_date": "2024-03-15"
    })

    assert response.status_code == 404


def test_cancel_nonexistent_invoice(client):
    """Test POST /api/v1/invoices/{invoice_id}/cancel with invalid ID"""
    response = client.post("/api/v1/invoices/999/cancel")

    assert response.status_code == 404


def test_add_item_to_nonexistent_invoice(client):
    """Test POST /api/v1/invoices/{invoice_id}/items with invalid invoice ID"""
    response = client.post("/api/v1/invoices/999/items", json={
        "description": "Item",
        "quantity": 1,
        "unit_price": "100.00"
    })

    assert response.status_code == 404


def test_update_nonexistent_item(client):
    """Test PATCH /api/v1/invoices/{invoice_id}/items/{item_id} with invalid item ID"""
    student = create_test_student(client)

    create_response = client.post("/api/v1/invoices/", json={
        "student_id": student["id"],
        "issue_date": "2024-01-20",
        "due_date": "2024-02-20",
        "items": [{"description": "Item", "quantity": 1, "unit_price": "100.00"}]
    })
    invoice_id = create_response.json()["id"]

    response = client.patch(f"/api/v1/invoices/{invoice_id}/items/999", json={
        "description": "Updated",
        "quantity": 1,
        "unit_price": "200.00"
    })

    assert response.status_code == 404

