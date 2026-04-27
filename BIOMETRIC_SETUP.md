# 🔐 IRIS Biometric Driver Recognition System

> **Facial Recognition & Driver Authentication for Road Inspection**

## 🎯 Overview

The IRIS Biometric system enables driver authentication and tracking through facial recognition. Instead of password-based login, drivers simply show their face to the camera for immediate authentication and session start.

**Key Features:**
- ✅ Real-time facial recognition
- ✅ Automatic driver enrollment
- ✅ Vehicle & route assignment
- ✅ Driver session tracking
- ✅ Performance metrics & statistics
- ✅ No passwords required

---

## 🚀 Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

**New packages added:**
- `face-recognition` - Facial recognition library
- `face_recognition_models` - Pre-trained face detection models

### 2. Start the Application

```bash
python main.py
```

The system will:
- Initialize the biometric database
- Start the web server
- Connect to camera
- Open dashboard

### 3. Access Biometric Login

Navigate to:
```
http://localhost:5000/login
```

---

## 📋 System Architecture

### Components

```
┌─────────────────────────────────────────────────────────┐
│                   IRIS Biometric System                  │
└─────────────────────────────────────────────────────────┘
                           │
        ┌──────────────────┼──────────────────┐
        │                  │                  │
    ┌───▼────┐         ┌───▼────┐        ┌───▼───────┐
    │ Webcam │         │ Encoder│        │ Detector  │
    │ Input  │────────▶│ Module │───────▶│ (YOLO)    │
    └────────┘         └────────┘        └───────────┘
                           │
        ┌──────────────────┼──────────────────┐
        │                  │                  │
    ┌───▼──────────┐   ┌──▼──────┐   ┌─────▼────┐
    │ Biometric DB │   │ Drivers │   │ Sessions │
    │ (faces)      │   │ Profile │   │ & Stats  │
    └──────────────┘   └─────────┘   └──────────┘
```

### Files

| File | Purpose |
|------|---------|
| `biometric.py` | Core facial recognition engine |
| `driver_manager.py` | Driver profile management |
| `web/templates/login.html` | Biometric login interface |
| `web/app.py` | Backend API & Socket events |
| `database/db_manager.py` | Database operations |

---

## 🔄 Workflow

### Driver Enrollment

```
1. Driver opens login page
2. Clicks "Scan Face" button
3. Webcam captures face
4. System extracts face encoding

IF Recognition Found:
└─▶ Auto-login to dashboard
   └─▶ Session starts automatically

IF No Recognition:
└─▶ Enrollment form appears
   ├─▶ Enter driver name
   ├─▶ Select assigned vehicles
   ├─▶ Select assigned routes
   └─▶ Complete enrollment
       └─▶ Face encoding stored
       └─▶ Driver profile created
       └─▶ Redirected to dashboard
```

### Driver Login (Subsequent)

```
1. Driver opens login page
2. Clicks "Scan Face" button
3. Webcam captures face
4. System recognizes driver
5. Auto-login & session starts
```

### Session Tracking

```
During Inspection:
├─▶ Driver ID linked to session
├─▶ All detections tagged with driver_id
├─▶ Real-time detection sync
└─▶ Statistics updated

After Session:
├─▶ Session summary calculated
├─▶ Driver stats updated
├─▶ Performance metrics recorded
└─▶ Report generated
```

---

## 🗄️ Database Schema

### `drivers` Table
```sql
driver_id          TEXT PRIMARY KEY
name              TEXT NOT NULL
email             TEXT
phone             TEXT
license_number    TEXT UNIQUE
assigned_vehicles TEXT (JSON)
assigned_routes   TEXT (JSON)
enrolled_at       TEXT
last_active       TEXT
total_sessions    INTEGER
total_detections  INTEGER
high_severity_count INTEGER
status            TEXT ('active'/'inactive')
```

### `driver_stats` Table
```sql
id                INTEGER PRIMARY KEY
driver_id         TEXT (FK → drivers)
session_id        TEXT
vehicle_id        TEXT
route             TEXT
start_time        TEXT
end_time          TEXT
duration          INTEGER (seconds)
total_detections  INTEGER
high_severity     INTEGER
medium_severity   INTEGER
low_severity      INTEGER
```

### `detections` Table (Enhanced)
```sql
... existing fields ...
driver_id         TEXT (NEW - links detection to driver)
```

---

## 🔌 Socket Events

### Client → Server

#### `biometric:capture_face`
Capture face from webcam
```javascript
socket.emit('biometric:capture_face', {}, (response) => {
  // response.success: bool
  // response.encoding: face encoding array
  // response.error: error message if failed
});
```

