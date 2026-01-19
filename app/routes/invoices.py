from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.core.database import get_db
from app.schemas.invoice import InvoiceCreate, InvoiceRead, InvoiceUpdate, InvoiceItemCreate, InvoiceItemRead
from app.schemas.payment import PaymentCreate, PaymentRead
from app.services.invoice_service import InvoiceService
from app.services.payment_service import PaymentService

router = APIRouter(prefix="/invoices", tags=["invoices"])


@router.post("/", response_model=InvoiceRead, status_code=201)
def create_invoice(invoice: InvoiceCreate, db: Session = Depends(get_db)):
    """Create a new invoice with items"""
    return InvoiceService.create(invoice, db)


@router.get("/", response_model=List[InvoiceRead])
def list_invoices(db: Session = Depends(get_db)):
    """List all invoices (excluding soft-deleted)"""
    return InvoiceService.get_all(db)


@router.get("/{invoice_id}", response_model=InvoiceRead)
def get_invoice(invoice_id: int, db: Session = Depends(get_db)):
    """Get an invoice by ID"""
    invoice = InvoiceService.get_by_id(invoice_id, db)
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    return invoice


@router.put("/{invoice_id}", response_model=InvoiceRead)
def update_invoice(invoice_id: int, invoice_update: InvoiceUpdate, db: Session = Depends(get_db)):
    """Update an invoice"""
    invoice = InvoiceService.get_by_id(invoice_id, db)
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    return InvoiceService.update(invoice, invoice_update, db)


@router.post("/{invoice_id}/cancel", response_model=InvoiceRead)
def cancel_invoice(invoice_id: int, db: Session = Depends(get_db)):
    """Cancel an invoice (business action, not deletion)"""
    invoice = InvoiceService.get_by_id(invoice_id, db)
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    return InvoiceService.cancel(invoice, db)


# Nested routes for invoice items (Invoice is the aggregate root)

@router.post("/{invoice_id}/items", response_model=InvoiceItemRead, status_code=201)
def add_invoice_item(invoice_id: int, item: InvoiceItemCreate, db: Session = Depends(get_db)):
    """Add item to invoice (recalculates total)"""
    invoice = InvoiceService.get_by_id(invoice_id, db)
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    return InvoiceService.add_item(invoice, item, db)


@router.patch("/{invoice_id}/items/{item_id}", response_model=InvoiceItemRead)
def update_invoice_item(invoice_id: int, item_id: int, item: InvoiceItemCreate, db: Session = Depends(get_db)):
    """Update invoice item (recalculates total)"""
    invoice = InvoiceService.get_by_id(invoice_id, db)
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")

    existing_item = InvoiceService.get_item(invoice_id, item_id, db)
    if not existing_item:
        raise HTTPException(status_code=404, detail="Invoice item not found")

    return InvoiceService.update_item(existing_item, item, db)


@router.delete("/{invoice_id}/items/{item_id}", status_code=204)
def delete_invoice_item(invoice_id: int, item_id: int, db: Session = Depends(get_db)):
    """Soft delete invoice item (recalculates total, cannot delete last item)"""
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
def create_payment(invoice_id: int, payment: PaymentCreate, db: Session = Depends(get_db)):
    """Create payment for invoice (cannot overpay, auto-updates status)"""
    invoice = InvoiceService.get_by_id(invoice_id, db)
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")

    try:
        return PaymentService.create(invoice, payment, db)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{invoice_id}/payments", response_model=List[PaymentRead])
def list_payments(invoice_id: int, db: Session = Depends(get_db)):
    """List all payments for an invoice"""
    invoice = InvoiceService.get_by_id(invoice_id, db)
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")

    return PaymentService.get_by_invoice(invoice_id, db)
