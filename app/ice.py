import json
from datetime import datetime, timedelta
from threading import Lock

from flask import Blueprint, jsonify, request, g

from app.db import get_db, seed_trays

bp = Blueprint('ice', __name__)

# SQLite is the source of truth (see DATABASE_PATH). This lock only covers
# the read-modify-write inside one process so two requests cannot drop a cube.
tray_states_lock = Lock()


def _parse_dt(value):
    if not value:
        return None
    if isinstance(value, datetime):
        return value
    return datetime.fromisoformat(value)


def _format_dt(value):
    if value is None:
        return None
    return value.isoformat()


def _row_to_state(row):
    return {
        'active_cubes': set(json.loads(row['active_cubes'] or '[]')),
        'is_frozen': bool(row['is_frozen']),
        'frozen_at': _parse_dt(row['frozen_at']),
        'expires_at': _parse_dt(row['expires_at']),
        'revision': row['revision'],
    }


def _load_tray_state(db, tray_id):
    row = db.execute(
        '''
        SELECT id, active_cubes, is_frozen, frozen_at, expires_at, revision
        FROM tray_state
        WHERE id = ?
        ''',
        (tray_id,),
    ).fetchone()
    if row is None:
        return None
    return _row_to_state(row)


def _save_tray_state(db, tray_id, state):
    db.execute(
        '''
        UPDATE tray_state
        SET active_cubes = ?, is_frozen = ?, frozen_at = ?, expires_at = ?, revision = ?
        WHERE id = ?
        ''',
        (
            json.dumps(sorted(state['active_cubes'])),
            1 if state['is_frozen'] else 0,
            _format_dt(state['frozen_at']),
            _format_dt(state['expires_at']),
            state['revision'],
            tray_id,
        ),
    )


def prune_expired_tray_state(state, current_time):
    if state['expires_at'] and state['expires_at'] <= current_time:
        state['is_frozen'] = False
        state['frozen_at'] = None
        state['expires_at'] = None
        state['revision'] += 1
        return True
    return False


def serialize_tray_state(state):
    return {
        'active_cubes': sorted(state['active_cubes']),
        'is_frozen': state['is_frozen'],
        'frozen_at': state['frozen_at'].isoformat() if state['frozen_at'] else None,
        'expires_at': state['expires_at'].isoformat() if state['expires_at'] else None,
        'revision': state['revision'],
    }


def _with_tray(tray_id, current_time, mutator):
    """Load one tray, drop an expired freeze, apply mutator, and persist changes.

    mutator(db, state) returns True when it changes the tray (or writes other
    rows that must be committed with it). Returns the serialized snapshot, or
    None when the tray id is unknown.
    """
    db = get_db()
    if seed_trays(db):
        db.commit()

    state = _load_tray_state(db, tray_id)
    if state is None:
        return None

    changed = prune_expired_tray_state(state, current_time)
    if mutator is not None and mutator(db, state):
        changed = True
    if changed:
        _save_tray_state(db, tray_id, state)
        db.commit()
    return serialize_tray_state(state)


def _toggle_cube(db, state, cube_index):
    if state['is_frozen']:
        return False

    if cube_index in state['active_cubes']:
        state['active_cubes'].remove(cube_index)
    else:
        state['active_cubes'].add(cube_index)
        db.execute(
            'UPDATE user_stats SET cubes_created = cubes_created + 1 WHERE user_id = ?',
            (g.user['id'],)
        )
    state['revision'] += 1
    return True


def _freeze_tray(db, state, current_time):
    state['is_frozen'] = True
    state['frozen_at'] = current_time
    state['expires_at'] = current_time + timedelta(hours=4)
    state['revision'] += 1

    frozen_cube_count = len(state['active_cubes'])
    db.execute(
        'UPDATE user_stats SET trays_frozen = trays_frozen + 1, cubes_frozen = cubes_frozen + ? WHERE user_id = ?',
        (frozen_cube_count, g.user['id'])
    )
    return True


@bp.route('/api/toggle-cube', methods=['POST'])
def toggle_cube():
    if g.user is None:
        return jsonify({'error': 'Not authenticated.'}), 401

    data = request.get_json()
    tray_id = data['trayId']
    cube_index = data['cubeIndex']

    with tray_states_lock:
        snapshot = _with_tray(
            tray_id,
            datetime.now(),
            lambda db, state: _toggle_cube(db, state, cube_index),
        )

    if snapshot is None:
        return jsonify({'error': 'Unknown tray.'}), 404
    return jsonify(snapshot)

@bp.route('/api/freeze-tray', methods=['POST'])
def freeze_tray():
    if g.user is None:
        return jsonify({'error': 'Not authenticated.'}), 401

    data = request.get_json()
    tray_id = data['trayId']
    current_time = datetime.now()

    with tray_states_lock:
        snapshot = _with_tray(
            tray_id,
            current_time,
            lambda db, state: _freeze_tray(db, state, current_time),
        )

    if snapshot is None:
        return jsonify({'error': 'Unknown tray.'}), 404
    return jsonify(snapshot)

@bp.route('/api/tray-states')
def get_tray_states():
    current_time = datetime.now()

    with tray_states_lock:
        db = get_db()
        if seed_trays(db):
            db.commit()
        tray_ids = [
            row['id'] for row in db.execute('SELECT id FROM tray_state ORDER BY id').fetchall()
        ]
        response = {}
        for tray_id in tray_ids:
            response[tray_id] = _with_tray(tray_id, current_time, None)

        return jsonify(response)
