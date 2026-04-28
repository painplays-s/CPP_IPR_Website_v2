# backend/routes/admin_auth.py
from flask import Blueprint, request, redirect, url_for, flash, session, render_template, make_response
import sys
import os
import datetime
import time
import random
import string

# Add parent directory to path to import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Now import from models and utils
from models.database import get_db
from utils.password_utils import verify_password, hash_password

admin_auth = Blueprint('admin_auth', __name__, url_prefix='/cppipr_cms')

# Track failed login attempts (in-memory, resets on server restart)
# For production, consider storing this in database or Redis
failed_attempts = {}

# Track CAPTCHA attempts to prevent brute force
captcha_failed_attempts = {}

# Track POST request IDs to prevent duplicate processing
processed_requests = {}

def get_client_ip():
    """Get client IP address for tracking attempts"""
    if request.headers.get('X-Forwarded-For'):
        return request.headers.get('X-Forwarded-For').split(',')[0].strip()
    return request.remote_addr or 'Unknown'

def get_request_id():
    """Generate unique request ID from form data and timestamp"""
    # Use a combination of username and timestamp to create unique ID
    # This prevents the same form submission from being processed twice
    username = request.form.get('username', '')
    captcha_value = request.form.get('captcha_value', '')
    # Create a hash-like identifier
    return f"{username}_{captcha_value}_{int(time.time() / 30)}"  # Changes every 30 seconds

def is_request_duplicate():
    """Check if the same request has been processed recently"""
    request_id = get_request_id()
    if request_id in processed_requests:
        return True
    # Clean up old entries (older than 60 seconds)
    current_time = time.time()
    for rid in list(processed_requests.keys()):
        if current_time - processed_requests[rid] > 60:
            del processed_requests[rid]
    processed_requests[request_id] = time.time()
    return False

def cleanup_old_attempts():
    """Remove failed attempt records older than 15 minutes"""
    current_time = time.time()
    for key in list(failed_attempts.keys()):
        if current_time - failed_attempts[key]['timestamp'] > 900:  # 15 minutes
            del failed_attempts[key]
    
    # Clean up CAPTCHA failed attempts
    for key in list(captcha_failed_attempts.keys()):
        if current_time - captcha_failed_attempts[key]['timestamp'] > 900:
            del captcha_failed_attempts[key]

def validate_captcha(captcha_input, captcha_value):
    """
    Validate CAPTCHA input against stored value.
    CAPTCHA is case-sensitive.
    """
    if not captcha_input or not captcha_value:
        return False
    return captcha_input.strip() == captcha_value.strip()

def is_captcha_rate_limited(ip):
    """Check if IP has too many CAPTCHA failures"""
    cleanup_old_attempts()
    key = f"captcha_{ip}"
    data = captcha_failed_attempts.get(key, {'count': 0, 'timestamp': time.time()})
    return data['count'] >= 10

def increment_captcha_failure(ip):
    """Increment CAPTCHA failure count for IP"""
    cleanup_old_attempts()
    key = f"captcha_{ip}"
    current_time = time.time()
    
    if key in captcha_failed_attempts:
        captcha_failed_attempts[key]['count'] += 1
        captcha_failed_attempts[key]['timestamp'] = current_time
    else:
        captcha_failed_attempts[key] = {'count': 1, 'timestamp': current_time}

