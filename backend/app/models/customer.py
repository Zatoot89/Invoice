"""
InvoiceFlow Pro - Customer Model
"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text, Numeric
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base


class Customer(Base):
    __tablename__ = "customers"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Basic Information
    name = Column(String(200), nullable=False, index=True)
    email = Column(String(255), nullable=False, index=True)
    phone = Column(String(50), nullable=True)
    company = Column(String(200), nullable=True)
    
    # Address Information
    address_line_1 = Column(String(255), nullable=True)
    address_line_2 = Column(String(255), nullable=True)
    city = Column(String(100), nullable=True)
    state = Column(String(100), nullable=True)
    postal_code = Column(String(20), nullable=True)
    country = Column(String(100), nullable=True)
    
    # Business Information
    tax_number = Column(String(100), nullable=True)
    website = Column(String(255), nullable=True)
    
    # Financial Summary (computed fields for performance)
    total_invoices = Column(Integer, default=0, nullable=False)
    total_amount = Column(Numeric(precision=15, scale=2), default=0, nullable=False)
    amount_paid = Column(Numeric(precision=15, scale=2), default=0, nullable=False)
    amount_outstanding = Column(Numeric(precision=15, scale=2), default=0, nullable=False)
    
    # Status and Settings
    is_active = Column(Boolean, default=True, nullable=False)
    preferred_currency = Column(String(3), default="USD", nullable=False)
    payment_terms = Column(Integer, default=30, nullable=False)  # Days
    
    # Additional Information
    notes = Column(Text, nullable=True)
    tags = Column(String(500), nullable=True)  # Comma-separated tags
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="customers")
    invoices = relationship("Invoice", back_populates="customer", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Customer(id={self.id}, name='{self.name}', email='{self.email}')>"

    @property
    def full_address(self) -> str:
        """Get formatted full address"""
        address_parts = [
            self.address_line_1,
            self.address_line_2,
            self.city,
            self.state,
            self.postal_code,
            self.country,
        ]
        return ", ".join(part for part in address_parts if part)