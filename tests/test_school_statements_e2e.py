import pytest
from datetime import date
from tests.factories import create_school, create_student, create_invoice, create_payment


def test_school_statement_endpoint(client):
    """Test GET /api/v1/schools/{school_id}/account-statement with date range"""
    school = create_school(client)
    student = create_student(client, school["id"])

    # Create invoice with payment
    invoice = create_invoice(client, student["id"])
    create_payment(client, invoice["id"], amount="400.00")

    response = client.get(
        f"/api/v1/schools/{school['id']}/account-statement",
        params={"start_date": "2024-01-01", "end_date": "2024-12-31", "include_invoices": "true"}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["school_id"] == school["id"]
    assert data["school_name"] == "Test School"
    assert data["period"]["start_date"] == "2024-01-01"
    assert data["period"]["end_date"] == "2024-12-31"
    assert data["student_count"] == 1
    assert data["summary"]["total_invoiced"] == "1000.00"
    assert data["summary"]["total_paid"] == "400.00"
    assert data["summary"]["total_pending"] == "600.00"
    assert len(data["invoices"]) == 1
    assert data["invoices"][0]["invoice_id"] == invoice["id"]
    assert data["invoices"][0]["total_amount"] == "1000.00"
    assert data["invoices"][0]["paid_amount"] == "400.00"
    assert data["invoices"][0]["pending_amount"] == "600.00"


def test_school_statement_multiple_students_endpoint(client):
    """Test school statement aggregates across multiple students"""
    school = create_school(client)
    student1 = create_student(client, school["id"])
    student2 = create_student(
        client,
        school["id"],
        first_name="Jane",
        last_name="Smith",
        email="jane@student.com"
    )

    # Create invoices for both students
    invoice1 = create_invoice(client, student1["id"])
    invoice2 = create_invoice(
        client,
        student2["id"],
        items=[{"description": "Tuition", "quantity": 1, "unit_price": "1200.00"}]
    )

    # Make payments
    create_payment(client, invoice1["id"], amount="500.00")
    create_payment(client, invoice2["id"], amount="1200.00")

    response = client.get(
        f"/api/v1/schools/{school['id']}/account-statement",
        params={"start_date": "2024-01-01", "end_date": "2024-12-31", "include_invoices": "true"}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["student_count"] == 2
    assert data["summary"]["total_invoiced"] == "2200.00"
    assert data["summary"]["total_paid"] == "1700.00"
    assert data["summary"]["total_pending"] == "500.00"


def test_school_statement_excludes_cancelled_endpoint(client):
    """Test that school statement excludes cancelled invoices"""
    school = create_school(client)
    student = create_student(client, school["id"])

    # Create two invoices
    invoice1 = create_invoice(
        client,
        student["id"],
        items=[{"description": "Invoice 1", "quantity": 1, "unit_price": "5000.00"}]
    )
    invoice2 = create_invoice(
        client,
        student["id"],
        issue_date=date(2024, 2, 1),
        due_date=date(2024, 3, 1),
        items=[{"description": "Invoice 2", "quantity": 1, "unit_price": "1000.00"}]
    )

    # Cancel the first invoice
    client.post(f"/api/v1/invoices/{invoice1['id']}/cancel")

    response = client.get(
        f"/api/v1/schools/{school['id']}/account-statement",
        params={"start_date": "2024-01-01", "end_date": "2024-12-31", "include_invoices": "true"}
    )

    # Should only include invoice2
    assert response.status_code == 200
    data = response.json()
    assert data["summary"]["total_invoiced"] == "1000.00"
    assert len(data["invoices"]) == 1


def test_school_statement_nonexistent_endpoint(client):
    """Test school statement for non-existent school"""
    response = client.get(
        "/api/v1/schools/999/account-statement",
        params={"start_date": "2024-01-01", "end_date": "2024-12-31"}
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "School not found"


def test_school_statement_date_filtering(client):
    """Test that school statement correctly filters by date range"""
    school = create_school(client)
    student = create_student(client, school["id"])

    # Create invoices with different dates
    create_invoice(
        client,
        student["id"],
        issue_date=date(2024, 1, 15),
        due_date=date(2024, 2, 15),
        items=[{"description": "January Invoice", "quantity": 1, "unit_price": "1000.00"}]
    )

    create_invoice(
        client,
        student["id"],
        issue_date=date(2024, 2, 15),
        due_date=date(2024, 3, 15),
        items=[{"description": "February Invoice", "quantity": 1, "unit_price": "2000.00"}]
    )

    create_invoice(
        client,
        student["id"],
        issue_date=date(2024, 3, 15),
        due_date=date(2024, 4, 15),
        items=[{"description": "March Invoice", "quantity": 1, "unit_price": "1500.00"}]
    )

    # Query for January-February only
    response = client.get(
        f"/api/v1/schools/{school['id']}/account-statement",
        params={"start_date": "2024-01-01", "end_date": "2024-02-28", "include_invoices": "true"}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["summary"]["total_invoiced"] == "3000.00"  # Only Jan + Feb invoices
    assert len(data["invoices"]) == 2

    # Query for all dates
    response_all = client.get(
        f"/api/v1/schools/{school['id']}/account-statement",
        params={"start_date": "2024-01-01", "end_date": "2024-12-31", "include_invoices": "true"}
    )

    assert response_all.status_code == 200
    data_all = response_all.json()
    assert data_all["summary"]["total_invoiced"] == "4500.00"  # All three invoices
    assert len(data_all["invoices"]) == 3


def test_school_statement_requires_date_params(client):
    """Test that school statement endpoint requires both start_date and end_date"""
    school = create_school(client)
    create_student(client, school["id"])

    # Missing both params
    response1 = client.get(f"/api/v1/schools/{school['id']}/account-statement")
    assert response1.status_code == 422  # Validation error

    # Missing end_date
    response2 = client.get(
        f"/api/v1/schools/{school['id']}/account-statement",
        params={"start_date": "2024-01-01"}
    )
    assert response2.status_code == 422  # Validation error

    # Missing start_date
    response3 = client.get(
        f"/api/v1/schools/{school['id']}/account-statement",
        params={"end_date": "2024-12-31"}
    )
    assert response3.status_code == 422  # Validation error


def test_school_statement_include_invoices_true(client):
    """Test that school statement includes invoices when include_invoices=true"""
    school = create_school(client)
    student = create_student(client, school["id"])

    # Create an invoice
    create_invoice(
        client,
        student["id"],
        issue_date=date(2024, 1, 15),
        due_date=date(2024, 2, 15),
        items=[{"description": "Test Invoice", "quantity": 1, "unit_price": "1000.00"}]
    )

    response = client.get(
        f"/api/v1/schools/{school['id']}/account-statement",
        params={"start_date": "2024-01-01", "end_date": "2024-12-31", "include_invoices": "true"}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["invoices"] is not None
    assert len(data["invoices"]) == 1
    assert data["invoices"][0]["invoice_id"] is not None
    assert data["summary"]["total_invoiced"] == "1000.00"


def test_school_statement_include_invoices_false(client):
    """Test that school statement excludes invoices when include_invoices=false"""
    school = create_school(client)
    student = create_student(client, school["id"])

    # Create an invoice
    create_invoice(
        client,
        student["id"],
        issue_date=date(2024, 1, 15),
        due_date=date(2024, 2, 15),
        items=[{"description": "Test Invoice", "quantity": 1, "unit_price": "1000.00"}]
    )

    response = client.get(
        f"/api/v1/schools/{school['id']}/account-statement",
        params={"start_date": "2024-01-01", "end_date": "2024-12-31", "include_invoices": "false"}
    )

    assert response.status_code == 200
    data = response.json()
    assert "invoices" not in data  # Key should not be present
    assert data["summary"]["total_invoiced"] == "1000.00"  # Summary should still be calculated


def test_school_statement_default_excludes_invoices(client):
    """Test that school statement excludes invoices by default (when param not specified)"""
    school = create_school(client)
    student = create_student(client, school["id"])

    # Create an invoice
    create_invoice(
        client,
        student["id"],
        issue_date=date(2024, 1, 15),
        due_date=date(2024, 2, 15),
        items=[{"description": "Test Invoice", "quantity": 1, "unit_price": "1000.00"}]
    )

    response = client.get(
        f"/api/v1/schools/{school['id']}/account-statement",
        params={"start_date": "2024-01-01", "end_date": "2024-12-31"}
    )

    assert response.status_code == 200
    data = response.json()
    assert "invoices" not in data  # Key should not be present
    assert data["summary"]["total_invoiced"] == "1000.00"  # Summary should still be calculated