@admin_auth.route('/login', methods=['GET', 'POST'])
def admin_login():
    # Handle GET request - just show the login page
    if request.method == 'GET':
        # Clear any existing session data on fresh login page load
        return render_template('admin_login.html')
    
    # Handle POST request - process login attempt
    if request.method == 'POST':
        # CRITICAL: Check for duplicate form submission (prevents refresh from counting)
        if is_request_duplicate():
            flash('This login attempt has already been processed. Please try again.', 'warning')
            return redirect(url_for('admin_auth.admin_login'))
        
        username = request.form.get('username')
        password = request.form.get('password')
        captcha_input = request.form.get('captcha_input')
        captcha_value = request.form.get('captcha_value')
        client_ip = get_client_ip()
        
        # Check if IP is rate limited for CAPTCHA failures
        if is_captcha_rate_limited(client_ip):
            flash('Too many CAPTCHA failures. Please wait 15 minutes before trying again.', 'error')
            return redirect(url_for('admin_auth.admin_login'))
        
        # Validate required fields
        if not username or not password:
            flash('Username and password are required. / उपयोगकर्ता नाम और पासवर्ड आवश्यक है।', 'error')
            return redirect(url_for('admin_auth.admin_login'))
        
        # FIRST: Check if account exists and is active before any attempt counting
        conn = get_db()
        user = None
        try:
            user = conn.execute(
                "SELECT * FROM user WHERE username = ?",
                (username,)
            ).fetchone()
            
            if not user:
                # User doesn't exist - don't count attempts, just show generic error
                flash('Invalid credentials. / अमान्य क्रेडेंशियल।', 'error')
                return redirect(url_for('admin_auth.admin_login'))
            
            # Check if account is already locked
            if user['is_active'] == 0:
                flash('This account has been locked. Please contact administrator. / यह खाता लॉक कर दिया गया है। कृपया व्यवस्थापक से संपर्क करें।', 'locked')
                return redirect(url_for('admin_auth.admin_login'))
                
        except Exception as e:
            flash(f'An error occurred: {str(e)}', 'error')
            return redirect(url_for('admin_auth.admin_login'))
        finally:
            if conn:
                conn.close()
        
        # SECOND: Validate CAPTCHA (this should NOT count toward password attempts)
        if not captcha_input or not captcha_value:
            increment_captcha_failure(client_ip)
            flash('CAPTCHA code is required. / CAPTCHA कोड आवश्यक है।', 'error')
            return redirect(url_for('admin_auth.admin_login'))
        
        if not validate_captcha(captcha_input, captcha_value):
            increment_captcha_failure(client_ip)
            flash('Invalid CAPTCHA code. Please try again. / अमान्य CAPTCHA कोड। कृपया पुनः प्रयास करें।', 'error')
            return redirect(url_for('admin_auth.admin_login'))
        
        # CAPTCHA is valid, reset CAPTCHA failure count for this IP
        key = f"captcha_{client_ip}"
        if key in captcha_failed_attempts:
            del captcha_failed_attempts[key]
        
        # THIRD: Check password - ONLY NOW do we count toward login attempts
        conn = get_db()
        try:
            # Re-fetch user (since connection was closed above)
            user = conn.execute(
                "SELECT * FROM user WHERE username = ?",
                (username,)
            ).fetchone()
            
            # Clean up old attempts
            cleanup_old_attempts()
            
            # Create key for this user
            user_key = username
            
            # Get current attempt count
            attempt_data = failed_attempts.get(user_key, {'count': 0, 'timestamp': time.time()})
            
            # Check if user has already exceeded max attempts (should be locked, but double-check)
            if attempt_data['count'] >= 5:
                # Ensure account is locked in database
                conn.execute(
                    "UPDATE user SET is_active = 0 WHERE id = ?",
                    (user['id'],)
                )
                conn.commit()
                flash('Account locked due to multiple failed login attempts. Please contact administrator.', 'locked')
                return redirect(url_for('admin_auth.admin_login'))
            
            # Verify password
            if verify_password(user['password'], password):
                # Successful login - reset failed attempts for this user
                if user_key in failed_attempts:
                    del failed_attempts[user_key]
                
                session['admin_logged_in'] = True
                session['user_id'] = user['id']
                session['username'] = user['username']
                
                # Update last login
                conn.execute(
                    "UPDATE user SET last_login = ? WHERE id = ?",
                    (datetime.datetime.now().isoformat(), user['id'])
                )
                conn.commit()
                
                flash(f'Welcome {username}! Logged in successfully. / स्वागत है {username}! सफलतापूर्वक लॉगिन किया।', 'success')
                return redirect(url_for('admin_home.admin_home'))
            else:
                # IMPORTANT: Only increment attempt counter for ACTUAL password failures
                current_time = time.time()
                attempt_data['count'] += 1
                attempt_data['timestamp'] = current_time
                failed_attempts[user_key] = attempt_data
                
                remaining_attempts = 5 - attempt_data['count']
                
                # Check if exceeded max attempts
                if attempt_data['count'] >= 5:
                    # Lock the account
                    conn.execute(
                        "UPDATE user SET is_active = 0 WHERE id = ?",
                        (user['id'],)
                    )
                    conn.commit()
                    
                    # Clear failed attempts for this user since account is locked
                    if user_key in failed_attempts:
                        del failed_attempts[user_key]
                    
                    flash('Account locked due to multiple failed login attempts. Please contact administrator. / कई असफल लॉगिन प्रयासों के कारण खाता लॉक कर दिया गया। कृपया व्यवस्थापक से संपर्क करें।', 'locked')
                else:
                    # Show remaining attempts
                    if remaining_attempts == 1:
                        flash(f'Invalid password. This is your LAST attempt before account lock! / अमान्य पासवर्ड। खाता लॉक होने से पहले यह आपका अंतिम प्रयास है!', 'warning')
                    else:
                        flash(f'Invalid password. {remaining_attempts} attempts remaining before account lock. / अमान्य पासवर्ड। खाता लॉक होने से पहले {remaining_attempts} प्रयास शेष हैं।', 'attempts')
                
                return redirect(url_for('admin_auth.admin_login'))
                    
        except Exception as e:
            flash(f'An error occurred: {str(e)} / एक त्रुटि हुई: {str(e)}', 'error')
            return redirect(url_for('admin_auth.admin_login'))
        finally:
            conn.close()

