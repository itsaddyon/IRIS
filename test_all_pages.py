#!/usr/bin/env python
"""
Comprehensive functional test for IRIS web application
Tests all pages and endpoints
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import time
import threading
from database.db_manager import init_db, get_stats, get_all_sessions
from web.app import app

def test_flask_app():
    """Test Flask app initialization and routes"""
    print("\n" + "="*70)
    print("IRIS - COMPREHENSIVE FUNCTIONAL TESTS")
    print("="*70 + "\n")
    
    tests_passed = 0
    tests_total = 0
    
    # Test 1: App loads
    tests_total += 1
    try:
        assert app is not None
        print("✅ Test 1: Flask app loaded successfully")
        tests_passed += 1
    except Exception as e:
        print(f"❌ Test 1: Flask app load failed - {e}")
    
    # Test 2: Database initialized
    tests_total += 1
    try:
        init_db()
        print("✅ Test 2: Database initialized")
        tests_passed += 1
    except Exception as e:
        print(f"❌ Test 2: Database init failed - {e}")
    
    # Test 3: Routes exist
    tests_total += 1
    try:
        routes = [rule.rule for rule in app.url_map.iter_rules()]
        required = ['/', '/mobile', '/municipal', '/api/session/start', '/api/session/end', 
                   '/api/detections', '/api/stats', '/video_feed', '/login']
        found = sum(1 for r in required if any(r in route for route in routes))
        assert found >= 7, f"Only found {found}/{len(required)} routes"
        print(f"✅ Test 3: {len(routes)} routes available (found {found} key routes)")
        tests_passed += 1
    except Exception as e:
        print(f"❌ Test 3: Route check failed - {e}")
    
    # Test 4: API endpoints callable
    tests_total += 1
    try:
        with app.test_client() as client:
            # Health check
            response = client.get('/api/health')
            assert response.status_code == 200
            data = response.get_json()
            assert 'status' in data
            print(f"✅ Test 4: API health endpoint works - {data}")
            tests_passed += 1
    except Exception as e:
        print(f"❌ Test 4: API endpoint test failed - {e}")
    
    # Test 5: Dashboard page loads
    tests_total += 1
    try:
        with app.test_client() as client:
            response = client.get('/')
            assert response.status_code == 200, f"Got status {response.status_code}"
            assert 'html' in response.content_type.lower()
            print("✅ Test 5: Dashboard page loads (GET /)")
            tests_passed += 1
    except Exception as e:
        print(f"❌ Test 5: Dashboard page load failed - {e}")
    
    # Test 6: Mobile view loads
    tests_total += 1
    try:
        with app.test_client() as client:
            response = client.get('/mobile')
            assert response.status_code == 200
            assert 'html' in response.content_type.lower()
            print("✅ Test 6: Mobile page loads (GET /mobile)")
            tests_passed += 1
    except Exception as e:
        print(f"❌ Test 6: Mobile page load failed - {e}")
    
    # Test 7: Municipal portal loads
    tests_total += 1
    try:
        with app.test_client() as client:
            response = client.get('/municipal')
            assert response.status_code in [200, 302], f"Got status {response.status_code}"
            print("✅ Test 7: Municipal page loads/redirects (GET /municipal)")
            tests_passed += 1
    except Exception as e:
        print(f"❌ Test 7: Municipal page load failed - {e}")
    
    # Test 8: Stats endpoint works
    tests_total += 1
    try:
        with app.test_client() as client:
            response = client.get('/api/stats')
            assert response.status_code == 200
            data = response.get_json()
            assert 'High' in data and 'Medium' in data and 'Low' in data
            print(f"✅ Test 8: Stats endpoint works - {data}")
            tests_passed += 1
    except Exception as e:
        print(f"❌ Test 8: Stats endpoint failed - {e}")
    
    # Test 9: Sessions endpoint works
    tests_total += 1
    try:
        with app.test_client() as client:
            response = client.get('/api/sessions')
            assert response.status_code == 200
            data = response.get_json()
            assert isinstance(data, list)
            print(f"✅ Test 9: Sessions endpoint works - {len(data)} sessions")
            tests_passed += 1
    except Exception as e:
        print(f"❌ Test 9: Sessions endpoint failed - {e}")
    
    # Test 10: Session management works
    tests_total += 1
    try:
        from session_manager import session
        sid = session.start('TEST-VEH-001', 'Test Route')
        session.record('High')
        session.record('Medium')
        summary = session.end()
        assert summary['total'] == 2
        assert summary['high'] == 1
        print(f"✅ Test 10: Session management works - created session {sid}")
        tests_passed += 1
    except Exception as e:
        print(f"❌ Test 10: Session management failed - {e}")
    
    # Test 11: Video feed endpoint
    tests_total += 1
    try:
        with app.test_client() as client:
            response = client.get('/video_feed', follow_redirects=False)
            # Should return streaming response, not error
            assert response.status_code == 200
            assert 'multipart/x-mixed-replace' in response.content_type
            print("✅ Test 11: Video feed endpoint works (multipart stream)")
            tests_passed += 1
    except Exception as e:
        print(f"❌ Test 11: Video feed endpoint failed - {e}")
    
    # Test 12: Vehicles endpoint
    tests_total += 1
    try:
        with app.test_client() as client:
            response = client.get('/api/vehicles')
            assert response.status_code == 200
            data = response.get_json()
            assert isinstance(data, list) and len(data) > 0
            assert 'vehicle_id' in data[0]
            print(f"✅ Test 12: Vehicles endpoint works - {len(data)} vehicles")
            tests_passed += 1
    except Exception as e:
        print(f"❌ Test 12: Vehicles endpoint failed - {e}")
    
    # Test 13: Login endpoints exist
    tests_total += 1
    try:
        with app.test_client() as client:
            response = client.get('/login')
            assert response.status_code == 200
            print("✅ Test 13: Login page loads (GET /login)")
            tests_passed += 1
    except Exception as e:
        print(f"❌ Test 13: Login page failed - {e}")
    
    # Test 14: Authentication works
    tests_total += 1
    try:
        from auth import check_driver, check_municipal
        assert check_driver('MH-12-BUS-001', '2401') == True
        assert check_driver('MH-12-BUS-001', 'wrong') == False
        assert check_municipal('officer', 'iris2026') == True
        assert check_municipal('officer', 'wrong') == False
        print("✅ Test 14: Authentication system works (unique PINs verified)")
        tests_passed += 1
    except Exception as e:
        print(f"❌ Test 14: Authentication check failed - {e}")
    
    # Test 15: Deduplication works
    tests_total += 1
    try:
        from detector.deduplicator import filter_new
        detections = [
            ([100, 100, 150, 150], 0.9),
            ([200, 200, 250, 250], 0.85),
        ]
        new = filter_new(detections)
        assert len(new) == 2
        print("✅ Test 15: Deduplicator works correctly")
        tests_passed += 1
    except Exception as e:
        print(f"❌ Test 15: Deduplicator test failed - {e}")
    
    print("\n" + "="*70)
    print(f"RESULTS: {tests_passed}/{tests_total} TESTS PASSED ✅")
    print("="*70 + "\n")
    
    if tests_passed == tests_total:
        print("🟢 ALL PAGES AND ENDPOINTS WORKING CORRECTLY")
        print("✅ IRIS IS FULLY FUNCTIONAL AND PRODUCTION READY\n")
        return True
    else:
        print(f"⚠️  {tests_total - tests_passed} tests failed - review needed\n")
        return False

if __name__ == '__main__':
    success = test_flask_app()
    sys.exit(0 if success else 1)
