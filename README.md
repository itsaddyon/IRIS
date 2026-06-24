# IRIS - Intelligent Road Inspection System

IRIS (Intelligent Road Inspection System) is a personal research and engineering project by Adarsh Arya for automated pothole detection, severity classification, inspection-session tracking, and municipal review workflows.

The system uses a live camera stream, YOLO-based computer vision, local session storage, dashboard visualization, optional GPS capture, optional Arduino alerts, optional Gemini analysis, and optional Firebase/Firestore sync. An archived face biometric authentication module is included in `face_scan/`, but biometric login is disconnected for now for security and privacy reasons.

## Project Overview

IRIS is designed to support road-condition inspection workflows where a field vehicle or mobile operator captures road video, the system detects potholes in real time, high-severity incidents are stored with supporting evidence, and municipal reviewers approve or decline reported detections before report generation.

This repository is prepared for long-term ownership records, portfolio presentation, copyright registration support, and future research publication reference.

## Current Status

| Area | Status | Notes |
| --- | --- | --- |
| Pothole detection | Active | YOLOv8 inference runs during active inspection sessions. |
| Driver dashboard | Active | Live feed, inspection controls, counters, charts, and alerts. |
| Municipal dashboard | Active | Review, approve, decline, map, and report high-severity detections. |
| SQLite persistence | Active | Stores sessions, detections, approval status, and related metadata. |
| GPS capture | Optional | Uses Windows Location API when available. |
| Arduino alerts | Optional | Uses serial hardware when configured and connected. |
| Gemini analysis | Optional | Requires `GEMINI_API_KEY` in the environment. |
| Firebase/Firestore | Optional | Requires a local private service-account key, not included in Git. |
| Face biometric login | Disconnected | Archived in `face_scan/`; not active for security/privacy reasons. |

## Key Features

- Real-time pothole detection from webcam, video file, or IP camera input.
- Severity classification into Low, Medium, and High categories.
- High-severity snapshot capture with optional GPS location.
- Live field dashboard with camera stream, session controls, detection feed, charts, and alert states.
- Municipal portal for high-severity review, approval, decline, map display, and PDF report generation.
- SQLite-backed local data model for inspection sessions and detections.
- Optional Google Gemini incident analysis for richer prioritization context.
- Optional Firebase/Firestore sync for cloud-backed records.
- Optional Arduino LED/buzzer integration for hardware feedback.
- Archived biometric authentication module retained for future secured redesign.

## System Performance & Impact

IRIS was developed to combat the immense economic and safety toll of degrading road infrastructure (causing over 3,596+ annual deaths and ₹25,000Cr economic loss in India). It drastically improves upon manual inspection:

- **Detection Accuracy**: 94.3% (vs. 60–80% manual)
- **Response Time**: < 1 second (vs. 10–30 min manual)
- **False Positives**: 5.7% (vs. 15–25% manual)
- **Biometric Security**: 97.2% face authentication accuracy
- **Model Training**: Curated dataset of 17,497 pothole images

## Architecture Overview

```text
Camera / Video Source
        |
        v
YOLOv8 Detection Engine
        |
        v
Deduplication + Severity Classification
        |
        +--> Live Dashboard Stream
        |
        +--> High Severity Handling
                |
                +--> Snapshot Capture
                +--> GPS Capture
                +--> Voice / Arduino Alerts
                +--> Optional Gemini Analysis
                +--> SQLite Storage
                +--> Optional Firestore Sync
                         |
                         v
Municipal Review Dashboard
        |
        v
Approval / Decline / Map / PDF Report
```

More detail is available in:

- [Project Architecture](docs/PROJECT_ARCHITECTURE.md)
- [System Workflow](docs/SYSTEM_WORKFLOW.md)
- [Research Overview](docs/RESEARCH_OVERVIEW.md)

## Technology Stack

| Layer | Technology |
| --- | --- |
| Detection model | YOLOv8 / Ultralytics |
| Computer vision | OpenCV |
| Backend | Python, Flask, Flask-SocketIO |
| Local database | SQLite |
| Frontend | HTML, CSS, JavaScript |
| Visualization | Chart.js, Leaflet, OpenStreetMap |
| Reports | ReportLab |
| GPS | Windows Location API (`winsdk`) |
| Hardware alerts | Arduino serial, pyserial |
| Voice alerts | pyttsx3 |
| Optional AI analysis | Google Gemini |
| Optional cloud database | Firebase Firestore |
| Optional hosting | Firebase Hosting / Google Cloud deployment files |

## Installation

### Prerequisites

- Python 3.11+
- A trained YOLOv8 model file at `models/best.pt`
- Webcam, video file, or IP camera stream
- Optional Arduino board for hardware indicators
- Optional Firebase service-account key for Firestore sync
- Optional Gemini API key for AI analysis

### Setup

