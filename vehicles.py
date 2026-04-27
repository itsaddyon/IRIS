"""
vehicles.py — Pre-configured vehicle fleet for IRIS demo.
In production this would come from a database/API.
"""

FLEET = [
    {
        'vehicle_id':  'MH-12-BUS-001',
        'name':        'City Bus 001',
        'type':        'Bus',
        'route':       'NH-44 Agra North',
        'driver':      'Ramesh Kumar',
        'color':       '#ef4444',   # red
        'icon':        '🚌',
    },
    {
        'vehicle_id':  'UP-80-AUTO-042',
        'name':        'Auto Rickshaw 042',
        'type':        'Auto',
        'route':       'Ring Road Agra',
        'driver':      'Suresh Yadav',
        'color':       '#3b82f6',   # blue
        'icon':        '🛺',
    },
    {
        'vehicle_id':  'DL-01-TRUCK-007',
        'name':        'Inspection Truck 007',
        'type':        'Truck',
        'route':       'Yamuna Expressway',
        'driver':      'Mahesh Singh',
        'color':       '#22c55e',   # green
        'icon':        '🚛',
    },
    {
        'vehicle_id':  'UP-80-BUS-023',
        'name':        'City Bus 023',
        'type':        'Bus',
        'route':       'Fatehabad Road',
        'driver':      'Dinesh Verma',
        'color':       '#f97316',   # orange
        'icon':        '🚌',
    },
    {
        'vehicle_id':  'MOBILE-01',
        'name':        'Mobile Inspector',
        'type':        'Mobile',
        'route':       'Field Inspection',
        'driver':      'Field Officer',
        'color':       '#a855f7',   # purple
        'icon':        '📱',
    },
]

def get_vehicle(vehicle_id):
    """Get vehicle info by ID."""
    for v in FLEET:
        if v['vehicle_id'] == vehicle_id:
            return v
    return {
        'vehicle_id': vehicle_id,
        'name':       vehicle_id,
        'type':       'Unknown',
        'route':      'Unknown Route',
        'driver':     'Unknown',
        'color':      '#64748b',
        'icon':       '🚗',
    }

def get_all_vehicles():
    return FLEET
