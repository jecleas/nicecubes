from flask import Blueprint, jsonify, request
from datetime import datetime, timedelta

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
@app.route('/ice')
def ice():
    return render_template('ice.html')
    
@bp.route('/api/toggle-cube', methods=['POST'])
def toggle_cube():
    data = request.get_json()
    tray_id = data['trayId']
    cube_index = data['cubeIndex']
    
    if not tray_states[tray_id]['is_frozen']:
        if cube_index in tray_states[tray_id]['active_cubes']:
            tray_states[tray_id]['active_cubes'].remove(cube_index)
        else:
            tray_states[tray_id]['active_cubes'].add(cube_index)
    
    return jsonify({
        'active_cubes': list(tray_states[tray_id]['active_cubes']),
        'is_frozen': tray_states[tray_id]['is_frozen']
    })

@bp.route('/api/freeze-tray', methods=['POST'])
def freeze_tray():
    data = request.get_json()
    tray_id = data['trayId']
    current_time = datetime.now()
    
    tray_states[tray_id]['is_frozen'] = True
    tray_states[tray_id]['frozen_at'] = current_time
    tray_states[tray_id]['expires_at'] = current_time + timedelta(hours=4)
    
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