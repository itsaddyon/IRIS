# IRIS System Workflow

This document describes the complete operational workflow for IRIS, from camera input to municipal report generation.

## End-To-End Flow

```text
Camera Input
    |
    v
YOLO Detection
    |
    v
Severity Classification
    |
    v
GPS Capture
    |
    v
Database Storage
    |
    v
Dashboard Display
    |
    v
Municipal Review
    |
    v
Approval Process
    |
    v
Report Generation
```

## 1. Camera Input

IRIS reads frames from a configured source:

- USB webcam;
- pre-recorded video file;
- IP camera stream.

The source is configured in `config.py` and opened through `detector/video_source.py`.

## 2. YOLO Detection

During an active inspection session, frames are passed to the YOLOv8 detection module. The detector identifies pothole candidates and returns bounding boxes with confidence values.

The active inference step is skipped when no inspection session is running, allowing the dashboard to stream frames without recording detections.

## 3. Severity Classification

Each new detection is classified by bounding-box area:

| Severity | Meaning |
| --- | --- |
| Low | Smaller detection, logged with lower urgency. |
| Medium | Moderate detection, visible in dashboard stats. |
| High | Critical detection, triggers evidence capture and review workflow. |

Thresholds are configured in `config.py`.

## 4. GPS Capture

For high-severity detections, IRIS attempts to capture location data through `gps.py`. If location access is unavailable, the detection is still stored with location marked as unavailable or unknown.

## 5. Database Storage

Detection and session information is stored in SQLite through `database/db_manager.py`.

Stored information can include:

- session ID;
- timestamp;
- severity;
- confidence;
- bounding box;
- snapshot path;
- location;
- approval/decline status;
- optional AI analysis fields.

## 6. Dashboard Display

`web/app.py` exposes dashboard routes and API endpoints. Live state is delivered to the browser through Flask and Socket.IO.

The field dashboard displays:

- live stream;
- inspection status;
- detection counters;
- charts;
- live detection feed;
- warning overlays and alert indicators.

## 7. Municipal Review

High-severity detections appear in the municipal workflow. Reviewers can inspect detection metadata, session context, location, and snapshot evidence when available.

## 8. Approval Process

Municipal reviewers can:

- approve a detection when it appears valid;
- decline a detection when it appears invalid or not actionable.

Approved detections become eligible for map display and report generation. Declined detections are removed from the pending review queue.

## 9. Report Generation

Approved detections can be exported through the report-generation route. `web/report.py` creates PDF reports using ReportLab.

Reports are intended to support municipal follow-up, field verification, and maintenance planning.

## Optional Enhancements In Workflow

### Gemini Analysis

When enabled, Gemini analysis can provide:

- recommended action;
- priority estimate;
- impact summary;
- contextual incident notes.

### Firestore Sync

When Firebase credentials are available locally, high-severity detections can also be synchronized to Firestore for cloud-backed access.

### Hardware Alerts

Arduino and voice alerts provide immediate field feedback for detected severity levels, especially high-severity potholes.

## Biometric Workflow Status

The biometric driver-authentication workflow is archived and disconnected. It is not part of the active operational workflow until privacy, storage, consent, and access controls are redesigned.
