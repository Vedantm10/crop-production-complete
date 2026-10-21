"""
api.py (Root entrypoint)
========================
Allows Render and local uvicorn servers to run from the repository root:
    uvicorn api:app --host 0.0.0.0 --port $PORT

Delegates directly to backend.api:app while ensuring all path dependencies
resolve regardless of the execution working directory.
"""
import os
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.join(ROOT, "backend")
SRC_DIR = os.path.join(BACKEND_DIR, "src")

if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

from backend.api import app  # noqa: E402
