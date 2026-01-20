"""
E2E test factories for creating objects via HTTP API endpoints.

These helpers are designed for end-to-end tests that need to create objects
through the API rather than directly through services.
"""

from datetime import date
from decimal import Decimal
from typing import Optional


def create_school(client, name: str = "Test School", contact_email: str = "test@school.com", contact_phone: str = "+1234567890"):
    """Create a school via API endpoint"""
    response = client.post(
        "/api/v1/schools",
        json={
            "name": name,
            "contact_email": contact_email,
            "contact_phone": contact_phone
        }
    )
    assert response.status_code == 201, f"Failed to create school: {response.json()}"
    return response.json()


def create_student(
    client,
    school_id: int,
    first_name: str = "John",
    last_name: str = "Doe",
    email: str = "john@student.com",
    enrollment_date: Optional[date] = None
):
    """Create a student via API endpoint"""
    if enrollment_date is None:
        enrollment_date = date(2024, 1, 15)

    response = client.post(
        "/api/v1/students",
        json={
            "school_id": school_id,
            "first_name": first_name,
            "last_name": last_name,
            "email": email,
            "enrollment_date": enrollment_date.isoformat()
        }
    )
    assert response.status_code == 201, f"Failed to create student: {response.json()}"
    return response.json()


def create_invoice(
    client,
    student_id: int,
    issue_date: Optional[date] = None,
    due_date: Optional[date] = None,
    items: Optional[list] = None
):
    """Create an invoice via API endpoint"""
    if issue_date is None:
        issue_date = date(2024, 1, 20)
    if due_date is None:
        due_date = date(2024, 2, 20)
    if items is None:
        items = [
            {
                "description": "Tuition",
                "quantity": 1,
                "unit_price": "1000.00"
            }
        ]

    response = client.post(
        "/api/v1/invoices",
        json={
            "student_id": student_id,
            "issue_date": issue_date.isoformat(),
            "due_date": due_date.isoformat(),
            "items": items
        }
    )
    assert response.status_code == 201, f"Failed to create invoice: {response.json()}"
    return response.json()


def create_payment(
    client,
    invoice_id: int,
    amount: Optional[Decimal] = None,
    payment_date: Optional[date] = None,
    payment_method: str = "cash"
):
    """Create a payment via API endpoint"""
    if amount is None:
        amount = Decimal("500.00")
    if payment_date is None:
        payment_date = date(2024, 1, 25)

    response = client.post(
        f"/api/v1/invoices/{invoice_id}/payments",
        json={
            "payment_date": payment_date.isoformat(),
            "amount": str(amount),
            "payment_method": payment_method
        }
    )
    assert response.status_code == 201, f"Failed to create payment: {response.json()}"
    return response.json()
