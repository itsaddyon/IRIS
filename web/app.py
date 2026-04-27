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
app.config['SECRET_KEY'] = 'iris_secret_2026'
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

# ── Auth routes ───────────────────────────────────────────────────────────────
@app.route('/login')
def login_page():
    return render_template('login.html')

@app.route('/login/municipal', methods=['POST'])
def login_municipal():
    data = request.get_json() or {}
    if check_municipal(data.get('username', ''), data.get('password', '')):
        flask_session['role'] = 'municipal'
        flask_session['username'] = data.get('username')
        return jsonify({'status': 'ok', 'redirect': '/municipal'})
    return jsonify({'status': 'error', 'message': 'Invalid credentials'}), 401

@app.route('/login/driver', methods=['POST'])
def login_driver():
    data = request.get_json() or {}
    vid, pin = data.get('vehicle_id', ''), data.get('pin', '')
    if check_driver(vid, pin):
        flask_session['role'] = 'driver'
        flask_session['vehicle_id'] = vid
        return jsonify({'status': 'ok', 'redirect': '/', 'vehicle_id': vid})
    return jsonify({'status': 'error', 'message': 'Invalid vehicle ID or PIN'}), 401

@app.route('/logout')
def logout():
    flask_session.clear()
    return redirect('/login')

@app.route('/api/me')
def api_me():
    driver_info = {
        'role':       flask_session.get('role'),
        'username':   flask_session.get('username'),
        'driver_id':  flask_session.get('driver_id'),
        'driver_name': flask_session.get('driver_name'),
        'vehicle_id': flask_session.get('vehicle_id'),
        'vehicles': [],
        'routes': [],
    }
    
    # Get vehicle and route assignments for driver
    if driver_info.get('driver_id'):
        try:
            from biometric_auth import get_biometric_engine
            engine = get_biometric_engine()
            assignments = engine.get_driver_vehicles(driver_info['driver_id'])
            driver_info['vehicles'] = assignments.get('vehicles', [])
            driver_info['routes'] = assignments.get('routes', [])
        except Exception as e:
            print(f"[API] Error getting driver assignments: {e}")
    
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

    try:
        from biometric_auth import get_biometric_engine
        engine = get_biometric_engine()
        assignments = engine.get_driver_vehicles(driver_id)
        vehicle_id = (assignments.get('vehicles') or [None])[0]
        if vehicle_id:
            flask_session['vehicle_id'] = vehicle_id
    except Exception as e:
        print(f"[Auth] Error hydrating driver session: {e}")

    flask_session.modified = True
    return True

# ── Pages ─────────────────────────────────────────────────────────────────────
@app.route('/')
def root():
    # Always redirect unauthenticated users to login
    if not flask_session.get('driver_id'):
        return redirect('/login')
    
    # Redirect authenticated drivers to their dashboard
    if flask_session.get('role') == 'driver':
        return render_template('driver_dashboard.html')
    
    return render_template('dashboard.html')

@app.route('/login')
def login():
    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    query_driver_id = request.args.get('driver_id')
    query_driver_name = request.args.get('driver_name')
    if query_driver_id:
        hydrate_driver_session(query_driver_id, query_driver_name)

    # Require authentication
    if not flask_session.get('driver_id'):
        return redirect('/login')
    
    if flask_session.get('role') == 'driver':
        return render_template('driver_dashboard.html')
    return render_template('dashboard.html')

@app.route('/live')
def live_dashboard():
    # Live monitoring dashboard for authenticated drivers
    if flask_session.get('role') != 'driver' or not flask_session.get('driver_id'):
        return redirect('/login')
    return render_template('dashboard.html')

@app.route('/driver')
def driver_dashboard():
    query_driver_id = request.args.get('driver_id')
    query_driver_name = request.args.get('driver_name')
    if query_driver_id:
        hydrate_driver_session(query_driver_id, query_driver_name)

    # Require authentication
    if not flask_session.get('driver_id'):
        return redirect('/login')
    return render_template('driver_dashboard.html')

@app.route('/municipal')
def municipal():
    if not is_municipal():
        return redirect('/login')
    return render_template('municipal.html')

