"""
Views for the user blueprint
"""
import re
from flask.views import MethodView
from flask import request, jsonify, make_response
from flask_bcrypt import Bcrypt
from . import user_blueprint
from ..models import User
from ..decorators import MyDecorator
my_dec = MyDecorator()


class SearchUser(MethodView):
    """
    Handles searching of users
    """
    @staticmethod
    def get():
        """
        GET request to search users
        """
        user_id = my_dec.check_token()

        if user_id == 'Missing':
            return jsonify({'message': 'You cannot access that page without a token.'}), 401
        elif user_id == 'Invalid':
            return jsonify({'message': 'Your token is either expired or invalid.'}), 401
        else:
            search_query = request.args.get("q")

            if search_query:
                # if parameter q is specified
                result = User.query. \
                    filter(User.username.ilike('%' + search_query + '%')). \
                    filter_by(admin=False).all()
                output = []

                if not result:
                    response = {'message': 'No users matching the criteria were found'}
                    return make_response(jsonify(response)), 404

                for user in result:
                    if user.id == user_id:
                        continue
                    else:
                        obj = {
                            'id': user.id,
                            'username': user.username,
                            'date_created': user.date_created,
                            'date_modified': user.date_modified
                        }
                        output.append(obj)

                response = jsonify(output)
                response.status_code = 200
                return response


class UserProfile(MethodView):
    """
    Handles user profile operations
    """
    @staticmethod
    def get(u_id):
        """
        Loads user profile
        """
        user_id = my_dec.check_token()

        if user_id == 'Missing':
            return jsonify({'message': 'You cannot access that page without a token.'}), 401
        elif user_id == 'Invalid':
            return jsonify({'message': 'Your token is either expired or invalid.'}), 401
        else:
            try:
                int(u_id)
            except (ValueError, TypeError):
                # An error occurred, therefore return a string message containing the error
                response = {'message': 'The parameter provided should be an integer'}
                return make_response(jsonify(response)), 401

            user = User.query.filter_by(id=u_id).first()

            if not user:
                response = {'message': 'User does not exist'}
                return make_response(jsonify(response)), 404

            user = {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'date_created': user.date_created,
                'date_modified': user.date_modified
            }
            response = jsonify(user)
            response.status_code = 200
            return response

    @staticmethod
    def put(u_id):
        """
        Updates user profile
        """
        user_id = my_dec.check_token()

        if user_id == 'Missing':
            return jsonify({'message': 'You cannot access that page without a token.'}), 401
        elif user_id == 'Invalid':
            return jsonify({'message': 'Your token is either expired or invalid.'}), 401
        else:
            try:
                int(u_id)
            except (ValueError, TypeError):
                # An error occurred, therefore return a string message containing the error
                response = {'message': 'The parameter provided should be an integer'}
                return make_response(jsonify(response)), 401

            if str(user_id) != str(u_id):
                response = {'message': 'You do not have permission to edit this profile'}
                return make_response(jsonify(response)), 403

            user = User.query.filter_by(id=user_id).first()

            username = str(request.data.get('username', '')) if \
                str(request.data.get('username', '')) else user.username
            email = str(request.data.get('email', '')) if \
                str(request.data.get('email', '')) else user.email
            password = str(request.data.get('password', '')) if \
                str(request.data.get('password', '')) else user.password

            if username and email and password:
                if not re.match("^[a-zA-Z0-9 _]*$", username):
                    response = {
                        'message': 'The username cannot contain special characters. '
                                   'Only underscores'
                    }
                    return make_response(jsonify(response)), 400

                email_resp = my_dec.validate_email(email)
                if not email_resp:
                    response = {'message': 'The email is not valid'}
                    return make_response(jsonify(response)), 400

                if len(password) < 6:
                    response = {
                        'message': 'The password should be at least 6 characters long'
                    }
                    return make_response(jsonify(response)), 400

                users = User.query.all()

                for user_ob in users:
                    # Check if user exists
                    if str(user.id) != str(user_ob.id) and email.lower() == user_ob.email.lower():
                        response = {"message": "That user already exists"}
                        return make_response(jsonify(response)), 401

                # Update user
                user.username = username
                user.email = email
                user.password = Bcrypt().generate_password_hash(password).decode()
                user.save()

                response = jsonify({
                    'id': user.id,
                    'username': user.username,
                    'email': user.email,
                    'date_created': user.date_created,
                    'date_modified': user.date_modified
                })
                response.status_code = 200
                return response

    @staticmethod
    def delete(u_id):
        """
        Deletes a user profile
        """
        user_id = my_dec.check_token()

        if user_id == 'Missing':
            return jsonify({'message': 'You cannot access that page without a token.'}), 401
        elif user_id == 'Invalid':
            return jsonify({'message': 'Your token is either expired or invalid.'}), 401
        else:
            try:
                int(u_id)
            except (ValueError, TypeError):
                # An error occurred, therefore return a string message containing the error
                response = {'message': 'The parameter provided should be an integer'}
                return make_response(jsonify(response)), 401

            if str(user_id) != str(u_id):
                response = {'message': 'You do not have permission to delete this profile'}
                return make_response(jsonify(response)), 403

            user = User.query.filter_by(id=user_id).first()

            user.delete()

            response = {'message': 'Profile deleted successfully'}
            return make_response(jsonify(response)), 200


search_user_view = SearchUser.as_view('search_user_view')  # pylint: disable=invalid-name
user_profile_view = UserProfile.as_view('user_profile_view')  # pylint: disable=invalid-name

# Define rules
user_blueprint.add_url_rule('/users', view_func=search_user_view, methods=['GET'])
user_blueprint.add_url_rule('/users/<u_id>', view_func=user_profile_view,
                            methods=['GET', 'PUT', 'DELETE'])