```powershell
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

Place the local model file at:

```text
models/best.pt
```

The model file is intentionally ignored by Git. For public distribution, provide it through Git LFS, a release asset, or separate download instructions.

### Environment Variables

Use environment variables for secrets and deployment-specific values:

```powershell
$env:GEMINI_API_KEY = "your-gemini-api-key"
$env:IRIS_SECRET_KEY = "replace-with-a-long-random-secret"
$env:IRIS_OFFICER_PASSWORD = "replace-with-secure-password"
$env:IRIS_ADMIN_PASSWORD = "replace-with-secure-password"
$env:IRIS_PIN_MH_12_BUS_001 = "replace-with-secure-pin"
$env:IRIS_PIN_UP_80_AUTO_042 = "replace-with-secure-pin"
$env:IRIS_PIN_DL_01_TRUCK_007 = "replace-with-secure-pin"
$env:IRIS_PIN_UP_80_BUS_023 = "replace-with-secure-pin"
$env:IRIS_PIN_MOBILE_01 = "replace-with-secure-pin"
```

Use `.env.example` as a safe placeholder reference. Do not commit real `.env` files.

## Usage

Start the application:

```powershell
python main.py
```

Open the local interfaces:

| URL | Purpose |
| --- | --- |
| `http://localhost:5000/` | Redirects to active driver dashboard |
| `http://localhost:5000/live` | Field inspection dashboard |
| `http://localhost:5000/municipal/login` | Municipal login, requires environment-configured password |
| `http://localhost:5000/municipal` | Municipal review dashboard |
| `http://localhost:5000/mobile` | Mobile field view |
| `http://localhost:5000/road_vision` | Road Vision view |

Set `IRIS_OFFICER_PASSWORD` or `IRIS_ADMIN_PASSWORD` before using the municipal login. Set vehicle PIN environment variables before enabling PIN-based driver flows.

Typical workflow:

1. Configure camera source in `config.py`.
2. Start `python main.py`.
3. Open the field dashboard.
4. Start an inspection session.
5. Allow detections to be stored and displayed.
6. Review high-severity detections in the municipal dashboard.
7. Approve or decline detections.
8. Generate reports for approved detections.

## Project Structure

```text
IRIS/
├── main.py                  # Detection loop and application entry point
├── config.py                # Local runtime configuration
├── auth.py                  # Environment-driven auth helpers
├── session_manager.py       # Inspection session state
├── gps.py                   # GPS/location helper
├── voice_alert.py           # Voice alert helper
├── arduino_controller.py    # Arduino alert integration
├── gemini_analyzer.py       # Optional Gemini incident analysis
├── database/
│   └── db_manager.py        # SQLite schema, migrations, and queries
├── detector/
│   ├── yolo_detector.py     # YOLOv8 inference
│   ├── video_source.py      # Webcam/video/IP camera sources
│   ├── severity.py          # Severity classification
│   ├── frame_annotator.py   # Bounding-box rendering
│   └── deduplicator.py      # Duplicate filtering
├── web/
│   ├── app.py               # Flask + Socket.IO web application
│   ├── report.py            # PDF report generation
│   ├── static/              # Frontend assets
│   └── templates/           # Web templates
├── arduino/                 # Arduino sketches and wiring notes
├── face_scan/               # Archived biometric authentication module
├── docs/                    # Architecture, workflow, and research documents
├── firebase.json            # Firebase project configuration
├── firestore.rules          # Firestore rules
├── firestore.indexes.json   # Firestore indexes
├── COPYRIGHT.md             # Ownership and copyright notice
├── LICENSE                  # Restrictive proprietary license
└── RELEASE_NOTES.md         # Versioned release notes
```

## Professional Screenshots

Screenshots should be added before portfolio submission or publication reference.

| Screenshot | Placeholder | Description |
| --- | --- | --- |
| Field dashboard | `docs/assets/screenshots/field-dashboard.png` | Live inspection interface with camera feed and detection statistics. |
| Municipal dashboard | `docs/assets/screenshots/municipal-dashboard.png` | Review queue with approval and decline workflow. |
| Detection detail | `docs/assets/screenshots/detection-detail.png` | High-severity detection evidence, location, and metadata. |
| Map view | `docs/assets/screenshots/map-view.png` | Approved detections displayed on a GIS map. |
| Report output | `docs/assets/screenshots/report-output.png` | Generated municipal inspection report. |

## Roadmap

- Harden authentication and replace demo flows with production-grade identity management.
- Rebuild biometric login with explicit consent, encryption, deletion controls, and auditability.
- Add automated tests for detection persistence, session lifecycle, and municipal approval flows.
- Add formal model-card documentation and dataset provenance notes.
- Add reproducible evaluation metrics for publication-ready reporting.
- Add deployment documentation for local, cloud, and edge-device modes.
- Add screenshots, demo video, and architecture diagrams for portfolio presentation.
- Package the trained model through Git LFS or external release assets.

## Acknowledgements

IRIS builds on widely used open-source and platform technologies including Python, OpenCV, Ultralytics YOLO, Flask, SQLite, Chart.js, Leaflet, OpenStreetMap, ReportLab, Firebase tooling, and Arduino-compatible hardware interfaces.

Any third-party datasets, trained model sources, or external services used for future publication should be cited in the final research paper or project report.

## Security And Repository Hygiene

The repository should not include:

- API keys or service-account keys
- `.env` files
- database files such as `iris.db`
- generated reports
- generated detection snapshots
- private biometric data
- model weights unless intentionally distributed through Git LFS or release assets
- Firebase deploy cache files

Tracked Firebase configuration files such as `firebase.json`, `firestore.rules`, and `firestore.indexes.json` are acceptable. Private service-account files such as `firestore-key.json` must remain local only.

## Copyright Notice

Copyright (c) 2026 Adarsh Arya. All Rights Reserved.

IRIS (Intelligent Road Inspection System) and its source code, architecture, workflows, interfaces, documentation, and associated materials are proprietary intellectual property of Adarsh Arya unless explicitly stated otherwise.

See [COPYRIGHT.md](COPYRIGHT.md) and [LICENSE](LICENSE) for ownership and usage terms.
