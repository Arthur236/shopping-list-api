"""
Views for the admin blueprint
"""
from flask.views import MethodView
from flask import request, jsonify, make_response
from app import db
from . import admin_blueprint
from ..models import User
from ..decorators import MyDecorator
my_dec = MyDecorator()


class GetAllUsers(MethodView):
    """
    Handles getting all users
    """
    @staticmethod
    def get():
        """
        Retrieves all registered users
        """
        user_id = my_dec.check_token()

        if user_id == 'Missing':
            return jsonify({'message': 'You cannot access that page without a token.'}), 401
        elif user_id == 'Invalid':
            return jsonify({'message': 'Your token is either expired or invalid.'}), 401

        user = User.query.filter_by(id=user_id).first()

        if not user.admin:
            response = {'message': 'Cannot perform that operation without admin rights'}
            return make_response(jsonify(response)), 403

        search_query = request.args.get("q")
        try:
            limit = int(request.args.get('limit', 10))
            page = int(request.args.get('page', 1))
        except (ValueError, TypeError):
            # An error occurred, therefore return a string message containing the error
            response = {'message': 'The parameters provided should be integers'}
            return make_response(jsonify(response)), 401

        if search_query:
            # if parameter q is specified
            result = User.query.\
                filter(User.username.ilike('%' + search_query + '%')).\
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
                        'email': user.email,
                        'date_created': user.date_created,
                        'date_modified': user.date_modified
                    }
                    output.append(obj)

            response = jsonify(output)
            response.status_code = 200
            return response

        users = []
        total_users = User.query.filter(User.id != user_id).\
            filter_by(admin=False).count()
        paginated_users = User.query.filter(User.id != user_id).\
            filter_by(admin=False).\
            order_by(User.username.asc()).paginate(page, limit)

        if not paginated_users.items:
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
                    'date_created': user.date_created,
                    'date_modified': user.date_modified
                }
                users.append(obj)

        next_page = 'None'
        previous_page = 'None'

        if paginated_users.has_next:
            next_page = '/admin/users' + '?page=' + str(page + 1) + \
                        '&limit=' + str(limit)
        if paginated_users.has_prev:
            previous_page = '/admin/users' + '?page=' + str(page - 1) + \
                            '&limit=' + str(limit)

        response = {
            'total': total_users,
            'previous_page': previous_page,
            'next_page': next_page,
            'users': users
        }

        return make_response(jsonify(response)), 200


class GetUser(MethodView):
    """
    Handles getting a specific user
    """
    @staticmethod
    def get(u_id):
        """
        Retrieves a specific user
        """
        user_id = my_dec.check_token()

        if user_id == 'Missing':
            return jsonify({'message': 'You cannot access that page without a token.'}), 401
        elif user_id == 'Invalid':
            return jsonify({'message': 'Your token is either expired or invalid.'}), 401

        try:
            int(u_id)
        except (ValueError, TypeError):
            # An error occurred, therefore return a string message containing the error
            response = {'message': 'The parameter provided should be an integer'}
            return make_response(jsonify(response)), 401

        user = User.query.filter_by(id=user_id).first()

        if not user.admin:
            response = {'message': 'Cannot perform that operation without admin rights'}
            return make_response(jsonify(response)), 403

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
    def delete(u_id):
        """
        Deletes a specific user
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

            user = User.query.filter_by(id=user_id).first()

            if not user.admin:
                response = {'message': 'Cannot perform that operation without admin rights'}
                return make_response(jsonify(response)), 403

            user = User.query.filter_by(id=u_id).first()

            if not user:
                response = {'message': 'That user does not exist'}
                return make_response(jsonify(response)), 404

            if user.id == user_id:
                response = {'message': 'You cannot delete yourself'}
                return make_response(jsonify(response)), 403

            db.session.delete(user)
            db.session.commit()

            response = {'message': 'User deleted successfully'}
            return make_response(jsonify(response)), 200


get_users_view = GetAllUsers.as_view('get_users_view')  # pylint: disable=invalid-name
get_user_view = GetUser.as_view('get_user_view')  # pylint: disable=invalid-name

# Define rules
admin_blueprint.add_url_rule('/admin/users', view_func=get_users_view, methods=['GET'])
admin_blueprint.add_url_rule('/admin/users/<u_id>',
                             view_func=get_user_view, methods=['GET', 'DELETE'])
