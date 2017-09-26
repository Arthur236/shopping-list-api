"""
Tests for friend system
"""
import unittest
import json
from app import create_app, db


class FriendTestCase(unittest.TestCase):
    """
    Tests for handling operations related to the friend system
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

        with self.app.app_context():
            # create all tables
            db.session.close()
            db.drop_all()
            db.create_all()

    def setup_users(self):
        # create user by making a POST request
        res = self.client().post('/auth/register', data=self.user1)
        self.assertEqual(res.status_code, 201)
        res = self.client().post('/auth/register', data=self.user2)
        self.assertEqual(res.status_code, 201)

        login_res = self.client().post('/auth/login', data={
            'email': 'user1@gmail.com',
            'password': 'password'
        })
        self.assertEqual(login_res.status_code, 200)
        access_token = json.loads(login_res.data.decode())['access-token']

        return access_token

    def test_add_friend(self):
        """
        Test user can send friend request
        """
        access_token = self.setup_users()

        # Send another user a friend request
        res = self.client().post('/friends',
                                 headers={'x-access-token': access_token}, data={'friend_id': 3})
        self.assertEqual(res.status_code, 200)

    def test_accept_request(self):
        """
        Test user can accept friend request
        """
        access_token = self.setup_users()

        # Send another user a friend request
        res = self.client().post('/friends',
                                 headers={'x-access-token': access_token}, data={'friend_id': 3})
        self.assertEqual(res.status_code, 200)

        # Login as other user
        login_res = self.client().post('/auth/login', data={
            'email': 'user2@gmail.com',
            'password': 'password'
        })
        self.assertEqual(login_res.status_code, 200)
        access_token = json.loads(login_res.data.decode())['access-token']

        # Accept friend request
        res = self.client().put('/friends',
                                headers={'x-access-token': access_token}, data={'friend_id': 2})
        self.assertEqual(res.status_code, 200)

    def test_get_friends(self):
        """
        Test user can get all their friends
        """
        access_token = self.setup_users()

        # Send another user a friend request
        res = self.client().post('/friends',
                                 headers={'x-access-token': access_token}, data={'friend_id': 3})
        self.assertEqual(res.status_code, 200)

        # Login as other user
        login_res = self.client().post('/auth/login', data={
            'email': 'user2@gmail.com',
            'password': 'password'
        })
        self.assertEqual(login_res.status_code, 200)
        access_token = json.loads(login_res.data.decode())['access-token']

        # Accept friend request
        res = self.client().put('/friends',
                                headers={'x-access-token': access_token}, data={'friend_id': 2})
        self.assertEqual(res.status_code, 200)

        # Get user after they have accepted request
        res = self.client().get('/friends', headers={'x-access-token': access_token})
        self.assertEqual(res.status_code, 200)

    def test_remove_friend(self):
        """
        Test user can remove friend
        """
        access_token = self.setup_users()

        # Send another user a friend request
        res = self.client().post('/friends',
                                 headers={'x-access-token': access_token}, data={'friend_id': 3})
        self.assertEqual(res.status_code, 200)

        # Login as other user
        login_res = self.client().post('/auth/login', data={
            'email': 'user2@gmail.com',
            'password': 'password'
        })
        self.assertEqual(login_res.status_code, 200)
        access_token = json.loads(login_res.data.decode())['access-token']

        # Accept friend request
        res = self.client().put('/friends',
                                headers={'x-access-token': access_token}, data={'friend_id': 2})
        self.assertEqual(res.status_code, 200)

        # Remove friend
        res = self.client().delete('/friends',
                                   headers={'x-access-token': access_token}, data={'friend_id': 2})
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
