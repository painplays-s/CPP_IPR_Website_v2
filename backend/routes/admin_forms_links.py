# backend/routes/admin_forms_links.py
from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from werkzeug.utils import secure_filename
from utils.decorators import login_required
from utils.helpers import format_date
from models.database import get_db, resequence
from config import FORMS_UPLOAD_DIR
import os

admin_forms_links_bp = Blueprint('admin_forms_links', __name__, url_prefix='/admin')

# Allowed file extensions for forms
ALLOWED_EXTENSIONS = {'.pdf'}

def allowed_file(filename):
    """Check if file has an allowed extension (PDF only)"""
    ext = os.path.splitext(filename)[1].lower()
    return ext in ALLOWED_EXTENSIONS

@admin_forms_links_bp.route('/forms-links')
@login_required
def admin_forms_links():
    conn = get_db()
    forms = conn.execute(
        "SELECT * FROM downloadable_forms ORDER BY sort_order ASC, uploaded_at DESC"
    ).fetchall()
    links = conn.execute(
        "SELECT * FROM links ORDER BY sort_order ASC, created_at DESC"
    ).fetchall()
    conn.close()
    return render_template(
        'admin_link.html',
        forms=forms,
        links=links,
        format_date=format_date
    )

@admin_forms_links_bp.route('/forms-links/upload-form', methods=['POST'])
@login_required
def upload_form():
    f = request.files.get('file')
    if not f:
        flash('File required', 'error')
        return redirect(url_for('admin_forms_links.admin_forms_links'))
    
    # Check file extension (PDF only)
    if not allowed_file(f.filename):
        flash('Only PDF files are allowed', 'error')
        return redirect(url_for('admin_forms_links.admin_forms_links'))

    fname = secure_filename(f.filename)
    final_name = f"{datetime.now():%Y%m%d%H%M%S}_{fname}"
    f.save(FORMS_UPLOAD_DIR / final_name)

    conn = get_db()
    next_order = conn.execute(
        "SELECT COALESCE(MAX(sort_order),0) FROM downloadable_forms"
    ).fetchone()[0] + 1

    conn.execute("""
        INSERT INTO downloadable_forms
        (name_en, name_hi, filename, uploaded_at, sort_order)
        VALUES (?, ?, ?, ?, ?)
    """, (
        request.form.get('name_en'),
        request.form.get('name_hi'),
        final_name,
        datetime.now().isoformat(timespec='seconds'),
        next_order,
    ))
    conn.commit()
    conn.close()

    flash('Form added successfully.', 'success')
    return redirect(url_for('admin_forms_links.admin_forms_links'))

@admin_forms_links_bp.route('/forms-links/add-link', methods=['POST'])
@login_required
def add_link():
    name_en = request.form.get('name_en', '').strip()
    name_hi = request.form.get('name_hi', '').strip()
    url = request.form.get('url', '').strip()

    if not name_en or not url:
        flash('Link name (English) and URL are required.', 'error')
        return redirect(url_for('admin_forms_links.admin_forms_links'))

    conn = get_db()
    next_order = conn.execute(
        "SELECT COALESCE(MAX(sort_order),0) FROM links"
    ).fetchone()[0] + 1

    conn.execute("""
        INSERT INTO links
        (name_en, name_hi, url, created_at, sort_order)
        VALUES (?, ?, ?, ?, ?)
    """, (
        name_en,
        name_hi,
        url,
        datetime.now().isoformat(timespec='seconds'),
        next_order,
    ))
    conn.commit()
    conn.close()

    flash('Link added successfully.', 'success')
    return redirect(url_for('admin_forms_links.admin_forms_links'))

@admin_forms_links_bp.route('/forms-links/edit-form/<int:item_id>', methods=['POST'])
@login_required
def edit_form(item_id):
    data = request.get_json(force=True)
    conn = get_db()
    conn.execute("""
        UPDATE downloadable_forms
        SET name_en=?, name_hi=?
        WHERE id=?
    """, (
        data.get('name_en', ''),
        data.get('name_hi', ''),
        item_id
    ))
    conn.commit()
    conn.close()
    return jsonify({'success': True})

@admin_forms_links_bp.route('/forms-links/edit-link/<int:item_id>', methods=['POST'])
@login_required
def edit_link(item_id):
    data = request.get_json(force=True)
    conn = get_db()
    conn.execute("""
        UPDATE links
        SET name_en=?, name_hi=?, url=?
        WHERE id=?
    """, (
        data.get('name_en', ''),
        data.get('name_hi', ''),
        data.get('url', ''),
        item_id
    ))
    conn.commit()
    conn.close()
    return jsonify({'success': True})

@admin_forms_links_bp.route('/forms-links/delete-form/<int:item_id>', methods=['POST'])
@login_required
def delete_form(item_id):
    conn = get_db()
    row = conn.execute(
        "SELECT filename FROM downloadable_forms WHERE id=?", (item_id,)
    ).fetchone()
    conn.execute("DELETE FROM downloadable_forms WHERE id=?", (item_id,))
    conn.commit()
    conn.close()

    try:
        (FORMS_UPLOAD_DIR / row["filename"]).unlink(missing_ok=True)
    except Exception:
        pass

    resequence("downloadable_forms")
    return jsonify({'success': True})

@admin_forms_links_bp.route('/forms-links/delete-link/<int:item_id>', methods=['POST'])
@login_required
def delete_link(item_id):
    conn = get_db()
    conn.execute("DELETE FROM links WHERE id=?", (item_id,))
    conn.commit()
    conn.close()

    resequence("links")
    return jsonify({'success': True})

@admin_forms_links_bp.route('/forms-links/reorder-forms', methods=['POST'])
@login_required
def reorder_forms():
    order = request.get_json(force=True).get('order', [])
    conn = get_db()
    for idx, oid in enumerate(order, start=1):
        conn.execute("UPDATE downloadable_forms SET sort_order=? WHERE id=?", (idx, oid))
    conn.commit()
    conn.close()
    return jsonify({'success': True})

@admin_forms_links_bp.route('/forms-links/reorder-links', methods=['POST'])
@login_required
def reorder_links():
    order = request.get_json(force=True).get('order', [])
    conn = get_db()
    for idx, oid in enumerate(order, start=1):
        conn.execute("UPDATE links SET sort_order=? WHERE id=?", (idx, oid))
    conn.commit()
    conn.close()
    return jsonify({'success': True})