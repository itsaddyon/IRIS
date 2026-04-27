import sqlite3
import config

def init_db():
    conn = sqlite3.connect(config.DB_PATH)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS detections (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id   TEXT,
            driver_id    INTEGER,
            timestamp    TEXT NOT NULL,
            severity     TEXT NOT NULL,
            confidence   REAL NOT NULL,
            bbox         TEXT NOT NULL,
            photo_path   TEXT,
            location     TEXT,
            approved     INTEGER DEFAULT 0,
            declined     INTEGER DEFAULT 0,
            FOREIGN KEY(driver_id) REFERENCES drivers(id)
        )''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS sessions (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id   TEXT UNIQUE,
            driver_id    INTEGER,
            vehicle_id   TEXT,
            route        TEXT,
            start_time   TEXT,
            end_time     TEXT,
            duration_sec INTEGER DEFAULT 0,
            total        INTEGER DEFAULT 0,
            high         INTEGER DEFAULT 0,
            medium       INTEGER DEFAULT 0,
            low          INTEGER DEFAULT 0,
            uploaded     INTEGER DEFAULT 0,
            FOREIGN KEY(driver_id) REFERENCES drivers(id)
        )''')
    
    # ✨ NEW: Driver biometric tables
    c.execute('''
        CREATE TABLE IF NOT EXISTS drivers (
            id               INTEGER PRIMARY KEY AUTOINCREMENT,
            name             TEXT NOT NULL UNIQUE,
            facial_encoding  BLOB,
            created_at       TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )''')
    
    c.execute('''
        CREATE TABLE IF NOT EXISTS driver_vehicles (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            driver_id INTEGER NOT NULL UNIQUE,
            vehicles  TEXT,
            routes    TEXT,
            FOREIGN KEY(driver_id) REFERENCES drivers(id)
        )''')
    
    existing = [r[1] for r in c.execute("PRAGMA table_info(detections)")]
    for col, defval in [('approved','0'),('declined','0'),('session_id',"''"),('driver_id', 'NULL')]:
        if col not in existing:
            col_type = 'INTEGER' if col == 'driver_id' else ('INTEGER DEFAULT '+defval if col!='session_id' else 'TEXT')
            c.execute(f"ALTER TABLE detections ADD COLUMN {col} {col_type}")
            print(f"[IRIS] DB migrated: added '{col}' to detections")
    
    # Check sessions table for driver_id column
    sessions_cols = [r[1] for r in c.execute("PRAGMA table_info(sessions)")]
    if 'driver_id' not in sessions_cols:
        c.execute("ALTER TABLE sessions ADD COLUMN driver_id INTEGER DEFAULT NULL")
        print(f"[IRIS] DB migrated: added 'driver_id' to sessions")
    
    # Check for orphaned sessions and warn
    c.execute("SELECT session_id, vehicle_id FROM sessions WHERE end_time IS NULL AND uploaded=0")
    orphaned = c.fetchall()
    if orphaned:
        print(f"[IRIS] ⚠️  WARNING: {len(orphaned)} orphaned session(s) found:")
        for sid, vid in orphaned:
            print(f"       - Session {sid} ({vid}) - was this session interrupted?")
        print("[IRIS] These sessions will be archived as incomplete.")
        # Mark as incomplete instead of deleting
        for sid, _ in orphaned:
            c.execute("UPDATE sessions SET end_time=datetime('now'), uploaded=0 WHERE session_id=?", (sid,))
    
    # Also reset global session manager's active flag
    import session_manager as sm
    sm.session.active = False
    conn.commit()
    conn.close()

def insert_detection(timestamp, severity, confidence, bbox,
                     photo_path, location, session_id=None):
    conn = sqlite3.connect(config.DB_PATH)
    conn.execute('''INSERT INTO detections
                 (session_id,timestamp,severity,confidence,bbox,photo_path,location)
                 VALUES (?,?,?,?,?,?,?)''',
                 (session_id,timestamp,severity,confidence,str(bbox),photo_path,location))
    conn.commit(); conn.close()

def get_recent_detections(limit=50):
    conn = sqlite3.connect(config.DB_PATH)
    c = conn.cursor()
    c.execute('''SELECT id, session_id, timestamp, severity, confidence,
                        bbox, photo_path, location
                 FROM detections ORDER BY id DESC LIMIT ?''', (limit,))
    rows = c.fetchall(); conn.close(); return rows

def get_stats():
    conn = sqlite3.connect(config.DB_PATH)
    c = conn.cursor()
    c.execute('SELECT severity, COUNT(*) FROM detections GROUP BY severity')
    raw = dict(c.fetchall())
    conn.close()
    return {
        'High': raw.get('High', 0),
        'Medium': raw.get('Medium', 0),
        'Low': raw.get('Low', 0),
    }

def get_high_detections():
    return get_high_detections_by_vehicle()

def approve_detection(did):
    conn = sqlite3.connect(config.DB_PATH)
    conn.execute('UPDATE detections SET approved=1,declined=0 WHERE id=?',(did,))
    conn.commit(); conn.close()

def decline_detection(did):
    conn = sqlite3.connect(config.DB_PATH)
    conn.execute('UPDATE detections SET declined=1,approved=0 WHERE id=?',(did,))
    conn.commit(); conn.close()

def create_session(session_id, vehicle_id, route, start_time):
    conn = sqlite3.connect(config.DB_PATH)
    conn.execute('INSERT INTO sessions (session_id,vehicle_id,route,start_time) VALUES (?,?,?,?)',
                 (session_id,vehicle_id,route,start_time))
    conn.commit(); conn.close()

def end_session(session_id, end_time, duration, total, high, medium, low):
    conn = sqlite3.connect(config.DB_PATH)
    conn.execute('''UPDATE sessions SET end_time=?,duration_sec=?,total=?,
                    high=?,medium=?,low=?,uploaded=1 WHERE session_id=?''',
                 (end_time,duration,total,high,medium,low,session_id))
    conn.commit(); conn.close()

def get_all_sessions():
    conn = sqlite3.connect(config.DB_PATH)
    c = conn.cursor()
    c.execute('''SELECT id, session_id, vehicle_id, route, start_time,
                        end_time, duration_sec, total, high, medium, low,
                        uploaded, driver_id
                 FROM sessions ORDER BY id DESC''')
    rows = c.fetchall(); conn.close()
    return [{'id':r[0],'session_id':r[1],'vehicle_id':r[2],'route':r[3],
             'start_time':r[4],'end_time':r[5],'duration_sec':r[6],
             'total':r[7],'high':r[8],'medium':r[9],'low':r[10],
             'uploaded':r[11],'driver_id':r[12]} for r in rows]

def get_vehicle_summary():
    conn = sqlite3.connect(config.DB_PATH)
    c = conn.cursor()
    c.execute('''SELECT vehicle_id, COUNT(DISTINCT session_id),
                        SUM(total), SUM(high), SUM(medium), SUM(low), MAX(end_time)
                 FROM sessions GROUP BY vehicle_id ORDER BY SUM(total) DESC''')
    rows = c.fetchall(); conn.close()
    return [{'vehicle_id':r[0],'sessions':r[1],'total':r[2],
             'high':r[3],'medium':r[4],'low':r[5],'last_active':r[6]} for r in rows]

def get_high_detections_by_vehicle(vehicle_id=None):
    conn = sqlite3.connect(config.DB_PATH)
    c = conn.cursor()
    if vehicle_id:
        c.execute('''SELECT d.id, d.session_id, COALESCE(s.vehicle_id,'Unknown'),
                            d.timestamp, d.severity, d.confidence, d.bbox,
                            d.photo_path, d.location, d.approved, d.declined
                     FROM detections d
                     LEFT JOIN sessions s ON d.session_id = s.session_id
                     WHERE d.severity=? AND d.approved=0 AND d.declined=0
                       AND COALESCE(s.vehicle_id,'Unknown')=?
                     ORDER BY d.id DESC''', ('High', vehicle_id))
    else:
        c.execute('''SELECT d.id, d.session_id, COALESCE(s.vehicle_id,'Unknown'),
                            d.timestamp, d.severity, d.confidence, d.bbox,
                            d.photo_path, d.location, d.approved, d.declined
                     FROM detections d
                     LEFT JOIN sessions s ON d.session_id = s.session_id
                     WHERE d.severity=? AND d.approved=0 AND d.declined=0
                     ORDER BY d.id DESC''', ('High',))
    rows = c.fetchall(); conn.close()
    return [{'id':r[0],'session_id':r[1],'vehicle_id':r[2],'timestamp':r[3],
             'severity':r[4],'confidence':r[5],'bbox':r[6],'photo_path':r[7],
             'location':r[8],'approved':r[9],'declined':r[10]} for r in rows]

def get_approved_detections():
    conn = sqlite3.connect(config.DB_PATH)
    c = conn.cursor()
    c.execute('''SELECT d.id, d.timestamp, d.confidence, d.photo_path, d.location,
                        COALESCE(s.vehicle_id,'Unknown')
                 FROM detections d
                 LEFT JOIN sessions s ON d.session_id = s.session_id
                 WHERE d.severity=? AND d.approved=1
                 ORDER BY d.id DESC''', ('High',))
    rows = c.fetchall(); conn.close()
    return [{'id':r[0],'timestamp':r[1],'confidence':r[2],
             'photo_path':r[3],'location':r[4],'vehicle_id':r[5]} for r in rows]

def get_declined_detections():
    conn = sqlite3.connect(config.DB_PATH)
    c = conn.cursor()
    c.execute('''SELECT d.id, d.timestamp, d.confidence, d.photo_path, d.location,
                        COALESCE(s.vehicle_id,'Unknown')
                 FROM detections d
                 LEFT JOIN sessions s ON d.session_id = s.session_id
                 WHERE d.severity=? AND d.declined=1
                 ORDER BY d.id DESC''', ('High',))
    rows = c.fetchall(); conn.close()
    return [{'id':r[0],'timestamp':r[1],'confidence':r[2],
             'photo_path':r[3],'location':r[4],'vehicle_id':r[5]} for r in rows]

def get_session_detections(session_id):
    conn = sqlite3.connect(config.DB_PATH)
    c = conn.cursor()
    c.execute('''SELECT id,timestamp,severity,confidence,bbox,photo_path,
                        location,approved,declined
                 FROM detections WHERE session_id=? ORDER BY id''', (session_id,))
    rows = c.fetchall(); conn.close()
    return [{'id':r[0],'timestamp':r[1],'severity':r[2],'confidence':r[3],
             'bbox':r[4],'photo_path':r[5],'location':r[6],
             'approved':r[7],'declined':r[8]} for r in rows]


# ✨ NEW: Driver biometric functions

def get_detections_by_driver(driver_id, limit=100):
    """Get detections for a specific driver"""
    conn = sqlite3.connect(config.DB_PATH)
    c = conn.cursor()
    c.execute('''SELECT id, session_id, timestamp, severity, confidence, 
                        bbox, photo_path, location
                 FROM detections 
                 WHERE driver_id = ?
                 ORDER BY timestamp DESC LIMIT ?''', (driver_id, limit))
    rows = c.fetchall()
    conn.close()
    return [{'id': r[0], 'session_id': r[1], 'timestamp': r[2], 
             'severity': r[3], 'confidence': r[4], 'bbox': r[5],
             'photo_path': r[6], 'location': r[7]} for r in rows]


def get_sessions_by_driver(driver_id, limit=50):
    """Get inspection sessions for a specific driver"""
    conn = sqlite3.connect(config.DB_PATH)
    c = conn.cursor()
    c.execute('''SELECT id, session_id, vehicle_id, route, start_time, 
                        end_time, total, high, medium, low
                 FROM sessions 
                 WHERE driver_id = ?
                 ORDER BY start_time DESC LIMIT ?''', (driver_id, limit))
    rows = c.fetchall()
    conn.close()
    return [{'id': r[0], 'session_id': r[1], 'vehicle_id': r[2], 'route': r[3],
             'start_time': r[4], 'end_time': r[5], 'total': r[6], 
             'high': r[7], 'medium': r[8], 'low': r[9]} for r in rows]


def create_session_with_driver(session_id, driver_id, vehicle_id, route, start_time):
    """Create session with driver ID tracking"""
    conn = sqlite3.connect(config.DB_PATH)
    conn.execute('''INSERT INTO sessions 
                 (session_id, driver_id, vehicle_id, route, start_time) 
                 VALUES (?, ?, ?, ?, ?)''',
                 (session_id, driver_id, vehicle_id, route, start_time))
    conn.commit()
    conn.close()


def insert_detection_with_driver(timestamp, severity, confidence, bbox,
                                 photo_path, location, session_id=None, driver_id=None):
    """Insert detection with driver ID"""
    conn = sqlite3.connect(config.DB_PATH)
    conn.execute('''INSERT INTO detections
                 (session_id, driver_id, timestamp, severity, confidence, 
                  bbox, photo_path, location)
                 VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
                 (session_id, driver_id, timestamp, severity, confidence, 
                  str(bbox), photo_path, location))
    conn.commit()
    conn.close()



