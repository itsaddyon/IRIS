"""
web/app.py — Flask + SocketIO web server for IRIS.
"""
import sys, os, time, threading, base64
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import config
import numpy as np
import cv2
from flask import (Flask, render_template, jsonify, Response,
                   send_file, abort, request,
                   session as flask_session, redirect)
from flask_socketio import SocketIO
from auth import check_municipal, check_driver
import session_manager as sm
from database.db_manager import (
    init_db, get_recent_detections, get_stats,
    get_high_detections, get_approved_detections, get_declined_detections,
    approve_detection, decline_detection, get_all_sessions,
    get_session_detections, get_vehicle_summary, get_high_detections_by_vehicle
)

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('IRIS_SECRET_KEY', 'dev-only-change-me')
# Increase max message size for large frame data (base64 encoded images)
socketio = SocketIO(app, cors_allowed_origins='*', async_mode='threading', 
                    max_http_buffer_size=50e6)  # 50MB
init_db()


@app.after_request
def add_no_cache_headers(response):
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response

# Thread-safe frame storage
_frame_lock  = threading.Lock()
_latest_frame = None

def update_frame(frame):
    global _latest_frame
    with _frame_lock:
        _latest_frame = frame.copy()

def emit_detection(data):
    socketio.emit('detection', data)

def emit_municipal(data):
    socketio.emit('new_high', data)


# ── Auth helpers ──────────────────────────────────────────────────────────────
def is_municipal():
    return flask_session.get('role') == 'municipal'

def is_driver():
    return flask_session.get('role') == 'driver'

def require_municipal():
    """Return a 403 response if the caller is not a municipal officer."""
    if not is_municipal():
        return jsonify({'status': 'error', 'message': 'Unauthorized'}), 403
    return None

def require_driver():
    """Bypass driver login wall and authenticate a default driver."""
    if not is_driver() or not flask_session.get('driver_id'):
        flask_session['role'] = 'driver'
        flask_session['driver_id'] = 1
        flask_session['driver_name'] = 'Ramesh Kumar'
        flask_session['vehicle_id'] = 'MH-12-BUS-001'
        flask_session.modified = True
    return None

# ── Auth routes ───────────────────────────────────────────────────────────────
@app.route('/login')
def login_page():
    return redirect('/municipal/login')

@app.route('/login/municipal', methods=['POST'])
def login_municipal():
    data = request.get_json() or {}
    if check_municipal(data.get('username', ''), data.get('password', '')):
        flask_session['role'] = 'municipal'
        flask_session['username'] = data.get('username')
        return jsonify({'status': 'ok', 'redirect': '/municipal'})
    return jsonify({'status': 'error', 'message': 'Invalid credentials'}), 401

@app.route('/logout')
def logout():
    flask_session.clear()
    return redirect('/live')

@app.route('/api/me')
def api_me():
    driver_info = {
        'role':       flask_session.get('role'),
        'username':   flask_session.get('username'),
        'driver_id':  flask_session.get('driver_id'),
        'driver_name': flask_session.get('driver_name'),
        'vehicle_id': flask_session.get('vehicle_id'),
        'vehicles': ['MH-12-BUS-001', 'UP-80-AUTO-042', 'DL-01-TRUCK-007'],
        'routes': ['NH-44 Agra North', 'Ring Road Agra', 'Yamuna Expressway'],
    }
    return jsonify(driver_info)

def hydrate_driver_session(driver_id, driver_name=None):
    try:
        driver_id = int(driver_id)
    except (TypeError, ValueError):
        return False

    flask_session['role'] = 'driver'
    flask_session['driver_id'] = driver_id
    if driver_name:
        flask_session['driver_name'] = driver_name
    flask_session['vehicle_id'] = 'MH-12-BUS-001'
    flask_session.modified = True
    return True

# ── Pages ─────────────────────────────────────────────────────────────────────
@app.route('/')
def root():
    role = flask_session.get('role')
    if role == 'municipal':
        return redirect('/municipal')
    require_driver()
    return redirect('/live')

@app.route('/dashboard')
def dashboard():
    require_driver()
    return redirect('/live')

@app.route('/live')
def live_dashboard():
    require_driver()
    return render_template('dashboard.html',
        driver_name=flask_session.get('driver_name', 'Driver'),
        vehicle_id=flask_session.get('vehicle_id', ''),
        driver_id=flask_session.get('driver_id', '')
    )

