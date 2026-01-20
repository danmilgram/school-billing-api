from datetime import date
from decimal import Decimal

from app.models.invoice import InvoiceStatus
from app.schemas.invoice import InvoiceCreate, InvoiceItemCreate, InvoiceUpdate
from app.services.invoice_service import InvoiceService


def test_create_invoice_with_items(db, test_student):
    """Test creating an invoice with items"""

    invoice_data = InvoiceCreate(
        student_id=test_student.id,
        issue_date=date(2024, 1, 20),
        due_date=date(2024, 2, 20),
        items=[
            InvoiceItemCreate(
                description="Tuition", quantity=1, unit_price=Decimal("10000.00")
            ),
            InvoiceItemCreate(
                description="Books", quantity=3, unit_price=Decimal("500.00")
            ),
        ],
    )

    invoice = InvoiceService.create(invoice_data, db)

    assert invoice.id is not None
    assert invoice.student_id == test_student.id
    assert invoice.total_amount == Decimal("11500.00")  # 10000 + (3 * 500)
    assert invoice.status == InvoiceStatus.PENDING
    assert len(invoice.items) == 2


def test_invoice_total_calculated_from_items(db, test_student):
    """Test that invoice total is correctly calculated from items"""

    invoice_data = InvoiceCreate(
        student_id=test_student.id,
        issue_date=date(2024, 1, 20),
        due_date=date(2024, 2, 20),
        items=[
            InvoiceItemCreate(
                description="Item 1", quantity=2, unit_price=Decimal("100.00")
            ),
            InvoiceItemCreate(
                description="Item 2", quantity=3, unit_price=Decimal("50.00")
            ),
            InvoiceItemCreate(
                description="Item 3", quantity=1, unit_price=Decimal("250.00")
            ),
        ],
    )

    invoice = InvoiceService.create(invoice_data, db)

    # Expected: (2 * 100) + (3 * 50) + (1 * 250) = 200 + 150 + 250 = 600
    assert invoice.total_amount == Decimal("600.00")


def test_get_all_invoices(db, invoice_factory, test_student):
    """Test getting all invoices"""
    invoice_factory(
        test_student.id,
        items=[
            InvoiceItemCreate(
                description="Item", quantity=1, unit_price=Decimal("100.00")
            )
        ],
    )
    invoice_factory(
        test_student.id,
        issue_date=date(2024, 2, 1),
        due_date=date(2024, 3, 1),
        items=[
            InvoiceItemCreate(
                description="Item", quantity=1, unit_price=Decimal("200.00")
            )
        ],
    )

    invoices = InvoiceService.get_all(db)

    assert len(invoices) == 2


def test_get_invoice_by_id(db, test_invoice):
    """Test getting an invoice by ID"""
    retrieved_invoice = InvoiceService.get_by_id(test_invoice.id, db)

    assert retrieved_invoice is not None
    assert retrieved_invoice.id == test_invoice.id


def test_update_invoice(db, test_invoice):
    """Test updating an invoice"""
    update_data = InvoiceUpdate(due_date=date(2024, 3, 15))
    updated_invoice = InvoiceService.update(test_invoice, update_data, db)

    assert updated_invoice.due_date == date(2024, 3, 15)


def test_cancel_invoice(db, test_invoice):
    """Test cancelling an invoice"""
    cancelled_invoice = InvoiceService.cancel(test_invoice, db)

    assert cancelled_invoice.status == InvoiceStatus.CANCELLED


def test_add_item_recalculates_total(db, test_invoice):
    """Test that adding an item recalculates the invoice total"""

    assert test_invoice.total_amount == Decimal("1000.00")

    # Add a new item
    new_item = InvoiceItemCreate(
        description="New Item", quantity=2, unit_price=Decimal("50.00")
    )
    InvoiceService.add_item(test_invoice, new_item, db)

    # Refresh invoice and check total
    db.refresh(test_invoice)
    assert test_invoice.total_amount == Decimal("1100.00")  # 1000 + (2 * 50)


def test_update_item_recalculates_total(db, invoice_factory, test_student):
    """Test that updating an item recalculates the invoice total"""
    invoice = invoice_factory(
        test_student.id,
        items=[
            InvoiceItemCreate(
                description="Item 1", quantity=1, unit_price=Decimal("100.00")
            ),
            InvoiceItemCreate(
                description="Item 2", quantity=1, unit_price=Decimal("50.00")
            ),
        ],
    )

    assert invoice.total_amount == Decimal("150.00")

    # Update the first item
    item_to_update = invoice.items[0]
    updated_item_data = InvoiceItemCreate(
        description="Updated Item", quantity=3, unit_price=Decimal("200.00")
    )
    InvoiceService.update_item(item_to_update, updated_item_data, db)

    # Refresh invoice and check total
    db.refresh(invoice)
    assert invoice.total_amount == Decimal("650.00")  # (3 * 200) + 50


def test_delete_item_recalculates_total(db, invoice_factory, test_student):
    """Test that deleting an item recalculates the invoice total"""
    invoice = invoice_factory(
        test_student.id,
        items=[
            InvoiceItemCreate(
                description="Item 1", quantity=1, unit_price=Decimal("100.00")
            ),
            InvoiceItemCreate(
                description="Item 2", quantity=1, unit_price=Decimal("50.00")
            ),
        ],
    )

    assert invoice.total_amount == Decimal("150.00")

    # Delete the first item
    item_to_delete = invoice.items[0]
    InvoiceService.delete_item(item_to_delete, db)

    # Refresh invoice and check total
    db.refresh(invoice)
    assert invoice.total_amount == Decimal("50.00")


def test_cannot_delete_last_item(db, test_invoice):
    """Test that you cannot delete the last item in an invoice"""

    # Try to delete the only item
    item = test_invoice.items[0]
    result = InvoiceService.delete_item(item, db)

    assert result is None  # Should return None (deletion not allowed)

    # Invoice should still have the item
    db.refresh(test_invoice)
    active_items = [item for item in test_invoice.items if item.deleted_at is None]
    assert len(active_items) == 1


def test_recalculate_total_excludes_deleted_items(db, invoice_factory, test_student):
    """Test that recalculate_total excludes soft-deleted items"""
    invoice = invoice_factory(
        test_student.id,
        items=[
            InvoiceItemCreate(
                description="Item 1", quantity=1, unit_price=Decimal("100.00")
            ),
            InvoiceItemCreate(
                description="Item 2", quantity=1, unit_price=Decimal("50.00")
            ),
            InvoiceItemCreate(
                description="Item 3", quantity=1, unit_price=Decimal("25.00")
            ),
        ],
    )

    assert invoice.total_amount == Decimal("175.00")

    # Delete the middle item
    item_to_delete = invoice.items[1]
    InvoiceService.delete_item(item_to_delete, db)

    # Total should now be 100 + 25 = 125 (excluding the deleted 50)
    db.refresh(invoice)
    assert invoice.total_amount == Decimal("125.00")
