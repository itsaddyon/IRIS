"""
deduplicator.py — IoU-based frame deduplication.

Compares each detection against the previous 3 frames.
If IoU > threshold with any previous box → same pothole, skip it.
If IoU < threshold → new pothole, count it.

This correctly handles:
- Stationary camera (same box every frame → always skipped after first)
- Fast-moving vehicle (box shifts → IoU drops → counted as new)
- Multiple nearby potholes (each has own box → independently tracked)
- Slow-moving vehicle (keeps 3 frames of history to handle slow transitions)
"""

IOU_THRESHOLD = 0.5   # overlap > 50% = same pothole

_prev_frames = []   # List of bbox lists from the last 3 processed frames

def _iou(boxA, boxB):
    """Calculate Intersection over Union between two [x1,y1,x2,y2] boxes."""
    xA = max(boxA[0], boxB[0])
    yA = max(boxA[1], boxB[1])
    xB = min(boxA[2], boxB[2])
    yB = min(boxA[3], boxB[3])

    inter = max(0, xB - xA) * max(0, yB - yA)
    if inter == 0:
        return 0.0

    areaA = (boxA[2]-boxA[0]) * (boxA[3]-boxA[1])
    areaB = (boxB[2]-boxB[0]) * (boxB[3]-boxB[1])
    union = areaA + areaB - inter
    return inter / union if union > 0 else 0.0

def filter_new(detections):
    """
    Given list of (bbox, confidence) from current frame,
    returns only those that are genuinely new (not seen in last 3 frames).
    Also updates internal state for next frame comparison.
    """
    global _prev_frames
    new_detections = []

    current_bboxes = [bbox for bbox, _ in detections]
    
    for bbox, confidence in detections:
        is_same = False
        # Check against all boxes in the last 3 frames
        for prev_frame in _prev_frames:
            if any(_iou(bbox, prev_bbox) > IOU_THRESHOLD for prev_bbox in prev_frame):
                is_same = True
                break
        
        if not is_same:
            new_detections.append((bbox, confidence))

    # Keep a sliding window of 3 frames
    _prev_frames.append(current_bboxes)
    if len(_prev_frames) > 3:
        _prev_frames.pop(0)
    
    return new_detections
