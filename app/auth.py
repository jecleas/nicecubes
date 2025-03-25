import functools
from flask import (
    Blueprint, flash, g, redirect, render_template, request, session, url_for
)
from app.db import get_db
import sqlite3

bp = Blueprint('auth', __name__, url_prefix='/auth')

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

@bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))