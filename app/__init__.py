from flask import Flask, render_template
from .auth import login_required

import os

def create_app(test_config=None):
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY='dev',
        DATABASE=os.path.join(app.instance_path, 'app.sqlite'),
    )

    if test_config is None: # Load the instance config, if it exists, when not testing
        app.config.from_pyfile('config.py', silent=True)
    else: # Load the test config if passed in
        app.config.from_mapping(test_config)

    try: # Ensure the instance folder exists
        os.makedirs(app.instance_path)
    except OSError:
        pass

    @app.route('/hello')
    def hello():
        return 'Hello, World!'
    
    @app.route('/')
    def index():
        return render_template('index.html')

    @app.route('/ice')
    @login_required
    def ice():
        return render_template('ice.html')

    from . import db
    db.init_app(app)

    from . import auth
    app.register_blueprint(auth.bp)

    from . import ice # Import and register the ice blueprint
    app.register_blueprint(ice.bp)

    return app
