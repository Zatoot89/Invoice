"""
InvoiceFlow Pro - Email Background Tasks
"""
from celery import current_app
from sqlalchemy.orm import Session
from typing import Optional
import structlog

from app.tasks import celery_app
from app.core.database import SessionLocal
from app.services.email_service import EmailService
from app.services.pdf_service import PDFService
from app.services.user_service import UserService
from app.services.customer_service import CustomerService
from app.services.invoice_service import InvoiceService
from app.core.exceptions import ExternalServiceException

logger = structlog.get_logger(__name__)


@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def send_invoice_email_task(
    self,
    invoice_id: int,
    custom_message: Optional[str] = None,
    attach_pdf: bool = True
):
    """Send invoice email with optional PDF attachment"""
    db: Session = SessionLocal()
    
    try:
        # Get services
        email_service = EmailService()
        pdf_service = PDFService()
        invoice_service = InvoiceService(db)
        customer_service = CustomerService(db)
        user_service = UserService(db)
        
        # Get data
        invoice = await invoice_service.get_by_id_with_items(invoice_id)
        if not invoice:
            raise Exception(f"Invoice {invoice_id} not found")
        
        customer = await customer_service.get_by_id(invoice.customer_id)
        if not customer:
            raise Exception(f"Customer {invoice.customer_id} not found")
        
        user = await user_service.get_by_id(invoice.user_id)
        if not user:
            raise Exception(f"User {invoice.user_id} not found")
        
        # Generate PDF if requested
        pdf_attachment = None
        if attach_pdf:
            try:
                pdf_attachment = await pdf_service.create_invoice_pdf(
                    invoice=invoice,
                    customer=customer,
                    user=user,
                    items=invoice.items,
                    template="professional"
                )
            except Exception as e:
                logger.warning(f"Failed to generate PDF for invoice {invoice_id}: {str(e)}")
        
        # Send email
        success = await email_service.send_invoice_email(
            invoice=invoice,
            customer=customer,
            user=user,
            pdf_attachment=pdf_attachment,
            custom_message=custom_message
        )
        
        if success:
            # Update invoice email tracking
            await invoice_service.mark_invoice_sent(invoice_id)
            logger.info(f"Invoice email sent successfully for invoice {invoice_id}")
        else:
            raise Exception("Email sending failed")
        
        return {
            "status": "success",
            "invoice_id": invoice_id,
            "customer_email": customer.email
        }
        
    except Exception as e:
        logger.error(f"Failed to send invoice email for invoice {invoice_id}: {str(e)}")
        
        # Retry logic
        if self.request.retries < self.max_retries:
            raise self.retry(countdown=60 * (2 ** self.request.retries))
        
        # Mark as failed after max retries
        return {
            "status": "failed",
            "invoice_id": invoice_id,
            "error": str(e)
        }
    
    finally:
        db.close()


@celery_app.task(bind=True, max_retries=3)
def send_payment_confirmation_task(
    self,
    invoice_id: int,
    payment_amount: float,
    payment_date: str
):
    """Send payment confirmation email"""
    db: Session = SessionLocal()
    
    try:
        from datetime import datetime
        
        # Get services
        email_service = EmailService()
        invoice_service = InvoiceService(db)
        customer_service = CustomerService(db)
        user_service = UserService(db)
        
        # Get data
        invoice = await invoice_service.get_by_id(invoice_id)
        customer = await customer_service.get_by_id(invoice.customer_id)
        user = await user_service.get_by_id(invoice.user_id)
        
        # Send email
        success = await email_service.send_payment_confirmation_email(
            invoice=invoice,
            customer=customer,
            user=user,
            payment_amount=payment_amount,
            payment_date=datetime.fromisoformat(payment_date)
        )
        
        if success:
            logger.info(f"Payment confirmation sent for invoice {invoice_id}")
        
        return {"status": "success" if success else "failed"}
        
    except Exception as e:
        logger.error(f"Failed to send payment confirmation: {str(e)}")
        raise self.retry(countdown=60 * (2 ** self.request.retries))
    
    finally:
        db.close()


