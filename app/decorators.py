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
    def check_token(self):
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

        except Exception:
            return 'Invalid'

    def validate_email(self, email):
        """
        Helper function to validate email
        """
        if re.match("^[_a-z0-9-]+(\.[_a-z0-9-]+)*@[a-z0-9-]+(\.[a-z0-9-]+)*(\.[a-z]{2,4})$", email):
            return True

        return False