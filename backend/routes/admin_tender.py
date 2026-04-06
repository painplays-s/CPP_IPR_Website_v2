# backend/routes/admin_tender.py
from datetime import datetime, timedelta
from flask import Blueprint, request, jsonify, render_template, redirect, url_for, flash
from pathlib import Path
from werkzeug.utils import secure_filename
from models.database import get_db
from utils.decorators import login_required
from utils.helpers import format_date
from config import PROJECT_ROOT

admin_tender_bp = Blueprint('admin_tender', __name__, url_prefix='/admin/tender')

UPLOAD_FOLDER = PROJECT_ROOT / "assets" / "files" / "tenders"
UPLOAD_FOLDER.mkdir(parents=True, exist_ok=True)

def init_tender_table():
    """Initialize tender table"""
    db = get_db()
    db.execute("""
        CREATE TABLE IF NOT EXISTS tenders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tender_no TEXT NOT NULL,
            nature_of_work TEXT NOT NULL,
            tender_date TEXT NOT NULL,
            tender_end_date TEXT NOT NULL,
            filename TEXT NOT NULL,
            is_new INTEGER DEFAULT 0,
            new_expire_date TEXT,
            year INTEGER NOT NULL,
            display_order INTEGER DEFAULT 0,
            uploaded_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)
    db.commit()

# Initialize table on import
init_tender_table()

def check_and_update_new_status():
    """Auto-remove NEW badge for expired tenders"""
    db = get_db()
    now = datetime.now().isoformat()
    db.execute("""
        UPDATE tenders 
        SET is_new = 0 
        WHERE is_new = 1 
        AND new_expire_date IS NOT NULL 
        AND new_expire_date < ?
    """, (now,))
    db.commit()

# ============================================
# ADMIN PANEL PAGE
# ============================================
@admin_tender_bp.route('/')
@login_required
def admin_tender_page():
    return render_template('admin_tender.html', format_date=format_date)

# ============================================
# GET YEARS
# ============================================
@admin_tender_bp.route('/years')
@login_required
def get_tender_years():
    check_and_update_new_status()
    db = get_db()
    rows = db.execute("SELECT DISTINCT year FROM tenders ORDER BY year DESC").fetchall()
    years = [r['year'] for r in rows]
    return jsonify({'years': years})

# ============================================
# CREATE NEW YEAR
# ============================================
@admin_tender_bp.route('/year/create', methods=['POST'])
@login_required
def create_tender_year():
    data = request.json
    year = data.get('year')
    
    if not year:
        return jsonify({'error': 'Year required'}), 400
    
    return jsonify({'success': True, 'year': year})

# ============================================
# GET TENDERS BY YEAR
# ============================================
@admin_tender_bp.route('/year/<int:year>')
@login_required
def get_tenders_by_year(year):
    check_and_update_new_status()
    db = get_db()
    rows = db.execute("""
        SELECT * FROM tenders 
        WHERE year = ? 
        ORDER BY display_order ASC, uploaded_at DESC
    """, (year,)).fetchall()
    
    tenders = [{
        'id': r['id'],
        'tender_no': r['tender_no'],
        'nature_of_work': r['nature_of_work'],
        'tender_date': r['tender_date'],
        'tender_end_date': r['tender_end_date'],
        'filename': r['filename'],
        'is_new': bool(r['is_new']),
        'year': r['year'],
        'uploaded_at': r['uploaded_at'] if r['uploaded_at'] else ''
    } for r in rows]
    
    return jsonify({'tenders': tenders})

# ============================================
# UPLOAD TENDER
# ============================================
@admin_tender_bp.route('/upload', methods=['POST'])
@login_required
def upload_tender():
    tender_no = request.form.get('tender_no', '').strip()
    nature_of_work = request.form.get('nature_of_work', '').strip()
    tender_date = request.form.get('tender_date', '').strip()
    tender_end_date = request.form.get('tender_end_date', '').strip()
    year = request.form.get('year', '').strip()
    is_new = 1 if request.form.get('is_new') else 0
    
    # Fix: Convert float-like string to integer (e.g., "7.0" -> 7)
    new_expire_days_input = request.form.get('new_expire_days', '7')
    try:
        new_expire_days = int(float(new_expire_days_input))
    except (ValueError, TypeError):
        new_expire_days = 7  # Default fallback
    
    if not all([tender_no, nature_of_work, tender_date, tender_end_date, year]):
        flash('All fields required', 'error')
        return redirect(url_for('admin_tender.admin_tender_page'))
    
    # Validate date formats (support both ISO date and datetime formats)
    try:
        # Try parsing tender_date as datetime first, then as date
        try:
            start_date_obj = datetime.strptime(tender_date, '%Y-%m-%dT%H:%M')
        except ValueError:
            try:
                start_date_obj = datetime.strptime(tender_date, '%Y-%m-%d')
                # Set time to 00:00:00 for date-only inputs
                start_date_obj = start_date_obj.replace(hour=0, minute=0, second=0)
            except ValueError:
                raise ValueError(f"Invalid tender_date format: {tender_date}")
        
        # Try parsing tender_end_date as datetime first, then as date
        try:
            end_date_obj = datetime.strptime(tender_end_date, '%Y-%m-%dT%H:%M')
        except ValueError:
            try:
                end_date_obj = datetime.strptime(tender_end_date, '%Y-%m-%d')
                # Set time to 23:59:59 for date-only end dates (end of day)
                end_date_obj = end_date_obj.replace(hour=23, minute=59, second=59)
            except ValueError:
                raise ValueError(f"Invalid tender_end_date format: {tender_end_date}")
        
        # Validate that end date is not before start date
        if end_date_obj < start_date_obj:
            flash('End date cannot be before start date', 'error')
            return redirect(url_for('admin_tender.admin_tender_page'))
        
        # Convert back to ISO format for storage (store as full ISO datetime)
        tender_date = start_date_obj.isoformat()
        tender_end_date = end_date_obj.isoformat()
            
    except ValueError as e:
        flash(f'Invalid date format. Please use YYYY-MM-DD or YYYY-MM-DDTHH:MM format', 'error')
        return redirect(url_for('admin_tender.admin_tender_page'))
    
    # Validate year format
    try:
        year_int = int(year)
        if year_int < 2000 or year_int > 2100:  # Reasonable year range
            flash('Invalid year', 'error')
            return redirect(url_for('admin_tender.admin_tender_page'))
    except ValueError:
        flash('Invalid year format', 'error')
        return redirect(url_for('admin_tender.admin_tender_page'))
    
    file = request.files.get('file')
    if not file or file.filename == '':
        flash('File required', 'error')
        return redirect(url_for('admin_tender.admin_tender_page'))
    
    # Validate that file is PDF only
    if not file.filename.lower().endswith('.pdf'):
        flash('Only PDF files are allowed', 'error')
        return redirect(url_for('admin_tender.admin_tender_page'))
    
    # Optional: Check MIME type as additional validation
    if file.content_type != 'application/pdf':
        flash('Invalid file type. Please upload a valid PDF file', 'error')
        return redirect(url_for('admin_tender.admin_tender_page'))
    
    # Save file
    filename = secure_filename(file.filename)
    # Ensure filename ends with .pdf
    if not filename.lower().endswith('.pdf'):
        filename += '.pdf'
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{timestamp}_{filename}"
    filepath = UPLOAD_FOLDER / filename
    file.save(str(filepath))
    
    # Calculate expiration date for NEW badge
    new_expire_date = None
    if is_new:
        expire_dt = datetime.now() + timedelta(days=new_expire_days)
        new_expire_date = expire_dt.isoformat()
    
    # Insert to database with display_order = 0 (new uploads appear first)
    db = get_db()
    
    db.execute("""
        INSERT INTO tenders 
        (tender_no, nature_of_work, tender_date, tender_end_date, filename, is_new, new_expire_date, year, display_order, uploaded_at) 
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, 0, ?)
    """, (tender_no, nature_of_work, tender_date, tender_end_date, filename, is_new, new_expire_date, year, datetime.now().isoformat()))
    db.commit()
    
    flash('Tender added successfully', 'success')
    return redirect(url_for('admin_tender.admin_tender_page'))

# ============================================
# EDIT TENDER
# ============================================
@admin_tender_bp.route('/edit/<int:item_id>', methods=['POST'])
@login_required
def edit_tender(item_id):
    data = request.json
    nature_of_work = data.get('nature_of_work', '').strip()
    is_new = 1 if data.get('is_new') else 0
    
    # Fix: Convert float-like string to integer for days if provided
    new_expire_days_input = data.get('new_expire_days', 7)
    try:
        new_expire_days = int(float(new_expire_days_input))
    except (ValueError, TypeError):
        new_expire_days = 7
    
    if not nature_of_work:
        return jsonify({'error': 'Nature of work required'}), 400
    
    # Calculate new expiration date if is_new is set
    new_expire_date = None
    if is_new:
        expire_dt = datetime.now() + timedelta(days=new_expire_days)
        new_expire_date = expire_dt.isoformat()
    
    db = get_db()
    db.execute("""
        UPDATE tenders 
        SET nature_of_work = ?, is_new = ?, new_expire_date = ?
        WHERE id = ?
    """, (nature_of_work, is_new, new_expire_date, item_id))
    db.commit()
    
    return jsonify({'success': True})

# ============================================
# DELETE TENDER
# ============================================
@admin_tender_bp.route('/delete/<int:item_id>', methods=['POST'])
@login_required
def delete_tender(item_id):
    db = get_db()
    row = db.execute("SELECT filename FROM tenders WHERE id = ?", (item_id,)).fetchone()
    
    if row:
        # Delete file
        filepath = UPLOAD_FOLDER / row['filename']
        if filepath.exists():
            filepath.unlink()
        
        # Delete from database
        db.execute("DELETE FROM tenders WHERE id = ?", (item_id,))
        db.commit()
        return jsonify({'success': True})
    
    return jsonify({'error': 'Not found'}), 404

# ============================================
# REORDER TENDERS
# ============================================
@admin_tender_bp.route('/reorder', methods=['POST'])
@login_required
def reorder_tenders():
    data = request.json
    order = data.get('order', [])
    
    db = get_db()
    for idx, tender_id in enumerate(order):
        db.execute("UPDATE tenders SET display_order = ? WHERE id = ?", (idx + 1, tender_id))
    db.commit()
    
    return jsonify({'success': True})