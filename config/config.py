"""Central configuration for CampusNav."""

import os
from pathlib import Path

# ------------------------------------------------------------------
# Paths
# ------------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent.parent

DATABASE_DIR = BASE_DIR / "database"
DATABASE_PATH = DATABASE_DIR / "campus.db"

FRONTEND_DIR = BASE_DIR / "frontend"
TEMPLATES_DIR = FRONTEND_DIR / "templates"
STATIC_DIR = FRONTEND_DIR / "static"

# ------------------------------------------------------------------
# Server (override with environment variables if needed)
#   CAMPUS_HOST=0.0.0.0  -> also reachable from a phone on the same Wi-Fi
# ------------------------------------------------------------------
HOST = os.environ.get("CAMPUS_HOST", "127.0.0.1")
PORT = int(os.environ.get("CAMPUS_PORT", "5000"))
DEBUG = os.environ.get("CAMPUS_DEBUG", "0") == "1"

# ------------------------------------------------------------------
# Navigation settings
# ------------------------------------------------------------------
APP_NAME = "CampusNav"
APP_TAGLINE = "Indoor & outdoor campus navigation"
APP_VERSION = "2.0.0"

# Average walking speed (metres / second) used for time estimates
WALKING_SPEED_MPS = 1.25

# Time (seconds) taken by each kind of transition
TRANSITION_SECONDS = {
    "door": 5,        # walking through a building entrance
    "exit_door": 5,   # emergency exit door
    "stairs": 20,     # one flight of stairs (one floor)
    "lift": 40,       # waiting for + riding the lift (one floor)
}
