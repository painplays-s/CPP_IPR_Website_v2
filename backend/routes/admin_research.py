# backend/routes/admin_research.py
import json
from datetime import datetime
from flask import Blueprint, render_template, request, jsonify
from werkzeug.utils import secure_filename
from utils.decorators import login_required
from utils.helpers import format_date
from models.database import get_db, resequence
from config import RESEARCH_HIGHLIGHT_DIR
import os

admin_research = Blueprint('admin_research', __name__, url_prefix='/admin')

# Allowed image extensions
ALLOWED_EXTENSIONS = {'.jpg', '.jpeg', '.png'}

def allowed_file(filename):
    """Check if file has an allowed image extension"""
    ext = os.path.splitext(filename)[1].lower()
    return ext in ALLOWED_EXTENSIONS

@admin_research.route('/research-highlight')
@login_required
def admin_research_highlight():
    conn = get_db()
    rows = conn.execute(
        "SELECT * FROM research_highlight ORDER BY sort_order ASC, uploaded_at DESC"
    ).fetchall()
    conn.close()
    return render_template(
        'admin_research_highlight.html', 
        items=rows, 
        format_date=format_date
    )

@admin_research.route('/research-highlight/upload', methods=['POST'])
@login_required
def upload_research_highlight():
    files = request.files.getlist('images')
    meta = json.loads(request.form.get('meta', '[]'))

    meta_map = {m['filename']: m for m in meta if 'filename' in m}

    conn = get_db()
    try:
        next_order = conn.execute(
            "SELECT COALESCE(MAX(sort_order),0) FROM research_highlight"
        ).fetchone()[0] + 1

        uploaded_count = 0
        skipped_count = 0
        
        for f in files:
            # Check file extension (image only)
            if not allowed_file(f.filename):
                skipped_count += 1
                continue
                
            fname = secure_filename(f.filename)
            if not fname:
                skipped_count += 1
                continue

            final_name = f"{datetime.now():%Y%m%d%H%M%S}_{fname}"
            f.save(RESEARCH_HIGHLIGHT_DIR / final_name)

            m = meta_map.get(f.filename, {})
            conn.execute("""
                INSERT INTO research_highlight
                (filename, link, uploaded_at, sort_order)
                VALUES (?, ?, ?, ?)
            """, (
                final_name,
                m.get('link', ''),
                datetime.now().isoformat(timespec='seconds'),
                next_order,
            ))
            next_order += 1
            uploaded_count += 1
            
        conn.commit()
        
        message = f'{uploaded_count} image(s) uploaded successfully!'
        if skipped_count > 0:
            message += f' {skipped_count} file(s) were skipped (invalid format).'
            
        return jsonify({'success': True, 'message': message})
    except Exception as e:
        return jsonify({'success': False, 'message': f'Upload failed: {str(e)}'}), 500
    finally:
        conn.close()

@admin_research.route('/research-highlight/edit/<int:item_id>', methods=['POST'])
@login_required
def edit_research_highlight(item_id):
    data = request.get_json(force=True)
    conn = get_db()
    try:
        conn.execute("""
            UPDATE research_highlight SET link=?
            WHERE id=?
        """, (data.get('link', ''), item_id))
        conn.commit()
        return jsonify({'success': True, 'message': 'Changes saved successfully!'})
    except Exception as e:
        return jsonify({'success': False, 'message': f'Save failed: {str(e)}'}), 500
    finally:
        conn.close()

@admin_research.route('/research-highlight/delete/<int:item_id>', methods=['POST'])
@login_required
def delete_research_highlight(item_id):
    conn = get_db()
    try:
        row = conn.execute("SELECT filename FROM research_highlight WHERE id=?", (item_id,)).fetchone()
        conn.execute("DELETE FROM research_highlight WHERE id=?", (item_id,))
        conn.commit()

        try:
            (RESEARCH_HIGHLIGHT_DIR / row["filename"]).unlink(missing_ok=True)
        except Exception:
            pass

        resequence("research_highlight")
        return jsonify({'success': True, 'message': 'Image deleted successfully!'})
    except Exception as e:
        return jsonify({'success': False, 'message': f'Delete failed: {str(e)}'}), 500
    finally:
        conn.close()

@admin_research.route('/research-highlight/reorder', methods=['POST'])
@login_required
def reorder_research_highlight():
    order = request.get_json(force=True).get('order', [])
    conn = get_db()
    try:
        for idx, oid in enumerate(order, start=1):
            conn.execute("UPDATE research_highlight SET sort_order=? WHERE id=?", (idx, oid))
        conn.commit()
        return jsonify({'success': True, 'message': 'Order saved successfully!'})
    except Exception as e:
        return jsonify({'success': False, 'message': f'Failed to save order: {str(e)}'}), 500
    finally:
        conn.close()