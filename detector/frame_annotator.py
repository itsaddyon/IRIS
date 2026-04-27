import cv2

SEVERITY_COLORS = {
    'Low':    (0, 255, 0),    # Green
    'Medium': (0, 165, 255),  # Orange
    'High':   (0, 0, 255),    # Red
}

def annotate(frame, bbox, severity, confidence):
    x1, y1, x2, y2 = [int(v) for v in bbox]
    color = SEVERITY_COLORS.get(severity, (255, 255, 255))

    cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)

    label = f'{severity} {confidence:.2f}'
    (tw, th), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)
    cv2.rectangle(frame, (x1, y1 - th - 8), (x1 + tw + 4, y1), color, -1)
    cv2.putText(frame, label, (x1 + 2, y1 - 4),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)

    return frame
