"""
Custom decorator functions
"""
import re
from functools import wraps
import jwt
from flask import request, jsonify, current_app
from app.models import User


class MyDecorator(object):
    """
    Class to hold decorator methods
    """
    def token_required(self, f):
        """
        Token decorator method
        """

        @wraps(f)
        def decorated(*args, **kwargs):
            """
            Check if token exists
            """
            token = None

            # Check if header token exists
            if 'x-access-token' in request.headers:
                token = request.headers['x-access-token']

            if not token:
                return jsonify({'message': 'Token is missing!'}), 401

            try:
                data = jwt.decode(token, current_app.config.get('SECRET'))
                current_user = User.query.filter_by(id=data['id']).first()
                user_id = current_user.id
            except Exception:
                return jsonify({'message': 'Token is invalid!'}), 401

            # Pass user object to the route
            return f(user_id, *args, **kwargs)

        return decorated

    def validate_email(self, email):
        """
        Helper function to validate email
        """
        if re.match("^[_a-z0-9-]+(\.[_a-z0-9-]+)*@[a-z0-9-]+(\.[a-z0-9-]+)*(\.[a-z]{2,4})$", email):
            return True

        return False
