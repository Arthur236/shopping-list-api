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
        # create users by making POST requests
        res = self.client().post('/auth/register', data=self.user1)
        self.assertEqual(res.status_code, 201)
        res = self.client().post('/auth/register', data=self.user2)
        self.assertEqual(res.status_code, 201)

        # Log in the first user
        login_res = self.client().post('/auth/login', data=self.user1)
        self.assertEqual(login_res.status_code, 200)
        access_token = json.loads(login_res.data.decode())['access-token']

        return access_token

    def test_shopping_list_creation(self):
        """
        Test API can create a shopping list (POST request)
        """
        # Register a test user, then log them in
        access_token = self.setup_users()

        # Create a shopping list by making a POST request
        res = self.client().post(
            '/shopping_lists',
            headers={'x-access-token': access_token},
            data=self.shopping_list)
        self.assertEqual(res.status_code, 201)
        self.assertIn('Groceries', str(res.data))

        # Create shopping list with special characters
        res = self.client().post(
            '/shopping_lists',
            headers={'x-access-token': access_token},
            data=self.shopping_list_special)
        self.assertEqual(res.status_code, 400)

    def test_api_can_get_all_shopping_lists(self):
        """
        Test API can get a shopping list (GET request)
        """
        access_token = self.setup_users()

        # Create a shopping list by making a POST request
        res = self.client().post(
            '/shopping_lists',
            headers={'x-access-token': access_token},
            data=self.shopping_list)
        self.assertEqual(res.status_code, 201)

        # Get all the shopping lists that belong to the test user by making a GET request
        res = self.client().get(
            '/shopping_lists',
            headers={'x-access-token': access_token},
        )
        self.assertEqual(res.status_code, 200)
        self.assertIn('Groceries', str(res.data))

        # Use the wrong limit and page data formats
        res = self.client().get('/shopping_lists?page=one&limit=two', headers={'x-access-token': access_token}, )
        self.assertEqual(res.status_code, 401)

        # Try search non existent list
        res = self.client().get(
            '/shopping_lists?q=hdiue',
            headers={'x-access-token': access_token},
        )
        self.assertEqual(res.status_code, 404)

        # Try search non existent list
        res = self.client().get(
            '/shopping_lists?q=gro',
            headers={'x-access-token': access_token},
        )
        self.assertEqual(res.status_code, 200)

        # Try get paginated lists when user has no lists
        res = self.client().get(
            '/shopping_lists?page=1&limit=2',
            headers={'x-access-token': access_token},
        )
        self.assertEqual(res.status_code, 200)

    def test_api_can_get_shopping_list_by_id(self):
        """
        Test API can get a single shopping list by using it's id
        """
        access_token = self.setup_users()

        rv = self.client().post('/shopping_lists', headers={'x-access-token': access_token},
                                data=self.shopping_list)
        # Assert that the shopping list is created
        self.assertEqual(rv.status_code, 201)
        # Get the response data in json format
        results = json.loads(rv.data.decode())

        result = self.client().get(
            '/shopping_lists/{}'.format(results['id']),
            headers={'x-access-token': access_token})
        # Assert that the shopping list is actually returned given its ID
        self.assertEqual(result.status_code, 200)
        self.assertIn('Groceries', str(result.data))

    def test_shopping_list_can_be_edited(self):
        """
        Test API can edit an existing shopping list. (PUT request)
        """
        access_token = self.setup_users()

        rv = self.client().post('/shopping_lists', headers={'x-access-token': access_token},
                                data={'name': 'Groceries'})
        self.assertEqual(rv.status_code, 201)
        rv = self.client().post('/shopping_lists', headers={'x-access-token': access_token},
                                data={'name': 'Movies'})
        self.assertEqual(rv.status_code, 201)
        # Get the json with the shopping list
        results = json.loads(rv.data.decode())

        # Then, we edit the created shopping list by making a PUT request
        rv = self.client().put(
            '/shopping_lists/{}'.format(results['id']),
            headers={'x-access-token': access_token},
            data={
                "name": "Electronics"
            })
        self.assertEqual(rv.status_code, 200)

        # Try to edit a list with special characters
        rv = self.client().put(
            '/shopping_lists/{}'.format(results['id']),
            headers={'x-access-token': access_token},
            data={
                "name": "Electronics/*-"
            })
        self.assertEqual(rv.status_code, 400)

        # Try to give it a name of a list that already exists
        rv = self.client().put(
            '/shopping_lists/{}'.format(results['id']),
            headers={'x-access-token': access_token},
            data={
                "name": "Groceries"
            })
        self.assertEqual(rv.status_code, 401)

        # Finally, we get the edited shopping list to see if it is actually edited.
        results = self.client().get(
            '/shopping_lists/{}'.format(results['id']),
            headers={'x-access-token': access_token})
        self.assertIn('Electronics', str(results.data))

    def test_shopping_list_deletion(self):
        """
        Test API can delete an existing shopping list. (DELETE request)
        """
        access_token = self.setup_users()

        rv = self.client().post('/shopping_lists', headers={'x-access-token': access_token},
                                data={'name': 'Consoles'})
        self.assertEqual(rv.status_code, 201)
        # Get the shopping list in json
        results = json.loads(rv.data.decode())

        # Delete the shopping list we just created
        res = self.client().delete(
            '/shopping_lists/{}'.format(results['id']),
            headers={'x-access-token': access_token})
        self.assertEqual(res.status_code, 200)

        # Give a list that doesnt exist
        res = self.client().delete(
            '/shopping_lists/23',
            headers={'x-access-token': access_token})
        self.assertEqual(res.status_code, 404)

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
