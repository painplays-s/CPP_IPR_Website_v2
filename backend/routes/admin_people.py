# backend/routes/admin_people.py
from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from werkzeug.utils import secure_filename
from utils.decorators import login_required
from utils.helpers import format_date
from models.database import get_db, resequence
from config import PEOPLE_UPLOAD_DIR
import os

admin_people_bp = Blueprint('admin_people', __name__, url_prefix='/admin')

# Allowed image extensions
ALLOWED_EXTENSIONS = {'.jpg', '.jpeg', '.png'}

def allowed_file(filename):
    """Check if file has an allowed extension"""
    ext = os.path.splitext(filename)[1].lower()
    return ext in ALLOWED_EXTENSIONS

@admin_people_bp.route('/people')
@login_required
def admin_people():
    conn = get_db()
    director = conn.execute("SELECT * FROM people_director LIMIT 1").fetchone()
    staff = conn.execute(
        "SELECT * FROM people_staff ORDER BY sort_order ASC, created_at ASC"
    ).fetchall()
    faculty = conn.execute(
        "SELECT * FROM people_faculty ORDER BY sort_order ASC, created_at ASC"
    ).fetchall()
    scholars = conn.execute(
        "SELECT * FROM people_scholars ORDER BY sort_order ASC, created_at ASC"
    ).fetchall()
    conn.close()
    return render_template(
        'admin_people.html',
        director=director,
        staff=staff,
        faculty=faculty,
        scholars=scholars,
        format_date=format_date
    )

@admin_people_bp.route('/people/add-director', methods=['POST'])
@login_required
def add_director():
    conn = get_db()
    existing = conn.execute("SELECT id FROM people_director LIMIT 1").fetchone()
    if existing:
        conn.close()
        flash('Director already exists. Please delete the existing one first.', 'error')
        return redirect(url_for('admin_people.admin_people'))

    f = request.files.get('photo')
    if not f:
        conn.close()
        flash('Photo required', 'error')
        return redirect(url_for('admin_people.admin_people'))
    
    # Check file extension
    if not allowed_file(f.filename):
        conn.close()
        flash('Only JPEG, JPG, and PNG files are allowed', 'error')
        return redirect(url_for('admin_people.admin_people'))

    fname = secure_filename(f.filename)
    final_name = f"{datetime.now():%Y%m%d%H%M%S}_{fname}"
    f.save(PEOPLE_UPLOAD_DIR / final_name)

    conn.execute("""
        INSERT INTO people_director
        (photo, name_en, name_hi, email, created_at)
        VALUES (?, ?, ?, ?, ?)
    """, (
        final_name,
        request.form.get('name_en'),
        request.form.get('name_hi'),
        request.form.get('email'),
        datetime.now().isoformat(timespec='seconds'),
    ))
    conn.commit()
    conn.close()

    flash('Director added successfully.', 'success')
    return redirect(url_for('admin_people.admin_people'))

@admin_people_bp.route('/people/add-staff', methods=['POST'])
@login_required
def add_staff():
    f = request.files.get('photo')
    if not f:
        flash('Photo required', 'error')
        return redirect(url_for('admin_people.admin_people'))
    
    # Check file extension
    if not allowed_file(f.filename):
        flash('Only JPEG, JPG, and PNG files are allowed', 'error')
        return redirect(url_for('admin_people.admin_people'))

    fname = secure_filename(f.filename)
    final_name = f"{datetime.now():%Y%m%d%H%M%S}_{fname}"
    f.save(PEOPLE_UPLOAD_DIR / final_name)

    conn = get_db()
    next_order = conn.execute(
        "SELECT COALESCE(MAX(sort_order),0) FROM people_staff"
    ).fetchone()[0] + 1

    conn.execute("""
        INSERT INTO people_staff
        (photo, name_en, name_hi, designation_en, designation_hi, 
         email, extn_no, sub_category, created_at, sort_order)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        final_name,
        request.form.get('name_en'),
        request.form.get('name_hi'),
        request.form.get('designation_en'),
        request.form.get('designation_hi'),
        request.form.get('email'),
        request.form.get('extn_no'),
        request.form.get('sub_category'),
        datetime.now().isoformat(timespec='seconds'),
        next_order,
    ))
    conn.commit()
    conn.close()

    flash('Staff member added successfully.', 'success')
    return redirect(url_for('admin_people.admin_people'))

@admin_people_bp.route('/people/add-faculty', methods=['POST'])
@login_required
def add_faculty():
    f = request.files.get('photo')
    if not f:
        flash('Photo required', 'error')
        return redirect(url_for('admin_people.admin_people'))
    
    # Check file extension
    if not allowed_file(f.filename):
        flash('Only JPEG, JPG, and PNG files are allowed', 'error')
        return redirect(url_for('admin_people.admin_people'))

    fname = secure_filename(f.filename)
    final_name = f"{datetime.now():%Y%m%d%H%M%S}_{fname}"
    f.save(PEOPLE_UPLOAD_DIR / final_name)

    conn = get_db()
    next_order = conn.execute(
        "SELECT COALESCE(MAX(sort_order),0) FROM people_faculty"
    ).fetchone()[0] + 1

    conn.execute("""
        INSERT INTO people_faculty
        (photo, name_en, name_hi, designation_en, designation_hi,
         location_en, location_hi, email, extn_no, sub_category, created_at, sort_order)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        final_name,
        request.form.get('name_en'),
        request.form.get('name_hi'),
        request.form.get('designation_en'),
        request.form.get('designation_hi'),
        request.form.get('location_en'),
        request.form.get('location_hi'),
        request.form.get('email'),
        request.form.get('extn_no'),
        request.form.get('sub_category'),
        datetime.now().isoformat(timespec='seconds'),
        next_order,
    ))
    conn.commit()
    conn.close()

    flash('Faculty member added successfully.', 'success')
    return redirect(url_for('admin_people.admin_people'))

