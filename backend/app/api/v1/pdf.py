"""
InvoiceFlow Pro - PDF Generation API Routes
"""
from fastapi import APIRouter, Depends, HTTPException, status, Response
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional
from io import BytesIO

from app.core.deps import get_db, get_current_user, validate_invoice_access
from app.services.pdf_service import PDFService
from app.services.invoice_service import InvoiceService
from app.services.customer_service import CustomerService
from app.models.user import User
from app.core.exceptions import ResourceNotFoundException

router = APIRouter()


class PDFGenerationRequest(BaseModel):
    template: str = "professional"
    download: bool = False  # If true, force download; if false, display inline


class TemplateResponse(BaseModel):
    id: str
    name: str
    description: str


class PDFResponse(BaseModel):
    pdf_base64: str
    filename: str
    size_bytes: int


@router.get("/templates", response_model=List[TemplateResponse])
async def get_pdf_templates(
    current_user: User = Depends(get_current_user)
):
    """Get available PDF templates"""
    pdf_service = PDFService()
    templates = pdf_service.get_available_templates()
    
    return [
        TemplateResponse(
            id=template["id"],
            name=template["name"], 
            description=template["description"]
        )
        for template in templates
    ]


@router.get("/invoice/{invoice_id}")
async def download_invoice_pdf(
    invoice_id: int,
    template: str = "professional",
    download: bool = True,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _: bool = Depends(validate_invoice_access)
):
    """Download invoice as PDF"""
    try:
        # Get services
        invoice_service = InvoiceService(db)
        customer_service = CustomerService(db)
        pdf_service = PDFService()
        
        # Get invoice and related data
        invoice = await invoice_service.get_by_id_with_items(invoice_id)
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
        
        # Generate PDF
        pdf_bytes = await pdf_service.create_invoice_pdf(
            invoice=invoice,
            customer=customer,
            user=current_user,
            items=invoice.items,
            template=template
        )
        
        # Create filename
        filename = f"invoice_{invoice.invoice_number}.pdf"
        
        # Return PDF as streaming response
        pdf_stream = BytesIO(pdf_bytes)
        
        headers = {
            "Content-Length": str(len(pdf_bytes)),
            "Content-Type": "application/pdf",
        }
        
        if download:
            headers["Content-Disposition"] = f'attachment; filename="{filename}"'
        else:
            headers["Content-Disposition"] = f'inline; filename="{filename}"'
        
        return StreamingResponse(
            BytesIO(pdf_bytes),
            media_type="application/pdf",
            headers=headers
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate PDF: {str(e)}"
        )


@router.post("/invoice/{invoice_id}/generate", response_model=PDFResponse)
async def generate_invoice_pdf(
    invoice_id: int,
    request: PDFGenerationRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _: bool = Depends(validate_invoice_access)
):
    """Generate invoice PDF and return as base64"""
    try:
        # Get services
        invoice_service = InvoiceService(db)
        customer_service = CustomerService(db)
        pdf_service = PDFService()
        
        # Get invoice and related data
        invoice = await invoice_service.get_by_id_with_items(invoice_id)
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
        
        # Generate PDF
        pdf_bytes = await pdf_service.create_invoice_pdf(
            invoice=invoice,
            customer=customer,
            user=current_user,
            items=invoice.items,
            template=request.template
        )
        
        # Convert to base64
        pdf_base64 = pdf_service.pdf_to_base64(pdf_bytes)
        filename = f"invoice_{invoice.invoice_number}.pdf"
        
        return PDFResponse(
            pdf_base64=pdf_base64,
            filename=filename,
            size_bytes=len(pdf_bytes)
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate PDF: {str(e)}"
        )


@router.get("/invoice/{invoice_id}/preview")
async def preview_invoice_pdf(
    invoice_id: int,
    template: str = "professional",
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _: bool = Depends(validate_invoice_access)
):
    """Preview invoice PDF in browser"""
    return await download_invoice_pdf(
        invoice_id=invoice_id,
        template=template,
        download=False,  # Display inline
        db=db,
        current_user=current_user,
        _=_
    )


@router.post("/bulk-generate")
async def bulk_generate_invoices_pdf(
    invoice_ids: List[int],
    template: str = "professional",
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Generate multiple invoice PDFs and return as ZIP"""
    try:
        import zipfile
        from io import BytesIO
        
        # Get services
        invoice_service = InvoiceService(db)
        customer_service = CustomerService(db)
        pdf_service = PDFService()
        
        # Create ZIP file in memory
        zip_buffer = BytesIO()
        
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            for invoice_id in invoice_ids:
                try:
                    # Validate access
                    await validate_invoice_access(invoice_id, current_user, db)
                    
                    # Get invoice and related data
                    invoice = await invoice_service.get_by_id_with_items(invoice_id)
                    if not invoice:
                        continue
                    
                    customer = await customer_service.get_by_id(invoice.customer_id)
                    if not customer:
                        continue
                    
                    # Generate PDF
                    pdf_bytes = await pdf_service.create_invoice_pdf(
                        invoice=invoice,
                        customer=customer,
                        user=current_user,
                        items=invoice.items,
                        template=template
                    )
                    
                    # Add to ZIP
                    filename = f"invoice_{invoice.invoice_number}.pdf"
                    zip_file.writestr(filename, pdf_bytes)
                    
                except Exception as e:
                    # Log error but continue with other invoices
                    continue
        
        zip_buffer.seek(0)
        
        # Return ZIP file
        headers = {
            "Content-Disposition": "attachment; filename=invoices.zip",
            "Content-Type": "application/zip"
        }
        
        return StreamingResponse(
            BytesIO(zip_buffer.getvalue()),
            media_type="application/zip",
            headers=headers
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate bulk PDFs: {str(e)}"
        )


@router.get("/test-pdf")
async def test_pdf_generation(
    current_user: User = Depends(get_current_user)
):
    """Generate a test PDF for debugging"""
    try:
        from reportlab.lib.pagesizes import letter
        from reportlab.platypus import SimpleDocTemplate, Paragraph
        from reportlab.lib.styles import getSampleStyleSheet
        from io import BytesIO
        
        # Create a simple test PDF
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        styles = getSampleStyleSheet()
        
        story = [
            Paragraph("Test PDF Generation", styles['Title']),
            Paragraph("This is a test PDF generated by InvoiceFlow Pro.", styles['Normal']),
            Paragraph(f"Generated for user: {current_user.email}", styles['Normal']),
            Paragraph(f"Generated at: {datetime.now().isoformat()}", styles['Normal']),
        ]
        
        doc.build(story)
        pdf_bytes = buffer.getvalue()
        buffer.close()
        
        return StreamingResponse(
            BytesIO(pdf_bytes),
            media_type="application/pdf",
            headers={
                "Content-Disposition": "inline; filename=test.pdf",
                "Content-Length": str(len(pdf_bytes))
            }
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate test PDF: {str(e)}"
        )