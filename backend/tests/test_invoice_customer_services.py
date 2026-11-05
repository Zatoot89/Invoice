"""
Unit tests for InvoiceService and CustomerService with SQLite
"""
import pytest
import os
import sys
from datetime import datetime, timezone
from decimal import Decimal

# Ensure backend directory is in sys.path
backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.database import Base
from app.models.user import User, UserRole, AuthProvider
from app.models.customer import Customer
from app.models.invoice import Invoice, InvoiceItem, InvoiceStatus
from app.services.invoice_service import InvoiceService
from app.services.customer_service import CustomerService


@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()

    # Seed test user
    user = User(
        email="test@invoiceflow.io",
        first_name="Jane",
        last_name="Doe",
        company_name="Acme Billing",
        role=UserRole.USER,
        auth_provider=AuthProvider.LOCAL,
        is_active=True,
    )
    session.add(user)
    session.commit()
    session.refresh(user)

    yield session
    session.close()


@pytest.mark.asyncio
async def test_customer_and_invoice_lifecycle(db_session):
    customer_service = CustomerService(db_session)
    invoice_service = InvoiceService(db_session)

    user = db_session.query(User).first()

    # 1. Create Customer
    customer = await customer_service.create_customer(
        user_id=user.id,
        name="John Client",
        email="client@example.com",
        company="Client Enterprises",
        address_line_1="456 Market St",
        city="Chicago",
        state="IL",
        postal_code="60601",
        country="USA",
        tax_number="IL-TAX-12345",
    )

    assert customer.id is not None
    assert customer.name == "John Client"

    fetched_customer = await customer_service.get_by_id(customer.id)
    assert fetched_customer is not None
    assert fetched_customer.email == "client@example.com"

    # 2. Create Invoice
    items_data = [
        {
            "description": "API Integration Consulting",
            "quantity": 20.0,
            "unit_price": Decimal("150.00"),
            "tax_rate": 10.0,
            "unit": "hours",
        },
        {
            "description": "Server Maintenance",
            "quantity": 1.0,
            "unit_price": Decimal("500.00"),
            "tax_rate": 0.0,
            "unit": "month",
        },
    ]

    invoice = await invoice_service.create_invoice(
        user_id=user.id,
        customer_id=customer.id,
        issue_date=datetime.now(timezone.utc),
        due_date=datetime.now(timezone.utc),
        items_data=items_data,
        discount_percentage=5.0,  # 5% discount
        notes="Thank you for your partnership.",
    )

    assert invoice.id is not None
    assert invoice.status == InvoiceStatus.DRAFT
    # Subtotal = (20 * 150) + (1 * 500) = 3000 + 500 = 3500
    assert invoice.subtotal == Decimal("3500.00")
    # Discount = 5% of 3500 = 175
    assert invoice.discount_amount == Decimal("175.00")
    # Tax = 10% on 3000 = 300
    assert invoice.tax_amount == Decimal("300.00")
    # Total = 3500 - 175 + 300 = 3625
    assert invoice.total == Decimal("3625.00")
    assert invoice.amount_due == Decimal("3625.00")

    # 3. Fetch with items eagerly loaded
    loaded_invoice = await invoice_service.get_by_id_with_items(invoice.id)
    assert loaded_invoice is not None
    assert len(loaded_invoice.items) == 2
    assert loaded_invoice.customer.name == "John Client"

    # 4. Status update
    updated_inv = await invoice_service.update_status(invoice.id, InvoiceStatus.PAID)
    assert updated_inv.status == InvoiceStatus.PAID
    assert updated_inv.amount_paid == Decimal("3625.00")
    assert updated_inv.amount_due == Decimal("0.00")
