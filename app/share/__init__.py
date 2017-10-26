"""
Initialize blueprint
"""
from flask import Blueprint

# This instance of a Blueprint that represents the authentication blueprint
share_blueprint = Blueprint('share_bp', __name__)  # pylint: disable=invalid-name

from . import views  # noqa
