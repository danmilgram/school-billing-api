from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.auth import get_current_user, require_admin
from app.core.database import get_db
from app.models.user import User
from app.schemas.invoice import (
    InvoiceCreate,
    InvoiceItemCreate,
    InvoiceItemRead,
    InvoiceRead,
    InvoiceUpdate,
)
from app.schemas.payment import PaymentCreate, PaymentRead
from app.services.invoice_service import InvoiceService
from app.services.payment_service import PaymentService

router = APIRouter(prefix="/invoices", tags=["invoices"])


@router.post("/", response_model=InvoiceRead, status_code=201)
def create_invoice(
    invoice: InvoiceCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """Create a new invoice with items (requires admin role)"""
    return InvoiceService.create(invoice, db)


@router.get("/", response_model=List[InvoiceRead])
def list_invoices(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Max number of records to return"),
    status: Optional[str] = Query(
        None, description="Filter by invoice status (pending, paid, cancelled)"
    ),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    List all invoices (excluding soft-deleted) with pagination and optional
    status filter (requires authentication)
    """
    return InvoiceService.get_all(db, skip=skip, limit=limit, status=status)


@router.get("/{invoice_id}", response_model=InvoiceRead)
def get_invoice(
    invoice_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get an invoice by ID (requires authentication)"""
    invoice = InvoiceService.get_by_id(invoice_id, db)
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    return invoice


@router.put("/{invoice_id}", response_model=InvoiceRead)
def update_invoice(
    invoice_id: int,
    invoice_update: InvoiceUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """Update an invoice (requires admin role)"""
    invoice = InvoiceService.get_by_id(invoice_id, db)
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    return InvoiceService.update(invoice, invoice_update, db)


@router.post("/{invoice_id}/cancel", response_model=InvoiceRead)
def cancel_invoice(
    invoice_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """Cancel an invoice (business action, not deletion) (requires admin role)"""
    invoice = InvoiceService.get_by_id(invoice_id, db)
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    return InvoiceService.cancel(invoice, db)


# Nested routes for invoice items (Invoice is the aggregate root)


@router.post("/{invoice_id}/items", response_model=InvoiceItemRead, status_code=201)
def add_invoice_item(
    invoice_id: int,
    item: InvoiceItemCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """Add item to invoice (recalculates total) (requires admin role)"""
    invoice = InvoiceService.get_by_id(invoice_id, db)
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    return InvoiceService.add_item(invoice, item, db)


@router.patch("/{invoice_id}/items/{item_id}", response_model=InvoiceItemRead)
def update_invoice_item(
    invoice_id: int,
    item_id: int,
    item: InvoiceItemCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """Update invoice item (recalculates total) (requires admin role)"""
    invoice = InvoiceService.get_by_id(invoice_id, db)
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")

    existing_item = InvoiceService.get_item(invoice_id, item_id, db)
    if not existing_item:
        raise HTTPException(status_code=404, detail="Invoice item not found")

    return InvoiceService.update_item(existing_item, item, db)


@router.delete("/{invoice_id}/items/{item_id}", status_code=204)
def delete_invoice_item(
    invoice_id: int,
    item_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """
    Soft delete invoice item (recalculates total, cannot delete last item)
    (requires admin role)
    """
    invoice = InvoiceService.get_by_id(invoice_id, db)
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")

    existing_item = InvoiceService.get_item(invoice_id, item_id, db)
    if not existing_item:
        raise HTTPException(status_code=404, detail="Invoice item not found")

    result = InvoiceService.delete_item(existing_item, db)
    if result is None:
        raise HTTPException(status_code=400, detail="Cannot delete last invoice item")

    return None


# Nested routes for payments (Invoice is the aggregate root)


@router.post("/{invoice_id}/payments", response_model=PaymentRead, status_code=201)
def create_payment(
    invoice_id: int,
    payment: PaymentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Create payment for invoice (cannot overpay, auto-updates status)
    (requires authentication)
    """
    invoice = InvoiceService.get_by_id(invoice_id, db)
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")

    try:
        return PaymentService.create(invoice, payment, db)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{invoice_id}/payments", response_model=List[PaymentRead])
def list_payments(
    invoice_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List all payments for an invoice (requires authentication)"""
    invoice = InvoiceService.get_by_id(invoice_id, db)
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")

    return PaymentService.get_by_invoice(invoice_id, db)
