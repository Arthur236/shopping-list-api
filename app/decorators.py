"""
Custom decorator functions
"""
import re
import jwt
from flask import request, current_app
from app.models import User


class MyDecorator(object):
    """
    Class to hold decorator methods
    """
    @staticmethod
    def check_token():
        """
        Helper function to check access token header
        """
        token = None

        # Check if header token exists
        if 'x-access-token' in request.headers:
            token = request.headers['x-access-token']

        if not token:
            return 'Missing'

        try:
            data = jwt.decode(token, current_app.config.get('SECRET'))
            current_user = User.query.filter_by(id=data['id']).first()
            user_id = current_user.id
            return user_id

        except (jwt.InvalidTokenError, jwt.ExpiredSignatureError):
            return 'Invalid'

    @staticmethod
    def validate_email(email):
        """
        Helper function to validate email
        """
        email_exp = r"(^[_a-z0-9-]+(\.[_a-z0-9-]+)*@[a-z0-9-]+(\.[a-z0-9-]+)*(\.[a-z]{2,4})$)"

        if re.match(email_exp, email):
            return True

        return False
