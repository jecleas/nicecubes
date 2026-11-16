import os
import sqlite3
import click
from flask import current_app, g
from flask.cli import with_appcontext

# Trays the UI shows. Inserted if missing; existing rows are left alone.
TRAY_IDS = ('tray1', 'tray2')


def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect(
            current_app.config['DATABASE'],
            detect_types=sqlite3.PARSE_DECLTYPES
        )
        g.db.row_factory = sqlite3.Row
        g.db.execute('PRAGMA busy_timeout = 5000')

    return g.db

def close_db(e=None):
    db = g.pop('db', None)

    if db is not None:
        db.close()

def _ensure_database_directory(database_path):
    """Create the parent directory for a file-backed SQLite database.

    Fly mounts an empty volume at /data on first boot, and local dev may point
    DATABASE_PATH at a folder that does not exist yet. :memory: and URI
    databases have no directory to create.
    """
    if not database_path or database_path == ':memory:' or database_path.startswith('file:'):
        return

    directory = os.path.dirname(os.path.abspath(database_path))
    if directory:
        os.makedirs(directory, exist_ok=True)

def seed_trays(db):
    """Insert the shared trays when they are missing. Does not commit.

    Returns True when at least one row was inserted.
    """
    inserted = False
    for tray_id in TRAY_IDS:
        cursor = db.execute(
            '''
            INSERT OR IGNORE INTO tray_state
                (id, active_cubes, is_frozen, frozen_at, expires_at, revision)
            VALUES (?, '[]', 0, NULL, NULL, 0)
            ''',
            (tray_id,),
        )
        if cursor.rowcount > 0:
            inserted = True
    return inserted

def _apply_schema(db):
    with current_app.open_resource('schema.sql') as f:
        db.executescript(f.read().decode('utf8'))

def ensure_database(app):
    """Create the database directory, tables, and default trays.

    Safe on every boot. Uses CREATE TABLE IF NOT EXISTS and INSERT OR IGNORE,
    so users, stats, and tray contents already on the Fly volume are kept.
    """
    _ensure_database_directory(app.config['DATABASE'])

    with app.app_context():
        db = get_db()
        _apply_schema(db)
        seed_trays(db)
        db.commit()

def init_db():
    """Drop every table, recreate the schema, and seed empty trays."""
    db = get_db()
    db.executescript(
        '''
        DROP TABLE IF EXISTS tray_state;
        DROP TABLE IF EXISTS user_stats;
        DROP TABLE IF EXISTS user;
        '''
    )
    _apply_schema(db)
    seed_trays(db)
    db.commit()

@click.command('init-db')
@with_appcontext
def init_db_command():
    """Clear the existing data and create new tables."""
    init_db()
    click.echo('Initialized the database.')

def init_app(app):
    app.teardown_appcontext(close_db)
    app.cli.add_command(init_db_command)
    ensure_database(app)
