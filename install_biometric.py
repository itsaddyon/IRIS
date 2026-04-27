#!/usr/bin/env python3
"""
IRIS Biometric Implementation - Installation & Verification Script
Automates setup and testing of facial recognition system
"""

import os
import sys
import subprocess
import sqlite3
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

print("""
╔════════════════════════════════════════════════════════════════╗
║           IRIS BIOMETRIC DRIVER SYSTEM INSTALLER               ║
║          Facial Recognition & Driver Authentication            ║
╚════════════════════════════════════════════════════════════════╝
""")

SCRIPT_DIR = Path(__file__).parent
DB_PATH = SCRIPT_DIR / "iris.db"
BIOMETRIC_DB = SCRIPT_DIR / "database" / "driver_biometrics.pkl"

def step(num, title):
    """Print step header"""
    print(f"\n{'='*60}")
    print(f"  STEP {num}: {title}")
    print(f"{'='*60}")

def success(msg):
    """Print success message"""
    print(f"  ✓ {msg}")

def error(msg):
    """Print error message"""
    print(f"  ✗ {msg}", file=sys.stderr)

def warning(msg):
    """Print warning message"""
    print(f"  ⚠ {msg}")

def check_python_version():
    """Verify Python 3.8+"""
    step(1, "Checking Python Version")
    version = sys.version_info
    if version.major >= 3 and version.minor >= 8:
        success(f"Python {version.major}.{version.minor}.{version.micro}")
        return True
    else:
        error(f"Python 3.8+ required (found {version.major}.{version.minor})")
        return False

def install_dependencies():
    """Install required packages"""
    step(2, "Installing Dependencies")
    
    print("  Installing from requirements.txt...")
    result = subprocess.run(
        [sys.executable, "-m", "pip", "install", "-r", str(SCRIPT_DIR / "requirements.txt")],
        capture_output=True,
        text=True
    )
    
    if result.returncode == 0:
        success("All packages installed successfully")
    else:
        error("Package installation failed")
        print(result.stderr)
        return False

    print("  Installing face-recognition package...")
    face_result = subprocess.run(
        [sys.executable, "-m", "pip", "install", "face-recognition==1.3.0", "--no-deps"],
        capture_output=True,
        text=True
    )

    if face_result.returncode == 0:
        success("face-recognition installed successfully")
        return True

    error("face-recognition package installation failed")
    print(face_result.stderr)
    return False

def verify_biometric_module():
    """Test biometric module import"""
    step(3, "Verifying Biometric Module")
    
    try:
        sys.path.insert(0, str(SCRIPT_DIR))
        import biometric
        success("biometric.py module loaded")
        
        from biometric import get_biometric_manager
        mgr = get_biometric_manager()
        success("BiometricManager initialized")
        
        drivers = mgr.get_all_drivers()
        success(f"Biometric database accessible ({len(drivers)} drivers enrolled)")
        return True
    except Exception as e:
        error(f"Biometric module error: {e}")
        return False

def verify_driver_manager():
    """Test driver manager import"""
    step(4, "Verifying Driver Manager")
    
    try:
        import driver_manager
        success("driver_manager.py module loaded")
        
        from driver_manager import get_driver_manager
        mgr = get_driver_manager()
        success("DriverManager initialized")
        
        drivers = mgr.get_all_drivers()
        success(f"Driver database accessible ({len(drivers)} drivers)")
        return True
    except Exception as e:
        error(f"Driver manager error: {e}")
        return False

def verify_database_schema():
    """Verify database tables"""
    step(5, "Verifying Database Schema")
    
    try:
        conn = sqlite3.connect(str(DB_PATH))
        c = conn.cursor()
        
        # Check for required tables
        tables = ['drivers', 'driver_stats', 'sessions', 'detections']
        c.execute("SELECT name FROM sqlite_master WHERE type='table'")
        existing_tables = [row[0] for row in c.fetchall()]
        
        for table in tables:
            if table in existing_tables:
                success(f"Table '{table}' exists")
            else:
                warning(f"Table '{table}' not found (will be created on first use)")
        
        conn.close()
        return True
    except Exception as e:
        error(f"Database error: {e}")
        return False

def verify_web_files():
    """Check web files exist"""
    step(6, "Verifying Web Files")
    
    files = [
        "web/app.py",
        "web/templates/login.html",
        "web/templates/dashboard.html",
        "web/static/dashboard.js",
        "web/static/style.css"
    ]
    
    all_exist = True
    for file in files:
        path = SCRIPT_DIR / file
        if path.exists():
            success(f"{file}")
        else:
            error(f"{file} NOT FOUND")
            all_exist = False
    
    return all_exist

