# backend/utils/helpers.py
from datetime import datetime

def format_date(dt_str):
    """Format ISO datetime string to readable format"""
    try:
        return datetime.fromisoformat(dt_str).strftime("%d %b %Y, %I:%M %p")
    except Exception:
        return dt_str
