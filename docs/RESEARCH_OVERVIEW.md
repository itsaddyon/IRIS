# IRIS Research Overview

## Title

IRIS: An Intelligent Road Inspection System for Automated Pothole Detection, Severity Classification, and Municipal Review

## Problem Statement

Road-surface degradation, especially pothole formation, creates safety risks, increases vehicle maintenance costs, and requires timely municipal response. Traditional inspection processes often depend on manual surveys, citizen complaints, or delayed maintenance reporting. These methods can be inconsistent, labor-intensive, and difficult to scale across large road networks.

IRIS addresses this problem by combining real-time computer vision, severity classification, evidence capture, dashboard visualization, and municipal review into a single inspection workflow.

## Methodology

The system follows an applied engineering methodology:

1. Capture road imagery from camera or video sources.
2. Use a YOLO-based object detection model to identify pothole candidates.
3. Filter repeated detections to reduce duplicate records.
4. Classify detected potholes into severity levels using bounding-box area.
5. Store detections, sessions, evidence paths, and review state in a local database.
6. Display detections through live operator and municipal dashboards.
7. Support municipal approval, decline, GIS display, and report generation.

## System Architecture

IRIS is built around modular layers:

| Layer | Description |
| --- | --- |
| Input layer | Captures video from webcam, video file, or IP camera stream. |
| Detection layer | Runs YOLO inference and duplicate filtering. |
| Classification layer | Assigns severity based on detection size thresholds. |
| Evidence layer | Captures snapshots and optional GPS data for high-severity events. |
| Persistence layer | Stores sessions, detections, and approval status in SQLite. |
| Dashboard layer | Provides field and municipal web interfaces using Flask. |
| Review layer | Supports approval, decline, mapping, and report generation. |
| Optional intelligence layer | Adds Gemini analysis and Firestore sync when configured. |
| Optional hardware layer | Supports Arduino indicators and voice alerts. |

## Innovation

IRIS combines several practical workflow elements into one system:

- real-time detection integrated with field-session tracking;
- severity-aware event handling instead of flat detection logging;
- municipal validation workflow for reducing false-positive operational impact;
- GIS-ready approved detection mapping;
- optional AI-generated incident prioritization;
- optional hardware feedback for inspection operators;
- archived biometric authentication concept for future secure identity workflows.

## Current Results And Capabilities

The current repository demonstrates a functional baseline implementation with:

- live dashboard streaming;
- YOLO-based pothole detection;
- severity categorization;
- session-based inspection flow;
- local database storage;
- high-severity evidence capture;
- municipal approval and decline interface;
- report generation for approved detections;
- optional cloud and hardware integrations.

Formal publication results should be added after controlled testing with documented datasets, reproducible evaluation methods, and measured performance metrics such as precision, recall, F1 score, false-positive rate, inference latency, and GPS accuracy.

## Future Scope

Future research and development directions include:

- dataset documentation and model-card publication;
- benchmark testing across road conditions, lighting conditions, camera angles, and vehicle speeds;
- improved severity estimation using depth, area calibration, or stereo/LiDAR support;
- mobile deployment and edge-device optimization;
- production-grade identity and access management;
- privacy-preserving biometric redesign;
- integration with municipal work-order systems;
- predictive maintenance analytics using weather, traffic, and historical deterioration data;
- multi-city deployment studies.

## Publication Notes

For future academic or technical publication, include:

- dataset source and licensing information;
- training configuration and model version;
- hardware specifications;
- evaluation methodology;
- baseline comparisons;
- ethical and privacy considerations;
- limitations and failure cases.

## Ownership Statement

IRIS and its original source code, architecture, workflows, interfaces, documentation, and associated project materials are proprietary intellectual property of Adarsh Arya unless explicitly stated otherwise.
