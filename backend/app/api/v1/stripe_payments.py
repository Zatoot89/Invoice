"""
InvoiceFlow Pro - Stripe Payment API Routes
"""
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
from decimal import Decimal

from app.core.deps import get_db, get_current_user, validate_invoice_access
from app.services.stripe_service import StripeService
from app.services.invoice_service import InvoiceService
from app.services.customer_service import CustomerService
from app.services.payment_service import PaymentService
from app.models.user import User
from app.core.exceptions import PaymentException
from app.tasks.email_tasks import send_payment_confirmation_task

router = APIRouter()


# Pydantic models
class PaymentIntentRequest(BaseModel):
    invoice_id: int
    save_payment_method: bool = False


class CheckoutSessionRequest(BaseModel):
    invoice_id: int
    success_url: str
    cancel_url: str


class RefundRequest(BaseModel):
    charge_id: str
    amount: Optional[Decimal] = None
    reason: str = "requested_by_customer"


# Response models
class PaymentIntentResponse(BaseModel):
    payment_intent_id: str
    client_secret: str
    amount: int
    currency: str
    status: str
    publishable_key: str


class CheckoutSessionResponse(BaseModel):
    session_id: str
    session_url: str
    payment_intent: Optional[str]
    publishable_key: str


class PaymentMethodResponse(BaseModel):
    id: str
    type: str
    card: Optional[Dict[str, Any]]
    created: int


@router.post("/create-payment-intent", response_model=PaymentIntentResponse)
async def create_payment_intent(
    request: PaymentIntentRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _: bool = Depends(validate_invoice_access)
):
    """Create a Stripe PaymentIntent for an invoice"""
    try:
        # Get services
        stripe_service = StripeService()
        invoice_service = InvoiceService(db)
        customer_service = CustomerService(db)
        
        # Get invoice and customer
        invoice = await invoice_service.get_by_id_with_items(request.invoice_id)
        if not invoice:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Invoice not found"
            )
        
        customer = await customer_service.get_by_id(invoice.customer_id)
        if not customer:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Customer not found"
            )
        
        # Check if invoice is already paid
        if invoice.amount_due <= 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invoice is already fully paid"
            )
        
        # Create PaymentIntent
        result = await stripe_service.create_payment_intent(
            invoice=invoice,
            customer=customer,
            save_payment_method=request.save_payment_method
        )
        
        return PaymentIntentResponse(**result)
        
    except PaymentException as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Payment intent creation failed: {str(e)}"
        )


@router.post("/create-checkout-session", response_model=CheckoutSessionResponse)
async def create_checkout_session(
    request: CheckoutSessionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _: bool = Depends(validate_invoice_access)
):
    """Create a Stripe Checkout session for hosted payment"""
    try:
        # Get services
        stripe_service = StripeService()
        invoice_service = InvoiceService(db)
        customer_service = CustomerService(db)
        
        # Get invoice and customer
        invoice = await invoice_service.get_by_id_with_items(request.invoice_id)
        customer = await customer_service.get_by_id(invoice.customer_id)
        
        # Create checkout session
        result = await stripe_service.create_checkout_session(
            invoice=invoice,
            customer=customer,
            success_url=request.success_url,
            cancel_url=request.cancel_url
        )
        
        return CheckoutSessionResponse(**result)
        
    except PaymentException as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/payment-intent/{payment_intent_id}")
