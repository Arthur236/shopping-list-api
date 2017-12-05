"""
Views for the friend blueprint
"""
from flask.views import MethodView
from flask import request, jsonify, make_response
from sqlalchemy.sql.expression import false
from sqlalchemy import and_, or_
from . import friend_blueprint
from ..models import Friend, User
from ..decorators import MyDecorator
my_dec = MyDecorator()


class FriendOps(MethodView):
    """
    Handles sending friend requests and showing friends
    """
    @staticmethod
    def post():
        """
        POST - Sends a friend request to a user
        """
        user_id = my_dec.check_token()

        if user_id == 'Missing':
            return jsonify({'message': 'You cannot access that page without a token.'}), 401
        elif user_id == 'Invalid':
            return jsonify({'message': 'Your token is either expired or invalid.'}), 401
        else:
            try:
                friend_id = int(request.data.get('friend_id', ''))
            except (ValueError, TypeError):
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

    @staticmethod
    def get():
        """
        GET - Retrieves all of a user's friends
        """
        user_id = my_dec.check_token()

        if user_id == 'Missing':
            return jsonify({'message': 'You cannot access that page without a token.'}), 401
        elif user_id == 'Invalid':
            return jsonify({'message': 'Your token is either expired or invalid.'}), 401
        else:
            search_query = request.args.get("q")
            try:
                limit = int(request.args.get('limit', 10))
                page = int(request.args.get('page', 1))
            except (ValueError, TypeError):
                # An error occurred, therefore return a string message containing the error
                response = {'message': 'The parameters provided should be integers'}
                return make_response(jsonify(response)), 401

            if search_query:
                result = User.query.filter(User.username.ilike('%' + search_query + '%')).all()
                friend_list = []
                search_output = []

                for r_fr in result:
                    output = Friend.query. \
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
                        'id': user.id,
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
                filter(or_(Friend.user1 == user_id, Friend.user2 == user_id), Friend.accepted).all()

            if not friend_list:
                response = {'message': 'You have no friends'}
                return make_response(jsonify(response)), 404

            for friend in friend_list:
                friend_ids.append(friend.user2)

            paginated_users = User.query.filter(User.id.in_(friend_ids)). \
                order_by(User.username.asc()).paginate(page, limit)

            for user in paginated_users.items:
                obj = {
                    'id': user.id,
                    'username': user.username,
                    'email': user.email
                }
                friends.append(obj)

            next_page = 'None'
            previous_page = 'None'

            if paginated_users.has_next:
                next_page = '/friends' + '?page=' + str(page + 1) + \
                            '&limit=' + str(limit)
            if paginated_users.has_prev:
                previous_page = '/friends' + '?page=' + str(page - 1) + \
                                '&limit=' + str(limit)

            response = {
                'previous_page': previous_page,
                'next_page': next_page,
                'friends': friends
            }

            return make_response(jsonify(response)), 200


class FriendMan(MethodView):
    """
    Handles friend manipulation
    """
    @staticmethod
    def put(friend_id):
        """
        Handles acceptance of friend requests
        """
        user_id = my_dec.check_token()

        if user_id == 'Missing':
            return jsonify({'message': 'You cannot access that page without a token.'}), 401
        elif user_id == 'Invalid':
            return jsonify({'message': 'Your token is either expired or invalid.'}), 401
        else:
            try:
                int(friend_id)
            except (ValueError, TypeError):
                # An error occurred, therefore return a string message containing the error
                response = {'message': 'The parameter needs to be an integer'}
                return make_response(jsonify(response)), 401

            friend = Friend.query.filter_by(user1=friend_id, user2=user_id).first()

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

    @staticmethod
    def delete(friend_id):
        """
        Removes a user as a friend
        """
        user_id = my_dec.check_token()

        if user_id == 'Missing':
            return jsonify({'message': 'You cannot access that page without a token.'}), 401
        elif user_id == 'Invalid':
            return jsonify({'message': 'Your token is either expired or invalid.'}), 401
        else:
            try:
                int(friend_id)
            except (ValueError, TypeError) as e:
                # An error occurred, therefore return a string message containing the error
                response = {'message': str(e)}
                return make_response(jsonify(response)), 401

            friend = Friend.query. \
                filter(or_((and_(Friend.user1 == user_id, Friend.user2 == friend_id)),
                           (and_(Friend.user1 == friend_id, Friend.user2 == user_id))),
                       Friend.accepted).first()

            if not friend:
                response = {'message': 'You are not friends with that user'}
                return make_response(jsonify(response)), 404

            if friend.user1 == user_id or friend.user2 == user_id:
                friend.delete()

                response = {"message": "Friend deleted successfully"}
                return make_response(jsonify(response)), 200


class FRequest(MethodView):
    """
    Handles friend requests
    """
    @staticmethod
    def get():
        """
        Get friend requests
        """
        user_id = my_dec.check_token()

        if user_id == 'Missing':
            return jsonify({'message': 'You cannot access that page without a token.'}), 401
        elif user_id == 'Invalid':
            return jsonify({'message': 'Your token is either expired or invalid.'}), 401
        else:
            search_query = request.args.get("q")
            try:
                limit = int(request.args.get('limit', 10))
                page = int(request.args.get('page', 1))
            except (ValueError, TypeError):
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
                                    Friend.accepted == false())).first()
                    if output:
                        search_output.append(output.user2)

                if not search_output:
                    response = {'message': 'You have no request from that user'}
                    return make_response(jsonify(response)), 404

                for friend in search_output:
                    user = User.query.filter_by(id=friend).first()
                    obj = {
                        'id': user.id,
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
                filter(and_(Friend.user2 == user_id, Friend.accepted == false())).all()

            if not friend_list:
                response = {'message': 'You have no friend requests'}
                return make_response(jsonify(response)), 404

            for friend in friend_list:
                friend_ids.append(friend.user1)

            paginated_users = User.query.filter(User.id.in_(friend_ids)). \
                order_by(User.username.asc()).paginate(page, limit)

            for user in paginated_users.items:
                obj = {
                    'id': user.id,
                    'username': user.username,
                    'email': user.email
                }
                friends.append(obj)

            next_page = 'None'
            previous_page = 'None'

            if paginated_users.has_next:
                next_page = '/friends/requests' + '?page=' + str(page + 1) + \
                            '&limit=' + str(limit)
            if paginated_users.has_prev:
                previous_page = '/friends/requests' + '?page=' + str(page - 1) + \
                                '&limit=' + str(limit)

            response = {
                'previous_page': previous_page,
                'next_page': next_page,
                'friend_requests': friends
            }

            return make_response(jsonify(response)), 200


friend_ops = FriendOps.as_view('friend_ops')  # pylint: disable=invalid-name
friend_man = FriendMan.as_view('friend_man')  # pylint: disable=invalid-name
request_op = FRequest.as_view('request_op')  # pylint: disable=invalid-name

# Define rules
friend_blueprint.add_url_rule('/friends',
                              view_func=friend_ops, methods=['POST', 'GET'])
friend_blueprint.add_url_rule('/friends/<friend_id>',
                              view_func=friend_man, methods=['PUT', 'DELETE'])
friend_blueprint.add_url_rule('/friends/requests',
                              view_func=request_op, methods=['GET'])
