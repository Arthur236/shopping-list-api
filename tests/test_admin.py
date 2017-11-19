"""
Tests for admin
"""
import json
from flask_testing import TestCase
from app import create_app, db


class AuthTestCase(TestCase):
    """
    Tests for admin operations
    """

    def create_app(self):
        """
        Instantiate app instance
        """
        app = create_app(config_name="testing")
        return app

    def setUp(self):
        """
        Set up test variables
        """
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
        access_token = json.loads(login_res.data.decode())['access_token']

        return access_token

    def test_get_users_token_correct(self):
        """
        Test if token is correct format
        """
        res = self.client.get('/v1/admin/users', headers={'x-access-token': 'wrong_token'})
        self.assertEqual(res.status_code, 401)

    def test_get_users_token_present(self):
        """
        Test if token is present
        """
        res = self.client.get('/v1/admin/users')
        self.assertEqual(res.status_code, 401)

    def test_get_users(self):
        """
        Test that an admin can get all users
        """
        access_token = self.login_user(self.admin)

        # Get all the users by making a GET request
        res = self.client.get('/v1/admin/users', headers={'x-access-token': access_token})
        # Make sure admin is not in list
        self.assertNotIn('admin', str(res.data))
        self.assertEqual(res.status_code, 200)

    def test_get_users_without_rights(self):
        """
        Try to get users without admin rights
        """
        self.login_user(self.admin)
        login_res = self.client.post('/v1/auth/login', data=self.user2)
        access_token = json.loads(login_res.data.decode())['access_token']

        # Get all the users by making a GET request
        res = self.client.get('/v1/admin/users', headers={'x-access-token': access_token})
        self.assertEqual(res.status_code, 403)

    def test_search_non_existent_user(self):
        """
        Try to search user that does not exist
        """
        access_token = self.login_user(self.admin)

        res = self.client.get('/v1/admin/users?q=70g', headers={'x-access-token': access_token})
        self.assertEqual(res.status_code, 404)

    def test_search_existent_user(self):
        """
        Try to search user that exists
        """
        access_token = self.login_user(self.admin)

        res = self.client.get('/v1/admin/users?q=us', headers={'x-access-token': access_token})
        self.assertEqual(res.status_code, 200)

    def test_get_pagination_limits(self):
        """
        Use the wrong limit and page data formats
        """
        access_token = self.login_user(self.admin)

        res = self.client.get('/v1/admin/users?page=one&limit=two',
                              headers={'x-access-token': access_token})
        self.assertEqual(res.status_code, 401)

    def test_get_paginated_users(self):
        """
        Get paginated users
        """
        access_token = self.login_user(self.admin)

        res = self.client.get('/v1/admin/users?page=1&limit=2',
                              headers={'x-access-token': access_token})
        self.assertNotIn('admin', str(res.data))
        self.assertEqual(res.status_code, 200)

    def test_get_user_by_id(self):
        """
        Test that an admin can get a user by their id
        """
        access_token = self.login_user(self.admin)

        # Get specific user
        res = self.client.get('/v1/admin/users/2', headers={'x-access-token': access_token})
        self.assertEqual(res.status_code, 200)

    def test_get_user_id_format(self):
        """
        Test that id is correct format
        """
        access_token = self.login_user(self.admin)

        # Get specific user
        res = self.client.get('/v1/admin/users/two', headers={'x-access-token': access_token})
        self.assertEqual(res.status_code, 401)

    def test_get_non_existent_user(self):
        """
        Try to get non existing user
        """
        access_token = self.login_user(self.admin)

        res = self.client.get('/v1/admin/users/26', headers={'x-access-token': access_token})
        self.assertEqual(res.status_code, 404)

    def test_get_user_admin_rights(self):
        """
        Try to get user without admin rights
        """
        self.login_user(self.admin)
        login_res = self.client.post('/v1/auth/login', data=self.user2)
        access_token = json.loads(login_res.data.decode())['access_token']

        res = self.client.get('/v1/admin/users/2', headers={'x-access-token': access_token})
        self.assertEqual(res.status_code, 403)

    def test_get_user_token_correct(self):
        """
        Test if token is correct format
        """
        res = self.client.get('/v1/admin/users/2', headers={'x-access-token': 'wrong_token'})
        self.assertEqual(res.status_code, 401)

    def test_get_user_token_present(self):
        """
        Test if token is present
        """
        res = self.client.get('/v1/admin/users/2')
        self.assertEqual(res.status_code, 401)

    def test_delete_user_without_admin(self):
        """
        Try to delete user without admin rights
        """
        self.login_user(self.admin)
        login_res = self.client.post('/v1/auth/login', data=self.user2)
        access_token = json.loads(login_res.data.decode())['access_token']

        res = self.client.delete('/v1/admin/users/2', headers={'x-access-token': access_token})
        self.assertEqual(res.status_code, 403)

    def test_delete_user_as_admin(self):
        """
        Try to access with admin rights
        """
        access_token = self.login_user(self.admin)

        # Attempt to delete a user
        res = self.client.delete('/v1/admin/users/2', headers={'x-access-token': access_token})
        self.assertEqual(res.status_code, 200)

    def test_delete_user_id_format(self):
        """
        Test id is correct format
        """
        access_token = self.login_user(self.admin)

        # Attempt to delete a user
        res = self.client.delete('/v1/admin/users/two', headers={'x-access-token': access_token})
        self.assertEqual(res.status_code, 401)

    def test_delete_non_existent_user(self):
        """
        Attempt to delete a non existent user
        """
        access_token = self.login_user(self.admin)

        res = self.client.delete('/v1/admin/users/298',
                                 headers={'x-access-token': access_token})
        self.assertEqual(res.status_code, 404)

    def test_admin_delete_themselves(self):
        """
        Attempt to delete yourself
        """
        access_token = self.login_user(self.admin)

        res = self.client.delete('/v1/admin/users/1', headers={'x-access-token': access_token})
        self.assertEqual(res.status_code, 403)

    def test_delete_user_token_correct(self):
        """
        Test if token is correct format
        """
        res = self.client.delete('/v1/admin/users/2', headers={'x-access-token': 'wrong_token'})
        self.assertEqual(res.status_code, 401)

    def test_delete_user_token_present(self):
        """
        Test if token is present
        """
        res = self.client.delete('/v1/admin/users/2')
        self.assertEqual(res.status_code, 401)

    def test_get_paginated_users_wn(self):
        """
        Try to get paginated users when none exist
        """
        login_res = self.client.post('/v1/auth/login', data=self.admin)
        access_token = json.loads(login_res.data.decode())['access_token']

        # Delete users
        self.client.delete('/v1/admin/users/2', headers={'x-access-token': access_token})
        self.client.delete('/v1/admin/users/3', headers={'x-access-token': access_token})

        res = self.client.get('/v1/admin/users?page=1&limit=2',
                              headers={'x-access-token': access_token})
        self.assertEqual(res.status_code, 404)
