# backend/routes/public_api.py
from flask import Blueprint, jsonify
from models.database import get_db
from datetime import datetime

public_api = Blueprint('public_api', __name__)

@public_api.route("/api/home-carousal")
def api_home_carousal():
    conn = get_db()
    rows = conn.execute(
        "SELECT * FROM home_carousal ORDER BY sort_order ASC, uploaded_at DESC"
    ).fetchall()
    conn.close()

    return jsonify([{
        "id": r["id"],
        "src": f"/assets/images/home_carousal/{r['filename']}",
        "caption_en": r["caption_en"] or "",
        "caption_hi": r["caption_hi"] or "",
        "href": r["href"] or "",
    } for r in rows])

@public_api.route("/api/current-notice")
def api_current_notice():
    # Auto-remove expired NEW badges
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
    
    rows = conn.execute(
        "SELECT * FROM current_notice ORDER BY sort_order ASC, uploaded_at DESC"
    ).fetchall()
    conn.close()

    return jsonify([{
        "id": r["id"],
        "type": r["type"],
        "description_en": r["description_en"],
        "description_hi": r["description_hi"] or "",
        "filename": r["filename"],
        "is_new": bool(r["is_new"]),
    } for r in rows])

@public_api.route("/api/research-highlight")
def api_research_highlight():
    conn = get_db()
    rows = conn.execute(
        "SELECT * FROM research_highlight ORDER BY sort_order ASC, uploaded_at DESC"
    ).fetchall()
    conn.close()

    return jsonify([{
        "id": r["id"],
        "link": r["link"],
        "image_path": f"images/research_highlight/{r['filename']}",
    } for r in rows])

@public_api.route("/api/recent-publication")
def api_recent_publication():
    conn = get_db()
    rows = conn.execute(
        "SELECT * FROM recent_publication ORDER BY sort_order ASC, date DESC"
    ).fetchall()
    conn.close()

    return jsonify([{
        "id": r["id"],
        "title_en": r["title_en"],
        "title_hi": r["title_hi"] or "",
        "url": r["url"],
        "date": r["date"],
    } for r in rows])

@public_api.route("/api/downloadable-forms")
def api_downloadable_forms():
    conn = get_db()
    rows = conn.execute(
        "SELECT * FROM downloadable_forms ORDER BY sort_order ASC, uploaded_at DESC"
    ).fetchall()
    conn.close()

    return jsonify([{
        "id": r["id"],
        "name_en": r["name_en"],
        "name_hi": r["name_hi"],
        "filename": r["filename"],
        "file_url": f"/assets/files/forms/{r['filename']}",
    } for r in rows])

@public_api.route("/api/links")
def api_links():
    conn = get_db()
    rows = conn.execute(
        "SELECT * FROM links ORDER BY sort_order ASC, created_at DESC"
    ).fetchall()
    conn.close()

    return jsonify([{
        "id": r["id"],
        "name_en": r["name_en"],
        "name_hi": r["name_hi"],
        "url": r["url"],
    } for r in rows])

@public_api.route("/api/people/director")
def api_people_director():
    conn = get_db()
    director = conn.execute("SELECT * FROM people_director LIMIT 1").fetchone()
    conn.close()
    
    if director:
        return jsonify({
            "id": director["id"],
            "photo": director["photo"],
            "name_en": director["name_en"],
            "name_hi": director["name_hi"],
            "email": director["email"],
        })
    return jsonify(None)

@public_api.route("/api/people/staff")
def api_people_staff():
    conn = get_db()
    rows = conn.execute(
        "SELECT * FROM people_staff ORDER BY sort_order ASC, created_at ASC"
    ).fetchall()
    conn.close()
    
    return jsonify([{
        "id": r["id"],
        "photo": r["photo"],
        "name_en": r["name_en"],
        "name_hi": r["name_hi"],
        "designation_en": r["designation_en"],
        "designation_hi": r["designation_hi"],
        "email": r["email"],
        "extn_no": r["extn_no"],
        "sub_category": r["sub_category"],
    } for r in rows])

@public_api.route("/api/people/faculty")
def api_people_faculty():
    conn = get_db()
    rows = conn.execute(
        "SELECT * FROM people_faculty ORDER BY sort_order ASC, created_at ASC"
    ).fetchall()
    conn.close()
    
    return jsonify([{
        "id": r["id"],
        "photo": r["photo"],
        "name_en": r["name_en"],
        "name_hi": r["name_hi"],
        "designation_en": r["designation_en"],
        "designation_hi": r["designation_hi"],
        "location_en": r["location_en"],
        "location_hi": r["location_hi"],
        "email": r["email"],
        "extn_no": r["extn_no"],
        "sub_category": r["sub_category"],
    } for r in rows])

