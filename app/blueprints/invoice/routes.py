from flask import render_template, redirect, url_for, flash, request, abort
from flask_login import current_user, login_required
from app.blueprints.invoice import invoice_bp
from app.forms import InvoiceForm
from app import db
from app.models import Invoice, InvoiceItem, Client
import datetime

def get_next_invoice_number():
    # This is a simple implementation. A more robust solution would handle
    # concurrency and allow for customizable prefixes.
    last_invoice = Invoice.query.filter_by(organization_id=current_user.organization_id).order_by(Invoice.id.desc()).first()
    if last_invoice and last_invoice.invoice_number:
        try:
            # Assuming format INV-YYYY-NNNN
            last_num = int(last_invoice.invoice_number.split('-')[-1])
            new_num = last_num + 1
            return f"INV-{datetime.date.today().year}-{new_num:04d}"
        except (ValueError, IndexError):
            pass # Fallback to default
    return f"INV-{datetime.date.today().year}-0001"

@invoice_bp.route('/invoices/new', methods=['GET', 'POST'])
@login_required
def create_invoice():
    form = InvoiceForm()
    if not current_user.organization.clients.first():
        flash('You must add a client before creating an invoice.', 'warning')
        return redirect(url_for('client.add_client'))

    if form.validate_on_submit():
        invoice = Invoice(
            organization_id=current_user.organization_id,
            client_id=form.client.data.id,
            issue_date=form.issue_date.data,
            due_date=form.due_date.data,
            notes=form.notes.data,
            invoice_number=get_next_invoice_number()
        )
        db.session.add(invoice)
        for item_form in form.items:
            item = InvoiceItem(
                description=item_form.description.data,
                quantity=item_form.quantity.data,
                unit_price=item_form.unit_price.data,
                invoice=invoice
            )
            db.session.add(item)
        db.session.commit()
        flash('Invoice created successfully!', 'success')
        return redirect(url_for('invoice.list_invoices'))

    elif request.method == 'GET':
        form.issue_date.data = datetime.date.today()
        form.due_date.data = datetime.date.today() + datetime.timedelta(days=30)

    return render_template('invoice/create_invoice.html', title='Create Invoice', form=form)

@invoice_bp.route('/invoices')
@login_required
def list_invoices():
    invoices = Invoice.query.filter_by(organization_id=current_user.organization_id).order_by(Invoice.issue_date.desc()).all()
    return render_template('invoice/list_invoices.html', invoices=invoices, title='Invoices')

@invoice_bp.route('/invoices/<int:invoice_id>')
@login_required
def view_invoice(invoice_id):
    invoice = Invoice.query.get_or_404(invoice_id)
    if invoice.organization_id != current_user.organization_id:
        abort(403)
    return render_template('invoice/view_invoice.html', invoice=invoice, title=f'Invoice {invoice.invoice_number}')
