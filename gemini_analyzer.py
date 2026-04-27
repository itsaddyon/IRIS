"""
gemini_analyzer.py — Google Gemini AI for contextual incident analysis.
Transforms raw detection data into human-readable, actionable alerts.
"""
import os
import config
import logging

try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    logging.warning("[IRIS] google-generativeai not installed. AI analysis disabled.")

logger = logging.getLogger(__name__)

def setup_gemini():
    """Initialize Gemini API with key from environment or config."""
    if not GEMINI_AVAILABLE:
        return False
    
    api_key = getattr(config, 'GEMINI_API_KEY', None) or os.getenv('GEMINI_API_KEY')
    if not api_key:
        logger.warning("[IRIS] GEMINI_API_KEY not found in config or environment")
        logger.warning("[IRIS] Get free key at: https://aistudio.google.com/apikey")
        return False
    
    try:
        genai.configure(api_key=api_key)
        logger.info("[IRIS] ✓ Gemini API initialized")
        return True
    except Exception as e:
        logger.error(f"[IRIS] Failed to initialize Gemini: {e}")
        return False


def analyze_incident(detection_data):
    """
    Analyze a traffic incident using Gemini AI.
    
    Args:
        detection_data (dict): {
            'severity': 'High'|'Medium'|'Low',
            'confidence': float (0-1),
            'bbox_area': int,
            'location': str,
            'timestamp': str,
            'photo_path': str (optional)
        }
    
    Returns:
        dict: {
            'ai_analysis': str (descriptive analysis),
            'recommended_action': str,
            'impact_estimate': str,
            'priority': int (1-5, 5=highest)
        }
    """
    if not GEMINI_AVAILABLE:
        return _fallback_analysis(detection_data)
    
    try:
        severity = detection_data.get('severity', 'Unknown')
        confidence = detection_data.get('confidence', 0)
        location = detection_data.get('location', 'Unknown location')
        timestamp = detection_data.get('timestamp', '')
        
        # Build context prompt
        prompt = f"""
You are an intelligent traffic incident analyzer for IRIS (Intelligent Road Inspection System).
Analyze this traffic incident and provide actionable insights:

INCIDENT DATA:
- Severity Level: {severity}
- Detection Confidence: {confidence*100:.1f}%
- Location: {location}
- Timestamp: {timestamp}
- Incident Type: Traffic accident/hazard

Based on the severity and confidence, provide:
1. A brief human-readable description of the situation (2-3 sentences)
2. Recommended action for traffic management (be specific)
3. Estimated impact (traffic delay, road closure need, etc.)
4. Priority level (1-5, where 5 is critical)

Format your response as:
ANALYSIS: [description]
ACTION: [recommended action]
IMPACT: [impact estimate]
PRIORITY: [1-5]
"""
        
        model = genai.GenerativeModel('gemini-pro')
        response = model.generate_content(prompt)
        
        if not response.text:
            logger.warning("[IRIS] Gemini returned empty response")
            return _fallback_analysis(detection_data)
        
        # Parse response
        result = _parse_gemini_response(response.text, severity)
        logger.info(f"[IRIS] Gemini analysis: {severity} incident → Priority {result.get('priority')}")
        return result
        
    except Exception as e:
        logger.error(f"[IRIS] Gemini analysis failed: {e}")
        return _fallback_analysis(detection_data)


def _parse_gemini_response(text, severity):
    """Extract structured data from Gemini response."""
    lines = text.strip().split('\n')
    result = {
        'ai_analysis': 'Unable to analyze',
        'recommended_action': 'Monitor situation',
        'impact_estimate': 'Unknown',
        'priority': {'High': 5, 'Medium': 3, 'Low': 2}.get(severity, 3)
    }
    
    for line in lines:
        if line.startswith('ANALYSIS:'):
            result['ai_analysis'] = line.replace('ANALYSIS:', '').strip()
        elif line.startswith('ACTION:'):
            result['recommended_action'] = line.replace('ACTION:', '').strip()
        elif line.startswith('IMPACT:'):
            result['impact_estimate'] = line.replace('IMPACT:', '').strip()
        elif line.startswith('PRIORITY:'):
            try:
                priority_str = line.replace('PRIORITY:', '').strip()
                # Extract number from response (e.g., "5" or "5/5")
                priority_val = int(''.join(filter(str.isdigit, priority_str.split('/')[0])))
                result['priority'] = max(1, min(5, priority_val))
            except (ValueError, IndexError):
                pass
    
    return result


def _fallback_analysis(detection_data):
    """Fallback analysis when Gemini is unavailable."""
    severity = detection_data.get('severity', 'Unknown')
    confidence = detection_data.get('confidence', 0)
    location = detection_data.get('location', 'Unknown')
    
    priority_map = {'High': 5, 'Medium': 3, 'Low': 2}
    priority = priority_map.get(severity, 3)
    
    action_map = {
        'High': 'Dispatch emergency services and issue public alert',
        'Medium': 'Alert traffic control and increase monitoring',
        'Low': 'Document and monitor'
    }
    
    return {
        'ai_analysis': f"{severity} severity incident detected at {location} (confidence: {confidence*100:.0f}%)",
        'recommended_action': action_map.get(severity, 'Monitor'),
        'impact_estimate': f"{severity} severity - may cause traffic disruption",
        'priority': priority
    }


def format_alert_message(detection_data, ai_analysis=None):
    """
    Format incident data into a human-friendly alert message.
    Used for voice alerts and notifications.
    """
    severity = detection_data.get('severity', 'Unknown')
    location = detection_data.get('location', 'Unknown location')
    
    if ai_analysis is None:
        ai_analysis = _fallback_analysis(detection_data)
    
    action = ai_analysis.get('recommended_action', 'Monitor situation')
    
    # Format for voice alert (concise)
    message = f"Alert: {severity} severity incident at {location}. {action}."
    
    return message
