"""
video_source.py — Robust camera input for IRIS.

Modes (VIDEO_MODE in config.py):
  'webcam'    → USB webcam
  'video'     → pre-recorded .mp4 file
  'ip_camera' → Android IP Webcam app over WiFi

IP Webcam setup:
  1. Install 'IP Webcam' by Pavel Khlebovich (Play Store, free)
  2. Open app → Start server
  3. Update config.py:  VIDEO_IP = 'http://<phone-ip>:8080/video'
  4. Phone and laptop must be on the SAME network/hotspot
"""

import cv2
import threading
import time
import os
import config


def _try_open(url, timeout_sec=12):
    """Try to open a VideoCapture URL within timeout_sec seconds."""
    cap = cv2.VideoCapture(url, cv2.CAP_FFMPEG)
    deadline = time.time() + timeout_sec
    while time.time() < deadline:
        if cap.isOpened():
            ret, frame = cap.read()
            if ret and frame is not None and frame.size > 0:
                return cap
        time.sleep(0.4)
    cap.release()
    return None


def find_usb_camera():
    """Scan indices 0-4 for first working USB webcam."""
    for idx in range(5):
        try:
            cap = cv2.VideoCapture(idx, cv2.CAP_DSHOW)
            if cap.isOpened():
                ret, frame = cap.read()
                if ret and frame is not None and frame.size > 0:
                    print(f"[VideoSource] USB webcam found at index {idx}")
                    return cap
            cap.release()
        except Exception:
            pass
    return None


class FrameGrabber:
    """
    Background thread that continuously drains the camera buffer.
    IP Webcam buffers frames over WiFi — without this you get 3-5s lag.
    Thread-safe: read() always returns a copy of the latest frame.
    """

    def __init__(self, cap, name="camera"):
        self._cap   = cap
        self._frame = None
        self._ok    = False
        self._lock  = threading.Lock()
        self._stop  = threading.Event()
        self._name  = name
        t = threading.Thread(target=self._grab, daemon=True, name=f"FrameGrabber-{name}")
        t.start()

    def _grab(self):
        while not self._stop.is_set():
            try:
                ret, frame = self._cap.read()
                if ret and frame is not None and frame.size > 0:
                    with self._lock:
                        self._frame = frame
                        self._ok    = True
                else:
                    with self._lock:
                        self._ok = False
                    time.sleep(0.02)
            except Exception:
                with self._lock:
                    self._ok = False
                time.sleep(0.05)

    def read(self):
        """Returns (success, frame_copy) — never blocks."""
        with self._lock:
            if self._frame is None:
                return False, None
            return self._ok, self._frame.copy()

    def release(self):
        self._stop.set()
        try:
            self._cap.release()
        except Exception:
            pass


def get_source():
    """
    Returns a FrameGrabber (or raw VideoCapture for video files).
    Raises RuntimeError if connection fails — caller should retry.
    """
    mode = config.VIDEO_MODE

    # ── USB Webcam ─────────────────────────────────────────────────────────
    if mode == 'webcam':
        cap = find_usb_camera()
        if cap is None:
            raise RuntimeError(
                "No USB webcam detected (indices 0-4). "
                "Try setting VIDEO_MODE = 'ip_camera' in config.py"
            )
        cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        return FrameGrabber(cap, "usb")

    # ── IP Webcam (Android IP Webcam app) ──────────────────────────────────
    elif mode == 'ip_camera':
        base_url = getattr(config, 'VIDEO_IP', 'http://172.168.19.76:8080/video')
        # Strip trailing /video so we can try both endpoints (Python 3.8 compatible)
        base = base_url.rstrip('/')
        if base.endswith('/video'):
            base = base[:-6]
        if base.endswith('/videofeed'):
            base = base[:-10]
        candidates = [
            base + '/video',       # MJPEG stream (standard IP Webcam)
            base + '/videofeed',   # alternative endpoint some versions use
            base + '/shot.jpg',    # fallback: single JPEG (slower)
        ]
        print(f"[VideoSource] Trying IP Webcam at {base} ...")
        for url in candidates:
            print(f"[VideoSource]   → {url}")
            cap = _try_open(url, timeout_sec=10)
            if cap is not None:
                cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
                print(f"[VideoSource] Connected ✅  {url}")
                return FrameGrabber(cap, "ip")
        raise RuntimeError(
            f"Cannot connect to IP Webcam.\n"
            f"Tried: {candidates}\n\n"
            "Fix checklist:\n"
            "  1. IP Webcam app is running — did you tap 'Start server'?\n"
            "  2. Phone and laptop on the SAME WiFi / hotspot\n"
            "  3. VIDEO_IP in config.py matches the IP shown in the app\n"
            "  4. Open the URL in a browser — you should see a video page\n"
            "  5. Firewall may be blocking — try disabling Windows Firewall temporarily"
        )

    # ── Pre-recorded video file ────────────────────────────────────────────
    elif mode == 'video':
        path = getattr(config, 'VIDEO_PATH', 'demo.mp4')
        if not os.path.exists(path):
            raise RuntimeError(
                f"Video file not found: {path}\n"
                "Place demo.mp4 in the IRIS root folder."
            )
        cap = cv2.VideoCapture(path)
        if not cap.isOpened():
            raise RuntimeError(f"Cannot open video file: {path}")
        return cap   # raw cap — main.py handles looping

    else:
        raise ValueError(f"Unknown VIDEO_MODE='{mode}' in config.py")
