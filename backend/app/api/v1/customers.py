"""
InvoiceFlow Pro - Customers API Routes
"""
from fastapi import APIRouter, Depends, Query
from fastapi.security import HTTPBearer
from pydantic import BaseModel, EmailStr
from typing import List, Optional
from datetime import datetime

router = APIRouter()
security = HTTPBearer()


class CustomerRequest(BaseModel):
    name: str
    email: EmailStr
    phone: Optional[str] = None
    company: Optional[str] = None
    address_line_1: Optional[str] = None
    address_line_2: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    postal_code: Optional[str] = None
    country: Optional[str] = None
    tax_number: Optional[str] = None
    notes: Optional[str] = None


class CustomerResponse(BaseModel):
    id: int
    name: str
    email: str
    phone: Optional[str]
    company: Optional[str]
    address_line_1: Optional[str]
    address_line_2: Optional[str]
    city: Optional[str]
    state: Optional[str]
    postal_code: Optional[str]
    country: Optional[str]
    tax_number: Optional[str]
    notes: Optional[str]
    total_invoices: int
    total_amount: float
    is_active: bool
    created_at: datetime
    updated_at: datetime


class CustomerListResponse(BaseModel):
    customers: List[CustomerResponse]
    total: int
    page: int
    page_size: int


@router.get("/", response_model=CustomerListResponse)
async def get_customers(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: Optional[str] = None,
    is_active: Optional[bool] = None,
    token: str = Depends(security),
):
    """Get list of customers with filtering and pagination"""
    # TODO: Implement customer listing
    mock_customer = {
        "id": 1,
        "name": "John Doe",
        "email": "john@example.com",
        "phone": "+1-555-123-4567",
        "company": "Acme Corporation",
        "address_line_1": "123 Business St",
        "address_line_2": "Suite 100",
        "city": "New York",
        "state": "NY",
        "postal_code": "10001",
        "country": "USA",
        "tax_number": "12-3456789",
        "notes": "Important client",
        "total_invoices": 5,
        "total_amount": 12500.00,
        "is_active": True,
        "created_at": datetime.now(),
        "updated_at": datetime.now(),
    }
    
    return {
        "customers": [mock_customer],
        "total": 1,
        "page": page,
        "page_size": page_size,
    }


@router.post("/", response_model=CustomerResponse)
async def create_customer(request: CustomerRequest, token: str = Depends(security)):
    """Create a new customer"""
    # TODO: Implement customer creation logic
    return {
        "id": 1,
        "name": request.name,
        "email": request.email,
        "phone": request.phone,
        "company": request.company,
        "address_line_1": request.address_line_1,
        "address_line_2": request.address_line_2,
        "city": request.city,
        "state": request.state,
        "postal_code": request.postal_code,
        "country": request.country,
        "tax_number": request.tax_number,
        "notes": request.notes,
        "total_invoices": 0,
        "total_amount": 0.0,
        "is_active": True,
        "created_at": datetime.now(),
        "updated_at": datetime.now(),
    }


@router.get("/{customer_id}", response_model=CustomerResponse)
async def get_customer(customer_id: int, token: str = Depends(security)):
    """Get customer by ID"""
    # TODO: Implement get customer by ID
    return {
        "id": customer_id,
        "name": "John Doe",
        "email": "john@example.com",
        "phone": "+1-555-123-4567",
        "company": "Acme Corporation",
        "address_line_1": "123 Business St",
        "address_line_2": "Suite 100",
        "city": "New York",
        "state": "NY",
        "postal_code": "10001",
        "country": "USA",
        "tax_number": "12-3456789",
        "notes": "Important client",
        "total_invoices": 5,
        "total_amount": 12500.00,
        "is_active": True,
        "created_at": datetime.now(),
        "updated_at": datetime.now(),
    }


@router.put("/{customer_id}", response_model=CustomerResponse)
async def update_customer(
    customer_id: int, request: CustomerRequest, token: str = Depends(security)
):
    """Update customer by ID"""
    # TODO: Implement customer update logic
    return {
        "id": customer_id,
        "name": request.name,
        "email": request.email,
        "phone": request.phone,
        "company": request.company,
        "address_line_1": request.address_line_1,
        "address_line_2": request.address_line_2,
        "city": request.city,
        "state": request.state,
        "postal_code": request.postal_code,
        "country": request.country,
        "tax_number": request.tax_number,
        "notes": request.notes,
        "total_invoices": 5,
        "total_amount": 12500.00,
        "is_active": True,
        "created_at": datetime.now(),
        "updated_at": datetime.now(),
    }


@router.delete("/{customer_id}")
async def delete_customer(customer_id: int, token: str = Depends(security)):
    """Delete customer by ID"""
    # TODO: Implement customer deletion logic
    return {"message": f"Customer {customer_id} deleted successfully"}


@router.get("/{customer_id}/invoices")
async def get_customer_invoices(
    customer_id: int,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    token: str = Depends(security),
):
    """Get all invoices for a customer"""
    # TODO: Implement get customer invoices
    return {
        "invoices": [],
        "total": 0,
        "page": page,
        "page_size": page_size,
    }


@router.post("/{customer_id}/activate")
async def activate_customer(customer_id: int, token: str = Depends(security)):
    """Activate customer"""
    # TODO: Implement customer activation logic
    return {"message": f"Customer {customer_id} activated successfully"}


@router.post("/{customer_id}/deactivate")
async def deactivate_customer(customer_id: int, token: str = Depends(security)):
    """Deactivate customer"""
    # TODO: Implement customer deactivation logic
    return {"message": f"Customer {customer_id} deactivated successfully"}