@public_api.route("/api/people/scholars")
def api_people_scholars():
    conn = get_db()
    rows = conn.execute(
        "SELECT * FROM people_scholars ORDER BY sort_order ASC, created_at ASC"
    ).fetchall()
    conn.close()
    
    return jsonify([{
        "id": r["id"],
        "photo": r["photo"],
        "name_en": r["name_en"],
        "name_hi": r["name_hi"],
        "position": r["position"],
        "lab_en": r["lab_en"],
        "lab_hi": r["lab_hi"],
        "email": r["email"],
        "extn_no": r["extn_no"],
    } for r in rows])

# ============================================
# TENDER PUBLIC APIs
# ============================================

@public_api.route('/api/tenders/years')
def api_tender_years():
    """Get all available tender years"""
    # Auto-remove expired NEW badges
    conn = get_db()
    now = datetime.now().isoformat()
    conn.execute("""
        UPDATE tenders 
        SET is_new = 0 
        WHERE is_new = 1 
        AND new_expire_date IS NOT NULL 
        AND new_expire_date < ?
    """, (now,))
    conn.commit()
    
    rows = conn.execute("SELECT DISTINCT year FROM tenders ORDER BY year DESC").fetchall()
    conn.close()
    
    years = [r['year'] for r in rows]
    return jsonify({'years': years})

@public_api.route('/api/tenders/year/<int:year>')
def api_tenders_by_year(year):
    """Get all tenders for a specific year"""
    # Auto-remove expired NEW badges
    conn = get_db()
    now = datetime.now().isoformat()
    conn.execute("""
        UPDATE tenders 
        SET is_new = 0 
        WHERE is_new = 1 
        AND new_expire_date IS NOT NULL 
        AND new_expire_date < ?
    """, (now,))
    conn.commit()
    
    rows = conn.execute("""
        SELECT id, tender_no, nature_of_work, tender_date, tender_end_date, 
               filename, is_new, year, uploaded_at, display_order
        FROM tenders 
        WHERE year = ? 
        ORDER BY display_order ASC, uploaded_at DESC
    """, (year,)).fetchall()
    conn.close()
    
    tenders = [{
        'id': r['id'],
        'tender_no': r['tender_no'],
        'nature_of_work': r['nature_of_work'],
        'tender_date': r['tender_date'],
        'tender_end_date': r['tender_end_date'],
        'filename': r['filename'],
        'is_new': bool(r['is_new']),
        'year': r['year']
    } for r in rows]
    
    return jsonify({'tenders': tenders})

# ============================================
# ADVERTISEMENT PUBLIC APIs
# ============================================

@public_api.route('/api/advertisements/years')
def api_advertisement_years():
    """Get all available advertisement years"""
    # Auto-remove expired NEW badges
    conn = get_db()
    now = datetime.now().isoformat()
    conn.execute("""
        UPDATE advertisements 
        SET is_new = 0 
        WHERE is_new = 1 
        AND new_expire_date IS NOT NULL 
        AND new_expire_date < ?
    """, (now,))
    conn.commit()
    
    rows = conn.execute("SELECT DISTINCT year FROM advertisements ORDER BY year DESC").fetchall()
    conn.close()
    
    years = [r['year'] for r in rows]
    return jsonify({'years': years})

@public_api.route('/api/advertisements/year/<int:year>')
def api_advertisements_by_year(year):
    """Get all advertisements for a specific year"""
    # Auto-remove expired NEW badges
    conn = get_db()
    now = datetime.now().isoformat()
    conn.execute("""
        UPDATE advertisements 
        SET is_new = 0 
        WHERE is_new = 1 
        AND new_expire_date IS NOT NULL 
        AND new_expire_date < ?
    """, (now,))
    conn.commit()
    
    rows = conn.execute("""
        SELECT id, advertisement_no, description, advertisement_date, 
               advertisement_end_date, filename, is_new, year, uploaded_at, display_order
        FROM advertisements 
        WHERE year = ? 
        ORDER BY display_order ASC, uploaded_at DESC
    """, (year,)).fetchall()
    conn.close()
    
    advertisements = [{
        'id': r['id'],
        'advertisement_no': r['advertisement_no'],
        'description': r['description'],
        'advertisement_date': r['advertisement_date'],
        'advertisement_end_date': r['advertisement_end_date'],
        'filename': r['filename'],
        'is_new': bool(r['is_new']),
        'year': r['year']
    } for r in rows]
    
    return jsonify({'advertisements': advertisements})
