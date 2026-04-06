# backend/routes/static_routes.py
from flask import Blueprint, send_from_directory
from config import PROJECT_ROOT

static_routes = Blueprint('static_routes', __name__)

@static_routes.route("/")
def index():
    return send_from_directory(PROJECT_ROOT / "pages" / "Home", "home.html")

@static_routes.route("/pages/<path:subpath>")
def serve_pages(subpath):
    return send_from_directory(PROJECT_ROOT / "pages", subpath)

@static_routes.route("/assets/<path:subpath>")
def serve_assets(subpath):
    return send_from_directory(PROJECT_ROOT / "assets", subpath)

@static_routes.route("/UI/<path:subpath>")
def serve_ui(subpath):
    return send_from_directory(PROJECT_ROOT / "UI", subpath)

@static_routes.route("/favicon.ico")
def favicon():
    return send_from_directory(PROJECT_ROOT, "favicon.ico")
