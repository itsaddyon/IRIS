"""
auth.py — Simple authentication for IRIS.
Municipal officer and vehicle driver logins.
Uses Flask session for login state.
"""
import os

# Municipal officer credentials
MUNICIPAL_USERS = {
    'officer': os.environ.get('IRIS_OFFICER_PASSWORD', ''),
    'admin': os.environ.get('IRIS_ADMIN_PASSWORD', ''),
}

# Vehicle driver PINs — vehicle_id: PIN (UNIQUE per vehicle for security)
DRIVER_PINS = {
    'MH-12-BUS-001': os.environ.get('IRIS_PIN_MH_12_BUS_001', ''),
    'UP-80-AUTO-042': os.environ.get('IRIS_PIN_UP_80_AUTO_042', ''),
    'DL-01-TRUCK-007': os.environ.get('IRIS_PIN_DL_01_TRUCK_007', ''),
    'UP-80-BUS-023': os.environ.get('IRIS_PIN_UP_80_BUS_023', ''),
    'MOBILE-01': os.environ.get('IRIS_PIN_MOBILE_01', ''),
}

def check_municipal(username, password):
    expected = MUNICIPAL_USERS.get(username)
    return bool(expected) and expected == password

def check_driver(vehicle_id, pin):
    expected = DRIVER_PINS.get(vehicle_id)
    return bool(expected) and expected == pin
