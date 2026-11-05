"""
InvoiceFlow Pro - Recurring Invoice Celery Tasks
Background tasks for automated recurring invoice processing
"""
from celery import Celery
from datetime import datetime
import logging
from typing import Dict, Any

from app.core.database import SessionLocal
from app.services.recurring_service import RecurringInvoiceService
from app.services.websocket_service import WebSocketService
from app.services.email_service import EmailService

logger = logging.getLogger(__name__)

# Initialize Celery app
celery_app = Celery('invoiceflow_tasks')


@celery_app.task(bind=True, name='process_recurring_invoices')
def process_recurring_invoices_task(self, max_invoices: int = 100) -> Dict[str, Any]:
    """
    Celery task to process due recurring invoices
    This task should be scheduled to run periodically (e.g., daily)
    """
    task_id = self.request.id
    logger.info(f"Starting recurring invoice processing task {task_id}")
    
    db = SessionLocal()
    try:
        # Initialize services
        websocket_service = WebSocketService()
        email_service = EmailService()
        recurring_service = RecurringInvoiceService(db, websocket_service, email_service)
        
        # Process recurring invoices
        results = await recurring_service.process_recurring_invoices(max_invoices)
        
        logger.info(f"Completed recurring invoice processing task {task_id}. Results: {results}")
        
        # Send summary notification to admin users if there were issues
        if results['failed_generations'] > 0:
            await _send_admin_error_notification(results)
        
        return {
            'task_id': task_id,
            'timestamp': datetime.utcnow().isoformat(),
            'status': 'completed',
            'results': results
        }
        
    except Exception as e:
        logger.error(f"Error in recurring invoice processing task {task_id}: {str(e)}")
        
        # Retry with exponential backoff
        raise self.retry(
            exc=e,
            countdown=60 * (2 ** self.request.retries),
            max_retries=3
        )
        
    finally:
        db.close()


@celery_app.task(name='send_recurring_invoice_reminders')
def send_recurring_invoice_reminders_task() -> Dict[str, Any]:
    """
    Celery task to send reminders about upcoming recurring invoice generations
    This can be scheduled to run weekly to remind users about upcoming recurring invoices
    """
    task_id = self.request.id
    logger.info(f"Starting recurring invoice reminders task {task_id}")
    
    db = SessionLocal()
    try:
        from app.models.invoice import Invoice, InvoiceType
        from app.models.user import User
        from sqlalchemy import and_
        from datetime import timedelta
        
        # Find recurring invoices due in the next 7 days
        next_week = datetime.utcnow() + timedelta(days=7)
        
        upcoming_recurring = db.query(Invoice).filter(
            and_(
                Invoice.is_recurring == True,
                Invoice.type == InvoiceType.RECURRING,
                Invoice.next_recurrence_date <= next_week,
                Invoice.next_recurrence_date >= datetime.utcnow()
            )
        ).all()
        
        results = {
            'reminders_sent': 0,
            'failed_reminders': 0,
            'errors': []
        }
        
        # Group by user to send one summary email per user
        user_invoices = {}
        for invoice in upcoming_recurring:
            if invoice.user_id not in user_invoices:
                user_invoices[invoice.user_id] = []
            user_invoices[invoice.user_id].append(invoice)
        
        # Send reminders
        email_service = EmailService()
        for user_id, invoices in user_invoices.items():
            try:
                user = db.query(User).filter(User.id == user_id).first()
                if user and user.email:
                    await email_service.send_recurring_invoice_reminder(
                        user.email,
                        {
                            'user_name': user.full_name or user.email,
                            'upcoming_invoices': [
                                {
                                    'invoice_number': inv.invoice_number,
                                    'customer_name': inv.customer.name,
                                    'total': inv.total,
                                    'next_date': inv.next_recurrence_date,
                                    'interval': inv.recurrence_interval.value
                                }
                                for inv in invoices
                            ],
                            'dashboard_url': f"{user.settings.get('base_url', 'https://app.invoiceflow.com')}/recurring"
                        }
                    )
                    results['reminders_sent'] += 1
                
            except Exception as e:
                logger.error(f"Failed to send reminder to user {user_id}: {str(e)}")
                results['errors'].append({
                    'user_id': user_id,
                    'error': str(e)
                })
                results['failed_reminders'] += 1
        
        logger.info(f"Completed recurring invoice reminders task {task_id}. Results: {results}")
        
        return {
            'task_id': task_id,
            'timestamp': datetime.utcnow().isoformat(),
            'status': 'completed',
            'results': results
        }
        
    except Exception as e:
        logger.error(f"Error in recurring invoice reminders task {task_id}: {str(e)}")
        return {
            'task_id': task_id,
            'timestamp': datetime.utcnow().isoformat(),
            'status': 'failed',
            'error': str(e)
        }
        
    finally:
        db.close()


