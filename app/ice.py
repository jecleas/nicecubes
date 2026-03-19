from flask import Blueprint, jsonify, request, session, g
from datetime import datetime, timedelta
from threading import Lock
from app.db import get_db

bp = Blueprint('ice', __name__)


def create_tray_state():
    return {
        'active_cubes': set(),  # Store indices of active cubes
        'is_frozen': False,
        'frozen_at': None,
        'expires_at': None,
        'revision': 0,
    }


tray_states = {
    'tray1': create_tray_state(),
    'tray2': create_tray_state(),
}

tray_states_lock = Lock()


def prune_expired_tray_state(state, current_time):
    if state['expires_at'] and state['expires_at'] <= current_time:
        state['is_frozen'] = False
        state['frozen_at'] = None
        state['expires_at'] = None
        state['revision'] += 1


def serialize_tray_state(state):
    return {
        'active_cubes': sorted(state['active_cubes']),
        'is_frozen': state['is_frozen'],
        'frozen_at': state['frozen_at'].isoformat() if state['frozen_at'] else None,
        'expires_at': state['expires_at'].isoformat() if state['expires_at'] else None,
        'revision': state['revision'],
    }


def get_tray_snapshot(tray_id, current_time):
    state = tray_states[tray_id]
    prune_expired_tray_state(state, current_time)
    return serialize_tray_state(state)

@bp.route('/api/toggle-cube', methods=['POST'])
def toggle_cube():
    if g.user is None:
        return jsonify({'error': 'Not authenticated.'}), 401

    data = request.get_json()
    tray_id = data['trayId']
    cube_index = data['cubeIndex']

    with tray_states_lock:
        state = tray_states[tray_id]
        prune_expired_tray_state(state, datetime.now())

        if not state['is_frozen']:
            if cube_index in state['active_cubes']:
                state['active_cubes'].remove(cube_index)
                state['revision'] += 1
            else:
                state['active_cubes'].add(cube_index)
                state['revision'] += 1

                # Track stat: cube was toggled ON
                db = get_db()
                db.execute(
                    'UPDATE user_stats SET cubes_created = cubes_created + 1 WHERE user_id = ?',
                    (g.user['id'],)
                )
                db.commit()

        return jsonify(get_tray_snapshot(tray_id, datetime.now()))

@bp.route('/api/freeze-tray', methods=['POST'])
def freeze_tray():
    if g.user is None:
        return jsonify({'error': 'Not authenticated.'}), 401

    data = request.get_json()
    tray_id = data['trayId']
    current_time = datetime.now()

    with tray_states_lock:
        state = tray_states[tray_id]
        prune_expired_tray_state(state, current_time)
        state['is_frozen'] = True
        state['frozen_at'] = current_time
        state['expires_at'] = current_time + timedelta(hours=4)
        state['revision'] += 1

        # Track stats: count active cubes in this tray, then mark tray as frozen
        frozen_cube_count = len(state['active_cubes'])
        db = get_db()
        db.execute(
            'UPDATE user_stats SET trays_frozen = trays_frozen + 1, cubes_frozen = cubes_frozen + ? WHERE user_id = ?',
            (frozen_cube_count, g.user['id'])
        )
        db.commit()

        return jsonify(get_tray_snapshot(tray_id, current_time))

@bp.route('/api/tray-states')
def get_tray_states():
    current_time = datetime.now()

    with tray_states_lock:
        response = {}

        for tray_id in tray_states:
            response[tray_id] = get_tray_snapshot(tray_id, current_time)

        return jsonify(response)