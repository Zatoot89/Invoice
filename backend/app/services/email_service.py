"""
InvoiceFlow Pro - Email Service
"""
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from typing import List, Optional, Dict, Any
import jinja2
from pathlib import Path
import asyncio
import aiofiles
from datetime import datetime

from app.core.config import settings
from app.models.invoice import Invoice
from app.models.customer import Customer
from app.models.user import User
from app.core.exceptions import ExternalServiceException


class EmailTemplateEngine:
    """
    Email template rendering engine using Jinja2
    """
    
    def __init__(self):
        # Set up Jinja2 environment
        template_dir = Path(__file__).parent.parent / "templates" / "email"
        self.env = jinja2.Environment(
            loader=jinja2.FileSystemLoader(template_dir),
            autoescape=jinja2.select_autoescape(['html', 'xml'])
        )
    
    def render_template(self, template_name: str, **context) -> str:
        """Render email template with context"""
        try:
            template = self.env.get_template(template_name)
            return template.render(**context)
        except jinja2.TemplateNotFound:
            raise ExternalServiceException("Email", f"Template {template_name} not found")
        except Exception as e:
            raise ExternalServiceException("Email", f"Template rendering failed: {str(e)}")


class EmailService:
    """
    Service for sending emails with templates and attachments
    """
    
    def __init__(self):
        self.smtp_server = settings.MAIL_SERVER
        self.smtp_port = settings.MAIL_PORT
        self.username = settings.MAIL_USERNAME
        self.password = settings.MAIL_PASSWORD
        self.from_email = settings.MAIL_FROM or settings.MAIL_USERNAME
        self.use_tls = settings.MAIL_TLS
        self.use_ssl = settings.MAIL_SSL
        
        self.template_engine = EmailTemplateEngine()
    
    def _create_smtp_connection(self) -> smtplib.SMTP:
        """Create and configure SMTP connection"""
        try:
            if self.use_ssl:
                server = smtplib.SMTP_SSL(self.smtp_server, self.smtp_port)
            else:
                server = smtplib.SMTP(self.smtp_server, self.smtp_port)
                if self.use_tls:
                    server.starttls()
            
            if self.username and self.password:
                server.login(self.username, self.password)
            
            return server
        except Exception as e:
            raise ExternalServiceException("Email", f"SMTP connection failed: {str(e)}")
    
    def send_email(
        self,
        to_email: str,
        subject: str,
        html_body: str,
        text_body: Optional[str] = None,
        attachments: Optional[List[Dict[str, Any]]] = None,
        cc: Optional[List[str]] = None,
        bcc: Optional[List[str]] = None
    ) -> bool:
        """Send email with optional attachments"""
        try:
            # Create message
            msg = MIMEMultipart('alternative')
            msg['From'] = self.from_email
            msg['To'] = to_email
            msg['Subject'] = subject
            
            if cc:
                msg['Cc'] = ', '.join(cc)
            
            # Add text and HTML parts
            if text_body:
                text_part = MIMEText(text_body, 'plain')
                msg.attach(text_part)
            
            html_part = MIMEText(html_body, 'html')
            msg.attach(html_part)
            
            # Add attachments
            if attachments:
                for attachment in attachments:
                    part = MIMEBase('application', 'octet-stream')
                    part.set_payload(attachment['data'])
                    encoders.encode_base64(part)
                    part.add_header(
                        'Content-Disposition',
                        f'attachment; filename= {attachment["filename"]}'
                    )
                    msg.attach(part)
            
            # Send email
            with self._create_smtp_connection() as server:
                recipients = [to_email]
                if cc:
                    recipients.extend(cc)
                if bcc:
                    recipients.extend(bcc)
                
                server.send_message(msg, to_addrs=recipients)
            
            return True
            
        except Exception as e:
            raise ExternalServiceException("Email", f"Failed to send email: {str(e)}")
    
    async def send_invoice_email(
        self,
        invoice: Invoice,
        customer: Customer,
        user: User,
        pdf_attachment: Optional[bytes] = None,
        custom_message: Optional[str] = None
    ) -> bool:
        """Send invoice email to customer"""
        try:
            # Prepare template context
            context = {
                'invoice': {
                    'number': invoice.invoice_number,
                    'issue_date': invoice.issue_date.strftime('%B %d, %Y'),
                    'due_date': invoice.due_date.strftime('%B %d, %Y'),
                    'total': f"{invoice.currency} {invoice.total:,.2f}",
                    'currency': invoice.currency,
                    'notes': invoice.notes,
                    'view_url': f"{settings.FRONTEND_URL}/invoices/{invoice.id}"
                },
                'customer': {
                    'name': customer.name,
                    'company': customer.company,
                    'email': customer.email
                },
                'sender': {
                    'name': user.full_name,
                    'company': user.company_name,
                    'email': user.email
                },
                'custom_message': custom_message,
                'current_year': datetime.now().year
            }
            
            # Render email templates
            subject = f"Invoice {invoice.invoice_number} from {user.company_name or user.full_name}"
            html_body = self.template_engine.render_template('invoice_email.html', **context)
            text_body = self.template_engine.render_template('invoice_email.txt', **context)
            
            # Prepare attachments
            attachments = []
            if pdf_attachment:
                attachments.append({
                    'filename': f'invoice_{invoice.invoice_number}.pdf',
                    'data': pdf_attachment
                })
            
            # Send email
            success = self.send_email(
                to_email=customer.email,
                subject=subject,
                html_body=html_body,
                text_body=text_body,
                attachments=attachments
            )
            
            return success
            
        except Exception as e:
            raise ExternalServiceException("Email", f"Failed to send invoice email: {str(e)}")
    
    async def send_payment_confirmation_email(
        self,
        invoice: Invoice,
        customer: Customer,
        user: User,
        payment_amount: float,
        payment_date: datetime
    ) -> bool:
        """Send payment confirmation email"""
        try:
            context = {
                'invoice': {
                    'number': invoice.invoice_number,
                    'total': f"{invoice.currency} {invoice.total:,.2f}",
                    'currency': invoice.currency
                },
                'payment': {
                    'amount': f"{invoice.currency} {payment_amount:,.2f}",
                    'date': payment_date.strftime('%B %d, %Y'),
                    'remaining': f"{invoice.currency} {invoice.amount_due:,.2f}"
                },
                'customer': {
                    'name': customer.name,
                    'company': customer.company
                },
                'sender': {
                    'name': user.full_name,
                    'company': user.company_name
                }
            }
            
            subject = f"Payment Confirmation - Invoice {invoice.invoice_number}"
            html_body = self.template_engine.render_template('payment_confirmation.html', **context)
            text_body = self.template_engine.render_template('payment_confirmation.txt', **context)
            
            return self.send_email(
                to_email=customer.email,
                subject=subject,
                html_body=html_body,
                text_body=text_body
            )
            
        except Exception as e:
            raise ExternalServiceException("Email", f"Failed to send payment confirmation: {str(e)}")
    
    async def send_overdue_reminder_email(
        self,
        invoice: Invoice,
        customer: Customer,
        user: User,
        days_overdue: int
    ) -> bool:
        """Send overdue payment reminder email"""
        try:
            context = {
                'invoice': {
                    'number': invoice.invoice_number,
                    'due_date': invoice.due_date.strftime('%B %d, %Y'),
                    'total': f"{invoice.currency} {invoice.total:,.2f}",
                    'amount_due': f"{invoice.currency} {invoice.amount_due:,.2f}",
                    'days_overdue': days_overdue,
                    'view_url': f"{settings.FRONTEND_URL}/invoices/{invoice.id}"
                },
                'customer': {
                    'name': customer.name,
                    'company': customer.company
                },
                'sender': {
                    'name': user.full_name,
                    'company': user.company_name,
                    'email': user.email
                }
            }
            
            subject = f"Payment Reminder - Invoice {invoice.invoice_number} ({days_overdue} days overdue)"
            html_body = self.template_engine.render_template('overdue_reminder.html', **context)
            text_body = self.template_engine.render_template('overdue_reminder.txt', **context)
            
            return self.send_email(
                to_email=customer.email,
                subject=subject,
                html_body=html_body,
                text_body=text_body
            )
            
        except Exception as e:
            raise ExternalServiceException("Email", f"Failed to send overdue reminder: {str(e)}")
    
    async def send_welcome_email(self, user: User) -> bool:
        """Send welcome email to new user"""
        try:
            context = {
                'user': {
                    'name': user.full_name,
                    'email': user.email
                },
                'login_url': f"{settings.FRONTEND_URL}/login",
                'dashboard_url': f"{settings.FRONTEND_URL}/dashboard"
            }
            
            subject = f"Welcome to InvoiceFlow Pro, {user.first_name}!"
            html_body = self.template_engine.render_template('welcome.html', **context)
            text_body = self.template_engine.render_template('welcome.txt', **context)
            
            return self.send_email(
                to_email=user.email,
                subject=subject,
                html_body=html_body,
                text_body=text_body
            )
            
        except Exception as e:
            raise ExternalServiceException("Email", f"Failed to send welcome email: {str(e)}")
    
    async def send_password_reset_email(self, user: User, reset_token: str) -> bool:
        """Send password reset email"""
        try:
            context = {
                'user': {
                    'name': user.full_name,
                    'email': user.email
                },
                'reset_url': f"{settings.FRONTEND_URL}/reset-password?token={reset_token}",
                'expires_hours': 1  # Token expires in 1 hour
            }
            
            subject = "Reset Your InvoiceFlow Pro Password"
            html_body = self.template_engine.render_template('password_reset.html', **context)
            text_body = self.template_engine.render_template('password_reset.txt', **context)
            
            return self.send_email(
                to_email=user.email,
                subject=subject,
                html_body=html_body,
                text_body=text_body
            )
            
        except Exception as e:
            raise ExternalServiceException("Email", f"Failed to send password reset email: {str(e)}")
    
    async def send_verification_email(self, user: User, verification_token: str) -> bool:
        """Send email verification email"""
        try:
            context = {
                'user': {
                    'name': user.full_name,
                    'email': user.email
                },
                'verify_url': f"{settings.FRONTEND_URL}/verify-email?token={verification_token}"
            }
            
            subject = "Verify Your InvoiceFlow Pro Email Address"
            html_body = self.template_engine.render_template('email_verification.html', **context)
            text_body = self.template_engine.render_template('email_verification.txt', **context)
            
            return self.send_email(
                to_email=user.email,
                subject=subject,
                html_body=html_body,
                text_body=text_body
            )
            
        except Exception as e:
            raise ExternalServiceException("Email", f"Failed to send verification email: {str(e)}")
    
    def test_email_connection(self) -> bool:
        """Test email configuration"""
        try:
            with self._create_smtp_connection() as server:
                server.noop()  # Simple test command
            return True
        except Exception:
            return False