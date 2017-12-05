"""
Views for the item blueprint
"""
import re
from flask.views import MethodView
from flask import request, jsonify, make_response
from sqlalchemy import func
from . import item_blueprint
from ..models import ShoppingList, ShoppingListItem
from ..decorators import MyDecorator
my_dec = MyDecorator()


class ItemOps(MethodView):
    """
    Handles shopping list item creation and retrieval
    """
    @staticmethod
    def post(list_id):
        """
        POST - Creates a shopping list item
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
                response = {'message': 'The parameter provided should be an integer'}
                return make_response(jsonify(response)), 401

            shopping_list = ShoppingList.query.filter_by(id=list_id, user_id=user_id).first()

            if not shopping_list:
                response = {"message": "That shopping list in not yours or does not exist"}
                return make_response(jsonify(response)), 404

            try:
                name = str(request.data.get('name', ''))
                quantity = float(request.data.get('quantity', 0.0))
                unit_price = float(request.data.get('unit_price', 0.0))
            except (ValueError, TypeError):
                # An error occurred, therefore return a string message containing the error
                response = {'message': 'The parameters provided should be strings or floats'}
                return make_response(jsonify(response)), 401

            if name and quantity and unit_price:
                if not re.match("^[a-zA-Z0-9 _]*$", name):
                    response = {
                        'message': 'The item name cannot contain special characters. '
                                   'Only underscores'
                    }
                    return make_response(jsonify(response)), 400

                s_list_item = ShoppingListItem.query.\
                    filter(func.lower(ShoppingListItem.name) == name.lower(),
                           ShoppingListItem.list_id == list_id).first()

                if not s_list_item:
                    # There is no list item so we'll try to create it
                    shopping_list_item = ShoppingListItem(list_id=list_id,
                                                          name=name, quantity=quantity,
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

                response = {'message': 'That item already exists.'}
                return make_response(jsonify(response)), 401

            response = {'message': 'Please provide all required the details.'}
            return make_response(jsonify(response)), 400

    @staticmethod
    def get(list_id):
        """
        GET - Retrieves all items belonging to a specific shopping list
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
                return make_response(jsonify(response)), 200

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
                next_page = '/shopping_lists/<list_id>/items' + '?page=' + str(page + 1) + \
                            '&limit=' + str(limit)
            if paginated_items.has_prev:
                previous_page = '/shopping_lists/<list_id>/items' + '?page=' + str(page - 1) + \
                                '&limit=' + str(limit)

            response = {
                'previous_page': previous_page,
                'next_page': next_page,
                'shopping_list_items': results
            }

            return make_response(jsonify(response)), 200


class ItemMan(MethodView):
    """
    Handles shopping list item manipulation operations
    """
    @staticmethod
    def get(list_id, item_id):
        """
        Retrieves a specific item
        """
        user_id = my_dec.check_token()

        if user_id == 'Missing':
            return jsonify({'message': 'You cannot access that page without a token.'}), 401
        elif user_id == 'Invalid':
            return jsonify({'message': 'Your token is either expired or invalid.'}), 401
        else:
            try:
                int(list_id)
                int(item_id)
            except (ValueError, TypeError):
                # An error occurred, therefore return a string message containing the error
                response = {'message': 'The parameters provided should be integers'}
                return make_response(jsonify(response)), 401

            # Retrieve a shopping list item using it's id
            shopping_list = ShoppingList.query.filter_by(id=list_id, user_id=user_id).first()
            shopping_list_item = \
                ShoppingListItem.query.filter_by(id=item_id, list_id=list_id).first()

            if not shopping_list or not shopping_list_item:
                response = {"message": "That shopping list or item is not yours or does not exist"}
                return make_response(jsonify(response)), 404

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
                response.status_code = 200
                return response

    @staticmethod
    def put(list_id, item_id):
        """
        Updates a specific item
        """
        user_id = my_dec.check_token()

        if user_id == 'Missing':
            return jsonify({'message': 'You cannot access that page without a token.'}), 401
        elif user_id == 'Invalid':
            return jsonify({'message': 'Your token is either expired or invalid.'}), 401
        else:
            try:
                int(list_id)
                int(item_id)
            except (ValueError, TypeError):
                # An error occurred, therefore return a string message containing the error
                response = {'message': 'The parameters provided should be integers'}
                return make_response(jsonify(response)), 401

            # retrieve a shopping list item using it's id
            shopping_list = ShoppingList.query.filter_by(id=list_id, user_id=user_id).first()
            shopping_list_item = \
                ShoppingListItem.query.filter_by(id=item_id, list_id=list_id).first()

            if not shopping_list or not shopping_list_item:
                response = {"message": "That shopping list or item is not yours or does not exist"}
                return make_response(jsonify(response)), 404

            name = str(request.data.get('name', '')) if str(request.data.get('name', '')) \
                else shopping_list_item.name
            quantity = str(request.data.get('quantity', '')) if \
                str(request.data.get('quantity', '')) else shopping_list_item.quantity
            unit_price = str(request.data.get('unit_price', '')) if \
                str(request.data.get('unit_price', '')) else shopping_list_item.unit_price

            if name and quantity and unit_price:
                if not re.match("^[a-zA-Z0-9 _]*$", name):
                    response = {
                        'message': 'The item name cannot contain special characters. '
                                   'Only underscores'
                    }
                    return make_response(jsonify(response)), 400

                s_list_item = ShoppingListItem.query.filter_by(list_id=list_id).all()

                for l_item in s_list_item:
                    # Check if item name exists
                    if str(item_id) != str(l_item.id) and name.lower() == l_item.name.lower():
                        response = {"message": "Item already exists"}
                        return make_response(jsonify(response)), 401

                # Check if item belongs to its owner's list
                if shopping_list.user_id == user_id:

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
                    response.status_code = 200
                    return response

    @staticmethod
    def delete(list_id, item_id):
        """
        Deletes a specific item
        """
        user_id = my_dec.check_token()

        if user_id == 'Missing':
            return jsonify({'message': 'You cannot access that page without a token.'}), 401
        elif user_id == 'Invalid':
            return jsonify({'message': 'Your token is either expired or invalid.'}), 401
        else:
            try:
                list_id = int(list_id)
                item_id = int(item_id)
            except (ValueError, TypeError):
                # An error occurred, therefore return a string message containing the error
                response = {'message': 'The parameters provided should be integers'}
                return make_response(jsonify(response)), 401

            # retrieve a shopping list item using it's id
            shopping_list = ShoppingList.query.filter_by(id=list_id, user_id=user_id).first()
            shopping_list_item = \
                ShoppingListItem.query.filter_by(id=item_id, list_id=list_id).first()

            if not shopping_list or not shopping_list_item:
                response = {"message": "That shopping list or item is not yours or does not exist"}
                return make_response(jsonify(response)), 404

            if shopping_list.user_id == user_id:
                shopping_list_item.delete()
                response = {"message": "Item {} deleted successfully".format(shopping_list_item.id)}
                return make_response(jsonify(response)), 200


item_ops = ItemOps.as_view('item_ops')  # pylint: disable=invalid-name
item_man = ItemMan.as_view('item_man')  # pylint: disable=invalid-name


# Define rules
item_blueprint.add_url_rule('/shopping_lists/<list_id>/items',
                            view_func=item_ops, methods=['POST', 'GET'])
item_blueprint.add_url_rule('/shopping_lists/<list_id>/items/<item_id>',
                            view_func=item_man, methods=['GET', 'PUT', 'DELETE'])