def test_face_recognition():
    """Test face recognition library"""
    step(7, "Testing Face Recognition Library")
    
    try:
        import face_recognition
        success("face_recognition library loaded")
        
        # Test basic functionality
        import numpy as np
        import cv2
        
        # Create dummy face encoding
        test_encoding = np.random.rand(128)
        success(f"Created test encoding ({len(test_encoding)} dimensions)")
        
        return True
    except ImportError as e:
        warning(f"face_recognition not available: {e}")
        warning("Install with: pip install face-recognition")
        return False
    except Exception as e:
        error(f"Face recognition test failed: {e}")
        return False

def test_web_framework():
    """Test Flask and SocketIO"""
    step(8, "Testing Web Framework")
    
    try:
        from importlib.metadata import version
        import flask
        success(f"Flask {version('flask')} loaded")
        
        import flask_socketio
        success(f"Flask-SocketIO {version('flask-socketio')} loaded")
        
        return True
    except ImportError as e:
        error(f"Web framework error: {e}")
        return False
    except Exception as e:
        error(f"Web framework test failed: {e}")
        return False

def generate_test_config():
    """Create test configuration"""
    step(9, "Generating Test Configuration")
    
    config_content = """
# IRIS Biometric Test Configuration
DEBUG = True
VIDEO_MODE = 'FILE'  # 'FILE', 'IP', or 'LOCAL'
VIDEO_IP = 'http://192.168.x.x:8080/video'

# Biometric settings
FACE_RECOGNITION_TOLERANCE = 0.6
FACE_RECOGNITION_MODEL = 'hog'  # 'hog' or 'cnn'

# Camera settings
CAMERA_ID = 0
CAMERA_WIDTH = 640
CAMERA_HEIGHT = 480
CAMERA_FPS = 30

# Session settings
SESSION_TIMEOUT = 3600  # 1 hour
BIOMETRIC_CAPTURE_TIMEOUT = 10  # seconds
"""
    
    try:
        config_path = SCRIPT_DIR / "biometric_config.py"
        with open(config_path, 'w') as f:
            f.write(config_content)
        success(f"Test config created: {config_path}")
        return True
    except Exception as e:
        error(f"Config generation failed: {e}")
        return False

def show_quick_start():
    """Display quick start instructions"""
    step(10, "Quick Start Guide")
    
    print("""
  1. INSTALL DEPENDENCIES:
     $ pip install -r requirements.txt
     $ pip install face-recognition==1.3.0 --no-deps

  2. START THE APPLICATION:
     $ python main.py

  3. OPEN BIOMETRIC LOGIN:
     Navigate to: http://localhost:5000/login

  4. TEST ENROLLMENT:
     - Click "🎥 Scan Face"
     - Point your face at camera
     - Complete enrollment form
     - Select vehicles and routes

  5. TEST RECOGNITION:
     - Log out
     - Go back to login
     - Click "Scan Face"
     - Should auto-login

  📚 DOCUMENTATION:
     See BIOMETRIC_SETUP.md for complete guide

  🔗 KEY FILES:
     • biometric.py - Facial recognition engine
     • driver_manager.py - Driver management
     • web/templates/login.html - Biometric UI
     • web/app.py - Backend API
     • database/db_manager.py - Database functions
    """)
    return True

def main():
    """Run all verification steps"""
    
    results = {
        "Python Version": check_python_version(),
        "Dependencies": install_dependencies(),
        "Biometric Module": verify_biometric_module(),
        "Driver Manager": verify_driver_manager(),
        "Database Schema": verify_database_schema(),
        "Web Files": verify_web_files(),
        "Face Recognition": test_face_recognition(),
        "Web Framework": test_web_framework(),
        "Test Config": generate_test_config(),
        "Quick Start": show_quick_start(),
    }
    
    # Summary
    print(f"\n{'='*60}")
    print("  INSTALLATION SUMMARY")
    print(f"{'='*60}\n")
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for name, result in results.items():
        status = "✓" if result else "✗"
        print(f"  {status} {name}")
    
    print(f"\n  Result: {passed}/{total} checks passed\n")
    
    if passed == total:
        print("  ✓✓✓ Installation complete! Ready to run IRIS Biometric System")
        print(f"\n  Next: python main.py\n")
        return 0
    else:
        print("  ⚠ Some checks failed. Review errors above.")
        print(f"\n  Missing: {total - passed} dependencies/issues\n")
        return 1

if __name__ == "__main__":
    sys.exit(main())
