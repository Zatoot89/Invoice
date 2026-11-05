"""
InvoiceFlow Pro - Invoice Models
"""
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Numeric, Boolean, Enum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base
import enum


class InvoiceStatus(str, enum.Enum):
    DRAFT = "draft"
    SENT = "sent"
    VIEWED = "viewed"
    PAID = "paid"
    PARTIALLY_PAID = "partially_paid"
    OVERDUE = "overdue"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"


class InvoiceType(str, enum.Enum):
    STANDARD = "standard"
    RECURRING = "recurring"
    CREDIT_NOTE = "credit_note"
    PROFORMA = "proforma"


class RecurrenceInterval(str, enum.Enum):
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    YEARLY = "yearly"


class Invoice(Base):
    __tablename__ = "invoices"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False)
    
    # Invoice Identification
    invoice_number = Column(String(100), unique=True, index=True, nullable=False)
    reference_number = Column(String(100), nullable=True)  # Customer's PO number
    
    # Invoice Type and Status
    type = Column(Enum(InvoiceType), default=InvoiceType.STANDARD, nullable=False)
    status = Column(Enum(InvoiceStatus), default=InvoiceStatus.DRAFT, nullable=False)
    
    # Dates
    issue_date = Column(DateTime(timezone=True), nullable=False)
    due_date = Column(DateTime(timezone=True), nullable=False)
    sent_date = Column(DateTime(timezone=True), nullable=True)
    viewed_date = Column(DateTime(timezone=True), nullable=True)
    paid_date = Column(DateTime(timezone=True), nullable=True)
    
    # Financial Information
    currency = Column(String(3), default="USD", nullable=False)
    subtotal = Column(Numeric(precision=15, scale=2), nullable=False)
    discount_percentage = Column(Numeric(precision=5, scale=2), default=0, nullable=False)
    discount_amount = Column(Numeric(precision=15, scale=2), default=0, nullable=False)
    tax_rate = Column(Numeric(precision=5, scale=2), default=0, nullable=False)
    tax_amount = Column(Numeric(precision=15, scale=2), default=0, nullable=False)
    total = Column(Numeric(precision=15, scale=2), nullable=False)
    amount_paid = Column(Numeric(precision=15, scale=2), default=0, nullable=False)
    amount_due = Column(Numeric(precision=15, scale=2), nullable=False)
    
    # Recurring Invoice Settings
    is_recurring = Column(Boolean, default=False, nullable=False)
    recurrence_interval = Column(Enum(RecurrenceInterval), nullable=True)
    recurrence_count = Column(Integer, nullable=True)  # Number of occurrences
    next_recurrence_date = Column(DateTime(timezone=True), nullable=True)
    parent_invoice_id = Column(Integer, ForeignKey("invoices.id"), nullable=True)
    
    # Additional Information
    notes = Column(Text, nullable=True)
    terms_and_conditions = Column(Text, nullable=True)
    footer_text = Column(Text, nullable=True)
    
    # File Attachments
    pdf_url = Column(String(500), nullable=True)
    attachments = Column(Text, nullable=True)  # JSON array of file URLs
    
    # Email Tracking
    email_sent_count = Column(Integer, default=0, nullable=False)
    last_email_sent = Column(DateTime(timezone=True), nullable=True)
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="invoices")
    customer = relationship("Customer", back_populates="invoices")
    items = relationship("InvoiceItem", back_populates="invoice", cascade="all, delete-orphan")
    payments = relationship("Payment", back_populates="invoice", cascade="all, delete-orphan")
    
    # Self-referential relationship for recurring invoices
    child_invoices = relationship("Invoice", remote_side=[id])

    def __repr__(self):
        return f"<Invoice(id={self.id}, number='{self.invoice_number}', total={self.total})>"

    @property
    def is_overdue(self) -> bool:
        """Check if invoice is overdue"""
        from datetime import datetime, timezone
        return (
            self.status in [InvoiceStatus.SENT, InvoiceStatus.VIEWED, InvoiceStatus.PARTIALLY_PAID]
            and self.due_date < datetime.now(timezone.utc)
        )

    @property
    def days_overdue(self) -> int:
        """Get number of days overdue"""
        if not self.is_overdue:
            return 0
        from datetime import datetime, timezone
        return (datetime.now(timezone.utc) - self.due_date).days


class InvoiceItem(Base):
    __tablename__ = "invoice_items"

    id = Column(Integer, primary_key=True, index=True)
    invoice_id = Column(Integer, ForeignKey("invoices.id"), nullable=False)
    
    # Item Information
    description = Column(Text, nullable=False)
    quantity = Column(Numeric(precision=10, scale=3), nullable=False)
    unit_price = Column(Numeric(precision=15, scale=2), nullable=False)
    
    # Tax Information
    tax_rate = Column(Numeric(precision=5, scale=2), default=0, nullable=False)
    tax_amount = Column(Numeric(precision=15, scale=2), default=0, nullable=False)
    
    # Calculated Fields
    subtotal = Column(Numeric(precision=15, scale=2), nullable=False)
    total = Column(Numeric(precision=15, scale=2), nullable=False)
    
    # Optional Fields
    unit = Column(String(50), nullable=True)  # hour, piece, kg, etc.
    sku = Column(String(100), nullable=True)
    category = Column(String(100), nullable=True)
    
    # Sort Order
    sort_order = Column(Integer, default=0, nullable=False)
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    invoice = relationship("Invoice", back_populates="items")

    def __repr__(self):
        return f"<InvoiceItem(id={self.id}, description='{self.description[:30]}...', total={self.total})>"