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
        self.shopping_list_item = \
            {'list_id': 1, 'name': 'Tomatoes', 'quantity': 20, 'unit_price': 5}
        self.shopping_list_item2 = \
            {'list_id': 1, 'name': 'Broccoli', 'quantity': 20, 'unit_price': 5}

        with self.app.app_context():
            # Create all tables
            db.session.close()
            db.drop_all()
            db.create_all()
            
            # Register users
            self.client().post('/v1/auth/register', data=self.user1)
            self.client().post('/v1/auth/register', data=self.user2)
            
            # Create list for user 1 and add items
            login_res = self.client().post('/v1/auth/login', data=self.user1)
            access_token = json.loads(login_res.data.decode())['access-token']
            self.client().post('/v1/shopping_lists', headers={'x-access-token': access_token}, 
                               data=self.shopping_list)

            self.client().post('/v1/shopping_lists/1/items', 
                               headers={'x-access-token': access_token},
                               data=self.shopping_list_item)
            self.client().post('/v1/shopping_lists/1/items',
                               headers={'x-access-token': access_token},
                               data=self.shopping_list_item2)
            
            # Send friend request
            self.client().post('/v1/friends', 
                               headers={'x-access-token': access_token},
                               data={'friend_id': 3})
            
            # Accept request
            login_res = self.client().post('/v1/auth/login', data=self.user2)
            access_token = json.loads(login_res.data.decode())['access-token']
            self.client().put('/v1/friends/2',
                              headers={'x-access-token': access_token})

    def login_user(self, user):
        """
        Helper function to login user
        """
        login_res = self.client().post('/v1/auth/login', data=user)
        access_token = json.loads(login_res.data.decode())['access-token']

        return access_token

    def test_share_list(self):
        """
        Test whether a user can share a list with another user
        """
        access_token = self.login_user(self.user1)

        # Share list
        res = self.client().post('/v1/shopping_lists/share',
                                 headers={'x-access-token': access_token},
                                 data={'list_id': 1, 'friend_id': 3})
        self.assertEqual(res.status_code, 200)

    def share_list(self):
        """
        Helper function for sharing list
        """
        access_token = self.login_user(self.user1)

        result = self.client().post('/v1/shopping_lists/share',
                                    headers={'x-access-token': access_token},
                                    data={'list_id': 1, 'friend_id': 3})

        return result

    def test_share_list_twice(self):
        """
        Try to share list twice
        """
        self.share_list()
        res = self.share_list()

        self.assertEqual(res.status_code, 401)

    def test_share_with_non_friend(self):
        """
        Try to share list with non friend
        """
        access_token = self.login_user(self.user1)

        res = self.client().post('/v1/shopping_lists/share',
                                 headers={'x-access-token': access_token},
                                 data={'list_id': 1, 'friend_id': 368})
        self.assertEqual(res.status_code, 401)

    def test_share_params(self):
        """
        Use the wrong friend id and list id formats
        """
        access_token = self.login_user(self.user1)

        res = self.client().post('/v1/shopping_lists/share',
                                 headers={'x-access-token': access_token},
                                 data={'friend_id': 'one', 'list_id': 'one'})
        self.assertEqual(res.status_code, 401)

    def test_get_shared_lists_when_none(self):
        """
        Try to get shared lists when none have been shared
        """
        access_token = self.login_user(self.user1)

        # Try to get lists when non are shared
        res = self.client().get('/v1/shopping_lists/share',
                                headers={'x-access-token': access_token})
        self.assertEqual(res.status_code, 404)

    def test_get_shared_lists(self):
        """
        Get shared lists
        """
        self.share_list()
        access_token = self.login_user(self.user1)

        # Get lists
        res = self.client().get('/v1/shopping_lists/share',
                                headers={'x-access-token': access_token})
        self.assertEqual(res.status_code, 200)

    def test_get_shared_list_params(self):
        """
        Use the wrong limit and page data formats
        """
        access_token = self.login_user(self.user1)

        res = self.client().get('/v1/shopping_lists/share?page=one&limit=two',
                                headers={'x-access-token': access_token})
        self.assertEqual(res.status_code, 401)

    def test_search_non_existent_shared_list(self):
        """
        Try to search list that doesnt exist
        """
        access_token = self.login_user(self.user1)

        res = self.client().get('/v1/shopping_lists/share?q=yuujk',
                                headers={'x-access-token': access_token})
        self.assertEqual(res.status_code, 404)

    def test_search_existent_shared_list(self):
        """
        Try to search list that exists
        """
        access_token = self.login_user(self.user1)

        self.share_list()
        res = self.client().get('/v1/shopping_lists/share?q=test',
                                headers={'x-access-token': access_token})
        self.assertEqual(res.status_code, 200)

    def test_get_shared_list_items(self):
        """
        Test whether a user can get items in a shared list
        """
        self.share_list()
        access_token = self.login_user(self.user1)

        # Get list items
        res = self.client().get('/v1/shopping_lists/share/1/items',
                                headers={'x-access-token': access_token})
        self.assertEqual(res.status_code, 200)

    def test_get_shared_list_pagination_params(self):
        """
        Use the wrong limit and page data formats
        """
        self.share_list()
        access_token = self.login_user(self.user1)

        res = self.client().get('/v1/shopping_lists/share/1/items?page=one&limit=two',
                                headers={'x-access-token': access_token})
        self.assertEqual(res.status_code, 401)

    def test_stop_sharing_list(self):
        """
        Test whether a user can stop sharing a shopping list
        """
        self.share_list()
        access_token = self.login_user(self.user1)

        res = self.client().delete('/v1/shopping_lists/share/1',
                                   headers={'x-access-token': access_token}, 
                                   data={'friend_id': 3})
        self.assertEqual(res.status_code, 200)

    def test_stop_sharing_non_shared_list(self):
        """
        Try to remove a list that's not shared
        """
        access_token = self.login_user(self.user1)

        res = self.client().delete('/v1/shopping_lists/share/1',
                                   headers={'x-access-token': access_token}, 
                                   data={'friend_id': 3})
        self.assertEqual(res.status_code, 404)

    def test_stop_shared_params(self):
        """
        Use the wrong list id formats
        """
        self.share_list()
        access_token = self.login_user(self.user1)

        res = self.client().delete('/v1/shopping_lists/share/one',
                                   headers={'x-access-token': access_token},
                                   data={'friend_id': 3})
        self.assertEqual(res.status_code, 401)

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