#### `biometric:recognize`
Recognize driver from face encoding
```javascript
socket.emit('biometric:recognize', 
  { encoding: faceEncoding }, 
  (response) => {
    // response.success: bool
    // response.driver: driver object if recognized
    // response.error: error message
  }
);
```

#### `biometric:enroll_driver`
Enroll new driver with biometric data
```javascript
socket.emit('biometric:enroll_driver', {
  name: 'Driver Name',
  vehicles: ['VEH-001', 'VEH-002'],
  routes: ['Route A', 'Route B'],
  face_encoding: encodingArray
}, (response) => {
  // response.success: bool
  // response.driver_id: assigned driver ID
  // response.message: confirmation message
});
```

### Server → Client

#### `driver_enrolled`
New driver successfully enrolled
```javascript
{
  driver_id: 'ABC123',
  name: 'Driver Name',
  vehicles: ['VEH-001'],
  routes: ['Route A']
}
```

---

## 📊 API Endpoints

### GET `/api/vehicles-and-routes`
Get available vehicles and routes for enrollment
```json
{
  "vehicles": [
    {"id": "VEH-001", "name": "Vehicle 1"},
    {"id": "VEH-002", "name": "Vehicle 2"}
  ],
  "routes": ["City Center", "Highway", "District"]
}
```

---

## 🛠️ Python API

### BiometricManager

```python
from biometric import get_biometric_manager

mgr = get_biometric_manager()

# Capture face from frame
result = mgr.capture_face(cv2_frame)
if result['success']:
    encoding = result['encoding']

# Enroll driver
result = mgr.enroll_driver('DRV001', 'John Doe', encoding)

# Recognize driver
result = mgr.recognize_driver(encoding)
if result['success']:
    print(f"Driver: {result['name']}")
    print(f"Confidence: {result['confidence']}")

# List all drivers
drivers = mgr.get_all_drivers()

# Delete driver
result = mgr.delete_driver('DRV001')
```

### DriverManager

```python
from driver_manager import get_driver_manager

mgr = get_driver_manager()

# Create driver
result = mgr.create_driver(
    'Jane Smith',
    email='jane@email.com',
    vehicles=['VEH-001'],
    routes=['Route A']
)

# Get driver info
driver = mgr.get_driver('DRV001')

# List all drivers
drivers = mgr.get_all_drivers()

# Record session
mgr.record_session(
    'DRV001', 'SESSION-ABC', 'VEH-001', 'Route A',
    '2024-01-15 08:00:00', '2024-01-15 16:00:00',
    {'total': 5, 'high': 1, 'medium': 2, 'low': 2}
)

# Get driver stats
stats = mgr.get_driver_stats('DRV001')

# Biometric enrollment
result = mgr.enroll_driver_biometric(
    'DRV001', 'Jane Smith', face_encoding,
    ['VEH-001'], ['Route A']
)

# Biometric recognition
result = mgr.recognize_driver_biometric(face_encoding)
```

---

## 🎨 UI Components

### Login Page (`web/templates/login.html`)

**Features:**
- Real-time webcam display
- "Scan Face" button
- Status indicators
- Error/success messages
- Enrollment form with vehicle/route selection
- Responsive mobile-friendly design

**Keyboard Shortcuts:**
- `Space` - Toggle camera
- `R` - Reset form
- `Enter` - Submit form

---

## 🔒 Security Considerations

### Face Encoding Storage
- Stored in pickle database (`database/driver_biometrics.pkl`)
- Not reversible to original image
- Can be backed up and transferred

### Biometric Matching
- Configurable tolerance threshold (default: 0.6)
- Confidence score for each match
- No password bypass possible

### Session Management
- Socket.IO authentication recommended for production
- CORS restrictions configured
- Session data encrypted in cookies

### Recommendations
- Use HTTPS in production
- Implement rate limiting on biometric endpoints
- Add audit logging for all authentication attempts
- Regular biometric database backups
- Multi-camera setup for liveness detection

---

## 🧪 Testing

### Manual Testing

1. **Test Enrollment:**
   - Go to `/login`
   - Click "Scan Face"
   - Complete enrollment form
   - Verify driver profile created

2. **Test Recognition:**
   - Log out
   - Go to `/login`
   - Click "Scan Face"
   - Verify automatic login

3. **Test Session Tracking:**
   - Start inspection session
   - Verify driver ID in detections
   - End session and check statistics

### Integration Testing

```bash
# Test biometric module
python -c "
from biometric import get_biometric_manager
mgr = get_biometric_manager()
print('✓ Biometric module loaded')
print('✓ Drivers:', len(mgr.get_all_drivers()))
"

# Test driver manager
python -c "
from driver_manager import get_driver_manager
mgr = get_driver_manager()
print('✓ Driver manager loaded')
print('✓ Drivers:', len(mgr.get_all_drivers()))
"
```

