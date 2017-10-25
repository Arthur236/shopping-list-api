"""
Initialing the application
"""
from flask_api import FlaskAPI
from flask_sqlalchemy import SQLAlchemy
from flask import request, jsonify, redirect

# Local import
from instance.config import app_config

# Initialize sql-alchemy
db = SQLAlchemy()


# Middleware for path prefixing
class PrefixMiddleware(object):
    """
    Middleware class for url prefixing
    """

    def __init__(self, app, prefix=''):
        self.app = app
        self.prefix = prefix

    def __call__(self, environ, start_response):

        if environ['PATH_INFO'].startswith(self.prefix):
            environ['PATH_INFO'] = environ['PATH_INFO'][len(self.prefix):]
            environ['SCRIPT_NAME'] = self.prefix
            return self.app(environ, start_response)

        start_response('404', [('Content-Type', 'text/plain')])
        return ["Ooops! Looks like we don't recognize this url.".encode()]


def create_app(config_name):
    """
    Initialize the application
    """
    from app.models import User, ShoppingList, ShoppingListItem, PasswordReset, Friend, SharedList

    app = FlaskAPI(__name__, instance_relative_config=True)
    app.config.from_object(app_config[config_name])
    app.config.from_pyfile('config.py')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.wsgi_app = PrefixMiddleware(app.wsgi_app, prefix='/v1')
    db.init_app(app)

    @app.before_first_request
    def insert_initial_user(*args, **kwargs):
        """
        Add admin user when tables are migrated
        """
        admin_user = User.query.all()
        if not admin_user:
            db.session.add(User(username='admin', email='admin@gmail.com', password='admin123'))
            db.session.commit()
            admin_user = User.query.filter_by(email='admin@gmail.com').first()
            admin_user.admin = True
            admin_user.save()

    @app.errorhandler(404)
    def error_404(error):
        """
        Handles 404 errors
        """
        message = {
            'status': 404,
            'message': 'The resource at {}, cannot be found.'.format(request.url)
        }
        response = jsonify(message)
        response.status_code = 404

        return response

    @app.errorhandler(500)
    def error_500(error):
        """
        Handles 500 errors
        """
        message = {
            'status': 500,
            'message': 'Looks like something went wrong. '
                       'Our team of experts is working to fix this.'
        }
        response = jsonify(message)
        response.status_code = 500

        return response

    @app.route('/', methods=['GET'])
    def index():
        """
        Redirect user to api documentation
        """
        return redirect('http://docs.shoppinglistapi4.apiary.io')

    # Import the blueprints and register them on the app
    from .auth import auth_blueprint
    from .user import user_blueprint
    from .admin import admin_blueprint
    from .shopping_list import shopping_list_blueprint
    from .item import item_blueprint
    from .friend import friend_blueprint
    from .share import share_blueprint
    app.register_blueprint(auth_blueprint)
    app.register_blueprint(user_blueprint)
    app.register_blueprint(admin_blueprint)
    app.register_blueprint(shopping_list_blueprint)
    app.register_blueprint(item_blueprint)
    app.register_blueprint(friend_blueprint)
    app.register_blueprint(share_blueprint)

    return app
