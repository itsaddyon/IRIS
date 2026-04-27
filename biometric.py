"""
biometric.py - Driver facial recognition and biometric enrollment system.
Handles face encoding, driver recognition, and biometric database management.
"""
import os
import pickle
import numpy as np
import cv2
import sqlite3
import config
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# Try to import face_recognition library
try:
    import face_recognition
    HAS_FACE_RECOGNITION = True
except ImportError:
    HAS_FACE_RECOGNITION = False
    print("⚠ face_recognition not installed. Install with: pip install face-recognition")


class BiometricManager:
    """Manages driver facial recognition and biometric enrollment."""
    
    def __init__(self):
        """Initialize biometric manager and ensure biometric database exists."""
        self.biometric_db = os.path.join(
            os.path.dirname(config.DB_PATH),
            'driver_biometrics.pkl'
        )
        self._ensure_biometric_db()
    
    def _ensure_biometric_db(self):
        """Create biometric database if it doesn't exist."""
        if not os.path.exists(self.biometric_db):
            with open(self.biometric_db, 'wb') as f:
                pickle.dump({}, f)
    
    def capture_face(self, frame):
        """
        Extract and encode face from video frame.
        
        Args:
            frame: OpenCV frame
            
        Returns:
            dict: {'success': bool, 'encoding': ndarray or None, 'error': str}
        """
        if frame is None:
            return {'success': False, 'encoding': None, 'error': 'No frame provided'}
        
        try:
            if not HAS_FACE_RECOGNITION:
                return {'success': False, 'encoding': None, 
                        'error': 'face_recognition library not available'}
            
            # Convert BGR to RGB
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            # Find faces in frame
            face_locations = face_recognition.face_locations(rgb_frame)
            face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)
            
            if not face_encodings:
                return {'success': False, 'encoding': None, 'error': 'No face detected in frame'}
            
            # Return the first face encoding
            encoding = face_encodings[0]
            return {'success': True, 'encoding': encoding, 'error': None}
        
        except Exception as e:
            return {'success': False, 'encoding': None, 'error': f'Face capture error: {str(e)}'}
    
    def enroll_driver(self, driver_id, driver_name, face_encoding):
        """
        Enroll a new driver with facial recognition data.
        
        Args:
            driver_id: Unique driver identifier
            driver_name: Full name of driver
            face_encoding: numpy array of face encoding
            
        Returns:
            dict: {'success': bool, 'driver_id': str, 'message': str}
        """
        try:
            # Load existing database
            with open(self.biometric_db, 'rb') as f:
                biometrics = pickle.load(f)
            
            # Store encoding (convert to list for pickle serialization)
            biometrics[driver_id] = {
                'name': driver_name,
                'encoding': face_encoding.tolist() if isinstance(face_encoding, np.ndarray) else face_encoding,
                'enrolled_at': __import__('datetime').datetime.now().isoformat()
            }
            
            # Save updated database
            with open(self.biometric_db, 'wb') as f:
                pickle.dump(biometrics, f)
            
            return {
                'success': True,
                'driver_id': driver_id,
                'message': f'Driver {driver_name} enrolled successfully'
            }
        
        except Exception as e:
            return {
                'success': False,
                'driver_id': None,
                'message': f'Enrollment error: {str(e)}'
            }
    
    def recognize_driver(self, face_encoding, tolerance=0.6):
        """
        Recognize driver from face encoding.
        
        Args:
            face_encoding: numpy array of face encoding
            tolerance: Distance threshold for recognition (0.0-1.0, lower = stricter)
            
        Returns:
            dict: {'success': bool, 'driver_id': str, 'name': str, 'confidence': float}
        """
        try:
            if not HAS_FACE_RECOGNITION:
                return {'success': False, 'driver_id': None, 'name': None, 'confidence': 0}
            
            # Load biometric database
            with open(self.biometric_db, 'rb') as f:
                biometrics = pickle.load(f)
            
            if not biometrics:
                return {'success': False, 'driver_id': None, 'name': None, 'confidence': 0}
            
            best_match_id = None
            best_distance = float('inf')
            
            # Compare against all enrolled drivers
            for driver_id, data in biometrics.items():
                stored_encoding = np.array(data['encoding'])
                distance = face_recognition.face_distance([stored_encoding], face_encoding)[0]
                
                if distance < best_distance:
                    best_distance = distance
                    best_match_id = driver_id
            
            # Check if match meets threshold
            if best_distance <= tolerance and best_match_id:
                driver_data = biometrics[best_match_id]
                confidence = 1.0 - best_distance  # Convert distance to confidence
                
                return {
                    'success': True,
                    'driver_id': best_match_id,
                    'name': driver_data['name'],
                    'confidence': float(confidence)
                }
            else:
                return {
                    'success': False,
                    'driver_id': None,
                    'name': None,
                    'confidence': 0
                }
        
        except Exception as e:
            return {
                'success': False,
                'driver_id': None,
                'name': None,
                'confidence': 0,
                'error': str(e)
            }
    
    def get_all_drivers(self):
        """Get list of all enrolled drivers."""
        try:
            with open(self.biometric_db, 'rb') as f:
                biometrics = pickle.load(f)
            
            return [{
                'driver_id': driver_id,
                'name': data['name'],
                'enrolled_at': data.get('enrolled_at', 'Unknown')
            } for driver_id, data in biometrics.items()]
        
        except Exception as e:
            return []
    
    def delete_driver(self, driver_id):
        """Delete driver from biometric database."""
        try:
            with open(self.biometric_db, 'rb') as f:
                biometrics = pickle.load(f)
            
            if driver_id in biometrics:
                del biometrics[driver_id]
                with open(self.biometric_db, 'wb') as f:
                    pickle.dump(biometrics, f)
                return {'success': True, 'message': f'Driver {driver_id} deleted'}
            else:
                return {'success': False, 'message': 'Driver not found'}
        
        except Exception as e:
            return {'success': False, 'message': str(e)}
    
    def export_biometric_profile(self, driver_id):
        """
        Export driver biometric profile for backup/transfer.
        
        Returns:
            dict with driver data or None
        """
        try:
            with open(self.biometric_db, 'rb') as f:
                biometrics = pickle.load(f)
            
            if driver_id in biometrics:
                return {
                    'driver_id': driver_id,
                    'data': biometrics[driver_id]
                }
            return None
        
        except Exception:
            return None
    
    def import_biometric_profile(self, driver_id, profile_data):
        """
        Import driver biometric profile from backup.
        
        Args:
            driver_id: Driver ID
            profile_data: Profile data dict with 'encoding' key
            
        Returns:
            dict with success status
        """
        try:
            with open(self.biometric_db, 'rb') as f:
                biometrics = pickle.load(f)
            
            biometrics[driver_id] = profile_data
            
            with open(self.biometric_db, 'wb') as f:
                pickle.dump(biometrics, f)
            
            return {'success': True, 'message': 'Profile imported successfully'}
        
        except Exception as e:
            return {'success': False, 'message': str(e)}


# Singleton instance
_biometric_manager = None

def get_biometric_manager():
    """Get or create biometric manager singleton."""
    global _biometric_manager
    if _biometric_manager is None:
        _biometric_manager = BiometricManager()
    return _biometric_manager


# ✨ Convenience functions for use throughout the app

def capture_and_encode(frame):
    """Capture face from frame and return encoding."""
    manager = get_biometric_manager()
    return manager.capture_face(frame)

def enroll(driver_id, name, encoding):
    """Enroll driver with face encoding."""
    manager = get_biometric_manager()
    return manager.enroll_driver(driver_id, name, encoding)

def recognize(encoding):
    """Recognize driver from face encoding."""
    manager = get_biometric_manager()
    return manager.recognize_driver(encoding)

def list_drivers():
    """List all enrolled drivers."""
    manager = get_biometric_manager()
    return manager.get_all_drivers()

def remove_driver(driver_id):
    """Remove driver from system."""
    manager = get_biometric_manager()
    return manager.delete_driver(driver_id)
