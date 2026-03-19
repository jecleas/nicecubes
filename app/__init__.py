from flask import Flask, render_template, send_from_directory
import os

def create_app(test_config=None):
    app = Flask(__name__, instance_relative_config=True)

    # Check if the React production build exists
    dist_dir = os.path.join(os.path.dirname(__file__), 'static', 'dist')
    has_frontend_build = os.path.isdir(dist_dir)

    app.config.from_mapping(
        SECRET_KEY=os.environ.get('SECRET_KEY', 'dev'),
        DATABASE=os.environ.get('DATABASE_PATH', os.path.join(app.instance_path, 'app.sqlite')),
    )

    if test_config is None: # Load the instance config, if it exists, when not testing
        app.config.from_pyfile('config.py', silent=True)
    else: # Load the test config if passed in
        app.config.from_mapping(test_config)

    try: # Ensure the instance folder exists
        os.makedirs(app.instance_path)
    except OSError:
        pass

    if has_frontend_build:
        # Production: serve React SPA from the Vite build output
        @app.route('/', defaults={'path': ''})
        @app.route('/<path:path>')
        def serve_react(path):
            # Serve static assets (JS, CSS, images) if the file exists
            file_path = os.path.join(dist_dir, path)
            if path and os.path.isfile(file_path):
                return send_from_directory(dist_dir, path)
            # Otherwise serve index.html (SPA catch-all)
            return send_from_directory(dist_dir, 'index.html')
    else:
        # Local dev: serve Jinja templates (React runs via Vite dev server)
        @app.route('/hello')
        def hello():
            return 'Hello, World!'

        @app.route('/')
        def index():
            return render_template('index.html')

        @app.route('/ice')
        def ice():
            return render_template('ice.html')

    from . import db
    db.init_app(app)

    from . import auth
    app.register_blueprint(auth.bp)

    # Register auth API routes at the app level (not under /auth prefix)
    app.add_url_rule('/api/auth/login', 'api_auth_login', auth.api_login, methods=['POST'])
    app.add_url_rule('/api/auth/me', 'api_auth_me', auth.api_me)
    app.add_url_rule('/api/auth/logout', 'api_auth_logout', auth.api_logout, methods=['POST'])
    app.add_url_rule('/api/auth/stats', 'api_auth_stats', auth.api_stats)
    app.add_url_rule('/api/leaderboard', 'api_leaderboard', auth.api_leaderboard)

    from . import ice # Import and register the ice blueprint
    app.register_blueprint(ice.bp)

    return app
