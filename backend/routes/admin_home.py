# backend/routes/admin_home.py
from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from utils.decorators import login_required

admin_home_bp = Blueprint('admin_home', __name__, url_prefix='/cppipr_cms')

@admin_home_bp.route('')
@login_required
def admin_home():
    """Admin dashboard homepage"""
    return render_template('admin_home.html')

@admin_home_bp.route('/logout')
def logout():
    """Logout admin user"""
    session.clear()
    flash('You have been logged out successfully.', 'success')
    return redirect(url_for('admin_auth.admin_login'))