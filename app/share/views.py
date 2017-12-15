"""
Views for the share blueprint
"""
from flask.views import MethodView
from flask import request, jsonify, make_response
from sqlalchemy import and_, or_
from . import share_blueprint
from ..models import Friend, SharedList, ShoppingList, ShoppingListItem
from ..decorators import MyDecorator
my_dec = MyDecorator()


class ShareOps(MethodView):
    """
    Handles sharing and retrieving shared lists
    """
    @staticmethod
    def post():
        """
        POST - Shares a list
        """
        user_id = my_dec.check_token()

        if user_id == 'Missing':
            return jsonify({'message': 'You cannot access that page without a token.'}), 401
        elif user_id == 'Invalid':
            return jsonify({'message': 'Your token is either expired or invalid.'}), 401
        else:
            try:
                list_id = int(request.data.get('list_id', ''))
                friend_id = int(request.data.get('friend_id', ''))
            except (ValueError, TypeError):
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

    @staticmethod
    def get():
        """
        GET - Retrieves all shared lists
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

            total_lists = ShoppingList.query.filter(ShoppingList.id.in_(shared_lists_ids)).count()
            paginated_lists = ShoppingList.query.filter(ShoppingList.id.in_(shared_lists_ids)).\
                order_by(ShoppingList.name.asc()).paginate(page, limit)

            for sha_list in paginated_lists.items:
                obj = {
                    'id': sha_list.id,
                    'name': sha_list.name,
                    'description': sha_list.description,
                    'date_created': sha_list.date_created,
                    'date_modified': sha_list.date_modified

                }
                shared_lists.append(obj)

            next_page = 'None'
            previous_page = 'None'

            if paginated_lists.has_next:
                next_page = '/shopping_lists/share' + '?page=' + str(page + 1) + \
                            '&limit=' + str(limit)
            if paginated_lists.has_prev:
                previous_page = '/shopping_lists/share' + '?page=' + str(page - 1) + \
                                '&limit=' + str(limit)

            response = {
                'total': total_lists,
                'previous_page': previous_page,
                'next_page': next_page,
                'shared_lists': shared_lists
            }

            return make_response(jsonify(response)), 200


class ShareMan(MethodView):
    """
    Handles shared list operations
    """
    @staticmethod
    def delete(list_id):
        """
        Stops sharing a list
        """
        user_id = my_dec.check_token()

        if user_id == 'Missing':
            return jsonify({'message': 'You cannot access that page without a token.'}), 401
        elif user_id == 'Invalid':
            return jsonify({'message': 'Your token is either expired or invalid.'}), 401
        else:
            try:
                int(list_id)
                friend_id = int(request.data.get('friend_id', ''))
            except (ValueError, TypeError):
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
                               and_(SharedList.user1 == friend_id, SharedList.user2 == user_id)))\
                    .filter_by(list_id=list_id).first()

                if shared_list:
                    shared_list.delete()

                    response = {'message': 'List sharing stopped successfully'}
                    return make_response(jsonify(response)), 200

                if friend_id == user_id:
                    shared_list = SharedList.query.filter(SharedList.user1 == user_id).filter_by(list_id=list_id).all()

                    if shared_list:
                        for s_list in shared_list:
                            s_list.delete()

                        response = {'message': 'List sharing stopped successfully'}
                        return make_response(jsonify(response)), 200

                response = {'message': 'That list has not been shared'}
                return make_response(jsonify(response)), 404


class ShareItems(MethodView):
    """
    Shows items in a shared list
    """
    @staticmethod
    def get(list_id):
        """
        Retrieves all items in shared shopping list
        """
        user_id = my_dec.check_token()

        if user_id == 'Missing':
            return jsonify({'message': 'You cannot access that page without a token.'}), 401
        elif user_id == 'Invalid':
            return jsonify({'message': 'Your token is either expired or invalid.'}), 401
        else:
            try:
                int(list_id)
            except (ValueError, TypeError):
                # An error occurred, therefore return a string message containing the error
                response = {'message': 'Please ensure the parameter provided is an integer'}
                return make_response(jsonify(response)), 401

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
            except (ValueError, TypeError):
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

            total_items = ShoppingListItem.query.filter_by(list_id=list_id).count()
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

            next_page = 'None'
            previous_page = 'None'

            if paginated_items.has_next:
                next_page = '/shopping_lists/share/<list_id>/items' + '?page=' + str(page + 1) + \
                            '&limit=' + str(limit)
            if paginated_items.has_prev:
                previous_page = '/shopping_lists/share/<list_id>/items' + '?page=' + str(page - 1) + \
                                '&limit=' + str(limit)

            response = {
                'total': total_items,
                'previous_page': previous_page,
                'next_page': next_page,
                'shared_list_items': results
            }

            return make_response(jsonify(response)), 200


share_ops = ShareOps.as_view('share_ops')  # pylint: disable=invalid-name
share_man = ShareMan.as_view('share_man')  # pylint: disable=invalid-name
share_items_ops = ShareItems.as_view('share_items_ops')  # pylint: disable=invalid-name

# Define rules
share_blueprint.add_url_rule('/shopping_lists/share',
                             view_func=share_ops, methods=['POST', 'GET'])
share_blueprint.add_url_rule('/shopping_lists/share/<list_id>',
                             view_func=share_man, methods=['DELETE'])
share_blueprint.add_url_rule('/shopping_lists/share/<list_id>/items',
                             view_func=share_items_ops, methods=['GET'])
