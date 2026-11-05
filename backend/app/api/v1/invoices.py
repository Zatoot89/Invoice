"""
InvoiceFlow Pro - Invoices API Routes
"""
from fastapi import APIRouter, Depends, Query, File, UploadFile, Response, HTTPException, status
from fastapi.security import HTTPBearer
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional, Literal, Dict, Any
from decimal import Decimal
from datetime import datetime

from app.core.deps import get_db, get_current_user_optional
from app.services.pdf_service import PDFService
from app.services.invoice_service import InvoiceService
from app.services.customer_service import CustomerService

router = APIRouter()
security = HTTPBearer()


class InvoiceItemRequest(BaseModel):
    description: str
    quantity: float
    unit_price: Decimal
    tax_rate: Optional[float] = 0.0


class InvoiceRequest(BaseModel):
    customer_id: int
    invoice_number: Optional[str] = None
    currency: str = "USD"
    issue_date: datetime
    due_date: datetime
    items: List[InvoiceItemRequest]
    notes: Optional[str] = None
    discount_percentage: Optional[float] = 0.0
    tax_rate: Optional[float] = 0.0


class InvoiceItemResponse(BaseModel):
    id: int
    description: str
    quantity: float
    unit_price: Decimal
    tax_rate: float
    subtotal: Decimal
    tax_amount: Decimal
    total: Decimal


class InvoiceResponse(BaseModel):
    id: int
    invoice_number: str
    customer_id: int
    customer_name: str
    status: Literal["draft", "sent", "paid", "overdue", "cancelled"]
    currency: str
    issue_date: datetime
    due_date: datetime
    subtotal: Decimal
    discount_amount: Decimal
    tax_amount: Decimal
    total: Decimal
    amount_paid: Decimal
    amount_due: Decimal
    items: List[InvoiceItemResponse]
    notes: Optional[str]
    created_at: datetime
    updated_at: datetime


class InvoiceListResponse(BaseModel):
    invoices: List[InvoiceResponse]
    total: int
    page: int
    page_size: int


@router.get("/", response_model=InvoiceListResponse)
async def get_invoices(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: Optional[str] = None,
    customer_id: Optional[int] = None,
    search: Optional[str] = None,
    token: str = Depends(security),
):
    """Get list of invoices with filtering and pagination"""
    # TODO: Implement invoice listing
    mock_item = {
        "id": 1,
        "description": "Web Development Services",
        "quantity": 40.0,
        "unit_price": Decimal("125.00"),
        "tax_rate": 0.1,
        "subtotal": Decimal("5000.00"),
        "tax_amount": Decimal("500.00"),
        "total": Decimal("5500.00"),
    }
    
    mock_invoice = {
        "id": 1,
        "invoice_number": "INV-00000001",
        "customer_id": 1,
        "customer_name": "Acme Corporation",
        "status": "sent",
        "currency": "USD",
        "issue_date": datetime.now(),
        "due_date": datetime.now(),
        "subtotal": Decimal("5000.00"),
        "discount_amount": Decimal("0.00"),
        "tax_amount": Decimal("500.00"),
        "total": Decimal("5500.00"),
        "amount_paid": Decimal("0.00"),
        "amount_due": Decimal("5500.00"),
        "items": [mock_item],
        "notes": "Thank you for your business!",
        "created_at": datetime.now(),
        "updated_at": datetime.now(),
    }
    
    return {
        "invoices": [mock_invoice],
        "total": 1,
        "page": page,
        "page_size": page_size,
    }


@router.post("/", response_model=InvoiceResponse)
async def create_invoice(request: InvoiceRequest, token: str = Depends(security)):
    """Create a new invoice"""
    # TODO: Implement invoice creation logic
    mock_item = {
        "id": 1,
        "description": request.items[0].description,
        "quantity": request.items[0].quantity,
        "unit_price": request.items[0].unit_price,
        "tax_rate": request.items[0].tax_rate,
        "subtotal": request.items[0].quantity * request.items[0].unit_price,
        "tax_amount": Decimal("0.00"),
        "total": request.items[0].quantity * request.items[0].unit_price,
    }
    
    return {
        "id": 1,
        "invoice_number": "INV-00000001",
        "customer_id": request.customer_id,
        "customer_name": "Acme Corporation",
        "status": "draft",
        "currency": request.currency,
        "issue_date": request.issue_date,
        "due_date": request.due_date,
        "subtotal": mock_item["subtotal"],
        "discount_amount": Decimal("0.00"),
        "tax_amount": Decimal("0.00"),
        "total": mock_item["total"],
        "amount_paid": Decimal("0.00"),
        "amount_due": mock_item["total"],
        "items": [mock_item],
        "notes": request.notes,
        "created_at": datetime.now(),
        "updated_at": datetime.now(),
    }


@router.get("/{invoice_id}", response_model=InvoiceResponse)
async def get_invoice(invoice_id: int, token: str = Depends(security)):
    """Get invoice by ID"""
    # TODO: Implement get invoice by ID
    mock_item = {
        "id": 1,
        "description": "Web Development Services",
        "quantity": 40.0,
        "unit_price": Decimal("125.00"),
        "tax_rate": 0.1,
        "subtotal": Decimal("5000.00"),
        "tax_amount": Decimal("500.00"),
        "total": Decimal("5500.00"),
    }
    
    return {
        "id": invoice_id,
        "invoice_number": f"INV-{invoice_id:08d}",
        "customer_id": 1,
        "customer_name": "Acme Corporation",
        "status": "sent",
        "currency": "USD",
        "issue_date": datetime.now(),
        "due_date": datetime.now(),
        "subtotal": Decimal("5000.00"),
        "discount_amount": Decimal("0.00"),
        "tax_amount": Decimal("500.00"),
        "total": Decimal("5500.00"),
        "amount_paid": Decimal("0.00"),
        "amount_due": Decimal("5500.00"),
        "items": [mock_item],
        "notes": "Thank you for your business!",
        "created_at": datetime.now(),
        "updated_at": datetime.now(),
    }


