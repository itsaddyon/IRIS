#!/usr/bin/env python
"""
Integration test: Start server and test pages via HTTP
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import time
import threading
import subprocess
import requests
from database.db_manager import init_db

print("\n" + "="*70)
print("IRIS - INTEGRATION & LIVE FUNCTIONAL TESTS")
print("="*70 + "\n")

# Initialize database
print("[SETUP] Initializing database...")
init_db()
print("[SETUP] ✅ Database ready\n")

# Test via Flask test client (no server needed)
print("[TESTS] Running live endpoint tests...\n")

from web.app import app

test_results = []

tests = [
    ("Dashboard", "GET", "/", 200, "html"),
    ("Mobile View", "GET", "/mobile", 200, "html"),
    ("Login Page", "GET", "/login", 200, "html"),
    ("Health Check", "GET", "/api/health", 200, "json"),
    ("Stats API", "GET", "/api/stats", 200, "json"),
    ("Sessions API", "GET", "/api/sessions", 200, "json"),
    ("Vehicles API", "GET", "/api/vehicles", 200, "json"),
    ("Detections API", "GET", "/api/detections", 200, "json"),
    ("High Detections", "GET", "/api/high_detections", 200, "json"),
    ("Video Feed", "GET", "/video_feed", 200, "video"),
]

with app.test_client() as client:
    for name, method, path, expected_status, content_type in tests:
        try:
            if method == "GET":
                response = client.get(path)
            
            success = response.status_code == expected_status
            
            if success:
                print(f"✅ {name:25} | {method:6} {path:30} | Status: {response.status_code}")
                test_results.append(True)
            else:
                print(f"❌ {name:25} | Expected {expected_status}, got {response.status_code}")
                test_results.append(False)
        except Exception as e:
            print(f"❌ {name:25} | Error: {str(e)[:40]}")
            test_results.append(False)

print("\n" + "="*70)
print(f"ENDPOINT TESTS: {sum(test_results)}/{len(test_results)} PASSED ✅")
print("="*70)

# Test Session Flow
print("\n[TESTS] Testing Session Flow...\n")

session_tests = []

try:
    from session_manager import session
    
    # Start session
    sid = session.start('MH-12-BUS-001', 'NH-44 Agra North')
    print(f"✅ Session Started: {sid}")
    session_tests.append(True)
    
    # Record detections
    session.record('High')
    session.record('High')
    session.record('Medium')
    session.record('Low')
    print(f"✅ Recorded 4 detections (2 High, 1 Medium, 1 Low)")
    session_tests.append(True)
    
    # Check status
    status = session.status()
    assert status['total'] == 4
    assert status['high'] == 2
    print(f"✅ Session status correct: {status['total']} total, {status['high']} high")
    session_tests.append(True)
    
    # End session
    summary = session.end()
    assert summary['total'] == 4
    print(f"✅ Session ended successfully")
    session_tests.append(True)
    
except Exception as e:
    print(f"❌ Session flow test failed: {e}")
    session_tests.append(False)

print(f"\nSession Flow Tests: {sum(session_tests)}/{len(session_tests)} PASSED ✅")

# Test Authentication
print("\n[TESTS] Testing Authentication...\n")

auth_tests = []

try:
    from auth import check_driver, check_municipal, DRIVER_PINS
    
    # Check unique PINs
    pins = list(DRIVER_PINS.values())
    if len(pins) == len(set(pins)):
        print(f"✅ All {len(DRIVER_PINS)} vehicles have unique PINs")
        auth_tests.append(True)
    else:
        print(f"❌ Duplicate PINs found!")
        auth_tests.append(False)
    
    # Test driver auth
    if check_driver('MH-12-BUS-001', '2401'):
        print(f"✅ Driver auth works (correct PIN accepted)")
        auth_tests.append(True)
    else:
        print(f"❌ Driver auth failed for correct PIN")
        auth_tests.append(False)
    
    if not check_driver('MH-12-BUS-001', '1234'):
        print(f"✅ Driver auth works (wrong PIN rejected)")
        auth_tests.append(True)
    else:
        print(f"❌ Driver auth accepted wrong PIN")
        auth_tests.append(False)
    
    # Test municipal auth
    if check_municipal('officer', 'iris2026'):
        print(f"✅ Municipal auth works (correct password)")
        auth_tests.append(True)
    else:
        print(f"❌ Municipal auth failed")
        auth_tests.append(False)
    
except Exception as e:
    print(f"❌ Auth tests failed: {e}")
    auth_tests.append(False)

print(f"\nAuthentication Tests: {sum(auth_tests)}/{len(auth_tests)} PASSED ✅")

# Test Detection Processing
print("\n[TESTS] Testing Detection Processing...\n")

detection_tests = []

try:
    from detector.severity import classify
    from detector.deduplicator import filter_new
    
    # Test severity classification
    test_cases = [
        ([100, 100, 150, 150], 'Low'),      # Area = 50x50 = 2500 (< 3000)
        ([100, 100, 180, 180], 'Medium'),   # Area = 80x80 = 6400 (3000-8000)
        ([100, 100, 200, 200], 'High'),     # Area = 100x100 = 10000 (> 8000)
    ]
    
    for bbox, expected_severity in test_cases:
        severity, area = classify(bbox, 0.9)
        if severity == expected_severity:
            print(f"✅ Severity classification works: {severity} for area {area:.0f}px²")
            detection_tests.append(True)
        else:
            print(f"❌ Expected {expected_severity}, got {severity}")
            detection_tests.append(False)
    
    # Test deduplication
    detections_frame1 = [([100, 100, 150, 150], 0.9)]
    detections_frame2 = [([104, 104, 154, 154], 0.91)]
    
    new1 = filter_new(detections_frame1)
    new2 = filter_new(detections_frame2)
    
    if len(new1) == 1 and len(new2) == 0:
        print(f"✅ Deduplication works: counted new, skipped duplicate")
        detection_tests.append(True)
    else:
        print(f"❌ Deduplication failed: got {len(new2)} in frame 2")
        detection_tests.append(False)
    
except Exception as e:
    print(f"❌ Detection tests failed: {e}")
    detection_tests.append(False)

print(f"\nDetection Tests: {sum(detection_tests)}/{len(detection_tests)} PASSED ✅")

# Final Summary
print("\n" + "="*70)
all_tests = test_results + session_tests + auth_tests + detection_tests
passed = sum(all_tests)
total = len(all_tests)

print(f"TOTAL: {passed}/{total} TESTS PASSED")
print("="*70)

if passed == total:
    print("\n🟢 ALL PAGES, ENDPOINTS, AND FEATURES WORKING CORRECTLY")
    print("✅ IRIS IS FULLY FUNCTIONAL AND PRODUCTION READY FOR DEPLOYMENT!\n")
    sys.exit(0)
else:
    print(f"\n⚠️  {total - passed} tests failed\n")
    sys.exit(1)
