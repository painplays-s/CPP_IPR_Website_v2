# backend/routes/admin_publication.py
from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from utils.decorators import login_required
from utils.helpers import format_date
from models.database import get_db, resequence
import re

admin_publication = Blueprint('admin_publication', __name__, url_prefix='/admin')

# Add current date to template context
@admin_publication.context_processor
def inject_now():
    return {'now': datetime.now}

def validate_past_date(date_string):
    """Validate date format (YYYY-MM-DD) and ensure it's in the past"""
    if not date_string:
        return False
    
    # Check if date matches YYYY-MM-DD format
    if not re.match(r'^\d{4}-\d{2}-\d{2}$', date_string):
        return False
    
    # Parse the date parts
    try:
        year, month, day = map(int, date_string.split('-'))
        
        # Check year is 4 digits (between 1000 and 9999)
        if year < 1000 or year > 9999:
            return False
        
        # Check if month is valid (1-12)
        if month < 1 or month > 12:
            return False
        
        # Check if day is valid for the given month
        # Create a date object to validate (this will catch invalid dates like Feb 30)
        date_obj = datetime(year, month, day)
        
        # Check if date is in the past (not today or future)
        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        return date_obj < today
    except (ValueError, TypeError):
        return False

@admin_publication.route('/recent-publication')
@login_required
def admin_recent_publication():
    conn = get_db()
    rows = conn.execute(
        "SELECT * FROM recent_publication ORDER BY sort_order ASC, date DESC"
    ).fetchall()
    conn.close()
    return render_template(
        'admin_recent_publication.html', 
        items=rows, 
        format_date=format_date
    )

@admin_publication.route('/recent-publication/add', methods=['POST'])
@login_required
def add_recent_publication():
    title_en = request.form.get('title_en', '').strip()
    title_hi = request.form.get('title_hi', '').strip()
    url = request.form.get('url', '').strip()
    date = request.form.get('date', '').strip()

    # Validate required fields
    if not title_en or not url or not date:
        flash('Title (English), URL, and Date are required.', 'error')
        return redirect(url_for('admin_publication.admin_recent_publication'))
    
    # Validate date is in the past (prevent future dates)
    if not validate_past_date(date):
        flash('Invalid date. Please enter a valid past date (YYYY-MM-DD format) that is before today.', 'error')
        return redirect(url_for('admin_publication.admin_recent_publication'))

    conn = get_db()
    try:
        next_order = conn.execute(
            "SELECT COALESCE(MAX(sort_order),0) FROM recent_publication"
        ).fetchone()[0] + 1

        conn.execute("""
            INSERT INTO recent_publication
            (title_en, title_hi, url, date, uploaded_at, sort_order)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            title_en,
            title_hi,
            url,
            date,
            datetime.now().isoformat(timespec='seconds'),
            next_order,
        ))
        conn.commit()
        flash('Publication added successfully.', 'success')
    finally:
        conn.close()

    return redirect(url_for('admin_publication.admin_recent_publication'))

@admin_publication.route('/recent-publication/edit/<int:item_id>', methods=['POST'])
@login_required
def edit_recent_publication(item_id):
    data = request.get_json(force=True)
    
    # Validate date is in the past (prevent future dates)
    date_value = data.get('date', '')
    if not validate_past_date(date_value):
        return jsonify({'success': False, 'error': 'Invalid date. Please enter a valid past date (YYYY-MM-DD format) that is before today.'}), 400
    
    conn = get_db()
    conn.execute("""
        UPDATE recent_publication
        SET title_en=?, title_hi=?, url=?, date=?
        WHERE id=?
    """, (
        data.get('title_en', ''),
        data.get('title_hi', ''),
        data.get('url', ''),
        date_value,
        item_id
    ))
    conn.commit()
    conn.close()
    return jsonify({'success': True})

@admin_publication.route('/recent-publication/delete/<int:item_id>', methods=['POST'])
@login_required
def delete_recent_publication(item_id):
    conn = get_db()
    conn.execute("DELETE FROM recent_publication WHERE id=?", (item_id,))
    conn.commit()
    conn.close()

    resequence("recent_publication")
    return jsonify({'success': True})

@admin_publication.route('/recent-publication/reorder', methods=['POST'])
@login_required
def reorder_recent_publication():
    order = request.get_json(force=True).get('order', [])
    conn = get_db()
    for idx, oid in enumerate(order, start=1):
        conn.execute("UPDATE recent_publication SET sort_order=? WHERE id=?", (idx, oid))
    conn.commit()
    conn.close()
    return jsonify({'success': True})