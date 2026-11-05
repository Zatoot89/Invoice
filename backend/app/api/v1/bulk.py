"""
InvoiceFlow Pro - Bulk Operations API
"""
from datetime import datetime
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query, Response
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel
import io

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.models.invoice import InvoiceStatus
from app.services.bulk_service import BulkOperationsService
from app.services.websocket_service import WebSocketService


router = APIRouter(prefix="/bulk", tags=["bulk-operations"])


# Pydantic models for requests
class BulkInvoiceUpdateRequest(BaseModel):
    invoice_ids: List[int]
    updates: Dict[str, Any]


class BulkInvoiceActionRequest(BaseModel):
    invoice_ids: List[int]
    force: Optional[bool] = False


class ExportFilters(BaseModel):
    status: Optional[List[str]] = None
    customer_ids: Optional[List[int]] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    is_active: Optional[bool] = None
    search: Optional[str] = None


@router.get("/export/invoices")
async def export_invoices_csv(
    filters: Optional[Dict[str, Any]] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Export invoices to CSV format
    
    **Parameters:**
    - **filters**: Optional filters for export (status, customer_ids, date_from, date_to)
    
    **Returns:** CSV file download
    """
    try:
        websocket_service = WebSocketService()
        bulk_service = BulkOperationsService(db, websocket_service)
        
        csv_data = await bulk_service.export_invoices_to_csv(current_user.id, filters)
        
        # Create response
        response = StreamingResponse(
            io.StringIO(csv_data),
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename=invoices_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"}
        )
        
        return response
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/export/customers")
async def export_customers_csv(
    filters: Optional[Dict[str, Any]] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Export customers to CSV format
    
    **Parameters:**
    - **filters**: Optional filters for export (is_active, search)
    
    **Returns:** CSV file download
    """
    try:
        websocket_service = WebSocketService()
        bulk_service = BulkOperationsService(db, websocket_service)
        
        csv_data = await bulk_service.export_customers_to_csv(current_user.id, filters)
        
        # Create response
        response = StreamingResponse(
            io.StringIO(csv_data),
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename=customers_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"}
        )
        
        return response
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/import/customers")
async def import_customers_csv(
    file: UploadFile = File(...),
    update_existing: bool = Query(False, description="Update existing customers if found"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Import customers from CSV file
    
    **Parameters:**
    - **file**: CSV file to upload
    - **update_existing**: Whether to update existing customers with matching email
    
    **Required CSV columns:**
    - Name (required)
    - Email (required)
    - Phone, Company, Address fields, etc. (optional)
    
    **Returns:** Import results with success/failure counts
    """
    try:
        # Validate file type
        if not file.filename.endswith('.csv'):
            raise HTTPException(status_code=400, detail="File must be a CSV file")
        
        # Validate file size (max 10MB)
        if file.size and file.size > 10 * 1024 * 1024:
            raise HTTPException(status_code=400, detail="File size too large (max 10MB)")
        
        websocket_service = WebSocketService()
        bulk_service = BulkOperationsService(db, websocket_service)
        
        results = await bulk_service.import_customers_from_csv(
            current_user.id, file, update_existing
        )
        
        return {
            "message": "Import completed",
            "results": results
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/invoices/update")
async def bulk_update_invoices(
    request: BulkInvoiceUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Bulk update multiple invoices
    
    **Supported update fields:**
    - status: Update invoice status (with validation)
    - due_date: Update due date (ISO format)
    - notes: Update invoice notes
    - terms_and_conditions: Update terms and conditions
    
    **Returns:** Update results with success/failure counts
    """
    try:
        if not request.invoice_ids:
            raise HTTPException(status_code=400, detail="No invoice IDs provided")
        
        if not request.updates:
            raise HTTPException(status_code=400, detail="No updates provided")
        
        # Validate status if provided
        if 'status' in request.updates:
            try:
                InvoiceStatus(request.updates['status'])
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid status value")
        
        websocket_service = WebSocketService()
        bulk_service = BulkOperationsService(db, websocket_service)
        
        results = await bulk_service.bulk_update_invoices(
            current_user.id, request.invoice_ids, request.updates
        )
        
        return {
            "message": "Bulk update completed",
            "results": results
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/invoices/send")
async def bulk_send_invoices(
    request: BulkInvoiceActionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Send multiple invoices via email
    
    **Note:** Only draft invoices will be sent
    
    **Returns:** Send results with success/failure counts
    """
    try:
        if not request.invoice_ids:
            raise HTTPException(status_code=400, detail="No invoice IDs provided")
        
        websocket_service = WebSocketService()
        bulk_service = BulkOperationsService(db, websocket_service)
        
        results = await bulk_service.bulk_send_invoices(current_user.id, request.invoice_ids)
        
        return {
            "message": "Bulk send completed",
            "results": results
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/invoices/delete")
async def bulk_delete_invoices(
    request: BulkInvoiceActionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Delete multiple invoices
    
    **Parameters:**
    - **force**: Allow deletion of non-draft invoices (default: false)
    
    **Note:** Without force flag, only draft invoices will be deleted
    
    **Returns:** Deletion results with success/failure counts
    """
    try:
        if not request.invoice_ids:
            raise HTTPException(status_code=400, detail="No invoice IDs provided")
        
        websocket_service = WebSocketService()
        bulk_service = BulkOperationsService(db, websocket_service)
        
        results = await bulk_service.bulk_delete_invoices(
            current_user.id, request.invoice_ids, request.force
        )
        
        return {
            "message": "Bulk delete completed",
            "results": results
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/template/customers")
async def download_customer_template():
    """
    Download a CSV template for customer import
    
    **Returns:** CSV template file
    """
    try:
        # Create template CSV
        template_data = """Name,Email,Phone,Company,Address Line 1,Address Line 2,City,State,Postal Code,Country,Tax Number,Website,Payment Terms,Preferred Currency,Is Active,Notes,Tags
John Doe,john.doe@example.com,+1-555-0123,Acme Corp,123 Main St,Suite 100,New York,NY,10001,USA,123456789,https://example.com,30,USD,true,"VIP customer","important,priority"
Jane Smith,jane.smith@example.com,+1-555-0124,Tech Solutions,,456 Oak Ave,San Francisco,CA,94102,USA,,https://techsolutions.com,15,USD,true,"Net 15 payment terms",technology"""
        
        response = StreamingResponse(
            io.StringIO(template_data),
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=customer_import_template.csv"}
        )
        
        return response
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status/{operation_id}")
async def get_bulk_operation_status(
    operation_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get the status of a bulk operation
    
    **Note:** This endpoint would typically connect to a task queue system
    like Celery to check operation status. For now, it returns a placeholder.
    """
    # TODO: Implement with actual task queue system (Celery/Redis)
    return {
        "operation_id": operation_id,
        "status": "completed",
        "progress": 100,
        "message": "Operation completed successfully"
    }