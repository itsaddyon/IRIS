# Release Notes

## Version 1.0.0 - IRIS Baseline Release

IRIS Version 1.0.0 establishes the first documented baseline of the Intelligent Road Inspection System as a personal research, portfolio, and ownership-record project by Adarsh Arya.

## Project Purpose

IRIS is designed to automate pothole inspection workflows by combining real-time video analysis, severity classification, evidence capture, municipal review, and report generation. The system supports field inspection scenarios where a camera-equipped vehicle or mobile operator captures road footage and high-priority detections are escalated for human review.

## Current Capabilities

- Real-time camera/video/IP-camera input handling.
- YOLOv8-based pothole detection.
- Duplicate detection filtering.
- Low, Medium, and High severity classification.
- Live field dashboard with stream, counters, charts, and detection feed.
- Session lifecycle tracking for inspection runs.
- Local SQLite storage for detections, sessions, approvals, and metadata.
- High-severity snapshot capture.
- Optional GPS capture for high-severity incidents.
- Optional Arduino LED/buzzer alert integration.
- Optional voice alert integration.
- Optional Gemini-based incident analysis.
- Optional Firestore synchronization.
- Municipal dashboard for review, approval, decline, map display, and PDF reporting.
- Archived biometric authentication module retained for future secure redesign.

## Architecture Summary

The Version 1.0 architecture follows a modular inspection pipeline:

1. Camera or video source provides frames.
2. YOLOv8 model performs pothole inference.
3. Deduplication filters repeated detections.
4. Severity classifier assigns Low, Medium, or High status.
5. High-severity events trigger snapshot, GPS, alerts, optional AI analysis, and optional cloud sync.
6. SQLite stores session and detection records.
7. Flask and Socket.IO deliver live dashboard updates.
8. Municipal review pages support approval, decline, mapping, and report generation.

## Major Modules

| Module | Purpose |
| --- | --- |
| `main.py` | Starts the detection loop and web application. |
| `detector/` | Handles YOLO inference, video input, severity classification, annotation, and deduplication. |
| `database/db_manager.py` | Defines and manages local SQLite data persistence. |
| `web/app.py` | Provides Flask routes, APIs, Socket.IO events, dashboards, and report endpoints. |
| `web/report.py` | Generates PDF reports for approved detections. |
| `gps.py` | Captures location data when available. |
| `arduino_controller.py` | Sends severity alerts to Arduino hardware. |
| `gemini_analyzer.py` | Adds optional AI-generated incident analysis. |
| `face_scan/` | Stores archived biometric authentication implementation. |

## Documentation Added

- Professional README.
- Copyright notice.
- Restrictive proprietary source-available license.
- Architecture documentation.
- Workflow documentation.
- Research overview.
- GitHub issue templates and contribution/security guidance.

## Known Limitations

- Biometric login is archived and disconnected for security/privacy reasons.
- Production-grade authentication is not yet implemented.
- The trained model file is local-only and not included in Git.
- Firebase service-account keys and runtime databases are intentionally excluded.
- GPS support is currently Windows-specific.
- Hardware alerts require configured Arduino-compatible devices.

## Ownership

Copyright (c) 2026 Adarsh Arya. All Rights Reserved.

This release documents IRIS as proprietary intellectual property of Adarsh Arya unless explicitly stated otherwise.
