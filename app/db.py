from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from datetime import datetime

db = SQLAlchemy()
migrate = Migrate()

def init_db():
    """Initialize the database with seed data."""
    from app.models import User  # Import here to avoid circular imports
    
    with db.session.begin():
        if not User.query.first():
            users = [
                User(username="Jeremy"),
                User(username="Mia"),
                User(username="Joanne"),
                User(username="Olivia"),
                User(username="Alana"),
                User(username="Thomas")
            ]
            db.session.add_all(users)

def init_app(app):
    """Initialize database, migrations and seed data."""
    app.config['SQLALCHEMY_DATABASE_URI'] = app.config.get('DATABASE_URL')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    db.init_app(app)
    migrate.init_app(app, db)
    
    with app.app_context():
        db.create_all()
        init_db()