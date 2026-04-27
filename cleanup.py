"""
cleanup.py — Remove temp/cache files from IRIS.
Safe for pre-demo cleanup: removes generated reports, caches, and stale temp files.
Run: python cleanup.py
"""
import os, shutil, glob

BASE = os.path.dirname(os.path.abspath(__file__))

def rm(path):
    full = os.path.join(BASE, path)
    if os.path.isfile(full):
        os.remove(full); print(f"  [deleted] {path}")
    else:
        print(f"  [skip] {path}")

print("[IRIS] Cleaning project...")

# Temp/generated files
rm("IRIS_Report.pdf")
rm("web/templates/_delete_me.tmp")
rm("web/templates/_gone.tmp")

# Old local debugging helper (not part of the demo app)
rm("debug_test_done.py")

# All __pycache__ folders
for pc in glob.glob(os.path.join(BASE,"**/__pycache__"),recursive=True):
    shutil.rmtree(pc); print(f"  [deleted dir] {os.path.relpath(pc,BASE)}")

print("\n[IRIS] Note:")
print("  web/static/style.css and web/static/dashboard.js are currently not wired into the active templates.")
print("  They are being kept only as deferred assets, not presentation-critical files.")
print("\n[IRIS] Done!")
