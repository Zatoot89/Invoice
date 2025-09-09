from app import db
import datetime
import enum
from sqlalchemy.ext.hybrid import hybrid_property

class InvoiceStatus(str, enum.Enum):
    DRAFT = 'draft'
    SENT = 'sent'
    PAID = 'paid'
    VOID = 'void'

class Invoice(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    invoice_number = db.Column(db.String(64), index=True) # Should be unique per organization
    status = db.Column(db.Enum(InvoiceStatus), default=InvoiceStatus.DRAFT, nullable=False)
    issue_date = db.Column(db.Date, default=datetime.date.today, nullable=False)
    due_date = db.Column(db.Date)
    notes = db.Column(db.Text)

    organization_id = db.Column(db.Integer, db.ForeignKey('organization.id'), nullable=False)
    client_id = db.Column(db.Integer, db.ForeignKey('client.id'), nullable=False)

    items = db.relationship('InvoiceItem', backref='invoice', lazy='dynamic', cascade="all, delete-orphan")

    @hybrid_property
    def total(self):
        return sum(item.total for item in self.items)

    def __repr__(self):
        return f'<Invoice {self.invoice_number}>'

class InvoiceItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    description = db.Column(db.String(256), nullable=False)
    quantity = db.Column(db.Numeric(10, 2), nullable=False)
    unit_price = db.Column(db.Numeric(10, 2), nullable=False)
    invoice_id = db.Column(db.Integer, db.ForeignKey('invoice.id'), nullable=False)

    @hybrid_property
    def total(self):
        return self.quantity * self.unit_price

    def __repr__(self):
        return f'<InvoiceItem {self.description}>'
