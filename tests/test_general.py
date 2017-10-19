"""
General application tests
"""
import unittest
from app import create_app, db


class GeneralTestCase(unittest.TestCase):
    """
    General tests
    """

    def setUp(self):
        """
        Set up test variables
        """
        self.app = create_app(config_name="testing")
        # Initialize the test client
        self.client = self.app.test_client

        with self.app.app_context():
            # Create all tables
            db.session.close()
            db.drop_all()
            db.create_all()

    def test_non_existent_url(self):
        """
        Try to access url that doesnt exist
        """
        res = self.client().get('/v1/auth/register/hei')
        self.assertEqual(res.status_code, 404)

    def test_home(self):
        """
        Test whether home redirects correctly
        """
        res = self.client().get('/v1')
        self.assertEqual(res.status_code, 301)

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
