from flask import Blueprint

invoice_bp = Blueprint('invoice', __name__)

from app.blueprints.invoice import routes