async def get_payment_intent(
    payment_intent_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get PaymentIntent status and details"""
    try:
        stripe_service = StripeService()
        result = await stripe_service.confirm_payment_intent(payment_intent_id)
        return result
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"PaymentIntent retrieval failed: {str(e)}"
        )


@router.post("/webhook")
async def stripe_webhook(request: Request, db: Session = Depends(get_db)):
    """Handle Stripe webhook events"""
    try:
        # Get request body and signature
        payload = await request.body()
        sig_header = request.headers.get("stripe-signature")
        
        if not sig_header:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Missing Stripe signature header"
            )
        
        # Process webhook
        stripe_service = StripeService()
        result = await stripe_service.handle_webhook(payload, sig_header)
        
        # Handle payment success
        if result.get("status") == "payment_succeeded":
            await _process_successful_payment(result, db)
        elif result.get("status") == "checkout_completed":
            await _process_checkout_completion(result, db)
        
        return {"status": "success", "processed": result}
        
    except PaymentException as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Webhook processing failed: {str(e)}"
        )


async def _process_successful_payment(result: Dict[str, Any], db: Session):
    """Process a successful payment from webhook"""
    try:
        invoice_id = int(result["invoice_id"])
        amount = Decimal(str(result["amount"]))
        
        # Get services
        invoice_service = InvoiceService(db)
        payment_service = PaymentService(db)
        
        # Create payment record
        payment_data = {
            "invoice_id": invoice_id,
            "amount": amount,
            "currency": result["currency"],
            "payment_method": "stripe",
            "gateway_provider": "stripe",
            "gateway_transaction_id": result["payment_intent_id"],
            "transaction_id": result.get("charge_id"),
            "receipt_url": result.get("receipt_url"),
            "status": "completed",
        }
        
        payment = await payment_service.create_payment(payment_data)
        
        # Update invoice
        await invoice_service.record_payment(invoice_id, amount, payment.id)
        
        # Send confirmation email
        from datetime import datetime
        send_payment_confirmation_task.delay(
            invoice_id=invoice_id,
            payment_amount=float(amount),
            payment_date=datetime.now().isoformat()
        )
        
    except Exception as e:
        # Log error but don't fail the webhook
        import structlog
        logger = structlog.get_logger(__name__)
        logger.error(f"Payment processing failed: {str(e)}")


async def _process_checkout_completion(result: Dict[str, Any], db: Session):
    """Process a completed checkout session"""
    # Similar to payment success, but from checkout session
    if result.get("payment_status") == "paid":
        # Retrieve the PaymentIntent to get payment details
        stripe_service = StripeService()
        payment_intent_id = result.get("payment_intent")
        
        if payment_intent_id:
            payment_details = await stripe_service.confirm_payment_intent(payment_intent_id)
            
            # Process as successful payment
            payment_result = {
                "status": "payment_succeeded",
                "invoice_id": result["invoice_id"],
                "payment_intent_id": payment_intent_id,
                "amount": payment_details["amount"],
                "currency": payment_details["currency"],
                "charge_id": payment_details["charges"][0]["id"] if payment_details["charges"] else None,
                "receipt_url": payment_details["charges"][0]["receipt_url"] if payment_details["charges"] else None,
            }
            
            await _process_successful_payment(payment_result, db)


@router.post("/refund")
async def create_refund(
    request: RefundRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a refund for a payment"""
    try:
        stripe_service = StripeService()
        result = await stripe_service.refund_payment(
            charge_id=request.charge_id,
            amount=request.amount,
            reason=request.reason
        )
        
        # TODO: Update payment record with refund information
        
        return result
        
    except PaymentException as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/customer/{customer_id}/payment-methods", response_model=List[PaymentMethodResponse])
async def get_customer_payment_methods(
    customer_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get saved payment methods for a customer"""
    try:
        # TODO: Get Stripe customer ID from database
        stripe_customer_id = "cus_example"  # This should come from customer record
        
        stripe_service = StripeService()
        payment_methods = await stripe_service.get_payment_methods(stripe_customer_id)
        
        return [PaymentMethodResponse(**pm) for pm in payment_methods]
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Payment methods retrieval failed: {str(e)}"
        )


@router.get("/config")
async def get_stripe_config(current_user: User = Depends(get_current_user)):
    """Get Stripe configuration for frontend"""
    stripe_service = StripeService()
    
    return {
        "publishable_key": stripe_service.publishable_key,
        "country": "US",  # TODO: Make this configurable
        "currency": "usd",
        "payment_methods": ["card"],
    }