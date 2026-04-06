# backend/models/database.py
import sqlite3
from config import DB_PATH

def get_db():
    """Get database connection with Row factory"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def ensure_db_and_migrations():
    """Create tables and run migrations"""
    conn = get_db()
    try:
        # ---------- HOME CAROUSAL ----------
        conn.execute("""
            CREATE TABLE IF NOT EXISTS home_carousal (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                filename TEXT NOT NULL,
                caption_en TEXT,
                caption_hi TEXT,
                href TEXT,
                uploaded_at TEXT NOT NULL,
                sort_order INTEGER DEFAULT 0
            )
        """)

        cols = [c["name"] for c in conn.execute("PRAGMA table_info(home_carousal)")]
        if "sort_order" not in cols:
            conn.execute("ALTER TABLE home_carousal ADD COLUMN sort_order INTEGER DEFAULT 0")

        # ---------- CURRENT NOTICE ----------
        conn.execute("""
            CREATE TABLE IF NOT EXISTS current_notice (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                type TEXT NOT NULL,
                description_en TEXT NOT NULL,
                description_hi TEXT,
                filename TEXT NOT NULL,
                is_new INTEGER DEFAULT 0,
                uploaded_at TEXT NOT NULL,
                sort_order INTEGER DEFAULT 0
            )
        """)

        cols = [c["name"] for c in conn.execute("PRAGMA table_info(current_notice)")]
        if "sort_order" not in cols:
            conn.execute("ALTER TABLE current_notice ADD COLUMN sort_order INTEGER DEFAULT 0")

        # ---------- RESEARCH HIGHLIGHT ----------
        table_exists = conn.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='research_highlight'
        """).fetchone()

        if table_exists:
            cols = [c["name"] for c in conn.execute("PRAGMA table_info(research_highlight)")]
            has_old_structure = "image_path" in cols and "updated_at" in cols
            has_new_structure = "filename" in cols and "sort_order" in cols

            if has_old_structure and not has_new_structure:
                print("⚙️  Migrating research_highlight table to multi-image support...")
                conn.execute("DROP TABLE IF EXISTS research_highlight")
                conn.execute("""
                    CREATE TABLE research_highlight (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        filename TEXT NOT NULL,
                        link TEXT NOT NULL,
                        uploaded_at TEXT NOT NULL,
                        sort_order INTEGER DEFAULT 0
                    )
                """)
                print("✅ Migration complete!")
            elif not has_new_structure:
                conn.execute("DROP TABLE IF EXISTS research_highlight")
                conn.execute("""
                    CREATE TABLE research_highlight (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        filename TEXT NOT NULL,
                        link TEXT NOT NULL,
                        uploaded_at TEXT NOT NULL,
                        sort_order INTEGER DEFAULT 0
                    )
                """)
        else:
            conn.execute("""
                CREATE TABLE research_highlight (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    filename TEXT NOT NULL,
                    link TEXT NOT NULL,
                    uploaded_at TEXT NOT NULL,
                    sort_order INTEGER DEFAULT 0
                )
            """)

        cols = [c["name"] for c in conn.execute("PRAGMA table_info(research_highlight)")]
        if "sort_order" not in cols:
            conn.execute("ALTER TABLE research_highlight ADD COLUMN sort_order INTEGER DEFAULT 0")

        # ---------- RECENT PUBLICATION ----------
        conn.execute("""
            CREATE TABLE IF NOT EXISTS recent_publication (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title_en TEXT NOT NULL,
                title_hi TEXT,
                url TEXT NOT NULL,
                date TEXT NOT NULL,
                uploaded_at TEXT NOT NULL,
                sort_order INTEGER DEFAULT 0
            )
        """)

        cols = [c["name"] for c in conn.execute("PRAGMA table_info(recent_publication)")]
        if "sort_order" not in cols:
            conn.execute("ALTER TABLE recent_publication ADD COLUMN sort_order INTEGER DEFAULT 0")

        # ---------- DOWNLOADABLE FORMS ----------
        conn.execute("""
            CREATE TABLE IF NOT EXISTS downloadable_forms (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name_en TEXT NOT NULL,
                name_hi TEXT NOT NULL,
                filename TEXT NOT NULL,
                uploaded_at TEXT NOT NULL,
                sort_order INTEGER DEFAULT 0
            )
        """)

        cols = [c["name"] for c in conn.execute("PRAGMA table_info(downloadable_forms)")]
        if "sort_order" not in cols:
            conn.execute("ALTER TABLE downloadable_forms ADD COLUMN sort_order INTEGER DEFAULT 0")

        # ---------- LINKS ----------
        conn.execute("""
            CREATE TABLE IF NOT EXISTS links (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name_en TEXT NOT NULL,
                name_hi TEXT NOT NULL,
                url TEXT NOT NULL,
                created_at TEXT NOT NULL,
                sort_order INTEGER DEFAULT 0
            )
        """)

        cols = [c["name"] for c in conn.execute("PRAGMA table_info(links)")]
        if "sort_order" not in cols:
            conn.execute("ALTER TABLE links ADD COLUMN sort_order INTEGER DEFAULT 0")

        # ---------- PEOPLE TABLES ----------
        # Center Director
        conn.execute("""
            CREATE TABLE IF NOT EXISTS people_director (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                photo TEXT NOT NULL,
                name_en TEXT NOT NULL,
                name_hi TEXT NOT NULL,
                email TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
        """)

        # Administrative Staff
        conn.execute("""
            CREATE TABLE IF NOT EXISTS people_staff (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                photo TEXT NOT NULL,
                name_en TEXT NOT NULL,
                name_hi TEXT NOT NULL,
                designation_en TEXT NOT NULL,
                designation_hi TEXT NOT NULL,
                email TEXT NOT NULL,
                extn_no TEXT NOT NULL,
                sub_category TEXT NOT NULL,
                created_at TEXT NOT NULL,
                sort_order INTEGER DEFAULT 0
            )
        """)

        cols = [c["name"] for c in conn.execute("PRAGMA table_info(people_staff)")]
        if "sort_order" not in cols:
            conn.execute("ALTER TABLE people_staff ADD COLUMN sort_order INTEGER DEFAULT 0")

        # Faculty/Scientists/Engineers
        conn.execute("""
            CREATE TABLE IF NOT EXISTS people_faculty (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                photo TEXT NOT NULL,
                name_en TEXT NOT NULL,
                name_hi TEXT NOT NULL,
                designation_en TEXT NOT NULL,
                designation_hi TEXT NOT NULL,
                location_en TEXT NOT NULL,
                location_hi TEXT NOT NULL,
                email TEXT NOT NULL,
                extn_no TEXT NOT NULL,
                sub_category TEXT NOT NULL,
                created_at TEXT NOT NULL,
                sort_order INTEGER DEFAULT 0
            )
        """)

        cols = [c["name"] for c in conn.execute("PRAGMA table_info(people_faculty)")]
        if "sort_order" not in cols:
            conn.execute("ALTER TABLE people_faculty ADD COLUMN sort_order INTEGER DEFAULT 0")

        # PDFs/Research Scholars
        conn.execute("""
            CREATE TABLE IF NOT EXISTS people_scholars (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                photo TEXT NOT NULL,
                name_en TEXT NOT NULL,
                name_hi TEXT NOT NULL,
                position TEXT NOT NULL,
                lab_en TEXT NOT NULL,
                lab_hi TEXT NOT NULL,
                email TEXT NOT NULL,
                extn_no TEXT NOT NULL,
                created_at TEXT NOT NULL,
                sort_order INTEGER DEFAULT 0
            )
        """)

        cols = [c["name"] for c in conn.execute("PRAGMA table_info(people_scholars)")]
        if "sort_order" not in cols:
            conn.execute("ALTER TABLE people_scholars ADD COLUMN sort_order INTEGER DEFAULT 0")

        # ---------- USER TABLE FOR AUTHENTICATION ----------
        conn.execute("""
            CREATE TABLE IF NOT EXISTS user (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                created_at TEXT NOT NULL,
                last_login TEXT,
                is_active INTEGER DEFAULT 1
            )
        """)

        # Check if we need to add any new columns to user table
        cols = [c["name"] for c in conn.execute("PRAGMA table_info(user)")]
        if "last_login" not in cols:
            conn.execute("ALTER TABLE user ADD COLUMN last_login TEXT")
        if "is_active" not in cols:
            conn.execute("ALTER TABLE user ADD COLUMN is_active INTEGER DEFAULT 1")

        # Create default admin user if no users exist
        admin_exists = conn.execute("SELECT COUNT(*) as count FROM user WHERE username = 'admin'").fetchone()
        if admin_exists['count'] == 0:
            # In production, use proper password hashing - but for initial setup, we'll use plain text
            # The CLI tool will handle password hashing for future users
            conn.execute("""
                INSERT INTO user (username, password, created_at, is_active)
                VALUES (?, ?, datetime('now'), 1)
            """, ('admin', '1499'))  # Default password - should be changed immediately using CLI tool
            print("✅ Default admin user created (username: admin, password: 1499)")
            print("⚠️  IMPORTANT: Please change the default password using the CLI tool!")

        conn.commit()
    finally:
        conn.close()

def resequence(table_name):
    """Resequence sort_order for a table"""
    conn = get_db()
    try:
        if table_name == "downloadable_forms":
            rows = conn.execute(
                f"SELECT id FROM {table_name} ORDER BY sort_order ASC, uploaded_at DESC"
            ).fetchall()
        elif table_name == "links":
            rows = conn.execute(
                f"SELECT id FROM {table_name} ORDER BY sort_order ASC, created_at DESC"
            ).fetchall()
        elif table_name in ["people_staff", "people_faculty", "people_scholars"]:
            rows = conn.execute(
                f"SELECT id FROM {table_name} ORDER BY sort_order ASC, created_at ASC"
            ).fetchall()
        elif table_name == "user":
            rows = conn.execute(
                f"SELECT id FROM {table_name} ORDER BY created_at ASC"
            ).fetchall()
        else:
            rows = conn.execute(
                f"SELECT id FROM {table_name} ORDER BY sort_order ASC, uploaded_at DESC"
            ).fetchall()
        
        for idx, r in enumerate(rows, start=1):
            conn.execute(
                f"UPDATE {table_name} SET sort_order = ? WHERE id = ?",
                (idx, r["id"])
            )
        conn.commit()
    finally:
        conn.close()