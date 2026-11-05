"""
InvoiceFlow Pro - Payment Model
"""
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Numeric, Boolean, Enum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base
import enum


class PaymentStatus(str, enum.Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"
    PARTIALLY_REFUNDED = "partially_refunded"


class PaymentMethod(str, enum.Enum):
    CASH = "cash"
    CHECK = "check"
    CREDIT_CARD = "credit_card"
    DEBIT_CARD = "debit_card"
    BANK_TRANSFER = "bank_transfer"
    PAYPAL = "paypal"
    STRIPE = "stripe"
    SQUARE = "square"
    WIRE_TRANSFER = "wire_transfer"
    CRYPTOCURRENCY = "cryptocurrency"
    OTHER = "other"


class RefundReason(str, enum.Enum):
    CUSTOMER_REQUEST = "customer_request"
    BILLING_ERROR = "billing_error"
    DUPLICATE_PAYMENT = "duplicate_payment"
    FRAUDULENT = "fraudulent"
    CANCELLED_SERVICE = "cancelled_service"
    OTHER = "other"


class Payment(Base):
    __tablename__ = "payments"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    invoice_id = Column(Integer, ForeignKey("invoices.id"), nullable=False)
    
    # Payment Information
    amount = Column(Numeric(precision=15, scale=2), nullable=False)
    currency = Column(String(3), nullable=False)
    payment_method = Column(Enum(PaymentMethod), nullable=False)
    status = Column(Enum(PaymentStatus), default=PaymentStatus.PENDING, nullable=False)
    
    # Payment Details
    reference_number = Column(String(255), nullable=True, index=True)
    transaction_id = Column(String(255), nullable=True, index=True)  # External transaction ID
    confirmation_number = Column(String(255), nullable=True)
    
    # Dates
    payment_date = Column(DateTime(timezone=True), nullable=False)
    processed_date = Column(DateTime(timezone=True), nullable=True)
    
    # Payment Gateway Information
    gateway_provider = Column(String(50), nullable=True)  # stripe, paypal, square, etc.
    gateway_transaction_id = Column(String(255), nullable=True)
    gateway_fee = Column(Numeric(precision=15, scale=2), default=0, nullable=False)
    gateway_response = Column(Text, nullable=True)  # JSON response from gateway
    
    # Refund Information
    is_refunded = Column(Boolean, default=False, nullable=False)
    refund_amount = Column(Numeric(precision=15, scale=2), default=0, nullable=False)
    refund_reason = Column(Enum(RefundReason), nullable=True)
    refund_date = Column(DateTime(timezone=True), nullable=True)
    refund_transaction_id = Column(String(255), nullable=True)
    
    # Bank/Check Information
    bank_name = Column(String(200), nullable=True)
    check_number = Column(String(100), nullable=True)
    routing_number = Column(String(20), nullable=True)
    account_number_last_4 = Column(String(4), nullable=True)
    
    # Additional Information
    notes = Column(Text, nullable=True)
    receipt_url = Column(String(500), nullable=True)
    
    # Reconciliation
    is_reconciled = Column(Boolean, default=False, nullable=False)
    reconciled_date = Column(DateTime(timezone=True), nullable=True)
    bank_statement_date = Column(DateTime(timezone=True), nullable=True)
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="payments")
    invoice = relationship("Invoice", back_populates="payments")

    def __repr__(self):
        return f"<Payment(id={self.id}, amount={self.amount}, method='{self.payment_method}', status='{self.status}')>"

    @property
    def net_amount(self) -> float:
        """Get net amount after gateway fees"""
        return float(self.amount - self.gateway_fee)

    @property
    def is_successful(self) -> bool:
        """Check if payment was successful"""
        return self.status == PaymentStatus.COMPLETED

    @property
    def can_be_refunded(self) -> bool:
        """Check if payment can be refunded"""
        return (
            self.status == PaymentStatus.COMPLETED
            and not self.is_refunded
            and self.refund_amount == 0
        )