@app.route('/road_vision')
def road_vision():
    if flask_session.get('role') not in ('driver', 'municipal'):
        return redirect('/login')
    return render_template('road_vision.html')

@app.route('/mobile')
def mobile():
    if flask_session.get('role') not in ('driver', 'municipal'):
        return redirect('/login')
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
    return jsonify(get_all_sessions())

@app.route('/api/session/<session_id>/detections')
def api_session_detections(session_id):
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
    return jsonify(get_approved_detections())

@app.route('/api/declined_detections')
def api_declined():
    return jsonify(get_declined_detections())

@app.route('/api/approved_map')
def api_approved_map():
    return jsonify([d for d in get_approved_detections() if d.get('location')])

@app.route('/api/approve/<int:did>', methods=['POST'])
def api_approve(did):
    approve_detection(did)
    return jsonify({'status': 'approved', 'id': did})

@app.route('/api/decline/<int:did>', methods=['POST'])
def api_decline(did):
    decline_detection(did)
    return jsonify({'status': 'declined', 'id': did})


# ── File serving ──────────────────────────────────────────────────────────────
@app.route('/snapshot/<path:filename>')
def snapshot(filename):
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    p = os.path.join(root, config.SNAPSHOTS_DIR, filename)
    if os.path.exists(p):
        return send_file(p, mimetype='image/jpeg')
    return abort(404)

@app.route('/generate_report')
def generate_report_route():
    # Import from web.report (correct path)
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

# ── Health check ──────────────────────────────────────────────────────────────
@app.route('/api/health')
def health():
    return jsonify({
        'status':      'ok',
        'session':     sm.session.active,
        'has_frame':   _latest_frame is not None,
        'video_mode':  config.VIDEO_MODE,
        'video_ip':    getattr(config, 'VIDEO_IP', ''),
    })

# ── Biometric endpoints ────────────────────────────────────────────────────────
@app.route('/api/vehicles-and-routes')
def api_vehicles_and_routes():
    """Get available vehicles and routes for driver enrollment"""
    from vehicles import get_all_vehicles
    vehicles = get_all_vehicles()
    routes = [
        'City Center Route',
        'North Highway',
        'South Highway', 
        'East District',
        'West District',
        'Airport Road'
    ]
    return jsonify({
        'vehicles': [{'id': v['vehicle_id'], 'name': v['name']} for v in vehicles],
        'routes': routes
    })

# ── SocketIO events ────────────────────────────────────────────────────────────
@socketio.on('biometric:capture_face')
def on_capture_face(data, callback=None):
    """Capture face from webcam frame for recognition/enrollment"""
    def send_response(response):
        """Send response via callback if provided, otherwise return"""
        if callback:
            callback(response)
        return response
    
    try:
        import base64
        import io
        from PIL import Image
        import face_recognition
        
        print("[BIOMETRIC] Received face capture request")
        
        # Get frame data from client (base64 encoded JPEG)
        frame_data = data.get('frame')
        if not frame_data:
            print("[BIOMETRIC] ❌ No frame data provided")
            return send_response({'success': False, 'error': 'No frame data provided'})
        
        # Decode base64 frame
        try:
            # Remove data URL prefix if present
            if frame_data.startswith('data:image'):
                frame_data = frame_data.split(',')[1]
            
            # Decode base64 to bytes
            frame_bytes = base64.b64decode(frame_data)
            print(f"[BIOMETRIC] Frame decoded: {len(frame_bytes)} bytes")
            
            # Convert to PIL Image then to numpy array
            pil_image = Image.open(io.BytesIO(frame_bytes))
            frame_array = np.array(pil_image)
            print(f"[BIOMETRIC] Frame shape: {frame_array.shape}")
            
            # PIL uses RGB, face_recognition expects RGB too
            if len(frame_array.shape) == 3 and frame_array.shape[2] == 3:
                rgb_frame = frame_array
            else:
                rgb_frame = cv2.cvtColor(frame_array, cv2.COLOR_BGR2RGB)
                
        except Exception as decode_err:
            print(f"[BIOMETRIC] ❌ Failed to decode frame: {decode_err}")
            return send_response({'success': False, 'error': f'Failed to decode frame: {str(decode_err)}'})
        
        # Detect faces
        print("[BIOMETRIC] Detecting faces...")
        face_locations = face_recognition.face_locations(rgb_frame, model='hog')
        print(f"[BIOMETRIC] Faces detected: {len(face_locations)}")
        
        if not face_locations:
            print("[BIOMETRIC] ❌ No face detected in frame")
            return send_response({'success': False, 'error': 'No face detected. Please ensure your face is clearly visible.'})
        
        # Generate face encoding
        print("[BIOMETRIC] Generating face encoding...")
        face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)
        if not face_encodings:
            print("[BIOMETRIC] ❌ Face encoding failed")
            return send_response({'success': False, 'error': 'Face found, but encoding failed. Try better lighting.'})
        
        # Return first face encoding
        encoding = face_encodings[0].astype(float).tolist()
        print(f"[BIOMETRIC] ✓ Face encoding generated successfully")
        return send_response({'success': True, 'encoding': encoding})
        
    except Exception as e:
        print(f"[BIOMETRIC] ❌ Exception in face capture: {e}")
        import traceback
        traceback.print_exc()
        return send_response({'success': False, 'error': f'Server error: {str(e)}'})

