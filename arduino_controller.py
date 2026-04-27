"""
arduino_controller.py — Controls Arduino LEDs + buzzer.

Supports two modes (set in config.py):
  ARDUINO_MODE = 'wifi'   → ESP8266 via HTTP over WiFi (wireless RC car)
  ARDUINO_MODE = 'serial' → Arduino Uno via USB cable

WiFi mode setup:
  1. Upload arduino/iris_esp8266/iris_esp8266.ino to ESP8266
  2. Note IP address from Serial Monitor
  3. Set ARDUINO_IP in config.py to that IP
  4. Set ARDUINO_MODE = 'wifi' in config.py

Serial mode setup:
  1. Upload arduino/iris_controller/iris_controller.ino to Arduino Uno
  2. Set ARDUINO_PORT = 'COM3' (check Device Manager)
  3. Set ARDUINO_MODE = 'serial' in config.py
"""

import threading
import time
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import config

MODE    = getattr(config, 'ARDUINO_MODE', 'wifi')
ENABLED = getattr(config, 'ARDUINO_ENABLED', True)
IP      = getattr(config, 'ARDUINO_IP', '192.168.1.105')
PORT_S  = getattr(config, 'ARDUINO_PORT', 'COM3')
ALERT_COOLDOWN_SEC = {
    'LOW': 0.4,
    'MEDIUM': 0.9,
    'HIGH': 1.5,
}

_serial    = None
_connected = False
_last_alert_at = {}

def _connect_serial():
    global _serial, _connected
    try:
        import serial
        from serial.tools import list_ports
        
        # Try configured port first
        ports = [p.device for p in list_ports.comports()]
        port = PORT_S
        
        if PORT_S not in ports and ports:
            print(f"[Arduino] COM port {PORT_S} not found. Available ports: {ports}")
            port = ports[0]
            print(f"[Arduino] Using {port} instead")
        elif not ports:
            print("[Arduino] No COM ports found. Is Arduino connected?")
            _connected = False
            return
        
        _serial = serial.Serial(port, 9600, timeout=2)
        time.sleep(2)
        _connected = True
        print(f"[Arduino] Serial connected on {port} ✅")
    except Exception as e:
        _connected = False
        print(f"[Arduino] Serial not connected ({e})")

def _connect_wifi():
    global _connected
    try:
        import urllib.request
        urllib.request.urlopen(f"http://{IP}/ping", timeout=3)
        _connected = True
        print(f"[Arduino] WiFi connected at http://{IP} ✅")
    except Exception as e:
        _connected = False
        print(f"[Arduino] WiFi not reachable at {IP} ({e})")

def connect():
    if not ENABLED:
        return
    if MODE == 'serial':
        _connect_serial()
    else:
        _connect_wifi()

def _send_wifi(command):
    try:
        import urllib.request
        urllib.request.urlopen(
            f"http://{IP}/{command.lower()}", timeout=2)
    except Exception as e:
        print(f"[Arduino] WiFi send error: {e}")

def _send_serial(command):
    try:
        _serial.write(f"{command}\n".encode())
    except Exception as e:
        print(f"[Arduino] Serial send error: {e}")

def send(command):
    if not _connected or not ENABLED:
        return
    def _run():
        if MODE == 'serial':
            _send_serial(command)
        else:
            _send_wifi(command)
    threading.Thread(target=_run, daemon=True).start()

def alert(severity):
    if severity not in ('Low', 'Medium', 'High'):
        return
    command = severity.upper()
    now = time.time()
    last = _last_alert_at.get(command, 0.0)
    if now - last < ALERT_COOLDOWN_SEC.get(command, 0.75):
        return
    _last_alert_at[command] = now
    send(command)

# Auto-connect on import
connect()
