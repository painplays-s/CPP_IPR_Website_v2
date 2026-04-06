# backend/routes/admin_auth.py
from flask import Blueprint, request, redirect, url_for, flash, session, render_template
import sys
import os
import datetime
import time

# Add parent directory to path to import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Now import from models and utils
from models.database import get_db
from utils.password_utils import verify_password, hash_password

admin_auth = Blueprint('admin_auth', __name__, url_prefix='/cppipr_cms')

# Track failed login attempts (in-memory, resets on server restart)
# For production, consider storing this in database or Redis
failed_attempts = {}

def get_client_ip():
    """Get client IP address for tracking attempts"""
    if request.headers.get('X-Forwarded-For'):
        return request.headers.get('X-Forwarded-For').split(',')[0].strip()
    return request.remote_addr or 'Unknown'

def cleanup_old_attempts():
    """Remove failed attempt records older than 15 minutes"""
    current_time = time.time()
    for key in list(failed_attempts.keys()):
        if current_time - failed_attempts[key]['timestamp'] > 900:  # 15 minutes
            del failed_attempts[key]

@admin_auth.route('/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        client_ip = get_client_ip()
        
        if not username or not password:
            flash('Username and password are required.', 'error')
            return render_template('admin_login.html')
        
        conn = get_db()
        try:
            # Get user from database
            user = conn.execute(
                "SELECT * FROM user WHERE username = ?",
                (username,)
            ).fetchone()
            
            # Check if user exists
            if not user:
                flash('Invalid credentials.', 'error')
                return render_template('admin_login.html')
            
            # Check if account is locked
            if user['is_active'] == 0:
                flash('This account has been locked due to multiple failed login attempts. Please contact administrator.', 'locked')
                return render_template('admin_login.html')
            
            # Clean up old attempts
            cleanup_old_attempts()
            
            # Create key for this user (without IP - we want per-user tracking)
            key = username
            
            # Get current attempt count
            attempt_data = failed_attempts.get(key, {'count': 0, 'timestamp': time.time()})
            
            # Verify password
            if verify_password(user['password'], password):
                # Successful login - reset failed attempts for this user
                if key in failed_attempts:
                    del failed_attempts[key]
                
                session['admin_logged_in'] = True
                session['user_id'] = user['id']
                session['username'] = user['username']
                
                # Update last login
                conn.execute(
                    "UPDATE user SET last_login = ? WHERE id = ?",
                    (datetime.datetime.now().isoformat(), user['id'])
                )
                conn.commit()
                
                flash(f'Welcome {username}! Logged in successfully.', 'success')
                return redirect(url_for('admin_home.admin_home'))
            else:
                # Failed login - increment counter
                current_time = time.time()
                attempt_data['count'] += 1
                attempt_data['timestamp'] = current_time
                failed_attempts[key] = attempt_data
                
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
                    if key in failed_attempts:
                        del failed_attempts[key]
                    
                    flash('Account locked due to multiple failed login attempts. Please contact administrator.', 'locked')
                else:
                    # Show remaining attempts
                    if remaining_attempts == 1:
                        flash(f'Invalid password. This is your LAST attempt before account lock!', 'warning')
                    else:
                        flash(f'Invalid password. {remaining_attempts} attempts remaining before account lock.', 'attempts')
                    
        except Exception as e:
            flash(f'An error occurred: {str(e)}', 'error')
        finally:
            conn.close()
            
    return render_template('admin_login.html')

@admin_auth.route('/logout')
def admin_logout():
    username = session.get('username', 'User')
    session.clear()
    flash(f'{username} logged out successfully.', 'success')
    return redirect(url_for('admin_auth.admin_login'))

# Optional: Add an admin function to unlock accounts
@admin_auth.route('/unlock/<int:user_id>', methods=['POST'])
def unlock_account(user_id):
    # This should be protected by admin-only access
    # You might want to add this to a separate admin management page
    if not session.get('admin_logged_in'):
        flash('Unauthorized access.', 'error')
        return redirect(url_for('admin_auth.admin_login'))
    
    conn = get_db()
    try:
        # Get username to clear failed attempts
        user = conn.execute(
            "SELECT username FROM user WHERE id = ?",
            (user_id,)
        ).fetchone()
        
        if user:
            # Clear failed attempts for this user
            key = user['username']
            if key in failed_attempts:
                del failed_attempts[key]
        
        # Unlock account
        conn.execute(
            "UPDATE user SET is_active = 1 WHERE id = ?",
            (user_id,)
        )
        conn.commit()
        flash('Account unlocked successfully.', 'success')
    except Exception as e:
        flash(f'Error unlocking account: {str(e)}', 'error')
    finally:
        conn.close()
    
    return redirect(url_for('admin_home.admin_home'))