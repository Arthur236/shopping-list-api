"""
Initialize blueprint
"""
from flask import Blueprint

# This instance of a Blueprint that represents the authentication blueprint
item_blueprint = Blueprint('item_bp', __name__)

from . import views