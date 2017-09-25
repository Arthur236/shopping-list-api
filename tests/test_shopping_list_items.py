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

    def register_user(self, username="test", email="test@gmail.com", password="password"):
        user_data = {
            'username': username,
            'email': email,
            'password': password
        }
        return self.client().post('/auth/register', data=user_data)

    def login_user(self, email="test@gmail.com", password="password"):
        user_data = {
            'email': email,
            'password': password
        }
        return self.client().post('/auth/login', data=user_data)

    def setUp(self):
        """
        Define test variables and initialize app
        """
        self.app = create_app(config_name="testing")
        self.client = self.app.test_client
        self.shopping_list = {'name': 'Groceries', 'description': 'Description'}
        self.shopping_list_item = {'list_id': 1, 'name': 'Tomatoes', 'quantity': 20,
                                   'unit_price': 5}

        # binds the app to the current context
        with self.app.app_context():
            # create all tables
            db.session.close()
            db.drop_all()
            db.create_all()

            # register a test user, then log them in
            self.register_user()
            result = self.login_user()
            self.access_token = json.loads(result.data.decode())['access-token']

            rv = self.client().post('/shopping_lists', headers={'x-access-token': self.access_token},
                                    data=self.shopping_list)
            # assert that the shopping list is created
            self.assertEqual(rv.status_code, 201)

    def test_item_creation(self):
        """
        Test API can create a shopping list item (POST request)
        """
        # create shopping list item
        res = self.client().post('/shopping_lists/1/items', headers={'x-access-token': self.access_token},
                                 data=self.shopping_list_item)
        # assert that the shopping list item is created
        self.assertEqual(res.status_code, 201)
        self.assertIn('Tomatoes', str(res.data))

    def test_api_can_get_item_by_id(self):
        """
        Test API can get a single shopping list item by using it's id
        """
        # create shopping list item
        res = self.client().post('/shopping_lists/1/items', headers={'x-access-token': self.access_token},
                                 data=self.shopping_list_item)
        # assert that the shopping list item is created
        self.assertEqual(res.status_code, 201)
        # get the response data in json format
        results = json.loads(res.data.decode())

        result = self.client().get('/shopping_lists/1/items/{}'.format(results['id']),
                                   headers={'x-access-token': self.access_token})
        # assert that the shopping list item is actually returned given its ID
        self.assertEqual(result.status_code, 201)
        self.assertIn('Tomatoes', str(result.data))

    def test_item_can_be_edited(self):
        """
        Test API can edit an existing shopping list item. (PUT request)
        """
        # create shopping list item
        res = self.client().post('/shopping_lists/1/items', headers={'x-access-token': self.access_token},
                                 data=self.shopping_list_item)
        # assert that the shopping list item is created
        self.assertEqual(res.status_code, 201)
        # get the json with the shopping list item
        results = json.loads(res.data.decode())

        # then, we edit the created shopping list item by making a PUT request
        rv = self.client().put(
            '/shopping_lists/1/items/{}'.format(results['id']),
            headers={'x-access-token': self.access_token},
            data={
                "name": "Oranges",
                "quantity": 2,
                "unit_price": 20
            })
        self.assertEqual(rv.status_code, 201)

        # finally, we get the edited shopping list item to see if it is actually edited.
        results = self.client().get(
            '/shopping_lists/1/items/{}'.format(results['id']),
            headers={'x-access-token': self.access_token})
        self.assertIn('Oranges', str(results.data))

    def test_item_deletion(self):
        """
        Test API can delete an existing shopping list item. (DELETE request)
        """
        # create shopping list item
        res = self.client().post('/shopping_lists/1/items', headers={'x-access-token': self.access_token},
                                 data=self.shopping_list_item)
        # assert that the shopping list item is created
        self.assertEqual(res.status_code, 201)
        # get the shopping list in json
        results = json.loads(res.data.decode())

        # delete the shopping list we just created
        res = self.client().delete(
            '/shopping_lists/1/items/{}'.format(results['id']),
            headers={'x-access-token': self.access_token})
        self.assertEqual(res.status_code, 201)

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
