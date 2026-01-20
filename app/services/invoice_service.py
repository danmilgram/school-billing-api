import logging
from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy.orm import Session

from app.models.invoice import Invoice
from app.models.invoice_item import InvoiceItem
from app.schemas.invoice import InvoiceCreate, InvoiceItemCreate, InvoiceUpdate

logger = logging.getLogger(__name__)


class InvoiceService:
    @staticmethod
    def recalculate_total(invoice: Invoice, db: Session):
        """Recalculate invoice total from non-deleted items"""
        items = (
            db.query(InvoiceItem)
            .filter(
                InvoiceItem.invoice_id == invoice.id, InvoiceItem.deleted_at.is_(None)
            )
            .all()
        )

        total = Decimal("0")
        for item in items:
            total += item.total_amount

        invoice.total_amount = total
        db.commit()
        db.refresh(invoice)
        return invoice

    @staticmethod
    def get_all(db: Session, skip: int = 0, limit: int = 100, status: str = None):
        """
        Get all invoices excluding soft-deleted with pagination and optional
        status filter
        """
        query = db.query(Invoice).filter(Invoice.deleted_at.is_(None))

        if status:
            query = query.filter(Invoice.status == status)

        return query.offset(skip).limit(limit).all()

    @staticmethod
    def get_by_id(invoice_id: int, db: Session):
        """Get invoice by ID excluding soft-deleted"""
        return (
            db.query(Invoice)
            .filter(Invoice.id == invoice_id, Invoice.deleted_at.is_(None))
            .first()
        )

    @staticmethod
    def create(invoice_in: InvoiceCreate, db: Session):
        """Create a new invoice with items"""
        logger.info(
            f"Creating invoice for student_id={invoice_in.student_id} "
            f"with {len(invoice_in.items)} items"
        )

        # Calculate total from items
        total_amount = Decimal("0")
        for item in invoice_in.items:
            item_total = Decimal(str(item.quantity)) * item.unit_price
            total_amount += item_total

        # Create invoice
        invoice_data = invoice_in.model_dump(exclude={"items"})
        invoice_data["total_amount"] = total_amount
        invoice = Invoice(**invoice_data)
        db.add(invoice)
        db.flush()  # Get invoice ID

        # Create invoice items
        for item in invoice_in.items:
            item_total = Decimal(str(item.quantity)) * item.unit_price
            invoice_item = InvoiceItem(
                invoice_id=invoice.id,
                description=item.description,
                quantity=item.quantity,
                unit_price=item.unit_price,
                total_amount=item_total,
            )
            db.add(invoice_item)

        db.commit()
        db.refresh(invoice)

        logger.info(
            f"Invoice created: invoice_id={invoice.id}, "
            f"total_amount={invoice.total_amount}, status={invoice.status.value}"
        )
        return invoice

    @staticmethod
    def update(invoice: Invoice, invoice_in: InvoiceUpdate, db: Session):
        """Update an existing invoice"""
        for field, value in invoice_in.model_dump(exclude_unset=True).items():
            setattr(invoice, field, value)
        db.commit()
        db.refresh(invoice)
        return invoice

    @staticmethod
    def cancel(invoice: Invoice, db: Session):
        """Cancel an invoice (business action)"""
        from app.models.invoice import InvoiceStatus

        logger.info(
            f"Cancelling invoice: invoice_id={invoice.id}, "
            f"student_id={invoice.student_id}, "
            f"previous_status={invoice.status.value}, "
            f"total_amount={invoice.total_amount}"
        )

        invoice.status = InvoiceStatus.CANCELLED
        db.commit()
        db.refresh(invoice)

        logger.info(f"Invoice cancelled successfully: invoice_id={invoice.id}")
        return invoice

    @staticmethod
    def add_item(invoice: Invoice, item_in: InvoiceItemCreate, db: Session):
        """Add item to invoice and recalculate total"""
        logger.info(
            f"Adding item to invoice: invoice_id={invoice.id}, "
            f"description='{item_in.description}', quantity={item_in.quantity}, "
            f"unit_price={item_in.unit_price}"
        )

        item_total = Decimal(str(item_in.quantity)) * item_in.unit_price
        invoice_item = InvoiceItem(
            invoice_id=invoice.id,
            description=item_in.description,
            quantity=item_in.quantity,
            unit_price=item_in.unit_price,
            total_amount=item_total,
        )
        db.add(invoice_item)
        db.commit()
        db.refresh(invoice_item)

        # Recalculate invoice total
        InvoiceService.recalculate_total(invoice, db)

        logger.info(
            f"Item added to invoice: invoice_id={invoice.id}, item_id={invoice_item.id}"
        )
        return invoice_item

    @staticmethod
    def update_item(item: InvoiceItem, item_in: InvoiceItemCreate, db: Session):
        """Update invoice item and recalculate invoice total"""
        item.description = item_in.description
        item.quantity = item_in.quantity
        item.unit_price = item_in.unit_price
        item.total_amount = Decimal(str(item_in.quantity)) * item_in.unit_price
        db.commit()
        db.refresh(item)

        # Get invoice and recalculate total
        invoice = db.query(Invoice).filter(Invoice.id == item.invoice_id).first()
        if invoice:
            InvoiceService.recalculate_total(invoice, db)

        return item

    @staticmethod
    def delete_item(item: InvoiceItem, db: Session):
        """Soft delete invoice item and recalculate invoice total"""
        # Check if it's the last item
        remaining_items = (
            db.query(InvoiceItem)
            .filter(
                InvoiceItem.invoice_id == item.invoice_id,
                InvoiceItem.deleted_at.is_(None),
                InvoiceItem.id != item.id,
            )
            .count()
        )

        if remaining_items == 0:
            return None  # Cannot delete last item

        item.deleted_at = datetime.now(timezone.utc)
        db.commit()

        # Get invoice and recalculate total
        invoice = db.query(Invoice).filter(Invoice.id == item.invoice_id).first()
        if invoice:
            InvoiceService.recalculate_total(invoice, db)

        return True

    @staticmethod
    def get_item(invoice_id: int, item_id: int, db: Session):
        """Get invoice item by ID (must belong to invoice)"""
        return (
            db.query(InvoiceItem)
            .filter(
                InvoiceItem.id == item_id,
                InvoiceItem.invoice_id == invoice_id,
                InvoiceItem.deleted_at.is_(None),
            )
            .first()
        )
