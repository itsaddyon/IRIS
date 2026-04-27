"""
session_manager.py — Manages inspection sessions for IRIS.

Real-world flow:
  Driver starts vehicle → clicks Start Session → IRIS begins detecting
  Vehicle completes route → driver clicks End Session
  → All session data uploads to municipal dashboard as one report
  → Municipal officer reviews, approves, dispatches repair teams
"""

import time
import uuid
from datetime import datetime
from database.db_manager import create_session, end_session, get_session_detections

class SessionManager:
    def __init__(self):
        self.active       = False
        self.session_id   = None
        self.start_time   = None
        self.detection_count = 0
        self.high_count   = 0
        self.medium_count = 0
        self.low_count    = 0

    def start(self, vehicle_id='VEHICLE-01', route='City Route'):
        """Start a new inspection session."""
        self.session_id   = str(uuid.uuid4())[:12].upper()  # 12 chars for better entropy
        self.start_time   = datetime.now()
        self.active       = True
        self.vehicle_id   = vehicle_id
        self.route        = route
        self.detection_count = 0
        self.high_count   = 0
        self.medium_count = 0
        self.low_count    = 0
        create_session(self.session_id, vehicle_id, route,
                       self.start_time.strftime('%Y-%m-%d %H:%M:%S'))
        print(f"[IRIS] Session {self.session_id} started — {vehicle_id} | {route}")
        return self.session_id

    def record(self, severity):
        """Count a detection in the current session."""
        if not self.active:
            return
        self.detection_count += 1
        if severity == 'High':
            self.high_count += 1
        elif severity == 'Medium':
            self.medium_count += 1
        else:
            self.low_count += 1

    def end(self):
        """End the session and return summary for upload."""
        if not self.active:
            return None
        self.active = False
        end_time = datetime.now()
        duration = int((end_time - self.start_time).total_seconds())
        summary = {
            'session_id':   self.session_id,
            'vehicle_id':   self.vehicle_id,
            'route':        self.route,
            'start_time':   self.start_time.strftime('%Y-%m-%d %H:%M:%S'),
            'end_time':     end_time.strftime('%Y-%m-%d %H:%M:%S'),
            'duration_sec': duration,
            'total':        self.detection_count,
            'high':         self.high_count,
            'medium':       self.medium_count,
            'low':          self.low_count,
        }
        end_session(self.session_id, end_time.strftime('%Y-%m-%d %H:%M:%S'),
                    duration, self.detection_count,
                    self.high_count, self.medium_count, self.low_count)
        print(f"[IRIS] Session {self.session_id} ended — "
              f"{self.detection_count} detections in {duration}s")
        return summary

    def status(self):
        """Return current session status dict."""
        if not self.active:
            return {'active': False}
        elapsed = int((datetime.now() - self.start_time).total_seconds())
        return {
            'active':     True,
            'session_id': self.session_id,
            'vehicle_id': self.vehicle_id,
            'route':      self.route,
            'elapsed':    elapsed,
            'total':      self.detection_count,
            'high':       self.high_count,
            'medium':     self.medium_count,
            'low':        self.low_count,
        }

# Global session manager instance
session = SessionManager()
