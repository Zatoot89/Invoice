"""
InvoiceFlow Pro - Bulk Operations Service
Handles bulk operations like CSV import/export, bulk updates, and batch processing
"""
import csv
import io
from datetime import datetime
from decimal import Decimal
from typing import List, Dict, Any, Optional, Union
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
import pandas as pd
from fastapi import HTTPException, UploadFile

from app.models.invoice import Invoice, InvoiceItem, InvoiceStatus, InvoiceType
from app.models.customer import Customer
from app.models.user import User
from app.services.websocket_service import WebSocketService


class BulkOperationsService:
    def __init__(self, db: Session, websocket_service: WebSocketService):
        self.db = db
        self.websocket_service = websocket_service

    async def export_invoices_to_csv(self, user_id: int, filters: Dict[str, Any] = None) -> str:
        """Export invoices to CSV format"""
        try:
            # Build query with filters
            query = self.db.query(Invoice).filter(Invoice.user_id == user_id)
            
            if filters:
                if filters.get('status'):
                    query = query.filter(Invoice.status.in_(filters['status']))
                if filters.get('customer_ids'):
                    query = query.filter(Invoice.customer_id.in_(filters['customer_ids']))
                if filters.get('date_from'):
                    query = query.filter(Invoice.issue_date >= filters['date_from'])
                if filters.get('date_to'):
                    query = query.filter(Invoice.issue_date <= filters['date_to'])

            invoices = query.all()
            
            # Create CSV data
            output = io.StringIO()
            writer = csv.writer(output)
            
            # Write headers
            headers = [
                'Invoice Number', 'Customer Name', 'Customer Email', 'Issue Date', 
                'Due Date', 'Status', 'Currency', 'Subtotal', 'Tax Amount', 
                'Total', 'Amount Paid', 'Amount Due', 'Notes'
            ]
            writer.writerow(headers)
            
            # Write data rows
            for invoice in invoices:
                writer.writerow([
                    invoice.invoice_number,
                    invoice.customer.name if invoice.customer else '',
                    invoice.customer.email if invoice.customer else '',
                    invoice.issue_date.strftime('%Y-%m-%d') if invoice.issue_date else '',
                    invoice.due_date.strftime('%Y-%m-%d') if invoice.due_date else '',
                    invoice.status.value,
                    invoice.currency,
                    float(invoice.subtotal),
                    float(invoice.tax_amount),
                    float(invoice.total),
                    float(invoice.amount_paid),
                    float(invoice.amount_due),
                    invoice.notes or ''
                ])
            
            return output.getvalue()
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")

    async def export_customers_to_csv(self, user_id: int, filters: Dict[str, Any] = None) -> str:
        """Export customers to CSV format"""
        try:
            # Build query with filters
            query = self.db.query(Customer).filter(Customer.user_id == user_id)
            
            if filters:
                if filters.get('is_active') is not None:
                    query = query.filter(Customer.is_active == filters['is_active'])
                if filters.get('search'):
                    search_term = f"%{filters['search']}%"
                    query = query.filter(
                        or_(
                            Customer.name.ilike(search_term),
                            Customer.email.ilike(search_term),
                            Customer.company.ilike(search_term)
                        )
                    )

            customers = query.all()
            
            # Create CSV data
            output = io.StringIO()
            writer = csv.writer(output)
            
            # Write headers
            headers = [
                'Name', 'Email', 'Phone', 'Company', 'Address Line 1', 'Address Line 2',
                'City', 'State', 'Postal Code', 'Country', 'Tax Number', 'Website',
                'Payment Terms', 'Preferred Currency', 'Total Invoices', 'Total Amount',
                'Amount Paid', 'Amount Outstanding', 'Is Active', 'Notes', 'Tags'
            ]
            writer.writerow(headers)
            
            # Write data rows
            for customer in customers:
                writer.writerow([
                    customer.name,
                    customer.email,
                    customer.phone or '',
                    customer.company or '',
                    customer.address_line_1 or '',
                    customer.address_line_2 or '',
                    customer.city or '',
                    customer.state or '',
                    customer.postal_code or '',
                    customer.country or '',
                    customer.tax_number or '',
                    customer.website or '',
                    customer.payment_terms,
                    customer.preferred_currency,
                    customer.total_invoices,
                    float(customer.total_amount),
                    float(customer.amount_paid),
                    float(customer.amount_outstanding),
                    customer.is_active,
                    customer.notes or '',
                    customer.tags or ''
                ])
            
            return output.getvalue()
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")

    async def import_customers_from_csv(self, user_id: int, file: UploadFile, 
                                      update_existing: bool = False) -> Dict[str, Any]:
        """Import customers from CSV file"""
        try:
            # Read CSV content
            content = await file.read()
            csv_data = io.StringIO(content.decode('utf-8'))
            reader = csv.DictReader(csv_data)
            
            results = {
                'total_rows': 0,
                'successful_imports': 0,
                'updated_records': 0,
                'failed_imports': 0,
                'errors': []
            }
            
            for row_num, row in enumerate(reader, start=2):  # Start from 2 (after header)
                results['total_rows'] += 1
                
                try:
                    # Validate required fields
                    if not row.get('Name') or not row.get('Email'):
                        results['errors'].append({
                            'row': row_num,
                            'error': 'Name and Email are required fields'
                        })
                        results['failed_imports'] += 1
                        continue
                    
                    # Check if customer exists
                    existing_customer = self.db.query(Customer).filter(
                        and_(
                            Customer.user_id == user_id,
                            Customer.email == row['Email']
                        )
                    ).first()
                    
                    if existing_customer and not update_existing:
                        results['errors'].append({
                            'row': row_num,
                            'error': f'Customer with email {row["Email"]} already exists'
                        })
                        results['failed_imports'] += 1
                        continue
                    
                    # Parse data with type conversion
                    customer_data = {
                        'user_id': user_id,
                        'name': row['Name'],
                        'email': row['Email'],
                        'phone': row.get('Phone', ''),
                        'company': row.get('Company', ''),
                        'address_line_1': row.get('Address Line 1', ''),
                        'address_line_2': row.get('Address Line 2', ''),
                        'city': row.get('City', ''),
                        'state': row.get('State', ''),
                        'postal_code': row.get('Postal Code', ''),
                        'country': row.get('Country', ''),
                        'tax_number': row.get('Tax Number', ''),
                        'website': row.get('Website', ''),
                        'payment_terms': int(row.get('Payment Terms', 30)),
                        'preferred_currency': row.get('Preferred Currency', 'USD'),
                        'is_active': row.get('Is Active', '').lower() in ['true', '1', 'yes'],
                        'notes': row.get('Notes', ''),
                        'tags': row.get('Tags', '')
                    }
                    
                    if existing_customer:
                        # Update existing customer
                        for key, value in customer_data.items():
                            if key != 'user_id':  # Don't update user_id
                                setattr(existing_customer, key, value)
                        results['updated_records'] += 1
                    else:
                        # Create new customer
                        customer = Customer(**customer_data)
                        self.db.add(customer)
                        results['successful_imports'] += 1
                    
                except ValueError as ve:
                    results['errors'].append({
                        'row': row_num,
                        'error': f'Data type error: {str(ve)}'
                    })
                    results['failed_imports'] += 1
                except Exception as e:
                    results['errors'].append({
                        'row': row_num,
                        'error': f'Unexpected error: {str(e)}'
                    })
                    results['failed_imports'] += 1
            
            # Commit changes
            self.db.commit()
            
            # Send real-time notification
            await self.websocket_service.broadcast_to_user(
                user_id, 
                {
                    'type': 'bulk_import_completed',
                    'data': {
                        'operation': 'customer_import',
                        'results': results
                    }
                }
            )
            
            return results
            
        except Exception as e:
            self.db.rollback()
            raise HTTPException(status_code=500, detail=f"Import failed: {str(e)}")

    async def bulk_update_invoices(self, user_id: int, invoice_ids: List[int], 
                                 updates: Dict[str, Any]) -> Dict[str, Any]:
        """Bulk update multiple invoices"""
        try:
            # Get invoices to update
            invoices = self.db.query(Invoice).filter(
                and_(
                    Invoice.user_id == user_id,
                    Invoice.id.in_(invoice_ids)
                )
            ).all()
            
            if not invoices:
                raise HTTPException(status_code=404, detail="No invoices found to update")
            
            results = {
                'total_invoices': len(invoice_ids),
                'updated_invoices': 0,
                'failed_updates': 0,
                'errors': []
            }
            
            for invoice in invoices:
                try:
                    # Apply updates based on allowed fields
                    if 'status' in updates:
                        # Validate status transition
                        new_status = InvoiceStatus(updates['status'])
                        if self._is_valid_status_transition(invoice.status, new_status):
                            invoice.status = new_status
                            if new_status == InvoiceStatus.SENT:
                                invoice.sent_date = datetime.utcnow()
                            elif new_status == InvoiceStatus.PAID:
                                invoice.paid_date = datetime.utcnow()
                                invoice.amount_paid = invoice.total
                                invoice.amount_due = Decimal('0.00')
                        else:
                            results['errors'].append({
                                'invoice_id': invoice.id,
                                'error': f'Invalid status transition from {invoice.status} to {new_status}'
                            })
                            results['failed_updates'] += 1
                            continue
                    
                    if 'due_date' in updates:
                        invoice.due_date = datetime.fromisoformat(updates['due_date'])
                    
                    if 'notes' in updates:
                        invoice.notes = updates['notes']
                    
                    if 'terms_and_conditions' in updates:
                        invoice.terms_and_conditions = updates['terms_and_conditions']
                    
                    results['updated_invoices'] += 1
                    
                except Exception as e:
                    results['errors'].append({
                        'invoice_id': invoice.id,
                        'error': str(e)
                    })
                    results['failed_updates'] += 1
            
            # Commit changes
            self.db.commit()
            
            # Send real-time notification
            await self.websocket_service.broadcast_to_user(
                user_id, 
                {
                    'type': 'bulk_update_completed',
                    'data': {
                        'operation': 'invoice_bulk_update',
                        'results': results
                    }
                }
            )
            
            return results
            
        except Exception as e:
            self.db.rollback()
            raise HTTPException(status_code=500, detail=f"Bulk update failed: {str(e)}")

    async def bulk_send_invoices(self, user_id: int, invoice_ids: List[int]) -> Dict[str, Any]:
        """Send multiple invoices via email"""
        try:
            # Get draft invoices to send
            invoices = self.db.query(Invoice).filter(
                and_(
                    Invoice.user_id == user_id,
                    Invoice.id.in_(invoice_ids),
                    Invoice.status == InvoiceStatus.DRAFT
                )
            ).all()
            
            results = {
                'total_invoices': len(invoice_ids),
                'sent_invoices': 0,
                'failed_sends': 0,
                'errors': []
            }
            
            for invoice in invoices:
                try:
                    # Update invoice status to sent
                    invoice.status = InvoiceStatus.SENT
                    invoice.sent_date = datetime.utcnow()
                    invoice.email_sent_count += 1
                    invoice.last_email_sent = datetime.utcnow()
                    
                    # TODO: Trigger email sending task (implement with Celery)
                    # from app.tasks.email_tasks import send_invoice_email
                    # send_invoice_email.delay(invoice.id)
                    
                    results['sent_invoices'] += 1
                    
                except Exception as e:
                    results['errors'].append({
                        'invoice_id': invoice.id,
                        'error': str(e)
                    })
                    results['failed_sends'] += 1
            
            # Commit changes
            self.db.commit()
            
            # Send real-time notification
            await self.websocket_service.broadcast_to_user(
                user_id, 
                {
                    'type': 'bulk_send_completed',
                    'data': {
                        'operation': 'invoice_bulk_send',
                        'results': results
                    }
                }
            )
            
            return results
            
        except Exception as e:
            self.db.rollback()
            raise HTTPException(status_code=500, detail=f"Bulk send failed: {str(e)}")

    async def bulk_delete_invoices(self, user_id: int, invoice_ids: List[int], 
                                 force: bool = False) -> Dict[str, Any]:
        """Delete multiple invoices (only draft invoices unless forced)"""
        try:
            # Build query based on force parameter
            query = self.db.query(Invoice).filter(
                and_(
                    Invoice.user_id == user_id,
                    Invoice.id.in_(invoice_ids)
                )
            )
            
            if not force:
                # Only allow deletion of draft invoices
                query = query.filter(Invoice.status == InvoiceStatus.DRAFT)
            
            invoices = query.all()
            
            results = {
                'total_requested': len(invoice_ids),
                'deleted_invoices': 0,
                'skipped_invoices': 0,
                'errors': []
            }
            
            for invoice in invoices:
                try:
                    if not force and invoice.status != InvoiceStatus.DRAFT:
                        results['errors'].append({
                            'invoice_id': invoice.id,
                            'error': 'Can only delete draft invoices without force flag'
                        })
                        results['skipped_invoices'] += 1
                        continue
                    
                    self.db.delete(invoice)
                    results['deleted_invoices'] += 1
                    
                except Exception as e:
                    results['errors'].append({
                        'invoice_id': invoice.id,
                        'error': str(e)
                    })
                    results['skipped_invoices'] += 1
            
            # Commit changes
            self.db.commit()
            
            return results
            
        except Exception as e:
            self.db.rollback()
            raise HTTPException(status_code=500, detail=f"Bulk delete failed: {str(e)}")

    def _is_valid_status_transition(self, current_status: InvoiceStatus, new_status: InvoiceStatus) -> bool:
        """Check if status transition is valid"""
        valid_transitions = {
            InvoiceStatus.DRAFT: [InvoiceStatus.SENT, InvoiceStatus.CANCELLED],
            InvoiceStatus.SENT: [InvoiceStatus.VIEWED, InvoiceStatus.PAID, InvoiceStatus.PARTIALLY_PAID, 
                               InvoiceStatus.OVERDUE, InvoiceStatus.CANCELLED],
            InvoiceStatus.VIEWED: [InvoiceStatus.PAID, InvoiceStatus.PARTIALLY_PAID, InvoiceStatus.OVERDUE],
            InvoiceStatus.PARTIALLY_PAID: [InvoiceStatus.PAID, InvoiceStatus.OVERDUE],
            InvoiceStatus.OVERDUE: [InvoiceStatus.PAID, InvoiceStatus.PARTIALLY_PAID],
            InvoiceStatus.PAID: [InvoiceStatus.REFUNDED],
            InvoiceStatus.CANCELLED: [],  # Terminal state
            InvoiceStatus.REFUNDED: []   # Terminal state
        }
        
        return new_status in valid_transitions.get(current_status, [])