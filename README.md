# IRIS - Intelligent Road Inspection System

IRIS is a personal road-inspection project that detects potholes from a live camera feed, classifies severity, records inspection sessions, and gives municipal reviewers a dashboard for approving or declining high-severity detections. It also contains an archived face biometric authentication module, but biometric login is disconnected for now for security and privacy reasons.

The project combines local computer vision, a Flask dashboard, optional Arduino alerts, optional GPS capture, optional Gemini analysis, and optional Firebase/Firestore sync.

## Current Status

| Area | Status | Notes |
| --- | --- | --- |
| Pothole detection | Active | YOLOv8 model inference runs during an active inspection session. |
| Driver dashboard | Active | Live feed, session controls, detection counters, charts, and alerts. |
| Municipal dashboard | Active | Review high detections, approve/decline items, map approved reports, and generate PDF reports. |
| SQLite storage | Active | Local sessions, detections, approvals, and driver-related tables are stored in `iris.db`. |
| Firebase/Firestore | Optional | Enabled only when `firestore-key.json` exists locally. |
| Gemini analysis | Optional | Enabled only when `GEMINI_API_KEY` is provided. |
| Arduino alerts | Optional | Works when configured hardware is connected. |
| Biometric driver login | Disconnected for now | The biometric implementation is archived in `face_scan/` and is intentionally not wired into the active login flow for security and privacy reasons. |

## Important Security Note

Biometric authentication is not currently connected to the running app. The old facial-recognition code and backup login UI are preserved under `face_scan/` for future work, but the active app bypasses the biometric login wall and opens a default driver session.

This is intentional for now:

- biometric data should not be casually exposed in a public demo repository;
- local face embeddings and driver records can contain sensitive personal data;
- re-enabling biometric login should happen only after the storage, consent, access-control, and deletion flows are reviewed carefully.

Do not commit `iris.db`, biometric pickle files, face images, or any private driver data.

## Features

- Real-time pothole detection with YOLOv8.
- Low, Medium, and High severity classification based on bounding-box area.
- Live driver dashboard with camera stream, inspection controls, session timer, severity counters, charts, and detection feed.
- Municipal dashboard for high-severity review, approval, decline, map display, and report generation.
- Snapshot capture for high-severity detections.
- GPS location capture for high-severity detections when Windows Location API is available.
- Voice and Arduino alert hooks for driver feedback.
- Optional Gemini incident analysis for high-severity detections.
- Optional Firestore upload for cloud-backed detection records.
- Firebase Hosting configuration for static web deployment.

## Project Structure

```text
IRIS/
├── main.py                  # Application entry point and detection loop
├── config.py                # Local runtime configuration
├── auth.py                  # Simple municipal and vehicle PIN auth helpers
├── session_manager.py       # Inspection session state
├── gps.py                   # Windows GPS/location helper
├── voice_alert.py           # Voice alert helper
├── arduino_controller.py    # Arduino LED/buzzer integration
├── gemini_analyzer.py       # Optional Gemini analysis
├── database/
│   └── db_manager.py        # SQLite schema and queries
├── detector/
│   ├── yolo_detector.py     # YOLOv8 inference
│   ├── severity.py          # Severity classification
│   ├── frame_annotator.py   # Frame annotations
│   ├── video_source.py      # Webcam/video/IP camera source
│   └── deduplicator.py      # Duplicate detection filtering
├── face_scan/               # Archived biometric implementation
├── models/
│   └── best.pt              # Local YOLOv8 model weights, not tracked
├── snapshots/               # Generated high-severity snapshots, not tracked
└── web/
    ├── app.py               # Flask + Socket.IO server
    ├── report.py            # PDF report generation
    ├── static/              # CSS/JS
    └── templates/           # Dashboard and portal templates
```

## Requirements

- Python 3.11+
- A trained YOLOv8 model at `models/best.pt`
- A webcam, video file, or IP camera stream
- Optional: Arduino board connected over serial
- Optional: Firebase service-account key saved locally as `firestore-key.json`
- Optional: Gemini API key provided through `GEMINI_API_KEY`

## Setup

