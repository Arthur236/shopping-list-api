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
        """
        Register and log in users
        """
        # create user by making a POST request
        res = self.client().post('/v1/auth/register', data=self.user1)
        self.assertEqual(res.status_code, 201)
        res = self.client().post('/v1/auth/register', data=self.user2)
        self.assertEqual(res.status_code, 201)

        login_res = self.client().post('/v1/auth/login', data={
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
        res = self.client().post('/v1/friends',
                                 headers={'x-access-token': access_token}, data={'friend_id': 3})
        self.assertEqual(res.status_code, 200)

        # Try to send request twice
        res = self.client().post('/v1/friends',
                                 headers={'x-access-token': access_token}, data={'friend_id': 3})
        self.assertEqual(res.status_code, 401)

        # Use the wrong friend id format
        res = self.client().post('/v1/friends',
                                 headers={'x-access-token': access_token},
                                 data={'friend_id': 'one'})
        self.assertEqual(res.status_code, 401)

        # Try to befriend yourself
        res = self.client().post('/v1/friends',
                                 headers={'x-access-token': access_token}, data={'friend_id': 2})
        self.assertEqual(res.status_code, 403)

        # Try to befriend user that doesnt exist
        res = self.client().post('/v1/friends',
                                 headers={'x-access-token': access_token}, data={'friend_id': 256})
        self.assertEqual(res.status_code, 401)

    def test_accept_request(self):
        """
        Test user can accept friend request
        """
        access_token = self.setup_users()

        # Send another user a friend request
        res = self.client().post('/v1/friends',
                                 headers={'x-access-token': access_token}, data={'friend_id': 3})
        self.assertEqual(res.status_code, 200)

        # Login as other user
        login_res = self.client().post('/v1/auth/login', data=self.user2)
        self.assertEqual(login_res.status_code, 200)
        access_token = json.loads(login_res.data.decode())['access-token']

        # Use the wrong friend id format
        res = self.client().put('/v1/friends/one',
                                headers={'x-access-token': access_token})
        self.assertEqual(res.status_code, 401)

        # Try to accept friend request that has not been sent
        res = self.client().put('/v1/friends/652',
                                headers={'x-access-token': access_token})
        self.assertEqual(res.status_code, 404)

        # Accept friend request
        res = self.client().put('/v1/friends/2',
                                headers={'x-access-token': access_token})
        self.assertEqual(res.status_code, 200)

        # Try to accept friend request twice
        res = self.client().put('/v1/friends/2',
                                headers={'x-access-token': access_token})
        self.assertEqual(res.status_code, 403)

        # Try to befriend user you are already friends with
        res = self.client().post('/v1/friends',
                                 headers={'x-access-token': access_token}, data={'friend_id': 2})
        self.assertEqual(res.status_code, 401)

    def test_get_friends(self):
        """
        Test user can get all their friends
        """
        access_token = self.setup_users()

        # Send another user a friend request
        res = self.client().post('/v1/friends',
                                 headers={'x-access-token': access_token}, data={'friend_id': 3})
        self.assertEqual(res.status_code, 200)

        # Login as other user
        login_res = self.client().post('/v1/auth/login', data=self.user2)
        self.assertEqual(login_res.status_code, 200)
        access_token = json.loads(login_res.data.decode())['access-token']

        # Try to get friends when you have none
        res = self.client().get('/v1/friends', headers={'x-access-token': access_token})
        self.assertEqual(res.status_code, 404)

        # Use the wrong friend id format
        res = self.client().post('/v1/friends',
                                 headers={'x-access-token': access_token},
                                 data={'friend_id': 'one'})
        self.assertEqual(res.status_code, 401)

        # Accept friend request
        res = self.client().put('/v1/friends/2',
                                headers={'x-access-token': access_token})
        self.assertEqual(res.status_code, 200)

        # Get user after they have accepted request
        res = self.client().get('/v1/friends', headers={'x-access-token': access_token})
        self.assertEqual(res.status_code, 200)

        # Use the wrong limit and page data formats
        res = self.client().get('/v1/friends?page=one&limit=two',
                                headers={'x-access-token': access_token})
        self.assertEqual(res.status_code, 401)

        # Try to search friend that doesnt exist
        res = self.client().get('/v1/friends?q=vhjk', headers={'x-access-token': access_token})
        self.assertEqual(res.status_code, 404)

        # Try to search friend that exists
        res = self.client().get('/v1/friends?q=user', headers={'x-access-token': access_token}, )
        self.assertEqual(res.status_code, 200)

    def test_remove_friend(self):
        """
        Test user can remove friend
        """
        access_token = self.setup_users()

        # Send another user a friend request
        res = self.client().post('/v1/friends',
                                 headers={'x-access-token': access_token}, data={'friend_id': 3})
        self.assertEqual(res.status_code, 200)

        # Login as other user
        login_res = self.client().post('/v1/auth/login', data=self.user2)
        self.assertEqual(login_res.status_code, 200)
        access_token = json.loads(login_res.data.decode())['access-token']

        # Accept friend request
        res = self.client().put('/v1/friends/2',
                                headers={'x-access-token': access_token})
        self.assertEqual(res.status_code, 200)

        # Use the wrong friend id format
        res = self.client().delete('/v1/friends/one',
                                   headers={'x-access-token': access_token})
        self.assertEqual(res.status_code, 401)

        # Remove friend
        res = self.client().delete('/v1/friends/2',
                                   headers={'x-access-token': access_token})
        self.assertEqual(res.status_code, 200)

        # Try to remove user you are not friends with
        res = self.client().delete('/v1/friends/2',
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
