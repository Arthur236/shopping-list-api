"""
Tests for friend system
"""
import json
from flask_testing import TestCase
from app import create_app, db


class FriendTestCase(TestCase):
    """
    Tests for handling operations related to the friend system
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

        db.create_all()
        # Register Users
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

    def test_send_friend_request(self):
        """
        Test user can send friend request
        """
        access_token = self.login_user(self.user1)

        # Send another user a friend request
        res = self.client.post('/v1/friends',
                               headers={'x-access-token': access_token},
                               data={'friend_id': 3})
        self.assertEqual(res.status_code, 200)

    def test_send_request_twice(self):
        """
        Try to send request twice
        """
        access_token = self.login_user(self.user1)

        self.client.post('/v1/friends',
                         headers={'x-access-token': access_token},
                         data={'friend_id': 3})

        res = self.client.post('/v1/friends',
                               headers={'x-access-token': access_token},
                               data={'friend_id': 3})
        self.assertEqual(res.status_code, 401)

    def test_friend_id_send_request(self):
        """
        Use the wrong friend id format
        """
        access_token = self.login_user(self.user1)

        res = self.client.post('/v1/friends',
                               headers={'x-access-token': access_token},
                               data={'friend_id': 'one'})
        self.assertEqual(res.status_code, 401)

    def test_befriend_yourself(self):
        """
        Try to befriend yourself
        """
        access_token = self.login_user(self.user1)

        res = self.client.post('/v1/friends',
                               headers={'x-access-token': access_token},
                               data={'friend_id': 2})
        self.assertEqual(res.status_code, 403)

    def test_user_exists_send_request(self):
        """
        Try to befriend user that doesnt exist
        """
        access_token = self.login_user(self.user1)

        res = self.client.post('/v1/friends',
                               headers={'x-access-token': access_token},
                               data={'friend_id': 256})
        self.assertEqual(res.status_code, 401)

    def test_send_request_token_correct(self):
        """
        Test if token is correct format
        """
        res = self.client.post('/v1/friends', headers={'x-access-token': 'wrong_token'},
                               data={'friend_id': 3})
        self.assertEqual(res.status_code, 401)

    def test_send_request_token_present(self):
        """
        Test if token is present
        """
        res = self.client.post('/v1/friends', data={'friend_id': 3})
        self.assertEqual(res.status_code, 401)

    def send_user2_request(self):
        """
        Helper method to send a request to a second user
        """
        access_token = self.login_user(self.user1)

        self.client.post('/v1/friends',
                         headers={'x-access-token': access_token},
                         data={'friend_id': 3})

        # Login as other user
        login_res = self.client.post('/v1/auth/login', data=self.user2)
        access_token = json.loads(login_res.data.decode())['access_token']

        return access_token

    def test_accept_request(self):
        """
        Test user can accept friend request
        """
        # Send another user a friend request
        access_token = self.send_user2_request()

        res = self.client.put('/v1/friends/2',
                              headers={'x-access-token': access_token})
        self.assertEqual(res.status_code, 200)

    def test_accept_request_token_correct(self):
        """
        Test if token is correct format
        """
        res = self.client.put('/v1/friends/2', headers={'x-access-token': 'wrong_token'},
                              data={'friend_id': 3})
        self.assertEqual(res.status_code, 401)

    def test_accept_request_token_present(self):
        """
        Test if token is present
        """
        res = self.client.put('/v1/friends/2', data={'friend_id': 3})
        self.assertEqual(res.status_code, 401)

    def test_accept_request_twice(self):
        """
        Test user can accept friend request twice
        """
        # Send another user a friend request
        access_token = self.send_user2_request()

        self.client.put('/v1/friends/2',
                        headers={'x-access-token': access_token})
        res = self.client.put('/v1/friends/2',
                              headers={'x-access-token': access_token})
        self.assertEqual(res.status_code, 403)

    def test_friend_id_accept_param(self):
        """
        Use the wrong friend id format
        """
        access_token = self.send_user2_request()

        res = self.client.put('/v1/friends/one',
                              headers={'x-access-token': access_token})
        self.assertEqual(res.status_code, 401)

    def test_accept_non_existent_request(self):
        """
        Try to accept friend request that has not been sent
        """
        access_token = self.send_user2_request()

        res = self.client.put('/v1/friends/652',
                              headers={'x-access-token': access_token})
        self.assertEqual(res.status_code, 404)

    def test_to_send_request_to_friend(self):
        """
        Try to send a friend request to a user you're friends with
        """
        access_token = self.send_user2_request()

        self.client.put('/v1/friends/2',
                        headers={'x-access-token': access_token})
        res = self.client.post('/v1/friends',
                               headers={'x-access-token': access_token},
                               data={'friend_id': 2})
        self.assertEqual(res.status_code, 401)

    def test_befriend_user_twice(self):
        """
        Try to befriend user you are already friends with
        """
        access_token = self.send_user2_request()

        self.client.post('/v1/friends',
                         headers={'x-access-token': access_token},
                         data={'friend_id': 2})
        res = self.client.post('/v1/friends',
                               headers={'x-access-token': access_token},
                               data={'friend_id': 2})
        self.assertEqual(res.status_code, 401)

    def test_get_friends_when_none(self):
        """
        Test user can get all their friends
        """
        self.login_user(self.user1)

        # Send another user a friend request
        access_token = self.send_user2_request()

        # Try to get friends when you have none
        res = self.client.get('/v1/friends',
                              headers={'x-access-token': access_token})
        self.assertEqual(res.status_code, 404)

    def test_get_friend_id_wrong_format(self):
        """
        Use the wrong friend id format
        """
        access_token = self.send_user2_request()

        res = self.client.post('/v1/friends',
                               headers={'x-access-token': access_token},
                               data={'friend_id': 'one'})
        self.assertEqual(res.status_code, 401)

    def test_get_friends(self):
        """
        Get specific friend by their id
        """
        access_token = self.send_user2_request()

        self.client.put('/v1/friends/2',
                        headers={'x-access-token': access_token})

        res = self.client.get('/v1/friends', headers={'x-access-token': access_token})
        self.assertEqual(res.status_code, 200)

    def test_get_friends_token_correct(self):
        """
        Test if token is correct format
        """
        res = self.client.get('/v1/friends', headers={'x-access-token': 'wrong_token'},
                              data={'friend_id': 3})
        self.assertEqual(res.status_code, 401)

    def test_get_friends_token_present(self):
        """
        Test if token is present
        """
        res = self.client.get('/v1/friends', data={'friend_id': 3})
        self.assertEqual(res.status_code, 401)

    def test_pagination_limit_format(self):
        """
        Use the wrong limit and page data formats
        """
        access_token = self.send_user2_request()

        res = self.client.get('/v1/friends?page=one&limit=two',
                              headers={'x-access-token': access_token})
        self.assertEqual(res.status_code, 401)

    def test_search_non_existent_user(self):
        """
        Try to search friend that doesnt exist
        """
        access_token = self.send_user2_request()

        res = self.client.get('/v1/friends?q=vhjk', headers={'x-access-token': access_token})
        self.assertEqual(res.status_code, 404)

    def test_search_user(self):
        """
        Try to search friend that exists
        """
        access_token = self.send_user2_request()

        self.client.put('/v1/friends/2',
                        headers={'x-access-token': access_token})

        res = self.client.get('/v1/friends?q=user', headers={'x-access-token': access_token}, )
        self.assertEqual(res.status_code, 200)

    def test_remove_friend(self):
        """
        Test user can remove friend
        """
        access_token = self.send_user2_request()

        # Accept friend request
        self.client.put('/v1/friends/2',
                        headers={'x-access-token': access_token})

        res = self.client.delete('/v1/friends/2',
                                 headers={'x-access-token': access_token})
        self.assertEqual(res.status_code, 200)

    def test_remove_friend_token_correct(self):
        """
        Test if token is correct format
        """
        res = self.client.delete('/v1/friends/2', headers={'x-access-token': 'wrong_token'},
                                 data={'friend_id': 3})
        self.assertEqual(res.status_code, 401)

    def test_remove_friend_token_present(self):
        """
        Test if token is present
        """
        res = self.client.delete('/v1/friends/2', data={'friend_id': 3})
        self.assertEqual(res.status_code, 401)

    def test_friend_id_remove_format(self):
        """
        Use the wrong friend id format
        """
        access_token = self.send_user2_request()

        res = self.client.delete('/v1/friends/one',
                                 headers={'x-access-token': access_token})
        self.assertEqual(res.status_code, 401)

    def test_remove_user_not_friends(self):
        """
        Try to remove user you are not friends with
        """
        access_token = self.send_user2_request()

        res = self.client.delete('/v1/friends/2',
                                 headers={'x-access-token': access_token})
        self.assertEqual(res.status_code, 404)

    def test_requests_pagination_params_format(self):
        """
        Test if page and limit params are correct format
        """
        access_token = self.send_user2_request()

        res = self.client.get('/v1/friends/requests?page=one&limit=two',
                              headers={'x-access-token': access_token})
        self.assertEqual(res.status_code, 401)

    def test_search_non_existent_request(self):
        """
        Look for a friend request that doesnt exist
        """
        access_token = self.send_user2_request()

        res = self.client.get('/v1/friends/requests?q=hrhre',
                              headers={'x-access-token': access_token})
        self.assertEqual(res.status_code, 404)

    def test_search_existent_request(self):
        """
        Look for a friend request that exists
        """
        access_token = self.send_user2_request()

        res = self.client.get('/v1/friends/requests?q=us',
                              headers={'x-access-token': access_token})
        self.assertEqual(res.status_code, 200)

    def test_get_friend_requests_when_none(self):
        """
        Try to get friend requests when you have none
        """
        access_token = self.login_user(self.user1)

        res = self.client.get('/v1/friends/requests',
                              headers={'x-access-token': access_token})
        self.assertEqual(res.status_code, 404)

    def test_get_friend_requests(self):
        """
        Try to get friend requests when you have some
        """
        access_token = self.send_user2_request()

        res = self.client.get('/v1/friends/requests',
                              headers={'x-access-token': access_token})
        self.assertEqual(res.status_code, 200)

    def test_get_requests_token_correct(self):
        """
        Test if token is correct format
        """
        res = self.client.get('/v1/friends/requests', headers={'x-access-token': 'wrong_token'})
        self.assertEqual(res.status_code, 401)

    def test_get_requests_token_present(self):
        """
        Test if token is present
        """
        res = self.client.get('/v1/friends/requests')
        self.assertEqual(res.status_code, 401)