```powershell
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

Add the model weights locally:

```text
models/best.pt
```

The model file is intentionally ignored by Git. Use Git LFS, a release asset, or separate download instructions if you want to share it publicly.

## Configuration

Edit `config.py` for local camera and hardware settings.

Useful settings:

```python
VIDEO_MODE = "webcam"      # "webcam", "video", or "ip_camera"
VIDEO_PATH = "demo.mp4"
VIDEO_IP = "http://phone-ip:8080/video"
MODEL_PATH = "models/best.pt"
ARDUINO_ENABLED = True
ARDUINO_PORT = "COM12"
```

Set Gemini from the environment instead of hardcoding secrets:

```powershell
$env:GEMINI_API_KEY = "your-api-key"
```

For deployed or shared environments, also override the demo auth values:

```powershell
$env:IRIS_SECRET_KEY = "replace-with-a-long-random-secret"
$env:IRIS_OFFICER_PASSWORD = "replace-demo-password"
$env:IRIS_ADMIN_PASSWORD = "replace-demo-password"
$env:IRIS_PIN_MH_12_BUS_001 = "replace-demo-pin"
```

Firebase/Firestore is enabled only when a local `firestore-key.json` service account file exists. Keep that file private.

## Run

```powershell
python main.py
```

Then open:

| URL | Purpose |
| --- | --- |
| `http://localhost:5000/` | Redirects to the active driver dashboard |
| `http://localhost:5000/live` | Driver inspection dashboard |
| `http://localhost:5000/municipal/login` | Municipal login |
| `http://localhost:5000/municipal` | Municipal review dashboard |
| `http://localhost:5000/mobile` | Mobile-friendly field view |
| `http://localhost:5000/road_vision` | Road Vision view |

Default municipal demo credentials are currently available for local development:

```text
Username: officer
Password: iris2026
```

For a public or deployed project, override these credentials with environment variables or use a proper auth provider before exposing the app.

## How It Works

1. Start the app with `python main.py`.
2. The background detection loop connects to the configured video source.
3. The dashboard streams frames through Flask/Socket.IO.
4. When an inspection session starts, YOLOv8 runs on incoming frames.
5. New detections are classified as Low, Medium, or High.
6. High detections save a snapshot, try to capture GPS, trigger alerts, and optionally run Gemini analysis.
7. Detections and session stats are stored in SQLite.
8. Municipal users review high detections and approve or decline them.
9. Approved detections can be shown on the map and exported as a PDF report.

## Firebase And GitHub Hygiene

These Firebase files are normal to commit:

- `.firebaserc` if you are comfortable exposing the Firebase project ID
- `firebase.json`
- `firestore.rules`
- `firestore.indexes.json`

These should not be committed:

- `.firebase/` deploy cache files
- `firestore-key.json` service-account private key
- `.env` files
- generated databases such as `iris.db`
- biometric data files
- generated snapshots and reports
- local virtual environments and cache folders

If this becomes a polished public project, consider replacing the real Firebase project ID in `.firebaserc` with setup instructions or a sample file.

## Generated And Local-Only Files

The following files are local runtime artifacts and should stay out of Git:

```text
.firebase/
.venv/
__pycache__/
iris.db
firestore-key.json
snapshots/
_recording_frames/
IRIS_Report.pdf
models/best.pt
.env
```

## Utility Scripts

```powershell
python reset_db.py     # Reset local database/snapshots
python cleanup.py      # Remove temporary/cache files
```

## Tech Stack

| Layer | Technology |
| --- | --- |
| Detection | YOLOv8 / Ultralytics |
| Computer vision | OpenCV |
| Backend | Flask, Flask-SocketIO |
| Local database | SQLite |
| Frontend | HTML, CSS, JavaScript |
| Charts | Chart.js |
| Maps | Leaflet + OpenStreetMap |
| Reports | ReportLab |
| GPS | Windows Location API (`winsdk`) |
| Alerts | pyttsx3, Arduino serial |
| Optional AI analysis | Google Gemini |
| Optional cloud sync | Firebase Firestore |
| Optional hosting | Firebase Hosting |

## Known Limitations

- Biometric login is archived and disconnected for security reasons.
- Demo municipal credentials have development fallbacks and should be overridden before any real deployment.
- `config.py` still contains local machine settings such as camera URL and Arduino port.
- Demo auth fallbacks are still present for local development and should be overridden outside your machine.
- The app expects a local YOLO model at `models/best.pt`.
- Firestore sync depends on a local private key file.
- GPS support is Windows-specific.
- Arduino features require the configured serial hardware to be connected.

## Roadmap

- Move remaining local machine settings to environment variables where useful.
- Add a setup script or startup validation for missing model/camera/key files.
- Rebuild biometric auth with explicit consent, encrypted storage, and safe deletion flows.
- Add tests for detection persistence, session lifecycle, and municipal approval flows.
- Provide public model-download instructions or Git LFS setup.
- Add screenshots or a short demo video once the UI is finalized.
- Add a clear license file if the project is intended to be open source.

## License

No license file is currently included. Add a `LICENSE` file before presenting this as an open-source project.
