import config

def classify(bbox, confidence):
    x1, y1, x2, y2 = bbox
    area = (x2 - x1) * (y2 - y1)

    if area < config.SEVERITY_LOW_MAX:
        severity = 'Low'
    elif area < config.SEVERITY_MEDIUM_MAX:
        severity = 'Medium'
    else:
        severity = 'High'

    return severity, area
