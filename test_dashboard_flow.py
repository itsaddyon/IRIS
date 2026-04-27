"""
Test script for verifying IRIS dashboard flow
Tests: login → dashboard → video streaming → detections
"""
import requests
import json
import time
import socketio

BASE_URL = 'http://127.0.0.1:5000'

def test_api_endpoints():
    """Test that API endpoints are responding"""
    print("\n📋 Testing API endpoints...")
    
    # Test health check
    resp = requests.get(f'{BASE_URL}/api/health')
    print(f"✓ Health check: {resp.status_code}")
    assert resp.status_code == 200
    
    # Test vehicles endpoint
    resp = requests.get(f'{BASE_URL}/api/vehicles')
    print(f"✓ Vehicles endpoint: {resp.status_code}")
    assert resp.status_code == 200
    
    # Test detections endpoint
    resp = requests.get(f'{BASE_URL}/api/detections')
    print(f"✓ Detections endpoint: {resp.status_code}")
    assert resp.status_code == 200
    
    # Test stats endpoint
    resp = requests.get(f'{BASE_URL}/api/stats')
    print(f"✓ Stats endpoint: {resp.status_code}")
    assert resp.status_code == 200

def test_video_feed():
    """Test video feed endpoint"""
    print("\n🎥 Testing video feed...")
    
    resp = requests.get(f'{BASE_URL}/video_feed', stream=True)
    print(f"✓ Video feed: {resp.status_code}")
    assert resp.status_code == 200
    assert 'multipart/x-mixed-replace' in resp.headers.get('content-type', '')

def test_html_pages():
    """Test that HTML pages load correctly"""
    print("\n📄 Testing HTML pages...")
    
    # Test login page
    resp = requests.get(f'{BASE_URL}/login')
    print(f"✓ Login page: {resp.status_code}")
    assert resp.status_code == 200
    assert 'IRIS' in resp.text
    
    # Test road_vision page
    resp = requests.get(f'{BASE_URL}/road_vision')
    print(f"✓ Road Vision page: {resp.status_code}")
    assert resp.status_code in [200, 302]  # May redirect if not authenticated

def test_municipal_page():
    """Test municipal portal"""
    print("\n🏛️ Testing municipal portal...")
    
    # Without auth, should redirect to login
    resp = requests.get(f'{BASE_URL}/municipal', allow_redirects=False)
    print(f"✓ Municipal page (no auth): {resp.status_code} (should be 302 redirect)")
    assert resp.status_code == 302

def main():
    print("=" * 50)
    print("IRIS Dashboard Flow Test")
    print("=" * 50)
    
    try:
        test_api_endpoints()
        test_video_feed()
        test_html_pages()
        test_municipal_page()
        
        print("\n" + "=" * 50)
        print("✅ All tests passed!")
        print("=" * 50)
        print("\n✨ Dashboard is ready for testing:")
        print(f"   Login: {BASE_URL}/login")
        print(f"   Driver Dashboard: {BASE_URL}/ (after login)")
        print(f"   Municipal Portal: {BASE_URL}/municipal (after officer login)")
        
    except AssertionError as e:
        print(f"\n❌ Test failed: {e}")
        return False
    except Exception as e:
        print(f"\n❌ Error: {e}")
        return False
    
    return True

if __name__ == '__main__':
    success = main()
    exit(0 if success else 1)
