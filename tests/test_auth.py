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
        # Initialize the test client
        self.client = self.app.test_client
        # This is the user test json data with a predefined username and password
        self.user_data = {
            'username': 'User1',
            'email': 'user1@gmail.com',
            'password': 'password'
        }

        with self.app.app_context():
            # Create all tables
            db.session.close()
            db.drop_all()
            db.create_all()

    def test_registration(self):
        """
        Test user registration works correctly
        """
        # Test email is correct format
        res = self.client().post('/v1/auth/register',
                                 data={'username': 'test', 'email': 'test.com',
                                       'password': 'password'})
        self.assertEqual(res.status_code, 400)

        # Test username cannot have special characters
        res = self.client().post('/v1/auth/register',
                                 data={'username': 'test*/-', 'email': 'test@gmail.com',
                                       'password': 'password'})
        self.assertEqual(res.status_code, 400)

        # Test password length
        res = self.client().post('/v1/auth/register',
                                 data={'username': 'test', 'email': 'test@gmail.com',
                                       'password': 'pass'})
        self.assertEqual(res.status_code, 400)

        res = self.client().post('/v1/auth/register', data=self.user_data)
        # Get the results returned in json format
        result = json.loads(res.data.decode())
        # Assert that the request contains a success message and a 201 status code
        self.assertEqual(result['message'], "You were registered successfully. Please log in.")
        self.assertEqual(res.status_code, 201)

    def test_already_registered_user(self):
        """
        Test that a user cannot be registered twice
        """
        res = self.client().post('/v1/auth/register', data=self.user_data)
        self.assertEqual(res.status_code, 201)
        second_res = self.client().post('/v1/auth/register', data=self.user_data)
        self.assertEqual(second_res.status_code, 202)

        # Get the results returned in json format
        result = json.loads(second_res.data.decode())
        self.assertEqual(
            result['message'], "User already exists. Please login.")

    def test_user_login(self):
        """
        Test registered user can login
        """
        res = self.client().post('/v1/auth/register', data=self.user_data)
        self.assertEqual(res.status_code, 201)
        login_res = self.client().post('/v1/auth/login', data=self.user_data)

        # Get the results in json format
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
        # Send a POST request to /v1/auth/login with the data above
        res = self.client().post('/v1/auth/login', data=not_a_user)
        # Get the result in json
        result = json.loads(res.data.decode())

        # Assert that this response must contain an error message
        # and an error status code 401(Unauthorized)
        self.assertEqual(res.status_code, 401)
        self.assertEqual(
            result['message'], "Invalid email or password. Please try again")

    def test_password_reset(self):
        """
        Test that a registered user can reset their password
        """
        # Register a user
        self.client().post('/v1/auth/register', data=self.user_data)
        # Get password reset token
        res = self.client().post('/v1/auth/reset', data={'email': 'user1@gmail.com'})
        self.assertEqual(res.status_code, 200)
        token = json.loads(res.data.decode())

        # Attempt to reset their password
        reset_res = self.client().put('/v1/auth/password/' + token['pass-reset-token'],
                                      data={'password': 'pass123'})
        self.assertEqual(reset_res.status_code, 201)

        # Attempt to use wrong token
        reset_res = self.client().put('/v1/auth/password/wrong_token',
                                      data={'password': 'pass123'})
        self.assertEqual(reset_res.status_code, 400)

        # Attempt to reset using short password
        reset_res = self.client().put('/v1/auth/password/' + token['pass-reset-token'],
                                      data={'password': 'pass'})
        self.assertEqual(reset_res.status_code, 400)

        # Ensure you can log in with changed password
        login_res = self.client().post('/v1/auth/login',
                                       data={'email': 'user1@gmail.com', 'password': 'pass123'})

        # Get the results in json format
        result = json.loads(login_res.data.decode())
        # Test that the response contains success message
        self.assertEqual(result['message'], "You logged in successfully.")
        # Assert that the status code is equal to 200
        self.assertEqual(login_res.status_code, 200)
        self.assertTrue(result['access-token'])

    def test_get_users(self):
        """
        Test that an admin can get all users
        """
        login_res = self.client().post('/v1/auth/login', data={
            'email': 'admin@gmail.com',
            'password': 'admin123'
        })
        self.assertEqual(login_res.status_code, 200)
        access_token = json.loads(login_res.data.decode())['access-token']

        # Create user by making a POST request
        res = self.client().post('/v1/auth/register', data=self.user_data)
        self.assertEqual(res.status_code, 201)

        # Get all the users by making a GET request
        res = self.client().get('/v1/users', headers={'x-access-token': access_token})
        self.assertEqual(res.status_code, 200)
        self.assertIn('user1', str(res.data))

        # Use the wrong limit and page data formats
        res = self.client().get('/v1/users?page=one&limit=two',
                                headers={'x-access-token': access_token})
        self.assertEqual(res.status_code, 401)

    def test_get_user_by_id(self):
        """
        Test that an admin can get a user by their id
        """
        # Create user by making a POST request
        res = self.client().post('/v1/auth/register', data=self.user_data)
        self.assertEqual(res.status_code, 201)

        login_res = self.client().post('/v1/auth/login', data={
            'email': 'admin@gmail.com',
            'password': 'admin123'
        })
        self.assertEqual(login_res.status_code, 200)
        access_token = json.loads(login_res.data.decode())['access-token']

        # Get all the users by making a GET request
        res = self.client().get('/v1/admin/users/2', headers={'x-access-token': access_token})
        self.assertEqual(res.status_code, 200)
        self.assertIn('user1', str(res.data))

        # Try to get non existing user
        res = self.client().get('/v1/admin/users/26', headers={'x-access-token': access_token})
        self.assertEqual(res.status_code, 404)

        # Try to access without admin rights
        login_res = self.client().post('/v1/auth/login', data=self.user_data)
        self.assertEqual(login_res.status_code, 200)
        access_token = json.loads(login_res.data.decode())['access-token']
        res = self.client().get('/v1/admin/users/2', headers={'x-access-token': access_token})
        self.assertEqual(res.status_code, 403)

    def test_delete_user(self):
        """
        Test that an admin can delete a user by their id
        """
        # Create user by making a POST request
        res = self.client().post('/v1/auth/register', data=self.user_data)
        self.assertEqual(res.status_code, 201)

        # Try to access without admin rights
        login_res = self.client().post('/v1/auth/login', data=self.user_data)
        self.assertEqual(login_res.status_code, 200)
        access_token = json.loads(login_res.data.decode())['access-token']
        res = self.client().delete('/v1/admin/users/2', headers={'x-access-token': access_token})
        self.assertEqual(res.status_code, 403)

        login_res = self.client().post('/v1/auth/login', data={
            'email': 'admin@gmail.com',
            'password': 'admin123'
        })
        self.assertEqual(login_res.status_code, 200)
        access_token = json.loads(login_res.data.decode())['access-token']

        # Attempt to delete a user
        res = self.client().delete('/v1/admin/users/2', headers={'x-access-token': access_token})
        self.assertEqual(res.status_code, 200)

        # Attempt to delete a non existent user
        res = self.client().delete('/v1/admin/users/298',
                                   headers={'x-access-token': access_token})
        self.assertEqual(res.status_code, 404)

        # Attempt to delete yourself
        res = self.client().delete('/v1/admin/users/1', headers={'x-access-token': access_token})
        self.assertEqual(res.status_code, 403)

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
