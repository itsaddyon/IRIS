"""
IRIS Biometric Authentication Module
Facial recognition for driver login & auto-enrollment
"""

import cv2
import face_recognition
import numpy as np
import os
import json
import sqlite3
import sys
from pathlib import Path
from typing import Optional, Dict, Tuple, List

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


class BiometricAuth:
    """Facial recognition engine for driver authentication"""
    
    def __init__(self, db_path: str = 'iris.db'):
        # Ensure we use absolute path for Windows compatibility
        if not os.path.isabs(db_path):
            db_path = os.path.join(os.getcwd(), db_path)
        self.db_path = db_path
        
        # Initialize database schema
        self._ensure_db_schema()
        
        self.face_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
        )
        self.known_face_encodings = []
        self.known_face_ids = []
        self.load_known_faces()
        
        print("[BIOMETRIC] ✓ Facial recognition engine initialized")
    
    def _ensure_db_schema(self):
        """Ensure database has proper schema before operations"""
        try:
            conn = sqlite3.connect(self.db_path, timeout=10.0)
            conn.isolation_level = None  # Autocommit
            cursor = conn.cursor()
            
            # Create drivers table if not exists
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS drivers (
                    id               INTEGER PRIMARY KEY AUTOINCREMENT,
                    name             TEXT NOT NULL UNIQUE,
                    facial_encoding  BLOB,
                    created_at       TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )''')
            
            # Create driver_vehicles table if not exists
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS driver_vehicles (
                    id        INTEGER PRIMARY KEY AUTOINCREMENT,
                    driver_id INTEGER NOT NULL UNIQUE,
                    vehicles  TEXT,
                    routes    TEXT,
                    FOREIGN KEY(driver_id) REFERENCES drivers(id)
                )''')
            
            conn.close()
            print(f"[BIOMETRIC] Database schema verified at {self.db_path}")
        except Exception as e:
            print(f"[BIOMETRIC] ⚠️  Schema error: {e}")
    
    def load_known_faces(self):
        """Load all enrolled driver faces from database"""
        try:
            conn = sqlite3.connect(self.db_path, timeout=10.0, check_same_thread=False)
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, name, facial_encoding 
                FROM drivers 
                WHERE facial_encoding IS NOT NULL
            """)
            rows = cursor.fetchall()
            
            self.known_face_encodings = []
            self.known_face_ids = []
            
            for driver_id, name, encoding_blob in rows:
                encoding = np.frombuffer(encoding_blob, dtype=np.float64)
                self.known_face_encodings.append(encoding)
                self.known_face_ids.append((driver_id, name))
            
            print(f"[BIOMETRIC] Loaded {len(self.known_face_encodings)} enrolled drivers")
            conn.close()
        except Exception as e:
            import traceback
            print(f"[BIOMETRIC] Error loading faces: {e}")
            traceback.print_exc()
    
    def detect_face_from_webcam(self, timeout: int = 10) -> Optional[np.ndarray]:
        """
        Capture face from webcam for recognition
        Returns: Face encoding or None if no face detected
        """
        cap = cv2.VideoCapture(0)
        start_time = cv2.getTickCount()
        
        print(f"[BIOMETRIC] 📹 Capturing face from webcam ({timeout}s timeout)...")
        
        while True:
            ret, frame = cap.read()
            if not ret:
                print("[BIOMETRIC] ❌ Failed to read from webcam")
                break
            
            # Convert to RGB for face_recognition
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            # Detect faces in current frame
            face_locations = face_recognition.face_locations(rgb_frame, model='hog')
            
            if face_locations:
                # Generate encoding for the detected face
                face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)
                
                if face_encodings:
                    cap.release()
                    print("[BIOMETRIC] ✓ Face captured successfully")
                    return face_encodings[0]  # Return first face encoding
            
            # Check timeout
            elapsed = (cv2.getTickCount() - start_time) / cv2.getTickFrequency()
            if elapsed > timeout:
                print(f"[BIOMETRIC] ⏱️  Timeout ({timeout}s) - no face detected")
                break
        
        cap.release()
        return None
    
    def recognize_driver(self, face_encoding: np.ndarray,
                        tolerance: float = 0.45) -> Optional[Dict]:
        """
        Recognize driver by comparing face encoding against database.

        Recognition gates:
          • Hard distance ceiling of `tolerance` (default 0.45, moderate strictness
            between library default of 0.6 and our previous 0.38).
          • Requires confidence ≥ 55 % (distance ≤ 0.45) when only one driver is
            enrolled — prevents false positives while allowing normal variations.
          • When multiple drivers are enrolled, requires the best distance to be
            meaningfully better than the second-best (gap ≥ 0.06) so a borderline
            match near a second candidate is rejected.

        Returns:
            {"driver_id": int, "name": str, "confidence": float} or None
        """
        if len(self.known_face_encodings) == 0:
            print("[BIOMETRIC] No enrolled drivers in database")
            return None

        face_distances = face_recognition.face_distance(
            self.known_face_encodings,
            face_encoding
        )

        if len(face_distances) == 0:
            return None

        best_idx      = int(np.argmin(face_distances))
        best_distance = float(face_distances[best_idx])
        confidence    = 1.0 - best_distance

        print(f"[BIOMETRIC] Best distance: {best_distance:.4f}  "
              f"Confidence: {confidence:.1%}  Tolerance: {tolerance}")

        # ── Primary gate: hard distance ceiling ───────────────────────────────
        if best_distance >= tolerance:
            print(f"[BIOMETRIC] ❌ Rejected — distance {best_distance:.4f} ≥ {tolerance}")
            return None

        # ── Single-driver gate ────────────────────────────────────────
        # When only 1 person is enrolled, argmin always picks them.
        # Require reasonable confidence to avoid obvious mismatches.
        if len(self.known_face_encodings) == 1:
            required = 0.45   # confidence must be > 55 % (distance ≤ 0.45)
            if best_distance > required:
                print(f"[BIOMETRIC] ❌ Rejected (single-driver gate) — "
                      f"distance {best_distance:.4f} > {required}")
                return None

        # ── Multi-driver separation gate ──────────────────────────────────────
        # If there are multiple drivers, make sure this person is clearly
        # different from the runner-up (avoid ambiguous matches).
        elif len(face_distances) > 1:
            sorted_dists = np.sort(face_distances)
            gap = float(sorted_dists[1] - sorted_dists[0])
            if gap < 0.06:
                print(f"[BIOMETRIC] ❌ Rejected — ambiguous match "
                      f"(gap {gap:.4f} < 0.06 between top-2 candidates)")
                return None

        driver_id, name = self.known_face_ids[best_idx]
        print(f"[BIOMETRIC] ✓ Recognised: {name}  "
              f"(distance={best_distance:.4f}, confidence={confidence:.1%})")

        return {
            "driver_id": driver_id,
            "name":      name,
            "confidence": confidence,
        }
    
    def enroll_new_driver(self, name: str, vehicles: List[str], 
                         routes: List[str], face_encoding: np.ndarray) -> Optional[int]:
        """
        Enroll new driver with facial biometric
        
        Args:
            name: Driver name
            vehicles: List of assigned vehicle IDs
            routes: List of allowed routes
            face_encoding: Face encoding from capture
        
        Returns:
            driver_id (int) or None if enrollment failed
        """
        try:
            # Ensure encoding is a proper numpy array
            if not isinstance(face_encoding, np.ndarray):
                face_encoding = np.array(face_encoding, dtype=np.float64)
            else:
                face_encoding = face_encoding.astype(np.float64)
            
            print(f"[BIOMETRIC] Encoding validation: shape={face_encoding.shape}, dtype={face_encoding.dtype}, size={face_encoding.size}")
            
            # ✓ Validate encoding has no NaN or Inf values
            if np.any(np.isnan(face_encoding)) or np.any(np.isinf(face_encoding)):
                print(f"[BIOMETRIC] ❌ Encoding contains NaN or Inf values - invalid encoding")
                return None
            
            # ✓ Validate encoding values are in reasonable range (-2.0 to 2.0)
            if np.min(face_encoding) < -2.0 or np.max(face_encoding) > 2.0:
                print(f"[BIOMETRIC] ⚠️  Encoding values out of typical range: min={np.min(face_encoding):.4f}, max={np.max(face_encoding):.4f}")
            
            # Connect with proper timeout for Windows
            conn = sqlite3.connect(self.db_path, timeout=10.0, check_same_thread=False)
            cursor = conn.cursor()
            
            # Store as BLOB - safe conversion
            try:
                encoding_blob = face_encoding.tobytes()
            except Exception as e:
                print(f"[BIOMETRIC] ❌ Failed to convert encoding to bytes: {e}")
                print(f"[BIOMETRIC]    Encoding stats: min={np.min(face_encoding):.6f}, max={np.max(face_encoding):.6f}, mean={np.mean(face_encoding):.6f}")
                raise
            
            # Insert driver
            cursor.execute("""
                INSERT INTO drivers (name, facial_encoding)
                VALUES (?, ?)
            """, (name, encoding_blob))
            
            driver_id = cursor.lastrowid
            
            # Store vehicle assignments
            vehicles_json = json.dumps(vehicles)
            routes_json = json.dumps(routes)
            
            cursor.execute("""
                INSERT INTO driver_vehicles (driver_id, vehicles, routes)
                VALUES (?, ?, ?)
            """, (driver_id, vehicles_json, routes_json))
            
            conn.commit()
            conn.close()
            
            # Reload known faces
            self.load_known_faces()
            
            print(f"[BIOMETRIC] ✓ Enrolled driver: {name} (ID: {driver_id})")
            print(f"[BIOMETRIC]   Vehicles: {vehicles}")
            print(f"[BIOMETRIC]   Routes: {routes}")
            
            return driver_id
            
        except Exception as e:
            import traceback
            print(f"[BIOMETRIC] ❌ Enrollment failed: {e}")
            traceback.print_exc()
            return None
    
    def get_driver_vehicles(self, driver_id: int) -> Dict:
        """Get assigned vehicles and routes for a driver"""
        try:
            conn = sqlite3.connect(self.db_path, timeout=10.0, check_same_thread=False)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT vehicles, routes 
                FROM driver_vehicles 
                WHERE driver_id = ?
            """, (driver_id,))
            
            row = cursor.fetchone()
            conn.close()
            
            if row:
                vehicles = json.loads(row[0])
                routes = json.loads(row[1])
                return {"vehicles": vehicles, "routes": routes}
            
            return {"vehicles": [], "routes": []}
        
        except Exception as e:
            print(f"[BIOMETRIC] Error fetching driver vehicles: {e}")
            return {"vehicles": [], "routes": []}
    
    def update_driver_assignment(self, driver_id: int, vehicles: List[str], 
                                routes: List[str]) -> bool:
        """Update driver's vehicle & route assignments"""
        try:
            conn = sqlite3.connect(self.db_path, timeout=10.0, check_same_thread=False)
            cursor = conn.cursor()
            
            vehicles_json = json.dumps(vehicles)
            routes_json = json.dumps(routes)
            
            cursor.execute("""
                UPDATE driver_vehicles 
                SET vehicles = ?, routes = ? 
                WHERE driver_id = ?
            """, (vehicles_json, routes_json, driver_id))
            
            conn.commit()
            conn.close()
            
            print(f"[BIOMETRIC] ✓ Updated driver {driver_id}")
            return True
        
        except Exception as e:
            print(f"[BIOMETRIC] Error updating driver: {e}")
            return False


# Singleton instance
_biometric_engine = None


def get_biometric_engine() -> BiometricAuth:
    """Get or create biometric authentication engine"""
    global _biometric_engine
    if _biometric_engine is None:
        _biometric_engine = BiometricAuth()
    return _biometric_engine


def quick_face_capture() -> Optional[np.ndarray]:
    """Quick helper to capture face from webcam"""
    engine = get_biometric_engine()
    return engine.detect_face_from_webcam()


def quick_recognize() -> Optional[Dict]:
    """Quick helper to capture and recognize driver"""
    engine = get_biometric_engine()
    face_encoding = engine.detect_face_from_webcam()
    if face_encoding is not None:
        return engine.recognize_driver(face_encoding)
    return None
