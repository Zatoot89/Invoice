"""
InvoiceFlow Pro - API Routes
"""
from fastapi import APIRouter

# Import route modules
from app.api.v1 import auth, users, invoices, customers, payments, analytics, pdf, bulk, recurring

# Create main API router
api_router = APIRouter()

# Include route modules
api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(users.router, prefix="/users", tags=["Users"])
api_router.include_router(customers.router, prefix="/customers", tags=["Customers"])
api_router.include_router(invoices.router, prefix="/invoices", tags=["Invoices"])
api_router.include_router(payments.router, prefix="/payments", tags=["Payments"])
api_router.include_router(analytics.router, prefix="/analytics", tags=["Analytics"])
api_router.include_router(pdf.router, prefix="/pdf", tags=["PDF Generation"])
api_router.include_router(bulk.router, prefix="/bulk", tags=["Bulk Operations"])
api_router.include_router(recurring.router, prefix="/recurring", tags=["Recurring Invoices"])