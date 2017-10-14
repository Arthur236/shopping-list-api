"""
Test cases for shopping list items
"""
import unittest
import json
from app import create_app, db


class ShoppingListTestCase(unittest.TestCase):
    """
    This class represents the shopping list item test case
    """
    def login_user(self, user):
        """
        Helper function to login user
        """
        login_res = self.client().post('/v1/auth/login', data=user)
        access_token = json.loads(login_res.data.decode())['access-token']

        return access_token

    def setUp(self):
        """
        Define test variables and initialize app
        """
        self.app = create_app(config_name="testing")
        self.client = self.app.test_client
        self.user1 = {
            'username': 'User1', 'email': 'user1@gmail.com', 'password': 'password'
        }
        self.user2 = {
            'username': 'User2', 'email': 'user2@gmail.com', 'password': 'password'
        }
        self.shopping_list = {'name': 'Groceries', 'description': 'Description'}
        self.shopping_list_item = \
            {'list_id': 1, 'name': 'Tomatoes', 'quantity': 20, 'unit_price': 5}
        self.shopping_list_item2 = \
            {'list_id': 1, 'name': 'Broccoli', 'quantity': 20, 'unit_price': 5}
        self.shopping_list_item_special = \
            {'list_id': 1, 'name': 'Tomatoes*-/', 'quantity': 20, 'unit_price': 5}

        # binds the app to the current context
        with self.app.app_context():
            # create all tables
            db.session.close()
            db.drop_all()
            db.create_all()

            self.client().post('/v1/auth/register', data=self.user1)
            self.client().post('/v1/auth/register', data=self.user2)

            user1_token = self.login_user(self.user1)
            self.client().post('/v1/shopping_lists', headers={'x-access-token': user1_token},
                               data=self.shopping_list)

            user2_token = self.login_user(self.user2)
            self.client().post('/v1/shopping_lists', headers={'x-access-token': user2_token},
                               data=self.shopping_list)

    def test_item_special_chars(self):
        """
        Try to create item with special characters
        """
        access_token = self.login_user(self.user1)

        res = self.client().post('/v1/shopping_lists/1/items',
                                 headers={'x-access-token': access_token},
                                 data=self.shopping_list_item_special)
        self.assertEqual(res.status_code, 400)

    def test_list_exists(self):
        """
        Test if shopping list exists
        """
        access_token = self.login_user(self.user1)

        res = self.client().post('/v1/shopping_lists/189/items',
                                 headers={'x-access-token': access_token},
                                 data=self.shopping_list_item_special)
        self.assertEqual(res.status_code, 404)

    def test_item_exists(self):
        """
        Try to create an item that already exists
        """
        access_token = self.login_user(self.user1)

        self.client().post('/v1/shopping_lists/1/items',
                           headers={'x-access-token': access_token},
                           data=self.shopping_list_item)

        res = self.client().post('/v1/shopping_lists/1/items',
                                 headers={'x-access-token': access_token},
                                 data=self.shopping_list_item)
        # Assert that the shopping list item is created
        self.assertEqual(res.status_code, 401)

    def test_item_create_params(self):
        """
        Test if all parameters are provided
        """
        access_token = self.login_user(self.user1)

        res = self.client().post('/v1/shopping_lists/1/items',
                                 headers={'x-access-token': access_token})
        self.assertEqual(res.status_code, 400)

    def test_item_creation(self):
        """
        Test API can create a shopping list item (POST request)
        """
        access_token = self.login_user(self.user1)

        # Create shopping list item
        res = self.client().post('/v1/shopping_lists/1/items',
                                 headers={'x-access-token': access_token},
                                 data=self.shopping_list_item)
        self.assertEqual(res.status_code, 201)

    def create_item(self):
        """
        Helper function to create item
        """
        access_token = self.login_user(self.user1)

        res = self.client().post('/v1/shopping_lists/1/items',
                                 headers={'x-access-token': access_token},
                                 data=self.shopping_list_item)
        return res

    def test_api_can_get_items(self):
        """
        Test API can get shopping list items
        """
        self.create_item()
        access_token = self.login_user(self.user1)

        # Get items
        result = self.client().get('/v1/shopping_lists/1/items',
                                   headers={'x-access-token': access_token})
        self.assertEqual(result.status_code, 200)

    def test_pagination_params_format(self):
        """
        Use the wrong limit and page data formats
        """
        access_token = self.login_user(self.user1)

        res = self.client().get('/v1/shopping_lists/1/items?page=one&limit=two',
                                headers={'x-access-token': access_token})
        self.assertEqual(res.status_code, 401)

    def test_search_non_existent_item(self):
        """
        Try to search for items not in list
        """
        access_token = self.login_user(self.user1)

        res = self.client().get('/v1/shopping_lists/1/items?q=vuyjb',
                                headers={'x-access-token': access_token})
        self.assertEqual(res.status_code, 404)

    def test_search_existent_item(self):
        """
        Try to search for items in list
        """
        self.create_item()
        access_token = self.login_user(self.user1)

        res = self.client().get('/v1/shopping_lists/1/items?q=tom',
                                headers={'x-access-token': access_token})
        self.assertEqual(res.status_code, 200)

    def test_get_paginated_items_when_none(self):
        """
        Try to get paginated items when there are no items
        """
        access_token = self.login_user(self.user1)

        res = self.client().get('/v1/shopping_lists/1/items?page=1&limit=2',
                                headers={'x-access-token': access_token})
        self.assertEqual(res.status_code, 404)

    def test_get_paginated_items(self):
        """
        Try to get paginated items
        """
        self.create_item()
        access_token = self.login_user(self.user1)

        res = self.client().get('/v1/shopping_lists/1/items?page=1&limit=2',
                                headers={'x-access-token': access_token})
        self.assertEqual(res.status_code, 200)

    def test_list_and_item_id_format(self):
        """
        Test whether list and item ids are both ints
        """
        access_token = self.login_user(self.user1)

        res = self.client().get('/v1/shopping_lists/hidw/items/guie',
                                headers={'x-access-token': access_token})
        self.assertEqual(res.status_code, 401)

    def test_api_can_get_item_by_id(self):
        """
        Test API can get a single shopping list item by using it's id
        """
        res = self.create_item()
        access_token = self.login_user(self.user1)
        results = json.loads(res.data.decode())

        result = self.client().get('/v1/shopping_lists/1/items/{}'.format(results['id']),
                                   headers={'x-access-token': access_token})
        # Assert that the shopping list item is actually returned given its ID
        self.assertEqual(result.status_code, 201)

    def test_get_non_existent_item_by_id(self):
        """
        Try to get non existent item by id
        """
        res = self.create_item()
        access_token = self.login_user(self.user1)
        results = json.loads(res.data.decode())

        result = self.client().get('/v1/shopping_lists/156/items/{}'.format(results['id']),
                                   headers={'x-access-token': access_token})
        # Assert that the shopping list item is actually returned given its ID
        self.assertEqual(result.status_code, 404)

    def test_item_can_be_edited(self):
        """
        Test API can edit an existing shopping list item. (PUT request)
        """
        self.create_item()
        access_token = self.login_user(self.user1)

        rv = self.client().put('/v1/shopping_lists/1/items/1',
                               headers={'x-access-token': access_token},
                               data={
                                   "name": "Oranges", "quantity": 2, "unit_price": 20
                               })
        self.assertEqual(rv.status_code, 201)

    def test_non_existent_item_edit(self):
        """
        Test if non existent item can be edited
        """
        access_token = self.login_user(self.user1)

        rv = self.client().put('/v1/shopping_lists/1/items/168',
                               headers={'x-access-token': access_token},
                               data={
                                   "name": "Oranges", "quantity": 2, "unit_price": 20
                               })
        self.assertEqual(rv.status_code, 404)

    def test_item_edit_special_chars(self):
        """
        Try to edit with special chars
        """
        self.create_item()
        access_token = self.login_user(self.user1)

        rv = self.client().put('/v1/shopping_lists/1/items/1',
                               headers={'x-access-token': access_token},
                               data=self.shopping_list_item_special)
        self.assertEqual(rv.status_code, 400)

    def test_edit_name_exists(self):
        """
        Try to use name of item that already exists
        """
        self.create_item()
        access_token = self.login_user(self.user1)

        self.client().post('/v1/shopping_lists/1/items',
                           headers={'x-access-token': access_token},
                           data=self.shopping_list_item2)

        rv = self.client().put('/v1/shopping_lists/1/items/2',
                               headers={'x-access-token': access_token},
                               data=self.shopping_list_item)
        self.assertEqual(rv.status_code, 401)

    def test_item_deletion(self):
        """
        Test API can delete an existing shopping list item. (DELETE request)
        """
        res = self.create_item()
        access_token = self.login_user(self.user1)

        # Get the shopping list in json
        results = json.loads(res.data.decode())

        # Delete the shopping list we just created
        res = self.client().delete('/v1/shopping_lists/1/items/{}'.format(results['id']),
                                   headers={'x-access-token': access_token})
        self.assertEqual(res.status_code, 200)

    def test_delete_non_existent_item(self):
        """
        Try to delete item that doesnt exist
        """
        self.create_item()
        access_token = self.login_user(self.user1)

        res = self.client().delete('/v1/shopping_lists/1/items/563',
                                   headers={'x-access-token': access_token})
        self.assertEqual(res.status_code, 404)

    def tearDown(self):
        """
        Delete all initialized variables
        """
        with self.app.app_context():
            # Drop all tables
            db.session.remove()
            db.drop_all()

    # Make the tests conveniently executable
    if __name__ == "__main__":
        unittest.main()
