"""
reset_db.py — Wipe the database and snapshots for a fresh start.
After cleanup, the schema is recreated so the app can be run immediately.
Run: python reset_db.py
"""
import sqlite3, os, glob, config
from database.db_manager import init_db

conn = sqlite3.connect(config.DB_PATH)
conn.execute("DROP TABLE IF EXISTS detections")
conn.execute("DROP TABLE IF EXISTS sessions")
conn.commit()
conn.close()
print("[IRIS] Database wiped (detections + sessions).")

os.makedirs(config.SNAPSHOTS_DIR, exist_ok=True)
files = glob.glob(os.path.join(config.SNAPSHOTS_DIR, '*.jpg'))
for f in files:
    os.remove(f)
print(f"[IRIS] Deleted {len(files)} snapshots.")

init_db()
print("[IRIS] Database schema recreated.")
print("[IRIS] Clean slate ready. Run: python main.py")