@app.route('/driver')
def driver_dashboard():
    require_driver()
    return redirect('/live')

@app.route('/municipal')
def municipal():
    if not is_municipal():
        return redirect('/municipal/login')
    return render_template('municipal.html')

@app.route('/pending_detail')
def pending_detail():
    if not is_municipal():
        return redirect('/municipal/login')
    return render_template('pending_detail.html')

@app.route('/approved_detail')
def approved_detail():
    if not is_municipal():
        return redirect('/municipal/login')
    return render_template('approved_detail.html')

@app.route('/declined_detail')
def declined_detail():
    if not is_municipal():
        return redirect('/municipal/login')
    return render_template('declined_detail.html')

@app.route('/session_detail')
def session_detail():
    if not is_municipal():
        return redirect('/municipal/login')
    return render_template('session_detail.html')

@app.route('/municipal/login')
def municipal_login_page():
    if is_municipal():
        return redirect('/municipal')
    return render_template('municipal_login.html')

@app.route('/road_vision')
def road_vision():
    require_driver()
    return render_template('road_vision.html')

@app.route('/mobile')
def mobile():
    require_driver()
    return render_template('mobile.html')


# ── Session API ───────────────────────────────────────────────────────────────
@app.route('/api/session/start', methods=['POST'])
def api_session_start():
    if sm.session.active:
        return jsonify({
            'status': 'already_active',
            'session': sm.session.status(),
        }), 409

    data = request.get_json() or {}
    sid = sm.session.start(
        vehicle_id=data.get('vehicle_id', 'VEHICLE-01'),
        route=data.get('route', 'City Route')
    )
    try:
        from voice_alert import speak
        speak("IRIS inspection session started. Drive safely.")
    except Exception:
        pass
    status = sm.session.status()
    socketio.emit('session_started', status)
    return jsonify({'status': 'started', 'session_id': sid, 'session': status})

@app.route('/api/session/end', methods=['POST'])
def api_session_end():
    summary = sm.session.end()
    if not summary:
        return jsonify({'status': 'no_active_session'}), 400
    try:
        from voice_alert import speak
        speak("Inspection session ended. Data uploaded.")
    except Exception:
        pass
    socketio.emit('session_ended', summary)
    socketio.emit('new_session_report', summary)
    return jsonify({'status': 'ended', 'summary': summary})

@app.route('/api/session/status')
def api_session_status():
    return jsonify(sm.session.status())

@app.route('/api/sessions')
def api_sessions():
    err = require_municipal()
    if err: return err
    return jsonify(get_all_sessions())

@app.route('/api/session/<session_id>/detections')
def api_session_detections(session_id):
    if flask_session.get('role') not in ('driver', 'municipal'):
        return jsonify({'status': 'error', 'message': 'Unauthorized'}), 403
    return jsonify(get_session_detections(session_id))

# ── Detection API ─────────────────────────────────────────────────────────────
@app.route('/api/detections')
def api_detections():
    rows = get_recent_detections(50)
    return jsonify([{
        'id': r[0], 'session_id': r[1], 'timestamp': r[2],
        'severity': r[3], 'confidence': r[4], 'bbox': r[5],
        'photo': r[6], 'location': r[7]
    } for r in rows])

@app.route('/api/stats')
def api_stats():
    return jsonify(get_stats())

@app.route('/api/high_detections')
def api_high():
    vehicle_id = request.args.get('vehicle_id')
    return jsonify(get_high_detections_by_vehicle(vehicle_id if vehicle_id else None))

@app.route('/api/vehicles')
def api_vehicles():
    from vehicles import get_all_vehicles
    fleet    = get_all_vehicles()
    stats    = {v['vehicle_id']: v for v in get_vehicle_summary()}
    sessions = get_all_sessions()
    result   = []
    for v in fleet:
        vid  = v['vehicle_id']
        stat = stats.get(vid, {})
        last = next((s for s in sessions if s['vehicle_id'] == vid), None)
        result.append({**v,
            'sessions':   stat.get('sessions', 0),
            'total':      stat.get('total', 0),
            'high':       stat.get('high', 0),
            'medium':     stat.get('medium', 0),
            'low':        stat.get('low', 0),
            'last_active':stat.get('last_active', 'Never'),
            'last_route': last['route'] if last else v['route'],
        })
    return jsonify(result)

@app.route('/api/approved_detections')
def api_approved():
    err = require_municipal()
    if err: return err
    return jsonify(get_approved_detections())

