# backend/utils/decorators.py
from functools import wraps
from flask import session, redirect, url_for

def login_required(view_func):
    """Decorator to require admin login for routes"""
    @wraps(view_func)
    def wrapped(*args, **kwargs):
        if not session.get("admin_logged_in"):
            return redirect(url_for("admin_auth.admin_login"))
        return view_func(*args, **kwargs)
    return wrapped
