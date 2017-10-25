"""
General application tests
"""
from flask_testing import TestCase
from app import create_app, db


class GeneralTestCase(TestCase):
    """
    General tests
    """
    
    def create_app(self):
        app = create_app(config_name="testing")
        return app

    def setUp(self):
        """
        Set up test variables
        """
        db.create_all()
        
    def tearDown(self):
        """
        Delete all initialized variables
        """
        db.session.remove()
        db.drop_all()

    def test_non_existent_url(self):
        """
        Try to access url that doesnt exist
        """
        res = self.client.get('/v1/auth/register/hei')
        self.assertEqual(res.status_code, 404)

    def test_home(self):
        """
        Test whether home redirects correctly
        """
        res = self.client.get('/v1/')
        self.assertEqual(res.status_code, 302)
