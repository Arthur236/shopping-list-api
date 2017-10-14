"""
Test cases for shopping lists
"""
import unittest
import json
from app import create_app, db


class ShoppingListTestCase(unittest.TestCase):
    """
    This class represents the shopping list test case
    """

    def setUp(self):
        """
        Define test variables and initialize app
        """
        self.app = create_app(config_name="testing")
        self.client = self.app.test_client
        self.user1 = {
            'username': 'User1',
            'email': 'user1@gmail.com',
            'password': 'password'
        }
        self.user2 = {
            'username': 'User2',
            'email': 'user2@gmail.com',
            'password': 'password'
        }
        self.shopping_list = {'name': 'Groceries', 'description': 'Description'}
        self.shopping_list_special = {'name': 'Groceries*-+', 'description': 'Description'}

        # Bind the app to the current context
        with self.app.app_context():
            # create all tables
            db.session.close()
            db.drop_all()
            db.create_all()

    def setup_users(self):
        """
        Register and log in users
        """
        # create users by making POST requests
        self.client().post('/v1/auth/register', data=self.user1)
        self.client().post('/v1/auth/register', data=self.user2)

        # Log in the first user
        login_res = self.client().post('/v1/auth/login', data=self.user1)
        access_token = json.loads(login_res.data.decode())['access-token']

        return access_token

    def test_token_correct(self):
        """
        Test if token is correct format
        """
        res = self.client().post(
            '/v1/shopping_lists',
            headers={'x-access-token': 'some_incorrect_token'},
            data=self.shopping_list)
        self.assertEqual(res.status_code, 401)

    def test_token_present(self):
        """
        Test if token is present
        """
        res = self.client().post(
            '/v1/shopping_lists',
            data=self.shopping_list)
        self.assertEqual(res.status_code, 401)

    def test_list_name_special_chars(self):
        """
        Test if list name has special chars
        """
        # Register a test user, then log them in
        access_token = self.setup_users()

        # Create shopping list with special characters
        res = self.client().post(
            '/v1/shopping_lists',
            headers={'x-access-token': access_token},
            data=self.shopping_list_special)
        self.assertEqual(res.status_code, 400)

    def test_empty_list_name_param(self):
        """
        Test if list name param is present
        """
        # Register a test user, then log them in
        access_token = self.setup_users()

        res = self.client().post(
            '/v1/shopping_lists',
            headers={'x-access-token': access_token})
        self.assertEqual(res.status_code, 400)

    def test_shopping_list_creation(self):
        """
        Test API can create a shopping list (POST request)
        """
        # Register a test user, then log them in
        access_token = self.setup_users()

        # Create a shopping list by making a POST request
        res = self.client().post(
            '/v1/shopping_lists',
            headers={'x-access-token': access_token},
            data=self.shopping_list)
        self.assertEqual(res.status_code, 201)
        self.assertIn('Groceries', str(res.data))

    def create_shopping_list(self):
        """
        Helper function to create shopping list
        """
        access_token = self.setup_users()

        results = self.client().post('/v1/shopping_lists', 
                                     headers={'x-access-token': access_token},
                                     data=self.shopping_list)

        return results

    def test_get_all_shopping_lists(self):
        """
        Test API can get a shopping list (GET request)
        """
        access_token = self.setup_users()

        self.create_shopping_list()

        # Get all the shopping lists that belong to the test user by making a GET request
        res = self.client().get(
            '/v1/shopping_lists',
            headers={'x-access-token': access_token},
        )
        self.assertEqual(res.status_code, 200)

    def test_wrong_get_pagination_limits(self):
        """
        Use the wrong limit and page data formats
        """
        access_token = self.setup_users()

        res = self.client().get('/v1/shopping_lists?page=one&limit=two',
                                headers={'x-access-token': access_token})
        self.assertEqual(res.status_code, 401)

    def test_get_non_existent_list(self):
        """
        Try search non existent list
        """
        access_token = self.setup_users()

        res = self.client().get(
            '/v1/shopping_lists?q=hdiue',
            headers={'x-access-token': access_token}
        )
        self.assertEqual(res.status_code, 404)

    def test_existent_list(self):
        """
        Try search existent list
        """
        access_token = self.setup_users()

        self.create_shopping_list()

        res = self.client().get(
            '/v1/shopping_lists?q=gro',
            headers={'x-access-token': access_token}
        )
        self.assertEqual(res.status_code, 200)

    def test_get_paginated_lists(self):
        """
        Try get paginated lists
        """
        access_token = self.setup_users()

        self.create_shopping_list()

        res = self.client().get(
            '/v1/shopping_lists?page=1&limit=2',
            headers={'x-access-token': access_token}
        )
        self.assertEqual(res.status_code, 200)

    def test_get_paginated_lists_when_none(self):
        """
        Try get paginated lists when user has no lists
        """
        access_token = self.setup_users()

        res = self.client().get(
            '/v1/shopping_lists?page=1&limit=2',
            headers={'x-access-token': access_token}
        )
        self.assertEqual(res.status_code, 404)

    def test_get_shopping_list_by_id(self):
        """
        Test API can get a single shopping list by using it's id
        """
        access_token = self.setup_users()

        rv = self.create_shopping_list()
        results = json.loads(rv.data.decode())

        result = self.client().get(
            '/v1/shopping_lists/{}'.format(results['id']),
            headers={'x-access-token': access_token})
        # Assert that the shopping list is actually returned given its ID
        self.assertEqual(result.status_code, 200)

    def test_get_non_existent_list_by_id(self):
        """
        Test API can get a shopping list that doesnt exist by using it's id
        """
        access_token = self.setup_users()

        result = self.client().get(
            '/v1/shopping_lists/65',
            headers={'x-access-token': access_token})
        # Assert that the shopping list is actually returned given its ID
        self.assertEqual(result.status_code, 404)

    def test_update_non_existent_list(self):
        """
        Test non existent lists
        """
        access_token = self.setup_users()

        result = self.client().put(
            '/v1/shopping_lists/689',
            headers={'x-access-token': access_token})
        self.assertEqual(result.status_code, 404)

    def test_shopping_list_edit(self):
        """
        Test API can edit an existing shopping list. (PUT request)
        """
        access_token = self.setup_users()

        rv = self.create_shopping_list()
        results = json.loads(rv.data.decode())

        # Then, we edit the created shopping list by making a PUT request
        rv = self.client().put(
            '/v1/shopping_lists/{}'.format(results['id']),
            headers={'x-access-token': access_token},
            data={
                "name": "Electronics"
            })
        self.assertEqual(rv.status_code, 200)

    def test_edit_with_special_chars(self):
        """
        Try to edit a list with special characters
        """
        access_token = self.setup_users()

        rv = self.create_shopping_list()

        # Get the json with the shopping list
        results = json.loads(rv.data.decode())

        rv = self.client().put(
            '/v1/shopping_lists/{}'.format(results['id']),
            headers={'x-access-token': access_token},
            data={
                "name": "Electronics/*-"
            })
        self.assertEqual(rv.status_code, 400)

    def test_edit_name_that_exists(self):
        """
        Try to give it a name of a list that already exists
        """
        access_token = self.setup_users()

        self.create_shopping_list()

        rv = self.client().post('/v1/shopping_lists', 
                                headers={'x-access-token': access_token}, 
                                data={'name': 'Movies'})
        results = json.loads(rv.data.decode())

        rv = self.client().put('/v1/shopping_lists/{}'.format(results['id']), 
                               headers={'x-access-token': access_token}, 
                               data={'name': 'Groceries'})
        self.assertEqual(rv.status_code, 401)

    def test_shopping_list_deletion(self):
        """
        Test API can delete an existing shopping list. (DELETE request)
        """
        access_token = self.setup_users()

        rv = self.create_shopping_list()
        # Get the shopping list in json
        results = json.loads(rv.data.decode())

        # Delete the shopping list we just created
        res = self.client().delete(
            '/v1/shopping_lists/{}'.format(results['id']),
            headers={'x-access-token': access_token})
        self.assertEqual(res.status_code, 200)

    def test_non_existent_list_delete(self):
        """
        Delete a list that doesnt exist
        """
        access_token = self.setup_users()

        res = self.client().delete(
            '/v1/shopping_lists/23',
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