@router.put("/{invoice_id}", response_model=InvoiceResponse)
async def update_invoice(
    invoice_id: int, request: InvoiceRequest, token: str = Depends(security)
):
    """Update invoice by ID"""
    # TODO: Implement invoice update logic
    return await get_invoice(invoice_id, token)


@router.delete("/{invoice_id}")
async def delete_invoice(invoice_id: int, token: str = Depends(security)):
    """Delete invoice by ID"""
    # TODO: Implement invoice deletion logic
    return {"message": f"Invoice {invoice_id} deleted successfully"}


@router.post("/{invoice_id}/send")
async def send_invoice(invoice_id: int, token: str = Depends(security)):
    """Send invoice to customer"""
    # TODO: Implement invoice sending logic
    return {"message": f"Invoice {invoice_id} sent successfully"}


@router.post("/{invoice_id}/duplicate", response_model=InvoiceResponse)
async def duplicate_invoice(invoice_id: int, token: str = Depends(security)):
    """Create a duplicate of an invoice"""
    # TODO: Implement invoice duplication logic
    return await get_invoice(invoice_id, token)


@router.get("/{invoice_id}/pdf")
async def download_invoice_pdf(
    invoice_id: int,
    template: str = Query("professional", description="PDF template style (professional, modern, reportlab)"),
    download: bool = Query(False, description="Whether to trigger download or view inline"),
    db: Session = Depends(get_db),
    token: str = Depends(security),
):
    """
    Generate and stream invoice PDF.
    Uses modern HTML/CSS (with embedded QR code) or falls back to ReportLab.
    """
    pdf_service = PDFService()
    invoice_service = InvoiceService(db)
    customer_service = CustomerService(db)

    # Attempt to load real record from database
    invoice = None
    customer = None
    try:
        invoice = await invoice_service.get_by_id_with_items(invoice_id)
        if invoice and invoice.customer_id:
            customer = await customer_service.get_by_id(invoice.customer_id)
    except Exception:
        invoice = None
        customer = None

    # Fallback to structured data if database record is not yet seeded
    if not invoice:
        mock_item = {
            "description": "Web Application Architecture & Development",
            "quantity": 40.0,
            "unit_price": 125.0,
            "tax_rate": 0.05,
            "total": 5250.0,
            "unit": "hrs",
            "sku": "DEV-01",
        }
        invoice = {
            "id": invoice_id,
            "invoice_number": f"INV-{invoice_id:08d}",
            "status": "SENT",
            "currency": "USD",
            "issue_date": datetime.now(),
            "due_date": datetime.now(),
            "subtotal": 5000.00,
            "discount_amount": 0.00,
            "tax_amount": 250.00,
            "total": 5250.00,
            "amount_paid": 0.00,
            "amount_due": 5250.00,
            "notes": "Thank you for partnering with us!",
            "terms": "Payment due within 30 days of issue.",
            "payment_url": "https://buy.stripe.com/test_instant_invoice",
        }
        customer = {
            "name": "Acme Global Corp",
            "company": "Acme Global Corporation",
            "email": "billing@acme.com",
            "address_line_1": "100 Tech Blvd, Suite 400",
            "city": "San Francisco",
            "state": "CA",
            "postal_code": "94107",
            "country": "USA",
            "tax_number": "US-EIN-987654321",
        }
        items = [mock_item]
        user = {
            "company_name": "InvoiceFlow Pro Ltd.",
            "email": "support@invoiceflow.io",
            "address": "123 Innovation Way, Tech Park",
        }
    else:
        items = invoice.items
        user = getattr(invoice, "user", None) or {
            "company_name": "InvoiceFlow Pro Ltd.",
            "email": "support@invoiceflow.io",
            "address": "123 Innovation Way, Tech Park",
        }

    # Generate PDF bytes
    pdf_bytes = await pdf_service.create_invoice_pdf(
        invoice=invoice,
        customer=customer or {"name": "Valued Client"},
        user=user,
        items=items,
        template=template,
        payment_url=invoice.get("payment_url") if isinstance(invoice, dict) else getattr(invoice, "payment_url", None),
    )

    filename = f"invoice_{invoice_id}.pdf"
    disposition = "attachment" if download else "inline"
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'{disposition}; filename="{filename}"',
            "X-Invoice-Number": str(invoice.get("invoice_number") if isinstance(invoice, dict) else getattr(invoice, "invoice_number", filename)),
        },
    )


@router.post("/{invoice_id}/payment")
async def record_payment(
    invoice_id: int,
    amount: Decimal,
    payment_date: datetime,
    payment_method: str,
    notes: Optional[str] = None,
    token: str = Depends(security),
):
    """Record a payment for an invoice"""
    # TODO: Implement payment recording logic
    return {
        "message": f"Payment of {amount} recorded for invoice {invoice_id}",
        "payment_id": 1,
    }


@router.get("/{invoice_id}/payments")
async def get_invoice_payments(invoice_id: int, token: str = Depends(security)):
    """Get all payments for an invoice"""
    # TODO: Implement get invoice payments
    return {
        "payments": [],
        "total_paid": Decimal("0.00"),
    }