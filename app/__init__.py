"""
Initialing the application
"""
from flask_api import FlaskAPI
from flask_sqlalchemy import SQLAlchemy
from flask import request, jsonify, abort, make_response
import re
from sqlalchemy import func

# local import
from instance.config import app_config

# initialize sql-alchemy
db = SQLAlchemy()


def create_app(config_name):
    from app.models import ShoppingList, User, ShoppingListItem

    app = FlaskAPI(__name__, instance_relative_config=True)
    app.config.from_object(app_config[config_name])
    app.config.from_pyfile('config.py')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    db.init_app(app)

    @app.route('/auth/register', methods=['POST'])
    def register():
        if request.method == "POST":
            username = str(request.data.get('username', ''))
            password = str(request.data.get('password', ''))

            if username:
                if not re.match("^[a-zA-Z0-9_]*$", username):
                    response = {
                        'message': 'The username cannot contain special characters. Only underscores'
                    }
                    return make_response(jsonify(response)), 400

                if len(password) < 6:
                    response = {
                        'message': 'The password should be at least 6 characters long'
                    }
                    return make_response(jsonify(response)), 400
                
                user = models.User.query.filter(func.lower(User.username) == username.lower()).first()
                if not user:
                    # There is no user so we'll try to register them
                    try:
                        post_data = request.data
                        # Register the user
                        username = post_data['username']
                        password = post_data['password']
                        user = User(username=username, password=password)
                        user.save()

                        response = {
                            'message': 'You were registered successfully. Please log in.'
                        }
                        # return a response notifying the user that they registered successfully
                        return make_response(jsonify(response)), 201
                    except Exception as e:
                        # An error occurred, therefore return a string message containing the error
                        response = {
                            'message': str(e)
                        }
                        return make_response(jsonify(response)), 401
                else:
                    # There is an existing user. We don't want to register users twice
                    # Return a message to the user telling them that they they already exist
                    response = {
                        'message': 'User already exists. Please login.'
                    }

                    return make_response(jsonify(response)), 202

    @app.route('/auth/login', methods=['POST'])
    def login():
        if request.method == "POST":
            try:
                username = str(request.data.get('username', ''))
                if username:
                    user = User.query.filter_by(username=username).first()
                    # Try to authenticate the found user using their password
                    if user and user.password_is_valid(request.data['password']):
                        response = {
                            'message': 'You logged in successfully.'
                        }
                        return make_response(jsonify(response)), 200
                    else:
                        # User does not exist. Therefore, we return an error message
                        response = {
                            'message': 'Invalid username or password, Please try again'
                        }
                        return make_response(jsonify(response)), 401

            except Exception as e:
                # Create a response containing an string error message
                response = {
                    'message': str(e)
                }
                # Return a server error using the HTTP Error Code 500 (Internal Server Error)
                return make_response(jsonify(response)), 500

    @app.route('/shopping_lists', methods=['POST', 'GET'])
    def shopping_list():
        if request.method == "POST":
            name = str(request.data.get('name', ''))
            description = str(request.data.get('description', ''))
            if name:
                shopping_list = ShoppingList(1, name=name, description=description)
                shopping_list.save()
                response = jsonify({
                    'id': shopping_list.id,
                    'name': shopping_list.name,
                    'description': shopping_list.description,
                    'date_created': shopping_list.date_created,
                    'date_modified': shopping_list.date_modified
                })
                response.status_code = 201
                return response
        else:
            # GET
            shopping_list = ShoppingList.get_all()
            results = []

            for shopping_list in shopping_list:
                obj = {
                    'id': shopping_list.id,
                    'name': shopping_list.name,
                    'description': shopping_list.description,
                    'date_created': shopping_list.date_created,
                    'date_modified': shopping_list.date_modified
                }
                results.append(obj)
            response = jsonify(results)
            response.status_code = 200
            return response

    return app
