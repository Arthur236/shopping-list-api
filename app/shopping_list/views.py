"""
Views for the admin blueprint
"""
from . import shopping_list_blueprint

import re
from flask.views import MethodView
from flask import request, jsonify, make_response
from sqlalchemy import func
from ..models import ShoppingList
from ..decorators import MyDecorator
md = MyDecorator()


class SListOps(MethodView):
    """
    Handles shopping list creation and retrieval
    """
    def post(self):
        """
        Creates shopping lists
        """
        user_id = md.check_token()

        if user_id == 'Missing':
            return jsonify({'message': 'Token is missing!'}), 401
        elif user_id == 'Invalid':
            return jsonify({'message': 'Token is invalid!'}), 401
        else:
            name = str(request.data.get('name', ''))
            description = str(request.data.get('description', ''))

            if name:
                if not re.match("^[a-zA-Z0-9 _]*$", name):
                    response = {
                        'message': 'The list name cannot contain special characters. '
                                   'Only underscores'
                    }
                    return make_response(jsonify(response)), 400

                s_list = ShoppingList.query. \
                    filter(func.lower(ShoppingList.name) == name.lower(),
                           ShoppingList.user_id == user_id).first()

                if not s_list:
                    # There is no list so we'll try to create it
                    shopping_list = ShoppingList(user_id=user_id,
                                                 name=name, description=description)
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

                response = {'message': 'That shopping list already exists.'}
                return make_response(jsonify(response)), 401

            response = {'message': 'Shopping list name not provided.'}
            return make_response(jsonify(response)), 400

    def get(self):
        """
        Retrieves shopping lists
        """
        user_id = md.check_token()

        if user_id == 'Missing':
            return jsonify({'message': 'Token is missing!'}), 401
        elif user_id == 'Invalid':
            return jsonify({'message': 'Token is invalid!'}), 401
        else:
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
                shopping_lists = ShoppingList.query. \
                    filter(ShoppingList.name.ilike('%' + search_query + '%')). \
                    filter_by(user_id=user_id).all()
                output = []

                if not shopping_lists:
                    response = {'message': 'You do not have shopping lists matching that criteria'}
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

            paginated_lists = ShoppingList.query.filter_by(user_id=user_id). \
                order_by(ShoppingList.name.asc()).paginate(page, limit)
            results = []

            if not paginated_lists.items:
                response = {'message': 'You have no shopping lists'}
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


class SListMan(MethodView):
    """
    Handles shopping list manipulation operations
    """
    def get(self, list_id):
        """
        Retrieves a specific shopping list
        """
        user_id = md.check_token()

        if user_id == 'Missing':
            return jsonify({'message': 'Token is missing!'}), 401
        elif user_id == 'Invalid':
            return jsonify({'message': 'Token is invalid!'}), 401
        else:
            try:
                int(list_id)
            except ValueError:
                # An error occurred, therefore return a string message containing the error
                response = {'message': 'The parameter provided should be an integer'}
                return make_response(jsonify(response)), 401

            # retrieve a shopping list using it's id
            shopping_list = ShoppingList.query.filter_by(id=list_id, user_id=user_id).first()

            if not shopping_list:
                response = {"message": "That shopping list is not yours or does not exist"}
                return make_response(jsonify(response)), 404

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

    def put(self, list_id):
        """
        Updates a specific shopping list
        """
        user_id = md.check_token()

        if user_id == 'Missing':
            return jsonify({'message': 'Token is missing!'}), 401
        elif user_id == 'Invalid':
            return jsonify({'message': 'Token is invalid!'}), 401
        else:
            try:
                int(list_id)
            except ValueError:
                # An error occurred, therefore return a string message containing the error
                response = {'message': 'The parameter provided should be an integer'}
                return make_response(jsonify(response)), 401

            # retrieve a shopping list using it's id
            shopping_list = ShoppingList.query.filter_by(id=list_id, user_id=user_id).first()

            if not shopping_list:
                response = {"message": "That shopping list is not yours or does not exist"}
                return make_response(jsonify(response)), 404

            name = str(request.data.get('name', '')) if str(request.data.get('name', '')) \
                else shopping_list.name
            description = str(request.data.get('description', '')) if \
                str(request.data.get('description', '')) else shopping_list.description

            if name:
                if not re.match("^[a-zA-Z0-9 _]*$", name):
                    response = {
                        'message': 'The list name cannot contain special characters. '
                                   'Only underscores'
                    }
                    return make_response(jsonify(response)), 400

                s_list = ShoppingList.query.filter_by(user_id=user_id).all()

                for sl in s_list:
                    # Check if name exists
                    if str(list_id) != str(sl.id) and name.lower() == sl.name.lower():
                        response = {"message": "Shopping list already exists"}
                        return make_response(jsonify(response)), 401

                # Check if user is owner
                if shopping_list.user_id == user_id:
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

    def delete(self, list_id):
        """
        Deletes a specific shopping list
        """
        user_id = md.check_token()

        if user_id == 'Missing':
            return jsonify({'message': 'Token is missing!'}), 401
        elif user_id == 'Invalid':
            return jsonify({'message': 'Token is invalid!'}), 401
        else:
            try:
                int(list_id)
            except ValueError:
                # An error occurred, therefore return a string message containing the error
                response = {'message': 'The parameter provided should be an integer'}
                return make_response(jsonify(response)), 401

            # retrieve a shopping list using it's id
            shopping_list = ShoppingList.query.filter_by(id=list_id, user_id=user_id).first()

            if not shopping_list:
                response = {
                    "message": "That shopping list is not yours or does not exist"
                }
                return make_response(jsonify(response)), 404

            if shopping_list.user_id == user_id:
                shopping_list.delete()
                response = {
                    "message": "Shopping list {} deleted successfully".format(shopping_list.id)
                }
                return make_response(jsonify(response)), 200


s_list_ops = SListOps.as_view('s_list_ops')
s_list_man = SListMan.as_view('s_list_man')


# Define rules
shopping_list_blueprint.add_url_rule('/shopping_lists',
                                     view_func=s_list_ops, methods=['POST', 'GET'])
shopping_list_blueprint.add_url_rule('/shopping_lists/<list_id>',
                                     view_func=s_list_man, methods=['GET', 'PUT', 'DELETE'])
