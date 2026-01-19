import pytest
from datetime import date
from decimal import Decimal
from app.services.invoice_service import InvoiceService
from app.services.school_service import SchoolService
from app.services.student_service import StudentService
from app.schemas.invoice import InvoiceCreate, InvoiceUpdate, InvoiceItemCreate
from app.schemas.school import SchoolCreate
from app.schemas.student import StudentCreate
from app.models.invoice import Invoice, InvoiceStatus


def create_test_student(db):
    """Helper to create a test student"""
    school = SchoolService.create(
        SchoolCreate(name="Test School", contact_email="test@school.com", contact_phone="+1234567890"),
        db
    )
    student = StudentService.create(
        StudentCreate(
            school_id=school.id,
            first_name="John",
            last_name="Doe",
            email="john@student.com",
            enrollment_date=date(2024, 1, 15)
        ),
        db
    )
    return student


def test_create_invoice_with_items(db):
    """Test creating an invoice with items"""
    student = create_test_student(db)

    invoice_data = InvoiceCreate(
        student_id=student.id,
        issue_date=date(2024, 1, 20),
        due_date=date(2024, 2, 20),
        items=[
            InvoiceItemCreate(description="Tuition", quantity=1, unit_price=Decimal("10000.00")),
            InvoiceItemCreate(description="Books", quantity=3, unit_price=Decimal("500.00"))
        ]
    )

    invoice = InvoiceService.create(invoice_data, db)

    assert invoice.id is not None
    assert invoice.student_id == student.id
    assert invoice.total_amount == Decimal("11500.00")  # 10000 + (3 * 500)
    assert invoice.status == InvoiceStatus.PENDING
    assert len(invoice.items) == 2


def test_invoice_total_calculated_from_items(db):
    """Test that invoice total is correctly calculated from items"""
    student = create_test_student(db)

    invoice_data = InvoiceCreate(
        student_id=student.id,
        issue_date=date(2024, 1, 20),
        due_date=date(2024, 2, 20),
        items=[
            InvoiceItemCreate(description="Item 1", quantity=2, unit_price=Decimal("100.00")),
            InvoiceItemCreate(description="Item 2", quantity=3, unit_price=Decimal("50.00")),
            InvoiceItemCreate(description="Item 3", quantity=1, unit_price=Decimal("250.00"))
        ]
    )

    invoice = InvoiceService.create(invoice_data, db)

    # Expected: (2 * 100) + (3 * 50) + (1 * 250) = 200 + 150 + 250 = 600
    assert invoice.total_amount == Decimal("600.00")


def test_get_all_invoices(db):
    """Test getting all invoices"""
    student = create_test_student(db)

    InvoiceService.create(
        InvoiceCreate(
            student_id=student.id,
            issue_date=date(2024, 1, 20),
            due_date=date(2024, 2, 20),
            items=[InvoiceItemCreate(description="Item", quantity=1, unit_price=Decimal("100.00"))]
        ),
        db
    )
    InvoiceService.create(
        InvoiceCreate(
            student_id=student.id,
            issue_date=date(2024, 2, 1),
            due_date=date(2024, 3, 1),
            items=[InvoiceItemCreate(description="Item", quantity=1, unit_price=Decimal("200.00"))]
        ),
        db
    )

    invoices = InvoiceService.get_all(db)

    assert len(invoices) == 2


def test_get_invoice_by_id(db):
    """Test getting an invoice by ID"""
    student = create_test_student(db)

    invoice = InvoiceService.create(
        InvoiceCreate(
            student_id=student.id,
            issue_date=date(2024, 1, 20),
            due_date=date(2024, 2, 20),
            items=[InvoiceItemCreate(description="Item", quantity=1, unit_price=Decimal("100.00"))]
        ),
        db
    )

    retrieved_invoice = InvoiceService.get_by_id(invoice.id, db)

    assert retrieved_invoice is not None
    assert retrieved_invoice.id == invoice.id


def test_update_invoice(db):
    """Test updating an invoice"""
    student = create_test_student(db)

    invoice = InvoiceService.create(
        InvoiceCreate(
            student_id=student.id,
            issue_date=date(2024, 1, 20),
            due_date=date(2024, 2, 20),
            items=[InvoiceItemCreate(description="Item", quantity=1, unit_price=Decimal("100.00"))]
        ),
        db
    )

    update_data = InvoiceUpdate(due_date=date(2024, 3, 15))
    updated_invoice = InvoiceService.update(invoice, update_data, db)

    assert updated_invoice.due_date == date(2024, 3, 15)


