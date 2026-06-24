"""
auth.py — Simple authentication for IRIS.
Municipal officer and vehicle driver logins.
Uses Flask session for login state.
"""
import os

# Municipal officer credentials
MUNICIPAL_USERS = {
    'officer': os.environ.get('IRIS_OFFICER_PASSWORD', 'iris2026'),
    'admin': os.environ.get('IRIS_ADMIN_PASSWORD', 'iris2026'),
}

# Vehicle driver PINs — vehicle_id: PIN (UNIQUE per vehicle for security)
DRIVER_PINS = {
    'MH-12-BUS-001': os.environ.get('IRIS_PIN_MH_12_BUS_001', '2401'),
    'UP-80-AUTO-042': os.environ.get('IRIS_PIN_UP_80_AUTO_042', '5678'),
    'DL-01-TRUCK-007': os.environ.get('IRIS_PIN_DL_01_TRUCK_007', '9012'),
    'UP-80-BUS-023': os.environ.get('IRIS_PIN_UP_80_BUS_023', '3456'),
    'MOBILE-01': os.environ.get('IRIS_PIN_MOBILE_01', '7890'),
}

def check_municipal(username, password):
    return MUNICIPAL_USERS.get(username) == password

def check_driver(vehicle_id, pin):
    return DRIVER_PINS.get(vehicle_id) == pin
