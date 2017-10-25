"""
Tests for authentication
"""
import unittest
import json
from app import create_app, db
from app.models import User


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
        self.admin = {
            'email': 'admin@gmail.com',
            'password': 'admin123'
        }

        with self.app.app_context():
            # Create all tables
            db.session.close()
            db.drop_all()
            db.create_all()

    def test_username_is_valid(self):
        """
        Test username cannot have special characters
        """
        res = self.client().post('/v1/auth/register',
                                 data={'username': 'test*/-', 'email': 'test@gmail.com',
                                       'password': 'password'})
        self.assertEqual(res.status_code, 400)

    def test_password_length(self):
        """
        Test password length
        """
        res = self.client().post('/v1/auth/register',
                                 data={'username': 'test', 'email': 'test@gmail.com',
                                       'password': 'pass'})
        self.assertEqual(res.status_code, 400)

    def test_email_is_valid(self):
        """
        Test email is correct format
        """
        res = self.client().post('/v1/auth/register',
                                 data={'username': 'test', 'email': 'test.com',
                                       'password': 'password'})
        self.assertEqual(res.status_code, 400)

    def test_registration(self):
        """
        Test user registration works correctly
        """
        res = self.client().post('/v1/auth/register', data=self.user1)
        self.assertEqual(res.status_code, 201)

    def create_user(self, user):
        """
        Helper function to create users
        """
        res = self.client().post('/v1/auth/register', data=user)

        return res

    def test_already_registered_user(self):
        """
        Test that a user cannot be registered twice
        """
        self.create_user(self.user1)
        res = self.create_user(self.user1)
        self.assertEqual(res.status_code, 202)

    def test_register_parameters(self):
        """
        Test if all parameters are provided
        """
        res = self.client().post('/v1/auth/register')
        self.assertEqual(res.status_code, 400)

    def test_user_login(self):
        """
        Test registered user can login
        """
        self.create_user(self.user1)
        login_res = self.client().post('/v1/auth/login', data=self.user1)

        # Get the results in json format
        result = json.loads(login_res.data.decode())
        # Assert that the status code is equal to 200
        self.assertEqual(login_res.status_code, 200)
        self.assertTrue(result['access-token'])

    def login_user(self, user):
        """
        Helper function to log in users
        """
        self.create_user(user)
        login_res = self.client().post('/v1/auth/login', data=user)
        access_token = json.loads(login_res.data.decode())['access-token']

        return access_token

    def test_login_parameters(self):
        """
        Test if all login parameters are provided
        """
        self.create_user(self.user1)
        login_res = self.client().post('/v1/auth/login')
        self.assertEqual(login_res.status_code, 400)

    def test_wrong_password(self):
        """
        Test whether a registered user can login with wrong password
        """
        self.create_user(self.user1)
        login_res = self.client().post('/v1/auth/login',
                                       data={'email': 'user1@gmail.com',
                                             'password': 'passwordssss'})

        # Assert that the status code
        self.assertEqual(login_res.status_code, 401)

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

        # Assert that this response must contain an error message
        # and an error status code 401(Unauthorized)
        self.assertEqual(res.status_code, 401)

    def test_password_reset_email(self):
        """
        Use invalid email
        """
        self.create_user(self.user1)

        res = self.client().post('/v1/auth/reset', data={'email': 'jwhe89@gmail.com'})
        self.assertEqual(res.status_code, 401)

    def test_pass_reset_email_parameter(self):
        """
        Exclude email parameter
        """
        self.create_user(self.user1)

        res = self.client().post('/v1/auth/reset')
        self.assertEqual(res.status_code, 400)

    def test_password_reset_token(self):
        """
        Test that a registered user can get password reset token
        """
        # Register a user
        self.create_user(self.user1)

        # Get password reset token
        res = self.client().post('/v1/auth/reset', data={'email': 'user1@gmail.com'})
        self.assertEqual(res.status_code, 200)

    def test_password_reset(self):
        """
        Attempt to reset their password
        """
        self.create_user(self.user1)

        # Get password reset token
        res = self.client().post('/v1/auth/reset', data={'email': 'user1@gmail.com'})
        token = json.loads(res.data.decode())

        reset_res = self.client().put('/v1/auth/password/' + token['pass-reset-token'],
                                      data={'password': 'pass123'})
        self.assertEqual(reset_res.status_code, 201)

        # Ensure you can log in with changed password
        login_res = self.client().post('/v1/auth/login',
                                       data={'email': 'user1@gmail.com', 'password': 'pass123'})

        # Get the results in json format
        result = json.loads(login_res.data.decode())
        # Assert that the status code is equal to 200
        self.assertEqual(login_res.status_code, 200)
        self.assertTrue(result['access-token'])

    def test_wrong_pass_reset_token(self):
        """
        Attempt to use wrong token
        """
        self.create_user(self.user1)

        reset_res = self.client().put('/v1/auth/password/wrong_token',
                                      data={'password': 'pass123'})
        self.assertEqual(reset_res.status_code, 400)

    def test_short_reset_password(self):
        """
        Attempt to reset using short password
        """
        self.create_user(self.user1)

        # Get password reset token
        res = self.client().post('/v1/auth/reset', data={'email': 'user1@gmail.com'})
        token = json.loads(res.data.decode())

        reset_res = self.client().put('/v1/auth/password/' + token['pass-reset-token'],
                                      data={'password': 'pass'})
        self.assertEqual(reset_res.status_code, 400)

    def test_reset_params(self):
        """
        Attempt to reset using no parameters
        """
        self.create_user(self.user1)

        # Get password reset token
        res = self.client().post('/v1/auth/reset', data={'email': 'user1@gmail.com'})
        token = json.loads(res.data.decode())

        reset_res = self.client().put('/v1/auth/password/' + token['pass-reset-token'])
        self.assertEqual(reset_res.status_code, 400)

    def test_get_profile_id_format(self):
        """
        Test the user id is the correct format
        """
        # Create user by making a POST request
        self.create_user(self.user1)
        access_token = self.login_user(self.user1)

        # Get the user profile
        res = self.client().get('/v1/users/two', headers={'x-access-token': access_token})
        self.assertEqual(res.status_code, 401)

    def test_get_profile(self):
        """
        Test that a user's profile can be loaded
        """
        # Create user by making a POST request
        self.create_user(self.user1)
        access_token = self.login_user(self.user1)

        # Get the user profile
        res = self.client().get('/v1/users/2', headers={'x-access-token': access_token})
        self.assertEqual(res.status_code, 200)

    def test_non_existent_user_profile(self):
        """
        Try to get non existing user profile
        """
        self.create_user(self.user1)
        access_token = self.login_user(self.user1)

        res = self.client().get('/v1/users/26', headers={'x-access-token': access_token})
        self.assertEqual(res.status_code, 404)

    def test_up_another_user_profile(self):
        """
        Try to update another user's profile
        """
        # Create user by making a POST request
        self.create_user(self.user1)
        access_token = self.login_user(self.user1)

        # Try to update another user's profile
        res = self.client().put('/v1/users/3', headers={'x-access-token': access_token},
                                data={
                                    'username': 'test_user',
                                    'email': 'test_email',
                                    'password': 'password'
                                })
        self.assertEqual(res.status_code, 403)

    def test_sp_chars_profile_update(self):
        """
        Put special characters in username
        """
        self.create_user(self.user1)
        access_token = self.login_user(self.user1)

        res = self.client().put('/v1/users/2', headers={'x-access-token': access_token},
                                data={
                                    'username': 'test_user*-/',
                                    'email': 'test_email@gmail.com',
                                    'password': 'password'
                                })
        self.assertEqual(res.status_code, 400)

    def test_invalid_email_prof_up(self):
        """
        Use invalid email
        """
        self.create_user(self.user1)
        access_token = self.login_user(self.user1)

        res = self.client().put('/v1/users/2', headers={'x-access-token': access_token},
                                data={
                                    'username': 'test_user',
                                    'email': 'test_email.com',
                                    'password': 'password'
                                })
        self.assertEqual(res.status_code, 400)

    def test_short_pass_profile_update(self):
        """
        Use short password
        """
        self.create_user(self.user1)
        access_token = self.login_user(self.user1)

        res = self.client().put('/v1/users/2', headers={'x-access-token': access_token},
                                data={
                                    'username': 'test_user',
                                    'email': 'test_email@gmail.com',
                                    'password': 'pass'
                                })
        self.assertEqual(res.status_code, 400)

    def test_email_exists_up_prof(self):
        """
        Use an email that already exists
        """
        self.create_user(self.user1)
        self.create_user(self.user2)
        access_token = self.login_user(self.user1)

        res = self.client().put('/v1/users/2', headers={'x-access-token': access_token},
                                data=self.user2)
        self.assertEqual(res.status_code, 401)

    def test_profile_edit_id_format(self):
        """
        Test that id format is correct when editing
        """
        self.create_user(self.user1)
        access_token = self.login_user(self.user1)

        res = self.client().put('/v1/users/two', headers={'x-access-token': access_token},
                                data=self.user1)
        self.assertEqual(res.status_code, 401)

    def test_update_profile(self):
        """
        Use correct details
        """
        self.create_user(self.user1)
        access_token = self.login_user(self.user1)

        res = self.client().put('/v1/users/2', headers={'x-access-token': access_token},
                                data={
                                    'username': 'test_user',
                                    'email': 'test_email@gmail.com',
                                    'password': 'password'
                                })
        self.assertEqual(res.status_code, 200)

    def test_del_diff_user_prof(self):
        """
        Try to delete another user's profile
        """
        self.create_user(self.user1)
        access_token = self.login_user(self.user1)

        res = self.client().delete('/v1/users/3', headers={'x-access-token': access_token})
        self.assertEqual(res.status_code, 403)

    def test_search_non_existent_user(self):
        """
        Try to search user that does not exist
        """
        self.create_user(self.user1)
        access_token = self.login_user(self.user1)

        res = self.client().get('/v1/users?q=70g', headers={'x-access-token': access_token})
        self.assertEqual(res.status_code, 404)

    def test_search_existent_user(self):
        """
        Try to search user that exists
        """
        self.create_user(self.user1)
        access_token = self.login_user(self.user1)

        res = self.client().get('/v1/users?q=us', headers={'x-access-token': access_token})
        self.assertEqual(res.status_code, 200)

    def test_delete_profile_id_format(self):
        """
        Test id is correct format when deleting
        """
        self.create_user(self.user1)
        access_token = self.login_user(self.user1)

        res = self.client().delete('/v1/users/two', headers={'x-access-token': access_token})
        self.assertEqual(res.status_code, 401)

    def test_delete_profile(self):
        """
        Use correct credentials
        """
        self.create_user(self.user1)
        access_token = self.login_user(self.user1)

        res = self.client().delete('/v1/users/3', headers={'x-access-token': access_token})
        self.assertEqual(res.status_code, 200)

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
