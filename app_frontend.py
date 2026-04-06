#!/usr/bin/env python3
"""
Frontend Server – Public Website
Serves static files and provides all public API endpoints by reusing backend blueprints.
Runs on 0.0.0.0:5000 with HTTP only.
"""

import sys
from pathlib import Path

# Add backend directory to path so we can import its modules
BACKEND_DIR = Path(__file__).parent / 'backend'
sys.path.insert(0, str(BACKEND_DIR))

from flask import Flask, jsonify
from config import PROJECT_ROOT, SECRET_KEY
from routes.public_api import public_api
from routes.static_routes import static_routes
from routes.error import register_error_handlers  # Import error handlers

# ------------------------------------------------------------
# Create Flask app
# ------------------------------------------------------------
app = Flask(__name__,
            template_folder=str(BACKEND_DIR / 'templates'),  # Point to backend templates for error.html
            static_folder=str(PROJECT_ROOT))     # serves root static files
app.secret_key = SECRET_KEY   # not strictly needed, but harmless

# Register blueprints – this gives you all public routes
app.register_blueprint(public_api)      # all /api/... endpoints
app.register_blueprint(static_routes)   # serves /pages, /assets, /UI, /, /favicon.ico

# Register error handlers from backend
app = register_error_handlers(app)

# ------------------------------------------------------------
# Optional health check
# ------------------------------------------------------------
@app.route('/health')
def health():
    from datetime import datetime, timezone
    return jsonify({
        'status': 'healthy',
        'mode': 'frontend',
        'timestamp': datetime.now(timezone.utc).isoformat()
    })

# ------------------------------------------------------------
# Run server
# ------------------------------------------------------------
if __name__ == '__main__':
    import argparse
    import logging
    from logging.handlers import RotatingFileHandler

    # Setup logging (optional)
    LOGS_DIR = PROJECT_ROOT / 'logs'
    LOGS_DIR.mkdir(exist_ok=True)
    handler = RotatingFileHandler(
        LOGS_DIR / 'frontend_access.log',
        maxBytes=10_485_760,
        backupCount=10,
        encoding='utf-8'
    )
    handler.setFormatter(logging.Formatter('%(asctime)s | %(message)s'))
    logger = logging.getLogger('frontend_access')
    logger.setLevel(logging.INFO)
    logger.addHandler(handler)
    app.access_logger = logger

    @app.before_request
    def log_request():
        if hasattr(app, 'access_logger'):
            from flask import request
            app.access_logger.info(f"{request.remote_addr} - {request.method} {request.path}")

    parser = argparse.ArgumentParser()
    parser.add_argument('--port', type=int, default=5000)
    parser.add_argument('--host', default='0.0.0.0')
    args = parser.parse_args()

    print("="*60)
    print("CPP Website Frontend Server (HTTP Only)")
    print("="*60)
    print(f"Host: {args.host}")
    print(f"Port: {args.port}")
    print(f"Protocol: HTTP")
    print(f"Serving files from: {PROJECT_ROOT}")
    print(f"Using error templates from: {BACKEND_DIR / 'templates'}")
    print("="*60)
    print(f"Access URLs:")
    print(f"  Local: http://127.0.0.1:{args.port}")
    print(f"  Network: http://{args.host}:{args.port}")
    print("="*60)

    app.run(host=args.host, port=args.port, debug=False)