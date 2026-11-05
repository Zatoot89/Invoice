"""
InvoiceFlow Pro - Stripe Payment Service
"""
import stripe
from typing import Dict, Any, Optional, List
from decimal import Decimal
from datetime import datetime
import structlog

from app.core.config import settings
from app.core.exceptions import PaymentException, ExternalServiceException
from app.models.invoice import Invoice
from app.models.customer import Customer
from app.models.payment import Payment, PaymentStatus, PaymentMethod
from app.models.user import User

# Configure Stripe
stripe.api_key = settings.STRIPE_SECRET_KEY

logger = structlog.get_logger(__name__)


class StripeService:
    """
    Service for Stripe payment processing
    """
    
    def __init__(self):
        self.api_key = settings.STRIPE_SECRET_KEY
        self.webhook_secret = settings.STRIPE_WEBHOOK_SECRET
        self.publishable_key = settings.STRIPE_PUBLISHABLE_KEY
    
    async def create_customer(self, customer: Customer, user: User) -> str:
        """Create a Stripe customer"""
        try:
            stripe_customer = stripe.Customer.create(
                email=customer.email,
                name=customer.name,
                phone=customer.phone,
                address={
                    "line1": customer.address_line_1,
                    "line2": customer.address_line_2,
                    "city": customer.city,
                    "state": customer.state,
                    "postal_code": customer.postal_code,
                    "country": customer.country,
                } if customer.address_line_1 else None,
                metadata={
                    "invoiceflow_customer_id": str(customer.id),
                    "invoiceflow_user_id": str(user.id),
                    "company": customer.company or "",
                }
            )
            
            logger.info(f"Created Stripe customer: {stripe_customer.id}")
            return stripe_customer.id
            
        except stripe.error.StripeError as e:
            logger.error(f"Stripe customer creation failed: {str(e)}")
            raise ExternalServiceException("Stripe", f"Customer creation failed: {str(e)}")
    
    async def create_payment_intent(
        self,
        invoice: Invoice,
        customer: Customer,
        stripe_customer_id: Optional[str] = None,
        save_payment_method: bool = False
    ) -> Dict[str, Any]:
        """Create a Stripe PaymentIntent for an invoice"""
        try:
            # Create Stripe customer if not exists
            if not stripe_customer_id:
                user = invoice.user  # Assuming relationship is loaded
                stripe_customer_id = await self.create_customer(customer, user)
            
            # Convert amount to cents
            amount_cents = int(invoice.total * 100)
            
            # Create PaymentIntent
            intent = stripe.PaymentIntent.create(
                amount=amount_cents,
                currency=invoice.currency.lower(),
                customer=stripe_customer_id,
                receipt_email=customer.email,
                description=f"Payment for Invoice {invoice.invoice_number}",
                metadata={
                    "invoice_id": str(invoice.id),
                    "invoice_number": invoice.invoice_number,
                    "customer_id": str(customer.id),
                    "user_id": str(invoice.user_id),
                },
                setup_future_usage="on_session" if save_payment_method else None,
                automatic_payment_methods={
                    "enabled": True,
                },
            )
            
            logger.info(f"Created PaymentIntent: {intent.id} for invoice {invoice.id}")
            
            return {
                "payment_intent_id": intent.id,
                "client_secret": intent.client_secret,
                "amount": intent.amount,
                "currency": intent.currency,
                "status": intent.status,
                "publishable_key": self.publishable_key,
            }
            
        except stripe.error.StripeError as e:
            logger.error(f"PaymentIntent creation failed: {str(e)}")
            raise PaymentException(f"Payment setup failed: {str(e)}")
    
    async def confirm_payment_intent(self, payment_intent_id: str) -> Dict[str, Any]:
        """Confirm a PaymentIntent and get status"""
        try:
            intent = stripe.PaymentIntent.retrieve(payment_intent_id)
            
            return {
                "id": intent.id,
                "status": intent.status,
                "amount": intent.amount / 100,  # Convert back from cents
                "currency": intent.currency.upper(),
                "charges": [
                    {
                        "id": charge.id,
                        "status": charge.status,
                        "amount": charge.amount / 100,
                        "created": charge.created,
                        "receipt_url": charge.receipt_url,
                        "payment_method_details": charge.payment_method_details,
                    }
                    for charge in intent.charges.data
                ],
                "metadata": intent.metadata,
            }
            
        except stripe.error.StripeError as e:
            raise ExternalServiceException("Stripe", f"PaymentIntent retrieval failed: {str(e)}")
    
    async def create_checkout_session(
        self,
        invoice: Invoice,
        customer: Customer,
        success_url: str,
        cancel_url: str,
        stripe_customer_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create a Stripe Checkout session for hosted payment"""
        try:
            # Create Stripe customer if not exists
            if not stripe_customer_id:
                user = invoice.user
                stripe_customer_id = await self.create_customer(customer, user)
            
            # Create line items from invoice items
            line_items = []
            for item in invoice.items:
                line_items.append({
                    "price_data": {
                        "currency": invoice.currency.lower(),
                        "product_data": {
                            "name": item.description,
                            "metadata": {
                                "invoice_item_id": str(item.id),
                            }
                        },
                        "unit_amount": int(item.unit_price * 100),  # Convert to cents
                    },
                    "quantity": int(item.quantity),
                })
            
            # Add discount if applicable
            discounts = []
            if invoice.discount_amount > 0:
                # Create a coupon for the discount
                coupon = stripe.Coupon.create(
                    amount_off=int(invoice.discount_amount * 100),
                    currency=invoice.currency.lower(),
                    duration="once",
                    name=f"Discount for {invoice.invoice_number}",
                )
                discounts = [{"coupon": coupon.id}]
            
            # Create checkout session
            session = stripe.checkout.Session.create(
                customer=stripe_customer_id,
                payment_method_types=["card"],
                line_items=line_items,
                discounts=discounts,
                mode="payment",
                success_url=success_url,
                cancel_url=cancel_url,
                metadata={
                    "invoice_id": str(invoice.id),
                    "invoice_number": invoice.invoice_number,
                    "customer_id": str(customer.id),
                },
                payment_intent_data={
                    "receipt_email": customer.email,
                    "description": f"Payment for Invoice {invoice.invoice_number}",
                },
                allow_promotion_codes=True,
                billing_address_collection="required",
            )
            
            logger.info(f"Created Checkout session: {session.id} for invoice {invoice.id}")
            
            return {
                "session_id": session.id,
                "session_url": session.url,
                "payment_intent": session.payment_intent,
                "publishable_key": self.publishable_key,
            }
            
        except stripe.error.StripeError as e:
            logger.error(f"Checkout session creation failed: {str(e)}")
            raise PaymentException(f"Checkout setup failed: {str(e)}")
    
    async def handle_webhook(self, payload: bytes, sig_header: str) -> Dict[str, Any]:
        """Handle Stripe webhook events"""
        try:
            event = stripe.Webhook.construct_event(
                payload, sig_header, self.webhook_secret
            )
            
            logger.info(f"Received Stripe webhook: {event['type']}")
            
            # Handle different event types
            if event["type"] == "payment_intent.succeeded":
                return await self._handle_payment_success(event["data"]["object"])
            
            elif event["type"] == "payment_intent.payment_failed":
                return await self._handle_payment_failure(event["data"]["object"])
            
            elif event["type"] == "checkout.session.completed":
                return await self._handle_checkout_completion(event["data"]["object"])
            
            elif event["type"] == "invoice.payment_succeeded":
                return await self._handle_subscription_payment(event["data"]["object"])
            
            else:
                logger.info(f"Unhandled webhook event: {event['type']}")
                return {"status": "ignored", "event_type": event["type"]}
            
        except ValueError as e:
            logger.error(f"Invalid webhook payload: {str(e)}")
            raise PaymentException("Invalid webhook payload")
        
        except stripe.error.SignatureVerificationError as e:
            logger.error(f"Invalid webhook signature: {str(e)}")
            raise PaymentException("Invalid webhook signature")
        
        except Exception as e:
            logger.error(f"Webhook processing failed: {str(e)}")
            raise ExternalServiceException("Stripe", f"Webhook processing failed: {str(e)}")
    
    async def _handle_payment_success(self, payment_intent: Dict[str, Any]) -> Dict[str, Any]:
        """Handle successful payment"""
        try:
            invoice_id = payment_intent["metadata"].get("invoice_id")
            if not invoice_id:
                return {"status": "ignored", "reason": "No invoice_id in metadata"}
            
            # Get charge details
            charges = payment_intent.get("charges", {}).get("data", [])
            charge = charges[0] if charges else {}
            
            return {
                "status": "payment_succeeded",
                "invoice_id": invoice_id,
                "payment_intent_id": payment_intent["id"],
                "amount": payment_intent["amount"] / 100,
                "currency": payment_intent["currency"].upper(),
                "charge_id": charge.get("id"),
                "receipt_url": charge.get("receipt_url"),
                "payment_method": charge.get("payment_method_details", {}).get("type"),
            }
            
        except Exception as e:
            logger.error(f"Payment success handling failed: {str(e)}")
            return {"status": "error", "error": str(e)}
    
    async def _handle_payment_failure(self, payment_intent: Dict[str, Any]) -> Dict[str, Any]:
        """Handle failed payment"""
        invoice_id = payment_intent["metadata"].get("invoice_id")
        
        return {
            "status": "payment_failed",
            "invoice_id": invoice_id,
            "payment_intent_id": payment_intent["id"],
            "last_payment_error": payment_intent.get("last_payment_error", {}),
        }
    
    async def _handle_checkout_completion(self, session: Dict[str, Any]) -> Dict[str, Any]:
        """Handle completed checkout session"""
        invoice_id = session["metadata"].get("invoice_id")
        
        return {
            "status": "checkout_completed",
            "invoice_id": invoice_id,
            "session_id": session["id"],
            "payment_intent": session.get("payment_intent"),
            "payment_status": session.get("payment_status"),
        }
    
    async def _handle_subscription_payment(self, stripe_invoice: Dict[str, Any]) -> Dict[str, Any]:
        """Handle subscription payment (for recurring invoices)"""
        return {
            "status": "subscription_payment",
            "stripe_invoice_id": stripe_invoice["id"],
            "amount_paid": stripe_invoice["amount_paid"] / 100,
            "customer": stripe_invoice["customer"],
        }
    
    async def refund_payment(
        self,
        charge_id: str,
        amount: Optional[Decimal] = None,
        reason: str = "requested_by_customer"
    ) -> Dict[str, Any]:
        """Create a refund for a payment"""
        try:
            refund_data = {
                "charge": charge_id,
                "reason": reason,
            }
            
            if amount:
                refund_data["amount"] = int(amount * 100)  # Convert to cents
            
            refund = stripe.Refund.create(**refund_data)
            
            logger.info(f"Created refund: {refund.id} for charge {charge_id}")
            
            return {
                "refund_id": refund.id,
                "amount": refund.amount / 100,
                "currency": refund.currency.upper(),
                "status": refund.status,
                "charge": refund.charge,
            }
            
        except stripe.error.StripeError as e:
            logger.error(f"Refund creation failed: {str(e)}")
            raise PaymentException(f"Refund failed: {str(e)}")
    
    async def get_payment_methods(self, stripe_customer_id: str) -> List[Dict[str, Any]]:
        """Get saved payment methods for a customer"""
        try:
            payment_methods = stripe.PaymentMethod.list(
                customer=stripe_customer_id,
                type="card",
            )
            
            return [
                {
                    "id": pm.id,
                    "type": pm.type,
                    "card": {
                        "brand": pm.card.brand,
                        "last4": pm.card.last4,
                        "exp_month": pm.card.exp_month,
                        "exp_year": pm.card.exp_year,
                    } if pm.card else None,
                    "created": pm.created,
                }
                for pm in payment_methods.data
            ]
            
        except stripe.error.StripeError as e:
            logger.error(f"Payment methods retrieval failed: {str(e)}")
            raise ExternalServiceException("Stripe", f"Payment methods retrieval failed: {str(e)}")
    
    async def create_subscription(
        self,
        stripe_customer_id: str,
        price_id: str,
        metadata: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """Create a subscription for recurring payments"""
        try:
            subscription = stripe.Subscription.create(
                customer=stripe_customer_id,
                items=[{"price": price_id}],
                metadata=metadata or {},
                expand=["latest_invoice.payment_intent"],
            )
            
            return {
                "subscription_id": subscription.id,
                "status": subscription.status,
                "current_period_start": subscription.current_period_start,
                "current_period_end": subscription.current_period_end,
                "latest_invoice": subscription.latest_invoice,
            }
            
        except stripe.error.StripeError as e:
            logger.error(f"Subscription creation failed: {str(e)}")
            raise PaymentException(f"Subscription creation failed: {str(e)}")
    
    def validate_webhook_signature(self, payload: bytes, sig_header: str) -> bool:
        """Validate webhook signature"""
        try:
            stripe.Webhook.construct_event(payload, sig_header, self.webhook_secret)
            return True
        except (ValueError, stripe.error.SignatureVerificationError):
            return False