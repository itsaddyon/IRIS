"""
IRIS Driver Management Module
Handles driver profiles, vehicle assignments, and route management
"""

import sqlite3
import json
import sys
from typing import Optional, Dict, List, Tuple
from datetime import datetime

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


class DriverManager:
    """Manage driver profiles and assignments"""
    
    def __init__(self, db_path: str = 'iris.db'):
        self.db_path = db_path
        self.current_driver = None  # Logged-in driver
        print("[DRIVER] ✓ Driver manager initialized")
    
    def get_driver_info(self, driver_id: int) -> Optional[Dict]:
        """Get driver profile information"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT id, name, created_at 
                FROM drivers 
                WHERE id = ?
            """, (driver_id,))
            
            row = cursor.fetchone()
            conn.close()
            
            if row:
                return {
                    "driver_id": row[0],
                    "name": row[1],
                    "created_at": row[2]
                }
            return None
        
        except Exception as e:
            print(f"[DRIVER] Error getting driver info: {e}")
            return None
    
    def get_all_drivers(self) -> List[Dict]:
        """Get list of all enrolled drivers"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT id, name, created_at 
                FROM drivers 
                ORDER BY created_at DESC
            """)
            
            drivers = []
            for row in cursor.fetchall():
                drivers.append({
                    "driver_id": row[0],
                    "name": row[1],
                    "created_at": row[2]
                })
            
            conn.close()
            return drivers
        
        except Exception as e:
            print(f"[DRIVER] Error fetching drivers: {e}")
            return []
    
    def get_driver_vehicles_and_routes(self, driver_id: int) -> Dict:
        """Get assigned vehicles and routes for a driver"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT vehicles, routes 
                FROM driver_vehicles 
                WHERE driver_id = ?
            """, (driver_id,))
            
            row = cursor.fetchone()
            conn.close()
            
            if row:
                vehicles = json.loads(row[0]) if row[0] else []
                routes = json.loads(row[1]) if row[1] else []
                return {
                    "vehicles": vehicles,
                    "routes": routes
                }
            
            return {"vehicles": [], "routes": []}
        
        except Exception as e:
            print(f"[DRIVER] Error fetching vehicles/routes: {e}")
            return {"vehicles": [], "routes": []}
    
    def set_current_driver(self, driver_id: int, name: str) -> bool:
        """Set logged-in driver session"""
        self.current_driver = {
            "driver_id": driver_id,
            "name": name,
            "login_time": datetime.now().isoformat(),
            "vehicles": self.get_driver_vehicles_and_routes(driver_id)["vehicles"],
            "routes": self.get_driver_vehicles_and_routes(driver_id)["routes"]
        }
        print(f"[DRIVER] 👤 Session started: {name} (ID: {driver_id})")
        return True
    
    def get_current_driver(self) -> Optional[Dict]:
        """Get currently logged-in driver"""
        return self.current_driver
    
    def logout_driver(self) -> bool:
        """Logout current driver"""
        if self.current_driver:
            name = self.current_driver["name"]
            self.current_driver = None
            print(f"[DRIVER] 👋 Logged out: {name}")
            return True
        return False
    
    def filter_detections_by_driver(self, detections: List[Dict], 
                                   driver_id: int) -> List[Dict]:
        """
        Filter detections to show only those from driver's assigned vehicles
        """
        assigned_vehicles = self.get_driver_vehicles_and_routes(driver_id)["vehicles"]
        
        filtered = [
            d for d in detections 
            if d.get("vehicle_id") in assigned_vehicles
        ]
        
        return filtered
    
    def filter_sessions_by_driver(self, sessions: List[Dict], 
                                 driver_id: int) -> List[Dict]:
        """Filter inspection sessions by driver"""
        assigned_vehicles = self.get_driver_vehicles_and_routes(driver_id)["vehicles"]
        
        filtered = [
            s for s in sessions 
            if s.get("vehicle_id") in assigned_vehicles and 
               s.get("driver_id") == driver_id
        ]
        
        return filtered
    
    def get_driver_statistics(self, driver_id: int) -> Dict:
        """Get driver inspection statistics"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Total detections
            cursor.execute("""
                SELECT COUNT(*) FROM detections 
                WHERE driver_id = ?
            """, (driver_id,))
            total_detections = cursor.fetchone()[0]
            
            # Severity breakdown
            cursor.execute("""
                SELECT severity, COUNT(*) FROM detections 
                WHERE driver_id = ? 
                GROUP BY severity
            """, (driver_id,))
            
            severity_stats = {}
            for row in cursor.fetchall():
                severity_stats[row[0]] = row[1]
            
            # Total sessions
            cursor.execute("""
                SELECT COUNT(*) FROM sessions 
                WHERE driver_id = ?
            """, (driver_id,))
            total_sessions = cursor.fetchone()[0]
            
            conn.close()
            
            return {
                "total_detections": total_detections,
                "severity_breakdown": severity_stats,
                "total_sessions": total_sessions,
                "avg_per_session": total_detections // total_sessions if total_sessions > 0 else 0
            }
        
        except Exception as e:
            print(f"[DRIVER] Error calculating statistics: {e}")
            return {
                "total_detections": 0,
                "severity_breakdown": {},
                "total_sessions": 0,
                "avg_per_session": 0
            }
    
    def validate_vehicle_access(self, driver_id: int, vehicle_id: str) -> bool:
        """Check if driver is authorized to use this vehicle"""
        assigned_vehicles = self.get_driver_vehicles_and_routes(driver_id)["vehicles"]
        return vehicle_id in assigned_vehicles
    
    def validate_route_access(self, driver_id: int, route: str) -> bool:
        """Check if driver is authorized for this route"""
        assigned_routes = self.get_driver_vehicles_and_routes(driver_id)["routes"]
        return route in assigned_routes
    
    # ✨ NEW: Biometric enrollment and recognition methods
    
    def enroll_driver_biometric(self, driver_id: int, name: str, 
                               face_encoding, vehicles: List[str], 
                               routes: List[str]) -> Dict:
        """
        Enroll driver with biometric data for facial recognition.
        
        Args:
            driver_id: Driver ID (can be UUID)
            name: Driver full name
            face_encoding: Face encoding array
            vehicles: List of assigned vehicle IDs
            routes: List of assigned routes
            
        Returns:
            dict with enrollment status
        """
        try:
            # Import biometric manager
            from biometric import get_biometric_manager
            
            biometric_mgr = get_biometric_manager()
            
            # Store face encoding in biometric database
            bio_result = biometric_mgr.enroll_driver(driver_id, name, face_encoding)
            
            if not bio_result['success']:
                return bio_result
            
            # Store driver record in main database
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Insert or update driver record
            cursor.execute("""
                INSERT OR REPLACE INTO drivers (id, name, created_at)
                VALUES (?, ?, ?)
            """, (driver_id, name, datetime.now().isoformat()))
            
            # Store vehicle and route assignments
            cursor.execute("""
                INSERT OR REPLACE INTO driver_vehicles (driver_id, vehicles, routes)
                VALUES (?, ?, ?)
            """, (driver_id, json.dumps(vehicles), json.dumps(routes)))
            
            conn.commit()
            conn.close()
            
            print(f"[DRIVER] ✓ Biometric enrolled: {name} (ID: {driver_id})")
            
            return {
                'success': True,
                'driver_id': driver_id,
                'message': f'Driver {name} biometrically enrolled'
            }
        
        except Exception as e:
            print(f"[DRIVER] ✗ Biometric enrollment error: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def recognize_driver_biometric(self, face_encoding) -> Dict:
        """
        Recognize driver from face encoding.
        
        Args:
            face_encoding: Face encoding array from camera
            
        Returns:
            dict with driver info if recognized, else None
        """
        try:
            from biometric import get_biometric_manager
            
            biometric_mgr = get_biometric_manager()
            
            # Perform face recognition
            result = biometric_mgr.recognize_driver(face_encoding)
            
            if result['success']:
                driver_id = result['driver_id']
                
                # Get full driver profile
                driver_info = self.get_driver_info(driver_id)
                vehicle_routes = self.get_driver_vehicles_and_routes(driver_id)
                
                return {
                    'success': True,
                    'driver_id': driver_id,
                    'name': result['name'],
                    'confidence': result['confidence'],
                    'profile': driver_info,
                    'assigned_vehicles': vehicle_routes['vehicles'],
                    'assigned_routes': vehicle_routes['routes']
                }
            else:
                return {
                    'success': False,
                    'message': 'Driver not recognized - enrollment required'
                }
        
        except Exception as e:
            print(f"[DRIVER] ✗ Recognition error: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def update_driver_assignments(self, driver_id: int, 
                                 vehicles: List[str] = None, 
                                 routes: List[str] = None) -> Dict:
        """Update driver vehicle and route assignments."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            if vehicles is not None or routes is not None:
                current = self.get_driver_vehicles_and_routes(driver_id)
                
                v = vehicles if vehicles is not None else current['vehicles']
                r = routes if routes is not None else current['routes']
                
                cursor.execute("""
                    INSERT OR REPLACE INTO driver_vehicles (driver_id, vehicles, routes)
                    VALUES (?, ?, ?)
                """, (driver_id, json.dumps(v), json.dumps(r)))
                
                conn.commit()
            
            conn.close()
            return {'success': True, 'message': 'Assignments updated'}
        
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def get_driver_face_match_confidence(self, driver_id: int, 
                                        face_encoding) -> float:
        """Get face matching confidence for a specific driver."""
        try:
            from biometric import get_biometric_manager
            import numpy as np
            import face_recognition
            
            biometric_mgr = get_biometric_manager()
            
            # Get driver's stored encoding
            drivers_db = biometric_mgr.get_all_drivers()
            driver_data = next((d for d in drivers_db if d['driver_id'] == driver_id), None)
            
            if not driver_data:
                return 0.0
            
            # Compare faces
            distance = face_recognition.face_distance(
                [np.array(driver_data['encoding'])],
                face_encoding
            )[0]
            
            # Convert distance to confidence (0-1, higher is better)
            confidence = 1.0 - distance
            return float(max(0, min(1, confidence)))
        
        except Exception:
            return 0.0


_driver_manager = None


def get_driver_manager() -> DriverManager:
    """Get or create driver manager"""
    global _driver_manager
    if _driver_manager is None:
        _driver_manager = DriverManager()
    return _driver_manager
