from flask_wtf import FlaskForm
from wtforms import (
    StringField, PasswordField, BooleanField, SubmitField, TextAreaField,
    Form, FieldList, FormField, DecimalField, DateField
)
from wtforms.validators import DataRequired, Email, EqualTo, ValidationError
from wtforms_sqlalchemy.fields import QuerySelectField
from flask_login import current_user
from app.models import User, Client

class ClientForm(FlaskForm):
    name = StringField('Client Name', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    address = TextAreaField('Address')
    submit = SubmitField('Save Client')

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Sign In')

class RegistrationForm(FlaskForm):
    organization_name = StringField('Organization Name', validators=[DataRequired()])
    username = StringField('Username', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    password2 = PasswordField(
        'Repeat Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Register')

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user is not None:
            raise ValidationError('Please use a different username.')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user is not None:
            raise ValidationError('Please use a different email address.')

def client_query():
    if not current_user.is_authenticated:
        return []
    return Client.query.filter_by(organization_id=current_user.organization_id).all()

class InvoiceItemForm(Form):
    description = StringField('Description', validators=[DataRequired()])
    quantity = DecimalField('Quantity', default=1, places=2)
    unit_price = DecimalField('Unit Price', default=0.00, places=2)

class InvoiceForm(FlaskForm):
    client = QuerySelectField('Client', query_factory=client_query, get_label='name', allow_blank=True)
    issue_date = DateField('Issue Date', format='%Y-%m-%d', validators=[DataRequired()])
    due_date = DateField('Due Date', format='%Y-%m-%d', validators=[DataRequired()])
    items = FieldList(FormField(InvoiceItemForm), min_entries=1)
    notes = TextAreaField('Notes')
    submit = SubmitField('Create Invoice')
