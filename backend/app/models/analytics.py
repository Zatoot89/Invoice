"""
InvoiceFlow Pro - Analytics Model (TimescaleDB)
"""
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Numeric, Boolean, Index
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base


class AnalyticsEvent(Base):
    __tablename__ = "analytics_events"
    
    # TimescaleDB hypertable - partitioned by time
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Event Information
    event_type = Column(String(100), nullable=False, index=True)  # invoice_created, payment_received, etc.
    event_category = Column(String(50), nullable=False, index=True)  # invoice, payment, customer, etc.
    event_action = Column(String(50), nullable=False)  # create, update, delete, send, etc.
    
    # Event Timestamp (primary partition key for TimescaleDB)
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    
    # Related Entity Information
    entity_type = Column(String(50), nullable=True)  # invoice, customer, payment
    entity_id = Column(Integer, nullable=True)
    
    # Event Metadata (JSON-like fields)
    event_data = Column(Text, nullable=True)  # JSON string with additional event data
    
    # Financial Metrics (for financial events)
    amount = Column(Numeric(precision=15, scale=2), nullable=True)
    currency = Column(String(3), nullable=True)
    
    # User Context
    ip_address = Column(String(45), nullable=True)  # IPv4 or IPv6
    user_agent = Column(String(500), nullable=True)
    
    # Session Information
    session_id = Column(String(255), nullable=True)
    
    # Geographic Information
    country = Column(String(2), nullable=True)  # ISO country code
    region = Column(String(100), nullable=True)
    city = Column(String(100), nullable=True)
    
    # Additional Metadata
    source = Column(String(50), nullable=True)  # web, mobile, api, etc.
    version = Column(String(20), nullable=True)  # app version
    
    def __repr__(self):
        return f"<AnalyticsEvent(id={self.id}, type='{self.event_type}', timestamp='{self.timestamp}')>"

# Create indexes for common query patterns
Index('ix_analytics_events_user_timestamp', AnalyticsEvent.user_id, AnalyticsEvent.timestamp)
Index('ix_analytics_events_type_timestamp', AnalyticsEvent.event_type, AnalyticsEvent.timestamp)
Index('ix_analytics_events_entity', AnalyticsEvent.entity_type, AnalyticsEvent.entity_id)


class RevenueSnapshot(Base):
    """Daily revenue snapshots for fast analytics queries"""
    __tablename__ = "revenue_snapshots"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Date for snapshot (daily granularity)
    date = Column(DateTime(timezone=True), nullable=False, index=True)
    
    # Revenue Metrics
    total_revenue = Column(Numeric(precision=15, scale=2), default=0, nullable=False)
    invoices_created = Column(Integer, default=0, nullable=False)
    invoices_sent = Column(Integer, default=0, nullable=False)
    invoices_paid = Column(Integer, default=0, nullable=False)
    
    # Payment Metrics
    total_payments = Column(Numeric(precision=15, scale=2), default=0, nullable=False)
    payment_count = Column(Integer, default=0, nullable=False)
    average_payment = Column(Numeric(precision=15, scale=2), default=0, nullable=False)
    
    # Customer Metrics
    new_customers = Column(Integer, default=0, nullable=False)
    active_customers = Column(Integer, default=0, nullable=False)
    
    # Outstanding Amounts
    total_outstanding = Column(Numeric(precision=15, scale=2), default=0, nullable=False)
    overdue_amount = Column(Numeric(precision=15, scale=2), default=0, nullable=False)
    
    # Currency breakdown (JSON)
    currency_breakdown = Column(Text, nullable=True)  # JSON: {"USD": 1000, "EUR": 800}
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    def __repr__(self):
        return f"<RevenueSnapshot(user_id={self.user_id}, date='{self.date}', revenue={self.total_revenue})>"

# Composite index for efficient queries
Index('ix_revenue_snapshots_user_date', RevenueSnapshot.user_id, RevenueSnapshot.date, unique=True)


class CustomerMetric(Base):
    """Customer-level metrics for analytics"""
    __tablename__ = "customer_metrics"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False)
    
    # Date for metrics
    date = Column(DateTime(timezone=True), nullable=False, index=True)
    
    # Lifetime Value Metrics
    total_revenue = Column(Numeric(precision=15, scale=2), default=0, nullable=False)
    total_invoices = Column(Integer, default=0, nullable=False)
    total_payments = Column(Integer, default=0, nullable=False)
    average_invoice_value = Column(Numeric(precision=15, scale=2), default=0, nullable=False)
    
    # Timing Metrics
    average_payment_days = Column(Numeric(precision=5, scale=2), default=0, nullable=False)
    last_invoice_date = Column(DateTime(timezone=True), nullable=True)
    last_payment_date = Column(DateTime(timezone=True), nullable=True)
    
    # Status Metrics
    outstanding_amount = Column(Numeric(precision=15, scale=2), default=0, nullable=False)
    overdue_amount = Column(Numeric(precision=15, scale=2), default=0, nullable=False)
    
    # Engagement Metrics
    invoice_open_rate = Column(Numeric(precision=5, scale=4), default=0, nullable=False)  # 0-1
    payment_punctuality_score = Column(Numeric(precision=5, scale=4), default=0, nullable=False)  # 0-1
    
    # Risk Assessment
    risk_score = Column(Numeric(precision=5, scale=4), default=0, nullable=False)  # 0-1
    is_high_risk = Column(Boolean, default=False, nullable=False)
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    customer = relationship("Customer")

    def __repr__(self):
        return f"<CustomerMetric(customer_id={self.customer_id}, date='{self.date}', revenue={self.total_revenue})>"

# Composite index for efficient queries
Index('ix_customer_metrics_user_date', CustomerMetric.user_id, CustomerMetric.date)
Index('ix_customer_metrics_customer_date', CustomerMetric.customer_id, CustomerMetric.date)