"""
Initialing the application
"""
from flask_api import FlaskAPI
from flask_sqlalchemy import SQLAlchemy
from flask import request, jsonify, abort, make_response, current_app
import re
from sqlalchemy import func
import jwt
from functools import wraps
from datetime import datetime, timedelta
from flask_bcrypt import Bcrypt

# local import
from instance.config import app_config

# initialize sql-alchemy
db = SQLAlchemy()


def create_app(config_name):
    from app.models import User, ShoppingList, ShoppingListItem, PasswordReset, Friend

    app = FlaskAPI(__name__, instance_relative_config=True)
    app.config.from_object(app_config[config_name])
    app.config.from_pyfile('config.py')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    db.init_app(app)

    @app.before_first_request
    def insert_initial_user(*args, **kwargs):
        user = User.query.all()
        if not user:
            db.session.add(User(username='admin', email='admin@gmail.com', password='admin123'))
            db.session.commit()
            user = User.query.filter_by(email='admin@gmail.com').first()
            user.admin = True
            user.save()

    def token_required(f):
        """
        Token decorator method
        """
        @wraps(f)
        def decorated(*args, **kwargs):
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
            except:
                return jsonify({'message': 'Token is invalid!'}), 401

            # Pass user object to the route
            return f(user_id, *args, **kwargs)

        return decorated

    def validate_email(email):
        """
        Function to validate email
        """
        if re.match("^[_a-z0-9-]+(\.[_a-z0-9-]+)*@[a-z0-9-]+(\.[a-z0-9-]+)*(\.[a-z]{2,4})$", email):
            return True
        return False

    @app.route('/auth/register', methods=['POST'])
    def register():
        if request.method == "POST":
            username = str(request.data.get('username', ''))
            email = str(request.data.get('email', ''))
            password = str(request.data.get('password', ''))

            if email:
                email_resp = validate_email(email)
                if not email_resp:
                    response = {
                        'message': 'The email is not valid'
                    }
                    return make_response(jsonify(response)), 400

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
                
                user = models.User.query.filter(func.lower(User.email) == email.lower()).first()
                if not user:
                    # There is no user so we'll try to register them
                    try:
                        post_data = request.data
                        # Register the user
                        username = post_data['username']
                        email = post_data['email']
                        password = post_data['password']
                        user = User(username=username, email=email, password=password)
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
                email = str(request.data.get('email', ''))

                if email:
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
                        response = {
                            'message': 'Invalid email or password. Please try again'
                        }
                        return make_response(jsonify(response)), 401

            except Exception as e:
                # Create a response containing an string error message
                response = {
                    'message': str(e)
                }
                # Return a server error using the HTTP Error Code 500 (Internal Server Error)
                return make_response(jsonify(response)), 500

    @app.route('/auth/reset', methods=['POST'])
    def reset():
        if request.method == "POST":
            try:
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
                                # email already has token so delete it
                                reset_email.delete()

                            post_data = request.data
                            # Save reset details
                            email = post_data['email']
                            p_token = token.decode('UTF-8')
                            pass_reset = PasswordReset(email=email, token=p_token)
                            pass_reset.save()

                            response = {
                                'pass-reset-token': token.decode('UTF-8')
                            }
                            return make_response(jsonify(response)), 200
                    else:
                        # User does not exist. Therefore, we return an error message
                        response = {
                            'message': 'Invalid email. Please try again'
                        }
                        return make_response(jsonify(response)), 401

            except Exception as e:
                # Create a response containing an string error message
                response = {
                    'message': str(e)
                }
                # Return a server error using the HTTP Error Code 500 (Internal Server Error)
                return make_response(jsonify(response)), 500

    @app.route('/auth/password/<token>', methods=['PUT'])
    def password_reset(token):
        # retrieve email related to token
        reset_dets = PasswordReset.query.filter_by(token=token).first()

        if not reset_dets:
            response = {
                'message': 'The token is not valid or missing'
            }
            return make_response(jsonify(response)), 400

        if request.method == 'PUT':
            email = reset_dets.email
            password = str(request.data.get('password', ''))

            if email and password:
                if len(password) < 6:
                    response = {
                        'message': 'The password should be at least 6 characters long'
                    }
                    return make_response(jsonify(response)), 400

                user = models.User.query.filter(func.lower(User.email) == email.lower()).first()
                if user:
                    try:
                        post_data = request.data

                        password = post_data['password']
                        password_hash = Bcrypt().generate_password_hash(password).decode()
                        user.password = password_hash
                        user.save()

                        response = {
                            'message': 'Password reset successfully. Please log in.'
                        }
                        # return a response notifying the user that they registered successfully
                        return make_response(jsonify(response)), 201
                    except Exception as e:
                        # An error occurred, therefore return a string message containing the error
                        response = {
                            'message': str(e)
                        }
                        return make_response(jsonify(response)), 401

    @app.route('/users', methods=['GET'])
    @token_required
    def get_all_users(user_id):
        search_query = request.args.get("q")
        limit = int(request.args.get('limit', 10))
        page = int(request.args.get('page', 1))

        if search_query:
            # if parameter q is specified
            result = User.query.filter(User.username.ilike('%' + search_query + '%'))
            output = []

            if not result:
                response = {'message': 'No users were found'}
                return make_response(jsonify(response)), 404

            for user in result:
                if user.id == user_id:
                    continue
                else:
                    obj = {
                        'id': user.id,
                        'username': user.username,
                        'email': user.email,
                        'date_created': user.date_created,
                        'date_modified': user.date_modified
                    }
                    output.append(obj)

            response = jsonify(output)
            response.status_code = 200
            return response

        users = []
        paginated_users = User.query.order_by(User.username.asc()).paginate(page, limit)

        if not paginated_users:
            response = {'message': 'No users were found'}
            return make_response(jsonify(response)), 404

        for user in paginated_users.items:
            if user.id == user_id:
                continue
            else:
                obj = {
                    'id': user.id,
                    'username': user.username,
                    'email': user.email,
                    'admin': user.admin,
                    'date_created': user.date_created,
                    'date_modified': user.date_modified
                }
                users.append(obj)

        response = jsonify(users)
        response.status_code = 200
        return response

    """ ********************************** Admin Operations *********************************** """

    @app.route('/admin/users/<id>', methods=['GET'])
    @token_required
    def get_user(user_id, id):
        user = User.query.filter_by(id=user_id).first()

        if not user.admin:
            response = {'message': 'Cannot perform that operation without admin rights'}
            return make_response(jsonify(response)), 403

        user = User.query.filter_by(id=id).first()

        if not user:
            response = {'message': 'User does not exist'}
            return make_response(jsonify(response)), 404

        user = {
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'admin': user.admin,
            'date_created': user.date_created,
            'date_modified': user.date_modified
        }
        response = jsonify(user)
        response.status_code = 200
        return response

    @app.route('/admin/users/<id>', methods=['DELETE'])
    @token_required
    def delete_user(user_id, id):
        user = User.query.filter_by(id=user_id).first()

        if not user.admin:
            response = {'message': 'Cannot perform that operation without admin rights'}
            return make_response(jsonify(response)), 403

        user = User.query.filter_by(id=id).first()

        if not user:
            response = {'message': 'User does not exist'}
            return make_response(jsonify(response)), 404

        if user.id == user_id:
            response = {'message': 'You cannot delete yourself'}
            return make_response(jsonify(response)), 403

        db.session.delete(user)
        db.session.commit()

        response = {'message': 'User deleted successfully'}
        return make_response(jsonify(response)), 200

    """ *********************************** Shopping Lists ************************************ """

    @app.route('/shopping_lists', methods=['POST', 'GET'])
    @token_required
    def shopping_list(user_id):
        if request.method == "POST":
            name = str(request.data.get('name', ''))
            description = str(request.data.get('description', ''))

            if name:
                if not re.match("^[a-zA-Z0-9 _]*$", name):
                    response = {
                        'message': 'The list name cannot contain special characters. Only underscores'
                    }
                    return make_response(jsonify(response)), 400

                s_list = models.ShoppingList.query.filter(func.lower(ShoppingList.name) == name.lower(),
                                                          ShoppingList.user_id == user_id).first()

                if not s_list:
                    # There is no list so we'll try to create it
                    try:

                        shopping_list = ShoppingList(user_id=user_id, name=name, description=description)
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

                    except Exception as e:
                        # An error occurred, therefore return a string message containing the error
                        response = {
                            'message': str(e)
                        }
                        return make_response(jsonify(response)), 401
                else:
                    response = {
                        'message': 'That shopping list already exists.'
                    }
                    return make_response(jsonify(response)), 401
        else:
            # GET
            search_query = request.args.get("q")
            limit = int(request.args.get('limit', 10))
            page = int(request.args.get('page', 1))

            if search_query:
                # if parameter q is specified
                shopping_lists = ShoppingList.query.filter(ShoppingList.name.ilike('%' + search_query + '%'))\
                    .filter_by(user_id=user_id).all()
                output = []

                if not shopping_lists:
                    response = {'message': 'User has no shopping lists'}
                    return make_response(jsonify(response)), 404

                for s_list in shopping_lists:
                    obj = {
                        'id': s_list.id,
                        'name': s_list.name,
                        'description': s_list.description,
                        'date_created': s_list.date_created,
                        'date_modified': s_list.date_modified
                    }
                    output.append(obj)
                response = jsonify(output)
                response.status_code = 200
                return response

            paginated_lists = ShoppingList.query.filter_by(user_id=user_id).\
                order_by(ShoppingList.name.asc()).paginate(page, limit)
            results = []

            if not paginated_lists:
                response = {'message': 'User has no shopping lists'}
                return make_response(jsonify(response)), 404

            for shopping_list in paginated_lists.items:
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

    @app.route('/shopping_lists/<list_id>', methods=['GET'])
    @token_required
    def get_shopping_list(user_id, list_id):
        # retrieve a shopping list using it's id
        shopping_list = ShoppingList.query.filter_by(id=list_id, user_id=user_id).first()

        if shopping_list.user_id == user_id:
            response = jsonify({
                'id': shopping_list.id,
                'name': shopping_list.name,
                'description': shopping_list.description,
                'date_created': shopping_list.date_created,
                'date_modified': shopping_list.date_modified
            })
            response.status_code = 200
            return response
        else:
            return {
                       "message": "You do not have permissions to view that shopping list"
                   }, 403

    @app.route('/shopping_lists/<list_id>', methods=['PUT'])
    @token_required
    def edit_shopping_list(user_id, list_id):
        # retrieve a shopping list using it's id
        shopping_list = ShoppingList.query.filter_by(id=list_id, user_id=user_id).first()

        if request.method == 'PUT':
            name = str(request.data.get('name', ''))
            description = str(request.data.get('description', ''))

            if not re.match("^[a-zA-Z0-9 _]*$", name):
                response = {
                    'message': 'The list name cannot contain special characters. Only underscores'
                }
                return make_response(jsonify(response)), 400

            s_list = models.ShoppingList.query.filter(func.lower(ShoppingList.name) == name.lower()).first()

            # There is no list so we'll try to create it
            if not s_list:
                # Check if user is owner
                if shopping_list.user_id == user_id:
                    try:

                        shopping_list.name = name
                        shopping_list.description = description
                        shopping_list.save()

                        response = jsonify({
                            'id': shopping_list.id,
                            'name': shopping_list.name,
                            'description': shopping_list.description,
                            'date_created': shopping_list.date_created,
                            'date_modified': shopping_list.date_modified
                        })
                        response.status_code = 200
                        return response

                    except Exception as e:
                        # An error occurred, therefore return a string message containing the error
                        response = {
                            'message': str(e)
                        }
                        return make_response(jsonify(response)), 401
                else:
                    return {
                               "message": "You do not have permissions to edit that shopping list"
                           }, 403
            else:
                return {
                           "message": "Shopping list already exists"
                       }, 401

    @app.route('/shopping_lists/<list_id>', methods=['DELETE'])
    @token_required
    def delete_shopping_list(user_id, list_id):
        # retrieve a shopping list using it's id
        shopping_list = ShoppingList.query.filter_by(id=list_id, user_id=user_id).first()

        if not shopping_list:
            # Raise an HTTPException with a 404 not found status code
            abort(404)

        if request.method == 'DELETE':
            if shopping_list.user_id == user_id:
                shopping_list.delete()
                return {
                           "message": "Shopping list {} deleted successfully".format(shopping_list.id)
                       }, 200
            else:
                return {
                           "message": "You do not have permissions to delete that shopping list"
                       }, 403

    """ ********************************* Shopping List Items ********************************* """

    @app.route('/shopping_lists/<list_id>/items', methods=['POST', 'GET'])
    @token_required
    def shopping_list_item(user_id, list_id):
        if request.method == "POST":
            name = str(request.data.get('name', ''))
            quantity = str(request.data.get('quantity', ''))
            unit_price = str(request.data.get('unit_price', ''))

            if name:
                if not re.match("^[a-zA-Z0-9 _]*$", name):
                    response = {
                        'message': 'The item name cannot contain special characters. Only underscores'
                    }
                    return make_response(jsonify(response)), 400

                s_list_item = \
                    models.ShoppingListItem.query.filter(func.lower(ShoppingListItem.name) == name.lower(),
                                                         ShoppingListItem.list_id == list_id).first()

                if not s_list_item:
                    # There is no list item so we'll try to create it
                    try:

                        shopping_list_item = ShoppingListItem(list_id=list_id, name=name, quantity=quantity,
                                                              unit_price=unit_price)
                        shopping_list_item.save()

                        response = jsonify({
                            'id': shopping_list_item.id,
                            'name': shopping_list_item.name,
                            'quantity': shopping_list_item.quantity,
                            'unit_price': shopping_list_item.unit_price,
                            'date_created': shopping_list_item.date_created,
                            'date_modified': shopping_list_item.date_modified
                        })
                        response.status_code = 201
                        return response

                    except Exception as e:
                        # An error occurred, therefore return a string message containing the error
                        response = {
                            'message': str(e)
                        }
                        return make_response(jsonify(response)), 401
                else:
                    response = {
                        'message': 'That item item already exists.'
                    }
                    return make_response(jsonify(response)), 401
        else:
            # GET
            search_query = request.args.get("q")
            limit = int(request.args.get('limit', 10))
            page = int(request.args.get('page', 1))
            
            if search_query:
                # if parameter q is specified
                shopping_list_items = ShoppingListItem.query.\
                    filter(ShoppingListItem.name.ilike('%' + search_query + '%')).\
                    filter_by(list_id=list_id).all()
                output = []

                if not shopping_list_items:
                    response = {'message': 'The list has no items'}
                    return make_response(jsonify(response)), 404

                for list_item in shopping_list_items:
                    obj = {
                        'id': list_item.id,
                        'name': list_item.name,
                        'quantity': list_item.quantity,
                        'unit_price': list_item.unit_price,
                        'date_created': list_item.date_created,
                        'date_modified': list_item.date_modified
                    }
                    output.append(obj)
                response = jsonify(output)
                response.status_code = 200
                return response

            paginated_items = ShoppingListItem.query.filter_by(list_id=list_id).\
                order_by(ShoppingListItem.name.asc()).paginate(page, limit)
            results = []

            if not paginated_items:
                response = {'message': 'The list has no items'}
                return make_response(jsonify(response)), 404

            for shopping_list_item in paginated_items.items:
                obj = {
                    'id': shopping_list_item.id,
                    'name': shopping_list_item.name,
                    'quantity': shopping_list_item.quantity,
                    'unit_price': shopping_list_item.unit_price,
                    'date_created': shopping_list_item.date_created,
                    'date_modified': shopping_list_item.date_modified
                }
                results.append(obj)
            response = jsonify(results)
            response.status_code = 200
            return response

    @app.route('/shopping_lists/<list_id>/items/<item_id>', methods=['GET'])
    @token_required
    def get_shopping_list_item(user_id, list_id, item_id):
        # retrieve a shopping list item using it's id
        shopping_list = ShoppingList.query.filter_by(id=list_id, user_id=user_id).first()
        shopping_list_item = ShoppingListItem.query.filter_by(id=item_id, list_id=list_id).first()

        # Check if item belongs to its owner's list
        if shopping_list.user_id == user_id:
            response = jsonify({
                'id': shopping_list_item.id,
                'name': shopping_list_item.name,
                'quantity': shopping_list_item.quantity,
                'unit_price': shopping_list_item.unit_price,
                'date_created': shopping_list_item.date_created,
                'date_modified': shopping_list_item.date_modified
            })
            response.status_code = 201
            return response
        else:
            return {
                       "message": "You do not have permissions to view that item"
                   }, 403

    @app.route('/shopping_lists/<list_id>/items/<item_id>', methods=['PUT'])
    @token_required
    def edit_item(user_id, list_id, item_id):
        # retrieve a shopping list item using it's id
        shopping_list = ShoppingList.query.filter_by(id=list_id, user_id=user_id).first()
        shopping_list_item = ShoppingListItem.query.filter_by(id=item_id, list_id=list_id).first()

        if request.method == 'PUT':
            name = str(request.data.get('name', ''))
            quantity = str(request.data.get('quantity', ''))
            unit_price = str(request.data.get('unit_price', ''))

            if not re.match("^[a-zA-Z0-9 _]*$", name):
                response = {
                    'message': 'The item name cannot contain special characters. Only underscores'
                }
                return make_response(jsonify(response)), 400

            s_list_item = \
                models.ShoppingListItem.query.filter(func.lower(ShoppingListItem.name) == name.lower(),
                                                     ShoppingListItem.list_id == list_id).first()

            # There is no item so we'll try to create it
            if not s_list_item:
                # Check if item belongs to its owner's list
                if shopping_list.user_id == user_id:
                    try:
                        shopping_list_item.name = name
                        shopping_list_item.quantity = quantity
                        shopping_list_item.unit_price = unit_price
                        shopping_list_item.save()

                        response = jsonify({
                            'id': shopping_list_item.id,
                            'name': shopping_list_item.name,
                            'quantity': shopping_list_item.quantity,
                            'unit_price': shopping_list_item.unit_price,
                            'date_created': shopping_list_item.date_created,
                            'date_modified': shopping_list_item.date_modified
                        })
                        response.status_code = 201
                        return response

                    except Exception as e:
                        # An error occurred, therefore return a string message containing the error
                        response = {
                            'message': str(e)
                        }
                        return make_response(jsonify(response)), 401
                else:
                    return {
                               "message": "You do not have permissions to edit that item"
                           }, 403
            else:
                return {
                           "message": "Item already exists"
                       }, 401

    @app.route('/shopping_lists/<list_id>/items/<item_id>', methods=['DELETE'])
    @token_required
    def delete_item(user_id, list_id, item_id):
        # retrieve a shopping list item using it's id
        shopping_list = ShoppingList.query.filter_by(id=list_id, user_id=user_id).first()
        shopping_list_item = ShoppingListItem.query.filter_by(id=item_id, list_id=list_id).first()

        if not shopping_list_item:
            # Raise an HTTPException with a 404 not found status code
            abort(404)

        if request.method == 'DELETE':
            if shopping_list.user_id == user_id:
                shopping_list.delete()
                return {
                           "message": "Item {} deleted successfully".format(shopping_list.id)
                       }, 201
            else:
                return {
                           "message": "You do not have permissions to delete that item"
                       }, 403

    """ ************************************ Friend System ************************************ """

    @app.route('/friends', methods=['GET', 'POST'])
    @token_required
    def get_friends_list(user_id):
        if request.method == "POST":
            try:
                friend_id = int(request.data.get('friend_id', ''))
            except Exception as e:
                # An error occurred, therefore return a string message containing the error
                response = {'message': str(e)}
                return make_response(jsonify(response)), 401

            if friend_id == user_id:
                response = {'message': 'You cannot befriend yourself'}
                return make_response(jsonify(response)), 403

            check_user_exists = User.query.filter_by(id=friend_id).first()
            if not check_user_exists:
                response = {'message': 'That user does not exist'}
                return make_response(jsonify(response)), 401

            if friend_id:
                friend = Friend.query.filter(Friend.user1 == user_id, Friend.user2 == friend_id).first()

                if not friend:
                    # The users are not friends
                    try:

                        friend = Friend(user1=user_id, user2=friend_id)
                        friend.save()

                        response = jsonify({
                            'id': friend.id,
                            'user1': friend.user1,
                            'user2': friend.user2,
                            'date_created': friend.date_created,
                            'date_modified': friend.date_modified
                        })
                        response.status_code = 201
                        return response

                    except Exception as e:
                        # An error occurred, therefore return a string message containing the error
                        response = {'message': str(e)}
                        return make_response(jsonify(response)), 401
                else:
                    response = {'message': 'You are already friends'}
                    return make_response(jsonify(response)), 401
        else:
            # GET
            search_query = request.args.get("q")
            limit = int(request.args.get('limit', 10))
            page = int(request.args.get('page', 1))

            if search_query:
                # if parameter q is specified
                result = Friend.query.filter(Friend.user2.ilike('%' + search_query + '%')).\
                    filter_by(user1=user_id).all()
                output = []

                if not result:
                    response = {'message': 'You have no friends'}
                    return make_response(jsonify(response)), 404

                for friend in result:
                    user = User.query.filter_by(id=friend.user2)
                    obj = {
                        'username': user.username,
                        'email': user.email
                    }
                    output.append(obj)

                response = jsonify(output)
                response.status_code = 200
                return response

            friends = []
            friend_list = Friend.query.filter_by(user1=user_id).all()

            if not friend_list:
                response = {'message': 'You have no friends'}
                return make_response(jsonify(response)), 404

            for friend in friend_list:
                paginated_users = User.query.filter_by(id=friend.user2).\
                    order_by(User.username.asc()).paginate(page, limit)

                for user in paginated_users.items:
                    obj = {
                        'username': user.username,
                        'email': user.email
                    }
                    friends.append(obj)

            response = jsonify(friends)
            response.status_code = 200
            return response

    return app