# ✨ NEW: Driver biometric functions

def get_detections_by_driver(driver_id, limit=100):
    """Get detections for a specific driver"""
    conn = sqlite3.connect(config.DB_PATH)
    c = conn.cursor()
    c.execute('''SELECT id, session_id, timestamp, severity, confidence, 
                        bbox, photo_path, location
                 FROM detections 
                 WHERE driver_id = ?
                 ORDER BY timestamp DESC LIMIT ?''', (driver_id, limit))
    rows = c.fetchall()
    conn.close()
    return [{'id': r[0], 'session_id': r[1], 'timestamp': r[2], 
             'severity': r[3], 'confidence': r[4], 'bbox': r[5],
             'photo_path': r[6], 'location': r[7]} for r in rows]


def get_sessions_by_driver(driver_id, limit=50):
    """Get inspection sessions for a specific driver"""
    conn = sqlite3.connect(config.DB_PATH)
    c = conn.cursor()
    c.execute('''SELECT id, session_id, vehicle_id, route, start_time, 
                        end_time, total, high, medium, low
                 FROM sessions 
                 WHERE driver_id = ?
                 ORDER BY start_time DESC LIMIT ?''', (driver_id, limit))
    rows = c.fetchall()
    conn.close()
    return [{'id': r[0], 'session_id': r[1], 'vehicle_id': r[2], 'route': r[3],
             'start_time': r[4], 'end_time': r[5], 'total': r[6], 
             'high': r[7], 'medium': r[8], 'low': r[9]} for r in rows]


def create_session_with_driver(session_id, driver_id, vehicle_id, route, start_time):
    """Create session with driver ID tracking"""
    conn = sqlite3.connect(config.DB_PATH)
    conn.execute('''INSERT INTO sessions 
                 (session_id, driver_id, vehicle_id, route, start_time) 
                 VALUES (?, ?, ?, ?, ?)''',
                 (session_id, driver_id, vehicle_id, route, start_time))
    conn.commit()
    conn.close()


def insert_detection_with_driver(timestamp, severity, confidence, bbox,
                                 photo_path, location, session_id=None, driver_id=None):
    """Insert detection with driver ID"""
    conn = sqlite3.connect(config.DB_PATH)
    conn.execute('''INSERT INTO detections
                 (session_id, driver_id, timestamp, severity, confidence, 
                  bbox, photo_path, location)
                 VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
                 (session_id, driver_id, timestamp, severity, confidence, 
                  str(bbox), photo_path, location))
    conn.commit()
    conn.close()
