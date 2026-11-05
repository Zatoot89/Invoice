"""
InvoiceFlow Pro - PDF Generation Service
"""
from typing import Optional, Dict, Any, List, Union, TYPE_CHECKING
from io import BytesIO
from pathlib import Path
import base64
import logging
from datetime import datetime
from decimal import Decimal

from jinja2 import Environment, FileSystemLoader, select_autoescape

# Try importing WeasyPrint for modern HTML/CSS rendering; fallback gracefully if system libs missing
try:
    from weasyprint import HTML
    WEASYPRINT_AVAILABLE = True
except Exception as e:
    WEASYPRINT_AVAILABLE = False
    HTML = None

# Try importing qrcode for embedded Stripe/payment QR codes
try:
    import qrcode
    QRCODE_AVAILABLE = True
except Exception:
    QRCODE_AVAILABLE = False
    qrcode = None

from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, mm
from reportlab.lib.colors import Color, black, blue, grey
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT
from reportlab.lib import colors
from PIL import Image as PILImage

if TYPE_CHECKING:
    from app.models.invoice import Invoice, InvoiceItem
    from app.models.customer import Customer
    from app.models.user import User
else:
    Invoice = Any
    InvoiceItem = Any
    Customer = Any
    User = Any

logger = logging.getLogger(__name__)


class DataProxy:
    """Wraps dictionaries or model instances to provide safe attribute and dictionary access."""
    def __init__(self, data: Any):
        self._data = data

    def __getattr__(self, name: str) -> Any:
        if isinstance(self._data, dict):
            val = self._data.get(name)
            if val is not None:
                return val
            if name == "full_address":
                parts = [
                    self._data.get("address_line_1") or self._data.get("address"),
                    self._data.get("city"),
                    self._data.get("state"),
                    self._data.get("postal_code"),
                    self._data.get("country"),
                ]
                return ", ".join([p for p in parts if p])
            if name in ("first_name", "last_name", "company"):
                return ""
            return ""
        return getattr(self._data, name, None)

    def __getitem__(self, key: str) -> Any:
        if isinstance(self._data, dict):
            return self._data.get(key)
        return getattr(self._data, key, None)

    def get(self, key: str, default: Any = None) -> Any:
        if isinstance(self._data, dict):
            return self._data.get(key, default)
        return getattr(self._data, key, default)


