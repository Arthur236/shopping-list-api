"""
Test cases for shopping lists
"""
from flask_testing import TestCase
import json
from app import create_app, db


class ShoppingListTestCase(TestCase):
    """
    This class represents the shopping list test case
    """

    def create_app(self):
        app = create_app(config_name="testing")
        return app

    def setUp(self):
        """
        Define test variables and initialize app
        """
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

        db.create_all()

        # Register users
        self.client.post('/v1/auth/register', data=self.user1)
        self.client.post('/v1/auth/register', data=self.user2)

    def tearDown(self):
        """
        Delete all initialized variables
        """
        db.session.remove()
        db.drop_all()

    def login_user(self, user):
        """
        Helper function to login users
        """
        login_res = self.client.post('/v1/auth/login', data=user)
        access_token = json.loads(login_res.data.decode())['access-token']

        return access_token

    def test_list_name_special_chars(self):
        """
        Test if list name has special chars
        """
        # Register a test user, then log them in
        access_token = self.login_user(self.user1)

        # Create shopping list with special characters
        res = self.client.post(
            '/v1/shopping_lists',
            headers={'x-access-token': access_token},
            data=self.shopping_list_special)
        self.assertEqual(res.status_code, 400)

    def test_empty_list_name_param(self):
        """
        Test if list name param is present
        """
        # Register a test user, then log them in
        access_token = self.login_user(self.user1)

        res = self.client.post(
            '/v1/shopping_lists',
            headers={'x-access-token': access_token})
        self.assertEqual(res.status_code, 400)

    def test_shopping_list_exists(self):
        """
        Test if shopping list already exists
        """
        # Register a test user, then log them in
        access_token = self.login_user(self.user1)

        # Create a shopping list by making a POST request
        self.client.post(
            '/v1/shopping_lists',
            headers={'x-access-token': access_token},
            data=self.shopping_list)

        res = self.client.post(
            '/v1/shopping_lists',
            headers={'x-access-token': access_token},
            data=self.shopping_list)

        self.assertEqual(res.status_code, 401)

    def test_shopping_list_creation(self):
        """
        Test API can create a shopping list (POST request)
        """
        # Register a test user, then log them in
        access_token = self.login_user(self.user1)

        # Create a shopping list by making a POST request
        res = self.client.post(
            '/v1/shopping_lists',
            headers={'x-access-token': access_token},
            data=self.shopping_list)
        self.assertEqual(res.status_code, 201)
        self.assertIn('Groceries', str(res.data))

    def test_list_creation_token_correct(self):
        """
        Test if token is correct format
        """
        res = self.client.post('/v1/shopping_lists',
                               headers={'x-access-token': 'some_incorrect_token'},
                               data=self.shopping_list)
        self.assertEqual(res.status_code, 401)

    def test_list_creation_token_present(self):
        """
        Test if token is present
        """
        res = self.client.post('/v1/shopping_lists',
                               data=self.shopping_list)
        self.assertEqual(res.status_code, 401)

    def create_shopping_list(self):
        """
        Helper function to create shopping list
        """
        access_token = self.login_user(self.user1)

        results = self.client.post('/v1/shopping_lists',
                                   headers={'x-access-token': access_token},
                                   data=self.shopping_list)

        return results

    def test_get_all_shopping_lists(self):
        """
        Test API can get a shopping list (GET request)
        """
        access_token = self.login_user(self.user1)

        self.create_shopping_list()

        # Get all the shopping lists that belong to the test user by making a GET request
        res = self.client.get(
            '/v1/shopping_lists',
            headers={'x-access-token': access_token},
        )
        self.assertEqual(res.status_code, 200)

    def test_get_lists_token_correct(self):
        """
        Test whether token is correct
        """
        self.create_shopping_list()

        res = self.client.get(
            '/v1/shopping_lists',
            headers={'x-access-token': 'wrong_token'},
        )
        self.assertEqual(res.status_code, 401)

    def test_get_lists_token_present(self):
        """
        Test whether token is present
        """
        self.create_shopping_list()

        res = self.client.get(
            '/v1/shopping_lists',
        )
        self.assertEqual(res.status_code, 401)

    def test_wrong_get_pagination_limits(self):
        """
        Use the wrong limit and page data formats
        """
        access_token = self.login_user(self.user1)

        res = self.client.get('/v1/shopping_lists?page=one&limit=two',
                              headers={'x-access-token': access_token})
        self.assertEqual(res.status_code, 401)

    def test_get_non_existent_list(self):
        """
        Try search non existent list
        """
        access_token = self.login_user(self.user1)

        res = self.client.get(
            '/v1/shopping_lists?q=hdiue',
            headers={'x-access-token': access_token}
        )
        self.assertEqual(res.status_code, 404)

    def test_existent_list(self):
        """
        Try search existent list
        """
        access_token = self.login_user(self.user1)

        self.create_shopping_list()

        res = self.client.get(
            '/v1/shopping_lists?q=gro',
            headers={'x-access-token': access_token}
        )
        self.assertEqual(res.status_code, 200)

    def test_get_paginated_lists(self):
        """
        Try get paginated lists
        """
        access_token = self.login_user(self.user1)

        self.create_shopping_list()

        res = self.client.get(
            '/v1/shopping_lists?page=1&limit=2',
            headers={'x-access-token': access_token}
        )
        self.assertEqual(res.status_code, 200)

    def test_get_paginated_lists_when_none(self):
        """
        Try get paginated lists when user has no lists
        """
        access_token = self.login_user(self.user1)

        res = self.client.get(
            '/v1/shopping_lists?page=1&limit=2',
            headers={'x-access-token': access_token}
        )
        self.assertEqual(res.status_code, 404)

    def test_get_shopping_list_by_id(self):
        """
        Test API can get a single shopping list by using it's id
        """
        access_token = self.login_user(self.user1)

        rv = self.create_shopping_list()
        results = json.loads(rv.data.decode())

        result = self.client.get(
            '/v1/shopping_lists/{}'.format(results['id']),
            headers={'x-access-token': access_token})
        # Assert that the shopping list is actually returned given its ID
        self.assertEqual(result.status_code, 200)

    def test_get_list_token_correct(self):
        """
        Test whether token is correct
        """
        rv = self.create_shopping_list()
        results = json.loads(rv.data.decode())

        result = self.client.get(
            '/v1/shopping_lists/{}'.format(results['id']),
            headers={'x-access-token': 'wrong_token'})
        self.assertEqual(result.status_code, 401)

    def test_get_list_token_present(self):
        """
        Test whether token is present
        """
        rv = self.create_shopping_list()
        results = json.loads(rv.data.decode())

        result = self.client.get(
            '/v1/shopping_lists/{}'.format(results['id']))
        self.assertEqual(result.status_code, 401)

    def test_get_shopping_list_id_format(self):
        """
        Test id is correct format
        """
        access_token = self.login_user(self.user1)

        result = self.client.get(
            '/v1/shopping_lists/one',
            headers={'x-access-token': access_token})
        self.assertEqual(result.status_code, 401)

    def test_get_non_existent_list_by_id(self):
        """
        Test API can get a shopping list that doesnt exist by using it's id
        """
        access_token = self.login_user(self.user1)

        result = self.client.get(
            '/v1/shopping_lists/65',
            headers={'x-access-token': access_token})
        # Assert that the shopping list is actually returned given its ID
        self.assertEqual(result.status_code, 404)

    def test_update_non_existent_list(self):
        """
        Test non existent lists
        """
        access_token = self.login_user(self.user1)

        result = self.client.put(
            '/v1/shopping_lists/689',
            headers={'x-access-token': access_token})
        self.assertEqual(result.status_code, 404)

    def test_shopping_list_edit(self):
        """
        Test API can edit an existing shopping list. (PUT request)
        """
        access_token = self.login_user(self.user1)

        rv = self.create_shopping_list()
        results = json.loads(rv.data.decode())

        # Then, we edit the created shopping list by making a PUT request
        rv = self.client.put(
            '/v1/shopping_lists/{}'.format(results['id']),
            headers={'x-access-token': access_token},
            data={
                "name": "Electronics"
            })
        self.assertEqual(rv.status_code, 200)

    def test_list_edit_token_correct(self):
        """
        Test whether token is correct
        """
        rv = self.create_shopping_list()
        results = json.loads(rv.data.decode())

        rv = self.client.put(
            '/v1/shopping_lists/{}'.format(results['id']),
            headers={'x-access-token': 'wrong_token'},
            data={
                "name": "Electronics"
            })
        self.assertEqual(rv.status_code, 401)

    def test_list_edit_token_present(self):
        """
        Test whether token is present
        """
        rv = self.create_shopping_list()
        results = json.loads(rv.data.decode())

        rv = self.client.put(
            '/v1/shopping_lists/{}'.format(results['id']),
            data={
                "name": "Electronics"
            })
        self.assertEqual(rv.status_code, 401)

    def test_shopping_list_edit_id_format(self):
        """
        Test id is correct format
        """
        access_token = self.login_user(self.user1)

        result = self.client.put(
            '/v1/shopping_lists/one',
            headers={'x-access-token': access_token})
        self.assertEqual(result.status_code, 401)

    def test_edit_with_special_chars(self):
        """
        Try to edit a list with special characters
        """
        access_token = self.login_user(self.user1)

        rv = self.create_shopping_list()

        # Get the json with the shopping list
        results = json.loads(rv.data.decode())

        rv = self.client.put(
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
        access_token = self.login_user(self.user1)

        self.create_shopping_list()

        rv = self.client.post('/v1/shopping_lists',
                              headers={'x-access-token': access_token},
                              data={'name': 'Movies'})
        results = json.loads(rv.data.decode())

        rv = self.client.put('/v1/shopping_lists/{}'.format(results['id']),
                             headers={'x-access-token': access_token},
                             data={'name': 'Groceries'})
        self.assertEqual(rv.status_code, 401)

    def test_shopping_list_deletion(self):
        """
        Test API can delete an existing shopping list. (DELETE request)
        """
        access_token = self.login_user(self.user1)

        rv = self.create_shopping_list()
        # Get the shopping list in json
        results = json.loads(rv.data.decode())

        # Delete the shopping list we just created
        res = self.client.delete(
            '/v1/shopping_lists/{}'.format(results['id']),
            headers={'x-access-token': access_token})
        self.assertEqual(res.status_code, 200)

    def test_list_deletion_token_correct(self):
        """
        Test whether token is correct
        """
        rv = self.create_shopping_list()
        results = json.loads(rv.data.decode())

        res = self.client.delete(
            '/v1/shopping_lists/{}'.format(results['id']),
            headers={'x-access-token': 'wrong_token'})
        self.assertEqual(res.status_code, 401)

    def test_list_deletion_token_present(self):
        """
        Test whether token is present
        """
        rv = self.create_shopping_list()
        results = json.loads(rv.data.decode())

        res = self.client.delete(
            '/v1/shopping_lists/{}'.format(results['id']))
        self.assertEqual(res.status_code, 401)

    def test_shopping_list_delete_id_format(self):
        """
        Test id is correct format
        """
        access_token = self.login_user(self.user1)

        result = self.client.delete(
            '/v1/shopping_lists/one',
            headers={'x-access-token': access_token})
        self.assertEqual(result.status_code, 401)

    def test_non_existent_list_delete(self):
        """
        Delete a list that doesnt exist
        """
        access_token = self.login_user(self.user1)

        res = self.client.delete(
            '/v1/shopping_lists/23',
            headers={'x-access-token': access_token})
        self.assertEqual(res.status_code, 404)
