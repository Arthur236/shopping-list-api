"""
Tests for sharing system
"""
import unittest
import json
from app import create_app, db


class ShareTestCase(unittest.TestCase):
    """
    Tests for handling operations related to the sharing system
    """

    def setUp(self):
        """
        Set up test variables
        """
        self.app = create_app(config_name="testing")
        # initialize the test client
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
        self.shopping_list = {
            'name': 'Test shopping list',
            'description': 'Test description'
        }

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

        # Create a list for sharing
        res = self.client().post('/shopping_lists', headers={'x-access-token': access_token},
                                 data=self.shopping_list)
        self.assertEqual(res.status_code, 201)

        # Send friend request
        res = self.client().post('/friends',
                                 headers={'x-access-token': access_token}, data={'friend_id': 3})
        self.assertEqual(res.status_code, 200)

        # Login as other user and accept friend request
        login_res = self.client().post('/auth/login', data=self.user2)
        self.assertEqual(login_res.status_code, 200)
        access_token = json.loads(login_res.data.decode())['access-token']

        # Accept friend request
        res = self.client().put('/friends',
                                headers={'x-access-token': access_token}, data={'friend_id': 2})
        self.assertEqual(res.status_code, 200)

        # Log in as first user
        login_res = self.client().post('/auth/login', data=self.user1)
        self.assertEqual(login_res.status_code, 200)
        access_token = json.loads(login_res.data.decode())['access-token']

        return access_token

    def test_share_list(self):
        """
        Test whether a user can share a list with another user
        """
        access_token = self.setup_users()

        # Share list
        res = self.client().post('/shopping_lists/share',
                                 headers={'x-access-token': access_token},
                                 data={'list_id': 1, 'friend_id': 3})
        self.assertEqual(res.status_code, 200)

    def test_get_shared_lists(self):
        """
        Test whether a user can get shared shopping lists
        """
        access_token = self.setup_users()

        # Share list
        res = self.client().post('/shopping_lists/share',
                                 headers={'x-access-token': access_token},
                                 data={'list_id': 1, 'friend_id': 3})
        self.assertEqual(res.status_code, 200)

        # Get lists
        res = self.client().get('/shopping_lists/share', headers={'x-access-token': access_token})
        self.assertEqual(res.status_code, 200)

    def test_stop_sharing_list(self):
        """
        Test whether a user can stop sharing a shopping list
        """
        access_token = self.setup_users()

        # Share list
        res = self.client().post('/shopping_lists/share',
                                 headers={'x-access-token': access_token},
                                 data={'list_id': 1, 'friend_id': 3})
        self.assertEqual(res.status_code, 200)

        # Stop sharing
        res = self.client().delete('/shopping_lists/share',
                                   headers={'x-access-token': access_token},
                                   data={'list_id': 1, 'friend_id': 3})
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