@celery_app.task(name='cleanup_expired_recurring_invoices')
def cleanup_expired_recurring_invoices_task() -> Dict[str, Any]:
    """
    Celery task to clean up expired recurring invoice templates
    This can be scheduled to run monthly to archive old recurring templates
    """
    task_id = self.request.id
    logger.info(f"Starting expired recurring invoices cleanup task {task_id}")
    
    db = SessionLocal()
    try:
        from app.models.invoice import Invoice, InvoiceType, InvoiceStatus
        from sqlalchemy import and_
        from datetime import timedelta
        
        # Find recurring invoices that have been cancelled or completed for more than 6 months
        six_months_ago = datetime.utcnow() - timedelta(days=180)
        
        expired_recurring = db.query(Invoice).filter(
            and_(
                Invoice.type == InvoiceType.RECURRING,
                Invoice.is_recurring == False,  # Already stopped
                Invoice.updated_at < six_months_ago,
                or_(
                    Invoice.status == InvoiceStatus.CANCELLED,
                    and_(
                        Invoice.recurrence_count == 0,
                        Invoice.next_recurrence_date.is_(None)
                    )
                )
            )
        ).all()
        
        results = {
            'archived_invoices': 0,
            'errors': []
        }
        
        # Archive expired recurring invoices (soft delete or status change)
        for invoice in expired_recurring:
            try:
                # You could either soft delete or change status
                # For now, we'll just add a note and keep them
                if not invoice.notes:
                    invoice.notes = ""
                invoice.notes += f"\n[ARCHIVED {datetime.utcnow().strftime('%Y-%m-%d')}] Recurring template archived due to inactivity"
                
                results['archived_invoices'] += 1
                
            except Exception as e:
                logger.error(f"Failed to archive recurring invoice {invoice.id}: {str(e)}")
                results['errors'].append({
                    'invoice_id': invoice.id,
                    'error': str(e)
                })
        
        db.commit()
        
        logger.info(f"Completed expired recurring invoices cleanup task {task_id}. Results: {results}")
        
        return {
            'task_id': task_id,
            'timestamp': datetime.utcnow().isoformat(),
            'status': 'completed',
            'results': results
        }
        
    except Exception as e:
        logger.error(f"Error in expired recurring invoices cleanup task {task_id}: {str(e)}")
        db.rollback()
        return {
            'task_id': task_id,
            'timestamp': datetime.utcnow().isoformat(),
            'status': 'failed',
            'error': str(e)
        }
        
    finally:
        db.close()


async def _send_admin_error_notification(results: Dict[str, Any]):
    """Send error notification to admin users when recurring invoice processing fails"""
    try:
        db = SessionLocal()
        from app.models.user import User
        
        # Get admin users
        admin_users = db.query(User).filter(User.is_admin == True).all()
        
        if not admin_users:
            return
        
        email_service = EmailService()
        for admin in admin_users:
            if admin.email:
                await email_service.send_admin_notification(
                    admin.email,
                    {
                        'admin_name': admin.full_name or admin.email,
                        'notification_type': 'Recurring Invoice Processing Errors',
                        'details': {
                            'total_processed': results['total_processed'],
                            'successful_generations': results['successful_generations'],
                            'failed_generations': results['failed_generations'],
                            'errors': results['errors'][:10]  # Limit to first 10 errors
                        },
                        'timestamp': datetime.utcnow(),
                        'dashboard_url': 'https://app.invoiceflow.com/admin/recurring'
                    }
                )
        
        db.close()
        
    except Exception as e:
        logger.error(f"Failed to send admin error notification: {str(e)}")


# Celery Beat schedule configuration
celery_app.conf.beat_schedule = {
    'process-recurring-invoices-daily': {
        'task': 'process_recurring_invoices',
        'schedule': 86400.0,  # Run daily (24 hours)
        'args': (100,)  # Max 100 invoices per run
    },
    'send-recurring-reminders-weekly': {
        'task': 'send_recurring_invoice_reminders',
        'schedule': 604800.0,  # Run weekly (7 days)
    },
    'cleanup-expired-recurring-monthly': {
        'task': 'cleanup_expired_recurring_invoices',
        'schedule': 2592000.0,  # Run monthly (30 days)
    }
}

celery_app.conf.timezone = 'UTC'