@admin_auth.route('/logout')
def admin_logout():
    username = session.get('username', 'User')
    session.clear()
    flash(f'{username} logged out successfully. / {username} सफलतापूर्वक लॉगआउट किया।', 'success')
    return redirect(url_for('admin_auth.admin_login'))

@admin_auth.route('/unlock/<int:user_id>', methods=['POST'])
def unlock_account(user_id):
    """Admin function to unlock a locked account"""
    if not session.get('admin_logged_in'):
        flash('Unauthorized access. / अनधिकृत पहुंच।', 'error')
        return redirect(url_for('admin_auth.admin_login'))
    
    conn = get_db()
    try:
        user = conn.execute(
            "SELECT username FROM user WHERE id = ?",
            (user_id,)
        ).fetchone()
        
        if user:
            user_key = user['username']
            if user_key in failed_attempts:
                del failed_attempts[user_key]
        
        conn.execute(
            "UPDATE user SET is_active = 1 WHERE id = ?",
            (user_id,)
        )
        conn.commit()
        flash('Account unlocked successfully. / खाता सफलतापूर्वक अनलॉक किया गया।', 'success')
    except Exception as e:
        flash(f'Error unlocking account: {str(e)} / खाता अनलॉक करने में त्रुटि: {str(e)}', 'error')
    finally:
        conn.close()
    
    return redirect(url_for('admin_home.admin_home'))

@admin_auth.route('/reset-captcha-failures', methods=['POST'])
def reset_captcha_failures():
    """Admin function to reset CAPTCHA failure counts for an IP"""
    if not session.get('admin_logged_in'):
        flash('Unauthorized access.', 'error')
        return redirect(url_for('admin_auth.admin_login'))
    
    ip = request.form.get('ip')
    if ip:
        key = f"captcha_{ip}"
        if key in captcha_failed_attempts:
            del captcha_failed_attempts[key]
        flash(f'CAPTCHA failures reset for IP: {ip}', 'success')
    else:
        captcha_failed_attempts.clear()
        flash('All CAPTCHA failure records cleared.', 'success')
    
    return redirect(url_for('admin_home.admin_home'))