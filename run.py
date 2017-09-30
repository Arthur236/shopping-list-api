"""
Running the application
"""
import os
from app import create_app

config_name = os.getenv('APP_SETTINGS')  # config_name = "development"
app = create_app(config_name)
app.config['APPLICATION_ROOT'] = '/v1'

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run('', port=port)
