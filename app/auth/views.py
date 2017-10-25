"""
Views for the auth blueprint
"""
from . import auth_blueprint

import re
from flask.views import MethodView
from datetime import datetime, timedelta
from flask import request, jsonify, make_response, current_app
from sqlalchemy import func
import jwt
from flask_bcrypt import Bcrypt
from ..models import User, PasswordReset
from ..decorators import MyDecorator
md = MyDecorator()


class RegistrationView(MethodView):
    """
    Handles user registration
    """

    def post(self):
        """
        POST request for user registration
        """
        username = str(request.data.get('username', ''))
        email = str(request.data.get('email', ''))
        password = str(request.data.get('password', ''))

        if email and password and username:
            email_resp = md.validate_email(email)
            if not email_resp:
                response = {'message': 'The email is not valid'}
                return make_response(jsonify(response)), 400

            if not re.match("^[a-zA-Z0-9 _]*$", username):
                response = {
                    'message': 'The username cannot contain special characters. '
                               'Only underscores'
                }
                return make_response(jsonify(response)), 400

            if len(password) < 6:
                response = {
                    'message': 'The password should be at least 6 characters long'
                }
                return make_response(jsonify(response)), 400

            user = User.query.filter(func.lower(User.email) == email.lower()).first()
            if not user:
                # There is no user so we'll try to register them
                post_data = request.data
                # Register the user
                username = post_data['username']
                email = post_data['email']
                password = post_data['password']
                user = User(username=username, email=email, password=password)
                user.save()

                response = {'message': 'You were registered successfully. Please log in.'}
                # return a response notifying the user that they registered successfully
                return make_response(jsonify(response)), 201

            # There is an existing user. We don't want to register users twice
            # Return a message to the user telling them that they they already exist
            response = {'message': 'User already exists. Please login.'}
            return make_response(jsonify(response)), 202

        response = {'message': 'Please provide all required information'}
        return make_response(jsonify(response)), 400


class LoginView(MethodView):
    """
    Handles user log in
    """
    def post(self):
        """
        POST request for user login
        """
        email = str(request.data.get('email', ''))
        password = str(request.data.get('password', ''))

        if email and password:
            user = User.query.filter_by(email=email).first()
            # Try to authenticate the found user using their password
            if user and user.password_is_valid(request.data['password']):
                # Generate the access token. This will be used as the authorization header
                token = jwt.encode({'id': user.id,
                                    'exp': datetime.utcnow() + timedelta(minutes=30)},
                                   current_app.config.get('SECRET'))
                if token:
                    response = {
                        'access-token': token.decode('UTF-8'),
                        'message': 'You logged in successfully.'
                    }
                    return make_response(jsonify(response)), 200
            else:
                # User does not exist. Therefore, we return an error message
                response = {'message': 'Invalid email or password. Please try again'}
                return make_response(jsonify(response)), 401

        response = {'message': 'Email or password not provided'}
        return make_response(jsonify(response)), 400


class ResetView(MethodView):
    """
    Generates password reset token
    """
    def post(self):
        """
        POST request for password reset token
        """
        email = str(request.data.get('email', ''))

        if email:
            user = User.query.filter_by(email=email).first()
            if user:
                # Generate the password reset token
                token = jwt.encode({'email': user.email,
                                    'exp': datetime.utcnow() + timedelta(minutes=60)},
                                   current_app.config.get('SECRET'))
                if token:
                    reset_email = PasswordReset.query.filter_by(email=email).first()
                    if reset_email:
                        # Email already has token so delete it
                        reset_email.delete()

                    post_data = request.data
                    # Save reset details
                    email = post_data['email']
                    p_token = token.decode('UTF-8')
                    pass_reset = PasswordReset(email=email, token=p_token)
                    pass_reset.save()

                    response = {'pass-reset-token': token.decode('UTF-8')}
                    return make_response(jsonify(response)), 200
            else:
                # User does not exist. Therefore, we return an error message
                response = {'message': 'Invalid email. Please try again'}
                return make_response(jsonify(response)), 401

        response = {'message': 'Email not provided'}
        return make_response(jsonify(response)), 400


class PassReset(MethodView):
    """
    Handles password reset
    """
    def put(self, token):
        """
        POST request for password reset
        """
        # Retrieve email related to token
        reset_dets = PasswordReset.query.filter_by(token=token).first()

        if not reset_dets:
            response = {'message': 'The token is not valid or missing'}
            return make_response(jsonify(response)), 400

        if request.method == 'PUT':
            email = reset_dets.email
            password = str(request.data.get('password', ''))

            if email and password:
                if len(password) < 6:
                    response = {'message': 'The password should be at least 6 characters long'}
                    return make_response(jsonify(response)), 400

                user = User.query.filter(func.lower(User.email) == email.lower()).first()
                if user:

                    post_data = request.data

                    password = post_data['password']
                    password_hash = Bcrypt().generate_password_hash(password).decode()
                    user.password = password_hash
                    user.save()

                    response = {
                        'message': 'Password reset successfully. Please log in.'
                    }
                    # Return a response notifying the user that they registered successfully
                    return make_response(jsonify(response)), 201

            response = {'message': 'Email or password not provided'}
            return make_response(jsonify(response)), 400


registration_view = RegistrationView.as_view('register_view')
login_view = LoginView.as_view('login_view')
reset_token_view = ResetView.as_view('reset_token_view')
pass_reset_view = PassReset.as_view('pass_reset_view')

# Define the rule for the registration url then add it to the blueprint
auth_blueprint.add_url_rule(
    '/auth/register',
    view_func=registration_view,
    methods=['POST'])

# Define the rule for the login url then add it to the blueprint
auth_blueprint.add_url_rule('/auth/login', view_func=login_view, methods=['POST'])

auth_blueprint.add_url_rule('/auth/reset', view_func=reset_token_view, methods=['POST'])

auth_blueprint.add_url_rule('/auth/password/<token>', view_func=pass_reset_view, methods=['PUT'])
