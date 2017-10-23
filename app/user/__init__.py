"""
Initialize blueprint
"""
from flask import Blueprint

# This instance of a Blueprint that represents the authentication blueprint
user_blueprint = Blueprint('user', __name__)

from . import views
