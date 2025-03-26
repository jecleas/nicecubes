from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from dotenv import load_dotenv
import os

load_dotenv()

def create_app(test_config=None):
    app = Flask(__name__, instance_relative_config=True)
    
    if test_config is None: # Load the instance config, if it exists, when not testing
        app.config['DATABASE_URL'] = os.getenv('DATABASE_URL')
    else: # Load the test config if passed in
        app.config.from_mapping(test_config)

    try: # Ensure the instance folder exists
        os.makedirs(app.instance_path)
    except OSError:
        pass

    from . import db
    db.init_app(app)
    #migrate.init_app(app, db)

    from . import auth #Import the auth blueprint
    app.register_blueprint(auth.bp)

    from . import ice # Import and register the ice blueprint
    app.register_blueprint(ice.bp)

    @app.route('/hello')
    def hello():
        return 'Hello, World!'
    
    @app.route('/')
    def index():
        return render_template('index.html')

    return app