class InvoicePDFGenerator:
    """
    Professional invoice PDF generator with customizable templates
    """
    
    def __init__(self):
        self.page_size = A4
        self.styles = getSampleStyleSheet()
        self.setup_custom_styles()
    
    def setup_custom_styles(self):
        """Setup custom paragraph styles"""
        # Company header style
        self.styles.add(ParagraphStyle(
            name='CompanyHeader',
            parent=self.styles['Heading1'],
            fontSize=24,
            textColor=Color(0.2, 0.4, 0.8),
            spaceAfter=12,
        ))
        
        # Invoice title style
        self.styles.add(ParagraphStyle(
            name='InvoiceTitle',
            parent=self.styles['Heading1'],
            fontSize=20,
            textColor=Color(0.3, 0.3, 0.3),
            spaceAfter=20,
            alignment=TA_RIGHT,
        ))
        
        # Section header style
        self.styles.add(ParagraphStyle(
            name='SectionHeader',
            parent=self.styles['Heading2'],
            fontSize=12,
            textColor=Color(0.2, 0.4, 0.8),
            spaceAfter=6,
            spaceBefore=12,
        ))
        
        # Address style
        self.styles.add(ParagraphStyle(
            name='Address',
            parent=self.styles['Normal'],
            fontSize=10,
            spaceAfter=3,
        ))
        
        # Table header style
        self.styles.add(ParagraphStyle(
            name='TableHeader',
            parent=self.styles['Normal'],
            fontSize=10,
            textColor=colors.white,
            alignment=TA_CENTER,
        ))
        
        # Total amount style
        self.styles.add(ParagraphStyle(
            name='TotalAmount',
            parent=self.styles['Normal'],
            fontSize=14,
            textColor=Color(0.2, 0.4, 0.8),
            alignment=TA_RIGHT,
        ))
    
    def generate_invoice_pdf(
        self, 
        invoice: Invoice, 
        customer: Customer, 
        user: User,
        items: List[InvoiceItem],
        template: str = "professional"
    ) -> bytes:
        """
        Generate PDF for an invoice
        """
        buffer = BytesIO()
        
        # Create document with margins
        doc = SimpleDocTemplate(
            buffer,
            pagesize=self.page_size,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=72
        )
        
        # Wrap dicts in DataProxy for safe attribute access in ReportLab
        inv = DataProxy(invoice) if isinstance(invoice, dict) else invoice
        cust = DataProxy(customer) if isinstance(customer, dict) else customer
        usr = DataProxy(user) if isinstance(user, dict) else user
        itms = [DataProxy(it) if isinstance(it, dict) else it for it in items]

        # Build PDF content
        story = []
        
        if template == "professional":
            story = self._build_professional_template(inv, cust, usr, itms)
        elif template == "modern":
            story = self._build_modern_template(inv, cust, usr, itms)
        elif template == "classic":
            story = self._build_classic_template(inv, cust, usr, itms)
        else:
            story = self._build_professional_template(inv, cust, usr, itms)
        
        # Build PDF
        doc.build(story)
        
        pdf_bytes = buffer.getvalue()
        buffer.close()
        
        return pdf_bytes
    
    def _build_professional_template(
        self, 
        invoice: Invoice, 
        customer: Customer, 
        user: User, 
        items: List[InvoiceItem]
    ) -> List:
        """Build professional template layout"""
        story = []
        
        # Header with logo and company info
        header_data = [
            [
                Paragraph(user.company_name or f"{user.first_name} {user.last_name}", 
                         self.styles['CompanyHeader']),
                Paragraph(f"INVOICE<br/>{invoice.invoice_number}", 
                         self.styles['InvoiceTitle'])
            ]
        ]
        
        header_table = Table(header_data, colWidths=[4*inch, 2.5*inch])
        header_table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('ALIGN', (0, 0), (0, 0), 'LEFT'),
            ('ALIGN', (1, 0), (1, 0), 'RIGHT'),
        ]))
        
        story.append(header_table)
        story.append(Spacer(1, 20))
        
        # Company and customer information
        info_data = [
            [
                Paragraph("<b>From:</b>", self.styles['SectionHeader']),
                Paragraph("<b>To:</b>", self.styles['SectionHeader']),
                Paragraph("<b>Invoice Details:</b>", self.styles['SectionHeader'])
            ],
            [
                Paragraph(f"{user.company_name or f'{user.first_name} {user.last_name}'}<br/>"
                         f"{user.email}", self.styles['Address']),
                Paragraph(f"{customer.name}<br/>"
                         f"{customer.company or ''}<br/>"
                         f"{customer.email}<br/>"
                         f"{customer.full_address}", self.styles['Address']),
                Paragraph(f"Issue Date: {invoice.issue_date.strftime('%B %d, %Y')}<br/>"
                         f"Due Date: {invoice.due_date.strftime('%B %d, %Y')}<br/>"
                         f"Currency: {invoice.currency}", self.styles['Address'])
            ]
        ]
        
        info_table = Table(info_data, colWidths=[2.2*inch, 2.2*inch, 2.1*inch])
        info_table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ]))
        
        story.append(info_table)
        story.append(Spacer(1, 30))
        
        # Items table
        story.append(Paragraph("Invoice Items", self.styles['SectionHeader']))
        story.append(Spacer(1, 10))
        
        # Table headers
        items_data = [
            [
                Paragraph("<b>Description</b>", self.styles['TableHeader']),
                Paragraph("<b>Qty</b>", self.styles['TableHeader']),
                Paragraph("<b>Unit Price</b>", self.styles['TableHeader']),
                Paragraph("<b>Tax</b>", self.styles['TableHeader']),
                Paragraph("<b>Total</b>", self.styles['TableHeader'])
            ]
        ]
        
        # Add items
        for item in items:
            items_data.append([
                Paragraph(item.description, self.styles['Normal']),
                Paragraph(str(item.quantity), self.styles['Normal']),
                Paragraph(f"{invoice.currency} {item.unit_price:,.2f}", self.styles['Normal']),
                Paragraph(f"{item.tax_rate:.1f}%", self.styles['Normal']),
                Paragraph(f"{invoice.currency} {item.total:,.2f}", self.styles['Normal'])
            ])
        
        items_table = Table(items_data, colWidths=[3*inch, 0.8*inch, 1*inch, 0.7*inch, 1*inch])
        items_table.setStyle(TableStyle([
            # Header styling
            ('BACKGROUND', (0, 0), (-1, 0), Color(0.2, 0.4, 0.8)),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            
            # Body styling
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
            ('ALIGN', (1, 1), (-1, -1), 'CENTER'),  # Align numbers to center
            ('ALIGN', (0, 1), (0, -1), 'LEFT'),     # Description left-aligned
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            
            # Grid
            ('GRID', (0, 0), (-1, -1), 1, Color(0.8, 0.8, 0.8)),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        
        story.append(items_table)
        story.append(Spacer(1, 20))
        
        # Totals section
        totals_data = [
            ['Subtotal:', f"{invoice.currency} {invoice.subtotal:,.2f}"],
        ]
        
        if invoice.discount_amount > 0:
            totals_data.append([
                f'Discount ({invoice.discount_percentage}%):',
                f"-{invoice.currency} {invoice.discount_amount:,.2f}"
            ])
        
        if invoice.tax_amount > 0:
            totals_data.append([
                f'Tax ({invoice.tax_rate}%):',
                f"{invoice.currency} {invoice.tax_amount:,.2f}"
            ])
        
        totals_data.append([
            Paragraph("<b>TOTAL:</b>", self.styles['TotalAmount']),
            Paragraph(f"<b>{invoice.currency} {invoice.total:,.2f}</b>", self.styles['TotalAmount'])
        ])
        
        totals_table = Table(totals_data, colWidths=[4.5*inch, 2*inch])
        totals_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
            ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
            ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, -1), (-1, -1), 12),
            ('LINEABOVE', (0, -1), (-1, -1), 2, Color(0.2, 0.4, 0.8)),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        
        story.append(totals_table)
        story.append(Spacer(1, 30))
        
        # Notes and terms
        if invoice.notes:
            story.append(Paragraph("Notes", self.styles['SectionHeader']))
            story.append(Paragraph(invoice.notes, self.styles['Normal']))
            story.append(Spacer(1, 15))
        
        if invoice.terms_and_conditions:
            story.append(Paragraph("Terms and Conditions", self.styles['SectionHeader']))
            story.append(Paragraph(invoice.terms_and_conditions, self.styles['Normal']))
            story.append(Spacer(1, 15))
        
        # Footer
        if invoice.footer_text:
            story.append(Spacer(1, 20))
            story.append(Paragraph(invoice.footer_text, self.styles['Normal']))
        
        return story
    
    def _build_modern_template(self, invoice: Invoice, customer: Customer, user: User, items: List[InvoiceItem]) -> List:
        """Build modern template layout (simplified version)"""
        # For now, return professional template
        # TODO: Implement modern design with different colors and layout
        return self._build_professional_template(invoice, customer, user, items)
    
    def _build_classic_template(self, invoice: Invoice, customer: Customer, user: User, items: List[InvoiceItem]) -> List:
        """Build classic template layout (simplified version)"""
        # For now, return professional template
        # TODO: Implement classic design with serif fonts and traditional layout
        return self._build_professional_template(invoice, customer, user, items)
    
    def generate_quote_pdf(self, quote_data: Dict[str, Any]) -> bytes:
        """Generate PDF for a quote"""
        # TODO: Implement quote PDF generation
        # Similar to invoice but with different terminology
        pass
    
    def generate_receipt_pdf(self, payment_data: Dict[str, Any]) -> bytes:
        """Generate PDF receipt for a payment"""
        # TODO: Implement receipt PDF generation
        pass


class PDFService:
    """
    Unified PDF generation service supporting modern HTML/CSS templates
    (via WeasyPrint + Jinja2 + dynamic QR code) with automatic fallback
    to pure-Python ReportLab.
    """

    def __init__(self):
        self.generator = InvoicePDFGenerator()
        self.templates_dir = Path(__file__).resolve().parent.parent / "templates" / "invoice"
        self.static_css = self.templates_dir / "invoice.css"

        if self.templates_dir.exists():
            self.jinja_env = Environment(
                loader=FileSystemLoader(str(self.templates_dir)),
                autoescape=select_autoescape(["html", "xml"]),
            )
        else:
            self.jinja_env = None

    def _generate_qr_data_url(self, data: str) -> Optional[str]:
        """Generate base64 data URL for a payment QR code"""
        if not QRCODE_AVAILABLE or not data:
            return None
        try:
            img = qrcode.make(data)
            buf = BytesIO()
            img.save(buf, format="PNG")
            b64 = base64.b64encode(buf.getvalue()).decode("utf-8")
            return f"data:image/png;base64,{b64}"
        except Exception as e:
            logger.warning(f"Failed to generate QR code: {e}")
            return None

    def render_html(
        self,
        invoice: Union[Invoice, Dict[str, Any]],
        customer: Union[Customer, Dict[str, Any]],
        user: Union[User, Dict[str, Any]],
        items: List[Union[InvoiceItem, Dict[str, Any]]],
        payment_url: Optional[str] = None,
        template_name: str = "invoice.html",
    ) -> str:
        """Render HTML string for invoice using Jinja2"""
        if not self.jinja_env:
            raise RuntimeError(f"Templates directory not found: {self.templates_dir}")

        template = self.jinja_env.get_template(template_name)
        css_text = self.static_css.read_text(encoding="utf-8") if self.static_css.exists() else ""

        # Check for payment url on invoice object if not explicitly passed
        resolved_payment_url = payment_url
        if not resolved_payment_url:
            if isinstance(invoice, dict):
                resolved_payment_url = invoice.get("payment_url")
            elif hasattr(invoice, "payment_url"):
                resolved_payment_url = getattr(invoice, "payment_url", None)

        payment_qr = self._generate_qr_data_url(resolved_payment_url) if resolved_payment_url else None

        # Build rendering context
        context = {
            "invoice": invoice,
            "customer": customer,
            "client": customer,
            "user": user,
            "org": {
                "name": getattr(user, "company_name", None) or (
                    user.get("company_name") if isinstance(user, dict) else None
                ) or "InvoiceFlow Pro",
                "email": getattr(user, "email", None) if not isinstance(user, dict) else user.get("email"),
                "phone": getattr(user, "phone", None) if not isinstance(user, dict) else user.get("phone"),
                "address": getattr(user, "address", None) if not isinstance(user, dict) else user.get("address"),
            },
            "items": items,
            "css_text": css_text,
            "payment_qr": payment_qr,
        }

        return template.render(**context)

    async def create_invoice_pdf(
        self,
        invoice: Union[Invoice, Dict[str, Any]],
        customer: Union[Customer, Dict[str, Any]],
        user: Union[User, Dict[str, Any]],
        items: List[Union[InvoiceItem, Dict[str, Any]]],
        template: str = "professional",
        payment_url: Optional[str] = None,
    ) -> bytes:
        """
        Generate invoice PDF bytes.
        Defaults to modern HTML/CSS via WeasyPrint with QR code.
        Gracefully falls back to ReportLab if WeasyPrint or its system libraries are unavailable.
        """
        # If user explicitly requested ReportLab or WeasyPrint is unavailable
        use_weasyprint = WEASYPRINT_AVAILABLE and template != "reportlab" and self.jinja_env is not None

        if use_weasyprint:
            try:
                html_content = self.render_html(
                    invoice=invoice,
                    customer=customer,
                    user=user,
                    items=items,
                    payment_url=payment_url,
                )
                pdf_bytes = HTML(
                    string=html_content,
                    base_url=str(self.templates_dir),
                ).write_pdf()
                return pdf_bytes
            except Exception as e:
                logger.warning(
                    f"WeasyPrint rendering failed ({e}), falling back to ReportLab generator."
                )

        # Fallback to ReportLab generator
        # If objects are dictionaries, convert or handle gracefully
        return self.generator.generate_invoice_pdf(invoice, customer, user, items, template)

    def get_available_templates(self) -> List[Dict[str, str]]:
        """Get list of available PDF templates"""
        templates = [
            {
                "id": "professional",
                "name": "Professional HTML/CSS (Recommended)",
                "description": "Modern responsive design with CSS styling, payment QR code, and tax breakdown",
            },
            {
                "id": "modern",
                "name": "Modern HTML/CSS",
                "description": "Clean contemporary layout with company branding and payment QR",
            },
            {
                "id": "reportlab",
                "name": "ReportLab Standard",
                "description": "Legacy pure-Python programmatic layout without native library dependencies",
            },
        ]
        return templates

    def pdf_to_base64(self, pdf_bytes: bytes) -> str:
        """Convert PDF bytes to base64 string"""
        return base64.b64encode(pdf_bytes).decode("utf-8")

    def base64_to_pdf(self, base64_string: str) -> bytes:
        """Convert base64 string to PDF bytes"""
        return base64.b64decode(base64_string)