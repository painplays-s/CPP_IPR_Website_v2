# backend/config.py
from pathlib import Path

# ============================================================
# PATHS
# ============================================================
BACKEND_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BACKEND_DIR.parent
DB_PATH = BACKEND_DIR / "database.db"

# Home carousel uploads
CAROUSAL_UPLOAD_DIR = PROJECT_ROOT / "assets" / "images" / "home_carousal"
CAROUSAL_UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

# Current notice uploads
NOTICE_UPLOAD_DIR = PROJECT_ROOT / "assets" / "files" / "currentNotice"
NOTICE_UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

# Research highlight uploads
RESEARCH_HIGHLIGHT_DIR = PROJECT_ROOT / "assets" / "images" / "research_highlight"
RESEARCH_HIGHLIGHT_DIR.mkdir(parents=True, exist_ok=True)

# Forms uploads
FORMS_UPLOAD_DIR = PROJECT_ROOT / "assets" / "files" / "forms"
FORMS_UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

# People photos uploads
PEOPLE_UPLOAD_DIR = PROJECT_ROOT / "assets" / "images" / "people"
PEOPLE_UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

# ============================================================
# APP CONFIG
# ============================================================
SECRET_KEY = "change_this_secret_key"  # CHANGE IN PRODUCTION