def test_cancel_invoice(db):
    """Test cancelling an invoice"""
    student = create_test_student(db)

    invoice = InvoiceService.create(
        InvoiceCreate(
            student_id=student.id,
            issue_date=date(2024, 1, 20),
            due_date=date(2024, 2, 20),
            items=[InvoiceItemCreate(description="Item", quantity=1, unit_price=Decimal("100.00"))]
        ),
        db
    )

    cancelled_invoice = InvoiceService.cancel(invoice, db)

    assert cancelled_invoice.status == InvoiceStatus.CANCELLED


def test_add_item_recalculates_total(db):
    """Test that adding an item recalculates the invoice total"""
    student = create_test_student(db)

    invoice = InvoiceService.create(
        InvoiceCreate(
            student_id=student.id,
            issue_date=date(2024, 1, 20),
            due_date=date(2024, 2, 20),
            items=[InvoiceItemCreate(description="Original Item", quantity=1, unit_price=Decimal("100.00"))]
        ),
        db
    )

    assert invoice.total_amount == Decimal("100.00")

    # Add a new item
    new_item = InvoiceItemCreate(description="New Item", quantity=2, unit_price=Decimal("50.00"))
    InvoiceService.add_item(invoice, new_item, db)

    # Refresh invoice and check total
    db.refresh(invoice)
    assert invoice.total_amount == Decimal("200.00")  # 100 + (2 * 50)


def test_update_item_recalculates_total(db):
    """Test that updating an item recalculates the invoice total"""
    student = create_test_student(db)

    invoice = InvoiceService.create(
        InvoiceCreate(
            student_id=student.id,
            issue_date=date(2024, 1, 20),
            due_date=date(2024, 2, 20),
            items=[
                InvoiceItemCreate(description="Item 1", quantity=1, unit_price=Decimal("100.00")),
                InvoiceItemCreate(description="Item 2", quantity=1, unit_price=Decimal("50.00"))
            ]
        ),
        db
    )

    assert invoice.total_amount == Decimal("150.00")

    # Update the first item
    item_to_update = invoice.items[0]
    updated_item_data = InvoiceItemCreate(description="Updated Item", quantity=3, unit_price=Decimal("200.00"))
    InvoiceService.update_item(item_to_update, updated_item_data, db)

    # Refresh invoice and check total
    db.refresh(invoice)
    assert invoice.total_amount == Decimal("650.00")  # (3 * 200) + 50


def test_delete_item_recalculates_total(db):
    """Test that deleting an item recalculates the invoice total"""
    student = create_test_student(db)

    invoice = InvoiceService.create(
        InvoiceCreate(
            student_id=student.id,
            issue_date=date(2024, 1, 20),
            due_date=date(2024, 2, 20),
            items=[
                InvoiceItemCreate(description="Item 1", quantity=1, unit_price=Decimal("100.00")),
                InvoiceItemCreate(description="Item 2", quantity=1, unit_price=Decimal("50.00"))
            ]
        ),
        db
    )

    assert invoice.total_amount == Decimal("150.00")

    # Delete the first item
    item_to_delete = invoice.items[0]
    InvoiceService.delete_item(item_to_delete, db)

    # Refresh invoice and check total
    db.refresh(invoice)
    assert invoice.total_amount == Decimal("50.00")


def test_cannot_delete_last_item(db):
    """Test that you cannot delete the last item in an invoice"""
    student = create_test_student(db)

    invoice = InvoiceService.create(
        InvoiceCreate(
            student_id=student.id,
            issue_date=date(2024, 1, 20),
            due_date=date(2024, 2, 20),
            items=[InvoiceItemCreate(description="Only Item", quantity=1, unit_price=Decimal("100.00"))]
        ),
        db
    )

    # Try to delete the only item
    item = invoice.items[0]
    result = InvoiceService.delete_item(item, db)

    assert result is None  # Should return None (deletion not allowed)

    # Invoice should still have the item
    db.refresh(invoice)
    active_items = [item for item in invoice.items if item.deleted_at is None]
    assert len(active_items) == 1


def test_recalculate_total_excludes_deleted_items(db):
    """Test that recalculate_total excludes soft-deleted items"""
    student = create_test_student(db)

    invoice = InvoiceService.create(
        InvoiceCreate(
            student_id=student.id,
            issue_date=date(2024, 1, 20),
            due_date=date(2024, 2, 20),
            items=[
                InvoiceItemCreate(description="Item 1", quantity=1, unit_price=Decimal("100.00")),
                InvoiceItemCreate(description="Item 2", quantity=1, unit_price=Decimal("50.00")),
                InvoiceItemCreate(description="Item 3", quantity=1, unit_price=Decimal("25.00"))
            ]
        ),
        db
    )

    assert invoice.total_amount == Decimal("175.00")

    # Delete the middle item
    item_to_delete = invoice.items[1]
    InvoiceService.delete_item(item_to_delete, db)

    # Total should now be 100 + 25 = 125 (excluding the deleted 50)
    db.refresh(invoice)
    assert invoice.total_amount == Decimal("125.00")
