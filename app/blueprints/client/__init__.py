from flask import Blueprint

client_bp = Blueprint('client', __name__)

from app.blueprints.client import routes
