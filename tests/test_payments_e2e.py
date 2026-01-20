def create_test_invoice(client, total_amount="1000.00"):
    """Helper to create a test invoice"""
    school_response = client.post(
        "/api/v1/schools/",
        json={
            "name": "Test School",
            "contact_email": "test@school.com",
            "contact_phone": "+1234567890",
        },
    )
    school_id = school_response.json()["id"]

    student_response = client.post(
        "/api/v1/students/",
        json={
            "school_id": school_id,
            "first_name": "John",
            "last_name": "Doe",
            "email": "john@student.com",
            "enrollment_date": "2024-01-15",
        },
    )
    student_id = student_response.json()["id"]

    invoice_response = client.post(
        "/api/v1/invoices/",
        json={
            "student_id": student_id,
            "issue_date": "2024-01-20",
            "due_date": "2024-02-20",
            "items": [{"description": "Item", "quantity": 1, "unit_price": total_amount}],
        },
    )
    return invoice_response.json()


def test_create_payment_endpoint(client):
    """Test POST /api/v1/invoices/{invoice_id}/payments"""
    invoice = create_test_invoice(client)

    response = client.post(
        f"/api/v1/invoices/{invoice['id']}/payments",
        json={"payment_date": "2024-01-25", "amount": "500.00", "payment_method": "cash"},
    )

    assert response.status_code == 201
    data = response.json()
    assert data["invoice_id"] == invoice["id"]
    assert data["amount"] == "500.00"
    assert data["payment_method"] == "cash"
    assert "id" in data


def test_full_payment_updates_invoice_status_endpoint(client):
    """Test that a full payment updates invoice status to PAID"""
    invoice = create_test_invoice(client, "1000.00")

    client.post(
        f"/api/v1/invoices/{invoice['id']}/payments",
        json={
            "payment_date": "2024-01-25",
            "amount": "1000.00",
            "payment_method": "cash",
        },
    )

    # Check invoice status
    invoice_response = client.get(f"/api/v1/invoices/{invoice['id']}")
    assert invoice_response.json()["status"] == "paid"


def test_partial_payment_keeps_pending_status_endpoint(client):
    """Test that a partial payment keeps invoice status as PENDING"""
    invoice = create_test_invoice(client, "1000.00")

    client.post(
        f"/api/v1/invoices/{invoice['id']}/payments",
        json={"payment_date": "2024-01-25", "amount": "500.00", "payment_method": "cash"},
    )

    # Check invoice status is still pending
    invoice_response = client.get(f"/api/v1/invoices/{invoice['id']}")
    assert invoice_response.json()["status"] == "pending"


def test_multiple_payments_to_full_amount_endpoint(client):
    """Test that multiple payments totaling full amount update status to PAID"""
    invoice = create_test_invoice(client, "1000.00")

    # First payment
    client.post(
        f"/api/v1/invoices/{invoice['id']}/payments",
        json={"payment_date": "2024-01-25", "amount": "600.00", "payment_method": "cash"},
    )

    # Check still pending
    invoice_response = client.get(f"/api/v1/invoices/{invoice['id']}")
    assert invoice_response.json()["status"] == "pending"

    # Second payment completing the total
    client.post(
        f"/api/v1/invoices/{invoice['id']}/payments",
        json={"payment_date": "2024-01-26", "amount": "400.00", "payment_method": "card"},
    )

    # Check now paid
    invoice_response = client.get(f"/api/v1/invoices/{invoice['id']}")
    assert invoice_response.json()["status"] == "paid"


def test_cannot_overpay_invoice_endpoint(client):
    """Test that you cannot overpay an invoice"""
    invoice = create_test_invoice(client, "1000.00")

    response = client.post(
        f"/api/v1/invoices/{invoice['id']}/payments",
        json={
            "payment_date": "2024-01-25",
            "amount": "1500.00",
            "payment_method": "cash",
        },
    )

    assert response.status_code == 400
    assert "Payment would exceed invoice total" in response.json()["detail"]


def test_cannot_overpay_with_multiple_payments_endpoint(client):
    """Test that you cannot overpay with multiple payments"""
    invoice = create_test_invoice(client, "1000.00")

    # First payment
    client.post(
        f"/api/v1/invoices/{invoice['id']}/payments",
        json={"payment_date": "2024-01-25", "amount": "800.00", "payment_method": "cash"},
    )

    # Try to pay more than remaining
    response = client.post(
        f"/api/v1/invoices/{invoice['id']}/payments",
        json={"payment_date": "2024-01-26", "amount": "300.00", "payment_method": "cash"},
    )

    assert response.status_code == 400
    assert "Payment would exceed invoice total" in response.json()["detail"]
    assert "Remaining amount: 200" in response.json()["detail"]


def test_list_payments_for_invoice_endpoint(client):
    """Test GET /api/v1/invoices/{invoice_id}/payments"""
    invoice = create_test_invoice(client, "1000.00")

    # Create multiple payments
    client.post(
        f"/api/v1/invoices/{invoice['id']}/payments",
        json={"payment_date": "2024-01-25", "amount": "300.00", "payment_method": "cash"},
    )
    client.post(
        f"/api/v1/invoices/{invoice['id']}/payments",
        json={"payment_date": "2024-01-26", "amount": "400.00", "payment_method": "card"},
    )

    response = client.get(f"/api/v1/invoices/{invoice['id']}/payments")

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert data[0]["amount"] == "300.00"
    assert data[1]["amount"] == "400.00"


def test_create_payment_for_nonexistent_invoice(client):
    """Test POST /api/v1/invoices/{invoice_id}/payments with invalid invoice"""
    response = client.post(
        "/api/v1/invoices/999/payments",
        json={"payment_date": "2024-01-25", "amount": "500.00", "payment_method": "cash"},
    )

    assert response.status_code == 404


def test_list_payments_for_nonexistent_invoice(client):
    """Test GET /api/v1/invoices/{invoice_id}/payments with invalid invoice"""
    response = client.get("/api/v1/invoices/999/payments")

    assert response.status_code == 404


def test_create_payment_with_invalid_payment_method(client):
    """Test POST with invalid payment method"""
    invoice = create_test_invoice(client)

    response = client.post(
        f"/api/v1/invoices/{invoice['id']}/payments",
        json={
            "payment_date": "2024-01-25",
            "amount": "500.00",
            "payment_method": "invalid_method",
        },
    )

    assert response.status_code == 422  # Validation error
