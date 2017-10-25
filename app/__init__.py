"""
Initialing the application
"""
import re
from functools import wraps
from flask_api import FlaskAPI
from flask_sqlalchemy import SQLAlchemy
from flask import request, jsonify, make_response, current_app, redirect
from sqlalchemy import func, or_, and_
import jwt

# Local import
from instance.config import app_config

# Initialize sql-alchemy
db = SQLAlchemy()


# Middleware for path prefixing
class PrefixMiddleware(object):
    """
    Middleware class for url prefixing
    """

    def __init__(self, app, prefix=''):
        self.app = app
        self.prefix = prefix

    def __call__(self, environ, start_response):

        if environ['PATH_INFO'].startswith(self.prefix):
            environ['PATH_INFO'] = environ['PATH_INFO'][len(self.prefix):]
            environ['SCRIPT_NAME'] = self.prefix
            return self.app(environ, start_response)

        start_response('404', [('Content-Type', 'text/plain')])
        return ["Ooops! Looks like we don't recognize this url.".encode()]


def create_app(config_name):
    """
    Initialize the application
    """
    from app.models import User, ShoppingList, ShoppingListItem, PasswordReset, Friend, SharedList

    app = FlaskAPI(__name__, instance_relative_config=True)
    app.config.from_object(app_config[config_name])
    app.config.from_pyfile('config.py')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.wsgi_app = PrefixMiddleware(app.wsgi_app, prefix='/v1')
    db.init_app(app)

    @app.before_first_request
    def insert_initial_user(*args, **kwargs):
        """
        Add admin user when tables are migrated
        """
        user = User.query.all()
        if not user:
            db.session.add(User(username='admin', email='admin@gmail.com', password='admin123'))
            db.session.commit()
            user = User.query.filter_by(email='admin@gmail.com').first()
            user.admin = True
            user.save()

    @app.errorhandler(404)
    def error_404(error):
        """
        Handles 404 errors
        """
        message = {
            'status': 404,
            'message': 'The resource at {}, cannot be found.'.format(request.url)
        }
        response = jsonify(message)
        response.status_code = 404

        return response

    @app.errorhandler(500)
    def error_500(error):
        """
        Handles 500 errors
        """
        message = {
            'status': 500,
            'message': 'Looks like something went wrong. '
                       'Our team of experts is working to fix this.'
        }
        response = jsonify(message)
        response.status_code = 500

        return response

    @app.route('/', methods=['GET'])
    def index():
        """
        Redirect user to api documentation
        """
        return redirect('http://docs.shoppinglistapi4.apiary.io')

    # ************************************ Friend System ************************************

    @app.route('/friends', methods=['GET', 'POST'])
    @token_required
    def get_friends_list(user_id):
        """
        GET - Retrieves all of a user's friends
        POST - Sends a friend request to a user
        """
        if request.method == "POST":
            try:
                friend_id = int(request.data.get('friend_id', ''))
            except ValueError:
                # An error occurred, therefore return a string message containing the error
                response = {'message': 'The parameters provided should be integers'}
                return make_response(jsonify(response)), 401

            if friend_id == user_id:
                response = {'message': 'You cannot befriend yourself'}
                return make_response(jsonify(response)), 403

            check_user_exists = User.query.filter_by(id=friend_id).first()
            if not check_user_exists:
                response = {'message': 'That user does not exist'}
                return make_response(jsonify(response)), 401

            if friend_id:
                friend = Friend.query.\
                    filter(or_(and_(Friend.user1 == user_id, Friend.user2 == friend_id),
                               and_(Friend.user1 == friend_id, Friend.user2 == user_id))).first()

                if not friend:
                    # The users are not friends
                    friend = Friend(user1=user_id, user2=friend_id)
                    friend.save()

                    response = {'message': 'Friend request sent'}
                    return make_response(jsonify(response)), 200

                elif friend.accepted:
                    response = {'message': 'You are already friends'}
                    return make_response(jsonify(response)), 401

                response = {'message': 'Friend request already sent'}
                return make_response(jsonify(response)), 401
        else:
            # GET
            search_query = request.args.get("q")
            try:
                limit = int(request.args.get('limit', 10))
                page = int(request.args.get('page', 1))
            except ValueError:
                # An error occurred, therefore return a string message containing the error
                response = {'message': 'The parameters provided should be integers'}
                return make_response(jsonify(response)), 401

            if search_query:
                result = User.query.filter(User.username.ilike('%' + search_query + '%')).all()
                friend_list = []
                search_output = []

                for r_fr in result:
                    output = Friend.query.\
                        filter(or_((and_(Friend.user1 == user_id, Friend.user2 == r_fr.id)),
                                   (and_(Friend.user1 == r_fr.id, Friend.user2 == user_id))),
                               Friend.accepted).first()
                    if output:
                        if output.user1 != user_id:
                            search_output.append(output.user1)
                        elif output.user2 != user_id:
                            search_output.append(output.user2)

                if not search_output:
                    response = {'message': 'You have no friends with that username'}
                    return make_response(jsonify(response)), 404

                for friend in search_output:
                    user = User.query.filter_by(id=friend).first()
                    obj = {
                        'username': user.username,
                        'email': user.email
                    }
                    friend_list.append(obj)

                response = jsonify(friend_list)
                response.status_code = 200
                return response

            friends = []
            friend_ids = []
            friend_list = Friend.query.\
                filter(or_(Friend.user1 == user_id, Friend.user2 == user_id), Friend.accepted).all()

            if not friend_list:
                response = {'message': 'You have no friends'}
                return make_response(jsonify(response)), 404

            for friend in friend_list:
                friend_ids.append(friend.user2)

            paginated_users = User.query.filter(User.id.in_(friend_ids)).\
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

    @app.route('/friends/<friend_id>', methods=['PUT'])
    @token_required
    def accept_friend_request(user_id, friend_id):
        """
        Handles acceptance of friend requests
        """
        try:
            int(friend_id)
        except Exception as e:
            # An error occurred, therefore return a string message containing the error
            response = {'message': 'The parameter needs to be an integer'}
            return make_response(jsonify(response)), 401

        friend = Friend.query.filter_by(user1=friend_id, user2=user_id).first()

        if request.method == 'PUT':
            if not friend:
                response = {'message': 'You have no friend request from that user'}
                return make_response(jsonify(response)), 404

            if friend.accepted:
                response = {'message': 'You are already friends with that user'}
                return make_response(jsonify(response)), 403

            friend.accepted = True
            friend.save()

            response = {'message': 'You are now friends'}
            return make_response(jsonify(response)), 200

    @app.route('/friends/<friend_id>', methods=['DELETE'])
    @token_required
    def delete_friend(user_id, friend_id):
        """
        Removes a user as a friend
        """
        try:
            int(friend_id)
        except Exception as e:
            # An error occurred, therefore return a string message containing the error
            response = {'message': str(e)}
            return make_response(jsonify(response)), 401

        friend = Friend.query. \
            filter(or_((and_(Friend.user1 == user_id, Friend.user2 == friend_id)),
                       (and_(Friend.user1 == friend_id, Friend.user2 == user_id))),
                   Friend.accepted).first()

        if request.method == 'DELETE':
            if not friend:
                response = {'message': 'You are not friends with that user'}
                return make_response(jsonify(response)), 404

            if friend.user1 == user_id or friend.user2 == user_id:
                friend.delete()

                response = {"message": "Friend deleted successfully"}
                return make_response(jsonify(response)), 200

    @app.route('/friends/requests', methods=['GET'])
    @token_required
    def get_friend_requests(user_id):
        """
        Shows requests a user has received
        """
        if request.method == "GET":
            search_query = request.args.get("q")
            try:
                limit = int(request.args.get('limit', 10))
                page = int(request.args.get('page', 1))
            except ValueError:
                # An error occurred, therefore return a string message containing the error
                response = {'message': 'The parameters provided should be integers'}
                return make_response(jsonify(response)), 401

            if search_query:
                result = User.query.filter(User.username.ilike('%' + search_query + '%')).all()
                friend_list = []
                search_output = []

                for r_fr in result:
                    output = Friend.query. \
                        filter(and_(Friend.user1 == r_fr.id, Friend.user2 == user_id,
                                    Friend.accepted == False)).first()
                    if output:
                        search_output.append(output.user2)

                if not search_output:
                    response = {'message': 'You have no request from that user'}
                    return make_response(jsonify(response)), 404

                for friend in search_output:
                    user = User.query.filter_by(id=friend).first()
                    obj = {
                        'username': user.username,
                        'email': user.email
                    }
                    friend_list.append(obj)

                response = jsonify(friend_list)
                response.status_code = 200
                return response

            friends = []
            friend_ids = []
            friend_list = Friend.query. \
                filter(and_(Friend.user2 == user_id, Friend.accepted == False)).all()

            if not friend_list:
                response = {'message': 'You have no friend requests'}
                return make_response(jsonify(response)), 404

            for friend in friend_list:
                friend_ids.append(friend.user2)

            paginated_users = User.query.filter(User.id.in_(friend_ids)). \
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

    # ************************************ Share System *************************************

    @app.route('/shopping_lists/share', methods=['GET', 'POST'])
    @token_required
    def shared_lists(user_id):
        """
        GET - Retrieves all shared lists
        POST - Shares a list
        """
        if request.method == "POST":
            try:
                list_id = int(request.data.get('list_id', ''))
                friend_id = int(request.data.get('friend_id', ''))
            except ValueError:
                # An error occurred, therefore return a string message containing the error
                response = {'message': 'The parameters provided should be integers'}
                return make_response(jsonify(response)), 401

            if list_id and friend_id:
                # Check if the users are already friends
                friend = Friend.query. \
                    filter(or_((and_(Friend.user1 == user_id, Friend.user2 == friend_id)),
                               (and_(Friend.user1 == friend_id, Friend.user2 == user_id))),
                           Friend.accepted).first()

                if friend:
                    # The users are friends
                    check_shared = SharedList.query.\
                        filter_by(user1=user_id, user2=friend_id, list_id=list_id).first()
                    if check_shared:
                        response = {'message': 'That list has already been shared'}
                        return make_response(jsonify(response)), 401

                    shared_list = SharedList(list_id, user_id, friend_id)
                    shared_list.save()

                    response = {'message': 'Shopping list shared successfully'}
                    return make_response(jsonify(response)), 200

                response = {'message': 'Lists can only be shared to friends'}
                return make_response(jsonify(response)), 401
        else:
            # GET
            search_query = request.args.get("q")
            try:
                limit = int(request.args.get('limit', 10))
                page = int(request.args.get('page', 1))
            except ValueError:
                # An error occurred, therefore return a string message containing the error
                response = {'message': 'The parameters provided should be integers'}
                return make_response(jsonify(response)), 401

            if search_query:
                shared_lists = []
                search_output = []
                # Get lists that match criteria
                result = ShoppingList.query. \
                    filter(ShoppingList.name.ilike('%' + search_query + '%')).all()

                if result:
                    for res in result:
                        # Get ids of lists that have been shared
                        output = SharedList.query. \
                            filter(or_(SharedList.user1 == user_id, SharedList.user2 == user_id)).\
                            filter_by(list_id=res.id).first()
                        if output:
                            search_output.append(output)

                if not search_output:
                    response = {'message': 'You have no shopping lists that match that criteria'}
                    return make_response(jsonify(response)), 404

                for list_out in search_output:
                    # Get names of lists that have been shared
                    sha_list = ShoppingList.query.filter_by(id=list_out.list_id).first()
                    obj = {
                        'id': sha_list.id,
                        'name': sha_list.name
                    }
                    shared_lists.append(obj)

                response = jsonify(shared_lists)
                response.status_code = 200
                return response

            shared_lists = []
            shared_lists_ids = []
            shared_list = SharedList.query.\
                filter(or_(SharedList.user1 == user_id, SharedList.user2 == user_id)).all()

            if not shared_list:
                response = {'message': 'You have no shared lists'}
                return make_response(jsonify(response)), 404

            for s_list in shared_list:
                shared_lists_ids.append(s_list.list_id)

            paginated_lists = ShoppingList.query.filter(ShoppingList.id.in_(shared_lists_ids)).\
                order_by(ShoppingList.name.asc()).paginate(page, limit)

            for sha_list in paginated_lists.items:
                obj = {
                    'id': sha_list.id,
                    'name': sha_list.name
                }
                shared_lists.append(obj)

            response = jsonify(shared_lists)
            response.status_code = 200
            return response

    @app.route('/shopping_lists/share/<list_id>', methods=['DELETE'])
    @token_required
    def stop_sharing(user_id, list_id):
        """
        Stops sharing a list
        """
        if request.method == "DELETE":
            try:
                int(list_id)
                friend_id = int(request.data.get('friend_id', ''))
            except Exception:
                # An error occurred, therefore return a string message containing the error
                response = {'message': 'Please ensure the parameter provided is correct'}
                return make_response(jsonify(response)), 401

            shopping_list = ShoppingList.query.filter_by(id=list_id).first()

            if not shopping_list:
                response = {'message': 'That list does not exist'}
                return make_response(jsonify(response)), 404

            if list_id and shopping_list:
                shared_list = SharedList.query.\
                    filter(or_(and_(SharedList.user1 == user_id, SharedList.user2 == friend_id),
                           and_(SharedList.user1 == friend_id, SharedList.user2 == user_id))).\
                    filter_by(list_id=list_id).first()

                if shared_list:
                    shared_list.delete()

                    response = {'message': 'List sharing stopped successfully'}
                    return make_response(jsonify(response)), 200

                response = {'message': 'That list has not been shared'}
                return make_response(jsonify(response)), 404

    @app.route('/shopping_lists/share/<list_id>/items', methods=['GET'])
    @token_required
    def get_shared_list_items(user_id, list_id):
        """
        Retrieves all items in shared shopping list
        """
        try:
            int(list_id)
        except Exception:
            # An error occurred, therefore return a string message containing the error
            response = {'message': 'Please ensure the parameter provided is an integer'}
            return make_response(jsonify(response)), 401

        if request.method == "GET":
            # Ensure that the list has been shared to that user
            check_shared = SharedList.query.\
                filter(and_(SharedList.list_id == list_id,
                            or_(SharedList.user1 == user_id, SharedList.user2 == user_id))).first()

            if not check_shared:
                response = {'message': 'You do not have permission to view items on that list'}
                return make_response(jsonify(response)), 403

            search_query = request.args.get("q")
            try:
                limit = int(request.args.get('limit', 10))
                page = int(request.args.get('page', 1))
            except ValueError:
                # An error occurred, therefore return a string message containing the error
                response = {'message': 'The parameters provided should be integers'}
                return make_response(jsonify(response)), 401

            if search_query:
                # if parameter q is specified
                shopping_list_items = ShoppingListItem.query. \
                    filter(ShoppingListItem.name.ilike('%' + search_query + '%')). \
                    filter_by(list_id=list_id).all()
                output = []

                if not shopping_list_items:
                    response = {'message': 'The list has no items matching that criteria'}
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

            paginated_items = ShoppingListItem.query.filter_by(list_id=list_id). \
                order_by(ShoppingListItem.name.asc()).paginate(page, limit)
            results = []

            if not paginated_items.items:
                response = {'message': 'That list has no items'}
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

    # Import the blueprints and register them on the app
    from .auth import auth_blueprint
    from .user import user_blueprint
    from .admin import admin_blueprint
    from .shopping_list import shopping_list_blueprint
    from .item import item_blueprint
    app.register_blueprint(auth_blueprint)
    app.register_blueprint(user_blueprint)
    app.register_blueprint(admin_blueprint)
    app.register_blueprint(shopping_list_blueprint)
    app.register_blueprint(item_blueprint)

    return app
