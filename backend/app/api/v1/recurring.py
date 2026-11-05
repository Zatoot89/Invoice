"""
InvoiceFlow Pro - Recurring Invoice API
"""
from datetime import datetime
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from pydantic import BaseModel, validator
from decimal import Decimal

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.models.invoice import RecurrenceInterval
from app.services.recurring_service import RecurringInvoiceService
from app.services.websocket_service import WebSocketService
from app.services.email_service import EmailService


router = APIRouter(prefix="/recurring", tags=["recurring-invoices"])


# Pydantic models
class InvoiceItemCreate(BaseModel):
    description: str
    quantity: Decimal
    unit_price: Decimal
    tax_rate: Optional[Decimal] = Decimal('0.00')
    tax_amount: Optional[Decimal] = Decimal('0.00')
    subtotal: Decimal
    total: Decimal
    unit: Optional[str] = None
    sku: Optional[str] = None
    category: Optional[str] = None
    sort_order: Optional[int] = 0


class RecurringInvoiceCreate(BaseModel):
    customer_id: int
    invoice_number: str
    reference_number: Optional[str] = None
    issue_date: datetime
    due_date: datetime
    currency: Optional[str] = "USD"
    subtotal: Decimal
    discount_percentage: Optional[Decimal] = Decimal('0.00')
    discount_amount: Optional[Decimal] = Decimal('0.00')
    tax_rate: Optional[Decimal] = Decimal('0.00')
    tax_amount: Optional[Decimal] = Decimal('0.00')
    total: Decimal
    recurrence_interval: RecurrenceInterval
    recurrence_count: Optional[int] = None
    notes: Optional[str] = None
    terms_and_conditions: Optional[str] = None
    footer_text: Optional[str] = None
    items: List[InvoiceItemCreate]
    is_recurring: bool = True

    @validator('recurrence_count')
    def validate_recurrence_count(cls, v):
        if v is not None and v <= 0:
            raise ValueError('Recurrence count must be positive')
        return v


class RecurringInvoiceUpdate(BaseModel):
    recurrence_interval: Optional[RecurrenceInterval] = None
    recurrence_count: Optional[int] = None
    notes: Optional[str] = None
    terms_and_conditions: Optional[str] = None

    @validator('recurrence_count')
    def validate_recurrence_count(cls, v):
        if v is not None and v <= 0:
            raise ValueError('Recurrence count must be positive')
        return v


class RecurringProcessResult(BaseModel):
    total_processed: int
    successful_generations: int
    failed_generations: int
    errors: List[Dict[str, Any]]


