import functools
import re
from flask import (
    Blueprint, flash, g, redirect, render_template, request, session, url_for, jsonify
)
from app.db import get_db
import sqlite3

bp = Blueprint('auth', __name__, url_prefix='/auth')


def format_name(raw: str) -> str:
    """Strip whitespace, remove all spaces, then capitalize correctly.

    Examples:
        "  ViSHal  " -> "Vishal"
        "jEREMY"     -> "Jeremy"
    """
    cleaned = re.sub(r'\s+', '', raw.strip())
    if not cleaned:
        return ''
    return cleaned[0].upper() + cleaned[1:].lower()


# ── JSON API endpoints (used by React frontend) ─────────────────────
# These routes are relative to the /auth url_prefix, so
# /api/login  →  /auth/api/login   (Vite proxies /api → Flask)
# We register them on the app directly in __init__.py instead.


def api_login():
    data = request.get_json(silent=True) or {}
    raw_name = data.get('name', '')
    name = format_name(raw_name)

    if not name:
        return jsonify({'error': 'Name is required.'}), 400

    db = get_db()

    # Look up or auto-register
    user = db.execute(
        'SELECT * FROM user WHERE username = ?', (name,)
    ).fetchone()

    if user is None:
        db.execute('INSERT INTO user (username) VALUES (?)', (name,))
        db.commit()
        user = db.execute(
            'SELECT * FROM user WHERE username = ?', (name,)
        ).fetchone()
        # Create stats row for new user
        db.execute(
            'INSERT INTO user_stats (user_id) VALUES (?)', (user['id'],)
        )
        db.commit()

    session.clear()
    session['user_id'] = user['id']

    return jsonify({
        'user': {
            'id': user['id'],
            'username': user['username'],
        }
    })


def api_me():
    if g.user is None:
        return jsonify({'error': 'Not authenticated.'}), 401
    return jsonify({
        'user': {
            'id': g.user['id'],
            'username': g.user['username'],
        }
    })


def api_logout():
    session.clear()
    return jsonify({'ok': True})


def api_stats():
    if g.user is None:
        return jsonify({'error': 'Not authenticated.'}), 401
    db = get_db()
    stats = db.execute(
        'SELECT cubes_created, cubes_frozen, trays_frozen FROM user_stats WHERE user_id = ?',
        (g.user['id'],)
    ).fetchone()
    if stats is None:
        return jsonify({'cubes_created': 0, 'cubes_frozen': 0, 'trays_frozen': 0})
    return jsonify({
        'cubes_created': stats['cubes_created'],
        'cubes_frozen': stats['cubes_frozen'],
        'trays_frozen': stats['trays_frozen'],
    })


def api_leaderboard():
    db = get_db()
    rows = db.execute(
        'SELECT u.username, s.cubes_created, s.cubes_frozen, s.trays_frozen '
        'FROM user u JOIN user_stats s ON u.id = s.user_id '
        'ORDER BY u.username'
    ).fetchall()
    return jsonify([
        {
            'username': row['username'],
            'cubes_created': row['cubes_created'],
            'cubes_frozen': row['cubes_frozen'],
            'trays_frozen': row['trays_frozen'],
        }
        for row in rows
    ])


# ── Session loader (runs before every request) ──────────────────────

@bp.before_app_request
def load_logged_in_user():
    user_id = session.get('user_id')

    if user_id is None:
        g.user = None
    else:
        try:
            g.user = get_db().execute(
                'SELECT * FROM user WHERE id = ?', (user_id,)
            ).fetchone()
        except sqlite3.Error:
            g.user = None
            session.clear()


# ── Legacy Jinja routes (kept for old UI) ────────────────────────────

@bp.route('/login', methods=('GET', 'POST'))
def login():
    if request.method == 'POST':
        username = request.form['username']
        error = None
        db = get_db()

        user = db.execute(
            'SELECT * FROM user WHERE username = ?', (username,)
        ).fetchone()

        if user is None:
            error = 'Unauthorized user.'
            flash(error)
            return redirect(url_for('auth.unauthorized'))

        session.clear()
        session['user_id'] = user['id']
        return redirect(url_for('ice'))

    return render_template('auth/login.html')

@bp.route('/unathorized')
def unauthorized():
    return render_template('auth/unauthorized.html')

@bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))