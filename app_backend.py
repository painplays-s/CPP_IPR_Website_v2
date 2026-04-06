#!/usr/bin/env python3
"""
Backend Server – Admin Panel
Provides the CMS for managing content (CRUD + file uploads).
Runs on 0.0.0.0:5001 (HTTP) – relies on its own login for security.
Serves all root static files (UI, assets, pages) so admin pages display correctly.
"""

import sys
from pathlib import Path
from flask import Flask, redirect, url_for, send_from_directory, abort

# Add backend directory to path so we can import its blueprints
BACKEND_DIR = Path(__file__).parent / 'backend'
ROOT_DIR = Path(__file__).parent.absolute()
sys.path.insert(0, str(BACKEND_DIR))

from config import SECRET_KEY
from models.database import ensure_db_and_migrations

# Import all admin blueprints
from routes.admin_auth import admin_auth
from routes.admin_home import admin_home_bp
from routes.admin_carousal import admin_carousal_bp
from routes.admin_notice import admin_notice
from routes.admin_research import admin_research
from routes.admin_publication import admin_publication
from routes.admin_forms_links import admin_forms_links_bp
from routes.admin_people import admin_people_bp
from routes.admin_tender import admin_tender_bp
from routes.admin_advertisement import admin_advertisement_bp
from routes.public_api import public_api
from routes.error import register_error_handlers  # Import error handlers

# ------------------------------------------------------------
# Create Flask app
# ------------------------------------------------------------
app = Flask(__name__,
            template_folder=str(BACKEND_DIR / 'templates'),
            static_folder=str(BACKEND_DIR / 'static'))
app.secret_key = SECRET_KEY

# Initialise database (creates tables if missing)
ensure_db_and_migrations()

# ------------------------------------------------------------
# Serve all root static files (so admin pages can load UI, assets, etc.)
# ------------------------------------------------------------
@app.route('/UI/<path:filename>')
def serve_ui(filename):
    """Serve files from the UI folder."""
    ui_path = ROOT_DIR / 'UI'
    if '..' in filename or (ui_path / filename).is_dir():
        abort(404)
    return send_from_directory(ui_path, filename)

@app.route('/assets/<path:filename>')
def serve_assets(filename):
    """Serve files from the assets folder."""
    assets_path = ROOT_DIR / 'assets'
    if '..' in filename or (assets_path / filename).is_dir():
        abort(404)
    return send_from_directory(assets_path, filename)

@app.route('/pages/<path:filename>')
def serve_pages(filename):
    """Serve files from the pages folder (if needed by admin)."""
    pages_path = ROOT_DIR / 'pages'
    if '..' in filename or (pages_path / filename).is_dir():
        abort(404)
    return send_from_directory(pages_path, filename)

@app.route('/favicon.ico')
def favicon():
    fav = ROOT_DIR / 'favicon.ico'
    if fav.exists():
        return send_from_directory(ROOT_DIR, 'favicon.ico')
    return '', 204

# Also serve any other root files that might be referenced (e.g., index.html, bilingual.js, etc.)
@app.route('/<path:filename>')
def serve_root_file(filename):
    """Serve other root files (like bilingual.js, etc.)"""
    root_file = ROOT_DIR / filename
    if root_file.exists() and root_file.is_file():
        return send_from_directory(ROOT_DIR, filename)
    abort(404)

# ------------------------------------------------------------
# Register blueprints
# ------------------------------------------------------------
app.register_blueprint(admin_auth)                # /cppipr_cms
app.register_blueprint(admin_home_bp)
app.register_blueprint(admin_carousal_bp)
app.register_blueprint(admin_notice)
app.register_blueprint(admin_research)
app.register_blueprint(admin_publication)
app.register_blueprint(admin_forms_links_bp)
app.register_blueprint(admin_people_bp)
app.register_blueprint(admin_tender_bp)
app.register_blueprint(admin_advertisement_bp)
app.register_blueprint(public_api)                # if needed by admin forms

# Register error handlers from backend
app = register_error_handlers(app)

# ------------------------------------------------------------
# Root redirect
# ------------------------------------------------------------
@app.route('/')
def index():
    return redirect(url_for('admin_auth.admin_login'))

@app.route('/health')
def health():
    from flask import jsonify
    return jsonify({'status': 'healthy', 'mode': 'backend'})

# ------------------------------------------------------------
# Run server
# ------------------------------------------------------------
if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--port', type=int, default=5001)
    parser.add_argument('--host', default='0.0.0.0')
    args = parser.parse_args()

    print("="*60)
    print("CPP Website Backend Admin Server")
    print("="*60)
    print(f"Host: {args.host} (accessible from localhost and your network)")
    print(f"Port: {args.port}")
    print(f"Admin URL: http://{args.host}:{args.port}/cppipr_cms/login")
    print(f"Error handling: Enabled (using backend/routes/error.py)")
    print("="*60)

    app.run(host=args.host, port=args.port, debug=False)