@app.route('/api/declined_detections')
def api_declined():
    err = require_municipal()
    if err: return err
    return jsonify(get_declined_detections())

@app.route('/api/approved_map')
def api_approved_map():
    err = require_municipal()
    if err: return err
    return jsonify([d for d in get_approved_detections() if d.get('location')])

@app.route('/api/approve/<int:did>', methods=['POST'])
def api_approve(did):
    err = require_municipal()
    if err: return err
    approve_detection(did)
    return jsonify({'status': 'approved', 'id': did})

@app.route('/api/decline/<int:did>', methods=['POST'])
def api_decline(did):
    err = require_municipal()
    if err: return err
    decline_detection(did)
    return jsonify({'status': 'declined', 'id': did})


# ── File serving ──────────────────────────────────────────────────────────────
@app.route('/snapshot/<path:filename>')
def snapshot(filename):
    if flask_session.get('role') not in ('driver', 'municipal'):
        return abort(403)
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    p = os.path.join(root, config.SNAPSHOTS_DIR, filename)
    if os.path.exists(p):
        return send_file(p, mimetype='image/jpeg')
    return abort(404)

@app.route('/generate_report')
def generate_report_route():
    if not is_municipal():
        return redirect('/login')
    from web.report import generate_report as _gen
    detections = get_approved_detections()
    if not detections:
        return "No approved detections to report.", 404
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    out  = os.path.join(root, 'IRIS_Report.pdf')
    _gen(detections, out)
    return send_file(out, as_attachment=True,
                     download_name='IRIS_Report.pdf',
                     mimetype='application/pdf')

# ── Video feed ────────────────────────────────────────────────────────────────
def _make_placeholder_jpeg():
    """JPEG bytes for 'camera connecting' placeholder."""
    frame = np.zeros((480, 640, 3), dtype=np.uint8)
    frame[:] = (12, 18, 28)
    cv2.putText(frame, "IRIS - Camera Connecting",
                (110, 230), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (60, 120, 200), 2)
    cv2.putText(frame, getattr(config, 'VIDEO_IP', ''),
                (160, 275), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (40, 180, 80), 1)
    _, buf = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 70])
    return buf.tobytes()

@app.route('/video_feed')
def video_feed():
    boundary = b'--frame\r\nContent-Type: image/jpeg\r\n\r\n'
    placeholder = _make_placeholder_jpeg()

    def generate():
        while True:
            with _frame_lock:
                frame = _latest_frame
            if frame is None:
                yield boundary + placeholder + b'\r\n'
                time.sleep(0.15)
                continue
            try:
                ok, buf = cv2.imencode('.jpg', frame,
                                       [cv2.IMWRITE_JPEG_QUALITY, 80])
                if ok:
                    yield boundary + buf.tobytes() + b'\r\n'
            except Exception:
                pass
            time.sleep(0.033)

    return Response(
        generate(),
        mimetype='multipart/x-mixed-replace; boundary=frame',
        headers={
            'Cache-Control': 'no-cache, no-store, must-revalidate',
            'Pragma':        'no-cache',
            'Expires':       '0',
            'X-Accel-Buffering': 'no',
        }
    )



@socketio.on('stream:join')
def on_stream_join(data):
    """Client requests to join the frame stream"""
    driver_id = flask_session.get('driver_id')
    if not driver_id:
        return False
    print(f"[Stream] Driver {driver_id} joined frame stream")
    return True

@socketio.on('stream:frame_request')
def on_frame_request(callback=None):
    """Send current frame to client"""
    with _frame_lock:
        frame = _latest_frame
    
    if frame is None:
        if callback:
            callback({'success': False, 'error': 'No frame available'})
        return
    
    try:
        _, buf = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 75])
        frame_base64 = 'data:image/jpeg;base64,' + base64.b64encode(buf.tobytes()).decode('utf-8')
        
        if callback:
            callback({'success': True, 'frame': frame_base64})
        else:
            socketio.emit('stream:frame', {'frame': frame_base64})
    except Exception as e:
        print(f"[Stream] Error encoding frame: {e}")
        if callback:
            callback({'success': False, 'error': str(e)})

# ── Run ────────────────────────────────────────────────────────────────────────
if __name__ == '__main__':
    socketio.run(app, debug=True, host='0.0.0.0', port=5000, allow_unsafe_werkzeug=True)
