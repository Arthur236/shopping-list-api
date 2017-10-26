"""
Initialize blueprint
"""
from flask import Blueprint

# This instance of a Blueprint that represents the authentication blueprint
shopping_list_blueprint = Blueprint('shopping_list_bp', __name__)  # pylint: disable=invalid-name

from . import views  # noqa
