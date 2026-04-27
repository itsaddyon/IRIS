"""
main.py — IRIS entry point.
Starts Flask web server + background detection loop simultaneously.
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import threading
import time
import cv2
import numpy as np
from datetime import datetime

import config
from database.db_manager import init_db, insert_detection
from detector.video_source import get_source
from detector.yolo_detector import detect
from detector.severity import classify
from detector.frame_annotator import annotate
from detector.deduplicator import filter_new
import session_manager as sm
from voice_alert import alert as voice_alert
from arduino_controller import alert as arduino_alert
from gps import get_location_string
from gemini_analyzer import analyze_incident, format_alert_message, setup_gemini

# ── Firebase Firestore (Cloud Storage) ──────────────────────────────────────
try:
    import firebase_admin
    from firebase_admin import credentials, firestore
    FIRESTORE_AVAILABLE = False
    try:
        # Try to initialize Firebase with service account key
        cred = credentials.Certificate('firestore-key.json')
        firebase_admin.initialize_app(cred)
        db = firestore.client()
        FIRESTORE_AVAILABLE = True
        print("[IRIS] ✓ Firestore initialized (Cloud storage enabled)")
    except FileNotFoundError:
        print("[IRIS] ⚠️ firestore-key.json not found (local-only mode)")
        db = None
    except Exception as e:
        print(f"[IRIS] ⚠️ Firestore not initialized (local-only mode): {e}")
        db = None
except ImportError:
    FIRESTORE_AVAILABLE = False
    db = None
    print("[IRIS] Firebase not installed (local-only mode)")

# ── Import web app AFTER all other modules to avoid circular imports ──────────
from web.app import app, socketio, update_frame, emit_detection


def make_placeholder(msg="Connecting to IP Webcam..."):
    """Dark placeholder frame shown in browser until camera connects."""
    frame = np.zeros((480, 640, 3), dtype=np.uint8)
    frame[:] = (12, 18, 28)
    cv2.rectangle(frame, (20, 20), (620, 460), (25, 45, 80), 1)
    cv2.putText(frame, "IRIS", (260, 180),
                cv2.FONT_HERSHEY_SIMPLEX, 2.0, (40, 100, 200), 3)
    cv2.putText(frame, msg, (80, 260),
                cv2.FONT_HERSHEY_SIMPLEX, 0.65, (60, 90, 130), 1)
    ip = getattr(config, 'VIDEO_IP', '')
    if ip:
        cv2.putText(frame, ip, (160, 300),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (40, 180, 80), 1)
    cv2.putText(frame, "Dashboard: http://localhost:5000", (155, 420),
                cv2.FONT_HERSHEY_SIMPLEX, 0.45, (40, 60, 100), 1)
    return frame


def save_to_firestore(detection_data, ai_analysis=None):
    """Save detection to Firestore for global access."""
    if not FIRESTORE_AVAILABLE or db is None:
        return False
    
    try:
        doc = {
            'timestamp': detection_data.get('timestamp'),
            'severity': detection_data.get('severity'),
            'confidence': float(detection_data.get('confidence', 0)),
            'location': detection_data.get('location'),
            'bbox_area': float(detection_data.get('bbox_area', 0)),
        }
        
        if ai_analysis:
            doc['ai_analysis'] = ai_analysis.get('ai_analysis')
            doc['recommended_action'] = ai_analysis.get('recommended_action')
            doc['impact_estimate'] = ai_analysis.get('impact_estimate')
            doc['priority'] = ai_analysis.get('priority')
        
        # Save to Firestore collection 'detections'
        db.collection('detections').add(doc)
        print(f"[IRIS] ✓ Saved to Firestore: {detection_data['severity']} pothole")
        return True
    except Exception as e:
        print(f"[IRIS] ⚠️ Firestore save failed: {e}")
        return False


def detection_loop():
    """
    Background daemon:
    - Connects/reconnects to camera automatically
    - Runs YOLO only during active sessions
    - Streams every frame to web via update_frame()
    - Never calls cv2.imshow() — headless server mode
    """
    # Push placeholder immediately so web feed isn't blank
    update_frame(make_placeholder())

    retry_delay = 5

    while True:
        # ── Connect ──────────────────────────────────────────────────────
        try:
            cap = get_source()
            update_frame(make_placeholder("Camera connected — waiting for session"))
            print("[IRIS] Camera connected ✅")
        except Exception as e:
            print(f"[IRIS] Camera failed: {e}")
            update_frame(make_placeholder(f"Camera error — retrying in {retry_delay}s"))
            time.sleep(retry_delay)
            continue

        consecutive_failures = 0

        # ── Frame loop ────────────────────────────────────────────────────
        while True:
            try:
                ret, frame = cap.read()
            except Exception as e:
                print(f"[IRIS] Read error: {e}")
                ret, frame = False, None

            if not ret or frame is None:
                consecutive_failures += 1
                if consecutive_failures > 60:
                    print("[IRIS] Camera lost — reconnecting...")
                    try: cap.release()
                    except Exception: pass
                    break
                if config.VIDEO_MODE == 'video':
                    try: cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                    except Exception: pass
                time.sleep(0.05)
                continue

            consecutive_failures = 0

            # No session → just stream the frame
            if not sm.session.active:
                update_frame(frame)
                time.sleep(0.033)
                continue

            # ── Active session: detect ────────────────────────────────────
            try:
                raw = detect(frame)
                new = filter_new(raw)
            except Exception as e:
                print(f"[IRIS] Detection error: {e}")
                update_frame(frame)
                time.sleep(0.033)
                continue

            for bbox, confidence in new:
                severity, area = classify(bbox, confidence)
                frame = annotate(frame, bbox, severity, confidence)
                ts = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                photo_path = None
                location = None
                ai_analysis = None

                if severity == 'High':
                    fname = f"High_{datetime.now().strftime('%Y%m%d_%H%M%S%f')}.jpg"
                    photo_path = os.path.join(config.SNAPSHOTS_DIR, fname)
                    cv2.imwrite(photo_path, frame, [cv2.IMWRITE_JPEG_QUALITY, 95])
                    location = get_location_string()
                    
                    # ── GOOGLE GEMINI AI ANALYSIS ────────────────────────
                    detection_data = {
                        'severity': severity,
                        'confidence': confidence,
                        'bbox_area': area,
                        'location': location or 'Unknown',
                        'timestamp': ts,
                        'photo_path': photo_path
                    }
                    ai_analysis = analyze_incident(detection_data)
                    ai_message = format_alert_message(detection_data, ai_analysis)
                    print(f"[IRIS] 🤖 AI Analysis: {ai_analysis.get('recommended_action')}")
                    
                    voice_alert('High')
                    arduino_alert('High')
                    print(f"[IRIS] HIGH | {location or 'no-GPS'} | {area:.0f}px² | Priority: {ai_analysis.get('priority')}/5")
                elif severity == 'Medium':
                    voice_alert('Medium')
                    arduino_alert('Medium')
                else:
                    arduino_alert('Low')

                sm.session.record(severity)
                insert_detection(ts, severity, confidence,
                                 bbox, photo_path, location,
                                 sm.session.session_id)

                emit_data = {
                    'timestamp':  ts,
                    'severity':   severity,
                    'confidence': round(confidence, 2),
                    'area':       round(area, 1),
                    'location':   location,
                    'photo':      photo_path,
                    'session_id': sm.session.session_id,
                }
                
                # Add AI analysis to emission if available
                if ai_analysis:
                    emit_data['ai_analysis'] = ai_analysis.get('ai_analysis')
                    emit_data['recommended_action'] = ai_analysis.get('recommended_action')
                    emit_data['impact_estimate'] = ai_analysis.get('impact_estimate')
                    emit_data['priority'] = ai_analysis.get('priority')
                
                emit_detection(emit_data)
                
                # ── SAVE TO FIRESTORE (Cloud) ────────────────────────────
                if severity == 'High':
                    save_to_firestore(detection_data, ai_analysis)

            update_frame(frame)
            time.sleep(0.033)


if __name__ == '__main__':
    init_db()
    os.makedirs(config.SNAPSHOTS_DIR, exist_ok=True)

    # Initialize Gemini AI
    gemini_ready = setup_gemini()

    # Start detection in background thread
    t = threading.Thread(target=detection_loop, daemon=True)
    t.start()

    print(f"[IRIS] ─────────────────────────────────────────")
    print(f"[IRIS] Dashboard  → http://localhost:{config.FLASK_PORT}")
    print(f"[IRIS] Camera     → {getattr(config,'VIDEO_IP','USB webcam')}")
    print(f"[IRIS] Arduino    → {'ENABLED on '+config.ARDUINO_PORT if config.ARDUINO_ENABLED else 'DISABLED'}")
    print(f"[IRIS] Gemini AI  → {'✓ ENABLED' if gemini_ready else '✗ DISABLED (set GEMINI_API_KEY)'}")
    print(f"[IRIS] Model      → {config.MODEL_PATH}")
    print(f"[IRIS] ─────────────────────────────────────────")

    # Run Flask + SocketIO (blocking)
    socketio.run(app,
                 host=config.FLASK_HOST,
                 port=config.FLASK_PORT,
                 debug=False,
                 allow_unsafe_werkzeug=True)
