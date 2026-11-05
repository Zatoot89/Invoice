"""
InvoiceFlow Pro - Recurring Invoice Service
Handles automated recurring invoice generation and management
"""
from datetime import datetime, timedelta
from decimal import Decimal
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from dateutil.relativedelta import relativedelta
import logging

from app.models.invoice import Invoice, InvoiceItem, InvoiceStatus, InvoiceType, RecurrenceInterval
from app.models.customer import Customer
from app.models.user import User
from app.services.websocket_service import WebSocketService
from app.services.email_service import EmailService

logger = logging.getLogger(__name__)


class RecurringInvoiceService:
    def __init__(self, db: Session, websocket_service: WebSocketService, email_service: EmailService):
        self.db = db
        self.websocket_service = websocket_service
        self.email_service = email_service

    async def process_recurring_invoices(self, max_invoices: int = 100) -> Dict[str, Any]:
        """
        Process all due recurring invoices
        This method should be called by a scheduled task (e.g., Celery beat)
        """
        try:
            logger.info("Starting recurring invoice processing")
            
            # Find recurring invoices that are due for generation
            due_recurring_invoices = self._get_due_recurring_invoices(max_invoices)
            
            results = {
                'total_processed': 0,
                'successful_generations': 0,
                'failed_generations': 0,
                'errors': []
            }
            
            for recurring_invoice in due_recurring_invoices:
                try:
                    new_invoice = await self._generate_next_invoice(recurring_invoice)
                    if new_invoice:
                        results['successful_generations'] += 1
                        
                        # Send notification
                        await self._send_recurring_invoice_notification(recurring_invoice, new_invoice)
                    
                    results['total_processed'] += 1
                    
                except Exception as e:
                    logger.error(f"Failed to process recurring invoice {recurring_invoice.id}: {str(e)}")
                    results['errors'].append({
                        'invoice_id': recurring_invoice.id,
                        'invoice_number': recurring_invoice.invoice_number,
                        'error': str(e)
                    })
                    results['failed_generations'] += 1
            
            # Commit all changes
            self.db.commit()
            
            logger.info(f"Completed recurring invoice processing. Results: {results}")
            return results
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error in recurring invoice processing: {str(e)}")
            raise

    def _get_due_recurring_invoices(self, limit: int) -> List[Invoice]:
        """Get recurring invoices that are due for generation"""
        now = datetime.utcnow()
        
        return self.db.query(Invoice).filter(
            and_(
                Invoice.is_recurring == True,
                Invoice.next_recurrence_date <= now,
                Invoice.status.in_([InvoiceStatus.SENT, InvoiceStatus.PAID]),  # Only process active recurring invoices
                or_(
                    Invoice.recurrence_count.is_(None),  # Unlimited recurrences
                    Invoice.recurrence_count > 0  # Has remaining recurrences
                )
            )
        ).limit(limit).all()

    async def _generate_next_invoice(self, recurring_invoice: Invoice) -> Optional[Invoice]:
        """Generate the next invoice in the recurring series"""
        try:
            # Create new invoice based on the recurring template
            next_invoice_number = self._generate_next_invoice_number(recurring_invoice.user_id)
            
            # Calculate next issue and due dates
            next_issue_date = recurring_invoice.next_recurrence_date
            next_due_date = self._calculate_due_date(next_issue_date, recurring_invoice.customer.payment_terms)
            
            # Create new invoice
            new_invoice = Invoice(
                user_id=recurring_invoice.user_id,
                customer_id=recurring_invoice.customer_id,
                invoice_number=next_invoice_number,
                reference_number=recurring_invoice.reference_number,
                type=InvoiceType.STANDARD,  # Generated invoices are always standard
                status=InvoiceStatus.DRAFT,
                issue_date=next_issue_date,
                due_date=next_due_date,
                currency=recurring_invoice.currency,
                subtotal=recurring_invoice.subtotal,
                discount_percentage=recurring_invoice.discount_percentage,
                discount_amount=recurring_invoice.discount_amount,
                tax_rate=recurring_invoice.tax_rate,
                tax_amount=recurring_invoice.tax_amount,
                total=recurring_invoice.total,
                amount_due=recurring_invoice.total,
                notes=recurring_invoice.notes,
                terms_and_conditions=recurring_invoice.terms_and_conditions,
                footer_text=recurring_invoice.footer_text,
                parent_invoice_id=recurring_invoice.id,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            
            self.db.add(new_invoice)
            self.db.flush()  # Get the new invoice ID
            
            # Copy invoice items
            for item in recurring_invoice.items:
                new_item = InvoiceItem(
                    invoice_id=new_invoice.id,
                    description=item.description,
                    quantity=item.quantity,
                    unit_price=item.unit_price,
                    tax_rate=item.tax_rate,
                    tax_amount=item.tax_amount,
                    subtotal=item.subtotal,
                    total=item.total,
                    unit=item.unit,
                    sku=item.sku,
                    category=item.category,
                    sort_order=item.sort_order
                )
                self.db.add(new_item)
            
            # Update the recurring invoice's next recurrence date and count
            self._update_recurring_schedule(recurring_invoice)
            
            return new_invoice
            
        except Exception as e:
            logger.error(f"Error generating next invoice for recurring invoice {recurring_invoice.id}: {str(e)}")
            raise

    def _generate_next_invoice_number(self, user_id: int) -> str:
        """Generate the next invoice number for the user"""
        # Get the latest invoice number for this user
        latest_invoice = self.db.query(Invoice).filter(
            Invoice.user_id == user_id
        ).order_by(Invoice.id.desc()).first()
        
        if not latest_invoice:
            return "INV-0001"
        
        # Extract number from latest invoice
        try:
            # Assuming format like "INV-0001"
            parts = latest_invoice.invoice_number.split('-')
            if len(parts) >= 2:
                number = int(parts[-1])
                return f"INV-{str(number + 1).zfill(4)}"
            else:
                return "INV-0001"
        except (ValueError, IndexError):
            # Fallback to simple incrementing
            return f"INV-{datetime.utcnow().strftime('%Y%m%d')}-001"

    def _calculate_due_date(self, issue_date: datetime, payment_terms: int) -> datetime:
        """Calculate due date based on issue date and payment terms"""
        return issue_date + timedelta(days=payment_terms)

    def _update_recurring_schedule(self, recurring_invoice: Invoice):
        """Update the recurring invoice's next recurrence date and count"""
        # Calculate next recurrence date
        current_date = recurring_invoice.next_recurrence_date
        
        if recurring_invoice.recurrence_interval == RecurrenceInterval.WEEKLY:
            next_date = current_date + timedelta(weeks=1)
        elif recurring_invoice.recurrence_interval == RecurrenceInterval.MONTHLY:
            next_date = current_date + relativedelta(months=1)
        elif recurring_invoice.recurrence_interval == RecurrenceInterval.QUARTERLY:
            next_date = current_date + relativedelta(months=3)
        elif recurring_invoice.recurrence_interval == RecurrenceInterval.YEARLY:
            next_date = current_date + relativedelta(years=1)
        else:
            raise ValueError(f"Invalid recurrence interval: {recurring_invoice.recurrence_interval}")
        
        recurring_invoice.next_recurrence_date = next_date
        
        # Decrement recurrence count if it's not unlimited
        if recurring_invoice.recurrence_count is not None:
            recurring_invoice.recurrence_count -= 1
            
            # If this was the last recurrence, mark as completed
            if recurring_invoice.recurrence_count <= 0:
                recurring_invoice.is_recurring = False
                recurring_invoice.next_recurrence_date = None

    async def _send_recurring_invoice_notification(self, recurring_invoice: Invoice, new_invoice: Invoice):
        """Send notification about the generated recurring invoice"""
        try:
            # Send WebSocket notification
            await self.websocket_service.broadcast_to_user(
                recurring_invoice.user_id,
                {
                    'type': 'recurring_invoice_generated',
                    'data': {
                        'recurring_invoice_id': recurring_invoice.id,
                        'recurring_invoice_number': recurring_invoice.invoice_number,
                        'new_invoice_id': new_invoice.id,
                        'new_invoice_number': new_invoice.invoice_number,
                        'customer_name': new_invoice.customer.name,
                        'total': float(new_invoice.total),
                        'due_date': new_invoice.due_date.isoformat()
                    }
                }
            )
            
            # Send email notification to user
            user = self.db.query(User).filter(User.id == recurring_invoice.user_id).first()
            if user and user.email:
                await self.email_service.send_recurring_invoice_notification(
                    user.email,
                    {
                        'user_name': user.full_name or user.email,
                        'recurring_invoice_number': recurring_invoice.invoice_number,
                        'new_invoice_number': new_invoice.invoice_number,
                        'customer_name': new_invoice.customer.name,
                        'total': new_invoice.total,
                        'due_date': new_invoice.due_date,
                        'dashboard_url': f"{user.settings.get('base_url', 'https://app.invoiceflow.com')}/dashboard"
                    }
                )
        
        except Exception as e:
            logger.error(f"Error sending recurring invoice notification: {str(e)}")
            # Don't raise here as the invoice was successfully generated

    async def create_recurring_invoice(self, user_id: int, invoice_data: Dict[str, Any]) -> Invoice:
        """Create a new recurring invoice template"""
        try:
            # Validate recurring settings
            if not invoice_data.get('is_recurring'):
                raise ValueError("Invoice must be marked as recurring")
            
            if not invoice_data.get('recurrence_interval'):
                raise ValueError("Recurrence interval is required")
            
            # Set initial recurring dates
            issue_date = datetime.fromisoformat(invoice_data['issue_date'])
            next_recurrence_date = self._calculate_next_recurrence_date(
                issue_date,
                RecurrenceInterval(invoice_data['recurrence_interval'])
            )
            
            # Create the recurring invoice
            recurring_invoice = Invoice(
                user_id=user_id,
                customer_id=invoice_data['customer_id'],
                invoice_number=invoice_data['invoice_number'],
                reference_number=invoice_data.get('reference_number'),
                type=InvoiceType.RECURRING,
                status=InvoiceStatus.SENT,  # Recurring templates are "active"
                issue_date=issue_date,
                due_date=datetime.fromisoformat(invoice_data['due_date']),
                currency=invoice_data.get('currency', 'USD'),
                subtotal=Decimal(str(invoice_data['subtotal'])),
                discount_percentage=Decimal(str(invoice_data.get('discount_percentage', 0))),
                discount_amount=Decimal(str(invoice_data.get('discount_amount', 0))),
                tax_rate=Decimal(str(invoice_data.get('tax_rate', 0))),
                tax_amount=Decimal(str(invoice_data.get('tax_amount', 0))),
                total=Decimal(str(invoice_data['total'])),
                amount_due=Decimal(str(invoice_data['total'])),
                is_recurring=True,
                recurrence_interval=RecurrenceInterval(invoice_data['recurrence_interval']),
                recurrence_count=invoice_data.get('recurrence_count'),
                next_recurrence_date=next_recurrence_date,
                notes=invoice_data.get('notes'),
                terms_and_conditions=invoice_data.get('terms_and_conditions'),
                footer_text=invoice_data.get('footer_text')
            )
            
            self.db.add(recurring_invoice)
            self.db.flush()
            
            # Add invoice items
            for item_data in invoice_data.get('items', []):
                item = InvoiceItem(
                    invoice_id=recurring_invoice.id,
                    description=item_data['description'],
                    quantity=Decimal(str(item_data['quantity'])),
                    unit_price=Decimal(str(item_data['unit_price'])),
                    tax_rate=Decimal(str(item_data.get('tax_rate', 0))),
                    tax_amount=Decimal(str(item_data.get('tax_amount', 0))),
                    subtotal=Decimal(str(item_data['subtotal'])),
                    total=Decimal(str(item_data['total'])),
                    unit=item_data.get('unit'),
                    sku=item_data.get('sku'),
                    category=item_data.get('category'),
                    sort_order=item_data.get('sort_order', 0)
                )
                self.db.add(item)
            
            self.db.commit()
            return recurring_invoice
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error creating recurring invoice: {str(e)}")
            raise

    def _calculate_next_recurrence_date(self, start_date: datetime, interval: RecurrenceInterval) -> datetime:
        """Calculate the next recurrence date based on interval"""
        if interval == RecurrenceInterval.WEEKLY:
            return start_date + timedelta(weeks=1)
        elif interval == RecurrenceInterval.MONTHLY:
            return start_date + relativedelta(months=1)
        elif interval == RecurrenceInterval.QUARTERLY:
            return start_date + relativedelta(months=3)
        elif interval == RecurrenceInterval.YEARLY:
            return start_date + relativedelta(years=1)
        else:
            raise ValueError(f"Invalid recurrence interval: {interval}")

    async def get_recurring_invoices(self, user_id: int) -> List[Invoice]:
        """Get all recurring invoice templates for a user"""
        return self.db.query(Invoice).filter(
            and_(
                Invoice.user_id == user_id,
                Invoice.is_recurring == True,
                Invoice.type == InvoiceType.RECURRING
            )
        ).all()

    async def get_generated_invoices(self, user_id: int, parent_invoice_id: int) -> List[Invoice]:
        """Get all invoices generated from a recurring template"""
        return self.db.query(Invoice).filter(
            and_(
                Invoice.user_id == user_id,
                Invoice.parent_invoice_id == parent_invoice_id
            )
        ).order_by(Invoice.created_at.desc()).all()

    async def update_recurring_invoice(self, user_id: int, invoice_id: int, update_data: Dict[str, Any]) -> Invoice:
        """Update a recurring invoice template"""
        recurring_invoice = self.db.query(Invoice).filter(
            and_(
                Invoice.id == invoice_id,
                Invoice.user_id == user_id,
                Invoice.is_recurring == True
            )
        ).first()
        
        if not recurring_invoice:
            raise ValueError("Recurring invoice not found")
        
        # Update allowed fields
        for field, value in update_data.items():
            if field in ['recurrence_interval', 'recurrence_count', 'notes', 'terms_and_conditions']:
                setattr(recurring_invoice, field, value)
        
        # Recalculate next recurrence date if interval changed
        if 'recurrence_interval' in update_data:
            recurring_invoice.next_recurrence_date = self._calculate_next_recurrence_date(
                datetime.utcnow(),
                RecurrenceInterval(update_data['recurrence_interval'])
            )
        
        self.db.commit()
        return recurring_invoice

    async def cancel_recurring_invoice(self, user_id: int, invoice_id: int) -> Invoice:
        """Cancel a recurring invoice (stop future generations)"""
        recurring_invoice = self.db.query(Invoice).filter(
            and_(
                Invoice.id == invoice_id,
                Invoice.user_id == user_id,
                Invoice.is_recurring == True
            )
        ).first()
        
        if not recurring_invoice:
            raise ValueError("Recurring invoice not found")
        
        recurring_invoice.is_recurring = False
        recurring_invoice.next_recurrence_date = None
        recurring_invoice.status = InvoiceStatus.CANCELLED
        
        self.db.commit()
        return recurring_invoice