"""
auth.py — Simple authentication for IRIS.
Municipal officer and vehicle driver logins.
Uses Flask session for login state.
"""

# Municipal officer credentials
MUNICIPAL_USERS = {
    'officer':  'iris2026',
    'admin':    'iris2026',
}

# Vehicle driver PINs — vehicle_id: PIN (UNIQUE per vehicle for security)
DRIVER_PINS = {
    'MH-12-BUS-001':   '2401',
    'UP-80-AUTO-042':  '5678',
    'DL-01-TRUCK-007': '9012',
    'UP-80-BUS-023':   '3456',
    'MOBILE-01':       '7890',
}

def check_municipal(username, password):
    return MUNICIPAL_USERS.get(username) == password

def check_driver(vehicle_id, pin):
    return DRIVER_PINS.get(vehicle_id) == pin
