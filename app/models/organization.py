from app import db

class Organization(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), index=True)
    users = db.relationship('User', backref='organization', lazy='dynamic')

    def __repr__(self):
        return f'<Organization {self.name}>'
