# 🧬 Biometric Face Scanning Archival System

This folder contains the fully completed, functional biometric facial recognition and webcam-capturing system for **IRIS**.

To optimize the application for live showcase competitions and eliminate webcam startup overhead, the biometric login wall has been temporarily disabled in favor of a seamless direct-access operator dashboard.

---

## 📂 Archived Assets
1.  **`biometric_auth.py`:** Core facial recognition engine built on `face_recognition` (dlib). Contains Euclidean distance checks, single-driver matching thresholds, and robust multi-frame median voting logic.
2.  **`login_backup.html`:** Full front-end capture portal featuring cyberpunk guide overlays, real-time video frame streaming via Socket.IO, and registration forms for vehicle/route mapping.

---

## 💾 Preserved Biometric Database Data
> [!IMPORTANT]
> All enrolled driver face records and 128D mathematical embeddings (including **Adarsh Arya**) remain safely stored in the `drivers` and `driver_vehicles` tables inside the persistent SQLite database **`iris.db`**.
> **No biometric databases or facial encodings were cleared or modified.**

---

## 🔄 Restoration Steps (How to re-enable)
If you wish to reconnect facial recognition login in the future:
1.  **Restore Files:** Move `biometric_auth.py` back to the root folder, and rename `login_backup.html` back to `login.html` inside `web/templates/`.
2.  **Re-enable imports & listeners in `web/app.py`:**
    - Import the biometric engine: `from biometric_auth import get_biometric_engine`
    - Reconnect Socket.IO event listeners: `biometric:capture_face`, `biometric:recognize`, and `biometric:enroll_driver`.
    - Restore biometric API routes: `/api/biometric-stats` and `/api/vehicles-and-routes`.
3.  **Update routing checks:** Modify `require_driver()` to redirect unauthorized sessions back to `/login` rather than auto-authenticating.
