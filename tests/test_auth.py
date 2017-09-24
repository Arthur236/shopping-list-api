"""
Tests for authentication blueprint
"""
import unittest
import json
from app import create_app, db


class AuthTestCase(unittest.TestCase):
    """
    Tests for handling registration, login and token generation
    """

    def setUp(self):
        """
        Set up test variables
        """
        self.app = create_app(config_name="testing")
        # initialize the test client
        self.client = self.app.test_client
        # This is the user test json data with a predefined username and password
        self.user_data = {
            'username': 'User1',
            'email': 'user1@gmail.com',
            'password': 'password'
        }

        with self.app.app_context():
            # create all tables
            db.session.close()
            db.drop_all()
            db.create_all()

    def test_registration(self):
        """
        Test user registration works correctly
        """
        res = self.client().post('/auth/register', data=self.user_data)
        # get the results returned in json format
        result = json.loads(res.data.decode())
        # assert that the request contains a success message and a 201 status code
        self.assertEqual(result['message'], "You were registered successfully. Please log in.")
        self.assertEqual(res.status_code, 201)

    def test_already_registered_user(self):
        """
        Test that a user cannot be registered twice
        """
        res = self.client().post('/auth/register', data=self.user_data)
        self.assertEqual(res.status_code, 201)
        second_res = self.client().post('/auth/register', data=self.user_data)
        self.assertEqual(second_res.status_code, 202)
        # get the results returned in json format
        result = json.loads(second_res.data.decode())
        self.assertEqual(
            result['message'], "User already exists. Please login.")

    def test_user_login(self):
        """
        Test registered user can login
        """
        res = self.client().post('/auth/register', data=self.user_data)
        self.assertEqual(res.status_code, 201)
        login_res = self.client().post('/auth/login', data=self.user_data)

        # get the results in json format
        result = json.loads(login_res.data.decode())
        # Test that the response contains success message
        self.assertEqual(result['message'], "You logged in successfully.")
        # Assert that the status code is equal to 200
        self.assertEqual(login_res.status_code, 200)
        self.assertTrue(result['access-token'])

    def test_non_registered_user_login(self):
        """
        Test non registered users cannot login
        """
        # define a dictionary to represent an unregistered user
        not_a_user = {
            'username': 'not_user',
            'email': 'not_user@gmail.com',
            'password': 'nope'
        }
        # send a POST request to /auth/login with the data above
        res = self.client().post('/auth/login', data=not_a_user)
        # get the result in json
        result = json.loads(res.data.decode())

        # assert that this response must contain an error message
        # and an error status code 401(Unauthorized)
        self.assertEqual(res.status_code, 401)
        self.assertEqual(
            result['message'], "Invalid email or password. Please try again")

    def test_password_reset(self):
        """
        Test that a registered user can reset their password
        """
        # Register a user
        self.client().post('/auth/register', data=self.user_data)
        # Get password reset token
        res = self.client().post('/auth/reset', data={'email': 'user1@gmail.com'})
        self.assertEqual(res.status_code, 200)
        token = json.loads(res.data.decode())

        # Attempt to reset their password
        reset_res = self.client().put('/auth/password/' + token['pass-reset-token'],
                                      data={'password': 'pass123'})
        self.assertEqual(reset_res.status_code, 201)

        # Ensure you can log in with changed password
        login_res = self.client().post('/auth/login',
                                       data={'email': 'user1@gmail.com', 'password': 'pass123'})

        # get the results in json format
        result = json.loads(login_res.data.decode())
        # Test that the response contains success message
        self.assertEqual(result['message'], "You logged in successfully.")
        # Assert that the status code is equal to 200
        self.assertEqual(login_res.status_code, 200)
        self.assertTrue(result['access-token'])