@socketio.on('biometric:recognize')
def on_recognize(data, callback=None):
    """Recognize driver from face encoding"""
    def send_response(response):
        if callback:
            callback(response)
        return response
    
    try:
        from biometric_auth import get_biometric_engine

        encoding = np.array(data.get('encoding') or [], dtype=np.float64)
        if encoding.size != 128:
            return send_response({'success': False, 'error': 'Invalid face encoding'})

        engine = get_biometric_engine()
        driver = engine.recognize_driver(encoding)
        if not driver:
            return send_response({'success': False, 'driver': None})

        assignments = engine.get_driver_vehicles(driver['driver_id'])
        vehicle_id = (assignments.get('vehicles') or [None])[0]
        
        # Set session data
        flask_session['role'] = 'driver'
        flask_session['driver_id'] = driver['driver_id']
        flask_session['driver_name'] = driver['name']
        if vehicle_id:
            flask_session['vehicle_id'] = vehicle_id
        
        # Explicitly mark session as modified to ensure it's saved
        flask_session.modified = True

        return send_response({
            'success': True,
            'driver': {
                **driver,
                'vehicles': assignments.get('vehicles', []),
                'routes': assignments.get('routes', []),
            }
        })
    except Exception as e:
        return send_response({'success': False, 'error': str(e)})

@socketio.on('biometric:enroll_driver')
def on_enroll_driver(data, callback=None):
    """Enroll new driver with biometric data"""
    def send_response(response):
        if callback:
            callback(response)
        return response
    
    try:
        from biometric_auth import get_biometric_engine
        
        name = (data.get('name') or 'Unknown Driver').strip()
        vehicles = data.get('vehicles', [])
        routes = data.get('routes', [])
        face_encoding = np.array(data.get('face_encoding') or [], dtype=np.float64)

        if not name:
            return send_response({'success': False, 'error': 'Driver name is required'})
        if not vehicles or not routes:
            return send_response({'success': False, 'error': 'Select at least one vehicle and one route'})
        if face_encoding.size != 128:
            return send_response({'success': False, 'error': 'Invalid face encoding'})

        engine = get_biometric_engine()
        driver_id = engine.enroll_new_driver(name, vehicles, routes, face_encoding)
        if driver_id is None:
            return send_response({'success': False, 'error': 'Enrollment failed. Driver may already exist.'})

        flask_session['role'] = 'driver'
        flask_session['driver_id'] = driver_id
        flask_session['driver_name'] = name
        flask_session['vehicle_id'] = vehicles[0]
        
        # Explicitly mark session as modified to ensure it's saved
        flask_session.modified = True
        
        return send_response({
            'success': True,
            'driver_id': driver_id,
            'name': name,
            'message': f'Driver {name} enrolled successfully'
        })
        
    except Exception as e:
        return send_response({'success': False, 'error': str(e)})

# ── WebSocket: Real-time Frame Streaming ──────────────────────────────────────
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
