"""
Initialize blueprint
"""
from flask import Blueprint

# This instance of a Blueprint that represents the authentication blueprint
friend_blueprint = Blueprint('friend_bp', __name__)

from . import views
