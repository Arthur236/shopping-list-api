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

    def setup_users_and_lists(self):
        """
        Register and log in users
        """
        # create users by making POST requests
        res = self.client().post('/v1/auth/register', data=self.user1)
        res = self.client().post('/v1/auth/register', data=self.user2)

        # Log in the first user
        login_res = self.client().post('/v1/auth/login', data=self.user1)
        access_token = json.loads(login_res.data.decode())['access-token']

        rv = self.client().post('/v1/shopping_lists', headers={'x-access-token': access_token},
                                data=self.shopping_list)

        return access_token

    def test_item_special_chars(self):
        """
        Try to create item with special characters
        """
        access_token = self.setup_users_and_lists()

        res = self.client().post('/v1/shopping_lists/1/items',
                                 headers={'x-access-token': access_token},
                                 data=self.shopping_list_item_special)
        self.assertEqual(res.status_code, 400)

    def test_item_exists(self):
        """
        Try to create an item that already exists
        """
        access_token = self.setup_users_and_lists()

        self.client().post('/v1/shopping_lists/1/items', 
                           headers={'x-access-token': access_token},
                           data=self.shopping_list_item)

        res = self.client().post('/v1/shopping_lists/1/items',
                                 headers={'x-access-token': access_token},
                                 data=self.shopping_list_item)
        # Assert that the shopping list item is created
        self.assertEqual(res.status_code, 401)

    def test_item_creation(self):
        """
        Test API can create a shopping list item (POST request)
        """
        access_token = self.setup_users_and_lists()

        # Create shopping list item
        res = self.client().post('/v1/shopping_lists/1/items',
                                 headers={'x-access-token': access_token},
                                 data=self.shopping_list_item)
        self.assertEqual(res.status_code, 201)

    def create_item(self):
        """
        Helper function to create item
        """
        access_token = self.setup_users_and_lists()

        res = self.client().post('/v1/shopping_lists/1/items',
                                 headers={'x-access-token': access_token},
                                 data=self.shopping_list_item)
        return res

    def test_api_can_get_items(self):
        """
        Test API can get shopping list items
        """
        access_token = self.setup_users_and_lists()
        self.create_item()

        # Get items
        result = self.client().get('/v1/shopping_lists/1/items',
                                   headers={'x-access-token': access_token})
        self.assertEqual(result.status_code, 200)

    def test_pagination_params_format(self):
        """
        Use the wrong limit and page data formats
        """
        access_token = self.setup_users_and_lists()
        res = self.client().get('/v1/shopping_lists/1/items?page=one&limit=two',
                                headers={'x-access-token': access_token})
        self.assertEqual(res.status_code, 401)

    def test_search_non_existent_item(self):
        """
        Try to search for items in list
        """
        access_token = self.setup_users_and_lists()
        res = self.client().get('/v1/shopping_lists/1/items?q=vuyjb',
                                headers={'x-access-token': access_token})
        self.assertEqual(res.status_code, 404)

    def test_get_paginated_items(self):
        """
        Try to get paginated items
        """
        access_token = self.setup_users_and_lists()
        self.create_item()

        res = self.client().get('/v1/shopping_lists/1/items?page=1&limit=2',
                                headers={'x-access-token': access_token})
        self.assertEqual(res.status_code, 200)

    def test_api_can_get_item_by_id(self):
        """
        Test API can get a single shopping list item by using it's id
        """
        access_token = self.setup_users_and_lists()
        res = self.create_item()

        # Get the response data in json format
        results = json.loads(res.data.decode())

        result = self.client().get('/v1/shopping_lists/1/items/{}'.format(results['id']),
                                   headers={'x-access-token': access_token})
        # Assert that the shopping list item is actually returned given its ID
        self.assertEqual(result.status_code, 201)

    def test_item_can_be_edited(self):
        """
        Test API can edit an existing shopping list item. (PUT request)
        """
        access_token = self.setup_users_and_lists()
        self.create_item()

        rv = self.client().put('/v1/shopping_lists/1/items/1',
                               headers={'x-access-token': access_token},
                               data={
                                   "name": "Oranges", "quantity": 2, "unit_price": 20
                               })
        self.assertEqual(rv.status_code, 201)

    def test_item_special_chars(self):
        """
        Try to edit with special chars
        """
        access_token = self.setup_users_and_lists()
        self.create_item()

        rv = self.client().put('/v1/shopping_lists/1/items/1',
                               headers={'x-access-token': access_token},
                               data=self.shopping_list_item_special)
        self.assertEqual(rv.status_code, 400)

    def test_edit_name_exists(self):
        """
        Try to use name of item that already exists
        """
        access_token = self.setup_users_and_lists()
        self.create_item()

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
        access_token = self.setup_users_and_lists()
        res = self.create_item()

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
        access_token = self.setup_users_and_lists()
        self.create_item()

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
