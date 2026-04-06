# backend/routes/admin_carousal.py
import json
from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from werkzeug.utils import secure_filename
from utils.decorators import login_required
from utils.helpers import format_date
from models.database import get_db, resequence
from config import CAROUSAL_UPLOAD_DIR

admin_carousal_bp = Blueprint('admin_carousal', __name__, url_prefix='/admin/carousal')

@admin_carousal_bp.route('')
@login_required
def admin_carousal():
    """List and manage carousel images"""
    conn = get_db()
    rows = conn.execute(
        "SELECT * FROM home_carousal ORDER BY sort_order ASC, uploaded_at DESC"
    ).fetchall()
    conn.close()
    return render_template('admin_home_carousal.html', items=rows, format_date=format_date)

@admin_carousal_bp.route('/upload', methods=['POST'])
@login_required
def upload_carousal():
    """Upload new carousel images"""
    files = request.files.getlist('images')
    meta = json.loads(request.form.get('meta', '[]'))

    meta_map = {m['filename']: m for m in meta if 'filename' in m}

    conn = get_db()
    try:
        next_order = conn.execute(
            "SELECT COALESCE(MAX(sort_order),0) FROM home_carousal"
        ).fetchone()[0] + 1

        uploaded_count = 0
        for f in files:
            fname = secure_filename(f.filename)
            if not fname:
                continue

            final_name = f"{datetime.now():%Y%m%d%H%M%S}_{fname}"
            f.save(CAROUSAL_UPLOAD_DIR / final_name)

            m = meta_map.get(f.filename, {})
            conn.execute("""
                INSERT INTO home_carousal
                (filename, caption_en, caption_hi, href, uploaded_at, sort_order)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                final_name,
                m.get('caption_en', ''),
                m.get('caption_hi', ''),
                m.get('href', ''),
                datetime.now().isoformat(timespec='seconds'),
                next_order,
            ))
            next_order += 1
            uploaded_count += 1
        conn.commit()
        
        return jsonify({
            'success': True, 
            'message': f'{uploaded_count} image(s) uploaded successfully!'
        })
    except Exception as e:
        return jsonify({'success': False, 'message': f'Upload failed: {str(e)}'}), 500
    finally:
        conn.close()

@admin_carousal_bp.route('/delete/<int:item_id>', methods=['POST'])
@login_required
def delete_carousal(item_id):
    """Delete a carousel image"""
    conn = get_db()
    try:
        row = conn.execute("SELECT filename FROM home_carousal WHERE id=?", (item_id,)).fetchone()
        conn.execute("DELETE FROM home_carousal WHERE id=?", (item_id,))
        conn.commit()

        try:
            (CAROUSAL_UPLOAD_DIR / row["filename"]).unlink(missing_ok=True)
        except Exception:
            pass

        resequence("home_carousal")
        return jsonify({'success': True, 'message': 'Image deleted successfully!'})
    except Exception as e:
        return jsonify({'success': False, 'message': f'Delete failed: {str(e)}'}), 500
    finally:
        conn.close()

@admin_carousal_bp.route('/edit/<int:item_id>', methods=['POST'])
@login_required
def edit_carousal(item_id):
    """Edit carousel image captions and link"""
    data = request.get_json(force=True)
    conn = get_db()
    try:
        conn.execute("""
            UPDATE home_carousal SET caption_en=?, caption_hi=?, href=?
            WHERE id=?
        """, (
            data.get('caption_en', ''),
            data.get('caption_hi', ''),
            data.get('href', ''),
            item_id
        ))
        conn.commit()
        return jsonify({'success': True, 'message': 'Changes saved successfully!'})
    except Exception as e:
        return jsonify({'success': False, 'message': f'Save failed: {str(e)}'}), 500
    finally:
        conn.close()

@admin_carousal_bp.route('/reorder', methods=['POST'])
@login_required
def reorder_carousal():
    """Reorder carousel images"""
    order = request.get_json(force=True).get('order', [])
    conn = get_db()
    try:
        for idx, oid in enumerate(order, start=1):
            conn.execute("UPDATE home_carousal SET sort_order=? WHERE id=?", (idx, oid))
        conn.commit()
        return jsonify({'success': True, 'message': 'Order saved successfully!'})
    except Exception as e:
        return jsonify({'success': False, 'message': f'Failed to save order: {str(e)}'}), 500
    finally:
        conn.close()