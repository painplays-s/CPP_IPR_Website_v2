# backend/routes/error.py
from flask import Blueprint, render_template, request, jsonify
from werkzeug.exceptions import HTTPException
import traceback
import os

error_bp = Blueprint('error', __name__)

# Custom error classes
class AccessDeniedError(Exception):
    pass

class MaintenanceError(Exception):
    pass

# Error handlers for HTTP status codes
@error_bp.app_errorhandler(400)
def bad_request_error(error):
    """Handle 400 Bad Request"""
    return render_error_template(400, "Bad Request", 
                                 "The request could not be understood by the server due to malformed syntax."), 400

@error_bp.app_errorhandler(401)
def unauthorized_error(error):
    """Handle 401 Unauthorized"""
    return render_error_template(401, "Unauthorized", 
                                 "You need to log in to access this page."), 401

@error_bp.app_errorhandler(403)
def forbidden_error(error):
    """Handle 403 Forbidden"""
    return render_error_template(403, "Access Denied", 
                                 "You don't have permission to access this resource."), 403

@error_bp.app_errorhandler(404)
def not_found_error(error):
    """Handle 404 Not Found"""
    return render_error_template(404, "Page Not Found", 
                                 "The page you are looking for doesn't exist or has been moved."), 404

@error_bp.app_errorhandler(405)
def method_not_allowed_error(error):
    """Handle 405 Method Not Allowed"""
    return render_error_template(405, "Method Not Allowed", 
                                 "The method is not allowed for this endpoint."), 405

@error_bp.app_errorhandler(408)
def request_timeout_error(error):
    """Handle 408 Request Timeout"""
    return render_error_template(408, "Request Timeout", 
                                 "The server timed out waiting for the request."), 408

@error_bp.app_errorhandler(429)
def too_many_requests_error(error):
    """Handle 429 Too Many Requests"""
    return render_error_template(429, "Too Many Requests", 
                                 "You have made too many requests. Please wait and try again."), 429

@error_bp.app_errorhandler(500)
def internal_server_error(error):
    """Handle 500 Internal Server Error"""
    # Log the error for debugging (but don't show to user)
    if os.getenv('FLASK_ENV') == 'development':
        traceback.print_exc()
    
    return render_error_template(500, "Internal Server Error", 
                                 "Something went wrong on our end. Please try again later."), 500

@error_bp.app_errorhandler(502)
def bad_gateway_error(error):
    """Handle 502 Bad Gateway"""
    return render_error_template(502, "Bad Gateway", 
                                 "Received an invalid response from the upstream server."), 502

@error_bp.app_errorhandler(503)
def service_unavailable_error(error):
    """Handle 503 Service Unavailable"""
    return render_error_template(503, "Service Unavailable", 
                                 "The server is temporarily unable to handle the request. Please try again later."), 503

@error_bp.app_errorhandler(504)
def gateway_timeout_error(error):
    """Handle 504 Gateway Timeout"""
    return render_error_template(504, "Gateway Timeout", 
                                 "The upstream server failed to respond in time."), 504

# Custom error handlers
@error_bp.app_errorhandler(AccessDeniedError)
def handle_access_denied(error):
    """Handle custom Access Denied error"""
    return render_error_template(403, "Access Denied", str(error)), 403

@error_bp.app_errorhandler(MaintenanceError)
def handle_maintenance(error):
    """Handle maintenance mode error"""
    return render_error_template(503, "Under Maintenance", 
                                 "The site is currently under maintenance. Please check back later."), 503

# Catch-all for any unhandled exceptions
@error_bp.app_errorhandler(Exception)
def handle_unhandled_exception(error):
    """Handle any unhandled exceptions"""
    # Log the error
    if os.getenv('FLASK_ENV') == 'development':
        traceback.print_exc()
    
    return render_error_template(500, "Unexpected Error", 
                                 "An unexpected error occurred. Our team has been notified."), 500

def render_error_template(code, title, message):
    """Helper function to render error template"""
    # For API requests, return JSON instead of HTML
    if request.path.startswith('/api/') or request.headers.get('Accept') == 'application/json':
        return jsonify({
            'error': True,
            'code': code,
            'title': title,
            'message': message
        }), code
    
    # For normal requests, render the error page
    return render_template('error.html', 
                          error_code=code,
                          error_title=title,
                          error_message=message,
                          error_description=get_error_description(code))

def get_error_description(code):
    """Get detailed description based on error code"""
    descriptions = {
        400: "This could be due to malformed syntax or invalid parameters in your request.",
        401: "Please log in with valid credentials to access this resource.",
        403: "This might be due to insufficient privileges or trying to access restricted areas.",
        404: "Please check the URL for typos or return to the <a href='/' class='error-link'>homepage</a>.",
        405: "The HTTP method used is not supported for this endpoint.",
        408: "The request took too long to complete. Please try again.",
        429: "Rate limit exceeded. Please wait before making more requests.",
        500: "Our technical team has been notified and is working on fixing the issue.",
        502: "This is usually a temporary issue. Please try refreshing the page.",
        503: "The server is temporarily busy. Please try again in a few minutes.",
        504: "The server took too long to respond. Please try again."
    }
    return descriptions.get(code, "Please try again or contact support if the problem persists.")

# Function to register error handlers with the app
def register_error_handlers(app):
    """Register all error handlers with the Flask app"""
    app.register_blueprint(error_bp)
    
    # Register error handlers
    app.register_error_handler(400, bad_request_error)
    app.register_error_handler(401, unauthorized_error)
    app.register_error_handler(403, forbidden_error)
    app.register_error_handler(404, not_found_error)
    app.register_error_handler(405, method_not_allowed_error)
    app.register_error_handler(408, request_timeout_error)
    app.register_error_handler(429, too_many_requests_error)
    app.register_error_handler(500, internal_server_error)
    app.register_error_handler(502, bad_gateway_error)
    app.register_error_handler(503, service_unavailable_error)
    app.register_error_handler(504, gateway_timeout_error)
    app.register_error_handler(Exception, handle_unhandled_exception)
    
    return app