"""
Tests for PDF Generation Service in InvoiceFlow Pro
"""
import pytest
import os
import sys
from datetime import datetime
from decimal import Decimal

# Ensure backend directory is in sys.path
backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from app.services.pdf_service import PDFService


def test_pdf_service_templates():
    service = PDFService()
    templates = service.get_available_templates()
    assert len(templates) >= 2
    template_ids = [t["id"] for t in templates]
    assert "professional" in template_ids


def test_pdf_service_render_html():
    service = PDFService()
    mock_invoice = {
        "invoice_number": "INV-TEST-001",
        "status": "SENT",
        "currency": "USD",
        "issue_date": datetime(2026, 11, 5),
        "due_date": datetime(2026, 12, 5),
        "subtotal": Decimal("1000.00"),
        "discount_amount": Decimal("50.00"),
        "tax_amount": Decimal("95.00"),
        "total": Decimal("1045.00"),
        "amount_paid": Decimal("0.00"),
        "amount_due": Decimal("1045.00"),
        "notes": "Test invoice note",
        "terms": "Net 30 days",
        "payment_url": "https://stripe.com/pay/test_invoice",
    }
    mock_customer = {
        "name": "Acme Widgets Ltd",
        "email": "billing@acme.com",
        "company": "Acme Corporation",
        "address_line_1": "123 Main St",
        "city": "Metropolis",
        "state": "NY",
        "postal_code": "10001",
        "country": "USA",
    }
    mock_user = {
        "company_name": "InvoiceFlow Pro",
        "email": "finance@invoiceflow.io",
    }
    mock_items = [
        {
            "description": "Cloud Architecture Consulting",
            "quantity": 10.0,
            "unit_price": Decimal("100.00"),
            "tax_rate": Decimal("0.10"),
            "total": Decimal("1000.00"),
            "unit": "hours",
        }
    ]

    html = service.render_html(
        invoice=mock_invoice,
        customer=mock_customer,
        user=mock_user,
        items=mock_items,
    )

    assert "INV-TEST-001" in html
    assert "Acme Widgets Ltd" in html
    assert "Cloud Architecture Consulting" in html
    assert "InvoiceFlow Pro" in html


@pytest.mark.asyncio
async def test_pdf_generation_bytes():
    service = PDFService()
    mock_invoice = {
        "invoice_number": "INV-TEST-002",
        "status": "DRAFT",
        "currency": "USD",
        "issue_date": datetime(2026, 11, 5),
        "due_date": datetime(2026, 11, 20),
        "subtotal": 500.00,
        "discount_amount": 0.00,
        "tax_amount": 25.00,
        "total": 525.00,
        "amount_paid": 0.00,
        "amount_due": 525.00,
        "notes": "Generated for test",
    }
    mock_customer = {
        "name": "Beta Testing Co",
        "email": "beta@test.com",
    }
    mock_user = {
        "company_name": "Test Org",
        "email": "admin@testorg.com",
    }
    mock_items = [
        {
            "description": "Standard Support",
            "quantity": 1.0,
            "unit_price": 500.00,
            "tax_rate": 0.05,
            "total": 500.00,
        }
    ]

    pdf_bytes = await service.create_invoice_pdf(
        invoice=mock_invoice,
        customer=mock_customer,
        user=mock_user,
        items=mock_items,
        template="reportlab",  # Tests pure-Python generator
    )

    assert isinstance(pdf_bytes, bytes)
    assert len(pdf_bytes) > 0
    assert pdf_bytes.startswith(b"%PDF")
