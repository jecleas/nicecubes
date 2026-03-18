from flask import Blueprint, jsonify, request, session, g
from datetime import datetime, timedelta
from app.db import get_db

bp = Blueprint('ice', __name__)
tray_states = {
    'tray1': {
        'active_cubes': set(),  # Store indices of active cubes
        'is_frozen': False,
        'frozen_at': None,
        'expires_at': None
    },
    'tray2': {
        'active_cubes': set(),
        'is_frozen': False,
        'frozen_at': None,
        'expires_at': None
    }
}

@bp.route('/api/toggle-cube', methods=['POST'])
def toggle_cube():
    if g.user is None:
        return jsonify({'error': 'Not authenticated.'}), 401

    data = request.get_json()
    tray_id = data['trayId']
    cube_index = data['cubeIndex']
    
    if not tray_states[tray_id]['is_frozen']:
        if cube_index in tray_states[tray_id]['active_cubes']:
            tray_states[tray_id]['active_cubes'].remove(cube_index)
        else:
            tray_states[tray_id]['active_cubes'].add(cube_index)
            # Track stat: cube was toggled ON
            db = get_db()
            db.execute(
                'UPDATE user_stats SET cubes_created = cubes_created + 1 WHERE user_id = ?',
                (g.user['id'],)
            )
            db.commit()
    
    return jsonify({
        'active_cubes': list(tray_states[tray_id]['active_cubes']),
        'is_frozen': tray_states[tray_id]['is_frozen']
    })

@bp.route('/api/freeze-tray', methods=['POST'])
def freeze_tray():
    if g.user is None:
        return jsonify({'error': 'Not authenticated.'}), 401

    data = request.get_json()
    tray_id = data['trayId']
    current_time = datetime.now()
    
    tray_states[tray_id]['is_frozen'] = True
    tray_states[tray_id]['frozen_at'] = current_time
    tray_states[tray_id]['expires_at'] = current_time + timedelta(hours=4)

    # Track stats: count active cubes in this tray, then mark tray as frozen
    frozen_cube_count = len(tray_states[tray_id]['active_cubes'])
    db = get_db()
    db.execute(
        'UPDATE user_stats SET trays_frozen = trays_frozen + 1, cubes_frozen = cubes_frozen + ? WHERE user_id = ?',
        (frozen_cube_count, g.user['id'])
    )
    db.commit()
    
    return jsonify({
        'is_frozen': tray_states[tray_id]['is_frozen'],
        'active_cubes': list(tray_states[tray_id]['active_cubes']),
        'frozen_at': tray_states[tray_id]['frozen_at'].isoformat(),
        'expires_at': tray_states[tray_id]['expires_at'].isoformat()
    })

@bp.route('/api/tray-states')
def get_tray_states():
    current_time = datetime.now()
    response = {}
    
    for tray_id, state in tray_states.items():
        if state['expires_at'] and state['expires_at'] <= current_time:
            state['is_frozen'] = False
            state['frozen_at'] = None
            state['expires_at'] = None
        response[tray_id] = {
            'active_cubes': list(state['active_cubes']),
            'is_frozen': state['is_frozen'],
            'expires_at': state['expires_at'].isoformat() if state['expires_at'] else None
        }
    
    return jsonify(response)