@celery_app.task(bind=True, max_retries=3)
def send_overdue_reminders_task(self):
    """Send overdue payment reminders for all overdue invoices"""
    db: Session = SessionLocal()
    
    try:
        email_service = EmailService()
        invoice_service = InvoiceService(db)
        customer_service = CustomerService(db)
        user_service = UserService(db)
        
        # Get overdue invoices
        overdue_invoices = await invoice_service.get_overdue_invoices()
        
        sent_count = 0
        failed_count = 0
        
        for invoice in overdue_invoices:
            try:
                customer = await customer_service.get_by_id(invoice.customer_id)
                user = await user_service.get_by_id(invoice.user_id)
                
                # Calculate days overdue
                from datetime import datetime, timezone
                days_overdue = (datetime.now(timezone.utc) - invoice.due_date).days
                
                # Send reminder
                success = await email_service.send_overdue_reminder_email(
                    invoice=invoice,
                    customer=customer,
                    user=user,
                    days_overdue=days_overdue
                )
                
                if success:
                    sent_count += 1
                    # Update last reminder sent
                    await invoice_service.update_last_reminder_sent(invoice.id)
                else:
                    failed_count += 1
                    
            except Exception as e:
                logger.error(f"Failed to send overdue reminder for invoice {invoice.id}: {str(e)}")
                failed_count += 1
        
        logger.info(f"Overdue reminders: {sent_count} sent, {failed_count} failed")
        
        return {
            "status": "completed",
            "sent_count": sent_count,
            "failed_count": failed_count
        }
        
    except Exception as e:
        logger.error(f"Failed to process overdue reminders: {str(e)}")
        raise self.retry(countdown=300)  # Retry in 5 minutes
    
    finally:
        db.close()


@celery_app.task
def send_welcome_email_task(user_id: int):
    """Send welcome email to new user"""
    db: Session = SessionLocal()
    
    try:
        email_service = EmailService()
        user_service = UserService(db)
        
        user = await user_service.get_by_id(user_id)
        if not user:
            raise Exception(f"User {user_id} not found")
        
        success = await email_service.send_welcome_email(user)
        
        if success:
            logger.info(f"Welcome email sent to user {user_id}")
        
        return {"status": "success" if success else "failed"}
        
    except Exception as e:
        logger.error(f"Failed to send welcome email: {str(e)}")
        return {"status": "failed", "error": str(e)}
    
    finally:
        db.close()


@celery_app.task
def send_password_reset_email_task(user_id: int, reset_token: str):
    """Send password reset email"""
    db: Session = SessionLocal()
    
    try:
        email_service = EmailService()
        user_service = UserService(db)
        
        user = await user_service.get_by_id(user_id)
        if not user:
            raise Exception(f"User {user_id} not found")
        
        success = await email_service.send_password_reset_email(user, reset_token)
        
        return {"status": "success" if success else "failed"}
        
    except Exception as e:
        logger.error(f"Failed to send password reset email: {str(e)}")
        return {"status": "failed", "error": str(e)}
    
    finally:
        db.close()


@celery_app.task
def send_verification_email_task(user_id: int, verification_token: str):
    """Send email verification email"""
    db: Session = SessionLocal()
    
    try:
        email_service = EmailService()
        user_service = UserService(db)
        
        user = await user_service.get_by_id(user_id)
        if not user:
            raise Exception(f"User {user_id} not found")
        
        success = await email_service.send_verification_email(user, verification_token)
        
        return {"status": "success" if success else "failed"}
        
    except Exception as e:
        logger.error(f"Failed to send verification email: {str(e)}")
        return {"status": "failed", "error": str(e)}
    
    finally:
        db.close()


@celery_app.task
def test_email_configuration_task():
    """Test email configuration"""
    try:
        email_service = EmailService()
        success = email_service.test_email_connection()
        
        return {
            "status": "success" if success else "failed",
            "smtp_server": email_service.smtp_server,
            "smtp_port": email_service.smtp_port,
            "use_tls": email_service.use_tls
        }
        
    except Exception as e:
        return {"status": "failed", "error": str(e)}


# Periodic tasks
@celery_app.task
def daily_overdue_reminders():
    """Daily task to send overdue reminders"""
    return send_overdue_reminders_task.delay()


@celery_app.task
def weekly_email_summary():
    """Weekly email summary for users"""
    # TODO: Implement weekly summary emails
    pass