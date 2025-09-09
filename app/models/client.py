from app import db
import datetime

class Client(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), index=True, nullable=False)
    email = db.Column(db.String(120), index=True, nullable=False)
    address = db.Column(db.Text)
    organization_id = db.Column(db.Integer, db.ForeignKey('organization.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)

    invoices = db.relationship('Invoice', backref='client', lazy='dynamic')

    def __repr__(self):
        return f'<Client {self.name}>'
