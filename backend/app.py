from flask import Flask, request, g, session
from config import SECRET_KEY, BACKEND_DIR
from models.database import ensure_db_and_migrations
import logging
from logging.handlers import RotatingFileHandler
import os
from datetime import datetime
import json
import socket
import hashlib

from routes.static_routes import static_routes
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
from routes.error import register_error_handlers, render_error_template


# =====================================================
# SECURITY LOGGING CONFIGURATION
# =====================================================

class SecurityLogger:
    """Custom security logger for tracking all requests and security events"""
    
    def __init__(self, app=None):
        self.app = app
        if app is not None:
            self.init_app(app)
    
    def init_app(self, app):
        # Create logs directory if it doesn't exist
        if not os.path.exists('logs'):
            os.makedirs('logs', mode=0o755)
        
        # ===== SECURITY LOG =====
        # Tracks all requests with detailed information
        security_handler = RotatingFileHandler(
            'logs/security.log', 
            maxBytes=10_485_760,  # 10MB
            backupCount=30,  # Keep 30 days of logs
            encoding='utf-8'
        )
        security_handler.setLevel(logging.INFO)
        security_formatter = logging.Formatter(
            '%(asctime)s | %(levelname)s | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        security_handler.setFormatter(security_formatter)
        
        # Create security logger
        security_logger = logging.getLogger('security')
        security_logger.setLevel(logging.INFO)
        security_logger.addHandler(security_handler)
        security_logger.propagate = False  # Don't propagate to root logger
        app.security_logger = security_logger
        
        # ===== ACCESS LOG =====
        # Tracks successful and failed access attempts
        access_handler = RotatingFileHandler(
            'logs/access.log',
            maxBytes=10_485_760,
            backupCount=30,
            encoding='utf-8'
        )
        access_handler.setLevel(logging.INFO)
        access_formatter = logging.Formatter(
            '%(asctime)s | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        access_handler.setFormatter(access_formatter)
        
        access_logger = logging.getLogger('access')
        access_logger.setLevel(logging.INFO)
        access_logger.addHandler(access_handler)
        access_logger.propagate = False
        app.access_logger = access_logger
        
        # ===== AUTH LOG =====
        # Tracks authentication events (logins, logouts, failed attempts)
        auth_handler = RotatingFileHandler(
            'logs/auth.log',
            maxBytes=10_485_760,
            backupCount=30,
            encoding='utf-8'
        )
        auth_handler.setLevel(logging.INFO)
        auth_formatter = logging.Formatter(
            '%(asctime)s | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        auth_handler.setFormatter(auth_formatter)
        
        auth_logger = logging.getLogger('auth')
        auth_logger.setLevel(logging.INFO)
        auth_logger.addHandler(auth_handler)
        auth_logger.propagate = False
        app.auth_logger = auth_logger
        
        # ===== ERROR LOG =====
        # Tracks application errors and exceptions
        error_handler = RotatingFileHandler(
            'logs/error.log',
            maxBytes=10_485_760,
            backupCount=30,
            encoding='utf-8'
        )
        error_handler.setLevel(logging.ERROR)
        error_formatter = logging.Formatter(
            '%(asctime)s | %(levelname)s | %(message)s | %(pathname)s:%(lineno)d',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        error_handler.setFormatter(error_formatter)
        
        error_logger = logging.getLogger('error')
        error_logger.setLevel(logging.ERROR)
        error_logger.addHandler(error_handler)
        error_logger.propagate = False
        app.error_logger = error_logger


def get_client_ip():
    """Get real client IP address considering proxies"""
    if request.headers.get('X-Forwarded-For'):
        # Handle cases with multiple IPs in X-Forwarded-For
        return request.headers.get('X-Forwarded-For').split(',')[0].strip()
    elif request.headers.get('X-Real-IP'):
        return request.headers.get('X-Real-IP')
    else:
        return request.remote_addr or 'Unknown'


def get_request_id():
    """Generate unique request ID for tracking"""
    data = f"{datetime.utcnow().timestamp()}{get_client_ip()}{request.path}"
    return hashlib.md5(data.encode()).hexdigest()[:8]


def log_security_event(app, request_type='ACCESS', status=200, details=None):
    """Log security event with all relevant details"""
    try:
        # Basic request info
        ip = get_client_ip()
        method = request.method
        path = request.path
        user_agent = request.headers.get('User-Agent', 'Unknown')
        
        # Get session info if available
        user = session.get('username', 'Anonymous')
        
        # Get request ID from g or generate new one
        request_id = getattr(g, 'request_id', get_request_id())
        g.request_id = request_id
        
        # Build log message
        log_data = {
            'request_id': request_id,
            'ip': ip,
            'user': user,
            'method': method,
            'path': path,
            'status': status,
            'type': request_type,
            'user_agent': user_agent
        }
        
        # Add referrer if available
        referrer = request.headers.get('Referer', '')
        if referrer:
            log_data['referrer'] = referrer
        
        # Add custom details
        if details:
            log_data['details'] = details
        
        # Log to security log
        if hasattr(app, 'security_logger'):
            app.security_logger.info(json.dumps(log_data))
        
        # Also log to specific log based on type
        if request_type == 'AUTH' and hasattr(app, 'auth_logger'):
            app.auth_logger.info(json.dumps(log_data))
        elif status >= 400 and hasattr(app, 'error_logger'):
            app.error_logger.error(json.dumps(log_data))
        elif hasattr(app, 'access_logger'):
            app.access_logger.info(json.dumps(log_data))
    except Exception as e:
        app.logger.error(f"Error in log_security_event: {e}")


# =====================================================
# APPLICATION FACTORY
# =====================================================

def create_app():
    app = Flask(__name__, template_folder=str(BACKEND_DIR / "templates"))
    app.secret_key = SECRET_KEY

    # Add ProxyFix here if needed
    # app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

    # Initialize security logging
    SecurityLogger(app)

    # Initialize database
    ensure_db_and_migrations()

    # ===== REQUEST LOGGING MIDDLEWARE =====
    @app.before_request
    def before_request():
        """Log request before processing"""
        g.start_time = datetime.utcnow()
        g.request_id = get_request_id()
        
        # Log suspicious patterns
        if any(pattern in request.path.lower() for pattern in ['.php', '.asp', 'wp-', 'adminer', 'phpmyadmin']):
            log_security_event(
                app,
                request_type='SUSPICIOUS',
                status=0,
                details={'reason': 'Suspicious path pattern detected'}
            )
        
        # Log file access attempts
        if '.' in request.path and not request.path.endswith(('.html', '.css', '.js', '.jpg', '.png', '.gif', '.ico')):
            log_security_event(
                app,
                request_type='FILE_ACCESS',
                status=0,
                details={'file': request.path}
            )

    @app.after_request
    def after_request(response):
        """Log request after processing"""
        try:
            # Calculate request duration
            if hasattr(g, 'start_time'):
                duration = (datetime.utcnow() - g.start_time).total_seconds() * 1000
            else:
                duration = 0
            
            # Determine request type
            request_type = 'ACCESS'
            if '/auth/' in request.path or '/login' in request.path:
                request_type = 'AUTH'
            elif '/admin/' in request.path:
                request_type = 'ADMIN'
            elif '/api/' in request.path:
                request_type = 'API'
            
            # Log the request
            log_security_event(
                app,
                request_type=request_type,
                status=response.status_code,
                details={'duration_ms': round(duration, 2)}
            )
            
            # Add security headers
            response.headers['X-Request-ID'] = getattr(g, 'request_id', '')
            response.headers['X-Content-Type-Options'] = 'nosniff'
            response.headers['X-Frame-Options'] = 'DENY'
            response.headers['X-XSS-Protection'] = '1; mode=block'
            response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
            response.headers['Server'] = 'Unknown'
            
        except Exception as e:
            # Don't let logging errors break the response
            app.logger.error(f"Error in after_request: {e}")
        
        return response

    # ===== FAVICON HANDLER =====
    @app.route('/favicon.ico')
    def favicon():
        """Handle favicon requests to avoid 404/500 errors"""
        return '', 204

    # ===== ERROR HANDLING =====
    @app.errorhandler(403)
    def forbidden_error(error):
        log_security_event(
            app,
            request_type='ACCESS_DENIED',
            status=403,
            details={'reason': str(error)}
        )
        return render_error_template(403, "Access Denied", "You don't have permission to access this resource."), 403

    @app.errorhandler(404)
    def not_found_error(error):
        log_security_event(
            app,
            request_type='NOT_FOUND',
            status=404,
            details={'path': request.path}
        )
        return render_error_template(404, "Page Not Found", "The page you are looking for doesn't exist."), 404

    @app.errorhandler(500)
    def internal_error(error):
        log_security_event(
            app,
            request_type='ERROR',
            status=500,
            details={'error': str(error)}
        )
        return render_error_template(500, "Internal Server Error", "Something went wrong on our end."), 500

    # ===== BLUEPRINT REGISTRATION =====
    app.register_blueprint(static_routes)
    app.register_blueprint(admin_auth)
    app.register_blueprint(admin_home_bp)
    app.register_blueprint(admin_carousal_bp)
    app.register_blueprint(admin_notice)
    app.register_blueprint(admin_research)
    app.register_blueprint(admin_publication)
    app.register_blueprint(admin_forms_links_bp)
    app.register_blueprint(admin_people_bp)
    app.register_blueprint(admin_tender_bp)
    app.register_blueprint(admin_advertisement_bp)
    app.register_blueprint(public_api)

    # Register error handlers (MUST be done after blueprints)
    app = register_error_handlers(app)

    return app


# expose for WSGI servers
app = create_app()


# =====================================================
# UTILITY FUNCTION (can be imported elsewhere)
# =====================================================
def log_auth_event(event_type, username, success=True, details=None):
    """Helper function for logging authentication events from other modules"""
    from flask import current_app, request, session
    
    try:
        log_data = {
            'timestamp': datetime.utcnow().isoformat(),
            'event': event_type,
            'username': username,
            'success': success,
            'ip': get_client_ip(),
            'user_agent': request.headers.get('User-Agent', 'Unknown') if request else 'Unknown'
        }
        
        if details:
            log_data['details'] = details
        
        if hasattr(current_app, 'auth_logger'):
            current_app.auth_logger.info(json.dumps(log_data))
    except Exception as e:
        current_app.logger.error(f"Error in log_auth_event: {e}")