@router.post("/", status_code=201)
async def create_recurring_invoice(
    invoice_data: RecurringInvoiceCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Create a new recurring invoice template
    
    **Parameters:**
    - **customer_id**: ID of the customer
    - **recurrence_interval**: How often to generate (weekly, monthly, quarterly, yearly)
    - **recurrence_count**: Number of times to recur (optional, unlimited if not specified)
    - **items**: List of invoice items
    
    **Returns:** Created recurring invoice template
    """
    try:
        websocket_service = WebSocketService()
        email_service = EmailService()
        recurring_service = RecurringInvoiceService(db, websocket_service, email_service)
        
        invoice = await recurring_service.create_recurring_invoice(
            current_user.id, 
            invoice_data.dict()
        )
        
        return {
            "message": "Recurring invoice created successfully",
            "invoice": {
                "id": invoice.id,
                "invoice_number": invoice.invoice_number,
                "customer_id": invoice.customer_id,
                "recurrence_interval": invoice.recurrence_interval.value,
                "next_recurrence_date": invoice.next_recurrence_date.isoformat(),
                "recurrence_count": invoice.recurrence_count,
                "total": float(invoice.total),
                "is_recurring": invoice.is_recurring
            }
        }
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/")
async def get_recurring_invoices(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get all recurring invoice templates for the current user
    
    **Returns:** List of recurring invoice templates
    """
    try:
        websocket_service = WebSocketService()
        email_service = EmailService()
        recurring_service = RecurringInvoiceService(db, websocket_service, email_service)
        
        invoices = await recurring_service.get_recurring_invoices(current_user.id)
        
        return {
            "invoices": [
                {
                    "id": invoice.id,
                    "invoice_number": invoice.invoice_number,
                    "customer_name": invoice.customer.name,
                    "customer_id": invoice.customer_id,
                    "recurrence_interval": invoice.recurrence_interval.value,
                    "next_recurrence_date": invoice.next_recurrence_date.isoformat() if invoice.next_recurrence_date else None,
                    "recurrence_count": invoice.recurrence_count,
                    "total": float(invoice.total),
                    "currency": invoice.currency,
                    "is_recurring": invoice.is_recurring,
                    "status": invoice.status.value,
                    "created_at": invoice.created_at.isoformat()
                }
                for invoice in invoices
            ]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{invoice_id}")
async def get_recurring_invoice(
    invoice_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get a specific recurring invoice template with its details
    
    **Returns:** Recurring invoice details including items
    """
    try:
        from app.models.invoice import Invoice
        from sqlalchemy import and_
        
        invoice = db.query(Invoice).filter(
            and_(
                Invoice.id == invoice_id,
                Invoice.user_id == current_user.id,
                Invoice.is_recurring == True
            )
        ).first()
        
        if not invoice:
            raise HTTPException(status_code=404, detail="Recurring invoice not found")
        
        return {
            "invoice": {
                "id": invoice.id,
                "invoice_number": invoice.invoice_number,
                "reference_number": invoice.reference_number,
                "customer": {
                    "id": invoice.customer.id,
                    "name": invoice.customer.name,
                    "email": invoice.customer.email
                },
                "recurrence_interval": invoice.recurrence_interval.value,
                "next_recurrence_date": invoice.next_recurrence_date.isoformat() if invoice.next_recurrence_date else None,
                "recurrence_count": invoice.recurrence_count,
                "issue_date": invoice.issue_date.isoformat(),
                "due_date": invoice.due_date.isoformat(),
                "currency": invoice.currency,
                "subtotal": float(invoice.subtotal),
                "tax_amount": float(invoice.tax_amount),
                "total": float(invoice.total),
                "notes": invoice.notes,
                "terms_and_conditions": invoice.terms_and_conditions,
                "is_recurring": invoice.is_recurring,
                "status": invoice.status.value,
                "items": [
                    {
                        "id": item.id,
                        "description": item.description,
                        "quantity": float(item.quantity),
                        "unit_price": float(item.unit_price),
                        "total": float(item.total),
                        "unit": item.unit,
                        "sku": item.sku
                    }
                    for item in invoice.items
                ],
                "created_at": invoice.created_at.isoformat()
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{invoice_id}/generated")
async def get_generated_invoices(
    invoice_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get all invoices generated from a recurring template
    
    **Returns:** List of generated invoices
    """
    try:
        websocket_service = WebSocketService()
        email_service = EmailService()
        recurring_service = RecurringInvoiceService(db, websocket_service, email_service)
        
        generated_invoices = await recurring_service.get_generated_invoices(
            current_user.id, invoice_id
        )
        
        return {
            "generated_invoices": [
                {
                    "id": invoice.id,
                    "invoice_number": invoice.invoice_number,
                    "customer_name": invoice.customer.name,
                    "total": float(invoice.total),
                    "status": invoice.status.value,
                    "issue_date": invoice.issue_date.isoformat(),
                    "due_date": invoice.due_date.isoformat(),
                    "created_at": invoice.created_at.isoformat()
                }
                for invoice in generated_invoices
            ]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{invoice_id}")
async def update_recurring_invoice(
    invoice_id: int,
    update_data: RecurringInvoiceUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Update a recurring invoice template
    
    **Updatable fields:**
    - recurrence_interval
    - recurrence_count
    - notes
    - terms_and_conditions
    
    **Returns:** Updated recurring invoice
    """
    try:
        websocket_service = WebSocketService()
        email_service = EmailService()
        recurring_service = RecurringInvoiceService(db, websocket_service, email_service)
        
        invoice = await recurring_service.update_recurring_invoice(
            current_user.id, 
            invoice_id, 
            update_data.dict(exclude_unset=True)
        )
        
        return {
            "message": "Recurring invoice updated successfully",
            "invoice": {
                "id": invoice.id,
                "recurrence_interval": invoice.recurrence_interval.value,
                "next_recurrence_date": invoice.next_recurrence_date.isoformat() if invoice.next_recurrence_date else None,
                "recurrence_count": invoice.recurrence_count,
                "notes": invoice.notes,
                "terms_and_conditions": invoice.terms_and_conditions
            }
        }
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{invoice_id}/cancel")
async def cancel_recurring_invoice(
    invoice_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Cancel a recurring invoice (stop future generations)
    
    **Returns:** Cancelled recurring invoice
    """
    try:
        websocket_service = WebSocketService()
        email_service = EmailService()
        recurring_service = RecurringInvoiceService(db, websocket_service, email_service)
        
        invoice = await recurring_service.cancel_recurring_invoice(current_user.id, invoice_id)
        
        return {
            "message": "Recurring invoice cancelled successfully",
            "invoice": {
                "id": invoice.id,
                "invoice_number": invoice.invoice_number,
                "is_recurring": invoice.is_recurring,
                "status": invoice.status.value
            }
        }
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/process")
async def process_recurring_invoices(
    background_tasks: BackgroundTasks,
    max_invoices: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Manually trigger processing of due recurring invoices
    
    **Note:** This is typically called by scheduled tasks, but can be triggered manually
    
    **Parameters:**
    - **max_invoices**: Maximum number of invoices to process in this batch
    
    **Returns:** Processing results
    """
    try:
        # Only allow admin users to manually trigger processing
        if not current_user.is_admin:
            raise HTTPException(status_code=403, detail="Admin access required")
        
        websocket_service = WebSocketService()
        email_service = EmailService()
        recurring_service = RecurringInvoiceService(db, websocket_service, email_service)
        
        # Process in background
        background_tasks.add_task(
            recurring_service.process_recurring_invoices,
            max_invoices
        )
        
        return {
            "message": f"Recurring invoice processing started (max {max_invoices} invoices)",
            "status": "processing"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/intervals/")
async def get_recurrence_intervals():
    """
    Get available recurrence intervals
    
    **Returns:** List of available recurrence intervals
    """
    return {
        "intervals": [
            {"value": "weekly", "label": "Weekly"},
            {"value": "monthly", "label": "Monthly"},
            {"value": "quarterly", "label": "Quarterly"},
            {"value": "yearly", "label": "Yearly"}
        ]
    }