@admin_people_bp.route('/people/add-scholar', methods=['POST'])
@login_required
def add_scholar():
    f = request.files.get('photo')
    if not f:
        flash('Photo required', 'error')
        return redirect(url_for('admin_people.admin_people'))
    
    # Check file extension
    if not allowed_file(f.filename):
        flash('Only JPEG, JPG, and PNG files are allowed', 'error')
        return redirect(url_for('admin_people.admin_people'))

    fname = secure_filename(f.filename)
    final_name = f"{datetime.now():%Y%m%d%H%M%S}_{fname}"
    f.save(PEOPLE_UPLOAD_DIR / final_name)

    conn = get_db()
    next_order = conn.execute(
        "SELECT COALESCE(MAX(sort_order),0) FROM people_scholars"
    ).fetchone()[0] + 1

    conn.execute("""
        INSERT INTO people_scholars
        (photo, name_en, name_hi, position, lab_en, lab_hi,
         email, extn_no, created_at, sort_order)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        final_name,
        request.form.get('name_en'),
        request.form.get('name_hi'),
        request.form.get('position'),
        request.form.get('lab_en'),
        request.form.get('lab_hi'),
        request.form.get('email'),
        request.form.get('extn_no'),
        datetime.now().isoformat(timespec='seconds'),
        next_order,
    ))
    conn.commit()
    conn.close()

    flash('Scholar added successfully.', 'success')
    return redirect(url_for('admin_people.admin_people'))

@admin_people_bp.route('/people/edit-director/<int:item_id>', methods=['POST'])
@login_required
def edit_director(item_id):
    data = request.get_json(force=True)
    conn = get_db()
    conn.execute("""
        UPDATE people_director
        SET name_en=?, name_hi=?, email=?
        WHERE id=?
    """, (
        data.get('name_en'),
        data.get('name_hi'),
        data.get('email'),
        item_id
    ))
    conn.commit()
    conn.close()
    return jsonify({'success': True})

@admin_people_bp.route('/people/edit-staff/<int:item_id>', methods=['POST'])
@login_required
def edit_staff(item_id):
    data = request.get_json(force=True)
    conn = get_db()
    conn.execute("""
        UPDATE people_staff
        SET name_en=?, name_hi=?, designation_en=?, designation_hi=?,
            email=?, extn_no=?, sub_category=?
        WHERE id=?
    """, (
        data.get('name_en'),
        data.get('name_hi'),
        data.get('designation_en'),
        data.get('designation_hi'),
        data.get('email'),
        data.get('extn_no'),
        data.get('sub_category'),
        item_id
    ))
    conn.commit()
    conn.close()
    return jsonify({'success': True})

@admin_people_bp.route('/people/edit-faculty/<int:item_id>', methods=['POST'])
@login_required
def edit_faculty(item_id):
    data = request.get_json(force=True)
    conn = get_db()
    conn.execute("""
        UPDATE people_faculty
        SET name_en=?, name_hi=?, designation_en=?, designation_hi=?,
            location_en=?, location_hi=?, email=?, extn_no=?, sub_category=?
        WHERE id=?
    """, (
        data.get('name_en'),
        data.get('name_hi'),
        data.get('designation_en'),
        data.get('designation_hi'),
        data.get('location_en'),
        data.get('location_hi'),
        data.get('email'),
        data.get('extn_no'),
        data.get('sub_category'),
        item_id
    ))
    conn.commit()
    conn.close()
    return jsonify({'success': True})

@admin_people_bp.route('/people/edit-scholar/<int:item_id>', methods=['POST'])
@login_required
def edit_scholar(item_id):
    data = request.get_json(force=True)
    conn = get_db()
    conn.execute("""
        UPDATE people_scholars
        SET name_en=?, name_hi=?, position=?, lab_en=?, lab_hi=?,
            email=?, extn_no=?
        WHERE id=?
    """, (
        data.get('name_en'),
        data.get('name_hi'),
        data.get('position'),
        data.get('lab_en'),
        data.get('lab_hi'),
        data.get('email'),
        data.get('extn_no'),
        item_id
    ))
    conn.commit()
    conn.close()
    return jsonify({'success': True})

@admin_people_bp.route('/people/delete-director/<int:item_id>', methods=['POST'])
@login_required
def delete_director(item_id):
    conn = get_db()
    row = conn.execute("SELECT photo FROM people_director WHERE id=?", (item_id,)).fetchone()
    conn.execute("DELETE FROM people_director WHERE id=?", (item_id,))
    conn.commit()
    conn.close()

    try:
        (PEOPLE_UPLOAD_DIR / row["photo"]).unlink(missing_ok=True)
    except Exception:
        pass

    return jsonify({'success': True})

@admin_people_bp.route('/people/delete-staff/<int:item_id>', methods=['POST'])
@login_required
def delete_staff(item_id):
    conn = get_db()
    row = conn.execute("SELECT photo FROM people_staff WHERE id=?", (item_id,)).fetchone()
    conn.execute("DELETE FROM people_staff WHERE id=?", (item_id,))
    conn.commit()
    conn.close()

    try:
        (PEOPLE_UPLOAD_DIR / row["photo"]).unlink(missing_ok=True)
    except Exception:
        pass

    resequence("people_staff")
    return jsonify({'success': True})

@admin_people_bp.route('/people/delete-faculty/<int:item_id>', methods=['POST'])
@login_required
def delete_faculty(item_id):
    conn = get_db()
    row = conn.execute("SELECT photo FROM people_faculty WHERE id=?", (item_id,)).fetchone()
    conn.execute("DELETE FROM people_faculty WHERE id=?", (item_id,))
    conn.commit()
    conn.close()

    try:
        (PEOPLE_UPLOAD_DIR / row["photo"]).unlink(missing_ok=True)
    except Exception:
        pass

    resequence("people_faculty")
    return jsonify({'success': True})

@admin_people_bp.route('/people/delete-scholar/<int:item_id>', methods=['POST'])
@login_required
def delete_scholar(item_id):
    conn = get_db()
    row = conn.execute("SELECT photo FROM people_scholars WHERE id=?", (item_id,)).fetchone()
    conn.execute("DELETE FROM people_scholars WHERE id=?", (item_id,))
    conn.commit()
    conn.close()

    try:
        (PEOPLE_UPLOAD_DIR / row["photo"]).unlink(missing_ok=True)
    except Exception:
        pass

    resequence("people_scholars")
    return jsonify({'success': True})

@admin_people_bp.route('/people/reorder-staff', methods=['POST'])
@login_required
def reorder_staff():
    order = request.get_json(force=True).get('order', [])
    conn = get_db()
    for idx, oid in enumerate(order, start=1):
        conn.execute("UPDATE people_staff SET sort_order=? WHERE id=?", (idx, oid))
    conn.commit()
    conn.close()
    return jsonify({'success': True})

@admin_people_bp.route('/people/reorder-faculty', methods=['POST'])
@login_required
def reorder_faculty():
    order = request.get_json(force=True).get('order', [])
    conn = get_db()
    for idx, oid in enumerate(order, start=1):
        conn.execute("UPDATE people_faculty SET sort_order=? WHERE id=?", (idx, oid))
    conn.commit()
    conn.close()
    return jsonify({'success': True})

@admin_people_bp.route('/people/reorder-scholars', methods=['POST'])
@login_required
def reorder_scholars():
    order = request.get_json(force=True).get('order', [])
    conn = get_db()
    for idx, oid in enumerate(order, start=1):
        conn.execute("UPDATE people_scholars SET sort_order=? WHERE id=?", (idx, oid))
    conn.commit()
    conn.close()
    return jsonify({'success': True})