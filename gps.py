"""
gps.py — Real GPS coordinates via Windows Location API (winsdk)
Only called for High severity detections.
Optimized to reuse event loop and cache GPS data.

Install: pip install winsdk
"""

import asyncio
import threading
import time

_gps_loop = None
_loop_lock = threading.Lock()
_last_coords = (None, None)
_last_fetch_time = 0
_gps_cache_ttl = 5  # Cache GPS for 5 seconds

def get_coordinates():
    """
    Returns (lat, lng) tuple from Windows GPS hardware.
    Falls back to None, None if GPS unavailable or times out.
    Uses cached data if fetched within last 5 seconds.
    """
    global _gps_loop, _last_coords, _last_fetch_time
    
    try:
        # Return cached data if fresh
        now = time.time()
        if _last_coords != (None, None) and (now - _last_fetch_time) < _gps_cache_ttl:
            return _last_coords
        
        from winsdk.windows.devices.geolocation import (
            Geolocator, PositionAccuracy, GeolocationAccessStatus
        )

        async def _fetch():
            locator = Geolocator()
            locator.desired_accuracy = PositionAccuracy.HIGH

            # Request access first (Windows 10+ requires permission)
            access = await Geolocator.request_access_async()
            if access != GeolocationAccessStatus.ALLOWED:
                print("[GPS] Access denied by Windows Location settings.")
                return None, None

            # Wait up to 8 seconds for a fix
            pos = await asyncio.wait_for(
                locator.get_geoposition_async(),
                timeout=8.0
            )
            coord = pos.coordinate
            lat = round(coord.latitude,  6)
            lng = round(coord.longitude, 6)
            return lat, lng

        # Use existing loop or create new one
        with _loop_lock:
            if _gps_loop is None or not _gps_loop.is_running():
                _gps_loop = asyncio.new_event_loop()
                asyncio.set_event_loop(_gps_loop)
            
            try:
                result = _gps_loop.run_until_complete(asyncio.wait_for(_fetch(), timeout=9))
                _last_coords = result
                _last_fetch_time = now
                return result
            except asyncio.TimeoutError:
                print("[GPS] Timed out waiting for GPS fix.")
                return None, None

    except ImportError:
        print("[GPS] winsdk not installed. Run: pip install winsdk")
        return None, None
    except Exception as e:
        print(f"[GPS] Error: {e}")
        return None, None


def get_location_string():
    """
    Returns formatted string 'lat,lng' for High severity detections.
    Returns None if GPS unavailable.
    """
    lat, lng = get_coordinates()
    if lat is not None and lng is not None:
        return f"{lat},{lng}"
    return None
