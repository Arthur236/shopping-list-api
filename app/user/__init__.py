"""
Initialize blueprint
"""
from flask import Blueprint

# This instance of a Blueprint that represents the authentication blueprint
user_blueprint = Blueprint('user_bp', __name__)  # pylint: disable=invalid-name

from . import views  # noqa
