import pytest


def test_regular_user_cannot_create_school(regular_user_client):
    """Test that regular users cannot create schools (admin-only)"""
    response = regular_user_client.post(
        "/api/v1/schools/",
        json={
            "name": "Test School",
            "contact_email": "test@school.com",
            "contact_phone": "+1234567890"
        }
    )

    assert response.status_code == 403
    assert "admin" in response.json()["detail"].lower()


def test_regular_user_can_list_schools(regular_user_client):
    """Test that regular users CAN list schools (read-only)"""
    response = regular_user_client.get("/api/v1/schools/")

    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_regular_user_cannot_update_school(db, regular_user_client):
    """Test that regular users cannot update schools (admin-only)"""
    from app.services.school_service import SchoolService
    from app.schemas.school import SchoolCreate

    school = SchoolService.create(
        SchoolCreate(
            name="Test School",
            contact_email="test@school.com",
            contact_phone="+1234567890"
        ),
        db
    )

    response = regular_user_client.put(
        f"/api/v1/schools/{school.id}",
        json={"name": "Updated Name"}
    )

    assert response.status_code == 403
    assert "admin" in response.json()["detail"].lower()


def test_regular_user_cannot_delete_school(db, regular_user_client):
    """Test that regular users cannot delete schools (admin-only)"""
    from app.services.school_service import SchoolService
    from app.schemas.school import SchoolCreate

    school = SchoolService.create(
        SchoolCreate(
            name="Test School",
            contact_email="test@school.com",
            contact_phone="+1234567890"
        ),
        db
    )

    response = regular_user_client.delete(f"/api/v1/schools/{school.id}")

    assert response.status_code == 403
    assert "admin" in response.json()["detail"].lower()


def test_regular_user_cannot_create_student(db, regular_user_client):
    """Test that regular users cannot create students (admin-only)"""
    from app.services.school_service import SchoolService
    from app.schemas.school import SchoolCreate

    school = SchoolService.create(
        SchoolCreate(
            name="Test School",
            contact_email="test@school.com",
            contact_phone="+1234567890"
        ),
        db
    )

    response = regular_user_client.post(
        "/api/v1/students/",
        json={
            "first_name": "John",
            "last_name": "Doe",
            "school_id": school.id,
            "email": "john@example.com",
            "enrollment_date": "2024-01-01"
        }
    )

    assert response.status_code == 403
    assert "admin" in response.json()["detail"].lower()


def test_regular_user_cannot_create_invoice(db, regular_user_client):
    """Test that regular users cannot create invoices (admin-only)"""
    from app.services.school_service import SchoolService
    from app.services.student_service import StudentService
    from app.schemas.school import SchoolCreate
    from app.schemas.student import StudentCreate

    school = SchoolService.create(
        SchoolCreate(
            name="Test School",
            contact_email="test@school.com",
            contact_phone="+1234567890"
        ),
        db
    )

    student = StudentService.create(
        StudentCreate(
            first_name="John",
            last_name="Doe",
            school_id=school.id,
            email="john@example.com",
            enrollment_date="2024-01-01"
        ),
        db
    )

    response = regular_user_client.post(
        "/api/v1/invoices/",
        json={
            "student_id": student.id,
            "issue_date": "2024-01-01",
            "due_date": "2024-12-31",
            "items": [
                {"description": "Tuition", "quantity": 1, "unit_price": 1000.00}
            ]
        }
    )

    assert response.status_code == 403
    assert "admin" in response.json()["detail"].lower()


def test_regular_user_can_make_payment(db, regular_user_client):
    """Test that regular users CAN make payments"""
    from app.services.school_service import SchoolService
    from app.services.student_service import StudentService
    from app.services.invoice_service import InvoiceService
    from app.schemas.school import SchoolCreate
    from app.schemas.student import StudentCreate
    from app.schemas.invoice import InvoiceCreate, InvoiceItemCreate

    school = SchoolService.create(
        SchoolCreate(
            name="Test School",
            contact_email="test@school.com",
            contact_phone="+1234567890"
        ),
        db
    )

    student = StudentService.create(
        StudentCreate(
            first_name="John",
            last_name="Doe",
            school_id=school.id,
            email="john.doe@example.com",
            enrollment_date="2024-01-01"
        ),
        db
    )

    invoice = InvoiceService.create(
        InvoiceCreate(
            student_id=student.id,
            issue_date="2024-01-01",
            due_date="2024-12-31",
            items=[InvoiceItemCreate(description="Tuition", quantity=1, unit_price=1000.00)]
        ),
        db
    )

    response = regular_user_client.post(
        f"/api/v1/invoices/{invoice.id}/payments",
        json={
            "amount": 500.00,
            "payment_method": "card",
            "payment_date": "2024-01-15"
        }
    )

    assert response.status_code == 201
    data = response.json()
    assert float(data["amount"]) == 500.00
