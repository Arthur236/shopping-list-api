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
            db.create_all()

    def test_shopping_list_creation(self):
        """
        Test API can create a shopping list (POST request)
        """
        res = self.client().post('/shopping_lists/', data=self.shopping_list)
        self.assertEqual(res.status_code, 201)
        self.assertIn('Groceries', str(res.data))

    def test_api_can_get_all_shopping_lists(self):
        """
        Test API can get a shopping list (GET request)
        """
        res = self.client().post('/shopping_lists/', data=self.shopping_list)
        self.assertEqual(res.status_code, 201)
        res = self.client().get('/shopping_lists/')
        self.assertEqual(res.status_code, 200)
        self.assertIn('Groceries', str(res.data))

    def test_api_can_get_shopping_list_by_id(self):
        """
        Test API can get a single shopping list by using it's id
        """
        rv = self.client().post('/shopping_lists/', data=self.shopping_list)
        self.assertEqual(rv.status_code, 201)
        result_in_json = json.loads(rv.data.decode('utf-8').replace("'", "\""))
        result = self.client().get(
            '/shopping_lists/{}'.format(result_in_json['id']))
        self.assertEqual(result.status_code, 200)
        self.assertIn('Groceries', str(result.data))

    def test_shopping_list_can_be_edited(self):
        """
        Test API can edit an existing shopping list. (PUT request)
        """
        rv = self.client().post(
            '/shopping_lists/',
            data={'name': 'Electronics'})
        self.assertEqual(rv.status_code, 201)
        rv = self.client().put(
            '/shopping_lists/1',
            data={
                "name": "Groceries"
            })
        self.assertEqual(rv.status_code, 200)
        results = self.client().get('/shopping_lists/1')
        self.assertIn('Groceries', str(results.data))

    def test_shopping_list_deletion(self):
        """
        Test API can delete an existing shopping list. (DELETE request)
        """
        rv = self.client().post(
            '/shopping_lists/',
            data={'name': 'Groceries'})
        self.assertEqual(rv.status_code, 201)
        res = self.client().delete('/shopping_lists/1')
        self.assertEqual(res.status_code, 200)
        # Test to see if it exists, should return a 404
        result = self.client().get('/shopping_lists/1')
        self.assertEqual(result.status_code, 404)

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
