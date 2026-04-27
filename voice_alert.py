"""
voice_alert.py — Driver voice alerts via pyttsx3.
Speaks severity alerts so driver is aware without looking at screen.
Install: pip install pyttsx3
"""
import threading

try:
    import pyttsx3
    _engine = pyttsx3.init()
    _engine.setProperty('rate', 160)
    _engine.setProperty('volume', 1.0)
    _available = True
except Exception:
    _available = False
    print("[IRIS] pyttsx3 not available — voice alerts disabled.")

_speaking = False
_lock = threading.Lock()

ALERTS = {
    'High':   "Warning! High severity pothole detected ahead.",
    'Medium': "Caution. Medium pothole detected.",
    'session_start': "IRIS inspection session started. Drive safely.",
    'session_end':   "Inspection session ended. Data uploaded to municipal dashboard.",
}

def speak(text):
    """Speak text in background thread — non-blocking."""
    global _speaking
    with _lock:
        if not _available or _speaking:
            return
        _speaking = True
    
    def _run():
        global _speaking
        try:
            _engine.say(text)
            _engine.runAndWait()
        except Exception:
            pass
        finally:
            with _lock:
                _speaking = False
    
    threading.Thread(target=_run, daemon=True).start()

def alert(severity):
    """Speak the alert for a given severity level."""
    if severity in ALERTS:
        speak(ALERTS[severity])
