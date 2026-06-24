# IRIS Project Architecture

## Overview

IRIS (Intelligent Road Inspection System) is organized as a modular inspection platform. The system captures road imagery, detects potholes with a YOLO-based model, classifies severity, stores structured inspection data, displays live status to field operators, and provides municipal review tools for validation and reporting.

## Detection Pipeline

The detection pipeline begins in `main.py` and uses components from the `detector/` package.

```text
Video Source
    |
    v
Frame Capture
    |
    v
YOLOv8 Detection
    |
    v
Duplicate Filtering
    |
    v
Severity Classification
    |
    v
Annotation + Event Handling
```

### Pipeline Components

| Component | File | Responsibility |
| --- | --- | --- |
| Video source | `detector/video_source.py` | Opens webcam, video file, or IP camera stream. |
| Model inference | `detector/yolo_detector.py` | Runs YOLOv8 detection on frames. |
| Deduplication | `detector/deduplicator.py` | Reduces repeated detections across frames. |
| Severity classification | `detector/severity.py` | Classifies detections by bounding-box area. |
| Annotation | `detector/frame_annotator.py` | Draws detection overlays on video frames. |
| Event loop | `main.py` | Coordinates detection, alerts, storage, and dashboard updates. |

## Dashboard Workflow

The dashboard layer is implemented through Flask and Socket.IO in `web/app.py`.

### Field Dashboard

The field dashboard supports:

- live camera feed;
- inspection-session start and stop controls;
- severity counters;
- detection timeline and charts;
- live detection feed;
- hardware/alert state visualization.

### Municipal Dashboard

The municipal dashboard supports:

- high-severity detection review;
- approval and decline decisions;
- approved detection map display;
- session review;
- report generation for approved detections.

## Database Design

IRIS uses SQLite for local persistence. The database schema is created and migrated by `database/db_manager.py`.

### Core Tables

| Table | Purpose |
| --- | --- |
| `detections` | Stores detection timestamp, severity, confidence, bounding box, photo path, location, approval state, and optional AI metadata. |
| `sessions` | Stores inspection session metadata, route, vehicle, timing, duration, and severity totals. |
| `drivers` | Preserved driver table used by the archived biometric module. |
| `driver_vehicles` | Preserved vehicle/route mapping table used by the archived biometric module. |

### Detection Record Fields

The detection record stores:

- session identifier;
- timestamp;
- severity;
- confidence;
- bounding-box metadata;
- snapshot path;
- location string;
- approval and decline status;
- optional Gemini analysis fields.

## GIS Integration

IRIS captures location data for high-severity detections when Windows Location API support is available through `gps.py`. Approved detections with location data can be displayed on the municipal map using Leaflet and OpenStreetMap.

The GIS workflow is:

1. High-severity detection occurs.
2. System attempts to capture current location.
3. Location is stored with the detection record.
4. Municipal reviewer approves the detection.
5. Approved detection appears in map-focused views.

## Municipal Approval Workflow

```text
High Detection Stored
        |
        v
Municipal Dashboard Queue
        |
        +--> Approve --> Approved Map + Report Eligibility
        |
        +--> Decline --> Removed from Pending Queue
```

Approval state is stored in the local database using `approved` and `declined` fields. Approved detections can be included in report generation through `web/report.py`.

## Hardware Integration

Hardware feedback is optional and handled through `arduino_controller.py`.

Supported hardware-oriented feedback:

- severity-specific LED indication;
- buzzer alerts;
- serial communication with Arduino-compatible boards;
- fallback behavior when hardware is disconnected or unavailable.

Arduino sketches and wiring notes are stored in `arduino/`.

## Optional Cloud And AI Services

### Firebase / Firestore

When a local `firestore-key.json` service-account key is present, IRIS can initialize Firebase Admin SDK and store high-severity detections in Firestore. The private key is intentionally excluded from Git.

### Gemini Analysis

When `GEMINI_API_KEY` is available, high-severity detections can be enriched with incident analysis, recommended action, impact estimate, and priority.

## Biometric Module Status

The face biometric authentication module is archived in `face_scan/` and disconnected from the active login flow. It is preserved for future redesign with stronger privacy controls, consent handling, encryption, and deletion workflows.