---

## 📈 Performance Metrics

### Driver Dashboard

Once a driver is logged in, the dashboard shows:
- Total sessions completed
- Total detections recorded
- High-severity violation count
- Average detections per session
- Performance badges
- Last active timestamp

### Statistics Available

```python
# Get driver statistics
stats = mgr.get_driver_stats('DRV001')

# Fields:
# - total_sessions: int
# - total_detections: int
# - high_severity_count: int
# - avg_confidence: float
# - last_active: datetime
```

---

## 🐛 Troubleshooting

### Camera Not Detected
```
Error: "No camera feed available"

Solution:
1. Check camera permissions
2. Ensure camera is not in use by another app
3. Restart application
4. Try different USB port (if external camera)
```

### No Face Detected
```
Error: "No face detected in frame"

Solution:
1. Ensure face is clearly visible
2. Good lighting in the room
3. Face directly facing camera
4. No excessive head tilt
5. Remove sunglasses/large hats
```

### Recognition Confidence Too Low
```
Solution:
1. Adjust tolerance in recognize_driver()
2. Re-enroll driver with multiple angles
3. Ensure consistent lighting during enrollment
```

### Biometric Database Corruption
```
Solution:
1. Backup: cp database/driver_biometrics.pkl database/driver_biometrics.pkl.bak
2. Delete corrupted: rm database/driver_biometrics.pkl
3. Restart app (will create new empty database)
4. Re-enroll drivers
```

---

## 📝 Example Usage

### Complete Enrollment Flow

```python
import cv2
from biometric import get_biometric_manager
from driver_manager import get_driver_manager

# Initialize managers
bio_mgr = get_biometric_manager()
drv_mgr = get_driver_manager()

# Capture frame from camera
cap = cv2.VideoCapture(0)
ret, frame = cap.read()
cap.release()

# Extract face encoding
result = bio_mgr.capture_face(frame)
if not result['success']:
    print(f"Error: {result['error']}")
    exit()

# Enroll driver
bio_result = bio_mgr.enroll_driver(
    'DRV-123',
    'John Smith',
    result['encoding']
)

# Create driver profile
drv_result = drv_mgr.create_driver(
    'John Smith',
    email='john@email.com',
    vehicles=['VEH-001', 'VEH-002'],
    routes=['Route A', 'Route B']
)

print(f"✓ Driver {bio_result['message']}")
print(f"✓ Driver {drv_result['message']}")
```

### Complete Recognition Flow

```python
import cv2
from biometric import get_biometric_manager
from driver_manager import get_driver_manager

bio_mgr = get_biometric_manager()
drv_mgr = get_driver_manager()

# Capture frame
cap = cv2.VideoCapture(0)
ret, frame = cap.read()
cap.release()

# Extract encoding
result = bio_mgr.capture_face(frame)
if not result['success']:
    print(f"Error: {result['error']}")
    exit()

# Recognize driver
rec_result = bio_mgr.recognize_driver(result['encoding'])

if rec_result['success']:
    driver_id = rec_result['driver_id']
    print(f"✓ Recognized: {rec_result['name']}")
    print(f"✓ Confidence: {rec_result['confidence']:.2%}")
    
    # Get full driver profile
    driver = drv_mgr.get_driver(driver_id)
    print(f"✓ Sessions: {driver['total_sessions']}")
    print(f"✓ Vehicles: {driver['assigned_vehicles']}")
else:
    print("✗ Driver not recognized - enrollment required")
```

---

## 🔗 Integration Points

### With Existing IRIS System

1. **Session Manager** (`session_manager.py`)
   - Start session with driver_id
   - Track driver throughout inspection

2. **Detection System** (`detector/`)
   - Tag detections with driver_id
   - Link to driver performance

3. **Dashboard** (`web/templates/dashboard.html`)
   - Display driver information
   - Show driver-specific metrics
   - Driver leaderboard

4. **Voice Alert** (`voice_alert.py`)
   - Driver-specific voice alerts
   - Personalized feedback

---

## 📚 References

- [face_recognition Documentation](https://face-recognition.readthedocs.io/)
- [OpenCV Face Detection](https://docs.opencv.org/master/db/d28/tutorial_cascade_classifier.html)
- [Socket.IO Events](https://python-socketio.readthedocs.io/)

---

## 📞 Support

For issues or questions:
1. Check the troubleshooting section
2. Review logs in console
3. Test with simplified examples
4. Ensure all dependencies installed: `pip install -r requirements.txt`

---

**Last Updated:** January 2025  
**Version:** 1.0 - Biometric System Launch  
**Team:** Grey Hats | Technomax 2026
