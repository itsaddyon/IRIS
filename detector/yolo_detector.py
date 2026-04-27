from ultralytics import YOLO
import config

model = YOLO(config.MODEL_PATH)

def detect(frame):
    results = model(frame, conf=config.CONFIDENCE_THRESHOLD, verbose=False)[0]
    detections = []
    for box in results.boxes:
        try:
            bbox = box.xyxy[0].tolist()
            confidence = float(box.conf[0]) if hasattr(box, 'conf') and box.conf is not None else 0.0
            if confidence > 0:  # Only add detections with valid confidence
                detections.append((bbox, confidence))
        except (ValueError, IndexError, TypeError, AttributeError) as e:
            # Silently skip malformed detections
            continue
    return detections
