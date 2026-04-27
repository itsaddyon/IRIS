import os

# ─── Mode ────────────────────────────────────────────────
# 'webcam'    → USB webcam
# 'video'     → pre-recorded video file
# 'ip_camera' → phone camera over WiFi
VIDEO_MODE = 'ip_camera'
VIDEO_PATH = 'demo.mp4'

# IP Camera — Steps:
# 1. Turn ON Mobile Hotspot on your phone
# 2. Connect laptop to that hotspot
# 3. Open IP Webcam app → Settings:
#    - Video resolution: 640x480 (less lag, better for detection)
#    - Quality: 50% (balance speed vs quality)
#    - FPS limit: 15 (enough for detection, reduces WiFi load)
# 4. Tap 'Start server' → note IP shown → update below
VIDEO_IP = 'http://172.168.27.85:8080/video'

# ─── Model ───────────────────────────────────────────────
MODEL_PATH = os.path.join('models', 'best.pt')
CONFIDENCE_THRESHOLD = 0.45

# ─── Severity thresholds (bounding box area in pixels) ───
SEVERITY_LOW_MAX    = 3000
SEVERITY_MEDIUM_MAX = 8000
# anything above SEVERITY_MEDIUM_MAX = High → GPS + snapshot

# ─── Database ────────────────────────────────────────────
DB_PATH = 'iris.db'

# ─── Snapshots ───────────────────────────────────────────
SNAPSHOTS_DIR = 'snapshots'

# ─── Flask ───────────────────────────────────────────────
FLASK_HOST = '0.0.0.0'
FLASK_PORT = 5000
DEBUG = False

# ─── Arduino ─────────────────────────────────────────────
ARDUINO_MODE    = 'serial'  # USB cable to Arduino Uno
ARDUINO_ENABLED = True      # ← Arduino is connected via USB
ARDUINO_IP      = '192.168.1.105'
ARDUINO_PORT    = 'COM12'   # ← Arduino Uno on COM12
# ─── Google Gemini AI ───────────────────────────────────────
# Set via environment variable: GEMINI_API_KEY
# Get free key at: https://aistudio.google.com/apikey
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY', '')
GEMINI_ENABLED = True       # Enable AI-powered incident analysis