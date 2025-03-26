import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app
from app import db

app = create_app()

with app.app_context():
    try:
        db.session.execute('SELECT 1')
        print("Successfully connected to AWS RDS PostgreSQL!")
    except Exception as e:
        print(f"Connection failed: {e}")