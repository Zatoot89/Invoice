"""
InvoiceFlow Pro - Invoice Service
"""
from typing import Optional, List, Tuple, Dict, Any
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import or_, and_, desc
from datetime import datetime, timezone
from decimal import Decimal

from app.models.invoice import Invoice, InvoiceItem, InvoiceStatus, InvoiceType
from app.models.customer import Customer
from app.models.payment import Payment, PaymentStatus
from app.core.exceptions import ResourceNotFoundException, ValidationException


class InvoiceService:
    """
    Service class for invoice operations
    """

    def __init__(self, db: Session):
        self.db = db

    async def get_by_id(self, invoice_id: int) -> Optional[Invoice]:
        """Get invoice by primary ID"""
        return self.db.query(Invoice).filter(Invoice.id == invoice_id).first()

    async def get_by_id_with_items(self, invoice_id: int) -> Optional[Invoice]:
        """Get invoice by ID with items and customer eagerly loaded"""
        return (
            self.db.query(Invoice)
            .options(joinedload(Invoice.items), joinedload(Invoice.customer))
            .filter(Invoice.id == invoice_id)
            .first()
        )

    async def get_by_number(self, invoice_number: str) -> Optional[Invoice]:
        """Get invoice by unique invoice number"""
        return self.db.query(Invoice).filter(Invoice.invoice_number == invoice_number).first()

    async def get_invoices(
        self,
        user_id: int,
        page: int = 1,
        page_size: int = 20,
        status: Optional[str] = None,
        customer_id: Optional[int] = None,
        search: Optional[str] = None,
    ) -> Tuple[List[Invoice], int]:
        """Get paginated list of invoices with filters"""
        query = self.db.query(Invoice).filter(Invoice.user_id == user_id)

        if status:
            query = query.filter(Invoice.status == status)
        if customer_id:
            query = query.filter(Invoice.customer_id == customer_id)
        if search:
            query = query.filter(
                or_(
                    Invoice.invoice_number.ilike(f"%{search}%"),
                    Invoice.notes.ilike(f"%{search}%"),
                    Invoice.reference_number.ilike(f"%{search}%"),
                )
            )

        total = query.count()
        offset = (page - 1) * page_size
        invoices = (
            query.order_by(desc(Invoice.created_at))
            .offset(offset)
            .limit(page_size)
            .all()
        )

        return invoices, total

    async def generate_invoice_number(self, user_id: int) -> str:
        """Generate unique sequential invoice number"""
        count = self.db.query(Invoice).filter(Invoice.user_id == user_id).count()
        return f"INV-{count + 1:08d}"

    async def create_invoice(
        self,
        user_id: int,
        customer_id: int,
        issue_date: datetime,
        due_date: datetime,
        items_data: List[Dict[str, Any]],
        invoice_number: Optional[str] = None,
        currency: str = "USD",
        notes: Optional[str] = None,
        discount_percentage: float = 0.0,
        tax_rate: float = 0.0,
        reference_number: Optional[str] = None,
    ) -> Invoice:
        """Create a new invoice with line items and computed financial totals"""
        if not items_data:
            raise ValidationException("An invoice must contain at least one line item.")

        if not invoice_number:
            invoice_number = await self.generate_invoice_number(user_id)

        subtotal = Decimal("0.00")
        tax_total = Decimal("0.00")
        items: List[InvoiceItem] = []

        for item_dict in items_data:
            qty = Decimal(str(item_dict["quantity"]))
            unit_price = Decimal(str(item_dict["unit_price"]))
            item_tax_rate = Decimal(str(item_dict.get("tax_rate", tax_rate or 0.0)))
            
            line_subtotal = qty * unit_price
            line_tax = line_subtotal * (item_tax_rate / Decimal("100") if item_tax_rate > 1 else item_tax_rate)
            line_total = line_subtotal + line_tax

            subtotal += line_subtotal
            tax_total += line_tax

            item = InvoiceItem(
                description=item_dict["description"],
                quantity=qty,
                unit_price=unit_price,
                tax_rate=item_tax_rate,
                tax_amount=line_tax,
                subtotal=line_subtotal,
                total=line_total,
                unit=item_dict.get("unit"),
                sku=item_dict.get("sku"),
            )
            items.append(item)

        discount_amount = subtotal * (Decimal(str(discount_percentage)) / Decimal("100") if discount_percentage > 1 else Decimal(str(discount_percentage)))
        total = subtotal - discount_amount + tax_total

        invoice = Invoice(
            user_id=user_id,
            customer_id=customer_id,
            invoice_number=invoice_number,
            reference_number=reference_number,
            status=InvoiceStatus.DRAFT,
            type=InvoiceType.STANDARD,
            issue_date=issue_date,
            due_date=due_date,
            currency=currency,
            subtotal=subtotal,
            discount_percentage=Decimal(str(discount_percentage)),
            discount_amount=discount_amount,
            tax_rate=Decimal(str(tax_rate)),
            tax_amount=tax_total,
            total=total,
            amount_paid=Decimal("0.00"),
            amount_due=total,
            notes=notes,
            items=items,
        )

        self.db.add(invoice)
        self.db.commit()
        self.db.refresh(invoice)
        return invoice

    async def update_status(self, invoice_id: int, new_status: InvoiceStatus) -> Invoice:
        """Update status of invoice"""
        invoice = await self.get_by_id(invoice_id)
        if not invoice:
            raise ResourceNotFoundException("Invoice", invoice_id)

        invoice.status = new_status
        if new_status == InvoiceStatus.SENT and not invoice.sent_date:
            invoice.sent_date = datetime.now(timezone.utc)
        elif new_status == InvoiceStatus.PAID and not invoice.paid_date:
            invoice.paid_date = datetime.now(timezone.utc)
            invoice.amount_paid = invoice.total
            invoice.amount_due = Decimal("0.00")

        self.db.commit()
        self.db.refresh(invoice)
        return invoice

    async def delete_invoice(self, invoice_id: int) -> bool:
        """Delete an invoice"""
        invoice = await self.get_by_id(invoice_id)
        if not invoice:
            raise ResourceNotFoundException("Invoice", invoice_id)

        self.db.delete(invoice)
        self.db.commit()
        return True
