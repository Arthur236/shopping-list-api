"""
Test cases for application
"""
import unittest
import os
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
        self.shopping_list = {'name': 'Groceries', 'description': 'Description'}

        # binds the app to the current context
        with self.app.app_context():
            # create all tables
            db.session.close()
            db.drop_all()
            db.create_all()

    def register_user(self, username="test", password="password"):
        user_data = {
            'username': username,
            'password': password
        }
        return self.client().post('/auth/register', data=user_data)

    def login_user(self, username="test", password="password"):
        user_data = {
            'username': username,
            'password': password
        }
        return self.client().post('/auth/login', data=user_data)

    def test_shopping_list_creation(self):
        """
        Test API can create a shopping list (POST request)
        """
        # register a test user, then log them in
        self.register_user()
        result = self.login_user()
        access_token = json.loads(result.data.decode())['access-token']

        # create a shopping list by making a POST request
        res = self.client().post(
            '/shopping_lists',
            headers={'x-access-token': access_token},
            data=self.shopping_list)
        self.assertEqual(res.status_code, 201)
        self.assertIn('Groceries', str(res.data))

    def test_api_can_get_all_shopping_lists(self):
        """
        Test API can get a shopping list (GET request)
        """
        self.register_user()
        result = self.login_user()
        access_token = json.loads(result.data.decode())['access-token']

        # create a shopping list by making a POST request
        res = self.client().post(
            '/shopping_lists',
            headers={'x-access-token': access_token},
            data=self.shopping_list)
        self.assertEqual(res.status_code, 201)

        # get all the shopping lists that belong to the test user by making a GET request
        res = self.client().get(
            '/shopping_lists',
            headers={'x-access-token': access_token},
        )
        self.assertEqual(res.status_code, 200)
        self.assertIn('Groceries', str(res.data))

    def test_api_can_get_shopping_list_by_id(self):
        """
        Test API can get a single shopping list by using it's id
        """
        self.register_user()
        result = self.login_user()
        access_token = json.loads(result.data.decode())['access-token']

        rv = self.client().post('/shopping_lists', headers={'x-access-token': access_token},
                                data=self.shopping_list)
        # assert that the shopping list is created
        self.assertEqual(rv.status_code, 201)
        # get the response data in json format
        results = json.loads(rv.data.decode())

        result = self.client().get(
            '/shopping_list/{}'.format(results['id']),
            headers={'x-access-token': access_token})
        # assert that the shopping list is actually returned given its ID
        self.assertEqual(result.status_code, 200)
        self.assertIn('Groceries', str(result.data))

    def test_shopping_list_can_be_edited(self):
        """
        Test API can edit an existing shopping list. (PUT request)
        """
        self.register_user()
        result = self.login_user()
        access_token = json.loads(result.data.decode())['access-token']

        rv = self.client().post('/shopping_lists', headers={'x-access-token': access_token},
                                data={'name': 'Movies'})
        self.assertEqual(rv.status_code, 201)
        # get the json with the shopping list
        results = json.loads(rv.data.decode())

        # then, we edit the created shopping list by making a PUT request
        rv = self.client().put(
            '/shopping_list/{}'.format(results['id']),
            headers={'x-access-token': access_token},
            data={
                "name": "Electronics"
            })
        self.assertEqual(rv.status_code, 200)

        # finally, we get the edited shopping list to see if it is actually edited.
        results = self.client().get(
            '/shopping_list/{}'.format(results['id']),
            headers={'x-access-token': access_token})
        self.assertIn('Electronics', str(results.data))

    def test_shopping_list_deletion(self):
        """
        Test API can delete an existing shopping list. (DELETE request)
        """
        self.register_user()
        result = self.login_user()
        access_token = json.loads(result.data.decode())['access-token']

        rv = self.client().post('/shopping_lists', headers={'x-access-token': access_token},
                                data={'name': 'Consoles'})
        self.assertEqual(rv.status_code, 201)
        # get the shopping list in json
        results = json.loads(rv.data.decode())

        # delete the shopping list we just created
        res = self.client().delete(
            '/shopping_list/{}'.format(results['id']),
            headers={'x-access-token': access_token})
        self.assertEqual(res.status_code, 200)

    def tearDown(self):
        """
        Delete all initialized variables
        """
        with self.app.app_context():
            # drop all tables
            db.session.remove()
            db.drop_all()

    # Make the tests conveniently executable
    if __name__ == "__main__":
        unittest.main()
