# backend/routes/admin_notice.py
from datetime import datetime, timedelta
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from werkzeug.utils import secure_filename
from utils.decorators import login_required
from utils.helpers import format_date
from models.database import get_db, resequence
from config import NOTICE_UPLOAD_DIR

admin_notice = Blueprint('admin_notice', __name__, url_prefix='/admin')

def init_notice_table():
    """Add new_expire_date and uploaded_at columns to current_notice table if not exists"""
    conn = get_db()
    
    # Add new_expire_date column
    try:
        conn.execute("SELECT new_expire_date FROM current_notice LIMIT 1")
    except:
        conn.execute("ALTER TABLE current_notice ADD COLUMN new_expire_date TEXT")
        conn.commit()
    
    # Add uploaded_at column
    try:
        conn.execute("SELECT uploaded_at FROM current_notice LIMIT 1")
    except:
        conn.execute("ALTER TABLE current_notice ADD COLUMN uploaded_at TEXT DEFAULT CURRENT_TIMESTAMP")
        conn.commit()
    
    conn.close()

# Initialize table on module import
init_notice_table()

def check_and_update_notice_new_status():
    """Auto-remove NEW badge for expired notices"""
    conn = get_db()
    now = datetime.now().isoformat()
    conn.execute("""
        UPDATE current_notice 
        SET is_new = 0 
        WHERE is_new = 1 
        AND new_expire_date IS NOT NULL 
        AND new_expire_date < ?
    """, (now,))
    conn.commit()
    conn.close()

@admin_notice.route('/current_notice')
@login_required
def admin_current_notice():
    check_and_update_notice_new_status()  # Auto-cleanup expired badges
    
    conn = get_db()
    rows = conn.execute(
        "SELECT * FROM current_notice ORDER BY sort_order ASC, uploaded_at DESC"
    ).fetchall()
    conn.close()
    return render_template('admin_current_notice.html', items=rows, format_date=format_date)

@admin_notice.route('/current-notice/upload', methods=['POST'])
@login_required
def upload_current_notice():
    f = request.files.get('file')
    if not f:
        flash('File required', 'error')
        return redirect(url_for('admin_notice.admin_current_notice'))

    fname = secure_filename(f.filename)
    final_name = f"{datetime.now():%Y%m%d%H%M%S}_{fname}"
    f.save(NOTICE_UPLOAD_DIR / final_name)

    # Get form data
    is_new = 1 if request.form.get('is_new') else 0
    
    # Fix: Convert float-like string to integer (e.g., "7.0" -> 7)
    new_expire_days_input = request.form.get('new_expire_days', '7')
    try:
        new_expire_days = int(float(new_expire_days_input))
    except (ValueError, TypeError):
        new_expire_days = 7  # Default fallback
    
    # Calculate expiration date
    new_expire_date = None
    if is_new:
        expire_dt = datetime.now() + timedelta(days=new_expire_days)
        new_expire_date = expire_dt.isoformat()

    conn = get_db()
    
    # Insert with sort_order = 0 (new uploads appear first)
    conn.execute("""
        INSERT INTO current_notice
        (type, description_en, description_hi, filename, is_new, new_expire_date, uploaded_at, sort_order)
        VALUES (?, ?, ?, ?, ?, ?, ?, 0)
    """, (
        request.form.get('type'),
        request.form.get('description_en'),
        request.form.get('description_hi', ''),
        final_name,
        is_new,
        new_expire_date,
        datetime.now().isoformat(),
    ))
    conn.commit()
    conn.close()

    flash('Notice added successfully.', 'success')
    return redirect(url_for('admin_notice.admin_current_notice'))

@admin_notice.route('/current-notice/edit/<int:item_id>', methods=['POST'])
@login_required
def edit_current_notice(item_id):
    data = request.get_json(force=True)
    is_new = 1 if data.get('is_new') else 0
    
    # Fix: Convert float-like string to integer for days if provided
    new_expire_days_input = data.get('new_expire_days', 7)
    try:
        new_expire_days = int(float(new_expire_days_input))
    except (ValueError, TypeError):
        new_expire_days = 7
    
    # Calculate new expiration date if is_new is set
    new_expire_date = None
    if is_new:
        expire_dt = datetime.now() + timedelta(days=new_expire_days)
        new_expire_date = expire_dt.isoformat()
    
    conn = get_db()
    conn.execute("""
        UPDATE current_notice
        SET type=?, description_en=?, description_hi=?, is_new=?, new_expire_date=?
        WHERE id=?
    """, (
        data.get('type'),
        data.get('description_en'),
        data.get('description_hi', ''),
        is_new,
        new_expire_date,
        item_id
    ))
    conn.commit()
    conn.close()
    return jsonify({'success': True})

@admin_notice.route('/current-notice/delete/<int:item_id>', methods=['POST'])
@login_required
def delete_current_notice(item_id):
    conn = get_db()
    row = conn.execute(
        "SELECT filename FROM current_notice WHERE id=?", (item_id,)
    ).fetchone()
    conn.execute("DELETE FROM current_notice WHERE id=?", (item_id,))
    conn.commit()
    conn.close()

    try:
        (NOTICE_UPLOAD_DIR / row["filename"]).unlink(missing_ok=True)
    except Exception:
        pass

    resequence("current_notice")
    return jsonify({'success': True})

@admin_notice.route('/current-notice/reorder', methods=['POST'])
@login_required
def reorder_current_notice():
    order = request.get_json(force=True).get('order', [])
    conn = get_db()
    for idx, oid in enumerate(order, start=1):
        conn.execute("UPDATE current_notice SET sort_order=? WHERE id=?", (idx, oid))
    conn.commit()
    conn.close()
    return jsonify({'success': True})